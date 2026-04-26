import json
import threading
import uuid
from django.db import connection
from django.test import Client, TransactionTestCase
from .models import Merchant, MerchantLedgerEntry, Payout

class PayoutIdempotencyTest(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.merchant = Merchant.objects.create(name='Test Merchant', bank_account_id='BANK-123')
        MerchantLedgerEntry.objects.create(
            merchant=self.merchant,
            entry_type=MerchantLedgerEntry.CREDIT,
            amount_paise=15000,
            description='Seed payment',
        )
        self.client = Client()

    def test_idempotency_key_returns_same_payout(self):
        key = uuid.uuid4()
        payload = {
            'merchant_id': self.merchant.id,
            'amount_paise': 5000,
            'bank_account_id': self.merchant.bank_account_id,
        }
        headers = {'HTTP_IDEMPOTENCY_KEY': str(key)}
        first = self.client.post('/api/v1/payouts/', json.dumps(payload), content_type='application/json', **headers)
        self.assertEqual(first.status_code, 201)
        second = self.client.post('/api/v1/payouts/', json.dumps(payload), content_type='application/json', **headers)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(Payout.objects.filter(merchant=self.merchant, idempotency_key=key).count(), 1)
        self.assertEqual(first.json()['id'], second.json()['id'])

class PayoutConcurrencyTest(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.merchant = Merchant.objects.create(name='Race Merchant', bank_account_id='BANK-456')
        MerchantLedgerEntry.objects.create(
            merchant=self.merchant,
            entry_type=MerchantLedgerEntry.CREDIT,
            amount_paise=10000,
            description='Seed payment',
        )

    def _request_payout(self, amount, responses):
        client = Client()
        payload = {
            'merchant_id': self.merchant.id,
            'amount_paise': amount,
            'bank_account_id': self.merchant.bank_account_id,
        }
        response = client.post(
            '/api/v1/payouts/',
            json.dumps(payload),
            content_type='application/json',
            HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
        )
        responses.append(response)

    def test_concurrent_payouts_do_not_overdraw(self):
        if connection.vendor == 'sqlite':
            self.skipTest('SQLite does not support reliable row-level lock simulation for concurrent requests')

        responses = []
        threads = [
            threading.Thread(target=self._request_payout, args=(6000, responses)),
            threading.Thread(target=self._request_payout, args=(6000, responses)),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(len(responses), 2)
        successful = [r for r in responses if r.status_code == 201]
        failed = [r for r in responses if r.status_code == 400]
        self.assertEqual(len(successful), 1)
        self.assertEqual(len(failed), 1)
        self.assertEqual(Payout.objects.filter(merchant=self.merchant).count(), 1)
