from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class Plan(models.Model):
    class BillingCycle(models.TextChoices):
        MONTHLY = 'monthly', 'Monthly'
        QUARTERLY = 'quarterly', 'Quarterly'
        YEARLY = 'yearly', 'Yearly'
        CUSTOM = 'custom', 'Custom'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'

    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    billing_cycle = models.CharField(max_length=20, choices=BillingCycle.choices)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(price__gt=0), name='plan_price_positive'),
        ]
        ordering = ['name']

    def clean(self):
        if self.billing_cycle == self.BillingCycle.CUSTOM and not self.description.strip():
            raise ValidationError({'description': 'Describe the custom billing cycle.'})
        self.currency = self.currency.upper()

    def __str__(self):
        return self.name