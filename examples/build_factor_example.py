"""
因子构建完整示例
Factor Building Example

展示:
1. 生成模拟数据
2. 构建原始因子
3. 市值中心化
4. 涨跌停剔除
5. 行业中性化
6. 标准化

使用:
    python examples/build_factor_example.py
"""

import os
import sys
import pandas as pd
import numpy as np

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quant_factor_system.factors import FactorProcessor


def build_momentum_factor(
    daily_data: pd.DataFrame,
    lookback: int = 20
) -> pd.DataFrame:
    """
    构建动量因子
    
    原始因子: N日收益率
    
    Args:
        daily_data: 日线数据
        lookback: 回溯天数
        
    Returns:
        原始动量因子
    """
    print(f"📊 构建动量因子 (lookback={lookback})...")
    
    df = daily_data.copy()
    df = df.sort_values(['symbol', 'date'])
    
    # 计算收益率
    df['pct_chg'] = df.groupby('symbol')['close'].pct_change()
    
    # 计算N日累计收益率
    df['ret'] = df.groupby('symbol')['pct_chg'].transform(
        lambda x: x.rolling(window=lookback, min_periods=lookback).sum()
    )
    
    # 因子数据
    factor_df = df[['date', 'symbol', 'ret']].copy()
    factor_df = factor_df.rename(columns={'ret': 'factor_value'})
    factor_df = factor_df.dropna()
    
    print(f"   原始因子: {len(factor_df)} 条")
    
    return factor_df


def build_size_factor(
    daily_data: pd.DataFrame,
    market_cap: pd.Series
) -> pd.DataFrame:
    """
    构建市值因子
    
    原始因子: ln(市值)
    
    Args:
        daily_data: 日线数据
        market_cap: 市值数据
        
    Returns:
        原始市值因子
    """
    print("📊 构建市值因子...")
    
    df = daily_data[['date', 'symbol']].copy()
    df['market_cap'] = df['symbol'].map(market_cap)
    df['factor_value'] = np.log(df['market_cap'].clip(lower=1))
    df = df.dropna()
    
    print(f"   原始因子: {len(df)} 条")
    
    return df[['date', 'symbol', 'factor_value']]


def build_value_factor(
    daily_data: pd.DataFrame,
    market_cap: pd.Series
) -> pd.DataFrame:
    """
    构建价值因子
    
    原始因子: 市盈率 (PE) 或 市值/净利润
    
    Args:
        daily_data: 日线数据
        market_cap: 市值数据
        
    Returns:
        原始价值因子
    """
    print("📊 构建价值因子...")
    
    df = daily_data[['date', 'symbol', 'close']].copy()
    df['market_cap'] = df['symbol'].map(market_cap)
    
    # 假设净利润数据 (这里用模拟数据)
    np.random.seed(42)
    profits = {}
    for symbol in df['symbol'].unique():
        profits[symbol] = np.random.uniform(1e7, 1e10)
    
    df['profit'] = df['symbol'].map(profits)
    
    # PE = 市值 / 净利润
    df['pe'] = df['market_cap'] / df['profit'].replace(0, np.nan)
    
    # 因子值: 取倒数 (低PE好)
    df['factor_value'] = 1 / df['pe']
    df = df.dropna()
    
    print(f"   原始因子: {len(df)} 条")
    
    return df[['date', 'symbol', 'factor_value']]


def build_quality_factor(
    daily_data: pd.DataFrame
) -> pd.DataFrame:
    """
    构建质量因子
    
    原始因子: ROE (净资产收益率)
    
    Args:
        daily_data: 日线数据
        
    Returns:
        原始质量因子
    """
    print("📊 构建质量因子...")
    
    df = daily_data[['date', 'symbol', 'close', 'volume']].copy()
    
    # 模拟ROE数据
    np.random.seed(42)
    roe = {}
    for symbol in df['symbol'].unique():
        roe[symbol] = np.random.uniform(0.05, 0.30)
    
    df['roe'] = df['symbol'].map(roe)
    df['factor_value'] = df['roe']
    df = df.dropna()
    
    print(f"   原始因子: {len(df)} 条")
    
    return df[['date', 'symbol', 'factor_value']]


def build_volatility_factor(
    daily_data: pd.DataFrame,
    lookback: int = 20
) -> pd.DataFrame:
    """
    构建波动率因子
    
    原始因子: N日收益率标准差
    
    Args:
        daily_data: 日线数据
        lookback: 回溯天数
        
    Returns:
        原始波动率因子
    """
    print(f"📊 构建波动率因子 (lookback={lookback})...")
    
    df = daily_data.copy()
    df = df.sort_values(['symbol', 'date'])
    
    # 计算收益率
    df['pct_chg'] = df.groupby('symbol')['close'].pct_change()
    
    # 计算波动率
    df['vol'] = df.groupby('symbol')['pct_chg'].transform(
        lambda x: x.rolling(window=lookback, min_periods=lookback).std()
    )
    
    factor_df = df[['date', 'symbol', 'vol']].copy()
    factor_df = factor_df.rename(columns={'vol': 'factor_value'})
    factor_df = factor_df.dropna()
    
    print(f"   原始因子: {len(factor_df)} 条")
    
    return factor_df


