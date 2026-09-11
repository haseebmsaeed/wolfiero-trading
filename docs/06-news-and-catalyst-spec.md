# Wolfiero — News & Catalyst Specification

> This document exists because "use news to decide which stocks go up" is the requirement most
> likely to be implemented naively, and the naive implementation loses money.

---

## 1. The correction, stated plainly

**The intuition:** good news → stock up, bad news → stock down. So classify headlines by sentiment
and buy the positive ones.

**Why it fails:**

1. **You are late.** A public headline has already been priced by participants with faster data.
   Trading a Reuters headline at 09:35 means taking the other side from someone who traded the wire
   at 09:30:01.
2. **Tone and direction decouple constantly.** "Beats earnings, stock falls 9%" is an everyday
   occurrence, because price responds to the *surprise versus expectations*, not to the adjective in
   the headline. A sentiment classifier cannot see expectations.
3. **Volume overwhelms signal.** A liquid stock generates dozens of items a day, most of which are
   syndicated duplicates, automated "shares move on volume" recaps, or listicles. Naive aggregation
   scores the noisiest stock as the most newsworthy.
4. **Promotional content is adversarial.** Some "news" exists specifically to be scraped by systems
   like yours.

**What news is actually good for at swing timeframes** — three jobs, and only these three:

| Job | Question it answers | Effect on the pipeline |
|---|---|---|
| **Explanation** | *Why* is this moving? | Converts an unexplained move into a thesis, or exposes it as noise |
| **Risk gating** | What is scheduled that could destroy my thesis overnight? | Hard veto or flag — this is the highest-value use by far |
| **Tie-breaking** | Between two similar setups, which has a durable reason behind it? | 10% of the composite score |

**In v1, news never creates a candidate on its own.** Technicals nominate; news promotes, demotes,
or vetoes. This ordering is deliberate and should not be "improved" without evidence.

---

## 2. Pipeline

```
FETCH  →  DEDUPE  →  NOISE FILTER  →  CLASSIFY  →  AGGREGATE  →  SCORE / VETO
```

### 2.1 Fetch

Only for symbols that matter: the top ~20 candidates, the watchlist, and all open positions.
Typically 30–50 symbols/day, never the full universe.

- Window: 7 days by default, 30 days for research queries.
- Per symbol, cap at 25 most recent items after filtering.
- Store raw payload in `news_items.classification.raw` for reprocessing under a new prompt version.

### 2.2 Dedupe

`content_hash = sha256(normalize(headline) + normalize(first_200_chars_of_body))` where
`normalize` lowercases, strips punctuation, collapses whitespace, and removes source prefixes
("(Reuters) -").

Near-duplicates (same story, reworded) are caught with token-set similarity ≥ 0.85 within a 48-hour
window; keep the earliest-published and the most authoritative source.

> Syndication routinely produces 8 copies of one story. Without dedupe, "number of articles" becomes
> a measure of wire distribution rather than of importance.

### 2.3 Noise filter — deterministic, before any LLM call

Drop items matching:
- Listicle patterns: `^\d+ (stocks|things)`, `stocks to watch`, `best stocks`, `why .* is trending`
- Auto-generated recaps: `shares (up|down) \d+%`, `moving average crossover`, `hits 52-week`
- Promotional sources (maintained blocklist), sponsored markers
- Aggregator stubs under 200 characters with no substantive body
- Items whose only relation to the symbol is appearance in a list of ten tickers

This is a regex-and-rules pass, not an LLM pass. It removes 40–60% of volume at effectively zero
cost, which is precisely why it runs first.

### 2.4 Classify — the one LLM step

Cheap/fast model, one call per item (batched where the provider allows), returning strict JSON:

```json
{
  "category": "GUIDANCE",
  "direction": "BULLISH",
  "materiality": 0.88,
  "durability": 0.75,
  "summary": "Raised FY revenue guidance ~8% above consensus, citing datacenter demand.",
  "affects_thesis": true,
  "reasoning": "A guidance raise changes forward estimates rather than describing past results."
}
```

**Materiality (0–1) — could this plausibly move the stock more than 2%?**

| Band | Examples |
|---|---|
| 0.8–1.0 | Earnings surprise, guidance change, M&A, FDA decision, CEO departure, major contract, index inclusion |
| 0.5–0.8 | Analyst upgrade/downgrade from a tier-1 house, notable product launch, partnership, insider cluster buy |
| 0.2–0.5 | Conference appearance, minor partnership, routine filing |
| 0.0–0.2 | Recaps, opinion pieces, generic sector commentary |

**Durability (0–1) — does this change the forward outlook, or is it a one-day event?**
High durability = re-rates forward estimates (guidance, secular contract wins, regulatory approval).
Low durability = one-day pop (a single upgrade, a conference mention, a short squeeze).

