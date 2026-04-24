import calendar
from datetime import datetime
from uuid import UUID

from sqlmodel import Session

from app.models.transaction import Transaction
from app.repositories import transaction_repository
from app.repositories import credit_card_repository
from app.repositories import credit_card_statement_repository


def _get_or_create_current_statement(
    session: Session,
    user_id: UUID,
    credit_card_id: UUID,
) -> UUID:
    """Find the open (unpaid) statement for this card, or create one.

    Raises ValueError if the only existing statement is already paid.
    """
    statements = credit_card_statement_repository.get_by_credit_card(session, credit_card_id)

    # Find open statement
    open_stmt = [s for s in statements if not s.is_paid]
    if open_stmt:
        # Return the most recent open statement
        open_stmt.sort(key=lambda s: s.end_date, reverse=True)
        return open_stmt[0].id

    # If there are statements but all are paid, reject
    if statements:
        raise ValueError("All existing statements for this card are already paid. Create a new statement first.")

    # No statements exist — create one for the current cycle
    card = credit_card_repository.get_by_id(session, credit_card_id)
    if not card:
        raise ValueError("Credit card not found")

    now = datetime.now()
    due_day = card.due_date
    offset = card.end_date_offset
    # Closing date = due_date - end_date_offset
    closing_day = due_day - offset

    # Determine which cycle we're in based on closing day
    if closing_day > 0:
        # e.g. due=4, offset=3 → closing=1
        if now.day <= closing_day:
            # Before closing → current cycle ends this month
            end_date = datetime(now.year, now.month, due_day)
        else:
            # After closing → next cycle
            month = now.month + 1
            year = now.year
            if month > 12:
                month = 1
                year += 1
            end_date = datetime(year, month, due_day)
    else:
        # closing_day <= 0 means offset >= due_day, wrap to previous month
        # e.g. due=4, offset=5 → closing=-1 → last day of prev month
        prev_month = now.month - 1 if now.month > 1 else 12
        prev_year = now.year if now.month > 1 else now.year - 1
        import calendar
        days_in_prev = calendar.monthrange(prev_year, prev_month)[1]
        actual_closing = days_in_prev + closing_day  # e.g. 31 + (-1) = 30

        if now.day <= actual_closing:
            end_date = datetime(now.year, now.month, due_day)
        else:
            month = now.month + 1
            year = now.year
            if month > 12:
                month = 1
                year += 1
            end_date = datetime(year, month, due_day)

    from app.models.credit_card_statement import CreditCardStatement
    statement = CreditCardStatement(
        user_id=user_id,
        credit_card_id=credit_card_id,
        end_date=end_date,
        is_paid=False,
        total_amount=0.0,
    )
    return credit_card_statement_repository.create(session, statement).id


def _recalculate_statement_total(session: Session, statement_id: UUID) -> None:
    """Recalculate the total_amount of a statement based on its transactions."""
    transactions = transaction_repository.get_by_statement_raw(session, statement_id)
    total = sum(t.amount for t in transactions)
    stmt = credit_card_statement_repository.get_by_id(session, statement_id)
    if stmt:
        stmt.total_amount = total
        credit_card_statement_repository.update(session, stmt)


def create_transaction(
    session: Session,
    user_id: UUID,
    date_transaction: datetime,
    type: str,
    subcategory_id: UUID,
    account_id: UUID,
    currency_id: UUID,
    amount: float,
    description: str | None = None,
    payment_methods: str | None = None,
    statement_id: UUID | None = None,
    credit_card_id: UUID | None = None,
) -> Transaction:
    # If payment method is credit, resolve or create statement
    if payment_methods == "credit":
        if credit_card_id:
            # Verify card ownership
            card = credit_card_repository.get_by_id(session, credit_card_id)
            if not card:
                raise ValueError("Credit card not found")
            if card.user_id != user_id:
                raise ValueError("Not authorized to use this credit card")

            # Find or create current statement
            statement_id = _get_or_create_current_statement(session, user_id, credit_card_id)

            # Verify statement is not paid (double check)
            stmt = credit_card_statement_repository.get_by_id(session, statement_id)
            if stmt and stmt.is_paid:
                raise ValueError("Cannot add transactions to a paid statement")

    transaction = Transaction(
        user_id=user_id,
        date_transaction=date_transaction,
        type=type,
        subcategory_id=subcategory_id,
        account_id=account_id,
        currency_id=currency_id,
        amount=amount,
        description=description,
        payment_methods=payment_methods,
        statement_id=statement_id,
    )
    result = transaction_repository.create(session, transaction)

    # Recalculate statement total if linked
    if result.statement_id:
        _recalculate_statement_total(session, result.statement_id)

    return result


