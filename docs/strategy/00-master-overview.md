# 00 — Master Overview: The Haseeb Long-Only Swing System

**Document owner:** Business analysis based on strategic dialogue between a swing-trader persona and ChatGPT quantitative researcher, iterated across four rounds and closed at a 9.5/10 design rating.

**Status:** Design locked. Ready for phased specification.

**Audience:** Product owner (Haseeb), engineering, quantitative research, review model, and any coding model executing the phased build.

---

## 1. Executive Summary

We are designing a **halal-only, long-only, cash-based, swing-trading research and execution system** to be operated by a single trader (Haseeb) with an initial $40,000 account. The system's purpose is **not** to guarantee returns. Its purpose is to:

1. **Preserve capital first**, generate risk-adjusted returns second.
2. **Enforce halal compliance** as a hard, non-overridable filter on every trade decision.
3. **Discover whether a well-defined swing setup has positive out-of-sample expectancy**, then execute it with discipline.
4. **Remove the trader from decisions where discipline routinely fails** (entry timing, position sizing, exit management, revenge trading).
5. **Keep the human as the final approver** of every discretionary new entry — never fully autonomous.

The system is deliberately **survival-first**. It is designed to still be operational after any single quarter, any single drawdown, any single strategy decay event, any single provider outage, and any single week of the trader being emotionally or physically compromised.

---

## 2. Context: Why This Design Exists

The trader (Haseeb) approached the problem initially with three flawed assumptions typical of retail entrants:

1. That $1,000/week from $40K (~130% annualized) was a reasonable baseline target.
2. That a single "best strategy" or indicator combination could be discovered.
3. That an AI/LLM could be trusted to select trades directly.

Across four rounds of dialogue between a swing-trader persona and a quantitative researcher persona, the following corrections were established:

| Original Assumption | Corrected Position |
|---------------------|--------------------|
| $1,000/week is realistic | 15–25% annualized is realistic; 130% is fantasy or leverage-blowup |
| Find the best strategy | Trade two isolated setups in parallel (DC20 breakout + Pullback-to-EMA) and let live data determine which fits the trader best |
| AI picks trades | AI provides context and statistical evidence; rules decide; human approves |
| Full deployment of $40K | Paper trade 3 months → $5K live 3 months → scale only if live matches paper |
| Complex indicator soup | Simple, mathematically-defined pipeline where complexity lives *under the hood* in research, not in the decision tree |

This document set is the output of that dialogue, formalized into an executable specification.

---

## 3. Design Principles (Non-Negotiable)

These principles govern every spec that follows. If any spec appears to contradict a principle, the principle wins.

> **Note on "active themes":** as of docs revision, "active themes" (e.g., AI infrastructure, GLP-1, nuclear) are **NOT** an algorithmic system filter. They are a trader-annotated overlay used for watchlist prioritization and portfolio concentration limits. Themes lack rigorous algorithmic definition; treating them as a hard filter introduces ambiguity that two implementations would resolve differently. See Spec 03 §3.8 for the formal definition of this demotion.

### P1 — Halal Is Rule Zero
No trade proceeds without at-time-of-trade halal verification against the configured Shariah standard. This is a hard filter, not a warning. Applies to live trading AND historical research.

### P2 — Capital Preservation Beats Return Chasing
The system's objective is *maximizing risk-adjusted expectancy subject to drawdown constraints*, not maximizing returns. Return targets do not exist inside the software.

### P3 — Rules Decide, AI Advises, Human Approves
The LLM produces context prose. Statistical models produce conditional expectancy. Deterministic rules produce trade candidates. The human clicks approve. No layer trades autonomously.

### P4 — Every Number Has Provenance
No threshold, weight, or parameter enters the system without a documented source: prior research citation, structural argument, or robustness-tested justification. No numbers "because they backtested well."

### P5 — Simple Decision Tree, Complex Research Underneath
The trade decision path must be human-readable and human-auditable. The complexity lives in the research engine that produces the parameters, not in the decision path that consumes them.

