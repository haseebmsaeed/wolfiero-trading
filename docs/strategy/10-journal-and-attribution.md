# Spec 10 — Journal & Attribution

**Status:** Draft
**Phase:** 3
**Depends on:** Specs 01–09
**Downstream:** All future improvement to the system routes through Journal data

---

## 1. Purpose

The Journal is the **permanent, immutable record of every trade card generated, every decision made, every fill received, every exit executed, and every prediction versus outcome.** It is the source of truth for:

- Post-trade attribution ("did the trade work? why or why not?")
- Systematic-drift detection ("is the live system executing what the backtester promised?")
- Setup decay detection (Spec 01 §5.5, Spec 05 §3.3)
- Human behavior tracking ("did the trader follow the plan?")
- Quarterly and annual review

**Neither the trader nor any AI can improve a system whose actual behavior is not measured.** The Journal is where measurement lives.

---

## 2. Guiding Principles

### P1 — Immutable, Append-Only
Once written, a Journal record is never modified. Corrections are new records that supersede prior ones.

### P2 — Complete
Every card, every fill, every exit, every state check, every kill-switch event is journaled. Silent operations are not permitted.

### P3 — Pre-Trade Prediction, Post-Trade Actual
Every trade records both:
- **Prediction:** what the system said should happen (entry, stop, target, expected hold, expected R, model probability, historical expectancy)
- **Actual:** what did happen (actual fills, actual exits, actual R, actual hold, actual slippage)

Drift between prediction and actual is the primary QA signal.

### P4 — Attribution Fields on Every Trade
Every trade record includes: setup, regime at entry, sector, theme, sample-size bucket, model version, prompt version, config version, human state at approval. This allows any performance breakdown.

### P5 — Reviewable Quarterly
Journal must produce a standardized quarterly attribution report without manual data wrangling.

### P6 — Per-Setup Isolation
DC20 and PBK are tracked as **fully isolated setups**. Their trades, orders, fills, positions, expectancy tables, kill switches, adherence rates, and reports are independent. Cross-setup comparison views exist, but no computation blends the two setups' outcomes into a single number that would obscure per-setup edge or decay.

**Concretely:**
- Journal queries scoped by `setup_id` return only that setup's records
- Per-setup expectancy tables are the default; combined-portfolio view is a separate, explicitly-labeled report
- A kill switch fires per-setup based on that setup's own metrics
- Adherence rate is computed per-setup
- Comparative dashboards must display setups side-by-side, never merged

---

## 3. Data Model (High Level)

### 3.1 Card Record
```
card_id: uuid
generated_at: timestamp
ticker: string
setup: string
config_version: string
constitution_version: string

# All upstream inputs (halal, regime, sector, stock, setup, stats, model, analyst)
halal_status: object
regime_snapshot: object
sector_context: object
stock_context: object
setup_context: object
historical_stats: object
model_prediction: object
analyst_output: object
portfolio_context: object

# Trade plan
entry_trigger_price: decimal
stop_price: decimal
target_price: decimal
shares: int
capital_planned: decimal
risk_planned: decimal

# Severity summary
green_flags: array
yellow_flags: array
red_flags: array

# Human state at generation
human_state_check: object

# Decision
decision: enum (APPROVED / REJECTED / EXPIRED / SNOOZED)
decision_at: timestamp
decision_reason: string  # if REJECTED
```

### 3.2 Order Event
```
event_id: uuid
card_id: uuid  # link back
order_id: string  # broker order id
event_type: enum (PLACED / MODIFIED / CANCELLED / FILLED / REJECTED)
event_at: timestamp
order_type: enum (BUY_STOP / STOP_LOSS / LIMIT / MARKET)
price: decimal
shares: int
broker_message: string
```

### 3.3 Fill Event
```
fill_id: uuid
order_id: string
card_id: uuid
filled_at: timestamp
side: enum (BUY / SELL)
shares_filled: int
fill_price: decimal
expected_price: decimal
slippage_dollars: decimal
commission: decimal
```

