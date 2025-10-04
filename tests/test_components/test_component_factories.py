"""Tests for built-in component factories."""

from __future__ import annotations

from typing import Any, Mapping

import pytest

from agent_ethan2.components.llm import (
    create_anthropic_messages_component,
    create_openai_chat_component,
)
from agent_ethan2.components.tool import create_tool_passthrough_component
from agent_ethan2.graph.errors import GraphExecutionError
from agent_ethan2.ir import NormalizedComponent


@pytest.mark.asyncio
async def test_openai_chat_component_uses_provider_context() -> None:
    captured: dict[str, Any] = {}

    class DummyMessage:
        def __init__(self, content: str) -> None:
            self.content = content

    class DummyChoice:
        def __init__(self, content: str) -> None:
            self.message = DummyMessage(content)

    class DummyUsage:
        def __init__(self) -> None:
            self.prompt_tokens = 10
            self.completion_tokens = 5

        def model_dump(self) -> Mapping[str, int]:
            return {
                "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
            }

    class DummyChatCompletions:
        def create(self, **kwargs: Any) -> Any:
            captured["kwargs"] = kwargs
            return type("Response", (), {
                "choices": [DummyChoice("hello world")],
                "usage": DummyUsage(),
            })()

    class DummyClient:
        def __init__(self) -> None:
            self.chat = type("Chat", (), {"completions": DummyChatCompletions()})()

    component = NormalizedComponent(
        id="llm",
        type="llm",
        provider_id="openai",
        tool_id=None,
        inputs={"prompt": "graph.inputs.prompt"},
        outputs={"text": "$.choices[0].text"},
        config={"temperature": 0.3, "max_output_tokens": 128},
    )
    provider_instance = {
        "client": DummyClient(),
        "model": "gpt-4o-mini",
    }

    component_callable = create_openai_chat_component(component, provider_instance, None)

    result = await component_callable({}, {"prompt": "Hi"}, {})

    assert captured["kwargs"]["model"] == "gpt-4o-mini"
    assert captured["kwargs"]["messages"] == [{"role": "user", "content": "Hi"}]
    assert captured["kwargs"]["temperature"] == pytest.approx(0.3)
    assert captured["kwargs"]["max_tokens"] == 128
    assert result["choices"][0]["text"] == "hello world"
    assert result["usage"] == {"prompt_tokens": 10, "completion_tokens": 5}


@pytest.mark.asyncio
async def test_openai_chat_component_accepts_pre_built_messages() -> None:
    class DummyResponse:
        def __init__(self) -> None:
            self.choices = [type("Choice", (), {"message": {"content": "ok"}})()]
            self.usage = None

    class DummyChat:
        def __init__(self) -> None:
            self.captured: dict[str, Any] = {}

        def create(self, **kwargs: Any) -> Any:
            self.captured = kwargs
            return DummyResponse()

    client = type("Client", (), {"chat": type("Chat", (), {"completions": DummyChat()})()})()
    component = NormalizedComponent(
        id="llm",
        type="llm",
        provider_id="openai",
        tool_id=None,
        inputs={},
        outputs={},
        config={},
    )
    provider_instance = {"client": client, "model": "gpt"}

    component_callable = create_openai_chat_component(component, provider_instance, None)
    messages = [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}]
    result = await component_callable({}, {"messages": messages}, {})

    assert client.chat.completions.captured["messages"] == messages
    assert result["choices"][0]["text"] == "ok"


@pytest.mark.asyncio
async def test_anthropic_messages_component_basic(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    class DummyResponse:
        def __init__(self) -> None:
            self.content = [type("Block", (), {"text": "anthropic"})()]
            self.usage = type("Usage", (), {"input_tokens": 5, "output_tokens": 3})()

    class DummyMessages:
        def create(self, **kwargs: Any) -> Any:
            captured["kwargs"] = kwargs
            return DummyResponse()

    class DummyClient:
        def __init__(self) -> None:
            self.messages = DummyMessages()

    component = NormalizedComponent(
        id="anthropic",
        type="anthropic_messages",
        provider_id="anthropic",
        tool_id=None,
        inputs={"prompt": "graph.inputs.prompt"},
        outputs={},
        config={"max_tokens": 256, "system_prompt": "be nice"},
    )
    provider_instance = {"client": DummyClient(), "model": "claude"}

    component_callable = create_anthropic_messages_component(component, provider_instance, None)
    result = await component_callable({}, {"prompt": "hello"}, {})

    assert captured["kwargs"]["model"] == "claude"
    assert captured["kwargs"]["system"] == "be nice"
    assert result["choices"][0]["text"] == "anthropic"


def test_tool_passthrough_component_returns_tool() -> None:
    async def tool(state: Mapping[str, Any], inputs: Mapping[str, Any], ctx: Mapping[str, Any]) -> Mapping[str, Any]:
        return {"echo": inputs}

    component = NormalizedComponent(
        id="tool",
        type="tool",
        provider_id=None,
        tool_id="calc",
        inputs={},
        outputs={},
        config={},
    )

    component_callable = create_tool_passthrough_component(component, None, tool)
    assert component_callable is tool


def test_tool_passthrough_component_requires_callable() -> None:
    component = NormalizedComponent(
        id="tool",
        type="tool",
        provider_id=None,
        tool_id="calc",
        inputs={},
        outputs={},
        config={},
    )

    with pytest.raises(GraphExecutionError):
        create_tool_passthrough_component(component, None, object())
