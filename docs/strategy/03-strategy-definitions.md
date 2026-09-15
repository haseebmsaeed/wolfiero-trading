# Spec 03 — Strategy Definitions

**Status:** Draft (Phase 1 critical)
**Phase:** 1
**Depends on:** Spec 01 (Constitution), Spec 02 (Data & Halal)
**Downstream:** Spec 04 (Backtester) tests what this defines. Spec 05 (Research Engine) computes stats for these setups. Spec 07 (Runtime) executes these definitions.

---

## 1. Purpose

Spec 03 defines **every setup, every entry, every exit, and every intermediate concept** in precise mathematical terms — with provenance for every numeric threshold.

The words "clean structure," "strong stock," "controlled pullback," and "volume dry-up" are not acceptable in this document. They must reduce to equations and comparisons.

**This is the single most consequential spec in the entire system.** Spec 03 defines what everything downstream tests, computes, and executes. Errors here compound everywhere.

---

## 2. Setup Catalog

### 2.1 Phase 1 — Two Parallel Setups

Both setups are **first-class, active, and tracked independently.** Neither is "primary." Each has its own expectancy table, its own kill switch, its own trade cards, and its own P&L attribution.

| Setup Name | Style | Notification Tag |
|------------|-------|------------------|
| `PULLBACK_TO_EMA_STAGE2` (a.k.a. `PBK`) | Retracement in confirmed uptrend | `[PBK]` |
| `DONCHIAN_20_BREAKOUT` (a.k.a. `DC20`) | Momentum breakout above 20-day high | `[DC20]` |

**Rationale for two parallel setups:** the trader wants live comparative evidence between a mean-revert-into-trend approach (PBK) and a pure momentum approach (DC20) before committing capital to one style. See [`setup-comparison-dc20-vs-pullback.md`](./setup-comparison-dc20-vs-pullback.md) for the trader-facing side-by-side.

**Isolation rule:** all downstream systems (Research Engine, Trade Cards, Journal) treat these as **fully isolated setups**. Neither's stats, kill switches, or expectancy tables affect the other. A kill switch that fires on DC20 does not pause PBK, and vice versa.

### 2.2 Future Setups (Not Active in Phase 1)

| Priority | Setup Name | Activation Condition |
|----------|------------|----------------------|
| 3 | `FLAT_BASE_BREAKOUT` | After 6+ months of positive live expectancy on at least one Phase 1 setup |
| 4 | `POST_EARNINGS_DRIFT` | After 12+ months of positive live expectancy on Phase 1 setups |

**Never more than four simultaneous setups.** Adding a fifth requires retiring one.

---

## 3. Building-Block Definitions

Every setup is composed of building blocks. This section defines the blocks with math and provenance.

> ### ⚠ CRITICAL — Look-Ahead Convention
>
> Every indicator in this spec follows this convention **exactly**:
>
> **"As of date D"** means using data from close of D backwards. It NEVER uses D+1 or any future bar.
>
> For any calculation that references *"the last N days"* or *"the previous N days"*:
> - **Detectors and signal computations at close of D** use bars `D-1, D-2, …, D-N` (N completed prior days) — **today's bar is NOT included** in the historical reference channel.
> - **The current bar D is compared AGAINST that historical reference** to determine whether a signal has fired.
>
> Example (DC20): "close > 20-day high" means `Close(D) > MAX(High(D-1), High(D-2), …, High(D-20))`. **Today's own high is not in the max.** If it were, every day would trivially satisfy the condition.
>
> Any implementation that violates this convention is a look-ahead bug. Test suites in Spec 04 must include assertions that catch this.

### 3.0 Parameter Provenance Legend

Each configurable parameter carries one of these tags:

| Tag | Meaning |
|-----|---------|
| **CITED** | Value derives from a specific published source (book, paper, historical practice) |
| **STRUCTURAL** | Value is a mathematical necessity (e.g., round numbers, hard boundaries) |
| **PROVISIONAL** | Heuristic starting point — NOT robustness-tested yet. Must be validated by Spec 05 before treated as authoritative. |
| **VALIDATED** | Robustness-tested and confirmed across a reasonable parameter neighborhood |

At the current stage (Phase 1), most parameters are **PROVISIONAL**. This will change as the Research Engine (Spec 05) produces evidence.

### 3.1 Stage 2 (Weinstein Trend Definition)

**Source:** Stan Weinstein, *Secrets for Profiting in Bull and Bear Markets* (1988), Chapter 2.

