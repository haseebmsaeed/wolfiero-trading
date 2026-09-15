# Spec 05 — Research Engine

**Status:** Draft
**Phase:** 2
**Depends on:** Specs 01, 02, 03, 04
**Downstream:** Spec 06 (ML layer), Spec 07 (Runtime — uses expectancy tables), Spec 09 (Trade cards embed stats)

---

## 1. Purpose

The Research Engine is the analytical layer that sits on top of the Backtester and produces the **statistical evidence** used to:

1. Decide whether a proposed setup has genuine positive expectancy.
2. Compute **expectancy tables** conditional on market regime, sector, and other context.
3. Enforce **sample-size gating** on position sizing (Spec 01 §4.2).
4. Detect **strategy decay** and trigger kill switches (Spec 01 §5.5).
5. Perform **robustness testing** on every parameter to detect overfit.
6. Provide **walk-forward validation** so no reported edge is contaminated by in-sample fitting.

The Research Engine does not trade. It informs.

---

## 2. Guiding Principles

### P1 — Out-of-Sample Or It Doesn't Count
Any expectancy number used to authorize a trade must come from data the parameters were not fitted on. In-sample stats are for exploration only.

### P2 — Confidence Intervals, Not Point Estimates
"Expectancy = +0.42R" is meaningless without knowing the confidence interval and sample size. Every stat reported must include both.

### P3 — Regime-Conditional Everything
A setup's edge in a Strong Bull is usually different from its edge in Chop. The research engine reports per-regime performance and lets the runtime consume the regime-matched stat.

### P4 — Rolling, Not Static
Markets shift. Expectancy is recomputed on a rolling window (default: last 24 months of trades) so the runtime uses recent evidence, not lifetime averages that mask decay.

### P5 — Fail Loud on Insufficient Data
When sample size is too small for confidence, the engine says INSUFFICIENT_DATA — it does not extrapolate.

### P6 — No Parameter Snooping
Parameter choices are recorded with their justification and dataset scope. Attempting to select parameters by scanning outcomes on the trading dataset is blocked at the tool level.

---

## 3. Core Outputs

### 3.1 Expectancy Table

For each active setup, the primary output is an **expectancy table** keyed by:

| Dimension | Values |
|-----------|--------|
| Regime | STRONG_BULL, NORMAL_BULL, CHOP, HIGH_VOL, BEAR |
| Sector | 11 GICS sectors |
| RS bucket | Top decile / top quartile / middle / bottom quartile |
| Sample window | Rolling 12 months, 24 months, 60 months, all-time |

Each cell contains:

```
n:                   number of trades in this cell
win_rate:            wins / n
avg_winner_R:        mean R of winning trades
avg_loser_R:         mean R of losing trades
expectancy_R:        (win_rate × avg_winner_R) − ((1 − win_rate) × |avg_loser_R|)
expectancy_CI_95:    95% bootstrap confidence interval
median_hold_days:    median holding period
max_drawdown:        worst drawdown observed in this cell
sharpe:              annualized Sharpe for this cell's trades
```

### 3.2 Sample-Size Bucket

Every proposed live trade is mapped to a sample-size bucket for risk-gating (Spec 01 §4.2):

```
bucket_A:  n < 30            → skip or risk 0.25%
bucket_B:  30  ≤ n < 100     → risk 0.50%
bucket_C:  100 ≤ n < 300     → risk 0.75%
bucket_D:  n ≥ 300           → risk 1.00%
```

Bucket lookup uses the regime-matched cell for the current setup.

### 3.3 Decay Signal

For each active setup, a **decay signal** is computed weekly:
```
rolling_12w_expectancy  = expectancy on last 12 weeks of trades
rolling_52w_expectancy  = expectancy on last 52 weeks of trades
decay_flag              = TRUE if rolling_12w_expectancy < 0 OR
                                 rolling_12w_expectancy < 0.5 × rolling_52w_expectancy
```

Decay flag persisting 3+ weeks fires the kill switch (Spec 01 §5.5).

### 3.4 Robustness Report

