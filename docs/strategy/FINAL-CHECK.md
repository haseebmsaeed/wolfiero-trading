# FINAL COHERENCE CHECK — Ready for Manual Paper Trading

**Purpose:** confirm all `docs/strategy/` documentation is internally consistent, coherent, and ready for the trader (Haseeb) to begin manual paper trading with confidence that no doc contradicts another.

**Status:** ✅ PASSED as of the coherence review completed at doc revision.

---

## 1. Trade Type Confirmation (What Kind of Trading This Is)

Verified across **all** documents:

- ✅ **LONG-ONLY.** No document describes or permits short-selling. The Constitution (Spec 01 §2.3) hard-bans short-selling and every downstream doc respects this.
- ✅ **CASH-BASED.** No document permits margin, borrowing, or leverage. Spec 01 §2.3 hard-bans margin; Spec 07 §5.8 enforces T+1 cash settlement rules.
- ✅ **US-LISTED COMMON STOCK ONLY.** No options, no futures, no forex, no crypto, no ETFs for trading (ETFs only used for sector leadership analysis).
- ✅ **HALAL RULE ZERO** enforced across every entry gate in every setup.
- ✅ **BUY-THEN-SELL MECHANIC.** You use cash to buy shares → hold shares → sell shares for cash. Profit when exit price > entry price. This is the ONLY way to make money in this system.

**Note on "buy low, sell high":** both setups are long positions aiming to exit higher than entry. DC20 buys at a 20-day high (a "high" in absolute terms, but expected to go higher); PBK buys a pullback in an uptrend (a temporary "low" within an ongoing trend). **Neither is a short. Neither uses leverage. Both are cash-out-to-buy, sell-later-for-cash long trades.**

---

## 2. Cross-Doc Numerical Consistency (Verified)

| Rule | Value | Source | Verified in |
|------|-------|--------|-------------|
| Account size | $40,000 | Spec 01 §2.1 | All docs |
| Reserve | $5K–$10K | Spec 01 §2.1 | All docs |
| Per-trade risk (starting) | 0.5% ($200) | Spec 01 §4.1 | 03, 05, 07, cheat sheet, learning guide, expected-behavior, setup-comparison, rule-audit |
| Per-trade risk (established) | 1.0% ($400) | Spec 01 §4.1 | All docs |
| Total open risk cap | ≤ 3% ($1,200) | Spec 01 §4.3 (reconciled from earlier "2-3%" range) | All docs |
| Target open risk (learning) | 2% | Spec 01 §4.3 | Referenced consistently |
| Max simultaneous positions | 6 (across both setups) | Spec 01 §4.3 | 01, 07, cheat sheet, comparison, rule-audit |
| Max per sector | 2 | Spec 01 §4.3 | All docs |
| Max per theme | 1 | Spec 01 §4.3 | All docs |
| Max position size | 10% of account | Spec 03 §4.4 | All docs |
| Sample-size buckets | <30 / 30-100 / 100-300 / 300+ → 0.25 / 0.50 / 0.75 / 1.0% | Spec 01 §4.2 | 01, 05, 07, rule-audit |
| Universe floors | $10 price, $1B mcap, $20M ADV | Spec 01 §2.4 | 01, 02, cheat sheet |
| Regime taxonomy | STRONG_BULL / NORMAL_BULL / CHOP / HIGH_VOL / BEAR | Spec 07 §2.2 | 05, 07, 09, comparison |
| Earnings blackout | 15 days out for holding decisions; 3 days out for exit | Spec 03 §5.1 | All docs |
| Halal standard (default) | AAOIFI via Zoya | Spec 01 §3.2 | 01, 02 |
| T+1 settlement enforcement | Cash account | Spec 07 §5.8 | 01, 07 |

---

## 3. Setup Definitions (Verified Consistent)

### PBK (`PULLBACK_TO_EMA_STAGE2`)
- 7-check filter matches across Spec 03 §4.1, setup-comparison §3, cheat sheet §PBK, learning guide §2.3
- Exit stack (structural stop → +2R partial → 20 EMA trail → 15-day time stop → regime/halal/earnings exits) matches across Spec 03 §5.1, setup-comparison §5, cheat sheet, learning guide §2.5
- Notification tag `[PBK]` used consistently in Spec 09 and setup-comparison

### DC20 (`DONCHIAN_20_BREAKOUT`)
- 5-check filter matches across Spec 03 §4A.1, setup-comparison §3, cheat sheet §DC20, learning guide §3.3
- Exit rule (trend exit at DC_lower(10); NO time stop; NO partial profits) matches across Spec 03 §5A.1, setup-comparison §5, cheat sheet, learning guide §3.5
- **Look-ahead convention** (today NOT in the reference channel) affirmed in Spec 03 §3.0 warning box and §4A.0 note; matches TradingView's default Donchian(20)
- Notification tag `[DC20]` used consistently

