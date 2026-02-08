"""
模拟数据生成器
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime


def create_multi_stock_data(
    symbols: List[str],
    start_date: str = '2024-01-01',
    periods: int = 500,
    freq: str = 'B',
    seed: int = 42,
    price_range: Tuple[float, float] = (80, 120),
    base_market_cap: float = 1e9,
) -> pd.DataFrame:
    """
    创建多股票模拟数据
    
    Args:
        symbols: 股票代码列表
        start_date: 开始日期
        periods: 周期数
        freq: 频率 ('B' 工作日, 'D' 日)
        seed: 随机种子
        price_range: 价格范围
        base_market_cap: 基础市值
        
    Returns:
        模拟数据 DataFrame，使用唯一 MultiIndex
    """
    np.random.seed(seed)
    dates = pd.date_range(start_date, periods=periods, freq=freq)
    
    index_tuples = []
    data_list = []
    
    for symbol in symbols:
        base_price = np.random.uniform(*price_range)
        trend = np.random.uniform(-0.0005, 0.0005)  # 日趋势
        
        for i, date in enumerate(dates):
            price = base_price * (1 + trend * i) + np.random.randn() * 2
            market_cap = price * np.random.uniform(1e7, 1e8)
            
            index_tuples.append((symbol, date))
            data_list.append({
                'open': price * (1 + np.random.uniform(-0.01, 0.01)),
                'high': price * (1 + np.random.uniform(0, 0.02)),
                'low': price * (1 + np.random.uniform(-0.02, 0)),
                'close': price,
                'volume': np.random.uniform(1e6, 1e8),
                'pe': np.random.uniform(10, 50),
                'pb': np.random.uniform(1, 5),
                'roe': np.random.uniform(0.05, 0.25),
                'market_cap': market_cap,
                'industry': np.random.choice(['金融', '医药', '科技', '消费', '制造'], 1)[0],
            })
    
    df = pd.DataFrame(data_list, index=pd.MultiIndex.from_tuples(index_tuples, names=['symbol', 'date']))
    
    return df


def create_factor_signal(
    data: pd.DataFrame,
    factor_type: str = 'momentum',
    **kwargs
) -> pd.Series:
    """
    创建因子信号
    
    Args:
        data: 价格数据
        factor_type: 因子类型 ('momentum', 'value', 'quality', 'volatility')
        **kwargs: 因子参数
        
    Returns:
        因子信号 Series
    """
    if factor_type == 'momentum':
        period = kwargs.get('period', 20)
        return data.groupby('symbol')['close'].pct_change(period)
    
    elif factor_type == 'value':
        return 1 / data['pe']  # 市盈率倒数
    
    elif factor_type == 'quality':
        return data['roe']
    
    elif factor_type == 'volatility':
        period = kwargs.get('period', 20)
        return data.groupby('symbol')['close'].rolling(period).std()
    
    elif factor_type == 'size':
        return np.log(data['market_cap'])
    
    elif factor_type == 'liquidity':
        period = kwargs.get('period', 20)
        return data.groupby('symbol')['volume'].rolling(period).mean()
    
    else:
        raise ValueError(f"Unknown factor type: {factor_type}")


def create_returns(
    data: pd.DataFrame,
    forward_periods: int = 1
) -> pd.Series:
    """
    创建未来收益序列
    
    Args:
        data: 价格数据
        forward_periods: 未来期数
        
    Returns:
        未来收益率 Series
    """
    return data.groupby('symbol')['close'].pct_change(forward_periods).shift(-forward_periods)


if __name__ == '__main__':
    # 测试
    print("测试模拟数据生成器...")
    
    data = create_multi_stock_data(
        symbols=['STOCK_%03d' % i for i in range(1, 11)],
        periods=100
    )
    
    print(f"数据形状: {data.shape}")
    print(f"索引类型: {type(data.index)}")
    print(f"索引唯一: {data.index.is_unique}")
    print(f"\n前5行:\n{data.head()}")
