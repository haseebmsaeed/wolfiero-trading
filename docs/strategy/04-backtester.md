# Spec 04 — Backtester

**Status:** Draft
**Phase:** 2
**Depends on:** Specs 01, 02, 03
**Downstream:** Spec 05 (Research Engine) is built on top of the backtester

---

## 1. Purpose

The Backtester simulates historical execution of the setups defined in Spec 03 against the data defined in Spec 02, subject to the constraints of Spec 01. Its output is the ground truth against which every strategy claim (win rate, expectancy, drawdown, Sharpe) is measured.

**A backtest that produces optimistic numbers because of unrealistic assumptions is worse than no backtest at all** — it justifies deploying a losing system. This spec's paranoia budget is therefore high.

---

## 2. Guiding Principles

### P1 — Realism Over Convenience
Every simplification (assumed fill at midpoint, no slippage, no gaps, no commissions) inflates results. We prefer conservative assumptions that under-state edge rather than convenient assumptions that over-state it.

### P2 — At-Time-of-Trade Everything
Every input on a historical date D must reflect the state that existed on date D:
- Halal classification as of D (Spec 02 §5.3)
- Universe membership as of D (Spec 02 §6.2)
- Corporate action adjustments known as of D
- Constitution version in effect on D (Spec 01 §7)

### P3 — Survivorship-Aware
Delisted stocks are part of the universe on the dates they existed. A backtest that ignores them is fantasy.

### P4 — Deterministic and Reproducible
Given the same code, config, and data snapshot, the backtester must produce identical results. Any randomness (e.g., in fill simulation) must use a seeded RNG.

### P5 — Fast Enough to Iterate
A single-setup backtest across 10 years of daily data on the halal universe should complete in under 15 minutes on a developer laptop. Slower means less experimentation, which means less validation.

---

## 3. Execution Model

### 3.1 Bar Frequency
Phase 1: **Daily bars only.** No intraday simulation.

### 3.2 Fill Model

**Entry fill (buy-stop order):**
- Order placed at close of D-1 as buy-stop at trigger price T
- On D, if `High(D) ≥ T`:
  - If `Open(D) ≥ T`: filled at `Open(D)` (gap fill, worse than trigger)
  - Else filled at `T + slippage`
- If `High(D) < T`: not filled; order re-evaluated tomorrow

**Exit fill (stop loss):**
- On D, if `Low(D) ≤ stop`:
  - If `Open(D) ≤ stop`: filled at `Open(D)` (gap fill, worse than stop)
  - Else filled at `stop − slippage`

**Exit fill (limit / partial profit target):**
- On D, if `High(D) ≥ target`:
  - Filled at `target − slippage`

**Time stop exit:**
- Filled at `Close(D)` on the trigger day

### 3.3 Slippage Model

Slippage applied on every fill:
```
slippage_dollars = MAX(
    0.01,                                           # 1 cent minimum
    0.0005 × price,                                 # 5 bps
    0.10 × spread_estimate(stock, date)             # 10% of estimated spread
)
```

Spread estimate: `min(0.005 × price, price / avg_daily_volume × liquidity_constant)`.

**Configurable parameters:**
- `slippage.min_dollars` = 0.01
- `slippage.pct_of_price` = 0.0005
- `slippage.spread_fraction` = 0.10

### 3.4 Commissions
- **Default:** $0 (most retail brokers are commission-free)
- **Configurable:** per-share and per-trade commission fields
- Model must support flipping commissions on to test sensitivity

### 3.5 Position Sizing at Backtest Time
Sizing uses the **account equity as of the entry date** — not the starting balance. This means winners compound and losers shrink the account per position, matching live behavior.

### 3.6 Cash Drag
Uninvested cash earns 0% by default (conservative). Configurable to reflect current risk-free rate for stress-testing.

---

## 4. Corporate Actions in Backtests

### 4.1 Splits Mid-Trade
If a stock splits while position is open:
- Share count multiplied by split ratio
- Stop price divided by split ratio
- All P&L calculations account for the split

### 4.2 Dividends Mid-Trade
- Dividend received in cash on ex-date
- Added to account equity, does not affect the position

### 4.3 Mergers / Delistings Mid-Trade
- Position closed at last available price on delisting date
- If closed above stop, treated as winner; below stop, treated as loser
- Logged separately as `EXIT_DELISTED` for review

