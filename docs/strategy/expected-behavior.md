# Expected Behavior — What "Normal" Looks Like Per Setup

**Purpose:** define the *expected* statistical envelope for each setup, so that during paper trading (and later live) the trader knows what is normal fluctuation versus what warrants investigation. **Without this document, every losing streak feels like the strategy is broken.**

**Status:** these are **prior expectations** based on published literature and structural characteristics of each setup, **NOT** guarantees. Live evidence will refine these ranges. Any live behavior *outside* the ranges here should trigger investigation, not automatic abandonment.

---

## 1. How to Use This Document

Every 5–10 trades, compare your live/paper results against these expectations. There are three possible outcomes:

- 🟢 **Within range** → the setup is behaving as expected. Continue.
- 🟡 **Near a boundary** → note it, watch closely, don't over-adjust.
- 🔴 **Outside range for 20+ trades** → investigate before continuing.

**Do NOT investigate on sample sizes under ~10 trades.** Small samples produce wild variance. Statistical fluctuation looks like signal when you squint hard enough.

---

## 2. Pullback Setup (`PBK`) — Expected Behavior

### 2.1 Statistical Envelope

| Metric | Expected Range | Warning Boundary | Red Flag (Investigate) |
|--------|----------------|-------------------|-------------------------|
| Win rate | 45–60% | < 40% or > 70% | < 35% or > 75% |
| Avg winner (R) | +1.5R to +2.5R | < +1.2R | < +1.0R |
| Avg loser (R) | −0.8R to −1.1R | > −1.3R | > −1.5R |
| Expectancy per trade | +0.2R to +0.5R | Below +0.1R | Below 0 (30+ trades) |
| Profit factor | 1.3 to 2.0 | < 1.15 | < 1.0 (30+ trades) |
| Median holding period | 5 to 12 trading days | > 20 days | > 30 days |
| Time-stop exits | 15% to 30% of trades | > 40% | > 50% |
| Trades per week (per trader) | 0 to 3 | 5+ in a bad market | 5+ during CHOP/BEAR |
| Max losing streak | 3 to 5 in a row | 6 in a row | 8 in a row |

### 2.2 Payoff Distribution Shape

PBK produces a **moderate-win, moderate-loss** distribution. You should see:
- Many small wins around +1R to +2R (the +2R partial captures most winners)
- Some medium wins where the runner trails to +3R to +5R
- Rare big wins (+6R or more) when a strong trend runs after entry
- Losers cluster near −1R (structural stop is well-defined)

**If your distribution shows** many tiny wins (+0.3R) and big losses (−1.5R), your stops are too wide relative to your targets — investigate.

### 2.3 Best and Worst Market Conditions

**PBK works best in:** trending markets with normal, orderly pullbacks. Late-stage bull markets. Rotation-driven bull markets (leaders keep leading).

**PBK struggles in:**
- **Sharp overnight reversals** — you buy the pullback, wake up to bad news, gap through stop
- **Choppy sideways markets** — pullbacks look valid, then keep pulling back
- **Regime-transition periods** — Stage 2 stocks becoming Stage 3

### 2.4 When to Actually Worry

**Investigate PBK when ALL of these are true simultaneously:**
- 30+ live trades completed
- Rolling 20-trade expectancy < 0
- Regime has been NORMAL_BULL or STRONG_BULL for the sample period
- Adherence rate > 90% (you actually followed the rules)

If all four hold → the setup is genuinely underperforming its prior. Time to investigate whether the market has structurally changed or whether a specific parameter needs revisiting.

**Do NOT investigate** when the losing streak is 5 trades, sample is 12 trades, or regime was CHOP/BEAR for most of the sample.

---

## 3. Donchian 20 Setup (`DC20`) — Expected Behavior

### 3.1 Statistical Envelope

