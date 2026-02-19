"""
因子报告生成器
Factor Report Generator

功能：
- 生成因子研究 HTML 报告
- 包含 IC 分析、分组收益、统计信息
- 支持嵌入可视化图表
- 输出到指定目录

使用方式：
    from quant_factor_system.factors.report import create_factor_report
    
    report = create_factor_report(
        name='momentum_20',
        factor=momentum_factor,
        price_data=price_data,
        output_dir='output/factors'
    )
    report.generate()
    report.open()
"""

import os
import json
from datetime import datetime
from typing import Dict, Optional, Any
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import webbrowser

from quant_factor_system.core.base import Factor


class FactorReportGenerator:
    """
    因子报告生成器
    
    生成因子研究的 HTML 报告，包含：
    - 因子基本信息
    - IC 分析（时间序列、分布）
    - 分组收益分析
    - 因子统计信息
    """
    
    def __init__(
        self,
        name: str,
        factor,
        price_data: pd.DataFrame,
        output_dir: str = 'output/factors',
        split_date: Optional[str] = None
    ):
        """
        初始化报告生成器
        
        Args:
            name: 因子名称
            factor: 因子实例或因子类
            price_data: 价格数据
            output_dir: 输出目录
            split_date: 训练/测试集分割日期
        """
        self.name = name
        self.factor = factor
        self.price_data = price_data.copy()
        self.output_dir = output_dir
        self.split_date = split_date
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 报告数据
        self.report_data: Dict[str, Any] = {}
    
    def analyze(self) -> Dict[str, Any]:
        """
        分析因子表现
        
        Returns:
            分析结果字典
        """
        # 1. 计算因子值
        if hasattr(self.factor, 'calculate'):
            factor_values = self.factor.calculate(self.price_data)
        else:
            factor_values = self.factor(self.price_data)
        
        # 确保是 Series
        if isinstance(factor_values, pd.DataFrame):
            factor_values = factor_values.iloc[:, 0]
        
        factor_values.name = self.name
        
        # 2. 计算未来收益（用于 IC 分析）
        close = self.price_data['close'] if 'close' in self.price_data.columns else self.price_data.iloc[:, 0]
        future_return = close.pct_change().shift(-1)
        
        # 合并数据
        merged = pd.DataFrame({
            'factor': factor_values,
            'future_return': future_return,
        }).dropna()
        
        # 3. IC 计算
        ic_all = merged['factor'].corr(merged['future_return'])
        
        # 分训练/测试集
        if self.split_date:
            split_dt = pd.to_datetime(self.split_date)
            train_data = merged[merged.index < split_dt]
            test_data = merged[merged.index >= split_dt]
            
            ic_train = train_data['factor'].corr(train_data['future_return']) if len(train_data) > 10 else None
            ic_test = test_data['factor'].corr(test_data['future_return']) if len(test_data) > 10 else None
        else:
            ic_train = None
            ic_test = None
        
        # 4. 统计信息
        factor_stats = {
            'mean': float(factor_values.mean()),
            'std': float(factor_values.std()),
            'min': float(factor_values.min()),
            'max': float(factor_values.max()),
            'skew': float(factor_values.skew()) if len(factor_values) > 10 else 0,
            'ic': ic_all,
            'ic_train': ic_train,
            'ic_test': ic_test,
            'samples': len(merged),
        }
        
        # 5. 分组收益分析
        # 将因子分为 5 组
        quantiles = pd.qcut(factor_values, q=5, labels=['Q1', 'Q2', 'Q3', 'Q4', 'Q5'])
        group_returns = merged.groupby(quantiles)['future_return'].mean()
        
        # 保存报告数据
        self.report_data = {
            'factor_name': self.name,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'factor_stats': factor_stats,
            'group_returns': group_returns.to_dict(),
            'ic_series': None,  # 滚动 IC（如果有）
            'factor_values': factor_values.to_dict(),
        }
        
        return self.report_data
    
    def _create_ic_timeseries_chart(self) -> str:
        """创建 IC 时间序列图"""
        if self.report_data.get('ic_series') is None:
            return ''
        
        ic_series = self.report_data['ic_series']
        if isinstance(ic_series, dict):
            dates = list(ic_series.keys())
            values = list(ic_series.values())
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates, y=values,
                mode='lines',
                name='Rolling IC',
                line=dict(color='#2196F3', width=1)
            ))
            
            # 添加均值线
            mean_ic = np.mean(values)
            fig.add_hline(y=mean_ic, line_dash='dash', line_color='gray')
            fig.add_hline(y=0, line_color='black')
            
            fig.update_layout(
                title='IC Time Series',
                xaxis_title='Date',
                yaxis_title='IC',
                height=300,
            )
            
            return fig.to_html(full_html=False, include_plotlyjs='cdn')
        return ''
    
    def _create_ic_distribution_chart(self) -> str:
        """创建 IC 分布图"""
        stats = self.report_data.get('factor_stats', {})
        
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=[],
            nbinsx=30,
            marker_color='#2196F3',
            name='IC Distribution'
        ))
        
        fig.update_layout(
            title=f'IC Distribution (IC={stats.get("ic", 0):.4f})',
            xaxis_title='IC',
            yaxis_title='Frequency',
            height=300,
        )
        
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    def _create_group_returns_chart(self) -> str:
        """创建分组收益图"""
        group_returns = self.report_data.get('group_returns', {})
        
        groups = list(group_returns.keys())
        returns = list(group_returns.values())
        
        # 颜色映射
        colors = ['#ef5350', '#ff9800', '#ffee58', '#66bb6a', '#26a69a']
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=groups,
            y=returns,
            marker_color=colors,
            text=[f'{r*100:.2f}%' for r in returns],
            textposition='outside',
            name='Group Returns'
        ))
        
        fig.update_layout(
            title='Group Returns by Factor Quantile',
            xaxis_title='Quantile',
            yaxis_title='Average Return',
            height=300,
        )
        
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    def _create_factor_distribution_chart(self) -> str:
        """创建因子值分布图"""
        factor_values = self.report_data.get('factor_values', {})
        if isinstance(factor_values, dict):
            values = list(factor_values.values())
            
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=values,
                nbinsx=50,
                marker_color='#7E57C2',
                name='Factor Distribution'
            ))
            
            fig.update_layout(
                title=f'{self.name} Distribution',
                xaxis_title='Factor Value',
                yaxis_title='Frequency',
                height=300,
            )
            
            return fig.to_html(full_html=False, include_plotlyjs='cdn')
        return ''
    
    def generate(self, output_file: Optional[str] = None) -> str:
        """
        生成 HTML 报告
        
        Args:
            output_file: 输出文件名，默认自动生成
            
        Returns:
            输出文件路径
        """
        # 如果没有分析，先进行分析
        if not self.report_data:
            self.analyze()
        
        # 生成文件名
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'{self.name}_{timestamp}.html'
        
        output_path = os.path.join(self.output_dir, output_file)
        
        # 生成图表
        ic_chart = self._create_ic_timeseries_chart()
        ic_dist_chart = self._create_ic_distribution_chart()
        group_chart = self._create_group_returns_chart()
        factor_dist_chart = self._create_factor_distribution_chart()
        
        # 生成 HTML
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.name} - Factor Research Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #1976D2;
            border-bottom: 3px solid #1976D2;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #424242;
            margin-top: 30px;
        }}
        .info-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .info-card h3 {{
            margin: 0 0 10px 0;
        }}
        .metric {{
            display: inline-block;
            background: #E3F2FD;
            padding: 10px 20px;
            margin: 5px;
            border-radius: 5px;
            text-align: center;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
            color: #1976D2;
        }}
        .metric-label {{
            font-size: 12px;
            color: #666;
        }}
        .chart-container {{
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }}
        th {{
            background: #1976D2;
            color: white;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 {self.name} - Factor Research Report</h1>
        
        <div class="info-card">
            <h3>Factor Information</h3>
            <p>Generated at: {self.report_data.get('generated_at', '')}</p>
            <p>Split Date: {self.split_date or 'None (Full Period)'}</p>
        </div>
        
        <h2>📈 Key Metrics</h2>
        <div>
            <div class="metric">
                <div class="metric-value">{self.report_data['factor_stats'].get('ic', 0):.4f}</div>
                <div class="metric-label">IC (All)</div>
            </div>
            <div class="metric">
                <div class="metric-value">{self.report_data['factor_stats'].get('samples', 0)}</div>
                <div class="metric-label">Samples</div>
            </div>
            <div class="metric">
                <div class="metric-value">{self.report_data['factor_stats'].get('mean', 0):.4f}</div>
                <div class="metric-label">Mean</div>
            </div>
            <div class="metric">
                <div class="metric-value">{self.report_data['factor_stats'].get('std', 0):.4f}</div>
                <div class="metric-label">Std</div>
            </div>
            <div class="metric">
                <div class="metric-value">{self.report_data['factor_stats'].get('skew', 0):.4f}</div>
                <div class="metric-label">Skewness</div>
            </div>
        </div>
        
        <h2>📊 IC Analysis</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>IC (All)</td>
                <td>{self.report_data['factor_stats'].get('ic', 0):.4f}</td>
            </tr>
            <tr>
                <td>IC (Train)</td>
                <td>{self.report_data['factor_stats'].get('ic_train', 'N/A')}</td>
            </tr>
            <tr>
                <td>IC (Test)</td>
                <td>{self.report_data['factor_stats'].get('ic_test', 'N/A')}</td>
            </tr>
        </table>
        
        <div class="chart-container">
            {ic_dist_chart}
        </div>
        
        <h2>📈 Group Returns</h2>
        <p>Average returns by factor quantile (Q1=Lowest, Q5=Highest)</p>
        
        <div class="chart-container">
            {group_chart}
        </div>
        
        <table>
            <tr>
                <th>Quantile</th>
                <th>Average Return</th>
            </tr>
            {''.join(f'<tr><td>{k}</td><td>{v*100:.4f}%</td></tr>' for k, v in self.report_data.get('group_returns', {}).items())}
        </table>
        
        <h2>📉 Factor Distribution</h2>
        <div class="chart-container">
            {factor_dist_chart}
        </div>
        
        <div class="footer">
            <p>Generated by QuantFactor System</p>
            <p>Report file: {output_path}</p>
        </div>
    </div>
</body>
</html>'''
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f'✅ 报告已生成: {output_path}')
        return output_path
    
    def open(self):
        """在浏览器中打开报告"""
        output_path = os.path.join(self.output_dir, f'{self.name}_*.html')
        # 找到最新的报告
        import glob
        files = sorted(glob.glob(output_path))
        if files:
            webbrowser.open(f'file://{files[-1]}')
            print(f'🌐 已在浏览器中打开: {files[-1]}')
        else:
            print('❌ 未找到报告文件，请先调用 generate()')


def create_factor_report(
    name: str,
    factor,
    price_data: pd.DataFrame,
    output_dir: str = 'output/factors',
    split_date: Optional[str] = None
) -> FactorReportGenerator:
    """
    创建因子报告生成器的便捷函数
    
    Args:
        name: 因子名称
        factor: 因子实例
        price_data: 价格数据
        output_dir: 输出目录
        split_date: 训练/测试分割日期
        
    Returns:
        FactorReportGenerator 实例
    """
    return FactorReportGenerator(
        name=name,
        factor=factor,
        price_data=price_data,
        output_dir=output_dir,
        split_date=split_date
    )


__all__ = [
    'FactorReportGenerator',
    'create_factor_report',
]
