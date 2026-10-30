from .models import Subscription
from customers.models import Customer
from plans.models import Plan


class SubscriptionRepository:
    @staticmethod
    def list():
        return Subscription.objects.select_related('customer', 'plan').all()

    @staticmethod
    def get(subscription_id):
        return Subscription.objects.select_related('customer', 'plan').get(pk=subscription_id)

    @staticmethod
    def get_for_invoice(subscription_id):
        return Subscription.objects.select_for_update().select_related('customer', 'plan').get(pk=subscription_id)

    @staticmethod
    def exists(subscription_id):
        return Subscription.objects.filter(pk=subscription_id).exists()

    @staticmethod
    def get_customer(customer_id):
        return Customer.objects.get(pk=customer_id)

    @staticmethod
    def get_plan(plan_id):
        return Plan.objects.get(pk=plan_id)

    @staticmethod
    def create(data):
        return Subscription.objects.create(**data)

    @staticmethod
    def save(subscription, **changes):
        for field, value in changes.items():
            setattr(subscription, field, value)
        subscription.save(update_fields=[*changes])
        return subscription