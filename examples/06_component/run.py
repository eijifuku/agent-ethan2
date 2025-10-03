"""Run the custom component example."""

from __future__ import annotations

import json
from pathlib import Path

from agent_ethan2.agent import AgentEthan


def main() -> None:
    config_path = Path(__file__).resolve().parent / "config.yaml"
    
    # Initialize agent
    agent = AgentEthan(config_path)
    
    # Test data
    text = """
    The quick brown fox jumps over the lazy dog.
    Python is a powerful programming language.
    Custom components enable flexible workflows.
    """
    
    numbers = [10, 25, 30, 15, 45, 20, 35]
    
    print("\n" + "="*70)
    print("Custom Component Example")
    print("="*70)
    
    print(f"\nInput Text:")
    print(text.strip())
    
    print(f"\nInput Numbers: {numbers}")
    
    # Run the agent
    result = agent.run_sync({
        "text": text,
        "numbers": numbers,
        "summary_prompt": (
            f"The text analysis shows {result.outputs.get('word_count', 'N/A')} words "
            f"and {result.outputs.get('unique_words', 'N/A')} unique words. "
            f"The numbers have an average of {result.outputs.get('avg', 'N/A')} "
            f"and a sum of {result.outputs.get('sum', 'N/A')}. "
            f"Briefly summarize these statistics."
        ) if False else "Summarize the data processing results in one sentence.",
    })
    
    print(f"\n{'='*70}")
    print("Text Analysis Results:")
    print('='*70)
    print(f"  Word Count: {result.outputs.get('word_count', 'N/A')}")
    print(f"  Character Count: {result.outputs.get('char_count', 'N/A')}")
    print(f"  Unique Words: {result.outputs.get('unique_words', 'N/A')}")
    
    print(f"\n{'='*70}")
    print("Number Aggregation Results:")
    print('='*70)
    print(f"  Sum: {result.outputs.get('sum', 'N/A')}")
    print(f"  Average: {result.outputs.get('avg', 'N/A')}")
    
    print(f"\n{'='*70}")
    print("LLM Summary:")
    print('='*70)
    summary = result.outputs.get('summary', 'N/A')
    print(f"  {summary}")
    
    print(f"\n{'='*70}")


if __name__ == "__main__":
    main()

