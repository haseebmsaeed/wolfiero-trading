# Wolfiero — Technical Architecture & Implementation Specification

**Status:** Draft v1.0 · **Last revised:** 2026-09-10
**Companion to:** [01-product-requirements.md](01-product-requirements.md)

---

## 1. Architectural thesis

> **Python computes. Firestore remembers. The AI interprets. Telegram delivers.**

Four responsibilities, four layers, no overlap. The most common way a project like this fails is
letting the LLM creep into the compute layer — asking it to "scan the market," "rank these," or
"work out the RSI." That path is slow, expensive, non-reproducible, and quietly wrong. The
architecture below makes it structurally hard to do.

| Layer | Owns | Must never |
|---|---|---|
| **Agent runtime** (OpenClaw) | Conversation, intent → tool selection, natural-language synthesis, scheduling triggers | Compute an indicator, hold business state, query the DB directly |
| **Backend API** (FastAPI) | All calculation, all business rules, all persistence, all provider access | Call an LLM for anything deterministic |
| **Firestore** | Durable state, history, outcomes, audit (append-only) | Hold derived values that are cheap to recompute *and* likely to change definition |
| **Telegram** | Input and output for one human | Contain logic |

**The load-bearing rule:** if a question can be answered by a formula, a formula answers it. The LLM
is only ever handed *already-computed structured data* and asked to explain, prioritise within a
pre-ranked set, or read unstructured text (news). That is genuine language work. Arithmetic is not.

---

## 2. System context

```
                          ┌─────────────────────┐
                          │      OPERATOR       │
                          │   (Telegram app)    │
                          └──────────┬──────────┘
                                     │ messages / reports
                                     ▼
┌───────────────────────────────────────────────────────────────────┐
│                        AZURE UBUNTU VM                            │
│                                                                   │
│  ┌─────────────────────────┐        ┌──────────────────────────┐  │
│  │      OpenClaw           │        │      Scheduler           │  │
│  │  agent runtime          │        │   (APScheduler, in-API)  │  │
│  │  • Telegram adapter     │        │  • premarket pipeline    │  │
│  │  • tool registry        │        │  • intraday monitor      │  │
│  │  • LLM provider router  │        │  • EOD / weekly          │  │
│  └───────────┬─────────────┘        └────────────┬─────────────┘  │
│              │ HTTP tool calls                   │ in-process     │
│              │ (internal Docker network)         │                │
│              ▼                                   ▼                │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                   WOLFIERO BACKEND API (FastAPI)            │  │
│  │                                                             │  │
│  │  api/     thin HTTP handlers — validation & serialisation   │  │
│  │  services/ ALL business logic                               │  │
│  │  providers/ vendor adapters behind stable interfaces        │  │
│  │  models/   SQLAlchemy ORM entities                          │  │
│  │  jobs/     scheduled pipeline orchestration                 │  │
│  └──────────┬────────────────────────────┬─────────────────────┘  │
│             │                            │                        │
│             ▼                            │                        │
│  ┌─────────────────────┐                 │                        │
│  │    PostgreSQL 16    │                 │                        │
│  │   (named volume)    │                 │                        │
│  └─────────────────────┘                 │                        │
└──────────────────────────────────────────┼────────────────────────┘
                                           │ HTTPS (egress only)
                    ┌──────────────────────┼──────────────────────┐
                    ▼                      ▼                      ▼
            Market data vendor      News vendor           LLM provider(s)
```

**Why the agent goes through HTTP rather than importing Python directly:** it forces a stable,
inspectable contract. Every capability the AI has is an endpoint you can curl, test, and log. If the
agent runtime is ever replaced, the backend is untouched. It also makes it impossible for the agent
to reach into the database and produce an answer no other caller could reproduce.

---

## 3. Technology decisions

