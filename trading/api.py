import os
import json, csv, requests, zipfile, io
from datetime import datetime
from itertools import zip_longest
from django.http import JsonResponse
from django.conf import settings
import pandas as pd


from tools.ebest.stock import Stock

BASEDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')

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
   
   def company_list(self):
      # 종목 정보 불러오기, market = kospi: '1' or kosdaq: '2' or all:'0'
      companies = self.ebest.get_companies_summary()
      data = []
      for key, item in companies.items():
            if item['market_cd'] == '1':
               market = '코스피'
            elif item['market_cd'] == '2':
               market = '코스닥'

            data.append([key, item['name'], market, item['sigavalue'], item['cashrate']])

      return JsonResponse(data, safe=False)
   
   def company_info(self, shcode):
      # 회사 정보 불러오기
      data = self.ebest.get_company_info(shcode)
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

class cftc:
   def __init__(self):
      self.dir = os.path.join(BASEDIR, 'tools','data','futures','cftc')


   def get_itemlist(self):
      filename = os.path.join(self.dir, 'categories.json')
      with open(filename) as f:
         return json.load(f)
   
   
   def update_data(self):
      year = datetime.today().year
      url_dir_file = [
         (f"https://www.cftc.gov/files/dea/history/dea_fut_xls_{year}.zip", "legacy", "annual.xls"),
         (f"https://www.cftc.gov/files/dea/history/dea_com_xls_{year}.zip", "legacy_option_combined", "annualof.xls"),
         #(f"https://www.cftc.gov/files/dea/history/dea_cit_xls_{year}.zip", "index_trader_supplement", "deacit.xls"),
         (f"https://www.cftc.gov/files/dea/history/fut_disagg_xls_{year}.zip", "disaggregated", "f_year.xls"),
         (f"https://www.cftc.gov/files/dea/history/com_disagg_xls_{year}.zip", "disaggregated_option_combined", "c_year.xls"),
         (f"https://www.cftc.gov/files/dea/history/fut_fin_xls_{year}.zip","financial_futures", "FinFutYY.xls"),
         (f"https://www.cftc.gov/files/dea/history/com_fin_xls_{year}.zip", "financial_futures_option_combined", 'FinComYY.xls')
      ]

      for url, dirname, file in url_dir_file:
         print(f"Update CFTC data: {dirname}")
         r = requests.get(url)
         z = zipfile.ZipFile(io.BytesIO(r.content))
         df = pd.read_excel(z.read(file))
         df['Report_Date_as_MM_DD_YYYY'] = df['Report_Date_as_MM_DD_YYYY'].dt.strftime('%Y-%m-%d')
         for name, group in df.groupby('Market_and_Exchange_Names'):
            name = name.replace('/','-').replace('<','-')
            filename = os.path.join(self.dir, dirname,f"{name}.csv")
            group.sort_values(by='As_of_Date_In_Form_YYMMDD', inplace=True)
            if not os.path.exists(filename):
                  group.to_csv(filename, mode='w', index=False)
            else:
                  old = pd.read_csv(filename)
                  #old = old.drop('Report_Date_as_MM_DD_YYYY', axis=1)
                  #old = old.rename(columns = {'Report_Date_as_MM_DD_YYYY.1':'Report_Date_as_MM_DD_YYYY'})
                  df = pd.concat([old, group])
                  df.drop_duplicates('As_of_Date_In_Form_YYMMDD', inplace=True)
                  df.to_csv(filename, mode='w', index=False)
      return JsonResponse({'success': True}, safe=False)
            
            
   def financials(self, sector, name):
      categories = self.get_itemlist()
      # Futures only
      filename = categories[sector][name]+'.csv'
      filepath = os.path.join(self.dir,'financial_futures', filename)
      df = pd.read_csv(filepath)
      df.index = pd.to_datetime(df['As_of_Date_In_Form_YYMMDD'], format='%y%m%d')
      df.fillna(0, inplace=True)
      df.insert(0,'date' , pd.to_datetime(df.index).values.astype('M8[ms]').astype('int64'))
      df.drop_duplicates('date', inplace=True)
      df['dealers'] = df['Dealer_Positions_Long_All'] - df['Dealer_Positions_Short_All']
      df['institutions'] = df['Asset_Mgr_Positions_Long_All'] - df['Asset_Mgr_Positions_Short_All']
      df['funds'] = df['Lev_Money_Positions_Long_All'] - df['Lev_Money_Positions_Short_All']
      df['others'] = df['Other_Rept_Positions_Long_All'] - df['Other_Rept_Positions_Short_All']
      df['traders'] = df['Traders_Tot_All'] - df['Traders_Dealer_Spread_All'] - df['Traders_Lev_Money_Spread_All'] - df['Traders_Other_Rept_Spread_All']

      futuresdata = df[['date','dealers','institutions','funds','others','traders']]

      #option
      # option combined 
      filepath = os.path.join(self.dir,'financial_futures_option_combined', filename)
      df2 = pd.read_csv(filepath)
      df2.index = pd.to_datetime(df['As_of_Date_In_Form_YYMMDD'], format='%y%m%d')
      df2.fillna(0, inplace=True)
      df2.insert(0,'date' , pd.to_datetime(df.index).values.astype('M8[ms]').astype('int64'))
      df2.drop_duplicates('date')
      df2['dealers'] = df2['Dealer_Positions_Long_All'] - df2['Dealer_Positions_Short_All'] - df['dealers']
      df2['institutions'] = df2['Asset_Mgr_Positions_Long_All'] - df2['Asset_Mgr_Positions_Short_All'] - df['institutions']
      df2['funds'] = df2['Lev_Money_Positions_Long_All'] - df2['Lev_Money_Positions_Short_All'] - df['funds']
      df2['others'] = df2['Other_Rept_Positions_Long_All'] - df2['Other_Rept_Positions_Short_All'] - df['others']
      df2['traders'] = df2['Traders_Tot_All'] - df2['Traders_Dealer_Spread_All'] - df2['Traders_Lev_Money_Spread_All'] - df2['Traders_Other_Rept_Spread_All'] - df['traders']
      optiondata = df2[['date','dealers','institutions','funds','others','traders']]

      #spread
      spread = df2[['date','Dealer_Positions_Spread_All','Asset_Mgr_Positions_Spread_All','Lev_Money_Positions_Spread_All',\
                    'Other_Rept_Positions_Spread_All','Traders_Dealer_Spread_All','Traders_Asset_Mgr_Spread_All',\
                     'Traders_Lev_Money_Spread_All', 'Traders_Other_Rept_Spread_All']]
      
      response = {
         'futures': futuresdata.values.tolist(),
         'option': optiondata.values.tolist(),
         'spread': spread.values.tolist(),
         'last_update': df.index[-1].strftime('%Y-%m-%d')
      }
      
      return JsonResponse(response, safe=False)

      
   def disaggregated(self, sector, name):
      categories = self.get_itemlist()
      # Futures only
      filename = categories[sector][name]+'.csv'
      filepath = os.path.join(self.dir,'disaggregated', filename)
      df = pd.read_csv(filepath)
      df.index = pd.to_datetime(df['As_of_Date_In_Form_YYMMDD'], format='%y%m%d')
      df.fillna(0, inplace=True)
      df.insert(0,'date' , pd.to_datetime(df.index).values.astype('M8[ms]').astype('int64'))
      df['producer'] = df['Prod_Merc_Positions_Long_ALL'] - df['Prod_Merc_Positions_Short_ALL']
      df['swap'] = df['Swap_Positions_Long_All'] - df['Swap__Positions_Short_All']
      df['funds'] = df['M_Money_Positions_Long_ALL'] - df['M_Money_Positions_Short_ALL']
      df['others'] = df['Other_Rept_Positions_Long_ALL'] - df['Other_Rept_Positions_Short_ALL']
      df['traders'] = df['Traders_Tot_All'] - df['Traders_Swap_Spread_All'] - df['Traders_M_Money_Spread_All'] - df['Traders_Other_Rept_Spread_All']

      futuresdata = df[['date','producer','swap','funds','others','Traders_Tot_All']].drop_duplicates('date')
      
      # option combined 
      filepath = os.path.join(self.dir,'disaggregated_option_combined', filename)
      df2 = pd.read_csv(filepath)
      df2.index = pd.to_datetime(df['As_of_Date_In_Form_YYMMDD'], format='%y%m%d')
      df2.fillna(0, inplace=True)
      df2.insert(0,'date' , pd.to_datetime(df.index).values.astype('M8[ms]').astype('int64'))
      df2['producer'] = df2['Prod_Merc_Positions_Long_ALL'] - df2['Prod_Merc_Positions_Short_ALL'] - df['producer']
      df2['swap'] = df2['Swap_Positions_Long_All'] - df2['Swap__Positions_Short_All'] - df['swap']
      df2['funds'] = df2['M_Money_Positions_Long_ALL'] - df2['M_Money_Positions_Short_ALL'] - df['funds']
      df2['others'] = df2['Other_Rept_Positions_Long_ALL'] - df2['Other_Rept_Positions_Short_ALL'] - df['others']
      df2['traders'] = df2['Traders_Tot_All'] - df2['Traders_Swap_Spread_All'] - df2['Traders_M_Money_Spread_All'] - df2['Traders_Other_Rept_Spread_All'] - df['traders']
      optiondata = df2[['date','producer','swap','funds','others','traders']].drop_duplicates('date')

      spread = df2[['date','Swap__Positions_Spread_All','M_Money_Positions_Spread_ALL','Other_Rept_Positions_Spread_ALL','Traders_Swap_Spread_All','Traders_M_Money_Spread_All','Traders_Other_Rept_Spread_All']].drop_duplicates('date')
      
      response = {
         'futures': futuresdata.values.tolist(),
         'option': optiondata.values.tolist(),
         'spread': spread.values.tolist(),
         'last_update': df.index[-1].strftime('%Y-%m-%d')
      }
      
      return JsonResponse(response, safe=False)
   
   def legacy(self,sector, name):
      #filename = os.path.join(self.dir,'legacy', f"{name}.csv")
      categories = self.get_itemlist()
      
      # Futures only
      filename = categories[sector][name]+'.csv'
      filepath = os.path.join(self.dir,'legacy', filename)
      df = pd.read_csv(filepath)
      df.index = pd.to_datetime(df['As_of_Date_In_Form_YYMMDD'], format='%y%m%d')
      df.fillna(0, inplace=True)
      df.insert(0,'date' , pd.to_datetime(df.index).values.astype('M8[ms]').astype('int64'))
      df['noncomm'] = df['NonComm_Positions_Long_All'] - df['NonComm_Positions_Short_All']
      df['comm'] = df['Comm_Positions_Long_All'] - df['Comm_Positions_Short_All']
      df['unknown'] = df['NonRept_Positions_Long_All'] - df['NonRept_Positions_Short_All']
      df['traders'] = df['Traders_Tot_All'] - df['Traders_NonComm_Spread_All']
      futuresdata = df[['date','noncomm','comm','unknown','traders']].drop_duplicates('date')
      
      # option combined 
      filepath = os.path.join(self.dir,'legacy_option_combined', filename)
      df2 = pd.read_csv(filepath)
      df2.index = pd.to_datetime(df['As_of_Date_In_Form_YYMMDD'], format='%y%m%d')
      df2.fillna(0, inplace=True)
      df2.insert(0,'date' , pd.to_datetime(df.index).values.astype('M8[ms]').astype('int64'))
      df2['noncomm'] = df2['NonComm_Positions_Long_All'] - df2['NonComm_Positions_Short_All'] - df['noncomm']
      df2['comm'] = df2['Comm_Positions_Long_All'] - df2['Comm_Positions_Short_All'] - df['comm']
      df2['unknown'] = df2['NonRept_Positions_Long_All'] - df2['NonRept_Positions_Short_All'] - df['unknown']
      df2['traders'] = df2['Traders_Tot_All'] - df2['Traders_NonComm_Spread_All'] - df['traders']
      optiondata = df2[['date','noncomm','comm','unknown','traders']].drop_duplicates('date')

      response = {
         'futures': futuresdata.values.tolist(),
         'option': optiondata.values.tolist(),
         'spread_position': df2[['date','NonComm_Postions_Spread_All']].drop_duplicates('date').values.tolist(),
         'spread_traders': df2[['date','Traders_NonComm_Spread_All']].drop_duplicates('date').values.tolist(),
         'last_update': df.index[-1].strftime('%Y-%m-%d')
      }

      return JsonResponse(response, safe=False)

class futuresapi:
   def __init__(self):
      self.dir = os.path.join(BASEDIR, 'tools','data','futures')
      self.cftc = cftc()