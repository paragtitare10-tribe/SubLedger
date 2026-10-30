from datetime import date
from decimal import Decimal

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from customers.models import Customer
from plans.models import Plan
from subscriptions.models import Subscription


@override_settings(DEBUG=True)
class SubscriptionAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = Customer.objects.create(name='API customer', email='subscription@example.test')
        self.plan = Plan.objects.create(
            name='API monthly plan',
            billing_cycle=Plan.BillingCycle.MONTHLY,
            price=Decimal('20.00'),
            currency='USD',
        )

    def create_subscription(self, start_date='2024-01-31'):
        return self.client.post('/api/subscriptions/', {
            'customer_id': self.customer.id,
            'plan_id': self.plan.id,
            'start_date': start_date,
        }, format='json')

    def test_create_calculates_month_end_and_supports_list_detail(self):
        response = self.create_subscription()

        self.assertEqual(response.status_code, 201, response.data)
        subscription_id = response.data['id']
        self.assertEqual(response.data['current_period_start'], '2024-01-31')
        self.assertEqual(response.data['current_period_end'], '2024-02-29')
        self.assertEqual(response.data['status'], Subscription.Status.ACTIVE)

        listing = self.client.get('/api/subscriptions/')
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(len(listing.data), 1)

        detail = self.client.get(f'/api/subscriptions/{subscription_id}/')
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data['plan_id'], self.plan.id)

    def test_inactive_customer_and_plan_are_rejected(self):
        self.customer.status = Customer.Status.INACTIVE
        self.customer.save(update_fields=['status'])
        response = self.create_subscription()
        self.assertEqual(response.status_code, 400)
        self.assertIn('customer_id', response.data)

        self.customer.status = Customer.Status.ACTIVE
        self.customer.save(update_fields=['status'])
        self.plan.status = Plan.Status.INACTIVE
        self.plan.save(update_fields=['status'])
        response = self.create_subscription()
        self.assertEqual(response.status_code, 400)
        self.assertIn('plan_id', response.data)

    def test_duplicate_active_subscription_is_rejected_and_cancel_is_idempotent(self):
        response = self.create_subscription()
        self.assertEqual(response.status_code, 201, response.data)
        subscription_id = response.data['id']

        duplicate = self.create_subscription(start_date='2024-02-01')
        self.assertEqual(duplicate.status_code, 400)

        canceled = self.client.post(f'/api/subscriptions/{subscription_id}/cancel/')
        self.assertEqual(canceled.status_code, 200, canceled.data)
        self.assertEqual(canceled.data['status'], Subscription.Status.CANCELED)
        canceled_at = canceled.data['canceled_at']

        canceled_again = self.client.post(f'/api/subscriptions/{subscription_id}/cancel/')
        self.assertEqual(canceled_again.status_code, 200, canceled_again.data)
        self.assertEqual(canceled_again.data['canceled_at'], canceled_at)