### 4.4 Ticker Symbol Changes
- Positions preserved across symbol change
- Historical data queried under the correct symbol for the date

---

## 5. Regime and Context

### 5.1 Regime Tagging
Every simulated trade is tagged with the market regime (Spec 07) that existed on its entry date. This enables per-regime performance breakdowns in Spec 05.

### 5.2 Sector and Theme Context
Sector and theme leadership (Spec 07) at entry date is also tagged. Enables analysis of "did our setup work only in trending tech, or across sectors?"

### 5.3 Halal Continuity Check
If a position's halal status changes mid-trade, the halal-exit rule fires (Spec 03 §5.1). Backtester must simulate this.

---

## 6. Anti-Cheat Rules

### 6.1 No Look-Ahead
Every calculation on date D may only use data available at close of D. Common failure modes to guard against:
- Using "adjusted close" values that include future splits
- Filtering universe by "stocks that later existed" (survivorship)
- Using earnings dates that were announced after-the-fact
- Using halal classifications from a date after D

### 6.2 No Perfect Fills
Every fill must go through the slippage model. Never fill at the "ideal" trigger price.

### 6.3 No Impossible Orders
- Cannot go long more shares than the day's total volume × 5% (conservative liquidity ceiling)
- Cannot fill at a price outside `[Low(D), High(D)]`
- If order size would move the market (> 1% of ADV), warn and cap

### 6.4 No Free Restarts
A backtest cannot be run, tweaked based on results, and re-run on the same test set. That's implicit overfitting. See Spec 05 for walk-forward methodology that prevents this.

---

## 7. Output Format

Every backtest run produces:

### 7.1 Trade Log
CSV/JSON of every simulated trade:
```
trade_id, setup, ticker, entry_date, entry_price, stop_price, target_price,
shares, capital_used, exit_date, exit_price, exit_reason, r_multiple,
pnl_dollars, regime_at_entry, sector, theme, halal_check_passed,
slippage_dollars, commission_dollars
```

### 7.2 Equity Curve
Daily account equity time series.

### 7.3 Summary Statistics
- Total trades, wins, losses
- Win rate
- Average winner (R), average loser (R)
- Expectancy (R)
- Profit factor
- Max drawdown ($ and %)
- Sharpe ratio
- Sortino ratio
- Time in market %
- Turnover (trades per month)
- Per-regime breakdown
- Per-sector breakdown

### 7.4 Kill-Switch Simulation
Track when kill switches would have fired during the backtest. Report:
- Which switch, on what date, what caused it
- Simulated impact if the switch had paused new entries

### 7.5 Configuration Snapshot
The full config (Spec 01 constitution version, Spec 03 parameters, backtester settings) is stored with every backtest run. Backtests are never comparable across different configs unless explicitly noted.

---

## 8. Backtester Modes

### 8.1 Vanilla Backtest
Single pass over historical data with a fixed config.

### 8.2 Walk-Forward Backtest
- Train on window [T-N, T], test on window [T, T+M]
- Advance by M and repeat
- Report per-window results; final expectancy is the concatenation of out-of-sample windows only

### 8.3 Monte Carlo Simulation
- Given the trade log, randomly reorder trades to construct 10,000 equity curves
- Report distribution of max drawdown, terminal equity, longest losing streak
- Purpose: understand "how bad could it have been?" not "how good was the actual sequence?"

### 8.4 Sensitivity / Robustness Sweep
- Vary a single parameter ±20% while holding others fixed
- Report performance across the sweep
- Fragile parameters (large drop with small change) are flagged

---

## 9. Stories

### Story 4.1 — Bar-by-Bar Simulator
**As:** engineering
**I want:** a deterministic simulator that walks the historical universe day-by-day
**So that:** the backtester matches the runtime's execution model precisely

**Acceptance criteria:**
- Given a start date, end date, universe, and setup, produces a trade log
- Uses only data that existed at the simulated date (no look-ahead)
- Same inputs produce byte-identical outputs across runs
- Progresses at ≥ 500 stock-days/second on developer hardware

### Story 4.2 — Fill Model
**As:** the simulator
**I want:** the fill model in §3.2 implemented and unit-tested
**So that:** simulated fills mirror plausible live fills

**Acceptance criteria:**
- Buy-stop, stop-loss, limit, and time-stop fills implemented per §3.2
- Gap fills correctly worsen the fill price (never improve)
- Slippage applied to every fill per §3.3
- Unit tests for each fill scenario with hand-verified expected prices

