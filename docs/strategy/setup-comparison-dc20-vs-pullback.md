# Setup Comparison — Donchian 20 vs Pullback to EMA

**Purpose:** Side-by-side comparison of the two active setups. Read this before every Sunday planning session. Print it, tape it above your monitor.

**Status:** Both setups are **first-class, active, and tracked independently.** Neither is "primary." Each has its own expectancy table, its own kill switch, its own trade cards, and its own P&L attribution.

> **⚠ Trade Type Clarification (Non-Negotiable):**
> Every trade described in this document is a **LONG position using cash**. That means:
> - You BUY shares at your entry price with your own money (no margin, no borrowing)
> - You OWN the shares while holding
> - You SELL the shares at your exit price
> - You profit when the exit price is HIGHER than the entry price
> - **You never short-sell, never use options, never trade on margin.** Period.
> Both DC20 and PBK are long-side setups. DC20 buys strength (breakout to 20-day high). PBK buys a temporary retracement within an uptrend. Different entry philosophies, same direction: LONG. Same money mechanic: cash-out to buy shares, sell shares later for cash.

---

## 1. The Two Setups at a Glance

> **⚠ ALL PERFORMANCE NUMBERS BELOW ARE PRIORS, NOT FACTS.** They are derived from published literature on similar setups and the general characteristics of the strategy families, NOT from testing of the specific Wolfiero-filtered variants. Actual live results may differ substantially. Treat these as *expectations for what "normal" might look like*, not as promises. See [`expected-behavior.md`](./expected-behavior.md) §1 for the discipline of comparing live results to priors.

|                     | **Donchian 20 (DC20) — Wolfiero-modified** | **Pullback to EMA (PBK) — Wolfiero-formalized** |
|---------------------|---------------------------------------------|--------------------------------------------------|
| **Style**           | Momentum breakout with added filters | Retracement in uptrend, formalized VCP-inspired |
| **Entry logic**     | Buy when close breaks above prior 20-day high, plus Wolfiero filters (regime, sector, volume) | Buy when Stage-2 uptrend pulls back to 20/50 EMA with volume dry-up, then resumes |
| **Origin of core** | Richard Donchian (1950s); Turtle System 1 (Faith 2007) | General concept from Weinstein / O'Neil / Minervini; specific thresholds are Wolfiero |
| **Origin of filters** | Classic Turtle has NO regime/sector/volume filter — these are Wolfiero additions (see Spec 03 §4A warning) | Specific thresholds (3–12%, 0.70 vol, 1.5 ATR extension, 0.5 ATR buffer) are Wolfiero heuristics, not verbatim Minervini rules |
| **Expected win rate (PRIOR — untested)** | ~30–40% (typical for trend-following systems in literature) | ~45–60% (typical for pullback systems in literature) |
| **Expected avg winner (PRIOR — untested)** | +2.5R to +4.0R | +1.5R to +2.5R |
| **Expected avg loser (PRIOR — untested)** | ~−1.0R | ~−1.0R |
| **Best market regime (hypothesis)** | STRONG_BULL (persistent trends) | NORMAL_BULL, STRONG_BULL (trending with pullbacks) |
| **Worst market regime (hypothesis)** | CHOP (whipsaw death) | Sharp reversals mid-trend |
| **Trades per stock per year (rough estimate)** | 4–8 | 6–12 |
| **Entry location relative to support** | Far above (20-day high) | Near support (at 20/50 EMA) |
| **Stop distance** | Wide (10-day low, often 8–12%) | Tight (below pullback low + 0.5 ATR, often 4–7%) |
| **Position size (same $risk)** | Smaller (wide stop) | Larger (tight stop) |
| **R:R per trade (target)** | Lower (2:1 typical) | Higher (2.5–3:1 typical) |
| **Psychological difficulty (subjective)** | HIGH (long losing streaks expected) | MODERATE (drawdowns still real) |
| **Time to first exit (rough estimate)** | Median ~15–30 days | Median ~8–15 days |
| **Halal compatible** | ✓ Yes (setup-neutral) | ✓ Yes (setup-neutral) |
| **Notification tag** | `[DC20]` | `[PBK]` |

