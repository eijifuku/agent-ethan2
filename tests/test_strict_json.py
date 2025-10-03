"""Tests for strict JSON validation helper (F2)."""

from __future__ import annotations

import pytest

from agent_ethan2.validation import JsonValidationError, validate_llm_json

SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
        "tags": {"type": "array", "minItems": 1, "items": {"type": "string"}},
    },
    "required": ["name", "age"],
    "additionalProperties": False,
}


def test_validate_llm_json_success() -> None:
    data = {"name": "Alice", "age": 30, "tags": ["engineer"]}
    parsed = validate_llm_json(data, SCHEMA)
    assert parsed["name"] == "Alice"


def test_validate_llm_json_missing_field() -> None:
    data = {"age": 30}
    with pytest.raises(JsonValidationError) as excinfo:
        validate_llm_json(data, SCHEMA)
    error = excinfo.value
    assert error.code == "ERR_LLM_JSON_PARSE"
    assert "required property" in error.message
    assert error.pointer == "/"
    assert error.expected.startswith("Field")
    assert error.suggestion.startswith("Include field")


def test_validate_llm_json_wrong_type() -> None:
    data = {"name": "Alice", "age": "thirty"}
    with pytest.raises(JsonValidationError) as excinfo:
        validate_llm_json(data, SCHEMA)
    error = excinfo.value
    assert error.pointer == "/age"
    assert error.expected
    assert error.actual == "str"


def test_validate_llm_json_parse_error() -> None:
    text = '{"name": "Alice", "age": 30,,}'
    with pytest.raises(JsonValidationError) as excinfo:
        validate_llm_json(text, SCHEMA)
    error = excinfo.value
    assert error.expected == "valid JSON"
    assert error.actual == "invalid JSON"
    assert error.suggestion
