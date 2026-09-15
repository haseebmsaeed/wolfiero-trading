# Spec 09 — Trade Card & Alerting

**Status:** Draft
**Phase:** 3
**Depends on:** Specs 01–08
**Downstream:** Journal (Spec 10) records every card and its outcome

---

## 1. Purpose

Spec 09 defines **all notifications the trader receives** — entry cards, exit alerts, position-management updates, and system-health digests. Every notification is:

- **Tagged by setup** (`[DC20]` or `[PBK]`) so the trader can filter, mute, or focus per setup
- **Tagged by category** (entry vs exit vs management vs health)
- **Delivered via Telegram** (Phase 3 default) with optional email fallback

There are **two card types**:

1. **Entry Trade Card** — the pre-approval briefing before opening a new position (requires human approval)
2. **Position Management Notification** — updates on existing positions (informational, or auto-executed per pre-approved plan)

**The trade card is where the whole system is judged.** If it is confusing, cluttered, or missing the information the trader needs at 9:32am, everything upstream is wasted.

---

## 2. Guiding Principles

### P1 — Scannable in 30 Seconds
The card must be readable in 30 seconds to reach a decision. Anything requiring longer belongs in an appendix or is redundant.

### P2 — Traffic-Light Severity
Risks are shown with severity symbols:
- 🟢 Green: positive
- 🟡 Yellow: concern (proceed with caution / reduced size)
- 🔴 Red: veto (do not trade)

### P3 — Why AND Why-NOT
Every card shows both the case for the trade and the case against. A card with only reasons to buy is dangerous.

### P4 — Numbers Over Words
Where a number exists, show the number. Prose is for context, not measurement.

### P5 — Provenance on the Card
Every stat cites its source (data date, sample size, model version, config version). No mysterious numbers.

### P6 — Approve / Reject Explicit
The card is not informational — it terminates in an explicit binary decision from the human. Timeout = reject.

---

## 3. Entry Trade Card Structure

### 3.1 Full Card Template

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    [{DC20|PBK}] ENTRY CARD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ticker:            {ticker}         Rank: {A/B/C}
Company:           {company_name}
Setup:             {setup_name}     Tag: [{DC20|PBK}]
Direction:         LONG
Card ID:           {uuid}
Generated:         {timestamp}
Config version:    {constitution_version} / {strategy_version}

━━━━━━━━ HALAL ━━━━━━━━
Status:            🟢 PASSED
Standard:          {standard}
Last verified:     {date}
Reason:            {business ok, ratios ok}

━━━━━━━━ MARKET ━━━━━━━━
Regime:            {STRONG_BULL / NORMAL_BULL / CHOP / HIGH_VOL / BEAR}
Regime score:      {n}/6 green signals
VIX:               {vix} ({trend})
Breadth:           {%} S&P above 50-day

━━━━━━━━ SECTOR & THEME ━━━━━━━━
Sector:            {sector} — RS rank {n}/11 ({direction})
Theme:             {theme} (active {n} weeks)

━━━━━━━━ STOCK ━━━━━━━━
Stage:             Stage 2 ({n} days)
RS vs SPY:         +{n}% (63-day)
Price:             ${p}
Distance from 20 EMA: {n} ATR
Distance from 50 EMA: {n} ATR

━━━━━━━━ SETUP DETAIL ━━━━━━━━
Pullback depth:    {n}% / {n} ATR
Volume ratio:      {n} (pullback / prior 20-day)
Support touched:   {20 EMA / 50 EMA / pivot} at ${p}
Days in pullback:  {n}
Entry trigger:     ${p}
Entry confirmation: reclaim of prior day high + vol > {n}× avg

━━━━━━━━ TRADE PLAN ━━━━━━━━
Entry:             ${p}         (buy-stop, good-for-day)
Stop:              ${p}         (structural, {n} ATR below entry)
First target:      ${p}         (2R — sell 1/3, move stop to BE on rest)
Position size:     {n} shares
Capital:           ${n}
Account risk:      ${n} ({risk_pct}%)
Sizing bucket:     {A / B / C / D} (n = {sample_size})

