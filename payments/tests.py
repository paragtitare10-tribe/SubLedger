from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from customers.models import Customer
from invoices.models import Invoice
from invoices.services import InvoiceService
from ledger.models import LedgerEntry
from payments.models import PaymentAttempt
from payments.services import PaymentService
from plans.models import Plan
from subscriptions.models import Subscription
from subscriptions.services import SubscriptionService


class BillingWorkflowTests(TestCase):
    def setUp(self):
        self.plan = Plan.objects.create(
            name='Standard',
            billing_cycle=Plan.BillingCycle.MONTHLY,
            price=Decimal('100.00'),
            currency='USD',
        )
        self.customer = Customer.objects.create(name='Acme', email='billing@acme.test')
        today = timezone.localdate()
        self.subscription = SubscriptionService.create({
            'customer_id': self.customer.id,
            'plan_id': self.plan.id,
            'start_date': today,
        })
        self.invoice = InvoiceService.generate({
            'subscription_id': self.subscription.id,
            'due_date': today + timedelta(days=14),
        })

    def record_payment(self, *, amount, status=PaymentAttempt.Status.SUCCESS, reference=None):
        return PaymentService.record({
            'invoice_id': self.invoice.id,
            'amount': Decimal(amount),
            'currency': 'USD',
            'status': status,
            'provider_reference': reference,
        })

    def test_partial_and_full_payments_update_invoice_and_append_ledger(self):
        self.record_payment(amount='25.00', reference='pay-1')
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, Invoice.Status.PARTIALLY_PAID)
        self.assertEqual(self.invoice.amount_paid, Decimal('25.00'))

        self.record_payment(amount='75.00', reference='pay-2')
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, Invoice.Status.PAID)
        self.assertEqual(self.invoice.amount_paid, Decimal('100.00'))
        self.assertEqual(LedgerEntry.objects.count(), 3)
        self.assertEqual(PaymentAttempt.objects.count(), 2)

    def test_failed_attempt_does_not_change_invoice_or_add_payment_ledger(self):
        self.record_payment(amount='25.00', status=PaymentAttempt.Status.FAILED)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.amount_paid, Decimal('0.00'))
        self.assertEqual(self.invoice.status, Invoice.Status.ISSUED)
        self.assertEqual(LedgerEntry.objects.count(), 1)

    def test_overpayment_is_rejected_without_recording_attempt(self):
        with self.assertRaises(ValidationError):
            self.record_payment(amount='100.01')
        self.assertEqual(PaymentAttempt.objects.count(), 0)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.amount_paid, Decimal('0.00'))

    def test_invoice_generation_rejects_missing_subscription(self):
        with self.assertRaises(ValidationError):
            InvoiceService.generate({'subscription_id': 0, 'due_date': timezone.localdate()})

    def test_invoice_generation_starts_issued_even_when_due_date_is_past(self):
        period_start = self.subscription.current_period_end
        period_end = period_start + timedelta(days=30)
        invoice = InvoiceService.generate({
            'subscription_id': self.subscription.id,
            'period_start': period_start,
            'period_end': period_end,
            'due_date': timezone.localdate() - timedelta(days=1),
        })
        self.assertEqual(invoice.status, Invoice.Status.ISSUED)

    def test_duplicate_active_subscription_and_invoice_are_rejected(self):
        with self.assertRaises(ValidationError):
            SubscriptionService.create({
                'customer_id': self.customer.id,
                'plan_id': self.plan.id,
                'start_date': timezone.localdate(),
            })
        with self.assertRaises(ValidationError):
            InvoiceService.generate({
                'subscription_id': self.subscription.id,
                'due_date': self.invoice.due_date,
            })

        SubscriptionService.cancel(self.subscription)
        replacement = SubscriptionService.create({
            'customer_id': self.customer.id,
            'plan_id': self.plan.id,
            'start_date': timezone.localdate(),
        })
        self.assertEqual(replacement.status, Subscription.Status.ACTIVE)

    def test_ledger_entries_cannot_be_changed_or_deleted(self):
        entry = LedgerEntry.objects.get(entry_type=LedgerEntry.EntryType.CHARGE)
        entry.description = 'rewritten'
        with self.assertRaises(DjangoValidationError):
            entry.save()
        with self.assertRaises(DjangoValidationError):
            entry.delete()
        with self.assertRaises(DjangoValidationError):
            LedgerEntry.objects.filter(pk=entry.pk).update(description='rewritten')

    @override_settings(DEBUG=True)
    def test_api_documentation_routes_are_available(self):
        client = APIClient()
        self.assertEqual(client.get('/api/schema/').status_code, 200)
        self.assertEqual(client.get('/api/docs/').status_code, 200)

    @override_settings(DEBUG=False)
    def test_api_requires_authentication_outside_debug_mode(self):
        response = APIClient().get('/api/plans/')
        self.assertEqual(response.status_code, 401)

    @override_settings(DEBUG=True)
    def test_api_billing_flow(self):
        client = APIClient()
        plan_response = client.post('/api/plans/', {
            'name': 'API plan',
            'billing_cycle': 'monthly',
            'price': '12.50',
            'currency': 'USD',
        }, format='json')
        self.assertEqual(plan_response.status_code, 201, plan_response.data)

        subscription_response = client.post('/api/subscriptions/', {
            'customer_id': self.customer.id,
            'plan_id': plan_response.data['id'],
            'start_date': timezone.localdate().isoformat(),
        }, format='json')
        self.assertEqual(subscription_response.status_code, 201, subscription_response.data)

        invoice_response = client.post('/api/invoices/generate/', {
            'subscription_id': subscription_response.data['id'],
            'due_date': (timezone.localdate() + timedelta(days=14)).isoformat(),
        }, format='json')
        self.assertEqual(invoice_response.status_code, 201, invoice_response.data)

        payment_response = client.post('/api/payments/', {
            'invoice_id': invoice_response.data['id'],
            'amount': '12.50',
            'currency': 'USD',
            'status': 'success',
            'provider_reference': 'api-payment-1',
        }, format='json')
        self.assertEqual(payment_response.status_code, 201, payment_response.data)

        ledger_response = client.get('/api/ledger/')
        self.assertEqual(ledger_response.status_code, 200)
        self.assertEqual(len(ledger_response.data), 3)


