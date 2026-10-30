from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from customers.models import Customer
from invoices.models import Invoice
from ledger.models import LedgerEntry
from plans.models import Plan
from subscriptions.models import Subscription
from subscriptions.services import SubscriptionService


@override_settings(DEBUG=True)
class InvoiceAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.plan = Plan.objects.create(
            name='Invoice API plan',
            billing_cycle=Plan.BillingCycle.MONTHLY,
            price=Decimal('32.50'),
            currency='USD',
        )
        self.customer = Customer.objects.create(name='Invoice customer', email='invoice@example.test')
        self.subscription = SubscriptionService.create({
            'customer_id': self.customer.id,
            'plan_id': self.plan.id,
            'start_date': timezone.localdate(),
        })

    def generate_invoice(self, **overrides):
        data = {
            'subscription_id': self.subscription.id,
            'due_date': (timezone.localdate() + timedelta(days=14)).isoformat(),
        }
        data.update(overrides)
        return self.client.post('/api/invoices/generate/', data, format='json')

    def test_generate_creates_issued_invoice_and_charge_ledger_entry(self):
        response = self.generate_invoice(due_date=(timezone.localdate() - timedelta(days=1)).isoformat())

        self.assertEqual(response.status_code, 201, response.data)
        invoice_id = response.data['id']
        self.assertEqual(response.data['status'], Invoice.Status.ISSUED)
        self.assertEqual(response.data['amount_due'], '32.50')
        self.assertEqual(response.data['amount_paid'], '0.00')

        entry = LedgerEntry.objects.get(invoice_id=invoice_id)
        self.assertEqual(entry.entry_type, LedgerEntry.EntryType.CHARGE)
        self.assertEqual(entry.amount, Decimal('32.50'))
        self.assertEqual(entry.reference_id, f'invoice:{invoice_id}')

        self.assertEqual(self.client.get('/api/invoices/').status_code, 200)
        detail = self.client.get(f'/api/invoices/{invoice_id}/')
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data['id'], invoice_id)

    def test_missing_inactive_and_duplicate_subscription_invoice_requests_are_rejected(self):
        missing = self.generate_invoice(subscription_id=999999)
        self.assertEqual(missing.status_code, 400)

        SubscriptionService.cancel(self.subscription)
        inactive = self.generate_invoice()
        self.assertEqual(inactive.status_code, 400)

        new_customer = Customer.objects.create(name='Active customer', email='active-invoice@example.test')
        active_subscription = SubscriptionService.create({
            'customer_id': new_customer.id,
            'plan_id': self.plan.id,
            'start_date': timezone.localdate(),
        })
        payload = {
            'subscription_id': active_subscription.id,
            'due_date': (timezone.localdate() + timedelta(days=10)).isoformat(),
        }
        first = self.client.post('/api/invoices/generate/', payload, format='json')
        self.assertEqual(first.status_code, 201, first.data)
        duplicate = self.client.post('/api/invoices/generate/', payload, format='json')
        self.assertEqual(duplicate.status_code, 400)

    def test_period_dates_must_be_provided_together_and_in_order(self):
        start = self.subscription.current_period_start.isoformat()
        end = self.subscription.current_period_end.isoformat()

        missing_end = self.generate_invoice(period_start=start)
        self.assertEqual(missing_end.status_code, 400)

        invalid_order = self.generate_invoice(period_start=end, period_end=start)
        self.assertEqual(invalid_order.status_code, 400)

    def test_invoice_collection_is_read_only_except_generate_action(self):
        self.assertEqual(self.client.post('/api/invoices/', {}, format='json').status_code, 405)
