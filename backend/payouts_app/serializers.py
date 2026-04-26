from rest_framework import serializers
from .models import Merchant, MerchantLedgerEntry, Payout

class MerchantLedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = MerchantLedgerEntry
        fields = ['id', 'entry_type', 'amount_paise', 'description', 'created_at']

class PayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payout
        fields = ['id', 'amount_paise', 'bank_account_id', 'state', 'idempotency_key', 'attempts', 'created_at', 'updated_at']

class PayoutCreateSerializer(serializers.Serializer):
    merchant_id = serializers.IntegerField()
    amount_paise = serializers.IntegerField(min_value=1)
    bank_account_id = serializers.CharField(max_length=128)

class MerchantDashboardSerializer(serializers.Serializer):
    merchant_id = serializers.IntegerField()
    name = serializers.CharField()
    ledger_balance = serializers.IntegerField()
    held_balance = serializers.IntegerField()
    available_balance = serializers.IntegerField()
    recent_ledger_entries = MerchantLedgerEntrySerializer(many=True)
    payout_history = PayoutSerializer(many=True)
