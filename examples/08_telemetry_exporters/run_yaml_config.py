"""Example: Exporters configured entirely via YAML."""

from __future__ import annotations

from pathlib import Path

from agent_ethan2.agent import AgentEthan


def main() -> None:
    config_path = Path(__file__).resolve().parent / "config_multi_exporters.yaml"
    
    print("\n" + "="*70)
    print("YAML-Configured Exporters Example")
    print("="*70)
    print("\nAll exporters configured in YAML:")
    print("  - JSONL (telemetry.jsonl)")
    print("  - Console (colored, filtered)")
    print("  - LangSmith (if LANGSMITH_API_KEY set)")
    print("  - Prometheus (on :9090)")
    print("\nWatch the console output below:\n")
    
    # Initialize agent - exporters are automatically loaded from YAML
    agent = AgentEthan(config_path)
    
    # Run multiple tests
    test_prompts = [
        "What is Python?",
        "Explain Docker in one sentence.",
        "What is async/await?",
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n{'─'*70}")
        print(f"Test {i}/3: {prompt}")
        print('─'*70)
        
        result = agent.run_sync(
            {"user_prompt": prompt},
            run_id=f"yaml-test-{i}"
        )
        
        response = result.outputs.get("final_response", "N/A")
        print(f"\nResponse: {response[:150]}...")
    
    print("\n" + "="*70)
    print("✓ All tests complete")
    print("="*70)
    print("\nCheck outputs:")
    print("  - telemetry.jsonl (detailed JSONL log)")
    print("  - Console output above (filtered events)")
    print("  - LangSmith: https://smith.langchain.com")
    print("  - Prometheus: http://localhost:9090/metrics")


if __name__ == "__main__":
    main()

