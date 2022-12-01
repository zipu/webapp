from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, View
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.middleware import csrf

from django.db.models import Sum, Window, F
from trading.models import Asset, Record, CashAccount
from trading.models import FuturesInstrument, FuturesEntry, FuturesExit, FuturesAccount, FuturesStrategy
from trading.models import StockTradeUnit, StockAccount, StockBuy, StockSell, CashAccount
from trading.models import create_record, CurrencyRates

from datetime import datetime, time, timedelta
import json
from decimal import Decimal as D

import requests
from bs4 import BeautifulSoup as bs
import statistics 



# Create your views here.
class UpdateCurrencyRateView(TemplateView):
    """
     환율 갱신하는 뷰
    """
    def get(self, request, *args, **kwargs):
        result = CurrencyRates.update()
        return JsonResponse(result, safe=False)


class CreateRecordView(TemplateView):
    """ 수동 레코드 업데이트 """
    def get(self, request, *args, **kwargs):
        create_record('all')
        return JsonResponse('done', safe=False)


class UpdateView(TemplateView):
    """
    보유중인 상품의 매매가격을 업데이트하는 뷰
    """
    def get(self, request, *args, **kwargs):
        newdata = {
            'stock': [],
            'futures': []
        }

        #1. 환율 업데이트 
        newdata['currencyrates'] = CurrencyRates.update()
                
        #2. 가격 업데이트
        
        #서버에 저장된 주식/선물 가격
        stock_codes = list(StockTradeUnit.objects.filter(is_open=True).values_list('code', flat=True))
        futures_codes = list(FuturesEntry.objects.filter(is_open=True).values_list('code', 'instrument__number_system'))
        olddata={
            'stock': stock_codes,
            'futures': list(set(futures_codes)),
        }
        
        #LOGIN_URL = "http://cyosep.appspot.com/login/"
        #UPDATE_URL="http://cyosep.appspot.com/trading/update/"
        STOCK_PRICE_URL = "https://finance.naver.com/item/sise.nhn?code="
        FUTURES_PRICE_URL = "https://quotes.esignal.com/esignalprod/quote.action?symbol="

        #네이버 증권에서 주식시세 불러오기
        for code in olddata['stock']:
            response = requests.get(STOCK_PRICE_URL+code)
            if response.ok:
                value = int(bs(response.text, "html.parser").find(id="_nowVal")\
                     .text.replace(',',''))
                newdata['stock'].append([code,value])
                print(f"주식시세 업데이트: 종목코드({code}), 가격({value})")
            else:
                raise ValueError("주식시세 업데이트에 실패했습니다")


        #해외선물 시세 업데이트
        for code, number_system in olddata['futures']:
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

                newdata['futures'].append([code, value])
                print(f"해외선물 시세 업데이트: 종목코드({code}), 가격({value})")
            else:
                raise ValueError(f"해외선물 시세 업데이트에 실패했습니다")

        #3. 서버에 저장
        for code, price in newdata['stock']:
            trades = StockTradeUnit.objects.filter(is_open=True, code=code).all()
            for trade in trades:
                trade.cur_stock_price = price
                trade.save()
        
        for code, price in newdata['futures']:
            trades = FuturesEntry.objects.filter(is_open=True, code=code).all()
            for trade in trades:
                trade.current_price = D(str(price))
                trade.save()
        
        create_record('all')
        return JsonResponse(newdata, safe=False)



