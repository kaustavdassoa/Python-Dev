"""
Shared Utilities — Resume Optimizer Pipeline

Canonical implementations of helper functions used across multiple agents.
All agents should import from here instead of defining their own copies.
"""

import json
import re
import logging

logger = logging.getLogger("ResumeOptimizer")


def get_dict_from_state(val) -> dict:
    """Extract a dict from a raw state value.

    State values written by LlmAgents may arrive as:
      - A plain ``dict`` (already parsed by ADK)
      - A raw JSON ``str``
      - A markdown-wrapped JSON ``str`` (```json ... ```)

    This function normalises all three representations into a ``dict``.

    Args:
        val: The raw value read from ``state[key]``.

    Returns:
        The parsed ``dict``, or ``{}`` if parsing fails.
    """
    if isinstance(val, dict):
        return val

    if isinstance(val, str):
        # Strategy 1: markdown code-block extraction (greedy to capture nested JSON)
        match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', val, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group(1))
                logger.debug("get_dict_from_state: extracted from markdown block (%d chars)", len(match.group(1)))
                return result
            except json.JSONDecodeError:
                pass

        # Strategy 2: outermost brace matching
        first_brace = val.find('{')
        last_brace = val.rfind('}')
        if first_brace != -1 and last_brace > first_brace:
            candidate = val[first_brace:last_brace + 1]
            try:
                result = json.loads(candidate)
                logger.debug("get_dict_from_state: extracted via brace matching (%d chars)", len(candidate))
                return result
            except json.JSONDecodeError:
                pass

        # Strategy 3: raw string parse
        try:
            return json.loads(val.strip())
        except json.JSONDecodeError:
            pass

        logger.warning(
            "get_dict_from_state: all strategies failed (input length=%d, preview=%.100s)",
            len(val), val[:100],
        )

    return {}
