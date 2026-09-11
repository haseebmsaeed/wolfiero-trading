# Epic 1 — Market Data & Technical Analysis

**Goal:** `POST /api/stocks/analyze` returns a complete, correct, verifiable technical read on any
symbol.
**Done when:** `curl` on NVDA returns the full payload from [04-api-contract.md](../04-api-contract.md)
and every number is reproducible by hand from the underlying bars.

> **This epic is the foundation of correctness for the entire product.** Scores, rankings, stops,
> position sizes, and outcome analytics are all functions of these numbers. An off-by-one in an RSI
> window does not throw an error — it produces a plausible-looking wrong answer that silently
> corrupts every recommendation for months. Test accordingly.

---

### W-07  Market data provider interface & first adapter                  [L] [depends: W-04]

**Why this exists**
Market data vendors change pricing, rate limits, and endpoints without warning, and some disappear.
If `yfinance` calls are scattered through the analysis code, a vendor change is a rewrite. Behind an
interface, it is a config line.

**Build**
- `providers/market_data/base.py` — the ABC from architecture §5, plus Pydantic models `Quote`,
  `OHLCVFrame`, `Fundamentals`, `EarningsEvent`, `ProviderHealth`.
- `providers/market_data/yahoo.py` — first concrete adapter.
- `providers/market_data/factory.py` — builds the ordered failover chain from
  `MARKET_DATA_PROVIDER`, with a circuit breaker per provider (open after 5 consecutive failures,
  half-open after 60s).
- Token-bucket rate limiter and exponential backoff with jitter, inside the adapter.
- `get_history_batch` with bounded concurrency (`asyncio.Semaphore`, default 10).

**Acceptance**
- `get_history("NVDA", start, end)` returns bars ascending by date with no duplicates.
- Symbol normalisation is bidirectional: internal `BRK.B` ↔ vendor `BRK-B`.
- Killing the primary provider transparently fails over to the secondary and logs a degradation event.
- `get_history_batch` on 100 symbols completes in under 30s and never issues more than 10 concurrent
  requests (assert via `respx`).
- All provider tests use recorded fixtures. **No network access in CI.**

**Notes**
Returned bars must be **split- and dividend-adjusted**. Yahoo's `auto_adjust` flag defaults differ
between versions — set it explicitly and assert the adjustment in a test, because mixing adjusted
and raw series produces indicator values that are wrong in a way no eyeball will catch.

**Out of scope** Intraday intervals below 1 day, options chains, level-2 data.

---

### W-08  OHLCV validation & the data-quality gate                        [M] [depends: W-07]

**Why this exists**
Vendors ship bad data regularly: zero-volume holiday rows, unadjusted split days showing a −50%
move, duplicated dates, NaNs. Each one produces indicators that are wrong but plausible. Bad data
must raise, never propagate.

**Build**
- `services/market_data.py::validate_ohlcv(frame) -> ValidationResult` checking: monotonic unique
  dates; no NaN in OHLC; `high >= max(open, close)`; `low <= min(open, close)`; `high >= low`;
  volume ≥ 0; no single-day move beyond `MAX_DAILY_MOVE_PCT` (default 50) without a known corporate
  action; no gap longer than 5 trading days per the market calendar.
- `DataQualityError` carrying symbol, offending dates, and the specific rule violated.
- Quarantine flow: a symbol failing validation is marked `is_active=false` with a reason and
  excluded from scans until re-validated.
- Coverage metric for batch fetches: `valid_symbols / requested_symbols`.

**Acceptance**
- Each malformed-frame fixture (NaN, duplicate date, inverted high/low, 60% jump) triggers the
  correct specific error.
- A batch fetch reports coverage, and coverage below `MIN_DATA_COVERAGE_PCT` (default 90) raises,
  so a partial universe never silently becomes a misleading scan.
- Known real split dates are **not** flagged (the corporate-action allowance works).

---

