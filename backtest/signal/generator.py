"""
交易信号生成器 - 生成买卖信号
Trade Signal Generator

功能:
1. 因子信号生成
2. 信号过滤
3. 信号存储
4. 信号历史查询
"""

import pandas as pd
from typing import Dict, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import os

# 信号历史最大保留条数，防止内存无限增长
MAX_HISTORY = 1000


class SignalType(Enum):
    """信号类型"""
    BUY = 'buy'
    SELL = 'sell'
    HOLD = 'hold'


class SignalSource(Enum):
    """信号来源"""
    FACTOR = 'factor'  # 因子驱动
    TECHNICAL = 'technical'  # 技术指标
    STOPLOSS = 'stoploss'  # 止损
    REBALANCE = 'rebalance'  # 再平衡


@dataclass
class TradeSignal:
    """交易信号"""
    timestamp: datetime
    symbol: str
    signal_type: SignalType
    source: SignalSource
    strength: float  # 信号强度 0-1
    price: float  # 当前价格
    reason: str = ''  # 信号原因
    
    def to_dict(self) -> dict:
        return {
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'symbol': self.symbol,
            'signal_type': self.signal_type.value,
            'source': self.source.value,
            'strength': self.strength,
            'price': self.price,
            'reason': self.reason
        }


@dataclass
class SignalBatch:
    """信号批次"""
    timestamp: datetime
    signals: List[TradeSignal] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'signals': [s.to_dict() for s in self.signals]
        }


