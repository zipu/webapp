import requests
from bs4 import BeautifulSoup as bs
import json

LOGIN_URL = "http://localhost:8000/login/"
STOCK_CODE_URL = "http://localhost:8000/trading/stock/opencodes"
STOCK_PRICE_URL = "https://finance.naver.com/item/sise.nhn?code="

username='yosep'
password='tkstjd'

rqst = requests.session()
token = rqst.get(LOGIN_URL).cookies['csrftoken']
rsp = rqst.post(LOGIN_URL, 
                data={'username':'yosep',
                      'password':'tkstjd',
                      'csrfmiddlewaretoken':token,
                      'next':'/'})
if rsp.ok:
    string_codes = rqst.get(STOCK_CODE_URL, cookies=rsp.cookies).text
    
else:
    raise ValueError("서버에서 종목코드를 불러올수 업습니다")
    
data = json.loads(string_codes)
codes = data['codes']
token = data['csrftoken']
prices = {}
for code in codes:
    response = requests.get(STOCK_PRICE_URL+code)
    if response.ok:
        value = int(bs(response.text, "html.parser").find(id="_nowVal")\
               .text.replace(',',''))
        prices[code] = value
        
prices['csrfmiddlewaretoken'] = token
rsp = rqst.post(STOCK_CODE_URL,
          data=prices)

if rsp.text != 'true':
    raise ValueError("서버에 종목코드를 업데이트하지 못했습니다.")