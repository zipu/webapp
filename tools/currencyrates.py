import requests, os
from csv import writer

currencies = ["USD","EUR","CNY","JPY","HKD"]
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