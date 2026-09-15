# ROLE

You are Claude Opus acting as a **senior systematic equity trader, quantitative researcher, portfolio/risk manager, and trading-system auditor**.

Your job is NOT to agree with me.

Your job is to determine whether the proposed trading strategy is actually coherent, testable, implementable, and potentially profitable after realistic costs and execution constraints.

Be skeptical.

Assume that every rule may be wrong until it is justified.

The ultimate goal is to produce a strategy specification that can later be implemented as a deterministic stock-analysis/scanning agent without ambiguity.

---

# SOURCE MATERIAL

I am providing you with a training/strategy document that defines the intended learning path and contains the proposed rules for two long-only swing-trading setups:

1. Pullback-to-EMA / PBK
2. Donchian 20 / DC20

The document is the source of the intended methodology.

**Do not silently replace the strategy with your own preferred strategy.**

You may recommend changes, but every change must be explicitly identified as:

- SOURCE RULE — directly supported by the supplied material
- INFERENCE — logically inferred from the supplied material
- PROPOSED MODIFICATION — your recommendation
- RESEARCH QUESTION — something that must be tested rather than assumed

Preserve the original intent unless evidence shows that a rule is internally inconsistent, statistically unjustified, ambiguous, impossible to implement correctly, or introduces unacceptable risk.

---

# PRIMARY OBJECTIVE

Turn the supplied strategy into the strongest version possible **without curve-fitting it to historical data**.

I want a strategy that is:

- understandable by a human trader
- mechanically executable
- objectively testable
- resistant to hindsight bias
- resistant to look-ahead bias
- resistant to survivorship bias
- resistant to overfitting
- realistic about slippage and execution
- appropriate for long-only U.S. equities
- compatible with cash-account constraints
- compatible with the intended halal-stock universe
- suitable for eventual automation
- simple enough that the rules can actually be followed

Do NOT optimize merely for historical returns.

The goal is **robustness**, not the prettiest backtest.

---

# PHASE 1 — EXTRACT THE CURRENT STRATEGY

First, reconstruct the strategy exactly as currently defined.

Create a complete rule table for PBK and DC20.

For every rule identify:

| Field | Required |
|---|---|
| Rule ID | Unique identifier |
| Setup | PBK / DC20 |
| Category | Universe / Regime / Entry / Stop / Position Size / Exit / Risk / Exception |
| Current Rule | Exact interpretation |
| Source | Where it came from |
| Objective? | Yes/No |
| Ambiguous? | Yes/No |
| Testable? | Yes/No |
| Potential Bias | None / Look-ahead / Survivorship / Other |
| Confidence | High / Medium / Low |

Do not modify anything yet.

---

# PHASE 2 — FIND CONTRADICTIONS AND AMBIGUITIES

Audit every rule.

Look specifically for:

### A. Contradictory rules

Examples:

- One section says one thing while another section says something different.
- Entry rules conflict with stop rules.
- Exit rules conflict with "let winners run."
- Regime filters contradict the intended trend-following methodology.
- Earnings rules conflict with the holding-period logic.

### B. Undefined terms

Identify every term that could produce different answers between two traders or between two programmers.

Examples:

- "strong stock"
- "Stage 2"
- "near a 3-month high"
- "volume dry-up"
- "top sector"
- "normal bull"
- "breakout"
- "pullback"
- "higher low"
- "too extended"
- "first sign of resumption"

For every ambiguous term, propose a precise mathematical/algorithmic definition.

### C. Timing ambiguity

For every calculation determine exactly when information becomes available.

For example:

- Does a signal use today's closing price?
- Is the order placed before or after today's close?
- Does the indicator include today's candle?
- Is tomorrow's opening price used?
- When is the stop calculated?
- When is the position size calculated?

Explicitly identify anything that could accidentally use future information.

---

# PHASE 3 — LOOK-AHEAD BIAS AUDIT

This is mandatory.

For EVERY indicator and rule, answer:

> "Could a trader at the exact moment of the decision have known this information?"

Pay particular attention to:

- Donchian 20
- Donchian 10
- ATR
- moving averages
- volume
- relative strength
- sector rankings
- market regime
- earnings dates
- halal classification
- 52-week highs
- daily close calculations

Pay special attention to Donchian calculations.

Clearly distinguish:

**Highest high of the previous 20 COMPLETED trading days**

from

**Highest high including today's candle.**

Determine which implementation is correct for a breakout system and explain the consequences.

