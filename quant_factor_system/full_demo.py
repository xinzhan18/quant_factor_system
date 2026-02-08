"""
完整自动化示例
Complete Automation Example

展示从数据获取到可视化报告的完整流程
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# 导入量化因子系统
from quant_factor_system import (
    # 核心组件
    FactorSystem,
    FactorEvaluator,
    BacktestEngine,
    
    # 因子
    MomentumFactor,
    ValueFactor,
    QualityFactor,
    SizeFactor,
    
    # 数据源
    get_a_stock_data,
    MultiSourceDataManager,
    
    # 数据持久化
    DataRepository,
    AutoDataUpdater,
    
    # 自动化
    FactorAnalysisPipeline,
    create_default_pipeline,
    
    # 可视化
    FactorDashboard,
    ReportGenerator,
)


def generate_sample_data():
    """生成模拟股票数据"""
    print("📊 生成模拟数据...")
    
    np.random.seed(42)
    
    n_stocks = 100
    n_days = 252 * 2  # 2年
    
    dates = pd.date_range(start='2022-01-01', periods=n_days, freq='B')
    stocks = [f'STOCK_{i:03d}' for i in range(n_stocks)]
    
    all_data = {}
    
    for stock in stocks:
        trend = np.linspace(0.01, 0.02, n_days)
        noise = np.random.randn(n_days) * 0.015
        returns = trend + noise
        
        prices = 100 * np.cumprod(1 + returns)
        
        pe = np.random.uniform(8, 40, n_days)
        pb = np.random.uniform(0.5, 5, n_days)
        roe = np.random.uniform(0.05, 0.25, n_days)
        revenue = np.cumsum(np.random.randn(n_days) * 1e7 + 1e7)
        market_cap = prices * np.random.uniform(1e6, 1e7, n_days)
        volume = np.random.randint(1e6, 1e8, n_days)
        
        df = pd.DataFrame({
            'symbol': stock,
            'open': prices * (1 + np.random.randn(n_days) * 0.01),
            'high': prices * (1 + np.abs(np.random.randn(n_days)) * 0.02),
            'low': prices * (1 - np.abs(np.random.randn(n_days)) * 0.02),
            'close': prices,
            'volume': volume,
            'pe': pe,
            'pb': pb,
            'roe': roe,
            'revenue': revenue,
            'market_cap': market_cap,
        }, index=dates)
        
        all_data[stock] = df
    
    combined = pd.concat(all_data.values())
    print(f"  ✅ 生成 {len(combined)} 条数据，{n_stocks} 只股票")
    
    return combined


def demo_data_persistence():
    """演示数据持久化"""
    print("\n" + "="*60)
    print("💾 Demo 1: 数据持久化")
    print("="*60)
    
    # 创建数据仓库
    repo = DataRepository("./data/factor_data.db")
    
    # 生成数据
    data = generate_sample_data()
    
    # 保存价格数据
    print("\n📁 保存价格数据...")
    records = repo.save_price_data(data)
    print(f"  ✅ 保存 {records} 条价格记录")
    
    # 获取数据
    print("\n📖 读取数据...")
    prices = repo.get_price_data(['STOCK_001', 'STOCK_002'], '2022-01-01', '2024-01-01')
    print(f"  ✅ 读取 {len(prices)} 条记录")
    
    # 获取最新交易日期
    latest = repo.get_latest_trade_date()
    print(f"  📅 最新交易日期: {latest}")
    
    return repo


def demo_factor_calculation(repo):
    """演示因子计算"""
    print("\n" + "="*60)
    print("🔢 Demo 2: 因子计算")
    print("="*60)
    
    # 生成数据
    data = generate_sample_data()
    
    # 创建因子系统
    system = FactorSystem(name="Automated Factor System")
    
    system.add_factor(MomentumFactor(period=120), weight=1.0)
    system.add_factor(ValueFactor(metric='pe'), weight=1.0)
    system.add_factor(QualityFactor(metric='roe'), weight=1.0)
    system.add_factor(SizeFactor(), weight=0.5)
    
    # 计算因子
    print("\n🔬 计算因子...")
    factor_values = system.calculate_all(data)
    print(f"  ✅ 计算 {len(system.factors)} 个因子")
    print(f"     因子列表: {list(system.factors.keys())}")
    
    # 保存因子数据
    print("\n💾 保存因子数据...")
    
    # 按日期分组保存
    dates = data.index.get_level_values('date').unique()
    
    for date in dates[:5]:  # 只保存前5天作为示例
        date_str = date.strftime('%Y-%m-%d')
        day_data = data.xs(date, level='date')
        
        for symbol in day_data.index[:10]:  # 每只股票
            symbol_data = day_data.loc[symbol]
            factors = {
                'Momentum': factor_values.loc[symbol, 'Momentum'] if 'Momentum' in factor_values.columns else 0,
                'Value': factor_values.loc[symbol, 'Value'] if 'Value' in factor_values.columns else 0,
                'Quality': factor_values.loc[symbol, 'Quality'] if 'Quality' in factor_values.columns else 0,
                'Size': factor_values.loc[symbol, 'Size'] if 'Size' in factor_values.columns else 0,
            }
            repo.save_factor_data(symbol, date_str, factors)
    
    print(f"  ✅ 因子数据已保存")
    
    return system, factor_values


def demo_factor_evaluation(system, repo):
    """演示因子评估"""
    print("\n" + "="*60)
    print("📊 Demo 3: 因子评估")
    print("="*60)
    
    # 生成数据
    data = generate_sample_data()
    returns = data.groupby('symbol')['close'].pct_change().dropna()
    
    # 创建评估器
    evaluator = FactorEvaluator(system)
    
    # IC 分析
    print("\n📈 IC 分析...")
    ic_results = evaluator.evaluate_ic(returns)
    
    for name, ic in ic_results.items():
        print(f"  {name}: IC={ic['ic']:.4f}, IC_IR={ic['ic_ir']:.4f}, 胜率={ic['ic_sign_ratio']:.2%}")
        
        # 保存绩效数据
        repo.save_factor_performance({
            'factor_name': name,
            'calculation_date': datetime.now().strftime('%Y-%m-%d'),
            'ic': ic['ic'],
            'ic_ir': ic['ic_ir'],
            'ic_sign_ratio': ic['ic_sign_ratio'],
            'turnover': 0.15,
            'group_return_q1': 0.05,
            'group_return_q5': 0.12,
            'spread_return': 0.07,
            'sharpe_q1': 0.8,
            'sharpe_q5': 1.2
        })
    
    # 分组收益
    print("\n💰 分组收益...")
    group_returns = evaluator.evaluate_group_return(returns, groups=5)
    
    for name in group_returns.columns:
        spread = group_returns[name].iloc[-1] - group_returns[name].iloc[0]
        print(f"  {name}: 多空收益差 = {spread:.2%}")
    
    return ic_results


def demo_automation():
    """演示自动化调度"""
    print("\n" + "="*60)
    print("⚙️ Demo 4: 自动化调度")
    print("="*60)
    
    # 创建流水线
    pipeline = create_default_pipeline()
    
    # 查看状态
    status = pipeline.scheduler.get_status()
    print(f"\n📋 调度器状态:")
    print(f"  运行中: {status['is_running']}")
    print(f"  任务数: {status['num_tasks']}")
    print(f"  启用任务: {status['enabled_tasks']}")
    
    print(f"\n📅 任务调度:")
    for name, task in pipeline.scheduler.tasks.items():
        print(f"  - {name}: {task.schedule_time} ({'启用' if task.enabled else '禁用'})")
    
    # 手动运行完整流水线
    print("\n🚀 手动运行完整流水线...")
    results = pipeline.run_full_pipeline()
    
    for task_name, result in results.items():
        status = result.get('status', 'unknown')
        print(f"  {task_name}: {status}")
    
    return pipeline


def demo_visualization(ic_results):
    """演示可视化"""
    print("\n" + "="*60)
    print("📊 Demo 5: 可视化报告")
    print("="*60)
    
    # 创建仪表盘
    dashboard = FactorDashboard("./data/reports")
    
    # 添加数据
    for name, ic in ic_results.items():
        dashboard.add_factor_performance(name, {
            'ic': ic['ic'],
            'ic_ir': ic['ic_ir'],
            'ic_sign_ratio': ic['ic_sign_ratio'],
            'turnover': np.random.uniform(0.1, 0.2),
            'spread_return': np.random.uniform(0.05, 0.15)
        })
    
    # 添加相关性矩阵（模拟）
    if len(ic_results) > 1:
        corr = pd.DataFrame(
            np.random.randn(len(ic_results), len(ic_results)) * 0.3,
            index=list(ic_results.keys()),
            columns=list(ic_results.keys())
        )
        np.fill_diagonal(corr.values, 1.0)
        dashboard.add_factor_correlation(corr)
    
    # 生成报告
    print("\n📄 生成 HTML 报告...")
    report_path = dashboard.generate_html_report("量化因子分析报告")
    print(f"  ✅ 报告已生成: {report_path}")
    
    # 创建报告生成器
    generator = ReportGenerator()
    
    # 导出 JSON
    print("\n📦 导出 JSON 数据...")
    json_path = generator.export_json({
        'factor_results': {k: dict(v) for k, v in ic_results.items()},
        'generated_at': datetime.now().isoformat()
    })
    print(f"  ✅ JSON 已导出: {json_path}")
    
    return report_path


def demo_full_pipeline():
    """演示完整流水线"""
    print("\n" + "="*60)
    print("🚀 完整自动化流水线演示")
    print("="*60)
    
    # 1. 数据持久化
    repo = demo_data_persistence()
    
    # 2. 因子计算
    system, factor_values = demo_factor_calculation(repo)
    
    # 3. 因子评估
    ic_results = demo_factor_evaluation(system, repo)
    
    # 4. 自动化调度
    pipeline = demo_automation()
    
    # 5. 可视化
    report_path = demo_visualization(ic_results)
    
    # 完成
    print("\n" + "="*60)
    print("✅ 完整演示完成!")
    print("="*60)
    
    print("\n📂 生成的文件:")
    print("  - data/factor_data.db (SQLite 数据库)")
    print("  - data/reports/*.html (HTML 报告)")
    print("  - data/reports/*.json (JSON 数据)")
    
    print("\n💡 下一步:")
    print("  1. 安装依赖: pip install -r requirements.txt")
    print("  2. 运行每日调度: python -m quant_factor_system.automation")
    print("  3. 自定义因子: 继承 Factor 类")
    print("  4. 扩展通知: 添加邮件/微信通知")


if __name__ == "__main__":
    print("🧪 量化因子系统 - 完整自动化演示")
    print("="*60)
    
    # 运行完整演示
    demo_full_pipeline()
    
    print("\n" + "="*60)
    print("✨ 所有演示完成!")
    print("="*60)