━━━━━━━━ HISTORICAL EVIDENCE ━━━━━━━━
Setup / regime / sector cell:
  Sample size:        {n} similar setups
  Win rate:           {n}%
  Avg winner:         +{n}R
  Avg loser:          −{n}R
  Expectancy:         +{n}R  (95% CI: [{low}, {high}])
  Median hold:        {n} days

Recent 20 (all regimes):
  {n}W / {n}L  Total: +{n}R

━━━━━━━━ ML MODEL (Advisory) ━━━━━━━━
Model A prediction:   {n}% probability of +1R first
Model B prediction:   ~{n} days expected hold
Model context sample: {n} similar training examples
Top drivers (SHAP):
  ↑ {feature}: +{shap}
  ↑ {feature}: +{shap}
  ↓ {feature}: {shap}
Model version:        {version}
[⚠ MODEL DEGRADED / MODEL HISTORY DIVERGENCE — if applicable]

━━━━━━━━ EARNINGS ━━━━━━━━
Next earnings:     {date} ({n} days away)
{✓ outside expected hold window / ⚠ inside window — will exit before}

━━━━━━━━ WHY (green flags) ━━━━━━━━
🟢 Strong market regime ({regime})
🟢 Leading sector (RS rank {n}/11)
🟢 Active theme: {theme}
🟢 Stage 2 leader ({days} days)
🟢 Controlled pullback ({n}% / {n} ATR)
🟢 Volume contraction ({ratio})
🟢 Positive historical expectancy (+{n}R, n={n})
🟢 Clean structural stop ({n} ATR distance)

━━━━━━━━ WHY-NOT (concerns) ━━━━━━━━
🟡 Sector slightly extended ({detail})
🟡 Market breadth softening ({detail})
🔴 (would appear here if a hard-veto condition were present)

━━━━━━━━ PORTFOLIO CONTEXT ━━━━━━━━
Current open positions:  {n}/6
Current open risk:       {n}% of account
After this trade:        {n}%
Sector exposure:         {sector}: {n} positions (max 2)
Highest correlation:     {n} with {ticker}
Cash after trade:        ${n}

━━━━━━━━ AI RESEARCH ANALYST (Advisory) ━━━━━━━━
One-sentence: "{one_sentence_summary}"

Recent developments:
- {summary} [source]
- {summary} [source]

Earnings context:
  Last report: {summary}
  Guidance: {raised/maintained/lowered}
  Source: {url}

Notable risks:
- {risk} [source]

Catalysts:
- {catalyst} on {date} [source]

━━━━━━━━ HUMAN STATE ━━━━━━━━
Today's state check: {PASSED / CASH_DAY}
{if CASH_DAY: This card is for reference only — no new entries today}

━━━━━━━━ DECISION ━━━━━━━━
[ ✅ APPROVE ]     [ ❌ REJECT ]     [ ⏸ SNOOZE 60 min ]

Auto-reject if no action by: {timestamp + 60 min}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 3.2 Compact Alert (Telegram Push)
When multiple candidates present simultaneously, a compact summary is sent first, **grouped by setup**:

```
📋 4 candidates ready — {timestamp}

[PBK] Pullback candidates (2):
  A: NVDA  Regime: NORMAL_BULL  Exp: +0.42R (n=183)
  B: AVGO  Regime: NORMAL_BULL  Exp: +0.31R (n=127)

[DC20] Breakout candidates (2):
  C: LRCX  Regime: NORMAL_BULL  Exp: +0.35R (n=94)
  D: PANW  Regime: NORMAL_BULL  Exp: +0.28R (n=71)

Reply "A" / "B" / "C" / "D" for full card,
"pbk only" / "dc20 only" to filter, or "cancel all"
```

---

## 3A. Position Management Notifications (Exit Alerts)

Once a position is opened, the trader receives ongoing notifications until it closes. Every notification is:
- Tagged with the position's setup: `[DC20]` or `[PBK]`
- Categorized: `INFO` (heads-up, no action) / `AUTO` (system already acted per pre-approved plan) / `ACTION` (approval needed)

### 3A.1 Notification Catalog

