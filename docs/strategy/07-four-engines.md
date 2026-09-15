# Spec 07 — The Four Engines (Regime + Risk + Portfolio + Execution)

**Status:** Draft
**Phase:** 3
**Depends on:** Specs 01–06
**Downstream:** Spec 09 (Trade Card is the outward face of these engines), Spec 10 (Journal records their decisions)

---

## 1. Purpose

Four separate concerns, deliberately not blended into a single "trading engine":

| Engine | Question It Answers |
|--------|---------------------|
| **Regime** | What kind of market are we in right now? |
| **Risk** | For a given trade candidate, how much capital should we expose? |
| **Portfolio** | Given what we already hold, should we take this trade at all? |
| **Execution** | How do we actually fill this order without bleeding edge? |

**They are ordered:** Regime informs both Risk and Portfolio; Risk sizes the position; Portfolio decides yes/no; Execution places the order.

**Why separate?** Blending them is where retail systems fail. "The regime looks great so I'll take a big correlated position" is exactly the confusion this spec prevents.

---

## 2. Engine 1 — Regime

### 2.1 Purpose
Classify the current market environment into a small, discrete set of regimes. Every downstream decision consumes this classification.

### 2.2 Regime Taxonomy

| Regime | Symbol | Trading Posture |
|--------|--------|-----------------|
| Strong Bull | `STRONG_BULL` | Full sizing, aggressive setups OK |
| Normal Bull | `NORMAL_BULL` | Full sizing, standard setups |
| Chop | `CHOP` | Half sizing, A+ setups only |
| High Volatility | `HIGH_VOL` | Quarter sizing, very selective |
| Bear | `BEAR` | No new long entries; existing positions run to their exits |

### 2.3 Classification Inputs

| Signal | Source | Weight |
|--------|--------|--------|
| SPY vs 50-day MA and slope | Spec 02 | High |
| QQQ vs 50-day MA and slope | Spec 02 | High |
| VIX level and slope | Spec 02 | High |
| % of S&P 500 above 50-day MA (breadth) | Spec 02 | High |
| Advance/decline line | Spec 02 | Medium |
| New highs vs new lows | Spec 02 | Medium |
| 10-year yield 20-day change | Spec 02 | Low (context only) |

### 2.4 Classification Rules
Rules-based classifier (Phase 1), Model C from Spec 06 (Phase 2+) as an alternate view.

> ### ⚠ PROVISIONAL — Thresholds Below Are Heuristics, Not Truth
>
> All numeric thresholds in this section (VIX 20, VIX 25, breadth 60%, yield spike 10%, 4/6 signals) are **PROVISIONAL** per Spec 03 §3.0 legend. They match common trader convention but have **not been robustness-tested or walk-forward validated** as of Phase 1. Spec 05 must validate these thresholds before they are treated as authoritative. Do not fine-tune them by grid search on the trading dataset (that produces overfit). Adjustments must be justified either by out-of-sample evidence or by structural argument, not by "looks better on the backtest."

**Rules-based (Phase 1):**
```
green_signals = count of the following that are TRUE:
  1. SPY above rising 50-day MA
  2. QQQ above rising 50-day MA
  3. VIX < 20                              [PROVISIONAL threshold]
  4. % S&P above 50-day > 60               [PROVISIONAL threshold]
  5. New highs > new lows
  6. 10-year yield not spiking (< 10% up in 20 days)   [PROVISIONAL threshold]

if green_signals == 6:                    regime = STRONG_BULL
elif green_signals >= 4:                  regime = NORMAL_BULL     [PROVISIONAL boundary]
elif green_signals >= 2 and VIX < 25:     regime = CHOP            [PROVISIONAL threshold]
elif VIX >= 25:                           regime = HIGH_VOL        [PROVISIONAL threshold]
else:                                     regime = BEAR
```

**Independence check required (Spec 05 story):** the six signals are not independent — SPY-above-50MA and QQQ-above-50MA are highly correlated; % above 50-day and new-highs vs new-lows both measure breadth. Ablation testing (Spec 05 §4A) must determine whether all six add value or whether 3–4 independent signals produce equivalent regime classification.

