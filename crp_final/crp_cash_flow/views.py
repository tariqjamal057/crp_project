import calendar
from datetime import date, timedelta
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from company.models import Company
from crp_accounting.models.journal import VoucherLine, Voucher
from company.utils import get_current_company  # Import existing models
from .forms import CashFlowPredictionForm

class CashFlowPredictionView(LoginRequiredMixin, View):
    template_name = 'crp_cash_flow/cash_flow_prediction.html'

    def get(self, request, *args, **kwargs):
        company = get_current_company()
        if not company:
            messages.error(request, _("No active company context found. Please select a company."))
            return render(request, self.template_name, {'form': CashFlowPredictionForm(), 'error_message': _("No active company context.")})

        form = CashFlowPredictionForm()
        context = {
            'form': form,
            'company': company,
            'historical_data': [],
            'prediction_data': None,
            'error_message': None,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        company = get_current_company()
        if not company:
            messages.error(request, _("No active company context found. Please select a company."))
            return render(request, self.template_name, {'form': CashFlowPredictionForm(), 'error_message': _("No active company context.")})

        form = CashFlowPredictionForm(request.POST)
        context = {
            'form': form,
            'company': company,
            'historical_data': [],
            'prediction_data': None,
            'error_message': None,
        }

        if form.is_valid():
            time_range = form.cleaned_data['time_range']

            # Determine the date range based on the selected time range
            end_date = timezone.now().date()
            if time_range == 'last_52_months':
                start_date = end_date - timedelta(days=52 * 30)  # Approximation for 52 months
            elif time_range == '5_years':
                start_date = end_date - timedelta(days=5 * 365)  # 5 years
            elif time_range == '1_year':
                start_date = end_date - timedelta(days=365)  # 1 year
            elif time_range == '1_month':
                start_date = end_date - timedelta(days=30)  # 1 month
            elif time_range == '1_week':
                start_date = end_date - timedelta(days=7)  # 1 week
            elif time_range == '1_day':
                start_date = end_date - timedelta(days=1)  # 1 day
            elif time_range == 'custom':
                start_date = form.cleaned_data['custom_start_date']
                end_date = form.cleaned_data['custom_end_date']

            # Fetch voucher lines for the current company and the specified date range
            voucher_lines = VoucherLine.objects.filter(
                voucher__company=company,
                voucher__voucher_date__range=(start_date, end_date),
                voucher__status=Voucher.TransactionStatus.POSTED.value
            )

            # Calculate total inflow (debits to cash/bank accounts)
            total_inflow = voucher_lines.filter(
                dr_cr=VoucherLine.DrCrType.DEBIT.value
            ).aggregate(sum_amount=Sum('amount'))['sum_amount'] or 0

            # Calculate total outflow (credits from cash/bank accounts)
            total_outflow = voucher_lines.filter(
                dr_cr=VoucherLine.DrCrType.CREDIT.value
            ).aggregate(sum_amount=Sum('amount'))['sum_amount'] or 0

            # Prepare prediction data
            context['prediction_data'] = {
                'predicted_inflow': total_inflow,
                'predicted_outflow': total_outflow,
                'predicted_net_flow': total_inflow - total_outflow,
            }

            # Prepare historical data for the selected period
            historical_data_filtered = []
            for summary in voucher_lines:
                summary_date = summary.voucher.voucher_date
                if start_date <= summary_date <= end_date:
                    historical_data_filtered.append(summary)

            context['historical_data'] = historical_data_filtered

            if not historical_data_filtered:
                context['error_message'] = _("No historical data available for the selected period.")

        return render(request, self.template_name, context)
