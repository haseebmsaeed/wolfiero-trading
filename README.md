# Wolfiero — Market Intelligence Agent for Swing Trading

A decision-support system for discretionary swing traders. Scans 3,000 liquid US equities daily,
ranks candidates using deterministic quantitative logic, enriches with news and catalysts, and
delivers a trade plan to your phone every morning.

**Status:** Under development (Epics 0–1 in progress)

## What it does

- **Market scanning:** 3,000 → ~150 → ~20 tradeable candidates daily under 10 minutes
- **Technical analysis:** Trend, momentum, volatility, support/resistance, setup classification
- **Risk framework:** Structural ATR-based stops, R-multiple validation, portfolio guardrails
- **Catalyst awareness:** News explains moves, gates risk, breaks ties — never predicts
- **Earnings protection:** Hard veto on dates inside your intended hold window
- **Live tracking:** Portfolio P&L, watchlist alerts, position health checks during the session
- **Decision support:** Telegram interface for conversational Q&A

**It does NOT:** place trades, manage money, predict prices, or require a broker API key.

## Quick start

```bash
# Clone and navigate
git clone https://github.com/haseebmsaeed/wolfiero-trading.git
cd wolfiero-trading

# Copy environment template
cp .env.example .env

# Start the stack (Postgres + API)
make up

# Run migrations
make migrate

# Verify health
make smoke
```

Then `curl http://localhost:8000/health` to confirm the API is running.

## Documentation

**Read in this order:**

1. [`docs/README.md`](docs/README.md) — navigation and core principles
2. [`docs/01-product-requirements.md`](docs/01-product-requirements.md) — what and why
3. [`docs/02-architecture.md`](docs/02-architecture.md) — how it is built
4. [`docs/03-data-model.md`](docs/03-data-model.md) — database schema
5. [`docs/04-api-contract.md`](docs/04-api-contract.md) — every HTTP endpoint
6. [`docs/05-scanner-and-scoring-spec.md`](docs/05-scanner-and-scoring-spec.md) — the funnel
7. [`docs/06-news-and-catalyst-spec.md`](docs/06-news-and-catalyst-spec.md) — how news is used
8. [`docs/07-risk-and-position-sizing.md`](docs/07-risk-and-position-sizing.md) — stops, sizing, guardrails
9. [`docs/stories/README.md`](docs/stories/README.md) — implementation backlog (53 stories, 9 epics)

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
Telegram → OpenClaw (agent) → FastAPI (backend) → PostgreSQL
   ↓           ↓                  ↓                    ↓
  I/O      Orchestration    Business logic      Durable state
           Intent → tools   Calculations
                          Validation
                          Persistence
```

**Core principle:** Python computes, Postgres remembers, AI interprets, Telegram delivers.

- **LLM never does arithmetic.** Services compute indicators, rank candidates, size positions.
  The agent reads structured data and produces natural-language output.
- **Every recommendation is frozen** with full context (prices, regime, model, prompt version)
  so later analysis is honest and traceable.
- **Failure is visible.** A missing report generates an alert. Bad data raises, never silences.

## Project structure

```
wolfiero-trading/
├── .claude/CLAUDE.md              Project guidelines for Claude Code
├── .gitignore
├── docker-compose.yml             Full stack definition
├── .env.example                   Environment template
├── Makefile                       Common tasks
├── pyproject.toml                 Project config
│
├── backend/                       FastAPI application
│   ├── Dockerfile
│   ├── app/
│   │   ├── main.py                Factory + lifespan
│   │   ├── config.py              Settings (typed)
│   │   ├── logging.py             Structured logging
│   │   ├── api/                   HTTP endpoints (thin)
│   │   ├── services/              All business logic
│   │   ├── providers/             Vendor adapters (market data, news, AI)
│   │   ├── models/                SQLAlchemy ORM
│   │   ├── schemas/               Pydantic request/response DTOs
│   │   ├── jobs/                  Scheduled pipelines
│   │   └── db/
│   │       ├── session.py
│   │       └── migrations/        Alembic
│   └── tests/
│       ├── unit/                  Logic in isolation
│       ├── integration/           With DB
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
    ├── 02-architecture.md
    ├── 03-data-model.md
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
make up && make migrate && make test

# Or with docker-compose directly
docker compose up -d
docker compose exec wolfiero-api alembic upgrade head
docker compose exec wolfiero-api pytest
```

The API listens on `http://localhost:8000` when published; see `docker-compose.yml` for the port.

## Testing

```bash
make test           # Full suite
make test-unit      # Unit tests only
make test-cov       # With coverage report (generates htmlcov/)
```

Every service is tested in isolation. Integration tests use an ephemeral Postgres. Golden fixtures
(hand-verified CSVs) are committed alongside tests to catch indicator regressions.

## Deployment

See `docs/deployment.md` (planned in Epic 0).

One VM, one `docker-compose.yml`. Migrations and backups are included.

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
