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
