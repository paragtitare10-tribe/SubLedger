from decimal import Decimal

from rest_framework import serializers

from invoices.repositories import InvoiceRepository

from .models import PaymentAttempt


class PaymentCreateSchema(serializers.Serializer):
    invoice_id = serializers.IntegerField(min_value=1)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))
    currency = serializers.CharField(min_length=3, max_length=3)
    status = serializers.ChoiceField(choices=PaymentAttempt.Status.choices)
    provider_reference = serializers.CharField(max_length=160, required=False, allow_null=True, allow_blank=False)
    failure_reason = serializers.CharField(required=False, allow_blank=True)

    def validate_currency(self, value):
        return value.upper()

    def validate_invoice_id(self, value):
        if not InvoiceRepository.exists(value):
            raise serializers.ValidationError('Invoice does not exist.')
        return value


class PaymentSchema(serializers.ModelSerializer):
    class Meta:
        model = PaymentAttempt
        fields = (
            'id', 'invoice', 'amount', 'currency', 'status', 'provider_reference',
            'failure_reason', 'created_at',
        )
        read_only_fields = fields