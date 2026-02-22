"""
因子报告生成器 (增强版)
Factor Report Generator - Enhanced

参考 Alphalens 设计，新增：
- 滚动 IC 分析
- 分组收益分析
- 因子换手率
- 因子自相关性
"""

import os
import json
from datetime import datetime
from typing import Dict, Optional, Any
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import webbrowser

from quant_factor_system.core.base import Factor


class FactorReportGenerator:
    """因子报告生成器 - 增强版"""
    
    def __init__(
        self,
        name: str,
        factor,
        price_data: pd.DataFrame,
        output_dir: str = 'output/factors',
        split_date: Optional[str] = None,
        quantiles: int = 5,
        ic_window: int = 60,
    ):
        self.name = name
        self.factor = factor
        self.price_data = price_data.copy()
        self.output_dir = output_dir
        self.split_date = split_date
        self.quantiles = quantiles
        self.ic_window = ic_window
        os.makedirs(output_dir, exist_ok=True)
        self.report_data: Dict[str, Any] = {}
    
    def analyze(self) -> Dict[str, Any]:
        """完整的因子分析"""
        print(f"📊 分析因子: {self.name}")
        
        # 计算因子值
        factor_values = self._calculate_factor()
        close = self._get_close_price()
        future_return = close.pct_change().shift(-1)
        merged = self._merge_data(factor_values, future_return)
        
        # IC 分析
        self._analyze_ic(merged)
        
        # 分组收益分析
        self._analyze_returns(merged)
        
        # 换手率分析
        self._analyze_turnover(merged, factor_values)
        
        # 自相关分析
        self._analyze_autocorrelation(factor_values)
        
        # 因子统计
        self._analyze_factor_stats(factor_values)
        
        print(f"   ✅ 分析完成，样本数: {len(merged)}")
        return self.report_data
    
    def _calculate_factor(self) -> pd.Series:
        if hasattr(self.factor, 'calculate'):
            result = self.factor.calculate(self.price_data)
        else:
            result = self.factor(self.price_data)
        if isinstance(result, pd.DataFrame):
            result = result.iloc[:, 0]
        return result.dropna()
    
    def _get_close_price(self) -> pd.Series:
        return self.price_data['close'] if 'close' in self.price_data.columns else self.price_data.iloc[:, 0]
    
    def _merge_data(self, factor_values: pd.Series, future_return: pd.Series) -> pd.DataFrame:
        merged = pd.DataFrame({
            'factor': factor_values,
            'future_return': future_return,
        }).dropna()
        merged = merged[~np.isinf(merged['factor'])]
        return merged
    
    def _analyze_ic(self, merged: pd.DataFrame):
        ic_all = merged['factor'].corr(merged['future_return'])
        rolling_ic = merged['factor'].rolling(self.ic_window).corr(merged['future_return'])
        
        if self.split_date:
            split_dt = pd.to_datetime(self.split_date)
            train = merged[merged.index < split_dt]
            test = merged[merged.index >= split_dt]
            ic_train = train['factor'].corr(train['future_return']) if len(train) > 10 else None
            ic_test = test['factor'].corr(test['future_return']) if len(test) > 10 else None
        else:
            ic_train, ic_test = None, None
        
        ic_series = rolling_ic.dropna()
        self.report_data['ic_analysis'] = {
            'ic_all': ic_all,
            'ic_train': ic_train,
            'ic_test': ic_test,
            'ic_mean': ic_series.mean(),
            'ic_std': ic_series.std(),
            'ic_icir': ic_series.mean() / ic_series.std() if ic_series.std() > 0 else 0,
            'ic_positive_ratio': (ic_series > 0).mean(),
            'rolling_ic': rolling_ic.dropna().to_dict(),
        }
    
    def _analyze_returns(self, merged: pd.DataFrame):
        try:
            quantile_labels = [f'Q{i+1}' for i in range(self.quantiles)]
            merged['quantile'] = pd.qcut(merged['factor'], q=self.quantiles, labels=quantile_labels, duplicates='drop')
        except:
            merged['quantile'] = pd.cut(merged['factor'], bins=self.quantiles, labels=quantile_labels, duplicates='drop')
        
        group_returns = merged.groupby('quantile')['future_return'].mean()
        self.report_data['returns_analysis'] = {
            'group_returns': group_returns.to_dict(),
            'long_short_return': group_returns.iloc[-1] - group_returns.iloc[0],
            'quantile_turnover': (merged['quantile'] != merged['quantile'].shift(1)).mean(),
        }
    
    def _analyze_turnover(self, merged: pd.DataFrame, factor_values: pd.Series):
        factor_change = factor_values.pct_change().abs()
        self.report_data['turnover'] = {
            'quantile_turnover': self.report_data.get('returns_analysis', {}).get('quantile_turnover', 0),
            'factor_change_mean': factor_change.mean(),
            'factor_change_std': factor_change.std(),
        }
    
    def _analyze_autocorrelation(self, factor_values: pd.Series):
        lags = [1, 5, 10, 20, 60]
        self.report_data['autocorrelation'] = {
            f'lag_{lag}': factor_values.autocorr(lag=lag) if len(factor_values) > lag else 0
            for lag in lags
        }
    
    def _analyze_factor_stats(self, factor_values: pd.Series):
        self.report_data['factor_stats'] = {
            'count': len(factor_values),
            'mean': float(factor_values.mean()),
            'std': float(factor_values.std()),
            'min': float(factor_values.min()),
            'max': float(factor_values.max()),
            'skew': float(factor_values.skew()) if len(factor_values) > 10 else 0,
            'kurtosis': float(factor_values.kurtosis()) if len(factor_values) > 10 else 0,
            'median': float(factor_values.median()),
        }
    
    def generate(self, output_file: Optional[str] = None) -> str:
        if not self.report_data:
            self.analyze()
        
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'{self.name}_{timestamp}.html'
        
        output_path = os.path.join(self.output_dir, output_file)
        
        # 生成图表
        rolling_ic_chart = self._create_rolling_ic_chart()
        group_returns_chart = self._create_group_returns_chart()
        autocorrelation_chart = self._create_autocorrelation_chart()
        
        # 生成 HTML
        ic = self.report_data.get('ic_analysis', {})
        returns = self.report_data.get('returns_analysis', {})
        turnover = self.report_data.get('turnover', {})
        autocorr = self.report_data.get('autocorrelation', {})
        factor_stats = self.report_data.get('factor_stats', {})
        
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.name} - Factor Research Report</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #1976D2; border-bottom: 3px solid #1976D2; padding-bottom: 10px; }}
        h2 {{ color: #424242; margin-top: 30px; border-left: 4px solid #1976D2; padding-left: 10px; }}
        .info-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 20px 0; }}
        .metric {{ background: #E3F2FD; padding: 15px; border-radius: 8px; text-align: center; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #1976D2; }}
        .metric-label {{ font-size: 12px; color: #666; margin-top: 5px; }}
        .chart-container {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; border: 1px solid #e0e0e0; }}
        .summary-box {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 20px 0; }}
        .summary-item {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
        .summary-item.bad {{ background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); }}
        .summary-value {{ font-size: 28px; font-weight: bold; }}
        .summary-label {{ font-size: 14px; margin-top: 5px; }}
        .positive {{ color: green; }}
        .negative {{ color: red; }}
        .section {{ margin: 40px 0; padding: 20px; background: #FAFAFA; border-radius: 8px; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; color: #666; font-size: 12px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px; }}
        th, td {{ padding: 12px; text-align: center; border-bottom: 1px solid #e0e0e0; }}
        th {{ background: #1976D2; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 {self.name} - Factor Research Report</h1>
        
        <div class="info-card">
            <h3>📋 Factor Information</h3>
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Quantiles:</strong> {self.quantiles} | <strong>IC Window:</strong> {self.ic_window}</p>
            <p><strong>Split Date:</strong> {self.split_date or 'None (Full Period)'}</p>
        </div>
        
        <!-- 关键指标摘要 -->
        <div class="summary-box">
            <div class="summary-item {'bad' if ic.get('ic_all', 0) < 0 else ''}">
                <div class="summary-value">{ic.get('ic_all', 0):.4f}</div>
                <div class="summary-label">IC (All)</div>
            </div>
            <div class="summary-item {'bad' if returns.get('long_short_return', 0) < 0 else ''}">
                <div class="summary-value">{returns.get('long_short_return', 0)*100:.2f}%</div>
                <div class="summary-label">Long-Short Return</div>
            </div>
            <div class="summary-item">
                <div class="summary-value">{ic.get('ic_icir', 0):.2f}</div>
                <div class="summary-label">IC IR</div>
            </div>
        </div>
        
        <!-- IC 分析 -->
        <div class="section">
            <h2>📈 Information Coefficient (IC) Analysis</h2>
            <div class="metric-grid">
                <div class="metric"><div class="metric-value">{ic.get('ic_all', 0):.4f}</div><div class="metric-label">IC (All)</div></div>
                <div class="metric"><div class="metric-value">{ic.get('ic_train', 'N/A')}</div><div class="metric-label">IC (Train)</div></div>
                <div class="metric"><div class="metric-value">{ic.get('ic_test', 'N/A')}</div><div class="metric-label">IC (Test)</div></div>
                <div class="metric"><div class="metric-value">{ic.get('ic_mean', 0):.4f}</div><div class="metric-label">Rolling IC Mean</div></div>
                <div class="metric"><div class="metric-value">{ic.get('ic_std', 0):.4f}</div><div class="metric-label">Rolling IC Std</div></div>
                <div class="metric"><div class="metric-value">{ic.get('ic_icir', 0):.2f}</div><div class="metric-label">IC IR</div></div>
                <div class="metric"><div class="metric-value">{ic.get('ic_positive_ratio', 0)*100:.1f}%</div><div class="metric-label">IC Positive %</div></div>
            </div>
            <div class="chart-container"><h3>Rolling IC Time Series</h3>{rolling_ic_chart}</div>
        </div>
        
        <!-- 分组收益分析 -->
        <div class="section">
            <h2>💰 Returns Analysis by Quantile</h2>
            <table>
                <tr><th>Quantile</th><th>Mean Return</th></tr>
                {''.join(f'<tr><td>{q}</td><td class="{"positive" if v > 0 else "negative"}">{v*100:.4f}%</td></tr>' for q, v in returns.get('group_returns', {}).items())}
            </table>
            <div class="chart-container"><h3>Group Returns</h3>{group_returns_chart}</div>
        </div>
        
        <!-- 换手率分析 -->
        <div class="section">
            <h2>🔄 Turnover Analysis</h2>
            <div class="metric-grid">
                <div class="metric"><div class="metric-value">{turnover.get('quantile_turnover', 0)*100:.2f}%</div><div class="metric-label">Quantile Turnover</div></div>
                <div class="metric"><div class="metric-value">{turnover.get('factor_change_mean', 0)*100:.4f}%</div><div class="metric-label">Factor Change Mean</div></div>
            </div>
        </div>
        
        <!-- 自相关分析 -->
        <div class="section">
            <h2>📐 Autocorrelation Analysis</h2>
            <div class="chart-container">{autocorrelation_chart}</div>
        </div>
        
        <!-- 因子统计 -->
        <div class="section">
            <h2>📊 Factor Statistics</h2>
            <div class="metric-grid">
                <div class="metric"><div class="metric-value">{factor_stats.get('count', 0)}</div><div class="metric-label">Samples</div></div>
                <div class="metric"><div class="metric-value">{factor_stats.get('mean', 0):.4f}</div><div class="metric-label">Mean</div></div>
                <div class="metric"><div class="metric-value">{factor_stats.get('std', 0):.4f}</div><div class="metric-label">Std</div></div>
                <div class="metric"><div class="metric-value">{factor_stats.get('skew', 0):.4f}</div><div class="metric-label">Skewness</div></div>
                <div class="metric"><div class="metric-value">{factor_stats.get('kurtosis', 0):.4f}</div><div class="metric-label">Kurtosis</div></div>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by QuantFactor System | Report: {output_path}</p>
        </div>
    </div>
</body>
</html>'''
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✅ 报告已生成: {output_path}")
        return output_path
    
    def _create_rolling_ic_chart(self) -> str:
        rolling_ic = self.report_data.get('ic_analysis', {}).get('rolling_ic', {})
        if not rolling_ic:
            return ''
        dates, values = list(rolling_ic.keys()), list(rolling_ic.values())
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=values, mode='lines', name='Rolling IC', line=dict(color='#2196F3', width=1)))
        fig.add_hline(y=0, line_color='black')
        fig.add_hline(y=np.mean(values), line_dash='dash', line_color='gray')
        fig.update_layout(title=f'Rolling IC (window={self.ic_window})', xaxis_title='Date', yaxis_title='IC', height=300)
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    def _create_group_returns_chart(self) -> str:
        group_returns = self.report_data.get('returns_analysis', {}).get('group_returns', {})
        groups, returns = list(group_returns.keys()), list(group_returns.values())
        colors = px.colors.diverging.RdBu_r[:len(groups)]
        fig = go.Figure()
        fig.add_trace(go.Bar(x=groups, y=returns, marker_color=colors, text=[f'{r*100:.2f}%' for r in returns], textposition='outside'))
        fig.update_layout(title='Group Returns (Q1=Lowest, Q5=Highest)', xaxis_title='Quantile', yaxis_title='Avg Return', height=300)
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    def _create_autocorrelation_chart(self) -> str:
        autocorr = self.report_data.get('autocorrelation', {})
        lags, values = list(autocorr.keys()), list(autocorr.values())
        fig = go.Figure()
        fig.add_trace(go.Bar(x=lags, y=values, marker_color='#FF9800'))
        fig.add_hline(y=0, line_color='black')
        fig.update_layout(title='Factor Autocorrelation', xaxis_title='Lag', yaxis_title='Autocorrelation', height=300)
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    def open(self):
        import glob
        files = sorted(glob.glob(os.path.join(self.output_dir, f'{self.name}_*.html')))
        if files:
            webbrowser.open(f'file://{files[-1]}')
            print(f"🌐 已在浏览器中打开: {files[-1]}")


def create_factor_report(
    name: str, factor, price_data: pd.DataFrame,
    output_dir: str = 'output/factors',
    split_date: Optional[str] = None,
    quantiles: int = 5, ic_window: int = 60,
) -> FactorReportGenerator:
    return FactorReportGenerator(name, factor, price_data, output_dir, split_date, quantiles, ic_window)


__all__ = ['FactorReportGenerator', 'create_factor_report']
