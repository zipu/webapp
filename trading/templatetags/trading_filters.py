from django import template

register = template.Library()

@register.filter
def currency_symbol(code):
    """통화 코드를 심볼로 변환"""
    symbols = {
        'USD': '$',
        'JPY': '¥',
        'EUR': '€',
        'CNY': 'CN¥',
        'HKD': 'HK$',
        'GBP': '£',
        'AUD': 'A$',
        'CAD': 'C$',
        'CHF': 'Fr',
        'KRW': '₩'
    }
    return symbols.get(code, code)
