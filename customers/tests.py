from datetime import date
from decimal import Decimal

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from customers.models import Customer
from plans.models import Plan
from subscriptions.services import SubscriptionService


@override_settings(DEBUG=True)
class CustomerAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_normalizes_email_and_supports_list_detail_update(self):
        response = self.client.post('/api/customers/', {
            'name': 'API Customer',
            'email': '  BILLING@EXAMPLE.TEST  ',
        }, format='json')

        self.assertEqual(response.status_code, 201, response.data)
        customer_id = response.data['id']
        self.assertEqual(response.data['email'], 'billing@example.test')

        listing = self.client.get('/api/customers/')
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(len(listing.data), 1)

        detail = self.client.get(f'/api/customers/{customer_id}/')
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data['name'], 'API Customer')

        update = self.client.patch(f'/api/customers/{customer_id}/', {
            'name': 'Updated Customer',
        }, format='json')
        self.assertEqual(update.status_code, 200, update.data)
        self.assertEqual(update.data['name'], 'Updated Customer')

    def test_customer_with_subscription_cannot_be_deleted(self):
        customer = Customer.objects.create(name='Protected customer', email='protected@example.test')
        plan = Plan.objects.create(
            name='Customer protection plan',
            billing_cycle=Plan.BillingCycle.MONTHLY,
            price=Decimal('12.00'),
            currency='USD',
        )
        SubscriptionService.create({
            'customer_id': customer.id,
            'plan_id': plan.id,
            'start_date': date(2025, 1, 1),
        })

        response = self.client.delete(f'/api/customers/{customer.id}/')

        self.assertEqual(response.status_code, 400)
        self.assertTrue(Customer.objects.filter(pk=customer.id).exists())
