"""
分钟级别可扩展量化架构
Minute-Level Scalable Architecture

核心设计:
1. 统一数据接口 (支持日线/分钟线)
2. 频率无关的因子计算
3. 可扩展的数据库设计
4. 自动频率检测
"""

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import hashlib


# ============ 频率枚举 ============

class Frequency(Enum):
    """数据频率"""
    MINUTE_1 = "1min"
    MINUTE_5 = "5min"
    MINUTE_15 = "15min"
    MINUTE_30 = "30min"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


# ============ 统一数据接口 ============

@dataclass
class OHLCV:
    """统一的价格数据结构"""
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float = 0.0
    
    @classmethod
    def from_dict(cls, data: dict) -> 'OHLCV':
        return cls(
            open=data['open'],
            high=data['high'],
            low=data['low'],
            close=data['close'],
            volume=data['volume'],
            amount=data.get('amount', 0.0)
        )


class DataFrameBuilder:
    """
    统一DataFrame构建器
    
    支持:
    - 日线数据
    - 分钟线数据
    - 自动频率检测
    """
    
    @staticmethod
    def create(
        data: List[Tuple[str, datetime, OHLCV]],
        frequency: Frequency = Frequency.DAILY
    ) -> pd.DataFrame:
        """
        创建统一格式的DataFrame
        
        Args:
            data: (symbol, timestamp, OHLCV) 元组列表
            frequency: 数据频率
            
        Returns:
            MultiIndex DataFrame
        """
        index_tuples = []
        records = []
        
        for symbol, timestamp, ohlcv in data:
            index_tuples.append((symbol, timestamp))
            records.append({
                'open': ohlcv.open,
                'high': ohlcv.high,
                'low': ohlcv.low,
                'close': ohlcv.close,
                'volume': ohlcv.volume,
                'amount': ohlcv.amount,
                'frequency': frequency.value,
            })
        
        df = pd.DataFrame(
            records,
            index=pd.MultiIndex.from_tuples(
                index_tuples,
                names=['symbol', 'timestamp']
            )
        )
        
        return df
    
    @staticmethod
    def detect_frequency(df: pd.DataFrame) -> Frequency:
        """
        自动检测数据频率
        
        通过计算时间戳间隔来判断:
        - 1分钟附近 -> MINUTE_1
        - 5分钟附近 -> MINUTE_5
        - 天级别 -> DAILY
        """
        # 获取第一个股票的时间序列
        first_stock = df.index.get_level_values('symbol')[0]
        timestamps = df.loc[first_stock].index
        
        # 计算时间间隔
        if len(timestamps) > 1:
            intervals = timestamps.to_series().diff().dropna()
            median_interval = intervals.median()
            
            # 转换为分钟
            minutes = median_interval.total_seconds() / 60
            
            if minutes < 3:
                return Frequency.MINUTE_1
            elif minutes < 10:
                return Frequency.MINUTE_5
            elif minutes < 20:
                return Frequency.MINUTE_15
            elif minutes < 60:
                return Frequency.MINUTE_30
            elif minutes < 300:  # 约5小时以内
                return Frequency.DAILY
            else:
                return Frequency.WEEKLY
        
        return Frequency.DAILY


# ============ 统一因子接口 ============

class BaseFactor(ABC):
    """
    因子基类
    
    频率无关的因子接口:
    - 自动适配日线/分钟线
    - 窗口自动按频率缩放
    """
    
    def __init__(
        self,
        window: int = 20,
        name: str = None,
        frequency: Frequency = None
    ):
        """
        Args:
            window: 窗口大小 (单位根据frequency自动调整)
            name: 因子名称
            frequency: 目标频率 (None则自动检测)
        """
        self.window = window
        self.name = name or self.__class__.__name__
        self.frequency = frequency
        self._cache = {}
    
    @property
    @abstractmethod
    def description(self) -> str:
        """因子描述"""
        pass
    
    def _scale_window(self, base_window: int, target_frequency: Frequency) -> int:
        """
        根据频率自动缩放窗口
        
        例如:
        - 日线20天 ≈ 分钟线4800 (20天 × 4小时 × 60分钟)
        """
        scale_factors = {
            Frequency.MINUTE_1: 1,
            Frequency.MINUTE_5: 5,
            Frequency.MINUTE_15: 15,
            Frequency.MINUTE_30: 30,
            Frequency.DAILY: 240,  # 4小时 × 60分钟
            Frequency.WEEKLY: 1200,
            Frequency.MONTHLY: 4800,
        }
        
        base_scale = scale_factors.get(Frequency.MINUTE_1, 1)
        target_scale = scale_factors.get(target_frequency, 1)
        
        return int(base_window * target_scale / base_scale)
    
    def compute(
        self,
        data: pd.DataFrame,
        frequency: Frequency = None
    ) -> pd.Series:
        """
        计算因子值
        
        Args:
            data: 价格数据 (MultiIndex)
            frequency: 数据频率 (None则自动检测)
            
        Returns:
            因子值 (MultiIndex Series)
        """
        # 自动检测频率
        if frequency is None:
            frequency = DataFrameBuilder.detect_frequency(data)
        
        self.frequency = frequency
        
        # 生成缓存键
        cache_key = self._get_cache_key(data)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # 缩放窗口
        scaled_window = self._scale_window(self.window, frequency)
        
        # 计算因子
        result = self._compute_impl(data, scaled_window, frequency)
        
        # 缓存
        self._cache[cache_key] = result
        
        return result
    
    @abstractmethod
    def _compute_impl(
        self,
        data: pd.DataFrame,
        scaled_window: int,
        frequency: Frequency
    ) -> pd.Series:
        """实际因子计算逻辑 (子类实现)"""
        pass
    
    def _get_cache_key(self, data: pd.DataFrame) -> str:
        """生成缓存键"""
        key_data = {
            'class': self.__class__.__name__,
            'window': self.window,
            'frequency': self.frequency.value if self.frequency else 'auto',
            'shape': data.shape,
        }
        return hashlib.md5(str(key_data).encode()).hexdigest()


