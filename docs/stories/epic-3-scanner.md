# Epic 3 — Universe & Scanner

**Goal:** "Find today's top swing candidates" returns a ranked, explainable list in under 10 minutes.
**Done when:** a full 3,000-symbol scan completes inside budget and every candidate's score can be
decomposed into its contributing components.

> **Scale discipline matters here.** The difference between a scanner that runs in 6 minutes and one
> that runs in 90 is entirely in whether stages 2–3 are vectorised and whether any network I/O
> leaked into the loop. Write it vectorised the first time; retrofitting it means rewriting it.

---

### W-19  Universe construction & refresh                                [M] [depends: W-09]

**Why this exists**
An unbounded universe scans junk; a hand-curated one embeds your existing blind spots. A mechanical
liquidity screen gives you a defensible, reproducible opportunity set.

**Build**
- `services/universe.py`:
  - `refresh_universe()` — pull the listed-symbol master, upsert `stocks`, apply the liquidity screen
    from [05-scanner-and-scoring-spec.md](../05-scanner-and-scoring-spec.md) §Stage 2, set
    `in_universe`.
  - Exclusions: leveraged/inverse ETFs (name and metadata matching), `first_trade_date` within 60
    trading days, blocklisted symbols, non-common-stock/ETF types.
  - Membership-change logging: entries and exits with the reason.
- `jobs/universe_refresh.py`, weekly (Sunday).
- `POST /api/admin/universe/refresh`, `GET /api/admin/universe/stats`.

**Acceptance**
- Refresh produces 2,000–4,000 symbols. Outside that band, fail loudly — it means the source
  changed shape, and a silently 200-symbol universe would produce plausible but impoverished scans.
- Membership changes are logged with reasons.
- Re-running is idempotent.
- Known leveraged ETFs (`TQQQ`, `SQQQ`, `UVXY`) are excluded.

**Notes**
Compute liquidity over a **20-trading-day** window using the market calendar. A calendar-day window
silently varies its sample size around holidays.

---

### W-20  Scanner funnel skeleton & instrumentation                      [L] [depends: W-19, W-12]

**Why this exists**
The funnel counts are the debugging interface for the whole product. On a morning that returns zero
candidates, they tell you in one glance whether the market genuinely offered nothing or stage 3 has
a bug. Build the instrumentation *with* the funnel, never after.

**Build**
- `services/scanner.py` with an explicit staged pipeline; each stage is a separate function taking
  and returning a symbol set plus a `StageResult(entered, exited, dropped_reasons: Counter)`.
- Stages 1–4 per the spec.
- **Stage 2 is fully vectorised**: load all universe bars into one multi-index DataFrame and filter
  cross-sectionally. No per-symbol loop, no I/O.
- **Stage 3 computes indicators in batch** over the surviving frame.
- Stage 4 loops over ~500 symbols, structured so a `ProcessPoolExecutor` can be dropped in later.
- `scan_runs` persistence with the full `funnel` JSONB, `data_coverage_pct`, timing per stage.
- Idempotency: unique `(trade_date, strategy_version)`; `force=true` replaces.

**Acceptance**
- End-to-end scan on the frozen 200-symbol fixture produces exactly the expected per-stage counts.
- Full 3,000-symbol scan completes in under 10 minutes on 2 vCPU / 8 GB, with per-stage timings
  logged.
- Zero network calls during stages 2–5 (assert with a patched HTTP transport).
- Every dropped symbol has a recorded reason; entered/exited/dropped reconcile exactly at each stage.

---

### W-21  Composite scoring engine                                       [M] [depends: W-20]

**Why this exists**
Ranking is what converts 150 survivors into a list you can act on before the open. It must be
explainable — "why is this number 1?" needs an answer with arithmetic in it, not a paragraph of prose.

**Build**
- `services/scoring.py::score_candidate(snapshot, setup, regime, catalyst, trade_plan) ->
  ScoreResult` implementing the formula in spec §Stage 5.
