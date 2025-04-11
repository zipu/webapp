import os
import requests
import json, time
from datetime import datetime

BASEDIR = os.path.dirname(__file__)
def get_secret(setting):
    """Get secret setting or fail with ImproperlyConfigured"""
    basedir = os.path.dirname(__file__)
    with open(os.path.join(basedir, 'secrets.json')) as secrets_file:
        secrets = json.load(secrets_file)
    return secrets[setting]

def set_secret(account, setting):
    with open(os.path.join(BASEDIR, 'secrets.json')) as secrets_file:
        secrets = json.load(secrets_file)
    
    for key, value in setting.items():
        secrets["futures"][account][key] = value
    
    with open(os.path.join(BASEDIR, 'secrets.json'), 'w+') as secrets_file:
        json.dump(secrets, secrets_file)

class Futures:

    def __init__(self):
        """ Ebest API Futures Class"""
        self.secret = get_secret("futures")
        self.baseurl = self.secret["BASEURL"]
        #self.appkey = self.secret["APPKEY"]
        #self.appsecretkey = self.secret['APPSECRETKEY']
        #self.access_token = self.secret['access_token']
        #self.token_issued_date = self.secret['token_issued_date']
        


    def get_access_token(self):
        """ 엑세스 토큰 발행 및 갱신"""
        
        for account in ["A001","A002"]:
            if self.secret[account]['token_issued_date'] != datetime.today().strftime("%Y%m%d"):    
                path = "oauth2/token"
                url = f"{self.baseurl}/{path}"
                header = {"content-type":"application/x-www-form-urlencoded"}
                body = {
                    "appkey": self.secret[account]["appkey"],
                    "appsecretkey": self.secret[account]["appsecretkey"],
                    "grant_type":"client_credentials",
                    "scope":"oob"
                }
                res = requests.post(url, headers=header, data=body)
                if res.ok:
                    #print(res.json())
                    #self.access_token = res.json()['access_token']
                    #self.token_issued_date = datetime.today().strftime("%Y%m%d")
                    self.secret[account]['access_token'] = res.json()['access_token']
                    self.secret[account]['token_issued_date'] = datetime.today().strftime("%Y%m%d")
                    set_secret(account, {
                        'access_token': self.secret[account]['access_token'],
                        'token_issued_date': self.secret[account]['token_issued_date']
                    })

                    #print("*연결계좌: 국내주식")
                    #print(f"*접속주소: {self.baseurl}")
                else: 
                    print(res.text)
                    return False
        return True
    
    def transactions(self, start, end=None):
        """ 주문체결내역상세조회"""
        path="overseas-futureoption/accno"
        url = f"{self.baseurl}/{path}"
        if not end:
            end = datetime.today().strftime("%Y%m%d")
        
        headers = {  
            "content-type":"application/json; charset=utf-8", 
            "authorization": f"Bearer {self.secret['A001']['access_token']}",
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
        
        data = []
        for account in ["A001","A002"]:
            headers = {  
                "content-type":"application/json; charset=utf-8", 
                "authorization": f"Bearer {self.secret[account]['access_token']}",
                "tr_cd":"CIDBQ02400", 
                "tr_cont":"N",
                "tr_cont_key":"",
            }

            res = requests.post(url, headers=headers, data=json.dumps(body))
            data += res.json().get("CIDBQ02400OutBlock2")
            #if not data:
            #    print("Transaction: 새로운 체결 기록이 없음")
            #    print(res.json())
            #    return []
            while res.headers['tr_cont'] == "Y":
                time.sleep(1) #초당 전송수: 1초당 1건
                headers['tr_cont'] = "Y"
                headers['tr_cont_key'] = res.headers['tr_cont_key']
                res = requests.post(url, headers=headers, data=json.dumps(body))
                data += res.json()["CIDBQ02400OutBlock2"]
        #print(data)
        return data        
    