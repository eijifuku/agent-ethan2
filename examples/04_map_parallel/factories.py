"""Factories for Example 04."""

from __future__ import annotations

from typing import Any, Mapping

from agent_ethan2.ir import NormalizedComponent


def map_component_factory(
    component: NormalizedComponent,
    provider_instance: Mapping[str, Any],
    tool_instance: Any,
):
    """Create a map component that processes each item."""
    
    # Note: collection, failure_mode, ordered, result_key are handled by the runtime scheduler
    # This component only processes individual items
    
    async def call(state: Mapping[str, Any], inputs: Mapping[str, Any], ctx: Mapping[str, Any]) -> Mapping[str, Any]:
        """
        Process a single item (used in map operation).
        
        Expected inputs:
            item: str - the item to process (automatically provided by map runtime)
        
        Returns:
            processed: str - uppercase version
            length: int - character count
            original: str - original item
        """
        item = inputs.get("item", "")
        processed = item.upper()
        length = len(item)
        
        return {
            "processed": processed,
            "length": length,
            "original": item,
        }
    
    return call