| Metric | Expected Range | Warning Boundary | Red Flag (Investigate) |
|--------|----------------|-------------------|-------------------------|
| Win rate | 30–40% | < 25% or > 50% | < 20% or > 55% |
| Avg winner (R) | +2.5R to +4.5R | < +2.0R | < +1.5R |
| Avg loser (R) | −0.9R to −1.1R | > −1.2R | > −1.4R |
| Expectancy per trade | +0.1R to +0.4R | Below 0 | Below −0.1R (50+ trades) |
| Profit factor | 1.3 to 2.5 | < 1.15 | < 1.0 (50+ trades) |
| Median holding period | 15 to 40 trading days | > 60 days | > 90 days |
| Trend-exit percentage | 55% to 70% of trades | > 80% (too many losers) | > 85% |
| Trades per week (per trader) | 0 to 2 | 3+ in a bad market | 3+ during CHOP/BEAR |
| **Max losing streak** | **5 to 8 in a row** | **10 in a row** | **12 in a row** |

**Note the losing streak numbers.** DC20's losing streaks are LONG. Turtles documented streaks of 10+ in real trading and stayed with the system. **If you cannot psychologically tolerate 7 losses in a row, DC20 is not for you.**

### 3.2 Payoff Distribution Shape

DC20 produces a **fat-tailed, positively-skewed** distribution:
- Many small losers at −1R (the 10-day low exit catches most failed breakouts)
- Some breakeven trades that trend a little then reverse
- Rare medium winners (+3R to +5R)
- **Very rare huge winners (+8R to +15R+)** — these are where the entire year's profit comes from

**If your DC20 distribution shows** balanced win/loss magnitudes (say +2R avg winner, −1R avg loser) — you're probably cutting winners too early or something is wrong with the exit implementation.

### 3.3 Best and Worst Market Conditions

**DC20 works best in:** strong, persistent bull trends. Sector rotations that produce multi-month runs. Post-consolidation breakouts. Late 2020, 2023, mid-2024 style regimes.

**DC20 struggles in (and by design skips) :**
- **Choppy markets** — the regime filter blocks entries; if it doesn't, whipsaw losses accumulate fast
- **High volatility** — false breakouts on emotional spikes
- **Post-crash recovery** — early rebounds trigger buys, then fizzle
- **Sector rotation days** — leaders one week, laggards the next

### 3.4 The Streak Problem — Read This Twice

**DC20 losing streaks are the reason 90% of traders abandon trend-following before their edge materializes.**

Expected losing streak distribution in a positive-expectancy DC20 system:
- 3 losses in a row: happens ~monthly
- 5 losses in a row: happens ~quarterly
- 7 losses in a row: happens ~yearly
- 10 losses in a row: happens ~once every 3–5 years

**All of these are NORMAL and do NOT indicate the strategy is broken.** They are the tax you pay to capture the fat tail. The 1 winner after a 7-loss streak often pays for all 7 losses plus 3–5R profit.

**Rules for surviving DC20 streaks:**
1. Never increase position size to "make it back"
2. Never abandon the rules mid-streak
3. Journal each losing trade with brutal honesty (did I follow the plan? Yes/No)
4. If adherence was 100% during the streak → the system is working exactly as designed
5. If adherence was < 90% → you are the problem, not the system

### 3.5 When to Actually Worry

**Investigate DC20 when ALL of these are true simultaneously:**
- 50+ live trades completed (DC20 needs a larger sample than PBK to be statistically meaningful)
- Rolling 30-trade expectancy < −0.10R
- Regime was NORMAL_BULL or STRONG_BULL for majority of the sample
- Adherence rate > 90%

Only then investigate. Not at 15 trades. Not during CHOP. Not when you deviated from the plan on 3 of the last 10.

---

## 4. Portfolio-Level Expectations (Both Setups Combined)

Assumes both setups active in parallel, 0.5% risk per trade, $40K account.

| Metric | Expected Range | Investigate Below |
|--------|----------------|--------------------|
| Trades per month combined | 4 to 12 | 20+ (over-trading) |
| Time in market | 20% to 60% | 90%+ (never in cash) |
| Simultaneous positions | 0 to 6 | consistently 6/6 |
| Max drawdown (annual) | 8% to 15% | > 20% |
| Annualized return (best case with real edge, year 2+) | 10% to 25% | Consistently negative for 6+ months |
| Sharpe ratio | 0.7 to 1.5 | Below 0.4 |

### 4.1 What a "Normal" Year Looks Like

For a $40K account trading both setups at 0.5% risk:

