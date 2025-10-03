"""Strict JSON/struct validation for LLM outputs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from jsonschema import Draft202012Validator, ValidationError


@dataclass
class JsonValidationError(ValueError):
    """Raised when JSON parsing or validation fails."""

    code: str
    message: str
    pointer: str
    expected: str
    actual: str
    suggestion: str | None

    def __str__(self) -> str:  # pragma: no cover - ValueError already uses args
        base = f"[{self.code}] {self.message}"
        if self.suggestion:
            return f"{base} (suggestion: {self.suggestion})"
        return base


def validate_llm_json(data: Any, schema: Mapping[str, Any]) -> Any:
    """Validate an LLM JSON/struct response against a schema.

    Parameters
    ----------
    data:
        JSON string or already-parsed object.
    schema:
        JSON Schema describing the expected structure.

    Returns
    -------
    Any
        Parsed data if validation succeeds.

    Raises
    ------
    JsonValidationError
        When parsing or validation fails.
    """

    parsed = _parse_json(data)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(parsed), key=lambda err: err.path)
    if not errors:
        return parsed
    error = errors[0]
    raise _from_schema_error(error)


def _parse_json(data: Any) -> Any:
    if isinstance(data, str):
        try:
            return json.loads(data)
        except json.JSONDecodeError as exc:  # pragma: no cover - simple mapping
            pointer = f"line {exc.lineno}, column {exc.colno}"
            raise JsonValidationError(
                code="ERR_LLM_JSON_PARSE",
                message=f"Malformed JSON near {pointer}: {exc.msg}",
                pointer="/",
                expected="valid JSON",
                actual="invalid JSON",
                suggestion="Verify quotes and trailing commas",
            ) from exc
    return data


def _from_schema_error(error: ValidationError) -> JsonValidationError:
    path = "/" + "/".join(str(part) for part in error.absolute_path)
    expected, actual, suggestion = _describe_validator(error)
    message = error.message
    return JsonValidationError(
        code="ERR_LLM_JSON_PARSE",
        message=message,
        pointer=path or "/",
        expected=expected,
        actual=actual,
        suggestion=suggestion,
    )


def _describe_validator(error: ValidationError) -> tuple[str, str, str | None]:
    validator = error.validator
    if validator == "type":
        expected = " / ".join(error.validator_value) if isinstance(error.validator_value, Sequence) else str(error.validator_value)
        actual = type(error.instance).__name__
        return expected, actual, f"Cast value to {expected}"
    if validator == "required":
        missing = error.message.split("'" )[1] if "'" in error.message else str(error.validator_value)
        expected = f"Field '{missing}'"
        actual = "missing"
        return expected, actual, f"Include field '{missing}'"
    if validator == "enum":
        expected = f"one of {error.validator_value}"
        actual = repr(error.instance)
        return expected, actual, "Use a supported value"
    if validator == "minItems":
        expected = f">= {error.validator_value} items"
        actual = f"{len(error.instance)} items"
        return expected, actual, "Append more items"
    return str(error.validator), type(error.instance).__name__, None
