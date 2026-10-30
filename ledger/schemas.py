from rest_framework import serializers

from .models import LedgerEntry


class LedgerEntrySchema(serializers.ModelSerializer):
    class Meta:
        model = LedgerEntry
        fields = (
            'id', 'customer', 'invoice', 'entry_type', 'amount', 'currency',
            'reference_id', 'description', 'created_at',
        )
        read_only_fields = fields