from rest_framework import serializers

from .models import Invoice


class InvoiceGenerateSchema(serializers.Serializer):
    subscription_id = serializers.IntegerField(min_value=1)
    period_start = serializers.DateField(required=False)
    period_end = serializers.DateField(required=False)
    due_date = serializers.DateField()

    def validate(self, attrs):
        if ('period_start' in attrs) != ('period_end' in attrs):
            raise serializers.ValidationError('Provide both period_start and period_end, or neither.')
        if attrs.get('period_start') and attrs['period_end'] <= attrs['period_start']:
            raise serializers.ValidationError({'period_end': 'Must be after period_start.'})
        return attrs


class InvoiceSchema(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = (
            'id', 'subscription', 'customer', 'amount_due', 'amount_paid', 'currency',
            'status', 'period_start', 'period_end', 'due_date', 'created_at',
        )
        read_only_fields = fields