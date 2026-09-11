# Wolfiero — Risk & Position Sizing Specification

> Selection decides whether you have an edge. Sizing decides whether you survive long enough to
> collect it. This module is not optional polish — it is the part of the system with the largest
> effect on your actual results.

---

## 1. Core model: fixed fractional risk

Every trade risks the **same fixed fraction of account equity**, regardless of how good the idea
looks.

```
risk_budget_usd   = account_equity × risk_per_trade_pct     # default 1%
risk_per_share    = |entry_price − stop_price|
shares            = floor(risk_budget_usd / risk_per_share)
position_value    = shares × entry_price
```

**Worked example:** $100,000 equity, 1% risk = $1,000 budget. Entry $183.10, stop $175.80 →
$7.30/share → 136 shares → $24,902 position. You are risking $1,000 on a $25k position. If the idea
had a tighter stop ($179.50, $3.60/share), you would buy 277 shares — a *larger* position for the
*same* $1,000 of risk.

**The point, which must be preserved in implementation:** conviction never enters the formula. A
trader who sizes up on their favourite ideas has, by construction, their largest losses on their
highest-conviction trades — and conviction is uncorrelated with outcome. Stop distance is the only
sizing input, because it is the only thing that actually determines loss.

### Regime adjustment

```
final_shares = floor(shares × regime.position_size_multiplier)
```
1.0 in `RISK_ON`, 0.6 in `NEUTRAL`, 0.0–0.3 in `RISK_OFF`.

### Position value cap

If `position_value > 25% of equity`, cap the shares and flag it. A very tight stop can otherwise
produce a position so concentrated that a gap through the stop breaches the risk budget many times
over. **The stop protects you from the move; the cap protects you from the gap.**

---

## 2. Stop placement

A stop must be **structural first, volatility-validated second**. Never a flat percentage — a flat
7% stop is far too tight for a 60%-volatility name and far too loose for a utility, and in both
cases it sits at a price the market has no reason to respect.

### Algorithm (long)

1. **Candidate structural levels:** most recent swing low; the 20-EMA; the 50-SMA; the low of the
   consolidation base — whichever are below entry.
2. **Choose the nearest level that is at least `0.8 × ATR(14)` below entry.** Closer than that and
   ordinary daily noise takes you out of a trade that was never wrong.
3. **Add a buffer:** `stop = level − (0.25 × ATR(14))`, placing you below the obvious price where
   stop clusters sit.
4. **Validate the distance:** must be between `1.0 × ATR` and `3.5 × ATR`.
   - Below 1.0 ATR → widen to 1.0 ATR.
   - Above 3.5 ATR → the entry is too far from defensible structure. **Emit `NO_VALID_STOP` and
     drop the candidate.** Do not accept an indefensible stop just to keep an idea alive.
5. **Absolute cap:** never more than 12% from entry, regardless of ATR.

Shorts mirror this exactly.

### Trailing

Trailing is operator-initiated, never automatic, but the system recommends:
- At +1R: move the stop to breakeven.
- At +2R: trail below the most recent swing low, or use a 2×ATR Chandelier stop.
- `initial_stop_price` is **immutable** — all R-multiples are computed against original risk. A
  system that recomputes R against a trailed stop reports inflated performance.

---

## 3. Targets

1. **Structural target** — the next significant resistance level above entry.
2. **Measured move** — for breakouts, base height projected from the breakout point.
3. **ATR target** — `entry + 3 × ATR(14)`, a volatility-normalised sanity check.

Primary target = the *most conservative* of the structural and measured-move values that still
clears the 2.0 R:R floor. If none does, the candidate is vetoed with `RR_BELOW_FLOOR`.

> Taking the conservative target is deliberate. An optimistic target inflates R:R, which inflates
> the `reward_risk_score`, which promotes the candidate — the system would be rewarding itself for
> wishful thinking. Conservative targets make the score honest.

Where a second target exists, suggest scaling out half at target 1 and trailing the remainder.

---

## 4. Portfolio-level guardrails

Individual-trade risk is necessary but not sufficient. Eight positions each risking 1% is 8% at
risk — and in a correlated market drawdown they do not fail independently.

| Guardrail | Default | Rationale |
|---|---|---|
| **Portfolio heat** — sum of open risk (current price to stop) across positions | ≤ 6% of equity | Bounds a correlated bad week to a recoverable loss |
| **Max concurrent positions** | 8 | Beyond this you cannot genuinely monitor each thesis |
| **Sector concentration** | ≤ 30% of exposure in one sector | Five semiconductor names are one bet, not five |
| **Single position value** | ≤ 25% of equity | Gap protection |
| **Correlation check** | Warn when a new candidate has a 60-day correlation > 0.75 with an existing position | The most common form of accidental concentration; sector labels alone miss it |
| **Daily new entries** | ≤ 3 | Prevents clustering all entries on a single market day |

Heat uses **current** risk, not initial: once a stop is raised to breakeven, that position
contributes ~0 heat and frees budget for a new entry. This is what makes the constraint dynamic and
rewards good trade management rather than merely counting positions.

`POST /api/stocks/trade-plan` returns `RISK_LIMIT_BREACHED` with the specific guardrail and the
current value whenever a proposed entry would breach one.

---

## 5. Time stops

A swing setup that has not worked within its expected window is a failed setup, even if it has not
hit the stop.

- If a position is held beyond `HOLD_WINDOW_DAYS` (15) and is below +0.5R, flag `TIME_STOP_EXCEEDED`.
- If entry never triggers within 5 sessions of a recommendation, mark it `EXPIRED` — the setup has
  gone stale and the original levels no longer describe the market.

> Capital tied up in a position going nowhere has a real cost that does not appear in a P&L
> statement: it is the position you could not take. Time stops make that cost visible.

---

## 6. The R-multiple as the unit of account

All performance is reported in **R**, not dollars or percent.

```
R = (exit_price − entry_price) / (entry_price − initial_stop_price)     # long
```

Because every trade risks the same fraction of equity, R makes trades comparable across price
levels, volatility regimes, and account sizes. "+2.3R" means the same thing on a $12 stock and a
$600 stock; "+$840" does not.

**Expectancy** is the number that matters:
```
expectancy_R = (win_rate × avg_win_R) − (loss_rate × avg_loss_R)
```
Positive expectancy with adequate sample size is the only evidence that the system works. A 40% win
rate with +2.5R winners and −1.0R losers gives +0.4R per trade and is an excellent system — which is
exactly why **win rate alone is a misleading metric and must never be reported without average R
alongside it.**

---

## 7. What the system will not do

- Average down. A losing position is not an opportunity to increase risk.
- Widen a stop after entry. The system will refuse to record it without an explicit override flag,
  and it logs a `STOP_WIDENED` event, because this is the single most destructive discretionary
  behaviour in swing trading.
- Size by conviction, by score, or by "how much I like it."
- Recommend an entry that breaches any guardrail, regardless of score.
- Suggest holding through earnings without an explicit, logged operator override.
