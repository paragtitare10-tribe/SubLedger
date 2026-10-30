from .models import PaymentAttempt
from invoices.models import Invoice


class PaymentRepository:
    @staticmethod
    def list():
        return PaymentAttempt.objects.select_related('invoice').all()

    @staticmethod
    def create(data):
        return PaymentAttempt.objects.create(**data)

    @staticmethod
    def invoice_for_update(invoice_id):
        return Invoice.objects.select_for_update().get(pk=invoice_id)