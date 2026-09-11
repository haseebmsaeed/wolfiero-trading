# Epic 2 — Agent Runtime & Telegram Interface

**Goal:** you type "Analyze NVDA" into Telegram from your phone and receive a grounded, readable
technical analysis.
**Done when:** the loop closes — Telegram → OpenClaw → API → analysis → LLM interpretation →
Telegram — with every number traceable to a tool result.

> **This is the milestone that makes the project feel real**, and it is deliberately placed before
> the scanner. A system you can talk to, with one working capability, teaches you more about what
> you actually want than three more weeks of backend built in the dark.

---

### W-14  OpenClaw deployment & configuration                            [M] [depends: W-02]

**Why this exists**
The agent runtime must live alongside the API on the same internal network, so tool calls never
leave the VM and no port is exposed.

**Build**
- `openclaw` service in `docker-compose.yml`, on the shared network, with `WOLFIERO_API_URL` and
  the API key injected.
- `openclaw/config/` — runtime config, AI provider routing (cheap / mid / strong model names from
  env), and conversation persistence.
- Health check plus restart policy.
- Startup log line confirming which models are configured for which tier.

**Acceptance**
- `make up` starts OpenClaw healthy and it can reach `http://wolfiero-api:8000/health`.
- Swapping `AI_MODEL_MID` in `.env` and restarting changes the model actually used, verified in the
  `model_runs` log.
- No OpenClaw port is published to the host.

---

### W-15  Telegram bot integration & access control                      [M] [depends: W-14]

**Why this exists**
Telegram is the entire user interface. It is also a public, probed surface: bot tokens leak and bots
receive unsolicited traffic within hours of first use. An allowlist is the whole auth model, so it
has to be correct.

**Build**
- Telegram adapter wired to OpenClaw, long-polling (no public webhook endpoint needed).
- **Hard allowlist** on `TELEGRAM_ALLOWED_CHAT_IDS`. Any other chat is rejected with a generic
  message and logged at `WARNING` with the chat ID.
- Typing indicator during processing; a "still working…" message after 10s.
- Message chunking at the 4096-character limit, splitting on paragraph boundaries so Markdown is
  never broken mid-entity.
- Markdown escaping for symbols like `_` and `*` that appear in tickers and numbers.
- `/start`, `/help`, `/status` commands.

**Acceptance**
- A message from an allowlisted chat gets a reply; one from any other chat gets the rejection and a
  log entry.
- A 9,000-character report arrives as multiple messages with intact formatting and no mid-table split.
- Bot survives an API restart and reports degraded status rather than crashing.

---

### W-16  Tool definitions & the API bridge                              [M] [depends: W-13, W-14]

**Why this exists**
Tool descriptions are the only information the model has when choosing what to call. A vague
description produces wrong tool selection, which is the dominant failure mode of agent systems — far
more common than the model reasoning badly about correct data.

**Build**
- `openclaw/tools/` — one definition per endpoint from architecture §8, with JSON-schema parameters.
- Shared HTTP bridge: injects the API key and a correlation ID, sets a 30s timeout, retries once on
  5xx, and surfaces the standard error envelope to the model as a readable message.
- Start with `analyze_stock` and `get_stock_history` only; the rest are added by their own epics.
- Tool descriptions state **when to use** and **when not to**, e.g.
  *"Use for technical analysis of ONE known symbol. Do NOT use to find new ideas — use `scan_market`."*

**Acceptance**
- "Analyze NVDA" calls `analyze_stock(symbol="NVDA")` exactly once.
- "How's Nvidia looking?" resolves to the same call — company name → ticker mapping works.
- An API 404 produces "I don't have data for that symbol" rather than a raw stack trace or, worse,
  an answer from model memory.
- A scripted conversation fixture asserts tool name and arguments, not prose.

---

### W-17  System prompt & the grounding contract                         [M] [depends: W-16]

**Why this exists**
The single most dangerous failure this product can have is stating a confident, wrong price. The
model's training data contains stale prices for every ticker and it will happily recite them. A
system that is usually right and occasionally invents a number is worse than no system, because you
will act on it.

**Build**
- `openclaw/prompts/system.v1.md`, versioned, containing:
  - Role: analytical assistant to one experienced swing trader. Direct, quantitative, no filler, no
    motivational language, no repeated disclaimers.
  - **Grounding rules** (architecture §8): every number from a tool result in this turn; no model
    memory for any market fact; state clearly when a tool returns nothing; cite source and timestamp
    for news; never assert certainty about future prices.
  - Explicit separation of *computed fact* / *interpretation* / *speculation*.
  - Domain vocabulary: the four setups, R-multiple, regime, heat — so it uses your language.
  - Output conventions for Telegram: short paragraphs, tables only when they survive at phone width,
    the key conclusion first.
- Prompt version recorded in `model_runs` for every call.

**Acceptance**
- Asked "what's the price of a stock the tools have no data for", the reply says it has no data —
  and does not produce a number. Test this against at least 5 symbols.
- Asked something outside the tool surface ("what will NVDA do next week?"), it declines to predict
  and reframes toward what the data shows.
- Responses put the conclusion first and are under ~300 words unless a report was requested.

**Notes**
Test this adversarially and repeatedly. Try to *make* it hallucinate: ask leading questions, supply
a wrong price and ask it to confirm, ask about a delisted ticker. Each prompt revision bumps the
version so regressions in this behaviour are attributable.

---

### W-18  Response grounding guard                                       [S] [depends: W-17]

**Why this exists**
The system prompt is a strong instruction, not a guarantee. A cheap deterministic check catches
drift and, just as importantly, gives you data on how often it happens — which tells you whether the
prompt is working.

**Build**
- Post-response validator: extract numeric tokens from the reply, compare against all numbers present
  in that turn's tool payloads (with tolerance for rounding and derived arithmetic like percentage
  differences).
- Unmatched numbers → log a `GROUNDING_WARNING` with the response, the turn's payloads, and the
  offending tokens.
- A daily counter exposed on `/health/deep`.
- Configurable `GROUNDING_GUARD_MODE`: `log` (default) or `block` (append a caveat to the reply).

**Acceptance**
- A synthetic response containing an invented price is flagged.
- Legitimately derived figures ("up 3.2%" computed from two provided prices) do **not** flag —
  false positives would train you to ignore the warning, which defeats its purpose.
- Guard adds under 50ms.

**Out of scope** Blocking by default. Start in `log` mode and tune the tolerance against real traffic
before ever enabling `block`.
