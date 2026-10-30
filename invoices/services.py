from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from ledger.services import LedgerService
from subscriptions.models import Subscription
from subscriptions.repositories import SubscriptionRepository

from .models import Invoice
from .repositories import InvoiceRepository


class InvoiceService:
    @staticmethod
    @transaction.atomic
    def generate(data):
        data = data.copy()
        try:
            subscription = SubscriptionRepository.get_for_invoice(data['subscription_id'])
        except Subscription.DoesNotExist as error:
            raise ValidationError({'subscription_id': 'Subscription does not exist.'}) from error
        if subscription.status != Subscription.Status.ACTIVE:
            raise ValidationError({'subscription_id': 'Invoices can only be generated for active subscriptions.'})

        period_start = data.get('period_start', subscription.current_period_start)
        period_end = data.get('period_end', subscription.current_period_end)
        existing = InvoiceRepository.find_for_period(subscription.id, period_start, period_end)
        if existing:
            raise ValidationError({'period_start': f'Invoice {existing.id} already exists for this period.'})

        due_date = data['due_date']
        try:
            invoice = InvoiceRepository.create({
                'subscription': subscription,
                'customer': subscription.customer,
                'amount_due': subscription.plan.price,
                'amount_paid': 0,
                'currency': subscription.plan.currency,
                'status': Invoice.Status.ISSUED,
                'period_start': period_start,
                'period_end': period_end,
                'due_date': due_date,
            })
        except IntegrityError as error:
            raise ValidationError('An invoice already exists for this subscription period.') from error

        LedgerService.record_invoice_created(invoice, subscription.id)
        return invoice

    @staticmethod
    @transaction.atomic
    def update_payment_state(invoice, amount):
        total_paid = invoice.amount_paid + amount
        if total_paid > invoice.amount_due:
            raise ValidationError({'amount': 'Payment exceeds the invoice balance.'})
        if total_paid == invoice.amount_due:
            invoice_status = Invoice.Status.PAID
        elif total_paid > 0:
            invoice_status = Invoice.Status.PARTIALLY_PAID
        elif invoice.due_date < timezone.localdate():
            invoice_status = Invoice.Status.OVERDUE
        else:
            invoice_status = Invoice.Status.ISSUED
        return InvoiceRepository.save(
            invoice,
            amount_paid=total_paid,
            status=invoice_status,
        )