# Wolfiero Market Agent — Product Requirements

**Status:** Draft v1.0 · **Owner:** Haseeb Saeed · **Last revised:** 2026-09-10

---

## 0. How to read this document

You gave me a requirement that was roughly *"I want an app for swing trading that uses trends and
news so I can decide which stocks go up and down."* That is a real and valid product instinct, but
as written it is not buildable — it does not say what a "trend" is, what makes news *actionable*,
what timeframe you hold for, or what the system does when it is wrong.

This document is my corrected, tightened version. Where I changed or added something material, I
flag it inline as **[PO correction]** with the reasoning, so you can push back on any of it.

---

## 1. The problem, stated precisely

You are a **discretionary swing trader**. That means:

- You hold positions for roughly **2 to 15 trading days** — longer than a day trade, shorter than an
  investment. This single number drives almost every design decision below.
- You make the final buy/sell call yourself. You are not trying to build a fund or a black box.
- Your edge is supposed to come from combining **price behaviour** (is this stock in a strong,
  orderly uptrend with a clean entry?) with **catalyst awareness** (is something happening to this
  company that explains or threatens that move?).

The problem is not "I don't know how to trade." The problem is **throughput and consistency**:

| Pain | What it actually costs you |
|---|---|
| There are ~3,000 liquid US stocks. You can eyeball maybe 50 a night. | You never see most of the good setups. Your universe is accidental, not chosen. |
| Checking news per-symbol is manual, slow, and biased toward whatever headline you happened to see. | You confirm ideas you already like instead of testing them. |
| Earnings dates ambush you. | You hold through a print you didn't know about and eat a 12% gap. This is the single most expensive recurring mistake in swing trading. |
| You judge stocks in isolation, ignoring whether the *whole market* is risk-on or risk-off. | You take clean long setups into a market-wide downtrend, and they all fail together. |
| You don't systematically record why you entered. | You cannot tell which of your setups actually make money, so you never improve. |

**[PO correction]** Your original framing was "which stocks will go up and down." I am deliberately
reframing the product goal away from *prediction* and toward **filtering, evidence assembly, and
discipline enforcement**. No system — including this one — reliably predicts direction. What a good
system does is surface a small number of statistically favourable, well-documented situations and
stop you from making known unforced errors. That reframe is what makes the product achievable.

---

## 2. Product vision

> Wolfiero is a private market analyst that works overnight. Each morning it hands its operator a
> short, ranked, evidence-backed list of swing-trade candidates — each with a defined entry, stop,
> target, catalyst, and risk — plus an honest read on whether today is a day to be taking risk at
> all. During the session it watches only what matters and speaks only when something changed.

**Success is not "the picks go up."** Success is:

1. You spend **under 15 minutes** each morning to have a fully-formed trading plan.
2. You **never again** hold a position into an unknown earnings date.
3. After 6 months you can answer, with data, *"which of my setups work, in which market regime?"*

---

## 3. Users

There is exactly one user class in v1. Do not build for anyone else.

### Primary: The Operator (you)

- Experienced enough to read RSI, moving averages, support/resistance without tutoring.
- Time-constrained; interacts mostly from a phone, mostly via Telegram.
- Wants raw analytical substance, not motivational language or hedged disclaimers.
- Trusts the system only as far as it can show its work.

**[PO correction]** A single-user system is a *massive* simplification and I am making it explicit
so nobody "helpfully" builds multi-tenancy, roles, billing, or a web signup flow. Auth in v1 is:
*is this Telegram chat ID on the allowlist?* Nothing more. Multi-user is a Phase 7+ conversation and
would require revisiting data isolation, rate limits, and — importantly — financial-advice
regulation, which does not apply to a tool you build for yourself but absolutely does apply the
moment a second person pays for it.

---

## 4. Scope

### 4.1 In scope for v1