# ============ 具体因子实现 ============

class RollingReturn(BaseFactor):
    """滚动收益因子"""
    
    @property
    def description(self) -> str:
        return f"{self.name}: 过去{self.window}期收益率"
    
    def _compute_impl(
        self,
        data: pd.DataFrame,
        scaled_window: int,
        frequency: Frequency
    ) -> pd.Series:
        close = data['close']
        return close.groupby(level='symbol').pct_change(scaled_window)


class MovingAverage(BaseFactor):
    """移动平均因子"""
    
    @property
    def description(self) -> str:
        return f"{self.name}: {self.window}期移动平均"
    
    def _compute_impl(
        self,
        data: pd.DataFrame,
        scaled_window: int,
        frequency: Frequency
    ) -> pd.Series:
        close = data['close']
        return close.groupby(level='symbol').rolling(scaled_window).mean().droplevel('timestamp')


class Volatility(BaseFactor):
    """波动率因子"""
    
    @property
    def description(self) -> str:
        return f"{self.name}: {self.window}期滚动标准差"
    
    def _compute_impl(
        self,
        data: pd.DataFrame,
        scaled_window: int,
        frequency: Frequency
    ) -> pd.Series:
        close = data['close']
        returns = close.groupby(level='symbol').pct_change()
        return returns.groupby(level='symbol').rolling(scaled_window).std().droplevel('timestamp')


class RSI(BaseFactor):
    """相对强弱指标"""
    
    def __init__(self, window: int = 14, **kwargs):
        super().__init__(window=window, **kwargs)
    
    @property
    def description(self) -> str:
        return f"{self.name}: RSI({self.window})"
    
    def _compute_impl(
        self,
        data: pd.DataFrame,
        scaled_window: int,
        frequency: Frequency
    ) -> pd.Series:
        close = data['close']
        delta = close.groupby(level='symbol').diff()
        
        gain = delta.copy()
        loss = delta.copy()
        gain[gain < 0] = 0
        loss[loss > 0] = 0
        
        avg_gain = gain.groupby(level='symbol').rolling(scaled_window, min_periods=1).mean()
        avg_loss = loss.abs().groupby(level='symbol').rolling(scaled_window, min_periods=1).mean()
        
        rs = avg_gain / (avg_loss + 1e-8)
        rsi = 100 - (100 / (1 + rs))
        
        return rsi


# ============ 分钟级专用因子 ============

class MinuteMomentum(BaseFactor):
    """
    分钟级动量因子
    
    特点:
    - 自动适配不同分钟频率
    - 可设置日内/日间平滑
    """
    
    @property
    def description(self) -> str:
        return f"{self.name}: {self.window}分钟动量"
    
    def _compute_impl(
        self,
        data: pd.DataFrame,
        scaled_window: int,
        frequency: Frequency
    ) -> pd.Series:
        close = data['close']
        
        # 计算原始动量
        momentum = close.groupby(level='symbol').pct_change(scaled_window)
        
        # 可选: 日内平滑 (消除噪音)
        if self.window > 60:  # 大于1小时应用平滑
            return momentum.groupby(level='symbol').rolling(5).mean().droplevel('timestamp')
        
        return momentum


