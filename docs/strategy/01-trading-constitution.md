# Spec 01 — Trading Constitution

**Status:** Immutable during any active paper or live trading window
**Phase:** 1
**Depends on:** None (this is the anchor)
**Downstream:** All other specs must comply

---

## 1. Purpose

The Trading Constitution is the **immutable anchor** of the entire system. Every other spec, every model, every AI output, and every configuration change must comply with it. Its purpose is to remove ambiguity from what the system is allowed to do, and to prevent any coding model, AI assistant, LLM analyst, or future contributor from "creatively reinterpreting" the objectives.

**This document is one page in spirit.** It is not a design document. It is a set of rules.

---

## 2. Capital & Instruments

### 2.1 Capital
- **Initial account size:** $40,000 USD, cash
- **Reserve:** $5,000–$10,000 always held as cash, never deployed
- **Trading capital ceiling:** $35,000 maximum deployed at any moment
- **Currency:** USD only
- **Account type:** Individual cash brokerage account (not margin)

### 2.2 Permitted Instruments
- US-listed common stock on NYSE or NASDAQ

### 2.3 Prohibited Instruments (Hard Ban)
- Margin loans of any form
- Short selling in any form
- Options (initially — may be reconsidered after 24+ months of live proof)
- Futures
- Forex
- Cryptocurrency
- ETFs (initially — leadership analysis only, not for trading)
- Mutual funds
- Bonds
- OTC / pink sheets / penny stocks
- ADRs of thinly traded foreign issuers
- SPACs (during 6 months post-deSPAC)
- Recent IPOs (during first 6 months of trading history)

### 2.4 Universe Constraints
- Price ≥ $10.00 per share
- Market cap ≥ $1B (mid-cap or larger)
- 20-day average dollar volume ≥ $20M
- At least 6 months of continuous trading history
- Optionable (indicator of institutional liquidity, even though we do not trade options)

---

## 3. Halal Rule (Rule Zero)

### 3.1 Applies to All Decisions
No stock enters the tradeable universe without at-time-of-trade halal verification.

### 3.2 Standard
- **Default standard:** AAOIFI (Accounting and Auditing Organization for Islamic Financial Institutions)
- **Provider:** Zoya API (or equivalent that implements AAOIFI)
- **Configurable:** The specific standard is a configuration parameter, not code. Alternative standards (Islamicly, Wahed, custom) may be selected but only one is active at a time.

### 3.3 Business-Level Exclusions (Hard Ban)
- Alcohol producers, distributors, or majority retailers
- Conventional banks and insurance companies
- Casinos, gambling operators, and pure-play gaming
- Tobacco producers or majority distributors
- Cannabis producers or majority distributors
- Adult entertainment
- Pork producers or majority-pork protein producers
- Weapons manufacturers (personal choice — configurable)
- Interest-based REITs (mortgage REITs)

### 3.4 Financial Ratio Screens (AAOIFI baseline; configurable per standard)
A stock is halal ONLY IF all three hold at the time of the trade:
- Interest-bearing debt / market cap < 33%
- Interest income / total revenue < 5%
- Cash + interest-bearing investments / market cap < 33%

### 3.5 Refresh Cadence
- **Business-level classification:** monthly re-verification
- **Financial ratios:** re-computed after each earnings release for each held or watchlisted stock
- **At-trade check:** every trade card must include a halal verification timestamp

### 3.6 Non-Overridable
The trader cannot override a halal VETO. There is no "just this once" clause. If the system rejects a trade on halal grounds, the trade does not happen.

### 3.7 Historical Application
When the research engine or backtester evaluates historical setups, the halal check must use the halal state as it existed at that historical date, not today's classification. A stock that is halal today but was not halal in 2022 does not count as a valid 2022 setup.

---

## 4. Risk Rules

### 4.1 Per-Trade Risk Ceiling
- **Starting phase (first 6 months live):** 0.5% of account = $200 on $40K
- **Established phase (after 6 months + positive expectancy proof):** may scale to 1.0% = $400
- **Never exceed:** 1.0% of account risk on any single new position