| Capability | One-line definition |
|---|---|
| Market regime assessment | A daily risk-on / neutral / risk-off read derived from SPY, QQQ, IWM, VIX, and sector breadth |
| Universe management | A maintained, liquidity-filtered list of tradeable US equities and ETFs |
| Daily scanner | A deterministic funnel that reduces the universe to a ranked short list |
| Technical analysis | Trend, momentum, volatility, volume, relative strength, support/resistance, setup classification |
| Catalyst & news research | Per-symbol news retrieval, deduplication, classification, and materiality scoring |
| Earnings calendar awareness | Hard blocking/flagging of symbols with an earnings event inside the intended hold window |
| Trade plan generation | Entry trigger, stop, target(s), R-multiple, and suggested position size for each candidate |
| Watchlist | Symbols you want tracked regardless of whether they score well today |
| Portfolio tracking | Manually-entered open positions with live P&L, stop/target distance, and health checks |
| Alerting | Price, volume, and catalyst-triggered notifications on portfolio + watchlist + top candidates |
| Scheduled reports | Pre-market report, midday pulse (optional), end-of-day report, weekly review |
| Conversational interface | Natural-language Q&A over all of the above, via Telegram |
| Outcome tracking | Every recommendation is scored against what actually happened afterwards |

### 4.2 Explicitly out of scope for v1

Listed so an implementing agent does not "add value" by building them.

- **Order execution of any kind.** No broker write access. No API keys with trade permission.
- Options, futures, crypto, forex. US cash equities and ETFs only.
- Intraday / sub-15-minute strategies. The data cadence and cost model do not support it.
- Short selling as a *primary* strategy. Bearish setups are *identified* and reported, because
  knowing what is weak informs regime and sector rotation, but sizing/borrow/locate logic is not built.
- A web UI or mobile app. Telegram is the interface. (A read-only web dashboard is a Phase 6 nice-to-have.)
- Multi-user, teams, sharing, billing.
- Backtesting engine. **[PO correction]** You will want this, and it is genuinely valuable, but a
  credible backtester is its own multi-week project with hard problems (survivorship bias,
  point-in-time fundamentals, look-ahead leakage in news timestamps). v1 instead captures *forward*
  outcomes on live recommendations, which is slower but leakage-free and far cheaper to build. See
  Epic 8.
- Social-media sentiment (Reddit/X/StockTwits). High noise, high cost, low demonstrated edge at
  swing timeframes. Revisit only with evidence.

---

## 5. Domain model — the concepts the system reasons about

An implementing agent must internalise these. They are the shared vocabulary of every later document.

### 5.1 Market Regime

A daily classification of the overall risk environment: `RISK_ON`, `NEUTRAL`, `RISK_OFF`, each with
a 0–1 confidence. Derived from index trend structure, breadth, and volatility.

**Why it exists:** roughly 60–70% of an individual stock's short-term move is explained by the market
and its sector. The best-looking breakout in the world fails when the index is breaking down. Regime
therefore acts as a **global multiplier on long candidate scores and on suggested position size** —
in `RISK_OFF`, the system shrinks the number of ideas and the size of each, rather than pretending
nothing changed.

### 5.2 Setup

The *shape* of the opportunity. v1 recognises four long setups and reports (but does not size) their
bearish mirrors:

| Setup | Plain English | Why a swing trader wants it |
|---|---|---|
| **Breakout** | Price clears a well-defined multi-week resistance level on above-average volume. | Supply above the level has been absorbed; the path of least resistance is up. |
| **Pullback** | A stock in a confirmed uptrend retraces to a rising moving average or prior support and stops falling. | Best risk/reward of the four — you buy near a level where being wrong is obvious and cheap. |
| **Consolidation / coil** | Price range contracts sharply (volatility compression) after an advance. | Compression precedes expansion. You get in before the move, with a tight stop. |
| **Momentum continuation** | Persistent relative strength with orderly, shallow retracements. | Winners keep winning over 1–3 month horizons; this is the most robust anomaly in the literature. |

