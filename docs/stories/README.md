# Wolfiero — Implementation Backlog

Stories are written to be picked up by an autonomous coding agent with no prior context. Each one is
self-contained: it states *why* it exists, exactly what to build, how to verify it, and what it must
not do.

## Epics

| Epic | Theme | Phase | Stories |
|---|---|---|---|
| [E0](epic-0-foundation.md) | Foundation & infrastructure | 0 | 6 |
| [E1](epic-1-market-data.md) | Market data & technical analysis | 1 | 7 |
| [E2](epic-2-agent-telegram.md) | Agent runtime & Telegram | 1 | 5 |
| [E3](epic-3-scanner.md) | Universe & scanner | 2 | 6 |
| [E4](epic-4-regime-risk.md) | Market regime, trade plans & risk | 3 | 6 |
| [E5](epic-5-news-catalysts.md) | News, catalysts & earnings | 4 | 6 |
| [E6](epic-6-scheduling-reports.md) | Scheduling & reports | 5 | 6 |
| [E7](epic-7-portfolio-alerts.md) | Portfolio, watchlist & alerts | 6 | 6 |
| [E8](epic-8-outcomes.md) | Outcome tracking & learning | 7 | 5 |

Total: 53 stories. Build them **in order**. The dependency graph is nearly linear by design — each
epic produces something verifiable that the next one consumes.

## Story format

```
### W-XX  Title                                          [size] [depends: W-YY]

**Why this exists**   The problem in the domain. An implementer who reads only this should
                      understand what would break if the story were skipped.
**Build**             Concrete deliverables.
**Acceptance**        Objectively checkable statements.
**Notes**             Pitfalls, formulas, decisions already made — do not re-litigate these.
**Out of scope**      What NOT to build. Present when scope creep is likely.
```

Sizes: **S** ≈ half a day · **M** ≈ 1–2 days · **L** ≈ 3–5 days.

## Definition of Done — applies to every story

1. Code merged to `main` and the Compose stack starts clean from scratch.
2. Unit tests for all new logic; integration tests for anything touching the DB or HTTP.
3. `make test` and `make lint` pass. Type hints on every public function; `mypy` clean.
4. New config in `.env.example` **and** `config.py`, documented.
5. New tables ship with an Alembic migration that upgrades *and* downgrades.
6. Structured logs at service boundaries, carrying `run_id` / `request_id`.
7. Errors use the standard envelope from [04-api-contract.md](../04-api-contract.md).
8. No secrets in the repo.
9. Relevant doc updated if behaviour diverged from spec — **and the divergence explained**.

## Standing rules for the implementing agent

These override any local convenience and are not negotiable without a spec change:

- **The LLM never calculates.** No indicator, ranking, arithmetic, or price ever comes from a model.
- **Services hold the logic.** API handlers validate and serialise; jobs orchestrate. A service must
  be callable from a test with no HTTP.
- **Providers never import services.** One-way dependency, enforced in review.
- **Money is `Decimal`/`NUMERIC`, never float.**
- **Timestamps are `TIMESTAMPTZ` in UTC; trading dates are `DATE` in market time.** Use a real
  market calendar (`pandas_market_calendars`) for every trading-day computation — never
  `timedelta(days=n)`.
- **Snapshots are immutable.** Never `UPDATE` a candidate, recommendation, or regime row.
- **Version-stamp every analytical output** with `strategy_version`, and with model and prompt
  version wherever an LLM was involved.
- **Fail loud on data quality, degrade gracefully on provider outage.** Bad data raises. A missing
  provider produces a partial result with an explicit warning — never silence.
- **Ask before adding a dependency or a service.** Redis, Celery, and Kubernetes are out of scope
  until a measured limit says otherwise.
