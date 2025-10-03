"""Run the hooks example."""

from __future__ import annotations

import json
from pathlib import Path

from agent_ethan2.agent import AgentEthan


def main() -> None:
    config_path = Path(__file__).resolve().parent / "config.yaml"
    
    print("\n" + "="*70)
    print("Component Lifecycle Hooks Example")
    print("="*70)
    print("\nThis example demonstrates:")
    print("  - before_execute: Log inputs, add timestamps")
    print("  - after_execute: Log outputs, add metadata")
    print("  - on_error: Handle and log errors")
    print("\nWatch the detailed hook output below:\n")
    
    # Initialize agent
    agent = AgentEthan(config_path)
    
    # Test 1: Normal execution
    print("\n" + "─"*70)
    print("Test 1: Normal Execution")
    print("─"*70)
    
    result = agent.run_sync({
        "prompt": "Explain Python decorators in one sentence.",
    })
    
    print(f"\n📤 Final Output:")
    print(f"  Response: {result.outputs.get('response', 'N/A')[:150]}...")
    
    metadata = result.outputs.get('metadata')
    if metadata:
        print(f"\n📊 Metadata (added by after_execute hook):")
        print(f"  {json.dumps(metadata, indent=4)}")
    
    print("\n" + "="*70)
    print("✓ Hooks executed successfully!")
    print("="*70)


if __name__ == "__main__":
    main()

