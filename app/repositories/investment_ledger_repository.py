from uuid import UUID

from sqlmodel import Session, select, text

from app.models.investment_ledger import InvestmentLedger


def get_by_id(session: Session, ledger_id: UUID) -> InvestmentLedger | None:
    return session.get(InvestmentLedger, ledger_id)


def get_all_by_user(session: Session, user_id: UUID) -> list[InvestmentLedger]:
    statement = select(InvestmentLedger).where(InvestmentLedger.user_id == user_id)
    return list(session.exec(statement).all())


def get_by_user_with_relations(session: Session, user_id: UUID) -> list[dict]:
    """
    Returns all investments for user with joined Transaction, Currency,
    Subcategory, and Category data. Used by portfolio aggregation service.
    """
    query = text("""
        SELECT
            il.id, il.symbol, il.quantity, il.currency, il.purchase_exchange_rate,
            il."index", il.index_rate, il.user_id, il.transaction_id,
            il.created_at, il.updated_at,
            t.id as transaction_id, t.amount, t.date_transaction, t.type,
            t.description as transaction_description,
            c.label as currency_label, c.symbol as currency_symbol,
            sc.id as subcategory_id, sc.label as subcategory_label,
            cat.id as category_id, cat.label as category_label, cat.nature as category_nature
        FROM investment_ledger il
        JOIN transactions t ON il.transaction_id = t.id
        JOIN currencies c ON t.currency_id = c.id
        JOIN subcategories sc ON t.subcategory_id = sc.id
        JOIN categories cat ON sc.category_id = cat.id
        WHERE il.user_id = :user_id
    """)
    result = session.exec(query, params={"user_id": str(user_id).replace("-", "")})
    return [dict(row._mapping) for row in result]


def create(session: Session, ledger: InvestmentLedger) -> InvestmentLedger:
    session.add(ledger)
    session.commit()
    session.refresh(ledger)
    return ledger


def update(session: Session, ledger: InvestmentLedger) -> InvestmentLedger:
    session.add(ledger)
    session.commit()
    session.refresh(ledger)
    return ledger


def delete(session: Session, ledger: InvestmentLedger) -> None:
    session.delete(ledger)
    session.commit()
