import calendar
from datetime import date, timedelta
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.db.models import Sum
from company.models import Company
from crp_accounting.models.journal import VoucherLine, Voucher
from company.utils import get_current_company  # Import existing models
from .forms import CashFlowPredictionForm
import requests
import json

class CashFlowPredictionView(LoginRequiredMixin, View):
    template_name = 'crp_cash_flow/cash_flow_prediction.html'

    def get(self, request, *args, **kwargs):
        form = CashFlowPredictionForm()
        context = {
            'form': form,
            'historical_data': [],
            'prediction_data': None,
            'error_message': None,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = CashFlowPredictionForm(request.POST)
        context = {
            'form': form,
            'historical_data': [],
            'prediction_data': None,
            'error_message': None,
        }

        if form.is_valid():
            company = form.cleaned_data['company']
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

            # Fetch voucher lines for the selected company and the specified date range
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

            # Prepare historical data for the selected period
            historical_data_filtered = []
            for summary in voucher_lines:
                summary_date = summary.voucher.voucher_date
                if start_date <= summary_date <= end_date:
                    historical_data_filtered.append(summary)

            context['historical_data'] = historical_data_filtered
            context['company'] = company

            if not historical_data_filtered:
                context['error_message'] = _("No historical data available for the selected period.")
            else:
                # Prepare data for AI prediction
                historical_cash_flows = []
                for voucher_line in voucher_lines:
                    # For cash flow, we consider DEBIT as inflow (positive) and CREDIT as outflow (negative)
                    amount = voucher_line.amount if voucher_line.dr_cr == VoucherLine.DrCrType.DEBIT.value else -voucher_line.amount
                    historical_cash_flows.append({
                        'date': voucher_line.voucher.voucher_date.isoformat(),
                        'amount': float(amount)
                    })

                # Sort by date
                historical_cash_flows.sort(key=lambda x: x['date'])

                # Get prediction from Ollama
                prediction = self.get_ollama_prediction(historical_cash_flows, company.name)
                
                if prediction:
                    context['prediction_data'] = {
                        'predicted_inflow': total_inflow,
                        'predicted_outflow': total_outflow,
                        'predicted_net_flow': total_inflow - total_outflow,
                        'ai_prediction': prediction
                    }
                else:
                    # Fallback to simple prediction if AI fails
                    context['prediction_data'] = {
                        'predicted_inflow': total_inflow,
                        'predicted_outflow': total_outflow,
                        'predicted_net_flow': total_inflow - total_outflow,
                        'ai_prediction': {
                            'message': _("AI prediction failed. Using simple calculation based on historical average."),
                            'predicted_inflow': total_inflow,
                            'predicted_outflow': total_outflow,
                            'predicted_net_flow': total_inflow - total_outflow
                        }
                    }

        return render(request, self.template_name, context)

    def get_ollama_prediction(self, historical_data, company_name):
        """
        Get cash flow prediction from Ollama AI model
        """
        try:
            # Prepare the prompt for the AI model
            prompt = f"""
            Analyze the following cash flow data for {company_name} and predict the next 3 months of cash flow patterns.
            Historical data (date, amount): {historical_data}
            
            Please provide:
            1. Predicted cash inflow for the next 3 months
            2. Predicted cash outflow for the next 3 months
            3. Predicted net cash flow for the next 3 months
            4. Key factors influencing these predictions
            5. Recommendations for cash flow management
            
            Format your response as JSON with the following structure:
            {{
                "predicted_inflow": number,
                "predicted_outflow": number,
                "predicted_net_flow": number,
                "factors": ["factor1", "factor2", ...],
                "recommendations": ["recommendation1", "recommendation2", ...]
            }}
            """
            
            # Send request to Ollama
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': 'llama2',
                    'prompt': prompt,
                    'stream': False,
                    'temperature': 0.7,
                    'max_tokens': 1000
                },
                timeout=60  # Add timeout to prevent hanging
            )
            
            if response.status_code == 200:
                response_data = response.json()
                # Try to parse the response as JSON
                try:
                    # Extract the response text from Ollama's response format
                    response_text = response_data.get('response', '{}')
                    # Clean up the response text to make it valid JSON
                    # Remove any markdown code block markers if present
                    response_text = response_text.replace('```json', '').replace('```', '').strip()
                    prediction = json.loads(response_text)
                    return prediction
                except json.JSONDecodeError:
                    # If parsing fails, return the raw response
                    return {
                        'raw_response': response_data.get('response', 'No response from AI model')
                    }
            else:
                print(f"Ollama API error: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            # Log the error for debugging
            print(f"Error connecting to Ollama: {e}")
            return None
        except Exception as e:
            # Log any other unexpected errors
            print(f"Unexpected error getting prediction from Ollama: {e}")
            return None
