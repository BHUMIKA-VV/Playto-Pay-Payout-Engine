import random
from django.db import transaction
from django.utils import timezone
from huey import crontab
from backend.huey_conf import huey
from .models import MerchantLedgerEntry, Payout

PROCESSING_HANG_RATE = 0.10
PROCESSING_FAIL_RATE = 0.20
PROCESSING_SUCCESS_RATE = 0.70


@huey.periodic_task(crontab(second='*/10'))
def process_pending_payouts():
    for payout in Payout.objects.filter(state__in=[Payout.PENDING, Payout.PROCESSING]):
        if not payout.can_process():
            continue
        _process_single_payout(payout.id)


def _process_single_payout(payout_id):
    with transaction.atomic():
        payout = Payout.objects.select_for_update().get(pk=payout_id)
        if not payout.can_process():
            return

        if payout.state == Payout.PENDING:
            payout.transition_to(Payout.PROCESSING)
        payout.attempts += 1
        payout.last_attempt_at = timezone.now()

        result = random.random()
        if result <= PROCESSING_SUCCESS_RATE:
            payout.transition_to(Payout.COMPLETED)
            MerchantLedgerEntry.objects.create(
                merchant=payout.merchant,
                entry_type=MerchantLedgerEntry.DEBIT,
                amount_paise=payout.amount_paise,
                description=f'Payout {payout.id} completed',
            )
        elif result <= PROCESSING_SUCCESS_RATE + PROCESSING_FAIL_RATE:
            payout.transition_to(Payout.FAILED)
        else:
            payout.state = Payout.PROCESSING

        if payout.attempts >= 3 and payout.state == Payout.PROCESSING:
            payout.transition_to(Payout.FAILED)

        payout.save()
