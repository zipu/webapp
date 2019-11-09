from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, View
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.middleware import csrf

from django.db.models import Sum, Window, F
from trading.models import Asset, Record, CashAccount
from trading.models import FuturesInstrument, FuturesEntry, FuturesExit, FuturesAccount
from trading.models import StockTradeUnit, StockAccount, StockBuy, StockSell, CashAccount
from trading.models import create_record


from datetime import datetime, time
import json
from decimal import Decimal as D
# Create your views here.
class UpdatePriceView(TemplateView):
    def get(self, request, *args, **kwargs):
        stock_codes = list(StockTradeUnit.objects.filter(is_open=True).values_list('code', flat=True))
        futures_codes = list(FuturesEntry.objects.filter(is_open=True).values_list('code', flat=True))
        csrftoken = csrf.get_token(request)
        data={
            'stock': stock_codes,
            'futures': futures_codes,
            'csrftoken': csrftoken
        }
        return JsonResponse(data, safe=False)

    def post(self, request, **kwargs):
        data = json.loads(request.body.decode("utf-8"))
        for code, price in data['stock']:
            trades = StockTradeUnit.objects.filter(is_open=True, code=code).all()
            for trade in trades:
                trade.cur_stock_price = price
                trade.save()
        
        for code, price in data['futures']:
            trades = FuturesEntry.objects.filter(is_open=True, code=code).all()
            for trade in trades:
                trade.current_price = D(str(price))
                trade.save()
        create_record('all')
        return JsonResponse('done', safe=False)


class ChartView(View):
    """ 차트 데이터 반환용 뷰"""
    def get(self, request, *args, **kwargs):
        records = Record.objects.filter(account_symbol=kwargs['account']).order_by('date')
        data = list(records.all().values_list(
            'date', 'value', 'risk_excluded_value','volatility')) 
        return JsonResponse(data, safe=False)


class AssetView(TemplateView):
    template_name = "asset.html"

    def get_context_data(self, **kwargs):
       context = super().get_context_data(**kwargs)
       context['record'] = Record.objects.filter(account_symbol='A').latest('date')
       context['cash'] = CashAccount.objects.all().latest('date').total
       context['stock'] = StockAccount.objects.all().first().principal
       context['futures'] = FuturesAccount.objects.all().aggregate(Sum('principal'))['principal__sum']
       context['activate'] = 'asset'
       return context

class FuturesView(TemplateView):
    template_name = "futures.html"

    def get_context_data(self, **kwargs):
       context = super().get_context_data(**kwargs)
       #context['account'] = FuturesAccount.objects.get(id=kwargs['system'])
       context['account'] = FuturesAccount.objects.all().first()
       context['record'] = Record.objects.filter(account_symbol=context['account'].symbol)\
                            .latest('date')
       context['activate'] = 'futures'
       return context

class FuturesHistoryView(ListView):
   template_name = "futures_history.html"
   model = FuturesEntry
   #queryset = FuturesEntry.objects.filter(system__id=1).order_by('-pk')
   context_object_name = "entries"
   paginate_by = 10

   def get_queryset(self):
       return FuturesAccount.objects.all().first().entries.order_by('-id')

   def get_context_data(self, **kwargs):
       context = super().get_context_data(**kwargs)
       start = int(context['page_obj'].number/10)+1
       end = min(start+10, context['page_obj'].paginator.num_pages+1)
       context['range'] = range(start, end)
       return context

class StockView(TemplateView):
    template_name = "stock.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activate'] = 'stock'
        context['account'] = StockAccount.objects.all().order_by('-id').first()
        context['record'] = Record.objects.filter(account_symbol=context['account'].symbol)\
                            .latest('date')
        return context

class StockHistoryView(ListView):
    template_name = "stock_history.html"
    model = StockTradeUnit
    queryset = StockTradeUnit.objects.all().order_by('-id')
    context_object_name = "trades"
    paginate_by = 10
 
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        start = int(context['page_obj'].number/10)+1
        end = min(start+10, context['page_obj'].paginator.num_pages+1)
        context['range'] = range(start, end)
        return context

class CashView(TemplateView):
    template_name = "cash.html"

    def get_context_data(self, **kwargs):
       context = super().get_context_data(**kwargs)
       #context['account'] = FuturesAccount.objects.get(id=kwargs['system'])
       context['account'] = CashAccount.objects.all().latest('date')
       context['record'] = Record.objects.filter(account_symbol=context['account'].symbol)\
                            .latest('date')
       context['activate'] = 'cash'
       return context