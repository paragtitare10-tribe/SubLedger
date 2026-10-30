from .models import LedgerEntry


class LedgerRepository:
    @staticmethod
    def list():
        return LedgerEntry.objects.select_related('customer', 'invoice').all()

    @staticmethod
    def create_entry(**data):
        return LedgerEntry.objects.create(**data)