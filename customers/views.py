from django.db.models import ProtectedError
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError

from .repositories import CustomerRepository
from .schemas import CustomerSchema
from .services import CustomerService


class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSchema

    def get_queryset(self):
        return CustomerRepository.list()

    def perform_create(self, serializer):
        serializer.instance = CustomerService.create(serializer.validated_data)

    def perform_update(self, serializer):
        serializer.instance = CustomerService.update(serializer.instance, serializer.validated_data)

    def perform_destroy(self, instance):
        try:
            CustomerService.delete(instance)
        except ProtectedError as error:
            raise ValidationError('A customer with billing records cannot be deleted.') from error