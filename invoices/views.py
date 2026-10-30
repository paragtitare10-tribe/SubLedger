from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .repositories import InvoiceRepository
from .schemas import InvoiceGenerateSchema, InvoiceSchema
from .services import InvoiceService


class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InvoiceSchema

    def get_queryset(self):
        return InvoiceRepository.list()

    @action(detail=False, methods=['post'], url_path='generate')
    def generate(self, request):
        schema = InvoiceGenerateSchema(data=request.data)
        schema.is_valid(raise_exception=True)
        invoice = InvoiceService.generate(schema.validated_data)
        return Response(self.get_serializer(invoice).data, status=status.HTTP_201_CREATED)