**Why it exists:** "this stock looks good" is unmeasurable. "This stock is a pullback setup" is a
testable category you can later compute a win rate for.

### 5.3 Candidate

A symbol that survived the scanner funnel on a given day, with its computed score, detected setup,
and generated trade plan. Candidates are snapshots — they belong to a date and are never mutated.

### 5.4 Recommendation

A candidate that the system actually surfaced to you in a report, **frozen with full context**: the
prices, the score, the thesis text, the AI model and prompt version that wrote it, the strategy
version, and the market regime at the time. This immutability is what makes later analysis honest.

### 5.5 Catalyst

A discrete, dated, company-specific event that plausibly explains or threatens a price move:
earnings, guidance change, analyst rating change, M&A, regulatory/FDA decision, major contract,
product launch, index inclusion, legal outcome, insider or institutional flow.

**[PO correction] — this is the most important correction in the document.** Your original ask was
"check news to see which stocks will go up and down." Treating raw news sentiment as a directional
signal is a well-known way to lose money: by the time a headline is published, liquid markets have
already repriced it, and headline *tone* correlates poorly with subsequent returns. So Wolfiero uses
news in three specific, defensible ways instead:

1. **Explanation.** A stock is up 9% on 5x volume — *why?* A confirmed catalyst turns an unexplained
   move (often a pump or a one-off) into a thesis you can reason about.
2. **Risk gating.** Known upcoming events (above all, earnings) are hard constraints. A setup that
   would otherwise be A-grade gets blocked or downgraded if earnings land inside the hold window,
   because a binary event overwhelms any technical edge.
3. **Tie-breaking.** Among similarly-scored technical setups, prefer the one with a fresh, durable,
   fundamental catalyst over the one moving on nothing.

News never *creates* a candidate on its own in v1. It promotes, demotes, or vetoes one.

### 5.6 Trade Plan

Entry trigger, stop loss, primary target, resulting R-multiple, and suggested share count for a
given account risk budget. A candidate without a valid plan — specifically, one whose reward:risk is
below the configured floor — is **not shown**, no matter how good it looks.

**Why it exists:** it converts an opinion into an executable, pre-committed decision, and it is the
mechanism that enforces discipline *before* you are emotionally invested.

---

## 6. Functional requirements

Numbered for traceability. Each story in `stories/` references these IDs.

### FR-1 Market data

- **FR-1.1** The system retrieves daily OHLCV history for every symbol in its universe, with at least
  400 trading days of lookback (enough for a 200-day moving average plus warm-up).
- **FR-1.2** All prices are **split- and dividend-adjusted**, consistently. Mixing adjusted and raw
  series silently corrupts every indicator; this must be asserted in code.
- **FR-1.3** Market data access sits behind a provider-agnostic interface. Swapping the vendor must
  not touch any analysis code.
- **FR-1.4** The system detects and flags stale, gapped, or obviously bad data (zero volume, zero
  price, >50% single-day move without a corporate action) and excludes those bars from analysis
  rather than computing nonsense on them.
- **FR-1.5** Intraday quotes are retrieved on demand for portfolio/watchlist monitoring, at a cadence
  no faster than every 5 minutes.

### FR-2 Market regime

- **FR-2.1** Regime is computed once per trading day before the pre-market report, and is persisted.
- **FR-2.2** Inputs: SPY/QQQ/IWM trend structure (price vs 20/50/200 EMA, slope), VIX level and
  20-day change, market breadth (% of universe above its 50-day MA), and sector ETF relative strength.
- **FR-2.3** Output: label, confidence, per-input contributions, and a human-readable rationale.
- **FR-2.4** Regime modulates candidate scores and suggested position sizing per
  [07-risk-and-position-sizing.md](07-risk-and-position-sizing.md).
- **FR-2.5** Regime *transitions* (e.g. NEUTRAL → RISK_OFF) generate an explicit alert; transitions
  are more actionable than states.

### FR-3 Universe

