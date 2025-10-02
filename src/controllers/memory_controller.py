from ..models.repository_model import RepositoryMetadata
from ..services.memory_service import MemoryService
from datetime import datetime


class MemoryController:
    """conversation controller"""

    def __init__(self, memory_service: MemoryService):
        self.memory_service = memory_service

    async def create_conversation(self, user_id, topic):
        conversation = await self.memory_service.create_converasation(user_id, topic)
        return {
            "conversation_id": conversation.id,
            "user_id": conversation.user_id,
            "topic": conversation.topic,
            "create_date": conversation.created_date.isoformat(),
        }

    async def add_interaction(self, conversation_id, user_message, assistant_response):
        await self.memory_service.add_interaction(
            conversation_id, user_message, assistant_response
        )
        return {
            "conversation_id": conversation_id,
            "status": "added",
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def get_conversation_context(self, conversation_id):
        context = await self.memory_service.get_conversation_context(conversation_id)
        return {"conversation_id": conversation_id, "context": context}
