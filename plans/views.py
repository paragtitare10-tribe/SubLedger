from django.db.models import ProtectedError
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError

from .repositories import PlanRepository
from .schemas import PlanSchema
from .services import PlanService


class PlanViewSet(viewsets.ModelViewSet):
    serializer_class = PlanSchema

    def get_queryset(self):
        return PlanRepository.list()

    def perform_create(self, serializer):
        serializer.instance = PlanService.create(serializer.validated_data)

    def perform_update(self, serializer):
        serializer.instance = PlanService.update(serializer.instance, serializer.validated_data)

    def perform_destroy(self, instance):
        try:
            PlanService.delete(instance)
        except ProtectedError as error:
            raise ValidationError('A plan with subscriptions cannot be deleted.') from error