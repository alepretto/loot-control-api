from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.finance.payment_method import PaymentMethod, PaymentMethodType
from app.models.finance.credit_card import CreditCard
from app.models.finance.transaction import Transaction
from app.repositories.finance.transaction_repository import TransactionRepository
from app.schemas.finance.transaction import TransactionCreate, TransactionFilter, TransactionUpdate


class TransactionService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = TransactionRepository(session)
        self.session = session

    async def create(self, user_id: uuid.UUID, data: TransactionCreate) -> Transaction:
        tx_data = data.model_dump()

        if not tx_data.get("invoice_id"):
            credit_card = await self._get_credit_card_for_account(data.account_id, user_id)
            if credit_card:
                from app.services.finance.invoice_service import InvoiceService

                invoice = await InvoiceService(self.session).get_or_create_for_transaction(
                    credit_card, user_id, data.date_transaction
                )
                tx_data["invoice_id"] = invoice.id

        transaction = Transaction(user_id=user_id, **tx_data)
        saved = await self.repo.save(transaction)

        if saved.invoice_id:
            await self._update_invoice_total(saved.invoice_id, saved.value)
            await self._update_credit_card_balance(saved.invoice_id, saved.value)

        return saved

    async def _get_credit_card_for_account(
        self, account_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[CreditCard]:
        pm_stmt = select(PaymentMethod).where(
            PaymentMethod.account_id == account_id,
            PaymentMethod.type == PaymentMethodType.credit,
            PaymentMethod.is_active == True,
        )
        pm_result = await self.session.exec(pm_stmt)
        payment_method = pm_result.first()

        if not payment_method:
            return None

        cc_stmt = select(CreditCard).where(
            CreditCard.payment_method_id == payment_method.id,
            CreditCard.user_id == user_id,
            CreditCard.is_active == True,
        )
        cc_result = await self.session.exec(cc_stmt)
        return cc_result.first()

    async def _update_invoice_total(self, invoice_id: uuid.UUID, value: float) -> None:
        from app.models.finance.invoice import Invoice
        stmt = select(Invoice).where(Invoice.id == invoice_id)
        result = await self.session.exec(stmt)
        invoice = result.first()
        if invoice:
            invoice.total_amount += value
            invoice.updated_at = datetime.now(UTC)
            self.session.add(invoice)
            await self.session.commit()

    async def _update_credit_card_balance(self, invoice_id: uuid.UUID, value: float) -> None:
        """Atualiza o saldo atual do cartão de crédito quando uma transação é adicionada."""
        from app.models.finance.invoice import Invoice
        from app.models.finance.credit_card import CreditCard
        
        # Buscar a fatura para obter o credit_card_id
        invoice_stmt = select(Invoice).where(Invoice.id == invoice_id)
        invoice_result = await self.session.exec(invoice_stmt)
        invoice = invoice_result.first()
        
        if invoice and invoice.credit_card_id:
            # Atualizar o saldo do cartão
            cc_stmt = select(CreditCard).where(CreditCard.id == invoice.credit_card_id)
            cc_result = await self.session.exec(cc_stmt)
            credit_card = cc_result.first()
            
            if credit_card:
                credit_card.current_balance += value
                credit_card.updated_at = datetime.now(UTC)
                self.session.add(credit_card)
                await self.session.commit()

    async def get_by_id(
        self, transaction_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[Transaction]:
        return await self.repo.get_by_id(transaction_id, user_id)

    async def list(
        self, user_id: uuid.UUID, filters: TransactionFilter
    ) -> tuple[list[Transaction], int]:
        return await self.repo.list(
            user_id,
            tag_id=filters.tag_id,
            category_id=filters.category_id,
            family_id=filters.family_id,
            nature=filters.nature,
            currency=filters.currency,
            account_id=filters.account_id,
            invoice_id=filters.invoice_id,
            date_from=filters.date_from,
            date_to=filters.date_to,
            page=filters.page,
            page_size=filters.page_size,
        )

    async def update(
        self, transaction_id: uuid.UUID, user_id: uuid.UUID, data: TransactionUpdate
    ) -> Optional[Transaction]:
        transaction = await self.repo.get_by_id(transaction_id, user_id)
        if not transaction:
            return None
        
        # Calcular diferença de valor se estiver sendo alterado
        old_value = transaction.value
        new_value = data.value if data.value is not None else old_value
        value_diff = new_value - old_value
        
        # Guardar invoice_id antigo antes da atualização
        old_invoice_id = transaction.invoice_id
        
        # Se credit_card_id foi fornecido em vez de invoice_id, buscar/criar a fatura
        new_invoice_id = data.invoice_id
        if data.credit_card_id is not None and not data.invoice_id:
            from app.services.finance.invoice_service import InvoiceService
            from app.models.finance.credit_card import CreditCard
            
            cc_stmt = select(CreditCard).where(
                CreditCard.id == data.credit_card_id,
                CreditCard.user_id == user_id
            )
            cc_result = await self.session.exec(cc_stmt)
            credit_card = cc_result.first()
            
            if credit_card:
                date_tx = data.date_transaction or transaction.date_transaction
                invoice = await InvoiceService(self.session).get_or_create_for_transaction(
                    credit_card, user_id, date_tx
                )
                new_invoice_id = invoice.id
        
        # Atualizar campos
        update_data = data.model_dump(exclude_unset=True)
        if new_invoice_id and not data.invoice_id:
            update_data['invoice_id'] = new_invoice_id
        
        # Remover credit_card_id pois não é um campo do modelo Transaction
        update_data.pop('credit_card_id', None)
            
        for key, value in update_data.items():
            setattr(transaction, key, value)
        transaction.updated_at = datetime.now(UTC)
        updated = await self.repo.save(transaction)
        
        # Gerenciar mudança de fatura (invoice_id mudou)
        new_invoice_id_final = transaction.invoice_id
        
        if old_invoice_id != new_invoice_id_final:
            # Se saiu de uma fatura antiga, remover valor da antiga
            if old_invoice_id:
                await self._update_credit_card_balance(old_invoice_id, -old_value)
                await self._update_invoice_total(old_invoice_id, -old_value)
            
            # Se entrou em uma fatura nova, adicionar valor na nova
            if new_invoice_id_final:
                await self._update_credit_card_balance(new_invoice_id_final, new_value)
                await self._update_invoice_total(new_invoice_id_final, new_value)
        else:
            # Mesma fatura, mas valor mudou
            if value_diff != 0 and transaction.invoice_id:
                await self._update_credit_card_balance(transaction.invoice_id, value_diff)
                await self._update_invoice_total(transaction.invoice_id, value_diff)
        
        return updated

    async def delete(self, transaction_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        transaction = await self.repo.get_by_id(transaction_id, user_id)
        if not transaction:
            return False
        
        # Subtrair do saldo do cartão antes de deletar
        if transaction.invoice_id:
            await self._update_credit_card_balance(transaction.invoice_id, -transaction.value)
            await self._update_invoice_total(transaction.invoice_id, -transaction.value)
        
        await self.repo.delete(transaction)
        return True