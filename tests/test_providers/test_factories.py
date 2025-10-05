"""Unit tests for built-in provider factories."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable, Dict

import pytest

from agent_ethan2.agent import AgentEthan
from agent_ethan2.graph.errors import GraphExecutionError
from agent_ethan2.ir import NormalizedProvider
from agent_ethan2.providers.anthropic import create_anthropic_provider
from agent_ethan2.providers.google import create_google_provider
from agent_ethan2.providers.openai import create_openai_provider


def _install_stub(
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
    attr_name: str,
    factory: Callable[..., Any],
) -> None:
    """Install a stub factory class/function on a target module."""

    if module_name in sys.modules:
        monkeypatch.setattr(f"{module_name}.{attr_name}", factory, raising=False)
    else:
        import types

        module = types.ModuleType(module_name)
        setattr(module, attr_name, factory)
        monkeypatch.setitem(sys.modules, module_name, module)


def _make_provider(provider_type: str, config: Dict[str, Any]) -> NormalizedProvider:
    return NormalizedProvider(id=f"{provider_type}-provider", type=provider_type, config=config)


def test_openai_factory_uses_provider_config(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, dict[str, Any]] = {}

    class DummyOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            captured["kwargs"] = kwargs

    _install_stub(monkeypatch, "openai", "OpenAI", DummyOpenAI)
    provider = _make_provider(
        "openai",
        {
            "api_key": "test-key",
            "model": "gpt-4o-mini",
            "base_url": "https://example.invalid/v1",
            "organization": "org-123",
            "timeout": "30",
            "max_retries": "2",
            "temperature": "0.5",
        },
    )

    context = create_openai_provider(provider)

    assert captured["kwargs"] == {
        "api_key": "test-key",
        "base_url": "https://example.invalid/v1",
        "organization": "org-123",
        "timeout": 30.0,
        "max_retries": 2,
    }
    assert context["model"] == "gpt-4o-mini"
    assert context["base_url"] == "https://example.invalid/v1"
    assert context["organization"] == "org-123"
    assert context["timeout"] == 30.0
    assert context["max_retries"] == 2
    assert context["temperature"] == 0.5
    assert context["config"] is not provider.config
    assert dict(context["config"]) == provider.config


def test_openai_factory_reads_environment_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, dict[str, Any]] = {}

    class DummyOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            captured["kwargs"] = kwargs

    _install_stub(monkeypatch, "openai", "OpenAI", DummyOpenAI)
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    provider = _make_provider("openai", {"model": "gpt-4o"})

    context = create_openai_provider(provider)

    assert captured["kwargs"]["api_key"] == "env-key"
    assert context["model"] == "gpt-4o"


def test_openai_factory_supports_base_url_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, dict[str, Any]] = {}

    class DummyOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            captured["kwargs"] = kwargs

    _install_stub(monkeypatch, "openai", "OpenAI", DummyOpenAI)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    provider = _make_provider(
        "openai",
        {
            "base_url": "http://localhost:11434/v1",
            "model": "local-model",
        },
    )

    context = create_openai_provider(provider)

    assert captured["kwargs"] == {"base_url": "http://localhost:11434/v1"}
    assert context["base_url"] == "http://localhost:11434/v1"
    assert context["model"] == "local-model"
    assert context["temperature"] is None


def test_openai_factory_validates_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_stub(monkeypatch, "openai", "OpenAI", lambda **_: None)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    provider = _make_provider("openai", {"model": "gpt-4o-mini"})

    with pytest.raises(GraphExecutionError) as exc_info:
        create_openai_provider(provider)

    assert exc_info.value.code == "ERR_PROVIDER_OPENAI"


def test_openai_factory_validates_numeric_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_stub(monkeypatch, "openai", "OpenAI", lambda **_: None)
    provider = _make_provider(
        "openai",
        {
            "api_key": "test-key",
            "timeout": "not-a-number",
        },
    )

    with pytest.raises(GraphExecutionError) as exc_info:
        create_openai_provider(provider)

    assert exc_info.value.code == "ERR_PROVIDER_OPENAI"


def test_anthropic_factory_uses_provider_config(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, dict[str, Any]] = {}

    class DummyAnthropic:
        def __init__(self, **kwargs: Any) -> None:
            captured["kwargs"] = kwargs

    _install_stub(monkeypatch, "anthropic", "Anthropic", DummyAnthropic)
    provider = _make_provider(
        "anthropic",
        {
            "api_key": "anthropic-key",
            "model": "claude-3-sonnet",
            "max_tokens": "2048",
            "temperature": "0.2",
        },
    )

    context = create_anthropic_provider(provider)

    assert captured["kwargs"] == {"api_key": "anthropic-key"}
    assert context["model"] == "claude-3-sonnet"
    assert context["max_tokens"] == 2048
    assert context["temperature"] == 0.2
    assert dict(context["config"]) == provider.config


def test_anthropic_factory_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, dict[str, Any]] = {}

    class DummyAnthropic:
        def __init__(self, **kwargs: Any) -> None:
            captured["kwargs"] = kwargs

    _install_stub(monkeypatch, "anthropic", "Anthropic", DummyAnthropic)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key")
    provider = _make_provider("anthropic", {"model": "claude"})

    context = create_anthropic_provider(provider)

    assert captured["kwargs"] == {"api_key": "env-key"}
    assert context["model"] == "claude"


def test_anthropic_factory_missing_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_stub(monkeypatch, "anthropic", "Anthropic", lambda **_: None)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    provider = _make_provider("anthropic", {"model": "claude"})

    with pytest.raises(GraphExecutionError) as exc_info:
        create_anthropic_provider(provider)

    assert exc_info.value.code == "ERR_PROVIDER_ANTHROPIC"



def test_google_provider_configures_client(monkeypatch: pytest.MonkeyPatch) -> None:
    import types

    captured: dict[str, Any] = {}

    module = types.ModuleType("google.generativeai")

    def configure(api_key: str) -> None:
        captured["api_key"] = api_key

    module.configure = configure
    module.GenerativeModel = lambda *args, **kwargs: None

    google_pkg = types.ModuleType("google")
    google_pkg.generativeai = module

    monkeypatch.setitem(sys.modules, "google", google_pkg)
    monkeypatch.setitem(sys.modules, "google.generativeai", module)

    provider = _make_provider(
        "google",
        {
            "api_key": "google-key",
            "model": "gemini-pro",
            "temperature": "0.2",
            "top_k": "32",
            "max_output_tokens": "512",
        },
    )

    context = create_google_provider(provider)

    assert captured["api_key"] == "google-key"
    assert context["model"] == "gemini-pro"
    assert context["generation_config"]["temperature"] == 0.2
    assert context["generation_config"]["top_k"] == 32
    assert context["generation_config"]["max_output_tokens"] == 512


def test_google_provider_env_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    import types

    module = types.ModuleType("google.generativeai")
    module.configure = lambda **_: None
    module.GenerativeModel = lambda *args, **kwargs: None

    google_pkg = types.ModuleType("google")
    google_pkg.generativeai = module

    monkeypatch.setitem(sys.modules, "google", google_pkg)
    monkeypatch.setitem(sys.modules, "google.generativeai", module)

    monkeypatch.setenv("GOOGLE_API_KEY", "env-key")
    provider = _make_provider("google", {"model": "gemini-pro"})

    context = create_google_provider(provider)

    assert context["model"] == "gemini-pro"


def test_google_provider_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    import types

    module = types.ModuleType("google.generativeai")
    module.configure = lambda **_: None
    module.GenerativeModel = lambda *args, **kwargs: None

    google_pkg = types.ModuleType("google")
    google_pkg.generativeai = module

    monkeypatch.setitem(sys.modules, "google", google_pkg)
    monkeypatch.setitem(sys.modules, "google.generativeai", module)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    provider = _make_provider("google", {"model": "gemini-pro"})

    with pytest.raises(GraphExecutionError) as exc_info:
        create_google_provider(provider)

    assert exc_info.value.code == "ERR_PROVIDER_GOOGLE"

def test_agentethan_uses_default_provider_factories(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    called: dict[str, NormalizedProvider] = {}

    def fake_provider(provider: NormalizedProvider) -> dict[str, Any]:
        called["provider"] = provider
        return {"client": object()}

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("agent_ethan2.providers.openai.create_openai_provider", fake_provider)

    config_path = tmp_path / "agent.yaml"
    config_path.write_text(
        """
meta:
  version: 2
  name: unit-test
runtime:
  engine: lc.lcel
  defaults:
    provider: default
  factories:
    components:
      dummy: tests.dummies.component_factory
providers:
  - id: default
    type: openai
    config:
      api_key: test-key
      model: gpt-4o-mini
components:
  - id: dummy_component
    type: dummy
    provider: default
    inputs: {}
    outputs: {}
    config: {}
graph:
  entry: dummy
  nodes:
    - id: dummy
      type: component
      component: dummy_component
  outputs:
    - key: result
      node: dummy
      output: config
""".strip()
    )

    AgentEthan(config_path)

    assert called["provider"].type == "openai"
    assert called["provider"].id == "default"
