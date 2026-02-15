"""
分钟级别可扩展量化架构 (简化版)
Minute-Level Scalable Architecture
"""

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union
from enum import Enum


# ============ 频率定义 ============

class Frequency(Enum):
    """数据频率"""
    MINUTE_1 = "1min"
    MINUTE_5 = "5min"
    MINUTE_15 = "15min"
    MINUTE_30 = "30min"
    DAILY = "daily"
    WEEKLY = "weekly"


# ============ 统一数据接口 ============

class QuantData:
    """
    统一数据类
    
    支持日线/分钟线
    MultiIndex: [symbol, timestamp]
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Args:
            df: MultiIndex DataFrame [symbol, timestamp]
        """
        self.df = df
        self._validate_index()
    
    def _validate_index(self):
        """验证索引结构"""
        if not isinstance(self.df.index, pd.MultiIndex):
            raise ValueError("DataFrame must have MultiIndex [symbol, timestamp]")
        
        if self.df.index.names[0] != 'symbol' or self.df.index.names[1] != 'timestamp':
            raise ValueError(f"Index names must be ['symbol', 'timestamp'], got {self.df.index.names}")
    
    @classmethod
    def create(
        cls,
        data: List[Dict],
        symbol_col: str = 'symbol',
        timestamp_col: str = 'timestamp'
    ) -> 'QuantData':
        """从列表创建"""
        df = pd.DataFrame(data)
        df = df.set_index([symbol_col, timestamp_col])
        return cls(df)
    
    @property
    def symbols(self) -> pd.Index:
        """所有股票"""
        return self.df.index.get_level_values('symbol').unique()
    
    @property
    def timestamps(self) -> pd.Index:
        """所有时间戳"""
        return self.df.index.get_level_values('timestamp').unique()
    
    def get_stock(self, symbol: str) -> pd.DataFrame:
        """获取单只股票数据"""
        return self.df.xs(symbol, level='symbol')
    
    def filter(self, symbols: List[str] = None, 
               start: str = None, end: str = None) -> 'QuantData':
        """筛选数据"""
        df = self.df.copy()
        
        if symbols:
            df = df[df.index.get_level_values('symbol').isin(symbols)]
        
        if start:
            df = df[df.index.get_level_values('timestamp') >= pd.Timestamp(start)]
        
        if end:
            df = df[df.index.get_level_values('timestamp') <= pd.Timestamp(end)]
        
        return QuantData(df)
    
    def detect_frequency(self) -> Frequency:
        """自动检测频率"""
        if len(self.symbols) == 0:
            return Frequency.DAILY
        
        # 取第一只股票的时间间隔
        first_stock = self.symbols[0]
        ts = self.get_stock(first_stock).index
        
        if len(ts) > 1:
            intervals = ts.to_series().diff().dropna()
            median_sec = intervals.median().total_seconds()
            minutes = median_sec / 60
            
            if minutes < 3:
                return Frequency.MINUTE_1
            elif minutes < 10:
                return Frequency.MINUTE_5
            elif minutes < 60:
                return Frequency.MINUTE_30
            elif minutes < 1440:
                return Frequency.DAILY
        
        return Frequency.DAILY


# ============ 因子基类 ============

class BaseFactor(ABC):
    """
    因子基类
    
    特点:
    - 频率自动检测
    - 窗口自动缩放
    - 统一的compute接口
    """
    
    def __init__(self, name: str = None, window: int = 20):
        self.name = name or self.__class__.__name__
        self.window = window
    
    def compute(self, data: QuantData, frequency: Frequency = None) -> pd.Series:
        """
        计算因子值
        
        Args:
            data: 统一数据接口
            frequency: 数据频率 (None则自动检测)
            
        Returns:
            因子值 Series [symbol, timestamp]
        """
        if frequency is None:
            frequency = data.detect_frequency()
        
        # 缩放窗口
        scaled_window = self._scale_window(self.window, frequency)
        
        return self._compute_impl(data.df, scaled_window, frequency)
    
    def _scale_window(self, base_window: int, frequency: Frequency) -> int:
        """根据频率缩放窗口"""
        factors = {
            Frequency.MINUTE_1: 1,
            Frequency.MINUTE_5: 5,
            Frequency.MINUTE_15: 15,
            Frequency.MINUTE_30: 30,
            Frequency.DAILY: 240,   # 日 ≈ 4小时×60分钟
            Frequency.WEEKLY: 1200,
        }
        
        scale = factors.get(frequency, 1)
        return int(base_window * scale / 1)
    
    @abstractmethod
    def _compute_impl(
        self, 
        df: pd.DataFrame, 
        scaled_window: int, 
        frequency: Frequency
    ) -> pd.Series:
        pass


# ============ 通用因子 ============

class RollingReturn(BaseFactor):
    """滚动收益因子"""
    
    def _compute_impl(self, df, window, freq):
        close = df['close']
        return close.groupby(level='symbol').pct_change(window)


class MovingAverage(BaseFactor):
    """移动平均"""
    
    def _compute_impl(self, df, window, freq):
        close = df['close']
        return close.groupby(level='symbol').rolling(window).mean()


class Volatility(BaseFactor):
    """波动率"""
    
    def _compute_impl(self, df, window, freq):
        close = df['close']
        ret = close.groupby(level='symbol').pct_change()
        return ret.groupby(level='symbol').rolling(window).std()


