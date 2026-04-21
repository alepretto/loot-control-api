import uuid
from typing import Optional

from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.finance.invoice import Invoice, InvoiceStatus


class InvoiceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, invoice_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Invoice]:
        stmt = select(Invoice).where(Invoice.id == invoice_id, Invoice.user_id == user_id)
        result = await self.session.exec(stmt)
        return result.first()

    async def get_open_by_credit_card_month(self, credit_card_id: uuid.UUID, reference_month: str) -> Optional[Invoice]:
        stmt = select(Invoice).where(
            Invoice.credit_card_id == credit_card_id,
            Invoice.reference_month == reference_month,
            Invoice.status == InvoiceStatus.open,
        )
        result = await self.session.exec(stmt)
        return result.first()

    async def get_by_credit_card_month(self, credit_card_id: uuid.UUID, reference_month: str) -> Optional[Invoice]:
        stmt = select(Invoice).where(
            Invoice.credit_card_id == credit_card_id,
            Invoice.reference_month == reference_month,
        )
        result = await self.session.exec(stmt)
        return result.first()

    async def list(
        self,
        user_id: uuid.UUID,
        credit_card_id: Optional[uuid.UUID] = None,
        status: Optional[InvoiceStatus] = None,
    ) -> list[Invoice]:
        stmt = select(Invoice).where(Invoice.user_id == user_id)
        if credit_card_id is not None:
            stmt = stmt.where(Invoice.credit_card_id == credit_card_id)
        if status is not None:
            stmt = stmt.where(Invoice.status == status)
        stmt = stmt.order_by(Invoice.reference_month.desc())
        result = await self.session.exec(stmt)
        return list(result.all())

    async def save(self, invoice: Invoice) -> Invoice:
        self.session.add(invoice)
        await self.session.commit()
        await self.session.refresh(invoice)
        return invoice

    async def delete(self, invoice: Invoice) -> None:
        await self.session.delete(invoice)
        await self.session.commit()

    async def get_unpaid_total(self, user_id: uuid.UUID) -> float:
        stmt = select(func.sum(Invoice.total_amount)).where(
            Invoice.user_id == user_id,
            Invoice.status.in_([InvoiceStatus.open, InvoiceStatus.closed]),
        )
        result = await self.session.exec(stmt)
        total = result.first()
        return float(total) if total else 0.0