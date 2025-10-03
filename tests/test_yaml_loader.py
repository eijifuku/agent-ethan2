"""Tests for the YAML v2 loader."""

from __future__ import annotations

import textwrap

import pytest

from agent_ethan2.loader import ValidationIssue, YamlLoaderV2, YamlValidationError


@pytest.fixture()
def loader() -> YamlLoaderV2:
    return YamlLoaderV2()


def test_valid_yaml_round_trip(loader: YamlLoaderV2) -> None:
    yaml_text = textwrap.dedent(
        """\
        meta:
          version: 2
          name: Sample Agent
        runtime:
          engine: lc.lcel
          graph_name: sample
        providers:
          - id: openai-gpt4
            type: openai
            config:
              model: gpt-4
        tools:
          - id: search
            type: rest
            provider: openai-gpt4
            config:
              endpoint: https://example.com/search
        components:
          - id: call_model
            type: llm
            provider: openai-gpt4
            inputs:
              prompt: graph.inputs.user_query
            outputs:
              text: $.text
        graph:
          entry: start
          nodes:
            - id: start
              type: component
              component: call_model
              next: end
            - id: end
              type: terminal
          outputs:
            - key: final_response
              node: start
              output: text
        policies:
          retry:
            default:
              max_attempts: 2
        """
    )

    document = loader.loads(yaml_text)

    assert document["meta"]["version"] == 2
    assert document["runtime"]["engine"] == "lc.lcel"
    assert document["graph"]["entry"] == "start"
    assert len(document["graph"]["nodes"]) == 2


def test_duplicate_provider_id_raises(loader: YamlLoaderV2) -> None:
    yaml_text = textwrap.dedent(
        """\
        meta:
          version: 2
        runtime:
          engine: lc.lcel
        providers:
          - id: openai
            type: openai
          - id: openai
            type: anthropic
        graph:
          entry: start
          nodes:
            - id: start
              type: component
              component: call_model
        components:
          - id: call_model
            type: llm
        """
    )

    with pytest.raises(YamlValidationError) as excinfo:
        loader.loads(yaml_text)

    issue: ValidationIssue = excinfo.value.issue
    assert issue.code == "ERR_PROVIDER_DUP"
    assert issue.pointer == "/providers/1/id"
    assert issue.line == 8


def test_runtime_engine_unsupported(loader: YamlLoaderV2) -> None:
    yaml_text = textwrap.dedent(
        """\
        meta:
          version: 2
        runtime:
          engine: unsupported-engine
        providers:
          - id: openai
            type: openai
        graph:
          entry: start
          nodes:
            - id: start
              type: component
              component: call_model
        components:
          - id: call_model
            type: llm
        """
    )

    with pytest.raises(YamlValidationError) as excinfo:
        loader.loads(yaml_text)

    issue = excinfo.value.issue
    assert issue.code == "ERR_RUNTIME_ENGINE_UNSUPPORTED"
    assert issue.pointer == "/runtime/engine"
    assert issue.line == 4


def test_output_key_collision(loader: YamlLoaderV2) -> None:
    yaml_text = textwrap.dedent(
        """\
        meta:
          version: 2
        runtime:
          engine: lc.lcel
        providers:
          - id: openai
            type: openai
        graph:
          entry: start
          nodes:
            - id: start
              type: component
              component: call_model
          outputs:
            - key: final
              node: start
              output: text
            - key: final
              node: start
              output: text
        components:
          - id: call_model
            type: llm
        """
    )

    with pytest.raises(YamlValidationError) as excinfo:
        loader.loads(yaml_text)

    issue = excinfo.value.issue
    assert issue.code == "ERR_OUTPUT_KEY_COLLISION"
    assert issue.pointer == "/graph/outputs/1/key"
    assert issue.line == 18


def test_meta_version_unsupported(loader: YamlLoaderV2) -> None:
    yaml_text = textwrap.dedent(
        """\
        meta:
          version: 1
        runtime:
          engine: lc.lcel
        providers:
          - id: openai
            type: openai
        graph:
          entry: start
          nodes:
            - id: start
              type: component
              component: call_model
        components:
          - id: call_model
            type: llm
        """
    )

    with pytest.raises(YamlValidationError) as excinfo:
        loader.loads(yaml_text)

    issue = excinfo.value.issue
    assert issue.code == "ERR_META_VERSION_UNSUPPORTED"
    assert issue.pointer == "/meta/version"
    assert issue.line == 2
