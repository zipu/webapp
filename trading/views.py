from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView
#from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.core.serializers import serialize


from django.db.models import Sum, Count, Avg, StdDev, F, FloatField, ExpressionWrapper,Func, Q, Max, Min
from django.db.models import IntegerField, Case, When, Value
from django.db.models.functions import Cast, TruncDate
from trading.models import Asset
from trading.models import FuturesInstrument, FuturesAccount, FuturesStrategy\
                          ,FuturesTrade, Transaction, Tags, Currency, Note, NoteFile
from trading.models import StockTradeUnit, StockAccount, StockBuy, StockSell, KiwoomPosition
from trading.models import UserGoal

from datetime import datetime, time, timedelta
import json, csv
from decimal import Decimal as D

import requests
from bs4 import BeautifulSoup as bs
import statistics 

from .api import stockapi, futuresapi, cftc
from tools.ebest.futures import Futures


class UnixTimestamp(Func):
    """
    mysql에서 로드한 datetime 을 초단위 timestamp로 변환
    """
    function = None #'UNIX_TIMESTAMP'
    template = "(UNIX_TIMESTAMP(%(expressions)s) * 1000)"#"%(function)s(%(expressions)s)"
    output_field = IntegerField()

def is_ajax(request):
  """ 들어온 request 가 ajax인지 아닌지 확인"""
  return request.headers.get('x-requested-with') == 'XMLHttpRequest'

class FuturesView(TemplateView):
    template_name = "trading/futures/futures.html"

    def get_context_data(self, **kwargs):
        #기간 설정
        context = super().get_context_data(**kwargs)
        #context['accounts'] = FuturesAccount.objects.all()
        context['entry_strategies'] = FuturesStrategy.objects.filter(type='entry')
        context['exit_strategies'] = FuturesStrategy.objects.filter(type='exit')
        #context['account'] = FuturesAccount.objects.get(symbol='FM02')
        context['activate'] = 'futures'

        # UserGoal 기반 알림 생성
        goal = UserGoal.objects.first()
        if goal:
            alerts = []
            today = datetime.now()

            # 일일 거래 횟수 체크
            today_trades = FuturesTrade.objects.filter(
                pub_date__date=today.date()
            ).count()

            if today_trades >= goal.max_trades_per_day:
                alerts.append({
                    'level': 'high',
                    'message': f'오늘 {today_trades}건 거래를 했습니다. 일일 최대 거래 횟수({goal.max_trades_per_day}건)에 도달했습니다.'
                })

            # 주간 손실 한도 체크
            week_start = today - timedelta(days=today.weekday())
            week_trades = FuturesTrade.objects.filter(
                is_open=False,
                end_date__gte=week_start
            ).annotate(
                profit_krw=ExpressionWrapper(
                    F('realized_profit') * F('instrument__currency__rate'),
                    output_field=FloatField()
                )
            )

            week_profit = week_trades.aggregate(Sum('profit_krw'))['profit_krw__sum'] or 0

            if week_profit < -float(goal.max_loss_limit):
                alerts.append({
                    'level': 'high',
                    'message': f'이번 주 손실이 ${abs(week_profit):.0f}입니다. 최대 손실 한도(${goal.max_loss_limit})를 초과했습니다. 거래를 중단하세요.'
                })

            # 연속 손실 체크
            recent_trades = list(FuturesTrade.objects.filter(is_open=False)\
                .annotate(
                    profit_krw=ExpressionWrapper(
                        F('realized_profit') * F('instrument__currency__rate'),
                        output_field=FloatField()
                    )
                ).order_by('-end_date')[:goal.alert_consecutive_losses])

            if len(recent_trades) == goal.alert_consecutive_losses:
                all_losses = all(t.profit_krw <= 0 for t in recent_trades)
                if all_losses:
                    alerts.append({
                        'level': 'high',
                        'message': f'{goal.alert_consecutive_losses}연속 손실이 발생했습니다. 거래를 멈추고 전략을 재검토하세요.'
                    })

            # 승률 저하 체크 (최근 10거래)
            recent_10 = list(FuturesTrade.objects.filter(is_open=False)\
                .annotate(
                    profit_krw=ExpressionWrapper(
                        F('realized_profit') * F('instrument__currency__rate'),
                        output_field=FloatField()
                    )
                ).order_by('-end_date')[:10])

            if len(recent_10) >= 10:
                # 승/무/패 구분 (무승부 제외하고 승률 계산)
                win_count = sum(1 for t in recent_10 if t.realized_profit_ticks > 5)
                lose_count = sum(1 for t in recent_10 if t.realized_profit_ticks < -5)
                win_lose_total = win_count + lose_count
                win_rate = (win_count / win_lose_total * 100) if win_lose_total else 0

                if win_rate < float(goal.alert_low_win_rate):
                    alerts.append({
                        'level': 'medium',
                        'message': f'최근 10건 승률이 {win_rate:.0f}%로 설정한 기준({goal.alert_low_win_rate}%) 이하입니다.'
                    })

            context['goal_alerts'] = alerts

        # 핵심 지표 계산 (전체 완료된 거래 기준)
        all_trades = FuturesTrade.objects.filter(is_open=False).annotate(
            profit_krw=ExpressionWrapper(
                F('realized_profit') * F('instrument__currency__rate'),
                output_field=FloatField()
            ),
            commission_krw=ExpressionWrapper(
                F('commission') * F('instrument__currency__rate'),
                output_field=FloatField()
            )
        )

        if all_trades.count() > 0:
            # 기본 통계
            total_trades = all_trades.count()
            # 승/무/패 구분 (틱 기준)
            wins = all_trades.filter(realized_profit_ticks__gt=5)
            draws = all_trades.filter(realized_profit_ticks__gte=-5, realized_profit_ticks__lte=5)
            losses = all_trades.filter(realized_profit_ticks__lt=-5)

            # 수익 지표
            total_profit = all_trades.aggregate(Sum('profit_krw'))['profit_krw__sum'] or 0
            total_commission = all_trades.aggregate(Sum('commission_krw'))['commission_krw__sum'] or 0
            net_profit = total_profit - total_commission
            avg_profit = total_profit / total_trades if total_trades else 0

            # 승률 및 손익비 (무승부 제외)
            win_lose_total = wins.count() + losses.count()
            win_rate = (wins.count() / win_lose_total * 100) if win_lose_total else 0
            avg_win = wins.aggregate(Avg('profit_krw'))['profit_krw__avg'] or 0
            avg_loss = losses.aggregate(Avg('profit_krw'))['profit_krw__avg'] or 0
            pnl_ratio = abs(avg_win / avg_loss) if avg_loss else 0

            # Optimal F
            win_rate_decimal = wins.count() / win_lose_total if win_lose_total else 0
            optimal_f = ((pnl_ratio + 1) * win_rate_decimal - 1) / pnl_ratio if pnl_ratio else 0

            # 최대/최소
            best_trade = all_trades.aggregate(Max('profit_krw'))['profit_krw__max'] or 0
            worst_trade = all_trades.aggregate(Min('profit_krw'))['profit_krw__min'] or 0

            # 표준편차
            std_profit = all_trades.aggregate(StdDev('profit_krw'))['profit_krw__stddev'] or 0

            # 기대값 계산
            expectancy = 0
            if win_rate_decimal and avg_win and avg_loss:
                loss_rate = 1 - win_rate_decimal
                expectancy = (win_rate_decimal * avg_win) - (loss_rate * abs(avg_loss))
                avg_commission_per_trade = total_commission / total_trades if total_trades else 0
                expectancy = expectancy - avg_commission_per_trade

            # 샤프 비율 계산
            sharpe_ratio = 0
            if std_profit and std_profit > 0:
                avg_net_profit = avg_profit - (total_commission / total_trades if total_trades else 0)
                sharpe_ratio = avg_net_profit / std_profit

            context['key_metrics'] = {
                'total_trades': total_trades,
                'total_profit': total_profit,
                'total_commission': total_commission,
                'net_profit': net_profit,
                'avg_profit': avg_profit,
                'win_rate': win_rate,
                'pnl_ratio': pnl_ratio,
                'optimal_f': optimal_f * 100,  # 퍼센트로 변환
                'best_trade': best_trade,
                'worst_trade': worst_trade,
                'expectancy': expectancy,
                'sharpe_ratio': sharpe_ratio,
            }
        else:
            context['key_metrics'] = None

        return context

