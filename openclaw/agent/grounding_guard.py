"""Response Grounding Guard — validates that all numbers come from tool results.

Catches hallucinated prices and out-of-turn numbers by comparing response
numeric tokens against tool payloads from this conversation turn.
"""

import re
import json
import logging
from typing import Any
from decimal import Decimal

logger = logging.getLogger(__name__)

# Configuration
GROUNDING_GUARD_MODE = "log"  # or "block"
TOLERANCE_PCT = 2.0  # Allow 2% rounding difference


class GroundingViolation:
    """A number in the response that doesn't match tool data."""

    def __init__(self, number: str, context: str):
        self.number = number
        self.context = context


def extract_numbers(text: str) -> list[tuple[str, str]]:
    """Extract numeric tokens from text.

    Returns: list of (number_str, context) tuples.
    Context is the surrounding 20 characters.
    """
    # Match numbers: integers, decimals, percentages, ranges
    pattern = r"[\d.,]+(?:%)?|\$[\d.,]+|[\d.]+-[\d.]+%"
    matches = []

    for match in re.finditer(pattern, text):
        num_str = match.group()
        start = max(0, match.start() - 10)
        end = min(len(text), match.end() + 10)
        context = text[start:end]
        matches.append((num_str, context))

    return matches


def normalize_number(num_str: str) -> float | None:
    """Convert a number string to float, handling formats like $123.45, 1.5K, etc."""
    try:
        # Remove currency symbols and percent signs
        clean = num_str.replace("$", "").replace("%", "").replace(",", "")

        # Handle ranges (1.5-2.0)
        if "-" in clean and clean.count(".") > 1:
            parts = clean.split("-")
            return (float(parts[0]) + float(parts[1])) / 2

        return float(clean)
    except ValueError:
        return None


def extract_payload_numbers(payload: dict | list) -> set[float]:
    """Recursively extract all numbers from a tool result payload."""
    numbers = set()

    def traverse(obj):
        if isinstance(obj, dict):
            for value in obj.values():
                traverse(value)
        elif isinstance(obj, list):
            for item in obj:
                traverse(item)
        elif isinstance(obj, (int, float)):
            numbers.add(float(obj))
        elif isinstance(obj, Decimal):
            numbers.add(float(obj))
        elif isinstance(obj, str):
            # Try to extract numbers from string values
            for match in re.findall(r"[\d.]+", obj):
                try:
                    numbers.add(float(match))
                except ValueError:
                    pass

    traverse(payload)
    return numbers


def numbers_match(response_num: float, tool_nums: set[float], tolerance: float = TOLERANCE_PCT) -> bool:
    """Check if a response number matches a tool number within tolerance."""
    for tool_num in tool_nums:
        if tool_num == 0:
            if abs(response_num) < 0.01:
                return True
        else:
            pct_diff = abs(response_num - tool_num) / abs(tool_num) * 100
            if pct_diff <= tolerance:
                return True

    # Also allow derived numbers (e.g., percentages, ratios)
    # This is a simplified check; in production, you might validate arithmetic
    return False


def validate_grounding(
    response: str,
    tool_results: list[dict],
    mode: str = GROUNDING_GUARD_MODE,
) -> tuple[bool, list[GroundingViolation]]:
    """Validate that response numbers come from tool results.

    Returns: (is_grounded, violations_list)
    """
    # Extract all numbers from tool payloads
    tool_numbers = set()
    for result in tool_results:
        tool_numbers.update(extract_payload_numbers(result))

    # Extract numbers from response
    response_numbers = extract_numbers(response)

    # Check each response number
    violations = []
    for num_str, context in response_numbers:
        normalized = normalize_number(num_str)
        if normalized is None:
            continue

        if not numbers_match(normalized, tool_numbers):
            violations.append(GroundingViolation(num_str, context))

    if violations:
        logger.warning(
            f"Grounding violations detected: {len(violations)} number(s) don't match tool data"
        )
        for v in violations:
            logger.warning(f"  - {v.number} in context: '{v.context}'")

    return len(violations) == 0, violations


def maybe_append_caveat(response: str, violations: list[GroundingViolation]) -> str:
    """If mode is 'block', append a caveat about grounding issues."""
    if GROUNDING_GUARD_MODE != "block" or not violations:
        return response

    caveat = "\n\n⚠️ Note: I found some numbers that may not be from current data. Please verify with live data."
    return response + caveat
