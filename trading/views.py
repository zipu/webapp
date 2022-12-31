from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, View
from django.shortcuts import get_object_or_404
from django.http import JsonResponse

from django.db.models import Sum, Count, Avg, StdDev, F, FloatField, ExpressionWrapper
from trading.models import Asset
from trading.models import FuturesInstrument, FuturesAccount, FuturesStrategy\
                          ,FuturesTrade, Transaction, Tags, Currency, Note, NoteFile
from trading.models import StockTradeUnit, StockAccount, StockBuy, StockSell

from datetime import datetime, time, timedelta
import json, csv
from decimal import Decimal as D

import requests
from bs4 import BeautifulSoup as bs
import statistics 



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

class FuturesView(TemplateView):
    template_name = "trading/futures/futures.html"

    def get_context_data(self, **kwargs):
        #기간 설정
        context = super().get_context_data(**kwargs)
        #context['accounts'] = FuturesAccount.objects.all()
        context['strategies'] = FuturesStrategy.objects.all()
        #context['account'] = FuturesAccount.objects.get(symbol='FM02')
        context['activate'] = 'futures'
        return context

class FuturesStatView(TemplateView):
    """
    trading/futures 메인에서 통계자료를 ajax로 전송하는 뷰
    """
    def get(self, request, *args, **kwargs):
        query= request.GET
        trades = FuturesTrade.objects.filter(is_open=False)\
                .annotate(
                    profit_krw = ExpressionWrapper(
                        F('realized_profit')*F('instrument__currency__rate'), output_field=FloatField()),
                    commission_krw = ExpressionWrapper(
                        F('commission')*F('instrument__currency__rate'),output_field=FloatField())
                ).order_by('end_date')
        
        if query.get('start'):
            # 부분 통계를 위해 그 이전까지의 수익을 합산한것을 원금으로 잡음
            olds = trades.filter(end_date__lt=query.get('start'))\
                         .annotate(
                           profit=F('realized_profit')*F('instrument__currency__rate'),
                           commission_krw = F('commission')*F('instrument__currency__rate'))\
                       .aggregate(Sum('profit'), Sum('commission_krw'))
            profit_diff = (olds['profit__sum'] or 0) - (olds['commission_krw__sum'] or 0) or 0
            
            trades = trades.filter(end_date__gte=query.get('start'))
        
        else:
            profit_diff = 0

        if query.get('end'):
            trades = trades.filter(end_date__lte=query.get('end'))
        
        if query.get('mental'):
            trades = trades.filter(mental=query.get('mental'))
        if query.get('strategy'):
            trades = trades.filter(strategy__id=query.get('strategy'))
        if query.get('tags'):
            tags = [x for x in query.get('tags').split(';') if x]
            trades = trades.filter(entry_tags__name__in=tags)\
                           .filter(exit_tags__name__in=tags)
        if query.get('timeframe'):
            trades = trades.filter(timeframe = query.get('timeframe'))
        
        account = FuturesAccount.objects.last()
        wins = trades.filter(profit_krw__gt=0)
        loses = trades.filter(profit_krw__lte=0)
        cnt = trades.count() #매매횟수

        trades_agg = trades.aggregate(
            Sum('profit_krw'), Sum('commission_krw'),
            Avg('profit_krw'), StdDev('profit_krw'),
        )
        
        wins_agg = wins.aggregate(
            Avg('profit_krw'), Sum('profit_krw')
        )
        loses_agg = loses.aggregate(
            Avg('profit_krw'), Sum('profit_krw')
        )

        principal = float(account.principal + profit_diff)
        revenue = trades_agg['profit_krw__sum'] or 0
        profit = wins_agg['profit_krw__sum'] or 0
        loss = loses_agg['profit_krw__sum'] or 0
        commission = trades_agg['commission_krw__sum'] or 0
        avg_profit = trades_agg['profit_krw__avg'] or 0
        std_profit = trades_agg['profit_krw__stddev'] or 0
        roe = revenue/principal if revenue and principal else 0
        if loses_agg['profit_krw__avg'] and wins_agg['profit_krw__avg']:
            pnl = -1*wins_agg['profit_krw__avg']/loses_agg['profit_krw__avg']
        else:
            pnl = 0
        win_rate = wins.count()/cnt if cnt else 0
        if trades.count():
            duration_in_year = (trades.last().end_date - trades.first().pub_date).days/365
            cagr = pow((principal+revenue-commission)/principal, 1/duration_in_year)-1
            data = {
                'principal':f'{principal:,.0f}',
                'revenue': f'{revenue:,.0f}',
                'profit':f'{profit:,.0f}',
                'loss':f'{loss:,.0f}',
                'commission':f'{commission:,.0f}',
                'avg_profit':f'{avg_profit:,.0f}',
                'std_profit':f'{std_profit:,.0f}',
                'pnl':f'{pnl:.2f}',
                'win_rate':f'{win_rate*100:.1f}',
                'roe':f'{roe*100:.1f}',
                'num_trades': cnt,
                #'chart_data': list(trades.values_list('end_date', 'profit_krw','commission_krw')),
                'principal_num': principal,
                'cagr': f'{cagr:,.2f}'
            }
        else:
            data = {
                'principal':f'{principal:,.0f}',
                'revenue': '0',
                'profit':'0',
                'loss':'0',
                'commission':'0',
                'avg_profit':'0',
                'std_profit':'0',
                'pnl':'0',
                'win_rate':'',
                'roe':'',
                'num_trades': 0,
                #'chart_data': list(trades.values_list('end_date', 'profit_krw','commission_krw')),
                'principal_num': principal,
                'cagr': '0'
            }

        #차트 데이터
        trades_by_day = trades.values('end_date__date')\
            .order_by('end_date__date')\
            .annotate(day_profit=Sum('profit_krw'),
                      day_commission=Sum('commission_krw'),
                      volume=Count('id'))
        
        data['chart_data'] = list(trades_by_day.values_list('end_date__date','day_profit','day_commission', 'volume'))
        #print(data)
        return JsonResponse(data, safe=False)

