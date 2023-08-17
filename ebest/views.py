from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.http import JsonResponse
import json

from .api import stockapi, futuresapi, cftc
Ebest = stockapi()
Futures= futuresapi()
CFTC = cftc()

def is_ajax(request):
  """ 들어온 request 가 ajax인지 아닌지 확인"""
  return request.headers.get('x-requested-with') == 'XMLHttpRequest'

# Create your views here.
class EbestStockView(TemplateView):
   template_name = "stock/stock.html"
    
   def get(self, request, *args, **kwargs):
      if is_ajax(request):
           # ajax call 인경우 별도로 처리
           action = request.GET.get('action')
           params = request.GET.get('params')
           if params:
            args = params.split(',')
            return getattr(Ebest, action)(*args)
           else:
            return getattr(Ebest, action)()
        
        
      context = self.get_context_data()
       
      return render(request, EbestStockView.template_name, context=context)
   
# Create your views here.
class CFTCView(TemplateView):
   template_name = "futures/cftc.html"

   def get(self, request, *args, **kwargs):
      context = self.get_context_data()
      context['activate'] = 'cftc'
      context['itemlist'] = CFTC.get_itemlist()
      
      if is_ajax(request):
           # ajax call 인경우 별도로 처리
           action = request.GET.get('action')
           params = request.GET.get('params')
           if params:
            args = params.split(',')
            print(params)
            return getattr(CFTC, action)(*args)
           else:
            return getattr(CFTC, action)()
        
        
      
       
      return render(request, CFTCView.template_name, context=context)
    
    
   