| Notification | Setup | Category | Trigger | Sample Text |
|--------------|-------|----------|---------|-------------|
| **Stop Hit — Position Closed** | Both | AUTO | Stop-loss order filled | `[PBK] NVDA stop hit at $XXX.XX. Position closed. Loss: −1.02R (−$204). Journal ID: {id}` |
| **Trend Exit — Position Closed** | DC20 | AUTO | Close < DC_lower(10) | `[DC20] LRCX trend exit at close $XXX.XX (below 10-day low). Position closed. Gain: +2.4R (+$480). Journal ID: {id}` |
| **+2R Reached — Partial Sell** | PBK | AUTO | First target hit | `[PBK] NVDA hit +2R at $XXX.XX. Sold 1/3 (XX shares). Stop moved to breakeven $XXX.XX on remaining 2/3.` |
| **Trail Updated** | Both | INFO | Daily post-close trail advance | `[PBK] NVDA trail updated to $XXX.XX (was $XXX.XX). Locked gain: +XR on remaining position.` |
| **10-Day Low Approaching** | DC20 | INFO | Price within 1 ATR of exit trigger | `[DC20] LRCX current $XXX.XX, 10-day low exit at $XXX.XX (0.7 ATR away). Position under pressure.` |
| **Time Stop Imminent** | PBK | INFO | Position ≤ 1.0R after 14 days | `[PBK] AVGO time stop tomorrow EOD (14/15 days, currently +0.4R). Will auto-close at close unless recovery.` |
| **Regime Downgrade** | Both | ACTION | Regime dropped to CHOP or worse | `[DC20] Market regime downgraded to CHOP. All DC20 positions: closing 1/2, tightening exit to DC_lower(5). Approve action?` |
| **Halal Reclassification** | Both | AUTO | Held stock reclassified | `[PBK] NVDA halal status changed from COMPLIANT to NON-COMPLIANT (source: Zoya, 2026-XX-XX). Auto-closing full position at next open.` |
| **Earnings in 3 Days** | Both | INFO | Position approaching earnings blackout | `[PBK] NVDA earnings on 2026-XX-XX (3 days). Auto-close will fire at close on 2026-XX-XX (1 day prior).` |
| **Data Quality Incident** | Both | ACTION | Data VETO on held stock | `[DC20] LRCX data quality veto: primary/secondary price divergence 1.2%. Investigating. Position monitoring paused; stops remain active.` |
| **Kill Switch Fired** | Setup-specific | ACTION | Setup paused per decay/drawdown/slippage rule | `[DC20] DC20 kill switch fired: rolling 12w expectancy −0.15R (was +0.32R). No new DC20 entries until re-authorized. Existing positions unaffected.` |
| **Order Rejected by Broker** | Both | ACTION | Broker failure | `[PBK] Broker rejected buy-stop on AAPL. Reason: {msg}. Trade cancelled.` |
| **Fill Anomaly** | Both | INFO | Slippage > 2× modeled | `[DC20] NVDA fill slippage $0.34 (modeled $0.11). Logged for review.` |

### 3A.2 Position Snapshot (Sent Daily Per Open Position)

At close of each trading day, one snapshot per open position:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[PBK] NVDA — Position Snapshot
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Setup:            [PBK]
Opened:           2026-XX-XX  (5 days ago)
Entry:            $XXX.XX     Shares: XX
Current:          $XXX.XX     P&L: +$XXX (+X.X%)
R multiple:       +X.XR
Initial stop:     $XXX.XX     Current stop: $XXX.XX
First target:     $XXX.XX     Hit: yes / no
Trail level:      $XXX.XX

Next action:      {Wait / Partial at $X / Stop hit / Time stop in N days}

Halal:            🟢 verified
Earnings:         X days away

Position Journal: {id}
```

DC20 snapshot is similar but shows the DC_lower(10) instead of trail level:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[DC20] LRCX — Position Snapshot
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Setup:            [DC20]
Opened:           2026-XX-XX  (12 days ago)
Entry:            $XXX.XX     Shares: XX
Current:          $XXX.XX     P&L: +$XXX (+X.X%)
R multiple:       +X.XR
Initial stop:     $XXX.XX     Current 10-day low: $XXX.XX
Distance to exit: X.X ATR

Next action:      {Hold / Approaching exit / Regime downgrade action}

Halal:            🟢 verified
Earnings:         X days away

Position Journal: {id}
```