class CustomerValidationTests(TestCase):
    @override_settings(DEBUG=True)
    def test_email_is_unique_without_case_sensitivity(self):
        client = APIClient()
        response = client.post('/api/customers/', {
            'name': 'First',
            'email': 'billing@example.test',
        }, format='json')
        self.assertEqual(response.status_code, 201)

        response = client.post('/api/customers/', {
            'name': 'Second',
            'email': 'BILLING@example.test',
        }, format='json')
        self.assertEqual(response.status_code, 400)


@override_settings(DEBUG=True)
class PaymentAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.plan = Plan.objects.create(
            name='Payment API plan',
            billing_cycle=Plan.BillingCycle.MONTHLY,
            price=Decimal('40.00'),
            currency='USD',
        )
        self.customer = Customer.objects.create(name='Payment customer', email='payment-api@example.test')
        self.subscription = SubscriptionService.create({
            'customer_id': self.customer.id,
            'plan_id': self.plan.id,
            'start_date': timezone.localdate(),
        })
        self.invoice = InvoiceService.generate({
            'subscription_id': self.subscription.id,
            'due_date': timezone.localdate() + timedelta(days=14),
        })

    def payment_payload(self, **overrides):
        payload = {
            'invoice_id': self.invoice.id,
            'amount': '10.00',
            'currency': 'USD',
            'status': PaymentAttempt.Status.SUCCESS,
            'provider_reference': 'payment-api-reference',
        }
        payload.update(overrides)
        return payload

    def test_failed_attempt_is_recorded_without_updating_invoice_or_payment_ledger(self):
        response = self.client.post('/api/payments/', self.payment_payload(
            status=PaymentAttempt.Status.FAILED,
            failure_reason='Card declined',
        ), format='json')

        self.assertEqual(response.status_code, 201, response.data)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.amount_paid, Decimal('0.00'))
        self.assertEqual(self.invoice.status, Invoice.Status.ISSUED)
        self.assertEqual(LedgerEntry.objects.filter(invoice=self.invoice).count(), 1)
        self.assertEqual(self.client.get('/api/payments/').status_code, 200)
        self.assertEqual(self.client.get(f'/api/payments/{response.data["id"]}/').status_code, 200)

    def test_currency_mismatch_and_duplicate_provider_reference_are_rejected(self):
        mismatch = self.client.post('/api/payments/', self.payment_payload(currency='EUR'), format='json')
        self.assertEqual(mismatch.status_code, 400)
        self.assertEqual(PaymentAttempt.objects.count(), 0)

        first = self.client.post('/api/payments/', self.payment_payload(), format='json')
        self.assertEqual(first.status_code, 201, first.data)
        duplicate = self.client.post('/api/payments/', self.payment_payload(), format='json')
        self.assertEqual(duplicate.status_code, 400)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.amount_paid, Decimal('10.00'))
        self.assertEqual(PaymentAttempt.objects.count(), 1)
        payment_entry = LedgerEntry.objects.get(entry_type=LedgerEntry.EntryType.PAYMENT)
        self.assertEqual(payment_entry.reference_id, f'payment_attempt:{first.data["id"]}')