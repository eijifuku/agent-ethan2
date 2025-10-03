"""Run the router example."""

from __future__ import annotations

import json
from pathlib import Path

from agent_ethan2.agent import AgentEthan


def main() -> None:
    config_path = Path(__file__).resolve().parent / "config.yaml"
    
    # Initialize agent
    agent = AgentEthan(config_path)
    
    # Test various types of inputs
    test_inputs = [
        "Hello! How are you today?",
        "What is the capital of France?",
        "Calculate 25 + 17",
        "I love programming!",
        "Why is the sky blue?",
        "Good morning!",
        "Compute 100 divided by 5",
        "Tell me a joke",
    ]
    
    for user_message in test_inputs:
        print(f"\n{'='*70}")
        print(f"Input: {user_message}")
        print('='*70)
        
        result = agent.run_sync({"user_message": user_message})
        
        route = result.outputs.get("route_taken", "unknown")
        # Response is stored in node's internal state, not graph outputs
        # For now, just show the route
        print(f"Route: {route}")


if __name__ == "__main__":
    main()

