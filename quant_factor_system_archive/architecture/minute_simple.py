"""
分钟级别可扩展量化架构 (简单稳定版)
Minute-Level Scalable Architecture
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Callable
from enum import Enum


class Frequency(Enum):
    """数据频率"""
    MINUTE_1 = "1min"
    MINUTE_5 = "5min"
    MINUTE_15 = "15min"
    MINUTE_30 = "30min"
    DAILY = "daily"


def create_sample_data(freq: Frequency, n_symbols: int = 3, n_periods: int = 100):
    """创建样本数据"""
    symbols = [f'STOCK_{i:03d}' for i in range(n_symbols)]
    
    if freq == Frequency.DAILY:
        dates = pd.date_range('2024-01-01', periods=n_periods, freq='B')
    else:
        base = pd.Timestamp('2024-01-01 09:30:00')
        dates = [base + pd.Timedelta(minutes=i) for i in range(n_periods)]
    
    all_data = []
    
    for symbol in symbols:
        price = np.random.uniform(10, 100)
        for d in dates:
            all_data.append({
                'symbol': symbol,
                'date': d,
                'close': price,
                'volume': np.random.uniform(1e5, 1e6)
            })
            price *= (1 + np.random.uniform(-0.001, 0.002))
    
    df = pd.DataFrame(all_data)
    return df


def detect_frequency(df: pd.DataFrame) -> Frequency:
    """检测频率"""
    dates = df['date'].unique()
    if len(dates) > 1:
        diff = pd.Series(dates).sort_values().diff().dropna().median().total_seconds() / 60
        if diff < 3: return Frequency.MINUTE_1
        if diff < 10: return Frequency.MINUTE_5
        if diff < 60: return Frequency.MINUTE_30
    return Frequency.DAILY


def scale_window(base: int, freq: Frequency) -> int:
    """缩放窗口"""
    scales = {
        Frequency.MINUTE_1: 1,
        Frequency.MINUTE_5: 5,
        Frequency.MINUTE_30: 30,
        Frequency.DAILY: 240,
    }
    return int(base * scales.get(freq, 1))


class FactorPipeline:
    """因子Pipeline"""
    
    def __init__(self):
        self.factors = []
    
    def add(self, name: str, func: Callable, base_window: int = 20):
        self.factors.append({'name': name, 'func': func, 'window': base_window})
        return self
    
    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        """运行Pipeline"""
        freq = detect_frequency(df)
        print(f"📊 检测到频率: {freq.value}")
        
        results = {}
        
        for item in self.factors:
            name = item['name']
            func = item['func']
            window = scale_window(item['window'], freq)
            
            try:
                results[name] = func(df, window)
                print(f"  ✅ {name} (window={window})")
            except Exception as e:
                print(f"  ❌ {name}: {e}")
        
        return pd.DataFrame(results)


# ============ 因子函数 ============

def momentum(df: pd.DataFrame, window: int) -> pd.Series:
    """动量"""
    df = df.copy()
    df = df.sort_values(['symbol', 'date'])
    df['prev_close'] = df.groupby('symbol')['close'].shift(window)
    return (df['close'] / df['prev_close'] - 1)


def ma(df: pd.DataFrame, window: int) -> pd.Series:
    """移动平均"""
    df = df.copy()
    df = df.sort_values(['symbol', 'date'])
    return df.groupby('symbol')['close'].rolling(window).mean().values


def volatility(df: pd.DataFrame, window: int) -> pd.Series:
    """波动率"""
    df = df.copy()
    df = df.sort_values(['symbol', 'date'])
    df['ret'] = df.groupby('symbol')['close'].pct_change()
    return df.groupby('symbol')['ret'].rolling(window).std().values


def rsi(df: pd.DataFrame, window: int) -> pd.Series:
    """RSI"""
    df = df.copy()
    df = df.sort_values(['symbol', 'date'])
    df['delta'] = df.groupby('symbol')['close'].diff()
    df['gain'] = df['delta'].clip(lower=0)
    df['loss'] = (-df['delta']).clip(lower=0)
    
    avg_gain = df.groupby('symbol')['gain'].rolling(window, min_periods=1).mean()
    avg_loss = df.groupby('symbol')['loss'].rolling(window, min_periods=1).mean()
    
    rs = avg_gain / (avg_loss + 1e-8)
    return (100 - 100 / (1 + rs)).values


# ============ 分钟专用因子 ============

def order_flow(df: pd.DataFrame, window: int) -> pd.Series:
    """订单流不平衡"""
    df = df.copy()
    df = df.sort_values(['symbol', 'date'])
    df['price_change'] = df.groupby('symbol')['close'].diff()
    df['order_flow'] = df['volume'] * np.sign(df['price_change'])
    return df.groupby('symbol')['order_flow'].rolling(window).sum().values


def vwap(df: pd.DataFrame, window: int) -> pd.Series:
    """VWAP"""
    df = df.copy()
    df = df.sort_values(['symbol', 'date'])
    df['dollar_vol'] = df['close'] * df['volume']
    
    sum_dollar = df.groupby('symbol')['dollar_vol'].rolling(window).sum()
    sum_vol = df.groupby('symbol')['volume'].rolling(window).sum()
    
    return (sum_dollar / sum_vol).values


# ============ 演示 ============

def demo():
    print("=" * 60)
    print("🚀 分钟级别可扩展架构演示")
    print("=" * 60)
    
    # 1. 创建数据
    print("\n1. 创建数据...")
    
    df_daily = create_sample_data(Frequency.DAILY, n_periods=50)
    df_minute = create_sample_data(Frequency.MINUTE_1, n_periods=500)
    
    print(f"   日线: {len(df_daily)} 行")
    print(f"   分钟: {len(df_minute)} 行")
    
    # 2. 构建Pipeline
    print("\n2. 构建通用Pipeline...")
    
    pipe = FactorPipeline()
    pipe.add('momentum', momentum, 20)
    pipe.add('ma', ma, 20)
    pipe.add('volatility', volatility, 20)
    pipe.add('rsi', rsi, 14)
    
    # 3. 运行日线
    print("\n3. 日线因子...")
    daily_result = pipe.run(df_daily)
    print(f"   结果: {daily_result.shape}")
    
    # 4. 运行分钟
    print("\n4. 分钟因子...")
    minute_result = pipe.run(df_minute)
    print(f"   结果: {minute_result.shape}")
    
    # 5. 分钟专用
    print("\n5. 分钟专用因子...")
    
    minute_pipe = FactorPipeline()
    minute_pipe.add('order_flow', order_flow, 10)
    minute_pipe.add('vwap', vwap, 5)
    
    minute_only = minute_pipe.run(df_minute)
    print(f"   结果: {minute_only.shape}")
    
    print("\n" + "=" * 60)
    print("✅ 演示完成!")
    print("=" * 60)
    
    return daily_result, minute_result


if __name__ == '__main__':
    demo()
