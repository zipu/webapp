"""
Claude Tool Use Definitions
각 앱별로 다른 도구 세트를 제공합니다.
"""

# Trading Tools
TRADING_TOOLS = [
    {
        "name": "get_recent_trades",
        "description": "최근 거래 내역을 조회합니다. 특정 전략이나 심리 상태로 필터링할 수 있습니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "조회할 기간 (일 단위)",
                    "default": 7
                },
                "strategy": {
                    "type": "string",
                    "description": "필터링할 전략 (예: 'breakout', 'range', 'trend')",
                },
                "mental_state": {
                    "type": "string",
                    "description": "심리 상태 필터 (예: '집중', '불안', '자신감')"
                }
            }
        }
    },
    {
        "name": "get_independence_test",
        "description": "거래 간 독립성 검정 결과를 가져옵니다. Runs Test, Autocorrelation, Conditional Win Rate를 포함합니다.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_equity_curve",
        "description": "수익 곡선 데이터를 가져옵니다. 누적 수익, MDD(Maximum Drawdown), 샤프 비율을 포함합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "조회할 기간 (일 단위)",
                    "default": 90
                }
            }
        }
    },
    {
        "name": "get_pattern_analysis",
        "description": "시간대별, 요일별, 전략별 패턴 분석 결과를 가져옵니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern_type": {
                    "type": "string",
                    "enum": ["hourly", "daily", "strategy", "mental_state"],
                    "description": "분석할 패턴 타입 (hourly: 시간대별, daily: 요일별, strategy: 전략별, mental_state: 심리 상태별)"
                }
            },
            "required": ["pattern_type"]
        }
    },
    {
        "name": "get_economic_news",
        "description": "미국 주요 경제지(WSJ, Bloomberg, Reuters, CNBC 등)에서 최신 경제 뉴스를 검색합니다. 연준, 금리, 주식시장, 인플레이션 등의 키워드로 검색 가능합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "검색 키워드 (예: 'fed', 'interest rate', 'S&P500', 'inflation'). 비워두면 전체 최신 뉴스를 가져옵니다."
                },
                "max_articles": {
                    "type": "integer",
                    "description": "가져올 최대 기사 수",
                    "default": 8
                }
            }
        }
    },
    {
        "name": "save_memory",
        "description": """사용자에 대한 중요한 사실을 장기 기억으로 저장합니다.

다음과 같은 경우에 이 도구를 사용하세요:
- 사용자가 거래 규칙을 설정할 때 (예: "손절은 -2%에서 할게")
- 사용자의 심리 패턴을 발견했을 때 (예: "연속 손실 후 감정적으로 매매하는 경향")
- 사용자가 특정 전략을 사용한다고 언급할 때
- 사용자가 목표나 제약사항을 언급할 때
- 사용자가 명시적으로 "이거 기억해줘"라고 요청할 때

주의사항:
- AI의 조언이나 일반적인 정보는 저장하지 마세요
- 오직 사용자에 대한 구체적인 사실만 저장하세요
- 중요한 사실이라고 판단될 때만 사용하세요""",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "기억할 내용 (사용자에 대한 구체적인 사실)"
                },
                "category": {
                    "type": "string",
                    "enum": ["strategy", "rule", "lesson", "psychology", "risk", "pattern", "goal", "other"],
                    "description": "메모리 카테고리 (strategy: 거래전략, rule: 거래규칙, lesson: 배운교훈, psychology: 심리패턴, risk: 리스크관리, pattern: 발견한패턴, goal: 목표/제약사항, other: 기타)"
                },
                "importance": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "description": "중요도 (1-10, 높을수록 중요). 거래 규칙=9, 전략=8, 심리 패턴=7, 발견한 패턴=6, 기타=5"
                }
            },
            "required": ["content", "category"]
        }
    }
]

# Echomind Tools (나중에 구현)
ECHOMIND_TOOLS = [
    {
        "name": "get_recent_activities",
        "description": "최근 활동 내역을 조회합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "조회할 기간 (일)",
                    "default": 7
                }
            }
        }
    },
    # 추가 도구들...
]


def get_tools(app_type):
    """앱 타입에 따른 도구 세트 반환"""
    tools_map = {
        'trading': TRADING_TOOLS,
        'echomind': ECHOMIND_TOOLS,
    }
    return tools_map.get(app_type, TRADING_TOOLS)
