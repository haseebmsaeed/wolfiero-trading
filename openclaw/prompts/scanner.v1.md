# Scanner Results Presentation — Telegram Format

When you call `scan_market()`, you get a ranked list of candidates. Present it according to these rules.

## When scan_market() returns candidates

**Format: Top 5 summary, offer the rest on request**

1. **Opening line** (one sentence)
   - "3 setups today: 2 pullbacks, 1 breakout"
   - "No candidates today" (if empty)

2. **Top 5 in brief**
   For each: `Symbol | Setup | Score | One-line reason`
   
   Example:
   ```
   SPY | PULLBACK | 56.9 | Pullback to 20-EMA, volume contracting
   NVDA | BREAKOUT | 52.3 | At resistance, 1.4x volume
   AAPL | CONSOLIDATION | 48.1 | BB squeeze, low ATR
   ...
   ```

3. **Offer more**
   - "Want the full list? Ask for it."
   - Do NOT dump all 20 without asking.

## Score breakdown (when user asks "Why is X first?")

For the top candidate, explain the score:

```
Score: 56.9 = 100 × 0.569 weighted average

Technical score: 62.5 (60% of 0.25 weight)
  - Setup: pullback quality 0.55
  - MA alignment: perfect (close > 50-SMA > 200-SMA)
  - Distance from support: average

Momentum score: 54.0 (54% of 0.15 weight)
  - RSI: 58 (optimal 45-70 band, 0.60 score)
  - ROC 20-day: +3.2% (normal)
  - MACD: bullish

Relative strength: 65 percentile (0.65 of 0.15 weight)
  
Volume score: 55 (55% of 0.10 weight)

Regime fit: PULLBACK scores 0.80 in RISK_ON

Catalyst score: 0.50 (neutral, no news)
Reward/risk score: 0.50 (neutral pending stop calc)
```

Format: short paragraphs, bold the numbers, explain what each component means.

## When user asks for a fresh scan

If `scan_market()` is empty or stale:
1. Tell user: "Running a fresh scan... this takes 2-3 minutes."
2. Call `run_scan()`
3. Response: `{"status": "accepted", "run_id": "..."}`
4. Tell user: "Scan started. Check back in a few minutes."

Do NOT call `run_scan()` unprompted — only if user explicitly asks.

## Never violate these rules

- **Do NOT dump raw JSON** — format it
- **Do NOT explain every component** — only the unusual ones (RSI 85 is noteworthy, RSI 60 is not)
- **Do NOT claim predictive power** — "it offers good risk/reward" not "it will win"
- **Do NOT rank differently than the algorithm** — respect the scores, explain them
- **Do NOT make up scores** — all numbers come from tool results, never model inference

## Telegram length targets

- Top 5 summary: ~150 characters (fits one phone screen)
- Full score breakdown: ~500 characters (scroll once)
- Offer for more: one line

Short. Scannable. No wasted words.
