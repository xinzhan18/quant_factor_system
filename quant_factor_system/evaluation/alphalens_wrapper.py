"""
Alphalens 集成模块
Alphalens Integration Module

功能：
- 数据格式转换（我们的格式 → Alphalens 格式）
- 生成专业 Tear Sheet
- 高级统计分析
- 保留原有架构
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import warnings
warnings.filterwarnings('ignore')

# 检查 Alphalens 是否安装
try:
    import alphalens
    import alphalens.performance as perf
    import alphalens.plotting as plotting
    import alphalens.utils as utils
    HAS_ALPHALENS = True
except ImportError:
    HAS_ALPHALENS = False
    print("⚠️ Alphalens 未安装，请运行: pip install alphalens")


class AlphalensWrapper:
    """
    Alphalens 包装器
    用于将我们的因子数据转换为 Alphalens 格式
    """
    
    def __init__(self, factor_data: pd.DataFrame = None, 
                 prices: pd.DataFrame = None):
        """
        初始化
        
        Args:
            factor_data: 因子值 DataFrame (index=date, columns=asset)
            prices: 价格 DataFrame (index=date, columns=asset)
        """
        self.factor_data = factor_data
        self.prices = prices
        self.alphalens_data = None
    
    @staticmethod
    def from_quant_system(factor_values: pd.DataFrame,
                         price_data: pd.DataFrame) -> 'AlphalensWrapper':
        """
        从我们的量化系统数据创建包装器
        
        Args:
            factor_values: 因子值（来自 FactorSystem.calculate_all）
            price_data: 价格数据
            
        Returns:
            AlphalensWrapper 实例
        """
        wrapper = AlphalensWrapper()
        
        # 转换为 Alphalens 格式
        # Alphalens 需要: MultiIndex (date, asset)
        
        if isinstance(factor_values, pd.DataFrame):
            # 如果是宽表格式，转换为长格式
            factor_long = factor_values.stack()
            factor_long.name = 'factor'
        else:
            factor_long = factor_values
        
        if isinstance(price_data, pd.DataFrame):
            # 价格转为长格式
            price_long = price_data.stack()
            price_long.name = 'price'
        else:
            price_long = price_data
        
        wrapper.factor_data = pd.DataFrame({'factor': factor_long})
        wrapper.prices = pd.DataFrame({'price': price_long})
        
        return wrapper
    
    def to_alphalens_format(self, 
                           periods: Tuple[int, ...] = (1, 5, 10)) -> pd.DataFrame:
        """
        转换为 Alphalens 格式
        
        Alphalens 需要的格式:
        MultiIndex DataFrame with levels [date, asset]
        Columns: [factor, forward_returns_1, forward_returns_5, ...]
        """
        if not HAS_ALPHALENS:
            print("⚠️ Alphalens 未安装")
            return None
        
        # 构建 Alphalens 数据
        # 因子数据应该已经是正确的格式
        
        self.alphalens_data = utils.get_clean_factor_and_forward_returns(
            factor=self.factor_data['factor'],
            prices=self.prices['price'] if 'price' in self.prices.columns else self.prices.iloc[:, 0],
            periods=periods,
            filter_zeros=True,
            # 常用参数
            max_loss=0.99  # 允许最多99%的数据丢失
        )
        
        return self.alphalens_data
    
    def create_returns_tear_sheet(self, 
                                 demeaned: bool = True,
                                 groupby: str = None,
                                 by_group: bool = False,
                                 plot_window: int = 10) -> Dict[str, Any]:
        """
        创建收益 Tear Sheet
        
        包含:
        - 累积收益曲线
        - 分组收益柱状图
        - 多空收益曲线
        """
        if not HAS_ALPHALENS or self.alphalens_data is None:
            print("⚠️ 请先调用 to_alphalens_format()")
            return {}
        
        try:
            # 这里我们会返回一个分析结果字典
            # 实际的图表生成需要 Jupyter 环境
            
            result = {
                'mean_return_by_q': perf.mean_return_by_q(self.alphalens_data, demeaned=demeaned),
                'mean_return_by_factor': perf.mean_return_by_factor(self.alphalens_data),
                'ic': perf.factor_information_coefficient(self.alphalens_data),
            }
            
            print("\n📊 Alphalens 收益分析结果:")
            print("="*60)
            
            # 平均收益 by 分组
            mean_ret = result['mean_return_by_q']
            print("\n📈 分组平均收益:")
            print(mean_ret.round(4))
            
            # IC 统计
            ic = result['ic']
            print("\n📉 IC 统计:")
            print(f"  IC 均值: {ic.mean():.4f}")
            print(f"  IC 标准差: {ic.std():.4f}")
            print(f"  IC 胜率: {(ic > 0).mean():.2%}")
            
            return result
            
        except Exception as e:
            print(f"❌ 分析失败: {e}")
            return {}
    
    def create_information_tear_sheet(self, group_adjust: bool = True,
                                      demeaned: bool = True) -> Dict[str, Any]:
        """
        创建信息系数 Tear Sheet
        
        包含:
        - IC 时序图
        - IC 分布直方图
        - IC 衰减分析
        """
        if not HAS_ALPHALENS or self.alphalens_data is None:
            return {}
        
        try:
            result = {
                'ic': perf.factor_information_coefficient(
                    self.alphalens_data, 
                    group_adjust=group_adjust,
                    demeaned=demeaned
                ),
                'ic_rank': perf.factor_rank_information_coefficient(
                    self.alphalens_data
                )
            }
            
            print("\n📊 IC 分析结果:")
            print("="*60)
            
            # IC 统计
            ic = result['ic']
            print(f"\n📈 IC 统计:")
            print(f"  均值: {ic.mean():.4f}")
            print(f"  标准差: {ic.std():.4f}")
            print(f"  胜率: {(ic > 0).mean():.2%}")
            
            # IC 衰减
            ic_by_period = self.alphalens_data.groupby(level='factor_quantile')[
                ['1D', '5D', '10D']
            ].apply(
                lambda x: perf.factor_information_coefficient(x)
            )
            
            print("\n📉 IC 衰减 (按分位数):")
            print(ic_by_period.round(4))
            
            return result
            
        except Exception as e:
            print(f"❌ IC 分析失败: {e}")
            return {}
    
    def create_turnover_tear_sheet(self) -> Dict[str, Any]:
        """
        创建换手率 Tear Sheet
        
        包含:
        - 分组换手率
        - 因子自相关
        """
        if not HAS_ALPHALENS or self.alphalens_data is None:
            return {}
        
        try:
            from alphalens.performance import factor_rank_autocorrelation
            
            result = {
                'turnover': perf.factor_turnover(self.alphalens_data, factor_quantile=5),
                'autocorr': factor_rank_autocorrelation(self.alphalens_data)
            }
            
            print("\n📊 换手率分析:")
            print("="*60)
            print(f"\n平均换手率: {result['turnover'].mean():.4f}")
            print(f"因子自相关: {result['autocorr'].mean():.4f}")
            
            return result
            
        except Exception as e:
            print(f"❌ 换手率分析失败: {e}")
            return {}


def create_tearsheet_report(factor_data: pd.DataFrame,
                           price_data: pd.DataFrame,
                           output_path: str = None) -> Dict[str, Any]:
    """
    创建完整的 Tear Sheet 报告
    
    Args:
        factor_data: 因子数据
        price_data: 价格数据
        output_path: 输出路径
        
    Returns:
        分析结果字典
    """
    # 创建包装器
    wrapper = AlphalensWrapper.from_quant_system(factor_data, price_data)
    
    # 转换为 Alphalens 格式
    wrapper.to_alphalens_format()
    
    # 运行分析
    results = {
        'returns': wrapper.create_returns_Tear_sheet(),
        'information': wrapper.create_information_Tear_sheet(),
        'turnover': wrapper.create_turnover_tear_sheet()
    }
    
    return results


# ========== 高级统计分析 ==========


def calculate_ic_stats(ic_series: pd.Series) -> Dict[str, float]:
    """
    计算 IC 统计指标
    
    包含:
    - 均值、标准差
    - t-statistic, p-value
    - 置信区间
    """
    from scipy import stats
    
    ic = ic_series.dropna()
    
    n = len(ic)
    mean = ic.mean()
    std = ic.std()
    
    # t-statistic
    t_stat = mean / (std / np.sqrt(n))
    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df=n-1))
    
    # 95% 置信区间
    ci = stats.t.interval(0.95, df=n-1, loc=mean, scale=std/np.sqrt(n))
    
    return {
        'ic_mean': mean,
        'ic_std': std,
        'ic_median': ic.median(),
        'ic_count': n,
        'ic_positive_ratio': (ic > 0).mean(),
        't_statistic': t_stat,
        'p_value': p_value,
        'ci_95_lower': ci[0],
        'ci_95_upper': ci[1]
    }


def calculate_ic_decay(ic_series: pd.Series, 
                      lags: List[int] = None) -> pd.Series:
    """
    计算 IC 衰减
    """
    if lags is None:
        lags = [1, 2, 3, 4, 5, 10, 20, 60]
    
    decay = {}
    
    for lag in lags:
        # IC(t) 与 IC(t-lag) 的自相关
        if lag < len(ic_series):
            decay[f'lag_{lag}'] = ic_series.autocorr(lag=lag)
        else:
            decay[f'lag_{lag}'] = np.nan
    
    return pd.Series(decay)


def calculate_group_returns(group_returns: pd.DataFrame) -> Dict[str, Any]:
    """
    计算分组收益统计
    
    Returns:
        统计字典
    """
    results = {}
    
    for col in group_returns.columns:
        rets = group_returns[col]
        
        results[col] = {
            'mean': rets.mean(),
            'std': rets.std(),
            'sharpe': rets.mean() / (rets.std() + 1e-8) * np.sqrt(252),
            'min': rets.min(),
            'max': rets.max(),
            'skew': rets.skew(),
            'kurtosis': rets.kurtosis()
        }
    
    # 多空组合
    if 'Q5' in results and 'Q1' in results:
        ls_ret = group_returns['Q5'] - group_returns['Q1']
        results['long_short'] = {
            'mean': ls_ret.mean(),
            'std': ls_ret.std(),
            'sharpe': ls_ret.mean() / (ls_ret.std() + 1e-8) * np.sqrt(252),
            'win_rate': (ls_ret > 0).mean()
        }
    
    return results


# ========== 可视化工具 ==========


def plot_ic_analysis(ic_series: pd.Series, 
                     save_path: str = None):
    """
    绘制 IC 分析图
    """
    try:
        import matplotlib.pyplot as plt
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # IC 时序图
        ax1 = axes[0, 0]
        ic_series.plot(ax=ax1)
        ax1.axhline(y=0, color='r', linestyle='--')
        ax1.axhline(y=ic_series.mean(), color='g', linestyle='--')
        ax1.set_title('IC Time Series')
        ax1.set_ylabel('IC')
        ax1.grid(True, alpha=0.3)
        
        # IC 分布
        ax2 = axes[0, 1]
        ic_series.hist(ax=ax2, bins=50)
        ax2.axvline(x=0, color='r', linestyle='--')
        ax2.axvline(x=ic_series.mean(), color='g', linestyle='--')
        ax2.set_title('IC Distribution')
        ax2.set_xlabel('IC')
        
        # IC 累积和
        ax3 = axes[1, 0]
        ic_series.cumsum().plot(ax=ax3)
        ax3.axhline(y=0, color='r', linestyle='--')
        ax3.set_title('IC Cumulative Sum')
        ax3.set_ylabel('Cumulative IC')
        
        # IC 衰减
        ic_decay = calculate_ic_decay(ic_series)
        ax4 = axes[1, 1]
        ic_decay.plot(kind='bar', ax=ax4)
        ax4.set_title('IC Decay')
        ax4.set_ylabel('Autocorrelation')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        return fig
        
    except Exception as e:
        print(f"❌ 绘图失败: {e}")
        return None


def plot_group_returns(group_returns: pd.DataFrame,
                      save_path: str = None):
    """
    绘制分组收益图
    """
    try:
        import matplotlib.pyplot as plt
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # 累积收益
        ax1 = axes[0, 0]
        (1 + group_returns).cumprod().plot(ax=ax1)
        ax1.set_title('Cumulative Returns by Group')
        ax1.set_ylabel('Cumulative Return')
        ax1.legend(title='Group')
        
        # 分组收益柱状图
        ax2 = axes[0, 1]
        mean_rets = group_returns.mean()
        mean_rets.plot(kind='bar', ax=ax2)
        ax2.set_title('Mean Return by Group')
        ax2.set_xlabel('Group')
        ax2.set_ylabel('Mean Return')
        
        # 多空收益
        ax3 = axes[1, 0]
        if 'Q5' in group_returns.columns and 'Q1' in group_returns.columns:
            ls = group_returns['Q5'] - group_returns['Q1']
            (1 + ls).cumprod().plot(ax=ax3)
            ax3.axhline(y=1, color='r', linestyle='--')
            ax3.set_title('Long-Short Return (Q5-Q1)')
        
        # 换手率
        ax4 = axes[1, 1]
        turnover = group_returns.std()  # 用标准差近似换手率
        turnover.plot(kind='bar', ax=ax4)
        ax4.set_title('Return Dispersion by Group')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        return fig
        
    except Exception as e:
        print(f"❌ 绘图失败: {e}")
        return None


# ========== 完整报告生成 ==========


def generate_factor_report(factor_data: pd.DataFrame,
                          price_data: pd.DataFrame,
                          report_title: str = "因子分析报告",
                          output_dir: str = "./reports") -> Dict[str, Any]:
    """
    生成完整的因子分析报告
    
    Args:
        factor_data: 因子数据
        price_data: 价格数据
        report_title: 报告标题
        output_dir: 输出目录
        
    Returns:
        报告结果字典
    """
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    results = {
        'report_title': report_title,
        'generated_at': str(pd.Timestamp.now()),
        'statistics': {},
        'ic_analysis': {},
        'returns_analysis': {}
    }
    
    # 1. 转换为 Alphalens 格式
    wrapper = AlphalensWrapper.from_quant_system(factor_data, price_data)
    alphalens_data = wrapper.to_alphalens_format()
    
    if alphalens_data is not None:
        # 2. IC 分析
        ic = perf.factor_information_coefficient(alphalens_data)
        ic_stats = calculate_ic_stats(ic)
        results['ic_analysis'] = {
            'statistics': ic_stats,
            'decay': calculate_ic_decay(ic).to_dict()
        }
        
        # 3. 分组收益分析
        mean_ret = perf.mean_return_by_q(alphalens_data)
        group_rets = calculate_group_returns(mean_ret)
        results['returns_analysis'] = group_rets
        
        # 4. 绘图
        try:
            plot_ic_analysis(ic, f"{output_dir}/ic_analysis.png")
            plot_group_returns(mean_ret, f"{output_dir}/group_returns.png")
        except:
            pass
        
        # 5. 生成 HTML 报告
        html_report = generate_html_report(results, report_title)
        with open(f"{output_dir}/factor_report.html", 'w') as f:
            f.write(html_report)
        
        results['output_files'] = {
            'ic_analysis': f"{output_dir}/ic_analysis.png",
            'group_returns': f"{output_dir}/group_returns.png",
            'html_report': f"{output_dir}/factor_report.html"
        }
    
    return results


def generate_html_report(results: Dict[str, Any],
                       title: str = "因子分析报告") -> str:
    """
    生成 HTML 报告
    """
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; border-bottom: 2px solid #4CAF50; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        .metric {{ font-size: 24px; color: #4CAF50; }}
        .success {{ color: green; }}
        .warning {{ color: orange; }}
        .danger {{ color: red; }}
    </style>
</head>
<body>
    <h1>📊 {title}</h1>
    <p>生成时间: {results.get('generated_at', '')}</p>
    
    <h2>📈 IC 分析</h2>
    <table>
        <tr><th>指标</th><th>值</th></tr>
"""
    
    # IC 统计
    ic_stats = results.get('ic_analysis', {}).get('statistics', {})
    for key, value in ic_stats.items():
        if isinstance(value, float):
            if 'ratio' in key or 'mean' in key or 'p_value' in key:
                html += f"<tr><td>{key}</td><td>{value:.4f}</td></tr>\n"
            else:
                html += f"<tr><td>{key}</td><td>{value:.6f}</td></tr>\n"
    
    html += """
    </table>
    
    <h2>💰 分组收益</h2>
    <table>
        <tr><th>分组</th><th>平均收益</th><th>夏普</th></tr>
"""
    
    for group, stats in results.get('returns_analysis', {}).items():
        if isinstance(stats, dict):
            html += f"<tr><td>{group}</td><td>{stats.get('mean', 0):.4f}</td><td>{stats.get('sharpe', 0):.4f}</td></tr>\n"
    
    html += """
    </table>
    
    <h2>📉 输出文件</h2>
    <ul>
        <li>IC 分析图</li>
        <li>分组收益图</li>
        <li>HTML 报告</li>
    </ul>
</body>
</html>
"""
    
    return html


if __name__ == "__main__":
    print("🧪 测试 Alphalens 集成模块...")
    
    if not HAS_ALPHALENS:
        print("⚠️ Alphalens 未安装")
        print("💡 安装: pip install alphalens")
    else:
        print("✅ Alphalens 已安装")
        
        # 创建测试数据
        np.random.seed(42)
        dates = pd.date_range('2020-01-01', periods=500, freq='B')
        n = len(dates)
        
        # 因子数据
        factor = pd.DataFrame(
            np.random.randn(n, 10),
            index=dates,
            columns=[f'ASSET_{i}' for i in range(10)]
        )
        
        # 价格数据
        prices = pd.DataFrame(
            100 * np.cumprod(1 + np.random.randn(n, 10) * 0.02, axis=0),
            index=dates,
            columns=[f'ASSET_{i}' for i in range(10)]
        )
        
        # 创建报告
        print("\n📊 生成因子分析报告...")
        results = generate_factor_report(factor, prices)
        
        print("\n✅ 报告生成完成!")
        print(f"IC 均值: {results.get('ic_analysis', {}).get('statistics', {}).get('ic_mean', 'N/A')}")
