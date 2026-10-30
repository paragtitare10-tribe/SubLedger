from .models import Customer


class CustomerRepository:
    @staticmethod
    def list():
        return Customer.objects.all()

    @staticmethod
    def get(customer_id):
        return Customer.objects.get(pk=customer_id)

    @staticmethod
    def exists(customer_id):
        return Customer.objects.filter(pk=customer_id).exists()

    @staticmethod
    def create(data):
        return Customer.objects.create(**data)

    @staticmethod
    def update(customer, data):
        for field, value in data.items():
            setattr(customer, field, value)
        customer.save()
        return customer

    @staticmethod
    def delete(customer):
        customer.delete()