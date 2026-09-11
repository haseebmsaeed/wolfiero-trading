# Epic 5 — News, Catalysts & Earnings

**Goal:** news explains moves, gates risk, and breaks ties — without ever becoming a naive sentiment
signal.
**Done when:** no candidate with earnings inside the hold window reaches you unflagged, and every
news-derived claim in a report carries a source and a timestamp.

> **Read [06-news-and-catalyst-spec.md](../06-news-and-catalyst-spec.md) before writing any code in
> this epic.** The obvious implementation — classify headline sentiment, buy the positive ones —
> loses money for reasons explained there, and this epic is deliberately structured to prevent it.

---

### W-31  News provider interface & adapter                             [M] [depends: W-07]

**Why this exists**
Same reasoning as market data: vendors change, and analysis code must not know which one is in use.

**Build**
- `providers/news/base.py` — ABC with `get_symbol_news(symbol, since, limit)`,
  `get_market_news(since)`, `get_earnings_calendar(symbols, through)`, `health()`.
- One concrete adapter; normalised `NewsItem` model.
- Rate limiting, retries, and circuit breaker inside the adapter.
- Raw vendor payload retained in `classification.raw` so items can be reprocessed under a new prompt
  version without re-fetching (and re-paying).

**Acceptance**
- Returns normalised items with UTC timestamps, regardless of the vendor's timezone convention.
- Recorded fixtures only; no network in CI.
- A provider outage returns an empty list with a `PROVIDER_UNAVAILABLE` warning rather than raising —
  **a missing catalyst must degrade the report, never abort the pipeline.**

---

### W-32  Deduplication & noise filtering                               [M] [depends: W-31]

**Why this exists**
Syndication routinely produces eight copies of one story, and 40–60% of the remaining volume is
listicles and automated price recaps. Without this stage, "number of articles" measures wire
distribution rather than importance — and every subsequent LLM call is spent classifying garbage.

**Build**
- `services/news.py`:
  - `content_hash` = SHA-256 of normalised headline + first 200 chars of body (lowercased,
    punctuation stripped, whitespace collapsed, source prefixes removed).
  - Near-duplicate detection: token-set similarity ≥ 0.85 within 48 hours; keep the earliest and
    most authoritative.
  - Deterministic noise filter with the regex and source rules from the spec §2.3.
- Metrics: `sources_count`, `deduplicated_count`, `noise_filtered` on every research response.

**Acceptance**
- A fixture with 8 syndicated copies of one story collapses to 1.
- All listicle and auto-recap patterns from the spec are removed.
- The filter runs **before** any LLM call — verify with a call counter, because this ordering is the
  entire cost argument.
- Removal rate on a real fixture day lands in the 40–60% band; well outside it means the rules are
  mistuned in one direction or the other.

---

### W-33  News classification                                          [M] [depends: W-32]

**Why this exists**
Materiality and durability are the two dimensions that make news usable at a 2–15 day horizon.
Sentiment alone is not, and an implementation that scores only materiality will systematically buy
one-day spikes at their top.

**Build**
- `providers/ai/prompts/news_classify.v1.md` — versioned, temperature 0, strict JSON output,
  explicitly instructing the model to classify **only the provided text** and never to draw on prior
  knowledge of the company.
- `services/news.py::classify(items)` using the **cheap** model tier, batched where supported.
- Output: category, direction, materiality (0–1), durability (0–1), summary, `affects_thesis`,
  reasoning. Persisted to `news_items` with model and prompt version.
- Classifications are cached permanently by `(content_hash, prompt_version)` — never reclassify the
  same item under the same prompt.
- Malformed JSON → one retry, then mark `is_noise=true` and log. Never crash the pipeline on a bad
  model response.

**Acceptance**
- A hand-labelled fixture of 50 items reaches ≥ 80% agreement on category and direction, and
  materiality within ±0.2.
- A guidance raise scores high durability; a single analyst upgrade scores low durability. This
  distinction is the point of the story — test it explicitly.
- Reclassifying an already-classified item issues zero model calls.
- Cost per 100 items is logged and stays within the configured budget.

---

### W-34  Catalyst aggregation & scoring                                [S] [depends: W-33]

