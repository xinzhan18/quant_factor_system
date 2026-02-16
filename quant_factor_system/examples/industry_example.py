"""
行业因子使用示例
Industry Factor Usage Examples

运行:
    python examples/industry_example.py
"""

import pandas as pd
from datetime import datetime, timedelta
import sys

# 添加路径
sys.path.insert(0, '.')

from quant_factor_system.data import (
    IndustrySource,
    IndustryStorage,
    TimescaleDB
)


def example_get_industry_classification():
    """示例: 获取行业分类"""
    print("\n" + "="*60)
    print("示例1: 获取行业分类")
    print("="*60)
    
    source = IndustrySource()
    
    # 获取最新行业分类
    df = source.get_industry_classification(
        date=datetime.now().strftime('%Y%m%d'),
        level='中信一级'
    )
    
    print(f"\n行业数量: {df['industry'].nunique()}")
    print(f"股票数量: {len(df)}")
    print(f"\n前10条记录:")
    print(df.head(10))
    
    return df


def example_get_industry_stocks():
    """示例: 获取某行业的成分股"""
    print("\n" + "="*60)
    print("示例2: 获取行业成分股")
    print("="*60)
    
    source = IndustrySource()
    
    # 获取银行股
    stocks = source.get_industry_stocks(
        industry='中信一级-银行',
        date=datetime.now().strftime('%Y%m%d')
    )
    
    print(f"\n银行股数量: {len(stocks)}")
    print(f"前20只: {stocks[:20]}")
    
    return stocks


def example_get_industry_factors():
    """示例: 获取行业因子"""
    print("\n" + "="*60)
    print("示例3: 获取行业因子")
    print("="*60)
    
    source = IndustrySource()
    
    # 获取行业因子
    df = source.get_industry_factors(
        date=datetime.now().strftime('%Y%m%d'),
        factors=['industry_return', 'industry_momentum', 'industry_volatility']
    )
    
    print(f"\n行业数量: {len(df)}")
    print(f"\n行业因子数据:")
    print(df.head(10))
    
    return df


def example_save_industry_factors():
    """示例: 保存行业因子到数据库"""
    print("\n" + "="*60)
    print("示例4: 保存行业因子到数据库")
    print("="*60)
    
    # 初始化存储
    storage = IndustryStorage()
    
    # 创建表
    storage.create_tables()
    
    # 获取因子
    source = IndustrySource()
    df = source.get_industry_factors(
        date=datetime.now().strftime('%Y%m%d')
    )
    
    if df.empty:
        print("⚠️ 无因子数据")
        return
    
    # 保存
    count = storage.save_industry_factors(df)
    print(f"✅ 保存行业因子: {count} 条")
    
    # 查询验证
    df_saved = storage.get_industry_factors(
        date=datetime.now().strftime('%Y-%m-%d')
    )
    print(f"验证查询: {len(df_saved)} 条")
    
    return df_saved


def example_get_factor_series():
    """示例: 获取行业因子时间序列"""
    print("\n" + "="*60)
    print("示例5: 获取行业因子时间序列")
    print("="*60)
    
    storage = IndustryStorage()
    
    # 获取银行板块动量因子
    df = storage.get_industry_factor_series(
        factor_name='industry_momentum',
        industry='中信一级-银行',
        start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
        end_date=datetime.now().strftime('%Y-%m-%d')
    )
    
    if df.empty:
        print("⚠️ 无历史数据")
        return
    
    print(f"\n时间序列长度: {len(df)}")
    print(df.head())
    
    return df


def main():
    """运行所有示例"""
    print("\n" + "="*60)
    print("🚀 行业因子模块示例")
    print("="*60)
    
    try:
        # 示例1: 获取行业分类
        example_get_industry_classification()
        
        # 示例2: 获取行业成分股
        example_get_industry_stocks()
        
        # 示例3: 获取行业因子
        example_get_industry_factors()
        
        # 示例4: 保存到数据库
        example_save_industry_factors()
        
        # 示例5: 获取时间序列
        example_get_factor_series()
        
        print("\n" + "="*60)
        print("✅ 所有示例运行完成")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
