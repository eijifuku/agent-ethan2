"""Example: Multiple exporters (JSONL + Console + LangSmith)."""

from __future__ import annotations

from pathlib import Path

from agent_ethan2.agent import AgentEthan
from agent_ethan2.telemetry import ConsoleExporter, JsonlExporter, EventBus


def main() -> None:
    # Use the basic LLM config
    config_path = Path(__file__).resolve().parent.parent / "01_basic_llm" / "config.yaml"
    
    # Create multiple exporters
    exporters = [
        # Console for real-time viewing
        ConsoleExporter(
            color=True,
            verbose=False,
            filter_events=["graph.start", "graph.complete", "error.raised"]
        ),
        
        # JSONL for detailed logging
        JsonlExporter(path="telemetry_detailed.jsonl"),
    ]
    
    # Try to add LangSmith if available
    try:
        from agent_ethan2.telemetry.exporters.langsmith import LangSmithExporter
        
        langsmith = LangSmithExporter(
            project_name="agent-ethan2-demo"
        )
        exporters.append(langsmith)
        print("✓ LangSmith exporter enabled")
    except (ImportError, ValueError) as e:
        print(f"⚠ LangSmith exporter not available: {e}")
    
    # Try to add Prometheus if available
    try:
        from agent_ethan2.telemetry.exporters.prometheus import PrometheusExporter
        
        prometheus = PrometheusExporter(port=9090)
        exporters.append(prometheus)
        print("✓ Prometheus exporter enabled on :9090")
    except (ImportError, OSError) as e:
        print(f"⚠ Prometheus exporter not available: {e}")
    
    # Create event bus with all exporters
    event_bus = EventBus(exporters=exporters)
    
    # Initialize agent
    agent = AgentEthan(config_path)
    
    print("\n" + "="*70)
    print("Multiple Exporters Example")
    print("="*70)
    print(f"Active exporters: {len(exporters)}")
    print("  - Console (filtered)")
    print("  - JSONL (detailed)")
    if len(exporters) > 2:
        print("  - LangSmith (tracing)")
    if len(exporters) > 3:
        print("  - Prometheus (metrics on :9090)")
    print()
    
    # Run multiple times to generate metrics
    test_prompts = [
        "What is Python?",
        "Explain machine learning briefly.",
        "What is Docker?",
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n--- Test {i}/3: {prompt[:50]}... ---")
        
        result = agent.run_sync(
            {"user_prompt": prompt},
            event_emitter=event_bus,
            run_id=f"test-{i}"
        )
        
        response = result.outputs.get("final_response", "N/A")
        print(f"Response: {response[:100]}...")
    
    print("\n" + "="*70)
    print("✓ All tests complete")
    print("="*70)
    print("\nCheck outputs:")
    print("  - telemetry_detailed.jsonl (full event log)")
    if len(exporters) > 2:
        print("  - LangSmith dashboard (https://smith.langchain.com)")
    if len(exporters) > 3:
        print("  - Prometheus metrics (http://localhost:9090)")


if __name__ == "__main__":
    main()

