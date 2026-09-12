"""LLM Provider abstraction — supports Claude and Bedrock."""

import asyncio
import json
import logging
import os
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import Any

logger = logging.getLogger(__name__)
executor = ThreadPoolExecutor(max_workers=2)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def create_message(
        self,
        model: str,
        max_tokens: int,
        system: str,
        tools: list[dict],
        messages: list[dict],
    ) -> Any:
        """Create a message using the LLM.

        Returns: Response object with .content attribute.
        """
        pass


class ClaudeProvider(LLMProvider):
    """Anthropic Claude provider."""

    def __init__(self, api_key: str):
        """Initialize Claude provider."""
        import anthropic

        self.client = anthropic.Anthropic(api_key=api_key)
        logger.info("Claude provider initialized")

    async def create_message(
        self,
        model: str,
        max_tokens: int,
        system: str,
        tools: list[dict],
        messages: list[dict],
    ) -> Any:
        """Create a message using Claude."""
        logger.info(f"Claude API call: model={model}, max_tokens={max_tokens}, tool_count={len(tools)}")

        response = self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            tools=tools,
            messages=messages,
        )

        return response


class BedrockProvider(LLMProvider):
    """AWS Bedrock provider."""

    def __init__(self, model_id: str, region: str = "us-east-1"):
        """Initialize Bedrock provider.

        Args:
            model_id: Bedrock model ID (e.g., anthropic.claude-opus-5-20250514-v1:0)
            region: AWS region
        """
        import boto3

        self.model_id = model_id
        self.region = region
        self.client = boto3.client("bedrock-runtime", region_name=region)
        logger.info(f"Bedrock provider initialized: model={model_id}, region={region}")

    async def create_message(
        self,
        model: str,
        max_tokens: int,
        system: str,
        tools: list[dict],
        messages: list[dict],
    ) -> Any:
        """Create a message using Bedrock Claude.

        Converts the Anthropic API format to Bedrock's converse API format.
        Runs boto3 call in thread pool for async compatibility.
        """
        logger.info(f"Bedrock API call: model={self.model_id}, max_tokens={max_tokens}, tool_count={len(tools)}")

        # Convert messages to Bedrock format
        bedrock_messages = self._convert_messages(messages)

        # Build tool definitions for Bedrock
        tool_config = self._build_tool_config(tools)

        # Run Bedrock API call in thread pool (boto3 is sync)
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            executor,
            self._call_bedrock,
            bedrock_messages,
            system,
            max_tokens,
            tool_config,
        )

        # Wrap response to match Anthropic API format
        return BedrockResponse(response)

    def _convert_messages(self, messages: list[dict]) -> list[dict]:
        """Convert messages to Bedrock format."""
        bedrock_messages = []
        for msg in messages:
            bedrock_messages.append(msg)
        return bedrock_messages

    def _build_tool_config(self, tools: list[dict]) -> dict:
        """Build tool definitions for Bedrock."""
        if not tools:
            return {}

        return {
            "tools": [
                {
                    "toolUseId": tool["name"],
                    "toolSpec": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "inputSchema": tool["input_schema"],
                    }
                }
                for tool in tools
            ]
        }

    def _call_bedrock(
        self,
        messages: list[dict],
        system: str,
        max_tokens: int,
        tool_config: dict,
    ) -> dict:
        """Sync wrapper for Bedrock API call (runs in thread pool)."""
        return self.client.converse(
            modelId=self.model_id,
            messages=messages,
            system=[{"text": system}],
            maxTokens=max_tokens,
            **(tool_config if tool_config else {}),
        )


class BedrockResponse:
    """Wrapper to make Bedrock response compatible with Anthropic API format."""

    def __init__(self, bedrock_response: dict):
        """Initialize with Bedrock response."""
        self.raw = bedrock_response
        self.content = self._convert_content(bedrock_response.get("output", {}).get("message", {}).get("content", []))

    def _convert_content(self, bedrock_content: list) -> list:
        """Convert Bedrock content blocks to Anthropic format."""
        converted = []

        for block in bedrock_content:
            if block.get("type") == "text":
                converted.append({"type": "text", "text": block.get("text", "")})
            elif block.get("type") == "tool_use":
                converted.append({
                    "type": "tool_use",
                    "id": block.get("toolUseId", ""),
                    "name": block.get("toolName", ""),
                    "input": block.get("toolInput", {}),
                })

        return converted


def get_llm_provider(provider_name: str = "claude") -> LLMProvider:
    """Factory function to get LLM provider based on configuration.

    Args:
        provider_name: "claude" or "bedrock"

    Returns:
        LLMProvider instance
    """
    if provider_name.lower() == "bedrock":
        model_id = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-opus-5-20250514-v1:0")
        region = os.getenv("AWS_REGION", "us-east-1")
        return BedrockProvider(model_id=model_id, region=region)
    else:
        # Default to Claude
        api_key = os.getenv("AI_API_KEY", "")
        return ClaudeProvider(api_key=api_key)