**Realistic best case (year 2, edge established):**
- ~60 trades total (35 PBK + 25 DC20)
- ~30 winners, ~30 losers
- PBK contributes ~+$3,000 (moderate wins, moderate losses, moderate frequency)
- DC20 contributes ~+$4,500 (fewer wins, bigger wins, longer holds)
- Total: **~+$7,500 (18.75%)** — this is a very good year
- 2–3 months negative, drawdown reaching ~10% at worst

**Realistic median case (year 2):**
- ~60 trades total
- Similar win/loss counts
- Total: **~+$3,500 to +$5,000 (8–12%)** — respectable
- 4–5 months negative, drawdown reaching ~12% at worst

**Realistic bad case (year 2):**
- ~50 trades
- Slight negative expectancy or breakeven
- Total: **−$1,500 to +$1,000 (−4% to +2.5%)**
- 6+ months negative, drawdown reaching ~15%
- Investigate whether regime, adherence, or setup itself is the issue

**Year 1 is typically worse across the board** — learning curve, adherence errors, small sample.

---

## 5. What NOT to Do When Behavior Falls Outside Range

**Amateur reactions that destroy accounts:**
1. **Increase position size to "make it back"** → doubles the drawdown when the streak continues
2. **Abandon the setup after 5 losses** → the 6th trade was going to be the winner
3. **"Improve" the entry rules by adding new filters** → over-fits to the recent losing sample
4. **Switch strategies mid-drawdown** → you now have zero live evidence on either
5. **Reduce position size to zero (paralysis)** → miss the mean-reversion when it comes

**Professional reaction:**
1. Continue trading the plan exactly
2. Journal every trade with adherence tag
3. Watch for 30+ trades on PBK / 50+ trades on DC20 before diagnosing
4. If diagnosis warranted: use Spec 05 tools (rolling expectancy, ablation, regime-conditional analysis) — never intuition
5. If a rule genuinely needs change: change it deliberately, with justification logged, and reset your sample counter

---

## 6. Emotional Warning Signs (Journal These Weekly)

Your emotional state IS the data. Note when any of these apply:

- "I want to skip this trigger — it looks scary" → you're second-guessing the system
- "I want to take this trade — it's not quite on the checklist but…" → you're inventing setups
- "I need to make money this week" → return-target thinking, destroys discipline
- "I'll widen the stop just this once" → you don't respect your risk
- "I already lost 4 in a row — I'll size down" → you're breaking the sizing rule for the wrong reason
- "The market feels different lately" → maybe. Wait 30 trades before acting on the feeling

**None of these mean you're bad at trading. All humans feel these.** Winning traders notice them, name them, and follow the plan anyway.

---

## 7. Summary Card (Print and Post Above Monitor)

```
┌────────────────────────────────────────────────┐
│ WHAT'S NORMAL — DO NOT PANIC WHEN YOU SEE THIS │
├────────────────────────────────────────────────┤
│ PBK:  5 losses in a row — normal quarterly     │
│ DC20: 8 losses in a row — normal annually      │
│                                                │
│ PBK win rate 45%: normal                       │
│ DC20 win rate 32%: normal                      │
│                                                │
│ 3 weeks with zero trades: normal in CHOP       │
│ 2 months negative P&L: normal, not diagnostic  │
│ 10% drawdown: normal, expected 1–2× per year   │
│                                                │
│ WHEN TO INVESTIGATE:                           │
│ ✓ 30+ trades (PBK) or 50+ (DC20)               │
│ ✓ Rolling expectancy < 0                       │
│ ✓ Regime was supportive                        │
│ ✓ Adherence > 90%                              │
│                                                │
│ Otherwise: FOLLOW THE PLAN. JOURNAL EVERYTHING.│
└────────────────────────────────────────────────┘
```

---

## 8. Related Docs

- Manual protocol: [`setup-comparison-dc20-vs-pullback.md`](./setup-comparison-dc20-vs-pullback.md)
- Setup math: [`03-strategy-definitions.md`](./03-strategy-definitions.md)
- Research validation: [`05-research-engine.md`](./05-research-engine.md)
- Journal design: [`10-journal-and-attribution.md`](./10-journal-and-attribution.md)