| Concern | Choice | Why this and not the alternative |
|---|---|---|
| Host | Google Cloud Run (serverless containers) | This is a solo trader's scanner: 1 user, 1-2 scans/day. No need for VM management, patches, or fixed capacity. Cloud Run scales to zero between scans, billing aligns with actual usage (~$0 for this workload). |
| Local dev | Docker Compose + Firestore emulator | One file, one `make up`, reproducible. Firestore emulator spins up locally for development and testing. |
| API | Python 3.12 + FastAPI | Async I/O for provider fan-out, Pydantic validation, free OpenAPI schema — which doubles as the agent's tool documentation. |
| Data | pandas + numpy | The analysis is tabular time-series. This is what the ecosystem is for. |
| Indicators | `pandas-ta` (fallback: hand-rolled) | **Important:** wrap it. Do not let `pandas-ta` calls litter the services layer — these libraries change APIs and occasionally disagree on formulas. One `indicators.py` module, fully unit-tested. TA-Lib is faster but a C-build headache; not worth it at this volume. |
| DB | Google Firestore | Document store with real-time capabilities, excellent for semi-structured data (price history, technical snapshots, score breakdowns). Free tier covers this workload (50K reads/day, 20K writes/day). Trade-off: no server-side aggregation (sector grouping now in Python), no atomic transactions across thousands of docs (chunked WriteBatch + audit doc instead). |
| Data access | Repository pattern with Protocol interfaces | All database access goes through typed repositories. Services never touch the database layer directly. Unit tests inject FakeRepositories (zero Docker dependency); integration tests use Firestore emulator via testcontainers. |
| Money handling | Scaled-integer Decimals (not strings, never float) | Prices stored as int (price × 10_000), Decimal arithmetic on retrieval. Preserves exactness and remains range-queryable. Single module `app/db/money.py` enforces "Money is Decimal, never float" rule. |
| Scheduling | Future: Cloud Scheduler + Cloud Run Jobs | Currently no scheduled jobs. When jobs are needed, use Cloud Scheduler (triggers) + Cloud Run Jobs (execution) instead of in-process APScheduler (Cloud Run's scale-to-zero is incompatible with persistent processes). |
| HTTP client | `httpx` (async) | Async, connection pooling, timeouts, retries. |
| Agent runtime | OpenClaw | Conversation, tool orchestration, LLM routing, Telegram. |
| LLM | Provider-abstracted, configurable | Model quality and pricing move monthly. Never hardcode a vendor; log which model produced each output so you can compare them later. |
| Secrets | `.env` → Google Secret Manager | `.env` is acceptable for local dev. Production: Google Secret Manager for Telegram tokens, API keys, etc. |
| Observability | structlog JSON → Cloud Logging | Container logs ship to Google Cloud Logging. `/health` endpoint for Cloud Run health checks. |

### Deliberately not in v1

Redis, Celery, Kafka, Kubernetes, microservices, a message bus, a vector database, a web frontend.
Every one of them is a real cost with no v1 payoff. Add one only when a *measured* limit forces it,
and write down the measurement.

---

## 4. Repository layout

```
wolfiero-trading/
│
├── docker-compose.yml
├── docker-compose.override.yml.example    # local dev overrides
├── .env.example
├── Makefile                               # up / down / test / migrate / seed / logs
├── README.md
│
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic.ini
│   │
│   ├── app/
│   │   ├── main.py                  # FastAPI app factory, router mount, lifespan
│   │   ├── config.py                # Pydantic Settings — the ONLY place env vars are read
│   │   ├── logging.py               # structlog config, correlation-ID middleware
│   │   ├── deps.py                  # FastAPI dependency providers (db session, auth)
│   │   │
│   │   ├── api/                     # THIN. validate → call service → serialise. No logic.
│   │   │   ├── health.py
│   │   │   ├── stocks.py
│   │   │   ├── scanner.py
│   │   │   ├── regime.py
│   │   │   ├── news.py
│   │   │   ├── portfolio.py
│   │   │   ├── watchlist.py
│   │   │   ├── alerts.py
│   │   │   ├── reports.py
│   │   │   └── admin.py             # trigger jobs, provider health, cost report
│   │   │
│   │   ├── services/                # ALL business logic lives here
│   │   │   ├── market_data.py       # fetch + cache + validate OHLCV
│   │   │   ├── indicators.py        # pure functions: series in, series out
│   │   │   ├── technical_analysis.py# indicators → trend/levels/TechnicalSnapshot
│   │   │   ├── setups.py            # graded setup detectors
│   │   │   ├── market_regime.py
│   │   │   ├── universe.py
│   │   │   ├── scanner.py           # the staged funnel
│   │   │   ├── scoring.py           # weighted composite + explainability
│   │   │   ├── trade_plan.py        # entry/stop/target/size
│   │   │   ├── risk.py              # heat, concentration, portfolio guardrails
│   │   │   ├── news.py              # fetch, dedupe, classify, score materiality
│   │   │   ├── earnings.py          # calendar + hold-window veto
│   │   │   ├── research.py          # LLM-assisted per-symbol synthesis
│   │   │   ├── portfolio.py
│   │   │   ├── watchlist.py
│   │   │   ├── alerts.py            # rule evaluation (deterministic)
│   │   │   ├── reporting.py         # report assembly
│   │   │   └── outcomes.py          # forward tracking + analytics
│   │   │
│   │   ├── providers/
│   │   │   ├── market_data/
│   │   │   │   ├── base.py          # ABC — the contract
│   │   │   │   ├── yahoo.py
│   │   │   │   ├── alpaca.py
│   │   │   │   └── factory.py       # env-driven selection + failover chain
│   │   │   ├── news/
│   │   │   │   ├── base.py
│   │   │   │   └── <vendor>.py
│   │   │   └── ai/
│   │   │       ├── base.py
│   │   │       ├── router.py        # model selection by task tier + cost logging
│   │   │       └── prompts/         # VERSIONED prompt templates
│   │   │
│   │   ├── models/                  # SQLAlchemy ORM
│   │   ├── schemas/                 # Pydantic request/response DTOs
│   │   │
│   │   ├── jobs/
│   │   │   ├── scheduler.py         # APScheduler wiring
│   │   │   ├── premarket.py
│   │   │   ├── intraday_monitor.py
│   │   │   ├── end_of_day.py
│   │   │   ├── weekly_review.py
│   │   │   └── universe_refresh.py
│   │   │
│   │   └── db/
│   │       ├── session.py
│   │       └── migrations/          # alembic versions
│   │
│   └── tests/
│       ├── unit/                    # indicators, scoring, sizing — fixture-based
│       ├── integration/             # API + DB, providers mocked
│       └── fixtures/                # golden OHLCV CSVs with hand-verified values
│
├── openclaw/
│   ├── config/
│   ├── tools/                       # tool defs mapping 1:1 to API endpoints
│   ├── prompts/                     # system prompts, versioned
│   └── skills/
│
└── docs/                            # you are here
```

### The layering rule, enforced

`api → services → (providers | models)`. Services may call other services. **Providers never import
services. Models never import services.** A service must be callable from a job, an endpoint, and a
test with no HTTP involved — that is what makes the scheduled pipeline and the conversational
interface share one code path instead of quietly diverging.

---

## 5. Provider abstraction

The vendor landscape for market data is unstable: pricing changes, rate limits change, vendors die.
Analysis code must never know which vendor it is talking to.

```python
# providers/market_data/base.py
class MarketDataProvider(ABC):
    name: str

    @abstractmethod
    async def get_quote(self, symbol: str) -> Quote: ...

    @abstractmethod
    async def get_history(
        self, symbol: str, *, start: date, end: date, interval: Interval = Interval.DAY
    ) -> OHLCVFrame:
        """MUST return split- and dividend-adjusted bars, ascending by date,
        with no duplicate dates and no gaps other than market holidays."""

    @abstractmethod
    async def get_history_batch(
        self, symbols: Sequence[str], *, start: date, end: date
    ) -> dict[str, OHLCVFrame]: ...

    @abstractmethod
    async def get_fundamentals(self, symbol: str) -> Fundamentals: ...

    @abstractmethod
    async def get_earnings_calendar(
        self, symbols: Sequence[str], *, through: date
    ) -> list[EarningsEvent]: ...

    @abstractmethod
    async def health(self) -> ProviderHealth: ...
```

Rules every implementation obeys:

1. **Normalise at the boundary.** Vendor quirks — column names, timezone, adjustment convention,
   symbol format (`BRK.B` vs `BRK-B`) — die inside the adapter. Everything above sees one shape.
2. **The returned frame is validated, not trusted.** Shared validator checks: monotonic dates, no
   NaN in OHLC, `high >= max(open, close)`, `low <= min(open, close)`, non-negative volume, no
   single-day move beyond a configured sanity bound. Failures raise `DataQualityError` with the
   symbol and the offending bar.
3. **Rate limits and retries belong to the adapter.** Token-bucket limiter, exponential backoff with
   jitter, and a circuit breaker that trips after N consecutive failures.
4. **The factory owns failover.** `MARKET_DATA_PROVIDER=alpaca,yahoo` means: try Alpaca; on circuit
   open, fall back to Yahoo and log a degradation event that surfaces in the report.
5. **`get_history_batch` is the hot path.** The scanner needs 3,000 symbols; per-symbol serial
   fetching will not hit the 10-minute budget. Implement it with bounded concurrency
   (`asyncio.Semaphore`, default 10) — never unbounded `gather` over 3,000 coroutines.

The identical pattern applies to news and AI providers. The AI router additionally selects a model
**tier by task** — cheap/fast for classification and summarisation, strong for the daily thesis
synthesis — and logs tokens and cost per call against the run.

---

## 6. Caching strategy

Daily bars for a closed session are immutable. Re-fetching them is wasted money and wasted minutes.

| Data | Where cached | TTL / invalidation |
|---|---|---|
| Daily OHLCV, completed sessions | `price_history` table | Permanent. Only refetched on an explicit corporate-action backfill. |
| Today's forming bar | In-memory | 5 minutes |
| Intraday quote | In-memory | 60 seconds |
| Fundamentals | `stocks` table | 7 days |
| Earnings calendar | `earnings_events` table | Daily refresh; confirmed dates stop refreshing |
| News items | `news_items` table | Permanent (they are historical facts) |
| LLM classification of a news item | `news_items.classification` JSONB | Permanent, keyed by prompt version |
| Computed indicators | **Not cached** | Recomputed from cached bars — cheap, and avoids stale-derived-value bugs when a formula changes |

**The rule:** cache *inputs*, recompute *outputs*. A stale price is detectable. A stale indicator
computed under an old formula is invisible and will silently corrupt months of analysis.

---

## 7. The daily pipeline

`jobs/premarket.py` orchestrates; every step is a service call that is independently testable and
independently re-runnable. Times are `America/New_York`.

```
05:30  REFRESH DATA
       └─ Batch-fetch yesterday's bars for the full universe → price_history
       └─ Validate; quarantine bad symbols; log coverage %
       └─ ABORT the whole run if coverage < 90% — a partial scan is a misleading scan

05:45  MARKET REGIME
       └─ Analyse SPY / QQQ / IWM / VIX + sector ETFs + breadth
       └─ Persist market_regimes row; emit an alert if the label changed

05:50  SCAN  (see 05-scanner-and-scoring-spec.md)
       Stage 1  Universe              ~3,000
       Stage 2  Liquidity + data      ~1,500
       Stage 3  Trend/technical       ~500
       Stage 4  Setup detection       ~150
       Stage 5  Composite score       → ranked
       Stage 6  Risk & catalyst veto  → top ~20
       └─ Persist scan_run + candidates with full stage funnel counts

06:15  CATALYST ENRICHMENT
       └─ For top 20 + watchlist + open positions: fetch news, dedupe, classify
       └─ Apply earnings hold-window veto; re-rank survivors
       └─ THIS is the first point an LLM is involved, and only on ~40 symbols

06:35  TRADE PLANS
       └─ entry / stop / target / R / size for each survivor
       └─ Drop anything below the R:R floor; enforce portfolio heat

06:45  POSITION HEALTH
       └─ Check every open position against stop, target, thesis, earnings, time stop

06:55  REPORT SYNTHESIS
       └─ ONE strong-model call over the assembled structured payload
       └─ Persist report; render Markdown

07:00  DELIVER  → Telegram
```

Design notes an implementer must respect:

- **Every step writes its result before the next begins.** If synthesis fails at 06:55, the scan is
  not lost — you re-run one step, not the pipeline.
- **Every step is idempotent for a given `(date, strategy_version)`.** Re-running replaces.
- **A step failure degrades, it does not abort** (except the 05:30 coverage gate). No news? Report
  ships with "catalyst data unavailable." Silence is the worst outcome.
- **The whole run carries one `run_id`**, on every log line and every persisted row.

### Intraday

Every 5 minutes between 09:30 and 16:00, `intraday_monitor.py` pulls quotes for open positions +
watchlist + today's top candidates, evaluates alert rules **in plain Python**, and pushes any firing
alert to Telegram. An LLM is involved only if the operator asks a follow-up question. Baseline
intraday AI cost is therefore **zero**.

---

## 8. Agent layer design

### Tools

Each tool is a thin wrapper over one endpoint. Tool descriptions matter as much as the code — they
are the only thing the model uses to choose correctly.

| Tool | Endpoint | Used for |
|---|---|---|
| `get_market_regime` | `GET /api/regime/current` | "How's the market?" |
| `analyze_stock` | `POST /api/stocks/analyze` | "Analyze NVDA" |
| `scan_market` | `POST /api/scanner/run` / `GET /api/scanner/candidates` | "Find candidates" |
| `research_stock` | `POST /api/news/research` | "Why is NVDA up?" |
| `get_trade_plan` | `POST /api/stocks/trade-plan` | "Where's my stop?" |
| `get_portfolio` | `GET /api/portfolio` | "How am I doing?" |
| `record_position` | `POST /api/portfolio/positions` | "I bought 100 NVDA at 182" |
| `manage_watchlist` | `GET/POST/DELETE /api/watchlist` | "Watch AMD" |
| `create_alert` | `POST /api/alerts` | "Tell me if NVDA loses 175" |
| `get_report` | `GET /api/reports/{date}` | "Show Tuesday's report" |
| `get_performance` | `GET /api/outcomes/analytics` | "Which setups work?" |

### The grounding contract

Non-negotiable, in the system prompt and enforced by a response guard:

1. Every number in a reply comes from a tool result **in the current turn**. No model memory, ever —
   the model's training data contains prices that are months or years stale and it will state them
   confidently.
2. If a tool errors or returns empty, say so plainly. Do not substitute general knowledge.
3. News claims carry source and timestamp.
4. Distinguish computed fact ("RSI is 62.3") from interpretation ("that's elevated but not extreme")
   from speculation ("if it holds the 50-day, ...").
5. Never state or imply certainty about future prices.

A lightweight post-response check scans for numeric tokens absent from that turn's tool payloads and
flags the response for logging. It is a smoke detector, not a firewall — but a hallucinated price is
the single failure mode that destroys trust in the product, so it earns its keep.

### Model tiering

| Task | Tier | Why |
|---|---|---|
| News classification (high volume) | Cheap/fast | Structured extraction; a small model does it well |
| Per-symbol research synthesis | Mid | Needs real reading comprehension |
| Daily report thesis | Strong | The one output you read every day |
| Conversational Q&A | Mid, escalating on complexity | Latency matters here |

Every call logs model, tokens, latency, and cost to `model_runs`, keyed by `run_id`. That table is
how you answer "is the expensive model actually better?" — which is a question you *will* ask.

---

## 9. Configuration

`config.py` is the only module that reads `os.environ`. Everything else takes typed settings.

```
# Core
DATABASE_URL, LOG_LEVEL, TZ=America/New_York, ENVIRONMENT

# Providers
MARKET_DATA_PROVIDER=alpaca,yahoo        # ordered failover chain
MARKET_DATA_API_KEY / _SECRET
NEWS_PROVIDER, NEWS_API_KEY
AI_PROVIDER, AI_API_KEY
AI_MODEL_CHEAP / _MID / _STRONG
AI_MONTHLY_BUDGET_USD

# Telegram
TELEGRAM_BOT_TOKEN, TELEGRAM_ALLOWED_CHAT_IDS

# Strategy (versioned; changes bump STRATEGY_VERSION)
STRATEGY_VERSION=v1.0.0
UNIVERSE_MIN_DOLLAR_VOLUME=20000000
UNIVERSE_MIN_PRICE=5.00
SCAN_MAX_CANDIDATES=20
MIN_REWARD_RISK=2.0
ACCOUNT_EQUITY_USD, RISK_PER_TRADE_PCT=1.0
MAX_PORTFOLIO_HEAT_PCT=6.0, MAX_POSITIONS=8, MAX_SECTOR_EXPOSURE_PCT=30
HOLD_WINDOW_DAYS=15
EARNINGS_POLICY=veto                     # veto | flag

# Schedule
PREMARKET_RUN_TIME=05:30, REPORT_SEND_TIME=07:00
INTRADAY_INTERVAL_MINUTES=5
EOD_REPORT_TIME=16:30
```

**Scoring weights live in a versioned YAML file, not in env**, because they are a coherent set that
must move together. `strategy_versions` records every published set so historical results stay
interpretable.

---

## 10. Security

- Backend binds to the internal Docker network only. No published port unless a dashboard exists.
- If exposed: Caddy + TLS + a static API token. Never open Postgres to the internet.
- Telegram: hard allowlist on chat ID. Reject and log everything else — bot tokens leak and bots get
  probed within hours of first use.
- No broker credentials with trade scope exist anywhere in the system. This is an architectural
  guarantee, not a policy.
- `.env` is gitignored; `.env.example` holds names only; a pre-commit secret scanner runs in CI.
- VM: SSH keys only, password auth disabled, UFW allowing 22 (source-restricted) and 443 only,
  unattended-upgrades enabled.
- DB user for the app has no `SUPERUSER`; migrations run as a separate role.

---

## 11. Observability

- **Structured JSON logging** with a `run_id` / `request_id` propagated Telegram → agent → API →
  provider. One trade recommendation must be reconstructable from logs end to end.
- **`/health`** — liveness. **`/health/deep`** — DB connectivity, provider circuit states, last
  successful pipeline run, data freshness.
- **Key metrics:** scan duration, per-stage funnel counts, provider error rate and latency, AI cost
  per run and month-to-date, alert fire counts, report delivery success.
- **A pipeline that does not run is the top-priority failure.** A watchdog checks by 07:15 that
  today's report exists and pages via Telegram if not. Missing data must never look like a quiet day.

---

## 12. Testing strategy

| Layer | Approach |
|---|---|
| Indicators | **Golden fixtures.** Small hand-verified OHLCV CSVs with expected RSI/MACD/ATR to 4dp. Non-negotiable — everything downstream inherits these values. |
| Setup detectors | Curated real historical windows: known-good breakouts, known-bad fakeouts. Assert the grade band, not an exact float. |
| Scoring | Property tests — monotonicity (better inputs never score lower), bounds (always 0–100), weight sum invariance. |
| Sizing & risk | Table-driven: equity × risk% × stop distance → expected shares, including edge cases (stop at entry, fractional shares, heat cap breach). |
| Providers | Recorded fixtures (VCR-style). **Never** hit a live vendor in CI. Include malformed-response cases. |
| Services | Integration tests against a real ephemeral Postgres; providers mocked. |
| Pipeline | One end-to-end test on a frozen seeded dataset, asserting a deterministic candidate list. This is the regression net for the whole system. |
| Agent | Scripted conversation fixtures asserting the *right tool* is called with the *right arguments* — not asserting exact prose. |

**A time-freezing utility is mandatory.** Half the logic is date-dependent (hold windows, earnings
proximity, trading-day math). Tests that use `date.today()` rot within a week.

---

## 13. Deployment

```bash
# One-time
az vm create ... --image Ubuntu2404 --size Standard_B2ms
ssh wolfiero@<ip>
curl -fsSL https://get.docker.com | sh && sudo usermod -aG docker $USER
sudo ufw allow 22/tcp && sudo ufw enable

git clone <repo> && cd wolfiero-trading
cp .env.example .env && $EDITOR .env

make up          # build + start
make migrate     # alembic upgrade head
make seed        # load universe
make smoke       # health + one analyze call
```

Deploys are `git pull && make up && make migrate`. Migrations are forward-only and additive;
destructive changes ship as a two-step expand/contract so a rollback never loses data.

Backups: nightly `pg_dump` to Azure Blob, 30-day retention, **and a monthly restore drill**. An
untested backup is not a backup, and `recommendations` + `outcomes` cannot be recomputed.

---

## 14. Build order

Build strictly bottom-up. Each step is verifiable before the next depends on it.

```
1  Compose + Postgres + FastAPI /health            → infrastructure works
2  Alembic + core schema                           → persistence works
3  MarketDataProvider + one adapter + validation   → real data arrives, validated
4  indicators.py + golden tests                    → the math is trustworthy
5  technical_analysis + POST /stocks/analyze       → one symbol, end to end
6  OpenClaw + Telegram + analyze_stock tool        → "Analyze NVDA" works in your pocket
────────────────────────────────────────────────── first genuinely useful milestone
7  Universe + liquidity filters
8  Scanner funnel + stage instrumentation
9  Scoring + strategy versioning
10 Market regime engine
11 Trade plans + sizing + risk guardrails
12 News provider + dedupe + classification
13 Earnings calendar + veto
14 Scheduler + pre-market pipeline + report
15 Alert engine + intraday monitor
16 Portfolio + health checks
17 Outcome tracking + analytics + weekly review
```

Step 6 is the milestone that matters psychologically: the day the loop closes and you can talk to
your own market analyst from your phone. Everything after it is incremental and independently
shippable.