**Why this exists**
One material catalyst is the signal. Averaging it against six trivial items dilutes exactly the thing
you are looking for — which is why this uses `max`, not `mean`.

**Build**
- `catalyst_score = max(materiality × durability × recency_weight)` with recency weights
  1.0 / 0.7 / 0.4 / 0.0 by age band.
- Direction handling: bullish on a long → as computed; bearish on a long → score 0 **plus** a
  `CONFLICTING_NEWS` flag surfaced in the report; no news → **0.5 neutral**.
- Wire into the scorer, replacing the W-21 default.

**Acceptance**
- A single high-materiality item outranks six low-materiality ones (proves `max`, not `mean`).
- A no-news candidate scores 0.5 and is not penalised.
- A bullish chart with bearish news raises `CONFLICTING_NEWS` and the flag reaches the report —
  that situation is for a human to look at, not for the system to average away silently.

---

### W-35  Earnings calendar & the hold-window veto                      [M] [depends: W-31]

**Why this exists**
**This is the highest-value story in the entire backlog per line of code.** Earnings is deterministic,
scheduled, binary risk that routinely produces 8–15% overnight gaps. Your stop does not protect you —
the gap opens straight through it. For a 2–15 day hold this is not an edge case; it is a recurring,
foreseeable hazard, and one avoided gap pays for the whole project.

**Build**
- Alembic migration for `earnings_events`.
- `services/earnings.py`:
  - `refresh_calendar(symbols, through)` — daily, tracking `is_confirmed` separately from estimated.
  - **Estimated dates are treated as 3 days earlier than stated** — vendor estimates drift, and
    drifting toward you is the dangerous direction.
  - `is_in_hold_window(symbol, as_of, window_days)` using a **real market calendar**, never
    `timedelta`.
  - `days_until_earnings(symbol)` in trading sessions.
- Veto applied in scanner stage 6 under `EARNINGS_POLICY=veto` (default); `flag` mode surfaces the
  candidate with a warning and a reduced size.
- Post-earnings re-eligibility after 1 session — having just cleared the event, risk is now *lower*
  than average.
- `GET /api/news/earnings-calendar`.

**Acceptance**
- A symbol reporting in 10 trading days is vetoed with `EARNINGS_IN_WINDOW` under the default policy.
- The vetoed candidate is still **persisted**, so the policy's cost can be measured later in Epic 8.
- Hold-window arithmetic is correct across a holiday week — assert specifically against Thanksgiving
  and the Christmas period, where calendar-day math is off by two or more sessions.
- Estimated dates apply the 3-day safety margin; confirmed dates do not.
- `flag` mode surfaces the candidate with the exact date and BMO/AMC session.

---

### W-36  Research synthesis & the `research_stock` tool                [M] [depends: W-34, W-35]

**Why this exists**
This is the first place an LLM does genuine language work: reading unstructured news and producing a
thesis. It is also where a persuasive-but-unfounded narrative could enter the system, so the
constraints matter as much as the output.

**Build**
- `providers/ai/prompts/research.v1.md` — mid tier, receiving **only** the technical snapshot, the
  classified news items, and the earnings record.
- Hard prompt constraints: cite source and date for every factual claim; never state a price absent
  from the provided data; explicitly say "no material catalyst identified" when true; **always state
  what would invalidate the trade.**
- `services/research.py::research(symbol)` → `catalyst_summary`, `risks[]`, `thesis`.
- A response validator that **rejects and retries** any thesis lacking a stated risk.
- `POST /api/news/research` with `include_analysis` gating the LLM call.
- `research_stock` tool added to the agent.

**Acceptance**
- Output cites a source and date for every factual claim; a claim without one fails the validator.
- A symbol with no news yields "no material catalyst identified" rather than a manufactured narrative.
- `include_analysis=false` issues zero model calls — verify with a counter, since this flag is the
  cost control.
- "Why is NVDA up today?" returns a sourced explanation, or an honest "no catalyst found in the
  available news."

**Notes**
The stated-risk requirement is what converts persuasion into analysis. An LLM asked to justify a
candidate will always produce a persuasive justification — that is what it is best at. Forcing it to
name the disconfirming evidence is the only structural defence against that.
