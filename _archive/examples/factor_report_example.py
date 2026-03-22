"""
因子研究报告示例
Factor Research Report Example

演示如何使用因子报告生成器进行探索性研究
"""

import sys
import os

# 直接使用本地路径，不通过 pip
sys.path.insert(0, '/Users/xinzhan/.openclaw/workspace')

import pandas as pd
import numpy as np
from datetime import datetime

from quant_factor_system.factors import FactorFactory, create_factor_report


def generate_sample_price_data():
    """生成模拟价格数据"""
    print("📊 生成模拟价格数据...")
    
    dates = pd.date_range('2023-01-01', periods=500, freq='B')
    
    # 生成模拟价格（带趋势和波动）
    np.random.seed(42)
    returns = np.random.randn(500) * 0.02 + 0.0005  # 日收益
    close = 100 * (1 + returns).cumprod()
    
    price_data = pd.DataFrame({
        'close': close,
        'open': close * (1 + np.random.randn(500) * 0.01),
        'high': close * (1 + np.abs(np.random.randn(500)) * 0.02),
        'low': close * (1 - np.abs(np.random.randn(500)) * 0.02),
        'volume': np.random.randint(1000000, 10000000, 500),
    }, index=dates)
    
    price_data.index.name = 'time'
    price_data['symbol'] = 'TEST_STOCK'
    
    print(f"   生成 {len(price_data)} 条数据")
    print(f"   日期范围: {dates[0].date()} ~ {dates[-1].date()}")
    
    return price_data


def example_momentum_factor():
    """示例：动量因子研究"""
    print("\n" + "="*60)
    print("📈 示例1: 动量因子研究")
    print("="*60)
    
    # 创建因子
    momentum = FactorFactory.create('momentum', {'period': 20})
    print(f"因子类型: {type(momentum).__name__}")
    print(f"因子参数: period={momentum.period}")
    
    # 生成数据
    price_data = generate_sample_price_data()
    
    # 创建报告
    print("\n📝 生成因子报告...")
    report = create_factor_report(
        name='momentum_20',
        factor=momentum,
        price_data=price_data,
        output_dir='output/factors'
    )
    
    # 分析
    report.analyze()
    
    # 生成报告
    output_path = report.generate()
    
    # 打开报告
    report.open()
    
    print(f"\n✅ 报告已生成: {output_path}")
    

def example_multiple_factors():
    """示例：多个因子对比研究"""
    print("\n" + "="*60)
    print("📈 示例2: 多因子对比研究")
    print("="*60)
    
    # 因子列表
    factors = [
        ('momentum_20', 'momentum', {'period': 20}),
        ('return_5d', 'return_5d', {}),
        ('zscore_60', 'zscore_60', {}),
    ]
    
    # 生成数据
    price_data = generate_sample_price_data()
    
    # 研究每个因子
    for name, factor_name, params in factors:
        print(f"\n📊 研究因子: {name}")
        
        factor = FactorFactory.create(factor_name, params)
        report = create_factor_report(
            name=name,
            factor=factor,
            price_data=price_data,
            output_dir='output/factors'
        )
        
        report.analyze()
        report.generate()
        print(f"   ✅ {name} 报告已生成")


def example_with_split_date():
    """示例：带训练/测试集分割的因子研究"""
    print("\n" + "="*60)
    print("📈 示例3: 训练/测试集分割研究")
    print("="*60)
    
    # 创建因子
    momentum = FactorFactory.create('momentum', {'period': 60})
    
    # 生成数据
    price_data = generate_sample_price_data()
    
    # 设定分割日期（前80%为训练集）
    split_idx = int(len(price_data) * 0.8)
    split_date = price_data.index[split_idx].strftime('%Y-%m-%d')
    
    print(f"训练集: 起始 ~ {split_date}")
    print(f"测试集: {split_date} ~ 结束")
    
    # 创建报告（带分割日期）
    report = create_factor_report(
        name='momentum_60_with_split',
        factor=momentum,
        price_data=price_data,
        output_dir='output/factors',
        split_date=split_date
    )
    
    report.analyze()
    report.generate()
    report.open()
    
    print(f"\n✅ 报告已生成（包含训练/测试集对比）")


if __name__ == '__main__':
    print("="*60)
    print("🎯 因子报告生成示例")
    print("="*60)
    
    # 运行示例
    example_momentum_factor()
    # example_multiple_factors()  # 解开注释运行多因子对比
    # example_with_split_date()  # 解开注释运行训练/测试集对比
    
    print("\n" + "="*60)
    print("📁 生成的报告位于: output/factors/")
    print("="*60)
