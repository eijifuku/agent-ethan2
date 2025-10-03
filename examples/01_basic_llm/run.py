"""Run the basic LLM example end-to-end."""

from __future__ import annotations

import json
from pathlib import Path

from agent_ethan2.agent import AgentEthan


def main() -> None:
    config_path = Path(__file__).resolve().parent / "config.yaml"
    
    # Simple one-liner initialization
    agent = AgentEthan(config_path)
    
    # Synchronous execution
    result = agent.run_sync({"user_prompt": "Summarize the latest AI news."})
    
    print(json.dumps(result.outputs, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