### 3A.3 Daily Digest (One Message, Pre-Open, Every Trading Day)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DAILY DIGEST — {date}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MARKET REGIME:    NORMAL_BULL (5/6 green signals)
VIX:              18.2 (stable)
Top sectors:      XLK, XLV, XLE
Active themes:    AI infra, GLP-1, nuclear

━━━━━━━━ SETUP STATUS ━━━━━━━━
[PBK]  🟢 ACTIVE   |  Rolling 12w exp: +0.34R (n=42)
[DC20] 🟢 ACTIVE   |  Rolling 12w exp: +0.28R (n=19)

━━━━━━━━ NEW CANDIDATES TODAY ━━━━━━━━
[PBK]  2 candidates awaiting trigger
[DC20] 1 candidate awaiting trigger

Cards will be sent when triggers fire.

━━━━━━━━ OPEN POSITIONS ━━━━━━━━
[PBK] NVDA   +1.2R   Trail: $XXX
[PBK] AVGO   +0.4R   Time stop in 3 days
[DC20] LRCX  +2.7R   10d low: $XXX

Total open risk: 2.1% of account

━━━━━━━━ DATA HEALTH ━━━━━━━━
🟢 All providers healthy
🟢 Halal classifications fresh
🟢 No divergence incidents

━━━━━━━━ HUMAN STATE ━━━━━━━━
Please reply:
"OK" — proceed with new trade cards today
"CASH" — CASH DAY, no new entries (mechanical exits continue)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 3.3 Post-Approval Confirmation

```
✅ Trade approved: NVDA
Order placed: buy-stop $XXX.XX + $0.05
Stop: $XXX.XX  Target: $XXX.XX  Shares: XX
Card: {uuid}
Journal ID: {id}
```

---

## 4. Severity Rules

### 4.1 🔴 Red Conditions (Veto — Card Not Sent Or Marked "DO NOT APPROVE")

Any of the following prevents card generation OR marks the card as VETOed:
- Halal failure
- Data staleness veto
- Regime = BEAR (no new entries)
- Portfolio veto (open risk, position count, sector, correlation, cash)
- Stop viability veto (structural stop > 2 × ATR)
- Earnings inside window (unless earnings setup)
- Sample size = INSUFFICIENT_DATA AND regime bucket is not favorable
- Kill switch active for this setup
- Human state = CASH_DAY (no new-entry cards generated at all)

### 4.2 🟡 Yellow Conditions (Reduce Size or Proceed with Caution)

- Regime = CHOP or HIGH_VOL
- Sector RS falling (was top, now slipping)
- Volume ratio > 0.90 (weak contraction)
- Distance from 20 EMA > 1.0 ATR (moderately extended)
- Model prediction disagrees with historical expectancy (MODEL_HISTORY_DIVERGENCE)
- ML model marked DEGRADED
- Historical sample size 30–99 (bucket B — reduced risk)

### 4.3 🟢 Green Conditions
Everything else that supports the trade.

---

## 5. Delivery Channels

### 5.1 Telegram (Phase 3 Default)
- Bot-hosted; trader adds bot to allowlisted chat
- Message split if longer than Telegram's limit
- Inline buttons for APPROVE / REJECT / SNOOZE
- Approval action makes an authenticated API call back to the runtime
- **Setup filtering via commands** (per-setup mute/focus):
  - `/mute pbk` — silence all PBK notifications until manually resumed
  - `/mute dc20` — silence all DC20 notifications
  - `/unmute pbk` / `/unmute dc20` — resume
  - `/only pbk` — receive only PBK notifications; DC20 auto-silenced
  - `/status` — show current mute/focus state and per-setup counters
  - `/positions` — list all open positions with snapshots
  - `/positions pbk` / `/positions dc20` — filtered list
- **Muting does NOT affect execution** — mechanical exits still run silently; muting only silences delivery

