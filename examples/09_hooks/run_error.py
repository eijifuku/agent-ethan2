"""Run the hooks example with error handling demonstration."""

from __future__ import annotations

from pathlib import Path

from agent_ethan2.agent import AgentEthan


def main() -> None:
    config_path = Path(__file__).resolve().parent / "config_error.yaml"
    
    print("\n" + "="*70)
    print("Component Lifecycle Hooks - Error Handling Example")
    print("="*70)
    print("\nThis example demonstrates:")
    print("  - on_error hook: Capture and log errors gracefully")
    print("\nWatch how the error hook is triggered:\n")
    
    # Initialize agent
    agent = AgentEthan(config_path)
    
    # Test: Trigger an error
    print("\n" + "─"*70)
    print("Test: Triggering API Error (invalid API key)")
    print("─"*70)
    
    try:
        result = agent.run_sync({
            "prompt": "This will fail due to invalid API key.",
        })
        print(f"\n📤 Unexpected success: {result.outputs}")
    except Exception as e:
        print(f"\n❌ Expected error occurred: {type(e).__name__}")
        print(f"   (The on_error hook should have logged this above)")
    
    print("\n" + "="*70)
    print("✓ Error hook demonstrated successfully!")
    print("="*70)


if __name__ == "__main__":
    main()

