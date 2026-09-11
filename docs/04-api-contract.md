# Wolfiero — API Contract

**Base:** `http://wolfiero-api:8000/api` (internal Docker network)
**Auth:** static bearer token (`X-API-Key`) — single-operator system, no user model
**Format:** JSON in, JSON out. All timestamps ISO-8601 UTC. All money as strings to avoid float drift.

---

## Conventions

**Error envelope** — uniform across every endpoint:

```json
{
  "error": {
    "code": "SYMBOL_NOT_FOUND",
    "message": "No data available for symbol 'XYZQ'.",
    "detail": {"symbol": "XYZQ"},
    "request_id": "9f2c..."
  }
}
```

| Code | HTTP | Meaning |
|---|---|---|
| `SYMBOL_NOT_FOUND` | 404 | Not in universe / no data |
| `INSUFFICIENT_HISTORY` | 422 | Fewer bars than the indicator needs |
| `DATA_QUALITY_ERROR` | 422 | Bars failed validation |
| `PROVIDER_UNAVAILABLE` | 503 | All providers in the chain are down |
| `STALE_DATA` | 200 + `warnings[]` | Served, but flagged — **never fail silently on staleness** |
| `SCAN_IN_PROGRESS` | 409 | A scan for this date is already running |
| `RISK_LIMIT_BREACHED` | 422 | Would exceed heat or concentration caps |

**Every success response carries a `meta` block.** This is what the agent layer uses to be honest
about freshness — it is not optional decoration.

```json
"meta": {
  "request_id": "9f2c...",
  "as_of": "2026-09-10T13:45:00Z",
  "data_source": "alpaca",
  "is_stale": false,
  "strategy_version": "v1.0.0",
  "warnings": []
}
```

---

## Health

### `GET /health`
Liveness. `{"status":"ok"}`.

### `GET /health/deep`
```json
{
  "status": "degraded",
  "database": {"ok": true, "latency_ms": 3},
  "providers": {
    "market_data": {"active": "yahoo", "primary": "alpaca", "circuit": "OPEN"},
    "news": {"active": "vendor", "circuit": "CLOSED"},
    "ai": {"circuit": "CLOSED"}
  },
  "last_pipeline_run": {"date": "2026-09-10", "status": "COMPLETED", "completed_at": "..."},
  "data_freshness": {"latest_bar_date": "2026-09-09", "coverage_pct": 99.2},
  "ai_spend_mtd_usd": "18.40"
}
```

---

## Stocks

### `POST /api/stocks/analyze`
The workhorse. Full technical read on one symbol.

Request: `{"symbol": "NVDA", "include_news": false, "lookback_days": 400}`

```json
{
  "symbol": "NVDA",
  "name": "NVIDIA Corporation",
  "sector": "Technology",
  "price": {
    "last": "182.44", "change": "2.13", "change_pct": "1.18",
    "open": "180.50", "high": "183.10", "low": "179.88",
    "volume": 41230000, "as_of": "2026-09-10T13:45:00Z", "is_realtime": true
  },
  "trend": {
    "direction": "UPTREND", "strength": 0.78,
    "above_20_ema": true, "above_50_sma": true, "above_200_sma": true,
    "ma_stack_aligned": true, "slope_50_sma_20d_pct": "4.2"
  },
  "momentum": {
    "rsi_14": "62.3",
    "macd": {"line": "2.14", "signal": "1.88", "histogram": "0.26", "state": "BULLISH_ABOVE_ZERO"},
    "roc_20d_pct": "8.4"
  },
  "volatility": {
    "atr_14": "5.62", "atr_pct_of_price": "3.08",
    "realized_vol_20d_pct": "34.1", "volatility_regime": "NORMAL",
    "bollinger_width_percentile": 22
  },
  "volume": {
    "avg_20d": 38400000, "ratio_vs_avg": "1.07",
    "dollar_volume_20d": "7003000000", "trend": "INCREASING"
  },
  "relative_strength": {
    "vs_spy_1m": "6.2", "vs_spy_3m": "14.8", "vs_spy_6m": "21.0",
    "percentile_rank": 88, "vs_sector_3m": "9.1"
  },
  "levels": {
    "support": [{"price":"171.20","strength":0.82,"touches":3,"type":"SWING_LOW"},
                {"price":"168.40","strength":0.61,"touches":2,"type":"MA_50"}],
    "resistance": [{"price":"186.90","strength":0.74,"touches":2,"type":"SWING_HIGH"}],
    "week_52_high": "191.20", "week_52_low": "96.30",
    "pct_from_52w_high": "-4.6"
  },
  "setup": {
    "type": "PULLBACK", "quality": 0.71, "direction": "LONG",
    "description": "Retraced to the rising 20-EMA after an 11% advance; volume contracting on the pullback.",
    "triggered": false, "trigger_condition": "Close above 183.10 on >1.2x average volume"
  },
  "data_quality": {"bars_available": 400, "last_bar_date": "2026-09-09", "gaps_detected": 0},
  "meta": { }
}
```

