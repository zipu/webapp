import json
from itertools import zip_longest
from django.http import JsonResponse
from tools.ebest.stock import Stock

class stockapi:
   def __init__(self):
      self.ebest = Stock()
   
   def etf(self):
      res = self.ebest.etf()
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
      res = self.ebest.chart(shcode)
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
   
   def entries(self):
      res = self.ebest.entries()
      if res:
         entries = []
         for entry in res:
            entries.append({
               'expcode': entry['expcode'], #종목번호
               'hname': entry['hname'], #종목명
               'entryprice': entry['pamt'], #평균단가
               'quantity': entry['janqty'], #잔고수량
               'price': entry['price'], #현재가
            })

         data = {
             'success': True,
             'data': entries,
             'msg': "잔고조회 성공"
          }
      else:
          data = {
             'success': False,
             'msg': "잔고조회 실패"
          }
      return JsonResponse(data, safe=False)
   

   def sector_list(self):
      
      res = self.ebest.sector_list().json()['t8424OutBlock']
      kospi = []
      kosdaq = []
      for item in res:
         if item['upcode'][0] in ['0','1']:
            kospi.append(item)
         elif item['upcode'][0] == '3':
            kosdaq.append(item)
         
      data = list(zip_longest(kospi, kosdaq,\
                              fillvalue={"hname":"", "upcode":""}))
      return JsonResponse(data, safe=False)
   
   def sector_chart(self, shcode):
      res = self.ebest.sector_chart(shcode)
      if res.ok:
         data = {
             'success': True,
             'data': res.json()['t8419OutBlock1'],
             'msg': res.json()['rsp_msg']
          }
      else:
          data = {
             'success': False,
             'msg': res.json()['rsp_msg']
          }
      return JsonResponse(data, safe=False)
