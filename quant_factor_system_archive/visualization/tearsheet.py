"""
Tearsheet 报告模块
基于 Alphalens tears.py 设计

功能:
- GridFigure 网格布局
- IC 分析报告
- 分组收益报告
- 换手率分析报告
- HTML 导出
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import io
import base64


@dataclass
class TearSheetConfig:
    """Tearsheet 配置"""
    title: str = "Factor Analysis Report"
    figsize: tuple = (14, 10)
    pagesize: str = 'A4'
    dpi: int = 150
    transparent: bool = False


class GridFigure:
    """
    网格图表布局系统
    
    使用 gridspec 实现复杂布局:
    - next_row(): 跨整行
    - next_cell(): 单个单元格
    """
    
    def __init__(self, rows: int, cols: int, figsize: tuple = (14, 10)):
        self.rows = rows
        self.cols = cols
        self.figsize = figsize
        
        self.fig = plt.figure(figsize=figsize)
        self.gs = gridspec.GridSpec(rows, cols, 
                                   wspace=0.4, hspace=0.3)
        self.curr_row = 0
        self.curr_col = 0
    
    def next_row(self):
        """跨整行"""
        if self.curr_col != 0:
            self.curr_row += 1
            self.curr_col = 0
        
        subplt = plt.subplot(self.gs[self.curr_row, :])
        self.curr_row += 1
        return subplt
    
    def next_cell(self):
        """单个单元格"""
        if self.curr_col >= self.cols:
            self.curr_row += 1
            self.curr_col = 0
        
        subplt = plt.subplot(self.gs[self.curr_row, self.curr_col])
        self.curr_col += 1
        return subplt
    
    def close(self):
        """关闭图表"""
        plt.close(self.fig)
        self.fig = None
        self.gs = None


class TearsheetBuilder:
    """
    Tearsheet 报告生成器
    
    标准报告结构:
    ┌────────────────────────────────────┐
    │ 1. 因子统计表                      │
    ├────────────────────────────────────┤
    │ 2. IC 分析图                        │
    ├────────────────────────────────────┤
    │ 3. 分组收益图                       │
    ├────────────────────────────────────┤
    │ 4. 换手率分析                       │
    └────────────────────────────────────┘
    """
    
    def __init__(self, config: TearSheetConfig = None):
        """
        初始化
        
        Args:
            config: 配置
        """
        self.config = config or TearSheetConfig()
        self.sections = []
    
    def add_factor_stats(self, 
                        ic: float,
                        ic_ir: float,
                        ic_win_rate: float,
                        group_returns: Dict[str, float]):
        """
        添加因子统计
        
        Args:
            ic: IC 均值
            ic_ir: IC IR
            ic_win_rate: IC 胜率
            group_returns: 分组收益字典
        """
        self.sections.append({
            'type': 'stats',
            'data': {
                'ic': ic,
                'ic_ir': ic_ir,
                'ic_win_rate': ic_win_rate,
                'group_returns': group_returns
            }
        })
    
    def add_ic_series(self, ic_series: pd.Series):
        """添加 IC 序列"""
        self.sections.append({
            'type': 'ic_series',
            'data': ic_series
        })
    
    def add_ic_decay(self, ic_decay: pd.Series):
        """添加 IC 衰减"""
        self.sections.append({
            'type': 'ic_decay',
            'data': ic_decay
        })
    
    def add_group_returns(self, group_returns: pd.DataFrame):
        """添加分组收益"""
        self.sections.append({
            'type': 'group_returns',
            'data': group_returns
        })
    
    def add_turnover(self, turnover: Dict[str, float]):
        """添加换手率"""
        self.sections.append({
            'type': 'turnover',
            'data': turnover
        })
    
    def render(self, return_fig: bool = False):
        """
        渲染报告
        
        Args:
            return_fig: 是否返回 figure 对象
            
        Returns:
            figure 或 None
        """
        # 计算需要的行数
        rows = 1  # 标题
        for section in self.sections:
            if section['type'] == 'ic_series':
                rows += 2
            elif section['type'] == 'group_returns':
                rows += 2
            elif section['type'] == 'ic_decay':
                rows += 1
            else:
                rows += 1
        
        # 创建 GridFigure
        gf = GridFigure(rows=rows, cols=1, figsize=self.config.figsize)
        
        # 1. 标题
        plt.suptitle(self.config.title, fontsize=16, fontweight='bold')
        
        # 2. 渲染各部分
        for section in self.sections:
            if section['type'] == 'stats':
                self._plot_stats(gf, section['data'])
            elif section['type'] == 'ic_series':
                self._plot_ic_series(gf, section['data'])
            elif section['type'] == 'ic_decay':
                self._plot_ic_decay(gf, section['data'])
            elif section['type'] == 'group_returns':
                self._plot_group_returns(gf, section['data'])
        
        plt.tight_layout()
        
        if return_fig:
            return gf.fig
        else:
            plt.show()
            gf.close()
    
    def _plot_stats(self, gf: GridFigure, data: Dict):
        """绘制统计表"""
        ax = gf.next_row()
        ax.axis('off')
        
        # 创建表格
        rows = [
            ['IC', f"{data['ic']:.4f}"],
            ['IC IR', f"{data['ic_ir']:.4f}"],
            ['IC Win Rate', f"{data['ic_win_rate']:.2%}"],
        ]
        
        for i, (name, value) in enumerate(data['group_returns'].items()):
            rows.append([f'{name} Return', f'{value:.4%}'])
        
        table = ax.table(cellText=rows,
                        colLabels=['Metric', 'Value'],
                        loc='center',
                        cellLoc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.5)
        
        ax.set_title('Factor Statistics', fontsize=12, fontweight='bold')
    
    def _plot_ic_series(self, gf: GridFigure, ic_series: pd.Series):
        """绘制 IC 序列"""
        ax = gf.next_row()
        
        if ic_series.empty:
            ax.text(0.5, 0.5, 'No IC data available', 
                   ha='center', va='center')
            return
        
        ax.plot(ic_series.index, ic_series.values, linewidth=1)
        ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        ax.axhline(y=ic_series.mean(), color='red', linestyle='--', 
                   label=f'Mean: {ic_series.mean():.4f}')
        ax.set_title('IC Time Series', fontsize=12, fontweight='bold')
        ax.set_xlabel('Date')
        ax.set_ylabel('IC')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_ic_decay(self, gf: GridFigure, ic_decay: pd.Series):
        """绘制 IC 衰减"""
        ax = gf.next_cell()
        
        if ic_decay.empty:
            ax.text(0.5, 0.5, 'No IC decay data available',
                   ha='center', va='center')
            return
        
        lags = [int(l.replace('lag_', '')) for l in ic_decay.index]
        values = ic_decay.values
        
        ax.bar(range(len(lags)), values, color='steelblue', alpha=0.7)
        ax.set_xticks(range(len(lags)))
        ax.set_xticklabels(lags)
        ax.set_title('IC Decay', fontsize=12, fontweight='bold')
        ax.set_xlabel('Lag (days)')
        ax.set_ylabel('IC')
        ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        ax.grid(True, alpha=0.3)
    
    def _plot_group_returns(self, gf: GridFigure, group_returns: pd.DataFrame):
        """绘制分组收益"""
        ax = gf.next_row()
        
        if group_returns.empty:
            ax.text(0.5, 0.5, 'No group returns data available',
                   ha='center', va='center')
            return
        
        # 按分位分组
        quantiles = sorted(group_returns.columns)
        means = group_returns.mean()
        
        x = range(len(quantiles))
        bars = ax.bar(x, means.values, color='steelblue', alpha=0.7)
        
        ax.set_xticks(x)
        ax.set_xticklabels([f'Q{q}' for q in quantiles])
        ax.set_title('Mean Returns by Quantile', fontsize=12, fontweight='bold')
        ax.set_xlabel('Quantile')
        ax.set_ylabel('Mean Return')
        ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        ax.grid(True, alpha=0.3)
    
    def save_html(self, path: str):
        """
        保存为 HTML 报告
        
        Args:
            path: 输出路径
        """
        # 先渲染图表
        fig = self.render(return_fig=True)
        
        # 保存为图片
        img_buffer = io.BytesIO()
        fig.savefig(img_buffer, format='png', dpi=self.config.dpi,
                   bbox_inches='tight')
        img_buffer.seek(0)
        
        # 编码为 base64
        img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
        
        # 生成 HTML
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{self.config.title}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 40px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
        }}
        .report-date {{
            color: #666;
            font-size: 14px;
            margin-bottom: 20px;
        }}
        .chart {{
            margin: 20px 0;
            text-align: center;
        }}
        .stats-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        .stats-table th, .stats-table td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: center;
        }}
        .stats-table th {{
            background-color: #4CAF50;
            color: white;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{self.config.title}</h1>
        <div class="report-date">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        
        <div class="chart">
            <img src="data:image/png;base64,{img_base64}" style="max-width:100%;">
        </div>
        
        <div class="footer">
            Generated by Quant Factor System
        </div>
    </div>
</body>
</html>
        """
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        plt.close(fig)
        print(f"✅ HTML report saved to: {path}")


