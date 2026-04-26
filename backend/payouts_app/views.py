import uuid
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Merchant, MerchantLedgerEntry, Payout
from .serializers import (
    MerchantDashboardSerializer,
    MerchantLedgerEntrySerializer,
    PayoutCreateSerializer,
    PayoutSerializer,
)

class MerchantDashboardView(APIView):
    def get(self, request, merchant_id):
        merchant = Merchant.objects.get(pk=merchant_id)
        data = {
            'merchant_id': merchant.id,
            'name': merchant.name,
            'ledger_balance': merchant.ledger_balance(),
            'held_balance': merchant.held_amount(),
            'available_balance': merchant.available_balance(),
            'recent_ledger_entries': merchant.ledger_entries.all()[:10],
            'payout_history': merchant.payouts.all()[:20],
        }
        serializer = MerchantDashboardSerializer(data)
        return Response(serializer.data)

class PayoutCreateView(APIView):
    def post(self, request):
        serializer = PayoutCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        idempotency_key = request.headers.get('Idempotency-Key')
        if not idempotency_key:
            return Response({'detail': 'Idempotency-Key header required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            idempotency_key = uuid.UUID(idempotency_key)
        except ValueError:
            return Response({'detail': 'Invalid Idempotency-Key UUID'}, status=status.HTTP_400_BAD_REQUEST)

        merchant_id = serializer.validated_data['merchant_id']
        amount_paise = serializer.validated_data['amount_paise']
        bank_account_id = serializer.validated_data['bank_account_id']

        cutoff = timezone.now() - timezone.timedelta(hours=24)
        with transaction.atomic():
            merchant = Merchant.objects.select_for_update().get(pk=merchant_id)
            existing = Payout.objects.filter(
                merchant=merchant,
                idempotency_key=idempotency_key,
                created_at__gte=cutoff,
            ).first()
            if existing:
                return Response(PayoutSerializer(existing).data)

            ledger_balance = merchant.ledger_balance()
            held_balance = merchant.held_amount()
            available_balance = ledger_balance - held_balance
            if amount_paise > available_balance:
                return Response(
                    {'detail': 'Insufficient available balance'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            payout = Payout.objects.create(
                merchant=merchant,
                amount_paise=amount_paise,
                bank_account_id=bank_account_id,
                idempotency_key=idempotency_key,
                state=Payout.PENDING,
            )
            return Response(PayoutSerializer(payout).data, status=status.HTTP_201_CREATED)