class OrderFlowImbalance(BaseFactor):
    """
    订单流不平衡因子 (分钟级专用)
    
    反映:
    - 主动买入vs卖出压力
    - 短期供需失衡
    """
    
    @property
    def description(self) -> str:
        return f"{self.name}: 订单流不平衡"
    
    def _compute_impl(
        self,
        data: pd.DataFrame,
        scaled_window: int,
        frequency: Frequency
    ) -> pd.Series:
        close = data['close']
        volume = data['volume']
        
        # 价格变化
        price_change = close.groupby(level='symbol').diff()
        
        # 订单流 = 成交量 × 方向
        order_flow = volume * np.sign(price_change)
        
        return order_flow.groupby(level='symbol').rolling(scaled_window).sum().droplevel('timestamp')


class VolumeWeightedPrice(BaseFactor):
    """
    VWAP因子 (分钟级专用)
    
    反映:
    - 真实平均成本
    - 机构参与程度
    """
    
    @property
    def description(self) -> str:
        return f"{self.name}: 成交量加权价格"
    
    def _compute_impl(
        self,
        data: pd.DataFrame,
        scaled_window: int,
        frequency: Frequency
    ) -> pd.Series:
        close = data['close']
        volume = data['volume']
        
        dollar_volume = close * volume
        
        vwap_sum = dollar_volume.groupby(level='symbol').rolling(scaled_window).sum()
        vol_sum = volume.groupby(level='symbol').rolling(scaled_window).sum()
        
        return vwap_sum / vol_sum


# ============ Pipeline引擎 ============

class MultiFrequencyPipeline:
    """
    多频率Pipeline引擎
    
    特点:
    - 频率自动检测
    - 因子批量计算
    - 统一输出接口
    """
    
    def __init__(self, name: str = "Pipeline"):
        self.name = name
        self.factors: Dict[str, BaseFactor] = {}
        self.frequency: Optional[Frequency] = None
    
    def add_factor(self, name: str, factor: BaseFactor) -> 'MultiFrequencyPipeline':
        """添加因子"""
        self.factors[name] = factor
        return self
    
    def run(
        self,
        data: pd.DataFrame,
        frequency: Frequency = None
    ) -> pd.DataFrame:
        """
        运行Pipeline
        
        Args:
            data: 价格数据
            frequency: 指定频率 (None则自动检测)
            
        Returns:
            因子值DataFrame
        """
        # 自动检测频率
        if frequency is None:
            frequency = DataFrameBuilder.detect_frequency(data)
        
        self.frequency = frequency
        
        results = {}
        
        for name, factor in self.factors.items():
            try:
                result = factor.compute(data, frequency)
                # 确保索引是唯一的
                if not result.index.is_unique:
                    result = result.groupby(level=['symbol', 'timestamp']).last()
                results[name] = result
                print(f"  ✅ {name}: 计算完成")
            except Exception as e:
                print(f"  ❌ {name}: 计算失败 - {e}")
                results[name] = pd.Series(index=data.index)
        
        # 合并结果
        if results:
            # 以原始数据索引为基准
            result_df = pd.DataFrame(results, index=data.index)
            return result_df
        else:
            return pd.DataFrame(results)


# ============ 使用示例 ============