### 3.4 Position Lifecycle Record
```
position_id: uuid
card_id: uuid
opened_at: timestamp
closed_at: timestamp
setup: string
ticker: string
entry_shares: int
entry_avg_price: decimal
initial_stop: decimal
initial_target: decimal
exits: array of ExitEvent

# Outcome
exit_reason: enum (STOP / TARGET_PARTIAL / TRAIL / TIME_STOP / REGIME_EXIT / HALAL_EXIT / EARNINGS_EXIT / MANUAL / DELISTED)
final_pnl_dollars: decimal
final_r_multiple: decimal
holding_days: int

# Attribution
regime_at_entry: string
regime_at_exit: string
sector: string
theme: string
sample_bucket: string
model_version: string
prompt_version: string
config_version: string

# Drift analysis
predicted_expectancy: decimal
predicted_r: decimal
predicted_hold_days: int
predicted_win_probability: decimal
slippage_vs_modeled: decimal
adherence: enum (FULL / PARTIAL / DEVIATED)
adherence_notes: string
```

### 3.5 System Event
For non-trade events:
```
event_id: uuid
event_at: timestamp
event_type: enum
  (KILL_SWITCH_FIRED / DATA_QUALITY_INCIDENT / MODEL_DEGRADED /
   HALAL_RECLASSIFICATION / REGIME_CHANGE / HUMAN_STATE_CHECK /
   CONSTITUTIONAL_AMENDMENT / CONFIG_CHANGE / PROVIDER_OUTAGE)
context: object  # event-specific detail
```

### 3.6 Human-State Check Record
```
check_id: uuid
performed_at: timestamp
sleep_ok: bool
health_ok: bool
stress_ok: bool
focus_ok: bool
result: enum (PASSED / CASH_DAY)
notes: string
```

---

## 4. Attribution Views

The Journal supports these standard views without ad-hoc queries:

### 4.1 Per-Setup Attribution (Rolling 12M / 24M / All-Time)
- Total trades, wins, losses
- Win rate, avg winner, avg loser, expectancy
- Per-regime breakdown
- Per-sector breakdown
- Adherence rate

### 4.2 Prediction vs Actual Drift Report
Weekly, quarterly, and yearly:
- Actual expectancy vs predicted expectancy per setup
- Actual slippage vs modeled slippage
- Actual holding period vs predicted holding period
- Actual win rate vs model-predicted win rate
- Drift > threshold triggers an investigation flag

### 4.3 Human Behavior Report
- Trades approved / rejected / snoozed / expired counts
- Approve latency (time from card to approval)
- Rate of approval on 🟡 flagged cards
- Rate of manual deviations from mechanical exits
- Trade P&L when human state was PASSED vs CASH_DAY history

### 4.4 System Health Report
- Kill-switch fire count per week
- Data quality incidents
- Provider outages
- Model degradation events
- Halal reclassifications affecting held positions

### 4.5 Quarterly Attribution Report (formal)
Comprehensive report generated at end of each calendar quarter:
- Sections: overview, per-setup, per-regime, drift, human behavior, system health, recommendations
- Delivered to trader; reviewed jointly with the reasoning model

---

## 5. Adherence Tagging

Every closed position is tagged for adherence:

| Tag | Meaning |
|-----|---------|
| **FULL** | Every action matched the plan: entry filled, exits executed per rules, no manual intervention |
| **PARTIAL** | Minor deviation: e.g., approved 5 min past trigger, or partial fill outside modeled slippage |
| **DEVIATED** | Manual intervention against the rules: e.g., manually widened stop, held past time-stop |

Adherence tagging is applied by the runtime, not the trader. Trader can annotate but cannot change the tag.

**Adherence rate is a first-class KPI.** A profitable strategy with low adherence rate is a trader-luck strategy, not a system-driven one.

---

## 6. Retention and Storage

### 6.1 Retention
All Journal records retained indefinitely. Storage cost is trivial; historical continuity is invaluable.

