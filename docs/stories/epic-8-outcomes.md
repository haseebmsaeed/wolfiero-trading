# Epic 8 — Outcome Tracking & Learning

**Goal:** the system answers, with data, *"which of my setups actually work, and in which market
regime?"*
**Done when:** the weekly review contains statistically-qualified observations drawn from real
forward outcomes.

> **This is what separates a tool from a system that compounds.** Everything before this epic
> produces opinions. This epic produces evidence about whether those opinions were any good —
> and it is the only honest basis for ever changing the strategy.

---

### W-49  Recommendation persistence                                    [M] [depends: W-39]

**Why this exists**
Analysis requires a frozen record of what was actually said, when, and under what assumptions.
Reconstructing a past recommendation from current data is impossible and would be contaminated by
hindsight even if it were possible.

**Build**
- Alembic migration for `recommendations`.
- When a report is generated, every surfaced candidate is frozen into a `recommendation`: prices,
  score, thesis, catalyst summary, risks, market regime, `strategy_version`, model provider, model
  name, and prompt version.
- `setup_type` and `market_regime` are **denormalised deliberately** — candidate rows may be pruned
  under the retention policy, and these must survive.
- Status lifecycle: `OPEN` → `TRIGGERED` / `EXPIRED` / `INVALIDATED` / `CLOSED`.
- Recommendations are **immutable** after creation; enforce it.

**Acceptance**
- Every candidate in a delivered report has a corresponding recommendation row.
- No code path updates a recommendation's prices, score, or thesis.
- The model and prompt version that produced each thesis are recorded — this is what later makes
  model-versus-model comparison possible.

---

### W-50  Forward outcome tracking                                      [L] [depends: W-49]

**Why this exists**
This is the leakage-free alternative to a backtest. It is slower — you accumulate samples in real
time — but it is honest, and it measures the system you actually have rather than an idealised
reconstruction of it.

**Build**
- Alembic migration for `recommendation_outcomes`.
- `jobs/outcome_tracker.py`, daily after the close: for every recommendation inside its horizon
  (default 15 trading days), walk the bars since recommendation and update:
  - `entry_triggered` and the date (did price reach the trigger at all?)
  - **MFE** — maximum favourable excursion, % — *was the target reasonable?*
  - **MAE** — maximum adverse excursion, % — *was the stop reasonable?*
  - `hit_target`, `hit_stop`, and `first_hit` — **order matters**; both can occur within a horizon
    and assuming the favourable one is how backtests flatter themselves
  - `realized_r_multiple`, `return_pct_at_horizon`, `days_to_resolution`
  - `benchmark_return_pct` — SPY over the identical window, so you measure **alpha, not just return**
- Mark `is_final` when the horizon closes.
- Backfill support for recommendations created before this story shipped.

**Acceptance**
- Hand-computed fixtures reproduce MFE, MAE, and R exactly, including a case where the stop is hit
  before the target and a case where the reverse is true.
- Intrabar ambiguity is resolved **conservatively**: when a single bar's range spans both stop and
  target, assume the stop was hit first. Anything else systematically overstates performance.
- Benchmark return uses the same trading-day window, not calendar days.
- An untriggered recommendation is marked `EXPIRED` after 5 sessions and excluded from
  entry-conditional statistics.

**Notes**
MFE and MAE are what turn outcome data into *improvement*. A strategy with a 35% win rate whose
losers rarely exceed −0.4 MAE before reversing does not have a selection problem — it has a
stop-placement problem. Win rate alone cannot distinguish those two cases, which is why it is the
most over-quoted and least useful statistic in trading.

---

### W-51  Performance analytics                                        [M] [depends: W-50]

**Why this exists**
Aggregate numbers are where patterns become visible — and where you are most likely to fool
yourself. The statistical guardrails in this story matter as much as the arithmetic.

**Build**
- `services/outcomes.py::analytics(group_by, period)` supporting `setup_type`, `market_regime`,
  `score_bucket`, `sector`, `has_catalyst`, `model_name`, `strategy_version`.
- Per group: count, entry trigger rate, win rate, average R, **expectancy in R**, average MFE,
  average MAE, average days to resolution, and alpha versus benchmark.
- **Every statistic is reported with its sample size, and the service refuses to state a conclusion
  below `MIN_SAMPLE_SIZE` (default 30)** — it returns the numbers labelled "insufficient sample"
  instead.
- `GET /api/outcomes/analytics`; `get_performance` tool.

**Acceptance**
- Analytics reconcile against a hand-computed fixture set.
- A group with n=11 is returned but explicitly labelled insufficient, and no conclusion is drawn
  from it.
- Win rate is never returned without average R alongside it — a 40% win rate with +2.5R winners is
  an excellent system, and reporting the 40% alone is actively misleading.
- Slicing by `strategy_version` correctly segregates results across a weight change.

---

### W-52  Weekly findings & observations                               [M] [depends: W-51]

**Why this exists**
Numbers that nobody reads change nothing. The weekly review is where evidence becomes a decision —
and the point at which you, not the system, choose whether to adjust.

**Build**
- Extend `jobs/weekly_review.py` with an analytics section.
- Deterministic observation generation for statistically-qualified patterns, e.g. *"PULLBACK setups
  in RISK_ON produced +0.81R over 44 samples; the same setup in RISK_OFF produced −0.12R over 17
  (insufficient sample)."*
- Structural observations comparing MAE to stop distance: *"Average MAE on winners is −2.4% against
  a mean stop distance of −4.1%, suggesting stops could tighten without materially increasing
  stop-outs."*
- Behavioural observations: recommendations you took versus skipped, and how each group performed —
  *do you follow your own system, and does deviating help?*
- The LLM writes the narrative **from the computed observations only**; it never derives a statistic
  itself.

**Acceptance**
- Observations appear only above the minimum sample size.
- The take-versus-skip comparison works via the `positions.recommendation_id` link.
- No statistic in the narrative is absent from the underlying payload — run the grounding guard over it.

---

### W-53  Strategy versioning workflow                                 [S] [depends: W-52]

**Why this exists**
Tuning weights is legitimate and expected. Tuning them **without a version boundary** silently
invalidates every historical comparison you have, and you will not notice until you try to answer a
question and find the data incoherent.

**Build**
- `POST /api/admin/strategy-versions` — publish a new weight and threshold set with mandatory notes
  explaining the rationale.
- Activation sets `deactivated_at` on the prior version; **all history is retained**.
- `GET /api/admin/strategy-versions` with a diff view between versions.
- Analytics default to grouping by `strategy_version` whenever more than one is present in the
  period, so a change can never be accidentally averaged across.
- The scanner regression fixture update procedure from W-23 is required as part of publishing.

**Acceptance**
- Publishing a version without notes is rejected.
- Analytics across a version boundary segregate rather than blend.
- The active version is visible on `/health/deep` and stamped on every scan.

**Out of scope**
**Automatic weight optimisation.** With a few hundred samples, an optimiser will overfit with
near-certainty and hand you a strategy tuned to noise, wearing the costume of rigour. The system
reports; you decide. Revisit only with thousands of samples and proper out-of-sample validation —
and treat that as its own project, not a story.