A stock is in Stage 2 on date D if ALL of the following hold:

```
Close(D) > EMA_50(D)
Close(D) > SMA_200(D)
SMA_200(D) > SMA_200(D - 20)                    # 200-MA sloping up over last 20 trading days
SMA_200(D-1) > SMA_200(D - 21)                  # slope confirmed on previous day too (anti-flip-flop)
EMA_50(D) > EMA_50(D - 10)                      # 50-EMA sloping up over last 10 trading days
EMA_50(D-1) > EMA_50(D - 11)                    # slope confirmed on previous day (anti-flip-flop)
Close(D) has closed > SMA_200 on ≥ 80% of last 30 days
```

**Anti-flip-flop rationale:** requiring the slope condition to hold on both D and D-1 prevents a stock that had a one-day negative-slope tick from qualifying purely on the recovery day. This eliminates a class of noise-driven false Stage-2 detections without materially reducing true positives.

**Configurable parameters:**
- `stage2.min_days_above_200sma_pct` = 80% [CITED — Weinstein: "the great majority"]
- `stage2.slope_lookback_50ema` = 10 [PROVISIONAL]
- `stage2.slope_lookback_200sma` = 20 [PROVISIONAL]
- `stage2.slope_confirmation_days` = 2 [STRUCTURAL — anti-flip-flop]

### 3.2 Relative Strength (O'Neil-style)

**Source:** William O'Neil, *How to Make Money in Stocks* (CANSLIM), 4th ed., Chapter 6.

`RS_line(stock, D) = Close(stock, D) / Close(SPY, D)`

A stock has strong relative strength on date D if:
- `RS_line(D)` is at a new 63-day (3-month) high, AND
- `RS_line` slope over the last 63 days is positive, AND
- Stock's 63-day return > SPY's 63-day return by at least 5 percentage points