> **Contract note for implementers:** every field here is computed by Python. The endpoint never
> calls an LLM. `description` is a *templated* string built from the detector's own outputs, not
> generated prose — it must be reproducible.

### `POST /api/stocks/trade-plan`
Request: `{"symbol":"NVDA","direction":"LONG","account_equity":"100000","risk_pct":"1.0"}`

```json
{
  "symbol": "NVDA", "direction": "LONG", "valid": true,
  "entry": {"trigger":"183.10","type":"BREAKOUT_STOP","rationale":"Above the pullback high"},
  "stop": {"price":"175.80","method":"STRUCTURE_AND_ATR","distance_pct":"3.99",
           "rationale":"Below the 20-EMA and the prior swing low at 176.40, widened by 0.5 ATR"},
  "targets": [
    {"price":"199.00","rationale":"Measured move from the base","r_multiple":"2.18"},
    {"price":"191.20","rationale":"52-week high — partial exit zone","r_multiple":"1.11"}
  ],
  "reward_risk": "2.18",
  "sizing": {"risk_usd":"1000.00","risk_per_share":"7.30","shares":136,
             "position_value":"24901.60","pct_of_equity":"24.90"},
  "risk_checks": {"passes_rr_floor":true,"passes_heat_limit":true,
                  "passes_sector_limit":true,"earnings_in_window":false,
                  "projected_portfolio_heat_pct":"4.2"},
  "warnings": ["Position value is 24.9% of equity despite 1% risk — stop is tight; consider a cap."],
  "meta": { }
}
```

If `valid: false`, `invalid_reasons` lists machine-readable codes (`RR_BELOW_FLOOR`,
`EARNINGS_IN_WINDOW`, `HEAT_LIMIT`, `NO_VALID_STOP`).

### `GET /api/stocks/{symbol}/history?days=120&interval=1d`
Raw adjusted bars. For charting and debugging.

---

## Regime

### `GET /api/regime/current`
```json
{
  "trade_date": "2026-09-10", "regime": "RISK_ON", "confidence": 0.78,
  "indices": {
    "SPY": {"trend":"UPTREND","above_50ma":true,"above_200ma":true,"pct_from_50ma":"2.1"},
    "QQQ": {"trend":"UPTREND","above_50ma":true,"above_200ma":true,"pct_from_50ma":"3.4"},
    "IWM": {"trend":"RANGE","above_50ma":true,"above_200ma":false,"pct_from_50ma":"0.4"}
  },
  "volatility": {"vix":"14.80","vix_change_20d_pct":"-12.4","state":"LOW_AND_FALLING"},
  "breadth": {"pct_above_50ma":"64.2","advance_decline_10d":"1.34","new_highs_vs_lows":"3.10"},
  "sector_leadership": {
    "leading":["Technology","Industrials","Financials"],
    "lagging":["Utilities","Staples"],
    "posture":"OFFENSIVE"
  },
  "components": {"index_trend":0.85,"breadth":0.72,"volatility":0.80,"leadership":0.70},
  "rationale": "All three major indices hold their 50-day averages with QQQ leading. Breadth is healthy at 64% above the 50-day and volatility is low and falling. Sector leadership is offensive. Conditions favour full position sizing on long setups.",
  "position_size_multiplier": "1.0",
  "changed_from_previous": false,
  "meta": { }
}
```

`position_size_multiplier` is the number the sizing service consumes — 1.0 in `RISK_ON`, 0.6 in
`NEUTRAL`, 0.0–0.3 in `RISK_OFF`. Exposing it keeps the regime→sizing link explicit and testable.

### `GET /api/regime/history?days=90`

