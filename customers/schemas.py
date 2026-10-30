from rest_framework import serializers

from .models import Customer
from .repositories import CustomerRepository


class CustomerSchema(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'
        read_only_fields = ('id', 'created_at')

    def validate_email(self, value):
        value = value.strip().lower()
        duplicates = CustomerRepository.list().filter(email__iexact=value)
        if self.instance:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError('A customer with this email already exists.')
        return value