def main():
    """
    主函数: 完整因子构建流程
    """
    print("=" * 60)
    print("Quant Factor System - 因子构建示例")
    print("=" * 60)
    
    # Step 1: 生成模拟日线数据
    print("\n📥 Step 1: 生成模拟日线数据...")
    daily_data = generate_mock_data()
    print(f"   日线数据: {len(daily_data)} 条")
    
    # Step 2: 准备市值和行业数据
    print("\n💰 Step 2: 准备市值和行业数据...")
    
    np.random.seed(42)
    symbols = daily_data['symbol'].unique()
    
    # 模拟市值数据
    market_cap = {}
    for symbol in symbols:
        market_cap[symbol] = np.random.uniform(1e9, 1e11)
    market_cap = pd.Series(market_cap)
    print(f"   市值数据: {len(market_cap)} 只股票")
    
    # 模拟行业数据
    industries = {}
    industry_list = ['银行', '地产', '医药', '消费', '科技', '制造']
    for symbol in symbols:
        industries[symbol] = np.random.choice(industry_list)
    industry = pd.Series(industries)
    print(f"   行业数据: {industry.nunique()} 个行业")
    
    # Step 3: 构建原始因子
    print("\n🔧 Step 3: 构建原始因子...")
    
    factors = {}
    
    # 动量因子
    factors['momentum_20'] = build_momentum_factor(daily_data, lookback=20)
    
    # 市值因子
    factors['size'] = build_size_factor(daily_data, market_cap)
    
    # 价值因子
    factors['value'] = build_value_factor(daily_data, market_cap)
    
    # 质量因子
    factors['quality'] = build_quality_factor(daily_data)
    
    # 波动率因子
    factors['volatility_20'] = build_volatility_factor(daily_data, lookback=20)
    
    # Step 4: 初始化因子处理器
    print("\n⚙️ Step 4: 初始化因子处理器...")
    
    processor = FactorProcessor()
    
    # Step 5: 处理每个因子
    print("\n🔄 Step 5: 处理因子...")
    
    processed_factors = {}
    
    for name, factor_df in factors.items():
        print(f"\n   处理因子: {name}")
        
        # 完整处理流程
        processed = processor.process(
            factor_df.copy(),
            daily_data,      # 日线数据 (涨跌停剔除)
            market_cap,      # 市值数据 (市值中心化)
            industry,        # 行业数据 (行业中性化)
            date_col='date',
            symbol_col='symbol',
            factor_col='factor_value'
        )
        
        # 保存处理后的因子
        processed_factors[name] = processed
        
        # 统计
        print(f"      原始: {len(factor_df)}, 处理后: {len(processed)}")
    
    # Step 6: 汇总统计
    print("\n📊 Step 6: 因子统计...")
    
    for name, df in processed_factors.items():
        valid = df['factor_value']
        print(f"\n   {name}:")
        print(f"      均值: {valid.mean():.4f}, 标准差: {valid.std():.4f}")
        print(f"      最小: {valid.min():.4f}, 最大: {valid.max():.4f}")
    
    # Step 7: 保存到数据库 (代码示例)
    print("\n💾 Step 7: 保存到数据库 (示例代码)...")
    print("""
    # 保存因子到TimescaleDB
    from quant_factor_system.data import QuantDataManager
    
    manager = QuantDataManager()
    
    for name, df in processed_factors.items():
        df['factor_name'] = name
        manager.save_factor(df, name)
    
    print("   ✅ 保存完成")
    """)
    
    print("\n" + "=" * 60)
    print("✅ 因子构建完成!")
    print("=" * 60)
    
    return processed_factors


def generate_mock_data() -> pd.DataFrame:
    """生成模拟日线数据"""
    print("   生成模拟数据...")
    
    np.random.seed(42)
    
    # 股票列表
    symbols = [f'SH{600000 + i}' for i in range(1, 51)]
    
    # 日期
    dates = pd.date_range('2024-01-01', '2024-01-31', freq='B')
    
    data = []
    
    for symbol in symbols:
        base_price = np.random.uniform(10, 50)
        
        for date in dates:
            # 随机涨跌
            change = np.random.uniform(-0.03, 0.035)
            close = base_price * (1 + change)
            base_price = close
            
            high = close * (1 + np.random.uniform(0, 0.02))
            low = close * (1 - np.random.uniform(0, 0.02))
            
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'symbol': symbol,
                'open': close * (1 + np.random.uniform(-0.01, 0.01)),
                'high': high,
                'low': low,
                'close': close,
                'volume': np.random.uniform(1e6, 1e7),
                'amount': np.random.uniform(1e7, 1e8)
            })
    
    df = pd.DataFrame(data)
    print(f"   模拟数据: {len(df)} 条, {len(symbols)} 只股票")
    
    return df


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    
    main()