---

## Scanner

### `POST /api/scanner/run`
Triggers a scan. Long-running → returns immediately.

Request: `{"trade_date":"2026-09-10","force":false,"max_candidates":20}`
Response `202`: `{"run_id":"...","status":"RUNNING","estimated_seconds":420}`

### `GET /api/scanner/runs/{run_id}`
Status plus the funnel — **the primary debugging surface**:

```json
{
  "run_id":"...","trade_date":"2026-09-10","status":"COMPLETED",
  "duration_seconds":389,"data_coverage_pct":"99.2","strategy_version":"v1.0.0",
  "funnel":[
    {"stage":1,"name":"universe","entered":3012,"exited":3012},
    {"stage":2,"name":"liquidity","entered":3012,"exited":1487,
     "dropped":{"below_dollar_volume":1203,"below_price":221,"insufficient_history":101}},
    {"stage":3,"name":"technical","entered":1487,"exited":512,
     "dropped":{"not_in_uptrend":806,"weak_relative_strength":169}},
    {"stage":4,"name":"setup_detection","entered":512,"exited":148,
     "dropped":{"no_setup_detected":364}},
    {"stage":5,"name":"scoring","entered":148,"exited":148},
    {"stage":6,"name":"risk_and_catalyst_veto","entered":148,"exited":19,
     "dropped":{"rr_below_floor":54,"earnings_in_window":31,"rank_cutoff":44}}
  ],
  "candidates_found":19
}
```

### `GET /api/scanner/candidates?date=2026-09-10&limit=20&include_vetoed=false`
Ranked candidates, each embedding its `analyze`-shaped technicals, setup, score breakdown, trade
plan, and catalyst summary. This single call is what the pre-market report is built from.

```json
{
  "trade_date":"2026-09-10","market_regime":"RISK_ON","count":19,
  "candidates":[{
    "rank":1,"symbol":"NVDA","score":"87.4",
    "score_breakdown":{
      "technical":{"raw":0.82,"weight":0.25,"contribution":20.5},
      "momentum":{"raw":0.79,"weight":0.15,"contribution":11.9},
      "relative_strength":{"raw":0.88,"weight":0.15,"contribution":13.2},
      "volume":{"raw":0.71,"weight":0.10,"contribution":7.1},
      "regime_fit":{"raw":0.90,"weight":0.10,"contribution":9.0},
      "catalyst":{"raw":0.75,"weight":0.10,"contribution":7.5},
      "reward_risk":{"raw":0.82,"weight":0.15,"contribution":12.3}
    },
    "setup":{"type":"PULLBACK","quality":0.71},
    "trade_plan":{ },
    "catalyst":{"has_catalyst":true,"summary":"...","items":[ ]},
    "technicals":{ }
  }]
}
```

---

## News & research

### `POST /api/news/research`
Request: `{"symbol":"NVDA","days":7,"include_analysis":true}`

```json
{
  "symbol":"NVDA",
  "items":[{
    "headline":"NVIDIA raises Q4 guidance on datacenter demand",
    "source":"Reuters","url":"https://...","published_at":"2026-09-09T21:05:00Z",
    "category":"GUIDANCE","direction":"BULLISH",
    "materiality":0.88,"durability":0.75,
    "summary":"Company raised revenue guidance ~8% above consensus, citing datacenter orders."
  }],
  "catalyst_summary":"Guidance raise on 2026-09-09 is the proximate driver of the 6% two-day advance. Durable — it re-rates forward estimates rather than producing a one-day pop.",
  "earnings":{"next_date":"2026-11-18","time_of_day":"AMC","is_confirmed":false,
              "days_until":69,"in_hold_window":false},
  "risks":["Guidance already reflected in price after a 6% move","China export policy remains unresolved"],
  "sources_count":14,"deduplicated_count":6,"noise_filtered":5,
  "meta": { }
}
```

> `include_analysis: true` is the only flag in the API that triggers an LLM call. Keeping it opt-in
> and explicit is what keeps cost controllable — the scanner sets it for ~20 symbols, never 3,000.

### `GET /api/news/earnings-calendar?days=14&symbols=NVDA,AMD`
### `GET /api/news/market?hours=24` — macro/market-wide items only.

---

## Portfolio

