"""Run the LLM with tool example."""

from __future__ import annotations

import json
from pathlib import Path

from agent_ethan2.agent import AgentEthan


def main() -> None:
    config_path = Path(__file__).resolve().parent / "config.yaml"
    
    # Initialize agent
    agent = AgentEthan(config_path)
    
    # Example calculations
    calculations = [
        {"operation": "add", "a": 15, "b": 27, "desc": "15 + 27"},
        {"operation": "divide", "a": 100, "b": 4, "desc": "100 / 4"},
        {"operation": "multiply", "a": 12, "b": 8, "desc": "12 * 8"},
        {"operation": "subtract", "a": 50, "b": 23, "desc": "50 - 23"},
    ]
    
    for calc in calculations:
        print(f"\n{'='*60}")
        print(f"Calculation: {calc['desc']}")
        print('='*60)
        
        # Prepare inputs
        inputs = {
            "operation": calc["operation"],
            "a": calc["a"],
            "b": calc["b"],
            "format_prompt": f"Please explain the calculation result '{calc['desc']}' in a friendly, natural way.",
        }
        
        result = agent.run_sync(inputs)
        
        print(f"\nCalculation: {result.outputs.get('calculation', 'N/A')}")
        print(f"Result: {result.outputs.get('result', 'N/A')}")
        print(f"LLM Response: {result.outputs.get('final_response', 'N/A')}")


if __name__ == "__main__":
    main()

