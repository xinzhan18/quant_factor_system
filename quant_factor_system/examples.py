"""
完整示例：量化多因子系统使用教程
Complete Example: Quantitative Multi-Factor System Tutorial

本示例展示：
1. 数据获取
2. 因子构建
3. 因子评估
4. 回测
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from quant_factor_system import (
    # 核心组件
    FactorSystem,
    FactorEvaluator,
    BacktestEngine,
    
    # 数据源
    get_a_stock_data,
    MultiSourceDataManager,
    AkshareDataSource,
    
    # 因子
    MomentumFactor,
    ValueFactor,
    QualityFactor,
    SizeFactor,
    GrowthFactor,
    VolatilityFactor,
    
    # Barra 风格因子
    BarraMomentumFactor,
    BarraValueFactor,
    BarraSizeFactor,
    BarraVolatilityFactor,
    BetaFactor,
)


def create_sample_data():
    """
    创建模拟股票数据
    
    在实际项目中，应该使用 get_a_stock_data() 从数据库获取
    """
    print("📊 创建模拟数据...")
    
    np.random.seed(42)
    
    # 配置
    n_stocks = 50
    n_days = 252 * 2  # 2年数据
    
    dates = pd.date_range(start='2022-01-01', periods=n_days, freq='B')
    
    # 股票列表
    stocks = [f'STOCK_{i:03d}' for i in range(n_stocks)]
    
    all_data = {}
    
    for stock in stocks:
        # 模拟价格走势（带趋势和波动）
        trend = np.linspace(0.02, 0.03, n_days)  # 日均收益趋势
        noise = np.random.randn(n_days) * 0.02   # 波动
        returns = trend + noise
        
        # 添加一些特定于股票的效应
        if stock in stocks[:10]:
            returns += 0.0005  # 小市值溢价
        if stock in stocks[20:30]:
            returns -= 0.0003
            
        prices = 100 * np.cumprod(1 + returns)
        
        # 模拟财务数据
        pe = np.random.uniform(8, 40, n_days)
        pb = np.random.uniform(0.5, 5, n_days)
        roe = np.random.uniform(0.05, 0.25, n_days)
        revenue = np.cumsum(np.random.randn(n_days) * 1e8 + 1e8)
        market_cap = prices * np.random.uniform(1e6, 1e7, n_days)
        volume = np.random.randint(1e6, 1e8, n_days)
        
        df = pd.DataFrame({
            'symbol': stock,
            'open': prices * (1 + np.random.randn(n_days) * 0.01),
            'high': prices * (1 + np.abs(np.random.randn(n_days)) * 0.02),
            'low': prices * (1 - np.abs(np.random.randn(n_days)) * 0.02),
            'close': prices,
            'pe': pe,
            'pb': pb,
            'roe': roe,
            'revenue': revenue,
            'market_cap': market_cap,
            'volume': volume,
        }, index=dates)
        
        all_data[stock] = df
    
    # 合并所有股票数据
    combined = pd.concat(all_data.values())
    
    print(f"  ✅ 创建了 {len(combined)} 条数据，{n_stocks} 只股票")
    
    return combined


def calculate_returns(data):
    """计算收益率"""
    print("\n📈 计算收益率...")
    
    # 按股票分组计算收益率
    returns = data.groupby('symbol')['close'].pct_change()
    data['returns'] = returns
    
    # 也计算市场收益
    market_returns = data.groupby('date')['close'].apply(
        lambda x: (x.pct_change()).mean()
    )
    
    print(f"  ✅ 收益率数据范围: {data['returns'].min():.2%} ~ {data['returns'].max():.2%}")
    
    return data, market_returns


def demo_basic_factors():
    """演示基础因子"""
    print("\n" + "="*60)
    print("🎯 Demo 1: 基础因子构建")
    print("="*60)
    
    # 创建数据
    data = create_sample_data()
    data, market_returns = calculate_returns(data)
    
    # 创建因子系统
    system = FactorSystem(name="My Basic Factor System")
    
    # 添加因子
    system.add_factor(MomentumFactor(period=60), weight=1.0)
    system.add_factor(ValueFactor(metric='pe'), weight=1.0)
    system.add_factor(QualityFactor(metric='roe'), weight=1.0)
    system.add_factor(SizeFactor(), weight=0.5)
    system.add_factor(GrowthFactor(metric='revenue'), weight=1.0)
    
    # 计算因子
    print("\n🔢 计算因子值...")
    factor_values = system.calculate_all(data)
    
    print(f"  因子数据形状: {factor_values.shape}")
    print(f"\n  因子统计:")
    print(factor_values.describe().round(4))
    
    # 获取综合得分
    scores = system.get_composite_score()
    print(f"\n⭐ 综合得分范围: [{scores.min():.4f}, {scores.max():.4f}]")
    
    return system, factor_values, data['returns'].dropna()


def demo_barra_factors():
    """演示 Barra 风格因子"""
    print("\n" + "="*60)
    print("🎯 Demo 2: Barra 风格因子")
    print("="*60)
    
    # 创建数据
    data = create_sample_data()
    data, market_returns = calculate_returns(data)
    
    # 创建 Barra 因子系统
    system = FactorSystem(name="Barra Style Factor System")
    
    # 添加 Barra 核心因子
    system.add_factor(BarraSizeFactor(), weight=1.0)
    system.add_factor(BarraMomentumFactor(period=252), weight=1.0)
    system.add_factor(BarraValueFactor(method='pe'), weight=1.0)
    system.add_factor(BarraVolatilityFactor(period=60), weight=0.5)
    system.add_factor(BarraSizeFactor(method='cube_root'), weight=1.0)
    
    # 计算因子
    print("\n🔢 计算 Barra 因子...")
    factor_values = system.calculate_all(data)
    
    print(f"  因子数量: {len(system.factors)}")
    print(f"  因子列表: {list(system.factors.keys())}")
    
    # 因子相关性分析
    corr = system.get_correlation_matrix()
    print(f"\n🔗 因子相关性矩阵:")
    print(corr.round(3))
    
    return system, data['returns'].dropna()


def demo_factor_evaluation():
    """演示因子评估"""
    print("\n" + "="*60)
    print("🎯 Demo 3: 因子评估")
    print("="*60)
    
    # 准备数据
    data = create_sample_data()
    data, market_returns = calculate_returns(data)
    
    # 创建因子系统
    system = FactorSystem(name="Evaluation Factor System")
    system.add_factor(MomentumFactor(period=120), weight=1.0)
    system.add_factor(ValueFactor(metric='pe'), weight=1.0)
    system.add_factor(QualityFactor(metric='roe'), weight=1.0)
    system.add_factor(VolatilityFactor(period=60), weight=0.5)
    
    # 计算因子
    factor_values = system.calculate_all(data)
    returns = data['returns'].dropna()
    
    # 创建评估器
    evaluator = FactorEvaluator(system)
    
    # IC 分析
    print("\n📊 IC 分析...")
    ic_results = evaluator.evaluate_ic(returns)
    
    print("  因子 IC 统计:")
    for name, ic in ic_results.items():
        print(f"    {name}:")
        print(f"      IC = {ic['ic']:.4f}")
        print(f"      IC_IR = {ic['ic_ir']:.4f}")
        print(f"      IC胜率 = {ic['ic_sign_ratio']:.2%}")
    
    # 分组回测
    print("\n💰 分组收益分析...")
    group_returns = evaluator.evaluate_group_return(returns, groups=5)
    
    print("  分组收益 (Q1=低因子值, Q5=高因子值):")
    for col in group_returns.columns:
        spread = group_returns[col].iloc[-1] - group_returns[col].iloc[0]
        print(f"    {col}: 多空收益差 = {spread:.2%}")
    
    # 换手率
    print("\n🔄 因子换手率...")
    turnover = evaluator.evaluate_turnover()
    
    for name, tr in turnover.items():
        print(f"    {name}: {tr:.4f}")
    
    # 打印完整报告
    print("\n📋 完整评估报告:")
    evaluator.print_report(returns)
    
    return evaluator, returns


def demo_backtest():
    """演示回测"""
    print("\n" + "="*60)
    print("🎯 Demo 4: 回测系统")
    print("="*60)
    
    # 准备数据
    data = create_sample_data()
    data, market_returns = calculate_returns(data)
    
    # 创建因子系统
    system = FactorSystem(name="Backtest Factor System")
    system.add_factor(MomentumFactor(period=60), weight=1.0)
    system.add_factor(ValueFactor(metric='pe'), weight=1.0)
    system.add_factor(QualityFactor(metric='roe'), weight=1.0)
    system.add_factor(SizeFactor(), weight=0.5)
    
    # 计算因子
    factor_values = system.calculate_all(data)
    returns = data['returns'].dropna()
    
    # 创建回测引擎
    backtest = BacktestEngine(
        system,
        rebalance_period=20,  # 每月调仓
        top_n=10               # 选前10只股票
    )
    
    # 运行回测
    print("\n🚀 运行回测...")
    portfolio_returns = backtest.run_backtest(data, returns)
    
    # 获取绩效
    performance = backtest.get_performance()
    
    print("\n📈 回测绩效:")
    for metric, value in performance.items():
        if 'return' in metric or 'drawdown' in metric:
            print(f"    {metric}: {value:.2%}")
        else:
            print(f"    {metric}: {value:.4f}")
    
    return backtest


def demo_data_source():
    """演示数据获取"""
    print("\n" + "="*60)
    print("🎯 Demo 5: 数据获取")
    print("="*60)
    
    # 检查可用的数据源
    manager = MultiSourceDataManager()
    
    print("\n📊 可用的数据源:")
    for name in manager.sources.keys():
        print(f"    ✅ {name}")
    
    # 如果有 akshare，尝试获取真实数据
    if 'akshare' in manager.sources:
        print("\n📈 测试获取 A股数据...")
        
        try:
            # 尝试获取平安银行数据
            data = get_a_stock_data('000001', '2023-01-01', '2024-01-01')
            
            if not data.empty:
                print(f"  ✅ 成功获取 {len(data)} 条数据")
                print(f"\n  数据列: {list(data.columns)}")
                print(f"\n  前5行:")
                print(data.head())
            else:
                print("  ⚠️ 获取数据为空")
                
        except Exception as e:
            print(f"  ❌ 获取数据失败: {e}")
            print("  💡 提示: 如果没有安装 akshare，可以安装后使用:")
            print("      pip install akshare")
    
    print("\n💡 数据使用提示:")
    print("    1. A股: pip install akshare")
    print("    2. 美股: pip install yfinance")
    print("    3. 使用 MultiSourceDataManager 统一管理")


def plot_results():
    """绘制结果图表"""
    print("\n" + "="*60)
    print("📊 绘制结果图表")
    print("="*60)
    
    try:
        # 创建数据
        data = create_sample_data()
        data, _ = calculate_returns(data)
        
        # 创建因子系统
        system = FactorSystem(name="Plot Factor System")
        system.add_factor(MomentumFactor(period=60), weight=1.0)
        system.add_factor(ValueFactor(metric='pe'), weight=1.0)
        system.add_factor(QualityFactor(metric='roe'), weight=1.0)
        
        # 计算因子
        factor_values = system.calculate_all(data)
        
        # 绘制因子分布
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # 1. 因子相关性热力图
        ax1 = axes[0, 0]
        corr = system.get_correlation_matrix()
        im = ax1.imshow(corr, cmap='RdBu_r', vmin=-1, vmax=1)
        ax1.set_xticks(range(len(corr.columns)))
        ax1.set_yticks(range(len(corr.columns)))
        ax1.set_xticklabels(corr.columns, rotation=45)
        ax1.set_yticklabels(corr.columns)
        ax1.set_title('因子相关性矩阵')
        plt.colorbar(im, ax=ax1)
        
        # 2. 综合得分分布
        ax2 = axes[0, 1]
        scores = system.get_composite_score()
        scores.dropna().hist(ax=ax2, bins=50)
        ax2.set_title('综合得分分布')
        ax2.set_xlabel('得分')
        ax2.set_ylabel('频率')
        
        # 3. 因子值时序
        ax3 = axes[1, 0]
        for col in factor_values.columns[:3]:
            (factor_values[col] / factor_values[col].abs().max()).rolling(20).mean().plot(ax=ax3, alpha=0.7)
        ax3.set_title('因子值时序 (标准化)')
        ax3.set_xlabel('日期')
        ax3.legend()
        
        # 4. 收益率分布
        ax4 = axes[1, 1]
        returns = data['returns'].dropna()
        returns.hist(ax=ax4, bins=50)
        ax4.set_title('收益率分布')
        ax4.set_xlabel('日收益率')
        ax4.set_ylabel('频率')
        
        plt.tight_layout()
        plt.savefig('factor_analysis.png', dpi=150)
        print("  ✅ 图表已保存到 factor_analysis.png")
        
    except Exception as e:
        print(f"  ❌ 绘图失败: {e}")
        print("  💡 需要安装 matplotlib: pip install matplotlib")


def main():
    """主函数"""
    print("\n" + "="*60)
    print("🚀 量化多因子评价系统 - 完整教程")
    print("="*60)
    
    # 运行所有演示
    demo_basic_factors()
    demo_barra_factors()
    demo_factor_evaluation()
    demo_backtest()
    demo_data_source()
    plot_results()
    
    print("\n" + "="*60)
    print("✅ 所有演示完成!")
    print("="*60)
    
    print("\n💡 下一步:")
    print("    1. 使用真实数据: get_a_stock_data()")
    print("    2. 自定义因子: 继承 Factor 类")
    print("    3. 优化权重: 调整 add_factor() 的 weight 参数")
    print("    4. 保存结果: evaluator.evaluation_results")
    print("="*60)


if __name__ == "__main__":
    main()
