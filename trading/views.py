from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, View
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.middleware import csrf

from django.db.models import Sum, Count, Avg, StdDev
from trading.models import Asset, Record, CashAccount
from trading.models import FuturesInstrument, FuturesEntry, FuturesExit, FuturesAccount,\
                           FuturesStrategy, FuturesTrade, Transaction, Tags
from trading.models import StockTradeUnit, StockAccount, StockBuy, StockSell, CashAccount
from trading.models import create_record, CurrencyRates

from datetime import datetime, time, timedelta
import json, csv
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

class ChartView(View):
    """ 차트 데이터 반환용 뷰"""
    def get(self, request, *args, **kwargs):
        records = Record.objects.filter(account_symbol=kwargs['account']).order_by('date','id')
        data = list(records.all().values_list(
            'date', 'value', 'risk_excluded_value','volatility_day', 'volatility', 'principal')) 
        return JsonResponse(data, safe=False)

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
    template_name = "trading/futures/futures.html"

    def get_context_data(self, **kwargs):
        #기간 설정
        #duration = self.request.GET.get('duration')
        context = super().get_context_data(**kwargs)
        context['accounts'] = FuturesAccount.objects.all()
        context['strategies'] = FuturesStrategy.objects.all()
        #context['account'] = FuturesAccount.objects.get(id=kwargs['system'])
        #if kwargs['system'] == 0:
        #    context['account'] = {'id':0, 'account_name': '시스템 합산'}
        #    record = Record.objects.filter(account_symbol='FA')
            #context['record'] = Record.objects.filter(account_symbol='FA').latest('date','id')
        
        #else:
        context['account'] = FuturesAccount.objects.get(symbol='FM02')
        record = Record.objects.filter(account_symbol=context['account'].symbol)
            #context['record'] = Record.objects.filter(account_symbol=context['account'].symbol)\
            #                     .latest('date','id')
        context['record'] = record.latest('date','id')
        context['active'] = 'futures'
        return context

