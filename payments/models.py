from django.db import models
from django.db.models import Q


class PaymentAttempt(models.Model):
    class Status(models.TextChoices):
        SUCCESS = 'success', 'Success'
        FAILED = 'failed', 'Failed'

    invoice = models.ForeignKey('invoices.Invoice', on_delete=models.PROTECT, related_name='payment_attempts')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3)
    status = models.CharField(max_length=10, choices=Status.choices)
    provider_reference = models.CharField(max_length=160, null=True, blank=True, unique=True)
    failure_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(amount__gt=0), name='payment_amount_positive'),
        ]
        ordering = ['-created_at', '-id']