---

## 4. Terminology & Attribution (Verified)

- ✅ **"Two parallel setups"** language consistent — no lingering "primary/sole setup" text (fixed in this pass)
- ✅ **"Active themes"** consistently framed as trader overlay (not algorithmic) — Spec 03 §3.8 authoritative, master overview + comparison + rule-audit all aligned
- ✅ **"Top-3 sectors"** consistently defined algorithmically per Spec 03 §3.7 (equal-weighted 1M+3M rank, 3M tie-breaker)
- ✅ **PROVISIONAL / CITED / STRUCTURAL / VALIDATED tags** applied per Spec 03 §3.0 legend
- ✅ **Classic-vs-Wolfiero distinction** made explicit in setup-comparison §1A and source-attribution.md
- ✅ **DC20 filter additions (regime, sector, volume, ATR, earnings)** correctly attributed to Wolfiero, NOT Turtle system
- ✅ **PBK numerical thresholds (3-12%, 0.70 vol, 0.5/1.5 ATR)** correctly attributed to Wolfiero heuristics inspired by Minervini concepts, NOT verbatim Minervini rules

---

## 5. Trader-Facing Consistency (What You'll Actually Read)

The two documents you will actually consult during paper trading:

### Learning Guide (`learning-guide-manual-trading.html`)
- ✅ Long-only, cash-only, no-shorts, no-margin box added at top
- ✅ Halal check at moment of trade emphasized
- ✅ Gap-through-stop warning present
- ✅ 7-check PBK filter matches Spec 03
- ✅ 5-check DC20 filter matches Spec 03
- ✅ Removed unsupported "70% of fake breakouts" claim
- ✅ Win rates and losing streaks framed as priors, not facts

### Cheat Sheet (`cheat-sheet-wall.html`)
- ✅ Header now reads "HALAL · LONG-ONLY CASH · NO MARGIN · NO SHORTS"
- ✅ All numeric rules match Constitution
- ✅ PBK and DC20 exit stacks match Spec 03
- ✅ Portfolio limits match Spec 01
- ✅ Position sizing formula matches Spec 03 §4.4

### Setup Comparison (`setup-comparison-dc20-vs-pullback.md`)
- ✅ Long-only clarification added at top
- ✅ Classic-vs-Wolfiero section (§1A) added
- ✅ All performance numbers labeled as PRIORS, not facts
- ✅ Portfolio limits match Constitution
- ✅ Notification catalog matches Spec 09

### Expected Behavior (`expected-behavior.md`)
- ✅ All statistical envelopes labeled as priors/hypotheses, not facts
- ✅ Investigation gates (30+ trades for PBK, 50+ for DC20) prevent premature strategy abandonment
- ✅ Emotional warning signs journaled weekly per protocol

---

## 6. Known Open Research Questions (Documented, Not Fixed)

These are legitimate research questions that will only be resolved by testing. They are documented in the relevant specs and do NOT block manual paper trading:

- **DC20 earnings blackout tension:** does closing before earnings destroy the fat-tail payoff DC20 depends on? (Documented in `rule-audit.md` §4.1)
- **Regime/sector filter ablation:** does adding regime + sector + volume filters to DC20 improve out-of-sample expectancy or over-filter? (Deferred to Spec 05 §4A ablation testing)
- **Regime score threshold 4/6:** is this statistically meaningful or arbitrary? (Marked PROVISIONAL in Spec 07 §2.4; Spec 05 story 5.12 will analyze signal independence)
- **PBK-specific parameters (3-12% pullback, 0.70 vol ratio, etc.):** are these optimal or heuristic? (Marked PROVISIONAL; Spec 05 §3.4 robustness testing will validate)
- **Swing high/low algorithm precision:** current specs use it informally in PBK-E-02 and PBK-X-03; needs formal detector (5-bar local min/max as reasonable default, TBD)

**These are honest gaps.** They do not invalidate paper trading — they define what future evidence will refine.

---

## 7. What's Ready and What's Not

### ✅ Ready for Manual Paper Trading (Now)

- Constitution (Spec 01) — immutable rules understood
- Data & Halal Universe (Spec 02) — trader knows which stocks are eligible
- Strategy Definitions (Spec 03) — PBK and DC20 mathematically defined
- Setup Comparison — daily/weekly manual protocol
- Learning Guide (HTML) — 4-week structured curriculum + trade mechanics
- Cheat Sheet (HTML) — wall-mounted daily reference
- Expected Behavior — statistical priors for interpreting live results
- Rule Audit — full accountability table for every rule
- Source Attribution — rigorous separation of authors vs Wolfiero

### 🟡 Ready When We Build the App (Phase 2+)

- Backtester (Spec 04)
- Research Engine (Spec 05)
- ML/Statistical Layer (Spec 06)
- Four Engines runtime (Spec 07)
- AI Research Analyst (Spec 08)
- Trade Card & Alerting notifications (Spec 09)
- Journal automation (Spec 10)

