# Epic 0 — Foundation & Infrastructure

**Goal:** a running, observable, migratable skeleton on one VM. No market logic yet.
**Done when:** `make up && make migrate && make smoke` succeeds on a clean machine and `/health/deep`
reports a healthy database.

> **Why this epic comes first and must not be rushed.** Every later story writes to the database,
> reads config, and emits logs. If migrations, settings, and logging are retrofitted after ten
> services exist, you will spend more time reworking them than building them now. Specifically:
> adding Alembic after the schema has drifted means hand-writing a baseline migration against a
> database nobody can reproduce.

---

### W-01  Repository skeleton & tooling                                          [S]

**Why this exists**
The layering rule in [02-architecture.md](../02-architecture.md) §4 (`api → services →
providers|models`) is the thing that keeps the LLM out of the compute layer. Directory structure is
how that rule gets enforced in practice — if `services/` does not exist on day one, logic lands in
route handlers and never leaves.

**Build**
- Repo tree exactly as in architecture §4. Every package gets `__init__.py`; empty dirs get a
  `.gitkeep`.
- `pyproject.toml`: Python 3.12, `fastapi`, `uvicorn[standard]`, `sqlalchemy[asyncio]>=2.0`,
  `alembic`, `asyncpg`, `pydantic-settings`, `httpx`, `pandas`, `numpy`, `pandas-ta`,
  `pandas_market_calendars`, `structlog`, `apscheduler`, `python-telegram-bot`.
  Dev: `pytest`, `pytest-asyncio`, `pytest-cov`, `ruff`, `mypy`, `freezegun`, `respx`,
  `testcontainers[postgres]`.
- `ruff` + `mypy` config (strict on `app/services` and `app/providers`).
- `Makefile`: `up down build logs test lint format migrate revision seed smoke shell`.
- `.gitignore`, `.env.example` (names only, no values), pre-commit with `detect-secrets`.
- `README.md`: what it is, how to run it, link to `docs/`.

**Acceptance**
- `make lint` and `make test` pass on an empty test suite.
- `detect-secrets` runs in pre-commit and blocks a deliberately planted fake key.

**Notes**
Pin versions. `pandas-ta` in particular has a history of breaking changes across minors, and a silent
formula change would alter every recommendation the system makes.

---

### W-02  Docker Compose stack                                                   [M]

**Why this exists**
One command must reproduce the whole environment. The scheduler and the API write to the same
database concurrently, so Postgres — not SQLite — has to be there from the very first story.

**Build**
- `docker-compose.yml` with `postgres` (16-alpine, named volume, healthcheck) and `wolfiero-api`
  (built from `backend/Dockerfile`, `depends_on: postgres: condition: service_healthy`).
- Multi-stage Dockerfile: builder installs deps, runtime is slim, runs as a **non-root** user.
- `docker-compose.override.yml.example` for dev: source bind-mount, `--reload`, published port.
- Base compose publishes **no** ports for the API — internal network only (architecture §10).
- `.env` wired via `env_file`.

**Acceptance**
- `make up` on a clean machine reaches a healthy API within 60s.
- `docker compose down && up` preserves database data (named volume, not anonymous).
- Container runs as non-root (`docker compose exec wolfiero-api id` ≠ uid 0).

**Out of scope** Caddy, TLS, published ports. Nothing is externally exposed in v1.

---

### W-03  Configuration & settings                                               [S]

**Why this exists**
Scattered `os.getenv` calls are untestable and unvalidatable — a typo in an env var name surfaces at
06:00 on a trading morning as a mysterious `None`. One typed settings object fails loudly at
startup instead.

**Build**
- `app/config.py`: a Pydantic `Settings` class covering every variable in architecture §9, with
  types, defaults, and validators (e.g. `risk_per_trade_pct` in (0, 5]; provider chain parses
  comma-separated into a list).
- `@lru_cache` singleton `get_settings()`; FastAPI dependency for injection.
- **The application refuses to start** if a required secret is missing, naming the variable.
- `strategy_versions` YAML loader with an assertion that scoring weights sum to 1.0 ± 1e-6.

