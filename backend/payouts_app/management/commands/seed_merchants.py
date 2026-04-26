from django.core.management.base import BaseCommand
from payouts_app.models import Merchant, MerchantLedgerEntry


class Command(BaseCommand):
    help = 'Seed merchants with sample credit history'

    def handle(self, *args, **options):
        MerchantLedgerEntry.objects.all().delete()
        Merchant.objects.all().delete()

        merchants = [
            Merchant(name='Pixel Studio', bank_account_id='BANK-PIXEL-01'),
            Merchant(name='Growth Agency', bank_account_id='BANK-GROWTH-02'),
            Merchant(name='Freelance India', bank_account_id='BANK-FR-03'),
        ]
        Merchant.objects.bulk_create(merchants)

        entries = []
        for merchant in Merchant.objects.all():
            entries.extend([
                MerchantLedgerEntry(
                    merchant=merchant,
                    entry_type=MerchantLedgerEntry.CREDIT,
                    amount_paise=120000,
                    description='Seed customer payment',
                ),
                MerchantLedgerEntry(
                    merchant=merchant,
                    entry_type=MerchantLedgerEntry.CREDIT,
                    amount_paise=80000,
                    description='Seed customer payment',
                ),
            ])
        MerchantLedgerEntry.objects.bulk_create(entries)
        self.stdout.write(self.style.SUCCESS('Seeded merchants and credit history.'))