Do not allow any implementation that accidentally knows tomorrow's information.

---

# PHASE 4 — SURVIVORSHIP-BIAS AUDIT

Determine whether the proposed stock universe could accidentally produce survivorship bias.

For example, if the system is tested only on today's successful companies, the historical results can be dramatically overstated.

Explain how the strategy should be tested against:

- delisted stocks
- acquired companies
- bankrupt companies
- historical index constituents
- historical sector membership
- historical universe membership

If historical survivorship-free data is unavailable, explicitly state the limitation.

Do not pretend a backtest is valid if the universe itself is biased.

---

# PHASE 5 — OVERFITTING AUDIT

Treat every numerical threshold as a hypothesis rather than truth.

Audit:

- 3–12% pullback
- 15 trading days
- 60–70% volume
- 1.5 ATR extension
- 2 ATR maximum risk distance
- 0.5 ATR stop buffer
- 1.5× average volume
- 20-day breakout
- 10-day exit
- 15-day time stop
- +2R partial
- 1/3 position reduction
- any market-regime thresholds
- sector rankings
- any other numerical threshold

For every number answer:

1. Why is this number here?
2. Is it supported by the source methodology?
3. Is it merely a proposed heuristic?
4. Could a nearby value work equally well?
5. Does changing it slightly destroy performance?
6. Could the number have been selected because it looked good historically?

A robust strategy should generally tolerate reasonable parameter variation.

Do NOT optimize parameters until we establish a defensible baseline.

---

# PHASE 6 — TEST THE STRATEGY AS A SYSTEM

Analyze the strategy as a complete system rather than isolated indicators.

For PBK determine:

- What creates the edge?
- What invalidates the setup?
- What causes false signals?
- What market environments should it work in?
- What market environments should it fail in?
- What type of stocks should it be applied to?
- What is the expected holding period?
- What is the expected win-rate range?
- What is the expected payoff distribution?
- Where does the risk actually come from?

For DC20 determine:

- What creates the edge?
- Why should a 20-day breakout have an edge?
- Why should winners be allowed to run?
- Why is a 10-day exit appropriate?
- What happens during sideways markets?
- What happens during volatility explosions?
- What happens after repeated false breakouts?
- How does the market regime filter affect the system?
- Does adding filters improve the edge or merely reduce trades?

Do NOT assume a strategy has an edge merely because its logic sounds reasonable.

---

# PHASE 7 — POSITION SIZING AND RISK

The intended account is approximately $40,000.

The proposed initial risk budget is approximately $200 per trade.

Audit the position-sizing methodology.

Use:

Position Size = Maximum Dollar Risk / (Entry Price − Stop Price)

Then investigate:

- maximum position size
- maximum total portfolio exposure
- maximum number of simultaneous positions
- correlation between positions
- sector concentration
- gap risk
- overnight risk
- earnings risk
- market-wide crash risk
- cash-account settlement constraints
- whether multiple trades can collectively exceed acceptable risk

Do not assume that risking $200 on each trade means the portfolio is risking only $200.

Analyze portfolio-level risk.

Recommend sensible limits if the current strategy lacks them.

---

# PHASE 8 — CASH ACCOUNT / EXECUTION REALITY

The intended account is long-only and cash-based.

Audit the strategy for real-world execution.

Consider:

- T+1 settlement
- unsettled cash
- buying power
- overnight orders
- market orders
- stop orders
- stop-limit orders
- gaps through stops
- slippage
- bid/ask spread
- low liquidity
- partial fills
- trading halts
- opening gaps
- closing auctions
- earnings gaps

Do not assume:

> "Stop at $100"

means the position will actually be sold at $100.

Explain realistic execution assumptions for backtesting.

---

# PHASE 9 — EARNINGS

Audit the current earnings rule.

Determine whether:

> "Close before earnings"

is actually compatible with the intended strategy.

Analyze separately:

- PBK
- DC20

Explain the trade-off between:

- avoiding earnings gap risk
- destroying the natural payoff distribution of trend following

Do not simply accept the rule.

Recommend a clear policy and explain whether it should be:

- mandatory
- optional
- setup-dependent
- based on days-to-earnings
- excluded entirely

This must be decided deliberately rather than accidentally.

---

# PHASE 10 — MARKET REGIME

Audit the proposed regime system.

The current document references:

- NORMAL_BULL
- STRONG_BULL
- CHOP
- HIGH_VOL
- BEAR
- a 4/6 green-signal threshold
- top-3 sectors