### P6 — Cash Is a Valid, Expected Output
"No trade tonight," "cash day today," "flat for the week" are normal, healthy system outputs — not failure modes. The system is allowed to say NO to itself.

### P7 — Bad Data Vetoes Trades, Absolutely
Stale, divergent, or unverifiable data produces a hard NO on the trade. No exceptions.

### P8 — Setups Are Hypotheses on a Schedule
Between scheduled reviews, the trader executes the rules with conviction. On scheduled reviews (monthly, quarterly), the rules are re-evaluated against fresh data. **The trader does not re-litigate the strategy mid-week.**

### P9 — Every Threshold Is Configurable, Not Sacred
Numeric thresholds (VIX cutoffs, EMA periods, ATR multipliers, sample-size floors) are configuration, not code. Changing them triggers a re-run of validation, not a code change.

### P10 — Survival Above All
No single failure — bad trade, bad week, bad month, provider outage, model deprecation, life event — should be able to remove the system from operation. Design for graceful degradation, not perfection.

---

## 4. The Master Pipeline

Every trade candidate flows through this pipeline. Each gate can produce PASS, WARN, or VETO. Any single VETO terminates evaluation.

```
                    ALL US-LISTED EQUITIES
                              │
                              ▼
                    ┌──────────────────┐
                    │ HALAL ELIGIBILITY│ ── HARD VETO
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  LIQUIDITY GATE  │ ── HARD VETO
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   DATA HEALTH    │ ── HARD VETO
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  MARKET REGIME   │
                    │   CLASSIFIER     │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  SECTOR & THEME  │
                    │   LEADERSHIP     │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  STOCK QUALITY   │
                    │  (Stage 2 + RS)  │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  SETUP ENGINE    │ (Strategy)
                    │  (Pullback etc.) │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  STATISTICAL     │
                    │  VALIDATION      │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   RISK ENGINE    │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ PORTFOLIO ENGINE │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   TRADE CARD     │
                    │  (Why / Why-NOT) │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  HUMAN-STATE     │
                    │     CHECK        │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  EXECUTION       │
                    │    ENGINE        │
                    └──────────────────┘
                              │
                              ▼
              BUY  /  WATCH  /  REJECT  /  CASH DAY
                              │
                              ▼
                    ┌──────────────────┐
                    │  JOURNAL &       │
                    │  ATTRIBUTION     │
                    └──────────────────┘

     ┌──────────────────────────────────────────────┐
     │           RESEARCH ENGINE (underneath)       │
     │  Backtesting · Walk-Forward · Expectancy     │
     │  Regime-conditional · Decay Detection        │
     │  Sample-Size Analysis · Robustness           │
     └──────────────────────────────────────────────┘
```

---

## 5. The Four Engines

Deliberately separated because they answer four different questions:

| Engine | Question | Owns |
|--------|----------|------|
| **Strategy** | Is there an edge here? | Setup detection, entry trigger, exit rules |
| **Risk** | How much capital should this trade expose? | Position sizing, stop distance validation, per-trade risk |
| **Portfolio** | Given what we already hold, should we take this? | Correlation, sector concentration, open risk budget |
| **Execution** | How do we actually fill this order without bleeding edge? | Order type, timing, slippage tracking, partial fills |

They interact but they do not blend. Each has its own spec (rolled up into Spec 07).

---

## 6. The Ten Specifications

