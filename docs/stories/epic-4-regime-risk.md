# Epic 4 — Market Regime, Trade Plans & Risk

**Goal:** every candidate arrives with a defined entry, stop, target, R-multiple, and position size,
adjusted for the market environment and constrained by portfolio-level limits.
**Done when:** no candidate can reach you without a valid, guardrail-checked trade plan.

> **This epic has the largest effect on your actual results of anything in the backlog.** Selection
> determines whether you have an edge; sizing and stops determine whether you survive long enough to
> collect it. A mediocre scanner with excellent risk management makes money. The reverse does not.

---

### W-25  Market regime engine                                          [L] [depends: W-11]

**Why this exists**
Roughly 60–70% of a stock's short-term move is explained by the market and its sector. The
best-looking breakout in the world fails when the index is breaking down — and, critically, *all of
them fail together*, which is how a diversified-looking portfolio produces a correlated loss.

**Build**
- `services/market_regime.py::compute_regime(trade_date) -> RegimeResult` per the API contract.
- Inputs: SPY / QQQ / IWM trend and MA position; VIX level and 20-day change; breadth (% of universe
  above its 50-day MA); sector ETF relative strength (XLK, XLF, XLV, XLE, XLI, XLY, XLP, XLU, XLRE,
  XLB, XLC).
- Weighted composite → `RISK_ON` / `NEUTRAL` / `RISK_OFF` with a confidence in [0,1].
- `sector_leadership.posture`: `OFFENSIVE` when cyclicals/tech lead, `DEFENSIVE` when
  staples/utilities lead. *(Defensive leadership inside a rising index is one of the more reliable
  early warnings of a regime change.)*
- `position_size_multiplier` derived from the label: 1.0 / 0.6 / 0.0–0.3.
- Templated `rationale` text — deterministic, not LLM-generated.
- Persist to `market_regimes`, one row per trading day.
- `GET /api/regime/current`, `GET /api/regime/history`.

**Acceptance**
- Hand-labelled historical dates classify correctly: Oct 2008 and Mar 2020 → `RISK_OFF`;
  mid-2017 and mid-2021 → `RISK_ON`.
- `components` shows each input's contribution; the rationale names the actual drivers.
- Recomputation for a date is idempotent.
- **Hysteresis:** the label does not flip on a single day's move — require 2 consecutive days of
  a contrary signal, or a confidence swing above a threshold. Without this the regime oscillates on
  noise and your sizing thrashes.

---

### W-26  Regime-adjusted scoring & candidate caps                      [S] [depends: W-25, W-21]

**Why this exists**
Regime must change *behaviour*, not just annotate a report. The candidate cap is the behavioural
control: a list of twenty ideas in a risk-off market invites you to trade twenty of them.

**Build**
- `regime_fit_score` component wired into the scorer.
- Long score multiplier applied by regime (1.00 / 0.85 / 0.60).
- `max_candidates` capped by regime (20 / 10 / 3).
- When the cap yields fewer candidates than usual, the scan result carries an explicit
  `regime_constrained: true` flag so the report can explain the short list rather than looking broken.

**Acceptance**
- A `RISK_OFF` scan on a fixture returns at most 3 candidates with reduced scores.
- The multiplier is recorded in `score_breakdown` so the adjustment is visible after the fact.
- A scan that returns zero candidates in `RISK_OFF` is a **valid, reportable outcome**, not an error.

---

### W-27  Stop placement engine                                         [M] [depends: W-11]

**Why this exists**
The stop determines the position size, the R-multiple, and whether you lose 1% or 4% when wrong. A
flat percentage stop sits at a price the market has no reason to respect and is simultaneously too
tight for volatile names and too loose for quiet ones.

**Build**
- `services/trade_plan.py::compute_stop(snapshot, bars, entry, direction) -> StopResult`
  implementing [07-risk-and-position-sizing.md](../07-risk-and-position-sizing.md) §2 exactly:
  structural candidates → nearest level ≥ 0.8 ATR away → 0.25 ATR buffer → validate within
  [1.0, 3.5] ATR → absolute 12% cap.
