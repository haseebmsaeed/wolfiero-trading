# Spec 02 — Data & Halal Universe

**Status:** Draft
**Phase:** 1
**Depends on:** Spec 01 (Trading Constitution)
**Downstream:** Every other spec depends on this

---

## 1. Purpose

Every downstream decision is only as good as the data underneath it. This spec defines:

1. **Data providers** and their roles
2. **Data quality gates** that must pass before any trade card can be generated
3. **Corporate action handling** (splits, dividends, spin-offs, mergers)
4. **Halal classification** — sourcing, refresh, and at-time-of-trade tagging
5. **The tradeable universe** — the pool of stocks the strategy engine may consider

This spec exists because **most quant blowups have roots in bad data**, not in bad strategy.

---

## 2. Data Providers

### 2.1 Primary Sources

| Data type | Primary provider | Purpose |
|-----------|------------------|---------|
| Historical prices (EOD OHLCV) | Yahoo Finance / Polygon.io / EODHD | Backtesting, indicator calculation |
| Historical prices (intraday) | Polygon.io (only if intraday setups are added later) | Not required in Phase 1–3 |
| Real-time / delayed quotes | Yahoo Finance / broker feed | Trade card generation, monitoring |
| Fundamentals (income, balance, cash flow) | Financial Modeling Prep / SEC EDGAR | Halal ratio calculation |
| Earnings calendar | Yahoo Finance / FMP | Earnings blackout enforcement |
| Corporate actions | Polygon.io / EODHD | Split/dividend/merger adjustment |
| Sector classification | GICS via provider | Sector leadership analysis |
| Halal classification | Zoya API (default) / Islamicly / manual | Rule Zero enforcement |
| VIX and market indices | Yahoo Finance | Regime classifier |

### 2.2 Redundancy Rule
For every data type marked as critical (prices, halal classification, earnings calendar), a **secondary provider** must be configured. Divergence between primary and secondary above a defined threshold (see 3.2) fires a data quality VETO.

### 2.3 Provider Abstraction
Every provider must be accessed through a **repository / adapter interface**. The strategy, research, and runtime engines never call provider APIs directly. This allows provider substitution without downstream changes.

---

## 3. Data Quality Gates

### 3.1 Freshness Requirements

| Data type | Max acceptable staleness | Action if stale |
|-----------|---------------------------|-----------------|
| EOD prices for held/watchlisted stocks | 1 trading day | VETO |
| Real-time quote before entry | 15 minutes (or as specified) | VETO |
| Halal classification | 90 days | Refresh required; VETO if unavailable |
| Fundamentals | 1 quarter beyond latest earnings | VETO |
| Earnings calendar | 24 hours | VETO |
| Corporate actions | Same trading day | VETO |

### 3.2 Cross-Provider Divergence
When primary and secondary providers both return data:

| Data type | Divergence threshold | Action |
|-----------|----------------------|--------|
| Prices | > 0.5% for the same OHLC bar | VETO; log for investigation |
| Halal classification | Disagreement on business exclusion | VETO |
| Halal classification | Disagreement on ratio pass/fail | VETO |
| Earnings dates | > 1 calendar day | VETO |

### 3.3 Gaps and Missing Data
- If a stock has a missing EOD bar within the analysis window, the stock is VETOed until the gap is resolved.
- No interpolation. No imputation. Missing data = no trade.

### 3.4 Data Health Reporting
- Every trade card includes a `data_health_summary` field showing timestamps of last-refresh for every input.
- Daily health digest sent to the trader listing any stocks that were VETOed on data grounds.

---

## 4. Corporate Actions

### 4.1 Splits
- All historical prices, volumes, and indicators must be **split-adjusted** for research.
- Live prices are **as-traded** for entry/exit; sizing uses as-traded price.
- Any position through a split is auto-adjusted (share count and stop price scale).

### 4.2 Dividends
- Historical prices are **total-return adjusted** for backtesting (assume reinvestment for benchmark comparison; assume paid-out for account P&L).
- Live positions: dividend received in cash, not reinvested by the system.

### 4.3 Mergers, Spin-offs, Delistings
- If a held position undergoes a corporate action mid-trade, position is closed at the last acceptable price and re-evaluated as a new trade if applicable.
- The research engine's universe must include delisted stocks in the historical universe — otherwise survivorship bias will inflate backtested edge.

