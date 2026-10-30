from django.db import IntegrityError, transaction
from rest_framework.exceptions import ValidationError

from invoices.services import InvoiceService
from ledger.repositories import LedgerRepository

from .models import PaymentAttempt
from .repositories import PaymentRepository


class PaymentService:
    @staticmethod
    @transaction.atomic
    def record(data):
        data = data.copy()
        invoice_id = data.pop('invoice_id')
        invoice = PaymentRepository.invoice_for_update(invoice_id)
        amount = data['amount']
        if data['currency'].upper() != invoice.currency:
            raise ValidationError({'currency': 'Payment currency must match invoice currency.'})
        if invoice.status in ('paid', 'void', 'draft'):
            raise ValidationError({'invoice_id': 'This invoice cannot accept payments.'})
        data['currency'] = data['currency'].upper()
        data['invoice'] = invoice

        if data['status'] == PaymentAttempt.Status.SUCCESS:
            invoice = InvoiceService.update_payment_state(invoice, amount)
        try:
            attempt = PaymentRepository.create(data)
        except IntegrityError as error:
            raise ValidationError({'provider_reference': 'This provider reference has already been recorded.'}) from error

        if attempt.status == PaymentAttempt.Status.SUCCESS:
            LedgerRepository.create_entry(
                customer=invoice.customer,
                invoice=invoice,
                entry_type='payment',
                amount=attempt.amount,
                currency=attempt.currency,
                reference_id=f'payment_attempt:{attempt.id}',
                description=f'Payment received for invoice {invoice.id}',
            )
        return attempt