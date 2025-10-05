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


def _extract_choice_parsed(choice: Any) -> Any:
    message = getattr(choice, "message", None)
    if message is not None:
        parsed = getattr(message, "parsed", None)
        if parsed is not None:
            return parsed
        if isinstance(message, Mapping) and "parsed" in message:
            return message["parsed"]
    parsed_choice = getattr(choice, "parsed", None)
    if parsed_choice is not None:
        return parsed_choice
    if isinstance(choice, Mapping) and "parsed" in choice:
        return choice["parsed"]
    return None


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
                choice_payloads: list[dict[str, Any]] = []
                for choice in choices:
                    payload: dict[str, Any] = {
                        "text": _extract_choice_text(choice),
                    }
                    message = getattr(choice, "message", None)
                    if message is not None:
                        payload["message"] = message
                    parsed = _extract_choice_parsed(choice)
                    if parsed is not None:
                        payload["parsed"] = parsed
                    choice_payloads.append(payload)
                usage = _serialise_usage(getattr(response, "usage", None))
                return {
                    "choices": choice_payloads,
                    "usage": usage,
                }

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


class GeminiChatComponentFactory(ComponentFactoryBase):
    """Create a Gemini chat component backed by Google Generative AI."""

    error_code = "ERR_COMPONENT_GEMINI_CHAT"

    def build(
        self,
        component: NormalizedComponent,
        provider_instance: Any,
        tool_instance: Any,
    ) -> Any:
        provider_ctx = self.require_provider(component, provider_instance)
        client = provider_ctx.get("client")
        if client is None or not hasattr(client, "GenerativeModel"):
            raise GraphExecutionError(
                self.error_code,
                "Google Generative AI client is missing from provider context",
                pointer=self._pointer(component),
            )

        model = component.config.get("model") or provider_ctx.get("model")
        if not model:
            raise GraphExecutionError(
                self.error_code,
                "Model name is required (set component.config.model or provider config)",
                pointer=self._pointer(component),
            )

        base_generation_config = dict(provider_ctx.get("generation_config") or {})

        def update_generation(key: str, field: str, *, is_int: bool = False) -> None:
            value = component.config.get(field)
            if value in (None, ""):
                return
            if is_int:
                coerced = self.coerce_int(component, value, field=field)
            else:
                coerced = self.coerce_float(component, value, field=field)
            if coerced is not None:
                base_generation_config[key] = coerced

        update_generation("temperature", "temperature")
        update_generation("top_p", "top_p")
        update_generation("top_k", "top_k", is_int=True)
        update_generation("max_output_tokens", "max_output_tokens", is_int=True)

        component_stop = component.config.get("stop_sequences")
        if component_stop is not None:
            if isinstance(component_stop, (list, tuple)):
                base_generation_config["stop_sequences"] = list(component_stop)
            else:
                raise GraphExecutionError(
                    self.error_code,
                    "stop_sequences must be a list",
                    pointer=self._pointer(component),
                )
        elif "stop_sequences" not in base_generation_config:
            provider_cfg = provider_ctx.get("generation_config") or {}
            if isinstance(provider_cfg, Mapping) and provider_cfg.get("stop_sequences") is not None:
                base_generation_config["stop_sequences"] = provider_cfg["stop_sequences"]

        safety_settings = component.config.get("safety_settings") or provider_ctx.get("safety_settings")
        system_instruction = component.config.get("system_instruction") or provider_ctx.get("system_instruction")

        def format_messages(inputs: Mapping[str, Any]) -> Any:
            messages = inputs.get("messages")
            if isinstance(messages, list):
                formatted: list[dict[str, Any]] = []
                for message in messages:
                    if not isinstance(message, Mapping):
                        continue
                    role = message.get("role", "user")
                    parts = message.get("parts")
                    if parts is None:
                        content = message.get("content", "")
                        if isinstance(content, list):
                            parts = content
                        else:
                            parts = [content]
                    formatted.append({"role": role, "parts": list(parts)})
                return formatted if formatted else ""
            prompt = inputs.get("prompt")
            return "" if prompt is None else prompt

        def extract_text(response: Any) -> str:
            text = getattr(response, "text", None)
            if isinstance(text, str) and text:
                return text
            candidates = getattr(response, "candidates", None)
            if candidates:
                first = candidates[0]
                content = getattr(first, "content", None)
                parts = getattr(content, "parts", None) if content is not None else None
                if parts:
                    return "".join(str(getattr(part, "text", part)) for part in parts)
            return ""

        def serialise_usage(response: Any) -> Mapping[str, Any]:
            usage = getattr(response, "usage_metadata", None)
            if usage is None:
                return {}
            data: dict[str, Any] = {}
            prompt_tokens = getattr(usage, "prompt_token_count", None)
            if prompt_tokens is not None:
                data["prompt_tokens"] = prompt_tokens
            candidates_tokens = getattr(usage, "candidates_token_count", None)
            if candidates_tokens is not None:
                data["candidates_tokens"] = candidates_tokens
            total_tokens = getattr(usage, "total_token_count", None)
            if total_tokens is not None:
                data["total_tokens"] = total_tokens
            return data

        async def call(state: Mapping[str, Any], inputs: Mapping[str, Any], ctx: Mapping[str, Any]) -> Mapping[str, Any]:
            content = format_messages(inputs)

            def _invoke() -> Mapping[str, Any]:
                kwargs: dict[str, Any] = {"model_name": model}
                if base_generation_config:
                    kwargs["generation_config"] = dict(base_generation_config)
                if safety_settings is not None:
                    kwargs["safety_settings"] = safety_settings
                if system_instruction is not None:
                    kwargs["system_instruction"] = system_instruction

                model_instance = client.GenerativeModel(**kwargs)
                response = model_instance.generate_content(content)
                text = extract_text(response)
                usage = serialise_usage(response)
                return {
                    "choices": [{"text": text}],
                    "usage": usage,
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


def create_gemini_chat_component(
    component: NormalizedComponent,
    provider_instance: Any,
    tool_instance: Any,
) -> Any:
    return GeminiChatComponentFactory()(component, provider_instance, tool_instance)


__all__ = [
    "OpenAIChatComponentFactory",
    "AnthropicMessagesComponentFactory",
    "create_openai_chat_component",
    "create_anthropic_messages_component",
    "GeminiChatComponentFactory",
    "create_gemini_chat_component",
]
