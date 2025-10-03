"""Debug history access in component."""

from pathlib import Path
from agent_ethan2.agent import AgentEthan

config_path = Path(__file__).parent / "config_multi_histories.yaml"

# Patch factory to print debug info
original_factory = None

def debug_factory(component, provider_instance, tool_instance):
    print(f"\n=== FACTORY CALLED ===")
    print(f"Component config: {component.config}")
    
    # Call original
    import importlib
    module = importlib.import_module("examples.10_conversation_history.factories")
    original = getattr(module, "llm_with_history_factory")
    instance = original(component, provider_instance, tool_instance)
    
    # Wrap call to print context
    original_call = instance
    
    async def debug_call(state, inputs, ctx):
        print(f"\n=== COMPONENT CALL ===")
        print(f"Context keys: {list(ctx.keys())}")
        print(f"Registries keys: {list(ctx.get('registries', {}).keys())}")
        histories = ctx.get('registries', {}).get('histories', {})
        print(f"Histories in context: {list(histories.keys())}")
        return await original_call(state, inputs, ctx)
    
    return debug_call

# Monkey patch - must happen before agent creation
import sys
import importlib
fac_module = importlib.import_module("examples.10_conversation_history.factories")
fac_module.llm_with_history_factory = debug_factory

agent = AgentEthan(config_path)
print("✓ Agent loaded")

result = agent.run_sync({
    "user_message": "Hello",
    "session_id": "test",
})

print(f"\nResponse: {result.outputs.get('response')}")

