import uuid
from django.db import models
from django.db.models import BigIntegerField, Case, F, Sum, Value, When
from django.utils import timezone

class Merchant(models.Model):
    name = models.CharField(max_length=128)
    bank_account_id = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def ledger_balance(self):
        total = (
            MerchantLedgerEntry.objects.filter(merchant=self)
            .aggregate(
                total=Sum(
                    Case(
                        When(entry_type=MerchantLedgerEntry.CREDIT, then=F('amount_paise')),
                        When(entry_type=MerchantLedgerEntry.DEBIT, then=F('amount_paise') * Value(-1)),
                        default=Value(0),
                        output_field=BigIntegerField(),
                    )
                )
            )
        )['total']
        return total or 0

    def held_amount(self):
        return (
            Payout.objects.filter(merchant=self, state__in=[Payout.PENDING, Payout.PROCESSING])
            .aggregate(total=Sum('amount_paise'))['total']
            or 0
        )

    def available_balance(self):
        return self.ledger_balance() - self.held_amount()

class MerchantLedgerEntry(models.Model):
    CREDIT = 'CREDIT'
    DEBIT = 'DEBIT'
    ENTRY_TYPE_CHOICES = [
        (CREDIT, 'Credit'),
        (DEBIT, 'Debit'),
    ]

    merchant = models.ForeignKey(Merchant, related_name='ledger_entries', on_delete=models.CASCADE)
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPE_CHOICES)
    amount_paise = models.BigIntegerField()
    description = models.CharField(max_length=256, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

class Payout(models.Model):
    PENDING = 'PENDING'
    PROCESSING = 'PROCESSING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'

    STATE_CHOICES = [
        (PENDING, 'Pending'),
        (PROCESSING, 'Processing'),
        (COMPLETED, 'Completed'),
        (FAILED, 'Failed'),
    ]

    merchant = models.ForeignKey(Merchant, related_name='payouts', on_delete=models.CASCADE)
    amount_paise = models.BigIntegerField()
    bank_account_id = models.CharField(max_length=128)
    state = models.CharField(max_length=16, choices=STATE_CHOICES, default=PENDING)
    idempotency_key = models.UUIDField(default=uuid.uuid4)
    attempts = models.PositiveSmallIntegerField(default=0)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['merchant', 'idempotency_key']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'Payout {self.pk} {self.state} {self.amount_paise}'

    def transition_to(self, new_state):
        legal = {
            self.PENDING: {self.PROCESSING},
            self.PROCESSING: {self.COMPLETED, self.FAILED},
            self.COMPLETED: set(),
            self.FAILED: set(),
        }
        if new_state not in legal[self.state]:
            raise ValueError(f'illegal payout state transition {self.state} -> {new_state}')
        self.state = new_state

    def next_retry_at(self):
        if not self.last_attempt_at:
            return self.created_at
        backoff_seconds = 2 ** max(0, self.attempts - 1)
        return self.last_attempt_at + timezone.timedelta(seconds=backoff_seconds)

    def can_process(self):
        if self.state == self.PENDING:
            return True
        if self.state == self.PROCESSING:
            return timezone.now() >= self.next_retry_at()
        return False