### 2.5 Regime Change Handling
- Regime is computed daily at market close for next-day use
- Regime changes are logged with timestamp and reason (which signals flipped)
- Regime downgrade (e.g., NORMAL_BULL → CHOP) triggers:
  - No new full-size trades tomorrow
  - Trailing stops on open positions tighten per Spec 03 §5.1
- Regime upgrade does not automatically expand new-trade sizing; requires 3 consecutive days at the new level

### 2.6 Regime Configurability
Every threshold (VIX < 20, breadth > 60, etc.) is configurable and subject to robustness testing per Spec 05.

---

## 3. Engine 2 — Risk

### 3.1 Purpose
Given a valid setup candidate that has passed regime gating, determine:
- How much dollar risk to allocate
- How many shares
- What the stop distance must be

### 3.2 Inputs
- Account equity (live)
- Constitutional per-trade risk cap (Spec 01 §4.1)
- Sample-size bucket for this setup / regime / sector (Spec 05 §3.2)
- Regime (Spec 07 §2)
- Setup candidate with entry, structural stop, ATR (Spec 03)
- Human state (Spec 01 §5.3)

### 3.3 Risk Calculation

```
base_risk_pct = min(
  constitutional_max,                         # Spec 01
  sample_size_bucket_max,                     # Spec 05
  regime_max                                  # from §3.4 below
)

risk_dollars = account_equity × base_risk_pct
stop_distance = entry_price − stop_price
shares = floor(risk_dollars / stop_distance)
capital = shares × entry_price

# Concentration guardrail
if capital > 0.10 × account_equity:
    shares = floor(0.10 × account_equity / entry_price)
    actual_risk = shares × stop_distance
    # actual_risk may be less than target; that is acceptable
```

### 3.4 Regime-Based Risk Caps

| Regime | Max risk % per trade |
|--------|-----------------------|
| STRONG_BULL | 1.00% |
| NORMAL_BULL | 1.00% |
| CHOP | 0.50% |
| HIGH_VOL | 0.25% |
| BEAR | 0.00% (no new entries) |

Multiplied against the sample-size bucket cap (whichever is lower wins).

### 3.5 Stop Viability
- Structural stop must be ≤ 2.0 × ATR (Spec 03 §4.3)
- If not, trade is VETOed by risk engine

### 3.6 Minimum Position Size
If the calculated `shares < 1`, or `capital < $500`, the trade is skipped (transaction costs make sub-$500 positions uneconomic).

### 3.7 Output
`RiskPlan { shares, capital_used, actual_risk_dollars, actual_risk_pct, stop_price, sizing_bucket, veto_reasons[] }`

---

## 4. Engine 3 — Portfolio

### 4.1 Purpose
Given a risk-sized trade candidate, decide whether to take it in the context of the existing portfolio.

### 4.2 Inputs
- Current open positions (tickers, sectors, themes, correlations, open risk)
- Proposed trade candidate with risk plan
- Correlation matrix (rolling 60-day) for current positions and candidate
- Portfolio constitutional limits (Spec 01 §4.3)

### 4.3 Portfolio Gates

**Gate 1 — Total Open Risk**
```
if (open_risk_sum + candidate.actual_risk) > 3.0% × account_equity:
    VETO — "portfolio risk ceiling"
```

**Gate 2 — Position Count**
```
if open_position_count >= 6:
    VETO — "max positions"
```

**Gate 3 — Sector Concentration**
```
if open_positions_in_same_sector >= 2:
    VETO — "sector concentration"
```

**Gate 4 — Theme Concentration**
```
if any open position is in the same active theme:
    VETO — "theme concentration"
```

**Gate 5 — Correlation**
```
for each open position P:
    if correlation(candidate, P, 60-day) > 0.75:
        VETO — "correlated with {P.ticker}"
```

**Gate 6 — Cash Requirement**
```
if (deployed_cash + candidate.capital_used) > (account_equity − reserve):
    VETO — "insufficient cash after reserve"
```

