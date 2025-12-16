from django.urls import path
from django.views.generic import RedirectView
from .views import FuturesView, TransactionView, FuturesTradeView, FuturesStatView
from .views import InsightsView, AnalysisView, SettingsView
from .views import StockView, StockHistoryView
from .views import NoteView

# Removed imports: CalculatorView, CFTCView, OptionStrategyView, KiwoomPositionView, LsApiTradeView

urlpatterns = [
    # Redirect root to futures home
    path('', RedirectView.as_view(url='futures/', permanent=False)),

    # Main pages (bottom tab navigation)
    path('futures/', FuturesView.as_view(), name='futures_home'),  # Home dashboard
    path('futures/insights/', InsightsView.as_view(), name='insights'),  # Insights page
    path('futures/analysis/', AnalysisView.as_view(), name='analysis'),  # Analysis page
    path('futures/settings/', SettingsView.as_view(), name='settings'),  # Settings page

    # Auxiliary pages
    path('futures/statdata/', FuturesStatView.as_view(), name='statdata'),  # API endpoint
    path('futures/transaction/<int:page>', TransactionView.as_view(), name='transaction'),
    path('futures/trade/<int:page>', FuturesTradeView.as_view(), name='futurestrade'),
    # path('futures/trades/<int:pk>/', ...) - TODO: Add trade detail view

    # Keep but not in navigation (for future use)
    path('note/<int:page>', NoteView.as_view(), name='note'),
    path('stock/', StockView.as_view(), name='stock'),
    path('stock/history/', StockHistoryView.as_view(), name='stockhistory'),

    # Removed URLs:
    # - futures/ls-api-trade
    # - futures/kiwoom-position
    # - futures/calculator
    # - futures/cftc
    # - futures/opstrat
]

