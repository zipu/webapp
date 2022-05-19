def update_prices(request):
    """Responds to any HTTP request.
    Args:
        request (flask.Request): HTTP request object.
    Returns:
        The response text or any set of values that can be turned into a
        Response object using
        `make_response <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>`.
    """
    import requests
    from bs4 import BeautifulSoup as bs
    import json

    LOGIN_URL = "http://cyosep.appspot.com/login/"
    UPDATE_URL="http://cyosep.appspot.com/trading/update/"
    STOCK_PRICE_URL = "https://finance.naver.com/item/sise.nhn?code="
    FUTURES_PRICE_URL = "https://quotes.esignal.com/esignalprod/quote.action?symbol="

    username='yosep'
    password='tkstjd'

    rqst = requests.session()
    token = rqst.get(LOGIN_URL).cookies['csrftoken']
    rsp = rqst.post(LOGIN_URL, 
                    data={'username':'yosep',
                          'password':'tkstjd',
                          'csrfmiddlewaretoken':token,
                          'next':'/'})

    #서버에서 보유중인 종목의 정보 불러오기
    if rsp.ok:
        string_codes = rqst.get(UPDATE_URL, cookies=rsp.cookies).text
    else:
        raise ValueError("서버에서 종목코드를 불러올수 업습니다")
    codes = json.loads(string_codes)

    data={
        "stock": [],
        "futures": [],
    }
    csrftoken = codes['csrftoken']


    #네이버 증권에서 주식시세 불러오기
    for code in codes['stock']:
        response = requests.get(STOCK_PRICE_URL+code)
        if response.ok:
            value = int(bs(response.text, "html.parser").find(id="_nowVal")\
                  .text.replace(',',''))
            data['stock'].append([code,value])
            print(f"주식시세 업데이트: 종목코드({code}), 가격({value})")
        else:
            print(f"주식시세 업데이트에 실패했습니다")


    #해외선물 시세 업데이트
    for code, number_system in codes['futures']:
        response = requests.get(FUTURES_PRICE_URL+code)
        if response.ok:
            try:
                value = bs(response.text, "html.parser").find("span", {"class": "majors"}).find('strong').text
                value = float(value.replace(',',''))
            except ValueError:
                #데이터 값이 숫자가 아니면 넘어감
                break
            
            #엔화 소숫점 보정
            if code[:3] == 'QJY':
                value = value * 10**6
            
            if number_system != 10:
                a,b = [float(i) for i in value.split("'")]
                value = a+b/number_system
            data['futures'].append([code, value])
            print(f"해외선물 시세 업데이트: 종목코드({code}), 가격({value})")
        else:
            print(f"해외선물 시세 업데이트에 실패했습니다")


    #서버에 업로드
    r = rqst.post(UPDATE_URL, data=json.dumps(data), headers = {'X-CSRFToken': csrftoken})
    print("시세 업데이트를 완료하였습니다.")
    return "done"