### 4.4 Output
`PortfolioDecision { PASS | VETO, veto_reasons[], portfolio_context {open_risk_after, position_count_after, sector_exposure_after} }`

### 4.5 Portfolio Rebalancing
Not implemented. Positions are entered and managed individually per Spec 03. No dynamic rebalancing algorithm.

---

## 5. Engine 4 — Execution

### 5.1 Purpose
Actually place the approved order and manage its lifecycle. **Execution is a source of edge or bleed** — sloppy execution can turn a positive-expectancy setup into a losing one.

### 5.2 Order Placement Model

**Entry:**
- Buy-stop order placed at trigger price (Spec 03 §4.2) + $0.05
- Good-for-day only (never GTC)
- Placed at market open on the trigger day if pre-market conditions still valid
- **Human approval required before placement** (per Spec 01 §5.1)

**Stop:**
- Placed simultaneously with entry as a stop-market order
- Adjusted only per Spec 03 §5.1 (structural moves, trailing)
- **Never removed while position open**

**Partial Profit Target:**
- Placed as a limit order at the +2R target
- Removed if the runner trail moves past the target price

**Trail Update:**
- Daily post-close: compute new trail level per Spec 03 §5.1; adjust stop order if new level is higher
- Never moves stop lower

**Time Stop:**
- Time-stop trigger evaluated at 15:45 US Eastern on the deadline day
- If active, cancel other orders and submit market order to close

### 5.3 Broker Abstraction
- All order operations go through a `BrokerAdapter` interface
- Concrete implementations: `PaperBroker` (Phase 4), `LiveBroker` (Phase 5+)
- Never call broker APIs directly from strategy or portfolio code

### 5.4 Fill Handling
- Every fill received produces a `FillEvent` recorded to Spec 10 (Journal)
- Partial fills tracked to completion; if unfilled at day end, unfilled portion is cancelled
- Slippage recorded: `slippage = actual_fill_price − expected_price`

### 5.5 Retry and Error Handling
- Order placement failures retried up to 3 times with exponential backoff
- Persistent failure alerts the trader and pauses new-trade generation until resolved
- Never silently drop an order

### 5.6 Order Timing
- Prefer market open (9:35–9:40 ET) for buy-stops, once opening range volatility settles
- Never place new orders in the last 15 minutes of session (except mandatory exits)
- No new orders on options-expiration Fridays after 15:00 ET (gamma pinning risk)

### 5.7 Slippage Tracking
- Per-trade slippage logged to Journal (Spec 10)
- Rolling 20-trade slippage compared to Backtester's modeled slippage (Spec 04 §3.3)
- Divergence > 50% for 20+ trades fires the slippage kill switch (Spec 01 §5.5)

### 5.8 Cash-Account Settlement (T+1) Constraints

The Constitution (Spec 01 §2.1) mandates a **cash brokerage account** — no margin. This creates a real-world execution constraint absent from margin accounts.

**T+1 settlement rule:** proceeds from a stock sale are not "settled cash" until 1 business day after the sale (T+1 as of May 2024 SEC change from T+2). Until settlement, those proceeds are **unsettled**.

**What this means operationally:**
- Buying stock with **settled cash** → always fine
- Buying stock with **unsettled cash** (funds from a recent sale) → allowed, but if you then sell the newly-bought stock before the original proceeds settle, you commit a **Good Faith Violation (GFV)**
- **3 GFVs in a 12-month rolling window** → the broker restricts the account to settled-cash-only trading for 90 days
- 90-day restriction = massive operational disruption

**Runtime enforcement rules:**

```
before opening a new position:
    settled_cash = current_settled_balance()
    unsettled_cash = current_unsettled_balance()

    if capital_needed <= settled_cash:
        PROCEED — normal buy with settled funds
    elif capital_needed <= (settled_cash + unsettled_cash):
        FLAG — buying with unsettled cash; position must be held until original sale settles
        (mark position with `held_until_settled: {date}`; block exit before that date except stop-loss)
    else:
        VETO — insufficient buying power (settled + unsettled)
```

