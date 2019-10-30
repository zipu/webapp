from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, View

from trading.models import Instrument, FuturesEntry, FuturesExit, FuturesSystem
# Create your views here.

class RecordsView(TemplateView):
    template_name = "records.html"
    
    def get_context_data(self, **kwargs):
       context = super().get_context_data(**kwargs)
       context['activate'] = 'records'
       context['system'] = FuturesSystem.objects.all().first()
       return context

class RecordsListView(ListView):
   template_name = "recordsdetail.html"
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

class ChartView(View):
    def get(self, request, *args, **kwargs):
        if request.GET and request.is_ajax():
            system = FuturesSystem.objects.filter(id=kwargs['pk'])
            exits = system.entires.exits.all().order_by('id')
            profit = []


        
        return 'Hello, World!'
        #if request.GET and request.is_ajax():

