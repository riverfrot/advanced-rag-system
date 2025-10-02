from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import datetime


@dataclass
class Interaction:
    user_message: str
    assistant_response: str
    search_results: Optional[List[Dict]]
    timestamp: datetime


@dataclass
class Conversation:
    id: str
    user_id: str
    topic: str
    interactions: List[Interaction]
    created_date: datetime
    update_date: datetime
    summary: Optional[str]

    def add_interaction(self, interaction):
        self.interactions.append(interaction)
        self.update_date = datetime.utcnow()

    def compress(self) -> bool:
        return len(self.interactions) > 20

    def get_recent_context(self, max_interactions: int = 5):
        recent = self.interactions[-max_interactions:]
        context_parts = []
        for interaction in recent:
            context_parts.append(f"User: {interaction.user_message}")
            context_parts.append(f"Assistant: {interaction.assistant_response}")
        return "\n".join(context_parts)
