"""Component lifecycle hooks."""

from __future__ import annotations

from typing import Any, Mapping, Optional, Protocol


class ComponentHooks(Protocol):
    """
    Protocol for component lifecycle hooks.
    
    Components can optionally implement these methods to add custom behavior
    before/after execution and during error handling.
    
    All hooks are optional - implement only what you need.
    """
    
    async def before_execute(
        self,
        inputs: Mapping[str, Any],
        ctx: Mapping[str, Any]
    ) -> Optional[Mapping[str, Any]]:
        """
        Called before component execution.
        
        Use cases:
        - Logging input data
        - Input validation
        - Input transformation
        - Pre-execution setup
        
        Args:
            inputs: Component inputs (read-only)
            ctx: Execution context with node_id, graph_name, config, etc.
            
        Returns:
            Modified inputs dict (or None to use original inputs)
            
        Example:
            async def before_execute(self, inputs, ctx):
                print(f"[{ctx['node_id']}] Starting with: {inputs}")
                # Add timestamp to inputs
                return {**inputs, "started_at": time.time()}
        """
        ...
    
    async def after_execute(
        self,
        result: Any,
        inputs: Mapping[str, Any],
        ctx: Mapping[str, Any]
    ) -> Optional[Any]:
        """
        Called after successful component execution.
        
        Use cases:
        - Logging output data
        - Output validation
        - Output transformation
        - Post-execution cleanup
        - Caching results
        
        Args:
            result: Component result (raw output before output mapping)
            inputs: Component inputs (read-only)
            ctx: Execution context with node_id, graph_name, config, etc.
            
        Returns:
            Modified result (or None to use original result)
            
        Example:
            async def after_execute(self, result, inputs, ctx):
                print(f"[{ctx['node_id']}] Completed: {result}")
                # Add metadata to result
                return {**result, "node_id": ctx['node_id']}
        """
        ...
    
    async def on_error(
        self,
        error: Exception,
        inputs: Mapping[str, Any],
        ctx: Mapping[str, Any]
    ) -> None:
        """
        Called when component execution fails.
        
        Use cases:
        - Error logging
        - Alert/notification
        - Error recovery attempt
        - Cleanup on failure
        
        Note: This is called BEFORE retry logic, so it will be called
        multiple times if retries are configured.
        
        Args:
            error: The exception that occurred
            inputs: Component inputs (read-only)
            ctx: Execution context with node_id, graph_name, config, etc.
            
        Returns:
            None (cannot modify the error)
            
        Example:
            async def on_error(self, error, inputs, ctx):
                print(f"[{ctx['node_id']}] ERROR: {error}")
                await send_alert(f"Component failed: {error}")
        """
        ...


def has_hook(component: Any, hook_name: str) -> bool:
    """
    Check if a component has a specific hook method.
    
    Args:
        component: Component instance
        hook_name: Name of the hook ('before_execute', 'after_execute', 'on_error')
        
    Returns:
        True if the component has the hook method
    """
    return (
        hasattr(component, hook_name) and
        callable(getattr(component, hook_name))
    )