**On the exit side:**

```
before closing a position:
    if position.held_until_settled_date is not null:
        if today < held_until_settled_date and exit_reason != HARD_STOP:
            defer non-stop exits (partial, trail, time-stop) until settlement date
            HARD stops still execute (safety > GFV avoidance)
```

**Note:** hard stop-loss ALWAYS executes even at risk of a GFV. Capital preservation beats compliance overhead. Track GFVs; if approaching 3 in the rolling window, alert the trader and pause new-entry generation.

**Configurable parameters:**
- `execution.settlement_days` = 1 (T+1 as of May 2024 SEC standard) [CITED]
- `execution.gfv_alert_threshold` = 2 (alert on second GFV; halt on third)
- `execution.honor_stops_over_gfv` = TRUE (stops always execute) [STRUCTURAL]

---

## 6. Engine Interaction Diagram

```
                     Setup Candidate (from Spec 03)
                                │
                                ▼
                    ┌───────────────────────┐
                    │   REGIME ENGINE       │  determines regime
                    │   (produces regime)   │
                    └───────────┬───────────┘
                                │
                     regime + candidate
                                │
                                ▼
                    ┌───────────────────────┐
                    │    RISK ENGINE        │  sizes the trade
                    │  (produces RiskPlan)  │
                    └───────────┬───────────┘
                                │
                        VETO ── or ── PASS + RiskPlan
                                │
                                ▼
                    ┌───────────────────────┐
                    │  PORTFOLIO ENGINE     │  gates against book
                    │ (produces Decision)   │
                    └───────────┬───────────┘
                                │
                        VETO ── or ── PASS
                                │
                                ▼
                        Trade Card generated (Spec 09)
                                │
                        HUMAN APPROVAL (or reject)
                                │
                                ▼
                    ┌───────────────────────┐
                    │  EXECUTION ENGINE     │  places & manages orders
                    └───────────────────────┘
                                │
                                ▼
                    Fills flow to JOURNAL (Spec 10)
```

---

## 7. Stories

### Story 7.1 — Regime Classifier (Rules-Based)
**As:** the runtime
**I want:** the rules-based regime classifier from §2.4
**So that:** every downstream decision has a regime tag

**Acceptance criteria:**
- Consumes SPY, QQQ, VIX, breadth, A/D, new-high/new-low, 10y yield inputs
- Produces one of 5 regime symbols
- Logged with timestamp and signal snapshot
- Golden fixture: known 2022 bear market date returns BEAR

### Story 7.2 — Regime Change Handler
**As:** the runtime
**I want:** regime downgrades and upgrades handled per §2.5
**So that:** open positions and new trades respond correctly

**Acceptance criteria:**
- Downgrade tightens trails; blocks full-size new entries
- Upgrade requires 3 consecutive days before enabling
- Regime change logged with reason (which signals flipped)

### Story 7.3 — Risk Engine
**As:** the pipeline
**I want:** a `size_trade(candidate, regime, sample_bucket) → RiskPlan | VETO`
**So that:** sizing is deterministic and constitutional

**Acceptance criteria:**
- Applies formula in §3.3
- Enforces regime cap, sample-size cap, concentration cap
- Applies stop viability check
- Rejects trades with capital < $500 or shares < 1
- Unit tests with hand-verified sizing

### Story 7.4 — Portfolio Engine
**As:** the pipeline
**I want:** portfolio gating per §4.3
**So that:** correlated / concentrated / over-risk positions are prevented

**Acceptance criteria:**
- All 6 gates implemented and testable independently
- Correlation gate uses rolling 60-day correlations
- Returns detailed veto reasons on failure
- Integration test: candidate that would breach each gate is correctly VETOed

### Story 7.5 — Broker Adapter Interface
**As:** engineering
**I want:** a Protocol-typed `BrokerAdapter` with paper and live implementations
**So that:** the runtime can be substituted between paper and live trading via config

