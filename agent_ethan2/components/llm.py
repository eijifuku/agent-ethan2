"""Built-in LLM component factories."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from agent_ethan2.graph.errors import GraphExecutionError
from agent_ethan2.ir import NormalizedComponent

from .base import ComponentFactoryBase


def _serialise_usage(usage: Any) -> Mapping[str, Any]:
    if usage is None:
        return {}
    if hasattr(usage, "model_dump"):
        return usage.model_dump()
    if isinstance(usage, Mapping):
        return dict(usage)
    return {
        key: getattr(usage, key)
        for key in dir(usage)
        if not key.startswith("_") and isinstance(getattr(usage, key), (int, float))
    }


def _extract_choice_text(choice: Any) -> str:
    if choice is None:
        return ""
    message = getattr(choice, "message", None)
    if isinstance(message, Mapping):
        return str(message.get("content", ""))
    if message is not None and hasattr(message, "content"):
        content = message.content
        if isinstance(content, str):
            return content
        if isinstance(content, Iterable):
            # Newer SDKs may return a list of content parts
            return "".join(str(part) for part in content)
    if isinstance(choice, Mapping):
        message = choice.get("message")
        if isinstance(message, Mapping):
            return str(message.get("content", ""))
    text = getattr(choice, "text", None)
    if text is None and isinstance(choice, Mapping):
        text = choice.get("text")
    return "" if text is None else str(text)


class OpenAIChatComponentFactory(ComponentFactoryBase):
    """Create an OpenAI chat completion component."""

    error_code = "ERR_COMPONENT_OPENAI_CHAT"

    def build(
        self,
        component: NormalizedComponent,
        provider_instance: Any,
        tool_instance: Any,
    ) -> Any:
        provider_ctx = self.require_provider(component, provider_instance)
        client = provider_ctx.get("client")
        if client is None:
            raise GraphExecutionError(
                self.error_code,
                "OpenAI client is missing from provider context",
                pointer=self._pointer(component),
            )

        model = (
            component.config.get("model")
            or provider_ctx.get("model")
        )
        if not model:
            raise GraphExecutionError(
                self.error_code,
                "Model name is required (set component.config.model or provider config)",
                pointer=self._pointer(component),
            )

        temperature_cfg = component.config.get("temperature", provider_ctx.get("temperature"))
        max_tokens_cfg = component.config.get("max_output_tokens", provider_ctx.get("max_output_tokens"))
        timeout_cfg = component.config.get("timeout", provider_ctx.get("timeout"))
        response_format = component.config.get("response_format")
        system_prompt = component.config.get("system_prompt")
        stop_sequences = component.config.get("stop")

        temperature = self.coerce_float(component, temperature_cfg, field="temperature")
        max_tokens = self.coerce_int(component, max_tokens_cfg, field="max_output_tokens")
        timeout = self.coerce_float(component, timeout_cfg, field="timeout")

        def build_messages(inputs: Mapping[str, Any]) -> list[dict[str, Any]]:
            messages_input = inputs.get("messages")
            if isinstance(messages_input, list):
                return list(messages_input)
            prompt = inputs.get("prompt", "")
            messages: list[dict[str, Any]] = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            return messages

        async def call(state: Mapping[str, Any], inputs: Mapping[str, Any], ctx: Mapping[str, Any]) -> Mapping[str, Any]:
            messages = build_messages(inputs)

            def _invoke() -> Mapping[str, Any]:
                kwargs: dict[str, Any] = {
                    "model": model,
                    "messages": messages,
                }
                if temperature is not None:
                    kwargs["temperature"] = float(temperature)
                if max_tokens is not None:
                    kwargs["max_tokens"] = int(max_tokens)
                if timeout is not None:
                    kwargs["timeout"] = float(timeout)
                if response_format is not None:
                    kwargs["response_format"] = response_format
                if stop_sequences is not None:
                    kwargs["stop"] = stop_sequences

                response = client.chat.completions.create(**kwargs)
                choices = getattr(response, "choices", [])
                text = _extract_choice_text(choices[0]) if choices else ""
                usage = _serialise_usage(getattr(response, "usage", None))
                result: Mapping[str, Any] = {
                    "choices": [{"text": text, "message": getattr(choices[0], "message", None)}] if choices else [],
                    "usage": usage,
                }
                return result

            return await self.run_in_executor(_invoke)

        return call


class AnthropicMessagesComponentFactory(ComponentFactoryBase):
    """Create an Anthropic messages component."""

    error_code = "ERR_COMPONENT_ANTHROPIC_MESSAGES"

    def build(
        self,
        component: NormalizedComponent,
        provider_instance: Any,
        tool_instance: Any,
    ) -> Any:
        provider_ctx = self.require_provider(component, provider_instance)
        client = provider_ctx.get("client")
        if client is None:
            raise GraphExecutionError(
                self.error_code,
                "Anthropic client is missing from provider context",
                pointer=self._pointer(component),
            )

        model = component.config.get("model") or provider_ctx.get("model")
        if not model:
            raise GraphExecutionError(
                self.error_code,
                "Model name is required (set component.config.model or provider config)",
                pointer=self._pointer(component),
            )

        temperature_cfg = component.config.get("temperature", provider_ctx.get("temperature"))
        max_tokens_cfg = component.config.get("max_tokens", provider_ctx.get("max_tokens"))
        system_prompt = component.config.get("system_prompt") or component.config.get("system")
        stop_sequences = component.config.get("stop")

        temperature = self.coerce_float(component, temperature_cfg, field="temperature")
        max_tokens = self.coerce_int(component, max_tokens_cfg, field="max_tokens")

        def build_messages(inputs: Mapping[str, Any]) -> list[dict[str, Any]]:
            messages_input = inputs.get("messages")
            if isinstance(messages_input, list):
                return list(messages_input)
            prompt = inputs.get("prompt", "")
            return [{"role": "user", "content": prompt}]

        def extract_text(response: Any) -> str:
            content = getattr(response, "content", None)
            if isinstance(content, list) and content:
                block = content[0]
                text = getattr(block, "text", None)
                if text is None and isinstance(block, Mapping):
                    text = block.get("text")
                return "" if text is None else str(text)
            return getattr(response, "output_text", "")

        async def call(state: Mapping[str, Any], inputs: Mapping[str, Any], ctx: Mapping[str, Any]) -> Mapping[str, Any]:
            messages = build_messages(inputs)

            def _invoke() -> Mapping[str, Any]:
                kwargs: dict[str, Any] = {
                    "model": model,
                    "messages": messages,
                }
                if temperature is not None:
                    kwargs["temperature"] = float(temperature)
                if max_tokens is not None:
                    kwargs["max_tokens"] = int(max_tokens)
                if system_prompt:
                    kwargs["system"] = system_prompt
                if stop_sequences is not None:
                    kwargs["stop_sequences"] = stop_sequences

                response = client.messages.create(**kwargs)
                text = extract_text(response)
                usage = getattr(response, "usage", None)
                usage_dict = usage.model_dump() if hasattr(usage, "model_dump") else (dict(usage) if isinstance(usage, Mapping) else {})
                return {
                    "choices": [{"text": text}],
                    "usage": usage_dict,
                }

            return await self.run_in_executor(_invoke)

        return call


def create_openai_chat_component(
    component: NormalizedComponent,
    provider_instance: Any,
    tool_instance: Any,
) -> Any:
    return OpenAIChatComponentFactory()(component, provider_instance, tool_instance)


def create_anthropic_messages_component(
    component: NormalizedComponent,
    provider_instance: Any,
    tool_instance: Any,
) -> Any:
    return AnthropicMessagesComponentFactory()(component, provider_instance, tool_instance)


__all__ = [
    "OpenAIChatComponentFactory",
    "AnthropicMessagesComponentFactory",
    "create_openai_chat_component",
    "create_anthropic_messages_component",
]
