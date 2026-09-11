# Wolfiero — Data Model

**Status:** Draft v1.0 · PostgreSQL 16 · SQLAlchemy 2.0 + Alembic

---

## Design principles

1. **Snapshots are immutable.** A candidate, a recommendation, or a regime reading belongs to a
   point in time and is never updated in place. Outcomes are recorded in *separate* rows. This is
   what makes "did my ideas work?" answerable without the analysis being contaminated by hindsight.
2. **Every analytical artefact is version-stamped** with `strategy_version` and, where an LLM was
   involved, `model_provider` / `model_name` / `prompt_version`. Without this, changing a weight
   silently invalidates all history.
3. **JSONB for shape-unstable payloads** (raw vendor responses, score breakdowns, classification
   output); real columns for anything you filter, sort, or join on.
4. **All timestamps `TIMESTAMPTZ`, stored UTC.** Trading *dates* are `DATE` in market time — a bar
   belongs to a session, not to an instant, and conflating the two breaks every alignment.
5. **Money as `NUMERIC(18,4)`.** Never float. Accumulated float error in P&L is indefensible.

---

## Entity overview

```
strategy_versions ──┐
                    ├──< scan_runs ──< candidates ──< recommendations ──< recommendation_outcomes
market_regimes ─────┘                      │
                                           │
stocks ──< price_history                   │
  │  ├──< news_items                       │
  │  ├──< earnings_events                  │
  │  ├──< watchlist_items                  │
  │  └──< positions ──< position_events    │
  │                                        │
alerts ──< alert_firings                   │
reports ───────────────────────────────────┘
agent_runs ──< model_runs
```

---

## Reference & market data

### `stocks`
The symbol master. One row per tradeable instrument.

| Column | Type | Notes |
|---|---|---|
| `id` | BIGSERIAL PK | |
| `symbol` | VARCHAR(16) UNIQUE NOT NULL | Canonical internal form; adapters normalise vendor variants |
| `name` | TEXT | |
| `exchange` | VARCHAR(16) | |
| `asset_type` | ENUM(`COMMON_STOCK`,`ETF`,`ADR`) | |
| `sector` / `industry` | VARCHAR(64) | Drives concentration limits and sector rotation |
| `market_cap` | NUMERIC(20,2) | Refreshed weekly |
| `shares_outstanding` | BIGINT | |
| `is_active` | BOOLEAN DEFAULT TRUE | Delisted symbols are deactivated, **never deleted** — history must survive |
| `in_universe` | BOOLEAN | Passed the latest liquidity screen |
| `is_blocklisted` | BOOLEAN | Operator override |
| `first_trade_date` | DATE | Enforces the minimum-history rule |
| `fundamentals` | JSONB | Vendor-shaped; cached 7 days |
| `fundamentals_updated_at` | TIMESTAMPTZ | |
| `created_at` / `updated_at` | TIMESTAMPTZ | |

Indexes: `symbol`, `(in_universe, is_active)`, `sector`.

### `price_history`
Adjusted daily bars. The largest table: ~3,000 symbols × ~400 days ≈ 1.2M rows, growing ~3,000/day.

| Column | Type | Notes |
|---|---|---|
| `stock_id` | BIGINT FK | |
| `trade_date` | DATE | Market-local session date |
| `open`/`high`/`low`/`close` | NUMERIC(18,4) | **Split- and dividend-adjusted** |
| `volume` | BIGINT | |
| `adjusted` | BOOLEAN DEFAULT TRUE | Guard against a future raw-bar source sneaking in |
| `source` | VARCHAR(32) | Provider name — invaluable when two vendors disagree |
| `ingested_at` | TIMESTAMPTZ | |

PK `(stock_id, trade_date)`. Index `(trade_date)` for cross-sectional breadth queries.

> **Why store bars at all rather than fetching on demand?** Three reasons: the scanner touches
> 3,000 symbols and vendor rate limits make live fetching impossible inside the time budget; bars
> for closed sessions never change, so re-fetching is pure waste; and you need a point-in-time
> record to reconstruct why a past recommendation was made.

---

## Regime & strategy

### `market_regimes`
One row per trading day.

