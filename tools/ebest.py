import os
import requests
import json, time
from datetime import datetime

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
def get_secret(setting):
    """Get secret setting or fail with ImproperlyConfigured"""
    
    with open(os.path.join(BASE_DIR, 'secrets.json')) as secrets_file:
        secrets = json.load(secrets_file)
    
    return secrets["Ebest"][setting]


class Stock:

    def __init__(self):
        self.secret = get_secret("Stock")
        self.baseurl = self.secret["BASEURL"]
        self.appkey = self.secret["APPKEY"]
        self.appsecretkey = self.secret['APPSECRETKEY']
        self.access_token = None
        self.token_issued_time = None

    def get_access_token(self):
        """ 엑세스 토큰 발행 및 갱신"""
        if not self.token_issued_time or (time.time()-self.token_issued_time)/(60*60) > 12:
            path = "oauth2/token"
            url = f"{self.baseurl}/{path}"
            header = {"content-type":"application/x-www-form-urlencoded"}
            body = {
                "appkey": self.appkey,
                "appsecretkey": self.appsecretkey,
                "grant_type":"client_credentials",
                "scope":"oob"
            }
            res = requests.post(url, headers=header, data=body)
            if res.ok:
                self.access_token = res.json()['access_token']
                self.token_issued_time = time.time()
                print("*로그인성공*")
                #print("*연결계좌: 국내주식")
                #print(f"*접속주소: {self.baseurl}")
                return True
            else: 
                print(res.text)
                return False
        
        return True
    
    def favorites(self):
        """ 멀티 현재가 조회 """
        # 토큰 만기 조회
        self.get_access_token()

        path = "stock/market-data"
        url = f"{self.baseurl}/{path}"
        num = len(self.secret['FAVORITES'])
        codes = ''.join(self.secret['FAVORITES'])

        headers = {
            "content-type":"application/json; charset=UTF-8",
            "authorization": f"Bearer {self.access_token}",
            "tr_cd":"t8407", 
            "tr_cont":"N",
            "tr_cont_key":"",
        }
        body = {
                "t8407InBlock" : {
                    "nrec" : num,
                    "shcode": codes
                }
        }

        res = requests.post(url, headers=headers, data=json.dumps(body))
        return res
    
    def chart(self, shcode):
        """ 주식차트(일주월년)"""
        # 토큰 만기 조회
        self.get_access_token()

        path = "stock/chart"
        url = f"{self.baseurl}/{path}"
        headers = {
            "content-type":"application/json; charset=UTF-8",
            "authorization": f"Bearer {self.access_token}",
            "tr_cd":"t8410", 
            "tr_cont":"N",
            "tr_cont_key":"",
        }
        body = {
                "t8410InBlock" : {
                    "shcode" : shcode,
                    "gubun" : "2",
                    "qrycnt" : 500,
                    "sdate" : "",
                    "edate" : datetime.today().strftime("%Y%m%d"),
                    "cts_date" : "",
                    "comp_yn" : "N",
                    "sujung" : "Y"
                }
        }

        res = requests.post(url, headers=headers, data=json.dumps(body))
        return res
    
    def entries(self):
        """ 보유 종목 """
        self.get_access_token()

        path="stock/accno"
        url = f"{self.baseurl}/{path}"
        headers = {  
            "content-type":"application/json; charset=utf-8", 
            "authorization": f"Bearer {self.access_token}",
            "tr_cd":"t0424", 
            "tr_cont":"N",
            "tr_cont_key":"",
        }
        body = {
                "t0424InBlock": {
                "prcgb": "",
                "chegb": "",
                "dangb": "",
                "charge": "",
                "cts_expcode": ""
            }
        }

        res = requests.post(url, headers=headers, data=json.dumps(body))
        data = res.json().get("t0424OutBlock1")
        while res.headers['tr_cont'] == "Y":
            time.sleep(1) #초당 전송수: 1초당 1건
            headers['tr_cont'] = "Y"
            headers['tr_cont_key'] = res.headers['tr_cont_key']
            res = requests.post(url, headers=headers, data=json.dumps(body))
            data += res.json()["t0424OutBlock1"]
        
        return data




class OverseasFutures:

    def __init__(self):
        secret = get_secret("Overseas")
        self.baseurl = secret["BASEURL"]
        self.appkey = secret["APPKEY"]
        self.appsecretkey = secret['APPSECRETKEY']
        self.access_token = None

    def login(self):
        path = "oauth2/token"
        url = f"{self.baseurl}/{path}"
        header = {"content-type":"application/x-www-form-urlencoded"}
        body = {
            "appkey": self.appkey,
            "appsecretkey": self.appsecretkey,
            "grant_type":"client_credentials",
            "scope":"oob"
        }
        res = requests.post(url, headers=header, data=body)
        if res.ok:
            self.access_token = res.json()['access_token']
            print("*로그인성공*")
            print("*접속서버: 해외선물 실서버")
            print(f"*접속주소: {self.baseurl}")
            return res
        else: 
            print(f"login failed: {res.text}")
            return res 
    
    def transactions(self, start, end=None):
        """ 주문체결내역상세조회"""
        path="overseas-futureoption/accno"
        url = f"{self.baseurl}/{path}"
        if not end:
            end = datetime.today().strftime("%Y%m%d")
        
        headers = {  
            "content-type":"application/json; charset=utf-8", 
            "authorization": f"Bearer {self.access_token}",
            "tr_cd":"CIDBQ02400", 
            "tr_cont":"N",
            "tr_cont_key":"",
        }

        body = {
                    "CIDBQ02400InBlock1": {
                        "RecCnt": 1,
                        "IsuCodeVal": "",
                        "QrySrtDt": start,
                        "QryEndDt": end,
                        "ThdayTpCode": "0",
                        "OrdStatCode": "1",
                        "BnsTpCode": "0",
                        "QryTpCode": "2",
                        "OrdPtnCode": "00",
                        "OvrsDrvtFnoTpCode": "A"
                    }
                }
        

        res = requests.post(url, headers=headers, data=json.dumps(body))
        data = res.json().get("CIDBQ02400OutBlock2")
        if not data:
            print("Transaction: 새로운 체결 기록이 없음")
            print(res.json())
            return []
        while res.headers['tr_cont'] == "Y":
            time.sleep(1) #초당 전송수: 1초당 1건
            headers['tr_cont'] = "Y"
            headers['tr_cont_key'] = res.headers['tr_cont_key']
            res = requests.post(url, headers=headers, data=json.dumps(body))
            data += res.json()["CIDBQ02400OutBlock2"]
        
        return data        
    