For each configurable parameter (Spec 03 §6 provenance table), a robustness report is produced quarterly:
- Vary parameter ±20% in 5 steps
- Compute expectancy at each step
- Report the sensitivity slope
- Flag parameters where a 20% change moves expectancy by > 30% of its baseline (fragile)

### 3.5 Walk-Forward Report

Every quarter, the setup is re-validated via walk-forward:
- Train windows: rolling 24-month windows
- Test windows: subsequent 6-month windows
- Stitch out-of-sample test results
- Report walk-forward expectancy vs backtest expectancy (delta > 0.15R = concern)

---

## 4. Methodology

### 4.1 Bootstrap Confidence Intervals
Rather than assume normal distribution of R, use bootstrap resampling (10,000 draws) to compute 95% CI on expectancy, win rate, and profit factor.

### 4.2 Regime Tagging
Uses Spec 07's Regime Engine, applied historically. Every trade in the backtest's trade log has a regime tag; expectancy tables group by that tag.

### 4.3 Rolling Windows
- **Rolling 12 weeks** for decay detection
- **Rolling 12 months** for short-term expectancy
- **Rolling 24 months** for gating decisions
- **Rolling 60 months** for long-term reference
- **All-time** for exploratory analysis (not used for gating)

### 4.4 Minimum Sample Enforcement
- If a rolling window has < 20 trades, report `INSUFFICIENT_DATA` for that cell
- The runtime consuming an INSUFFICIENT_DATA cell must either skip the trade or size at the smallest bucket

### 4.5 Multiple Comparisons Awareness
When testing many setups × regimes × sectors × RS buckets, chance produces some false positives. Apply Bonferroni correction (or false discovery rate) when claiming statistical significance.

### 4.6 Exit Policy Comparison (from Spec 03 §5.2)
For the primary setup, run each exit policy (E-01 through E-08) against the same trade entry set. Report per-policy expectancy, drawdown, Sharpe. Pick the winner per regime.

### 4A Ablation Testing (Does Each Filter Actually Add Value?)

Robustness testing (§3.4) asks *"does the strategy survive parameter variation?"* Ablation testing asks a different question: *"does each filter add value at all, or does it merely reduce trade count?"*

**A filter that removes trades is NOT automatically beneficial.** If removing filter X drops trades from 200 to 50 and average expectancy drops from +0.30R to +0.05R — filter X was actively destroying edge, and removing it exposes that. If removing filter X drops trades from 200 to 50 and expectancy STAYS at +0.30R (or rises) — filter X was just over-filtering.

#### 4A.1 Ablation Protocol

For each setup, run the following variants against the same historical universe and time window:

**Base variant (minimum viable setup):**
- Halal + Universe (always required — Rule Zero)
- Setup's core geometric condition (Stage 2 + pullback for PBK; 20-day breakout for DC20)
- Volatility-viable stop (Spec 03 §4.3 / §4A.3)
- No other filters

**Then compare against each filter added independently:**
- BASE
- BASE + market regime filter
- BASE + top-3 sector filter
- BASE + relative strength filter (PBK only)
- BASE + volume confirmation (PBK ≥ 1.25×; DC20 ≥ 1.5×)
- BASE + volume dry-up (PBK only)
- BASE + earnings blackout
- BASE + not-overextended check (PBK; distance to 20 EMA ≤ 1.5 ATR)
- BASE + ATR volatility sanity (DC20; 0.5–2.0× 60d median)

**And the fully-loaded variant:**
- FULL = BASE + all filters (current Spec 03 definition)

Report per variant:
- Number of trades
- Win rate
- Expectancy (R)
- Max drawdown
- Sharpe
- Profit factor
- Time in market

#### 4A.2 Decision Rule for Retaining a Filter

A filter earns its place only if it:

1. **Improves expected R by ≥ 0.05 vs BASE** on out-of-sample data, OR
2. **Reduces max drawdown by ≥ 20% while holding expectancy flat** (defensive value), OR
3. Has a **defensible structural argument** for inclusion regardless of statistics (e.g., halal filter — non-optional; earnings blackout — risk-management even if it costs a few R)

Filters that fail all three criteria are **removed** in the next spec revision. The strategy gets simpler, not more elaborate.

#### 4A.3 Cadence