### 4.2 Sample-Size Gated Risk
The Research Engine (Spec 05) reports the sample size of historical similar setups. Position risk scales with sample size:

| Historical sample size | Max risk per trade |
|------------------------|--------------------|
| < 30 similar setups | 0.25% (or skip) |
| 30–100 | 0.50% |
| 100–300 | 0.75% |
| 300+ | 1.00% |

These thresholds are configurable research parameters, not permanent truths. They are re-validated quarterly.

### 4.3 Portfolio-Level Risk Ceiling
- **Maximum total open risk (HARD CAP):** 3% of account (sum of per-trade risks across all open positions)
- **Target open risk during learning phase (first 6 months live):** 2% of account
- **Maximum simultaneous positions:** 6 (total across BOTH setups — not 6 per setup)
- **Maximum correlated exposure:** no more than 2 positions in the same sector, no more than 1 position per trader-annotated theme (themes are trader overlay per Spec 03 §3.8, not algorithmic)

### 4.4 Stop Loss Discipline
- Every position enters with a pre-defined stop
- Stop location is determined by market structure (see Spec 03)
- Stop viability is validated against volatility (must be ≤ N × ATR-14)
- **Stops move only in the trader's favor.** Never wider. Never overridden.
- If stop is hit intraday, position is closed by end of that session

### 4.5 No-Averaging-Down Rule
Adding capital to a losing position is prohibited. The trader adds to winners only, and only per pre-defined pyramid rules (Spec 03).

### 4.6 Earnings Blackout
No position may be held through an earnings announcement unless the entire trade thesis IS the earnings play — in which case a separate specialized setup applies (Phase 3+). Default rule: exit any position with earnings inside the expected holding window.

---

## 5. Human Authority Rules

### 5.1 Human Approval Required
Every new discretionary entry requires the human trader to click BUY. The system generates the trade card, defines the entry trigger, and monitors — it does not place opening orders autonomously.

### 5.2 Autonomous Actions Permitted
The system may autonomously (without per-action human approval):
- Update watchlists
- Refresh halal classifications
- Refresh data
- Compute regime, sector, theme, and setup states
- Generate and deliver trade cards
- **Execute pre-defined mechanical exits (stop, target, trail, time-stop) on open positions**
- Send alerts

### 5.3 Human-State Gating
- Before generating any trade cards for the day, the system prompts the human for a state check (sleep, health, focus, stress).
- **If human state check returns NO:** the system generates zero new-entry cards for that day.
- **Mechanical exits on existing positions continue regardless of human state.** This is explicitly a constitutional rule.

### 5.4 Cash Day
- The system is allowed and expected to output "CASH DAY — no new trades" as a valid result.
- "No trade" is a first-class output, not a system failure.

### 5.5 Kill Switches
The system automatically pauses new-entry generation for a specific setup when any of the following triggers fire:
- Rolling 12-week expectancy for the setup turns negative
- Rolling drawdown on setup exceeds 2x historical worst-case
- Slippage on the setup exceeds modeled slippage by > 50% for 20+ trades
- Data quality incident (Spec 02) affecting the setup's inputs
- Regime classifier reports a regime the setup is not authorized to trade in
- Halal classification for held or watchlisted stock becomes uncertain

**A paused setup requires manual re-authorization by the trader after review.**

---

## 6. What the Algorithm Does NOT Know

Explicitly forbidden from being encoded into the system:

### 6.1 Return Targets
There is no target return in the algorithm. Not in the config. Not in a KPI dashboard. Not in an alert. Not in a comment. The trader's private mental target lives only in the personal journal.

### 6.2 Weekly Income Goals
There is no weekly, monthly, or yearly income goal in the system. Drawdown-adjusted expectancy is the only optimization target.

### 6.3 Prediction Language
The system never says "will go up," "will hit target," "will succeed." It says "historical similar setups produced X outcome Y% of the time" and "current risk/reward is Z." No forward-looking claims.

### 6.4 Trader Emotion
The system does not adjust behavior because the trader "feels good" or "feels lucky." State check is binary (fit to trade or not), never scaled.

---