- Weights loaded from the active `strategy_versions.weights`; startup assertion that they sum to 1.0.
- Per-component normalisers, each a separate tested function. **RSI is scored as a band
  (45–70 optimal), not monotonically** — RSI 85 must score *lower* than RSI 60.
- Missing component → neutral 0.5, flagged in the breakdown. **Never 0.**
- `score_breakdown` persists raw, normalised, weight, and contribution for every component.
- `catalyst_score` accepts an injected value, defaulting to 0.5 until Epic 5 provides real ones.

**Acceptance**
- Property tests: score always in [0,100]; improving any single input never lowers the total;
  identical inputs give identical outputs (fully deterministic).
- Component contributions sum to the total within floating-point tolerance.
- RSI 85 scores below RSI 60 on the momentum component — regression-test this explicitly.
- A candidate with no news data is not penalised relative to one with neutral news.

**Notes**
Weights are a coherent set that must move together, which is why they live in versioned YAML rather
than individual env vars. Changing any weight requires a new `strategy_version` and a note saying
why — otherwise all prior outcome analytics become uninterpretable.

---

### W-22  Candidate persistence & the candidates API                     [M] [depends: W-21]

**Why this exists**
Candidates are immutable point-in-time snapshots. Storing them — including the vetoed ones — is what
makes Epic 8 possible at all, and specifically what lets you later measure whether your veto rules
are helping or costing you.

**Build**
- Alembic migration for `candidates` per the data model.
- `services/scanner.py` persists the ranked list with full technicals, score breakdown, and setup.
- `GET /api/scanner/candidates?date=&limit=&include_vetoed=`
- `GET /api/scanner/runs/{run_id}` returning status and funnel.
- `POST /api/scanner/run` returning `202` with a `run_id`; concurrent run for the same date → `409`.

**Acceptance**
- Candidates are never updated after insert (enforce with a DB trigger or a repository-level guard).
- `include_vetoed=true` returns vetoed rows with populated `veto_reasons`.
- Querying candidates for a date with no scan returns an empty list with an explanatory `meta`
  warning — not a 404, because "no scan ran" and "no candidates found" are different facts and the
  agent must be able to tell you which.

---

### W-23  Scanner regression fixture                                     [M] [depends: W-22]

**Why this exists**
This is the safety net for the entire product. Without it, an innocuous refactor of an indicator can
silently change every recommendation you receive, and you would not find out for months — by which
point the outcome data is contaminated too.

**Build**
- `tests/fixtures/scan_2026_XX_XX/` — real historical bars for ~200 symbols across one known date,
  covering all four setups, plus edge cases (a low-liquidity name, a recent IPO, a high-volatility
  name, a symbol with a data gap).
- Expected output: per-stage counts and the exact ranked candidate list with scores to 2dp.
- `test_scanner_regression` asserting every stage and the final ranking.
- A documented procedure for intentionally updating the fixture: bump `strategy_version`, regenerate,
  **diff and review the change**, record the rationale in `strategy_versions.notes`.

**Acceptance**
- Test passes deterministically, with time frozen via `freezegun`.
- A deliberately introduced off-by-one in the RSI period makes it fail.
- Runs in under 60 seconds so it stays in the default test run rather than being skipped.

---

### W-24  `scan_market` tool & conversational scanning                   [S] [depends: W-22, W-16]

**Why this exists**
Closes the loop on the epic: the scanner becomes usable from your phone.

**Build**
- `scan_market` tool → `GET /api/scanner/candidates` (latest completed scan).
- `run_scan` tool → `POST /api/scanner/run` for an on-demand refresh, with an explicit warning to the
  user that it takes several minutes.
- Prompt guidance: present the top 5 conversationally with setup, score, and the one-line reason;
  offer the rest on request. **Never dump twenty JSON blobs into Telegram.**

**Acceptance**
- "What looks good today?" returns a readable ranked summary.
- "Why is X ranked first?" produces the score decomposition in plain language, with the actual
  component numbers.
- If no scan has run today, the agent says so and offers to trigger one — it does not silently serve
  yesterday's list as though it were current.
