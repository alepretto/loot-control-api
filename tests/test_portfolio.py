from datetime import date, datetime, timezone

from app.models.account import Account, AccountType
from app.models.asset_price import AssetPrice
from app.models.category import Category, CategoryNature
from app.models.currency import Currency
from app.models.exchange_rate import ExchangeRate
from app.models.investment_ledger import InvestmentLedger
from app.models.subcategory import Subcategory
from app.models.transaction import Transaction


# ============================================================
# Helpers — direct DB inserts (no API coupling)
# ============================================================


def _make_investment_context(session, user_id):
    """Create Category (investment) + Subcategory + Currency + Account.

    Returns dict with category_id, subcategory_id, currency_id, account_id.
    """
    cat = Category(label="Investimentos", nature=CategoryNature.investment, user_id=user_id)
    session.add(cat)
    session.commit()
    session.refresh(cat)

    sub = Subcategory(label="Ações", category_id=cat.id, user_id=user_id)
    session.add(sub)
    session.commit()
    session.refresh(sub)

    currency = Currency(code="BRL", label="Real", symbol="R$")
    session.add(currency)
    session.commit()
    session.refresh(currency)

    account = Account(label="Nubank", type=AccountType.digital, user_id=user_id)
    session.add(account)
    session.commit()
    session.refresh(account)

    return {
        "category_id": cat.id,
        "subcategory_id": sub.id,
        "currency_id": currency.id,
        "account_id": account.id,
    }


def _make_transaction(session, user_id, ctx, amount=3500.0, tx_type="outcome"):
    """Create a Transaction row and return it."""
    tx = Transaction(
        user_id=user_id,
        date_transaction=datetime.now(timezone.utc),
        type=tx_type,
        subcategory_id=ctx["subcategory_id"],
        account_id=ctx["account_id"],
        currency_id=ctx["currency_id"],
        amount=amount,
    )
    session.add(tx)
    session.commit()
    session.refresh(tx)
    return tx


def _make_investment(session, user_id, transaction_id, symbol="PETR4", quantity=100.0,
                     currency="BRL", purchase_exchange_rate=None):
    """Create an InvestmentLedger row and return it."""
    inv = InvestmentLedger(
        user_id=user_id,
        transaction_id=transaction_id,
        symbol=symbol,
        quantity=quantity,
        currency=currency,
        purchase_exchange_rate=purchase_exchange_rate,
    )
    session.add(inv)
    session.commit()
    session.refresh(inv)
    return inv


def _make_asset_price(session, symbol, price, price_date=None, currency="BRL"):
    """Create an AssetPrice row."""
    ap = AssetPrice(
        symbol=symbol,
        price_date=price_date or date.today(),
        price=price,
        currency=currency,
    )
    session.add(ap)
    session.commit()
    session.refresh(ap)
    return ap


def _make_exchange_rate(session, from_currency, to_currency, rate, rate_date=None):
    """Create an ExchangeRate row."""
    er = ExchangeRate(
        from_currency=from_currency,
        to_currency=to_currency,
        rate_date=rate_date or date.today(),
        rate=rate,
    )
    session.add(er)
    session.commit()
    session.refresh(er)
    return er


# ============================================================
# TestGetPortfolioSummary
# ============================================================


class TestGetPortfolioSummary:

    def test_empty_portfolio(self, client, user_headers):
        """User with no investments gets zero totals and empty by_category."""
        response = client.get("/investments/portfolio", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_invested"] == 0.0
        assert data["total_current_value"] == 0.0
        assert data["total_return"] == 0.0
        assert data["total_return_pct"] == 0.0
        assert data["by_category"] == []

    def test_single_brl_investment(self, client, user_headers, session, normal_user):
        """BRL investment: invested=3500, current=3850 (100*38.50), return=350, pct=10%."""
        ctx = _make_investment_context(session, normal_user.id)
        tx = _make_transaction(session, normal_user.id, ctx, amount=3500.0)
        _make_investment(session, normal_user.id, tx.id, symbol="PETR4", quantity=100.0, currency="BRL")
        _make_asset_price(session, "PETR4", 38.50)

        response = client.get("/investments/portfolio", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_invested"] == 3500.0
        assert data["total_current_value"] == 3850.0
        assert data["total_return"] == 350.0
        assert data["total_return_pct"] == 10.0
        assert len(data["by_category"]) == 1
        cat = data["by_category"][0]
        assert cat["category"] == "Investimentos"
        assert cat["total_invested"] == 3500.0
        assert cat["total_current_value"] == 3850.0
        assert len(cat["assets"]) == 1
        asset = cat["assets"][0]
        assert asset["symbol"] == "PETR4"
        assert asset["quantity"] == 100.0
        assert asset["current_price"] == 38.50

    def test_multi_currency(self, client, user_headers, session, normal_user):
        """USD investment converted to BRL via purchase_exchange_rate and current exchange rate."""
        ctx = _make_investment_context(session, normal_user.id)
        # Transaction amount=1500 USD, purchase_exchange_rate=5.00 → invested BRL = 1500*5.00 = 7500
        tx = _make_transaction(session, normal_user.id, ctx, amount=1500.0)
        _make_investment(
            session, normal_user.id, tx.id,
            symbol="AAPL", quantity=10.0, currency="USD",
            purchase_exchange_rate=5.00,
        )
        # Current price: AAPL = 160.00 USD
        _make_asset_price(session, "AAPL", 160.00, currency="USD")
        # Current exchange rate: USD→BRL = 5.25
        _make_exchange_rate(session, "USD", "BRL", 5.25)

        response = client.get("/investments/portfolio", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        # invested = 1500 * 5.00 = 7500
        assert data["total_invested"] == 7500.0
        # current = 10 * 160.00 * 5.25 = 8400
        assert data["total_current_value"] == 8400.0
        # return = 8400 - 7500 = 900
        assert data["total_return"] == 900.0

    def test_unauthorized(self, client):
        """GET /investments/portfolio without auth returns 401."""
        response = client.get("/investments/portfolio")
        assert response.status_code == 401


# ============================================================
# TestGetPortfolioTimeline
# ============================================================


class TestGetPortfolioTimeline:

    def test_timeline_returns_list(self, client, user_headers, session, normal_user):
        """With at least one investment + price, timeline returns non-empty list."""
        ctx = _make_investment_context(session, normal_user.id)
        tx = _make_transaction(session, normal_user.id, ctx, amount=1000.0)
        _make_investment(session, normal_user.id, tx.id, symbol="PETR4", quantity=50.0, currency="BRL")
        _make_asset_price(session, "PETR4", 25.00)

        response = client.get("/investments/portfolio/timeline", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        entry = data[0]
        assert "date" in entry
        assert "cumulative_invested" in entry
        assert "market_value" in entry

    def test_timeline_empty_portfolio(self, client, user_headers):
        """No investments → empty timeline list."""
        response = client.get("/investments/portfolio/timeline", headers=user_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_timeline_unauthorized(self, client):
        """GET /investments/portfolio/timeline without auth returns 401."""
        response = client.get("/investments/portfolio/timeline")
        assert response.status_code == 401