class FuturesStatView(TemplateView):
    """
    trading/futures 메인에서 통계자료를 ajax로 전송하는 뷰
    """
    def get(self, request, *args, **kwargs):
        query= request.GET
        if query.get('account'):
            
            trades = FuturesTrade.objects.filter(account=query.get('account'))
            print(query.get('account'))
            print(trades)
        else:
            trades = FuturesTrade.objects.all()

        trades = trades.filter(is_open=False)\
                .annotate(
                    profit_krw = ExpressionWrapper(
                        F('realized_profit')*F('instrument__currency__rate'), output_field=FloatField()),
                    commission_krw = ExpressionWrapper(
                        F('commission')*F('instrument__currency__rate'),output_field=FloatField())
                ).order_by('end_date')
        
        if query.get('start'):
            # 부분 통계를 위해 그 이전까지의 수익을 합산한것을 원금으로 잡음
            #olds = trades.filter(end_date__lt=query.get('start'))\
            #             .annotate(
            #               profit=F('realized_profit')*F('instrument__currency__rate'),
            #               commission_krw = F('commission')*F('instrument__currency__rate'))\
            #           .aggregate(Sum('profit'), Sum('commission_krw'))
            #profit_diff = (olds['profit__sum'] or 0) - (olds['commission_krw__sum'] or 0) or 0
            
            trades = trades.filter(end_date__date__gte=query.get('start'))

        #else:
        #    profit_diff = 0

        if query.get('end'):
            trades = trades.filter(end_date__date__lte=query.get('end'))
        
        #if query.get('mental'):
        #    trades = trades.filter(mental=query.get('mental'))
        #if query.get('entry_strategy'):
        #    trades = trades.filter(entry_strategy__id=query.get('entry_strategy'))
        #if query.get('exit_strategy'):
        #    trades = trades.filter(exit_strategy__id=query.get('exit_strategy'))
        if query.get('tags'):
            tags = [x for x in query.get('tags').split(';') if x]
            trades = trades.filter(entry_tags__name__in=tags)\
                           .filter(exit_tags__name__in=tags)
        #if query.get('timeframe'):
        #    trades = trades.filter(timeframe = query.get('timeframe'))
        #account = FuturesAccount.objects.last()

        # 승/무/패 구분 (틱 기준)
        wins = trades.filter(realized_profit_ticks__gt=5)
        draws = trades.filter(realized_profit_ticks__gte=-5, realized_profit_ticks__lte=5)
        loses = trades.filter(realized_profit_ticks__lt=-5)
        cnt = trades.count() #매매횟수

        trades_agg = trades.aggregate(
            Sum('profit_krw'), Sum('commission_krw'),
            Avg('profit_krw'), StdDev('profit_krw'),
            Sum('realized_profit_ticks'),
            Avg('realized_profit_ticks'), #StdDev('realized_profit_ticks'),
        )
        
        wins_agg = wins.aggregate(
            Avg('profit_krw'), Sum('profit_krw'), 
            Avg('realized_profit_ticks'), Sum('realized_profit_ticks')
        )
        loses_agg = loses.aggregate(
            Avg('profit_krw'), Sum('profit_krw'),
            Avg('realized_profit_ticks'), Sum('realized_profit_ticks')
        )

        #principal = float(account.principal + profit_diff)
        commission = trades_agg['commission_krw__sum'] or 0
        revenue = trades_agg['profit_krw__sum'] or 0
        revenue_ticks = trades_agg['realized_profit_ticks__sum']
        #value = principal + revenue - commission
        profit = revenue - commission
        win = wins_agg['profit_krw__sum'] or 0
        avg_win = wins_agg['profit_krw__avg'] or 0
        win_ticks = wins_agg['realized_profit_ticks__sum'] or 0
        avg_win_ticks = wins_agg['realized_profit_ticks__avg'] or 0
        loss = loses_agg['profit_krw__sum'] or 0
        avg_loss = loses_agg['profit_krw__avg'] or 0
        loss_ticks = loses_agg['realized_profit_ticks__sum'] or 0
        avg_loss_ticks = loses_agg['realized_profit_ticks__avg'] or 0
        
        avg_profit = trades_agg['profit_krw__avg'] or 0
        avg_profit_ticks = trades_agg['realized_profit_ticks__avg'] or 0
        std_profit = trades_agg['profit_krw__stddev'] or 0
        #std_profit_ticks = trades_agg['realized_profit_ticks__stddev'] or 0

        #roe = revenue/principal if revenue and principal else 0
        if loses_agg['profit_krw__avg'] and wins_agg['profit_krw__avg']:
            pnl = -1*wins_agg['profit_krw__avg']/loses_agg['profit_krw__avg']
        else:
            pnl = 0

        # 승률 계산 (무승부 제외: 승 / (승 + 패))
        win_lose_count = wins.count() + loses.count()
        win_rate = wins.count() / win_lose_count if win_lose_count else 0

        optimal_f = ((pnl+1)*win_rate-1)/pnl if pnl else 0

        # key_metrics 계산 (최대/최소, 기대값, 샤프 비율)
        best_trade = trades.aggregate(Max('profit_krw'))['profit_krw__max'] or 0
        worst_trade = trades.aggregate(Min('profit_krw'))['profit_krw__min'] or 0

        # 기대값 계산: (승률 × 평균수익) - (패율 × 평균손실)
        # 수수료를 차감한 순수익 기준으로 계산
        expectancy = 0
        if win_rate and avg_win and avg_loss:
            loss_rate = 1 - win_rate
            # avg_loss는 음수이므로 절댓값 사용
            expectancy = (win_rate * avg_win) - (loss_rate * abs(avg_loss))
            # 수수료도 반영
            avg_commission_per_trade = commission / cnt if cnt else 0
            expectancy = expectancy - avg_commission_per_trade

        # 샤프 비율 계산: (평균 순수익) / (수익의 표준편차)
        sharpe_ratio = 0
        if std_profit and std_profit > 0:
            avg_net_profit = avg_profit - (commission / cnt if cnt else 0)
            sharpe_ratio = avg_net_profit / std_profit

        if trades.count():
            #duration_in_year = (trades.last().end_date - trades.first().pub_date).days/365
            
            #if duration_in_year > 0 and principal+revenue-commission > 0:
            #    cagr = pow((principal+revenue-commission)/principal, 1/duration_in_year)-1
            #else: 
            #    cagr = 0
            #print(principal, revenue, commission, duration_in_year)
            
            
            
            data = {
                #'value': value,
                #'principal':principal,
                'revenue': float(revenue) if revenue else 0,
                'revenue_ticks': float(revenue_ticks) if revenue_ticks else 0,
                'profit': float(profit) if profit else 0,
                'win': float(win) if win else 0,
                'win_ticks': float(win_ticks) if win_ticks else 0,
                'avg_win': float(avg_win) if avg_win else 0,
                'avg_win_ticks': float(avg_win_ticks) if avg_win_ticks else 0,
                'loss': float(loss) if loss else 0,
                'avg_loss': float(avg_loss) if avg_loss else 0,
                'loss_ticks': float(loss_ticks) if loss_ticks else 0,
                'avg_loss_ticks': float(avg_loss_ticks) if avg_loss_ticks else 0,
                'commission': float(commission) if commission else 0,
                'avg_profit': float(avg_profit) if avg_profit else 0,
                'avg_profit_ticks': float(avg_profit_ticks) if avg_profit_ticks else 0,
                #'std_profit':std_profit,
                #'std_profit_ticks':std_profit_ticks,
                'pnl': float(pnl) if pnl else 0,
                'win_rate': float(win_rate * 100) if win_rate else 0,
                #'roe':roe*100,
                'num_trades': int(cnt),
                #'cagr': cagr,
                'optimal_f': float(optimal_f) if optimal_f else 0,
                # key_metrics 추가
                'key_metrics': {
                    'total_trades': int(cnt),
                    'total_profit': float(revenue) if revenue else 0,
                    'total_commission': float(commission) if commission else 0,
                    'net_profit': float(profit) if profit else 0,
                    'avg_profit': float(avg_profit) if avg_profit else 0,
                    'win_rate': float(win_rate * 100) if win_rate else 0,
                    'pnl_ratio': float(pnl) if pnl else 0,
                    'optimal_f': float(optimal_f * 100) if optimal_f else 0,
                    'best_trade': float(best_trade) if best_trade else 0,
                    'worst_trade': float(worst_trade) if worst_trade else 0,
                    'expectancy': float(expectancy) if expectancy else 0,
                    'sharpe_ratio': float(sharpe_ratio) if sharpe_ratio else 0,
                    'day_avg_profit': 0,  # 아래에서 계산 후 업데이트
                }
            }
        else:
            data = {
                #'value': value,
                #'principal':principal,
                'revenue': 0,
                'revenue_ticks': 0,
                'profit':0,
                'win':0,
                'win_ticks':0,
                'avg_win':0,
                'avg_win_ticks':0,
                'loss':0,
                'avg_loss':0,
                'loss_ticks':0,
                'avg_loss_ticks':0,
                'commission':0,
                'avg_profit':0,
                'avg_profit_ticks':0,
                'std_profit':0,
                'std_profit_ticks':0,
                'pnl':0,
                'win_rate':0,
                #'roe':0,
                'num_trades': 0,
                #'cagr': 0,
                'optimal_f': 0,
                # key_metrics 추가
                'key_metrics': {
                    'total_trades': 0,
                    'total_profit': 0,
                    'total_commission': 0,
                    'net_profit': 0,
                    'avg_profit': 0,
                    'win_rate': 0,
                    'pnl_ratio': 0,
                    'optimal_f': 0,
                    'best_trade': 0,
                    'worst_trade': 0,
                    'expectancy': 0,
                    'sharpe_ratio': 0,
                }
            }

        #차트 데이터
        trades_by_day = trades.values('end_date__date')\
            .order_by('end_date__date')\
            .annotate(day_profit=Sum('profit_krw'),
                      day_commission=Sum('commission_krw'),
                      volume=Count('id'))

        # 날짜를 문자열로 변환하여 JSON 직렬화 가능하게 함
        chart_data = []
        for row in trades_by_day:
            chart_data.append([
                row['end_date__date'].isoformat() if row['end_date__date'] else None,
                float(row['day_profit']) if row['day_profit'] else 0,
                float(row['day_commission']) if row['day_commission'] else 0,
            ])
        data['chart_data'] = chart_data
        # 일간 데이터
        cnt = trades_by_day.count()
        revenue = trades_by_day.annotate(
                        revenue=F('day_profit') - F('day_commission'),
               )
        wins = revenue.filter(revenue__gt=0)
        win_revenue =  wins.aggregate(
                            Avg('revenue')
                        )['revenue__avg']
        lose_revenue = revenue.filter(revenue__lte=0).aggregate(
                            Avg('revenue')
                        )['revenue__avg']
        data['days'] = int(cnt)
        day_avg = revenue.aggregate(Avg('revenue'))['revenue__avg']
        data['day_avg_revenue'] = float(day_avg) if day_avg else 0
        data['day_win_rate'] = float(wins.count() / cnt) if cnt else 0
        data['day_pnl'] = float(abs(win_revenue / lose_revenue)) if (lose_revenue and win_revenue) else 0
        data['day_optimal_f'] = float(((1 + data['day_pnl']) * data['day_win_rate'] - 1) / data['day_pnl']) if data['day_pnl'] else 0

        # key_metrics에 일평균 수익 추가
        if 'key_metrics' in data:
            data['key_metrics']['day_avg_profit'] = float(day_avg) if day_avg else 0

        #print(data)
        return JsonResponse(data, safe=False)

