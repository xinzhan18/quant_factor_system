#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alphalens 集成演示
Alphalens Integration Demo

展示：
1. 数据格式转换
2. 生成专业 Tear Sheet
3. 高级统计分析
4. 保留原有架构
"""

import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

import pandas as pd
import numpy as np


def demo_alphalens_integration():
    """演示 Alphalens 集成"""
    print("\n" + "="*70)
    print("🚀 Alphalens 集成演示")
    print("="*70)
    
    # 检查 Alphalens
    from quant_factor_system.evaluation import ALPHALENS_AVAILABLE
    
    if not ALPHALENS_AVAILABLE:
        print("\n⚠️ Alphalens 未安装")
        print("💡 安装: pip install alphalens")
        print("\n先演示我们的架构...")
    
    # 1. 创建测试数据
    print("\n📊 Step 1: 创建测试数据")
    np.random.seed(42)
    
    dates = pd.date_range('2020-01-01', periods=500, freq='B')
    assets = ['ASSET_%03d' % i for i in range(10)]
    n, m = len(dates), len(assets)
    
    # 因子数据
    factor_data = pd.DataFrame(
        np.random.randn(n, m),
        index=dates,
        columns=assets
    )
    
    # 价格数据
    prices = pd.DataFrame(
        100 * np.cumprod(1 + np.random.randn(n, m) * 0.02, axis=0),
        index=dates,
        columns=assets
    )
    
    print(f"  因子数据: {factor_data.shape}")
    print(f"  价格数据: {prices.shape}")
    
    # 2. 使用我们的架构
    print("\n🔧 Step 2: 使用原有架构")
    
    from quant_factor_system import (
        BacktestConfig, FactorEvaluator, FactorSystem,
        MomentumFactor, ValueFactor
    )
    
    config = BacktestConfig(
        num_groups=5,
        winsorize=True,
        neutralize_market_cap=True
    )
    
    evaluator = FactorEvaluator(config)
    
    # 转换为长格式
    factor_long = factor_data.stack()
    factor_long.name = 'factor'
    
    returns_long = prices.pct_change().stack()
    returns_long.name = 'returns'
    
    # 评估因子
    results = evaluator.evaluate(
        'TestFactor',
        factor_long,
        returns_long
    )
    
    print(f"  IC: {results.ic:.4f}")
    print(f"  IC胜率: {results.ic_sign_ratio:.2%}")
    print(f"  多空收益: {results.long_short_return:.4f}")
    
    # 3. 使用 Alphalens（如果已安装）
    if ALPHALENS_AVAILABLE:
        print("\n📈 Step 3: 使用 Alphalens")
        
        from quant_factor_system.evaluation import (
            AlphalensWrapper,
            calculate_ic_stats,
            calculate_ic_decay,
            plot_ic_analysis
        )
        
        # 创建包装器
        wrapper = AlphalensWrapper.from_quant_system(factor_data, prices)
        
        # 转换为 Alphalens 格式
        alphalens_data = wrapper.to_alphalens_format()
        print(f"  Alphalens 数据: {alphalens_data.shape}")
        
        # IC 统计
        ic = alphalens_data.groupby(level='date').apply(
            lambda x: x['factor'].corr(x['1D'])
        )
        
        ic_stats = calculate_ic_stats(ic)
        
        print("\n  📊 IC 统计:")
        print(f"    均值: {ic_stats['ic_mean']:.4f}")
        print(f"    t-stat: {ic_stats['t_statistic']:.4f}")
        print(f"    p-value: {ic_stats['p_value']:.4f}")
        print(f"    95%置信区间: [{ic_stats['ci_95_lower']:.4f}, {ic_stats['ci_95_upper']:.4f}]")
        
        # IC 衰减
        ic_decay = calculate_ic_decay(ic)
        print("\n  📉 IC 衰减:")
        for lag, corr in ic_decay.head(5).items():
            print(f"    {lag}: {corr:.4f}")
        
        # 绘图
        try:
            fig = plot_ic_analysis(ic, './test_reports/ic_analysis.png')
            print("\n  ✅ IC 分析图已保存")
        except Exception as e:
            print(f"  ⚠️ 绘图失败: {e}")
    
    # 4. 总结
    print("\n" + "="*70)
    print("📋 架构对比")
    print("="*70)
    
    print("""
┌─────────────────┬────────────────────────────────────────┐
│     特性        │              说明                        │
├─────────────────┼────────────────────────────────────────┤
│ 我们的架构      │ ✅ 轻量、简单、易用                      │
│                │ ✅ 灵活、可定制                          │
│                │ ⚠️ 功能相对基础                          │
├─────────────────┼────────────────────────────────────────┤
│ Alphalens 集成  │ ✅ 完整 Tear Sheet                      │
│                │ ✅ 高级统计分析 (t-test, p-value)        │
│                │ ✅ 专业可视化                            │
│                │ ❌ 需要安装额外依赖                      │
├─────────────────┼────────────────────────────────────────┤
│ 混合使用        │ ✅ 兼两家之长                           │
│                │ ✅ 数据 → 计算 → 评估 (我们)              │
│                │ ✅ 分析 → 可视化 (Alphalens)             │
└─────────────────┴────────────────────────────────────────┘
""")
    
    print("💡 使用建议:")
    print("   1. 日常分析: 使用我们的架构，简单快捷")
    print("   2. 深度研究: 集成 Alphalens，获取专业分析")
    print("   3. 报告生成: 使用 Alphalens Tear Sheet")
    
    print("\n" + "="*70)


def demo_advanced_statistics():
    """演示高级统计功能"""
    print("\n" + "="*70)
    print("📊 高级统计分析演示")
    print("="*70)
    
    from quant_factor_system.evaluation import (
        calculate_ic_stats,
        calculate_ic_decay,
        calculate_group_returns
    )
    
    # 创建测试数据
    np.random.seed(42)
    ic_series = pd.Series(np.random.randn(100))
    ic_series.iloc[::5] = np.random.uniform(0.05, 0.15, 20)  # 添加一些正IC
    
    # IC 统计
    ic_stats = calculate_ic_stats(ic_series)
    
    print("\n📈 IC 统计检验:")
    print(f"  均值: {ic_stats['ic_mean']:.4f}")
    print(f"  t-statistic: {ic_stats['t_statistic']:.4f}")
    print(f"  p-value: {ic_stats['p_value']:.4f}")
    
    if ic_stats['p_value'] < 0.05:
        print("  ✅ IC 统计显著 (p < 0.05)")
    else:
        print("  ⚠️ IC 不显著 (p >= 0.05)")
    
    # IC 衰减
    ic_decay = calculate_ic_decay(ic_series)
    print("\n📉 IC 衰减:")
    for lag, corr in ic_decay.items():
        print(f"  {lag}: {corr:.4f}")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    demo_alphalens_integration()
    demo_advanced_statistics()
    
    print("\n✅ Alphalens 集成演示完成!")
