from typing import Optional, Dict, List
import uuid
from models.memory_models import Conversation, Interaction
from infrastructure.memory.conversation_store import ConversationStore


class MemoryService:
    def __init__(self, conversation_store: ConversationStore):
        self.store = conversation_store

    async def create_converasation(self, user_id, topic):
        conversation = Conversation(id=str(uuid.uuid4()), user_id=user_id, topic=topic)
        await self.store.save(conversation)
        return conversation

    async def add_interaction(
        self,
        conversation_id: str,
        user_message: str,
        assistant_resposne: str,
        search_results: Optional[List[Dict]],
    ):

        conversation = await self.store.get(conversation_id)

        interaction = Interaction(
            user_message=user_message,
            assistant_response=assistant_resposne,
            search_results=search_results,
        )

        conversation.add_interaction(interaction)

        if conversation.compress():
            if len(conversation.interactions) > 10:
                # 10개 이상일때 대화 압축
                old_interactions = conversation.interactions[:-5]  # 최근 5개만 제외
                summary_text = self._create_simple_summary(old_interactions)

                conversation.summary = summary_text
                conversation.interactions = conversation.interactions[-5:]

        conversation.add_interaction(interaction)

        await self.store.save(conversation)

    async def get_conversation_context(self, conversation_id):
        conversation = await self.store.get(conversation_id)
        return conversation.get_recent_context()

    def _create_simple_summary(self, interactions):
        topics = []
        for inter in interactions:
            words = inter.user_message.split()
            important_words = [w for w in words if len(w) > 4]
            topics.extend(important_words[:3])

        unique = list(set(topics))[:10]
        return f"Previous discussion topics: {', '.join(unique)}"
