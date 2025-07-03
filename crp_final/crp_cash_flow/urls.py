from django.urls import path
from .views import CashFlowPredictionView

app_name = 'crp_cash_flow'

urlpatterns = [
    path('predict/', CashFlowPredictionView.as_view(), name='cash_flow_prediction'),
]
