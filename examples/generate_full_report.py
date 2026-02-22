"""
使用数据库真实的 factor_return_5d 数据生成完整报告
包含所有图表可视化
"""

import sys
sys.path.insert(0, '/Users/xinzhan/.openclaw/workspace')

from quant_factor_system.data import TimescaleDB
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_full_report():
    print("="*60)
    print("🎯 生成完整的因子研究报告 (含图表)")
    print("="*60)
    
    db = TimescaleDB()
    
    try:
        with db.connection() as conn:
            cursor = conn.cursor()
            
            print("\n📥 从数据库加载数据...")
            
            # 获取因子数据
            cursor.execute("""
                SELECT symbol, time::date as date, value 
                FROM factor_return_5d
                ORDER BY symbol, date
                LIMIT 500000
            """)
            factor_rows = cursor.fetchall()
            print(f"   因子数据: {len(factor_rows):,} 条")
            
            symbols = list(set([r[0] for r in factor_rows]))
            print(f"   股票数: {len(symbols)}")
            
            # 获取价格数据
            cursor.execute("""
                SELECT symbol, time::date as date, close 
                FROM price_daily
                WHERE symbol = ANY(%s)
                ORDER BY symbol, date
            """, (symbols,))
            price_rows = cursor.fetchall()
            print(f"   价格数据: {len(price_rows):,} 条")
            
            # 转换数据
            factor_df = pd.DataFrame(factor_rows, columns=['symbol', 'date', 'factor'])
            factor_df['date'] = pd.to_datetime(factor_df['date'])
            
            price_df = pd.DataFrame(price_rows, columns=['symbol', 'date', 'close'])
            price_df['date'] = pd.to_datetime(price_df['date'])
            
            # 合并
            merged = factor_df.merge(price_df, on=['symbol', 'date'])
            merged = merged.sort_values(['symbol', 'date'])
            print(f"   合并后: {len(merged):,} 条")
            
            # 计算未来收益
            merged['future_return'] = merged.groupby('symbol')['close'].pct_change().shift(-1)
            merged = merged.replace([np.inf, -np.inf], np.nan).dropna()
            print(f"   有效数据: {len(merged):,} 条")
            
            # ===== 分析计算 =====
            print("\n📊 计算分析指标...")
            
            # IC 分析
            ic_all = merged['factor'].corr(merged['future_return'])
            ic_window = 60
            merged['rolling_ic'] = merged.groupby('symbol').apply(
                lambda x: x['factor'].rolling(ic_window).corr(x['future_return'])
            ).reset_index(level=0, drop=True)
            ic_series = merged['rolling_ic'].dropna()
            
            ic_mean = ic_series.mean()
            ic_std = ic_series.std()
            ic_icir = ic_mean / ic_std if ic_std > 0 else 0
            ic_positive = (ic_series > 0).mean()
            
            # 分组收益
            merged['quantile'] = pd.qcut(merged['factor'], q=5, labels=['Q1', 'Q2', 'Q3', 'Q4', 'Q5'], duplicates='drop')
            group_returns = merged.groupby('quantile')['future_return'].mean()
            long_short = group_returns['Q5'] - group_returns['Q1']
            
            # 换手率
            turnover = (merged['quantile'] != merged['quantile'].shift(1)).mean()
            
            # ===== 生成图表 =====
            print("\n📈 生成可视化图表...")
            
            # 1. IC 时间序列图
            ic_ts = merged.groupby('date')['rolling_ic'].mean().dropna()
            
            fig_ic = go.Figure()
            fig_ic.add_trace(go.Scatter(
                x=ic_ts.index, y=ic_ts.values,
                mode='lines',
                name='Rolling IC',
                line=dict(color='#2196F3', width=1)
            ))
            fig_ic.add_hline(y=0, line_color='black')
            fig_ic.add_hline(y=ic_mean, line_dash='dash', line_color='gray')
            fig_ic.update_layout(
                title=f'Rolling IC Time Series (window={ic_window})',
                xaxis_title='Date',
                yaxis_title='IC',
                height=350,
                template='plotly_white'
            )
            ic_ts_html = fig_ic.to_html(full_html=False, include_plotlyjs='cdn')
            
            # 2. IC 分布直方图
            fig_ic_dist = go.Figure()
            fig_ic_dist.add_trace(go.Histogram(
                x=ic_series.values,
                nbinsx=50,
                marker_color='#2196F3',
                name='IC Distribution'
            ))
            fig_ic_dist.add_vline(x=ic_all, line_dash='dash', line_color='red', annotation_text=f'IC={ic_all:.4f}')
            fig_ic_dist.update_layout(
                title='IC Distribution',
                xaxis_title='IC',
                yaxis_title='Frequency',
                height=350,
                template='plotly_white'
            )
            ic_dist_html = fig_ic_dist.to_html(full_html=False, include_plotlyjs='cdn')
            
            # 3. 分组收益柱状图
            colors = ['#ef5350', '#ff9800', '#ffee58', '#66bb6a', '#26a69a']
            fig_group = go.Figure()
            fig_group.add_trace(go.Bar(
                x=group_returns.index,
                y=group_returns.values * 100,
                marker_color=colors,
                text=[f'{v*100:.3f}%' for v in group_returns.values],
                textposition='outside',
                name='Avg Return'
            ))
            fig_group.add_hline(y=0, line_color='black')
            fig_group.update_layout(
                title='Group Returns by Factor Quantile',
                xaxis_title='Quantile (Q1=Low, Q5=High)',
                yaxis_title='Average Daily Return (%)',
                height=350,
                template='plotly_white'
            )
            group_html = fig_group.to_html(full_html=False, include_plotlyjs='cdn')
            
            # 4. 因子值分布
            fig_factor_dist = go.Figure()
            fig_factor_dist.add_trace(go.Histogram(
                x=merged['factor'].values,
                nbinsx=50,
                marker_color='#7E57C2',
                name='Factor Distribution'
            ))
            fig_factor_dist.update_layout(
                title='Factor Value Distribution',
                xaxis_title='Factor Value',
                yaxis_title='Frequency',
                height=350,
                template='plotly_white'
            )
            factor_dist_html = fig_factor_dist.to_html(full_html=False, include_plotlyjs='cdn')
            
            # 5. 累计收益曲线
            fig_cum = go.Figure()
            for q in ['Q1', 'Q3', 'Q5']:
                q_data = merged[merged['quantile'] == q].copy()
                q_data = q_data.sort_values('date')
                q_data['cum_ret'] = (1 + q_data['future_return']).cumprod() - 1
                fig_cum.add_trace(go.Scatter(
                    x=q_data['date'].unique(),
                    y=q_data.groupby('date')['future_return'].mean().cumprod() - 1,
                    mode='lines',
                    name=f'{q}',
                    line=dict(width=2)
                ))
            fig_cum.update_layout(
                title='Cumulative Returns by Quantile',
                xaxis_title='Date',
                yaxis_title='Cumulative Return',
                height=350,
                template='plotly_white'
            )
            cum_html = fig_cum.to_html(full_html=False, include_plotlyjs='cdn')
            
            # 6. IC 热力图（按月份）
            merged['month'] = merged['date'].dt.month
            ic_by_month = merged.groupby('month').apply(
                lambda x: x['factor'].corr(x['future_return'])
            )
            fig_heat = go.Figure(data=go.Heatmap(
                z=[ic_by_month.values],
                x=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                y=['IC'],
                colorscale='RdBu_r',
                zmid=0
            ))
            fig_heat.update_layout(
                title='IC by Month',
                height=250,
                template='plotly_white'
            )
            heat_html = fig_heat.to_html(full_html=False, include_plotlyjs='cdn')
            
            # ===== 生成完整 HTML 报告 =====
            print("\n📝 生成 HTML 报告...")
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'return_5d_full_report_{timestamp}.html'
            
            html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>return_5d - 完整因子研究报告</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{ 
            max-width: 1400px; 
            margin: 0 auto; 
            background: white; 
            padding: 40px; 
            border-radius: 16px; 
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        h1 {{ 
            color: #1a237e; 
            border-bottom: 4px solid #3f51b5; 
            padding-bottom: 15px;
            margin-bottom: 30px;
            font-size: 32px;
        }}
        h2 {{ 
            color: #303f9f; 
            margin-top: 40px; 
            padding: 15px;
            background: linear-gradient(90deg, #3f51b5 0%, #5c6bc0 100%);
            color: white;
            border-radius: 8px;
            font-size: 24px;
        }}
        h3 {{ 
            color: #3949ab; 
            margin-top: 25px;
            font-size: 18px;
        }}
        .header-info {{
            background: linear-gradient(135deg, #1a237e 0%, #3949ab 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin: 20px 0;
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
        }}
        .info-item {{ text-align: center; }}
        .info-value {{ font-size: 28px; font-weight: bold; margin-bottom: 5px; }}
        .info-label {{ font-size: 14px; opacity: 0.9; }}
        
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin: 30px 0;
        }}
        .summary-card {{
            padding: 25px;
            border-radius: 12px;
            text-align: center;
            color: white;
        }}
        .summary-card.ic {{ background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%); }}
        .summary-card.ls {{ background: linear-gradient(135deg, #4CAF50 0%, #388E3C 100%); }}
        .summary-card.ir {{ background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%); }}
        .summary-card .value {{ font-size: 36px; font-weight: bold; }}
        .summary-card .label {{ font-size: 16px; margin-top: 10px; }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .metric-box {{
            background: #E8EAF6;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }}
        .metric-value {{ font-size: 28px; font-weight: bold; color: #3f51b5; }}
        .metric-label {{ font-size: 14px; color: #5c6bc0; margin-top: 8px; }}
        
        .chart-section {{
            margin: 30px 0;
            padding: 25px;
            background: #FAFAFA;
            border-radius: 12px;
            border: 1px solid #E0E0E0;
        }}
        .chart-title {{
            font-size: 20px;
            font-weight: bold;
            color: #303f9f;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #3f51b5;
        }}
        
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin: 25px 0;
            font-size: 16px;
        }}
        th, td {{ padding: 15px; text-align: center; border-bottom: 2px solid #E0E0E0; }}
        th {{ 
            background: linear-gradient(90deg, #3f51b5 0%, #5c6bc0 100%);
            color: white;
            font-weight: bold;
        }}
        tr:hover {{ background: #E8EAF6; }}
        .positive {{ color: #2E7D32; font-weight: bold; }}
        .negative {{ color: #C62828; font-weight: bold; }}
        .highlight {{ background: #C5CAE9 !important; font-weight: bold; }}
        
        .footer {{
            margin-top: 40px;
            padding-top: 25px;
            border-top: 3px solid #3f51b5;
            color: #5c6bc0;
            font-size: 14px;
            text-align: center;
        }}
        
        .two-charts {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        
        @media (max-width: 768px) {{
            .header-info, .summary-grid, .two-charts {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 return_5d 因子研究报告</h1>
        
        <div class="header-info">
            <div class="info-item">
                <div class="info-value">{len(merged):,}</div>
                <div class="info-label">样本数量</div>
            </div>
            <div class="info-item">
                <div class="info-value">{merged['symbol'].nunique()}</div>
                <div class="info-label">股票数量</div>
            </div>
            <div class="info-item">
                <div class="info-value">{merged['date'].min().date()}</div>
                <div class="info-label">起始日期</div>
            </div>
            <div class="info-item">
                <div class="info-value">{merged['date'].max().date()}</div>
                <div class="info-label">结束日期</div>
            </div>
        </div>
        
        <!-- 关键指标摘要 -->
        <h2>🎯 关键指标摘要</h2>
        <div class="summary-grid">
            <div class="summary-card ic">
                <div class="value">{ic_all:.4f}</div>
                <div class="label">IC (信息系数)</div>
            </div>
            <div class="summary-card ls">
                <div class="value">{long_short*100:.3f}%</div>
                <div class="label">多空收益 (Q5-Q1)</div>
            </div>
            <div class="summary-card ir">
                <div class="value">{ic_icir:.2f}</div>
                <div class="label">IC IR (信息比率)</div>
            </div>
        </div>
        
        <!-- IC 分析 -->
        <h2>📈 IC (信息系数) 分析</h2>
        <div class="metrics-grid">
            <div class="metric-box">
                <div class="metric-value">{ic_all:.4f}</div>
                <div class="metric-label">整体 IC</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{ic_mean:.4f}</div>
                <div class="metric-label">滚动 IC 均值</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{ic_std:.4f}</div>
                <div class="metric-label">滚动 IC 标准差</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{ic_icir:.2f}</div>
                <div class="metric-label">IC IR</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{ic_positive*100:.1f}%</div>
                <div class="metric-label">IC 正比例</div>
            </div>
        </div>
        
        <div class="chart-section">
            <div class="chart-title">📊 滚动 IC 时间序列</div>
            {ic_ts_html}
        </div>
        
        <div class="two-charts">
            <div class="chart-section">
                <div class="chart-title">📉 IC 分布直方图</div>
                {ic_dist_html}
            </div>
            <div class="chart-section">
                <div class="chart-title">📅 IC 月度分布</div>
                {heat_html}
            </div>
        </div>
        
        <!-- 分组收益分析 -->
        <h2>💰 分组收益分析</h2>
        <div class="metrics-grid">
            <div class="metric-box">
                <div class="metric-value">{group_returns['Q1']*100:.4f}%</div>
                <div class="metric-label">Q1 (最低) 收益</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{group_returns['Q3']*100:.4f}%</div>
                <div class="metric-label">Q3 (中位) 收益</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{group_returns['Q5']*100:.4f}%</div>
                <div class="metric-label">Q5 (最高) 收益</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{long_short*100:.4f}%</div>
                <div class="metric-label">多空收益差</div>
            </div>
        </div>
        
        <div class="chart-section">
            <div class="chart-title">📊 各分位组平均收益</div>
            {group_html}
        </div>
        
        <div class="chart-section">
            <div class="chart-title">📈 累计收益曲线</div>
            {cum_html}
        </div>
        
        <!-- 分组收益表格 -->
        <h3>📋 详细分组统计</h3>
        <table>
            <tr>
                <th>分位组</th>
                <th>平均收益</th>
                <th>胜率</th>
                <th>样本数</th>
            </tr>
            {''.join(f'''<tr>
                <td><strong>{q}</strong></td>
                <td class="{'positive' if v > 0 else 'negative'}">{v*100:.4f}%</td>
                <td>{(merged[merged['quantile']==q]['future_return']>0).mean()*100:.1f}%</td>
                <td>{(merged['quantile']==q).sum():,}</td>
            </tr>''' for q, v in group_returns.items())}
            <tr class="highlight">
                <td><strong>多空 (Q5-Q1)</strong></td>
                <td class="{'positive' if long_short > 0 else 'negative'}">{long_short*100:.4f}%</td>
                <td>-</td>
                <td>-</td>
            </tr>
        </table>
        
        <!-- 因子统计 -->
        <h2>📊 因子值统计分析</h2>
        <div class="metrics-grid">
            <div class="metric-box">
                <div class="metric-value">{merged['factor'].mean():.4f}</div>
                <div class="metric-label">均值</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{merged['factor'].std():.4f}</div>
                <div class="metric-label">标准差</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{merged['factor'].min():.4f}</div>
                <div class="metric-label">最小值</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{merged['factor'].max():.4f}</div>
                <div class="metric-label">最大值</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{merged['factor'].skew():.4f}</div>
                <div class="metric-label">偏度</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{merged['factor'].kurtosis():.4f}</div>
                <div class="metric-label">峰度</div>
            </div>
        </div>
        
        <div class="chart-section">
            <div class="chart-title">📉 因子值分布</div>
            {factor_dist_html}
        </div>
        
        <!-- 换手率分析 -->
        <h2>🔄 换手率分析</h2>
        <div class="metrics-grid">
            <div class="metric-box">
                <div class="metric-value">{turnover*100:.2f}%</div>
                <div class="metric-label">分位组换手率</div>
            </div>
        </div>
        
        <!-- 结论 -->
        <h2>📝 研究结论</h2>
        <div style="background: #E8EAF6; padding: 25px; border-radius: 12px; margin-top: 20px;">
            <p style="font-size: 16px; line-height: 1.8; color: #1a237e;">
                <strong>1. IC 表现：</strong>
                {'该因子 IC 为 ' + f'{ic_all:.4f}' + ('，呈现正相关，说明过去5日收益高的股票未来收益也倾向更高' if ic_all > 0 else '，因子表现需进一步观察') if ic_all != 0 else ''}
                <br><br>
                <strong>2. 分组收益：</strong>
                {'Q5组（高因子值）明显跑赢Q1组（低因子值），多空组合收益为 ' + f'{long_short*100:.3f}%' if long_short > 0 else '多空组合表现需进一步优化'}
                <br><br>
                <strong>3. 因子稳定性：</strong>
                {'IC IR 为 ' + f'{ic_icir:.2f}' + ('，具有一定的预测能力' if abs(ic_icir) > 0.3 else '，因子稳定性一般，建议进一步优化参数')}
                <br><br>
                <strong>4. 整体评价：</strong>
                {'return_5d 因子在历史数据上表现良好，具有一定的alpha能力，可作为选股因子的参考' if ic_all > 0 and long_short > 0 else '因子整体表现一般，建议结合其他因子使用'}
            </p>
        </div>
        
        <div class="footer">
            <p>Generated by <strong>QuantFactor System</strong> | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Data Source: TimescaleDB (factor_return_5d)</p>
        </div>
    </div>
</body>
</html>'''
            
            # 保存报告
            output_path = f'output/factors/{output_file}'
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            print(f"\n✅ 完整报告已生成: {output_path}")
            
            # 列出所有报告
            print("\n" + "="*60)
            print("📁 生成的报告:")
            print("="*60)
            import os
            for f in sorted(os.listdir('output/factors')):
                if f.endswith('.html'):
                    print(f"   📄 {f}")
                    
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    create_full_report()
