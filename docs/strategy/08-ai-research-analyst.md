# Spec 08 — AI Research Analyst

**Status:** Draft
**Phase:** 3
**Depends on:** Specs 01, 02, 09
**Downstream:** Trade Card (Spec 09) embeds AI analyst prose

---

## 1. Purpose

The AI Research Analyst is an LLM-powered component that produces **qualitative context** for each trade candidate: earnings summaries, guidance interpretation, SEC-filing highlights, catalyst identification, and risk callouts.

**It does not decide trades. It does not vote. It does not produce numbers used for sizing or thresholding.** Its role is analogous to a junior analyst preparing a briefing note for the trader — informative, cited, and always overridable.

---

## 2. Guiding Principles

### P1 — Prose, Not Numbers
The analyst produces text. Any number in that text is quoted from source material (e.g., "Q3 EPS came in at $2.14 vs consensus $2.02"). The analyst does not produce probability scores, price targets, or expectancy estimates.

### P2 — Cited or Absent
Every claim in analyst output must cite its source (SEC filing URL, earnings-call transcript, press release, news article). Unattributed claims are treated as hallucinations and stripped.

### P3 — Bounded Input, Bounded Output
The analyst reads a defined corpus (last earnings release, most recent 10-Q/10-K, last 30 days of press releases, analyst upgrade/downgrade actions). It does not roam the internet.

### P4 — Optional, Not Load-Bearing
If the analyst is unavailable (LLM outage, quota exhausted, source data missing), the trade card is still generated with a "no analyst context available" note. The system does not halt.

### P5 — Reproducible-ish
LLM outputs are non-deterministic. We accept this for prose. However:
- Same-day repeated queries should produce substantially similar summaries
- Analyst outputs are versioned (LLM model + prompt version stamped on every output)
- Regressions detected via periodic manual review

### P6 — Read-Only
The analyst never triggers actions. It writes context that a human reads and considers.

---

## 3. Inputs

For each trade candidate, the analyst is provided:

| Input | Source | Purpose |
|-------|--------|---------|
| Ticker, company name, sector | Spec 02 | Identity |
| Most recent earnings release (as text) | SEC EDGAR / FMP | Earnings context |
| Most recent 10-Q or 10-K (excerpt: MD&A + risk factors) | SEC EDGAR | Business context |
| Last earnings call transcript excerpt | Provider | Management tone |
| Press releases in last 30 days | Provider | Recent developments |
| Analyst rating changes in last 30 days | Provider | Sentiment shift |
| Upcoming earnings date and time | Spec 02 | Blackout check |
| Recent news headlines (top 10) | Provider | Catalyst identification |

**Inputs are NOT:** speculation, forums, Twitter, meme signals, "unusual options activity" narratives. Those belong elsewhere or not at all.

---

## 4. Prompt Structure

### 4.1 System Prompt
```
You are a research analyst preparing a briefing note for a swing trader.
You produce concise, factual context — never predictions, price targets, or trade recommendations.
Every factual claim must cite its source (URL or filing identifier).
Never estimate probabilities. Never say "will" — use past-tense or citational language.
Output structured JSON per the schema.
```

### 4.2 User Prompt (Templated)
```
Ticker: {ticker}
Company: {company_name}
Sector: {sector}
Upcoming earnings: {earnings_date_time}

Context sources:
- Latest earnings release: {earnings_text}
- Latest 10-Q excerpt: {10q_excerpt}
- Recent press releases: {press_list}
- Recent analyst actions: {analyst_actions}
- Recent headlines: {headlines}

Produce a briefing per the schema.
```

### 4.3 Output Schema (JSON)
```json
{
  "recent_developments": [
    { "summary": "string", "source": "URL or filing id", "date": "YYYY-MM-DD" }
  ],
  "earnings_context": {
    "last_report_summary": "string",
    "guidance_direction": "raised | maintained | lowered | none | unknown",
    "guidance_source": "URL",
    "next_earnings_date": "YYYY-MM-DD"
  },
  "management_tone": {
    "summary": "string",
    "source": "URL or transcript id",
    "confidence": "low | medium | high"
  },
  "notable_risks": [
    { "risk": "string", "source": "URL or filing id" }
  ],
  "catalysts": [
    { "catalyst": "string", "source": "URL", "expected_date": "YYYY-MM-DD or null" }
  ],
  "one_sentence_summary": "string (≤ 200 chars)"
}
```

**Fields NOT permitted in output:** price predictions, probability estimates, buy/sell recommendations, forward-looking claims without citation, opinions attributed to "the market" or "traders."

---

## 5. Fallback Behavior

### 5.1 LLM Unavailable
If the LLM API call fails after 3 retries:
- Trade card is generated with `analyst_context: null`
- Trade card includes note: "AI analyst context unavailable"
- Trader still receives all quantitative context (Specs 03, 05, 06, 07)

### 5.2 Source Data Missing
If a source (earnings release, 10-Q, transcript) is missing:
- Analyst proceeds with available sources
- Output includes `sources_used` and `sources_missing` fields
- Trade card notes reduced context

### 5.3 Cost Guardrails
- Monthly LLM spend cap configured (default: $50/month for Phase 3)
- If cap approached, analyst runs only for A-rated candidates
- If cap reached, analyst pauses; trade cards proceed without it

---

## 6. Governance

