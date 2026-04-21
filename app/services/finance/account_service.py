from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.finance.account import Account, AccountType, BalanceMode
from app.models.finance.asset_price import AssetPrice
from app.models.finance.exchange_rate import ExchangeRate
from app.models.finance.transaction import Currencies, Transaction
from app.repositories.finance.account_repository import AccountRepository
from app.schemas.finance.account import AccountCreate, AccountReadWithBalance, AccountUpdate


class AccountService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = AccountRepository(session)
        self.session = session

    async def create(self, user_id: uuid.UUID, data: AccountCreate) -> Account:
        existing = await self.repo.get_by_name(user_id, data.name)
        if existing:
            raise HTTPException(status_code=409, detail="Conta com esse nome já existe")
        account = Account(user_id=user_id, **data.model_dump())
        return await self.repo.save(account)

    async def get_by_id(self, account_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Account]:
        return await self.repo.get_by_id(account_id, user_id)

    async def list(self, user_id: uuid.UUID, is_active: Optional[bool] = None) -> list[Account]:
        return await self.repo.list(user_id, is_active)

    async def update(
        self, account_id: uuid.UUID, user_id: uuid.UUID, data: AccountUpdate
    ) -> Optional[Account]:
        account = await self.repo.get_by_id(account_id, user_id)
        if not account:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(account, key, value)
        account.updated_at = datetime.now(UTC)
        return await self.repo.save(account)

    async def delete(self, account_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        account = await self.repo.get_by_id(account_id, user_id)
        if not account:
            return False
        if await self.repo.has_transactions(account_id):
            raise HTTPException(
                status_code=409,
                detail="Conta possui transações vinculadas e não pode ser removida",
            )
        await self.repo.delete(account)
        return True

    async def calculate_balance(self, account: Account) -> AccountReadWithBalance:
        balance: Optional[float] = None
        holdings_dict: Optional[dict[str, float]] = None

        if account.balance_mode == BalanceMode.manual:
            balance = account.manual_balance
        elif account.type in (AccountType.wallet, AccountType.broker):
            # For crypto wallets and brokerage accounts, calculate balance using current asset prices
            # Sum quantities by symbol from ALL transactions (ignore value field - it's historical cost)
            stmt = select(
                Transaction.symbol,
                func.sum(Transaction.quantity).label("total_quantity")
            ).where(
                Transaction.account_id == account.id,
                Transaction.symbol.isnot(None),
                Transaction.quantity.isnot(None),
            ).group_by(Transaction.symbol)
            
            result = await self.session.exec(stmt)
            holdings = result.all()
            
            if not holdings:
                # No symbol-based transactions, balance is zero
                balance = 0.0
            else:
                # Calculate total value using current prices and build holdings dict
                total_brl = Decimal("0")
                holdings_dict = {}
                
                for symbol, total_quantity in holdings:
                    if total_quantity is None or symbol is None or total_quantity == 0:
                        continue
                    
                    # Store quantity for debugging
                    holdings_dict[symbol] = float(total_quantity)
                    
                    # Get latest price for this symbol
                    price_stmt = select(AssetPrice).where(
                        AssetPrice.symbol == symbol
                    ).order_by(AssetPrice.date.desc()).limit(1)
                    
                    price_result = await self.session.exec(price_stmt)
                    latest_price = price_result.first()
                    
                    if latest_price:
                        # Convert quantity to BRL using current price
                        qty_decimal = Decimal(str(total_quantity))
                        price_decimal = Decimal(str(latest_price.price))
                        
                        # If price is in USD/EUR, convert to BRL first
                        if latest_price.currency == Currencies.USD:
                            usd_rate_stmt = select(ExchangeRate).where(
                                ExchangeRate.currency == Currencies.USD
                            ).order_by(ExchangeRate.date.desc()).limit(1)
                            usd_rate = (await self.session.exec(usd_rate_stmt)).first()
                            if usd_rate:
                                price_decimal = price_decimal * Decimal(str(usd_rate.rate))
                        elif latest_price.currency == Currencies.EUR:
                            eur_rate_stmt = select(ExchangeRate).where(
                                ExchangeRate.currency == Currencies.EUR
                            ).order_by(ExchangeRate.date.desc()).limit(1)
                            eur_rate = (await self.session.exec(eur_rate_stmt)).first()
                            if eur_rate:
                                price_decimal = price_decimal * Decimal(str(eur_rate.rate))
                        
                        total_brl += qty_decimal * price_decimal
                
                balance = float(total_brl)
        else:
            # Standard accounts: sum transaction values
            stmt = select(func.sum(Transaction.value)).where(
                Transaction.account_id == account.id,
            )
            result = await self.session.exec(stmt)
            balance = float(result.first() or 0.0)

        data = AccountReadWithBalance.model_validate(account)
        data.balance = balance
        if holdings_dict:
            data.holdings = holdings_dict
        # Add statement URL for frontend
        data.statement_url = f"/finance/accounts/{account.id}/statement"
        return data

    async def get_statement(
        self,
        account_id: uuid.UUID,
        user_id: uuid.UUID,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Transaction], int]:
        account = await self.repo.get_by_id(account_id, user_id)
        if not account:
            raise HTTPException(status_code=404, detail="Conta não encontrada")

        stmt = select(Transaction).where(
            Transaction.account_id == account_id,
            Transaction.user_id == user_id,
        )
        if date_from:
            stmt = stmt.where(Transaction.date_transaction >= date_from)
        if date_to:
            stmt = stmt.where(Transaction.date_transaction <= date_to)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.exec(count_stmt)).one()

        items = (
            await self.session.exec(
                stmt.order_by(Transaction.date_transaction.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).all()

        return list(items), total