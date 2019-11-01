from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, View
from django.shortcuts import get_object_or_404
from django.http import JsonResponse

from django.db.models import Sum, Window, F
from trading.models import Instrument, FuturesEntry, FuturesExit, FuturesSystem

from datetime import datetime, time
# Create your views here.

class FuturesView(TemplateView):
    template_name = "futures.html"

    def get_context_data(self, **kwargs):
       context = super().get_context_data(**kwargs)
       context['system'] = get_object_or_404(FuturesSystem, id=self.kwargs['system'])
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
        exits = FuturesExit.objects.filter(entry__system__id=self.kwargs['system']).order_by('date')
        data = list(exits.all().values_list('date', 'cum_profit_krw', 'entry__cum_commission_krw'))
        
        return JsonResponse(data, safe=False)