### 6.1 Model Selection
- Primary: strongest available reasoning model (Anthropic Opus, OpenAI o-series, etc.)
- Downgrade tier: mid-tier model (Sonnet, GPT-4-mini) for cost management if daily spend spikes
- Model + version stamped on every output

### 6.2 Prompt Versioning
- Prompt is a versioned config artifact
- Prompt changes require review (does the change alter the schema? did we A/B test?)
- Historical outputs retain the prompt version used

### 6.3 Output Sampling and Review
- Weekly: sample 5 recent analyst outputs; manual spot-check for hallucination
- If hallucination detected, log and investigate; may trigger prompt adjustment or model change

### 6.4 Redaction
- If the LLM produces content that violates Section 4.3 (prices, probabilities, recommendations), the runtime auto-redacts before showing to trader
- Redaction events logged for prompt iteration

---

## 7. Role in the Trade Decision

The analyst's output appears in the Trade Card (Spec 09) under a `Context (AI Analyst)` section. It:

- **Adds:** narrative context the trader can skim to check for "anything I should know before approving?"
- **Does not:** change the deterministic setup detection, expectancy stats, or portfolio decision
- **Can:** flag a catalyst that overlaps a scheduled position, prompting the trader to defer approval

**The trader may:**
- Read the analyst context and approve as normal
- Read the analyst context, notice a red flag (e.g., a subpoena mentioned in filings), and reject
- Ignore the analyst context entirely (still valid — it is advisory)

---

## 8. Stories

### Story 8.1 — Analyst Prompt Template
**As:** engineering
**I want:** a versioned prompt template per §4
**So that:** analyst behavior is auditable and reproducible-ish

**Acceptance criteria:**
- Prompt stored as a versioned file
- Version bumped on any change; historical versions retained
- Every analyst output stamps the prompt version

### Story 8.2 — Analyst Runner
**As:** the trade card generator
**I want:** a `run_analyst(ticker, sources) → AnalystOutput | None`
**So that:** analyst context is appended when available

**Acceptance criteria:**
- Assembles inputs per §3
- Calls LLM with system + user prompt
- Parses JSON output; rejects malformed responses
- Retries up to 3 times on transient failures; returns None thereafter
- Latency < 10 seconds per call (typical)

### Story 8.3 — Hallucination Guard
**As:** the runtime
**I want:** automatic redaction of forbidden content per §4.3 and §6.4
**So that:** the trader never sees a hallucinated price target

**Acceptance criteria:**
- Regex + rule-based filter for numeric predictions, probability language, buy/sell verbs without citation
- Redacted content replaced with "[redacted — {reason}]"
- Redaction event logged
- False-positive rate reviewed quarterly

### Story 8.4 — Source Citation Enforcer
**As:** the runtime
**I want:** every factual claim in analyst output to have a `source` field populated
**So that:** unattributed claims are treated as hallucination

**Acceptance criteria:**
- Parser rejects output items missing source or with source="unknown"
- Rejected items either regenerated (one retry) or omitted
- Analyst output includes `sources_used` array

### Story 8.5 — Cost Guardrail
**As:** the trader
**I want:** monthly LLM spend capped and monitored
**So that:** costs never surprise

**Acceptance criteria:**
- Config `analyst_monthly_cap_usd`
- Rolling monthly spend tracked
- At 80% of cap: alert; only A-rated candidates get analyst
- At 100%: analyst pauses; trade cards continue without

### Story 8.6 — Model Fallback Tier
**As:** engineering
**I want:** auto-downgrade to a cheaper model when daily spend spikes
**So that:** the system remains operational without breaking the cost cap

**Acceptance criteria:**
- Config lists primary and fallback model
- Daily spend threshold triggers fallback
- Every output records which tier was used

### Story 8.7 — Weekly Sample Review
**As:** the trader / QA
**I want:** a weekly digest of 5 sampled analyst outputs
**So that:** hallucination and quality drift can be caught early

**Acceptance criteria:**
- Weekly job selects 5 random recent outputs
- Digest includes output, ticker, timestamp, model, prompt version
- Reviewer marks each pass/fail; failures logged for investigation

### Story 8.8 — Trade Card Integration
**As:** the trade card generator (Spec 09)
**I want:** analyst output rendered under a clearly labeled section
**So that:** the trader knows this is qualitative context, not a signal

**Acceptance criteria:**
- Section titled "AI Research Analyst (advisory)" with disclaimer
- Rendered fields: recent_developments, earnings_context, management_tone, notable_risks, catalysts, one_sentence_summary
- If analyst unavailable, section shows "context unavailable"

---

## 9. Acceptance Criteria for Spec 08

- All stories 8.1–8.8 pass their acceptance criteria
- Hallucination guard test: feed the LLM a prompt designed to elicit a price target; confirm redaction
- Fallback test: simulate LLM outage; confirm trade card still generated
- Cost guardrail test: simulate spend at threshold; confirm downgrade and pause behavior
- Strongest available reasoning model has reviewed and APPROVED

---

## 10. Open Questions for the Trader

1. **Primary model:** which model tier for analyst (Opus-class, Sonnet, GPT-4o)?
2. **Monthly LLM cap:** $50 default — adjust up or down?
3. **News source:** paid news feeds (Benzinga, Polygon news) or free (RSS, Google news)?
4. **Manual review cadence:** weekly sample of 5 — appropriate?
5. **Language:** English only, or should we support multi-language filings for foreign ADRs?