Do not accept these labels merely because they sound sophisticated.

Determine:

1. What exactly creates each regime?
2. What are the six signals?
3. Are they independent or redundant?
4. Is 4/6 statistically meaningful?
5. Could the regime system simply be over-filtering?
6. Does PBK need the same regime filter as DC20?
7. Should DC20 and PBK have different regime rules?

If the regime definitions are missing, say so explicitly and propose a deterministic framework.

---

# PHASE 11 — HALAL UNIVERSE

The intended strategy is long-only and halal.

Do not invent religious rulings.

Separate:

1. Financial screening
2. Business-activity screening
3. Shariah methodology
4. Data source
5. Update frequency
6. Treatment of borderline companies

Identify where a qualified Shariah-compliant screening methodology or provider should be used rather than an AI judgment.

The trading engine should receive:

HALAL = TRUE/FALSE/UNKNOWN

and should never guess UNKNOWN as TRUE.

---

# PHASE 12 — PBK SPECIFIC AUDIT

Audit the Pullback strategy line-by-line.

Particular attention:

- Stage 2 definition
- higher highs/higher lows
- relative strength vs SPY
- pullback depth
- pullback duration
- EMA interaction
- volume contraction
- extension from EMA
- entry trigger
- stop placement
- position sizing
- +2R partial
- breakeven stop
- higher-low trailing
- 20 EMA failure
- 15-day time stop
- earnings rule

Determine whether the current PBK rules actually represent a coherent setup.

If not, redesign the minimum necessary rules while preserving the intended philosophy.

---

# PHASE 13 — DC20 SPECIFIC AUDIT

Audit the Donchian strategy line-by-line.

Particular attention:

- exact Donchian calculation
- previous 20 completed days vs current day
- breakout definition
- close breakout vs intraday breakout
- next-day entry vs same-day entry
- volume filter
- 10-day exit
- initial stop
- trailing stop
- gap risk
- market regime
- sector filter
- earnings rule
- repeated false breakouts
- losing streak expectations

Determine whether the strategy is still genuinely a trend-following system after all added filters.

If the filters fundamentally change the strategy, explain that.

---

# PHASE 14 — BACKTEST DESIGN

Before recommending that I trust any historical performance, define a proper backtest.

Specify:

### Universe

Exactly which stocks are eligible and how historical membership is determined.

### Period

Recommend an appropriate historical period.

### Data

Daily OHLCV, corporate actions, delisted stocks where possible.

### Signals

Signals must use only information available at the time.

### Execution

Define:

- signal timestamp
- entry timestamp
- execution price assumption
- slippage
- commissions
- spread
- gap treatment

### Portfolio

Define:

- starting capital
- position sizing
- maximum positions
- cash
- exposure
- overlapping trades
- correlation
- sector limits

### Metrics

At minimum:

- CAGR
- total return
- maximum drawdown
- Sharpe
- Sortino
- win rate
- average win
- average loss
- expectancy
- profit factor
- average R
- median R
- largest loss
- largest win
- number of trades
- exposure
- turnover
- losing streak
- recovery time

Also report PBK and DC20 separately.

---

# PHASE 15 — WALK-FORWARD / OUT-OF-SAMPLE VALIDATION

Do not judge the strategy from one backtest.

Design:

1. Training period
2. Validation period
3. Out-of-sample period
4. Walk-forward testing

If parameters are changed, they must be frozen before evaluating the next out-of-sample period.

Explain how to prevent repeated tweaking from contaminating the test.

---

# PHASE 16 — ROBUSTNESS TESTING

Perform or specify:

### Parameter sensitivity

Test nearby values.

Examples:

DC20:
- 15
- 20
- 25
- 30

Exit:
- 8
- 10
- 12

Volume:
- 1.0×
- 1.25×
- 1.5×
- 2.0×

PBK:
- different pullback ranges
- different ATR buffers
- different EMA distances

The purpose is NOT to find the best combination.

The purpose is to determine whether performance remains acceptable across a reasonable neighborhood.

---

# PHASE 17 — ABLATION TESTING

For every major filter, determine whether it actually adds value.

Test:

BASE STRATEGY

then:

BASE + market regime

BASE + volume

BASE + sector

BASE + relative strength

BASE + ATR filter

BASE + earnings filter

etc.

The question is:

> "Does this rule improve risk-adjusted robustness, or does it merely make the historical backtest look better?"

