"""
使用数据库真实的 factor_return_5d 数据生成报告
"""

import sys
sys.path.insert(0, '/Users/xinzhan/.openclaw/workspace')

from quant_factor_system.data import TimescaleDB
from quant_factor_system.factors.report import FactorReportGenerator
import pandas as pd
import numpy as np
from datetime import datetime


def main():
    print("="*60)
    print("🎯 使用数据库真实因子数据生成报告")
    print("="*60)
    
    db = TimescaleDB()
    
    try:
        with db.connection() as conn:
            cursor = conn.cursor()
            
            print(f"\n{'='*60}")
            print(f"📊 处理因子: factor_return_5d")
            print("="*60)
            
            # 获取因子数据 - 使用较大时间范围
            print(f"\n📥 从数据库加载因子数据...")
            cursor.execute("""
                SELECT symbol, time::date as date, value 
                FROM factor_return_5d
                ORDER BY symbol, date
                LIMIT 500000
            """)
            factor_rows = cursor.fetchall()
            
            if not factor_rows:
                print(f"   ❌ 没有因子数据")
                return
            
            print(f"   ✅ 加载 {len(factor_rows):,} 条因子数据")
            
            # 获取股票列表
            symbols = list(set([r[0] for r in factor_rows]))
            print(f"   📈 股票数: {len(symbols)}")
            
            # 获取价格数据（用于计算未来收益）
            print(f"\n📥 加载价格数据...")
            cursor.execute("""
                SELECT symbol, time::date as date, close 
                FROM price_daily
                WHERE symbol = ANY(%s)
                ORDER BY symbol, date
            """, (symbols,))
            price_rows = cursor.fetchall()
            
            print(f"   ✅ 加载 {len(price_rows):,} 条价格数据")
            
            # 转换为 DataFrame
            factor_df = pd.DataFrame(factor_rows, columns=['symbol', 'date', 'factor'])
            factor_df['date'] = pd.to_datetime(factor_df['date'])
            
            price_df = pd.DataFrame(price_rows, columns=['symbol', 'date', 'close'])
            price_df['date'] = pd.to_datetime(price_df['date'])
            
            print(f"\n📊 准备分析数据...")
            
            # 合并因子和价格
            merged = factor_df.merge(price_df, on=['symbol', 'date'])
            merged = merged.sort_values(['symbol', 'date'])
            
            print(f"   ✅ 合并后: {len(merged):,} 条记录")
            print(f"   📅 日期范围: {merged['date'].min().date()} ~ {merged['date'].max().date()}")
            
            # 计算未来收益（未来1日）
            merged['future_return'] = merged.groupby('symbol')['close'].pct_change().shift(-1)
            
            # 去除无效值
            merged = merged.replace([np.inf, -np.inf], np.nan)
            merged = merged.dropna(subset=['factor', 'future_return'])
            
            print(f"   ✅ 有效数据: {len(merged):,} 条")
            
            # ===== IC 分析 =====
            print(f"\n📈 计算 IC (信息系数)...")
            
            # 整体 IC
            ic_all = merged['factor'].corr(merged['future_return'])
            print(f"   IC (All): {ic_all:.4f}")
            
            # 滚动 IC
            ic_window = 60
            merged['rolling_ic'] = merged.groupby('symbol').apply(
                lambda x: x['factor'].rolling(ic_window).corr(x['future_return'])
            ).reset_index(level=0, drop=True)
            
            ic_series = merged['rolling_ic'].dropna()
            ic_mean = ic_series.mean()
            ic_std = ic_series.std()
            ic_icir = ic_mean / ic_std if ic_std > 0 else 0
            ic_positive = (ic_series > 0).mean()
            
            print(f"   Rolling IC Mean: {ic_mean:.4f}")
            print(f"   Rolling IC Std: {ic_std:.4f}")
            print(f"   IC IR: {ic_icir:.2f}")
            print(f"   IC Positive %: {ic_positive*100:.1f}%")
            
            # ===== 分组收益分析 =====
            print(f"\n💰 计算分组收益...")
            
            merged['quantile'] = pd.qcut(merged['factor'], q=5, labels=['Q1', 'Q2', 'Q3', 'Q4', 'Q5'], duplicates='drop')
            group_returns = merged.groupby('quantile')['future_return'].mean()
            
            print(f"   Q1 (低): {group_returns.get('Q1', 0)*100:.4f}%")
            print(f"   Q5 (高): {group_returns.get('Q5', 0)*100:.4f}%")
            print(f"   Long-Short: {(group_returns.get('Q5', 0) - group_returns.get('Q1', 0))*100:.4f}%")
            
            # ===== 换手率 =====
            print(f"\n🔄 计算换手率...")
            turnover = (merged['quantile'] != merged['quantile'].shift(1)).mean()
            print(f"   Quantile Turnover: {turnover*100:.2f}%")
            
            # ===== 因子统计 =====
            print(f"\n📊 因子统计...")
            print(f"   Mean: {merged['factor'].mean():.4f}")
            print(f"   Std: {merged['factor'].std():.4f}")
            print(f"   Skew: {merged['factor'].skew():.4f}")
            
            # ===== 生成 HTML 报告 =====
            print(f"\n📝 生成 HTML 报告...")
            
            # 准备数据
            factor_stats = {
                'mean': float(merged['factor'].mean()),
                'std': float(merged['factor'].std()),
                'min': float(merged['factor'].min()),
                'max': float(merged['factor'].max()),
                'skew': float(merged['factor'].skew()) if len(merged) > 10 else 0,
                'count': len(merged),
            }
            
            ic_analysis = {
                'ic_all': ic_all,
                'ic_mean': ic_mean,
                'ic_std': ic_std,
                'ic_icir': ic_icir,
                'ic_positive_ratio': ic_positive,
            }
            
            returns_analysis = {
                'group_returns': group_returns.to_dict(),
                'long_short_return': group_returns.get('Q5', 0) - group_returns.get('Q1', 0),
                'quantile_turnover': turnover,
            }
            
            turnover_analysis = {
                'quantile_turnover': turnover,
                'factor_change_mean': 0,
                'factor_change_std': 0,
            }
            
            autocorrelation = {}
            
            # 生成报告
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'return_5d_real_{timestamp}.html'
            
            # 准备表格行
            table_rows = ""
            for q, v in group_returns.items():
                color_class = "positive" if v > 0 else "negative"
                count = (merged['quantile'] == q).sum()
                table_rows += f'<tr><td>{q}</td><td class="{color_class}">{v*100:.4f}%</td><td>{count:,}</td></tr>'
            
            ls_return = returns_analysis['long_short_return']
            ls_class = "positive" if ls_return > 0 else "negative"
            
            # 创建简化版报告
            html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>return_5d - Factor Research Report</title>
    <style>
        body {{ font-family: 'Segoe UI'; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
        h1 {{ color: #1976D2; border-bottom: 3px solid #1976D2; padding-bottom: 10px; }}
        h2 {{ color: #424242; margin-top: 30px; }}
        .summary-box {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 20px 0; }}
        .summary-item {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
        .summary-value {{ font-size: 28px; font-weight: bold; }}
        .summary-label {{ font-size: 14px; margin-top: 5px; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 20px 0; }}
        .metric {{ background: #E3F2FD; padding: 15px; border-radius: 8px; text-align: center; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #1976D2; }}
        .metric-label {{ font-size: 12px; color: #666; margin-top: 5px; }}
        .section {{ margin: 40px 0; padding: 20px; background: #FAFAFA; border-radius: 8px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: center; border-bottom: 1px solid #e0e0e0; }}
        th {{ background: #1976D2; color: white; }}
        .positive {{ color: green; }}
        .negative {{ color: red; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 return_5d - Factor Research Report</h1>
        
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3>Factor Information</h3>
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Data Source:</strong> TimescaleDB (factor_return_5d)</p>
            <p><strong>Samples:</strong> {len(merged):,} 条记录</p>
            <p><strong>Date Range:</strong> {merged['date'].min().date()} ~ {merged['date'].max().date()}</p>
        </div>
        
        <!-- 关键指标摘要 -->
        <div class="summary-box">
            <div class="summary-item">
                <div class="summary-value">{ic_all:.4f}</div>
                <div class="summary-label">IC (All)</div>
            </div>
            <div class="summary-item">
                <div class="summary-value">{ls_return*100:.2f}%</div>
                <div class="summary-label">Long-Short Return</div>
            </div>
            <div class="summary-item">
                <div class="summary-value">{ic_icir:.2f}</div>
                <div class="summary-label">IC IR</div>
            </div>
        </div>
        
        <!-- IC 分析 -->
        <div class="section">
            <h2>Information Coefficient (IC) Analysis</h2>
            <div class="metric-grid">
                <div class="metric">
                    <div class="metric-value">{ic_all:.4f}</div>
                    <div class="metric-label">IC (All)</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{ic_mean:.4f}</div>
                    <div class="metric-label">Rolling IC Mean</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{ic_std:.4f}</div>
                    <div class="metric-label">Rolling IC Std</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{ic_icir:.2f}</div>
                    <div class="metric-label">IC IR</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{ic_positive*100:.1f}%</div>
                    <div class="metric-label">IC Positive %</div>
                </div>
            </div>
        </div>
        
        <!-- 分组收益分析 -->
        <div class="section">
            <h2>Returns Analysis by Quantile</h2>
            <table>
                <tr>
                    <th>Quantile</th>
                    <th>Mean Return</th>
                    <th>Count</th>
                </tr>
                {table_rows}
                <tr style="background: #E3F2FD; font-weight: bold;">
                    <td>Long-Short</td>
                    <td class="{ls_class}">{ls_return*100:.4f}%</td>
                    <td>-</td>
                </tr>
            </table>
        </div>
        
        <!-- 换手率分析 -->
        <div class="section">
            <h2>Turnover Analysis</h2>
            <div class="metric-grid">
                <div class="metric">
                    <div class="metric-value">{turnover*100:.2f}%</div>
                    <div class="metric-label">Quantile Turnover</div>
                </div>
            </div>
        </div>
        
        <!-- 因子统计 -->
        <div class="section">
            <h2>Factor Statistics</h2>
            <div class="metric-grid">
                <div class="metric">
                    <div class="metric-value">{factor_stats['count']:,}</div>
                    <div class="metric-label">Samples</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{factor_stats['mean']:.4f}</div>
                    <div class="metric-label">Mean</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{factor_stats['std']:.4f}</div>
                    <div class="metric-label">Std</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{factor_stats['skew']:.4f}</div>
                    <div class="metric-label">Skewness</div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by QuantFactor System</p>
        </div>
    </div>
</body>
</html>'''
            
            # 保存报告
            output_path = f'output/factors/{output_file}'
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            print(f"\n✅ 报告已生成: {output_path}")
    
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("📁 生成的报告:")
    print("="*60)
    
    import os
    for f in sorted(os.listdir('output/factors')):
        if f.endswith('.html') and 'return_5d' in f:
            print(f"   📄 {f}")


if __name__ == '__main__':
    main()
