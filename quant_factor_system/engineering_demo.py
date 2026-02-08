#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工程化因子评估演示
Engineering Factor Evaluation Demo

展示：
1. 数据对齐 (因子t → 收益t+1)
2. 因子预处理 (去极值、标准化、中性化)
3. IC计算 (前一期因子 vs 当期收益)
4. 分组回测 (信号日选股，t+1计算收益)
5. 交易成本 (滑点、手续费、印花税)
"""

import sys
import os
import pandas as pd
import numpy as np

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from quant_factor_system import (
    BacktestConfig,
    FactorEvaluator,
    FactorPreprocessor,
    ICAnalyzer,
    GroupBacktester,
    TransactionCostCalculator,
    align_factor_returns,
    create_return_series,
    MomentumFactor,
    ValueFactor,
    QualityFactor,
    FactorSystem
)


def create_test_data():
    """创建测试数据"""
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=1000, freq='B')
    n = len(dates)
    
    # 创建多只股票
    stocks = ['STOCK_%03d' % i for i in range(1, 51)]
    all_data = {}
    
    for stock in stocks:
        # 价格走势
        trend = np.linspace(0.01, 0.02, n)
        noise = np.random.randn(n) * 0.02
        returns = trend + noise
        prices = 100 * np.cumprod(1 + returns)
        
        df = pd.DataFrame({
            'symbol': stock,
            'close': prices,
            'pct_chg': returns * 100,
            'pe': np.random.uniform(10, 50, n),
            'roe': np.random.uniform(0.05, 0.25, n),
            'market_cap': prices * np.random.uniform(1e6, 1e7, n),
            'industry': np.random.choice(['银行', '医药', '消费', '科技', '制造'], n),
        }, index=dates)
        
        all_data[stock] = df
    
    data = pd.concat(all_data)
    return data


def demo_data_alignment():
    """演示数据对齐"""
    print("\n" + "="*70)
    print("📐 Step 1: 数据对齐演示")
    print("="*70)
    
    # 创建测试数据
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=100, freq='B')
    
    factor = pd.Series(np.random.randn(100) * 0.1 + 0.02, index=dates)
    returns = pd.Series(np.random.randn(100) * 0.02 + 0.01, index=dates)
    
    # 对齐数据
    factor_aligned, returns_aligned = align_factor_returns(factor, returns, shift=1)
    
    print(f"原始因子数: {len(factor)}")
    print(f"原始收益数: {len(returns)}")
    print(f"对齐后: {len(factor_aligned)}")
    
    print("\n关键: 因子在 t 期，收益在 t+1 期")
    print("这样可以避免前视偏差 (look-ahead bias)")


def demo_factor_preprocessing():
    """演示因子预处理"""
    print("\n" + "="*70)
    print("🔧 Step 2: 因子预处理演示")
    print("="*70)
    
    # 创建测试因子
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=500, freq='B')
    factor = pd.Series(np.random.randn(500), index=dates)
    
    # 添加异常值
    factor.iloc[10] = 100
    factor.iloc[20] = -100
    
    market_cap = pd.Series(np.random.uniform(1e9, 1e11, 500), index=dates)
    industry = pd.Series(np.random.choice(['A', 'B', 'C'], 500), index=dates)
    
    # 配置
    config = BacktestConfig(
        winsorize=True,
        standardize=True,
        neutralize_market_cap=True,
        neutralize_industry=True
    )
    
    preprocessor = FactorPreprocessor(config)
    
    print(f"\n原始因子: 均值={factor.mean():.4f}, 标准差={factor.std():.4f}")
    print(f"异常值: {factor.abs() > 3}.sum() = {(factor.abs() > 3).sum()} 个")
    
    # 预处理
    factor_processed = preprocessor.process(factor, market_cap, industry)
    
    print(f"\n预处理后:")
    print(f"  均值={factor_processed.mean():.4f}")
    print(f"  标准差={factor_processed.std():.4f}")
    print(f"  异常值: {(factor_processed.abs() > 3).sum()} 个")
    
    print("\n预处理步骤:")
    print("  1. 去极值 (Winsorize): 截断到 [2%, 98%] 分位数")
    print("  2. 标准化 (Z-score): 转换为均值为0，标准差为1")
    print("  3. 中性化: 去除市值和行业偏差")


def demo_ic_calculation():
    """演示IC计算"""
    print("\n" + "="*70)
    print("📊 Step 3: IC计算演示")
    print("="*70)
    
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=500, freq='B')
    
    factor = pd.Series(np.random.randn(500) * 0.1 + 0.02, index=dates)
    returns = pd.Series(np.random.randn(500) * 0.02 + 0.01, index=dates)
    
    ic_analyzer = ICAnalyzer()
    
    # IC 统计
    ic_stats = ic_analyzer.calculate_ic(factor, returns)
    
    print(f"\nIC 统计:")
    print(f"  IC = {ic_stats['ic']:.4f}")
    print(f"  IC_IR = {ic_stats['ic_ir']:.4f}")
    print(f"  IC胜率 = {ic_stats['ic_sign_ratio']:.2%}")
    
    # IC 衰减
    ic_decay = ic_analyzer.calculate_ic_decay(factor, returns)
    
    print(f"\nIC 衰减:")
    for lag, ic in ic_decay.items():
        print(f"  {lag}: {ic:.4f}")
    
    print("\n解读:")
    print("  IC > 0.03: 因子有预测能力")
    print("  IC衰减慢: 因子效果持久")
    print("  IC胜率 > 50%: 正相关时间多")


def demo_group_backtest():
    """演示分组回测"""
    print("\n" + "="*70)
    print("💰 Step 4: 分组回测演示")
    print("="*70)
    
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=500, freq='B')
    
    factor = pd.Series(np.random.randn(500) * 0.1 + 0.02, index=dates)
    returns = pd.Series(np.random.randn(500) * 0.02 + 0.01, index=dates)
    
    config = BacktestConfig(num_groups=5)
    backtester = GroupBacktester(config)
    
    # 运行回测
    group_rets, stats = backtester.run_backtest(factor, returns)
    
    print(f"\n分组收益 (因子Q1最低 -> Q5最高):")
    for g, ret in group_rets.items():
        print(f"  {g}: {ret:.4f}")
    
    print(f"\n多空收益 (Q5 - Q1): {stats['long_short_return']:.4f}")
    print(f"多空夏普: {stats['long_short_sharpe']:.4f}")
    print(f"换手率: {stats['turnover']:.4f}")
    
    print("\n解读:")
    print("  多空收益 > 0: 因子方向正确")
    print("  夏普越高: 风险调整后收益越好")


def demo_transaction_cost():
    """演示交易成本"""
    print("\n" + "="*70)
    print("💸 Step 5: 交易成本演示")
    print("="*70)
    
    config = BacktestConfig(
        commission_rate=0.001,   # 万1
        stamp_tax_rate=0.001,     # 千1 (卖出)
        slippage_rate=0.001       # 千1
    )
    
    calculator = TransactionCostCalculator(config)
    
    print(f"\n交易成本配置:")
    print(f"  手续费率: {config.commission_rate:.4f} ({config.commission_rate*100:.2f}%)")
    print(f"  印花税率: {config.stamp_tax_rate:.4f} ({config.stamp_tax_rate*100:.2f}%)")
    print(f"  滑点率: {config.slippage_rate:.4f} ({config.slippage_rate*100:.2f}%)")
    
    # 假设
    portfolio_value = 1000000  # 100万
    turnover_rate = 0.2        # 20% 换手率
    
    costs = calculator.calculate_total_cost(portfolio_value, turnover_rate)
    
    print(f"\n成本估算 (组合100万, 换手率20%):")
    print(f"  佣金: {costs['commission']:.2f} 元")
    print(f"  滑点: {costs['slippage']:.2f} 元")
    print(f"  总成本: {costs['total_cost']:.2f} 元")
    print(f"  成本占比: {costs['total_cost']/portfolio_value*100:.4f}%")
    
    print("\n计算公式:")
    print("  佣金 = 交易金额 × 手续费率")
    print("  印花税 = 卖出金额 × 印花税率")
    print("  滑点 = 成交价 × 滑点率 × 规模因子")


def demo_full_evaluation():
    """完整评估演示"""
    print("\n" + "="*70)
    print("🚀 Step 6: 完整因子评估")
    print("="*70)
    
    # 创建测试数据
    print("\n创建测试数据...")
    data = create_test_data()
    print(f"数据: {len(data)} 条, {data['symbol'].nunique()} 只股票")
    
    # 计算因子
    print("\n计算因子...")
    system = FactorSystem(name="Test System")
    system.add_factor(MomentumFactor(period=20), weight=1.0)
    system.add_factor(ValueFactor(metric='pe'), weight=1.0)
    system.add_factor(QualityFactor(metric='roe'), weight=1.0)
    
    factor_values = system.calculate_all(data)
    
    # 计算收益率
    returns = data.groupby('symbol')['close'].pct_change().dropna()
    
    # 配置
    config = BacktestConfig(
        num_groups=5,
        winsorize=True,
        standardize=True,
        neutralize_market_cap=True,
        neutralize_industry=True,
        commission_rate=0.001,
        stamp_tax_rate=0.001,
        slippage_rate=0.001
    )
    
    # 评估
    evaluator = FactorEvaluator(config)
    
    results = evaluator.evaluate_multiple(
        factor_values,
        returns,
        data['market_cap'],
        data['industry']
    )
    
    # 打印报告
    evaluator.print_report()
    
    return results


def main():
    """主函数"""
    print("\n" + "="*70)
    print("🚀 工程化因子评估框架演示")
    print("="*70)
    print("""
标准因子评估架构:

1. 数据对齐: 因子(t) → 收益(t+1)  避免前视偏差
2. 因子预处理: 去极值 → 标准化 → 中性化
3. IC计算: 前一期因子 vs 当期收益
4. 分组回测: 信号日选股，t+1计算收益
5. 交易成本: 滑点、手续费、印花税
""")
    
    # 各步骤演示
    demo_data_alignment()
    demo_factor_preprocessing()
    demo_ic_calculation()
    demo_group_backtest()
    demo_transaction_cost()
    
    # 完整评估
    results = demo_full_evaluation()
    
    print("\n" + "="*70)
    print("✅ 工程化因子评估演示完成!")
    print("="*70)
    
    print("""
下一步:
  1. 使用真实数据: get_real_stock_data()
  2. 添加更多因子
  3. 优化参数配置
  4. 生成可视化报告
""")


if __name__ == "__main__":
    main()
