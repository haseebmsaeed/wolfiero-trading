# Wolfiero — Scanner & Scoring Specification

This is the algorithmic heart of the system. It must be implemented **exactly** as specified, because
every downstream number — score, rank, outcome analytics — inherits from it.

---

## 1. Why a staged funnel

The naive design is "load 3,000 symbols, compute everything, sort." It is wrong for three reasons:

1. **Cost.** Full indicator computation on 3,000 symbols is ~40× more work than on the 500 that
   survive a trend filter, for zero additional insight — you were going to discard them anyway.
2. **Explainability.** When a morning returns nothing, a funnel tells you *which stage* emptied.
   A monolith tells you nothing.
3. **Ordering matters.** Cheap, high-rejection filters must run first. Liquidity is a single
   arithmetic comparison that removes half the universe; earnings lookup is a network call. Running
   them in the wrong order costs you ten minutes a day.

**The funnel principle: cheapest filter with the highest rejection rate goes first.**

---

## 2. The stages

### Stage 1 — Universe (~3,000)

Active, non-blocklisted symbols from `stocks` where `asset_type IN (COMMON_STOCK, ETF, ADR)`.
Refreshed weekly by `universe_refresh.py`.

### Stage 2 — Liquidity & data quality (~3,000 → ~1,500)

Pure arithmetic on cached bars. No network calls.

| Filter | Threshold | Why |
|---|---|---|
| 20-day avg dollar volume | ≥ $20,000,000 | You must be able to enter and exit a position without moving the price. Dollar volume, not share volume — 5M shares of a $2 stock is not liquidity. |
| Last close | ≥ $5.00 | Below $5 the tape is dominated by gaps and promotion; stops are unenforceable. |
| Trading history | ≥ 250 bars | A 200-day MA needs 200 bars plus warm-up. Recent IPOs also have no base structure to trade. |
| Data freshness | last bar within 3 trading days | A stale symbol produces confidently wrong indicators. |
| Bar validity | passes the OHLCV validator | Bad data in, plausible garbage out. |

### Stage 3 — Trend & relative strength (~1,500 → ~500)

Now compute the full indicator set. This is the expensive stage; it runs on the survivors only.

**Long path** — all must hold:
- Close > 200-day SMA (the long-term regime for the individual stock)
- Close > 50-day SMA
- 50-day SMA slope over 20 days > 0
- Relative strength percentile vs the universe ≥ 50
- Not extended: close ≤ 15% above the 20-day EMA
  *(Buying a stock 25% above its 20-EMA is buying a blow-off. The subsequent mean reversion hits
  your stop before the trend resumes.)*

**Short path** (informational only in v1) — the mirror of the above.

### Stage 4 — Setup detection (~500 → ~150)

Run all four detectors; keep the highest-quality result per symbol. Drop anything below
`min_setup_quality = 0.45`. Each detector returns a **graded 0–1 score**, never a boolean.

#### Breakout
- Identify resistance: highest high over the last 20–60 bars, touched ≥ 2 times within 1.5% of each other.
- Trigger: today's close within 2% below, or has just crossed above, that level.
- Volume confirmation: today's volume ≥ 1.3× the 20-day average.
- Base quality: the preceding consolidation range is ≤ 15% wide over ≥ 10 bars.

`quality = 0.35·volume_confirmation + 0.30·base_tightness + 0.20·touch_count_strength + 0.15·trend_alignment`

> A breakout from a tight, well-tested base on heavy volume is a different animal from a drift
> through a single prior high on average volume. Grading captures that; a boolean does not.

#### Pullback — *the highest-quality setup for swing trading*
- Confirmed uptrend (Stage 3 already guarantees it).
- Prior advance ≥ 8% within the last 30 bars.
- Current retracement into a support zone: the 20-EMA, the 50-SMA, or a prior swing low.
- Retracement depth between 3% and 15% off the recent high. *(Shallower isn't a pullback; deeper is
  a trend break.)*
- **Volume contracting** during the pullback — the 3-day average volume is below the 20-day average.
- Stabilisation: at least one bar closing in the upper half of its range, or a higher low.

`quality = 0.30·support_confluence + 0.25·volume_contraction + 0.20·retracement_depth_fit + 0.15·prior_trend_strength + 0.10·stabilisation`

> Contracting volume on the pullback is the single most informative input here. Falling price on
> *rising* volume is distribution, not a pullback — and it is the most common way this setup is
> misidentified.

#### Consolidation / coil
- Bollinger Band width in the bottom 25th percentile of the last 100 bars.
- ATR% below its own 50-day average.
- Range ≤ 10% over the last 10–20 bars.
- Preceded by an advance (a coil after a decline is a bear flag, not this setup).

`quality = 0.40·compression_percentile + 0.30·range_tightness + 0.20·prior_trend + 0.10·duration_fit`

#### Momentum continuation
- Relative strength percentile ≥ 80 over 3 months.
- Within 10% of the 52-week high.
- Orderly: no single-day drop > 8% in the last 20 bars.
- Higher highs and higher lows over the last 3 swings.

