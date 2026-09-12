# Wolfiero — Market Intelligence Agent for Swing Trading

A decision-support system for discretionary swing traders. Scans 3,000 liquid US equities daily,
ranks candidates using deterministic quantitative logic, enriches with news and catalysts, and
delivers a trade plan to your phone every morning.

**Status:** Production system (Firestore + Cloud Run)  
**Deployment:** Google Cloud Run (serverless)  
**Database:** Google Firestore (zero monthly cost for this workload)

## What it does

- **Market scanning:** 3,000 → ~150 → ~20 tradeable candidates daily under 10 minutes
- **Technical analysis:** Trend, momentum, volatility, support/resistance, setup classification
- **Risk framework:** Structural ATR-based stops, R-multiple validation, portfolio guardrails
- **Catalyst awareness:** News explains moves, gates risk, breaks ties — never predicts
- **Earnings protection:** Hard veto on dates inside your intended hold window
- **Live tracking:** Portfolio P&L, watchlist alerts, position health checks during the session
- **Decision support:** Telegram interface for conversational Q&A

**It does NOT:** place trades, manage money, predict prices, or require a broker API key.

## Quick start (local dev)

```bash
# Clone and navigate
git clone https://github.com/haseebmsaeed/wolfiero-trading.git
cd wolfiero-trading

# Copy environment template
cp .env.example .env

# Build and start (Firestore emulator + API)
make build
make up

# Load initial data (strategy version + sample stocks)
make seed

# Run test suite (full)
make test

# Verify health
curl http://localhost:8000/health
```

The API listens on `http://localhost:8000`. Firestore emulator runs in Docker (port 8080).

For **production deployment**, see `docs/deployment.md`.

## Documentation

**Read in this order:**

1. [`docs/README.md`](docs/README.md) — navigation and core principles
2. [`docs/01-product-requirements.md`](docs/01-product-requirements.md) — what and why
3. [`docs/02-architecture.md`](docs/02-architecture.md) — how it is built (Firestore, Cloud Run)
4. [`docs/deployment.md`](docs/deployment.md) — **deploying to production**
5. [`docs/03-data-model.md`](docs/03-data-model.md) — Firestore collections and document shapes
6. [`docs/04-api-contract.md`](docs/04-api-contract.md) — every HTTP endpoint
7. [`docs/05-scanner-and-scoring-spec.md`](docs/05-scanner-and-scoring-spec.md) — the funnel
8. [`docs/06-news-and-catalyst-spec.md`](docs/06-news-and-catalyst-spec.md) — how news is used
9. [`docs/07-risk-and-position-sizing.md`](docs/07-risk-and-position-sizing.md) — stops, sizing, guardrails
10. [`docs/stories/README.md`](docs/stories/README.md) — implementation backlog (53 stories, 9 epics)

## Development

All common tasks are in the `Makefile`:

```bash
make help         # List all commands
make build        # Build Docker images
make up           # Start services
make test         # Run test suite
make lint         # Lint + type check
make migrate      # Run migrations
make shell        # Enter API container
```

## Architecture at a glance

```
Telegram → OpenClaw (agent) → FastAPI (backend) → Firestore
   ↓           ↓                  ↓                    ↓
  I/O      Orchestration    Business logic      Durable state
           Intent → tools   Calculations        (append-only)
                          Validation
                          Persistence
                          
                       [Cloud Run]
                      (serverless, scale-to-zero)
```

**Core principle:** Python computes, Firestore remembers, AI interprets, Telegram delivers.

- **LLM never does arithmetic.** Services compute indicators, rank candidates, size positions.
  The agent reads structured data and produces natural-language output.
- **Every recommendation is frozen** with full context (prices, regime, model, prompt version)
  so later analysis is honest and traceable.
- **Failure is visible.** A missing report generates an alert. Bad data raises, never silences.
- **Repository pattern.** All database access through typed repositories. Unit tests inject fakes (no Docker). Integration tests use Firestore emulator.

## Project structure

