"""
数据模拟器
Data Simulator

生成模拟的股票价格数据用于测试
"""

import pandas as pd
import numpy as np
from typing import List, Union
from datetime import datetime, timedelta


def create_multi_stock_data(
    symbols: List[str] = None,
    start_date: Union[str, datetime] = '2024-01-01',
    periods: int = 100,
    freq: str = '1min',
    seed: int = 42
) -> pd.DataFrame:
    """
    生成多股票模拟数据
    
    Args:
        symbols: 股票代码列表
        start_date: 开始日期
        periods: 数据周期数
        freq: 频率 ('1min', '5min', '1h', '1D', etc.)
        seed: 随机种子
    
    Returns:
        DataFrame with columns: [symbol, timestamp, open, high, low, close, volume]
    """
    if symbols is None:
        symbols = ['STOCK_%03d' % i for i in range(1, 11)]
    
    np.random.seed(seed)
    
    all_data = []
    
    for symbol in symbols:
        # 生成时间索引
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date)
        
        dates = pd.date_range(
            start=start_date,
            periods=periods,
            freq=freq
        )
        
        # 生成价格路径 (带趋势和波动)
        n = len(dates)
        
        # 初始价格 10-100
        initial_price = 10 + np.random.random() * 90
        
        # 每日收益率 (均值0，方差2%)
        returns = np.random.normal(0.0001, 0.02, n)
        
        # 价格
        close = initial_price * np.cumprod(1 + returns)
        
        # 生成 OHLCV
        intraday_volatility = 0.005  # 日内波动
        
        open_price = close * (1 + np.random.normal(0, intraday_volatility, n))
        high_price = np.maximum(open_price, close) * (1 + np.abs(np.random.normal(0, intraday_volatility, n)))
        low_price = np.minimum(open_price, close) * (1 - np.abs(np.random.normal(0, intraday_volatility, n)))
        
        # 成交量
        base_volume = 1000000
        volume = base_volume * (1 + np.random.random(n) * 0.5)
        
        # 涨跌停限制
        limit_up = initial_price * 1.10  # 10% 涨停
        limit_down = initial_price * 0.90  # 跌停
        
        close = np.clip(close, limit_down, limit_up)
        high_price = np.maximum(high_price, close)
        low_price = np.minimum(low_price, close)
        
        df = pd.DataFrame({
            'symbol': symbol,
            'timestamp': dates,
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close,
            'volume': volume
        })
        
        all_data.append(df)
    
    return pd.concat(all_data, ignore_index=True)


def create_single_stock_data(
    symbol: str = 'STOCK_001',
    start_date: Union[str, datetime] = '2024-01-01',
    periods: int = 100,
    freq: str = '1D',
    seed: int = 42
) -> pd.DataFrame:
    """
    生成单股票模拟数据
    
    Args:
        symbol: 股票代码
        start_date: 开始日期
        periods: 数据周期数
        freq: 频率
        seed: 随机种子
    
    Returns:
        DataFrame
    """
    return create_multi_stock_data(
        symbols=[symbol],
        start_date=start_date,
        periods=periods,
        freq=freq,
        seed=seed
    )


def generate_factor_data(
    price_data: pd.DataFrame,
    factor_type: str = 'momentum',
    params: dict = None
) -> pd.DataFrame:
    """
    基于价格数据生成因子值
    
    Args:
        price_data: 价格数据
        factor_type: 因子类型 ('momentum', 'mean_reversion', 'volatility')
        params: 因子参数
    
    Returns:
        DataFrame with [symbol, timestamp, factor_name, factor_value]
    """
    if params is None:
        params = {}
    
    factor_name = factor_type
    
    if factor_type == 'momentum':
        # 动量因子: n日收益率
        n = params.get('n', 20)
        factor_name = f'momentum_{n}d'
        
        result = price_data.groupby('symbol').apply(
            lambda x: x.set_index('timestamp')['close'].pct_change(n)
        ).reset_index()
        result.columns = ['symbol', 'timestamp', 'factor_value']
    
    elif factor_type == 'mean_reversion':
        # 均值回归因子: 偏离n日均线
        n = params.get('n', 20)
        factor_name = f'ma_dist_{n}d'
        
        result = price_data.groupby('symbol').apply(
            lambda x: {
                'timestamp': x['timestamp'],
                'factor_value': (x['close'] - x['close'].rolling(n).mean()) / x['close'].rolling(n).std()
            }
        ).reset_index()
        result = pd.concat(result.tolist(), ignore_index=True)
    
    elif factor_type == 'volatility':
        # 波动率因子: n日收益率标准差
        n = params.get('n', 20)
        factor_name = f'volatility_{n}d'
        
        result = price_data.groupby('symbol').apply(
            lambda x: {
                'timestamp': x['timestamp'],
                'factor_value': x['close'].pct_change().rolling(n).std()
            }
        ).reset_index()
        result = pd.concat(result.tolist(), ignore_index=True)
    
    else:
        raise ValueError(f"Unknown factor type: {factor_type}")
    
    result['factor_name'] = factor_name
    
    return result[['symbol', 'timestamp', 'factor_name', 'factor_value']]


# ==================== 导出 ====================

__all__ = [
    'create_multi_stock_data',
    'create_single_stock_data',
    'generate_factor_data'
]
