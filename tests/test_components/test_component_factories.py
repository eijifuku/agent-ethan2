"""Tests for built-in component factories."""

from __future__ import annotations

import sys
from typing import Any, Mapping

import pytest

from agent_ethan2.components.llm import (
    create_anthropic_messages_component,
    create_gemini_chat_component,
    create_openai_chat_component,
)
from agent_ethan2.components.tool import create_tool_passthrough_component
from agent_ethan2.graph.errors import GraphExecutionError
from agent_ethan2.ir import NormalizedComponent, NormalizedProvider
from agent_ethan2.providers.google import create_google_provider


@pytest.mark.asyncio
async def test_openai_chat_component_uses_provider_context() -> None:
    captured: dict[str, Any] = {}

    class DummyMessage:
        def __init__(self, content: str) -> None:
            self.content = content
            self.parsed = {"json": True}

    class DummyChoice:
        def __init__(self, content: str) -> None:
            self.message = DummyMessage(content)
            self.parsed = {"legacy": True}

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
    assert result["choices"][0]["parsed"] == {"json": True}
    assert result["choices"][0]["message"].parsed == {"json": True}
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


@pytest.mark.asyncio
async def test_gemini_chat_component_basic(monkeypatch: pytest.MonkeyPatch) -> None:
    import types

    captured: dict[str, Any] = {}

    class DummyUsage:
        prompt_token_count = 5
        candidates_token_count = 7
        total_token_count = 12

    class DummyResponse:
        def __init__(self) -> None:
            self.text = "gemini reply"
            self.usage_metadata = DummyUsage()

    class DummyGenerativeModel:
        def __init__(self, *, model_name: str, generation_config=None, safety_settings=None, system_instruction=None) -> None:
            captured["init"] = {
                "model_name": model_name,
                "generation_config": generation_config,
                "safety_settings": safety_settings,
                "system_instruction": system_instruction,
            }

        def generate_content(self, content: Any) -> Any:
            captured["content"] = content
            return DummyResponse()

    module = types.ModuleType("google.generativeai")

    def configure(api_key: str) -> None:
        captured["api_key"] = api_key

    module.configure = configure
    module.GenerativeModel = DummyGenerativeModel

    google_pkg = types.ModuleType("google")
    google_pkg.generativeai = module

    monkeypatch.setitem(sys.modules, "google", google_pkg)
    monkeypatch.setitem(sys.modules, "google.generativeai", module)

    provider = NormalizedProvider(id="google", type="google", config={"api_key": "key", "model": "gemini-pro"})
    provider_ctx = create_google_provider(provider)

    component = NormalizedComponent(
        id="gemini",
        type="gemini_chat",
        provider_id="google",
        tool_id=None,
        inputs={"prompt": "graph.inputs.prompt"},
        outputs={},
        config={"temperature": 0.1, "max_output_tokens": 64},
    )

    component_callable = create_gemini_chat_component(component, provider_ctx, None)
    result = await component_callable({}, {"prompt": "Hello"}, {})

    assert captured["api_key"] == "key"
    assert captured["init"]["model_name"] == "gemini-pro"
    assert captured["init"]["generation_config"]["temperature"] == 0.1
    assert captured["init"]["generation_config"]["max_output_tokens"] == 64
    assert captured["content"] == "Hello"
    assert result["choices"][0]["text"] == "gemini reply"
    assert result["usage"] == {
        "prompt_tokens": 5,
        "candidates_tokens": 7,
        "total_tokens": 12,
    }


@pytest.mark.asyncio
async def test_gemini_chat_component_formats_messages(monkeypatch: pytest.MonkeyPatch) -> None:
    import types

    class DummyResponse:
        def __init__(self) -> None:
            self.text = "ok"
            self.usage_metadata = None

    class DummyGenerativeModel:
        last_content: Any = None

        def __init__(self, **kwargs: Any) -> None:
            self.kwargs = kwargs

        def generate_content(self, content: Any) -> Any:
            DummyGenerativeModel.last_content = content
            return DummyResponse()

    module = types.ModuleType("google.generativeai")
    module.configure = lambda **_: None
    module.GenerativeModel = DummyGenerativeModel

    google_pkg = types.ModuleType("google")
    google_pkg.generativeai = module
    monkeypatch.setitem(sys.modules, "google", google_pkg)
    monkeypatch.setitem(sys.modules, "google.generativeai", module)

    provider = NormalizedProvider(id="google", type="google", config={"api_key": "key", "model": "gemini-pro"})
    provider_ctx = create_google_provider(provider)

    component = NormalizedComponent(
        id="gemini",
        type="gemini_chat",
        provider_id="google",
        tool_id=None,
        inputs={},
        outputs={},
        config={},
    )

    component_callable = create_gemini_chat_component(component, provider_ctx, None)
    messages = [
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Hi"},
    ]
    result = await component_callable({}, {"messages": messages}, {})

    assert DummyGenerativeModel.last_content == [
        {"role": "system", "parts": ["You are helpful."]},
        {"role": "user", "parts": ["Hi"]},
    ]
    assert result["choices"][0]["text"] == "ok"


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