---

## 1A. Classic Rules vs Wolfiero-Modified Rules

**We are NOT trading the classic versions of these setups.** We are trading Wolfiero-modified variants that add several filters on top of the classical cores. This distinction matters — attributing our filtered variants' behavior to the classic authors would be dishonest.

### DC20 — What's Classic Turtle vs What's Wolfiero-Added

| Rule | Classic Turtle System 1 (Faith 2007) | Wolfiero-Modified DC20 |
|------|--------------------------------------|-------------------------|
| Buy signal | Close breaks 20-day high | Close breaks 20-day high **AND** the added filters below |
| Halal screen | (not applicable — Turtles traded futures) | ✓ ADDED (Rule Zero) |
| Regime gate | None — Turtles took every breakout | ✓ ADDED (STRONG_BULL / NORMAL_BULL only) |
| Sector filter | None | ✓ ADDED (top-3 sectors) |
| Volume filter | None | ✓ ADDED (≥ 1.5× 20d avg) |
| ATR sanity | None | ✓ ADDED (0.5–2.0× 60d median) |
| Stop viability | Turtles had 2% N-based position size | ✓ ADDED (stop ≤ 2 × ATR check) |
| Earnings blackout | (not applicable) | ✓ ADDED (close 3 days before) |
| Exit signal | Close breaks 10-day low | ✓ SAME (with regime tightening added) |
| Time stop | None (letting winners run) | ✓ SAME (no time stop) |
| Partial profits | None | ✓ SAME (no partials) |

**Implication:** the Wolfiero-DC20 is more selective than classic Turtle. It will produce fewer trades. Whether the added filters improve expectancy or over-filter and destroy edge is a research question — see Spec 05 §4A ablation testing.

### PBK — What's from the Authors vs What's Wolfiero-Formalized

| Rule | Author-Provided | Wolfiero-Formalized |
|------|-----------------|---------------------|
| Stage 2 concept | ✓ Weinstein 1988 (qualitative) | Precise mathematical definition (5 conditions, anti-flip-flop) |
| Relative strength | ✓ O'Neil CANSLIM | Specific 63-day + 5% outperformance thresholds |
| VCP / controlled pullback concept | ✓ Minervini 2013 (qualitative) | Specific 3–12% band, 1.0–3.5 ATR, 15-day lookback, ≤ 7 down days |
| Volume dry-up concept | ✓ Minervini 2013 (qualitative) | Specific ≤ 0.70 ratio threshold |
| Entry trigger | Various authors describe "reclaim of prior high" | Specific buy-stop @ High(D-1) + $0.05 with 1.25× vol confirmation |
| Structural stop | ✓ Weinstein / Minervini concept | Specific Pullback low − 0.5 × ATR formula |
| Position size | ✓ Van Tharp risk-of-ruin | Standard formula |
| Halal screen | Not from any trading author | ✓ WOLFIERO — Constitution Rule Zero |
| Regime gate | Not from any pullback author | ✓ WOLFIERO — added |
| +2R partial | Common trader convention | ✓ WOLFIERO default (research question — Spec 05 will validate) |
| 15-day time stop | Not from any pullback author | ✓ WOLFIERO — added |
| Earnings blackout | Common trader convention | ✓ WOLFIERO — added |

**Implication:** while the *inspiration* comes from established authors, the specific tradeable rules are Wolfiero's formalization. Do not attribute the exact numerical thresholds to Weinstein, O'Neil, or Minervini — they are our extensions.

**For complete attribution rigor:** see [`source-attribution.md`](./source-attribution.md).

---

## 2. When Each One Shines

### DC20 shines when…
- Market is in a persistent, strong trend (2020–2021, 2023–2024 AI rally)
- Leaders are making new highs on rising volume
- Volatility is moderate — enough movement to trigger, not so much you get whipsawed
- You have the discipline to sit through 5–8 losing trades before the big winner

