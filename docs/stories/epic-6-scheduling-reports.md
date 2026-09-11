# Epic 6 — Scheduling & Reports

**Goal:** the pre-market report arrives at 07:00 every trading day without being asked.
**Done when:** reports land on time for five consecutive trading days, and a failure is impossible to
mistake for a quiet market.

> **The product becomes valuable the day it stops needing to be asked.** Everything before this epic
> is a tool you have to remember to use; everything after it is an analyst who shows up.

---

### W-37  Scheduler infrastructure                                      [M] [depends: W-03]

**Why this exists**
Jobs must run on market time, skip non-trading days, never overlap, and survive restarts. Getting
this subtly wrong means a report at the wrong hour, or two scans racing each other into the same
database rows.

**Build**
- `jobs/scheduler.py` — APScheduler wired into the FastAPI lifespan, with an
  `AsyncIOScheduler` and a persistent jobstore so a restart does not lose the schedule.
- **Market-calendar awareness**: jobs skip weekends, holidays, and half-day sessions (the EOD report
  must follow a 13:00 close on a half day, not 16:00).
- All cron triggers in `America/New_York`; all storage in UTC.
- `max_instances=1` and a misfire grace period per job — never run two scans concurrently.
- `agent_runs` row per execution with per-step status, timing, and cost.
- `POST /api/admin/jobs/{name}/run` for manual triggering.
- Startup log listing every registered job and its next fire time.

**Acceptance**
- Jobs do not fire on a US market holiday (test with `freezegun` against Thanksgiving and July 4).
- Half-day sessions shift the EOD job correctly.
- A restart mid-schedule resumes without duplicating or dropping jobs.
- Two simultaneous triggers of the same job result in one execution.

---

### W-38  Pre-market pipeline orchestration                             [L] [depends: W-37, W-30, W-36]

**Why this exists**
This is the assembly line the whole product runs on. Its design goal is **resilience through
granularity**: a failure at 06:55 must not discard work done at 05:30.

**Build**
- `jobs/premarket.py` implementing architecture §7 step by step: refresh data → regime → scan →
  catalyst enrichment → trade plans → position health → synthesis → deliver.
- **Every step persists its result before the next begins.**
- Every step is idempotent for `(date, strategy_version)`; re-running a single step is supported.
- **The 05:30 coverage gate is the one hard abort**: below `MIN_DATA_COVERAGE_PCT`, stop and alert.
  A scan on 60% of the universe is not a partial answer, it is a misleading one.
- Every other step degrades: no news → report ships with "catalyst data unavailable"; regime failure
  → fall back to the previous day's regime with an explicit notice.
- One `run_id` on every log line and persisted row.
- Per-step timing recorded so the 20-minute margin before send time is measurable, not assumed.

**Acceptance**
- Full pipeline on the fixture dataset completes end to end.
- Simulated news-provider failure still produces a delivered report carrying the gap notice.
- Simulated 60% coverage aborts with an alert and no report.
- Re-running the synthesis step alone reuses the persisted scan rather than rescanning.
- Total runtime leaves ≥ 20 minutes before `REPORT_SEND_TIME`.

---

### W-39  Pre-market report generation                                  [L] [depends: W-38]

**Why this exists**
This is the artefact you actually read every morning, and the one output where a strong model earns
its cost. It has to be scannable on a phone in under two minutes.

**Build**
- `services/reporting.py::build_premarket_payload(date)` assembling the structured input: regime,
  candidates with plans and catalysts, portfolio status and required actions, today's earnings and
  economic events, and **what changed since yesterday**.
- `providers/ai/prompts/premarket_report.v1.md` — **strong** tier, one call, receiving only that
  payload.
- Report structure, in this order: market regime and its implication for sizing → required actions
  on open positions (stops hit, targets near, earnings tomorrow) → top candidates with entry, stop,
  target, R, size, catalyst, and risk → what changed → today's calendar.
- **Actions on existing positions come before new ideas.** Managing what you hold is always more
  urgent than adding to it, and a report that leads with shiny new candidates encourages exactly the
  wrong behaviour.
- Persist to `reports` with both `content_markdown` and the `payload`, so it can be re-rendered or
  re-synthesised without re-running the pipeline.

**Acceptance**
- The report is under 2,000 words and readable on a phone.
- Every number in it appears in the payload — run the grounding guard over the generated report too.
- A zero-candidate day produces a coherent report explaining *why* (regime constrained, all vetoed
  on earnings, etc.) rather than an empty section.
- Generation cost per report is logged and stays within budget.

---

### W-40  Telegram report delivery                                      [M] [depends: W-39, W-15]

**Why this exists**
An undelivered report is a failed report. Delivery needs to be verified, retried, and — if it
ultimately fails — loudly visible.

**Build**
- Delivery service: chunking on paragraph boundaries, Markdown escaping, ordered send.
- Retry with backoff on Telegram API failure; `delivery_status` recorded on the report row.
- A short summary message first ("📈 Pre-market report — RISK_ON, 7 candidates, 1 action required"),
  then the full report. *(The summary is what you read at a glance; the body is what you read when
  the summary says something needs you.)*
- Failure after all retries → a `CRITICAL` log and a retry on the next scheduled cycle.

**Acceptance**
- A 6,000-character report arrives as correctly ordered chunks with intact formatting.
- A simulated Telegram outage retries and records the failure state.
- The summary message accurately reflects candidate count and action count.

---

### W-41  End-of-day & weekly reports                                   [M] [depends: W-39]

**Why this exists**
The EOD report closes the daily loop; the weekly review is the only place the system holds you
accountable to your own process. Skipping the weekly is how a disciplined system quietly becomes a
tip service.

**Build**
- `jobs/end_of_day.py` (16:30, half-day aware): how the morning's candidates actually performed,
  position updates, alerts that fired, tomorrow's earnings in your book, tomorrow's watch items.
- `jobs/weekly_review.py` (Sunday): realised performance in R, win rate **and average R** by setup
  and regime, largest win and largest loss with a brief post-mortem, guardrail adherence, and
  observations from outcome analytics once Epic 8 lands.
- Both persisted and delivered like the pre-market report.

**Acceptance**
- EOD report correctly attributes intraday moves to the morning's candidates.
- Weekly review reports sample sizes alongside every statistic.
- Both are half-day and holiday aware.

---

### W-42  Pipeline watchdog                                             [S] [depends: W-38]

**Why this exists**
**A missing report must never be indistinguishable from a quiet market.** Silent failure is the worst
outcome this system can produce, because you will assume everything is fine and trade without the
information you were relying on.

**Build**
- A watchdog job at 07:15 checking that today's `PREMARKET` report exists with
  `delivery_status='DELIVERED'`.
- On failure: a `CRITICAL` Telegram alert naming the last completed pipeline step and the error.
- Equivalent checks for the EOD and weekly reports.
- `/health/deep` exposes the last successful run per job.

**Acceptance**
- Deliberately failing the pipeline produces the alert within 15 minutes of the expected delivery.
- The alert names the failed step, not a generic "something went wrong".
- The watchdog does not fire on non-trading days.