- Returns price, the method used, distance in % and ATR, and a `rationale` naming the structure.
- `NO_VALID_STOP` when no defensible level exists within range.

**Acceptance**
- Table-driven tests across low/normal/high volatility symbols produce stops in the specified ATR band.
- A stop is never placed above entry for a long (or below for a short).
- A symbol whose nearest structure is 20% away returns `NO_VALID_STOP` — it does **not** fall back to
  an arbitrary percentage. Accepting an indefensible stop to keep an idea alive is the exact failure
  this story prevents.
- The rationale names the actual structural level used.

---

### W-28  Target selection & reward:risk                                [M] [depends: W-27]

**Why this exists**
R:R is 15% of the composite score, so an optimistic target inflates the score and promotes the
candidate — the system would be rewarding itself for wishful thinking. Conservative targets keep the
score honest.

**Build**
- `compute_targets(snapshot, bars, entry, stop, setup) -> list[Target]`:
  structural resistance, measured move (breakouts), and `entry + 3×ATR`.
- Primary target = the **most conservative** of structural and measured-move that still clears the
  2.0 R:R floor.
- Secondary target for scale-out where one exists.
- `reward_risk = (target − entry) / (entry − stop)`.
- `RR_BELOW_FLOOR` veto when no target qualifies.

**Acceptance**
- Targets are never below entry for a long.
- A candidate whose only qualifying target requires an implausible 40% move is vetoed rather than
  promoted on an inflated R:R.
- R:R arithmetic verified against hand-computed fixtures.

---

### W-29  Position sizing & portfolio guardrails                        [M] [depends: W-28]

**Why this exists**
Fixed fractional sizing is what makes every trade risk the same amount regardless of how you feel
about it. Portfolio guardrails are what stop eight individually-reasonable positions from being one
oversized correlated bet.

**Build**
- `services/risk.py`:
  - `size_position(equity, risk_pct, entry, stop, regime_multiplier) -> SizingResult`
  - Position-value cap at 25% of equity, with a warning flag when it binds.
  - `check_guardrails(proposed, open_positions) -> GuardrailResult` for heat (≤6%), max positions
    (8), sector concentration (≤30%), single-position value (≤25%), correlation (warn above 0.75 on
    60-day returns), daily new entries (≤3).
- Heat uses **current** risk (current price to current stop), not initial — a position with a stop at
  breakeven contributes ~0 heat and frees budget.
- `RISK_LIMIT_BREACHED` error naming the specific guardrail and its current value.

**Acceptance**
- Worked example from the risk doc reproduces exactly: $100k / 1% / entry 183.10 / stop 175.80 → 136
  shares.
- A tighter stop yields a **larger** share count for the same dollar risk.
- `regime_multiplier = 0.6` scales shares down proportionally.
- Heat correctly drops when a stop is raised to breakeven.
- Correlation warning fires for two highly-correlated names in different sectors — sector labels
  alone miss this, which is exactly why the check exists.
- Fractional-share and zero-share edge cases handled (a risk budget too small for one share returns
  0 with an explanatory reason, not a crash).

---

### W-30  `POST /api/stocks/trade-plan` & scanner integration            [M] [depends: W-29]

**Why this exists**
Wires risk into the scanner so a candidate without a valid plan is never surfaced. This is where the
discipline becomes structural rather than aspirational.

**Build**
- Implement the endpoint per the API contract, replacing the W-13 stub.
- Scanner stage 6 applies `RR_BELOW_FLOOR`, `NO_VALID_STOP`, `HEAT_LIMIT`, `SECTOR_LIMIT`,
  `ALREADY_HELD`, `EXTENDED`; vetoed candidates are persisted with reasons rather than dropped.
- Trade plan fields written onto each candidate row.
- `get_trade_plan` tool added to the agent.

**Acceptance**
- Every non-vetoed candidate has a complete, valid plan.
- Veto reasons appear in the funnel's `dropped` counts and reconcile with the persisted rows.
- "Where should my stop be on NVDA?" returns the stop with its structural rationale.
- `valid: false` responses carry machine-readable `invalid_reasons`.
