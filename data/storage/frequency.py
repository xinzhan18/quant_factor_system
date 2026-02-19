"""
频率常量
Frequency Constants
"""

class Frequency:
    """频率常量"""
    TICK = 'tick'
    MINUTE_1 = '1min'
    MINUTE_5 = '5min'
    MINUTE_15 = '15min'
    MINUTE_30 = '30min'
    HOUR_1 = '1hour'
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    
    # 可聚合的频率 (从1min聚合)
    AGGREGATABLE = ['5min', '15min', '30min', '1hour', 'daily', 'weekly', 'monthly']


__all__ = ['Frequency']