> The distinction matters directly for a 2–15 day hold. A high-materiality, low-durability item
> produces a spike that mean-reverts inside your window — it is a reason to *avoid* chasing, not a
> reason to buy. An implementation that only scores materiality will systematically buy tops.

**Prompt discipline:** the classification prompt is versioned in `providers/ai/prompts/`, its
version is stored on every row, and it explicitly instructs the model to classify *the text
provided only*, never to use prior knowledge about the company. Temperature 0.

### 2.5 Aggregate → `catalyst_score`

```python
score = max(item.materiality * item.durability * recency_weight(item) for item in items)
recency_weight = 1.0 (≤2d), 0.7 (3–5d), 0.4 (6–10d), 0.0 (>10d)
```

**`max`, not `mean`.** One genuinely material catalyst is the signal; averaging it against six
trivial items dilutes exactly the thing you are looking for.

Direction handling:
- Bullish catalyst on a long candidate → score as computed.
- Bearish catalyst on a long candidate → `catalyst_score = 0` **and** raise a `CONFLICTING_NEWS`
  flag that appears in the report. A bullish chart against bearish news is a situation for a human
  to look at, not for the system to silently average away.
- No news at all → **0.5, the neutral value.** Absence of news is not bad news.

---

## 3. Earnings — the highest-value component in the system

### 3.1 Why it is treated separately

Everything above is probabilistic. Earnings is deterministic risk: a scheduled, binary event that
routinely produces 8–15% overnight gaps in liquid names. Your stop does not protect you — the gap
opens through it. One such event can erase a month of disciplined gains.

For a 2–15 day hold, this is not an edge case. It is a recurring, foreseeable hazard, and the
cheapest thing the entire system does is prevent it.

### 3.2 Rules

1. Maintain `earnings_events` for the full universe, refreshed daily, with `is_confirmed` distinct
   from estimated. **Treat an estimated date as if it were three days earlier than stated** — vendor
   estimates drift, and drifting *toward* you is the dangerous direction.
2. Hold window = `HOLD_WINDOW_DAYS` (default 15 *trading* days — use a market calendar, never
   calendar-day arithmetic).
3. `EARNINGS_POLICY=veto` (default): any long candidate with earnings inside the window is vetoed,
   with `veto_reasons: ["EARNINGS_IN_WINDOW"]`. Vetoed candidates are still persisted so the policy's
   cost can be measured later.
4. `EARNINGS_POLICY=flag`: the candidate is surfaced with a prominent warning and a reduced position
   size, and the report states the exact date and session (BMO/AMC).
5. **Open positions get escalating warnings** at T-5, T-3, and T-1 sessions. The T-1 alert is
   explicit: *"NVDA reports after the close today. You hold 136 shares. Decide before 16:00."*
6. Post-earnings, the symbol becomes eligible again after 1 session — post-earnings drift is a
   legitimate setup, and having just cleared the event, the risk is now *lower* than average.

### 3.3 Sector- and macro-level events

Track a lightweight economic calendar: FOMC, CPI, PCE, NFP. These do not veto individual candidates
but reduce the regime `position_size_multiplier` on the day of and the day before a high-impact
release, and the report names the event.

---

## 4. Research synthesis

For the final top candidates, one mid-tier LLM call per symbol produces the `catalyst_summary`,
`risks`, and the thesis paragraph, given **only**: the technical snapshot, the classified news
items, and the earnings record.

Hard constraints in the prompt:
- Cite source and date for every factual claim.
- Never state a price not present in the provided data.
- Explicitly say "no material catalyst identified" when that is the case — do not manufacture one.
- Surface disconfirming evidence, not just the bull case. A thesis without a stated risk is
  incomplete and must be rejected by the response validator.

> The last constraint is the one that makes the output trustworthy. An LLM asked to justify a
> candidate will always produce a persuasive justification — that is what it is good at. Forcing it
> to also state what would invalidate the trade is what converts persuasion into analysis.

---

## 5. What is deliberately excluded

| Excluded | Why |
|---|---|
| Reddit / X / StockTwits sentiment | Extreme noise, adversarial manipulation, and no demonstrated edge at 2–15 day horizons. Revisit only with measured evidence. |
| Real-time news trading | Requires sub-second latency the architecture does not have and you should not compete for. |
| Full-text article scraping | Copyright and fragility. Use vendor-provided summaries. |
| Sentiment scores from the news vendor | Black-box, unversioned, and not comparable across time. Classify in-house where you control and version the definition. |
| Options-flow "unusual activity" | Widely misinterpreted — most large prints are hedges, not directional bets. |
