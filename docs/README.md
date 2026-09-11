# Wolfiero Market Agent — Documentation Index

Wolfiero is a **decision-support system for discretionary swing trading**. It scans the US equity
market every day, ranks candidates using deterministic quantitative logic, enriches the short list
with news and catalyst research, and delivers the result to a single human operator over Telegram.

It does **not** place trades. It does **not** manage money. It produces *evidence*; the human
produces *decisions*.

## Read in this order

| # | Document | What it answers |
|---|---|---|
| 1 | [01-product-requirements.md](01-product-requirements.md) | Who is this for, what problem does it solve, what must it do, what is explicitly out of scope |
| 2 | [02-architecture.md](02-architecture.md) | How the system is physically built — VM, containers, services, module boundaries |
| 3 | [03-data-model.md](03-data-model.md) | Every PostgreSQL table, column, and why it exists |
| 4 | [04-api-contract.md](04-api-contract.md) | Every HTTP endpoint the agent layer and jobs call |
| 5 | [05-scanner-and-scoring-spec.md](05-scanner-and-scoring-spec.md) | The exact funnel, indicator formulas, setup detectors, and scoring weights |
| 6 | [06-news-and-catalyst-spec.md](06-news-and-catalyst-spec.md) | How news becomes a tradeable signal instead of noise |
| 7 | [07-risk-and-position-sizing.md](07-risk-and-position-sizing.md) | Stops, targets, R-multiples, sizing, portfolio-level guardrails |
| 8 | [stories/README.md](stories/README.md) | The implementation backlog — epics and stories written for an autonomous coding agent |

## The one-sentence architecture

> Python computes, PostgreSQL remembers, the AI interprets, Telegram delivers.

Every design decision in these documents traces back to that sentence. If a proposed change makes
the AI responsible for arithmetic, or makes the database optional, or makes the human read JSON —
it is the wrong change.

## Non-negotiable principles

1. **Determinism before intelligence.** Anything that can be computed with a formula is computed
   with a formula. The LLM never calculates an indicator, never ranks a list, never invents a price.
2. **The funnel is the cost control.** 3,000 symbols → ~150 by math → ~20 by score → AI reads 20.
   AI cost is bounded by design, not by hope.
3. **Every recommendation is a falsifiable record.** Entry, stop, target, thesis, model, strategy
   version, and market regime are all written to the database at the moment of the call, so the
   system can later be asked *"which of my ideas actually worked?"*
4. **Human in the loop, always.** No broker keys with trade permissions. No auto-execution. Ever.
5. **One VM, one compose file.** Complexity is added only when a measured limit is hit.
