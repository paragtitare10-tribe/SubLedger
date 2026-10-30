from django.db import models
from django.db.models import F, Q


class Invoice(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        ISSUED = 'issued', 'Issued'
        PARTIALLY_PAID = 'partially_paid', 'Partially paid'
        PAID = 'paid', 'Paid'
        OVERDUE = 'overdue', 'Overdue'
        VOID = 'void', 'Void'

    subscription = models.ForeignKey('subscriptions.Subscription', on_delete=models.PROTECT, related_name='invoices')
    customer = models.ForeignKey('customers.Customer', on_delete=models.PROTECT, related_name='invoices')
    amount_due = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ISSUED)
    period_start = models.DateField()
    period_end = models.DateField()
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('subscription', 'period_start', 'period_end'),
                name='one_invoice_per_subscription_period',
            ),
            models.CheckConstraint(condition=Q(amount_due__gte=0), name='invoice_amount_due_nonnegative'),
            models.CheckConstraint(condition=Q(amount_paid__gte=0), name='invoice_amount_paid_nonnegative'),
            models.CheckConstraint(condition=Q(amount_paid__lte=F('amount_due')), name='invoice_paid_not_overdue'),
            models.CheckConstraint(condition=Q(period_end__gt=F('period_start')), name='invoice_period_has_positive_length'),
        ]
        ordering = ['-created_at', '-id']

    def __str__(self):
        return f'Invoice {self.pk}'