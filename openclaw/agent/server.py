"""OpenClaw Agent Server — LLM-based trading assistant with tool integration."""

import os
import json
import logging
import asyncio
from typing import Any
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import httpx

from .telegram_adapter import TelegramAdapter
from . import tools
from .grounding_guard import validate_grounding, maybe_append_caveat
from .llm_provider import get_llm_provider

# Load configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

# Configuration from environment
AI_PROVIDER = os.getenv("AI_PROVIDER", "claude").lower()
AI_MODEL = os.getenv("AI_MODEL", "claude-opus-5")
AI_API_KEY = os.getenv("AI_API_KEY", "")
WOLFIERO_API_URL = os.getenv("WOLFIERO_API_URL", "http://wolfiero-api:8000")
WOLFIERO_API_KEY = os.getenv("WOLFIERO_API_KEY", "prod-key")

# Initialize FastAPI
app = FastAPI(
    title="OpenClaw Trading Agent",
    description="AI-powered swing trading assistant",
    version="1.0.0",
)

# Global state
telegram_adapter = None
telegram_task = None
SYSTEM_PROMPT = None
PROMPT_VERSION = "v1"
GROUNDING_VIOLATIONS_TODAY = 0
GROUNDING_GUARD_MODE = os.getenv("GROUNDING_GUARD_MODE", "log")  # log or block
llm_provider = None


def load_system_prompt():
    """Load system prompt from file."""
    global SYSTEM_PROMPT
    prompt_file = "/app/prompts/system.v1.md"
    try:
        with open(prompt_file, "r") as f:
            SYSTEM_PROMPT = f.read()
        logger.info(f"Loaded system prompt v1 from {prompt_file}")
    except FileNotFoundError:
        logger.warning(f"System prompt not found at {prompt_file}, using fallback")
        SYSTEM_PROMPT = """You are an analytical assistant to a swing trader.
You have access to tools for technical analysis of stocks.

GROUNDING RULES:
- Every number in your response MUST come from a tool result in this conversation
- Do NOT make up prices, percentages, or any market data
- If a tool returns no data, say so clearly
- Do NOT predict future prices

Be direct, quantitative, and concise."""


def init_llm_provider():
    """Initialize LLM provider (Claude or Bedrock)."""
    global llm_provider
    llm_provider = get_llm_provider(AI_PROVIDER)
    logger.info(f"LLM provider initialized: {AI_PROVIDER}")

# Initialize tools module with API config
tools.WOLFIERO_API_URL = WOLFIERO_API_URL
tools.WOLFIERO_API_KEY = WOLFIERO_API_KEY

# HTTP client for health checks
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
    prompt_version: str = PROMPT_VERSION  # For tracking regressions


# Use tools from tools module
TOOLS = tools.TOOL_SCHEMAS


async def call_tool(tool_name: str, tool_input: dict) -> dict:
    """Call a tool via the Wolfiero API."""
    return await tools.call_tool(tool_name, tool_input)


@app.post("/chat")
async def chat(message: Message) -> AgentResponse:
    """Handle a user message and return an agent response."""
    logger.info(f"Chat from {message.user_id}: {message.text}")

    if not SYSTEM_PROMPT:
        load_system_prompt()

    messages = [{"role": "user", "content": message.text}]

    # Agentic loop
    max_iterations = 5
    tool_calls_made = []
    tool_results_collected = []  # For grounding guard validation

    for iteration in range(max_iterations):
        logger.info(f"Agent iteration {iteration + 1}")

        response = await llm_provider.create_message(
            model=AI_MODEL,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
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

            # Validate grounding
            is_grounded, violations = validate_grounding(reply, tool_results_collected, GROUNDING_GUARD_MODE)
            if not is_grounded:
                global GROUNDING_VIOLATIONS_TODAY
                GROUNDING_VIOLATIONS_TODAY += 1
                reply = maybe_append_caveat(reply, violations)

            return AgentResponse(
                reply=reply,
                tool_calls=tool_calls_made,
                grounding_ok=is_grounded,
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
            tool_results_collected.append(tool_result)  # For grounding validation

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
        "provider": AI_PROVIDER,
        "model": AI_MODEL,
    }


@app.on_event("startup")
async def startup():
    """Initialize on app startup."""
    global telegram_adapter, telegram_task

    # Initialize LLM provider
    init_llm_provider()

    # Load system prompt
    load_system_prompt()
    logger.info(f"Using prompt version: {PROMPT_VERSION}")
    logger.info(f"Using AI provider: {AI_PROVIDER}, model: {AI_MODEL}")

    if not os.getenv("TELEGRAM_BOT_TOKEN"):
        logger.warning("TELEGRAM_BOT_TOKEN not set, Telegram bot disabled")
        return

    logger.info("Starting Telegram bot adapter...")
    telegram_adapter = TelegramAdapter(agent_chat_handler=chat_internal)
    telegram_task = asyncio.create_task(telegram_adapter.start())
    logger.info("Telegram bot started")


@app.on_event("shutdown")
async def shutdown():
    """Stop Telegram polling on app shutdown."""
    global telegram_adapter, telegram_task

    if telegram_adapter:
        await telegram_adapter.stop()
        if telegram_task:
            await telegram_task


async def chat_internal(chat_id: str, user_id: str, text: str) -> str:
    """Internal chat handler (used by Telegram adapter)."""
    response = await chat(
        Message(
            chat_id=chat_id,
            user_id=user_id,
            text=text,
            conversation_id=f"tg-{chat_id}",
        )
    )
    return response.reply


@app.get("/health/deep")
async def health_deep() -> dict:
    """Deep health check."""
    global telegram_adapter, telegram_task

    api_ok = False
    try:
        response = await http_client.get("/health")
        api_ok = response.status_code == 200
    except Exception as e:
        logger.warning(f"API health check failed: {e}")

    telegram_ok = False
    if telegram_adapter:
        telegram_ok = telegram_adapter.running and (
            telegram_task is None or not telegram_task.done()
        )

    return {
        "status": "healthy" if (api_ok and (not telegram_adapter or telegram_ok)) else "degraded",
        "openclaw": "ok",
        "wolfiero_api": "ok" if api_ok else "unreachable",
        "telegram": "ok" if telegram_ok else "disabled" if not telegram_adapter else "offline",
        "provider": AI_PROVIDER,
        "model": AI_MODEL,
        "grounding": {
            "mode": GROUNDING_GUARD_MODE,
            "violations_today": GROUNDING_VIOLATIONS_TODAY,
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001, log_level=LOG_LEVEL.lower())