class RSI(BaseFactor):
    """RSI指标"""
    
    def _compute_impl(self, df, window, freq):
        close = df['close']
        delta = close.groupby(level='symbol').diff()
        
        gain = delta.where(delta > 0, 0)
        loss = (-delta).where(delta < 0, 0)
        
        avg_gain = gain.groupby(level='symbol').rolling(window, min_periods=1).mean()
        avg_loss = loss.groupby(level='symbol').rolling(window, min_periods=1).mean()
        
        rs = avg_gain / (avg_loss + 1e-8)
        return 100 - 100 / (1 + rs)


# ============ 分钟专用因子 ============

class OrderFlowImbalance(BaseFactor):
    """订单流不平衡"""
    
    def _compute_impl(self, df, window, freq):
        close = df['close']
        volume = df['volume']
        
        price_change = close.groupby(level='symbol').diff()
        order_flow = volume * np.sign(price_change)
        
        return order_flow.groupby(level='symbol').rolling(window).sum()


class VWAP(BaseFactor):
    """成交量加权价格"""
    
    def _compute_impl(self, df, window, freq):
        close = df['close']
        volume = df['volume']
        
        dollar_vol = close * volume
        
        vwap_sum = dollar_vol.groupby(level='symbol').rolling(window).sum()
        vol_sum = volume.groupby(level='symbol').rolling(window).sum()
        
        return vwap_sum / (vol_sum + 1e-8)


# ============ Pipeline ============

class Pipeline:
    """多频率Pipeline"""
    
    def __init__(self, name: str = "Pipeline"):
        self.name = name
        self.factors: Dict[str, BaseFactor] = {}
    
    def add_factor(self, name: str, factor: BaseFactor) -> 'Pipeline':
        self.factors[name] = factor
        return self
    
    def run(self, data: QuantData, frequency: Frequency = None) -> pd.DataFrame:
        if frequency is None:
            frequency = data.detect_frequency()
        
        print(f"📊 Pipeline运行中... (频率: {frequency.value})")
        
        results = {}
        for name, factor in self.factors.items():
            try:
                results[name] = factor.compute(data, frequency)
                print(f"  ✅ {name}")
            except Exception as e:
                print(f"  ❌ {name}: {e}")
        
        # 合并结果
        result_df = pd.DataFrame(results)
        
        # 对齐到原始数据
        aligned = result_df.reindex(data.df.index)
        
        return aligned


# ============ 使用示例 ============

def demo():
    """演示"""
    print("=" * 60)
    print("🚀 分钟级别可扩展架构演示")
    print("=" * 60)
    
    # ============ 1. 创建数据 ============
    print("\n1. 创建模拟数据...")
    
    # 日线数据
    daily_records = []
    symbols = ['SH600000', 'SZ000001']
    
    for symbol in symbols:
        base_price = 10.0
        for day in range(20):
            date = pd.Timestamp(f"2024-01-{day+1:02d}")
            daily_records.append({
                'symbol': symbol,
                'timestamp': date,
                'open': base_price,
                'high': base_price * 1.02,
                'low': base_price * 0.98,
                'close': base_price,
                'volume': 1e7
            })
            base_price *= 1.001
    
    daily_data = QuantData.create(daily_records)
    print(f"   日线: {daily_data.df.shape}, 频率: {daily_data.detect_frequency().value}")
    
    # 分钟数据
    minute_records = []
    for symbol in symbols:
        base_price = 10.0
        for day in range(3):
            base_date = pd.Timestamp(f"2024-01-{day+1:02d} 09:30:00")
            for minute in range(60):  # 简化: 每分钟
                ts = base_date + pd.Timedelta(minutes=minute)
                minute_records.append({
                    'symbol': symbol,
                    'timestamp': ts,
                    'open': base_price,
                    'high': base_price * 1.001,
                    'low': base_price * 0.999,
                    'close': base_price,
                    'volume': 1e5
                })
                base_price *= 1.0001
    
    minute_data = QuantData.create(minute_records)
    print(f"   分钟: {minute_data.df.shape}, 频率: {minute_data.detect_frequency().value}")
    
    # ============ 2. 构建Pipeline ============
    print("\n2. 构建Pipeline...")
    
    pipe = Pipeline("MultiFreq")
    pipe.add_factor('momentum', RollingReturn(window=20))
    pipe.add_factor('ma', MovingAverage(window=20))
    pipe.add_factor('volatility', Volatility(window=20))
    pipe.add_factor('rsi', RSI(window=14))
    
    # ============ 3. 运行日线 ============
    print("\n3. 运行日线Pipeline...")
    daily_factors = pipe.run(daily_data, Frequency.DAILY)
    print(f"   结果: {daily_factors.shape}")
    
    # ============ 4. 运行分钟线 ============
    print("\n4. 运行分钟线Pipeline...")
    minute_factors = pipe.run(minute_data, Frequency.MINUTE_1)
    print(f"   结果: {minute_factors.shape}")
    
    # ============ 5. 分钟专用因子 ============
    print("\n5. 分钟专用因子...")
    
    minute_pipe = Pipeline("MinuteOnly")
    minute_pipe.add_factor('order_flow', OrderFlowImbalance(window=10))
    minute_pipe.add_factor('vwap', VWAP(window=5))
    
    minute_only = minute_pipe.run(minute_data, Frequency.MINUTE_1)
    print(f"   结果: {minute_only.shape}")
    
    print("\n" + "=" * 60)
    print("✅ 演示完成!")
    print("=" * 60)
    
    return daily_data, minute_data, pipe


if __name__ == '__main__':
    demo()