### W-09  Price history persistence & incremental backfill                [M] [depends: W-08]

**Why this exists**
The scanner touches 3,000 symbols inside a 10-minute budget; live fetching cannot meet it under any
vendor's rate limit. Bars for closed sessions are immutable, so fetching them twice is pure waste,
and a point-in-time record is required to reconstruct why a past recommendation was made.

**Build**
- `services/market_data.py`: `ensure_history(symbols, lookback_days)` — determines each symbol's
  latest stored bar, fetches only the missing tail, upserts on `(stock_id, trade_date)`.
- `backfill_history(symbols, start, end)` for initial population (400 trading days).
- `get_bars(symbol, days) -> pd.DataFrame` returning a clean, indexed, adjusted frame from the DB —
  **this is the single accessor every analysis service uses.** Nothing reads `price_history` directly.
- Corporate-action detection: when a newly fetched bar implies a ratio change versus the stored
  series, trigger a full re-fetch for that symbol and log it.

**Acceptance**
- Running `ensure_history` twice fetches nothing the second time (assert zero provider calls).
- A 400-day backfill of 100 symbols completes in under 3 minutes.
- `get_bars` returns a `DatetimeIndex` in market time, ascending, no duplicates.
- A simulated 2:1 split triggers re-fetch, and the resulting stored series is internally consistent.

---

### W-10  Indicator library with golden tests                            [L] [depends: W-09]

**Why this exists**
This is the most correctness-critical module in the system, and the one where errors are least
visible. Everything downstream — scores, ranks, stops, sizes, performance analytics — is a function
of these values.

**Build**
`services/indicators.py` — **pure functions only**: series in, series out. No DB, no I/O, no config.

- `sma(series, period)`, `ema(series, period)`
- `rsi(series, period=14)` — **Wilder's smoothing**, not a simple moving average of gains/losses
- `macd(series, 12, 26, 9)` → line, signal, histogram
- `atr(high, low, close, period=14)` — Wilder's, with correct true-range handling of gaps
- `bollinger_bands(series, 20, 2)` and `bollinger_width_percentile(series, lookback=100)`
- `realized_volatility(series, period=20)` — annualised, √252
- `rate_of_change(series, period)`
- `volume_ratio(volume, period=20)`
- `relative_strength(symbol_series, benchmark_series, period)` — ratio-based, normalised
- `swing_pivots(high, low, lookback=5)` → pivot highs/lows
- `support_resistance_levels(bars, lookback=60)` → clustered levels with touch count and strength

**Acceptance**
- **Golden fixtures**: hand-verified CSVs in `tests/fixtures/` with expected values to 4 decimal
  places for at least 3 symbols × 3 market conditions (trending, ranging, volatile). These are
  committed and never regenerated from the code under test.
- Insufficient-data cases return `NaN` for the warm-up period, never raise, never silently pad.
- Property tests: `ema` responds faster than `sma` to a step change; `rsi` stays within [0, 100];
  `atr` is non-negative.
- ≥ 95% coverage on this module.

**Notes**
Wilder's RSI/ATR smoothing (`alpha = 1/period`) differs materially from a simple MA and from EMA
(`alpha = 2/(period+1)`). Getting this wrong shifts RSI by several points — enough to move a
candidate across the momentum band boundary. **Verify the fixtures against a second independent
source** (a charting platform), not against another Python library that may share the same bug.

**Out of scope** Ichimoku, Elliott waves, Fibonacci, and every other indicator not listed. Add one
only when a scoring component actually consumes it.

---

### W-11  Technical analysis service                                     [M] [depends: W-10]

**Why this exists**
Raw indicator values are not decisions. This layer turns numbers into the classifications the scanner
and the reports reason about: is this an uptrend, where is support, how extended is it.

**Build**
- `services/technical_analysis.py::analyze(symbol, bars) -> TechnicalSnapshot` producing every
  field in the `analyze` response contract.
