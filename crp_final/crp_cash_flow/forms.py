from django import forms
from django.utils.translation import gettext_lazy as _
from datetime import date

class CashFlowPredictionForm(forms.Form):
    """
    Form for users to select a period for cash flow prediction.
    """
    TIME_RANGE_CHOICES = [
        ('last_52_months', _('Last 52 Months')),
        ('5_years', _('Last 5 Years')),
        ('1_year', _('Last 1 Year')),
        ('1_month', _('Last 1 Month')),
        ('1_week', _('Last 1 Week')),
        ('1_day', _('Last 1 Day')),
        ('custom', _('Custom Date Range')),
    ]

    time_range = forms.ChoiceField(
        choices=TIME_RANGE_CHOICES,
        label=_("Select Time Range")
    )

    # Custom date fields for custom range
    custom_start_date = forms.DateField(
        required=False,
        label=_("Custom Start Date"),
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    custom_end_date = forms.DateField(
        required=False,
        label=_("Custom End Date"),
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    def clean(self):
        cleaned_data = super().clean()
        time_range = cleaned_data.get("time_range")
        custom_start_date = cleaned_data.get("custom_start_date")
        custom_end_date = cleaned_data.get("custom_end_date")

        if time_range == 'custom':
            if not custom_start_date or not custom_end_date:
                raise forms.ValidationError(_("Both start and end dates are required for custom range."))
            if custom_start_date > custom_end_date:
                raise forms.ValidationError(_("Start date must be before end date."))

        return cleaned_data