def demo_minute_extension():
    """演示分钟级别扩展"""
    
    print("=" * 60)
    print("🚀 分钟级别可扩展架构演示")
    print("=" * 60)
    
    # ============ 1. 创建日线数据 ============
    print("\n1. 创建日线数据...")
    
    daily_data = []
    symbols = ['SH600000', 'SZ000001']
    
    for symbol in symbols:
        base_price = 10.0
        for day in range(20):
            date = datetime(2024, 1, 1) + pd.Timedelta(days=day)
            ohlcv = OHLCV(
                open=base_price,
                high=base_price * 1.02,
                low=base_price * 0.98,
                close=base_price,
                volume=1e7
            )
            daily_data.append((symbol, date, ohlcv))
            base_price *= 1.001  # 轻微上涨
    
    df_daily = DataFrameBuilder.create(daily_data, Frequency.DAILY)
    print(f"   日线数据: {df_daily.shape}")
    
    # ============ 2. 创建分钟数据 ============
    print("\n2. 创建分钟级数据...")
    
    minute_data = []
    symbols = ['SH600000', 'SZ000001']
    
    for symbol in symbols:
        base_price = 10.0
        for day in range(5):  # 5天
            date = datetime(2024, 1, 1) + pd.Timedelta(days=day)
            
            # 每天 4小时 = 240分钟
            for minute in range(240):
                # 9:30 + minute分钟
                minute_ts = datetime(
                    date.year, date.month, date.day,
                    9, 30, 0
                ) + pd.Timedelta(minutes=minute)
                
                ohlcv = OHLCV(
                    open=base_price,
                    high=base_price * 1.001,
                    low=base_price * 0.999,
                    close=base_price,
                    volume=1e5
                )
                minute_data.append((symbol, minute_ts, ohlcv))
                base_price *= 1.0001
    
    df_minute = DataFrameBuilder.create(minute_data, Frequency.MINUTE_1)
    print(f"   分钟数据: {df_minute.shape}")
    
    # ============ 3. 自动频率检测 ============
    print("\n3. 自动频率检测...")
    
    freq_daily = DataFrameBuilder.detect_frequency(df_daily)
    freq_minute = DataFrameBuilder.detect_frequency(df_minute)
    
    print(f"   日线数据检测: {freq_daily.value}")
    print(f"   分钟数据检测: {freq_minute.value}")
    
    # ============ 4. 构建Pipeline ============
    print("\n4. 构建多频率Pipeline...")
    
    pipeline = MultiFrequencyPipeline("MultiFreqPipeline")
    
    # 添加因子 (窗口以"期"为单位，自动适配)
    pipeline.add_factor('momentum', RollingReturn(window=20))
    pipeline.add_factor('ma', MovingAverage(window=20))
    pipeline.add_factor('volatility', Volatility(window=20))
    pipeline.add_factor('rsi', RSI(window=14))
    
    # ============ 5. 运行日线Pipeline ============
    print("\n5. 运行日线Pipeline...")
    daily_factors = pipeline.run(df_daily, Frequency.DAILY)
    print(f"   结果形状: {daily_factors.shape}")
    
    # ============ 6. 运行分钟线Pipeline ============
    print("\n6. 运行分钟线Pipeline...")
    minute_factors = pipeline.run(df_minute, Frequency.MINUTE_1)
    print(f"   结果形状: {minute_factors.shape}")
    
    # ============ 7. 分钟级专用因子 ============
    print("\n7. 分钟级专用因子...")
    
    minute_pipeline = MultiFrequencyPipeline("MinutePipeline")
    minute_pipeline.add_factor('momentum', MinuteMomentum(window=60))  # 60分钟
    minute_pipeline.add_factor('order_flow', OrderFlowImbalance(window=10))
    minute_pipeline.add_factor('vwap', VolumeWeightedPrice(window=5))
    
    minute_only_factors = minute_pipeline.run(df_minute, Frequency.MINUTE_1)
    print(f"   分钟因子结果: {minute_only_factors.shape}")
    
    print("\n" + "=" * 60)
    print("✅ 演示完成!")
    print("=" * 60)


# ============ 架构总结 ============

ARCHITECTURE_SUMMARY = """
📐 分钟级别可扩展架构设计
═══════════════════════════════════════════════

1. 统一数据接口
   ┌─────────────────────────────────────────┐
   │ DataFrameBuilder                         │
   │ - create(): 创建MultiIndex DataFrame     │
   │ - detect_frequency(): 自动检测频率        │
   └─────────────────────────────────────────┘

2. 频率无关因子
   ┌─────────────────────────────────────────┐
   │ BaseFactor                               │
   │ - _scale_window(): 自动缩放窗口           │
   │ - compute(): 统一计算接口                │
   └─────────────────────────────────────────┘
              │
              ▼
   ┌─────────────────────────────────────────┐
   │ 具体因子 (子类实现)                       │
   │ - RollingReturn (通用)                   │
   │ - MovingAverage (通用)                    │
   │ - RSI (通用)                             │
   │ - MinuteMomentum (分钟专用)               │
   │ - OrderFlowImbalance (分钟专用)          │
   └─────────────────────────────────────────┘

3. Pipeline引擎
   ┌─────────────────────────────────────────┐
   │ MultiFrequencyPipeline                   │
   │ - add_factor(): 添加因子                  │
   │ - run(): 批量计算                        │
   │ - 自动频率适配                           │
   └─────────────────────────────────────────┘

4. 使用流程
   ┌─────────────────────────────────────────┐
   │ 1. 准备数据 (日线/分钟线)                 │
   │ 2. 创建Pipeline                          │
   │ 3. 添加因子 (窗口用"期"为单位)           │
   │ 4. 运行Pipeline (自动适配频率)           │
   │ 5. 获取因子结果                          │
   └─────────────────────────────────────────┘

5. 扩展新因子
   ┌─────────────────────────────────────────┐
   │ class MyFactor(BaseFactor):             │
   │     def _compute_impl(...):             │
   │         # 实现计算逻辑                   │
   │         return result                   │
   └─────────────────────────────────────────┘
"""

if __name__ == '__main__':
    print(ARCHITECTURE_SUMMARY)
    print("\n")
    demo_minute_extension()
