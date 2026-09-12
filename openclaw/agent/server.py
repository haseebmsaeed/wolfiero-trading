"""OpenClaw Agent Server — LLM-based trading assistant with tool integration."""

import os
import json
import logging
from typing import Any
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import anthropic
import httpx

# Load configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

# Models from environment
AI_MODEL_MID = os.getenv("AI_MODEL_MID", "claude-opus-5")
AI_API_KEY = os.getenv("AI_API_KEY", "")
WOLFIERO_API_URL = os.getenv("WOLFIERO_API_URL", "http://wolfiero-api:8000")
WOLFIERO_API_KEY = os.getenv("WOLFIERO_API_KEY", "dev-key")

# Initialize FastAPI
app = FastAPI(
    title="OpenClaw Trading Agent",
    description="AI-powered swing trading assistant",
    version="1.0.0",
)

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=AI_API_KEY)

# HTTP client for tool calls
http_client = httpx.AsyncClient(
    base_url=WOLFIERO_API_URL,
    headers={"Authorization": f"Bearer {WOLFIERO_API_KEY}"},
    timeout=30.0,
)


class Message(BaseModel):
    """User message to the agent."""

    chat_id: str
    user_id: str
    text: str
    conversation_id: str = "default"


class AgentResponse(BaseModel):
    """Response from the agent."""

    reply: str
    tool_calls: list[dict] = []
    grounding_ok: bool = True


# Define tools for Claude to use
TOOLS = [
    {
        "name": "analyze_stock",
        "description": "Perform comprehensive technical analysis of a stock. Use this when the user asks about a specific stock (NVDA, AAPL, etc). Do NOT use this to find new ideas — that's for scan_market.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock ticker symbol (e.g., NVDA, SPY)",
                }
            },
            "required": ["symbol"],
        },
    },
]


async def call_tool(tool_name: str, tool_input: dict) -> dict:
    """Call a tool via the Wolfiero API."""
    logger.info(f"Calling tool: {tool_name} with input: {tool_input}")

    try:
        if tool_name == "analyze_stock":
            symbol = tool_input.get("symbol", "").upper()
            response = await http_client.post(
                "/api/stocks/analyze",
                params={"symbol": symbol},
            )
            response.raise_for_status()
            return response.json()
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    except httpx.HTTPError as e:
        logger.error(f"Tool call failed: {e}")
        return {"error": f"API error: {str(e)}"}


@app.post("/chat")
async def chat(message: Message) -> AgentResponse:
    """Handle a user message and return an agent response."""
    logger.info(f"Chat from {message.user_id}: {message.text}")

    # System prompt for grounding
    system_prompt = """You are an analytical assistant to a swing trader.
You have access to tools for technical analysis of stocks.

GROUNDING RULES:
- Every number in your response MUST come from a tool result in this conversation
- Do NOT make up prices, percentages, or any market data
- If a tool returns no data, say so clearly
- Do NOT predict future prices

Be direct, quantitative, and concise. When asked about a stock, analyze its technical setup.
When asked something outside your tool scope, politely decline."""

    messages = [{"role": "user", "content": message.text}]

    # Agentic loop
    max_iterations = 5
    tool_calls_made = []

    for iteration in range(max_iterations):
        logger.info(f"Agent iteration {iteration + 1}")

        response = client.messages.create(
            model=AI_MODEL_MID,
            max_tokens=2048,
            system=system_prompt,
            tools=TOOLS,
            messages=messages,
        )

        # Check for tool use
        tool_use_blocks = [block for block in response.content if block.type == "tool_use"]

        if not tool_use_blocks:
            # No more tool calls, extract text response
            text_blocks = [block for block in response.content if block.type == "text"]
            reply = "\n".join(block.text for block in text_blocks)
            logger.info(f"Agent final response: {reply[:200]}...")
            return AgentResponse(
                reply=reply,
                tool_calls=tool_calls_made,
            )

        # Process tool calls
        for tool_use in tool_use_blocks:
            logger.info(f"Tool use: {tool_use.name}")
            tool_calls_made.append(
                {
                    "name": tool_use.name,
                    "input": tool_use.input,
                }
            )

            # Call tool
            tool_result = await call_tool(tool_use.name, tool_use.input)

            # Add to messages for next iteration
            messages.append({"role": "assistant", "content": response.content})
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use.id,
                            "content": json.dumps(tool_result),
                        }
                    ],
                }
            )

    # Max iterations reached
    return AgentResponse(
        reply="Analysis took too many steps. Please try again.",
        tool_calls=tool_calls_made,
    )


@app.get("/health")
async def health() -> dict:
    """Health check."""
    return {
        "status": "ok",
        "service": "openclaw-agent",
        "model": AI_MODEL_MID,
    }


@app.get("/health/deep")
async def health_deep() -> dict:
    """Deep health check."""
    api_ok = False
    try:
        response = await http_client.get("/health")
        api_ok = response.status_code == 200
    except Exception as e:
        logger.warning(f"API health check failed: {e}")

    return {
        "status": "healthy" if api_ok else "degraded",
        "openclaw": "ok",
        "wolfiero_api": "ok" if api_ok else "unreachable",
        "model": AI_MODEL_MID,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001, log_level=LOG_LEVEL.lower())
