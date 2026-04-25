from uuid import UUID

from sqlmodel import Session, select

from app.models.investment_ledger import InvestmentLedger


def get_by_id(session: Session, ledger_id: UUID) -> InvestmentLedger | None:
    return session.get(InvestmentLedger, ledger_id)


def get_all_by_user(session: Session, user_id: UUID) -> list[InvestmentLedger]:
    statement = select(InvestmentLedger).where(InvestmentLedger.user_id == user_id)
    return list(session.exec(statement).all())


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