| Column | Type | Notes |
|---|---|---|
| `id` | BIGSERIAL PK | |
| `trade_date` | DATE UNIQUE | |
| `regime` | ENUM(`RISK_ON`,`NEUTRAL`,`RISK_OFF`) | |
| `confidence` | NUMERIC(4,3) | 0–1 |
| `spy_trend`/`qqq_trend`/`iwm_trend` | VARCHAR(16) | |
| `vix_level` | NUMERIC(8,2) | |
| `vix_change_20d_pct` | NUMERIC(8,2) | Direction of volatility matters more than level |
| `breadth_pct_above_50ma` | NUMERIC(5,2) | % of universe above its 50-day MA |
| `sector_leadership` | JSONB | Ranked sector RS — offensive vs defensive leadership is a regime tell |
| `components` | JSONB | Per-input contribution to the label — explainability |
| `rationale` | TEXT | Human-readable |
| `strategy_version` | VARCHAR(32) | |
| `computed_at` | TIMESTAMPTZ | |

### `strategy_versions`
The published parameter sets. Append-only.

| Column | Type | Notes |
|---|---|---|
| `version` | VARCHAR(32) PK | e.g. `v1.0.0` |
| `weights` | JSONB | Full scoring weight set |
| `thresholds` | JSONB | Liquidity floors, R:R minimum, hold window, etc. |
| `notes` | TEXT | *Why* this version differs — the most valuable column here |
| `activated_at` / `deactivated_at` | TIMESTAMPTZ | |

---

## Scanning

### `scan_runs`

| Column | Type | Notes |
|---|---|---|
| `id` | BIGSERIAL PK | |
| `run_id` | UUID UNIQUE | Correlates with logs and `model_runs` |
| `trade_date` | DATE | |
| `started_at` / `completed_at` | TIMESTAMPTZ | |
| `status` | ENUM(`RUNNING`,`COMPLETED`,`FAILED`,`DEGRADED`) | `DEGRADED` = finished with a data gap |
| `funnel` | JSONB | `[{stage, name, entered, exited, dropped_reasons:{...}}]` |
| `universe_size` / `candidates_found` | INT | |
| `data_coverage_pct` | NUMERIC(5,2) | Below the gate → run aborts |
| `strategy_version` | VARCHAR(32) | |
| `market_regime_id` | BIGINT FK | |
| `error` | TEXT | |

UNIQUE `(trade_date, strategy_version)` — enforces idempotent re-runs.

> The `funnel` column is the debugging tool for the whole system. When a morning returns zero
> candidates, it tells you *instantly* whether the market genuinely offered nothing or stage 3
> accidentally filtered everything out.

### `candidates`
Immutable per-scan snapshot.

| Column | Type | Notes |
|---|---|---|
| `id` | BIGSERIAL PK | |
| `scan_run_id` | BIGINT FK | |
| `stock_id` | BIGINT FK | |
| `rank` | INT | |
| `score` | NUMERIC(6,2) | 0–100 composite |
| `score_breakdown` | JSONB | Per-component raw, normalised, weighted contribution |
| `setup_type` | ENUM(`BREAKOUT`,`PULLBACK`,`CONSOLIDATION`,`MOMENTUM`,`NONE`) | |
| `setup_quality` | NUMERIC(4,3) | Graded, not boolean |
| `direction` | ENUM(`LONG`,`SHORT`) | |
| `technicals` | JSONB | The full `TechnicalSnapshot` as of that date |
| `price_at_scan` | NUMERIC(18,4) | |
| `entry_trigger`/`stop_price`/`target_price` | NUMERIC(18,4) | |
| `reward_risk` | NUMERIC(6,2) | |
| `suggested_shares` | INT | |
| `suggested_risk_usd` | NUMERIC(18,2) | |
| `vetoed` | BOOLEAN | |
| `veto_reasons` | JSONB | e.g. `["EARNINGS_IN_WINDOW","RR_BELOW_FLOOR"]` |
| `has_catalyst` | BOOLEAN | |
| `created_at` | TIMESTAMPTZ | |

Indexes: `(scan_run_id, rank)`, `(stock_id, created_at)`.

> **Why persist vetoed candidates instead of dropping them?** Because "what did the veto cost me?"
> is a question worth answering. If earnings-vetoed setups consistently outperform, the policy is
> wrong and only the data will tell you.

---

## Recommendations & outcomes

### `recommendations`
A candidate actually surfaced to the operator. **Frozen at creation.**

