from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.http import JsonResponse

from tools import ebest
Ebest = ebest.Stock()

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
            return getattr(self, action)(params)
           else:
            return getattr(self, action)()
        
        
      context = self.get_context_data()
       
      return render(request, EbestStockView.template_name, context=context)
    
   def get_access_token(self):
      if Ebest.get_access_token():
          data = {
             'success': True,
             'server_url': Ebest.baseurl,
          }
      else:
          data = {
             'success': False,
          }
      return JsonResponse(data, safe=False)
    

   def product_list(self):
      res = Ebest.all_stocks()
      if res.ok:
          res.json()['t9945OutBlock']
          
          data = {
             'success': True,
             'products': [i for i in res.json()['t9945OutBlock'] if i['etfchk']=='1'],
             'msg': res.json()['rsp_msg']
          }
      else:
          data = {
             'success': False,
             'msg': res.json()['rsp_msg']
          }
      return JsonResponse(data, safe=False)
    
   def favorites(self):
      res = Ebest.favorites()
      if res.ok:
          data = {
             'success': True,
             'data': res.json()['t8407OutBlock1'],
             'msg': res.json()['rsp_msg']
          }
      else:
          data = {
             'success': False,
             'msg': res.json()['rsp_msg']
          }
      return JsonResponse(data, safe=False)

   def chartdata(self, shcode):
      res = Ebest.chart(shcode)
      if res.ok:
         data = {
             'success': True,
             'data': res.json()['t8410OutBlock1'],
             'msg': res.json()['rsp_msg']
          }
      else:
          data = {
             'success': False,
             'msg': res.json()['rsp_msg']
          }
      return JsonResponse(data, safe=False)
      