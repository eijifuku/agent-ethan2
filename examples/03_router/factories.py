"""Factories for Example 03."""

from __future__ import annotations

from typing import Any, Mapping

from agent_ethan2.ir import NormalizedComponent


def router_component_factory(
    component: NormalizedComponent,
    provider_instance: Mapping[str, Any],
    tool_instance: Any,
):
    """Create a router component that classifies input and returns a route."""
    
    async def call(state: Mapping[str, Any], inputs: Mapping[str, Any], ctx: Mapping[str, Any]) -> Mapping[str, Any]:
        """
        Classify the user input and return routing decision.
        
        Expected inputs:
            user_input: str - the user's message
        
        Returns:
            route: str - one of "greeting", "question", "calculation", "other"
        """
        user_input = inputs.get("user_input", "").lower()
        
        # Simple keyword-based routing
        if any(word in user_input for word in ["hello", "hi", "hey", "good morning", "good evening"]):
            route = "greeting"
        elif any(word in user_input for word in ["?", "what", "how", "why", "when", "where", "who"]):
            route = "question"
        elif any(word in user_input for word in ["calculate", "compute", "+", "-", "*", "/", "add", "subtract", "multiply", "divide"]):
            route = "calculation"
        else:
            route = "other"
        
        return {
            "route": route,
            "input": user_input,
        }
    
    return call
