from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, View
from django.shortcuts import get_object_or_404
from django.http import JsonResponse

from trading.models import Instrument, FuturesEntry, FuturesExit, FuturesSystem
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
   queryset = FuturesEntry.objects.filter(system__id=1).order_by('-pk')
   context_object_name = "entries"
   paginate_by = 10

   def get_context_data(self, **kwargs):
       context = super().get_context_data(**kwargs)
       start = int(context['page_obj'].number/10)+1
       end = min(start+10, context['page_obj'].paginator.num_pages+1)
       context['range'] = range(start, end)
       return context

class FuturesChartView(View):
    """ 차트 데이터 반환용 뷰"""
    def get(self, request, *args, **kwargs):
        exits = FuturesExit.objects.filter(entry__system__id=self.kwargs['system'])
        profit = list(exits.all().values_list('date','profit'))
        commissions = list(exits.all().values_list('date','entry__commission'))

        return JsonResponse({'profit':profit, 'commission':commissions}, safe=False)

