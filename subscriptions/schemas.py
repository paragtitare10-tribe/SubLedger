from rest_framework import serializers

from .models import Subscription
from .repositories import SubscriptionRepository
from customers.repositories import CustomerRepository
from plans.repositories import PlanRepository


class SubscriptionCreateSchema(serializers.Serializer):
    customer_id = serializers.IntegerField(min_value=1)
    plan_id = serializers.IntegerField(min_value=1)
    start_date = serializers.DateField(required=False)
    current_period_start = serializers.DateField(required=False)
    current_period_end = serializers.DateField(required=False)

    def validate_customer_id(self, value):
        if not CustomerRepository.exists(value):
            raise serializers.ValidationError('Customer does not exist.')
        return value

    def validate_plan_id(self, value):
        if not PlanRepository.exists(value):
            raise serializers.ValidationError('Plan does not exist.')
        return value

    def validate(self, attrs):
        period_start = attrs.get('current_period_start', attrs.get('start_date'))
        period_end = attrs.get('current_period_end')
        if period_start and period_end and period_end <= period_start:
            raise serializers.ValidationError({'current_period_end': 'Must be after the period start.'})
        return attrs


class SubscriptionSchema(serializers.ModelSerializer):
    customer_id = serializers.IntegerField(read_only=True)
    plan_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Subscription
        fields = (
            'id', 'customer_id', 'plan_id', 'status', 'start_date',
            'current_period_start', 'current_period_end', 'canceled_at',
        )
        read_only_fields = fields