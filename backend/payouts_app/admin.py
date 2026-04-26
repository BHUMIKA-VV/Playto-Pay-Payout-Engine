from django.contrib import admin
from .models import Merchant, MerchantLedgerEntry, Payout

admin.site.register(Merchant)
admin.site.register(MerchantLedgerEntry)
admin.site.register(Payout)
