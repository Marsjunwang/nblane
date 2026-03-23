"""Shared JSON extraction helpers (LLM replies, fenced blocks)."""

from __future__ import annotations

import json
import re


def extract_json_object(text: str) -> dict | None:
    """Parse a JSON object from model output; tolerate fences."""
    raw = text.strip()
    fence = re.search(
        r"```(?:json)?\s*([\s\S]*?)```", raw, re.IGNORECASE
    )
    if fence:
        raw = fence.group(1).strip()
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        pass
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(raw[start : end + 1])
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None