`quality = 0.35·rs_percentile + 0.25·proximity_to_high + 0.25·orderliness + 0.15·swing_structure`

### Stage 5 — Composite scoring (~150, ranked)

```
score = 100 × (
    0.25 × technical_score       +
    0.15 × momentum_score        +
    0.15 × relative_strength     +
    0.10 × volume_score          +
    0.10 × regime_fit_score      +
    0.10 × catalyst_score        +
    0.15 × reward_risk_score
)
```

| Component | Composed of | Normalisation |
|---|---|---|
| `technical_score` | Setup quality (0.5), MA stack alignment (0.2), distance-from-support risk (0.3) | Already 0–1 |
| `momentum_score` | RSI positioned 45–70 (0.4), MACD state (0.3), 20-day ROC (0.3) | **RSI is scored as a band, not "higher is better"** — RSI 85 is a warning, not a strength |
| `relative_strength` | Percentile rank vs universe, 3-month weighted | Percentile/100 |
| `volume_score` | Volume ratio vs 20-day avg (0.6), dollar-volume trend (0.4) | Clipped at 3.0× then scaled |
| `regime_fit_score` | Does this setup historically suit the current regime | Lookup table, later replaced by measured outcomes |
| `catalyst_score` | Materiality × durability of the best recent news item | 0.5 neutral when no news is available — **absence of news is not a negative** |
| `reward_risk_score` | `min(reward_risk / 4.0, 1.0)` | Caps the influence of implausibly high R:R, which usually signals a bad stop |

**Rules that must be enforced in code:**
- Weights load from the active `strategy_versions.weights`, never hardcoded.
- Weights must sum to 1.0 — assert at startup.
- Every component's raw, normalised, and weighted contribution is persisted in `score_breakdown`.
- A missing component defaults to its neutral value (0.5) and is flagged, never treated as 0.
  *(Treating "no news data" as a 0 catalyst score would systematically penalise every quiet,
  well-behaved stock — exactly the opposite of what you want.)*

### Stage 6 — Risk & catalyst veto (~150 → ~20)

Applied **after** scoring so the veto reason is recorded rather than hidden inside a zero.

| Veto | Condition | Rationale |
|---|---|---|
| `RR_BELOW_FLOOR` | reward:risk < 2.0 | Below 2:1 you need a win rate most discretionary traders do not have |
| `EARNINGS_IN_WINDOW` | earnings date ≤ hold window (15 trading days) | A binary event overwhelms any technical edge |
| `NO_VALID_STOP` | no defensible structural stop within 12% | An undefined stop means undefined risk |
| `HEAT_LIMIT` | would breach 6% total portfolio heat | Portfolio-level survival beats any single idea |
| `SECTOR_LIMIT` | would breach 30% sector exposure | Correlated positions are one position wearing a disguise |
| `ALREADY_HELD` | open position exists | Adding is a separate decision with separate rules |
| `EXTENDED` | > 15% above the 20-EMA | Late entry, wide stop, poor R:R |

Survivors are re-ranked by score. Top `SCAN_MAX_CANDIDATES` (default 20) proceed to enrichment.

---

## 3. Regime interaction

Regime does not just adjust scores — it changes how many ideas the system will even surface.

| Regime | Long score multiplier | Max new candidates | Size multiplier |
|---|---|---|---|
| `RISK_ON` | 1.00 | 20 | 1.0 |
| `NEUTRAL` | 0.85 | 10 | 0.6 |
| `RISK_OFF` | 0.60 | 3 | 0.0–0.3 |

> **Why cap the count rather than only shrinking scores?** Because a list of twenty ideas in a
> risk-off market invites you to trade twenty of them. The count *is* the behavioural control. In
> `RISK_OFF` the correct output is usually "there is nothing worth doing today" — and a system that
> can never say that is a system that will hurt you.

---

## 4. Performance requirements

Full scan under **10 minutes** on 2 vCPU / 8 GB.

Where the time goes, and how to keep it there:
- **Stage 2 is vectorised.** Load all bars into a single pandas frame and filter cross-sectionally.
  Do not loop per symbol.
- **Stage 3 computes indicators in batch** over a multi-index frame.
- **Stage 4 loops**, but over ~500 symbols, and is the natural parallelisation point
  (`ProcessPoolExecutor`, workers = vCPU count) if the budget is threatened.
- **No network I/O in stages 2–5.** All bars come from `price_history`, pre-warmed at 05:30.
- Network calls happen only in the 05:30 refresh and the 06:15 enrichment, both bounded-concurrent.

---

## 5. Testability

The scanner's regression test is a **frozen fixture dataset**: ~200 symbols of real historical bars
for a known date, committed to the repo, with a hand-verified expected candidate list.

- Every stage asserts its expected entry/exit counts.
- The final ranked list is asserted exactly.
- A change in output is either an intentional strategy change (bump `strategy_version`, update the
  fixture, record why in `strategy_versions.notes`) or a bug. There is no third case.

This test is the safety net for the entire product. Without it, an innocuous refactor of an
indicator can quietly change every recommendation you receive and nobody will notice for months.
