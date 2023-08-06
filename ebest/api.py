import os
import json, csv
from itertools import zip_longest
from django.http import JsonResponse
from tools.ebest.stock import Stock

from django.conf import settings
BASEDIR = settings.BASE_DIR

class stockapi:
   def __init__(self):
      self.ebest = Stock()

   def get_access_token(self):
      result, data = self.ebest.get_access_token()
      response = {
            'success': result,
            'data': data,
            'etflist': self.ebest.get_secret("stock")["ETF"]
         }

      return JsonResponse(response, safe=False)
   
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

   def stockchart(self, shcode, period):
      res = self.ebest.chart(shcode,period)
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
   
   def company_list(self, market):
      # 종목 정보 불러오기, market = kospi: '1' or kosdaq: '2'
      codes = self.ebest.company_codes
      data = []
      
      for key, item in codes.items():
         if item['gubun'] == market:
            data.append([key, item['name']])

      return JsonResponse(data, safe=False)

   def sector_list(self):
      
      res = self.ebest.sector_list().json()['t8424OutBlock']
      kospi = []
      kp200 = []
      kosdaq = []
      for item in res:
         if item['upcode'][0] == '0':
            kospi.append(item)
         elif item['upcode'][0] == '1':
            kp200.append(item)
         elif item['upcode'][0] == '3':
            kosdaq.append(item)
         
      data = list(zip_longest(kospi,kp200, kosdaq,\
                              fillvalue={"hname":"", "upcode":""}))
      return JsonResponse(data, safe=False)
   
   def sector_chart(self, shcode, period):
      res = self.ebest.sector_chart(shcode, period)
      if res.ok:

         response = {
             'success': True,
             'data': res.json()['t8419OutBlock1'],
             'msg': res.json()['rsp_msg']
          }
      else:
          response = {
             'success': False,
             'msg': res.json()['rsp_msg']
          }
      return JsonResponse(response, safe=False)
   
   def get_currency_rate(self):
      path = os.path.join(BASEDIR, 'tools','currencyrates')
      currencyrates = {'USD':[], 'EUR':[], 'JPY':[], 'CNY':[]}
      for currency in currencyrates.keys():
         filename  =os.path.join(path, f"{currency}.csv")
         with open(filename, 'r') as f:
            currencyrates[currency]=list(csv.reader(f))[-24*365:] #최근 1년 정도만.
      return JsonResponse(currencyrates, safe=False)
   

   def COT(self, shcode):
      # 기관/외국인 매매 동향
      res = self.ebest.COT(shcode)
      if res.ok:
         data = []
         for day in reversed(res.json()['t1716OutBlock']):
            data.append([day['date'], day['krx_0008'], day['krx_0018'],\
            day['fsc_0009'], day['pgmvol'], day['gm_volume']])
         
         response = {
             'success': True,
             'data': data,
             'msg': res.json()['rsp_msg']
         }
      else: 
         response = {
             'success': False,
             'msg': res.json()['rsp_msg']
         }
      return JsonResponse(response, safe=False)
   
   def market_COT(self, shcode):
      # 기관/외국인 매매 동향
      res = self.ebest.market_COT(shcode)
      if res.ok:
         data = []
         for day in reversed(res.json()['t1665OutBlock1']):
            data.append([day['date'], day['sv_08'], day['sv_18'], day['sv_17'], day['sv_11']])
         
         response = {
             'success': True,
             'data': data,
             'msg': res.json()['rsp_msg']
         }
      else: 
         response = {
             'success': False,
             'msg': res.json()['rsp_msg']
         }
      return JsonResponse(response, safe=False)
   
   def google_trends(self, name):
      # 구글 트랜드를 그래프로 보여줌
      data = self.ebest.google_trend(name)
      return JsonResponse(data, safe=False)
