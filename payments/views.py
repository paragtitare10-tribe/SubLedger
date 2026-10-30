from rest_framework import mixins, status, viewsets
from rest_framework.response import Response

from .models import PaymentAttempt
from .repositories import PaymentRepository
from .schemas import PaymentCreateSchema, PaymentSchema
from .services import PaymentService


class PaymentViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = PaymentSchema
    queryset = PaymentAttempt.objects.none()

    def get_queryset(self):
        return PaymentRepository.list()

    def create(self, request):
        schema = PaymentCreateSchema(data=request.data)
        schema.is_valid(raise_exception=True)
        attempt = PaymentService.record(schema.validated_data)
        return Response(self.get_serializer(attempt).data, status=status.HTTP_201_CREATED)