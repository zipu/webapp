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
class CreateRecordView(TemplateView):
    """ 수동 레코드 업데이트 """
    def get(self, request, *args, **kwargs):
        create_record('all')
        return JsonResponse('done', safe=False)


class UpdatePriceView(TemplateView):
    def get(self, request, *args, **kwargs):
        stock_codes = list(StockTradeUnit.objects.filter(is_open=True).values_list('code', flat=True))
        futures_codes = list(FuturesEntry.objects.filter(is_open=True).values_list('code', 'instrument__number_system'))
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

# slack 으로 매매내역 요약 전송
class ReportView(TemplateView):
    def get(self, request, *args, **kwargs):
        asset = Record.objects.filter(account_symbol='A').latest('date','id')
        futures = FuturesAccount.objects.all().first()
        stock = StockAccount.objects.all().first()

        data={
            'asset': {
                'principal': int(asset.principal),
                'value': int(asset.value),
                'profit': int(asset.gross_profit),
                'rate_profit': round(float(asset.rate_profit),2)
            },
            'futures': {
                'principal': int(futures.principal),
                'value': int(futures.value),
                'profit': int(futures.gross_profit),
                'risk': int(futures.risk),
                'entries': []
            },
            'stock': {
                'principal': int(stock.principal),
                'value': int(stock.value),
                'profit': int(stock.value - stock.principal),
                'value_stock': int(stock.value_stock),
                'balance': int(stock.balance),
                'risk': int(stock.risk),
                'trades': []
            }
        }

        entries = futures.entries.filter(is_open=True).all()
        for entry in entries:
            e = {
                'name': entry.instrument.name,
                'position': entry.position,
                'contracts': entry.num_open_cons,
                'entry_price': float(entry.entry_price),
                'cur_price': float(entry.current_price),
                'stop_price': float(entry.stop_price),
                'profit': int(entry.current_profit),
                'risk': int(entry.current_risk),
                'remains': (entry.expiration - datetime.today().date()).days
            }
            data['futures']['entries'].append(e)

        trades = stock.trades.filter(is_open=True).all()
        for trade in trades:
            e = {
                'name': trade.name,
                'num': trade.num_hold,
                'amount': int(trade.purchase_amount),
                'buy_price': float(trade.avg_buy_price),
                'cur_price': float(trade.cur_stock_price),
                'stop_price': float(trade.stop_price),
                'profit': int(trade.value_stock),
                'risk': int(trade.risk)
            }
            data['stock']['trades'].append(e)

        return JsonResponse(data, safe=False, json_dumps_params={'ensure_ascii': False})


class ChartView(View):
    """ 차트 데이터 반환용 뷰"""
    def get(self, request, *args, **kwargs):
        records = Record.objects.filter(account_symbol=kwargs['account']).order_by('date','id')
        data = list(records.all().values_list(
            'date', 'value', 'risk_excluded_value','volatility_day', 'volatility', 'principal')) 
        return JsonResponse(data, safe=False)


class AssetView(TemplateView):
    template_name = "asset.html"

    def get_context_data(self, **kwargs):
       context = super().get_context_data(**kwargs)
       context['record'] = Record.objects.filter(account_symbol='A').latest('date', 'id')
       context['cash'] = CashAccount.objects.all().latest('date','id').total
       context['stock'] = StockAccount.objects.all().first().value
       context['futures'] = FuturesAccount.objects.all().aggregate(Sum('value'))['value__sum']
       context['activate'] = 'asset'

       return context

class FuturesView(TemplateView):
    template_name = "futures.html"

    def get_context_data(self, **kwargs):
       context = super().get_context_data(**kwargs)
       context['accounts'] = FuturesAccount.objects.all()
       #context['account'] = FuturesAccount.objects.get(id=kwargs['system'])
       if kwargs['system'] == 0:
           context['account'] = {'id':0, 'account_name': '시스템 합산'}
           record = Record.objects.filter(account_symbol='FA')
           #context['record'] = Record.objects.filter(account_symbol='FA').latest('date','id')
       
       else:
           context['account'] = FuturesAccount.objects.get(id=kwargs['system'])
           record = Record.objects.filter(account_symbol=context['account'].symbol)
           #context['record'] = Record.objects.filter(account_symbol=context['account'].symbol)\
           #                     .latest('date','id')
       context['record'] = record.latest('date','id')
       context['activate'] = 'futures'
       return context

class FuturesHistoryView(ListView):
   template_name = "futures_history.html"
   model = FuturesEntry
   #queryset = FuturesEntry.objects.filter(system__id=1).order_by('-pk')
   context_object_name = "entries"
   paginate_by = 10

   def get_queryset(self):
       return FuturesAccount.objects.get(id=self.kwargs['system']).entries.order_by('-is_open','-exits__date','-date')

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
                            .latest('date','id')
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
       context['account'] = CashAccount.objects.all().latest('date', 'id')
       context['record'] = Record.objects.filter(account_symbol=context['account'].symbol)\
                            .latest('date', 'id')
       context['activate'] = 'cash'
       return context