- **Baseline ablation run:** required before any live deployment (part of Phase 2 acceptance criteria)
- **Rerun cadence:** annual, or after any significant regime shift
- **Documented in:** per-setup ablation report, checked into `docs/strategy/reports/`

---

## 5. Anti-Overfitting Enforcement

### 5.1 Parameter Grid Search Ban on Trading Data
Any tool that scans parameter grids must accept a dataset-partition argument. The trading dataset (most recent partition) is off-limits to grid search.

### 5.2 Change Auditing
Every parameter change is logged with:
- Old value, new value
- Dataset used to justify the change
- Effect on backtest metrics
- Reviewer sign-off

### 5.3 Robustness-Gated Rollout
A parameter change proposed based on out-of-sample research still cannot go live until the robustness report shows the new value is not fragile.

### 5.4 Deflated Sharpe Ratio
When comparing multiple candidate strategies or parameter sets, report the **deflated Sharpe ratio** (Bailey & López de Prado 2014) to correct for the multiplicity of trials. A raw Sharpe of 1.5 from 20 trials is often 0.8 after deflation.

---

## 6. Regime Model (for Spec 07 handshake)

While the Regime Engine is speced in Spec 07, the Research Engine consumes it. The regime taxonomy used across both specs:

| Regime | Rough Definition | Trading Posture |
|--------|-----------------|-----------------|
| STRONG_BULL | SPY > rising 50 and 200 MA; VIX < 15; breadth > 65% | Full risk sizing |
| NORMAL_BULL | SPY > rising 50 MA; VIX 15–20; breadth 50–65% | Full risk sizing |
| CHOP | SPY flat / choppy; VIX 20–25; breadth 40–50% | Half sizing, A+ setups only |
| HIGH_VOL | VIX > 25; large daily ranges | Very selective, quarter sizing |
| BEAR | SPY < falling 50 MA; breadth < 40% | No new long entries |

Precise thresholds live in Spec 07 (and are testable — see §4.5 above).

---

## 7. Stories

### Story 5.1 — Expectancy Table Builder
**As:** the research engine
**I want:** to produce a full expectancy table from a backtest trade log
**So that:** the runtime can consume regime-conditional stats

**Acceptance criteria:**
- Input: trade log with regime, sector, RS tags per trade
- Output: expectancy table with all Section 3.1 cells populated
- CI computed via 10,000-draw bootstrap
- Cells with n < 20 marked INSUFFICIENT_DATA
- Persisted with backtest config snapshot

### Story 5.2 — Sample-Size Bucket Lookup
**As:** the runtime risk engine
**I want:** a `lookup_bucket(setup, regime, sector, rs_bucket)` function
**So that:** position sizing is automatically gated by evidence weight

**Acceptance criteria:**
- Returns bucket A/B/C/D per §3.2
- Returns "SKIP" if regime cell is INSUFFICIENT_DATA
- Uses the most recent rolling 24-month expectancy table
- Test: known cell with n=45 returns bucket B

### Story 5.3 — Decay Detector
**As:** the kill-switch system
**I want:** weekly computation of the decay signal per §3.3
**So that:** setups that stop working are automatically paused

**Acceptance criteria:**
- Scheduled weekly job
- Computes 12-week and 52-week rolling expectancy
- Sets decay_flag per rule
- 3 consecutive weekly flags triggers the kill switch
- Alert sent to the trader

### Story 5.4 — Robustness Sweep
**As:** the research engine
**I want:** quarterly robustness sweeps across every parameter in Spec 03
**So that:** fragile parameters are surfaced before they cause a live surprise

**Acceptance criteria:**
- Vary each parameter ±20% in 5 steps
- Fragility flag when expectancy moves > 30% of baseline
- Report published quarterly with visualization
- Blocking: fragile parameters cannot enter production without an explicit override

### Story 5.5 — Walk-Forward Validator
**As:** the research engine
**I want:** rolling walk-forward validation with 24m train / 6m test windows
**So that:** reported expectancy is honestly out-of-sample

**Acceptance criteria:**
- Runs per quarter
- Stitches out-of-sample test windows
- Flags when walk-forward expectancy diverges from backtest expectancy by > 0.15R
- Divergence alert triggers investigation before continued live trading

