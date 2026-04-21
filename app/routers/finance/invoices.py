import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.models.finance.invoice import InvoiceStatus
from app.schemas.finance.invoice import InvoiceCreate, InvoicePayRequest, InvoiceRead, InvoiceUpdate
from app.services.finance.invoice_service import InvoiceService

router = APIRouter(prefix="/finance/invoices", tags=["invoices"])


@router.post("/", response_model=InvoiceRead, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    data: InvoiceCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    return await InvoiceService(session).create(uuid.UUID(current_user_id), data)


@router.get("/current", response_model=Optional[InvoiceRead])
async def get_current_invoice(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    credit_card_id: uuid.UUID = Query(...),
):
    return await InvoiceService(session).get_current_by_credit_card(credit_card_id, uuid.UUID(current_user_id))


@router.get("/", response_model=List[InvoiceRead])
async def list_invoices(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    credit_card_id: Optional[uuid.UUID] = Query(default=None),
    invoice_status: Optional[InvoiceStatus] = Query(default=None, alias="status"),
):
    return await InvoiceService(session).list(uuid.UUID(current_user_id), credit_card_id, invoice_status)


@router.get("/{invoice_id}", response_model=InvoiceRead)
async def get_invoice(
    invoice_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    invoice = await InvoiceService(session).get_by_id(invoice_id, uuid.UUID(current_user_id))
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fatura não encontrada")
    return invoice


@router.patch("/{invoice_id}", response_model=InvoiceRead)
async def update_invoice(
    invoice_id: uuid.UUID,
    data: InvoiceUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    invoice = await InvoiceService(session).update(invoice_id, uuid.UUID(current_user_id), data)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fatura não encontrada")
    return invoice


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    deleted = await InvoiceService(session).delete(invoice_id, uuid.UUID(current_user_id))
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fatura não encontrada")


@router.post("/{invoice_id}/pay", response_model=InvoiceRead)
async def pay_invoice(
    invoice_id: uuid.UUID,
    data: InvoicePayRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    return await InvoiceService(session).pay(
        invoice_id, uuid.UUID(current_user_id), data.payment_account_id, data.payment_date
    )