### 4.4 Symbol Changes
- Historical continuity must be preserved across symbol changes (e.g., FB → META).

---

## 5. Halal Classification

### 5.1 Standard Selection
Per Spec 01 §3.2, the active Shariah standard is a configuration parameter. Default: AAOIFI as implemented by Zoya.

### 5.2 Classification Storage
Halal classifications are stored with:
- Ticker
- Standard used
- Classification (halal / not halal / uncertain)
- Reason (business exclusion / ratio failure / passed)
- Date of classification
- Source (provider name and version)
- **All historical classifications retained** — never overwritten

### 5.3 At-Time-of-Trade Rule
**Critical:** When the research engine or backtester evaluates a historical setup on date D:
- It queries the halal classification as of date D
- It uses the standard active as of date D (from Spec 01 amendment log)
- If no classification exists for date D (e.g., historical gap), the setup is excluded from research — never assumed halal

### 5.4 Refresh Cadence

| Trigger | Action |
|---------|--------|
| Monthly (calendar) | Re-verify business classification for entire watchlist |
| After each earnings release | Re-compute financial ratios for that stock |
| Before generating trade card | Check classification age; VETO if > 90 days |
| Before executing on approved trade | Final classification check; VETO if changed |

### 5.5 Uncertain Classification
If the provider returns "uncertain" or "under review" for a stock:
- Stock is VETOed from any new-entry trade card
- Existing positions are flagged for review but not force-closed unless downgraded to "not halal"
- Uncertain-for-30-days = auto-flat position

### 5.6 Manual Override
The trader may **only** override toward *stricter*, never toward *less strict*. That is: the trader may manually blacklist a stock the provider passed. The trader may **never** manually pass a stock the provider failed.

---

## 6. The Tradeable Universe

### 6.1 Universe Definition
A stock is in the universe on date D if and only if:

1. Listed on NYSE or NASDAQ as common stock
2. Price on date D ≥ $10.00
3. Market cap on date D ≥ $1B
4. 20-day average dollar volume on date D ≥ $20M
5. At least 6 months of continuous EOD history preceding D
6. Optionable (per exchange data on date D)
7. Halal per Spec 01 §3 on date D
8. Not on the internal blacklist (see 6.3)
9. Not a recent IPO (within 6 months of first trade)
10. Not a recent deSPAC (within 6 months of merger completion)

### 6.2 Historical Universe (For Research)
The research engine's universe on any historical date D must satisfy the same criteria evaluated at date D — not today.

### 6.3 Internal Blacklist
Manual list of stocks the trader has decided to permanently exclude, regardless of automated screens. Reasons logged but not restricted.

### 6.4 Universe Refresh Cadence
- **Daily post-close:** rebuild the tradeable universe
- **Intra-day:** universe additions are honored but only for tomorrow's trade cards

### 6.5 Universe Size Expectations
- Approximate universe size after all filters: 400–800 stocks (subject to market conditions)
- If universe drops below 100 stocks: alert the trader; review filters

---

## 7. Data Storage Requirements

### 7.1 Retention
- **Prices:** minimum 10 years of daily history for every stock ever in the universe
- **Fundamentals:** minimum 10 years
- **Halal classifications:** every classification ever recorded, indexed by stock and date
- **Corporate actions:** all events for every historical universe member

### 7.2 Delisted Stocks
Historical data for delisted stocks must be retained indefinitely. Purging historical universe members introduces survivorship bias into all downstream research.

### 7.3 Audit Trail
Every data record (price bar, fundamental snapshot, halal classification, corporate action) is stamped with:
- `provider` (source)
- `retrieved_at` (when we got it)
- `as_of_date` (what date it applies to)
- `provider_version` (if applicable)

---

## 8. Stories

### Story 2.1 — Provider Adapter Interface
**As:** engineering
**I want:** a Protocol-typed adapter for each provider category (prices, halal, fundamentals, earnings, corporate actions)
**So that:** providers can be substituted without downstream changes

**Acceptance criteria:**
- One Protocol per data category
- Each concrete provider implements the Protocol
- All strategy/research code depends on the Protocol, never the concrete class
- Unit tests use fake implementations
- Integration tests run against at least one real provider