### 6.2 Backup
- Daily backup to durable cloud storage
- Weekly integrity check (row counts, checksums)
- Monthly disaster-recovery drill (restore from backup, verify)

### 6.3 Access Control
- Read: trader, review models, reporting jobs
- Write: runtime processes only (no manual edits)
- Corrections: append a new record with reason; original preserved

---

## 7. Integrations

### 7.1 To Research Engine (Spec 05)
- Real Journal trade log fed into Research Engine to compute live-derived expectancy tables
- Compared to backtested expectancy for drift detection

### 7.2 To Trade Card (Spec 09)
- Card generation queries Journal for recent similar-setup outcomes to show on card
- Card generation queries Journal for open positions (feeds Portfolio Engine)

### 7.3 To Kill Switches (Spec 01, 05)
- Journal rolling windows feed decay detection
- Journal slippage tracking feeds slippage kill switch

### 7.4 Export
- CSV export by date range or setup for external analysis
- Read-only API for reporting tools

---

## 8. Stories

### Story 10.1 — Card Record Persistence
**As:** the runtime
**I want:** every trade card persisted with full context at generation time
**So that:** the exact inputs behind every decision are recoverable

**Acceptance criteria:**
- Storage schema per §3.1
- Card written atomically at generation
- Idempotent by `card_id`
- Retrieval by card_id, ticker, date range

### Story 10.2 — Order and Fill Event Recording
**As:** the execution engine
**I want:** every broker interaction and every fill journaled
**So that:** the full order lifecycle is auditable

**Acceptance criteria:**
- Storage per §3.2 and §3.3
- Events linked back to card_id
- Slippage computed on every fill
- No fill missing from Journal (integration test: mock 100 fills, all present)

### Story 10.3 — Position Lifecycle Closure
**As:** the execution engine
**I want:** each closed position aggregated into a lifecycle record per §3.4
**So that:** attribution is straightforward

**Acceptance criteria:**
- Position record built from opening card + all fills + exit event
- Final P&L, R multiple, holding days computed correctly
- Attribution tags set (regime, sector, model version, etc.)
- Prediction vs actual fields populated
- Adherence tag applied per §5

### Story 10.4 — Adherence Tagging Logic
**As:** the runtime
**I want:** automatic adherence classification per §5
**So that:** manual bias does not enter adherence tracking

**Acceptance criteria:**
- Rule set for FULL / PARTIAL / DEVIATED
- Tag applied at position close
- Immutable once applied (annotations allowed, tag change not)

### Story 10.5 — System Event Log
**As:** the runtime
**I want:** every non-trade event (kill switch, data incident, regime change, human state check, config change) journaled
**So that:** system behavior is fully traceable

**Acceptance criteria:**
- Storage per §3.5
- Every enumerated event type has a producer
- Retrievable by type, date range

### Story 10.6 — Prediction-vs-Actual Drift Report
**As:** the researcher
**I want:** a weekly drift report per §4.2
**So that:** systematic drift is detected before it becomes a blowup

**Acceptance criteria:**
- Weekly job produces the report
- Drift metrics: expectancy delta, slippage delta, hold-time delta, win-rate delta
- Thresholds trigger investigation flags
- Report delivered to trader

### Story 10.7 — Quarterly Attribution Report
**As:** the trader
**I want:** a comprehensive quarterly report per §4.5
**So that:** I can conduct disciplined quarterly review

**Acceptance criteria:**
- Report generated automatically at end of quarter
- Covers all §4 views
- Delivered via email or dashboard
- Prior quarters accessible for comparison

### Story 10.8 — Human Behavior Report
**As:** the trader
**I want:** a monthly view of my own behavior per §4.3
**So that:** I can see where discipline is slipping

**Acceptance criteria:**
- Monthly job produces report
- Includes approve/reject/expire counts, approve latency, adherence rate
- Correlates human-state check to P&L over time
- Delivered privately (not embedded in trade cards)

### Story 10.9 — Backup and Recovery
**As:** engineering
**I want:** daily backup and monthly restore drill
**So that:** Journal is durable

