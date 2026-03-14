import json
import uuid
from datetime import UTC, date, datetime

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.bot.memory import agent_memory_service
from app.models.finance.category import Category
from app.models.finance.tag import Tag
from app.models.finance.tag_family import TagFamily
from app.models.finance.transaction import Transaction
from app.schemas.finance.transaction import TransactionFilter
from app.services.finance.summary_service import SummaryService
from app.services.finance.transaction_service import TransactionService

summary_service = SummaryService()

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_monthly_summary",
            "description": (
                "Retorna resumo financeiro do mês: entradas totais, saídas totais, saldo, "
                "saving rate e breakdown por família de gastos. Use quando o usuário perguntar "
                "sobre como foi um mês, quanto gastou, saving rate, etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "month": {"type": "integer", "description": "Mês de 1 a 12"},
                    "year": {
                        "type": "integer",
                        "description": "Ano com 4 dígitos, ex: 2026",
                    },
                },
                "required": ["month", "year"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_transactions",
            "description": (
                "Lista transações recentes. Use quando o usuário quiser ver transações "
                "específicas, filtrar por categoria ou período."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Número de transações a retornar (padrão 10, máximo 50)",
                        "default": 10,
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Data inicial no formato YYYY-MM-DD",
                    },
                    "date_to": {
                        "type": "string",
                        "description": "Data final no formato YYYY-MM-DD",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_asset_performance",
            "description": (
                "Retorna o rendimento dos ativos (ações, crypto, etc.) em um período. "
                "Mostra preço inicial, preço final, variação percentual e valor da posição. "
                "Use quando o usuário perguntar sobre rendimento, performance ou valorização dos investimentos."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date_from": {"type": "string", "description": "Data inicial no formato YYYY-MM-DD"},
                    "date_to": {"type": "string", "description": "Data final no formato YYYY-MM-DD"},
                },
                "required": ["date_from", "date_to"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_memory",
            "description": (
                "Salva uma informação importante sobre o usuário ou suas finanças para lembrar "
                "em conversas futuras. Use quando o usuário mencionar algo relevante como metas, "
                "preferências, contexto de vida, etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "A informação a ser salva de forma clara e concisa",
                    }
                },
                "required": ["content"],
            },
        },
    },
]


async def execute_tool(
    tool_name: str,
    tool_args: dict,
    session: AsyncSession,
    user_id: uuid.UUID,
) -> str:
    """Execute a tool call and return result as JSON string."""
    try:
        if tool_name == "get_monthly_summary":
            result = await summary_service.get_monthly_summary(
                session, user_id, tool_args["month"], tool_args["year"]
            )
            return json.dumps(result, ensure_ascii=False, default=str)

        elif tool_name == "get_recent_transactions":
            limit = min(tool_args.get("limit", 10), 50)
            date_from_str = tool_args.get("date_from")
            date_to_str = tool_args.get("date_to")

            query = (
                select(Transaction, Tag, Category, TagFamily)
                .join(Tag, Transaction.tag_id == Tag.id)
                .join(Category, Tag.category_id == Category.id)
                .outerjoin(TagFamily, Category.family_id == TagFamily.id)
                .where(Transaction.user_id == user_id)
            )
            if date_from_str:
                query = query.where(
                    Transaction.date_transaction >= datetime.fromisoformat(date_from_str).replace(tzinfo=UTC)
                )
            if date_to_str:
                query = query.where(
                    Transaction.date_transaction <= datetime.fromisoformat(date_to_str).replace(hour=23, minute=59, second=59, tzinfo=UTC)
                )
            query = query.order_by(Transaction.date_transaction.desc()).limit(limit)  # type: ignore[union-attr]
            rows = (await session.exec(query)).all()  # type: ignore[call-overload]

            result = {
                "total": len(rows),
                "transactions": [
                    {
                        "date": tx.date_transaction.strftime("%d/%m/%Y %H:%M"),
                        "value": tx.value,
                        "currency": tx.currency.value if hasattr(tx.currency, "value") else str(tx.currency),
                        "type": tag.type.value if hasattr(tag.type, "value") else str(tag.type),
                        "tag": tag.name,
                        "category": cat.name,
                        "family": fam.name if fam else "Sem família",
                    }
                    for tx, tag, cat, fam in rows
                ],
            }
            return json.dumps(result, ensure_ascii=False, default=str)

        elif tool_name == "get_asset_performance":
            date_from = date.fromisoformat(tool_args["date_from"])
            date_to = date.fromisoformat(tool_args["date_to"])
            result = await summary_service.get_asset_performance(session, user_id, date_from, date_to)
            return json.dumps(result, ensure_ascii=False, default=str)

        elif tool_name == "save_memory":
            await agent_memory_service.save_memory(session, user_id, tool_args["content"])
            return json.dumps({"saved": True})

        else:
            return json.dumps({"error": f"Tool {tool_name} not found"})

    except Exception as e:
        return json.dumps({"error": str(e)})
