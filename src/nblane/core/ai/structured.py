"""Structured JSON extraction and lightweight schema validation."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class StructuredValidation:
    """Result for parsing and validating model JSON."""

    ok: bool
    data: dict[str, Any] | list[Any] | None = None
    error: str = ""


def extract_json_value(text: str) -> dict[str, Any] | list[Any] | None:
    """Parse a JSON object or array from model output.

    The parser accepts fenced JSON and common prose-wrapped responses.
    """

    raw = str(text or "").strip()
    fence = re.search(
        r"```(?:json)?\s*([\s\S]*?)```",
        raw,
        re.IGNORECASE,
    )
    if fence:
        raw = fence.group(1).strip()
    parsed = _loads_structured(raw)
    if parsed is not None:
        return parsed
    for opener, closer in (("{", "}"), ("[", "]")):
        start = raw.find(opener)
        end = raw.rfind(closer)
        if start < 0 or end <= start:
            continue
        parsed = _loads_structured(raw[start : end + 1])
        if parsed is not None:
            return parsed
    return None


def validate_json_response(
    raw: str,
    schema: dict[str, Any] | None = None,
) -> StructuredValidation:
    """Extract JSON and validate it against the supported schema subset."""

    data = extract_json_value(raw)
    if data is None:
        return StructuredValidation(
            ok=False,
            error="validation_error: response did not contain a JSON object or array",
        )
    error = validate_schema(data, schema or {})
    if error:
        return StructuredValidation(
            ok=False,
            data=data,
            error=f"validation_error: {error}",
        )
    return StructuredValidation(ok=True, data=data)


def validate_schema(data: Any, schema: dict[str, Any]) -> str:
    """Validate data against a small JSON-schema-like subset.

    Supported keywords are ``type``, ``required``, ``properties``, ``items``,
    ``enum`` and ``minItems``. This keeps runtime dependencies light while
    giving business code typed failures instead of raw text parsing.
    """

    if not schema:
        return ""
    return _validate_node(data, schema, path="$")


def schema_for_keys(
    required: list[str],
    *,
    properties: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Convenience helper for object schemas used by action specs."""

    return {
        "type": "object",
        "required": list(required),
        "properties": properties or {},
    }


def _loads_structured(raw: str) -> dict[str, Any] | list[Any] | None:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, (dict, list)) else None


def _validate_node(data: Any, schema: dict[str, Any], *, path: str) -> str:
    expected_type = schema.get("type")
    if expected_type:
        allowed = (
            [expected_type]
            if isinstance(expected_type, str)
            else list(expected_type)
            if isinstance(expected_type, list)
            else []
        )
        if allowed and not any(_matches_type(data, item) for item in allowed):
            return f"{path} expected {allowed[0]}, got {type(data).__name__}"

    enum = schema.get("enum")
    if isinstance(enum, list) and data not in enum:
        return f"{path} expected one of {enum!r}"

    if isinstance(data, dict):
        required = schema.get("required") or []
        if isinstance(required, list):
            for key in required:
                if not isinstance(key, str):
                    continue
                if key not in data:
                    return f"{path}.{key} is required"
        properties = schema.get("properties") or {}
        if isinstance(properties, dict):
            for key, child_schema in properties.items():
                if key not in data or not isinstance(child_schema, dict):
                    continue
                error = _validate_node(
                    data[key],
                    child_schema,
                    path=f"{path}.{key}",
                )
                if error:
                    return error

    if isinstance(data, list):
        min_items = schema.get("minItems")
        if isinstance(min_items, int) and len(data) < min_items:
            return f"{path} expected at least {min_items} item(s)"
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(data):
                error = _validate_node(
                    item,
                    item_schema,
                    path=f"{path}[{index}]",
                )
                if error:
                    return error
    return ""


def _matches_type(data: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(data, dict)
    if expected == "array":
        return isinstance(data, list)
    if expected == "string":
        return isinstance(data, str)
    if expected == "boolean":
        return isinstance(data, bool)
    if expected == "integer":
        return isinstance(data, int) and not isinstance(data, bool)
    if expected == "number":
        return isinstance(data, (int, float)) and not isinstance(data, bool)
    if expected == "null":
        return data is None
    return True


__all__ = [
    "StructuredValidation",
    "extract_json_value",
    "schema_for_keys",
    "validate_json_response",
    "validate_schema",
]
