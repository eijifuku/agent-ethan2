"""Factories for Example 10 - Conversation History."""

from __future__ import annotations

import asyncio
from typing import Any, Mapping

from openai import OpenAI

from agent_ethan2.ir import NormalizedComponent
from agent_ethan2.runtime.history import build_messages_with_history


def _call_openai(client, model, messages, temperature, max_tokens):
    """Helper to call OpenAI API synchronously."""
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=float(temperature),
        max_tokens=int(max_tokens),
    )
    return response.choices[0].message.content if response.choices else ""



def llm_with_history_factory(
    component: NormalizedComponent,
    provider_instance: Mapping[str, Any],
    tool_instance: Any,
):
    """Create LLM component with conversation history support."""
    
    client: OpenAI = provider_instance["client"]
    model: str = provider_instance["model"]
    
    # Configuration from component
    temperature = component.config.get("temperature", 0.7)
    max_output_tokens = component.config.get("max_output_tokens", 256)
    use_history = component.config.get("use_history", False)
    
    # History configuration
    # New: Use history_id to reference a defined history instance
    history_id = component.config.get("history_id")
    
    # Fallback: Old style with direct config
    history_key = component.config.get("history_key", "chat_history")
    system_message = component.config.get("system_message")
    max_history = component.config.get("max_history")
    
    # Cache for backend instances (shared across calls)
    backend_cache = {}
    
    async def call(
        state: Mapping[str, Any],
        inputs: Mapping[str, Any],
        ctx: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        prompt = inputs.get("prompt", "")
        loop = asyncio.get_running_loop()
        
        async def _invoke() -> Mapping[str, Any]:
            # Build messages with or without history
            if use_history and history_id:
                # New: Get history from context registries
                from agent_ethan2.runtime.history_backend import create_history_backend
                
                histories = ctx.get("registries", {}).get("histories", {})
                history_config = histories.get(history_id)
                
                if history_config:
                    # Create or get cached backend
                    if history_id not in backend_cache:
                        backend_cache[history_id] = create_history_backend(history_config.backend)
                    backend = backend_cache[history_id]
                    
                    # Get session ID from state
                    session_id = state.get("session_id", "default")
                    
                    # Retrieve history
                    history_messages = await backend.get_history(session_id)
                    
                    # Build messages with history
                    messages = []
                    if history_config.system_message:
                        messages.append({
                            "role": "system",
                            "content": history_config.system_message
                        })
                    messages.extend(history_messages)
                    messages.append({"role": "user", "content": prompt})
                    
                    # Call LLM
                    response_text = _call_openai(client, model, messages, temperature, max_output_tokens)
                    
                    # Save to history
                    await backend.append_message(session_id, "user", prompt)
                    await backend.append_message(session_id, "assistant", response_text)
                    
                    return {
                        "choices": [{"text": response_text}],
                        "usage": {},
                        "messages": messages,
                    }
            
            # Fallback: old style or no history
            if use_history:
                messages = build_messages_with_history(
                    prompt=prompt,
                    state=state,
                    history_key=history_key,
                    system_message=system_message,
                    max_history=max_history,
                )
            else:
                # No history - single message
                messages = [{"role": "user", "content": prompt}]
                if system_message:
                    messages.insert(0, {"role": "system", "content": system_message})
            
            # Call OpenAI API (fallback path)
            text = _call_openai(client, model, messages, temperature, max_output_tokens)
            
            return {
                "choices": [{"text": text}],
                "usage": {},
                "messages": messages,
            }
        
        # Run async _invoke
        return await _invoke()
    
    return call