**Acceptance criteria:**
- Daily backup to cloud storage
- Backup integrity check (checksum, row counts)
- Monthly restore drill validates recoverability
- Alert on any backup failure

### Story 10.10 — CSV Export and Read-Only API
**As:** the trader / researcher
**I want:** external tools able to read Journal data
**So that:** analysis is not gated on the internal system

**Acceptance criteria:**
- CSV export by date range and setup
- Read-only REST API with authenticated access
- Rate limits to prevent abuse
- Access logged

### Story 10.11 — Journal Feed to Research Engine
**As:** the research engine
**I want:** live Journal trade data flowing into expectancy computations
**So that:** live-derived and backtest-derived expectancy are comparable

**Acceptance criteria:**
- Research engine can produce expectancy tables from Journal trades
- Comparison view: backtest expectancy vs live expectancy per regime cell
- Divergence beyond threshold triggers investigation

### Story 10.12 — Correction Workflow
**As:** the trader / auditor
**I want:** ability to correct records without mutating history
**So that:** errors can be fixed without losing audit trail

**Acceptance criteria:**
- Correction is a new record with `supersedes: old_record_id` and `correction_reason`
- Original preserved
- Reports use the latest non-superseded record for each entity
- All corrections themselves logged as System Events

### Story 10.13 — Per-Setup Isolation Enforcement
**As:** engineering
**I want:** every record in the Journal partitioned by `setup_id`
**So that:** per-setup analytics cannot accidentally blend data across setups

**Acceptance criteria:**
- All record schemas include mandatory `setup_id` field (`DC20` or `PBK` in Phase 1)
- All query APIs default to a `setup_id` filter; combined queries require explicit `setups=[...]` argument
- All expectancy computations, decay signals, drawdown metrics, adherence rates, and kill switches operate per-setup by default
- Test: writing a record without `setup_id` fails validation
- Test: querying "all trades" returns per-setup grouped result unless explicitly overridden

### Story 10.14 — Side-by-Side Setup Comparison Report
**As:** the trader
**I want:** a comparison view showing DC20 and PBK metrics side by side over the same time period
**So that:** I can objectively evaluate which setup fits me better after N trades

**Acceptance criteria:**
- Report generated on demand and monthly
- Columns: DC20 | PBK
- Rows: trades, win rate, avg winner (R), avg loser (R), expectancy (R), max drawdown, adherence rate, avg holding period, best regime, worst regime, active/paused status
- Delivered as HTML/PDF and via Telegram command `/compare setups`
- Includes annotation: minimum ~30 trades per setup before drawing conclusions

### Story 10.15 — Per-Setup Kill Switch Scope
**As:** the runtime
**I want:** every kill switch scoped to its setup (unless the trigger is global)
**So that:** a decay event on one setup does not silence the other

**Acceptance criteria:**
- Kill-switch records include `scope: setup_id | global`
- Setup-scoped kill switches fire based on that setup's rolling metrics only
- Global kill switches (data outage, regime=BEAR, halal reclassification of specific stock) documented explicitly
- Test: injecting negative rolling expectancy on DC20 pauses DC20 only, not PBK

---

## 9. Acceptance Criteria for Spec 10

- All stories 10.1–10.12 pass their acceptance criteria
- End-to-end: card generated → approved → filled → exited → position record populated with all attribution and adherence
- Drift report correctly detects a deliberately injected drift
- Restore drill successfully recovers Journal from backup
- Strongest available reasoning model has reviewed and APPROVED

---

## 10. Open Questions for the Trader

1. **Storage backend:** Firestore (aligns with existing project) or Postgres for reporting workloads?
2. **Retention:** confirm indefinite retention.
3. **Adherence tag manual override:** allow trader to annotate but never modify — confirm?
4. **Quarterly report delivery:** email PDF, Telegram, or web dashboard?
5. **Human-state-to-P&L correlation:** OK to surface publicly to the trader, or private-only?
