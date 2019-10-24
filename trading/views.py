from django.shortcuts import render, redirect
from django.views.generic import TemplateView

from trading.models import Instrument
# Create your views here.

class RecordView(TemplateView):
    template_name = "trading.html"
    
    """
    def get_context_data(self, **kwargs):
       context = super().get_context_data(**kwargs)
       context['activate'] = 'asset'
       context['cash'] = Cash.objects.all()
       context['equity'] = Stock.objects.all()
       context['futures'] = Futures.objects.all()
       cash = Cash.objects.latest('id').total if Cash.objects.count() else 0
       equity = Stock.objects.latest('id').total if Stock.objects.count() else 0
       futures = Futures.objects.latest('id').total if Futures.objects.count() else 0
       context['total'] = cash+equity+futures

       return context
    """