def list_transactions(session: Session, user_id: UUID) -> list[Transaction]:
    return transaction_repository.get_all_by_user(session, user_id)


def list_transactions_by_account(
    session: Session, user_id: UUID, account_id: UUID
) -> list[Transaction]:
    return transaction_repository.get_by_account(session, user_id, account_id)


def list_transactions_by_statement(
    session: Session, user_id: UUID, statement_id: UUID
) -> list[Transaction]:
    return transaction_repository.get_by_statement(session, user_id, statement_id)


def get_transaction_by_id(session: Session, transaction_id: UUID) -> Transaction:
    transaction = transaction_repository.get_by_id(session, transaction_id)
    if not transaction:
        raise ValueError("Transaction not found")
    return transaction


def update_transaction(
    session: Session,
    transaction_id: UUID,
    date_transaction: datetime | None = None,
    type: str | None = None,
    subcategory_id: UUID | None = None,
    account_id: UUID | None = None,
    currency_id: UUID | None = None,
    description: str | None = None,
    amount: float | None = None,
    payment_methods: str | None = None,
    statement_id: UUID | None = None,
    credit_card_id: UUID | None = None,
    user_id: UUID | None = None,
) -> Transaction:
    transaction = transaction_repository.get_by_id(session, transaction_id)
    if not transaction:
        raise ValueError("Transaction not found")

    # Track old statement_id for recalculation
    old_statement_id = transaction.statement_id

    # If payment method changed to credit, resolve statement
    if payment_methods == "credit" and credit_card_id and user_id:
        card = credit_card_repository.get_by_id(session, credit_card_id)
        if not card:
            raise ValueError("Credit card not found")
        if card.user_id != user_id:
            raise ValueError("Not authorized to use this credit card")
        statement_id = _get_or_create_current_statement(session, user_id, credit_card_id)
        stmt = credit_card_statement_repository.get_by_id(session, statement_id)
        if stmt and stmt.is_paid:
            raise ValueError("Cannot add transactions to a paid statement")
    elif payment_methods and payment_methods != "credit":
        statement_id = None

    if date_transaction is not None:
        transaction.date_transaction = date_transaction
    if type is not None:
        transaction.type = type
    if subcategory_id is not None:
        transaction.subcategory_id = subcategory_id
    if account_id is not None:
        transaction.account_id = account_id
    if currency_id is not None:
        transaction.currency_id = currency_id
    if description is not None:
        transaction.description = description
    if amount is not None:
        transaction.amount = amount
    if payment_methods is not None:
        transaction.payment_methods = payment_methods
    if statement_id is not None:
        transaction.statement_id = statement_id

    result = transaction_repository.update(session, transaction)

    # Recalculate old statement total (if different)
    if old_statement_id and old_statement_id != result.statement_id:
        _recalculate_statement_total(session, old_statement_id)
    # Recalculate current statement total
    if result.statement_id:
        _recalculate_statement_total(session, result.statement_id)

    return result


def delete_transaction(session: Session, transaction_id: UUID) -> None:
    transaction = transaction_repository.get_by_id(session, transaction_id)
    if not transaction:
        raise ValueError("Transaction not found")
    statement_id = transaction.statement_id
    transaction_repository.delete(session, transaction)
    # Recalculate statement total if was linked
    if statement_id:
        _recalculate_statement_total(session, statement_id)