```
wolfiero-trading/
├── .claude/CLAUDE.md              Project guidelines (production-only system)
├── .gitignore
├── docker-compose.yml             Firestore emulator + API
├── .env.example                   Environment template
├── Makefile                       Common tasks
├── pyproject.toml                 Project config
│
├── backend/                       FastAPI application
│   ├── Dockerfile
│   ├── app/
│   │   ├── main.py                Factory + lifespan
│   │   ├── config.py              Settings (typed, Firestore)
│   │   ├── logging.py             Structured logging
│   │   ├── api/
│   │   │   ├── deps.py            Dependency injection
│   │   │   ├── scanner.py
│   │   │   ├── admin.py
│   │   │   └── stocks.py
│   │   ├── services/              All business logic
│   │   ├── repositories/          Firestore access layer (6 repos)
│   │   ├── providers/             Vendor adapters (market data, news, AI)
│   │   ├── models/                Pydantic document shapes
│   │   ├── schemas/               Request/response DTOs
│   │   ├── jobs/                  Scheduled pipelines (future)
│   │   └── db/
│   │       ├── firestore.py       Async Firestore client
│   │       ├── money.py           Decimal ↔ scaled-int conversion
│   │       └── seed.py            Firestore seeding
│   └── tests/
│       ├── unit/                  Pure functions (fakes, no Docker)
│       ├── integration/           With Firestore emulator
│       └── fixtures/              Golden data CSVs
│
├── openclaw/                      Agent runtime (placeholder)
│   ├── config/
│   ├── tools/
│   ├── prompts/
│   └── skills/
│
└── docs/                          Specifications and stories
    ├── 01-product-requirements.md
    ├── 02-architecture.md         (updated: Firestore + Cloud Run)
    ├── deployment.md              (new: Cloud Run deployment)
    ├── 03-data-model.md           (Firestore collections)
    ├── 04-api-contract.md
    ├── 05-scanner-and-scoring-spec.md
    ├── 06-news-and-catalyst-spec.md
    ├── 07-risk-and-position-sizing.md
    └── stories/                   53 implementation stories
```

## First steps for a developer

1. **Read the architecture**: `docs/02-architecture.md` §1–3.
2. **Understand the core flow**: Telegram → agent → API → services → Postgres.
3. **Pick an epic** from `docs/stories/README.md`, starting with Epic 0 (foundation).
4. **Read the story**, implement it exactly as written, test it, leave it done.
5. **Use `.claude/CLAUDE.md`** as a reference when you hit decisions.

## Configuration

All configuration lives in `.env`, which is loaded and validated by `app/config.py`.

Key secrets:
- `DATABASE_URL` — Postgres connection
- `AI_API_KEY` — LLM provider (Anthropic, etc.)
- `TELEGRAM_BOT_TOKEN` — Telegram bot token
- `MARKET_DATA_API_KEY` — Market data vendor

Never commit `.env`; it is in `.gitignore`.

## Running locally

```bash
# With make (recommended)
make build          # Build Docker images
make up             # Start Firestore emulator + API
make seed           # Load initial data
make test-unit      # Fast unit tests (no Docker)
make test           # Full test suite (with Firestore emulator)

# Individual commands
make logs           # Tail logs
make shell          # Enter API container
make down           # Stop containers
make clean          # Hard reset (remove volumes)
```

The API listens on `http://localhost:8000`; Firestore emulator on `localhost:8080`. See `docker-compose.yml` for ports.

## Testing

```bash
make test           # Full suite (against Firestore emulator)
make test-unit      # Unit tests only (pure functions, fakes, zero Docker)
make test-integ     # Integration tests only (with Firestore emulator)
make test-cov       # With coverage report (generates htmlcov/)
make lint           # ruff + mypy
```

**Unit tests** use fake in-memory repositories (no Docker, runs in milliseconds).  
**Integration tests** spin up Firestore emulator via testcontainers.  
Every service is tested in isolation. Golden fixtures (hand-verified CSVs) are committed alongside tests to catch indicator regressions.

**Before deploying to production:** Run `make test` (full suite) locally to verify against Firestore emulator.

## Production deployment

**See [`docs/deployment.md`](docs/deployment.md) for the complete guide.**

Summary:
- **Platform:** Google Cloud Run (serverless containers, scale-to-zero)
- **Database:** Google Firestore (free tier covers this workload)
- **Cost:** ~$0/month (within free tier limits)

Pre-deployment checklist:
- Full test suite passes locally (`make test`)
- Smoke test succeeds (`make smoke`)
- All secrets configured (`.env`)
- Git is clean

Deploy:
```bash
gcloud run deploy wolfiero-api \
  --image gcr.io/$PROJECT_ID/wolfiero-api:latest \
  --set-env-vars "GCP_PROJECT_ID=$PROJECT_ID,TELEGRAM_BOT_TOKEN=$TOKEN,TELEGRAM_ALLOWED_CHAT_IDS=$CHAT_ID,AI_API_KEY=$API_KEY"
```

This is a **production-only system** — no separate staging/dev environments. Test locally with Docker + Firestore emulator before deploying.

## Contributing

1. Read `.claude/CLAUDE.md` for coding conventions.
2. Pick a story from `docs/stories/`, implement it completely.
3. All acceptance criteria must pass (test, lint, type check).
4. Leave the code in a state where the next story can build on it.

Non-negotiable rules:
- **Python computes.** No LLM arithmetic.
- **Immutable snapshots.** No UPDATE on candidates, recommendations, regimes.
- **Version-stamped outputs.** Every analytical result carries `strategy_version` and model info.
- **One-way dependencies.** Services → providers. Never reverse.

## License

MIT

## Contact

Haseeb Saeed · haseeb@goevolo.com