| # | Spec | Owns | Phase |
|---|------|------|-------|
| 01 | **Trading Constitution** | Immutable rules, capital constraints, human authority | 1 |
| 02 | **Data & Halal Universe** | Providers, quality gates, halal standard, at-time-of-trade tagging, corporate actions | 1 |
| 03 | **Strategy Definitions** | Mathematical setup definitions with provenance, entry and exit policies | 1 |
| 04 | **Backtester** | Realistic fills, slippage, gaps, corporate actions, survivorship-adjusted universe | 2 |
| 05 | **Research Engine** | Expectancy tables, regime-conditional stats, confidence intervals, decay detection | 2 |
| 06 | **ML / Statistical Layer** | Evaluators only, feature engineering, no-leakage rules | 2 |
| 07 | **Four Engines (Regime + Risk + Portfolio + Execution)** | The runtime decision core | 3 |
| 08 | **AI Research Analyst** | LLM context prose from filings, earnings, news — never a numerical vote | 3 |
| 09 | **Trade Card & Alerting** | Card format with Why / Why-NOT severity, human-state check, Telegram delivery | 3 |
| 10 | **Journal & Attribution** | Trade lifecycle logging, prediction-vs-actual, drift detection, quarterly review outputs | 3 |

---

## 7. Phased Build Order

**Do not proceed to phase N+1 until phase N's acceptance criteria are met and reviewed by the strongest available reasoning model.**

### Phase 1 — Foundation (Specs 01, 02, 03)
Weeks 1–4. Constitution, data, halal universe, and mathematical strategy definitions for **two parallel setups** (DC20 breakout and Pullback-to-EMA). **Halt after Spec 03 for formal review.** Spec 03 dictates what everything downstream must test — if it's wrong, everything else compounds the error.

### Phase 2 — Research Infrastructure (Specs 04, 05, 06)
Weeks 5–10. Backtester, research engine, statistical evaluators. **Purpose: determine whether the primary hypothesis (pullback-to-EMA in Stage-2 leaders) has demonstrable positive out-of-sample expectancy.** If it doesn't, stop and reconsider before building runtime.

### Phase 3 — Runtime & Delivery (Specs 07, 08, 09, 10)
Weeks 11–16. Four-engine runtime, LLM analyst, trade card, alerting, journal. This is where the paper-trading system becomes real.

### Phase 4 — Paper Trading (3 months minimum)
Weeks 17–29. System runs live but no real orders. Every trade card produces a hypothetical position; journal tracks all metrics. **Success criterion: live paper results match backtest expectancy within confidence intervals.**

### Phase 5 — Small Live ($5K, 3 months minimum)
Weeks 30–42. Real orders, real fills, real slippage. Continue journaling. Compare live vs paper for execution drift.

### Phase 6 — Scale to Full $40K
Only after Phases 4 and 5 pass their acceptance criteria. Never a "let's just try it" scale-up.

---

## 8. Success Criteria & KPIs

**The system does not have a return target.** It has quality-of-execution targets. Returns are an emergent property.

### Primary KPIs (measured continuously)

| KPI | Target | Definition |
|-----|--------|------------|
| Positive expectancy | > 0 in current regime | Rolling 12-month expected R per trade |
| Profit factor | > 1.3 | Gross winners / gross losers |
| Max drawdown | ≤ 15% of high-water mark | Peak-to-trough on equity curve |
| Sortino ratio | > 1.0 | Downside-adjusted risk return |
| Win rate | 40–65% acceptable | Wins / total trades (with sufficient R:R) |
| Average R (winner) | ≥ 1.5R | Average magnitude of wins |
| Average R (loser) | ≤ 1.0R | Average magnitude of losses |
| Time in market | 20–70% | Prevents both under- and over-trading |
| Turnover | Sane | Trades per month; flags excess churn |
| Slippage vs modeled | ≤ 0.1% divergence | Execution honesty |
| Setup decay | No 3-month negative streak in rolling expectancy | Kill-switch trigger |
| Per-regime performance | Positive in favorable regimes | Regime-conditional stat |

### Secondary Indicators (reviewed monthly)

- Rule adherence rate (did we follow the plan?)
- Journal completeness (100% required)
- Data quality incidents (target: 0 that reached BUY)
- Halal reclassification events (tracked, never overridden)

---

## 9. Explicit Non-Goals

The system will NOT:

