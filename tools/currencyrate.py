import requests, json, os

currencies = ["USD","EUR","CNY","JPY","HDK"]
querystring = ",".join([f"FRX.KRW{currency}" for currency in currencies])
url = f'https://quotation-api-cdn.dunamu.com/v1/forex/recent?codes={querystring}'
response = requests.get(url)
if response.ok:
    filename = "currency.json"
    if  os.path.isfile(filename):
        jsonobj = json.load(open(filename))
    else:
        jsonobj = {"USD":[], "EUR":[], "CNY":[], "JPY":[], "HDK":[]}

    for currency in response.json():
        jsonobj[currency['currencyCode']].append([currency['date'], currency['basePrice']])

    with open(filename, mode='w+', encoding='utf-8') as f:
        json.dump(jsonobj, f)
    
    print("환율 갱신 완료")