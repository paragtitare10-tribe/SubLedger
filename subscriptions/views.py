from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .repositories import SubscriptionRepository
from .schemas import SubscriptionCreateSchema, SubscriptionSchema
from .services import SubscriptionService


class SubscriptionViewSet(viewsets.GenericViewSet):
    serializer_class = SubscriptionSchema

    def get_queryset(self):
        return SubscriptionRepository.list()

    def list(self, request):
        return Response(self.get_serializer(self.get_queryset(), many=True).data)

    def retrieve(self, request, pk=None):
        subscription = self.get_object()
        return Response(self.get_serializer(subscription).data)

    def create(self, request):
        schema = SubscriptionCreateSchema(data=request.data)
        schema.is_valid(raise_exception=True)
        subscription = SubscriptionService.create(schema.validated_data)
        return Response(self.get_serializer(subscription).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        subscription = SubscriptionService.cancel(self.get_object())
        return Response(self.get_serializer(subscription).data)