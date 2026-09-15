# Source Attribution — What the Authors Actually Teach vs Wolfiero Additions

**Purpose:** rigorously separate (a) what published trading authors actually wrote from (b) what we (Wolfiero) have added, formalized, or modified on top. This exists so that:

1. We do not misattribute Wolfiero heuristics to published authors.
2. We do not overstate the historical validation of our specific numerical thresholds.
3. We know exactly which rules can appeal to prior literature and which are novel proposals awaiting evidence.
4. Readers, reviewers, and future collaborators can trace every rule to its true origin.

**Convention:** for each item, we distinguish:

- **AUTHOR** — verbatim or clear paraphrase from the cited source, with location where possible
- **WOLFIERO** — Wolfiero addition, formalization, or numerical proposal

**Honest disclaimer:** the author summaries below are our best-effort paraphrases from our reading of the source books. They are NOT verbatim quotes. For rigor, consult the original texts directly. If any paraphrase misrepresents what the author actually wrote, this document should be corrected.

---

## 1. Weinstein — Stage Analysis

**Source:** Stan Weinstein, *Secrets for Profiting in Bull and Bear Markets* (1988), Chapters 1–2.

### What Weinstein Actually Teaches

- **AUTHOR:** Stocks move through four stages: basing (Stage 1), uptrending (Stage 2), topping (Stage 3), downtrending (Stage 4).
- **AUTHOR:** Buy in Stage 2, avoid Stage 3, sell/short Stage 4.
- **AUTHOR:** Stage 2 is characterized by price above a rising 30-week MA (equivalent to ~150-day MA).
- **AUTHOR:** Volume characteristics differ by stage — Stage 2 typically shows expansion on advances.
- **AUTHOR:** Buy on strength, not weakness (buy stocks making new highs, not falling ones).
- **AUTHOR:** Use point-and-figure charts and momentum indicators to confirm stage.

### What Wolfiero Adds on Top

- **WOLFIERO:** Reformulate "Stage 2" using EMA_50 and SMA_200 (modern equivalents; Weinstein used 30-week MA in a pre-EMA-common era).
- **WOLFIERO:** Add slope confirmation (`EMA_50(D) > EMA_50(D-10)`; `SMA_200(D) > SMA_200(D-20)`) — Weinstein describes slope qualitatively; we formalize.
- **WOLFIERO:** Add anti-flip-flop requirement (both D and D-1 confirm slope) — not in Weinstein.
- **WOLFIERO:** Add "80% of last 30 days above SMA_200" — Weinstein says "the great majority"; we quantify.
- **WOLFIERO:** Halal screening (not applicable to Weinstein's framework).

### What We Do NOT Take From Weinstein

- Point-and-figure charting (we use candles)
- Weinstein's specific momentum indicators (we don't use them)
- Weinstein's short-selling framework (we're long-only)

---

## 2. O'Neil — CANSLIM & Relative Strength

**Source:** William O'Neil, *How to Make Money in Stocks* (various editions).

### What O'Neil Actually Teaches

- **AUTHOR:** CANSLIM framework: Current earnings, Annual earnings, New product/mgmt, Supply/demand, Leader/laggard, Institutional sponsorship, Market direction.
- **AUTHOR:** "Leaders lead by wide margins" — outperformance in RS vs the market is a hallmark of true leaders.
- **AUTHOR:** RS ranking on a 1–99 scale relative to all listed stocks; top-decile RS preferred.
- **AUTHOR:** Cup-and-handle base pattern with specific proportions.
- **AUTHOR:** Buy at breakout above cup's right-side high, on above-average volume.
- **AUTHOR:** 7–8% stop-loss from purchase price (max acceptable loss).
- **AUTHOR:** Emphasis on IBD's own tools (Marketsmith, IBD 50 lists).

### What Wolfiero Adopts