class MonteCarloSimulator:
    """
    Monte Carlo 模拟器
    基于 QuantStats 设计
    
    功能:
    - 生成模拟收益路径
    - 计算破产概率
    - 计算目标达成概率
    - 可视化模拟结果
    """
    
    def __init__(self, returns: pd.Series, sims: int = 1000, seed: int = 42):
        """
        初始化
        
        Args:
            returns: 历史收益率序列
            sims: 模拟次数
            seed: 随机种子
        """
        self.returns = returns
        self.sims = sims
        self.seed = seed
        self.paths = None
    
    def run(self) -> 'MonteCarloSimulator':
        """
        运行模拟
        
        Returns:
            self
        """
        np.random.seed(self.seed)
        
        # 采样生成模拟路径
        self.paths = []
        n = len(self.returns)
        
        for _ in range(self.sims):
            # 有放回采样
            sampled = np.random.choice(self.returns, size=n, replace=True)
            
            # 计算累计收益
            path = (1 + sampled).cumprod()
            self.paths.append(path)
        
        self.paths = np.array(self.paths)
        
        return self
    
    def calculate_bust_probability(self, threshold: float = -0.2) -> float:
        """
        计算破产概率
        
        Args:
            threshold: 破产阈值 (默认 -20%)
            
        Returns:
            破产概率
        """
        if self.paths is None:
            self.run()
        
        # 检查每条路径是否跌破阈值
        busts = (self.paths.min(axis=1) < (1 + threshold)).sum()
        
        return busts / self.sims
    
    def calculate_goal_probability(self, goal: float = 0.5) -> float:
        """
        计算目标达成概率
        
        Args:
            goal: 目标收益率 (默认 50%)
            
        Returns:
            达成概率
        """
        if self.paths is None:
            self.run()
        
        successes = (self.paths[-1] >= (1 + goal)).sum()
        
        return successes / self.sims
    
    def get_percentile(self, percentile: float = 0.5) -> np.ndarray:
        """
        获取百分位路径
        
        Args:
            percentile: 百分位 (0-1)
            
        Returns:
            百分位路径
        """
        if self.paths is None:
            self.run()
        
        return np.percentile(self.paths, percentile * 100, axis=0)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计字典
        """
        if self.paths is None:
            self.run()
        
        final_returns = self.paths[-1] - 1
        
        return {
            'final_returns_mean': final_returns.mean(),
            'final_returns_std': final_returns.std(),
            'final_returns_min': final_returns.min(),
            'final_returns_max': final_returns.max(),
            'bust_probability': self.calculate_bust_probability(),
            'goal_probability': self.calculate_goal_probability(),
            'median_path': self.get_percentile(0.5),
            'percentile_5': self.get_percentile(0.05),
            'percentile_95': self.get_percentile(0.95),
        }
    
    def plot(self, title: str = "Monte Carlo Simulation"):
        """
        绘制模拟结果
        
        Args:
            title: 标题
        """
        if self.paths is None:
            self.run()
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # 1. 累计收益路径
        ax1 = axes[0]
        dates = range(len(self.paths[0]))
        
        # 绘制部分路径
        for i in range(min(100, self.sims)):
            ax1.plot(dates, self.paths[i], alpha=0.1, color='blue')
        
        # 绘制百分位
        ax1.plot(dates, self.get_percentile(0.5), 'r-', linewidth=2, label='Median')
        ax1.plot(dates, self.get_percentile(0.05), 'g--', linewidth=1, label='5th')
        ax1.plot(dates, self.get_percentile(0.95), 'g--', linewidth=1, label='95th')
        
        ax1.set_title(f'{title} - Cumulative Returns')
        ax1.set_xlabel('Day')
        ax1.set_ylabel('Cumulative Return')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. 最终收益分布
        ax2 = axes[1]
        final_returns = self.paths[-1] - 1
        
        ax2.hist(final_returns, bins=50, color='steelblue', alpha=0.7, edgecolor='white')
        ax2.axvline(x=0, color='red', linestyle='--', label='Break Even')
        ax2.axvline(x=final_returns.mean(), color='green', linestyle='--', 
                   label=f'Mean: {final_returns.mean():.2%}')
        
        ax2.set_title(f'{title} - Final Returns Distribution')
        ax2.set_xlabel('Final Return')
        ax2.set_ylabel('Frequency')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()


def create_factor_tearsheet(
    factor_name: str,
    ic_series: pd.Series,
    ic_decay: pd.Series,
    group_returns: Dict[str, float],
    group_returns_series: pd.DataFrame = None,
    output_path: str = None
) -> TearsheetBuilder:
    """
    创建因子 Tearsheet 的便捷函数
    
    Args:
        factor_name: 因子名称
        ic_series: IC 序列
        ic_decay: IC 衰减
        group_returns: 分组收益
        group_returns_series: 分组收益时序
        output_path: 输出路径
        
    Returns:
        TearsheetBuilder
    """
    builder = TearsheetBuilder(
        config=TearSheetConfig(title=f"{factor_name} Tearsheet")
    )
    
    # 添加 IC
    if not ic_series.empty:
        builder.add_ic_series(ic_series)
    
    # 添加 IC 衰减
    if not ic_decay.empty:
        builder.add_ic_decay(ic_decay)
    
    # 添加分组收益
    if group_returns_series is not None:
        builder.add_group_returns(group_returns_series)
    
    # 渲染
    if output_path:
        builder.save_html(output_path)
    else:
        builder.render()
    
    return builder


if __name__ == '__main__':
    print("=" * 60)
    print("🧪 测试 Tearsheet 模块")
    print("=" * 60)
    
    import numpy as np
    np.random.seed(42)
    
    # 创建测试数据
    dates = pd.date_range('2024-01-01', periods=252, freq='B')
    
    # IC 序列
    ic_series = pd.Series(np.random.randn(12) * 0.05, 
                         index=pd.date_range('2024-01-01', periods=12, freq='M'))
    
    # IC 衰减
    ic_decay = pd.Series({
        'lag_1': 0.05,
        'lag_2': 0.04,
        'lag_3': 0.03,
        'lag_5': 0.02,
        'lag_10': 0.01,
        'lag_20': 0.00,
    })
    
    # 分组收益
    group_returns = {
        'Q1': -0.02,
        'Q2': -0.01,
        'Q3': 0.00,
        'Q4': 0.01,
        'Q5': 0.03,
    }
    
    print("\n1. 创建 Tearsheet:")
    builder = TearsheetBuilder()
    builder.add_ic_series(ic_series)
    builder.add_ic_decay(ic_decay)
    builder.add_group_returns(pd.DataFrame(group_returns))
    
    # 渲染
    print("\n2. 渲染图表...")
    builder.render()
    
    print("\n3. 保存 HTML:")
    builder.save_html('/tmp/factor_tearsheet.html')
    
    print("\n4. 测试 Monte Carlo:")
    returns = pd.Series(np.random.randn(252) * 0.02)
    mc = MonteCarloSimulator(returns, sims=1000)
    stats = mc.get_statistics()
    
    print(f"   最终收益均值: {stats['final_returns_mean']:.2%}")
    print(f"   破产概率: {stats['bust_probability']:.2%}")
    print(f"   目标达成概率: {stats['goal_probability']:.2%}")
    
    print("\n   绘制模拟结果...")
    mc.plot("Test Monte Carlo")
    
    print("\n" + "=" * 60)
    print("✅ Tearsheet 模块测试完成!")
    print("=" * 60)
