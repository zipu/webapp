"""
Context Builders
각 앱의 데이터베이스에서 데이터를 조회하여 AI에게 제공합니다.
"""

from datetime import datetime, timedelta
from django.db.models import Sum, Avg, Count, Q
from .models import ContextCache


class TradingContextBuilder:
    """트레이딩 데이터 컨텍스트 빌더"""

    @staticmethod
    def get_summary_context(days=30):
        """
        최근 거래 요약 (항상 시스템 프롬프트에 포함)
        """
        from trading.models import FuturesTrade

        cutoff = datetime.now() - timedelta(days=days)
        trades = FuturesTrade.objects.filter(
            is_open=False,
            end_date__gte=cutoff
        )

        if trades.count() == 0:
            return {
                "total_trades": 0,
                "message": "최근 거래 데이터가 없습니다."
            }

        wins = trades.filter(realized_profit_ticks__gt=5)
        losses = trades.filter(realized_profit_ticks__lt=-5)
        total_decided = wins.count() + losses.count()

        win_rate = (wins.count() / total_decided * 100) if total_decided > 0 else 0

        net_profit = trades.aggregate(Sum('realized_profit'))['realized_profit__sum'] or 0
        avg_profit = trades.aggregate(Avg('realized_profit'))['realized_profit__avg'] or 0

        return {
            "period_days": days,
            "total_trades": trades.count(),
            "wins": wins.count(),
            "losses": losses.count(),
            "win_rate": round(win_rate, 1),
            "net_profit": int(net_profit),
            "avg_profit": int(avg_profit)
        }

    @staticmethod
    def get_recent_trades(days=7, is_closed=None, strategy=None, mental_state=None):
        """
        최근 거래 내역 조회 (Tool use)

        Args:
            days: 조회 기간 (일)
            is_closed: True=완료된 거래만, False=진행중인 거래만, None=전체
            strategy: 전략 필터
            mental_state: 심리 상태 필터
        """
        from trading.models import FuturesTrade

        # 캐시 키 생성
        cache_key = f"recent_trades_{days}_{is_closed}_{strategy}_{mental_state}"
        cached = ContextCache.get_cached(cache_key)
        if cached:
            return cached

        from django.db.models import Q

        cutoff = datetime.now() - timedelta(days=days)

        # is_closed에 따라 쿼리 분기
        if is_closed is True:
            # 완료된 거래만: end_date 기준 필터링
            trades = FuturesTrade.objects.filter(
                is_open=False,
                end_date__gte=cutoff
            ).order_by('-end_date')
        elif is_closed is False:
            # 진행중인 거래만: 날짜 필터링 없음 (언제 시작했든 모두 표시)
            trades = FuturesTrade.objects.filter(
                is_open=True
            ).order_by('-pub_date')
        else:
            # 전체: 진행중(전체) + 완료(최근 N일)
            trades = FuturesTrade.objects.filter(
                Q(is_open=True) |  # 진행중은 전체
                Q(is_open=False, end_date__gte=cutoff)  # 완료는 최근 N일
            ).order_by('-end_date', '-pub_date')

        if strategy:
            trades = trades.filter(strategy__icontains=strategy)
        if mental_state:
            trades = trades.filter(mental_state__icontains=mental_state)

        result = {
            "total_count": trades.count(),
            "trades": [{
                "date": t.end_date.strftime('%Y-%m-%d %H:%M') if t.end_date else "N/A",
                "symbol": t.instrument.symbol if t.instrument else "N/A",
                "instrument_name": t.instrument.name if t.instrument else "N/A",
                "position": "Long" if t.position == 1 else "Short" if t.position == -1 else "N/A",
                "profit_ticks": round(t.realized_profit_ticks or 0, 2),
                "profit": int(t.realized_profit or 0),
                "entry_price": float(t.avg_entry_price or 0),
                "exit_price": float(t.avg_exit_price or 0),
                "contracts": t.num_entry_cons or 0,
                "entry_strategy": t.entry_strategy.name if t.entry_strategy else "없음",
                "exit_strategy": t.exit_strategy.name if t.exit_strategy else "없음",
                "mental": t.mental or "미기록",
                "entry_reason": (t.entry_reason or "")[:100],
                "exit_reason": (t.exit_reason or "")[:100]
            } for t in trades[:50]]  # 최대 50개만
        }

        # 캐시 저장 (10분)
        ContextCache.set_cache(cache_key, result, hours=0.17)
        return result

    @staticmethod
    def get_independence_test():
        """
        거래 간 독립성 검정 결과 (Post-processing 데이터)
        """
        from trading.models import FuturesTrade

        # 캐시 확인
        cache_key = "independence_test"
        cached = ContextCache.get_cached(cache_key)
        if cached:
            return cached

        trades = FuturesTrade.objects.filter(is_open=False).order_by('end_date')

        if trades.count() < 10:
            return {"error": "독립성 검정을 위한 충분한 거래가 없습니다 (최소 10개 필요)"}

        # 승/패 시퀀스 생성
        results = []
        for t in trades:
            profit = t.realized_profit_ticks or 0
            if profit > 5:
                results.append('W')
            elif profit < -5:
                results.append('L')
            else:
                results.append('D')

        # Runs Test 계산
        runs_test = TradingContextBuilder._calculate_runs_test(results)

        # Conditional Win Rate 계산
        conditional_wr = TradingContextBuilder._calculate_conditional_wr(results)

        result = {
            "total_trades": len(results),
            "runs_test": runs_test,
            "conditional_win_rate": conditional_wr
        }

        # 캐시 저장 (1시간)
        ContextCache.set_cache(cache_key, result, hours=1)
        return result

    @staticmethod
    def _calculate_runs_test(results):
        """Runs Test 계산"""
        # 간단한 Runs 카운트
        runs = 1
        for i in range(1, len(results)):
            if results[i] != results[i-1]:
                runs += 1

        n_w = results.count('W')
        n_l = results.count('L')
        n = n_w + n_l

        if n < 2:
            return {"error": "데이터 부족"}

        # 기대 runs 수
        expected_runs = (2 * n_w * n_l) / n + 1

        # 표준편차
        import math
        if n > 1:
            variance = (2 * n_w * n_l * (2 * n_w * n_l - n)) / (n ** 2 * (n - 1))
            std_dev = math.sqrt(variance) if variance > 0 else 0
        else:
            std_dev = 0

        # Z-score
        z_score = (runs - expected_runs) / std_dev if std_dev > 0 else 0

        # p-value (대략)
        p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(z_score) / math.sqrt(2))))

        interpretation = "독립적" if p_value > 0.05 else "상관관계 있음"

        return {
            "runs": runs,
            "expected_runs": round(expected_runs, 2),
            "z_score": round(z_score, 2),
            "p_value": round(p_value, 3),
            "interpretation": interpretation
        }

    @staticmethod
    def _calculate_conditional_wr(results):
        """조건부 승률 계산"""
        after_win = {'W': 0, 'L': 0, 'D': 0}
        after_loss = {'W': 0, 'L': 0, 'D': 0}

        for i in range(1, len(results)):
            prev = results[i-1]
            curr = results[i]

            if prev == 'W':
                after_win[curr] += 1
            elif prev == 'L':
                after_loss[curr] += 1

        total_after_win = sum(after_win.values())
        total_after_loss = sum(after_loss.values())

        wr_after_win = (after_win['W'] / total_after_win * 100) if total_after_win > 0 else 0
        wr_after_loss = (after_loss['W'] / total_after_loss * 100) if total_after_loss > 0 else 0

        return {
            "after_win": {
                "total": total_after_win,
                "win_rate": round(wr_after_win, 1)
            },
            "after_loss": {
                "total": total_after_loss,
                "win_rate": round(wr_after_loss, 1)
            }
        }

    @staticmethod
    def get_equity_curve(days=90):
        """
        수익 곡선 데이터 (Post-processing 데이터)
        """
        from trading.models import FuturesTrade

        # 캐시 확인
        cache_key = f"equity_curve_{days}"
        cached = ContextCache.get_cached(cache_key)
        if cached:
            return cached

        cutoff = datetime.now() - timedelta(days=days)
        trades = FuturesTrade.objects.filter(
            is_open=False,
            end_date__gte=cutoff
        ).order_by('end_date')

        cumulative_profit = 0
        max_profit = 0
        max_drawdown = 0
        curve_data = []

        for trade in trades:
            profit = float(trade.realized_profit or 0)
            cumulative_profit += profit

            # MDD 계산
            if cumulative_profit > max_profit:
                max_profit = cumulative_profit
            drawdown = max_profit - cumulative_profit
            if drawdown > max_drawdown:
                max_drawdown = drawdown

            curve_data.append({
                "date": trade.end_date.strftime('%Y-%m-%d'),
                "cumulative_profit": int(cumulative_profit),
                "trade_profit": int(profit)
            })

        result = {
            "period_days": days,
            "total_trades": len(curve_data),
            "final_profit": int(cumulative_profit),
            "max_drawdown": int(max_drawdown),
            "data_points": curve_data
        }

        # 캐시 저장 (1시간)
        ContextCache.set_cache(cache_key, result, hours=1)
        return result

    @staticmethod
    def get_pattern_analysis(pattern_type='hourly'):
        """
        패턴 분석 (시간대별, 요일별, 전략별, 심리 상태별)
        """
        from trading.models import FuturesTrade

        # 캐시 확인
        cache_key = f"pattern_{pattern_type}"
        cached = ContextCache.get_cached(cache_key)
        if cached:
            return cached

        trades = FuturesTrade.objects.filter(is_open=False)

        if pattern_type == 'hourly':
            result = TradingContextBuilder._analyze_by_hour(trades)
        elif pattern_type == 'daily':
            result = TradingContextBuilder._analyze_by_day(trades)
        elif pattern_type == 'strategy':
            result = TradingContextBuilder._analyze_by_strategy(trades)
        elif pattern_type == 'mental_state':
            result = TradingContextBuilder._analyze_by_mental_state(trades)
        else:
            result = {"error": "Unknown pattern type"}

        # 캐시 저장 (1시간)
        ContextCache.set_cache(cache_key, result, hours=1)
        return result

    @staticmethod
    def _analyze_by_hour(trades):
        """시간대별 분석"""
        from collections import defaultdict

        hourly_stats = defaultdict(lambda: {'count': 0, 'profit': 0, 'wins': 0})

        for trade in trades:
            hour = trade.end_date.hour
            hourly_stats[hour]['count'] += 1
            hourly_stats[hour]['profit'] += float(trade.realized_profit or 0)
            if (trade.realized_profit_ticks or 0) > 5:
                hourly_stats[hour]['wins'] += 1

        result = []
        for hour in range(24):
            stats = hourly_stats[hour]
            if stats['count'] > 0:
                result.append({
                    "hour": hour,
                    "count": stats['count'],
                    "total_profit": int(stats['profit']),
                    "avg_profit": int(stats['profit'] / stats['count']),
                    "win_rate": round(stats['wins'] / stats['count'] * 100, 1)
                })

        return {"pattern_type": "hourly", "data": result}

    @staticmethod
    def _analyze_by_day(trades):
        """요일별 분석"""
        from collections import defaultdict

        daily_stats = defaultdict(lambda: {'count': 0, 'profit': 0, 'wins': 0})
        day_names = ['월', '화', '수', '목', '금', '토', '일']

        for trade in trades:
            day = trade.end_date.weekday()
            daily_stats[day]['count'] += 1
            daily_stats[day]['profit'] += float(trade.realized_profit or 0)
            if (trade.realized_profit_ticks or 0) > 5:
                daily_stats[day]['wins'] += 1

        result = []
        for day in range(7):
            stats = daily_stats[day]
            if stats['count'] > 0:
                result.append({
                    "day": day_names[day],
                    "count": stats['count'],
                    "total_profit": int(stats['profit']),
                    "avg_profit": int(stats['profit'] / stats['count']),
                    "win_rate": round(stats['wins'] / stats['count'] * 100, 1)
                })

        return {"pattern_type": "daily", "data": result}

    @staticmethod
    def _analyze_by_strategy(trades):
        """전략별 분석"""
        from collections import defaultdict

        strategy_stats = defaultdict(lambda: {'count': 0, 'profit': 0, 'wins': 0})

        for trade in trades:
            strategy = trade.entry_strategy.name if trade.entry_strategy else '미분류'
            strategy_stats[strategy]['count'] += 1
            strategy_stats[strategy]['profit'] += float(trade.realized_profit or 0)
            if (trade.realized_profit_ticks or 0) > 5:
                strategy_stats[strategy]['wins'] += 1

        result = []
        for strategy, stats in strategy_stats.items():
            result.append({
                "strategy": strategy,
                "count": stats['count'],
                "total_profit": int(stats['profit']),
                "avg_profit": int(stats['profit'] / stats['count']),
                "win_rate": round(stats['wins'] / stats['count'] * 100, 1)
            })

        # 거래 수로 정렬
        result.sort(key=lambda x: x['count'], reverse=True)

        return {"pattern_type": "strategy", "data": result}

    @staticmethod
    def _analyze_by_mental_state(trades):
        """심리 상태별 분석"""
        from collections import defaultdict

        mental_stats = defaultdict(lambda: {'count': 0, 'profit': 0, 'wins': 0})

        for trade in trades:
            mental = trade.mental or '미기록'
            mental_stats[mental]['count'] += 1
            mental_stats[mental]['profit'] += float(trade.realized_profit or 0)
            if (trade.realized_profit_ticks or 0) > 5:
                mental_stats[mental]['wins'] += 1

        result = []
        for mental, stats in mental_stats.items():
            result.append({
                "mental_state": mental,
                "count": stats['count'],
                "total_profit": int(stats['profit']),
                "avg_profit": int(stats['profit'] / stats['count']),
                "win_rate": round(stats['wins'] / stats['count'] * 100, 1)
            })

        # 거래 수로 정렬
        result.sort(key=lambda x: x['count'], reverse=True)

        return {"pattern_type": "mental_state", "data": result}


class EchomindContextBuilder:
    """에코마인드 데이터 컨텍스트 빌더 (나중에 구현)"""

    @staticmethod
    def get_recent_activities(days=7):
        """최근 활동 조회"""
        return {"message": "Echomind 컨텍스트는 아직 구현되지 않았습니다."}


def get_context_builder(app_type):
    """앱 타입에 따른 컨텍스트 빌더 반환"""
    builders = {
        'trading': TradingContextBuilder,
        'echomind': EchomindContextBuilder,
    }
    return builders.get(app_type, TradingContextBuilder)
