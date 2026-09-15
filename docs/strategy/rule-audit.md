# Rule-by-Rule Audit — PBK and DC20

**Purpose:** enumerate every rule in the current strategy specification with its provenance, objectivity, testability, and known biases. This is the Phase-1 output requested by ChatGPT's Strategy Foolproofing prompt.

**Convention:**
- **SOURCE RULE** — directly supported by supplied source material (Weinstein, Minervini, O'Neil, Faith)
- **INFERENCE** — logically inferred from supplied material
- **PROPOSED MODIFICATION** — my recommendation
- **RESEARCH QUESTION** — must be tested rather than assumed

**Confidence:**
- **High** — well-established in literature, structurally sound
- **Medium** — reasonable heuristic, requires validation
- **Low** — provisional; likely to change after live evidence

---

## 1. PBK — Pullback to EMA Rules

| Rule ID | Category | Rule (Concise) | Source | Objective? | Ambiguous? | Testable? | Bias | Confidence |
|---------|----------|----------------|--------|------------|------------|-----------|------|------------|
| PBK-U-01 | Universe | Halal-compliant per configured standard | Constitution §3 | Yes | No | Yes | None | High |
| PBK-U-02 | Universe | Price ≥ $10, mcap ≥ $1B, ADV ≥ $20M, ≥ 6mo history, optionable | Spec 01 §2.4 | Yes | No | Yes | None | High |
| PBK-U-03 | Universe | Not recent IPO (< 6 mo), not recent deSPAC (< 6 mo) | Spec 01 §2.3 | Yes | No | Yes | None | High |
| PBK-R-01 | Regime | Market regime ∈ {STRONG_BULL, NORMAL_BULL} | Spec 07 §2 | Yes | No | Yes | Look-ahead risk if regime uses today's bar | Medium |
| PBK-R-02 | Regime | Stock in top-3 sectors by combined 1M+3M rank | Spec 03 §3.7 | Yes | No | Yes | None | Medium |
| PBK-E-01 | Entry-Filter | Stage 2 (5-condition test with anti-flip-flop) | Weinstein 1988, tightened | Yes | No | Yes | None | Medium |
| PBK-E-02 | Entry-Filter | Higher highs + higher lows over last 3 swings | INFERENCE from Weinstein Stage 2 | **Partial** — "swing" definition needs precision | **Yes — swing detection algorithm unspecified** | Yes (after definition) | None | Low |
| PBK-E-03 | Entry-Filter | RS line > 3-mo high AND stock 63d return > SPY 63d return + 5% | O'Neil CANSLIM adapted | Yes | No | Yes | None | Medium |
| PBK-E-04 | Entry-Filter | Pullback exists (§3.3): 3–12% off high, 1.0–3.5 ATR, ≤ 15 days, above 50 EMA, ≤ 7 down days | Minervini VCP adapted | Yes | No | Yes | None | Medium |
| PBK-E-05 | Entry-Filter | Volume dry-up: pullback vol / prior 20d avg ≤ 0.70 | Minervini VCP | Yes | No | Yes | None | Medium |
| PBK-E-06 | Entry-Filter | Support touched: 20 EMA or 50 EMA | INFERENCE | Yes | No | Yes | None | Medium |
| PBK-E-07 | Entry-Filter | Distance from Close to 20 EMA ≤ 1.5 × ATR (not overextended) | PROPOSED MODIFICATION | Yes | No | Yes | None | Low |
| PBK-E-08 | Entry-Filter | No earnings within 15 trading days | PROPOSED MODIFICATION | Yes | No | Yes | None | Medium |
| PBK-T-01 | Trigger | Close > High(D-1) AND Volume > 1.25 × 20d avg vol | INFERENCE + PROPOSED | Yes | No | Yes | None | Low |
| PBK-T-02 | Trigger | Order type: Buy-stop @ High(D-1) + $0.05, GFD | PROPOSED MODIFICATION | Yes | No | Yes | None | Medium |
| PBK-S-01 | Stop | Structural: `Low(pullback) − 0.5 × ATR(14)` | PROPOSED MODIFICATION | Yes | No | Yes | None | Medium |
| PBK-S-02 | Stop | Viability veto: if (entry − stop) > 2.0 × ATR → skip | PROPOSED MODIFICATION | Yes | No | Yes | None | Medium |
| PBK-P-01 | Position Size | `shares = floor(risk_$ / (entry − stop))`, risk = 0.5–1% acct | Van Tharp risk-of-ruin | Yes | No | Yes | None | High |
| PBK-P-02 | Position Size | Max 10% account per position | Constitution §4 | Yes | No | Yes | None | High |
| PBK-P-03 | Position Size | Sample-size gated (Spec 05 §3.2): <30 setups → 0.25%; 30–100 → 0.5%; 100–300 → 0.75%; 300+ → 1% | PROPOSED MODIFICATION | Yes | No | Yes | None | Low |
| PBK-X-01 | Exit | Structural stop (PBK-S-01) | — | Yes | No | Yes | Gap-through risk | High |
| PBK-X-02 | Exit | At +2R: sell 1/3, move rest stop to breakeven | PROPOSED MODIFICATION | Yes | No | Yes | None | Low |
| PBK-X-03 | Exit | Trail rest: `MIN(EMA_20, most-recent-HL − 0.5 × ATR)` | PROPOSED MODIFICATION | **Partial** — "HL" definition needs precision | **Yes — swing-low algorithm unspecified** | Yes (after def) | None | Low |
| PBK-X-04 | Exit | Time stop: close if unrealized R < 1.0 after 15 trading days | PROPOSED MODIFICATION | Yes | No | Yes | None | Low |
| PBK-X-05 | Exit | Regime downgrade → CHOP: sell 1/2, tighten trail | PROPOSED MODIFICATION | Yes | No | Yes | None | Low |
| PBK-X-06 | Exit | Halal reclassification → close at next open | Constitution | Yes | No | Yes | None | High |
| PBK-X-07 | Exit | Earnings within 3 days → close before | PROPOSED MODIFICATION | Yes | No | Yes | None | Medium |

---

## 2. DC20 — Donchian 20 Breakout Rules

| Rule ID | Category | Rule (Concise) | Source | Objective? | Ambiguous? | Testable? | Bias | Confidence |
|---------|----------|----------------|--------|------------|------------|-----------|------|------------|
| DC20-U-01 | Universe | Same as PBK-U-01 through U-03 | See PBK | Yes | No | Yes | None | High |
| DC20-R-01 | Regime | Regime ∈ {STRONG_BULL, NORMAL_BULL} — DC20 does NOT trade CHOP/HIGH_VOL/BEAR | INFERENCE + PROPOSED | Yes | No | Yes | Regime look-ahead risk | Medium |
| DC20-R-02 | Regime | Top-3 sector (same rule as PBK-R-02) | Spec 03 §3.7 | Yes | No | Yes | None | Medium |
| DC20-E-01 | Entry-Filter | `Close(D) > MAX(High(D-1)…High(D-20))` — TODAY EXCLUDED from reference channel | Donchian 1950s / Turtle System 1 | Yes | No — clarified in Spec 03 §3.0 warning | Yes | **CRITICAL: look-ahead if implemented wrong** | High |
| DC20-E-02 | Entry-Filter | Volume ≥ 1.5 × 20d avg | PROPOSED MODIFICATION | Yes | No | Yes | None | Low |
| DC20-E-03 | Entry-Filter | ATR sanity: 0.5 × 60d median ≤ ATR(14) ≤ 2.0 × 60d median | PROPOSED MODIFICATION | Yes | No | Yes | None | Low |
| DC20-E-04 | Entry-Filter | Stop viability: (Close − DC_lower(10)) ≤ 2.0 × ATR | PROPOSED MODIFICATION | Yes | No | Yes | None | Medium |
| DC20-E-05 | Entry-Filter | No earnings within 15 trading days | PROPOSED MODIFICATION | Yes | No | Yes | Reduces trend-following payoff | Medium |
| DC20-T-01 | Trigger | Entry Mode A (close of D) OR Mode B (open of D+1); configurable | INFERENCE from Turtle rules | Yes | No | Yes | Mode A has slippage risk; Mode B has gap risk | Medium |
| DC20-S-01 | Stop | `stop = DC_lower(10)` at time of entry, FIXED (not sliding) | Turtle System 1 (Faith 2007) | Yes | No | Yes | None | High |
| DC20-P-01 | Position Size | Same formula as PBK-P-01, PBK-P-02, PBK-P-03 | See PBK | Yes | No | Yes | None | High |
| DC20-X-01 | Exit | Trend exit: `Close(D) < MIN(Low(D-1)…Low(D-10))` — TODAY EXCLUDED | Turtle System 1 | Yes | No | Yes | Look-ahead risk if wrong | High |
| DC20-X-02 | Exit | Regime → CHOP: sell 1/2, tighten exit to `DC_lower(5)` | PROPOSED MODIFICATION | Yes | No | Yes | None | Low |
| DC20-X-03 | Exit | Halal reclassification → close at next open | Constitution | Yes | No | Yes | None | High |
| DC20-X-04 | Exit | Earnings within 3 days → close before | PROPOSED MODIFICATION | Yes | No | Yes | **Destroys trend-following payoff distribution** — see §4 | Medium |
| DC20-X-05 | Exit | NO time stop | Turtle System 1 (letting winners run IS the edge) | Yes | No | Yes (as absence) | None | High |
| DC20-X-06 | Exit | NO partial profit taking | Turtle System 1 (fat-tail capture) | Yes | No | Yes (as absence) | None | High |

---

## 3. Cross-Setup / Portfolio Rules

| Rule ID | Category | Rule (Concise) | Source | Objective? | Ambiguous? | Testable? | Bias | Confidence |
|---------|----------|----------------|--------|------------|------------|-----------|------|------------|
| PORT-01 | Portfolio | Max 6 open positions total (across both setups) | Constitution §4.3 | Yes | No | Yes | None | High |
| PORT-02 | Portfolio | Max 2 positions per sector | Constitution §4.3 | Yes | No | Yes | None | High |
| PORT-03 | Portfolio | Max 1 position per trader-annotated theme | Trader overlay | **Partial** — theme is subjective | **Yes** — theme requires trader judgment | Only via journal review | None | Low |
| PORT-04 | Portfolio | Total open risk ≤ 3% of account | Constitution §4.3 | Yes | No | Yes | None | High |
| PORT-05 | Portfolio | Correlation gate: veto if 60d ρ > 0.75 with existing position | PROPOSED MODIFICATION | Yes | No | Yes | None | Low |
| RISK-01 | Risk | Per-trade risk 0.5% start, scale to 1% after 6mo positive expectancy | Constitution §4.1 | Yes | No | Yes | None | High |
| RISK-02 | Risk | Stop only moves in trader's favor | Universal | Yes | No | Yes | None | High |
| RISK-03 | Risk | No averaging down | Constitution §4.5 | Yes | No | Yes | None | High |
| EXEC-01 | Execution | T+1 settlement: block new entries using unsettled cash if would trigger GFV | Spec 07 §5.8 | Yes | No | Yes | None | Medium |
| EXEC-02 | Execution | Hard stops execute regardless of GFV risk | Spec 07 §5.8 | Yes | No | Yes | None | High |

---

## 4. Known Contradictions / Tensions

### 4.1 Earnings Blackout vs Trend-Following Payoff

**Rules:** PBK-X-07, DC20-X-04 (both mandate closing 3 days before earnings)

**Tension:** DC20's edge comes from capturing rare, large trend continuations. A stock trending powerfully into earnings and gapping UP on a beat is exactly the kind of fat-tail outcome DC20 is designed to capture. **Closing before earnings destroys this asymmetry.**

**Counter-argument:** gap-down risk on a miss can produce a −3R to −5R day. That's uncompensated tail risk on the wrong side.

**Resolution proposed:**
- **PBK:** keep earnings blackout — PBK holding periods are short (median 5–12 days); missing a few earnings runs costs little
- **DC20:** research question — test *both* variants (blackout vs no-blackout) in backtest and compare fat-tail impact
- **Interim rule:** keep blackout for both, tagged as **RESEARCH QUESTION** to revisit

### 4.2 Regime Filter vs Trend-Following Purity

**Rules:** DC20-R-01 (blocks CHOP/HIGH_VOL/BEAR)

**Tension:** Pure Turtle-style DC20 has NO regime filter — it trades every breakout. The Turtles argued that a regime filter, however well-designed, will eventually filter out the setup that would have caught the next major trend.

**Counter-argument:** trend-following on individual stocks (not commodities/futures where Turtles operated) has different dynamics. Whipsaw in equity chop is more expensive due to slippage and correlation with market.

**Resolution proposed:** keep regime filter as PROPOSED MODIFICATION, subject to ablation testing per Spec 05 §4A. If ablation shows the regime filter doesn't add value → remove it and revert to Turtle-pure DC20.

### 4.3 Volume Confirmation vs Breakout Timing

**Rules:** DC20-E-02 (require 1.5× volume on breakout day)

**Tension:** Turtle rules had NO volume filter. Volume is a lagging indicator by construction (you know volume only at close, not during the bar). Requiring 1.5× volume means Mode A entries (close of D) must decide extremely late.

**Counter-argument:** filtering fake breakouts is worth the timing cost.

**Resolution proposed:** ablation test both variants.

### 4.4 Anti-Flip-Flop on Stage 2 vs Signal Freshness

**Rules:** PBK-E-01 with anti-flip-flop requirement

**Tension:** requiring slope-up on both D and D-1 means missing the first bar of a fresh Stage 2 transition.

**Counter-argument:** first-bar transitions are noise-heavy; delaying by 1 bar filters more noise than signal.

**Resolution:** keep as-is for PBK (slow moving MAs make 1-bar delay negligible).

---

## 5. Ambiguous Terms Flagged for Precise Definition

| Term | Where Used | Current Definition | Recommended Precision |
|------|------------|---------------------|-----------------------|
| "Swing high / swing low" | PBK-E-02, PBK-X-03 | Informal | Needs formal algorithm (e.g., local max/min over N-bar window; N=5 default) — **RESEARCH QUESTION** |
| "Active theme" | Portfolio + trader annotation | Subjective | DEMOTED to trader overlay per Spec 03 §3.8 |
| "Recent higher low" | PBK-X-03 | Informal | Uses swing-low algorithm above |
| "Volume drying up" | PBK-E-05 | ≤ 0.70 ratio | Precisely defined; keep as-is |
| "Strong stock" | Various | Fuzzy | Deprecated — use PBK-R-02 (top-3 sector) + PBK-E-03 (RS thresholds) instead |
| "Breakout" | DC20-E-01 | `Close(D) > DC_upper(20) using bars D-1..D-20` | Precise; keep look-ahead warning prominent |

---

## 6. Look-Ahead Bias Audit — Explicit Verification

| Indicator | Uses Today's Close? | Uses Future Bars? | Verdict |
|-----------|---------------------|---------------------|---------|
| DC_upper(20) at close of D | NO (bars D-20 to D-1 only) | NO | ✅ Safe |
| DC_lower(10) at close of D | NO (bars D-10 to D-1 only) | NO | ✅ Safe |
| ATR(14) at close of D | Yes (includes D's high/low/close) | NO | ✅ Safe (D is the current bar being decided on) |
| SMA_200(D) | Yes (bars D-199 to D) | NO | ✅ Safe |
| EMA_20, EMA_50 | Yes | NO | ✅ Safe |
| Volume(D) at close of D | Yes | NO | ✅ Safe (known at close) |
| avg_volume_20(D-1) | No (bars D-21 to D-1) | NO | ✅ Safe |
| RS_line at close of D | Yes | NO | ✅ Safe |
| Regime at close of D | Yes (uses signals at close) | NO | ✅ Safe |
| Sector rank at close of D | Yes | NO | ✅ Safe |
| Halal classification | As of last verification date; must not use future reclassification | NO | ✅ Safe (historical halal tagging per Spec 02 §5.3) |
| Earnings date | Historical announced date; must not use restated dates | NO | ⚠ Requires verified historical earnings source (some providers restate) |
| Corporate actions | Split/dividend as of ex-date | NO | ✅ Safe when provider is honest |

**Overall look-ahead audit:** ✅ Safe by construction. Backtester (Spec 04) must include automated assertions that detect any accidental leakage.

---

## 7. Survivorship Bias Audit

| Concern | Applies? | Mitigation |
|---------|----------|------------|
| Historical universe includes only stocks that survive to today | YES if not mitigated | Spec 02 §7.2 mandates retaining delisted stocks in historical universe |
| Halal classification retroactively applied | YES if not mitigated | Spec 02 §5.3 mandates at-time-of-trade halal tagging (never today's classification for historical evaluation) |
| Sector membership retroactively applied | YES if not mitigated | Historical GICS membership required; some providers only carry current classification (RESEARCH QUESTION — verify provider) |
| Index membership (e.g., S&P 500 constituents) | Not applicable — we don't filter by index membership | N/A |

**Overall:** mitigations are speced but require validation once data providers are integrated. **RESEARCH QUESTION:** verify chosen provider (Polygon.io / EODHD / FMP) actually delivers survivorship-adjusted historical data.

---

## 8. Overfitting Risk Audit

| Parameter | Provisional / Cited / Validated? | Overfitting Risk |
|-----------|------------------------------------|-------------------|
| DC20 entry lookback = 20 | CITED (Donchian original) | Low (documented publicly for 70 years) |
| DC20 exit lookback = 10 | CITED (Turtle System 1) | Low |
| PBK EMA periods 20, 50 | STRUCTURAL (round numbers, widely used) | Low |
| PBK pullback 3–12% | PROVISIONAL (Minervini range) | Medium |
| PBK pullback ATR 1.0–3.5 | PROVISIONAL | Medium |
| PBK volume ratio ≤ 0.70 | PROVISIONAL | Medium |
| PBK entry volume mult 1.25× | PROVISIONAL | Medium |
| DC20 entry volume mult 1.5× | PROVISIONAL | Medium |
| DC20 ATR bounds 0.5–2.0× | PROVISIONAL | Medium |
| Stop buffer 0.5 ATR | PROVISIONAL | Medium |
| Stop max distance 2.0 ATR | PROVISIONAL | Medium |
| Regime signals threshold 4/6 | PROVISIONAL | **High** — no cited source |
| VIX regime thresholds 20 / 25 | PROVISIONAL | **High** — no cited source |
| Breadth regime threshold 60% | PROVISIONAL | **High** — no cited source |
| PBK time stop 15 days | PROVISIONAL | Medium |
| PBK partial at 2R | PROVISIONAL | Medium |
| Sample-size buckets (30/100/300) | PROVISIONAL | Medium |
| Correlation gate 0.75 | PROVISIONAL | Medium |

**Highest overfitting risk:** regime thresholds. All are trader-heuristic starting points. Spec 05 must run robustness sweeps (§3.4) and ablation tests (§4A) on these before treating them as validated.

**Anti-overfitting policy in effect:** Spec 05 §5 forbids grid search on the trading dataset. Parameter changes require an out-of-sample justification.

---

## 9. Testability Audit

| Dimension | Assessment |
|-----------|------------|
| Rules objectively testable | 95%+ of rules are mathematically defined |
| Ambiguous rules requiring formalization | 3 (swing high/low, active theme, "strong stock" legacy language) |
| Simulation-ready | Yes, after Spec 04 (Backtester) implementation |
| Manual-execution-ready | Yes — trader can execute today per the manual guide |
| Automation-ready | Yes — deterministic rules with configurable parameters |

---

## 10. Categorization by Source

| Source | Rule Count |
|--------|-----------|
| SOURCE RULE (cited literature) | ~14 |
| INFERENCE (logically derived from source) | ~7 |
| PROPOSED MODIFICATION (my recommendation) | ~22 |
| RESEARCH QUESTION (unresolved) | ~5 |

**Observation:** the majority of specific parameters are PROPOSED MODIFICATIONS. This is honest — I did not invent PBK or DC20, but the specific thresholds (volume multiples, ATR bounds, R-multiples for partial profit, time stops, regime thresholds) are largely modern additions to the classical frameworks. Robustness testing and ablation testing (Spec 05) exist specifically to validate or refute these.

---

## 11. Recommendation

**Do not treat any PROVISIONAL parameter as authoritative until validated** by:
1. Robustness sweep (Spec 05 §3.4) — performance stable across ±20% parameter variation
2. Ablation testing (Spec 05 §4A) — filter demonstrably adds value beyond BASE
3. Walk-forward validation (Spec 05 §3.5) — out-of-sample expectancy matches in-sample

Until then, parameters are starting points. Live paper trading provides the first real evidence.

---

## 12. Related Docs

- Full setup math: [`03-strategy-definitions.md`](./03-strategy-definitions.md)
- Validation methodology: [`05-research-engine.md`](./05-research-engine.md)
- Expected statistical envelope: [`expected-behavior.md`](./expected-behavior.md)
- Manual trading protocol: [`setup-comparison-dc20-vs-pullback.md`](./setup-comparison-dc20-vs-pullback.md)
