from .repositories import CustomerRepository


class CustomerService:
    @staticmethod
    def create(data):
        return CustomerRepository.create(data)

    @staticmethod
    def update(customer, data):
        return CustomerRepository.update(customer, data)

    @staticmethod
    def delete(customer):
        CustomerRepository.delete(customer)