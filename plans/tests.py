from datetime import date
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from customers.models import Customer
from plans.models import Plan
from subscriptions.services import SubscriptionService


@override_settings(DEBUG=True)
class PlanAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_list_retrieve_and_update_plan(self):
        response = self.client.post('/api/plans/', {
            'name': 'Standard API plan',
            'billing_cycle': 'monthly',
            'price': '19.99',
            'currency': 'usd',
        }, format='json')

        self.assertEqual(response.status_code, 201, response.data)
        plan_id = response.data['id']
        self.assertEqual(response.data['currency'], 'USD')
        self.assertEqual(response.data['price'], '19.99')

        self.assertEqual(self.client.get('/api/plans/').status_code, 200)
        detail = self.client.get(f'/api/plans/{plan_id}/')
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data['name'], 'Standard API plan')

        update = self.client.patch(f'/api/plans/{plan_id}/', {
            'status': 'inactive',
        }, format='json')
        self.assertEqual(update.status_code, 200, update.data)
        self.assertEqual(update.data['status'], Plan.Status.INACTIVE)

    def test_custom_billing_cycle_requires_description(self):
        response = self.client.post('/api/plans/', {
            'name': 'Custom API plan',
            'billing_cycle': Plan.BillingCycle.CUSTOM,
            'price': '30.00',
            'currency': 'USD',
        }, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('description', response.data)

    def test_plan_price_must_be_positive_at_api_and_database_boundaries(self):
        for price in ('0.00', '-0.01'):
            with self.subTest(price=price):
                response = self.client.post('/api/plans/', {
                    'name': f'Invalid price plan {price}',
                    'billing_cycle': 'monthly',
                    'price': price,
                    'currency': 'USD',
                }, format='json')
                self.assertEqual(response.status_code, 400)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Plan.objects.create(
                    name='Zero price database plan',
                    billing_cycle=Plan.BillingCycle.MONTHLY,
                    price=Decimal('0.00'),
                    currency='USD',
                )

    def test_plan_with_subscription_cannot_be_deleted(self):
        plan = Plan.objects.create(
            name='Subscribed plan',
            billing_cycle=Plan.BillingCycle.MONTHLY,
            price=Decimal('25.00'),
            currency='USD',
        )
        customer = Customer.objects.create(name='Plan customer', email='plan@example.test')
        SubscriptionService.create({
            'customer_id': customer.id,
            'plan_id': plan.id,
            'start_date': date(2025, 1, 1),
        })

        response = self.client.delete(f'/api/plans/{plan.id}/')

        self.assertEqual(response.status_code, 400)
        self.assertTrue(Plan.objects.filter(pk=plan.id).exists())