- Trend classification: `UPTREND` when close > 50-SMA > 200-SMA **and** the 50-SMA slope over 20
  bars is positive; `DOWNTREND` mirrored; else `RANGE`. `strength` ∈ [0,1] from MA separation and
  slope steepness.
- MACD state: `BULLISH_ABOVE_ZERO`, `BULLISH_BELOW_ZERO`, `BEARISH_ABOVE_ZERO`, `BEARISH_BELOW_ZERO`.
  *(Position relative to zero distinguishes a genuine trend from a bounce inside a downtrend.)*
- Volatility regime: ATR% versus its own 50-day average → `LOW` / `NORMAL` / `HIGH`.
- Support/resistance clustering: group pivots within 1.5% of each other; `strength` from touch
  count, recency, and volume at the touches.
- Relative strength versus SPY at 1/3/6 months, plus a universe percentile rank.

**Acceptance**
- `TechnicalSnapshot` is a frozen Pydantic model — immutable snapshots are a data-model invariant.
- Trend classification matches hand-labelled expectations on curated historical windows.
- Support/resistance never returns a "support" above the current price or a "resistance" below it.
- With fewer than 250 bars, raises `INSUFFICIENT_HISTORY` rather than computing a 200-SMA on padding.

---

### W-12  Setup detectors                                                [L] [depends: W-11]

**Why this exists**
"This chart looks good" is not measurable. Naming the setup is what makes it possible to later ask
"what is my win rate on pullbacks in a risk-on market?" — which is the whole point of Epic 8.

**Build**
`services/setups.py` — one detector per setup, implementing
[05-scanner-and-scoring-spec.md](../05-scanner-and-scoring-spec.md) §Stage 4 exactly, each returning
`SetupResult(type, quality: float, direction, components: dict, description: str, triggered: bool,
trigger_condition: str)`.

- `detect_breakout`, `detect_pullback`, `detect_consolidation`, `detect_momentum`
- `detect_best_setup(snapshot, bars)` → highest quality above `min_setup_quality` (0.45)
- `description` is **template-generated from the component values**, never LLM-written, so it is
  reproducible and free.

**Acceptance**
- Quality is graded in [0,1], never boolean, and `components` shows each sub-score's contribution.
- Curated historical fixtures: ≥ 5 known-good and ≥ 5 known-bad examples per setup, asserting the
  quality band (e.g. textbook breakout > 0.7, fakeout < 0.45).
- Pullback correctly **rejects** a decline on rising volume — the most common misclassification, and
  the one that costs real money because distribution looks like a pullback on a price chart alone.
- Consolidation requires a *preceding advance*; a coil after a decline is not surfaced as a long setup.

**Notes**
Weight each detector's sub-scores exactly as specified. These weights are part of
`strategy_version` and must be loaded from config, not hardcoded, so that tuning them remains
traceable.

---

### W-13  `POST /api/stocks/analyze` endpoint                            [M] [depends: W-12]

**Why this exists**
The first end-to-end vertical slice, and the endpoint the agent calls most. It is also the
integration test for everything in this epic.

**Build**
- `api/stocks.py`: `POST /analyze`, `POST /trade-plan` (stub returning 501 until W-25),
  `GET /{symbol}/history`.
- Pydantic request/response schemas exactly matching the API contract.
- Wire the flow: validate symbol → `ensure_history` → `get_bars` → `analyze` → `detect_best_setup`
  → assemble → attach `meta`.
- `meta.is_stale = true` when the latest bar is older than 1 trading day, with an entry in
  `warnings[]`. **Serve the data anyway** — the agent needs to be able to say "this is yesterday's
  close", which is far more useful than an error.
- Error mapping: unknown symbol → 404, short history → 422, all providers down → 503.

**Acceptance**
- Full round trip on a live-ish fixture returns every contracted field with correct types.
- All money fields serialise as strings, not floats.
- p95 latency under 3s for a cached symbol.
- Integration test asserts the complete response shape against the contract.
