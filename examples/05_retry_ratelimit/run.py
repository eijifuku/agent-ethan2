"""Run the retry and rate limit example."""

from __future__ import annotations

import json
from pathlib import Path

from agent_ethan2.agent import AgentEthan


def main() -> None:
    config_path = Path(__file__).resolve().parent / "config.yaml"
    
    # Initialize agent
    agent = AgentEthan(config_path)
    
    # Test messages
    messages = [
        "Hello, world!",
        "Testing retry mechanism",
        "Rate limiting in action",
    ]
    
    print("\n" + "="*70)
    print("Retry & Rate Limit Example")
    print("="*70)
    print("\nNote: The flaky component has a 60% failure rate.")
    print("Retry policy will attempt up to 5 times with exponential backoff.")
    print("Rate limit: 5 tokens/sec for LLM, 3 tokens/sec for flaky node.\n")
    
    for i, message in enumerate(messages, 1):
        print(f"\n{'='*70}")
        print(f"Test {i}: {message}")
        print('='*70)
        
        try:
            result = agent.run_sync({
                "message": message,
                "summary_prompt": f"Briefly confirm the message '{message}' was processed successfully.",
            })
            
            flaky_result = result.outputs.get("flaky_result", "N/A")
            flaky_status = result.outputs.get("flaky_status", "N/A")
            summary = result.outputs.get("summary", "N/A")
            
            print(f"✓ Flaky Result: {flaky_result}")
            print(f"✓ Status: {flaky_status}")
            print(f"✓ Summary: {summary}")
            
        except Exception as e:
            print(f"✗ Failed after all retries: {e}")
    
    print(f"\n{'='*70}")
    print("Check run.jsonl for detailed retry and rate limit events")
    print('='*70)


if __name__ == "__main__":
    main()

