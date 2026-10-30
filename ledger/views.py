from rest_framework import viewsets

from .schemas import LedgerEntrySchema
from .services import LedgerService


class LedgerEntryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LedgerEntrySchema

    def get_queryset(self):
        return LedgerService.list_entries()