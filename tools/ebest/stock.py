import os
import requests
import json, time
from datetime import datetime, timedelta

BASEDIR = os.path.dirname(__file__)


class Stock:

    def __init__(self):
        self.secret = self.get_secret("stock")
        self.baseurl = self.secret["BASEURL"]
        self.appkey = self.secret["APPKEY"]
        self.appsecretkey = self.secret['APPSECRETKEY']
        self.access_token = self.secret['access_token']
        self.token_issued_date = self.secret['token_issued_date']
    
    def get_secret(self, setting):
        """Get secret setting or fail with ImproperlyConfigured"""
        
        with open(os.path.join(BASEDIR, 'secrets.json')) as secrets_file:
            secrets = json.load(secrets_file)
        return secrets[setting]
    
    def set_secret(self, setting):
        with open(os.path.join(BASEDIR, 'secrets.json')) as secrets_file:
            secrets = json.load(secrets_file)
        
        for key, value in setting.items():
            secrets["stock"][key] = value
        
        with open(os.path.join(BASEDIR, 'secrets.json'), 'w+') as secrets_file:
            json.dump(secrets, secrets_file)


    def get_access_token(self):
        """ 엑세스 토큰 발행 및 갱신"""
        
        if self.token_issued_date != datetime.today().strftime("%Y%m%d"):
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
                self.token_issued_date = datetime.today().strftime("%Y%m%d")
                self.secret['access_token'] = self.access_token
                self.secret['token_issued_date'] = self.token_issued_date
                self.set_secret({
                    'access_token': self.access_token,
                    'token_issued_date': self.token_issued_date
                })

                #print("*연결계좌: 국내주식")
                #print(f"*접속주소: {self.baseurl}")
            else: 
                print(res.text)
                return False, res.json()

        return True, self.access_token
    
    def chart(self, shcode, period):
        """ 주식차트(일주월년)
            period: 2=일, 3=주, 4=월
        """

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
                    "gubun" : period,
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
            body["cts_expcode"] = res.json()['t0424OutBlock']['cts_expcode']
            res = requests.post(url, headers=headers, data=json.dumps(body))
            data += res.json()["t0424OutBlock1"]
        
        return data 

    def etf(self):
        """ etf 조회 """
        # 토큰 만기 조회
        self.get_access_token()

        path = "stock/market-data"
        url = f"{self.baseurl}/{path}"
        num = len(self.secret['ETF'])
        codes = ''.join(self.secret['ETF'])

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
    
    def sector_list(self):
        """ 업종 목록 """
        # 토큰 만기 조회
        self.get_access_token()

        path = "indtp/market-data"
        url = f"{self.baseurl}/{path}"
        headers = {
            "content-type":"application/json; charset=UTF-8",
            "authorization": f"Bearer {self.access_token}",
            "tr_cd":"t8424", 
            "tr_cont":"N",
            "tr_cont_key":"",
        }
        body = {
                "t8424InBlock" : {
                    "gubun1":"0"
                }
        } 

        res = requests.post(url, headers=headers, data=json.dumps(body))
        return res
    
    def sector_chart(self, shcode, period):
        """ 업종차트"""
        # 토큰 만기 조회
        self.get_access_token()

        path = 	"indtp/chart"
        url = f"{self.baseurl}/{path}"
        headers = {
            "content-type":"application/json; charset=UTF-8",
            "authorization": f"Bearer {self.access_token}",
            "tr_cd":"t8419", 
            "tr_cont":"N",
            "tr_cont_key":"",
        }
        body = {
            "t8419InBlock": {
                "shcode": shcode,
                "gubun": period,
                "qrycnt": 500,
                "sdate": " ",
                "edate": "99999999",
                "cts_date": " ",
                "comp_yn": "N"
            }
        }
        res = requests.post(url, headers=headers, data=json.dumps(body))
        return res
    
    def COT(self, shcode):
        """ 투자주체 (기관/외인 별 매매 동향)"""
        # 토큰 만기 조회
        self.get_access_token()
        today = datetime.today()
        start = today - timedelta(days=500)


        path = "stock/frgr-itt"
        url = f"{self.baseurl}/{path}"
        headers = {
            "content-type":"application/json; charset=UTF-8",
            "authorization": f"Bearer {self.access_token}",
            "tr_cd":"t1716", 
            "tr_cont":"N",
            "tr_cont_key":"",
        }
        body = {
                "t1716InBlock" : {
                    "shcode" : shcode,
                    "gubun" : "1",
                    "fromdt" : start.strftime("%Y%m%d"),
                    "todt" : today.strftime("%Y%m%d"),
                    "prapp" : 0,
                    "prgubun" : "0",
                    "orggubun" : "0",
                    "frggubun" : "0"
                }
        }

        res = requests.post(url, headers=headers, data=json.dumps(body))
        return res
    
    def market_COT(self, shcode):
        """ 업종별 기관/외인  매매 동향"""
        # 토큰 만기 조회
        self.get_access_token()
        today = datetime.today()
        start = today - timedelta(days=500)

        path = "stock/chart"
        url = f"{self.baseurl}/{path}"
        headers = {
            "content-type":"application/json; charset=UTF-8",
            "authorization": f"Bearer {self.access_token}",
            "tr_cd":"t1665", 
            "tr_cont":"N",
            "tr_cont_key":"",
        }
        body = {
            "t1665InBlock" : {
                "market" : shcode[0],
                "upcode" : shcode,
                "gubun2" : "2",
                "gubun3" : "1",
                "from_date" : start.strftime("%Y%m%d"),
                "to_date" : today.strftime("%Y%m%d")
            }
        }

        res = requests.post(url, headers=headers, data=json.dumps(body))
        return res
    
    def get_item_list(self):
        self.get_access_token()
        data = {}

        path = "stock/etc"
        url = f"{self.baseurl}/{path}"
        headers = {
            "content-type":"application/json; charset=UTF-8",
            "authorization": f"Bearer {self.access_token}",
            "tr_cd":"t8436", 
            "tr_cont":"N",
            "tr_cont_key":"",
        }
        body = {
            "t8436InBlock" : {
                "gubun" : "0"
            }
        }
        
        res = requests.post(url, headers=headers, data=json.dumps(body))
        return res
    
    def download_market_data(self):
        #종목 정보 전체를 다운 받는 함수
        self.get_access_token()
        data = {}
        print("전체 종목 정보 다운로드")
        chk = [] #우선 기업 필터
        for item in self.get_item_list().json()['t8436OutBlock']:
                if item['etfgubun'] != "0":
                    continue
                if item['spac_gubun'] == 'Y':
                    continue
                if not chk:
                    chk.append(item['hname'])
                else:
                    if chk[0] in item['hname']:
                        continue
                    else:
                        chk = [item['hname']]
                
                data[item['shcode']] = {
                    'shcode': item['shcode'],
                    'expcode': item['expcode'],
                    'name': item['hname'],
                }
                        

        #fng 요약
        for shcode in data.keys():
            #fng 요약
            fng = self.FNG_summary(shcode).json()
            print(f"기업정보 다운로드: {data[shcode]['name']}")
            print(fng)
            outblock = fng['t3320OutBlock']
            outblock2 = fng['t3320OutBlock1']
            data[shcode]['upgubunnm'] = outblock['upgubunnm']
            data[shcode]['market_cd'] = outblock['sijangcd']
            data[shcode]['market'] = outblock['marketnm']
            data[shcode]['foreignratio'] = outblock['foreignratio']
            data[shcode]['capital'] = outblock['capital']
            data[shcode]['sigavalue'] = outblock['sigavalue']
            data[shcode]['cashsis'] = outblock['cashsis']
            data[shcode]['cashrate'] = outblock['cashrate']
            data[shcode]['price'] = outblock['price']
            data[shcode]['is_danger'] = outblock['notice2']
            data[shcode]['is_clearing'] = outblock['notice1']
            data[shcode]['is_hot'] = outblock['notice3']
            data[shcode]['per'] = outblock2['per']
            data[shcode]['eps'] = outblock2['eps']
            data[shcode]['pbr'] = outblock2['pbr']
            data[shcode]['roa'] = outblock2['roa']
            data[shcode]['ebitda'] = outblock2['ebitda']
            data[shcode]['evebitda'] = outblock2['evebitda']
            data[shcode]['sps'] = outblock2['sps']
            data[shcode]['cps'] = outblock2['cps']
            data[shcode]['bps'] = outblock2['bps']
            data[shcode]['t_per'] = outblock2['t_per']
            data[shcode]['t_eps'] = outblock2['t_eps']
            data[shcode]['peg'] = outblock2['peg']
            data[shcode]['t_peg'] = outblock2['t_peg']
            time.sleep(1.2)
        
        return data
    
    def FNG_summary(self, shcode):
        # FNG 요약
        self.get_access_token()

        path = "stock/investinfo"
        url = f"{self.baseurl}/{path}"
        headers = {
            "content-type":"application/json; charset=UTF-8",
            "authorization": f"Bearer {self.access_token}",
            "tr_cd":"t3320", 
            "tr_cont":"N",
            "tr_cont_key":"",
        }
        body = {
            "t3320InBlock": {
                "gicode": shcode
            }
        }
        res = requests.post(url, headers=headers, data=json.dumps(body))
        return res