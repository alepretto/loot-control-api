import uuid

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.agent.memory import AgentMemory
from app.models.agent.message import AgentMessage


class AgentMemoryService:
    async def get_history(
        self, session: AsyncSession, user_id: uuid.UUID, limit: int = 20
    ) -> list[dict]:
        """Returns last `limit` messages ordered by created_at ASC."""
        query = (
            select(AgentMessage)
            .where(AgentMessage.user_id == user_id)
            .order_by(AgentMessage.created_at.desc())
            .limit(limit)
        )
        result = await session.exec(query)
        messages = result.all()
        # Reverse so oldest is first (ASC order for the LLM context window)
        return [{"role": m.role, "content": m.content} for m in reversed(messages)]

    async def save_message(
        self, session: AsyncSession, user_id: uuid.UUID, role: str, content: str
    ) -> None:
        """Save AgentMessage to DB."""
        msg = AgentMessage(user_id=user_id, role=role, content=content)
        session.add(msg)
        await session.commit()

    async def get_memories(
        self, session: AsyncSession, user_id: uuid.UUID
    ) -> list[str]:
        """Returns list of memory content strings."""
        query = (
            select(AgentMemory)
            .where(AgentMemory.user_id == user_id)
            .order_by(AgentMemory.created_at.asc())
        )
        result = await session.exec(query)
        return [m.content for m in result.all()]

    async def save_memory(
        self, session: AsyncSession, user_id: uuid.UUID, content: str
    ) -> None:
        """Save AgentMemory to DB."""
        mem = AgentMemory(user_id=user_id, content=content)
        session.add(mem)
        await session.commit()


agent_memory_service = AgentMemoryService()
