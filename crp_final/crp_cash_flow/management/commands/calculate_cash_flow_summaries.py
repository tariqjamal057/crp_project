import calendar
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.utils import timezone
from company.models import Company
from crp_accounting.models.journal import VoucherLine, Voucher
from crp_cash_flow.models import MonthlyCashFlowSummary

class Command(BaseCommand):
    help = 'Calculates and stores monthly cash flow summaries for all companies.'

    def handle(self, *args, **options):
        companies = Company.objects.all()

        for company in companies:
            self.stdout.write(self.style.HTTP_INFO(f"\nProcessing company: {company.name} (ID: {company.id})"))

            # Identify cash/bank accounts for this company
            cash_bank_accounts = Account.objects.filter(
                company=company,
                account_type=AccountType.ASSET.value,
                account_nature=AccountNature.BANK_CASH.value,
                is_active=True
            )
            if not cash_bank_accounts.exists():
                self.stdout.write(self.style.WARNING(f"  No active cash/bank accounts found for {company.name}. Skipping."))
                continue

            cash_bank_account_ids = list(cash_bank_accounts.values_list('id', flat=True))

            # Calculate for the last 52 months
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=52 * 30)  # Approximation for 52 months

            # Filter voucher lines for the current company, period, and cash/bank accounts
            voucher_lines_in_period = VoucherLine.objects.filter(
                voucher__company=company,
                voucher__voucher_date__range=(start_date, end_date),
                voucher__status=Voucher.TransactionStatus.POSTED.value,
                account_id__in=cash_bank_account_ids
            )

            # Calculate total inflow (debits to cash/bank accounts)
            total_inflow = voucher_lines_in_period.filter(
                dr_cr=VoucherLine.DrCrType.DEBIT.value
            ).aggregate(sum_amount=Sum('amount'))['sum_amount'] or 0

            # Calculate total outflow (credits from cash/bank accounts)
            total_outflow = voucher_lines_in_period.filter(
                dr_cr=VoucherLine.DrCrType.CREDIT.value
            ).aggregate(sum_amount=Sum('amount'))['sum_amount'] or 0

            net_cash_flow = total_inflow - total_outflow

            # Create or update the MonthlyCashFlowSummary
            MonthlyCashFlowSummary.objects.update_or_create(
                company=company,
                year=end_date.year,
                month=end_date.month,
                defaults={
                    'total_inflow': total_inflow,
                    'total_outflow': total_outflow,
                    'net_cash_flow': net_cash_flow
                }
            )

        self.stdout.write(self.style.SUCCESS("\nCash flow summary calculation complete."))