- **AUTHOR-ADOPTED:** RS as leadership signal — we use the RS line vs SPY at 3-month high.
- **AUTHOR-ADOPTED:** "Leaders lead by wide margins" — we require +5% outperformance over 63 days.
- **AUTHOR-ADOPTED:** Volume confirmation on breakouts (though O'Neil suggests 50%+ above avg; we use 1.25× for PBK, 1.5× for DC20).

### What Wolfiero Adds on Top

- **WOLFIERO:** Specific 63-day lookback for RS (O'Neil uses various timeframes).
- **WOLFIERO:** Specific 5% outperformance threshold (O'Neil says "wide margins," qualitative).
- **WOLFIERO:** Ratio-line construction (`STOCK/SPY`) as the RS measure.
- **WOLFIERO:** RS line at 3-month high requirement.

### What We Do NOT Take From O'Neil

- CANSLIM fundamental analysis (Wolfiero does not use fundamentals for entry — only halal screening ratios).
- Cup-and-handle pattern as a Phase-1 setup (deferred to Phase 3+).
- O'Neil's 7–8% fixed stop-loss (we use ATR-based structural stops instead).
- IBD's proprietary tools (we may reference IBD 50 as an idea source but do not use their RS rating specifically).

---

## 3. Minervini — VCP (Volatility Contraction Pattern)

**Source:** Mark Minervini, *Trade Like a Stock Market Wizard* (2013), Chapters 4–5 (and *Think & Trade Like a Champion*, 2017).

### What Minervini Actually Teaches

- **AUTHOR:** "Trend Template" — 8 conditions for a stock to be in a proper uptrend (Chapter 4). These include: price above 150 and 200 day MAs, 150 MA above 200 MA, 200 MA trending up for at least 1 month, price at least 25% above 52-week low, price within 25% of 52-week high, RS rank ≥ 70.
- **AUTHOR:** VCP (Volatility Contraction Pattern) — a base pattern where each subsequent pullback within the base becomes smaller in percentage terms.
- **AUTHOR:** Volume "quiets down" during proper VCP formation (qualitative — no specific ratio published).
- **AUTHOR:** Entry on breakout from the final tight contraction, with volume expansion.
- **AUTHOR:** Position sizing: risk small percentage per trade (Minervini often mentions 1.25–2.5% risk per trade, higher than we use).
- **AUTHOR:** Cut losses fast (typically 5–8% max loss).
- **AUTHOR:** "Progressive exposure" — start small and scale in as a trade works.

### What Wolfiero Adopts

- **AUTHOR-ADOPTED:** The general VCP concept — a controlled pullback with quieting volume as a leadership signal.
- **AUTHOR-ADOPTED:** Buy on breakout from contraction with volume expansion.
- **AUTHOR-ADOPTED:** Cut losses fast (though we use ATR-based stops, not 5–8% flat).

### What Wolfiero Adds on Top

- **WOLFIERO:** Specific 3–12% pullback depth band (Minervini describes contraction patterns qualitatively without publishing specific %).
- **WOLFIERO:** Specific 1.0–3.5 ATR retracement band (Minervini does not use ATR-normalized pullback measurement).
- **WOLFIERO:** Specific 15-day lookback window for the pullback.
- **WOLFIERO:** Specific ≤ 7 down-days cap.
- **WOLFIERO:** Specific 0.70 volume contraction ratio (Minervini says "volume quiets down," qualitative).
- **WOLFIERO:** Specific 20 EMA / 50 EMA as support levels (Minervini uses various MAs).
- **WOLFIERO:** Specific 1.5 ATR overextension check.
- **WOLFIERO:** Specific 0.5 ATR stop buffer.
- **WOLFIERO:** Specific 15-day time stop (Minervini does not use time stops).
- **WOLFIERO:** Specific +2R partial-profit rule.

### What We Do NOT Take From Minervini

- Full 8-condition Trend Template (we use a 5-condition simplification).
- Minervini's larger position sizing (1.25–2.5% risk per trade — we start at 0.5%).
- Fundamental screening (Minervini also emphasizes earnings/revenue growth; we do not).
- Progressive exposure / pyramid adding (not in Phase 1).
- Minervini's specific chart-pattern taxonomy (double-bottoms, high-tight flags, etc.).

---

## 4. Faith / Turtle System — Donchian Breakout

**Source:** Curtis Faith, *Way of the Turtle* (2007); Michael Covel, *The Complete TurtleTrader* (2007); Curtis Faith's original Turtle Rules leak (2003).

### What the Turtle System 1 Actually Teaches

- **AUTHOR:** Buy when price breaks 20-day high (System 1 entry).
- **AUTHOR:** Exit when price breaks 10-day low (System 1 exit).
- **AUTHOR:** Alternative System 2: 55-day breakout entry, 20-day breakout exit.
- **AUTHOR:** Only take System 1 entry if the PREVIOUS System 1 breakout would have been a loser (filter to avoid over-trading in trends).
- **AUTHOR:** Position sizing based on "N" (equivalent to ATR): risk 1% of account per unit; unit size = (1% of account) / N.
- **AUTHOR:** Add units (pyramid) as price moves in your favor by ½N (up to 4 units per market).
- **AUTHOR:** Never hold through the exit signal — 10-day low exit is mandatory.
- **AUTHOR:** No time stop; no partial profits; let winners run.
- **AUTHOR:** Traded futures across ~20 markets, diversified by market and by system.
- **AUTHOR:** Turtles ran the system on their entire portfolio, expected large drawdowns (documented > 50% at times).

### What Wolfiero Adopts

- **AUTHOR-ADOPTED:** 20-day breakout entry.
- **AUTHOR-ADOPTED:** 10-day low exit.
- **AUTHOR-ADOPTED:** No time stop, no partial profits — let winners run (this is the DC20 edge).
- **AUTHOR-ADOPTED:** ATR-based position sizing philosophy (though we compute shares from risk-per-trade formula, not N-units).

### What Wolfiero Adds on Top

- **WOLFIERO:** Halal screening (Turtles traded futures — no halal question).
- **WOLFIERO:** Market regime gate (Turtles took every breakout; we filter for STRONG_BULL / NORMAL_BULL only).
- **WOLFIERO:** Top-3 sector filter (Turtles did not filter by sector).
- **WOLFIERO:** Volume ≥ 1.5× average confirmation (Turtles did not use volume).
- **WOLFIERO:** ATR volatility sanity check (0.5–2.0× 60d median) — Turtles did not have this.
- **WOLFIERO:** Stop viability check (structural stop ≤ 2 × ATR).
- **WOLFIERO:** Earnings blackout (Turtles traded futures — no earnings question).
- **WOLFIERO:** Regime downgrade tightening exit to DC_lower(5).

### What We Do NOT Take From the Turtle System

- **NOT ADOPTED:** System 2 (55-day breakout) — we do only System 1 in Phase 1.
- **NOT ADOPTED:** "Skip if previous breakout would have been a winner" filter — Faith describes this but we do not use it.
- **NOT ADOPTED:** Pyramid adding (add units on ½N moves) — we do not pyramid in Phase 1.
- **NOT ADOPTED:** Trading futures/commodities/forex — we trade only US equities.
- **NOT ADOPTED:** Turtles' position sizing (N-units) — we use standard risk-per-trade formula.
- **NOT ADOPTED:** Turtles' portfolio-wide 50%+ drawdown tolerance — we have much stricter portfolio risk limits.

---

## 5. Van Tharp — Position Sizing & Expectancy

**Source:** Van Tharp, *Trade Your Way to Financial Freedom* (2007).

### What Van Tharp Actually Teaches

- **AUTHOR:** Position sizing is the most important element of a trading system.
- **AUTHOR:** Risk a fixed % of equity per trade (typically 0.5–2%).
- **AUTHOR:** Position size formula: `shares = (equity × risk%) / (entry − stop)`.
- **AUTHOR:** R-multiple framework: express every trade's outcome in units of risk.
- **AUTHOR:** Expectancy = (win% × avg winner R) − (loss% × avg loser R).
- **AUTHOR:** Categorize systems by expectancy per opportunity (SQN = System Quality Number).

### What Wolfiero Adopts

- **AUTHOR-ADOPTED:** Position sizing formula (identical).
- **AUTHOR-ADOPTED:** R-multiple framework throughout Journal and Research Engine.
- **AUTHOR-ADOPTED:** Expectancy as the primary success metric.

### What Wolfiero Adds on Top

- **WOLFIERO:** Sample-size gated risk buckets (< 30 setups → 0.25%; 30–100 → 0.5%; etc.) — Van Tharp does not vary risk by sample size.
- **WOLFIERO:** Regime-based risk caps (0.25% in HIGH_VOL, etc.).
- **WOLFIERO:** Portfolio-level open-risk ceiling (3% max across all positions).

---

## 6. Douglas — Trading Psychology

**Source:** Mark Douglas, *Trading in the Zone* (2000).

### What Douglas Actually Teaches

- **AUTHOR:** Think in probabilities, not certainties. Any single trade is a coin flip; the edge shows over many trades.
- **AUTHOR:** Five fundamental truths: anything can happen; you don't need to know what will happen next to make money; there's a random distribution of wins and losses; an edge is nothing more than a higher probability; every moment is unique.
- **AUTHOR:** The trader's mindset (discipline, focus, confidence) is the primary determinant of results.
- **AUTHOR:** Emotional attachment to individual trade outcomes destroys long-term performance.

### What Wolfiero Adopts

- **AUTHOR-ADOPTED:** Probabilistic thinking baked into how we present expectancy and encourage the trader to interpret losing streaks.
- **AUTHOR-ADOPTED:** "Judge process, not P&L" — Constitution Rule.
- **AUTHOR-ADOPTED:** "Cash is a position" — expected system output, not failure.

### What Wolfiero Adds on Top

- **WOLFIERO:** Human-state check before trading — Douglas doesn't operationalize this.
- **WOLFIERO:** Structural kill switches on strategy decay — removes emotional decision-making from setup evaluation.
- **WOLFIERO:** Journaling protocol with prediction-vs-actual attribution.

---

## 7. What Wolfiero Contributes Beyond Any Cited Author

These elements are neither in nor easily derivable from any of the above sources:

- **The full halal integration** — Rule Zero constitutional filter, AAOIFI ratio screens, at-time-of-trade tagging, historical halal continuity.
- **The multi-engine architecture** — separation of Strategy, Risk, Portfolio, Execution engines.
- **The market regime taxonomy** with specific 4/6 signal threshold (novel).
- **The specific top-3 sector ranking algorithm** (novel).
- **The T+1 cash-account settlement enforcement** (novel operational concern).
- **The trade card format** with Why/Why-NOT severity system and human-state gate.
- **The setup isolation design** — DC20 and PBK as fully independent with separate expectancy tables and kill switches.
- **The parameter provenance discipline** — every threshold tagged CITED / STRUCTURAL / PROVISIONAL / VALIDATED.
- **The ablation testing methodology** for justifying each filter's retention.
- **The AI Research Analyst role** as context-only, never authoritative for trades.

---

## 8. Categorization Summary

| Setup / Rule Family | % from Authors | % Wolfiero Addition |
|---------------------|----------------|-----------------------|
| DC20 core (entry, exit) | 100% (Turtle System 1) | 0% |
| DC20 filters (regime, sector, volume, ATR, earnings) | 0% | 100% |
| DC20 position sizing formula | ~50% (Van Tharp) | ~50% (Wolfiero sample-size gating) |
| PBK Stage 2 concept | 100% (Weinstein) | 0% (concept); 100% (formalization) |
| PBK Relative Strength concept | 100% (O'Neil) | 0% (concept); 100% (thresholds) |
| PBK VCP / pullback concept | 100% (Minervini) | 0% (concept); 100% (specific thresholds) |
| PBK exit stack (partials, trail, time stop) | ~0% | 100% |
| Halal integration | 0% | 100% |
| Regime engine | 0% | 100% |
| Portfolio engine | 0% | 100% |
| Execution engine (T+1, slippage tracking) | 0% | 100% |
| Trade card, journal, kill switches | 0% | 100% |

---

## 9. What This Means for Testing

**Any specific numerical threshold in the Wolfiero specs (except the very few CITED ones like DC20-entry-20 and DC20-exit-10) is a PROPOSED MODIFICATION requiring validation.** They should not be trusted because they "sound like Minervini" or "come from the Turtle rules." They are our extensions.

Validation happens via:
1. Robustness testing (Spec 05 §3.4) — does performance survive ±20% parameter variation?
2. Ablation testing (Spec 05 §4A) — does the filter actually add value?
3. Walk-forward validation (Spec 05 §3.5) — does out-of-sample expectancy match backtest?
4. Live paper trading (Phase 4 in master overview) — does live match paper?

Until then: PROVISIONAL.

---

## 10. Related Docs

- Full setup math with per-parameter provenance tags: [`03-strategy-definitions.md`](./03-strategy-definitions.md)
- Rule-by-rule audit with SOURCE / INFERENCE / PROPOSED / RESEARCH QUESTION labels: [`rule-audit.md`](./rule-audit.md)
- Validation methodology: [`05-research-engine.md`](./05-research-engine.md)
- Expected behavior (framed as priors, not facts): [`expected-behavior.md`](./expected-behavior.md)
- Setup comparison with classic-vs-Wolfiero side-by-side: [`setup-comparison-dc20-vs-pullback.md`](./setup-comparison-dc20-vs-pullback.md)
