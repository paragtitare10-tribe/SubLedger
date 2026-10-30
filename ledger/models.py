from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class LedgerEntryQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError('Ledger entries are append-only.')

    def delete(self):
        raise ValidationError('Ledger entries are append-only.')

    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError('Ledger entries are append-only.')


class LedgerEntry(models.Model):
    class EntryType(models.TextChoices):
        CHARGE = 'charge', 'Charge'
        PAYMENT = 'payment', 'Payment'
        REFUND = 'refund', 'Refund'
        ADJUSTMENT = 'adjustment', 'Adjustment'

    customer = models.ForeignKey('customers.Customer', on_delete=models.PROTECT, related_name='ledger_entries')
    invoice = models.ForeignKey(
        'invoices.Invoice', on_delete=models.PROTECT, related_name='ledger_entries', null=True, blank=True
    )
    entry_type = models.CharField(max_length=12, choices=EntryType.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3)
    reference_id = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = LedgerEntryQuerySet.as_manager()

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(amount__gt=0), name='ledger_entry_amount_positive'),
            models.CheckConstraint(condition=~Q(reference_id=''), name='ledger_reference_id_required'),
        ]
        ordering = ['created_at', 'id']

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError('Ledger entries are append-only.')
        self.currency = self.currency.upper()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Ledger entries are append-only.')