#!/usr/bin/env python3
"""
生成完整的因子研究报告 - 含图表可视化
"""

import sys
sys.path.insert(0, '/Users/xinzhan/.openclaw/workspace')

from quant_factor_system.data import TimescaleDB
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import os

def main():
    print("="*60)
    print("生成完整的因子研究报告")
    print("="*60)
    
    db = TimescaleDB()
    
    try:
        with db.connection() as conn:
            cursor = conn.cursor()
            
            print("\n加载数据...")
            
            # 获取因子数据
            cursor.execute("""
                SELECT symbol, time::date as date, value 
                FROM factor_return_5d
                ORDER BY symbol, date LIMIT 500000
            """)
            factor_rows = cursor.fetchall()
            print(f"  因子数据: {len(factor_rows):,} 条")
            
            symbols = list(set([r[0] for r in factor_rows]))
            
            # 获取价格数据
            cursor.execute("""
                SELECT symbol, time::date as date, close 
                FROM price_daily WHERE symbol = ANY(%s) ORDER BY symbol, date
            """, (symbols,))
            price_rows = cursor.fetchall()
            print(f"  价格数据: {len(price_rows):,} 条")
            
            # 转换
            factor_df = pd.DataFrame(factor_rows, columns=['symbol', 'date', 'factor'])
            factor_df['date'] = pd.to_datetime(factor_df['date'])
            
            price_df = pd.DataFrame(price_rows, columns=['symbol', 'date', 'close'])
            price_df['date'] = pd.to_datetime(price_df['date'])
            
            # 合并
            merged = factor_df.merge(price_df, on=['symbol', 'date']).sort_values(['symbol', 'date'])
            merged['future_return'] = merged.groupby('symbol')['close'].pct_change().shift(-1)
            merged = merged.replace([np.inf, -np.inf], np.nan).dropna()
            print(f"  有效数据: {len(merged):,} 条")
            
            # 分析
            ic_all = merged['factor'].corr(merged['future_return'])
            merged['rolling_ic'] = merged.groupby('symbol').apply(
                lambda x: x['factor'].rolling(60).corr(x['future_return'])
            ).reset_index(level=0, drop=True)
            
            merged['quantile'] = pd.qcut(merged['factor'], 5, labels=['Q1','Q2','Q3','Q4','Q5'], duplicates='drop')
            group_returns = merged.groupby('quantile')['future_return'].mean()
            long_short = group_returns['Q5'] - group_returns['Q1']
            turnover = (merged['quantile'] != merged['quantile'].shift(1)).mean()
            
            ic_series = merged['rolling_ic'].dropna()
            ic_mean = ic_series.mean()
            ic_std = ic_series.std()
            ic_icir = ic_mean / ic_std if ic_std > 0 else 0
            
            print("\n生成图表...")
            
            # 1. IC时间序列
            ic_ts = merged.groupby('date')['rolling_ic'].mean().dropna()
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(x=ic_ts.index, y=ic_ts.values, line=dict(color='#2196F3', width=1), name='Rolling IC'))
            fig1.add_hline(y=0, line_color='black')
            fig1.update_layout(title='Rolling IC Time Series', height=350, template='plotly_white')
            ic_ts_html = fig1.to_html(full_html=False, include_plotlyjs='cdn')
            
            # 2. IC分布
            fig2 = go.Figure()
            fig2.add_trace(go.Histogram(x=ic_series.values, nbinsx=50, marker_color='#2196F3'))
            fig2.add_vline(x=ic_all, line_dash='dash', line_color='red')
            fig2.update_layout(title='IC Distribution', height=350, template='plotly_white')
            ic_dist_html = fig2.to_html(full_html=False, include_plotlyjs='cdn')
            
            # 3. 分组收益
            colors = ['#ef5350', '#ff9800', '#ffee58', '#66bb6a', '#26a69a']
            fig3 = go.Figure()
            fig3.add_trace(go.Bar(x=group_returns.index, y=group_returns.values*100, marker_color=colors,
                text=[f'{v*100:.3f}%' for v in group_returns.values], textposition='outside'))
            fig3.add_hline(y=0, line_color='black')
            fig3.update_layout(title='Group Returns', height=350, template='plotly_white')
            group_html = fig3.to_html(full_html=False, include_plotlyjs='cdn')
            
            # 4. 因子分布
            fig4 = go.Figure()
            fig4.add_trace(go.Histogram(x=merged['factor'].values, nbinsx=50, marker_color='#7E57C2'))
            fig4.update_layout(title='Factor Distribution', height=350, template='plotly_white')
            factor_html = fig4.to_html(full_html=False, include_plotlyjs='cdn')
            
            # 5. 累计收益
            fig5 = go.Figure()
            for q in ['Q1', 'Q3', 'Q5']:
                q_data = merged[merged['quantile']==q].sort_values('date')
                cum = q_data.groupby('date')['future_return'].mean().cumprod() - 1
                fig5.add_trace(go.Scatter(x=cum.index, y=cum.values, mode='lines', name=q, line=dict(width=2)))
            fig5.update_layout(title='Cumulative Returns', height=350, template='plotly_white')
            cum_html = fig5.to_html(full_html=False, include_plotlyjs='cdn')
            
            print("\n生成HTML报告...")
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'return_5d_full_{timestamp}.html'
            
            html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>return_5d 因子研究报告</title>
    <style>
        body {{ font-family: 'Segoe UI'; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea, #764ba2); min-height: 100vh; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; padding: 40px; border-radius: 16px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }}
        h1 {{ color: #1a237e; border-bottom: 4px solid #3f51b5; padding-bottom: 15px; font-size: 32px; }}
        h2 {{ color: white; background: linear-gradient(90deg, #3f51b5, #5c6bc0); padding: 15px; border-radius: 8px; margin-top: 40px; font-size: 24px; }}
        .header {{ background: linear-gradient(135deg, #1a237e, #3949ab); color: white; padding: 30px; border-radius: 12px; margin: 20px 0; display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; text-align: center; }}
        .summary {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 30px 0; }}
        .card {{ padding: 25px; border-radius: 12px; text-align: center; color: white; }}
        .card.ic {{ background: linear-gradient(135deg, #2196F3, #1976D2); }}
        .card.ls {{ background: linear-gradient(135deg, #4CAF50, #388E3C); }}
        .card.ir {{ background: linear-gradient(135deg, #FF9800, #F57C00); }}
        .card .val {{ font-size: 36px; font-weight: bold; }}
        .card .lbl {{ font-size: 16px; margin-top: 10px; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 20px 0; }}
        .metric {{ background: #E8EAF6; padding: 20px; border-radius: 10px; text-align: center; }}
        .metric .v {{ font-size: 28px; font-weight: bold; color: #3f51b5; }}
        .metric .l {{ font-size: 14px; color: #5c6bc0; margin-top: 8px; }}
        .chart {{ margin: 30px 0; padding: 25px; background: #FAFAFA; border-radius: 12px; }}
        .chart h3 {{ color: #303f9f; margin-bottom: 20px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 25px 0; }}
        th, td {{ padding: 15px; text-align: center; border-bottom: 2px solid #E0E0E0; }}
        th {{ background: linear-gradient(90deg, #3f51b5, #5c6bc0); color: white; }}
        tr:hover {{ background: #E8EAF6; }}
        .pos {{ color: #2E7D32; font-weight: bold; }}
        .neg {{ color: #C62828; font-weight: bold; }}
        .two {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        .footer {{ margin-top: 40px; padding-top: 25px; border-top: 3px solid #3f51b5; color: #5c6bc0; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>return_5d 因子研究报告</h1>
        
        <div class="header">
            <div><div class="info-value">{len(merged):,}</div><div class="info-label">样本数</div></div>
            <div><div class="info-value">{merged['symbol'].nunique()}</div><div class="info-label">股票数</div></div>
            <div><div class="info-value">{merged['date'].min().date()}</div><div class="info-label">起始</div></div>
            <div><div class="info-value">{merged['date'].max().date()}</div><div class="info-label">结束</div></div>
        </div>
        
        <h2>关键指标</h2>
        <div class="summary">
            <div class="card ic"><div class="val">{ic_all:.4f}</div><div class="lbl">IC (信息系数)</div></div>
            <div class="card ls"><div class="val">{long_short*100:.3f}%</div><div class="lbl">多空收益</div></div>
            <div class="card ir"><div class="val">{ic_icir:.2f}</div><div class="lbl">IC IR</div></div>
        </div>
        
        <h2>IC 分析</h2>
        <div class="metrics">
            <div class="metric"><div class="v">{ic_all:.4f}</div><div class="l">整体IC</div></div>
            <div class="metric"><div class="v">{ic_mean:.4f}</div><div class="l">滚动IC均值</div></div>
            <div class="metric"><div class="v">{ic_std:.4f}</div><div class="l">滚动IC标准差</div></div>
            <div class="metric"><div class="v">{ic_icir:.2f}</div><div class="l">IC IR</div></div>
        </div>
        
        <div class="chart"><h3>滚动IC时间序列</h3>{ic_ts_html}</div>
        
        <div class="two">
            <div class="chart"><h3>IC分布</h3>{ic_dist_html}</div>
            <div class="chart"><h3>因子分布</h3>{factor_html}</div>
        </div>
        
        <h2>分组收益分析</h2>
        <div class="metrics">
            <div class="metric"><div class="v">{group_returns['Q1']*100:.4f}%</div><div class="l">Q1收益</div></div>
            <div class="metric"><div class="v">{group_returns['Q5']*100:.4f}%</div><div class="l">Q5收益</div></div>
            <div class="metric"><div class="v">{long_short*100:.4f}%</div><div class="l">多空差</div></div>
        </div>
        
        <div class="chart"><h3>各分位组收益</h3>{group_html}</div>
        <div class="chart"><h3>累计收益曲线</h3>{cum_html}</div>
        
        <h2>分组统计表</h2>
        <table>
            <tr><th>分位</th><th>平均收益</th><th>胜率</th><th>样本数</th></tr>
            <tr><td><strong>Q1</strong></td><td class="neg">{group_returns['Q1']*100:.4f}%</td><td>{(merged[merged['quantile']=='Q1']['future_return']>0).mean()*100:.1f}%</td><td>{(merged['quantile']=='Q1').sum():,}</td></tr>
            <tr><td><strong>Q2</strong></td><td>{group_returns['Q2']*100:.4f}%</td><td>{(merged[merged['quantile']=='Q2']['future_return']>0).mean()*100:.1f}%</td><td>{(merged['quantile']=='Q2').sum():,}</td></tr>
            <tr><td><strong>Q3</strong></td><td>{group_returns['Q3']*100:.4f}%</td><td>{(merged[merged['quantile']=='Q3']['future_return']>0).mean()*100:.1f}%</td><td>{(merged['quantile']=='Q3').sum():,}</td></tr>
            <tr><td><strong>Q4</strong></td><td>{group_returns['Q4']*100:.4f}%</td><td>{(merged[merged['quantile']=='Q4']['future_return']>0).mean()*100:.1f}%</td><td>{(merged['quantile']=='Q4').sum():,}</td></tr>
            <tr style="background:#C5CAE9;font-weight:bold"><td><strong>多空</strong></td><td class="pos">{long_short*100:.4f}%</td><td>-</td><td>-</td></tr>
        </table>
        
        <h2>因子统计</h2>
        <div class="metrics">
            <div class="metric"><div class="v">{merged['factor'].mean():.4f}</div><div class="l">均值</div></div>
            <div class="metric"><div class="v">{merged['factor'].std():.4f}</div><div class="l">标准差</div></div>
            <div class="metric"><div class="v">{merged['factor'].min():.4f}</div><div class="l">最小</div></div>
            <div class="metric"><div class="v">{merged['factor'].max():.4f}</div><div class="l">最大</div></div>
            <div class="metric"><div class="v">{merged['factor'].skew():.4f}</div><div class="l">偏度</div></div>
            <div class="metric"><div class="v">{turnover*100:.1f}%</div><div class="l">换手率</div></div>
        </div>
        
        <div class="footer">
            <p>Generated by QuantFactor System | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Data Source: TimescaleDB (factor_return_5d)</p>
        </div>
    </div>
</body>
</html>'''
            
            # 保存
            os.makedirs('output/factors', exist_ok=True)
            output_path = f'output/factors/{output_file}'
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            print(f"\n✅ 完整报告已生成: {output_path}")
            
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
