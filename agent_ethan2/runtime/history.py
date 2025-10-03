"""Conversation history management utilities."""

from __future__ import annotations

from typing import Any, Mapping, Sequence


def build_messages_with_history(
    prompt: str,
    state: Mapping[str, Any],
    *,
    history_key: str = "chat_history",
    system_message: str | None = None,
    max_history: int | None = None,
) -> list[dict[str, str]]:
    """
    Build messages array with conversation history from state.
    
    Args:
        prompt: Current user prompt
        state: Graph state containing previous messages
        history_key: Key in state where history is stored (default: "chat_history")
        system_message: Optional system message to prepend
        max_history: Maximum number of history messages to include
        
    Returns:
        List of message dicts compatible with OpenAI API
        
    Example:
        messages = build_messages_with_history(
            prompt="What's the capital of France?",
            state={"chat_history": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ]},
            system_message="You are a helpful assistant."
        )
        # Returns:
        # [
        #   {"role": "system", "content": "You are a helpful assistant."},
        #   {"role": "user", "content": "Hello"},
        #   {"role": "assistant", "content": "Hi there!"},
        #   {"role": "user", "content": "What's the capital of France?"}
        # ]
    """
    messages: list[dict[str, str]] = []
    
    # Add system message if provided
    if system_message:
        messages.append({"role": "system", "content": system_message})
    
    # Add conversation history from state
    history = state.get(history_key, [])
    if isinstance(history, Sequence):
        history_messages = list(history)
        
        # Limit history if max_history is specified
        if max_history is not None and len(history_messages) > max_history:
            # Keep the most recent max_history messages
            history_messages = history_messages[-max_history:]
        
        # Add history messages
        for msg in history_messages:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                messages.append({
                    "role": str(msg["role"]),
                    "content": str(msg["content"])
                })
    
    # Add current user prompt
    messages.append({"role": "user", "content": prompt})
    
    return messages


def append_to_history(
    history: Sequence[dict[str, str]] | None,
    user_message: str,
    assistant_message: str,
) -> list[dict[str, str]]:
    """
    Append user and assistant messages to conversation history.
    
    Args:
        history: Existing conversation history (or None)
        user_message: User's message
        assistant_message: Assistant's response
        
    Returns:
        Updated conversation history
        
    Example:
        new_history = append_to_history(
            history=[{"role": "user", "content": "Hello"}],
            user_message="What's 2+2?",
            assistant_message="2+2 equals 4."
        )
        # Returns:
        # [
        #   {"role": "user", "content": "Hello"},
        #   {"role": "user", "content": "What's 2+2?"},
        #   {"role": "assistant", "content": "2+2 equals 4."}
        # ]
    """
    result = list(history) if history else []
    result.append({"role": "user", "content": user_message})
    result.append({"role": "assistant", "content": assistant_message})
    return result


def extract_history_from_state(
    state: Mapping[str, Any],
    history_key: str = "chat_history",
) -> list[dict[str, str]]:
    """
    Extract conversation history from graph state.
    
    Args:
        state: Graph state
        history_key: Key where history is stored
        
    Returns:
        Conversation history as list of message dicts
    """
    history = state.get(history_key, [])
    if isinstance(history, Sequence):
        return [
            {"role": str(msg["role"]), "content": str(msg["content"])}
            for msg in history
            if isinstance(msg, dict) and "role" in msg and "content" in msg
        ]
    return []