### DC20 struggles when…
- Market is choppy or range-bound (60–70% of trading days)
- Volatility is very high (fake breakouts everywhere)
- Sector rotation is fast (leaders become laggards mid-trend)
- Volume is thin (breakouts fail without institutional participation)

### Pullback shines when…
- Market is trending but with normal pullbacks (most bull markets)
- Leaders show clean, orderly retracements to support
- You want higher win rate and more frequent trades
- You prefer buying near support with tight stops

### Pullback struggles when…
- Market gaps hard against you overnight
- A trending stock rolls over mid-pullback (Stage 2 → Stage 3 transition)
- Volatility spikes (support levels blow through)

---

## 3. Side-by-Side Entry Rules

### DC20 Entry

**Setup conditions (all must be TRUE on evaluation date D):**
- Stock ∈ Halal Universe
- Stock ∈ Liquidity filter (price > $10, mcap > $1B, ADV > $20M)
- Market regime ≥ NORMAL_BULL (skip in CHOP, HIGH_VOL, BEAR)
- Stock is in a top-3 sector
- Close(D) > MAX(High(D-1), High(D-2), …, High(D-20))   ← the 20-day high breakout
- Volume(D) > 1.5 × avg_volume_20(D-1)   ← volume confirmation
- ATR(14) at D is within a normal range (not spiking > 2× 60-day median)
- No earnings within next 15 trading days
- Distance from breakout to 10-day-low stop is ≤ 2.0 × ATR (viability)

**Entry order:** Buy at close of D, OR next-day open (choose one consistently). No mid-day chasing.

### Pullback Entry

**Setup conditions (all must be TRUE on evaluation date D):**
- Stock ∈ Halal Universe
- Stock ∈ Liquidity filter
- Market regime ≥ NORMAL_BULL
- Stock is in a top-3 sector
- Stock is in Stage 2 (above rising 50 EMA and 200 SMA)
- Stock has strong Relative Strength (RS line at 3-month high, outperforming SPY by 5%+)
- Stock pulled back 3–12% (and 1.0–3.5 ATR) from a recent swing high in the last 15 days
- Pullback stayed above the 50 EMA
- Volume during pullback contracted (avg pullback vol ÷ prior 20-day avg ≤ 0.70)
- Support touched: 20 EMA or 50 EMA
- Current price within 1.5 × ATR of the 20 EMA
- No earnings within next 15 trading days

**Entry trigger:** Buy-stop above the prior day's high, requires Volume > 1.25× avg.

---

## 4. Side-by-Side Stop Rules

| Rule | DC20 | Pullback |
|------|------|----------|
| **Initial stop** | 10-day low at time of entry | Pullback low − 0.5 × ATR(14) |
| **Viability check** | Stop distance ≤ 2.0 × ATR — else skip | Stop distance ≤ 2.0 × ATR — else skip |
| **Stops move only in your favor** | ✓ | ✓ |
| **Time stop** | None (Turtle-style: let trend run) | 15 trading days if unrealized R < 1.0 |

---

## 5. Side-by-Side Exit Rules

### DC20 Exit Stack (in priority order)
1. **Trend exit:** Close below MIN(Low(D-1), …, Low(D-10))  — the 10-day low
2. **Regime exit:** if market regime downgrades to CHOP or worse, close 1/2 immediately; tighten 10-day exit to 5-day
3. **Halal exit:** if halal status changes to "not halal," close full position at next open
4. **Earnings exit:** if earnings scheduled within 3 days, close full position before announcement
5. **No time stop:** DC20 lets winners run indefinitely (this is a feature)

### Pullback Exit Stack (in priority order)
1. **Structural stop:** at initial stop level (pullback low − 0.5 × ATR)
2. **Partial profit at +2R:** sell 1/3 of position; move stop on remaining 2/3 to breakeven
3. **Runner trail:** on remaining 2/3, trail stop at MIN(EMA_20, most-recent-higher-low − 0.5 × ATR)
4. **Time stop:** if unrealized R < 1.0 after 15 trading days, close full position at close
5. **Regime exit:** if regime downgrades to CHOP or worse, close 1/2 immediately; tighten trail on rest
6. **Halal exit:** close at next open if halal status changes
7. **Earnings exit:** close full position before announcement (3 days out)