- **FR-3.1** The universe is a persisted, refreshable list of US-listed common stocks and liquid ETFs.
- **FR-3.2** Liquidity floor: 20-day average dollar volume ≥ $20M and price ≥ $5.
  **[PO correction]** A *dollar*-volume floor, not a share-volume floor — 5M shares of a $2 stock is
  not liquidity, it is a trap. The price floor removes the sub-$5 tape where gaps are unmanageable.
- **FR-3.3** Exclusions: recent IPOs with under 60 trading days of history (no meaningful base),
  leveraged/inverse ETFs, and an operator-maintained blocklist.
- **FR-3.4** Universe refresh runs weekly; membership changes are logged.

### FR-4 Technical analysis

- **FR-4.1** Computes per symbol: SMA/EMA (20/50/200), RSI(14), MACD(12,26,9), ATR(14),
  ATR-as-%-of-price, 20-day realised volatility, volume vs 20-day average, relative strength vs SPY
  over 1/3/6 months, distance from 52-week high/low, and swing-pivot support/resistance levels.
- **FR-4.2** Classifies trend as `UPTREND` / `DOWNTREND` / `RANGE` using moving-average stack and slope.
- **FR-4.3** Detects the four setups in §5.2, each returning a 0–1 quality score, not a boolean.
  **[PO correction]** Booleans throw away information and make everything a tie. Graded detectors let
  the scorer distinguish a textbook pullback from a marginal one.
- **FR-4.4** Every indicator implementation is unit-tested against fixed, hand-checked fixtures.
  Silent indicator bugs are the most dangerous class of defect in this system because the output
  still *looks* plausible.

### FR-5 Scanner

- **FR-5.1** Executes the staged funnel in [05-scanner-and-scoring-spec.md](05-scanner-and-scoring-spec.md).
- **FR-5.2** Records, for every stage, how many symbols entered and exited, and why symbols were
  dropped. Without this you cannot debug an empty result set.
- **FR-5.3** Completes a full 3,000-symbol scan in **under 10 minutes** on the target VM.
- **FR-5.4** Produces a ranked candidate list persisted with the scan run.
- **FR-5.5** Is idempotent: re-running for the same date replaces, never duplicates.

### FR-6 Scoring

- **FR-6.1** A single composite 0–100 score per candidate, from weighted normalised components.
- **FR-6.2** Weights live in versioned configuration, not in code, and every scan records which
  `strategy_version` produced it. **[PO correction]** Without version stamping, tuning the weights
  silently invalidates all historical performance analysis.
- **FR-6.3** Scores are explainable: the per-component contribution is stored and reportable.
- **FR-6.4** Hard vetoes (earnings inside hold window, reward:risk below floor, failed liquidity)
  are applied *after* scoring and recorded as explicit reasons, not by silently zeroing a score.

### FR-7 News & catalysts

- **FR-7.1** Retrieves news per symbol for the top-N candidates, the watchlist, and all open positions.
- **FR-7.2** Deduplicates syndicated copies of the same story.
- **FR-7.3** Classifies each item: category, direction (bullish/bearish/neutral), materiality (0–1),
  and durability (one-day pop vs multi-week re-rating).
- **FR-7.4** Filters out low-value noise: routine "5 stocks to watch" listicles, automated price-move
  recaps, and paid promotional content.
- **FR-7.5** Maintains an earnings calendar with confirmed vs estimated status per symbol.
- **FR-7.6** **Any** candidate with earnings inside the intended hold window is either vetoed or
  flagged `EARNINGS_RISK` per operator configuration. Default: veto for new long entries.
- **FR-7.7** Every news-derived claim in a report carries a source link and a timestamp. Unsourced
  claims are a hallucination surface and are not permitted.

### FR-8 Trade plans

- **FR-8.1** Per candidate: entry trigger, stop, target, R-multiple, suggested shares, suggested
  dollar exposure, and the reasoning for each level.
- **FR-8.2** Stops are volatility-aware (ATR-based) and structure-aware (below the relevant swing
  low / moving average), taking whichever is more defensible — never a flat percentage.
