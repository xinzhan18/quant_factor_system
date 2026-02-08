"""
量化多因子系统示例
Example Usage
"""

import pandas as pd
import numpy as np
from quant_factor_system import (
    FactorSystem,
    MomentumFactor,
    ValueFactor,
    QualityFactor,
    VolatilityFactor,
    GrowthFactor,
    FactorEvaluator
)


def generate_sample_data(n_stocks: int = 100, n_days: int = 500) -> pd.DataFrame:
    """
    生成示例数据
    
    Args:
        n_stocks: 股票数量
        n_days: 交易日数量
        
    Returns:
        示例数据
    """
    np.random.seed(42)
    
    dates = pd.date_range(start='2023-01-01', periods=n_days, freq='B')
    
    data_dict = {}
    
    for i in range(n_stocks):
        stock_id = f'STOCK_{i:03d}'
        
        # 生成模拟价格数据
        returns = np.random.randn(n_days) * 0.02
        prices = 100 * np.cumprod(1 + returns)
        
        # PE: 10-50
        pe = np.random.uniform(10, 50, n_days)
        
        # ROE: 0.05-0.30
        roe = np.random.uniform(0.05, 0.30, n_days)
        
        # 营收增长: -0.2 - 0.5
        revenue = 100 * (1 + np.cumsum(np.random.randn(n_days) * 0.02))
        
        # 市值: 10亿 - 1000亿
        market_cap = np.random.uniform(10, 1000, n_days) * 1e8
        
        # 成交量
        volume = np.random.randint(100000, 10000000, n_days)
        
        df = pd.DataFrame({
            'close': prices,
            'pe': pe,
            'roe': roe,
            'revenue': revenue,
            'market_cap': market_cap,
            'volume': volume
        }, index=dates)
        
        df['stock_id'] = stock_id
        data_dict[stock_id] = df
    
    # 合并所有股票数据
    all_data = pd.concat(data_dict.values())
    all_data['stock_id'] = all_data.index
    
    return all_data


def generate_returns(data: pd.DataFrame) -> pd.Series:
    """
    生成收益率序列
    
    Args:
        data: 价格数据
        
    Returns:
        日收益率
    """
    close = data['close']
    returns = close.pct_change()
    return returns


def main():
    """
    主函数：演示因子系统使用
    """
    print("🚀 量化多因子评价系统演示")
    print("=" * 50)
    
    # Step 1: 生成示例数据
    print("\n📊 Step 1: 生成示例数据...")
    data = generate_sample_data(n_stocks=50, n_days=250)
    print(f"   生成了 {len(data)} 条数据")
    
    returns = generate_returns(data)
    print(f"   收益率序列长度: {len(returns)}")
    
    # Step 2: 创建因子系统
    print("\n📈 Step 2: 创建因子系统...")
    system = FactorSystem(name="My Quant Factor System")
    
    # 添加因子
    system.add_factor(MomentumFactor(period=6), weight=1.0)
    system.add_factor(ValueFactor(metric='pe'), weight=1.0)
    system.add_factor(QualityFactor(metric='roe'), weight=1.0)
    system.add_factor(VolatilityFactor(period=20), weight=0.5)
    system.add_factor(GrowthFactor(metric='revenue'), weight=1.0)
    
    print(f"   添加了 {len(system.factors)} 个因子")
    for name in system.factors.keys():
        print(f"   - {name}")
    
    # Step 3: 计算因子值
    print("\n🔢 Step 3: 计算因子值...")
    factor_values = system.calculate_all(data)
    print(f"   因子数据形状: {factor_values.shape}")
    print(f"\n   因子统计:")
    print(factor_values.describe().round(4))
    
    # Step 4: 评估因子
    print("\n🎯 Step 4: 评估因子...")
    evaluator = FactorEvaluator(system)
    
    # IC分析
    ic_results = evaluator.evaluate_ic(returns)
    print("\n   IC分析结果:")
    for name, ic in ic_results.items():
        print(f"   {name}: IC={ic['ic']:.4f}, IC_IR={ic['ic_ir']:.4f}")
    
    # 分组收益
    group_returns = evaluator.evaluate_group_return(returns, groups=5)
    print("\n   分组收益 (多空组合):")
    for name in group_returns.columns:
        spread = group_returns[name].iloc[-1] - group_returns[name].iloc[0]
        print(f"   {name}: 多空收益差 = {spread:.4%}")
    
    # 换手率
    turnover = evaluator.evaluate_turnover()
    print("\n   因子换手率:")
    for name, tr in turnover.items():
        print(f"   {name}: {tr:.4f}")
    
    # Step 5: 综合得分
    print("\n⭐ Step 5: 计算综合得分...")
    composite_score = system.get_composite_score()
    print(f"   综合得分范围: [{composite_score.min():.4f}, {composite_score.max():.4f}]")
    print(f"   综合得分均值: {composite_score.mean():.4f}")
    
    # Step 6: 相关性分析
    print("\n🔗 Step 6: 因子相关性分析...")
    corr_matrix = system.get_correlation_matrix()
    print(corr_matrix.round(3))
    
    # Step 7: 打印完整报告
    print("\n📋 Step 7: 完整评估报告...")
    evaluator.print_report(returns)
    
    # Step 8: 运行简单回测
    print("\n💰 Step 8: 运行回测...")
    from quant_factor_system.evaluator import BacktestEngine
    
    backtest = BacktestEngine(system, rebalance_period=20, top_n=10)
    portfolio_returns = backtest.run_backtest(data, returns)
    
    performance = backtest.get_performance()
    print("\n   回测绩效:")
    for metric, value in performance.items():
        if 'return' in metric or 'drawdown' in metric:
            print(f"   {metric}: {value:.2%}")
        else:
            print(f"   {metric}: {value:.4f}")
    
    print("\n" + "=" * 50)
    print("✅ 演示完成！")
    print("\n💡 提示:")
    print("   1. 修改 generate_sample_data() 使用真实数据")
    print("   2. 添加更多自定义因子")
    print("   3. 调整因子权重优化组合")
    print("   4. 使用 evaluate_ic_decay() 分析因子稳定性")
    print("=" * 50)


if __name__ == "__main__":
    main()
