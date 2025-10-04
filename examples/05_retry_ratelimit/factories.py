"""Factories for Example 05."""

from __future__ import annotations

import random
from typing import Any, Mapping

from agent_ethan2.ir import NormalizedComponent


def flaky_component_factory(
    component: NormalizedComponent,
    provider_instance: Mapping[str, Any],
    tool_instance: Any,
):
    """Create a component that randomly fails to demonstrate retry."""
    
    failure_rate = component.config.get("failure_rate", 0.5)
    
    async def call(state: Mapping[str, Any], inputs: Mapping[str, Any], ctx: Mapping[str, Any]) -> Mapping[str, Any]:
        """
        A flaky component that fails randomly.
        
        Expected inputs:
            message: str - message to process
        
        Returns:
            result: str - processed message
            attempts: int - number of attempts made
        """
        message = inputs.get("message", "")
        
        # Simulate random failure
        if random.random() < failure_rate:
            raise RuntimeError(f"Simulated failure (failure_rate={failure_rate})")
        
        # Success
        return {
            "result": f"Processed: {message}",
            "status": "success",
        }
    
    return call