| Column | Type | Notes |
|---|---|---|
| `id` | BIGSERIAL PK | |
| `candidate_id` | BIGINT FK | |
| `stock_id` | BIGINT FK | |
| `report_id` | BIGINT FK NULL | Where it was delivered |
| `recommended_at` | TIMESTAMPTZ | |
| `trade_date` | DATE | |
| `direction` | ENUM | |
| `setup_type` | ENUM | Denormalised deliberately — candidates could be pruned; this must survive |
| `entry_price`/`stop_price`/`target_price` | NUMERIC(18,4) | |
| `reward_risk` / `score` / `confidence` | NUMERIC | |
| `thesis` | TEXT | The AI-written rationale |
| `catalyst_summary` | TEXT | |
| `risks` | TEXT | |
| `market_regime` | VARCHAR(16) | Denormalised for fast slicing |
| `strategy_version` | VARCHAR(32) | |
| `model_provider`/`model_name`/`prompt_version` | VARCHAR | Enables model-vs-model comparison |
| `status` | ENUM(`OPEN`,`TRIGGERED`,`EXPIRED`,`INVALIDATED`,`CLOSED`) | |

### `recommendation_outcomes`
Written by the forward-tracking job. One row per recommendation, updated until the horizon closes.

| Column | Type | Notes |
|---|---|---|
| `recommendation_id` | BIGINT FK UNIQUE | |
| `entry_triggered` | BOOLEAN | Did price ever reach the trigger? |
| `entry_triggered_at` | DATE | |
| `max_favorable_excursion_pct` | NUMERIC(8,3) | Best it got — measures whether the *target* was reasonable |
| `max_adverse_excursion_pct` | NUMERIC(8,3) | Worst it got — measures whether the *stop* was reasonable |
| `hit_target` / `hit_stop` | BOOLEAN | |
| `first_hit` | ENUM(`TARGET`,`STOP`,`NEITHER`) | Order matters; both can happen in a horizon |
| `realized_r_multiple` | NUMERIC(8,3) | The single most important performance number |
| `return_pct_at_horizon` | NUMERIC(8,3) | |
| `days_to_resolution` | INT | |
| `benchmark_return_pct` | NUMERIC(8,3) | SPY over the same window — **alpha, not just return** |
| `horizon_days` | INT | |
| `is_final` | BOOLEAN | Horizon closed |
| `evaluated_at` | TIMESTAMPTZ | |

> MFE/MAE are what turn outcome data into *improvement*. A strategy with a 35% win rate whose losers
> rarely exceed −0.4 MAE before reversing does not have a selection problem, it has a stop-placement
> problem. Raw win rate cannot distinguish those two cases.

---

## Portfolio

### `positions`

| Column | Type | Notes |
|---|---|---|
| `id` | BIGSERIAL PK | |
| `stock_id` | BIGINT FK | |
| `recommendation_id` | BIGINT FK NULL | Links a real trade back to the idea — powers "do I follow my own system?" |
| `status` | ENUM(`OPEN`,`CLOSED`) | |
| `direction` | ENUM(`LONG`,`SHORT`) | |
| `shares` | NUMERIC(18,4) | |
| `entry_price` / `entry_date` | NUMERIC / DATE | |
| `stop_price` / `target_price` | NUMERIC(18,4) | Mutable — trailing stops are legitimate |
| `initial_stop_price` | NUMERIC(18,4) | **Immutable.** The R denominator must be the *original* risk |
| `exit_price` / `exit_date` | | |
| `realized_pnl` / `realized_r_multiple` | NUMERIC | |
| `thesis` / `exit_reason` | TEXT | |
| `sector` | VARCHAR(64) | Denormalised for concentration checks |

### `position_events`
Append-only audit: `OPENED`, `STOP_MOVED`, `PARTIAL_EXIT`, `ADDED`, `CLOSED`, `THESIS_UPDATED`, with
`event_at`, `payload` JSONB, `note`.

> Without this you cannot reconstruct *when* you moved a stop, which is exactly the behaviour most
> worth auditing in a discretionary trader.

---

## Watchlist & alerts

### `watchlist_items`
`stock_id`, `note`, `target_entry_low`/`_high`, `added_at`, `is_active`, `source` (`MANUAL` | `SCAN`).

### `alerts`
Rule definitions.

| Column | Type | Notes |
|---|---|---|
| `id` | BIGSERIAL PK | |
| `stock_id` | BIGINT FK NULL | NULL for market-wide (e.g. regime change) |
| `alert_type` | ENUM(`PRICE_ABOVE`,`PRICE_BELOW`,`PCT_MOVE`,`VOLUME_SPIKE`,`SETUP_TRIGGERED`,`NEWS_MATERIAL`,`EARNINGS_APPROACHING`,`REGIME_CHANGE`,`STOP_BREACH`,`TARGET_REACHED`) | |
| `condition` | JSONB | Type-specific parameters |
| `is_active` | BOOLEAN | |
| `cooldown_minutes` | INT DEFAULT 60 | |
| `expires_at` | TIMESTAMPTZ | |
| `last_fired_at` | TIMESTAMPTZ | |
| `created_via` | ENUM(`CHAT`,`SYSTEM`,`API`) | |
| `natural_language` | TEXT | The original phrasing — so you can ask "what alerts do I have?" and get your own words back |

