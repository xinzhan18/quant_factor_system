"""
因子表现可视化示例
生成因子分析图表
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 非GUI后端

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'PingFang SC']
plt.rcParams['axes.unicode_minus'] = False

# ============ 模拟数据生成 ============

def create_sample_data():
    """创建模拟股票数据"""
    np.random.seed(42)
    
    n_stocks = 100
    n_days = 252 * 2  # 2年数据
    
    dates = pd.date_range(start='2022-01-01', periods=n_days, freq='B')
    stocks = [f'STOCK_{i:03d}' for i in range(n_stocks)]
    
    all_data = {}
    
    for stock in stocks:
        # 模拟价格走势
        trend = np.linspace(0.02, 0.03, n_days)
        noise = np.random.randn(n_days) * 0.02
        returns = trend + noise
        
        # 添加股票效应
        if stock in stocks[:20]:
            returns += 0.0003  # 动量效应
        if stock in stocks[80:]:
            returns -= 0.0002
            
        prices = 100 * np.cumprod(1 + returns)
        
        # 财务数据
        pe = np.random.uniform(8, 40, n_days)
        pb = np.random.uniform(0.5, 5, n_days)
        roe = np.random.uniform(0.05, 0.25, n_days)
        
        df = pd.DataFrame({
            'symbol': stock,
            'close': prices,
            'pe': pe,
            'pb': pb,
            'roe': roe,
            'volume': np.random.randint(1e6, 1e8, n_days),
        }, index=dates)
        
        all_data[stock] = df
    
    return pd.concat(all_data.values()), dates, stocks


def calculate_factors(data, stocks, dates):
    """计算因子值"""
    
    # 1. 动量因子 (Momentum)
    momentum = {}
    for stock in stocks:
        stock_data = data[data['symbol'] == stock]['close']
        returns_20d = stock_data.pct_change(20)
        momentum[stock] = returns_20d
    
    # 2. 价值因子 (PE倒数)
    value = {}
    for stock in stocks:
        pe_series = data[data['symbol'] == stock]['pe']
        value[stock] = 1 / pe_series
    
    # 3. 质量因子 (ROE)
    quality = {}
    for stock in stocks:
        roe_series = data[data['symbol'] == stock]['roe']
        quality[stock] = roe_series
    
    # 4. 波动率因子
    volatility = {}
    for stock in stocks:
        stock_data = data[data['symbol'] == stock]['close']
        vol_20d = stock_data.pct_change().rolling(20).std()
        volatility[stock] = vol_20d
    
    return momentum, value, quality, volatility


def calculate_returns_series(data, stocks):
    """计算收益率序列"""
    returns_dict = {}
    for stock in stocks:
        stock_data = data[data['symbol'] == stock]['close']
        returns_dict[stock] = stock_data.pct_change()
    
    returns = pd.DataFrame(returns_dict).dropna()
    return returns


# ============ 因子评估 ============

def evaluate_factor_ic(factor_dict, returns):
    """计算IC (Information Coefficient)"""
    ic_series = []
    dates = []
    
    # 获取所有股票在所有日期的因子值
    all_dates = None
    for stock, f_vals in factor_dict.items():
        if all_dates is None:
            all_dates = f_vals.dropna().index
        else:
            all_dates = all_dates.intersection(f_vals.dropna().index)
    
    for date in all_dates:
        if date in returns.index:
            f_vals = pd.Series({stock: factor_dict[stock].loc[date] for stock in factor_dict if date in factor_dict[stock].index})
            r_vals = returns.loc[date].dropna()
            
            # 找到共同的股票
            common = f_vals.index.intersection(r_vals.index)
            if len(common) > 10:
                ic = np.corrcoef(f_vals[common], r_vals[common])[0, 1]
                ic_series.append(ic)
                dates.append(date)
    
    return pd.Series(ic_series, index=dates)


def group_backtest(factor_dict, returns, n_groups=5):
    """分组回测"""
    cumulative_returns = {}
    
    # 获取所有日期
    all_dates = None
    for stock, f_vals in factor_dict.items():
        if all_dates is None:
            all_dates = f_vals.dropna().index
        else:
            all_dates = all_dates.intersection(f_vals.dropna().index)
    
    for date in all_dates:
        if date in returns.index:
            f_vals = pd.Series({stock: factor_dict[stock].loc[date] for stock in factor_dict if date in factor_dict[stock].index})
            r_vals = returns.loc[date].dropna()
            
            common = f_vals.index.intersection(r_vals.index)
            if len(common) > 20:
                # 分组
                try:
                    quantiles = pd.qcut(f_vals[common], n_groups, labels=[f'Q{i+1}' for i in range(n_groups)], duplicates='drop')
                except:
                    continue
                
                group_rets = {}
                for group in quantiles.unique():
                    stocks_in_group = quantiles[quantiles == group].index
                    group_rets[group] = r_vals[stocks_in_group].mean()
                
                if not cumulative_returns:
                    for g in group_rets:
                        cumulative_returns[g] = [group_rets[g]]
                else:
                    for g in group_rets:
                        if g in cumulative_returns:
                            cumulative_returns[g].append(cumulative_returns[g][-1] * (1 + group_rets[g]))
    
    return pd.DataFrame(cumulative_returns)


# ============ 主程序 ============

def main():
    print("📊 生成因子表现分析图...")
    
    # 1. 创建数据
    print("  📈 创建模拟数据...")
    data, dates, stocks = create_sample_data()
    print(f"     {len(stocks)} 只股票, {len(dates)} 个交易日")
    
    # 2. 计算因子
    print("  🔢 计算因子...")
    momentum, value, quality, volatility = calculate_factors(data, stocks, dates)
    
    # 3. 计算收益率
    print("  💰 计算收益率...")
    returns = calculate_returns_series(data, stocks)
    
    # 4. 评估因子
    print("  📊 评估因子...")
    ic_momentum = evaluate_factor_ic(momentum, returns)
    ic_value = evaluate_factor_ic(value, returns)
    ic_quality = evaluate_factor_ic(quality, returns)
    
    # 5. 分组回测
    print("  🎯 分组回测...")
    group_momentum = group_backtest(momentum, returns)
    group_value = group_backtest(value, returns)
    
    # ============ 绘图 ============
    
    fig = plt.figure(figsize=(16, 12))
    
    # 1. IC时序图
    ax1 = fig.add_subplot(2, 2, 1)
    ic_df = pd.DataFrame({
        'Momentum': ic_momentum,
        'Value': ic_value,
        'Quality': ic_quality
    })
    ic_df.rolling(20).mean().plot(ax=ax1, linewidth=2)
    ax1.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    ax1.set_title('IC Time Series (20-day Rolling Average)', fontsize=14)
    ax1.set_xlabel('Date')
    ax1.set_ylabel('IC')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. IC分布图
    ax2 = fig.add_subplot(2, 2, 2)
    ic_df.plot(kind='box', ax=ax2)
    ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    ax2.set_title('IC Distribution', fontsize=14)
    ax2.set_ylabel('IC')
    ax2.grid(True, alpha=0.3)
    
    # 3. 分组收益曲线 (Momentum)
    ax3 = fig.add_subplot(2, 2, 3)
    group_momentum.plot(ax=ax3, linewidth=2)
    ax3.set_title('Momentum Factor: Group Returns (Q1=Low, Q5=High)', fontsize=14)
    ax3.set_xlabel('Date')
    ax3.set_ylabel('Cumulative Return')
    ax3.legend(title='Quantile')
    ax3.grid(True, alpha=0.3)
    
    # 4. 多空收益差
    ax4 = fig.add_subplot(2, 2, 4)
    long_short = group_momentum['Q5'] - group_momentum['Q1']
    long_short.plot(ax=ax4, linewidth=2, color='green')
    ax4.fill_between(long_short.index, 0, long_short.values, alpha=0.3, color='green')
    ax4.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    ax4.set_title('Long-Short Portfolio Return (Q5 - Q1)', fontsize=14)
    ax4.set_xlabel('Date')
    ax4.set_ylabel('Return')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # 保存图片
    output_path = '/Users/xinzhan/.openclaw/workspace/factor_performance.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"  ✅ 图表已保存到: {output_path}")
    
    # 打印统计信息
    print("\n📋 因子统计:")
    print(f"  Momentum IC: {ic_momentum.mean():.4f} (IR: {ic_momentum.mean()/ic_momentum.std():.4f})")
    print(f"  Value IC: {ic_value.mean():.4f} (IR: {ic_value.mean()/ic_value.std():.4f})")
    print(f"  Quality IC: {ic_quality.mean():.4f} (IR: {ic_quality.mean()/ic_quality.std():.4f})")
    
    print(f"\n  Momentum 多空收益: {group_momentum['Q5'].iloc[-1] - group_momentum['Q1'].iloc[-1]:.2%}")
    
    return output_path


if __name__ == "__main__":
    main()