### Story 2.2 — Historical Halal Classification Store
**As:** the research engine
**I want:** to query "was ticker X halal on date D under standard S?"
**So that:** backtests respect at-time-of-trade halal status

**Acceptance criteria:**
- Storage schema keyed by (ticker, standard, date)
- Immutable append-only: classifications never mutate; corrections create new records
- Query returns classification, reason, source, and provider timestamp
- If no classification exists for the date, returns UNKNOWN (never assumes halal)
- Test: querying a 2022 date returns 2022 classification even if the stock has been reclassified since

### Story 2.3 — Cross-Provider Divergence Detection
**As:** the runtime
**I want:** automatic divergence checks between primary and secondary providers
**So that:** bad data never reaches a trade card

**Acceptance criteria:**
- Every critical data pull invokes both primary and secondary
- Divergence beyond configured threshold (see §3.2) fires a VETO
- Divergence event is logged with both values, both providers, and stock/date context
- Daily digest lists all divergence events
- If secondary provider is unavailable, primary alone can proceed but with a WARN flag on the trade card

### Story 2.4 — Tradeable Universe Builder
**As:** the runtime
**I want:** a daily job that rebuilds the tradeable universe per §6.1
**So that:** the strategy engine has a fresh, correct pool to evaluate

**Acceptance criteria:**
- Runs after market close, before the next trading day
- Applies all 10 filters in §6.1
- Publishes universe with timestamp and filter counts (how many dropped at each stage)
- Alerts if universe size drops below 100 or grows above 1500 (both are anomalies)
- Historical universe query supports "universe as of date D" for research

### Story 2.5 — Corporate Action Adjuster
**As:** the research and runtime engines
**I want:** all historical prices and indicators split-adjusted, and dividends handled per §4.2
**So that:** indicators computed today match indicators that would have been computed historically

**Acceptance criteria:**
- Split adjustment applied consistently across all historical bars
- Historical indicator values match a golden reference (fixture) for a known-good stock
- Live positions through a corporate action have shares and stop price auto-adjusted
- Delisted stocks remain in the historical universe

### Story 2.6 — Data Health Digest
**As:** the trader
**I want:** a daily summary of data health issues
**So that:** I know before market open whether the system is running on clean data

**Acceptance criteria:**
- Digest delivered by Telegram before US market open
- Lists: stocks VETOed on data quality, halal reclassifications, provider outages, staleness alerts
- Digest also confirms which providers are healthy (positive assertion, not just absence of alerts)

### Story 2.7 — Halal Classification Refresh Job
**As:** the system
**I want:** scheduled refresh of halal classifications
**So that:** classifications never exceed the freshness threshold in §5.4

**Acceptance criteria:**
- Monthly job re-verifies business classification for all watchlisted and held stocks
- Post-earnings hook triggers ratio refresh for the affected stock
- All refreshes append new records; never mutate historical
- Refresh failures alert the trader and pause new-entry generation for affected stocks

### Story 2.8 — Data Freshness Enforcer
**As:** the runtime
**I want:** every input to every trade card checked against its staleness threshold
**So that:** stale data never reaches the trader

**Acceptance criteria:**
- Before card generation, every input timestamp is checked
- Any staleness violation fires a VETO for that stock
- VETO reason and stale input are surfaced in the daily digest
- Test: manually staling a provider by mocking timestamps causes the correct stocks to VETO

---

## 9. Acceptance Criteria for Spec 02

- All stories 2.1–2.8 pass their acceptance criteria
- Golden-fixture tests verify indicator continuity across corporate actions
- A dry-run demonstrates: stale data → VETO; provider divergence → VETO; missing halal classification → EXCLUDED from research; delisted stock present in historical universe
- The strongest reasoning model has reviewed and APPROVED

---

## 10. Open Questions for the Trader

1. **Primary price provider:** Yahoo Finance is free but rate-limited and occasionally stale. Polygon.io or EODHD cost $30–100/month. Which is acceptable?
2. **Halal provider:** Zoya has an API (paid). Islamicly and Wahed do not have accessible APIs. Confirm Zoya.
3. **Historical depth:** minimum 10 years — is 15 years better for research? (More data, less relevant to current regime.)
4. **Provider outage policy:** if primary is down for > 4 hours, do we halt all new-entry generation or proceed with warnings on secondary?
5. **Manual override for halal blacklist:** does the trader want a UI, a config file, or a CLI command?
