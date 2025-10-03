"""Run the full agent example."""

from __future__ import annotations

import json
from pathlib import Path

from agent_ethan2.agent import AgentEthan


def main() -> None:
    config_path = Path(__file__).resolve().parent / "config.yaml"
    
    # Initialize agent
    agent = AgentEthan(config_path)
    
    print("\n" + "="*70)
    print("Full Agent Example - All Features Combined")
    print("="*70)
    print("\nThis example demonstrates:")
    print("  - Intent Classification (Router)")
    print("  - Multiple Tools (Search, Calculator, Validator)")
    print("  - LLM Integration")
    print("  - Retry Policies")
    print("  - Complex Routing Logic")
    
    # Test cases
    test_cases = [
        {
            "name": "Search Query",
            "inputs": {
                "user_input": "search for latest AI news",
                "search_query": "latest AI news",
                "search_prompt": "Summarize these search results about AI news.",
            },
        },
        {
            "name": "Math Calculation",
            "inputs": {
                "user_input": "calculate 150 + 75",
                "operation": "add",
                "operand_a": 150,
                "operand_b": 75,
                "calc_prompt": "The calculation result is ready. Please confirm.",
            },
        },
        {
            "name": "Data Validation",
            "inputs": {
                "user_input": "validate this data",
                "validation_data": {"name": "John", "age": 30},
                "required_fields": ["name", "age", "email"],
                "validate_prompt": "Report on the validation results.",
            },
        },
        {
            "name": "General Query",
            "inputs": {
                "user_input": "tell me about Python programming",
                "general_prompt": "Tell me about Python programming in one paragraph.",
            },
        },
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"Test {i}: {test_case['name']}")
        print('='*70)
        print(f"User Input: {test_case['inputs']['user_input']}")
        
        try:
            result = agent.run_sync(test_case['inputs'])
            
            intent = result.outputs.get("intent", "N/A")
            confidence = result.outputs.get("confidence", 0.0)
            
            print(f"\n  Intent: {intent} (confidence: {confidence:.2f})")
            print(f"  Status: ✓ Success")
            
        except Exception as e:
            print(f"  Status: ✗ Error - {e}")
    
    print(f"\n{'='*70}")
    print("Check run.jsonl for detailed execution logs")
    print('='*70)


if __name__ == "__main__":
    main()