**Configurable parameters:**
- `rs.lookback_days` = 63 [CITED — O'Neil CANSLIM 3-month convention]
- `rs.min_outperformance_pct` = 5.0 [PROVISIONAL]

### 3.3 Pullback (Controlled Retracement)

**Conceptual source:** the *general idea* of a "controlled pullback" comes from Minervini's VCP (*Trade Like a Stock Market Wizard*, Chapter 5) and Weinstein's Stage-2 pullback discussions. **The specific numerical thresholds below are Wolfiero proposed heuristics, not verbatim rules from any author.** Minervini describes the pattern qualitatively; the concrete 3–12% band, 15-day lookback, ATR ratios, and down-day cap are our formalization for algorithmic execution. See [`source-attribution.md`](./source-attribution.md) for a rigorous separation.

A pullback exists on date D if:
- Stock made a swing high `H` within the last 15 trading days
- Current `Close(D) < H`
- Retracement magnitude: `(H − Low_within_pullback) / H ∈ [3%, 12%]`
- Retracement magnitude in ATR units: `(H − Low_within_pullback) / ATR_14(H) ∈ [1.0, 3.5]`
- Stock has NOT closed below EMA_50 during the pullback
- Number of down days during pullback ≤ 7

**Configurable parameters:**
- `pullback.max_lookback_days` = 15 [PROVISIONAL]
- `pullback.min_retracement_pct` = 3.0 [PROVISIONAL — Minervini range]
- `pullback.max_retracement_pct` = 12.0 [PROVISIONAL — Minervini range]
- `pullback.min_retracement_atr` = 1.0 [PROVISIONAL]
- `pullback.max_retracement_atr` = 3.5 [PROVISIONAL]
- `pullback.max_down_days` = 7 [PROVISIONAL]

### 3.4 Volume Dry-Up

**Conceptual source:** Minervini describes volume contraction as a signature of the VCP pattern (*Trade Like a Stock Market Wizard*, Chapter 5) — that volume "quiets down" during accumulation. **The specific 0.70 ratio threshold is a Wolfiero proposed heuristic**, not a Minervini rule. Minervini does not publish a specific numeric threshold for volume contraction; he describes it qualitatively.

Volume contracted during pullback if:
- `avg_volume(pullback_days) / avg_volume(prior 20 days pre-pullback) ≤ 0.70`

**Configurable parameters:**
- `volume.contraction_ratio_max` = 0.70 [PROVISIONAL — Wolfiero heuristic inspired by Minervini's qualitative VCP volume signature]

### 3.5 Support Zone

Pullback support is defined as the FIRST of these levels the price touches:
1. Rising 20-day EMA
2. Rising 50-day EMA
3. Prior breakout pivot level (documented per stock)

**The support level touched becomes the reference for the stop.**

### 3.6 ATR (Average True Range)

Standard 14-day ATR (Wilder). Used for stop viability and volatility gating.

### 3.7 Top-3 Sectors (Deterministic Ranking)

**Provenance:** PROVISIONAL — matches trader convention; robustness-testing pending.

**Purpose:** produce an unambiguous, reproducible ranking of the 11 GICS sector ETFs so that "top-3 sectors" means the same thing to any two implementations.

**Sector ETFs (fixed universe of 11):**
`XLK, XLV, XLE, XLF, XLI, XLY, XLP, XLB, XLU, XLRE, XLC`

**Algorithm (all computations as of close of date D, using only bars ≤ D):**

```
For each sector ETF s:
    return_1m(s, D) = Close(s, D) / Close(s, D-21) − 1
    return_3m(s, D) = Close(s, D) / Close(s, D-63) − 1

Convert to ranks (higher return = better rank; rank 1 = best):
    rank_1m(s, D) = rank of s among all 11 by return_1m
    rank_3m(s, D) = rank of s among all 11 by return_3m

Combined rank:
    combined_rank(s, D) = (rank_1m(s, D) + rank_3m(s, D)) / 2

Tie-break: if two sectors have identical combined_rank, the one with LOWER rank_3m wins
(3-month is the more stable signal; use it to break ties).

top_3_sectors(D) = the 3 sectors with the lowest combined_rank (best combined ranks)
```

**Refresh cadence:** computed daily post-close; used for next trading day's decisions.

**Configurable parameters:**
- `sectors.lookback_1m_days` = 21 [PROVISIONAL]
- `sectors.lookback_3m_days` = 63 [PROVISIONAL]
- `sectors.top_n` = 3 [PROVISIONAL]

### 3.8 Active Themes (Trader Overlay — NOT Algorithmic)

**Status:** DEMOTED to trader-heuristic layer as of docs revision.

**Rationale:** "Active themes" (e.g., "AI infrastructure," "GLP-1 obesity," "nuclear") are qualitative narratives without a rigorous algorithmic definition. Two people looking at the same market will produce different theme lists. Rather than pretend otherwise, themes are **not** used as a hard system filter.

**Where themes ARE used:**
- Trader watchlist prioritization (subjective, journal-tracked)
- Trade card `theme` field (informational)
- Portfolio concentration limit ("max 1 position per active theme" — where the trader annotates the theme)

**Where themes are NOT used:**
- Setup detection VETO
- Regime classification
- Position sizing
- Any automated ranking

**Journal treatment:** every trade card records the theme (trader-supplied). Quarterly review examines whether theme-labeled trades outperformed non-themed; if a rigorous signal emerges from that data, themes may be promoted to an algorithmic filter in a future spec revision.

---

## 4. Setup 1 — `PULLBACK_TO_EMA_STAGE2` (`PBK`) — Full Definition

### 4.1 `PULLBACK_TO_EMA_STAGE2` Setup

A candidate is valid on date D if ALL of the following are true:

**Universe (from Spec 02 §6.1):**
```
stock ∈ Universe(D)
```

**Trend:**
```
stock is Stage 2 on date D                          [§3.1]
```

**Relative strength:**
```
stock has strong RS on date D                       [§3.2]
```

**Pullback structure:**
```
stock is in a pullback on date D                    [§3.3]
volume contracted during pullback                    [§3.4]
pullback support is at EMA_20 or EMA_50              [§3.5]
```

**Not overextended after pullback:**
```
distance from Close(D) to EMA_20(D) ≤ 1.5 × ATR_14(D)
```

**No blackouts:**
```
no earnings announcement scheduled within next 15 trading days
no ex-dividend event within next 5 trading days
stock has not been on a kill switch pause list
```

### 4.2 Entry Trigger

The trade activates on date D+n when:
```
Close(D+n) > High(D+n-1)                             # reclaim of prior day's high
AND Volume(D+n) > 1.25 × avg_volume(20-day, D+n-1)   # volume confirmation
AND all Section 4.1 conditions still valid on D+n
AND market regime permits new entries (Spec 07)
```

**Order type:** Buy-stop order at `High(D+n-1) + 0.05`, expires end-of-day.

**Configurable parameters:**
- `entry.volume_multiple` = 1.25 [PROVISIONAL]
- `entry.stop_offset_dollars` = 0.05 [STRUCTURAL — trigger buffer above prior high]

### 4.3 Initial Stop Loss

**Structural stop:** `stop_price = Low(pullback) − 0.5 × ATR_14(entry_day)`

**Stop viability check:**
```
if (entry_price − stop_price) > 2.0 × ATR_14(entry_day):
    VETO — trade too extended for clean stop
```

**Configurable parameters:**
- `stop.structural_buffer_atr` = 0.5
- `stop.max_distance_atr` = 2.0

### 4.4 Position Sizing

Per Spec 01 §4.1 and §4.2:
```
risk_dollars = account × per_trade_risk_pct(sample_size_bucket)
shares = floor(risk_dollars / (entry_price − stop_price))
capital_used = shares × entry_price

if capital_used > 0.10 × account:
    reduce shares until capital_used ≤ 0.10 × account
```

**Configurable parameters:**
- `sizing.max_position_pct_of_account` = 10.0

---

## 4A. Setup 2 — `DONCHIAN_20_BREAKOUT` (`DC20`) — Full Definition

> ### ⚠ IMPORTANT — Classic Turtle vs Wolfiero-Modified DC20
>
> The **classic Turtle System 1** consists of only these rules: buy on new 20-day high, exit on new 10-day low. **That is it.** No volume filter, no regime filter, no sector filter, no ATR viability, no halal screen, no earnings blackout.
>
> The **Wolfiero DC20** below adds several filters on top of the classic Turtle core:
> - **Halal Rule Zero** (required by Constitution — non-Turtle)
> - **Market regime gate** (STRONG_BULL / NORMAL_BULL only — Wolfiero-added)
> - **Top-3 sector requirement** (Wolfiero-added)
> - **Volume ≥ 1.5× average confirmation** (Wolfiero-added)
> - **ATR volatility sanity** (Wolfiero-added)
> - **Stop viability check** (Wolfiero-added)
> - **Earnings blackout** (Wolfiero-added — see §4A tension in [`rule-audit.md`](./rule-audit.md) §4.1)
>
> These additions are **PROPOSED MODIFICATIONS**, not part of the historically-tested Turtle System 1. Whether they improve the setup or over-filter it is a research question — see Spec 05 §4A ablation testing. Do not attribute these filters to Curtis Faith or the Turtle program. See [`source-attribution.md`](./source-attribution.md) for a rigorous separation.

### 4A.0 Building Blocks Specific to DC20

**Donchian channels (20-day and 10-day):**
```
DC_upper(N, D) = MAX(High(D-1), High(D-2), ..., High(D-N))
DC_lower(N, D) = MIN(Low(D-1),  Low(D-2),  ..., Low(D-N))
```

**Note on TradingView reference:** TradingView's default Donchian Channels indicator uses this exact convention (the upper band is the highest high of the previous N completed bars, excluding the current bar). Our implementation must match this. If a chart platform's indicator INCLUDES today's bar in the reference, that is a different indicator and will produce different signals.

**Source:** Richard Donchian, published 1950s; popularized by the Turtle Trader program (Richard Dennis, William Eckhardt, 1983–1988). Documented in Curtis Faith's *Way of the Turtle* (2007), Michael Covel's *The Complete TurtleTrader* (2007), and Faith's original Turtle rules leak (2003).

**Configurable parameters:**
- `dc20.entry_lookback` = 20
- `dc20.exit_lookback` = 10

### 4A.1 `DONCHIAN_20_BREAKOUT` Setup

A candidate is valid on date D if ALL of the following are true:

**Universe (from Spec 02 §6.1):**
```
stock ∈ Universe(D)
```

**Halal (from Spec 01 §3):**
```
halal_status(stock, D) == COMPLIANT     # at-time-of-trade check
```

**Regime gate (from Spec 07 §3.4):**
```
regime(D) ∈ { STRONG_BULL, NORMAL_BULL }
# DC20 explicitly does NOT trade in CHOP, HIGH_VOL, or BEAR
```

**Sector leadership (from Spec 07):**
```
stock.sector ∈ top_3_sectors(D)
```

**Breakout condition:**
```
Close(D) > DC_upper(20, D)                                # closing break of 20-day high
```

**Volume confirmation:**
```
Volume(D) > 1.5 × avg_volume_20(D-1)                      # institutional participation
```

**Volatility sanity:**
```
0.5 × ATR_60_median ≤ ATR_14(D) ≤ 2.0 × ATR_60_median
# not compressed to near-zero, not spiking violently
```

**Stop viability (must be tradeable):**
```
initial_stop_price = DC_lower(10, D)
stop_distance = Close(D) − initial_stop_price
if stop_distance > 2.0 × ATR_14(D):
    VETO — trade too extended for clean stop
```

**Blackouts:**
```
no earnings within next 15 trading days
no ex-dividend within next 5 trading days
setup is not on kill switch pause list
```

**Configurable parameters:**
- `dc20.entry_volume_multiple` = 1.5
- `dc20.atr_lower_bound_multiple` = 0.5
- `dc20.atr_upper_bound_multiple` = 2.0

### 4A.2 Entry Trigger and Order

**Entry decision:** at close of D, if all §4A.1 conditions are true, the setup fires.

**Order:** two order-timing modes are permitted (choose one per config and stick to it):
- **Mode A — Close entry:** buy at close of D (day of signal)
- **Mode B — Open entry:** buy at open of D+1

**Default:** Mode B (next-day open) — slightly worse fills on average, but simpler execution and matches Turtle-original rules.

**Configurable parameters:**
- `dc20.entry_mode` = "next_open" | "same_close"

### 4A.3 Initial Stop Loss

**Stop:** `stop_price = DC_lower(10, D)` at the time of entry.

**Stop viability check** (already applied in §4A.1 — repeated here for completeness):
```
if (entry_price − stop_price) > 2.0 × ATR_14(entry_day):
    trade was VETOed at §4A.1
```

**Stop location is FIXED at trade entry — it does not slide with the 10-day low** until the exit rule (§5A.1) fires.

### 4A.4 Position Sizing

Same formula as PBK (Spec 03 §4.4):
```
risk_dollars = account × per_trade_risk_pct(sample_size_bucket)
shares = floor(risk_dollars / (entry_price − stop_price))
capital_used = shares × entry_price

if capital_used > 0.10 × account:
    reduce shares until capital_used ≤ 0.10 × account
```

Because DC20 stops are wider than PBK stops in absolute terms, position sizes will typically be smaller for the same risk budget. That is intended.

---

## 5. Exit Policies

Exits are defined **per setup**. PBK and DC20 have different exit mechanics because their entry philosophies are different.

### 5.1 `PBK` — Research-Phase Default Exit Policy

Until Spec 05 (Research Engine) has produced statistical evidence favoring an alternative, the default exit stack for PBK is:

```
1. STRUCTURAL STOP  (§4.3)
2. PARTIAL PROFIT   at 2.0R:  sell 1/3 of position; move stop on remaining 2/3 to entry
3. RUNNER TRAIL     on remaining 2/3: trail stop at MIN(EMA_20, most-recent-higher-low − 0.5 × ATR)
4. TIME STOP        if unrealized R < 1.0 after 15 trading days: close full position at close
5. REGIME EXIT      if market regime downgrades to CHOP or worse: close 1/2 immediately; tighten trail on rest
6. HALAL EXIT       if halal classification changes to "not halal": close full position at next open
7. EARNINGS EXIT    if earnings announced within 3 days of scheduled: close full position before announcement
```

**Configurable parameters (PBK):**
- `pbk.exit.partial_at_R` = 2.0
- `pbk.exit.partial_size_fraction` = 0.333
- `pbk.exit.trail_atr_buffer` = 0.5
- `pbk.exit.time_stop_days` = 15
- `pbk.exit.time_stop_min_R` = 1.0
- `pbk.exit.earnings_exit_days` = 3

### 5A.1 `DC20` — Research-Phase Default Exit Policy

DC20 is a trend-following system. Its power comes from letting winners run. The exit is intentionally simpler than PBK's.

```
1. STRUCTURAL STOP  (§4A.3) — fixed at DC_lower(10) at entry time
2. TREND EXIT       if Close(D) < DC_lower(10, D): close full position at close
                    # NOTE: this is the "trailing" exit — the 10-day low re-computes daily,
                    # naturally trailing up as the trend advances
3. REGIME EXIT      if market regime downgrades to CHOP or worse: close 1/2 immediately;
                    tighten trend exit from DC_lower(10) to DC_lower(5)
4. HALAL EXIT       if halal classification changes to "not halal": close full position at next open
5. EARNINGS EXIT    if earnings announced within 3 days: close full position before announcement
6. NO TIME STOP     — DC20 does NOT have a time stop; letting winners run is the edge
7. NO PARTIAL       — DC20 does NOT take partial profits; the trend exit does it all
```

**Rationale for no time stop / no partials on DC20:** the Turtle-style edge is capturing the fat tail of extreme trends. Time stops and partials cut off that tail and destroy the expectancy. If a DC20 trade sits at breakeven for 20 days, that is normal — trends can consolidate for weeks before continuing.

**Configurable parameters (DC20):**
- `dc20.exit_lookback` = 10  (10-day trailing low)
- `dc20.chop_exit_lookback` = 5  (tightened to 5 during CHOP)
- `dc20.earnings_exit_days` = 3

### 5.2 Exit Policies Under Research

These candidate exit policies must be backtested and compared per setup (Spec 05):

**For `PBK`:**

| Policy ID | Description |
|-----------|-------------|
| PBK-E-01 | Structural stop only (baseline) |
| PBK-E-02 | Structural + partial at 1.5R + move stop to entry |
| PBK-E-03 | Structural + partial at 2R + 20 EMA trail (default) |
| PBK-E-04 | Structural + partial at 2R + ATR-based trail (2 × ATR) |
| PBK-E-05 | Structural + no partial + higher-low trail |
| PBK-E-06 | Structural + time stop at 10 days |
| PBK-E-07 | Structural + time stop at 15 days (default component) |
| PBK-E-08 | Structural + fixed 3R target (no trail) |

**For `DC20`:**

| Policy ID | Description |
|-----------|-------------|
| DC20-E-01 | DC_lower(10) trailing exit (default, Turtle-original) |
| DC20-E-02 | DC_lower(20) trailing exit (wider, catches larger trends) |
| DC20-E-03 | DC_lower(10) + partial at 3R (blended) |
| DC20-E-04 | DC_lower(10) + time stop at 40 days if unrealized R < 0.5 |
| DC20-E-05 | ATR-based trailing (Close − 3 × ATR) instead of Donchian |
| DC20-E-06 | DC_lower(10) but exit half at 2R structural target |

**Research output required:** which policy produces the highest out-of-sample expectancy AND lowest drawdown, per regime.

### 5.3 Non-Negotiable Exit Rules
Regardless of research outcome, these are permanent:

- Stops only move in the trader's favor. Never wider.
- Halal exit: mandatory.
- Earnings exit: mandatory unless the setup itself IS earnings-based.
- Kill-switched setup: no new entries; existing positions run to their exits.

---

## 6. Provenance Table

Every numeric threshold in this spec must cite its source. This table is authoritative.

| Parameter | Value | Source |
|-----------|-------|--------|
| Stage 2: 80% of last 30 days above 200-SMA | 80%, 30 | Weinstein 1988 Ch. 2, adapted |
| Stage 2: 50-EMA slope lookback | 10 days | Convention, robustness-tested (pending) |
| RS lookback | 63 days | O'Neil CANSLIM 3-month convention |
| RS min outperformance | 5% | O'Neil "leaders lead by wide margins"; robustness-tested (pending) |
| Pullback lookback | 15 days | Typical swing horizon |
| Pullback retracement 3–12% | 3–12% | Minervini VCP typical range |
| Pullback retracement 1.0–3.5 ATR | 1.0–3.5 | ATR-normalized version of above |
| Pullback max down days | 7 | Prevents capitulation from qualifying |
| Volume contraction ≤ 0.70 | 0.70 | Minervini VCP volume signature |
| Overextension check ≤ 1.5 ATR | 1.5 | Prevents chasing far above support |
| Entry volume multiple 1.25× | 1.25× | Institutional accumulation signal, testable |
| Stop buffer 0.5 ATR | 0.5 | Prevents "obvious" stop hunt |
| Stop max distance 2.0 ATR | 2.0 | Volatility viability of structural stop |
| Per-trade risk 0.5–1.0% | 0.5–1.0% | Van Tharp risk-of-ruin literature |
| Max position 10% of account | 10% | Concentration ceiling per Constitution |
| Partial at 2R | 2R | Testable, research to confirm |
| Time stop 15 days | 15 | Median swing hold window; testable |
| Earnings blackout 15 days | 15 | Constitution §4.6 |
| DC20 entry lookback | 20 days | Donchian original convention; Turtle System 1 entry |
| DC20 exit lookback | 10 days | Turtle System 1 exit rule (Faith, *Way of the Turtle*, 2007) |
| DC20 entry volume multiple | 1.5× | Institutional participation filter; robustness-tested (pending) |
| DC20 ATR bounds 0.5–2.0× 60d median | 0.5, 2.0 | Prevents both dead volatility and volatility spikes; robustness-tested (pending) |
| DC20 chop-exit lookback | 5 days | Tightened exit during regime downgrade; robustness-tested (pending) |
| DC20 no time stop | N/A | Turtle-original; letting winners run is the edge (Faith 2007) |

**RULE:** any parameter added to this system without a source citation is a bug.

---

## 7. Explicit Anti-Overfitting Rules

### 7.1 No Grid Search on Same Data As Trading
No parameter in this spec may be selected by grid-searching for maximum CAGR on the same dataset that will be used for validation or trading.

### 7.2 Small Number of Free Parameters
The total number of tunable parameters must remain small (~20 max) and each must have a defensible prior from source literature.

### 7.3 Round Numbers
Prefer round numbers (0.5, 1.0, 2.0, 20, 50, 63). Do not tune to 1.47 or 63.4. Round numbers are honest about the noise floor.

### 7.4 Robustness Testing (Spec 05 will implement)
Every parameter must show that performance is not brittle: nudging the parameter ±20% should not collapse performance. If it does, the parameter is overfit.

---

## 8. Stories

### Story 3.1 — Building Block Implementation
**As:** engineering
**I want:** each Section 3 building block (Stage 2, RS, Pullback, Volume Dry-Up, Support Zone, ATR) implemented as a pure function
**So that:** setups compose from tested primitives with no duplication

**Acceptance criteria:**
- One function per building block, in a `strategy/primitives/` module
- Each function takes a price series and returns a boolean (or numeric where applicable)
- Golden fixture tests: each function returns known values on a fixed historical dataset
- Coverage ≥ 95% on the primitives module
- No primitive reads config or has side effects

### Story 3.2 — PBK Setup Detector
**As:** the runtime
**I want:** a `detect_pullback_stage2(stock, date)` function that returns `SetupCandidate | None`
**So that:** the pipeline can enumerate PBK candidates independently of DC20

**Acceptance criteria:**
- Applies all conditions in §4.1
- Returns candidate object with all relevant computed values (stage, RS score, pullback %, volume ratio, ATR, support level)
- Returns None with a `reason` when any condition fails (surfaced in daily digest)
- Golden fixture test: a known historical setup on a known ticker returns a valid candidate

### Story 3.3 — Entry Trigger Monitor
**As:** the runtime
**I want:** a monitor that watches candidate stocks and fires when the entry condition (§4.2) is met
**So that:** the trader is alerted the moment the trigger activates

**Acceptance criteria:**
- Given a list of candidates, checks intraday whether entry condition is met
- Fires alert with proposed order details (buy-stop price, expiration)
- Re-validates §4.1 conditions at trigger time (VETO if any condition invalidated)
- Alert deduplicated per candidate per day

### Story 3.4 — Stop Calculator
**As:** the risk engine
**I want:** a `calculate_stop(entry_price, pullback_low, atr)` function
**So that:** stops are consistent and viable

**Acceptance criteria:**
- Applies structural stop formula (§4.3)
- Applies viability check (§4.3)
- Returns `Stop | VETO`
- Unit tests cover edge cases: very tight stops, very wide stops, boundary at 2 × ATR

### Story 3.5 — Position Sizer
**As:** the risk engine
**I want:** a `calculate_position_size(account, risk_pct, entry, stop)` function
**So that:** every trade is sized to exactly the intended risk

**Acceptance criteria:**
- Applies formula in §4.4
- Enforces 10% max concentration
- Rounds down to whole shares
- Returns `PositionPlan` with shares, capital, actual risk in $
- Unit tests confirm sizing math matches hand calculation

### Story 3.6 — Exit Policy Executor
**As:** the runtime
**I want:** the default exit stack (§5.1) implemented as an ordered rule chain
**So that:** open positions have deterministic exit behavior

**Acceptance criteria:**
- Each of the 7 rules is a discrete function
- Rules evaluated in order every bar (EOD in Phase 1)
- First rule that fires wins; action logged
- Regime and halal exits can fire mid-session (real-time), not just EOD
- Integration test: simulate a full trade with each exit type triggered

### Story 3.7 — Parameter Configuration Schema
**As:** engineering
**I want:** all parameters in this spec exposed via a typed config
**So that:** research can propose changes without code edits

**Acceptance criteria:**
- One config module per building block and per exit policy
- Every parameter has a default, a valid range, and a source citation
- Config version stamped on every setup detection and trade card
- Config load fails fast on out-of-range values

### Story 3.8 — Provenance Enforcement
**As:** the reviewer / QA
**I want:** an automated check that every configurable parameter has a source citation
**So that:** unsourced numbers cannot slip into production

**Acceptance criteria:**
- CI check reads the config schema and verifies each parameter has a non-empty `source` field
- Missing source fails the build
- Source references point to real citations (validated at review, not code)

### Story 3.9 — Alternative Exit Policy Registry
**As:** the research engine
**I want:** each candidate exit policy from §5.2 registered as a testable strategy
**So that:** they can be evaluated against the default

**Acceptance criteria:**
- E-01 through E-08 implemented as policy classes conforming to a common interface
- Each policy can be applied to a backtested trade stream to compute per-policy stats
- Research engine can compare policies side-by-side per regime

### Story 3.10 — Non-Overfitting Guard
**As:** engineering
**I want:** an enforced rule that parameters cannot be grid-searched on the trading dataset
**So that:** the anti-overfitting principle is not just a hope

**Acceptance criteria:**
- Research engine's parameter search API requires an explicit `dataset_partition` argument
- Any parameter selection is logged with its dataset scope
- If parameter changes are proposed based on the trading dataset, the change is rejected with an error

### Story 3.11 — DC20 Setup Detector
**As:** the runtime
**I want:** a `detect_dc20_breakout(stock, date)` function that returns `SetupCandidate | None`
**So that:** the pipeline enumerates DC20 candidates independently of PBK

**Acceptance criteria:**
- Applies all conditions in §4A.1
- Computes `DC_upper(20, D)` and `DC_lower(10, D)` correctly per §4A.0
- Returns candidate object with entry, stop, volume ratio, ATR, DC channels
- Returns None with a `reason` when any condition fails
- Setup output tagged `setup=DC20` explicitly
- Golden fixture test: a known 2020 DC20 breakout on a leader returns a valid candidate

### Story 3.12 — DC20 Exit Executor
**As:** the runtime
**I want:** the DC20 exit stack (§5A.1) implemented per priority
**So that:** DC20 positions have deterministic exit behavior

**Acceptance criteria:**
- 10-day low re-computed daily post-close
- Trend exit fires when Close < DC_lower(10)
- Regime downgrade tightens exit to DC_lower(5)
- Halal and earnings exits identical to PBK
- **No time stop, no partial profit** — enforced (config values cannot enable them for DC20)
- Integration test: simulate a full DC20 trade with each exit type triggered

### Story 3.13 — Setup Isolation Enforcement
**As:** engineering
**I want:** every setup detector and exit executor tagged with its setup ID
**So that:** downstream systems can filter, group, and analyze per setup independently

**Acceptance criteria:**
- Every `SetupCandidate` object has a required `setup_id` field
- Every trade card, order, fill, and journal entry carries `setup_id`
- Kill switches are scoped to `setup_id`
- Expectancy tables (Spec 05) are keyed by `setup_id`
- Test: pausing DC20 kill switch does not pause PBK

### Story 3.14 — Setup Registry
**As:** engineering
**I want:** a single registry of active setups with their detector, exit stack, config, and tag
**So that:** adding or retiring a setup is one code change, not scattered updates

**Acceptance criteria:**
- Registry maps `setup_id → { detector, exit_stack, config, notification_tag, description }`
- Only setups in the registry are evaluated by the runtime
- Retiring a setup removes it from active evaluation but preserves historical journal data
- Configuration flag can enable/disable individual setups

---

## 9. Acceptance Criteria for Spec 03

- All stories 3.1–3.10 pass their acceptance criteria
- Golden fixture: a known 2019 setup on AAPL (or similar) detects correctly
- Provenance table (§6) has zero blank cells
- Robustness test skeleton exists (implementation in Spec 05)
- Strongest available reasoning model has reviewed and APPROVED

---

## 10. Open Questions for the Trader

1. **Two parallel setups confirmed:** PBK and DC20 are both Phase-1 active setups per current spec. When (if ever) do we add a third setup (candidate: `FLAT_BASE_BREAKOUT`)? Suggested trigger: 6+ months of positive live expectancy on both existing setups.
2. **Support tier order:** in §3.5, the order is 20 EMA → 50 EMA → pivot. Should pivots be first (structural)?
3. **RS outperformance threshold:** 5% is O'Neil's approximate — should we test 3%, 5%, 7% ranges as robustness (not overfitting)?
4. **Time stop:** 15 trading days is ~3 weeks. Comfortable, or too long?
5. **Partial profit target:** 2R default — should we test 1.5R and 2.5R as alternatives before deciding default?