---

## 6. Notifications You Will Get (Per Setup)

Every notification is tagged `[DC20]` or `[PBK]` so you can filter.

### Entry Notifications
| Notification | When Fired | Requires Action |
|--------------|------------|-----------------|
| **`[DC20|PBK]` Setup Detected** | End of day D: candidate meets all setup criteria | Review card; consider watchlist |
| **`[DC20|PBK]` Entry Trigger Fired** | Intraday: entry condition met | ✅ APPROVE / ❌ REJECT / ⏸ SNOOZE 60m |
| **`[DC20|PBK]` Trade Filled** | Broker confirms fill | Read only; recorded to Journal |

### Position Management Notifications (Exits)
| Notification | When Fired | Requires Action |
|--------------|------------|-----------------|
| **`[DC20|PBK]` Stop Hit** | Position stopped out | Read only; recorded |
| **`[PBK]` +2R Reached — Partial Sell** | Pullback trade hits first target | Read only; system sells 1/3 automatically per your pre-approved plan |
| **`[PBK]` Trail Updated** | Daily post-close: new trail level set | Read only |
| **`[DC20]` 10-Day Low Approaching** | Price within 1 ATR of the exit trigger | Heads-up; no action |
| **`[PBK]` Time Stop Tomorrow EOD** | Position ≤ 1.0R after 14 days | Heads-up; system will close tomorrow unless price recovers |
| **`[DC20|PBK]` Regime Downgrade** | Market regime dropped to CHOP or worse | Alerts to expected position reduction |
| **`[DC20|PBK]` Halal Reclassification** | Held stock's halal status changed | Alert only; system auto-closes at next open |
| **`[DC20|PBK]` Earnings in 3 Days** | Position approaching earnings blackout | Alert; system will close automatically |
| **`[DC20|PBK]` Kill Switch Fired** | Setup paused (decay / drawdown / slippage) | Alert; no new entries for this setup until re-authorized |

### Daily Digest (One Message, Every Trading Day, Pre-Open)
- Market regime + score
- Top 3 sectors (algorithmic — see Spec 03 §3.7)
- Active themes (trader-annotated overlay — informational only, NOT a system filter; see Spec 03 §3.8)
- New setup candidates today: DC20 count, Pullback count
- Open positions: current P&L per position, next expected action
- Kill-switch status per setup: 🟢 active / 🟡 warning / 🔴 paused
- Data health: all systems green, or specific issues

---

## 7. Running Both in Parallel — The Manual Protocol

You are experimenting with both. Here's how to run them cleanly without confusing yourself.

### Sunday Session (60–90 minutes)

**Step 1 — Market regime and sectors (20 min)**
Same for both setups. Do this once.

**Step 2 — Idea generation for BOTH (20 min)**
Same source lists (52-week highs, IBD 50, sector top holdings) feed both setups. Halal-screen once, use for both.

**Step 3 — Chart cut for DC20 (15 min)**
For each halal candidate, check:
- Is it near a 20-day high? (within 3%)
- Is it in a top-3 sector?
- Would the 10-day low stop be within 2 ATR of a potential entry?
- Any earnings in 15 days?

Write these on the **DC20 watchlist** page of your notebook.

**Step 4 — Chart cut for Pullback (15 min)**
For each halal candidate (same list), check:
- Is it Stage 2?
- Is it pulled back to 20 or 50 EMA?
- Did volume dry up during pullback?
- Is it within 1.5 ATR of the 20 EMA?

Write these on the **Pullback watchlist** page.

**Step 5 — Write trade cards (10 min)**
Cards for each finalist go on the SEPARATE page for that setup. Don't mix them.

### Weekday Mornings (15 min)

**One state check** applies to both setups. Bad state = CASH DAY for both.

**Check triggers separately:**
- DC20 triggers: is any candidate closing above its 20-day high with volume?
- Pullback triggers: is any candidate reclaiming the prior day high with volume?