class FuturesStatView(TemplateView):
    """
    trading/futures 메인에서 통계자료를 ajax로 전송하는 뷰
    """
    def get(self, request, *args, **kwargs):
        query= request.GET
        print(query)
        trades = FuturesTrade.objects.filter(is_open=False)
        if query.get('start'):
            trades = trades.filter(pub_date__gte=query.get('start'))
            # 부분 통계를 위해 그 이전까지의 수익을 합산한것을 원금으로 잡음
            profit_diff = trades.filter(pub_date__lt=query.get('start'))\
                       .aggregate(Sum('realized_profit_krw'))['realized_profit_krw__sum'] or 0
        else:
            profit_diff = 0

        if query.get('end'):
            trades = trades.filter(pub_date__lte=query.get('end'))
        if query.get('mental'):
            trades = trades.filter(mental=query.get('mental'))
        if query.get('strategy'):
            trades = trades.filter(strategy__id=query.get('strategy'))
        if query.get('tags'):
            tags = [x for x in query.get('tags').split(';') if x]
            trades = trades.filter(entry_tags__name__in=tags)\
                           .filter(exit_tags__name__in=tags)
        if query.get('timeframe'):
            timeframe = query.get('timeframe')
            if timeframe == 'day':
                trades = trades.filter(duration__lte=24*3600)
            elif timeframe == 'swing':
                trades = trades.filter(duration__gt=24*3600)\
                               .filter(duration__lte=3600*24*7)
            elif timeframe == 'long':
                trades = trades.filter(duration__gt=3600*24*7)
        
        account = FuturesAccount.objects.last()
        wins = trades.filter(realized_profit__gt=0)
        loses = trades.filter(realized_profit__lte=0)
        cnt = trades.count() #매매횟수

        trades_agg = trades.aggregate(
            Sum('realized_profit_krw'), Sum('paper_profit'), Sum('commission_krw'),
            Avg('realized_profit_krw'), StdDev('realized_profit_krw'),
            Avg('duration')
        )
        wins_agg = wins.aggregate(
            Avg('realized_profit_krw'), Sum('realized_profit_krw')
        )
        loses_agg = loses.aggregate(
            Avg('realized_profit_krw'), Sum('realized_profit_krw')
        )

        data ={}
        principal = account.principal + profit_diff
        revenue = trades_agg['realized_profit_krw__sum']
        profit = wins_agg['realized_profit_krw__sum']
        loss = loses_agg['realized_profit_krw__sum']
        commission = trades_agg['commission_krw__sum']
        avg_profit = trades_agg['realized_profit_krw__avg']
        std_profit = trades_agg['realized_profit_krw__stddev']
        avg_duration = trades_agg['duration__avg']
        roe = revenue/principal if principal else 0
        if loses_agg['realized_profit_krw__avg']:
            pnl = -1*wins_agg['realized_profit_krw__avg']/loses_agg['realized_profit_krw__avg']
        else:
            pnl = 0
        win_rate = wins.count()/cnt
        data['stat'] = {
            'principal':principal,
            'revenue': revenue,
            'profit':profit,
            'loss':loss,
            'commission':commission,
            'avg_profit':avg_profit,
            'std_profit':std_profit,
            'avg_duration':avg_duration,
            'pnl':pnl,
            'win_rate':win_rate,
            'roe':roe
        }


        # 일별로 그룹화된 쿼리셋
        trades_by_day = trades.values('pub_date__date')\
            .order_by('pub_date__date')\
            .annotate(profit=Sum('realized_profit_krw'),
                      commission=Sum('commission_krw'))
        print(trades_by_day)
        


        data['day'] ={
            'avg_profit': trades_by_day['realized_profit_krw__avg'],
            'std_profit': trades_by_day['realized_profit_krw__stddev'],
            'commission': trades_by_day['commission__krw__avg'],
            'num_cons': trades_by_day['num_entry_cons__avg'],
            'win_rate': win_rate,
            'pnl': pnl
        }

        print(data['day'])


        return JsonResponse(data, safe=False)

class FuturesTradeView(TemplateView):
    template_name = "trading/futures/trade.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        
        context['active'] = 'trade'
        trades = FuturesTrade.objects.order_by('-is_open', '-pub_date')
        paginate_by = 20 # 페이지당 30개
        cnt = trades.count()
        num_pages = int(cnt/paginate_by)+1
        page = kwargs['page']
        obj_start = (page-1)*paginate_by
        obj_end = obj_start + paginate_by
        trades = trades.all()[obj_start:obj_end]
        
        # 거래 정보 오브젝트
        data = []
        for trade in trades:
            entries= trade.transactions.filter(position = trade.position)\
                            .values('price').annotate(cnt=Count('price'))
            exits = trade.transactions.filter(position = trade.position*-1)\
                            .values('price').annotate(cnt=Count('price'))
            duration = timedelta(seconds=trade.duration) if trade.duration else ''
            data.append(
                (trade, entries, exits, duration)
            )
        context['strategies'] = FuturesStrategy.objects.all()

        
        # 페이지 오브젝트
        context['data'] = data
        context['is_paginated'] = True if num_pages > 1 else False
        pages = [ i for i in range(1,num_pages+1) ] 
        ranges = [[i for i in range(k,k+10) if i <= pages[-1]] for k in pages[::10]]
        rng = [k for k in ranges if page in k][0]
        context['page_obj']={
            'page': page,
            'num_page': num_pages,
            'previous': page-1,
            'next': page+1,
            'rng': rng
        }

        return render(request, FuturesTradeView.template_name, context=context)

    def post(self, request, *args, **kwargs):
        id = request.POST.get('id')
        entry_tags = [x for x in request.POST.get('entrytags').split(';') if x]
        exit_tags = [x for x in request.POST.get('exittags').split(';') if x]
        # 태그 등록
        tags = set(entry_tags+exit_tags)
        Tags.objects.bulk_create([Tags(name=x) for x in tags if x], ignore_conflicts=True)

        
        trade = FuturesTrade.objects.get(id=id)
        if request.POST.get('mental'):
            trade.mental = request.POST.get('mental')
        if request.POST.get('strategy'):
            trade.strategy = FuturesStrategy.objects.get(id=request.POST.get('strategy'))
        if request.POST.get('stopprice'):
            trade.stop_price = D(request.POST.get('stopprice'))
        trade.entry_tags.add(*Tags.objects.filter(name__in=entry_tags))
        trade.exit_tags.add(*Tags.objects.filter(name__in=exit_tags))
        trade.entry_reason = request.POST.get('entryreason').strip()
        trade.exit_reason = request.POST.get('exitreason').strip()
        #trade.save()
        trade.update()

        return redirect('futurestrade', page=1)

