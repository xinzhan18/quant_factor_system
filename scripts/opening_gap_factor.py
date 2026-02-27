"""
开盘缺口因子 (Opening Gap Factor)
===================================
公式: delta(close_return, 1) / yesterday_intraday_return
其中:
  - close_return = (close - delay(close,1)) / delay(close,1)
  - yesterday_intraday_return = (delay(close,1) - delay(open,1)) / delay(close,1)

含义: 今日收益率变化 / 昨日日内收益率，反映动量加速程度
"""

import pandas as pd
import numpy as np


def calc_opening_gap(df: pd.DataFrame) -> pd.Series:
    """
    计算开盘缺口因子
    
    Parameters:
    -----------
    df : pd.DataFrame
        必须包含 'open', 'close' 列，index 为 (symbol, time)
    
    Returns:
    --------
    pd.Series : 因子值
    """
    # 昨日收盘价
    delay_close = df['close'].groupby(level='symbol').shift(1)
    # 昨日开盘价
    delay_open = df['open'].groupby(level='symbol').shift(1)
    
    # 收盘收益率 (当日)
    close_return = (df['close'] - delay_close) / delay_close
    
    # 昨日日内收益率
    yesterday_return = (delay_close - delay_open) / delay_close
    
    # 因子值: 收益率变化 / 昨日日内收益
    factor = close_return.groupby(level='symbol').diff(1) / yesterday_return
    
    return factor


if __name__ == '__main__':
    # 测试
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    symbols = ['000001.SZ', '000002.SZ']
    idx = pd.MultiIndex.from_product([symbols, dates], names=['symbol', 'time'])
    np.random.seed(42)
    df = pd.DataFrame({
        'open': np.random.uniform(10, 20, len(idx)),
        'close': np.random.uniform(10, 20, len(idx)),
    }, index=idx).reset_index()
    
    df['opening_gap'] = calc_opening_gap(df)
    print(df.dropna().head(10))
