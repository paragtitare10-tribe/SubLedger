from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from customers.models import Customer
from ledger.models import LedgerEntry


@override_settings(DEBUG=True)
class LedgerAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = Customer.objects.create(name='Ledger customer', email='ledger@example.test')
        self.entry = LedgerEntry.objects.create(
            customer=self.customer,
            entry_type=LedgerEntry.EntryType.ADJUSTMENT,
            amount=Decimal('5.00'),
            currency='usd',
            reference_id='adjustment-1',
            description='Test entry',
        )

    def test_list_and_retrieve_entries(self):
        listing = self.client.get('/api/ledger/')
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(len(listing.data), 1)
        self.assertEqual(listing.data[0]['currency'], 'USD')

        detail = self.client.get(f'/api/ledger/{self.entry.id}/')
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data['reference_id'], 'adjustment-1')

    def test_ledger_api_rejects_create_update_and_delete(self):
        payload = {
            'customer': self.customer.id,
            'entry_type': 'adjustment',
            'amount': '1.00',
            'currency': 'USD',
        }
        self.assertEqual(self.client.post('/api/ledger/', payload, format='json').status_code, 405)
        self.assertEqual(
            self.client.patch(f'/api/ledger/{self.entry.id}/', {'description': 'changed'}, format='json').status_code,
            405,
        )
        self.assertEqual(self.client.delete(f'/api/ledger/{self.entry.id}/').status_code, 405)

    def test_ledger_reference_id_cannot_be_empty(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                LedgerEntry.objects.create(
                    customer=self.customer,
                    entry_type=LedgerEntry.EntryType.ADJUSTMENT,
                    amount=Decimal('1.00'),
                    currency='USD',
                    reference_id='',
                )
