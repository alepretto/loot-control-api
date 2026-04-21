from __future__ import annotations

import uuid
from calendar import monthrange
from datetime import UTC, date, datetime
from typing import Optional

from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.finance.credit_card import CreditCard
from app.models.finance.invoice import Invoice, InvoiceStatus
from app.repositories.finance.invoice_repository import InvoiceRepository
from app.schemas.finance.invoice import InvoiceCreate, InvoiceUpdate


class InvoiceService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = InvoiceRepository(session)
        self.session = session

    async def create(self, user_id: uuid.UUID, data: InvoiceCreate) -> Invoice:
        existing = await self.repo.get_by_credit_card_month(data.credit_card_id, data.reference_month)
        if existing:
            raise HTTPException(status_code=409, detail="Já existe uma fatura para esse cartão e mês")
        invoice = Invoice(user_id=user_id, **data.model_dump())
        return await self.repo.save(invoice)

    async def get_by_id(self, invoice_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Invoice]:
        return await self.repo.get_by_id(invoice_id, user_id)

    async def list(
        self,
        user_id: uuid.UUID,
        credit_card_id: Optional[uuid.UUID] = None,
        status: Optional[InvoiceStatus] = None,
    ) -> list[Invoice]:
        return await self.repo.list(user_id, credit_card_id, status)

    async def update(
        self, invoice_id: uuid.UUID, user_id: uuid.UUID, data: InvoiceUpdate
    ) -> Optional[Invoice]:
        invoice = await self.repo.get_by_id(invoice_id, user_id)
        if not invoice:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(invoice, key, value)
        invoice.updated_at = datetime.now(UTC)
        return await self.repo.save(invoice)

    async def delete(self, invoice_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        invoice = await self.repo.get_by_id(invoice_id, user_id)
        if not invoice:
            return False
        await self.repo.delete(invoice)
        return True

    async def pay(
        self,
        invoice_id: uuid.UUID,
        user_id: uuid.UUID,
        payment_account_id: uuid.UUID,
        payment_date: Optional[datetime] = None,
    ) -> Invoice:
        invoice = await self.repo.get_by_id(invoice_id, user_id)
        if not invoice:
            raise HTTPException(status_code=404, detail="Fatura não encontrada")
        if invoice.status == InvoiceStatus.paid:
            raise HTTPException(status_code=409, detail="Fatura já foi paga")
        invoice.status = InvoiceStatus.paid
        invoice.paid_at = payment_date or datetime.now(UTC)
        invoice.updated_at = datetime.now(UTC)
        return await self.repo.save(invoice)

    async def get_current_by_credit_card(
        self, credit_card_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[Invoice]:
        reference_month = date.today().strftime("%Y-%m")
        return await self.repo.get_open_by_credit_card_month(credit_card_id, reference_month)

    async def get_or_create_for_transaction(
        self, credit_card: CreditCard, user_id: uuid.UUID, tx_date: datetime
    ) -> Invoice:
        reference_month = tx_date.strftime("%Y-%m")
        existing = await self.repo.get_open_by_credit_card_month(credit_card.id, reference_month)
        if existing:
            return existing

        year, month = tx_date.year, tx_date.month
        last_day = monthrange(year, month)[1]
        closing_day = credit_card.closing_day
        due_day = credit_card.due_day

        closing_date = date(year, month, min(closing_day, last_day))
        due_date = date(year, month, min(due_day, last_day))

        invoice = Invoice(
            user_id=user_id,
            credit_card_id=credit_card.id,
            reference_month=reference_month,
            closing_date=closing_date,
            due_date=due_date,
            total_amount=0.0,
            status=InvoiceStatus.open,
        )
        return await self.repo.save(invoice)