- **FR-8.3** Minimum reward:risk of **2.0** by default; below that, the candidate is dropped.
- **FR-8.4** Position size derives from a fixed fractional risk budget (default 1% of account equity
  per trade) and the stop distance — *not* from conviction. **[PO correction]** Sizing by conviction
  is how traders blow up; sizing by stop distance equalises risk across every idea.
- **FR-8.5** A maximum portfolio heat (total open risk, default 6%) and a sector-concentration cap
  are enforced, and the system refuses to suggest new entries that would breach them.

### FR-9 Portfolio

- **FR-9.1** Operator records open positions manually (symbol, shares, entry price, date, stop,
  target, thesis).
- **FR-9.2** The system computes live and closed P&L, % to stop, % to target, R-multiple to date,
  days held, and current portfolio heat.
- **FR-9.3** Daily position health check flags: stop breached, target reached, thesis invalidated
  (trend break), earnings approaching, time stop exceeded (held well past the intended window),
  and abnormal volatility.
- **FR-9.4** Closed positions are retained with full history for performance analytics.

### FR-10 Watchlist & alerts

- **FR-10.1** Operator can add/remove symbols with an optional note and target entry zone.
- **FR-10.2** Alert types: price crosses level, % move threshold, volume spike, setup triggered,
  material news published, earnings date approaching, regime change.
- **FR-10.3** Alerts are created conversationally ("tell me if NVDA loses 175") and translated into
  structured, stored rules.
- **FR-10.4** Alerts are evaluated by deterministic code on a schedule — **not** by an LLM loop.
- **FR-10.5** Alerts deduplicate and cool down; an alert fires once per condition per configurable
  window. **[PO correction]** Un-throttled alerting is how a useful system becomes a muted one.

### FR-11 Reports

- **FR-11.1 Pre-market report** (before the open): regime, top candidates with plans, portfolio
  status and required actions, today's earnings/economic events, and what changed since yesterday.
- **FR-11.2 End-of-day report:** how the day's ideas performed, position updates, triggered alerts,
  tomorrow's watch items.
- **FR-11.3 Weekly review:** realised performance, win rate by setup and by regime, largest win/loss
  with post-mortem, and adherence to the plan.
- **FR-11.4** Reports are persisted and retrievable ("show me last Tuesday's report").
- **FR-11.5** Telegram delivery is chunked to fit message limits without breaking formatting.

### FR-12 Conversational interface

- **FR-12.1** Free-form Q&A over every capability above.
- **FR-12.2** The agent answers **only** from data returned by backend tool calls. If a tool returns
  nothing, it says so. It never fills a gap from model memory.
  **[PO correction]** This is the single highest-risk behaviour in the product. An LLM stating a
  stale or invented price with total confidence is worse than no system at all. It must be enforced
  in the system prompt *and* checked by a response guard.
- **FR-12.3** Every numeric claim in a response must be traceable to a tool result in that turn.
- **FR-12.4** Conversation context persists across messages within a session.

### FR-13 Outcome tracking & learning

- **FR-13.1** Each recommendation is tracked forward for a configurable horizon (default 15 trading
  days), recording max favourable excursion, max adverse excursion, whether entry triggered, whether
  stop or target hit first, and the realised R-multiple.
- **FR-13.2** Aggregate analytics sliced by setup, regime, score bucket, sector, catalyst presence,
  AI model, and strategy version.
- **FR-13.3** Findings surface in the weekly review as observations — e.g. *"pullback setups in
  RISK_ON returned +0.7R average over 34 samples; breakouts in RISK_OFF returned −0.4R over 21."*
- **FR-13.4** The system **does not** auto-tune its own weights in v1. It reports; you decide.
  **[PO correction]** Automatic optimisation on a few hundred samples overfits with near-certainty.
  Human-in-the-loop tuning with version stamping is both safer and more informative.

---