class FuturesTradeView(TemplateView):
    template_name = "trading/futures/trade.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()

        context['active'] = 'trade'

        # 필터 처리
        filter_type = request.GET.get('filter', 'week')
        context['current_filter'] = filter_type  # 템플릿에 현재 필터 전달
        trades = FuturesTrade.objects.all()

        today = datetime.now()
        if filter_type == 'week':
            week_start = today - timedelta(days=today.weekday())
            trades = trades.filter(
                Q(is_open=True) | Q(end_date__gte=week_start)
            )
        elif filter_type == 'month':
            month_start = today.replace(day=1)
            trades = trades.filter(
                Q(is_open=True) | Q(end_date__gte=month_start)
            )
        # 'all'이면 필터링 하지 않음

        # 진행 중인 거래를 먼저 표시하고, 그 다음 최근 완료 거래 표시
        trades = trades.order_by('-is_open', '-end_date')
        paginate_by = 20 # 페이지당 20개
        cnt = trades.count()
        num_pages = max(1, (cnt + paginate_by - 1) // paginate_by)  # 올림 나눗셈
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

        # 페이지가 범위를 벗어나면 1페이지로 리다이렉트
        if page > num_pages or page < 1:
            from django.shortcuts import redirect
            return redirect('futurestrade', page=1)

        # 현재 페이지가 속한 range 찾기
        matching_ranges = [k for k in ranges if page in k]
        rng = matching_ranges[0] if matching_ranges else [page]

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
        trade.save()
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
        api = Futures()
        
        if api.get_access_token():
            start = (Transaction.objects.order_by('-date').first().date-timedelta(1)).strftime('%Y%m%d')
            new_transactions = api.transactions(start=start)
        else:
            new_transactions = {}
        

        for account, transactions_by_account in new_transactions.items():
            for transaction in transactions_by_account:
                # 중복 신청시 코등 안보임 해결
                symbol = transaction['IsuCodeVal']
                date = datetime.strptime(transaction['ExecDttm'][:-3], "%Y%m%d%H%M%S" )
                ebest_id = int(transaction['OvrsFutsExecNo'].lstrip('0'))
                
                transactions = []
                #print(ebest_id, date, symbol)
                if not Transaction.objects.filter(date=date, ebest_id=ebest_id):
                    #print(transaction)
                    num_cons = int(transaction['ExecQty'])
                    # 체결 수량 1개당 한개의 transaction으로 함
                    if symbol.count('_') == 2: #주식옵션
                        tradetype='StockOption'
                        code = symbol.split('_')[0][1:]
                        instrument = FuturesInstrument.objects.get(symbol=code)

                    elif symbol.count('_') == 1: #선물옵션
                        tradetype = 'Option'
                        code = symbol.split('_')[0][:-3]
                        filter = FuturesInstrument.objects.filter(option_codes__contains=code)
                        if not filter:
                            raise LookupError(f"No Futures Instrument contains option code: {code}")
                        
                        else: 
                            instrument = filter[0]

                    elif '-' in symbol:
                        tradetype = 'Spread'
                    
                    else:
                        tradetype = 'Futures'
                        
                        instrument = FuturesInstrument.objects.get(symbol=symbol[:-3])
                    
                    for i in range(num_cons):
                        #instrument = FuturesInstrument.objects.get(symbol=line[4][:-3])
                        if (tradetype == 'Option' or tradetype == 'StockOption') and not transaction['AbrdFutsExecPrc']:
                            price = 0
                        #elif tradetype == 'Option' and line[13]:
                        #    price = instrument.convert_to_decimal(line[13].replace(',',''))
                        else:
                            price = instrument.convert_to_decimal(transaction['AbrdFutsExecPrc'].replace(',',''))

                        transactions.append(Transaction(
                            instrument = instrument,
                            type = tradetype,
                            account = account,
                            order_id = transaction['OvrsFutsOrdNo'].lstrip('0'),
                            ebest_id = transaction['OvrsFutsExecNo'].lstrip('0'),
                            ebest_code = transaction['IsuCodeVal'],
                            date = date,
                            position = 1 if transaction['ExecBnsTpCode']=="2" else -1,
                            price = price,
                            commission = float(transaction['CsgnCmsn'])/num_cons or 0
                        
                        ))
                Transaction.objects.bulk_create(transactions)
        # 거래 기록 생성
        #FuturesTrade.add_transactions()
        return redirect('transaction', page=1)

# Views removed: KiwoomPositionView, LsApiTradeView, CFTCView, OptionStrategyView, CalculatorView
# These features are not used in the mobile PWA version


class InsightsView(TemplateView):
    """인사이트 페이지 - 자동 패턴 감지 및 분석"""
    template_name = "trading/futures/insights.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active'] = 'insights'

        # 최근 30일 거래 데이터 가져오기
        thirty_days_ago = datetime.now() - timedelta(days=30)
        trades = FuturesTrade.objects.filter(
            is_open=False,
            end_date__gte=thirty_days_ago
        ).annotate(
            profit_krw=ExpressionWrapper(
                F('realized_profit') * F('instrument__currency__rate'),
                output_field=FloatField()
            )
        ).order_by('-end_date')

        if trades.count() == 0:
            context['no_data'] = True
            return context

        # 1. 상품별 성과
        instrument_stats_raw = trades.values('instrument__name', 'instrument__symbol')\
            .annotate(
                total_profit=Sum('profit_krw'),
                num_trades=Count('id'),
                wins=Sum(Case(
                    When(realized_profit_ticks__gt=5, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )),
                losses=Sum(Case(
                    When(realized_profit_ticks__lt=-5, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                ))
            ).order_by('-total_profit')[:5]

        # 승률 계산 추가
        instrument_stats = []
        for item in instrument_stats_raw:
            wins = item['wins'] or 0
            losses = item['losses'] or 0
            win_lose_total = wins + losses
            win_rate = (wins / win_lose_total * 100) if win_lose_total else 0
            instrument_stats.append({
                'instrument__name': item['instrument__name'],
                'instrument__symbol': item['instrument__symbol'],
                'total_profit': item['total_profit'],
                'num_trades': item['num_trades'],
                'win_rate': win_rate
            })
        context['instrument_stats'] = instrument_stats

        # 3. 시간대별 분석 (시간대별 승률)
        from django.db.models.functions import ExtractHour
        hour_stats_raw = trades.annotate(hour=ExtractHour('pub_date'))\
            .values('hour')\
            .annotate(
                num_trades=Count('id'),
                avg_profit=Avg('profit_krw'),
                wins=Sum(Case(
                    When(realized_profit_ticks__gt=5, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )),
                losses=Sum(Case(
                    When(realized_profit_ticks__lt=-5, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                ))
            )

        # 승률 계산 후 정렬
        hour_stats_list = []
        for item in hour_stats_raw:
            wins = item['wins'] or 0
            losses = item['losses'] or 0
            win_lose_total = wins + losses
            win_rate = (wins / win_lose_total * 100) if win_lose_total else 0
            hour_stats_list.append({
                'hour': item['hour'],
                'num_trades': item['num_trades'],
                'avg_profit': item['avg_profit'],
                'win_rate': win_rate
            })

        # 승률 기준으로 정렬하여 상위 5개 선택
        hour_stats = sorted(hour_stats_list, key=lambda x: x['win_rate'], reverse=True)[:5]
        context['hour_stats'] = hour_stats

        # 4. 타임프레임별 성과
        timeframe_stats_raw = trades.filter(timeframe__isnull=False)\
            .values('timeframe')\
            .annotate(
                num_trades=Count('id'),
                total_profit=Sum('profit_krw'),
                avg_profit=Avg('profit_krw'),
                wins=Sum(Case(
                    When(realized_profit_ticks__gt=5, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )),
                losses=Sum(Case(
                    When(realized_profit_ticks__lt=-5, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                ))
            ).order_by('-total_profit')

        # 승률 계산 추가
        timeframe_stats = []
        for item in timeframe_stats_raw:
            wins = item['wins'] or 0
            losses = item['losses'] or 0
            win_lose_total = wins + losses
            win_rate = (wins / win_lose_total * 100) if win_lose_total else 0
            timeframe_stats.append({
                'timeframe': item['timeframe'],
                'num_trades': item['num_trades'],
                'total_profit': item['total_profit'],
                'avg_profit': item['avg_profit'],
                'win_rate': win_rate
            })
        context['timeframe_stats'] = timeframe_stats

        # 5. 전략별 성과
        strategy_stats_raw = trades.filter(entry_strategy__isnull=False)\
            .values('entry_strategy__name')\
            .annotate(
                num_trades=Count('id'),
                total_profit=Sum('profit_krw'),
                wins=Sum(Case(
                    When(realized_profit_ticks__gt=5, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )),
                losses=Sum(Case(
                    When(realized_profit_ticks__lt=-5, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                ))
            ).order_by('-total_profit')[:5]

        # 승률 계산 추가
        strategy_stats = []
        for item in strategy_stats_raw:
            wins = item['wins'] or 0
            losses = item['losses'] or 0
            win_lose_total = wins + losses
            win_rate = (wins / win_lose_total * 100) if win_lose_total else 0
            strategy_stats.append({
                'entry_strategy__name': item['entry_strategy__name'],
                'num_trades': item['num_trades'],
                'total_profit': item['total_profit'],
                'win_rate': win_rate
            })
        context['strategy_stats'] = strategy_stats

        # 6. 위험 지표 (승/패만 필터링, 무승부 제외)
        wins = trades.filter(realized_profit_ticks__gt=5)
        losses = trades.filter(realized_profit_ticks__lt=-5)

        if wins.count() > 0 and losses.count() > 0:
            avg_win = wins.aggregate(Avg('profit_krw'))['profit_krw__avg'] or 0
            avg_loss = losses.aggregate(Avg('profit_krw'))['profit_krw__avg'] or 0
            largest_win = wins.aggregate(Max('profit_krw'))['profit_krw__max'] or 0
            largest_loss = losses.aggregate(Max('profit_krw'))['profit_krw__max'] or 0

            context['avg_win'] = avg_win
            context['avg_loss'] = avg_loss
            context['largest_win'] = largest_win
            context['largest_loss'] = largest_loss
            context['pnl_ratio'] = abs(avg_win / avg_loss) if avg_loss else 0

        # 7. 알림/경고 생성
        alerts = []

        # 승률 저하 경고
        recent_10 = list(trades[:10])
        if len(recent_10) >= 10:
            recent_win_rate = sum(1 for t in recent_10 if t.profit_krw > 0) / 10 * 100
            if recent_win_rate < 40:
                alerts.append({
                    'level': 'medium',
                    'message': f'최근 10건 승률이 {recent_win_rate:.0f}%로 낮습니다.'
                })

        context['alerts'] = alerts

        return context

class SettingsView(TemplateView):
    """설정 페이지 - 목표 설정 및 알림 관리"""
    template_name = "trading/futures/settings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active'] = 'settings'

        # 현재 목표 가져오기 (없으면 기본값)
        goal = UserGoal.objects.first()
        if not goal:
            goal = UserGoal()  # 기본값으로 인스턴스 생성

        context['goal'] = goal

        # AI 설정 가져오기
        from ai_advisor.models import AISettings
        context['ai_settings'] = AISettings.get_settings()

        # 현재 주간 통계
        from datetime import datetime, timedelta
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())

        trades = FuturesTrade.objects.filter(
            is_open=False,
            end_date__gte=week_start
        ).annotate(
            profit_krw=ExpressionWrapper(
                F('realized_profit') * F('instrument__currency__rate'),
                output_field=FloatField()
            )
        )

        if trades.count() > 0:
            total_profit = trades.aggregate(Sum('profit_krw'))['profit_krw__sum'] or 0
            context['current_profit'] = total_profit
            context['num_trades_this_week'] = trades.count()

            # 목표 대비 진행률
            if goal.profit_goal > 0:
                context['progress_percent'] = min((total_profit / float(goal.profit_goal)) * 100, 100)
            else:
                context['progress_percent'] = 0
        else:
            context['current_profit'] = 0
            context['num_trades_this_week'] = 0
            context['progress_percent'] = 0

        return context

    def post(self, request, *args, **kwargs):
        # 목표 업데이트 또는 생성
        goal = UserGoal.objects.first()

        if not goal:
            goal = UserGoal()

        # 폼 데이터로 업데이트
        if request.POST.get('period'):
            goal.period = request.POST.get('period')
        if request.POST.get('profit_goal'):
            goal.profit_goal = D(request.POST.get('profit_goal'))
        if request.POST.get('max_loss_limit'):
            goal.max_loss_limit = D(request.POST.get('max_loss_limit'))
        if request.POST.get('max_trades_per_day'):
            goal.max_trades_per_day = int(request.POST.get('max_trades_per_day'))
        if request.POST.get('alert_consecutive_losses'):
            goal.alert_consecutive_losses = int(request.POST.get('alert_consecutive_losses'))
        if request.POST.get('alert_low_win_rate'):
            goal.alert_low_win_rate = D(request.POST.get('alert_low_win_rate'))

        goal.save()

        # AI 설정 업데이트
        from ai_advisor.models import AISettings
        ai_settings = AISettings.get_settings()

        ai_settings.enable_long_term_memory = request.POST.get('enable_long_term_memory') == '1'
        if request.POST.get('message_retention_days'):
            ai_settings.message_retention_days = int(request.POST.get('message_retention_days'))
        if request.POST.get('ai_model'):
            ai_settings.ai_model = request.POST.get('ai_model')

        ai_settings.save()

        return redirect('settings')

class AnalysisView(TemplateView):
    """분석 페이지 - 심화 통계 및 차트"""
    template_name = "trading/futures/analysis.html"

    def get_context_data(self, **kwargs):
        import json
        context = super().get_context_data(**kwargs)
        context['active'] = 'analysis'

        # 전체 완료된 거래 데이터
        trades = FuturesTrade.objects.filter(is_open=False).annotate(
            profit_krw=ExpressionWrapper(
                F('realized_profit') * F('instrument__currency__rate'),
                output_field=FloatField()
            ),
            commission_krw=ExpressionWrapper(
                F('commission') * F('instrument__currency__rate'),
                output_field=FloatField()
            ),
            net_profit_krw=ExpressionWrapper(
                F('realized_profit') * F('instrument__currency__rate') - F('commission') * F('instrument__currency__rate'),
                output_field=FloatField()
            )
        ).order_by('end_date')

        if trades.count() == 0:
            context['no_data'] = True
            return context

        # 1. 월별 수익 데이터 (전체 기간, 수수료 포함)
        from django.db.models.functions import TruncMonth
        monthly_data = trades.annotate(month=TruncMonth('end_date'))\
            .values('month')\
            .annotate(
                total_profit=Sum('net_profit_krw'),
                num_trades=Count('id'),
                wins=Sum(Case(
                    When(realized_profit_ticks__gt=5, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )),
                losses=Sum(Case(
                    When(realized_profit_ticks__lt=-5, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                ))
            ).order_by('-month')

        # JSON 직렬화 가능하도록 변환 (승률 계산: 승 / (승 + 패))
        monthly_data_list = []
        for item in reversed(list(monthly_data)):
            wins = item['wins'] or 0
            losses = item['losses'] or 0
            win_lose_total = wins + losses
            win_rate = (wins / win_lose_total * 100) if win_lose_total else 0

            monthly_data_list.append({
                'month': item['month'].strftime('%Y-%m-%d') if item['month'] else None,
                'total_profit': float(item['total_profit']) if item['total_profit'] else 0,
                'num_trades': int(item['num_trades']) if item['num_trades'] else 0,
                'win_rate': float(win_rate)
            })
        context['monthly_data'] = json.dumps(monthly_data_list)

        # 2. 멘탈 상태별 성과
        mental_stats_raw = trades.filter(mental__isnull=False)\
            .values('mental')\
            .annotate(
                num_trades=Count('id'),
                total_profit=Sum('profit_krw'),
                avg_profit=Avg('profit_krw'),
                wins=Sum(Case(
                    When(realized_profit_ticks__gt=5, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )),
                losses=Sum(Case(
                    When(realized_profit_ticks__lt=-5, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                ))
            ).order_by('-total_profit')

        # 승률 계산 추가
        mental_stats = []
        for item in mental_stats_raw:
            wins = item['wins'] or 0
            losses = item['losses'] or 0
            win_lose_total = wins + losses
            win_rate = (wins / win_lose_total * 100) if win_lose_total else 0
            mental_stats.append({
                'mental': item['mental'],
                'num_trades': item['num_trades'],
                'total_profit': item['total_profit'],
                'avg_profit': item['avg_profit'],
                'win_rate': win_rate
            })
        context['mental_stats'] = mental_stats

        # 3. 요일별 성과
        from django.db.models.functions import ExtractWeekDay
        weekday_stats_raw = trades.annotate(weekday=ExtractWeekDay('pub_date'))\
            .values('weekday')\
            .annotate(
                num_trades=Count('id'),
                total_profit=Sum('profit_krw'),
                wins=Sum(Case(
                    When(realized_profit_ticks__gt=5, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )),
                losses=Sum(Case(
                    When(realized_profit_ticks__lt=-5, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                ))
            ).order_by('weekday')

        # 승률 계산 추가
        weekday_stats = []
        for item in weekday_stats_raw:
            wins = item['wins'] or 0
            losses = item['losses'] or 0
            win_lose_total = wins + losses
            win_rate = (wins / win_lose_total * 100) if win_lose_total else 0
            weekday_stats.append({
                'weekday': item['weekday'],
                'num_trades': item['num_trades'],
                'total_profit': item['total_profit'],
                'win_rate': win_rate
            })
        context['weekday_stats'] = weekday_stats

        # 4. 손익 분포 (히스토그램 데이터)
        profits = [float(p) if p else 0 for p in trades.values_list('profit_krw', flat=True)]
        context['profit_distribution'] = json.dumps(profits)

        # 5. 최대 낙폭 (MDD) 계산
        cumulative_profit = 0
        peak = 0
        max_drawdown = 0

        for trade in trades:
            cumulative_profit += trade.profit_krw
            if cumulative_profit > peak:
                peak = cumulative_profit
            drawdown = peak - cumulative_profit
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        context['max_drawdown'] = max_drawdown

        # 6. 평균 보유 시간
        durations = []
        for trade in trades:
            if trade.end_date and trade.pub_date:
                duration = (trade.end_date - trade.pub_date).total_seconds() / 3600  # 시간 단위
                durations.append(duration)

        if durations:
            context['avg_duration'] = sum(durations) / len(durations)
        else:
            context['avg_duration'] = 0

        # 7. 매매 간 독립성 검정
        import math

        # 정규분포 CDF 근사 함수 (scipy 없이)
        def norm_cdf(x):
            """표준정규분포의 누적분포함수 근사"""
            # Abramowitz and Stegun approximation
            t = 1.0 / (1.0 + 0.2316419 * abs(x))
            d = 0.3989423 * math.exp(-x * x / 2.0)
            prob = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))))
            if x > 0:
                return 1.0 - prob
            else:
                return prob

        # 승/무/패 시퀀스 생성 (틱 기준)
        # 1: 승 (>5틱), 0: 무 (-5~5틱), -1: 패 (<-5틱)
        outcomes = []
        for t in trades:
            if t.realized_profit_ticks > 5:
                outcomes.append(1)  # 승
            elif t.realized_profit_ticks < -5:
                outcomes.append(-1)  # 패
            else:
                outcomes.append(0)  # 무

        profits = [t.profit_krw for t in trades]

        independence_test = {
            'runs_test_p': None,
            'runs_interpretation': '데이터 부족',
            'autocorr_lag1': None,
            'win_after_win': None,
            'win_after_loss': None,
            'draw_after_win': None,
            'draw_after_loss': None,
            'conditional_test_p': None,
            'overall_interpretation': '거래 데이터가 충분하지 않습니다.'
        }

        if len(outcomes) >= 10:
            # Runs Test (런 검정) - 승/무/패 모두 포함
            n_wins = sum(1 for o in outcomes if o == 1)
            n_draws = sum(1 for o in outcomes if o == 0)
            n_losses = sum(1 for o in outcomes if o == -1)

            if n_wins > 0 and n_losses > 0:
                # 런(run) 계산: 연속된 같은 결과의 시퀀스
                runs = 1
                for i in range(1, len(outcomes)):
                    if outcomes[i] != outcomes[i-1]:
                        runs += 1

                # 기대 런 수 및 표준편차
                n = len(outcomes)
                expected_runs = (2 * n_wins * n_losses) / n + 1
                variance = (2 * n_wins * n_losses * (2 * n_wins * n_losses - n)) / (n**2 * (n - 1))

                if variance > 0:
                    z_score = (runs - expected_runs) / math.sqrt(variance)
                    # 양측 검정
                    runs_p_value = 2 * (1 - norm_cdf(abs(z_score)))
                    independence_test['runs_test_p'] = runs_p_value

                    if runs_p_value < 0.05:
                        if runs < expected_runs:
                            independence_test['runs_interpretation'] = '연승/연패 경향 있음 (패턴 존재)'
                        else:
                            independence_test['runs_interpretation'] = '승/패가 과도하게 교차함'
                    else:
                        independence_test['runs_interpretation'] = '랜덤 (독립적)'

            # 자기상관 검정 (Lag 1)
            if len(profits) >= 3:
                # 수익의 자기상관
                mean_profit = sum(profits) / len(profits)

                numerator = sum((profits[i] - mean_profit) * (profits[i-1] - mean_profit) for i in range(1, len(profits)))
                denominator = sum((p - mean_profit)**2 for p in profits)

                if denominator > 0:
                    autocorr = numerator / denominator
                    independence_test['autocorr_lag1'] = autocorr

            # 조건부 승률 분석 (승/무/패 포함)
            if len(outcomes) >= 5:
                win_after_win_count = 0
                win_after_win_total = 0
                win_after_loss_count = 0
                win_after_loss_total = 0
                win_after_draw_count = 0
                win_after_draw_total = 0

                for i in range(1, len(outcomes)):
                    if outcomes[i-1] == 1:  # 이전 거래가 승
                        win_after_win_total += 1
                        if outcomes[i] == 1:
                            win_after_win_count += 1
                    elif outcomes[i-1] == -1:  # 이전 거래가 패
                        win_after_loss_total += 1
                        if outcomes[i] == 1:
                            win_after_loss_count += 1
                    else:  # 이전 거래가 무승부
                        win_after_draw_total += 1
                        if outcomes[i] == 1:
                            win_after_draw_count += 1

                if win_after_win_total > 0:
                    independence_test['win_after_win'] = (win_after_win_count / win_after_win_total) * 100
                if win_after_loss_total > 0:
                    independence_test['win_after_loss'] = (win_after_loss_count / win_after_loss_total) * 100
                if win_after_draw_total > 0:
                    independence_test['win_after_draw'] = (win_after_draw_count / win_after_draw_total) * 100

                # Chi-square 검정 (수동 구현)
                if win_after_win_total > 0 and win_after_loss_total > 0:
                    # 2x2 contingency table
                    a = win_after_win_count
                    b = win_after_win_total - win_after_win_count
                    c = win_after_loss_count
                    d = win_after_loss_total - win_after_loss_count

                    n = a + b + c + d

                    # Chi-square 통계량 계산
                    if n > 0:
                        expected_a = (a + b) * (a + c) / n
                        expected_b = (a + b) * (b + d) / n
                        expected_c = (c + d) * (a + c) / n
                        expected_d = (c + d) * (b + d) / n

                        if expected_a > 0 and expected_b > 0 and expected_c > 0 and expected_d > 0:
                            chi2 = ((a - expected_a)**2 / expected_a +
                                   (b - expected_b)**2 / expected_b +
                                   (c - expected_c)**2 / expected_c +
                                   (d - expected_d)**2 / expected_d)

                            # df=1에 대한 p-value 근사 (chi-square to normal approximation for large samples)
                            # 간단한 근사: chi2 > 3.84이면 p < 0.05
                            if chi2 > 6.63:
                                p_value = 0.01
                            elif chi2 > 3.84:
                                p_value = 0.04
                            elif chi2 > 2.71:
                                p_value = 0.10
                            else:
                                p_value = 0.20

                            independence_test['conditional_test_p'] = p_value

            # 종합 해석
            interpretations = []

            if independence_test['runs_test_p'] is not None:
                if independence_test['runs_test_p'] < 0.05:
                    interpretations.append('승패 패턴이 감지되었습니다.')
                else:
                    interpretations.append('승패가 독립적으로 발생하고 있습니다.')

            if independence_test['autocorr_lag1'] is not None:
                if abs(independence_test['autocorr_lag1']) > 0.3:
                    interpretations.append('이전 거래 손익이 다음 거래에 영향을 주고 있습니다.')

            if independence_test['conditional_test_p'] is not None:
                if independence_test['conditional_test_p'] < 0.05:
                    interpretations.append('이전 거래 결과가 다음 거래 승률에 영향을 줍니다.')

            if not interpretations:
                interpretations.append('매매가 서로 독립적입니다. 감정적 거래 패턴이 없습니다.')

            independence_test['overall_interpretation'] = ' '.join(interpretations)

        context['independence_test'] = independence_test

        return context

class NoteView(TemplateView):
    template_name = "trading/note_simple.html"

    def get(self, request, *args, **kwargs):
        # 노트 삭제
        if request.GET.get('id'):
            note = Note.objects.get(id=request.GET.get('id'))
            note.delete()

        context = self.get_context_data()
        context['active'] = 'note'

        notes = Note.objects.order_by('-date')
        paginate_by = 20 # 페이지당 20개
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




        