class SignalGenerator:
    """
    交易信号生成器
    
    根据因子值、仓位状态、市场条件生成交易信号
    """
    
    def __init__(self, min_strength: float = 0.3):
        """
        初始化
        
        Args:
            min_strength: 最小信号强度阈值
        """
        self.min_strength = min_strength
        self.signal_history: List[SignalBatch] = []
    
    def generate_factor_signals(
        self,
        factor_df: pd.DataFrame,
        price_df: pd.DataFrame,
        top_n: int = 50,
        rebalance_freq: str = 'daily'
    ) -> List[TradeSignal]:
        """
        根据因子生成信号
        
        Args:
            factor_df: 因子数据
            price_df: 价格数据
            top_n: 选入股票数量
            rebalance_freq: 调仓频率
            
        Returns:
            信号列表
        """
        # 合并数据
        merged = pd.merge(factor_df, price_df, on=['time', 'symbol'], how='inner')
        merged = merged.dropna(subset=['value'])
        
        # 获取最新日期
        latest_date = merged['time'].max()
        latest_data = merged[merged['time'] == latest_date]
        
        # 按因子值排序
        latest_data = latest_data.sort_values('value', ascending=False)
        
        signals = []
        
        # 生成买入信号（Top N）
        for i, row in latest_data.head(top_n).iterrows():
            signal = TradeSignal(
                timestamp=latest_date,
                symbol=row['symbol'],
                signal_type=SignalType.BUY,
                source=SignalSource.FACTOR,
                strength=1.0 - (i / top_n),  # 排名越高，强度越强
                price=row['close'],
                reason=f"因子值排名第{i+1}"
            )
            signals.append(signal)
        
        # 保存到历史
        self.signal_history.append(SignalBatch(latest_date, signals))
        if len(self.signal_history) > MAX_HISTORY:
            self.signal_history = self.signal_history[-MAX_HISTORY:]

        return signals
    
    def generate_technical_signals(
        self,
        price_df: pd.DataFrame,
        indicators: Dict[str, pd.Series] = None
    ) -> List[TradeSignal]:
        """
        生成技术指标信号
        
        Args:
            price_df: 价格数据
            indicators: 技术指标字典
            
        Returns:
            信号列表
        """
        signals = []
        
        if price_df.empty:
            return signals
        
        latest = price_df.iloc[-1]
        timestamp = latest['time']
        
        # 简单的MA交叉信号
        if 'ma5' in price_df.columns and 'ma20' in price_df.columns:
            if len(price_df) >= 2:
                prev = price_df.iloc[-2]
                
                # 金叉买入
                if prev['ma5'] <= prev['ma20'] and latest['ma5'] > latest['ma20']:
                    signals.append(TradeSignal(
                        timestamp=timestamp,
                        symbol=latest['symbol'],
                        signal_type=SignalType.BUY,
                        source=SignalSource.TECHNICAL,
                        strength=0.7,
                        price=latest['close'],
                        reason="MA5上穿MA20金叉"
                    ))
                
                # 死叉卖出
                elif prev['ma5'] >= prev['ma20'] and latest['ma5'] < latest['ma20']:
                    signals.append(TradeSignal(
                        timestamp=timestamp,
                        symbol=latest['symbol'],
                        signal_type=SignalType.SELL,
                        source=SignalSource.TECHNICAL,
                        strength=0.7,
                        price=latest['close'],
                        reason="MA5下穿MA20死叉"
                    ))
        
        return signals
    
    def filter_signals(
        self,
        signals: List[TradeSignal],
        min_strength: float = None,
        exclude_symbols: List[str] = None
    ) -> List[TradeSignal]:
        """
        过滤信号
        
        Args:
            signals: 原始信号
            min_strength: 最小强度
            exclude_symbols: 排除的股票
            
        Returns:
            过滤后的信号
        """
        if min_strength is None:
            min_strength = self.min_strength
        
        filtered = []
        
        for signal in signals:
            # 强度过滤
            if signal.strength < min_strength:
                continue
            
            # 排除列表
            if exclude_symbols and signal.symbol in exclude_symbols:
                continue
            
            filtered.append(signal)
        
        return filtered
    
    def merge_signals(
        self,
        signal_lists: List[List[TradeSignal]],
        method: str = 'strength'
    ) -> List[TradeSignal]:
        """
        合并多个信号源
        
        Args:
            signal_lists: 信号列表
            method: 合并方法 ('strength'/'union')
            
        Returns:
            合并后的信号
        """
        if method == 'strength':
            # 按强度排序，取最高的
            all_signals = []
            for signals in signal_lists:
                all_signals.extend(signals)
            
            # 按股票分组，取最强信号
            symbol_signals = {}
            for signal in all_signals:
                if signal.symbol not in symbol_signals:
                    symbol_signals[signal.symbol] = signal
                elif signal.strength > symbol_signals[signal.symbol].strength:
                    symbol_signals[signal.symbol] = signal
            
            return list(symbol_signals.values())
        
        elif method == 'union':
            # 取并集
            all_signals = []
            seen = set()
            for signals in signal_lists:
                for signal in signals:
                    key = (signal.symbol, signal.signal_type)
                    if key not in seen:
                        all_signals.append(signal)
                        seen.add(key)
            return all_signals
        
        return []
    
    def get_signals_by_date(
        self,
        date: datetime
    ) -> List[TradeSignal]:
        """获取指定日期的信号"""
        for batch in self.signal_history:
            if batch.timestamp.date() == date.date():
                return batch.signals
        return []
    
    def get_signal_history(
        self,
        symbol: str = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> pd.DataFrame:
        """
        获取信号历史
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            信号历史DataFrame
        """
        all_signals = []
        
        for batch in self.signal_history:
            # 日期过滤
            if start_date and batch.timestamp < start_date:
                continue
            if end_date and batch.timestamp > end_date:
                continue
            
            for signal in batch.signals:
                # 股票过滤
                if symbol and signal.symbol != symbol:
                    continue
                
                all_signals.append(signal.to_dict())
        
        return pd.DataFrame(all_signals)
    
    def save_signals(self, filepath: str):
        """保存信号到文件"""
        data = {
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'batches': [batch.to_dict() for batch in self.signal_history]
        }
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def load_signals(self, filepath: str):
        """从文件加载信号"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.signal_history = []
        for batch_data in data.get('batches', []):
            signals = []
            for s in batch_data.get('signals', []):
                signal = TradeSignal(
                    timestamp=datetime.strptime(s['timestamp'], '%Y-%m-%d %H:%M:%S'),
                    symbol=s['symbol'],
                    signal_type=SignalType(s['signal_type']),
                    source=SignalSource(s['source']),
                    strength=s['strength'],
                    price=s['price'],
                    reason=s.get('reason', '')
                )
                signals.append(signal)
            
            batch = SignalBatch(
                timestamp=datetime.strptime(batch_data['timestamp'], '%Y-%m-%d %H:%M:%S'),
                signals=signals
            )
            self.signal_history.append(batch)
    
    def clear_history(self):
        """清空信号历史"""
        self.signal_history = []


def create_signal_generator(min_strength: float = 0.3) -> SignalGenerator:
    """创建信号生成器"""
    return SignalGenerator(min_strength)


# ==================== 导出 ====================

__all__ = [
    'SignalGenerator',
    'SignalType',
    'SignalSource',
    'TradeSignal',
    'SignalBatch',
    'create_signal_generator',
]
