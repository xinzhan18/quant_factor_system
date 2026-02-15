"""
分钟级别可扩展量化架构 (最终版)
Minute-Level Scalable Architecture
"""

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from enum import Enum


class Frequency(Enum):
    """数据频率"""
    MINUTE_1 = "1min"
    MINUTE_5 = "5min"
    MINUTE_15 = "15min"
    MINUTE_30 = "30min"
    DAILY = "daily"


# ============ 简化版因子计算 ============

def calculate_momentum(df: pd.DataFrame, window: int = 20) -> pd.Series:
    """动量因子"""
    return df['close'].groupby(level='symbol').pct_change(window)


def calculate_ma(df: pd.DataFrame, window: int = 20) -> pd.Series:
    """移动平均"""
    return df['close'].groupby(level='symbol').rolling(window).mean().droplevel('timestamp')


def calculate_volatility(df: pd.DataFrame, window: int = 20) -> pd.Series:
    """波动率"""
    ret = df['close'].groupby(level='symbol').pct_change()
    return ret.groupby(level='symbol').rolling(window).std().droplevel('timestamp')


def calculate_rsi(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """RSI"""
    close = df['close']
    delta = close.groupby(level='symbol').diff()
    
    gain = delta.where(delta > 0, 0)
    loss = (-delta).where(delta < 0, 0)
    
    avg_gain = gain.groupby(level='symbol').rolling(window, min_periods=1).mean()
    avg_loss = loss.groupby(level='symbol').rolling(window, min_periods=1).mean()
    
    rs = avg_gain / (avg_loss + 1e-8)
    return 100 - 100 / (1 + rs)


# ============ 分钟专用因子 ============

def calculate_order_flow(df: pd.DataFrame, window: int = 10) -> pd.Series:
    """订单流不平衡"""
    close = df['close']
    volume = df['volume']
    
    price_change = close.groupby(level='symbol').diff()
    order_flow = volume * np.sign(price_change)
    
    return order_flow.groupby(level='symbol').rolling(window).sum().droplevel('timestamp')


def calculate_vwap(df: pd.DataFrame, window: int = 5) -> pd.Series:
    """VWAP"""
    close = df['close']
    volume = df['volume']
    
    dollar_vol = close * volume
    
    vwap_sum = dollar_vol.groupby(level='symbol').rolling(window).sum()
    vol_sum = volume.groupby(level='symbol').rolling(window).sum()
    
    return (vwap_sum / vol_sum).droplevel('timestamp')


# ============ Pipeline ============

class FactorPipeline:
    """因子Pipeline"""
    
    def __init__(self, name: str = "Pipeline"):
        self.name = name
        self.factors = {}
    
    def add_factor(self, name: str, func, window: int = 20):
        """添加因子"""
        self.factors[name] = {'func': func, 'window': window}
        return self
    
    def run(self, df: pd.DataFrame, frequency: Frequency = None) -> pd.DataFrame:
        """运行Pipeline"""
        if frequency is None:
            frequency = self._detect_frequency(df)
        
        print(f"📊 Pipeline: {frequency.value}")
        
        results = {}
        
        for name, config in self.factors.items():
            func = config['func']
            window = config['window']
            
            # 频率缩放
            scaled_window = self._scale_window(window, frequency)
            
            try:
                results[name] = func(df, scaled_window)
                print(f"  ✅ {name} (window={scaled_window})")
            except Exception as e:
                print(f"  ❌ {name}: {e}")
        
        return pd.DataFrame(results)
    
    def _scale_window(self, base: int, freq: Frequency) -> int:
        """缩放窗口"""
        scales = {
            Frequency.MINUTE_1: 1,
            Frequency.MINUTE_5: 5,
            Frequency.MINUTE_30: 30,
            Frequency.DAILY: 240,
        }
        return int(base * scales.get(freq, 1))
    
    def _detect_frequency(self, df: pd.DataFrame) -> Frequency:
        """检测频率"""
        first_stock = df.index.get_level_values('symbol')[0]
        ts = df.xs(first_stock, level='symbol').index
        
        if len(ts) > 1:
            median = ts.to_series().diff().dropna().median().total_seconds() / 60
            if median < 3: return Frequency.MINUTE_1
            if median < 10: return Frequency.MINUTE_5
            if median < 60: return Frequency.MINUTE_30
        
        return Frequency.DAILY


# ============ 数据创建 ============

def create_sample_data(freq: Frequency, n_symbols: int = 3, n_periods: int = 100):
    """创建样本数据"""
    symbols = [f'STOCK_{i:03d}' for i in range(n_symbols)]
    
    if freq == Frequency.DAILY:
        dates = pd.date_range('2024-01-01', periods=n_periods, freq='B')
        time_col = 'date'
    else:
        base = pd.Timestamp('2024-01-01 09:30:00')
        dates = [base + pd.Timedelta(minutes=i) for i in range(n_periods)]
        time_col = 'timestamp'
    
    index_tuples = []
    records = []
    
    for symbol in symbols:
        price = np.random.uniform(10, 100)
        for i, d in enumerate(dates):
            index_tuples.append((symbol, d))
            records.append({
                'open': price,
                'high': price * 1.01,
                'low': price * 0.99,
                'close': price,
                'volume': np.random.uniform(1e5, 1e6)
            })
            price *= (1 + np.random.uniform(-0.001, 0.002))
    
    index = pd.MultiIndex.from_tuples(index_tuples, names=['symbol', time_col])
    df = pd.DataFrame(records, index=index)
    
    return df


# ============ 演示 ============

def demo():
    print("=" * 60)
    print("🚀 分钟级别可扩展架构")
    print("=" * 60)
    
    # 1. 创建数据
    print("\n1. 创建数据...")
    
    df_daily = create_sample_data(Frequency.DAILY, n_periods=50)
    print(f"   日线: {df_daily.shape}")
    
    df_minute = create_sample_data(Frequency.MINUTE_1, n_periods=500)
    print(f"   分钟: {df_minute.shape}")
    
    # 2. 构建Pipeline
    print("\n2. 构建Pipeline...")
    
    pipe = FactorPipeline("MultiFreq")
    pipe.add_factor('momentum', calculate_momentum, window=20)
    pipe.add_factor('ma', calculate_ma, window=20)
    pipe.add_factor('volatility', calculate_volatility, window=20)
    pipe.add_factor('rsi', calculate_rsi, window=14)
    
    # 3. 运行日线
    print("\n3. 日线因子...")
    daily_result = pipe.run(df_daily, Frequency.DAILY)
    print(f"   结果: {daily_result.shape}")
    
    # 4. 运行分钟
    print("\n4. 分钟因子...")
    minute_result = pipe.run(df_minute, Frequency.MINUTE_1)
    print(f"   结果: {minute_result.shape}")
    
    # 5. 分钟专用因子
    print("\n5. 分钟专用因子...")
    
    minute_pipe = FactorPipeline("MinuteOnly")
    minute_pipe.add_factor('order_flow', calculate_order_flow, window=10)
    minute_pipe.add_factor('vwap', calculate_vwap, window=5)
    
    minute_only = minute_pipe.run(df_minute, Frequency.MINUTE_1)
    print(f"   结果: {minute_only.shape}")
    
    print("\n" + "=" * 60)
    print("✅ 完成!")
    print("=" * 60)
    
    return df_daily, df_minute, pipe


if __name__ == '__main__':
    demo()