class TransactionView(TemplateView):
    template_name = "trading/futures/transaction.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        context['active'] = 'transaction'
        
        transactions = Transaction.objects.order_by('-date')
        paginate_by = 20 # 페이지당 30개
        cnt = transactions.count()
        num_pages = int(cnt/paginate_by)+1
        page = kwargs['page']
        obj_start = (page-1)*paginate_by
        obj_end = obj_start + paginate_by
        context['transactions'] = transactions.all()[obj_start:obj_end]

        context['is_paginated'] = True if num_pages > 1 else False
        pages = [ i for i in range(1,num_pages+1) ] 
        ranges = [[i for i in range(k,k+10) if i <= pages[-1]] for k in pages[::10]]
        rng = [k for k in ranges if page in k][0]

        context['page_obj']={
            'page': page,
            'num_page': num_pages,
            'previous': page-1,
            'next': page+1,
            'rng': rng
        }
        return render(request, TransactionView.template_name, context=context)

    def post(self, request, *args, **kwargs):
        # 거래내역 생성
        """
        if request.GET.get('key') == 'create_trade': 
            
            # 체결내역에 시스템 연결
            for tr, ac in request.POST.items():
                transaction = Transaction.objects.get(id=tr)
                account = FuturesAccount.objects.get(id=ac[0])
                transaction.account = account
                transaction.save()
            
            # 신규등록된 체
            FuturesTrade.add_transactions()
            return JsonResponse(True, safe=False)
        """
        # 체결기록 등록
        
        file_data = csv.reader(request.FILES['file'].read().decode("cp949").splitlines())
        for l, line in enumerate(file_data):
            if l < 2:
                continue
            # 중복 신청시 코등 안보임 해결
            if not line[4]:
                line[4] = symbol
            else:
                symbol = line[4]
            
            date = datetime.strptime(line[19], "%Y-%m-%d %H:%M:%S" )
            if not Transaction.objects.filter(ebest_id=line[3]):
                num_cons = int(line[14])
                # 체결 수량 1개당 한개의 transaction으로 함
                for i in range(int(line[14])):
                    Transaction(
                        instrument = FuturesInstrument.objects.get(symbol=line[4][:-3]),
                        ebest_id = line[3],
                        ebest_code = line[4],
                        date = date,
                        position = 1 if line[12]=="매수" else -1,
                        price = line[13].replace(',',''),
                        commission = float(line[16])/num_cons
                    ).save()
        # 거래 기록 생성
        FuturesTrade.add_transactions()
        return redirect('transaction', page=1)

class StockView(TemplateView):
    template_name = "trading/stock/stock.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activate'] = 'stock'
        context['account'] = StockAccount.objects.all().order_by('-id').first()
        context['record'] = Record.objects.filter(account_symbol=context['account'].symbol)\
                            .latest('date','id')
        return context

class StockHistoryView(ListView):
    template_name = "trading/stock/stock_history.html"
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



        