**Acceptance**
- Missing `DATABASE_URL` produces a clear startup error naming the variable.
- Weights that do not sum to 1.0 raise at startup, not at scan time.
- `os.environ` / `os.getenv` appear **only** in `config.py` (enforce with a grep test in CI).

---

### W-04  Database foundation & migrations                                       [M]

**Why this exists**
Alembic must exist before the first table. Retrofitting it means reverse-engineering a baseline from
a drifted database, which is error-prone and unrepeatable.

**Build**
- `app/db/session.py`: async engine, `async_sessionmaker`, `get_db()` dependency with correct
  commit/rollback/close semantics.
- `Base` declarative class with a `TimestampMixin` (`created_at`, `updated_at`).
- Alembic configured for async + autogenerate, with a naming convention set on `Base.metadata` so
  constraint names are deterministic across environments.
- First migration: `stocks`, `price_history`, `strategy_versions` per
  [03-data-model.md](../03-data-model.md).
- `make seed`: inserts `strategy_versions` `v1.0.0` from YAML.
- A `testcontainers`-based pytest fixture giving each test module a fresh migrated database.

**Acceptance**
- `alembic upgrade head` then `downgrade base` runs cleanly both ways.
- `alembic revision --autogenerate` on an unchanged model set produces an **empty** migration.
  *(If it does not, your metadata and migration have already diverged — fix it now, not later.)*
- Integration test writes and reads a `stocks` row.

**Notes**
Use `NUMERIC(18,4)` for all prices from the very first migration. Converting a populated `FLOAT`
column later is a data-integrity exercise nobody enjoys.

---

### W-05  Logging, correlation IDs & health endpoints                            [M]

**Why this exists**
When a recommendation looks wrong three weeks from now, you need to reconstruct the entire path:
which Telegram message, which tool call, which provider response, which model. That is only possible
if one identifier threads through everything from the first line of code.

**Build**
- `app/logging.py`: structlog JSON renderer, level from config, stdlib logging routed through it.
- `contextvars`-based correlation ID; middleware reads `X-Request-ID` or generates one, binds it to
  the log context, and echoes it in the response.
- Background jobs bind a `run_id` the same way, so scheduled and interactive paths are traced
  identically.
- Request/response logging with method, path, status, duration — **secrets and API keys redacted**.
- `GET /health` (liveness) and `GET /health/deep` per API contract §Health.
- Global exception handler emitting the standard error envelope with the request ID.

**Acceptance**
- Every log line is valid JSON containing `request_id` or `run_id`.
- A request with `X-Request-ID: abc` produces logs and an error envelope carrying `abc`.
- `/health/deep` reports DB latency and returns `degraded` (not 500) when Postgres is stopped.
  *(A health endpoint that itself crashes tells you nothing.)*
- An unhandled exception returns the envelope, not a stack trace.

---

### W-06  VM provisioning & deployment runbook                                   [M]

**Why this exists**
The system's value depends on a report arriving at 07:00 every trading morning. That is an
availability requirement, and availability comes from provisioning and backups, not from code.

**Build**
- `docs/deployment.md`: Azure VM creation, Docker install, UFW (22 source-restricted + nothing
  else), SSH key-only auth, unattended-upgrades, timezone `UTC` with app-level market-time handling.
- Deploy script: `git pull && make build && make up && make migrate && make smoke`.
- Nightly `pg_dump` to Azure Blob via cron, 30-day retention.
- **A documented and actually-performed restore drill**, with the date of the last successful drill
  recorded in the runbook.
- Docker log rotation (`json-file`, `max-size: 10m`, `max-file: 3`) — otherwise logs fill the disk
  and the pipeline dies in a way that looks like a code bug.

**Acceptance**
- A fresh VM reaches a working stack by following the runbook literally, with no undocumented steps.
- A backup is taken, the database is dropped in a scratch environment, and the restore is verified.
- `docker system df` shows bounded log growth after a simulated high-volume day.

**Out of scope** CI/CD pipelines, blue-green deploys, autoscaling. `git pull && make up` on one box.
