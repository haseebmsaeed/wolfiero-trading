# Wolfiero Trading Agent — Implementation Guidelines

## Read first

- `docs/README.md` — navigation hub and core principles
- `docs/01-product-requirements.md` — problem and scope
- `docs/02-architecture.md` — system design and tech stack
- Story files in `docs/stories/` for specific work — they are self-contained

## Core rules — non-negotiable

**Python computes. Postgres remembers. AI interprets. Telegram delivers.**

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
├── docker-compose.yml
├── .env.example
├── Makefile
├── pyproject.toml
│
├── backend/                        # FastAPI application
│   ├── Dockerfile
│   ├── requirements.txt            (or use pyproject.toml)
│   ├── alembic.ini
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── logging.py
│   │   ├── deps.py
│   │   ├── api/
│   │   ├── services/
│   │   ├── providers/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── jobs/
│   │   └── db/
│   └── tests/
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
make build      # Build Docker images
make up         # Start the stack
make down       # Stop and remove containers
make migrate    # Run Alembic migrations
make test       # Run test suite
make lint       # Run linter
make logs       # Tail Docker logs
make shell      # Open a shell in the API container
```

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
- Unit tests are pure functions: no DB, no HTTP, no side effects.
- Integration tests use `testcontainers` for an ephemeral Postgres.
- Fixtures are committed CSVs or JSON files in `tests/fixtures/`.
- A `freezegun` utility freezes time for date-dependent tests.
- No tests make real HTTP calls; use `respx` or `responses` for mocking.

**Config**: Everything in `app/config.py`, typed with Pydantic. `os.getenv` appears **only** there.
Enforce via a CI check: `grep -r "os.getenv" app/ | grep -v "config.py"` must return nothing.

## Decision record

**Why no Redis/Celery initially?**
Half a dozen cron-like jobs on one host do not justify two extra services. Graduate only when a
measured limit says otherwise — job concurrency, job distribution, or retry semantics that are
genuinely required.

**Why Alembic from day one?**
Retrofitting migrations after the schema has drifted is miserable. A `baseline()` migration on a
drifted database is error-prone and unrepeatable. Write migrations as you go.

**Why immutable snapshots?**
So that "did my ideas work?" is answerable without the analysis being contaminated by hindsight. A
candidate row never changes. Outcomes are recorded separately. This is what makes Epic 8 possible at all.

**Why version-stamp analytical outputs?**
Changing a weight without a version boundary silently invalidates all prior analytics. The system
must be able to segregate results by strategy version so tuning is traceable.

## Talking to me (Claude)

When you reach a decision point or hit a blocker:

- Paste the relevant spec excerpt or story section, not the whole doc.
- State what you tried and what happened.
- If it's a design choice, frame it as a trade-off you're weighing.

I'll help unblock without second-guessing completed work.
