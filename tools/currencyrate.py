import requests, json, os

currencies = ["USD","EUR","CNY","JPY","HDK"]
querystring = ",".join([f"FRX.KRW{currency}" for currency in currencies])
url = f'https://quotation-api-cdn.dunamu.com/v1/forex/recent?codes={querystring}'
response = requests.get(url)
if response.ok:
    filename = "currencyrate.json"
    filepath = os.path.join(os.path.dirname(__file__),filename)
    if  os.path.isfile(filepath):
        jsonobj = json.load(open(filepath))
    else:
        jsonobj = {"USD":[], "EUR":[], "CNY":[], "JPY":[], "HDK":[]}

    for currency in response.json():
        jsonobj[currency['currencyCode']].append([currency['date'], currency['basePrice']])

    with open(filepath, mode='w+', encoding='utf-8') as f:
        json.dump(jsonobj, f)
    
    print("환율 갱신 완료")
    print(os.path.join(os.path.dirname(__file__),filename))