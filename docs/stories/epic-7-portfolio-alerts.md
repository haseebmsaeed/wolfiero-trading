# Epic 7 — Portfolio, Watchlist & Alerts

**Goal:** you manage real open trades through Wolfiero instead of a spreadsheet, and it tells you
when something needs attention.
**Done when:** you run two weeks of live positions through it without opening a spreadsheet once.

> **Where the system starts protecting you rather than just informing you.** Selection is a
> once-a-day activity; position management is continuous, and it is where discretionary traders
> actually lose money — by moving stops, holding past the thesis, and not noticing an earnings date.

---

### W-43  Position management                                           [M] [depends: W-29]

**Why this exists**
Without knowing what you hold, the system cannot compute portfolio heat, enforce concentration
limits, or tell you when to act. Every guardrail in Epic 4 is inert until this exists.

**Build**
- Alembic migration for `positions` and `position_events`.
- `services/portfolio.py`: open, update (stop/target/thesis), partial exit, add, close.
- `initial_stop_price` is **immutable after creation** — enforce at the repository level. All
  R-multiples are computed against original risk; a system that recomputes R against a trailed stop
  reports inflated performance.
- Every mutation writes a `position_events` row.
- **Widening a stop requires an explicit `override=true`** and logs a `STOP_WIDENED` event. This is
  the single most destructive discretionary behaviour in swing trading, and making it require a
  deliberate act is the point.
- Optional link to the originating `recommendation_id`.
- `POST /positions`, `PATCH /positions/{id}`, `POST /positions/{id}/close`.

**Acceptance**
- Opening, trailing a stop, partially exiting, and closing produces a complete, ordered event trail.
- Attempting to widen a stop without the override is rejected with a clear error.
- `initial_stop_price` cannot be modified by any code path — test it directly.
- Realised R on close is computed against the initial stop.

---

### W-44  Portfolio state & P&L                                         [M] [depends: W-43]

**Why this exists**
"How am I doing?" needs a correct, instant answer — and heat needs to be live, because it gates
whether you may take a new position at all.

**Build**
- `GET /api/portfolio` per the API contract: per-position live P&L, % to stop, % to target, current
  R, days held, open risk; plus summary exposure, heat, sector concentration, and
  `remaining_risk_budget_usd`.
- **Heat uses current risk**, not initial — a stop at breakeven contributes ~0 and frees budget.
- `can_add_position` computed from the guardrails.
- Quotes fetched in one batch call, not per position.
- `GET /api/portfolio/performance?period=` — win rate, average R, expectancy, by setup and regime.

**Acceptance**
- P&L reconciles exactly against hand-computed fixtures, including a partial exit.
- Heat drops as expected when a stop is raised.
- A closed position leaves realised P&L and realised R permanently recorded.
- Endpoint responds in under 2s with 8 open positions.

---

### W-45  Daily position health checks                                  [M] [depends: W-44, W-35]

**Why this exists**
Positions decay silently. A thesis breaks, an earnings date approaches, a trade goes nowhere for
three weeks. Each is a decision point you will miss unless something surfaces it.

**Build**
- `services/portfolio.py::check_health(position) -> HealthResult` producing flags:
  `STOP_BREACHED`, `TARGET_REACHED`, `THESIS_INVALIDATED` (trend classification broke), `EARNINGS_APPROACHING`
  (T-5 / T-3 / T-1), `TIME_STOP_EXCEEDED` (held past the hold window and below +0.5R),
  `VOLATILITY_SPIKE` (ATR% more than 2× its 50-day average), `BELOW_ENTRY_AFTER_N_DAYS`.
- Status rollup: `HEALTHY` / `WATCH` / `ACTION_REQUIRED`.
- Templated notes explaining each flag — deterministic, not LLM-generated.
- Runs in the pre-market pipeline; results feed the report's actions section.
- The T-1 earnings warning is explicit and unmissable: *"NVDA reports after the close today. You hold
  136 shares. Decide before 16:00."*

**Acceptance**
- Each flag triggers on a purpose-built fixture and on nothing else.
- `THESIS_INVALIDATED` fires when a held position's trend classification degrades from `UPTREND`.
- Earnings warnings escalate correctly at T-5, T-3, T-1 in **trading** sessions.
- `ACTION_REQUIRED` positions appear at the top of the pre-market report.

---

### W-46  Watchlist                                                     [S] [depends: W-13]

**Why this exists**
Some symbols you want tracked regardless of whether they score well today — a name waiting for a
pullback, or a setup you are early on.

**Build**
- Alembic migration for `watchlist_items`.
- `services/watchlist.py` with add / remove / list, an optional note, and a target entry zone.
- Watchlist symbols are always included in news enrichment and intraday monitoring, even when they
  do not appear in the scan.
- `GET|POST|DELETE /api/watchlist`; `manage_watchlist` tool.

**Acceptance**
- "Watch AMD for a pullback to 140" creates an item with the note and the entry zone captured.
- Watchlist symbols receive news enrichment regardless of scan rank.
- "What's on my watchlist?" returns current prices and distance to each target zone.

---

### W-47  Alert engine                                                  [L] [depends: W-44, W-46]

**Why this exists**
Alerts are what let you stop staring at charts. They must be evaluated by **deterministic code, never
an LLM loop** — an LLM polling every five minutes is expensive, slow, and non-reproducible.

**Build**
- Alembic migration for `alerts` and `alert_firings`.
- `services/alerts.py::evaluate(alerts, quotes) -> list[Firing]` — pure Python, no model calls.
- Alert types from the data model: price above/below, % move, volume spike, setup triggered,
  material news, earnings approaching, regime change, stop breach, target reached.
- **Cooldown and dedup**: one firing per condition per `cooldown_minutes` (default 60). Un-throttled
  alerting is how a useful system becomes a muted one.
- Auto-created system alerts for every open position: stop breach and target reached.
- `natural_language` preserved on every alert, so "what alerts do I have?" returns your own words.
- `GET|POST|DELETE /api/alerts`, `GET /api/alerts/firings`; `create_alert` tool.

**Acceptance**
- Creating "tell me if NVDA loses 175" produces a `PRICE_BELOW` alert at 175.00 with the phrasing
  preserved.
- An alert firing twice within the cooldown notifies once.
- Zero LLM calls during evaluation — assert with a call counter.
- Opening a position auto-creates its stop and target alerts.
- Expired alerts stop evaluating and are cleaned up.

---

### W-48  Intraday monitor                                              [M] [depends: W-47]

**Why this exists**
Baseline intraday AI cost must be **zero**. Python watches; the model is involved only if you ask a
follow-up question.

**Build**
- `jobs/intraday_monitor.py`, every `INTRADAY_INTERVAL_MINUTES` (default 5) between 09:30 and 16:00
  on trading days only.
- One batch quote call for open positions + watchlist + today's top candidates.
- Evaluate alerts, persist firings, push notifications to Telegram.
- Alert messages are **templated**, with the relevant context: *"🚨 NVDA broke above $182.50 on 1.8×
  average volume. You have no position. Planned entry was $183.10, stop $175.80."*
- Batch multiple simultaneous firings into a single Telegram message.

**Acceptance**
- Runs only during trading hours on trading days, half-day aware.
- One batch quote call per cycle regardless of symbol count.
- Zero LLM calls in a full simulated session.
- Ten simultaneous firings produce one message, not ten.
- A provider failure skips the cycle with a logged warning and does not kill the scheduler.
