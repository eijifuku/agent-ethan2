"""Run the conversation history example."""

from __future__ import annotations

from pathlib import Path

from agent_ethan2.agent import AgentEthan
from agent_ethan2.runtime.history import append_to_history


def main() -> None:
    config_path = Path(__file__).resolve().parent / "config.yaml"
    
    print("\n" + "="*70)
    print("Conversation History Example")
    print("="*70)
    print("\nThis example demonstrates:")
    print("  - Multi-turn conversations with context")
    print("  - Automatic history management")
    print("  - System message for behavior control")
    print("\n" + "="*70 + "\n")
    
    # Initialize agent
    agent = AgentEthan(config_path)
    
    # Conversation history (empty at start)
    chat_history: list[dict[str, str]] = []
    
    # Multi-turn conversation
    conversation = [
        "My name is Alice.",
        "What's my name?",
        "I like Python programming.",
        "What do I like?",
        "Can you summarize what you know about me?",
    ]
    
    for i, user_message in enumerate(conversation, 1):
        print(f"\n{'─'*70}")
        print(f"Turn {i}: User")
        print(f"{'─'*70}")
        print(f"💬 {user_message}")
        
        # Run agent with current history
        result = agent.run_sync({
            "user_message": user_message,
            "chat_history": chat_history,
        })
        
        response = result.outputs.get("response", "")
        
        print(f"\n{'─'*70}")
        print(f"Turn {i}: Assistant")
        print(f"{'─'*70}")
        print(f"🤖 {response}")
        
        # Update conversation history
        chat_history = append_to_history(
            history=chat_history,
            user_message=user_message,
            assistant_message=response,
        )
        
        # Show current history size
        print(f"\n📚 History size: {len(chat_history)} messages")
    
    print("\n" + "="*70)
    print("Full Conversation History")
    print("="*70)
    for msg in chat_history:
        role = msg["role"].upper()
        content = msg["content"]
        print(f"\n{role}: {content}")
    
    print("\n" + "="*70)
    print("✓ Conversation completed successfully!")
    print("="*70)


if __name__ == "__main__":
    main()

