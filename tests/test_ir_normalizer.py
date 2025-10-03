"""Tests for IR normalization (A2)."""

from __future__ import annotations

import pytest

from agent_ethan2.ir import IRNormalizationError, normalize_document


def _base_document() -> dict:
    return {
        "meta": {"version": 2, "name": "Sample"},
        "runtime": {"engine": "lc.lcel", "defaults": {"provider": "openai"}},
        "providers": [
            {"id": "openai", "type": "openai"},
        ],
        "components": [
            {
                "id": "call_model",
                "type": "llm",
                "inputs": {"prompt": "graph.inputs.user"},
                "outputs": {"text": "$.choices[0].text"},
            }
        ],
        "graph": {
            "entry": "start",
            "nodes": [
                {
                    "id": "start",
                    "type": "component",
                    "component": "call_model",
                    "next": "end",
                },
                {
                    "id": "end",
                    "type": "terminal",
                },
            ],
            "outputs": [
                {"key": "final", "node": "start", "output": "text"},
            ],
        },
    }


def test_normalize_document_success_assigns_default_provider() -> None:
    document = _base_document()

    result = normalize_document(document)

    component = result.ir.components["call_model"]
    assert component.provider_id == "openai"
    assert result.ir.graph.entry_id == "start"
    assert not result.warnings


def test_normalize_document_warns_for_unreachable_nodes() -> None:
    document = _base_document()
    document["graph"]["nodes"].append({"id": "unused", "type": "terminal"})

    result = normalize_document(document)

    warning_codes = {warning.code for warning in result.warnings}
    assert "WARN_GRAPH_NODE_UNREACHABLE" in warning_codes


def test_normalize_document_missing_entry_raises() -> None:
    document = _base_document()
    document["graph"]["entry"] = "missing"

    with pytest.raises(IRNormalizationError) as excinfo:
        normalize_document(document)

    assert excinfo.value.code == "ERR_GRAPH_ENTRY_NOT_FOUND"


def test_normalize_document_invalid_edge_raises() -> None:
    document = _base_document()
    document["graph"]["nodes"][0]["next"] = "missing"

    with pytest.raises(IRNormalizationError) as excinfo:
        normalize_document(document)

    assert excinfo.value.code == "ERR_EDGE_ENDPOINT_INVALID"


def test_component_missing_inputs_outputs_warns() -> None:
    document = _base_document()
    document["components"][0].pop("inputs")
    document["components"][0].pop("outputs")

    result = normalize_document(document)

    warning_codes = {warning.code for warning in result.warnings}
    assert "WARN_V1_COMPONENT_INPUTS_OPTIONAL" in warning_codes
    assert "WARN_V1_COMPONENT_OUTPUTS_OPTIONAL" in warning_codes


def test_legacy_error_policy_warning() -> None:
    document = _base_document()
    document.setdefault("policies", {})["error_policy"] = {"strategy": "retry"}

    result = normalize_document(document)

    warning_codes = {warning.code for warning in result.warnings}
    assert "WARN_V1_ERROR_POLICY" in warning_codes