# slack 으로 매매내역 요약 전송
class ReportView(TemplateView):
    def get(self, request, *args, **kwargs):
        asset = Record.objects.filter(account_symbol='A').latest('date','id')
        futures = FuturesAccount.objects.all().first()
        stock = StockAccount.objects.all().first()

        data={
            'asset': {
                'principal': int(asset.principal),
                'value': int(asset.value),
                'profit': int(asset.gross_profit),
                'rate_profit': round(float(asset.rate_profit),2)
            },
            'futures': {
                'principal': int(futures.principal),
                'value': int(futures.value),
                'profit': int(futures.gross_profit),
                'risk': int(futures.risk),
                'entries': []
            },
            'stock': {
                'principal': int(stock.principal),
                'value': int(stock.value),
                'profit': int(stock.value - stock.principal),
                'value_stock': int(stock.value_stock),
                'balance': int(stock.balance),
                'risk': int(stock.risk),
                'trades': []
            }
        }

        entries = futures.entries.filter(is_open=True).all()
        for entry in entries:
            e = {
                'name': entry.instrument.name,
                'position': entry.position,
                'contracts': entry.num_open_cons,
                'entry_price': float(entry.entry_price),
                'cur_price': float(entry.current_price),
                'stop_price': float(entry.stop_price),
                'profit': int(entry.current_profit),
                'risk': int(entry.current_risk),
                'remains': (entry.expiration - datetime.today().date()).days
            }
            data['futures']['entries'].append(e)

        trades = stock.trades.filter(is_open=True).all()
        for trade in trades:
            e = {
                'name': trade.name,
                'num': trade.num_hold,
                'amount': int(trade.purchase_amount),
                'buy_price': float(trade.avg_buy_price),
                'cur_price': float(trade.cur_stock_price),
                'stop_price': float(trade.stop_price),
                'profit': int(trade.value_stock),
                'risk': int(trade.risk)
            }
            data['stock']['trades'].append(e)

        return JsonResponse(data, safe=False, json_dumps_params={'ensure_ascii': False})


class ChartView(View):
    """ 차트 데이터 반환용 뷰"""
    def get(self, request, *args, **kwargs):
        records = Record.objects.filter(account_symbol=kwargs['account']).order_by('date','id')
        data = list(records.all().values_list(
            'date', 'value', 'risk_excluded_value','volatility_day', 'volatility', 'principal')) 
        return JsonResponse(data, safe=False)

class StatView(View):
    """ 통계 데이터 반환용 뷰 """
    
    def get(self, request, *args, **kwargs):
        

        duration = int(request.GET.get('duration'))
        system = FuturesAccount.objects.get(id=kwargs['account'])
        since = datetime.now()-timedelta(days=duration)
        
        if request.GET.get('strategy'):
            strategyid = int(request.GET.get('strategy'))
            entries = system.entries.filter(date__gte=since, strategy__id=strategyid)
        else:
            entries = system.entries.filter(date__gte=since)
        
        print("통계 데이터 뷰")
        print(system, kwargs)

        stat = {
            'gross_profit':0, #누적손익
            'net_profit': 0, #순손익 (누적손인 - 수수료)
            'cum_profit': 0, #누적수익
            'cum_loss':0, #누적손실
            'winrate':0, 
            'pnl_per_trade': 0, #매매당 손익비
            'avg_profit_day':0, #일평균 손익
            'avg_profit_trade':0, #매매당 평균 손익
            'avg_profit_std':0, #손익 표준편차
            'avg_trade_day':0, #일 평균 매매횟수
            'cum_commission':0, #누적 수수료
            'avg_commission':0 #평균 수수료
        }
       

        win_trades = []
        loss_trades = []
        for entry in entries:
            stat['cum_commission'] += entry.commission
            if entry.is_open:
                #평가손익합산
                cur_profit = entry.current_profit
                stat['gross_profit'] += cur_profit
                if cur_profit >= 0:
                    stat['cum_profit'] += cur_profit
                else: 
                    stat['cum_loss'] += cur_profit

            if entry.exits.all():
                profit = sum([p.profit for p in entry.exits.all()])
                if profit >= 0:
                    win_trades.append(profit)
                else:
                    loss_trades.append(profit)

        num_trades = entries.count() #매매횟수
        days = round(duration*5/7)  #영업일 
        trades = win_trades+loss_trades
        
        stat['cum_profit'] = sum(win_trades)
        stat['cum_loss'] = sum(loss_trades)
        gross_profit = stat['cum_profit'] + stat['cum_loss']
        
        stat['gross_profit'] += gross_profit
        stat['net_profit'] = stat['gross_profit'] - stat['cum_commission']
        if num_trades > 0:
            stat['winrate'] = 100*len(win_trades)/num_trades
            stat['avg_profit_trade'] = gross_profit/num_trades
            
        if loss_trades and win_trades:
            stat['pnl_per_trade'] = -(stat['cum_profit']/len(win_trades))/(stat['cum_loss']/len(loss_trades))
        stat['avg_profit_day'] = gross_profit/days
        stat['avg_profit_std'] = statistics.pstdev(trades)
        stat['avg_trade_day'] = num_trades/days
        stat['avg_commission'] = stat['cum_commission']/days

        #print(stat)

        return JsonResponse(stat, safe=False)