1. Guarantee any specific return
2. Day trade or scalp
3. Short sell
4. Use margin or leverage
5. Trade options (initially)
6. Trade futures, forex, crypto, or other instruments
7. Trade haram-classified stocks under any circumstance
8. Automate final trade approval (human clicks BUY)
9. Predict prices or make forward-looking claims
10. Optimize thresholds by scanning parameter grids for max-CAGR
11. Include return targets in the algorithm's objective function
12. Continue trading through data outages or halal-status uncertainty
13. Take new discretionary entries when the trader is emotionally or physically compromised

---

## 10. Glossary

| Term | Meaning |
|------|---------|
| **R** | One unit of risk. If risk-per-trade is $200, then +1R = +$200 |
| **Stage 2** | Weinstein classification: uptrend phase — price above rising 50 and 200 MA |
| **Halal** | Shariah-compliant per configured standard (default: AAOIFI as implemented by Zoya) |
| **Expectancy** | (Win% × Avg Win) − (Loss% × Avg Loss), expressed in R |
| **Regime** | Classification of current market: Strong Bull / Normal Bull / Chop / Bear / High-Vol |
| **RS** | Relative Strength vs SPY (or sector benchmark) |
| **ATR** | Average True Range; rolling volatility measure |
| **VCP** | Volatility Contraction Pattern (Minervini) |
| **Setup** | A specific, mathematically-defined trade configuration |
| **Trade card** | Human-readable pre-trade briefing showing thesis, risks, historical stats, decision |
| **Kill switch** | Automatic pause of a strategy based on decay conditions |
| **At-time-of-trade** | Historical evaluation uses the halal/data state that existed on the trade date, not today's |
| **VETO** | Terminal NO — no downstream evaluation, no trade |

---

## 11. Change Control

Any modification to a numbered spec requires:

1. Written proposal describing what changes and why
2. Impact analysis on downstream specs
3. Re-validation trigger (backtest / walk-forward / paper) if the change alters trading behavior
4. Review by the strongest available reasoning model
5. Human (Haseeb) approval to merge

**The Trading Constitution (Spec 01) is immutable during any active paper or live trading window.** Constitutional changes require the system to be flat first.

---

## 12. Document Map

- **Spec 01** → [`01-trading-constitution.md`](./01-trading-constitution.md)
- **Spec 02** → [`02-data-and-halal-universe.md`](./02-data-and-halal-universe.md)
- **Spec 03** → [`03-strategy-definitions.md`](./03-strategy-definitions.md)
- **Spec 04** → [`04-backtester.md`](./04-backtester.md)
- **Spec 05** → [`05-research-engine.md`](./05-research-engine.md)
- **Spec 06** → [`06-ml-statistical-layer.md`](./06-ml-statistical-layer.md)
- **Spec 07** → [`07-four-engines.md`](./07-four-engines.md)
- **Spec 08** → [`08-ai-research-analyst.md`](./08-ai-research-analyst.md)
- **Spec 09** → [`09-trade-card-and-alerting.md`](./09-trade-card-and-alerting.md)
- **Spec 10** → [`10-journal-and-attribution.md`](./10-journal-and-attribution.md)
- **Trader guide — DC20 vs Pullback side-by-side** → [`setup-comparison-dc20-vs-pullback.md`](./setup-comparison-dc20-vs-pullback.md)
- **Expected statistical behavior per setup** → [`expected-behavior.md`](./expected-behavior.md)
- **Rule-by-rule audit table** → [`rule-audit.md`](./rule-audit.md)
- **Source attribution — authors vs Wolfiero additions** → [`source-attribution.md`](./source-attribution.md)
- **Final coherence check + trader green-light** → [`FINAL-CHECK.md`](./FINAL-CHECK.md)
- **Manual trading learning guide (HTML, printable)** → [`learning-guide-manual-trading.html`](./learning-guide-manual-trading.html)
- **Wall-mounted cheat sheet (HTML, printable)** → [`cheat-sheet-wall.html`](./cheat-sheet-wall.html)
