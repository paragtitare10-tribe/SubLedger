from django.db import models
from django.db.models import Q


class Subscription(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        CANCELED = 'canceled', 'Canceled'

    customer = models.ForeignKey('customers.Customer', on_delete=models.PROTECT, related_name='subscriptions')
    plan = models.ForeignKey('plans.Plan', on_delete=models.PROTECT, related_name='subscriptions')
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)
    start_date = models.DateField()
    current_period_start = models.DateField()
    current_period_end = models.DateField()
    canceled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('customer', 'plan'),
                condition=Q(status='active'),
                name='one_active_subscription_per_customer_plan',
            ),
            models.CheckConstraint(
                condition=Q(current_period_end__gt=models.F('current_period_start')),
                name='subscription_period_has_positive_length',
            ),
        ]
        ordering = ['-start_date', '-id']