### `alert_firings`
`alert_id`, `fired_at`, `trigger_price`, `context` JSONB, `notified` BOOLEAN, `message` TEXT.

---

## News & catalysts

### `news_items`

| Column | Type | Notes |
|---|---|---|
| `id` | BIGSERIAL PK | |
| `stock_id` | BIGINT FK NULL | NULL = macro/market-wide |
| `external_id` | VARCHAR(128) | Vendor id |
| `content_hash` | VARCHAR(64) | SHA-256 of normalised title+body — **the dedup key** |
| `headline` / `summary` / `url` / `source` | | |
| `published_at` | TIMESTAMPTZ | |
| `category` | ENUM(`EARNINGS`,`GUIDANCE`,`ANALYST`,`MA`,`REGULATORY`,`PRODUCT`,`CONTRACT`,`LEGAL`,`INSIDER`,`INDEX`,`MACRO`,`OTHER`) | |
| `direction` | ENUM(`BULLISH`,`BEARISH`,`NEUTRAL`) | |
| `materiality` | NUMERIC(4,3) | 0–1: could this move the stock? |
| `durability` | NUMERIC(4,3) | 0–1: one-day pop vs multi-week re-rating |
| `is_noise` | BOOLEAN | Listicles, auto-generated recaps, promos |
| `classification` | JSONB | Raw model output + reasoning |
| `classified_by_model` / `prompt_version` | VARCHAR | |

UNIQUE `(content_hash)`. Index `(stock_id, published_at DESC)`.

### `earnings_events`

| Column | Type | Notes |
|---|---|---|
| `stock_id` | BIGINT FK | |
| `earnings_date` | DATE | |
| `time_of_day` | ENUM(`BMO`,`AMC`,`UNKNOWN`) | Before/after market — changes which session gaps |
| `is_confirmed` | BOOLEAN | Estimated dates move; confirmed ones do not |
| `fiscal_period` | VARCHAR(16) | |
| `eps_estimate` / `eps_actual` / `surprise_pct` | NUMERIC | |
| `source` / `updated_at` | | |

UNIQUE `(stock_id, earnings_date)`.

> This is the highest-value table per line of code in the system. One avoided earnings gap pays for
> the whole project.

---

## Reports & agent telemetry

### `reports`
`id`, `report_type` ENUM(`PREMARKET`,`MIDDAY`,`END_OF_DAY`,`WEEKLY`,`AD_HOC`), `trade_date`,
`title`, `content_markdown`, `payload` JSONB (the structured data the LLM was given — lets you
re-render or re-synthesise without re-running the pipeline), `scan_run_id`, `market_regime_id`,
`delivered_at`, `delivery_status`, `model_name`, `prompt_version`, `generation_cost_usd`.

UNIQUE `(report_type, trade_date)`.

### `agent_runs`
`run_id` UUID, `trigger` ENUM(`SCHEDULED`,`CHAT`,`MANUAL`), `job_name`, `started_at`,
`completed_at`, `status`, `steps` JSONB (per-step timing/status), `total_cost_usd`, `error`.

### `model_runs`
Per-LLM-call ledger: `agent_run_id`, `purpose`, `provider`, `model`, `prompt_version`,
`input_tokens`, `output_tokens`, `cost_usd`, `latency_ms`, `success`, `error`.

> Two questions this answers that nothing else can: *"where is my AI budget actually going?"* and
> *"is the expensive model producing better recommendations than the cheap one?"* — the latter by
> joining through to `recommendation_outcomes`.

---

## Retention

| Table | Policy |
|---|---|
| `price_history` | Keep 5 years; archive older to Blob |
| `news_items` | Keep 2 years |
| `candidates` | Keep 2 years (top 50 per run); prune deeper tail after 90 days |
| `recommendations`, `*_outcomes`, `positions` | **Keep forever.** Irreplaceable. |
| `model_runs` | Keep 1 year |
| `agent_runs` | Keep 90 days (successes), 1 year (failures) |
