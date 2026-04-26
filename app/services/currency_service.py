from uuid import UUID

from sqlmodel import Session

from app.models.currency import Currency
from app.repositories import currency_repository


def create_currency(
    session: Session,
    code: str,
    label: str,
    symbol: str,
) -> Currency:
    # Check for duplicate code
    existing = currency_repository.get_by_code(session, code)
    if existing:
        raise ValueError(f"Currency with code '{code}' already exists")
    currency = Currency(
        code=code,
        label=label,
        symbol=symbol,
    )
    return currency_repository.create(session, currency)


def list_currencies(session: Session) -> list[Currency]:
    return currency_repository.get_all(session)


def get_currency_by_id(session: Session, currency_id: UUID) -> Currency:
    currency = currency_repository.get_by_id(session, currency_id)
    if not currency:
        raise ValueError("Currency not found")
    return currency


def update_currency(
    session: Session,
    currency_id: UUID,
    code: str | None = None,
    label: str | None = None,
    symbol: str | None = None,
) -> Currency:
    currency = currency_repository.get_by_id(session, currency_id)
    if not currency:
        raise ValueError("Currency not found")

    if code is not None:
        # Check for duplicate code (excluding self)
        existing = currency_repository.get_by_code(session, code)
        if existing and existing.id != currency_id:
            raise ValueError(f"Currency with code '{code}' already exists")
        currency.code = code
    if label is not None:
        currency.label = label
    if symbol is not None:
        currency.symbol = symbol

    return currency_repository.update(session, currency)


def delete_currency(session: Session, currency_id: UUID) -> None:
    currency = currency_repository.get_by_id(session, currency_id)
    if not currency:
        raise ValueError("Currency not found")
    currency_repository.delete(session, currency)


SEED_CURRENCIES: list[dict[str, str]] = [
    {"code": "BRL", "label": "Real", "symbol": "R$"},
    {"code": "USD", "label": "Dólar Americano", "symbol": "$"},
    {"code": "EUR", "label": "Euro", "symbol": "€"},
    {"code": "GBP", "label": "Libra Esterlina", "symbol": "£"},
    {"code": "ARS", "label": "Peso Argentino", "symbol": "$"},
    {"code": "JPY", "label": "Iene Japonês", "symbol": "¥"},
    {"code": "CHF", "label": "Franco Suíço", "symbol": "CHF"},
    {"code": "CAD", "label": "Dólar Canadense", "symbol": "C$"},
    {"code": "AUD", "label": "Dólar Australiano", "symbol": "A$"},
    {"code": "CNY", "label": "Yuan Chinês", "symbol": "¥"},
    {"code": "CLP", "label": "Peso Chileno", "symbol": "$"},
    {"code": "UYU", "label": "Peso Uruguaio", "symbol": "$"},
    {"code": "PYG", "label": "Guarani Paraguaio", "symbol": "₲"},
    {"code": "BOB", "label": "Boliviano", "symbol": "Bs"},
    {"code": "PEN", "label": "Sol Peruano", "symbol": "S/"},
]


def seed_currencies(session: Session) -> int:
    """Insert seed currencies if the table is empty. Returns count of inserted rows."""
    existing = currency_repository.get_all(session)
    if existing:
        return 0  # already seeded

    count = 0
    for data in SEED_CURRENCIES:
        currency = Currency(
            code=data["code"],
            label=data["label"],
            symbol=data["symbol"],
        )
        session.add(currency)
        count += 1

    session.commit()
    return count
