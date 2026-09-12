"""Telegram Bot Adapter for OpenClaw Agent.

Handles:
- Long-polling from Telegram API
- Chat ID allowlist enforcement
- Message chunking (4096 char limit)
- Markdown escaping
- Typing indicators
"""

import os
import asyncio
import logging
import re
from typing import Optional, Callable
import httpx

logger = logging.getLogger(__name__)

# Configuration from environment
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ALLOWED_CHAT_IDS = os.getenv("TELEGRAM_ALLOWED_CHAT_IDS", "")
TELEGRAM_MESSAGE_DELAY_SECONDS = 10  # "still working..." message after this

# Parse allowlist
ALLOWED_CHATS = set()
if TELEGRAM_ALLOWED_CHAT_IDS:
    try:
        ALLOWED_CHATS = set(int(cid.strip()) for cid in TELEGRAM_ALLOWED_CHAT_IDS.split(","))
        logger.info(f"Telegram allowlist: {ALLOWED_CHATS}")
    except ValueError:
        logger.error(f"Invalid TELEGRAM_ALLOWED_CHAT_IDS: {TELEGRAM_ALLOWED_CHAT_IDS}")


def escape_markdown(text: str) -> str:
    """Escape special Markdown characters for Telegram."""
    # Characters that need escaping in Telegram's MarkdownV2
    special_chars = r"_*[\]()~`>#+-=|{}.!"
    return "".join(f"\\{char}" if char in special_chars else char for char in text)


def chunk_message(text: str, max_length: int = 4096) -> list[str]:
    """Split message at paragraph boundaries, respecting max length."""
    if len(text) <= max_length:
        return [text]

    chunks = []
    paragraphs = text.split("\n\n")
    current_chunk = ""

    for para in paragraphs:
        # If a single paragraph is longer than max, we have to split it
        if len(para) > max_length:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            # Split the long paragraph on newlines
            lines = para.split("\n")
            for line in lines:
                if len(current_chunk) + len(line) + 1 > max_length:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = line
                else:
                    current_chunk += ("\n" if current_chunk else "") + line
        else:
            if len(current_chunk) + len(para) + 2 > max_length:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = para
            else:
                current_chunk += ("\n\n" if current_chunk else "") + para

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


class TelegramAdapter:
    """Telegram bot adapter for the agent."""

    def __init__(self, agent_chat_handler: Callable):
        """Initialize adapter.

        Args:
            agent_chat_handler: async function(chat_id, user_id, text) -> str
        """
        self.agent_chat = agent_chat_handler
        self.http_client = httpx.AsyncClient()
        self.base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
        self.offset = 0
        self.running = False

    async def start(self):
        """Start polling for messages."""
        self.running = True
        logger.info("Telegram adapter started")

        while self.running:
            try:
                await self.poll_once()
                await asyncio.sleep(0.5)  # Poll every 500ms
            except Exception as e:
                logger.error(f"Polling error: {e}")
                await asyncio.sleep(5)

    async def stop(self):
        """Stop polling."""
        self.running = False
        logger.info("Telegram adapter stopped")

    async def poll_once(self):
        """Poll for one batch of updates."""
        try:
            response = await self.http_client.post(
                f"{self.base_url}/getUpdates",
                json={"offset": self.offset, "timeout": 30},
                timeout=35.0,
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("ok"):
                logger.error(f"Telegram API error: {data}")
                return

            updates = data.get("result", [])
            for update in updates:
                await self.handle_update(update)
                self.offset = update["update_id"] + 1

        except Exception as e:
            logger.error(f"Poll error: {e}")

    async def handle_update(self, update: dict):
        """Handle a single Telegram update."""
        message = update.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        user_id = message.get("from", {}).get("id")
        text = message.get("text", "")

        if not text:
            return

        # Allowlist check
        if chat_id not in ALLOWED_CHATS:
            logger.warning(f"Rejected message from unauthorized chat {chat_id}")
            await self.send_message(
                chat_id,
                "I'm not configured to respond in this chat.",
            )
            return

        logger.info(f"Message from {user_id} (chat {chat_id}): {text}")

        # Handle commands
        if text.startswith("/"):
            await self.handle_command(chat_id, text)
            return

        # Send typing indicator
        await self.send_chat_action(chat_id, "typing")

        # Start "still working..." timer
        still_working_task = asyncio.create_task(
            self.send_still_working_after(chat_id, TELEGRAM_MESSAGE_DELAY_SECONDS)
        )

        try:
            # Call agent
            reply = await self.agent_chat(
                chat_id=str(chat_id),
                user_id=str(user_id),
                text=text,
            )

            # Cancel "still working" if it hasn't fired
            still_working_task.cancel()
            try:
                await still_working_task
            except asyncio.CancelledError:
                pass

            # Send response, chunked at 4096 chars
            chunks = chunk_message(reply)
            for chunk in chunks:
                await self.send_message(chat_id, chunk)
                await asyncio.sleep(0.5)  # Small delay between chunks

        except Exception as e:
            logger.error(f"Agent error: {e}")
            still_working_task.cancel()
            await self.send_message(
                chat_id,
                f"Error: {str(e)[:200]}",
            )

    async def handle_command(self, chat_id: int, text: str):
        """Handle special commands."""
        if text == "/start":
            await self.send_message(
                chat_id,
                "Welcome to Wolfiero Trading Agent. Send a stock symbol (NVDA, SPY, etc) to analyze.",
            )
        elif text == "/help":
            await self.send_message(
                chat_id,
                """Commands:
/analyze SYMBOL - Technical analysis
/status - System status
/help - This message""",
            )
        elif text.startswith("/status"):
            await self.send_message(
                chat_id,
                "✓ Agent online",
            )
        else:
            await self.send_message(
                chat_id,
                f"Unknown command: {text}",
            )

    async def send_message(self, chat_id: int, text: str):
        """Send a message to a chat."""
        try:
            response = await self.http_client.post(
                f"{self.base_url}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "MarkdownV2",
                },
                timeout=10.0,
            )
            response.raise_for_status()
            logger.debug(f"Message sent to {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    async def send_chat_action(self, chat_id: int, action: str = "typing"):
        """Send typing indicator."""
        try:
            await self.http_client.post(
                f"{self.base_url}/sendChatAction",
                json={"chat_id": chat_id, "action": action},
                timeout=5.0,
            )
        except Exception as e:
            logger.warning(f"Failed to send chat action: {e}")

    async def send_still_working_after(self, chat_id: int, delay: int):
        """Send 'still working' message after delay."""
        try:
            await asyncio.sleep(delay)
            await self.send_message(chat_id, "Still working on that…")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.warning(f"Still working message failed: {e}")
