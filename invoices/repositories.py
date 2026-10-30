from .models import Invoice
from subscriptions.models import Subscription


class InvoiceRepository:
    @staticmethod
    def list():
        return Invoice.objects.select_related('customer', 'subscription').all()

    @staticmethod
    def get(invoice_id):
        return Invoice.objects.select_related('customer', 'subscription').get(pk=invoice_id)

    @staticmethod
    def get_for_update(invoice_id):
        return Invoice.objects.select_for_update().select_related('customer').get(pk=invoice_id)

    @staticmethod
    def exists(invoice_id):
        return Invoice.objects.filter(pk=invoice_id).exists()

    @staticmethod
    def get_subscription_for_update(subscription_id):
        return Subscription.objects.select_for_update().select_related('customer', 'plan').get(pk=subscription_id)

    @staticmethod
    def find_for_period(subscription_id, period_start, period_end):
        return Invoice.objects.filter(
            subscription_id=subscription_id,
            period_start=period_start,
            period_end=period_end,
        ).first()

    @staticmethod
    def create(data):
        return Invoice.objects.create(**data)

    @staticmethod
    def save(invoice, **changes):
        for field, value in changes.items():
            setattr(invoice, field, value)
        invoice.save(update_fields=[*changes])
        return invoice