## 7. Non-functional requirements

| ID | Requirement | Rationale |
|---|---|---|
| NFR-1 | Pre-market pipeline completes with ≥20 min of margin before the report send time | A late report is a useless report |
| NFR-2 | Conversational query p95 latency < 8s; simple lookups < 3s | Telegram feels broken beyond that |
| NFR-3 | AI spend ≤ a configured monthly cap, with per-run cost logged | The funnel is the control; the log proves it |
| NFR-4 | Any single provider outage degrades gracefully — partial report with an explicit gap notice, never silence | Silence is indistinguishable from a crash |
| NFR-5 | All secrets in environment/secret store; never in the repo; scanned in CI | Market-data and AI keys are billable |
| NFR-6 | API not exposed to the public internet without authentication; Telegram restricted to an allowlisted chat ID | It is a single-operator system |
| NFR-7 | Structured logging with a correlation ID spanning Telegram → agent → API → provider | Debugging a bad recommendation requires the full trace |
| NFR-8 | Indicator and scoring logic ≥90% unit-test coverage; fixture-based golden tests | Silent math errors produce plausible garbage |
| NFR-9 | Nightly database backup with a **restore that has actually been tested** | Outcome history is irreplaceable; it cannot be recomputed |
| NFR-10 | All timestamps stored UTC, displayed in the operator's market timezone (America/New_York) | Timezone bugs around the open/close are endemic and corrupt daily bar alignment |

---

## 8. Assumptions and open questions

**Assumptions** (correct me if wrong):
- US market hours only; operator is comfortable with pre-market reports in local time.
- Account equity is entered manually and updated occasionally, not synced from a broker.
- Long-biased strategy; shorts are informational.
- Budget tolerance exists for one paid market-data tier and one paid news source.

**Open questions blocking specific epics:**
1. What is the account equity and per-trade risk %? (Blocks FR-8.4 defaults.)
2. Maximum concurrent open positions? (Blocks portfolio heat defaults — I have assumed 6.)
3. Preferred market-data vendor, or should the abstraction ship with a free tier first?
4. Is a midday pulse report wanted, or is it noise? (I have defaulted it to off.)
5. Hard monthly ceiling for AI + data spend?

---

## 9. Release plan

| Phase | Deliverable | "Done" means |
|---|---|---|
| **0 — Foundation** | VM, Docker Compose, Postgres, FastAPI skeleton, Telegram round-trip | You send "ping" in Telegram and get a reply from the agent |
| **1 — Single-stock analysis** | Provider abstraction, indicators, `/stocks/analyze` | "Analyze NVDA" returns a correct, sourced technical read end-to-end |
| **2 — Scanner** | Universe, funnel, scoring, candidate persistence | "Find today's top swing candidates" returns a ranked, explainable list in under 10 min |
| **3 — Regime & risk** | Regime engine, trade-plan generator, sizing, vetoes | Every candidate arrives with entry/stop/target/size and regime-adjusted score |
| **4 — News & catalysts** | News provider, dedup, classification, earnings calendar, veto logic | No candidate with earnings in the window ever reaches you unflagged |
| **5 — Reports & alerts** | Scheduler, pre-market/EOD/weekly reports, alert engine | Reports arrive on time, unprompted, for five consecutive trading days |
| **6 — Portfolio** | Positions, P&L, health checks, heat | You manage real open trades through it for two weeks without a spreadsheet |
| **7 — Memory & learning** | Outcome tracking, analytics, weekly findings | The weekly review answers "which setups worked" from real data |

Each phase is independently useful. Stop after any of them and you still have something you'd use.

---

## 10. Compliance and safety posture

- Wolfiero is a **personal decision-support tool**, not investment advice, and every report carries
  that notice.
- No execution capability, and no broker credentials with write scope, in any phase.
- The agent must never present a projection as a fact, and must always attribute news claims.
- If a data source is stale or unavailable, the report says so explicitly rather than proceeding
  quietly on old numbers.
