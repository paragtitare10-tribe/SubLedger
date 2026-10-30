from decimal import Decimal

from rest_framework import serializers

from .models import Plan


class PlanSchema(serializers.ModelSerializer):
    price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))

    class Meta:
        model = Plan
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_currency(self, value):
        return value.upper()

    def validate(self, attrs):
        cycle = attrs.get('billing_cycle', getattr(self.instance, 'billing_cycle', None))
        description = attrs.get('description', getattr(self.instance, 'description', ''))
        if cycle == Plan.BillingCycle.CUSTOM and not description.strip():
            raise serializers.ValidationError({'description': 'Describe the custom billing cycle.'})
        return attrs