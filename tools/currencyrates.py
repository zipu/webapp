import requests, os
from csv import writer
from currency_converter import CurrencyConverter
from datetime import datetime


c=CurrencyConverter()
basedir = os.path.join(os.path.dirname(__file__), 'currencyrates')

currencies = ["USD","EUR","CNY","JPY","HKD"]
now = datetime.now()
date = now.strftime('%Y%m%d')
time = now.strftime('%H%M%S')
for code in currencies:
    rate = c.convert(1, code, 'KRW')
    filename = f"{code}.csv"
    filepath = os.path.join(basedir, filename)
    with open(filepath, mode='a', encoding='utf-8', newline='') as f:
            wobj = writer(f)
            wobj.writerow([date, time, rate])
            f.close()
print("환율 갱신 완료")




"""
querystring = ",".join([f"FRX.KRW{currency}" for currency in currencies])
url = f'https://quotation-api-cdn.dunamu.com/v1/forex/recent?codes={querystring}'
response = requests.get(url)
if response.ok:
    basedir = os.path.join(os.path.dirname(__file__), 'currencyrates')
    for currency in response.json():
        symbol = currency['currencyCode']
        date = currency['date'].replace('-','')
        time = currency['time'].replace(':','')
        rate = currency['basePrice']
        filename = f"{symbol}.csv"
        filepath = os.path.join(basedir,filename)
        with open(filepath, mode='a', encoding='utf-8', newline='') as f:
            wobj = writer(f)
            wobj.writerow([date, time, rate])
            f.close()

    print("환율 갱신 완료")
"""