from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, View
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.middleware import csrf

from django.db.models import Sum, Window, F
from trading.models import Instrument, FuturesEntry, FuturesExit, FuturesSystem, FuturesTrackRecord
from trading.models import StockSummary, StockStatement, StockBuy, StockSell

from datetime import datetime, time
import json
# Create your views here.

class FuturesView(TemplateView):
    template_name = "futures.html"

    def get_context_data(self, **kwargs):
       context = super().get_context_data(**kwargs)
       context['system'] = FuturesTrackRecord.objects.filter(system__id=self.kwargs['system']).first()
       context['activate'] = 'futures'
       return context

class FuturesHistoryView(ListView):
   template_name = "futures_history.html"
   model = FuturesEntry
   #queryset = FuturesEntry.objects.filter(system__id=1).order_by('-pk')
   context_object_name = "entries"
   paginate_by = 10

   def get_queryset(self):
       return FuturesSystem.objects.get(id=self.kwargs['system']).entries.order_by('-id')

   def get_context_data(self, **kwargs):
       context = super().get_context_data(**kwargs)
       start = int(context['page_obj'].number/10)+1
       end = min(start+10, context['page_obj'].paginator.num_pages+1)
       context['range'] = range(start, end)
       return context

class FuturesChartView(View):
    """ 차트 데이터 반환용 뷰"""
    def get(self, request, *args, **kwargs):
        records = FuturesTrackRecord.objects.filter(system__id=self.kwargs['system']).order_by('date')
        data = list(records.all().values_list('date', 'gross_return_krw', 'commission_krw', 'risk_krw'))

        return JsonResponse(data, safe=False)


class StockView(TemplateView):
    template_name = "stock.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activate'] = 'stock'
        context['summary'] = StockSummary.objects.all().order_by('-id').first()

        return context

class StockHistoryView(ListView):
    template_name = "stock_history.html"
    model = StockStatement
    queryset = StockStatement.objects.all().order_by('-id')
    context_object_name = "statements"
    paginate_by = 10
 
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        start = int(context['page_obj'].number/10)+1
        end = min(start+10, context['page_obj'].paginator.num_pages+1)
        context['range'] = range(start, end)
        return context

class StockChartView(View):
    """ 차트 데이터 반환용 뷰"""
    def get(self, request, *args, **kwargs):
        data = list(StockSummary.objects.all().order_by('id').values_list('date', 'cash', 'stock'))
        return JsonResponse(data, safe=False)

class UpdateOpenCode(View):
    """ 매매중인 종목의 현재가 불러오기/저장하기 """
    def get(self, request, *args, **kwargs):
        data = list(StockStatement.objects.filter(is_open=True).all().values_list('code', flat=True))
        csrftoken = csrf.get_token(request)
        return JsonResponse({'codes': data, 'csrftoken':csrftoken}, safe=False)

    def post(self, request, **kwargs):
       for item in request.POST.items():
           if item[0] == 'csrfmiddlewaretoken':
               continue

           trade = StockStatement.objects.filter(is_open=True).get(code=item[0])
           trade.current_price=int(item[1])
           trade.save()
       return JsonResponse(True, safe=False)