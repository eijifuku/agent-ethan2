"""Custom component implementations for Example 07."""

from __future__ import annotations

from typing import Any, Mapping


async def intent_classifier(state: Mapping[str, Any], inputs: Mapping[str, Any], ctx: Mapping[str, Any]) -> Mapping[str, Any]:
    """
    Classify user intent and route to appropriate handler.
    
    Expected inputs:
        user_input: str - the user's input text
    
    Returns:
        intent: str - detected intent (search, calculate, validate, general)
        confidence: float - confidence score
        route: str - routing decision
    """
    user_input = inputs.get("user_input", "").lower()
    
    # Simple keyword-based intent detection
    if any(keyword in user_input for keyword in ["search", "find", "look up", "google"]):
        return {
            "intent": "search",
            "confidence": 0.9,
            "route": "search",
        }
    elif any(keyword in user_input for keyword in ["calculate", "compute", "add", "subtract", "multiply", "divide", "+", "-", "*", "/"]):
        return {
            "intent": "calculate",
            "confidence": 0.85,
            "route": "calculate",
        }
    elif any(keyword in user_input for keyword in ["validate", "check", "verify"]):
        return {
            "intent": "validate",
            "confidence": 0.8,
            "route": "validate",
        }
    else:
        return {
            "intent": "general",
            "confidence": 0.6,
            "route": "general",
        }


async def result_formatter(state: Mapping[str, Any], inputs: Mapping[str, Any], ctx: Mapping[str, Any]) -> Mapping[str, Any]:
    """
    Format results for presentation.
    
    Expected inputs:
        data: dict - data to format
        format_type: str - formatting style (json, text, markdown)
    
    Returns:
        formatted: str - formatted output
        format_used: str - the format that was used
    """
    data = inputs.get("data", {})
    format_type = inputs.get("format_type", "text")
    
    if format_type == "json":
        import json
        formatted = json.dumps(data, indent=2, ensure_ascii=False)
    elif format_type == "markdown":
        lines = ["## Results\n"]
        for key, value in data.items():
            lines.append(f"- **{key}**: {value}")
        formatted = "\n".join(lines)
    else:  # text
        lines = []
        for key, value in data.items():
            lines.append(f"{key}: {value}")
        formatted = "\n".join(lines)
    
    return {
        "formatted": formatted,
        "format_used": format_type,
    }

