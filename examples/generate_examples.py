#!/usr/bin/env python3
"""
量化因子系统 - 经典场景示例

生成以下场景的图片:
1. 因子评估结果
2. IC 分析图
3. 分组收益图
4. 相关性热力图
5. Pipeline 结果
6. 风险指标图
7. Tearsheet 报告
8. Monte Carlo 模拟
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib import rcParams
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 设置样式
plt.style.use('seaborn-v0_8-whitegrid')

OUTPUT_DIR = "/Users/xinzhan/.openclaw/workspace/examples"


def setup_output_dir():
    """创建输出目录"""
    import os
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def create_sample_factor_data(n_days=500, n_stocks=100):
    """创建样本因子数据"""
    dates = pd.date_range('2023-01-01', periods=n_days, freq='B')
    symbols = [f'STOCK_{i:03d}' for i in range(n_stocks)]
    
    # MultiIndex
    index_tuples = []
    for date in dates:
        for symbol in symbols:
            index_tuples.append((date, symbol))
    
    multi_index = pd.MultiIndex.from_tuples(
        index_tuples, names=['date', 'symbol']
    )
    
    # 因子数据
    np.random.seed(42)
    momentum = pd.Series(np.random.randn(len(multi_index)) * 0.1, index=multi_index)
    rsi = pd.Series(np.random.uniform(30, 70, len(multi_index)), index=multi_index)
    pe = pd.Series(np.random.uniform(5, 30, len(multi_index)), index=multi_index)
    
    # 收益数据
    returns = pd.Series(np.random.randn(len(multi_index)) * 0.02, index=multi_index)
    
    return {
        'momentum': momentum,
        'rsi': rsi,
        'pe': pe,
        'returns': returns,
        'dates': dates,
        'symbols': symbols
    }


def create_sample_ic_data():
    """创建样本 IC 数据"""
    dates = pd.date_range('2023-01-01', periods=24, freq='M')
    
    # IC 序列
    ic_series = pd.Series(
        np.random.randn(24) * 0.03 + 0.02,
        index=dates,
        name='IC'
    )
    
    # IC 衰减
    lags = [1, 2, 3, 4, 5, 10, 20]
    ic_decay = pd.Series({
        f'lag_{lag}': 0.05 * (0.9 ** lag) + np.random.randn() * 0.01
        for lag in lags
    })
    
    return ic_series, ic_decay


def create_sample_group_returns():
    """创建样本分组收益"""
    groups = ['Q1', 'Q2', 'Q3', 'Q4', 'Q5']
    returns = [-0.02, -0.01, 0.00, 0.01, 0.03]
    
    # 带日期的数据
    dates = pd.date_range('2023-01-01', periods=100, freq='B')
    group_data = {}
    
    for group in groups:
        base_ret = returns[groups.index(group)]
        group_data[group] = base_ret + np.random.randn(100) * 0.01
    
    return pd.DataFrame(group_data, index=dates)


# ========== 场景 1: 因子评估结果 ==========

def plot_factor_evaluation():
    """场景1: 因子评估结果"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # IC 序列
    ic_series, _ = create_sample_ic_data()
    
    ax1 = axes[0, 0]
    ax1.plot(ic_series.index, ic_series.values, 'b-', linewidth=1.5)
    ax1.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax1.axhline(y=ic_series.mean(), color='red', linestyle='--', 
                label=f'Mean: {ic_series.mean():.4f}')
    ax1.set_title('场景1: IC 时间序列', fontsize=14, fontweight='bold')
    ax1.set_xlabel('日期')
    ax1.set_ylabel('IC')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 分组收益柱状图
    ax2 = axes[0, 1]
    groups = ['Q1', 'Q2', 'Q3', 'Q4', 'Q5']
    rets = [-0.02, -0.01, 0.00, 0.01, 0.03]
    colors = ['red' if r < 0 else 'green' for r in rets]
    bars = ax2.bar(groups, rets, color=colors, alpha=0.7, edgecolor='white')
    ax2.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax2.set_title('场景1: 分组收益', fontsize=14, fontweight='bold')
    ax2.set_xlabel('分位组')
    ax2.set_ylabel('平均收益')
    ax2.grid(True, alpha=0.3)
    
    # 添加数值标签
    for bar, ret in zip(bars, rets):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.002,
                f'{ret:.2%}', ha='center', fontsize=10)
    
    # 统计指标
    ax3 = axes[1, 0]
    ax3.axis('off')
    metrics_text = """
    📊 因子评估统计
    
    IC 均值: 0.0245
    IC IR: 0.82
    IC 胜率: 62.5%
    
    多空收益: 5.2%
    多空夏普: 1.45
    
    分组数: 5
    样本量: 50,000
    """
    ax3.text(0.1, 0.5, metrics_text, fontsize=14, verticalalignment='center',
            fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
    ax3.set_title('场景1: 评估指标', fontsize=14, fontweight='bold')
    
    # IC 分布
    ax4 = axes[1, 1]
    ax4.hist(ic_series.values, bins=15, color='steelblue', alpha=0.7, edgecolor='white')
    ax4.axvline(x=ic_series.mean(), color='red', linestyle='--', linewidth=2,
                label=f'Mean: {ic_series.mean():.4f}')
    ax4.set_title('场景1: IC 分布', fontsize=14, fontweight='bold')
    ax4.set_xlabel('IC')
    ax4.set_ylabel('频次')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


# ========== 场景 2: IC 相关性热力图 ==========

def plot_correlation_heatmap():
    """场景2: 因子相关性热力图"""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # 创建相关性矩阵
    factors = ['Momentum', 'RSI', 'PE', 'ROE', 'Size']
    
    # 模拟相关性
    corr_matrix = pd.DataFrame([
        [1.00, -0.15, 0.05, 0.20, -0.10],
        [-0.15, 1.00, -0.25, 0.10, 0.05],
        [0.05, -0.25, 1.00, 0.15, -0.05],
        [0.20, 0.10, 0.15, 1.00, 0.08],
        [-0.10, 0.05, -0.05, 0.08, 1.00]
    ], index=factors, columns=factors)
    
    # 热力图
    ax1 = axes[0]
    sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='RdBu_r',
                center=0, vmin=-1, vmax=1, ax=ax1,
                square=True, linewidths=0.5)
    ax1.set_title('场景2: 因子相关性热力图', fontsize=14, fontweight='bold')
    
    # IC 相关性
    ax2 = axes[1]
    ic_corr = pd.DataFrame([
        [1.00, -0.12, 0.08, 0.25],
        [-0.12, 1.00, -0.30, 0.15],
        [0.08, -0.30, 1.00, 0.20],
        [0.25, 0.15, 0.20, 1.00]
    ], index=factors[:4], columns=factors[:4])
    
    sns.heatmap(ic_corr, annot=True, fmt='.2f', cmap='RdBu_r',
                center=0, vmin=-1, vmax=1, ax=ax2,
                square=True, linewidths=0.5)
    ax2.set_title('场景2: IC 相关性热力图', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    return fig


# ========== 场景 3: Pipeline 结果 ==========

def plot_pipeline_results():
    """场景3: Pipeline 结果"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    dates = pd.date_range('2023-01-01', periods=100, freq='B')
    
    # 动量因子
    ax1 = axes[0, 0]
    momentum = np.cumsum(np.random.randn(100) * 0.01)
    ax1.plot(dates, momentum, 'b-', linewidth=1.5, label='Momentum')
    ax1.set_title('场景3: 动量因子', fontsize=14, fontweight='bold')
    ax1.set_xlabel('日期')
    ax1.set_ylabel('因子值')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # RSI 因子
    ax2 = axes[0, 1]
    rsi = 50 + np.cumsum(np.random.randn(100) * 2)
    rsi = np.clip(rsi, 30, 70)
    ax2.plot(dates, rsi, 'g-', linewidth=1.5, label='RSI')
    ax2.axhline(y=70, color='red', linestyle='--', alpha=0.5, label='Overbought')
    ax2.axhline(y=30, color='blue', linestyle='--', alpha=0.5, label='Oversold')
    ax2.set_title('场景3: RSI 因子', fontsize=14, fontweight='bold')
    ax2.set_xlabel('日期')
    ax2.set_ylabel('RSI')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 多因子组合
    ax3 = axes[1, 0]
    combo = momentum * 0.6 + (70 - rsi) * 0.4 / 10
    ax3.plot(dates, combo, 'purple', linewidth=1.5, label='组合信号')
    ax3.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax3.fill_between(dates, 0, combo, where=(combo > 0), 
                     color='green', alpha=0.3, label='做多')
    ax3.fill_between(dates, 0, combo, where=(combo <= 0), 
                     color='red', alpha=0.3, label='做空')
    ax3.set_title('场景3: 多因子组合', fontsize=14, fontweight='bold')
    ax3.set_xlabel('日期')
    ax3.set_ylabel('组合信号')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Pipeline 信息
    ax4 = axes[1, 1]
    ax4.axis('off')
    pipeline_info = """
    🔧 Pipeline 配置
    
    【因子】
    1. Momentum (window=20)
    2. RSI (window=14)
    3. MA (window=20)
    
    【变换】
    - rolling(60)
    - rank()
    - zscore()
    
    【过滤】
    - PercentileFilter (80-100)
    
    【输出】
    - 因子值
    - 分组标签
    - 过滤掩码
    """
    ax4.text(0.05, 0.5, pipeline_info, fontsize=12, verticalalignment='center',
            fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))
    ax4.set_title('场景3: Pipeline 配置', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    return fig


# ========== 场景 4: 风险指标 ==========

def plot_risk_metrics():
    """场景4: 风险指标"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    dates = pd.date_range('2023-01-01', periods=252, freq='B')
    
    # 累计收益曲线
    ax1 = axes[0, 0]
    returns = np.random.randn(252) * 0.02
    cum_returns = np.cumprod(1 + returns) - 1
    ax1.plot(dates, cum_returns * 100, 'b-', linewidth=1.5, label='组合')
    ax1.fill_between(dates, 0, cum_returns * 100, alpha=0.3)
    ax1.set_title('场景4: 累计收益曲线', fontsize=14, fontweight='bold')
    ax1.set_xlabel('日期')
    ax1.set_ylabel('累计收益 (%)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 回撤曲线
    ax2 = axes[0, 1]
    running_max = np.maximum.accumulate(cum_returns)
    drawdown = (cum_returns - running_max) * 100
    ax2.fill_between(dates, drawdown, 0, color='red', alpha=0.5)
    ax2.plot(dates, drawdown, 'r-', linewidth=1)
    ax2.set_title('场景4: 回撤曲线', fontsize=14, fontweight='bold')
    ax2.set_xlabel('日期')
    ax2.set_ylabel('回撤 (%)')
    ax2.grid(True, alpha=0.3)
    
    # 收益分布
    ax3 = axes[1, 0]
    ax3.hist(returns * 100, bins=30, color='steelblue', alpha=0.7, 
             edgecolor='white', density=True)
    # 正态分布拟合
    from scipy import stats
    x = np.linspace(-5, 5, 100)
    ax3.plot(x, stats.norm.pdf(x, 0, 1), 'r--', linewidth=2, label='正态分布')
    ax3.axvline(x=0, color='gray', linestyle='--', alpha=0.5)
    ax3.set_title('场景4: 日收益分布', fontsize=14, fontweight='bold')
    ax3.set_xlabel('日收益 (%)')
    ax3.set_ylabel('密度')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 风险指标
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    metrics = {
        '总收益': f'{cum_returns[-1]*100:.1f}%',
        '年化收益': f'{cum_returns[-1]*252/252*100:.1f}%',
        '年化波动率': f'{np.std(returns)*np.sqrt(252)*100:.1f}%',
        '最大回撤': f'{drawdown.min():.1f}%',
        '夏普比率': f'{np.mean(returns)/np.std(returns)*np.sqrt(252):.2f}',
        '索提诺比率': f'{np.mean(returns)/np.std(returns[returns<0])*np.sqrt(252):.2f}',
        'VaR (95%)': f'{np.percentile(returns, 5)*100:.2f}%',
        'CVaR (95%)': f'{np.mean(returns[returns<=np.percentile(returns, 5)])*100:.2f}%',
        '胜率': f'{(returns>0).mean()*100:.1f}%',
    }
    
    text = '📈 风险指标统计\n\n'
    for k, v in metrics.items():
        text += f'{k}: {v}\n'
    
    ax4.text(0.1, 0.5, text, fontsize=14, verticalalignment='center',
            fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
    ax4.set_title('场景4: 风险指标', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    return fig


# ========== 场景 5: Tearsheet 报告 ==========

def plot_tearsheet():
    """场景5: Tearsheet 报告"""
    fig = plt.figure(figsize=(16, 12))
    gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.3, wspace=0.3)
    
    dates = pd.date_range('2023-01-01', periods=12, freq='M')
    
    # 1. IC 序列
    ax1 = fig.add_subplot(gs[0, 0])
    ic = np.random.randn(12) * 0.03 + 0.02
    ax1.bar(range(12), ic, color=['green' if i > 0 else 'red' for i in ic], alpha=0.7)
    ax1.set_title('📊 IC 月度', fontsize=12, fontweight='bold')
    ax1.set_xlabel('月份')
    ax1.set_ylabel('IC')
    ax1.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax1.grid(True, alpha=0.3)
    
    # 2. 分组收益
    ax2 = fig.add_subplot(gs[0, 1])
    groups = ['Q1', 'Q2', 'Q3', 'Q4', 'Q5']
    rets = [-0.02, -0.01, 0.00, 0.01, 0.03]
    colors = ['red' if r < 0 else 'green' for r in rets]
    ax2.bar(groups, [r*100 for r in rets], color=colors, alpha=0.7)
    ax2.set_title('📈 分组收益 (%)', fontsize=12, fontweight='bold')
    ax2.set_xlabel('分位组')
    ax2.set_ylabel('收益 (%)')
    ax2.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax2.grid(True, alpha=0.3)
    
    # 3. 统计表格
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.axis('off')
    stats_text = """
    📋 因子统计
    
    IC 均值: 0.024
    IC IR: 0.85
    胜率: 65%
    
    多空收益: 5.2%
    多空夏普: 1.45
    """
    ax3.text(0.1, 0.5, stats_text, fontsize=11, verticalalignment='center',
            fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
    ax3.set_title('📊 统计', fontsize=12, fontweight='bold')
    
    # 4. 累计收益
    ax4 = fig.add_subplot(gs[1, :2])
    dates_daily = pd.date_range('2023-01-01', periods=100, freq='B')
    cum_ret = np.cumprod(1 + np.random.randn(100) * 0.02) - 1
    ax4.plot(dates_daily, cum_ret * 100, 'b-', linewidth=1.5, label='多空组合')
    ax4.fill_between(dates_daily, 0, cum_ret * 100, alpha=0.3)
    ax4.set_title('📈 累计收益曲线', fontsize=12, fontweight='bold')
    ax4.set_xlabel('日期')
    ax4.set_ylabel('累计收益 (%)')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    # 5. 相关性
    ax5 = fig.add_subplot(gs[1, 2])
    corr = pd.DataFrame([
        [1.00, -0.15, 0.05],
        [-0.15, 1.00, 0.10],
        [0.05, 0.10, 1.00]
    ], index=['Momentum', 'RSI', 'PE'],
       columns=['Momentum', 'RSI', 'PE'])
    sns.heatmap(corr, annot=True, fmt='.2f', cmap='RdBu_r',
                center=0, ax=ax5, square=True)
    ax5.set_title('🔗 因子相关', fontsize=12, fontweight='bold')
    
    # 6. 换手率
    ax6 = fig.add_subplot(gs[2, 0])
    turnover = [20 + np.random.randn() * 5 for _ in range(12)]
    ax6.bar(range(1, 13), turnover, color='orange', alpha=0.7)
    ax6.set_title('🔄 月度换手率 (%)', fontsize=12, fontweight='bold')
    ax6.set_xlabel('月份')
    ax6.set_ylabel('换手率 (%)')
    ax6.grid(True, alpha=0.3)
    
    # 7. 收益分布
    ax7 = fig.add_subplot(gs[2, 1])
    daily_ret = np.random.randn(252) * 0.02
    ax7.hist(daily_ret * 100, bins=30, color='steelblue', alpha=0.7, 
             edgecolor='white', density=True)
    ax7.axvline(x=0, color='red', linestyle='--', alpha=0.5)
    ax7.set_title('📉 收益分布', fontsize=12, fontweight='bold')
    ax7.set_xlabel('日收益 (%)')
    ax7.grid(True, alpha=0.3)
    
    # 8. 结论
    ax8 = fig.add_subplot(gs[2, 2])
    ax8.axis('off')
    conclusion = """
    ✅ 因子评估结论
    
    1. IC 显著为正
       预测能力稳定
    
    2. 分组收益单调
       Q5 > Q4 > ... > Q1
    
    3. 多空收益5.2%
       夏普比率1.45
    
    建议: ✓ 采用
    """
    ax8.text(0.05, 0.5, conclusion, fontsize=10, verticalalignment='center',
            fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
    ax8.set_title('📝 结论', fontsize=12, fontweight='bold')
    
    plt.suptitle('📊 因子 Tearsheet 报告', fontsize=16, fontweight='bold', y=1.02)
    
    return fig


# ========== 场景 6: Monte Carlo 模拟 ==========

def plot_monte_carlo():
    """场景6: Monte Carlo 模拟"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    n_sims = 100
    n_days = 252
    
    # 生成模拟路径
    np.random.seed(42)
    paths = np.zeros((n_sims, n_days))
    
    for i in range(n_sims):
        returns = np.random.randn(n_days) * 0.02
        paths[i] = np.cumprod(1 + returns) - 1
    
    dates = range(n_days)
    
    # 1. 模拟路径
    ax1 = axes[0, 0]
    for i in range(min(50, n_sims)):
        ax1.plot(dates, paths[i] * 100, alpha=0.1, color='blue')
    
    # 百分位
    p5 = np.percentile(paths, 5, axis=0) * 100
    p50 = np.percentile(paths, 50, axis=0) * 100
    p95 = np.percentile(paths, 95, axis=0) * 100
    
    ax1.fill_between(dates, p5, p95, alpha=0.2, color='blue', label='5-95%')
    ax1.plot(dates, p50, 'r-', linewidth=2, label='中位数')
    ax1.set_title('场景6: Monte Carlo 路径模拟', fontsize=14, fontweight='bold')
    ax1.set_xlabel('交易日')
    ax1.set_ylabel('累计收益 (%)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. 最终收益分布
    ax2 = axes[0, 1]
    final_returns = paths[:, -1] * 100
    ax2.hist(final_returns, bins=30, color='steelblue', alpha=0.7, 
             edgecolor='white', density=True)
    ax2.axvline(x=np.mean(final_returns), color='red', linestyle='--', 
                linewidth=2, label=f'Mean: {np.mean(final_returns):.1f}%')
    ax2.axvline(x=np.percentile(final_returns, 5), color='orange', 
                linestyle='--', label=f'5%: {np.percentile(final_returns, 5):.1f}%')
    ax2.axvline(x=np.percentile(final_returns, 95), color='green', 
                linestyle='--', label=f'95%: {np.percentile(final_returns, 95):.1f}%')
    ax2.set_title('场景6: 最终收益分布', fontsize=14, fontweight='bold')
    ax2.set_xlabel('最终收益 (%)')
    ax2.set_ylabel('密度')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. 统计信息
    ax3 = axes[1, 0]
    ax3.axis('off')
    
    bust_prob = (paths.min(axis=1) < -0.2).mean()
    goal_prob = (paths[:, -1] > 0.5).mean()
    
    stats_text = f"""
    🎲 Monte Carlo 模拟统计
    
    模拟次数: {n_sims}
    模拟天数: {n_days}
    
    📊 收益统计
    均值: {np.mean(final_returns):.1f}%
    标准差: {np.std(final_returns):.1f}%
    最小: {np.min(final_returns):.1f}%
    最大: {np.max(final_returns):.1f}%
    
    ⚠️ 风险统计
    破产概率 (亏损20%): {bust_prob*100:.1f}%
    目标达成概率 (盈利50%): {goal_prob*100:.1f}%
    
    📈 置信区间
    90%: [{np.percentile(final_returns, 5):.1f}%, {np.percentile(final_returns, 95):.1f}%]
    """
    ax3.text(0.05, 0.5, stats_text, fontsize=12, verticalalignment='center',
            fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))
    ax3.set_title('场景6: 模拟统计', fontsize=14, fontweight='bold')
    
    # 4. 概率分布
    ax4 = axes[1, 1]
    
    # 计算各阈值下的达成概率
    thresholds = np.arange(-0.5, 1.0, 0.1)
    achieve_probs = [(paths[:, -1] > t).mean() * 100 for t in thresholds]
    
    ax4.plot(thresholds * 100, achieve_probs, 'b-o', linewidth=2, markersize=5)
    ax4.axhline(y=50, color='gray', linestyle='--', alpha=0.5, label='50%')
    ax4.axvline(x=0, color='gray', linestyle='--', alpha=0.5)
    ax4.set_title('场景6: 目标达成概率', fontsize=14, fontweight='bold')
    ax4.set_xlabel('目标收益率 (%)')
    ax4.set_ylabel('达成概率 (%)')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    ax4.set_ylim(0, 105)
    
    plt.tight_layout()
    return fig


# ========== 主函数 ==========

def main():
    """生成所有场景图片"""
    print("=" * 60)
    print("生成量化因子系统 - 经典场景示例图片")
    print("=" * 60)
    
    setup_output_dir()
    
    scenarios = [
        ("场景1_因子评估结果.png", plot_factor_evaluation),
        ("场景2_相关性热力图.png", plot_correlation_heatmap),
        ("场景3_Pipeline结果.png", plot_pipeline_results),
        ("场景4_风险指标.png", plot_risk_metrics),
        ("场景5_Tearsheet报告.png", plot_tearsheet),
        ("场景6_MonteCarlo模拟.png", plot_monte_carlo),
    ]
    
    for filename, plot_func in scenarios:
        print(f"\n生成 {filename}...")
        try:
            fig = plot_func()
            filepath = f"{OUTPUT_DIR}/{filename}"
            fig.savefig(filepath, dpi=150, bbox_inches='tight', 
                      facecolor='white', edgecolor='none')
            plt.close(fig)
            print(f"✅ 已保存: {filepath}")
        except Exception as e:
            print(f"❌ 失败: {e}")
    
    print("\n" + "=" * 60)
    print(f"所有图片已保存到: {OUTPUT_DIR}")
    print("=" * 60)
    
    # 列出生成的文件
    import os
    files = sorted(os.listdir(OUTPUT_DIR))
    print("\n生成的文件:")
    for f in files:
        filepath = f"{OUTPUT_DIR}/{f}"
        size = os.path.getsize(filepath) / 1024
        print(f"  📄 {f} ({size:.1f} KB)")
    
    return OUTPUT_DIR


if __name__ == "__main__":
    main()
