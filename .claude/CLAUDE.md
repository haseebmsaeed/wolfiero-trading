# Wolfiero Trading Agent — Implementation Guidelines

## ⚠️ PRODUCTION-ONLY SYSTEM

**This is the sole production trading application. There are NO separate dev/staging/test environments.**
All changes go directly to production code. Test locally with docker-compose + Firestore emulator before
committing. Once deployed to Cloud Run, changes are live immediately.

## Read first

- `docs/README.md` — navigation hub and core principles
- `docs/01-product-requirements.md` — problem and scope
- `docs/02-architecture.md` — system design and tech stack
- Story files in `docs/stories/` for specific work — they are self-contained

## Core rules — non-negotiable

**Python computes. Firestore remembers. AI interprets. Telegram delivers.**

1. **The LLM never calculates.** No indicator, ranking, arithmetic, or price ever comes from a model.
   Services compute. APIs expose. Agents interpret structured data.

2. **Services hold all logic.** Never put business rules in an endpoint handler or a job. A service
   must be testable from a unit test with no HTTP involved.

3. **Money is `Decimal`, never float.** Accumulated float error in P&L is indefensible.

4. **Timestamps are `TIMESTAMPTZ` (UTC); trading dates are `DATE` (market time).** Use the market
   calendar (`pandas_market_calendars`) for every trading-day computation.

5. **Every analytical output is version-stamped**: `strategy_version`, and — where an LLM was involved
   — `model_provider`, `model_name`, `prompt_version`. Without this, changing a weight silently
   invalidates historical analysis.

6. **Snapshots are immutable.** Never UPDATE a candidate, recommendation, or regime row after
   creation. Outcomes are recorded in separate rows.

7. **Fail loud on data quality, degrade gracefully on provider outage.** Bad data raises. A missing
   provider produces a partial result with an explicit warning, never silence.

8. **Test structure must match code structure.** If `services/foo.py` exists, `tests/unit/test_foo.py`
   tests it in isolation. If an endpoint touches the DB, it has an integration test. Golden fixtures
   exist for every indicator.

## Working with this codebase

### Starting a task

Every story in `docs/stories/` is self-contained and has acceptance criteria. Read the story first.

1. Read the story (§**Build**, §**Acceptance**, §**Notes**).
2. Check the **dependencies** — the story may list prior stories that must exist.
3. Implement the code.
4. Make sure **all acceptance criteria pass**, including tests.
5. Leave the code in a state where the next story can build on it.

### Repository structure

```
wolfiero-trading/
├── .claude/CLAUDE.md               (this file)
├── .gitignore
├── docker-compose.yml              (Firestore emulator + API)
├── .env.example
├── Makefile
├── pyproject.toml
│
├── backend/                        # FastAPI application
│   ├── Dockerfile
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py               (Firestore settings, no DB URL)
│   │   ├── logging.py
│   │   ├── api/                    # FastAPI routes
│   │   │   ├── deps.py             # Dependency injection (repositories → services)
│   │   │   ├── scanner.py
│   │   │   ├── admin.py
│   │   │   └── stocks.py
│   │   ├── services/               # Business logic (Scanner, Universe, MarketData)
│   │   ├── repositories/           # Firestore data access layer (6 repos)
│   │   ├── providers/              # External data sources (Yahoo Finance)
│   │   ├── models/                 # Pydantic document shapes
│   │   ├── schemas/
│   │   ├── jobs/                   (empty, no scheduled jobs yet)
│   │   └── db/
│   │       ├── firestore.py        # Async Firestore client (cached)
│   │       ├── money.py            # Decimal ↔ scaled-int conversion
│   │       └── seed.py             # Firestore seeding (strategy + stocks)
│   └── tests/
│       ├── unit/                   (pure functions, no DB/HTTP)
│       └── integration/            (Firestore emulator tests)
│
├── openclaw/                       # Agent runtime config
│   ├── config/
│   ├── tools/
│   ├── prompts/
│   └── skills/
│
└── docs/                           (specs and stories)
```

### Running the project

```bash
make build           # Build Docker images (FastAPI + Firestore emulator)
make up              # Start the stack (Firestore emulator + API)
make seed            # Load initial universe and strategy version
make down            # Stop and remove containers
make test            # Run full test suite
make test-unit       # Unit tests only (no Docker needed)
make test-integ      # Integration tests (uses Firestore emulator)
make lint            # Run ruff + mypy
make format          # Auto-format code with ruff
make smoke           # Health check + quick analysis test
make logs            # Tail Docker logs
make shell           # Open bash in the API container
make clean           # Remove all containers and volumes (hard reset)
```

**Local dev workflow:**
1. `make build` — build images
2. `make up` — start Firestore emulator + API
3. `make seed` — load sample data
4. Hit `http://localhost:8000/health` to verify API is up
5. `make test-unit` — run unit tests (no Docker dependency)
6. `POST http://localhost:8000/api/scanner/run` to trigger a scan
7. `make down` when done

### Conventions

**Imports**: Prefer explicit, local imports over `*`. Every service/provider is imported where used,
making dependencies visible.