### Story 5.6 — Exit Policy Comparator
**As:** the research engine
**I want:** to compare exit policies E-01 through E-08 (Spec 03 §5.2) on the same trade entries
**So that:** the default exit policy is chosen with evidence

**Acceptance criteria:**
- Runs per exit policy against the same entry stream
- Reports per-policy expectancy, drawdown, Sharpe, holding-period distribution
- Reports per-regime winner
- Output persists so the trade card can cite it

### Story 5.7 — Deflated Sharpe Reporter
**As:** the researcher
**I want:** deflated Sharpe reported when multiple strategy candidates are evaluated
**So that:** the multiplicity of trials does not fool us into deploying noise

**Acceptance criteria:**
- Given N candidate strategies, computes deflated Sharpe per Bailey/López de Prado
- Flagged in the research report
- Applied automatically when the exit policy comparator (5.6) evaluates multiple policies

### Story 5.8 — Parameter Change Auditor
**As:** the reviewer
**I want:** every parameter change logged with justification and evaluation dataset
**So that:** no parameter drift happens silently

**Acceptance criteria:**
- Append-only change log
- Records: parameter name, old value, new value, justification, dataset partition used, reviewer
- Report retrievable at any time

### Story 5.9 — Insufficient Data Enforcement
**As:** the runtime
**I want:** trades to be skipped or minimally sized when historical evidence is thin
**So that:** the sample-size principle is honored automatically

**Acceptance criteria:**
- Runtime queries the expectancy table before finalizing a trade card
- INSUFFICIENT_DATA returns propagate to trade card
- Trade card shows sample size explicitly (per Spec 09)

### Story 5.10 — Research Dashboard
**As:** the trader
**I want:** a single dashboard showing current expectancy per setup per regime, decay flags, robustness flags, and walk-forward divergence
**So that:** I have a weekly health check of the research state

**Acceptance criteria:**
- Web or generated static dashboard
- Auto-refreshed weekly
- Visible: green/yellow/red indicators per setup
- Deep-link to underlying report per indicator

### Story 5.11 — Ablation Test Runner
**As:** research
**I want:** an ablation runner that produces BASE, BASE+filter (each), and FULL variants of each setup
**So that:** every filter is objectively justified before entering production

**Acceptance criteria:**
- Given a setup definition, enumerates the ablation variants per §4A.1
- Runs each variant through the backtester with identical data
- Produces per-variant report with all metrics from §4A.1
- Flags any filter that fails all three retention criteria (§4A.2)
- Report persisted under `docs/strategy/reports/ablation-{setup}-{date}/`
- Failing filters trigger a Spec 03 amendment proposal

### Story 5.12 — Regime Signal Independence Analysis
**As:** research
**I want:** analysis of the correlations among the 6 regime signals (Spec 07 §2.4)
**So that:** redundant signals are removed and the regime score reflects genuinely independent evidence

**Acceptance criteria:**
- Computes pairwise correlation of the 6 signals over rolling 5-year window
- Identifies signals with > 0.85 correlation
- Proposes a reduced signal set that captures ≥ 95% of the variance
- Report includes: original vs reduced classifier agreement rate, per-regime performance delta

---

## 8. Acceptance Criteria for Spec 05

- All stories 5.1–5.10 pass their acceptance criteria
- Golden-fixture research run reproduces hand-computed expectancy on a known trade log
- Robustness report identifies at least one fragile parameter on a deliberately fragile test setup
- Walk-forward divergence detector correctly flags a setup deliberately overfit to in-sample data
- Strongest available reasoning model has reviewed and APPROVED

---

## 9. Open Questions for the Trader

1. **Rolling window sizes:** default 12-month and 24-month — adjust?
2. **Sample-size thresholds:** 30/100/300 per §3.2 — comfortable?
3. **Decay window:** 12 weeks rolling — is that too fast (reactive to noise) or too slow (misses real decay)?
4. **Robustness threshold:** 30% expectancy movement on 20% parameter change — adjust?
5. **Walk-forward window:** 24m train / 6m test — adjust based on regime turnover?
