# Explainer

## 1. The Ledger
Balance is computed using a database aggregation over ledger entries:

```python
balance = MerchantLedgerEntry.objects.filter(
    merchant=merchant,
    entry_type__in=[MerchantLedgerEntry.CREDIT, MerchantLedgerEntry.DEBIT],
).aggregate(
    total=Sum(
        Case(
            When(entry_type=MerchantLedgerEntry.CREDIT, then=F('amount_paise')),
            When(entry_type=MerchantLedgerEntry.DEBIT, then=F('amount_paise') * Value(-1)),
            default=Value(0),
            output_field=BigIntegerField(),
        )
    )
)['total'] or 0
```

Credits model customer inflows. Debits model only completed bank payouts. That keeps the ledger invariant tight: displayed balance is always `sum(credits) - sum(debits)`.

## 2. The Lock
The payout request code locks the merchant row inside a transaction:

```python
with transaction.atomic():
    merchant = Merchant.objects.select_for_update().get(pk=merchant_id)
```

This uses PostgreSQL row-level locking via `SELECT ... FOR UPDATE` to serialize payout requests for the same merchant.

## 3. The Idempotency
Idempotency is scoped per merchant. The request handler checks for an existing payout with the same `Idempotency-Key` created in the last 24 hours. If found, it returns that payout without creating a duplicate.

If the first request is still in flight, the second request waits on the same merchant lock and sees the created payout after the first transaction commits.

## 4. The State Machine
The `Payout.transition_to` method enforces legal transitions. It rejects invalid moves like `FAILED -> COMPLETED` or `COMPLETED -> PENDING`.

## 5. The AI Audit
AI suggested computing available balance by subtracting the current payout amount from the ledger balance in Python before locking the merchant. That is unsafe under concurrency. I replaced it with a transaction using `select_for_update` and recomputed pending holds inside the lock.