**Acceptance criteria:**
- Interface covers: place, cancel, modify, query positions, query orders, fill events
- `PaperBroker` simulates fills using Spec 04's fill model
- `LiveBroker` wraps the actual broker API (Alpaca, IBKR, etc.)
- Configuration switches between them without code change

### Story 7.6 — Order Lifecycle Manager
**As:** the execution engine
**I want:** entry, stop, target, trail, and time-stop orders coordinated through their lifecycle
**So that:** open positions have consistent, deterministic behavior

**Acceptance criteria:**
- Entry order placed only after human approval
- Stop order placed at fill confirmation, never before
- Target order placed at partial-profit level
- Trail evaluated daily post-close
- Time stop enforced at 15:45 ET on deadline day
- All order events flow to Journal

### Story 7.7 — Slippage Tracker
**As:** the execution engine
**I want:** per-fill slippage recorded and compared to Backtester's modeled slippage
**So that:** execution honesty is monitored

**Acceptance criteria:**
- Every fill records `slippage_dollars`
- Rolling 20-trade avg compared to Backtester model
- > 50% divergence for 20+ trades fires slippage kill switch (Spec 01 §5.5)

### Story 7.8 — Human Approval Interstitial
**As:** the trader
**I want:** every new-entry order to require my explicit approval
**So that:** the system is never fully autonomous for opening positions

**Acceptance criteria:**
- Trade card presented via Telegram (Spec 09) with approve/reject buttons
- Approval action produces a Broker.place() call
- Rejection or timeout (default: 60 minutes after trigger) cancels
- Approval logged with timestamp and trader ID

### Story 7.9 — Human-State Enforcement
**As:** the regime/risk pipeline
**I want:** the human-state check (Spec 01 §5.3) enforced before generating new-entry trade cards
**So that:** the trader is not asked to approve trades on a bad day

**Acceptance criteria:**
- Runtime checks human-state flag before scheduling trade card generation
- If CASH_DAY, only mechanical exit management continues; no new cards produced
- CASH_DAY status auto-clears at midnight local time or on manual clear

### Story 7.10 — Engine Interaction Test
**As:** engineering
**I want:** an integration test that walks a candidate through all four engines
**So that:** the pipeline is verified end-to-end

**Acceptance criteria:**
- Fixture: known candidate in known regime with known portfolio state
- Result: expected RiskPlan, expected PortfolioDecision, expected ExecutionActions
- Assertions cover VETO paths as well as PASS paths

### Story 7.11 — T+1 Cash Settlement Enforcement
**As:** the execution engine
**I want:** buying power gated by settled vs unsettled cash per §5.8
**So that:** the trader does not accidentally trigger Good Faith Violations

**Acceptance criteria:**
- Buying power query returns both `settled` and `unsettled` cash from broker
- Entry blocked when `capital_needed > settled + unsettled`
- Entry with unsettled cash flags position with `held_until_settled_date`
- Non-stop exits (partial, trail, time-stop) defer until settlement date; hard stops always execute
- GFV counter tracked; alert on GFV #2 in rolling 12-month window; halt on #3
- Integration test: simulate sell → buy → sell-before-settle → assertion that GFV is flagged

---

## 8. Acceptance Criteria for Spec 07

- All stories 7.1–7.10 pass their acceptance criteria
- End-to-end test: bear market date + strong candidate = VETO at regime engine
- End-to-end test: bull market + strong candidate + already 2 open tech positions = VETO at portfolio engine (sector concentration)
- Slippage kill switch fires deterministically when injected slippage exceeds threshold
- Strongest available reasoning model has reviewed and APPROVED

---

## 9. Open Questions for the Trader

1. **Regime taxonomy:** 5 regimes — comfortable, or too many / too few?
2. **Regime upgrade delay:** 3 days required before scaling up — adjust?
3. **Correlation threshold:** > 0.75 vetoes — adjust?
4. **Broker:** which broker for Live phase? (Alpaca / IBKR / TD / Schwab)
5. **Order timing:** OK to wait 5–10 minutes after open for buy-stop placement? Or place at open?