**These specs are complete but not yet implemented.** You do not need them for manual paper trading. When you're ready to build, they're waiting.

---

## 8. The Manual Paper-Trading Green Light

Everything you need to start paper trading manually is now in these three documents:

1. **Print/read:** [`learning-guide-manual-trading.html`](./learning-guide-manual-trading.html) — 20 pages, cover to cover
2. **Print/pin:** [`cheat-sheet-wall.html`](./cheat-sheet-wall.html) — one-page wall reference
3. **Reference during trades:** [`setup-comparison-dc20-vs-pullback.md`](./setup-comparison-dc20-vs-pullback.md) + [`expected-behavior.md`](./expected-behavior.md)

**Suggested sequence for the trader (Haseeb):**

Week 1:
- Read `learning-guide-manual-trading.html` cover to cover
- Print `cheat-sheet-wall.html` — pin above monitor
- Skim `setup-comparison-dc20-vs-pullback.md` — understand the two setups side-by-side
- Skim `expected-behavior.md` — understand what "normal" looks like
- Read foundational chapters of Minervini + start Faith's Turtle book (per learning guide §4)

Weeks 2–4:
- Continue reading (Faith, Douglas, Minervini)
- Practice the 7-check PBK filter + 5-check DC20 filter on 5 stocks daily
- Do NOT paper-trade yet — internalize the checks first

Weeks 5–8 (start paper trading):
- Sunday: run full planning session per learning guide §2.3 and §3.3
- Weekdays: 15-min morning ritual per learning guide §2.5 and §3.5
- Journal every trade per learning guide §5
- Compare live results against `expected-behavior.md` priors
- Do NOT investigate the strategy on small samples (< 20 trades)

Weeks 9–16:
- Continue paper trading, accumulate 30+ PBK trades and 50+ DC20 trades
- Monthly review per journal protocol
- Only THEN begin serious statistical evaluation

Post-Week-16 review:
- Sit down together, review the journal
- Decide: continue both setups, drop one, adjust parameters
- If evidence supports live trading, begin Phase 5 (small live $5K)

---

## 9. If You Notice Documentation Inconsistency During Trading

**Trust this hierarchy** (source of truth in descending order):

1. **Constitution (Spec 01)** — immutable; if anything else contradicts it, Constitution wins
2. **Setup mathematics (Spec 03)** — for any question about "how is this rule computed"
3. **Setup comparison + Learning guide + Cheat sheet** — trader-facing operational
4. **Everything else** — supporting docs

If you find a real contradiction: journal it, note the file/line, and flag it for the next review. Do NOT resolve it by "picking one" mid-trade — that path leads to inconsistent execution. Trust the highest-priority doc in the hierarchy above.

---

## 10. Documentation Index (Master List)

**Constitution & Foundations:**
- [`00-master-overview.md`](./00-master-overview.md)
- [`01-trading-constitution.md`](./01-trading-constitution.md)
- [`02-data-and-halal-universe.md`](./02-data-and-halal-universe.md)

**Strategy Definitions:**
- [`03-strategy-definitions.md`](./03-strategy-definitions.md)

**Research & Runtime Specs (Phase 2+):**
- [`04-backtester.md`](./04-backtester.md)
- [`05-research-engine.md`](./05-research-engine.md)
- [`06-ml-statistical-layer.md`](./06-ml-statistical-layer.md)
- [`07-four-engines.md`](./07-four-engines.md)
- [`08-ai-research-analyst.md`](./08-ai-research-analyst.md)
- [`09-trade-card-and-alerting.md`](./09-trade-card-and-alerting.md)
- [`10-journal-and-attribution.md`](./10-journal-and-attribution.md)

**Trader-Facing (Manual Paper Trading):**
- [`setup-comparison-dc20-vs-pullback.md`](./setup-comparison-dc20-vs-pullback.md)
- [`expected-behavior.md`](./expected-behavior.md)
- [`learning-guide-manual-trading.html`](./learning-guide-manual-trading.html)
- [`cheat-sheet-wall.html`](./cheat-sheet-wall.html)

**Audit & Attribution:**
- [`rule-audit.md`](./rule-audit.md)
- [`source-attribution.md`](./source-attribution.md)

**This document:**
- [`FINAL-CHECK.md`](./FINAL-CHECK.md) — you are here

---

## 11. Signature Line

Documentation coherence: ✅ PASSED
Trader long-only, cash-only affirmation: ✅ EXPLICIT throughout
Numeric consistency: ✅ VERIFIED
Setup definitions coherent across all docs: ✅ VERIFIED
Attribution honest (authors vs Wolfiero): ✅ VERIFIED
Ready for manual paper trading: ✅ YES

**Go trade on paper. Journal every trade. See you in 8 weeks with 20+ trades in the log.**