class FuturesTradeView(TemplateView):
    template_name = "trading/futures/trade.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        
        context['active'] = 'trade'
        trades = FuturesTrade.objects.order_by('-is_open', '-end_date')
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
            cons = trade.num_entry_cons - trade.num_exit_cons
            data.append(
                (trade, entries, exits, cons)
            )
        context['entry_strategies'] = FuturesStrategy.objects.filter(type='entry')
        context['exit_strategies'] = FuturesStrategy.objects.filter(type='exit')

        
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
        entry_tags = [x.strip(' ') for x in request.POST.get('entrytags').split(';') if x]
        exit_tags = [x.strip(' ') for x in request.POST.get('exittags').split(';') if x]
        # 태그 등록
        tags = set(entry_tags+exit_tags)
        Tags.objects.bulk_create([Tags(name=x) for x in tags if x], ignore_conflicts=True)
        trade = FuturesTrade.objects.get(id=id)
        if request.POST.get('mental'):
            trade.mental = request.POST.get('mental')
        if request.POST.get('entry_strategy'):
            trade.entry_strategy = FuturesStrategy.objects.get(id=request.POST.get('entry_strategy'))
        if request.POST.get('exit_strategy'):
            trade.exit_strategy = FuturesStrategy.objects.get(id=request.POST.get('exit_strategy'))
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
        if request.GET.get('currency'):
            Currency.update()
        
        if request.GET.get('create_trades'):
            FuturesTrade.create_trades()

        context = self.get_context_data()
        context['active'] = 'transaction'
        context['currencies'] = Currency.objects.all()
        
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
            transactions = []
            if not Transaction.objects.filter(order_id=line[1], ebest_id=line[3]):
                num_cons = int(line[14])
                # 체결 수량 1개당 한개의 transaction으로 함
                for i in range(int(line[14])):
                    instrument = FuturesInstrument.objects.get(symbol=line[4][:-3])
                    price = instrument.convert_to_decimal(line[13].replace(',',''))
                    transactions.append(Transaction(
                        instrument = instrument,
                        order_id = line[1],
                        ebest_id = line[3],
                        ebest_code = line[4],
                        date = date,
                        position = 1 if line[12]=="매수" else -1,
                        price = price,
                        commission = float(line[16])/num_cons
                    ))
            Transaction.objects.bulk_create(transactions)
        # 거래 기록 생성
        #FuturesTrade.add_transactions()
        return redirect('transaction', page=1)

class NoteView(TemplateView):
    template_name = "trading/note.html"

    def get(self, request, *args, **kwargs):
        # 노트 삭제
        if request.GET.get('id'):
            note = Note.objects.get(id=request.GET.get('id'))
            note.delete()

        context = self.get_context_data()
        context['active'] = 'note'
        
        notes = Note.objects.order_by('-date')
        paginate_by = 20 # 페이지당 30개
        cnt = notes.count()
        num_pages = int(cnt/paginate_by)+1
        page = kwargs['page']
        obj_start = (page-1)*paginate_by
        obj_end = obj_start + paginate_by
        context['notes'] = notes.all()[obj_start:obj_end]

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

        return render(request, NoteView.template_name, context=context)

    def post(self, request, *args, **kwargs):
        note = Note(
            title = request.POST.get('title'),
            memo = request.POST.get('memo').strip(),
        )
        
        note.save()

        if request.POST.get('tags'):
            tags = [x.strip(' ') for x in request.POST.get('tags').split(';') if x]
            Tags.objects.bulk_create([Tags(name=x) for x in tags if x], ignore_conflicts=True)
            note.tags.add(*Tags.objects.filter(name__in=tags))
        
        if request.FILES.get('file'):
            for file in request.FILES.getlist('file'):
                NoteFile(
                    file = file,
                    note = note,
                    name = str(file)
                ).save()

        return redirect('note', page=1)



class StockView(TemplateView):
    template_name = "trading/stock/stock.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activate'] = 'stock'
        context['account'] = StockAccount.objects.all().order_by('-id').first()
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




        