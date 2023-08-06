import os
import requests
import json, time, math
from datetime import datetime, timedelta

from pytrends.request import TrendReq

BASEDIR = os.path.dirname(__file__)
DBDIR = os.path.join(os.path.dirname(__file__), '..', 'data')


class Stock:

    def __init__(self):
        self.secret = self.get_secret("stock")
        self.baseurl = self.secret["BASEURL"]
        self.appkey = self.secret["APPKEY"]
        self.appsecretkey = self.secret['APPSECRETKEY']
        self.access_token = self.secret['access_token']
        self.token_issued_date = self.secret['token_issued_date']
        self.dart_api_key = self.secret['dart_api_key']
    
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
    
    @property
    def company_codes(self):
        filename = os.path.join(DBDIR, 'companies.json')
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)

    
    def download_market_data(self):
        #종목 정보 전체를 다운 받는 함수
        self.get_access_token()
        
        print("전체 종목 정보 다운로드")

        today = datetime.today().strftime('%Y%m%d')
        data = {}
        for item in self.get_item_list().json()['t8436OutBlock']:
                if item['etfgubun'] != "0":
                    continue
                if item['spac_gubun'] == 'Y':
                    continue

                if len(item['hname'])>2:
                    if item['hname'][-2:] == '우B' or item['hname'][-1] == '우'or item['hname'][-2:] == '우C'\
                        or '(전환)' in item['hname']:
                        continue
                
                data[item['shcode']] = {
                    'shcode': item['shcode'],
                    'expcode': item['expcode'],
                    'name': item['hname'],
                }
                        

        #fng 요약
        length = len(list(data.keys()))
        for i, shcode in enumerate(data.keys()):
            #fng 요약
            fng = self.FNG_summary(shcode).json()
            
            outblock = fng.get('t3320OutBlock')
            if not outblock: 
                continue
            outblock2 = fng.get('t3320OutBlock1')
            if not outblock2:
                continue

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
            data[shcode]['date'] = today
            with open(f'companies/{shcode}.json', 'w', encoding='utf-8') as f:
                json.dump(data[shcode], f, ensure_ascii=False)
            print(f"기업정보 다운로드: {data[shcode]['name']} ({i}/{length})")
            time.sleep(1.05)
        
        with open('companies/companies.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)

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
    

    def google_trend(self, name):
        
        # 구글 트랜드 
        trends = TrendReq(hl='ko-KR', tz=540)
        keywords = [name]
        trends.build_payload(keywords, timeframe='today 12-m', geo='KR')
        df = trends.interest_over_time()
        df['date'] = df.index.values.astype('M8[ms]').astype('int64')
        return df[['date',name]].values.tolist()


    def get_dart_company_code_list(self):
        """ 
        dart api 로 회사 번호 내려 받기
        return : [dict, dict, ...]
            dict: {'corp_code': '00434003',
                    'corp_name': '다코',
                    'stock_code': None,
                    'modify_date': '20170630'
                    }
        """


        import io
        import zipfile
        import xmltodict

        url = "https://opendart.fss.or.kr/api/corpCode.xml"
        params = {
            "crtfc_key": self.dart_api_key
        }
        resp = requests.get(url, params=params)
        f = io.BytesIO(resp.content)
        zfile = zipfile.ZipFile(f)
        xml = zfile.read("CORPCODE.xml").decode("utf-8")
        return xmltodict.parse(xml)['result']['list']
    
    def update_company_codes(self):
        itemlist = self.get_item_list().json()['t8436OutBlock']
        dart_codes = self.get_dart_company_code_list()
        today = datetime.today().strftime('%Y%m%d')
        data = {}
        for item in itemlist:
                if item['etfgubun'] != "0":
                    continue
                if item['spac_gubun'] == 'Y':
                    continue

                if len(item['hname'])>2:
                    if item['hname'][-2:] == '우B' or item['hname'][-1] == '우'or item['hname'][-2:] == '우C'\
                        or '(전환)' in item['hname']:
                        continue
                
                data[item['shcode']] = {
                    'shcode': item['shcode'],
                    'expcode': item['expcode'],
                    'name': item['hname'],
                    'gubun': item['gubun']
                }
        for item in data.values():
            for dart in dart_codes:
                 if item['shcode'] ==  dart['stock_code']:
                    item.update({'dart_code': dart['corp_code']})
        filename = os.path.join(DBDIR, 'companies.json')
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        
    

    def update_cfs(self, year, quarter):
        shcodes = {}
        dart_codes = []
        for item in self.company_codes.values():
            shcodes[item['shcode']] = []
            dart_codes.append(item['dart_code'])


        #filename = os.path.join(DBDIR, 'cfs', f"{shcode}.json")
        #with open(filename, 'r', encoding='utf-8') as f:
        #    file = json.load(f)


        quarter_index =["","11013","11012","11014","11011"]
        url = "https://opendart.fss.or.kr/api/fnlttMultiAcnt.json"
        print("재무제표 다운로드..")
        length = math.ceil(len(dart_codes)/100)
        print(len(dart_codes),length)
        for i in range(length):
            print(i)
            params = {
                "crtfc_key": self.dart_api_key,
                "corp_code": ','.join(dart_codes[i*100:i*100+100]),
                "bsns_year": year,
                "reprt_code": quarter_index[quarter],
            }
            resp = requests.get(url, params=params)
            if not resp.json().get('list'):
                continue
            for item in resp.json().get('list'):
                if item['fs_div'] == 'CFS':
                    shcodes[item['stock_code']].append(item)
            
        
        ords = {
                '1': 'current_asset',
                '3': 'non_current_asset',
                '5': 'asset',
                '7': 'current_liability',
                '9': 'non_current_liability',
                '11': 'liability',
                '13': 'capital',
                '17': 'retained_earnings',
                '21': 'equity',
                '23': 'revenue',
                '25': 'operating_income',
                '27': 'net_income_before_tax',
                '29': 'net_income'
        }
        print("기록중..")
        for shcode, jemu in shcodes.items():
            if not jemu:
                continue
            flag = ['1','3','5','7','9','11','13','17','21','23','25','27','29']
            filename = os.path.join(DBDIR, 'cfs', f"{shcode}.json")
            with open(filename, 'r', encoding='utf-8') as f:
                file = json.load(f)
            
            date = jemu[0]['thstrm_dt'][:10].replace('.','')
            if date in file['cfs']['date']:
                continue
            else:
                file['cfs']['date'].append(date)
            
            for item in jemu:
                amount = item['thstrm_amount']
                name = ords[item['ord']]
                flag.remove(item['ord'])
                file['cfs'][name].append(amount)
            for empty in flag:
                
                name = ords[empty]
                file['cfs'][name].append('')
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(file, f, ensure_ascii=False)
    