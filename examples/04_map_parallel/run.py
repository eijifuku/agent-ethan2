"""Run the map/parallel example."""

from __future__ import annotations

import json
from pathlib import Path

from agent_ethan2.agent import AgentEthan


def main() -> None:
    config_path = Path(__file__).resolve().parent / "config.yaml"
    
    # Initialize agent
    agent = AgentEthan(config_path)
    
    # Example: process a list of items
    items = [
        "apple",
        "banana",
        "cherry",
        "date",
        "elderberry",
    ]
    
    print(f"\n{'='*70}")
    print(f"Processing {len(items)} items...")
    print('='*70)
    
    # Prepare summary prompt
    summary_prompt = f"You processed {len(items)} fruit names. Briefly summarize what was done."
    
    result = agent.run_sync({
        "items": items,
        "summary_prompt": summary_prompt,
    })
    
    print(f"\nResults:")
    results = result.outputs.get("results", [])
    for i, res in enumerate(results):
        if res:
            print(f"  {i+1}. Original: '{res.get('original')}' -> Processed: '{res.get('processed')}' (length: {res.get('length')})")
    
    errors = result.outputs.get("errors", [])
    if errors:
        print(f"\nErrors: {len(errors)}")
        for err in errors:
            print(f"  Index {err.get('index')}: {err.get('error')}")
    
    summary = result.outputs.get("summary", "N/A")
    print(f"\nSummary: {summary}")


if __name__ == "__main__":
    main()