## 7. Change Control

### 7.1 During Trading
The Trading Constitution is IMMUTABLE during any active paper-trading or live-trading window. Changes require:
1. Full flat portfolio (zero open positions)
2. Written change proposal with impact analysis on all downstream specs
3. Review by strongest available reasoning model
4. Approval by the human trader
5. Re-validation of any affected downstream spec via full research cycle

### 7.2 Between Trading Windows
Amendments are permitted but must be recorded in this document with:
- Date of change
- Reason
- Superseded rule (verbatim)
- New rule (verbatim)
- Validation trigger fired

---

## 8. Stories

### Story 1.1 — Constitutional Configuration Schema
**As:** engineering
**I want:** a typed configuration object that encodes every rule in this constitution
**So that:** downstream systems can query the current constitutional state programmatically and no rule is hardcoded in multiple places

**Acceptance criteria:**
- All numeric thresholds in this document appear in one config file
- Config is validated on load (fails fast if any value is out of range)
- Config version is stamped on every generated trade card
- Config is read-only after startup; changes require restart
- Unit tests confirm every rule maps to a config field

### Story 1.2 — Halal Standard Selection
**As:** the trader
**I want:** to select which Shariah standard is active (AAOIFI, Islamicly, custom)
**So that:** I can align the system with my chosen scholarly opinion without a code change

**Acceptance criteria:**
- Configuration field `halal_standard` accepts one of: `aaoifi_zoya`, `islamicly`, `wahed`, `custom`
- Each option is documented with its business exclusions and ratio thresholds
- Changing the standard is logged as a constitutional amendment event
- Historical halal tagging respects the standard active *at that historical date*, not today's standard

### Story 1.3 — Kill Switch Registry
**As:** the trader
**I want:** every kill switch to be explicit, named, and observable
**So that:** when a setup pauses, I know exactly which switch fired and why

**Acceptance criteria:**
- Registry of all kill switches (rolling expectancy, drawdown, slippage, data quality, regime, halal)
- Each kill switch has a name, trigger condition, and pause scope (which setups it affects)
- When a switch fires, an alert is sent with the switch name and observed values
- A paused setup cannot generate new-entry cards until manual re-authorization
- Re-authorization is a logged, timestamped event

### Story 1.4 — Human-State Check Interaction
**As:** the trader
**I want:** a fast (< 30 second) morning state check
**So that:** the system knows whether to generate new-entry cards today, without becoming an obstacle

**Acceptance criteria:**
- State check prompts: sleep hours, physical state, life stress, focus quality
- Any single "NO" flags the day as CASH DAY
- CASH DAY status is honored for 24 hours or until manually cleared
- Mechanical exits on open positions continue during CASH DAY
- State check history is journaled (used later to correlate state with P&L)

### Story 1.5 — Constitutional Amendment Log
**As:** the trader and any auditor
**I want:** a permanent record of every constitutional amendment
**So that:** we can reconstruct exactly what rules were in effect at any historical point

**Acceptance criteria:**
- Append-only amendment log stored durably
- Each amendment records: date, reason, old rule text, new rule text, validation triggered, approver
- Any live trade card references the constitution version in effect at the time
- Backtests must load the constitution version in effect at the historical trade date

---

## 9. Acceptance Criteria for Spec 01

- All rules in sections 2–7 are enumerated in the configuration schema
- All stories 1.1–1.5 pass acceptance criteria
- A dry-run simulation demonstrates that a haram stock, a leveraged trade, a short trade, and an over-sized trade are all rejected before any downstream evaluation
- The strongest available reasoning model has reviewed this spec and returned APPROVED with any correction notes addressed

---

## 10. Open Questions for the Trader

1. **Halal standard choice:** confirm AAOIFI-via-Zoya as the default, or select another.
2. **Weapons stocks:** confirm exclusion (personal choice, not a scholarly rule for all).
3. **Reserve size:** confirm $5K, $10K, or a percentage.
4. **State check timing:** morning-only, or also before evening cards are viewed?
5. **Kill-switch re-authorization:** manual only, or auto after N days of positive expectancy return?