**Naming**: 
- Routes: kebab-case (`/api/stocks/analyze`)
- Functions/methods: snake_case
- Classes: PascalCase
- Constants: UPPER_SNAKE_CASE

**Error handling**: Use the standard error envelope from `04-api-contract.md`. Every error response
is JSON with `error.code`, `error.message`, `error.detail`, `error.request_id`.

**Logging**: Structured JSON via `structlog`. Every log at a service boundary carries
`request_id`/`run_id`. No raw prints; no stack traces in production responses.

**Testing**:
- **Unit tests** are pure functions: use `FakeStockRepository`, `FakePriceHistoryRepository`, etc. from `app.repositories.fakes`. Zero Docker/Firestore dependency. Run with `make test-unit` locally.
- **Integration tests** use `testcontainers` to spin up an ephemeral Firestore emulator (via `docker`). Run with `make test-integ`.
- Fixtures are committed CSVs or JSON files in `tests/fixtures/`.
- A `freezegun` utility freezes time for date-dependent tests.
- No tests make real HTTP calls; use `respx` or `responses` for mocking.
- **Before deploying to production, run `make test` (full suite) locally to verify against Firestore emulator.**

**Config**: Everything in `app/config.py`, typed with Pydantic. `os.getenv` appears **only** there.
Enforce via a CI check: `grep -r "os.getenv" app/ | grep -v "config.py"` must return nothing.

## Decision record

**Why Firestore instead of PostgreSQL?**
This is a solo trader's scanning system: 1 user, 1-2 scans/day, minimal Telegram queries. Cloud SQL
costs ~$8/month minimum; Firestore free tier (50K reads/day, 20K writes/day) covers this usage at
$0/month. Cloud Run's scale-to-zero billing matches actual usage (runs only during scans). Trade-off:
no server-side GROUP BY (sector aggregation now in Python), no single atomic transaction across
thousands of docs (replaced with chunked WriteBatch + audit doc). Decision: Firestore is correct for
this workload.

**Why Cloud Run instead of Compute Engine/VM?**
No servers to patch, scales to zero between scans, billing matches actual usage. Forward note: if
scheduled jobs (Celery, APScheduler) are added later, they'll need Cloud Scheduler + Cloud Run Jobs
(Cloud Run's scale-to-zero incompatible with in-process schedulers). Currently no scheduled jobs.

**Why repository pattern with Protocol interfaces?**
Services never touch the database layer directly. All data access goes through repositories typed
against Protocol interfaces. This allows unit tests to inject FakeStockRepository, FakePriceHistoryRepository,
etc., running in milliseconds with zero Docker/Firestore dependency. Integration tests use real Firestore
emulator via testcontainers. Structurally enforces testability.

**Why scaled-integer money (not strings)?**
Firestore has no native Decimal type. Storing prices as strings requires parsing on every read.
Scaled integers (price × 10_000 → store as int, divide on retrieval) preserve exactness under JSON
serialization and remain range-queryable. Conversion funnels through one module (`app/db/money.py`)
using Decimal arithmetic only (never float). Satisfies core rule: "Money is Decimal, never float."

**Why immutable snapshots?**
So that "did my ideas work?" is answerable without the analysis being contaminated by hindsight.
A candidate row never changes. Outcomes are recorded separately. Firestore enforces this via the
repository: `create_many()` uses `.create()` semantics (fails on duplicate), not `.set()` (upsert).

**Why version-stamp analytical outputs?**
Changing a weight without a version boundary silently invalidates all prior analytics. The system
must be able to segregate results by strategy version so tuning is traceable.

**Why no Redis/Celery initially?**
Half a dozen cron-like jobs on one host do not justify two extra services. Graduate only when a
measured limit says otherwise — job concurrency, job distribution, or retry semantics that are
genuinely required.

## Production deployment checklist

**Before any change goes live, you MUST:**
1. Run `make test` locally (full test suite against Firestore emulator).
2. Run `make smoke` to verify API health + quick analysis.
3. Verify no remaining `os.getenv` calls outside `app/config.py` (except tests).
4. Verify all Firestore queries are indexed (check `firestore.indexes.json`).
5. Verify Telegram token and chat IDs are set in `.env`.
6. Test the full scanning pipeline manually via `POST /api/scanner/run`.

**Deployment to Cloud Run:**
- Use `gcloud run deploy` with production Firestore project.
- Set environment: `GCP_PROJECT_ID`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_CHAT_IDS`, `AI_API_KEY`.
- Monitor logs via Cloud Logging.
- No separate staging — test locally with emulator, deploy directly to production.

**Critical safeguards:**
- Candidate immutability is enforced at repository level (`.create()` fails on duplicate).
- Money arithmetic uses Decimal throughout (never float).
- Scan runs are idempotent (same run_id returns existing result).
- Strategy versions are append-only (no UPDATE).

## Talking to me (Claude)

When you reach a decision point or hit a blocker:

- Paste the relevant spec excerpt or story section, not the whole doc.
- State what you tried and what happened.
- If it's a design choice, frame it as a trade-off you're weighing.
- **Remember: This is production-only. All changes are live after deployment. No staging environment.**

I'll help unblock without second-guessing completed work.