### `GET /api/portfolio`
```json
{
  "account_equity":"100000.00","cash":"42100.00",
  "positions":[{
    "id":12,"symbol":"NVDA","direction":"LONG","shares":"136",
    "entry_price":"183.10","entry_date":"2026-09-03","days_held":5,
    "current_price":"189.40","unrealized_pnl":"856.80","unrealized_pnl_pct":"3.44",
    "stop_price":"179.50","initial_stop_price":"175.80",
    "target_price":"199.00",
    "pct_to_stop":"-5.23","pct_to_target":"5.07",
    "current_r_multiple":"0.86","open_risk_usd":"1346.40",
    "health":{"status":"HEALTHY","flags":[],
              "notes":"Trend intact; stop raised to breakeven+."}
  }],
  "summary":{
    "open_positions":3,"total_exposure":"57900.00","exposure_pct":"57.90",
    "portfolio_heat_pct":"3.1","total_unrealized_pnl":"1420.30",
    "sector_concentration":{"Technology":"41.2","Healthcare":"16.7"},
    "can_add_position":true,"remaining_risk_budget_usd":"2900.00"
  },
  "meta": { }
}
```

`health.flags` ∈ `STOP_BREACHED`, `TARGET_REACHED`, `THESIS_INVALIDATED`, `EARNINGS_APPROACHING`,
`TIME_STOP_EXCEEDED`, `VOLATILITY_SPIKE`, `BELOW_ENTRY_AFTER_N_DAYS`.

### `POST /api/portfolio/positions` — record an entry
### `PATCH /api/portfolio/positions/{id}` — move stop/target, partial exit, update thesis
### `POST /api/portfolio/positions/{id}/close`
### `GET /api/portfolio/performance?period=90d` — win rate, avg R, expectancy, by setup and regime

---

## Watchlist & alerts

### `GET|POST|DELETE /api/watchlist`
### `GET|POST|DELETE /api/alerts`

Alert creation accepts a structured condition *and* preserves the operator's original phrasing:

```json
{
  "symbol":"NVDA","alert_type":"PRICE_BELOW",
  "condition":{"price":"175.00"},
  "natural_language":"tell me if NVDA loses 175",
  "cooldown_minutes":60,"expires_at":"2026-10-10T00:00:00Z"
}
```

### `GET /api/alerts/firings?days=7`

---

## Reports

### `GET /api/reports/latest?type=PREMARKET`
### `GET /api/reports?type=PREMARKET&date=2026-09-10`
### `POST /api/reports/generate` — `{"type":"PREMARKET","trade_date":"...","deliver":true}`

Reports return both `content_markdown` (for Telegram) and `payload` (the structured data the model
was given — so a report can be re-rendered or re-synthesised without re-running the pipeline).

---

## Outcomes & analytics

### `GET /api/outcomes/analytics?group_by=setup_type&period=180d`
```json
{
  "period":"180d","total_recommendations":214,"evaluated":198,
  "groups":[{
    "key":"PULLBACK","count":71,"entry_trigger_rate":"0.72",
    "win_rate":"0.54","avg_r_multiple":"0.68","expectancy_r":"0.68",
    "avg_mfe_pct":"6.2","avg_mae_pct":"-3.1",
    "avg_days_to_resolution":6.4,"vs_benchmark_alpha_pct":"3.9"
  }],
  "observations":[
    "PULLBACK setups in RISK_ON produced +0.81R over 44 samples; the same setup in RISK_OFF produced -0.12R over 17. Sample size in RISK_OFF is too small to be conclusive.",
    "Average MAE on winning trades is -2.4% versus a mean stop distance of -4.1%, suggesting stops could be tightened without materially increasing stop-outs."
  ]
}
```

`group_by` ∈ `setup_type`, `market_regime`, `score_bucket`, `sector`, `has_catalyst`,
`model_name`, `strategy_version`.

> **Every analytics response must report sample size alongside every statistic, and must refuse to
> draw a conclusion below a configured minimum (default n=30).** Tuning a strategy on 11 trades is
> how you convert noise into confident, expensive error.

---

## Admin

### `POST /api/admin/jobs/{job_name}/run` — manual pipeline trigger
### `GET /api/admin/costs?period=mtd` — AI spend by purpose and model
### `POST /api/admin/universe/refresh`
### `GET /api/admin/strategy-versions` · `POST /api/admin/strategy-versions`