### 5.2 Email (Optional Fallback)
- Sent in parallel for durable record
- Approval via link with signed token (single-use)

### 5.3 Web Dashboard (Phase 4+)
- Live view of all outstanding cards
- History browser
- Journal integration

### 5.4 SMS (Not planned Phase 3)
- Deferred; add if Telegram becomes unreliable

---

## 6. Timing and Frequency

### 6.1 Card Generation Times
- **Sunday evening (10 PM local):** watchlist generation for the upcoming week
- **Weekday pre-open (30 min before US open):** any candidates whose triggers are within 1 ATR of current price
- **Intraday:** trigger alerts when a candidate hits its entry condition (real-time or 15-min delayed depending on data feed)

### 6.2 Card Expiry
- Every card includes an expiry (default 60 minutes after generation)
- Expired card auto-rejects with reason "expired"
- Trader can snooze once for 60 minutes; second timeout auto-rejects

### 6.3 Rate Limits
- Maximum 5 candidate cards per day (avoids overload)
- If more than 5 candidates surface, rank by expectancy × sample size and take top 5

---

## 7. Stories

### Story 9.1 — Trade Card Template Renderer
**As:** the trade card generator
**I want:** a rendering function that assembles all upstream inputs into the §3.1 template
**So that:** cards look consistent and no field is missing

**Acceptance criteria:**
- Renderer takes structured inputs from Specs 03, 05, 06, 07, 08
- Missing optional inputs render as "n/a" or omit their section
- Missing required inputs (e.g., halal status) prevent card generation
- Output matches template character-for-character for a golden fixture

### Story 9.2 — Severity Classifier
**As:** the card generator
**I want:** every condition automatically tagged 🟢 / 🟡 / 🔴 per §4
**So that:** severity is consistent, not judgment-based

**Acceptance criteria:**
- Rules table mapping condition → severity
- All conditions from §4.1–§4.3 covered
- Unit tests cover boundary cases
- Any 🔴 present prevents APPROVE button rendering

### Story 9.3 — Telegram Bot Integration
**As:** the runtime
**I want:** cards delivered to Telegram with inline APPROVE / REJECT / SNOOZE buttons
**So that:** the trader can act from the phone

**Acceptance criteria:**
- Bot authenticates via allowlisted chat IDs
- Message split for long cards
- Button callbacks make signed API calls back to the runtime
- APPROVE → order placement (Spec 07); REJECT → card closed as REJECTED; SNOOZE → 60-minute deferred re-notify

### Story 9.4 — Approval Handler
**As:** the runtime
**I want:** approval / rejection / snooze actions handled idempotently
**So that:** double-clicks or network retries don't produce duplicate orders

**Acceptance criteria:**
- Each card has a unique ID
- APPROVE action produces at most one broker.place() call per card
- Rejection / expiration produces a Journal entry with reason
- Idempotency verified in integration test

### Story 9.5 — Card Expiry
**As:** the runtime
**I want:** cards to auto-reject if not acted on within the expiry window
**So that:** stale cards do not produce trades at wrong prices

**Acceptance criteria:**
- Default expiry 60 min from generation
- Snooze extends by 60 min once
- Expiration action logs to Journal with reason "expired"

### Story 9.6 — Compact Multi-Card Digest
**As:** the trader
**I want:** a one-message summary when multiple cards present at once
**So that:** I can triage before reading full cards

**Acceptance criteria:**
- If ≥ 2 cards ready in same batch, digest sent first
- Digest lists rank, ticker, setup, regime, expectancy, sample size
- Reply commands fetch specific card or cancel all

### Story 9.7 — Rate Limiter
**As:** the runtime
**I want:** no more than 5 cards per day generated
**So that:** the trader is not overwhelmed

**Acceptance criteria:**
- If > 5 candidates pass all gates in a day, rank by expectancy × log(sample_size) and take top 5
- Non-selected candidates logged for Journal but not delivered

### Story 9.8 — Post-Approval Confirmation Message
**As:** the trader
**I want:** confirmation of order placement and Journal ID within seconds of approval
**So that:** I know the order actually went through

**Acceptance criteria:**
- Confirmation sent within 5 seconds of broker.place() success
- Includes ticker, order type, price, stop, target, shares, Journal ID
- On broker failure, alert with retry status