**One trade at a time per setup preferred.** Don't take two DC20 entries in the same day; don't take two Pullback entries in the same day. This keeps the sample size clean for analysis.

### Portfolio Limits Apply Across BOTH

- Max 6 open positions total (not 6 per setup)
- Max 2 per sector total
- Max 1 per trader-annotated theme (theme is your judgment call at trade card time — journaled but not algorithmic)
- Total open risk ≤ 3% of account
- **Track how many open positions come from each setup** — you want a rough balance so both get tested equally

### Journaling Rules

**Every trade tagged:** `setup=DC20` or `setup=PBK`. Non-negotiable.

Separate columns in your journal for each setup so you can compute per-setup:
- Win rate
- Avg winner (R)
- Avg loser (R)
- Expectancy (R)
- Max drawdown
- Adherence rate

**After 50 trades total** (roughly 25 per setup if balanced), sit down and compare. You'll know which fits you better.

---

## 8. What to Watch For While Running Both

### Warning Signs You're Not Really Running Both

- All your recent trades are one setup → you're subconsciously avoiding the other
- You're skipping Pullback entries because DC20 "feels better" (or vice versa) → follow the rules, not the feeling
- You keep manually overriding one setup's exit → note it in the journal as DEVIATED
- One setup's win rate is way off expected range → normal early on, wait for larger sample before adjusting

### Signs That One Setup Is Winning For You

After 40–60 trades per setup:
- Consistently higher expectancy on one → that's real
- Consistently higher adherence on one → that's honest (you can actually execute it)
- Consistently better psychological experience on one → factor this in

**The goal isn't to prove DC20 is better than Pullback or vice versa. The goal is to discover which one YOU can execute with 90%+ adherence over 500+ trades.**

---

## 9. The Kill Switch Applies Per Setup

Both setups are subject to the same kill switch conditions (Spec 05 §3.3), but **independently**. That is:

- DC20 rolling 12-week expectancy goes negative → DC20 pauses; Pullback continues
- Pullback slippage divergence exceeds 50% → Pullback pauses; DC20 continues
- Halal reclassification affects a specific stock → only positions in that stock exit; other stocks in both setups continue

**Kill switches ARE NOT global unless the underlying issue is global** (e.g., regime = BEAR → both setups pause new entries; data outage → both setups pause).

---

## 10. Success Criteria After 90 Days of Parallel Trading

At end of Week 12, you should be able to fill in this table honestly:

|                         | DC20    | Pullback |
|-------------------------|---------|----------|
| Trades taken            |         |          |
| Win rate                |         |          |
| Avg winner (R)          |         |          |
| Avg loser (R)           |         |          |
| **Expectancy (R)**      |         |          |
| Max drawdown            |         |          |
| **Adherence rate**      |         |          |
| Psychological score (1–10) |     |          |

**Then decide together:**
- Both profitable and adherent → keep both
- One clearly better → reduce or drop the other, deploy more capital to the winner
- Neither profitable → investigate whether the market regime was wrong for both, or whether execution was the issue

---

## 11. Cheat Sheet — Which Setup Am I Looking At?

If you're confused mid-week which setup a chart is for, ask yourself:

**Am I looking at a 20-day high breakout with volume?** → DC20
**Am I looking at a Stage-2 leader that pulled back to its 20 or 50 EMA?** → Pullback

If the answer is BOTH — that's a rare and interesting case. It doesn't mean bigger position. It means take one entry (whichever setup fires first) and note the confluence in the journal. Track it separately as an "OVERLAP" tag. Confluence trades often perform better and we want to know.

---

## 12. Related Docs

- Setup mathematical definitions: [`03-strategy-definitions.md`](./03-strategy-definitions.md)
- Notification and trade card details: [`09-trade-card-and-alerting.md`](./09-trade-card-and-alerting.md)
- Per-setup journaling: [`10-journal-and-attribution.md`](./10-journal-and-attribution.md)
- Master framework: [`00-master-overview.md`](./00-master-overview.md)
