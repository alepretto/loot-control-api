from uuid import UUID

from sqlmodel import Session

from app.models.investment_ledger import InvestmentLedger
from app.repositories import investment_ledger_repository


def create_investment(
    session: Session,
    user_id: UUID,
    transaction_id: UUID,
    symbol: str,
    quantity: float,
    index: str | None = None,
    index_rate: float | None = None,
) -> InvestmentLedger:
    ledger = InvestmentLedger(
        user_id=user_id,
        transaction_id=transaction_id,
        symbol=symbol,
        quantity=quantity,
        index=index,
        index_rate=index_rate,
    )
    return investment_ledger_repository.create(session, ledger)


def list_investments(session: Session, user_id: UUID) -> list[InvestmentLedger]:
    return investment_ledger_repository.get_all_by_user(session, user_id)


def get_investment_by_id(session: Session, ledger_id: UUID) -> InvestmentLedger:
    ledger = investment_ledger_repository.get_by_id(session, ledger_id)
    if not ledger:
        raise ValueError("Investment not found")
    return ledger


def update_investment(
    session: Session,
    ledger_id: UUID,
    transaction_id: UUID | None = None,
    symbol: str | None = None,
    quantity: float | None = None,
    index: str | None = None,
    index_rate: float | None = None,
) -> InvestmentLedger:
    ledger = investment_ledger_repository.get_by_id(session, ledger_id)
    if not ledger:
        raise ValueError("Investment not found")

    if transaction_id is not None:
        ledger.transaction_id = transaction_id
    if symbol is not None:
        ledger.symbol = symbol
    if quantity is not None:
        ledger.quantity = quantity
    if index is not None:
        ledger.index = index
    if index_rate is not None:
        ledger.index_rate = index_rate

    return investment_ledger_repository.update(session, ledger)


def delete_investment(session: Session, ledger_id: UUID) -> None:
    ledger = investment_ledger_repository.get_by_id(session, ledger_id)
    if not ledger:
        raise ValueError("Investment not found")
    investment_ledger_repository.delete(session, ledger)
