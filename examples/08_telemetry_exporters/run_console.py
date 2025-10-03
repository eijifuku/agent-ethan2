"""Example: Console exporter with colored output."""

from __future__ import annotations

from pathlib import Path

from agent_ethan2.agent import AgentEthan
from agent_ethan2.telemetry import ConsoleExporter, EventBus


def main() -> None:
    # Use the basic LLM config
    config_path = Path(__file__).resolve().parent.parent / "01_basic_llm" / "config.yaml"
    
    # Create console exporter
    console_exporter = ConsoleExporter(
        color=True,
        verbose=False,  # Set to True for full payloads
        filter_events=None,  # Or filter specific events: ["graph.start", "graph.complete"]
    )
    
    # Create event bus with console exporter
    event_bus = EventBus(exporters=[console_exporter])
    
    # Initialize agent with custom event bus
    agent = AgentEthan(config_path)
    
    print("\n" + "="*70)
    print("Console Exporter Example - Colored Real-time Output")
    print("="*70)
    print("\nWatch the colored event stream below:\n")
    
    # Run with console output
    result = agent.run_sync(
        {"user_prompt": "Explain async/await in Python in 2 sentences."},
        event_emitter=event_bus
    )
    
    print("\n" + "="*70)
    print("Final Result:")
    print("="*70)
    print(result.outputs.get("final_response", "N/A"))


if __name__ == "__main__":
    main()

