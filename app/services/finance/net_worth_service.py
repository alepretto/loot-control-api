from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from typing import Optional

from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.finance.account import Account, AccountType, BalanceMode
from app.models.finance.asset_price import AssetPrice
from app.models.finance.credit_card import CreditCard
from app.models.finance.invoice import Invoice, InvoiceStatus
from app.models.finance.liability import Liability
from app.models.finance.net_worth_snapshot import NetWorthSnapshot
from app.models.finance.transaction import Transaction
from app.repositories.finance.net_worth_repository import NetWorthRepository
from app.schemas.finance.net_worth import NetWorthCurrent, NetWorthSnapshotRead


class NetWorthService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = NetWorthRepository(session)
        self.session = session

    async def get_current(self, user_id: uuid.UUID) -> NetWorthCurrent:
        financial_assets = await self._calc_financial_assets(user_id)
        investment_assets = await self._calc_investment_assets(user_id)
        liabilities_credit = await self._calc_liabilities_credit(user_id)
        liabilities_long_term = await self._calc_liabilities_long_term(user_id)
        net_worth = financial_assets + investment_assets - liabilities_credit - liabilities_long_term

        return NetWorthCurrent(
            financial_assets=round(financial_assets, 2),
            investment_assets=round(investment_assets, 2),
            liabilities_credit=round(liabilities_credit, 2),
            liabilities_long_term=round(liabilities_long_term, 2),
            net_worth=round(net_worth, 2),
            calculated_at=datetime.now(UTC),
        )

    async def get_history(self, user_id: uuid.UUID, months: int = 12) -> list[NetWorthSnapshotRead]:
        snapshots = await self.repo.get_history(user_id, months)
        return [NetWorthSnapshotRead.model_validate(s) for s in snapshots]

    async def save_snapshot(self, user_id: uuid.UUID) -> NetWorthSnapshot:
        current = await self.get_current(user_id)
        today = date.today()

        existing_stmt = select(NetWorthSnapshot).where(
            NetWorthSnapshot.user_id == user_id,
            NetWorthSnapshot.date == today,
        )
        existing_result = await self.session.exec(existing_stmt)
        snapshot: Optional[NetWorthSnapshot] = existing_result.first()

        if snapshot:
            snapshot.financial_assets = current.financial_assets
            snapshot.investment_assets = current.investment_assets
            snapshot.liabilities_credit = current.liabilities_credit
            snapshot.liabilities_long_term = current.liabilities_long_term
            snapshot.net_worth = current.net_worth
        else:
            snapshot = NetWorthSnapshot(
                user_id=user_id,
                date=today,
                financial_assets=current.financial_assets,
                investment_assets=current.investment_assets,
                liabilities_credit=current.liabilities_credit,
                liabilities_long_term=current.liabilities_long_term,
                net_worth=current.net_worth,
            )

        return await self.repo.save(snapshot)

    async def _calc_financial_assets(self, user_id: uuid.UUID) -> float:
        # Otimização: Usar uma única query agregada ao invés de N+1
        # Soma manual_balance das contas em modo manual
        manual_stmt = select(func.coalesce(func.sum(Account.manual_balance), 0.0)).where(
            Account.user_id == user_id,
            Account.is_active == True,
            Account.type != AccountType.credit_card,
            Account.balance_mode == BalanceMode.manual,
        )
        manual_result = await self.session.exec(manual_stmt)
        manual_total = float(manual_result.first() or 0.0)
        
        # Soma transactions das contas em modo calculated
        # Subquery para pegar IDs das contas em modo calculated
        calc_accounts_stmt = select(Account.id).where(
            Account.user_id == user_id,
            Account.is_active == True,
            Account.type != AccountType.credit_card,
            Account.balance_mode == BalanceMode.calculated,
        )
        calc_accounts_result = await self.session.exec(calc_accounts_stmt)
        calc_account_ids = [row for row in calc_accounts_result.all()]
        
        calculated_total = 0.0
        if calc_account_ids:
            tx_stmt = select(func.coalesce(func.sum(Transaction.value), 0.0)).where(
                Transaction.account_id.in_(calc_account_ids),
            )
            tx_result = await self.session.exec(tx_stmt)
            calculated_total = float(tx_result.first() or 0.0)
        
        return manual_total + calculated_total

    async def _calc_investment_assets(self, user_id: uuid.UUID) -> float:
        # Otimização: Query única para quantidades por símbolo
        qty_by_symbol_stmt = (
            select(Transaction.symbol, func.coalesce(func.sum(Transaction.quantity), 0.0))
            .where(
                Transaction.user_id == user_id,
                Transaction.symbol.isnot(None),
                Transaction.quantity.isnot(None),
            )
            .group_by(Transaction.symbol)
            .having(func.coalesce(func.sum(Transaction.quantity), 0.0) > 0)
        )
        qty_result = await self.session.exec(qty_by_symbol_stmt)
        symbol_qty_map = {row[0]: float(row[1]) for row in qty_result.all() if row[0]}
        
        if not symbol_qty_map:
            return 0.0
        
        # Buscar últimos preços para todos os símbolos de uma vez
        symbols = list(symbol_qty_map.keys())
        # Usar DISTINCT ON para pegar o preço mais recente de cada símbolo
        latest_prices_stmt = (
            select(
                AssetPrice.symbol,
                AssetPrice.price,
            )
            .distinct(AssetPrice.symbol)
            .where(AssetPrice.symbol.in_(symbols))
            .order_by(AssetPrice.symbol, AssetPrice.date.desc())
        )
        prices_result = await self.session.exec(latest_prices_stmt)
        
        total = 0.0
        for row in prices_result.all():
            symbol = row[0]
            price = float(row[1])
            qty = symbol_qty_map.get(symbol, 0.0)
            total += qty * price
            
        return total

    async def _calc_liabilities_credit(self, user_id: uuid.UUID) -> float:
        stmt = select(func.sum(Invoice.total_amount)).where(
            Invoice.user_id == user_id,
            Invoice.status.in_([InvoiceStatus.open, InvoiceStatus.closed]),
        )
        result = await self.session.exec(stmt)
        return float(result.first() or 0.0)

    async def _calc_liabilities_long_term(self, user_id: uuid.UUID) -> float:
        stmt = select(func.sum(Liability.outstanding_balance)).where(
            Liability.user_id == user_id,
            Liability.is_active == True,
        )
        result = await self.session.exec(stmt)
        return float(result.first() or 0.0)