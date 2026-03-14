import json
import logging
import uuid

from sqlmodel.ext.asyncio.session import AsyncSession

from app.bot import llm
from app.bot.memory import agent_memory_service
from app.bot.prompt import build_system_prompt
from app.bot.tools import TOOLS, execute_tool

logger = logging.getLogger(__name__)


async def process_message(
    session: AsyncSession,
    user_id: uuid.UUID,
    user_text: str,
    is_telegram: bool = False,
) -> str:
    history = await agent_memory_service.get_history(session, user_id)
    memories = await agent_memory_service.get_memories(session, user_id)

    system_prompt = build_system_prompt(memories, is_telegram=is_telegram)
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_text})

    await agent_memory_service.save_message(session, user_id, "user", user_text)

    response = await llm.chat_with_tools(messages, TOOLS)

    while response.get("tool_calls"):
        messages.append(response)

        for tool_call in response["tool_calls"]:
            tool_name = tool_call["function"]["name"]
            tool_args = {}
            if tool_call["function"].get("arguments"):
                tool_args = json.loads(tool_call["function"]["arguments"])

            result = await execute_tool(tool_name, tool_args, session, user_id)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": result,
            })

        response = await llm.chat_with_tools(messages, TOOLS)

    final_text = response.get("content", "Não consegui processar sua mensagem.")
    await agent_memory_service.save_message(session, user_id, "assistant", final_text)
    return final_text