### Story 9.9 — Card Persistence
**As:** the Journal (Spec 10)
**I want:** every card persisted with all its inputs and the resulting decision
**So that:** historical review is complete

**Acceptance criteria:**
- Card object stored with unique ID, all fields, generation timestamp, decision, decision timestamp
- Immutable after decision is recorded
- Query API by ticker, date, decision

### Story 9.10 — Golden Fixture Test
**As:** engineering
**I want:** a golden fixture card produced from known inputs
**So that:** regressions in card rendering are detected

**Acceptance criteria:**
- Fixture input JSON committed
- Expected card output committed
- Test compares rendered output to expected; passes only on exact match

### Story 9.11 — Position Management Notification Publisher
**As:** the execution engine
**I want:** every notification in §3A.1 published to the alerting layer
**So that:** the trader is informed of every exit-relevant event without exception

**Acceptance criteria:**
- Every event from the catalog fires exactly one notification per event occurrence
- Notification tagged with `setup_id` (`DC20` / `PBK`) and category (`INFO` / `AUTO` / `ACTION`)
- ACTION notifications require trader response before the referenced action completes
- AUTO notifications inform after the action is already done
- INFO notifications are read-only
- Test: simulate each catalog event; verify one and only one notification produced

### Story 9.12 — Daily Position Snapshots
**As:** the trader
**I want:** one snapshot per open position at close of each trading day
**So that:** I have a full daily status without opening the platform

**Acceptance criteria:**
- Snapshot format per §3A.2 (PBK and DC20 templates)
- Includes current P&L, R multiple, next expected action
- Delivered after market close, before the next daily digest
- Snapshots suppressed for muted setups

### Story 9.13 — Daily Pre-Open Digest
**As:** the trader
**I want:** a single pre-open digest per §3A.3
**So that:** I know the market state, setup state, open position state, and my human-state requirement all at once

**Acceptance criteria:**
- Delivered 30 min before US market open
- Includes: regime, VIX, top sectors, active themes, per-setup expectancy, new candidates awaiting trigger, open positions summary, data health, human-state prompt
- Waits for OK / CASH reply before generating new-entry cards for the day
- Timeout on reply (default: market open) defaults to OK

### Story 9.14 — Setup Filtering Commands
**As:** the trader
**I want:** Telegram commands to mute, focus, or query specific setups
**So that:** I can control notification volume during experimentation

**Acceptance criteria:**
- Commands per §5.1 (`/mute`, `/unmute`, `/only`, `/status`, `/positions`) all implemented
- Muting affects delivery only, never execution
- `/status` shows current mute state and per-setup 30-day counters
- Idempotent (repeated `/mute pbk` is a no-op with confirmation)
- Command usage journaled

### Story 9.15 — Per-Setup Trade Card Routing
**As:** the trade card generator
**I want:** every card carry an unambiguous `setup_id` tag in both header and payload
**So that:** downstream systems can route, filter, and analyze by setup

**Acceptance criteria:**
- Card ID scheme includes `setup_id` (e.g., `card-pbk-{uuid}` or `card-dc20-{uuid}`)
- Header prominently shows `[PBK]` or `[DC20]`
- Compact digest groups candidates by setup (§3.2)
- Approval action routes to correct setup's Journal partition

---

## 8. Acceptance Criteria for Spec 09

- All stories 9.1–9.10 pass their acceptance criteria
- End-to-end: candidate → card → Telegram approve → order placed → Journal entry
- Fault test: Telegram outage → card falls back to email; approval still works
- Rate limit test: 8 candidates in a day → 5 cards sent, 3 logged
- Strongest available reasoning model has reviewed and APPROVED

---

## 9. Open Questions for the Trader

1. **Delivery:** Telegram only, or also email in parallel from day one?
2. **Card expiry:** 60 minutes — comfortable?
3. **Rate limit:** 5 cards/day max — increase for active weeks?
4. **Card language:** English default — bilingual (Urdu/English) support desired?
5. **Snooze:** should snooze also delay time-based triggers, or just re-notify?