### Story 4.3 — Corporate Action Handler
**As:** the simulator
**I want:** splits, dividends, mergers, delistings correctly handled mid-trade
**So that:** backtest returns reflect what would actually have happened

**Acceptance criteria:**
- Golden fixtures: known historical splits (e.g., AAPL 4-for-1 in 2020) correctly adjust simulated positions
- Delisted stocks close at last price with `EXIT_DELISTED` reason
- Dividends flow to cash without affecting position

### Story 4.4 — Survivorship-Adjusted Universe
**As:** the simulator
**I want:** the historical universe query to return the stocks that were tradeable on the historical date, including those later delisted
**So that:** backtests are free of survivorship bias

**Acceptance criteria:**
- Query "universe on 2018-06-15" returns stocks that met all Spec 02 §6.1 criteria on that date
- Result includes stocks that were later delisted (e.g., companies acquired, bankruptcies)
- Regression test: universe count on a historical date matches a golden reference

### Story 4.5 — Halal at Historical Trade Time
**As:** the simulator
**I want:** every simulated trade to consult the halal classification that existed on the trade date
**So that:** backtests reflect the constitutional constraint we would have faced then

**Acceptance criteria:**
- Setup detection on date D excludes stocks that were "not halal" on D under the standard active on D
- If halal status changes mid-position, halal-exit rule fires (per Spec 03 §5.1)
- Test: a stock reclassified from halal → not halal in 2021 does not appear in setups after that date

### Story 4.6 — Walk-Forward Runner
**As:** research
**I want:** a walk-forward backtest that trains on one window and tests on the next
**So that:** the reported expectancy is honestly out-of-sample

**Acceptance criteria:**
- Configurable train window, test window, and step size
- Only out-of-sample test-window trades count toward reported expectancy
- Per-window results reported; final aggregate is the concatenation

### Story 4.7 — Monte Carlo Analyzer
**As:** research
**I want:** to run 10,000 reorderings of the trade log to estimate the drawdown distribution
**So that:** we know how bad the strategy could plausibly have looked with a different trade order

**Acceptance criteria:**
- Reads a trade log, produces 10,000 shuffled equity curves
- Reports 5th / 50th / 95th percentile of max drawdown and terminal equity
- Reports longest losing streak distribution

### Story 4.8 — Sensitivity Sweep
**As:** research
**I want:** to vary each parameter ±20% and report performance
**So that:** overfit parameters are identified

**Acceptance criteria:**
- Given a parameter and a range, runs N backtests
- Reports performance metrics across the sweep
- Flags parameters where a small change collapses performance

### Story 4.9 — Configuration Snapshot
**As:** the auditor
**I want:** every backtest run to persist the full config used
**So that:** old backtests can be reproduced exactly

**Acceptance criteria:**
- Config hash and full config stored with every backtest result
- Attempting to compare backtests with different configs surfaces a warning
- Re-running with the same config on the same data produces identical results

### Story 4.10 — Backtest Reporter
**As:** the researcher
**I want:** a standardized report showing trade log, equity curve, and all summary stats
**So that:** results are reviewable at a glance

**Acceptance criteria:**
- Report produced as a single HTML or Markdown document
- Includes equity curve chart, drawdown chart, R-distribution histogram, per-regime table, per-sector table
- Config snapshot embedded at the top

---

## 10. Acceptance Criteria for Spec 04

- All stories 4.1–4.10 pass their acceptance criteria
- Golden fixture backtest on a known setup and stock reproduces a hand-verified trade log
- Look-ahead test: deliberately inject future data into a stock's history; backtest should NOT use it (assertion fails if it does)
- Survivorship test: a backtest on the S&P 500 including delisted names produces meaningfully lower returns than one excluding them
- Strongest available reasoning model has reviewed and APPROVED

---

## 11. Open Questions for the Trader

1. **Slippage model:** the defaults are conservative. Should we calibrate against actual live fills once we have some?
2. **Commissions:** confirm $0 default is realistic for your broker.
3. **Cash yield:** confirm 0% cash drag or should we credit prevailing rates?
4. **Backtest depth:** 10 years vs 15 years — more data or more regime-relevance?
5. **Walk-forward windows:** typical setup is 2 years train / 6 months test — adjust?
