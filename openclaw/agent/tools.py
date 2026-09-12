"""Tool definitions and API bridge for the agent.

Tools are Claude's interface to Wolfiero API. Descriptions must be precise:
- When to use this tool
- When NOT to use this tool
- Expected inputs and outputs
"""

import json
import logging
from datetime import date
from typing import Any, Optional
import httpx

logger = logging.getLogger(__name__)

# API configuration
WOLFIERO_API_URL = ""  # Set by server
WOLFIERO_API_KEY = ""  # Set by server
API_TIMEOUT_SECONDS = 30
RETRY_COUNT = 1


class ToolCallError(Exception):
    """Error calling a tool."""

    pass


async def call_api(endpoint: str, method: str = "POST", **kwargs) -> dict:
    """Call Wolfiero API with retries and error handling."""
    headers = {
        "Authorization": f"Bearer {WOLFIERO_API_KEY}",
        "Content-Type": "application/json",
    }

    url = f"{WOLFIERO_API_URL}{endpoint}"
    logger.debug(f"{method} {url}")

    async with httpx.AsyncClient(timeout=API_TIMEOUT_SECONDS, headers=headers) as client:
        for attempt in range(RETRY_COUNT + 1):
            try:
                if method == "GET":
                    response = await client.get(url, **kwargs)
                elif method == "POST":
                    response = await client.post(url, **kwargs)
                else:
                    raise ValueError(f"Unsupported method: {method}")

                # Errors from API
                if response.status_code >= 400:
                    error_data = response.json()
                    error_detail = error_data.get("error", {})
                    error_msg = (
                        error_detail.get("message")
                        or error_detail.get("detail")
                        or str(error_data)
                    )

                    # Don't retry 4xx (client error)
                    if response.status_code < 500:
                        raise ToolCallError(f"API error: {error_msg}")

                    # Retry on 5xx
                    if attempt < RETRY_COUNT:
                        logger.warning(f"API 5xx error, retrying: {error_msg}")
                        continue

                    raise ToolCallError(f"API error (after retry): {error_msg}")

                return response.json()

            except httpx.TimeoutException:
                if attempt < RETRY_COUNT:
                    logger.warning("API timeout, retrying...")
                    continue
                raise ToolCallError("API timeout (after retry)")
            except httpx.HTTPError as e:
                raise ToolCallError(f"API connection error: {str(e)}")

    raise ToolCallError("API unreachable")


async def analyze_stock(symbol: str) -> dict:
    """Comprehensive technical analysis of a stock.

    Use this for: analyzing a specific, known stock ticker
    Do NOT use for: finding new stock ideas (use scan_market instead)

    Returns technical analysis with trend, momentum, volatility, setup, support/resistance.
    """
    try:
        result = await call_api("/api/stocks/analyze", method="POST", params={"symbol": symbol.upper()})
        return result
    except ToolCallError as e:
        return {"error": str(e)}


async def get_stock_history(
    symbol: str,
    days: int = 90,
    interval: str = "1d",
) -> dict:
    """Get historical price data for a stock.

    Use this for: getting recent price data for analysis or comparison
    Do NOT use for: finding new ideas (the analyze_stock tool already includes history)

    Args:
        symbol: Stock ticker (e.g., NVDA, SPY)
        days: How many days of history to return (default 90)
        interval: Candle interval: 1d (daily), 1h (hourly), etc. (default 1d)

    Returns OHLCV bars with dates and prices.
    """
    try:
        result = await call_api(
            "/api/stocks/history",
            method="GET",
            params={"symbol": symbol.upper(), "days": days, "interval": interval},
        )
        return result
    except ToolCallError as e:
        return {"error": str(e)}


# Tool schema for Claude
TOOL_SCHEMAS = [
    {
        "name": "analyze_stock",
        "description": """Perform comprehensive technical analysis of ONE known stock.

Use this when:
- User asks about a specific stock (NVDA, SPY, AAPL, etc)
- You need trend, momentum, volatility, setup quality, support/resistance
- You want a complete snapshot of a stock right now

Do NOT use this for:
- Finding new ideas (use scan_market instead)
- Getting only historical prices (use get_stock_history)
- Screening a list of stocks (use scan_market)

Returns: trend direction/strength, momentum (RSI/MACD), volatility regime,
volume metrics, technical setup (UPTREND/DOWNTREND/RANGE), support/resistance levels, 52-week stats.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock ticker symbol (e.g., NVDA, SPY, AAPL). Will be uppercased.",
                }
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "get_stock_history",
        "description": """Get historical price data (OHLCV bars) for a stock.

Use this when:
- You need recent price history for comparison or analysis
- You want to see recent price action in detail

Do NOT use this for:
- General analysis (analyze_stock does this better and includes history)
- Finding new ideas (use scan_market)

Returns: array of OHLCV bars with dates, open/high/low/close, volume.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock ticker (e.g., NVDA)",
                },
                "days": {
                    "type": "integer",
                    "description": "Number of trading days of history (default 90)",
                    "default": 90,
                },
                "interval": {
                    "type": "string",
                    "description": "Candle interval: 1d (daily), 1h (hourly), 15m, 5m (default 1d)",
                    "default": "1d",
                },
            },
            "required": ["symbol"],
        },
    },
]


async def call_tool(tool_name: str, tool_input: dict) -> dict:
    """Route a tool call to the correct handler."""
    logger.info(f"Tool call: {tool_name} with {tool_input}")

    try:
        if tool_name == "analyze_stock":
            return await analyze_stock(**tool_input)
        elif tool_name == "get_stock_history":
            return await get_stock_history(**tool_input)
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    except Exception as e:
        logger.error(f"Tool error: {e}")
        return {"error": f"Tool error: {str(e)[:200]}"}