class AssetView(TemplateView):
    template_name = "trading/asset.html"

    def get_context_data(self, **kwargs):
       context = super().get_context_data(**kwargs)
       context['record'] = Record.objects.filter(account_symbol='A').latest('date', 'id')
       context['cash'] = CashAccount.objects.all().latest('date','id').total
       context['stock'] = StockAccount.objects.all().first().value
       context['futures'] = FuturesAccount.objects.all().aggregate(Sum('value'))['value__sum']
       context['activate'] = 'asset'

       return context

class FuturesView(TemplateView):
    template_name = "trading/futures.html"

    def get_context_data(self, **kwargs):
        #기간 설정
        #duration = self.request.GET.get('duration')
        
        context = super().get_context_data(**kwargs)
        context['accounts'] = FuturesAccount.objects.all()
        context['strategies'] = FuturesStrategy.objects.all()
        #context['account'] = FuturesAccount.objects.get(id=kwargs['system'])
        if kwargs['system'] == 0:
            context['account'] = {'id':0, 'account_name': '시스템 합산'}
            record = Record.objects.filter(account_symbol='FA')
            #context['record'] = Record.objects.filter(account_symbol='FA').latest('date','id')
        
        else:
            context['account'] = FuturesAccount.objects.get(id=kwargs['system'])
            record = Record.objects.filter(account_symbol=context['account'].symbol)
            #context['record'] = Record.objects.filter(account_symbol=context['account'].symbol)\
            #                     .latest('date','id')
        context['record'] = record.latest('date','id')
        context['activate'] = 'futures'
        return context

class FuturesHistoryView(ListView):
   template_name = "trading/futures_history.html"
   model = FuturesEntry
   #queryset = FuturesEntry.objects.filter(system__id=1).order_by('-pk')
   context_object_name = "entries"
   paginate_by = 10

   def get_queryset(self):
    return FuturesAccount.objects.get(id=self.kwargs['system']).entries.order_by('-is_open','-exits__date','-date')

   def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    start = int(context['page_obj'].number/10)+1
    end = min(start+10, context['page_obj'].paginator.num_pages+1)
    context['range'] = range(start, end)
    return context

class StockView(TemplateView):
    template_name = "trading/stock.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activate'] = 'stock'
        context['account'] = StockAccount.objects.all().order_by('-id').first()
        context['record'] = Record.objects.filter(account_symbol=context['account'].symbol)\
                            .latest('date','id')
        return context

class StockHistoryView(ListView):
    template_name = "trading/stock_history.html"
    model = StockTradeUnit
    queryset = StockTradeUnit.objects.all().order_by('-id')
    context_object_name = "trades"
    paginate_by = 10
 
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        start = int(context['page_obj'].number/10)+1
        end = min(start+10, context['page_obj'].paginator.num_pages+1)
        context['range'] = range(start, end)
        return context

class CashView(TemplateView):
    template_name = "trading/cash.html"

    def get_context_data(self, **kwargs):
       context = super().get_context_data(**kwargs)
       #context['account'] = FuturesAccount.objects.get(id=kwargs['system'])
       context['account'] = CashAccount.objects.all().latest('date', 'id')
       context['record'] = Record.objects.filter(account_symbol=context['account'].symbol)\
                            .latest('date', 'id')
       context['activate'] = 'cash'
       return context