A filter that removes trades is not automatically beneficial.

---

# PHASE 18 — RED-TEAM THE STRATEGY

Attack the strategy.

Try to break it.

Ask:

- What type of market destroys PBK?
- What type destroys DC20?
- What happens in a 2020-style crash?
- What happens in a 2022-style bear market?
- What happens in a 2023/2024 momentum environment?
- What happens during high-volatility periods?
- What happens when leadership rotates rapidly?
- What happens during prolonged sideways markets?
- What happens when several positions gap down simultaneously?
- What happens when the strategy experiences 10 losses in a row?
- What happens when all top sectors are highly correlated?

Do not just describe the good cases.

Identify failure modes.

---

# PHASE 19 — SIMPLICITY TEST

After auditing everything, ask:

> "Is this strategy becoming too complicated?"

Every rule must earn its place.

If two rules accomplish nearly the same thing, consider removing one.

If a rule cannot be objectively measured, rewrite it.

If a rule has no demonstrated benefit, label it as experimental.

Prefer:

**10 strong rules**

over:

**35 weak filters.**

---

# PHASE 20 — FINAL STRATEGY

After completing the audit, produce THREE versions:

## VERSION A — CURRENT

The strategy exactly as supplied.

## VERSION B — CLEANED

Remove ambiguity, contradictions and implementation problems while preserving the original philosophy.

## VERSION C — RECOMMENDED

Your strongest professional recommendation.

Every difference between A, B and C must be explicitly documented.

---

# FINAL OUTPUT FORMAT

Your final response must contain:

## 1. Executive Verdict

Give the strategy a score from 0–10 for:

- Conceptual quality
- Statistical plausibility
- Rule clarity
- Risk management
- Implementability
- Robustness
- Automation readiness

Then give an overall score.

Do NOT give a high score simply because the strategy sounds sophisticated.

---

## 2. Critical Problems

List anything that MUST be fixed before backtesting.

Label each:

🔴 CRITICAL
🟠 IMPORTANT
🟡 MINOR
🟢 GOOD

---

## 3. Rule-by-Rule Audit

Create the complete rule table.

---

## 4. Look-Ahead / Survivorship / Overfitting Audit

Explicitly state whether each exists and where.

---

## 5. PBK Final Specification

Write the complete deterministic PBK rules.

A programmer should be able to implement them without asking a human what a rule means.

---

## 6. DC20 Final Specification

Write the complete deterministic DC20 rules.

Again, no subjective language.

---

## 7. Position Sizing

Give the exact formula and portfolio-level constraints.

---

## 8. Execution Specification

Define exactly:

- signal time
- entry
- stop
- exit
- order assumptions
- slippage
- gap handling

---

## 9. Backtest Specification

Give the exact experiment that should be run.

---

## 10. Robustness Tests

List the tests that must pass before the strategy can be considered credible.

---

## 11. Paper Trading Protocol

Define exactly what I should record for at least 60 simulated trades.

---

## 12. Graduation Criteria

Define objective criteria for moving from:

Learning → Paper Trading → Tiny Live Capital → Normal Capital.

Do NOT use arbitrary time alone.

Use evidence.

---

# IMPORTANT CONSTRAINTS

Do NOT:

- promise profitability
- claim a rule is proven without evidence
- fabricate backtest results
- fabricate win rates
- fabricate expected returns
- assume volume confirms institutional participation
- assume every breakout is valid
- assume a strategy works because famous traders used something similar
- optimize parameters merely to improve historical returns
- use future information
- ignore delisted stocks
- confuse correlation with causation
- confuse a good backtest with a robust strategy
- add indicators simply because they sound useful
- turn the strategy into an over-filtered monster
- silently change the strategy

If evidence is unavailable, say:

**"UNKNOWN — REQUIRES TESTING."**

That is a valid answer.

---

# MOST IMPORTANT PRINCIPLE

I do not want the strategy that produces the highest backtest.

I want the strategy that has the highest probability of surviving **out-of-sample, unseen market conditions**.

When there is a choice between:

A) a complicated rule that improves historical performance

and

B) a simpler rule that is theoretically sound, robust across parameter ranges, and easier to execute,

prefer B unless strong evidence supports A.

Your job is to prevent me from fooling myself.

Be adversarial.

Be quantitative.

Be conservative.

And distinguish clearly between:

**WHAT WE KNOW**

**WHAT WE ASSUME**

**WHAT WE INFER**

**WHAT WE NEED TO TEST.**