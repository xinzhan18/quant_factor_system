#!/usr/bin/env python
"""生成因子IC可视化图表"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import warnings
warnings.filterwarnings('ignore')

# 设置字体
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 读取IC数据
df = pd.read_csv('/tmp/ic_results_2022.csv')
df = df.sort_values('IC', key=abs, ascending=False)

# 创建图表
fig = plt.figure(figsize=(16, 12))

# 1. IC排名柱状图
ax1 = fig.add_subplot(2, 2, 1)
colors = ['#e74c3c' if x < 0 else '#27ae60' for x in df['IC']]
bars = ax1.barh(range(len(df)), df['IC'], color=colors, alpha=0.8)
ax1.set_yticks(range(len(df)))
ax1.set_yticklabels(df['因子'], fontsize=9)
ax1.set_xlabel('IC (Information Coefficient)', fontsize=10)
ax1.set_title('Factor IC Ranking (2022 Training Set)', fontsize=12, fontweight='bold')
ax1.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
ax1.invert_yaxis()
ax1.grid(axis='x', alpha=0.3)

# 添加数值标签
for i, (ic, sig) in enumerate(zip(df['IC'], df['显著'])):
    ax1.text(ic + 0.002 if ic > 0 else ic - 0.002, i, f'{ic:.4f}{sig}', 
             va='center', ha='left' if ic > 0 else 'right', fontsize=8)

# 2. IC分布（按因子类型）
ax2 = fig.add_subplot(2, 2, 2)

def get_type(x):
    if 'momentum' in x:
        return 'Momentum'
    elif 'return' in x:
        return 'Return'
    elif 'dist' in x:
        return 'MA Dist'
    elif 'volatility' in x:
        return 'Volatility'
    elif 'zscore' in x:
        return 'Z-Score'
    return 'Other'

df['Type'] = df['因子'].apply(get_type)
type_ic = df.groupby('Type')['IC'].agg(['mean', 'std', 'count'])
type_ic = type_ic.sort_values('mean', key=abs, ascending=False)

x = range(len(type_ic))
bars = ax2.bar(x, type_ic['mean'], yerr=type_ic['std']/10, capsize=5, 
                color=['#e74c3c' if x < 0 else '#27ae60' for x in type_ic['mean']], alpha=0.8)
ax2.set_xticks(x)
labels = [f'{idx}\\n(n={row["count"]})' for idx, row in type_ic.iterrows()]
ax2.set_xticklabels(labels, fontsize=9)
ax2.set_ylabel('Mean IC', fontsize=10)
ax2.set_title('IC by Factor Type', fontsize=12, fontweight='bold')
ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax2.grid(axis='y', alpha=0.3)

# 3. IC与周期的关系
ax3 = fig.add_subplot(2, 2, 3)

def get_period(x):
    for num in ['5', '10', '20', '60', '120']:
        if f'_{num}' in x:
            return int(num)
    return 0

df['Period'] = df['因子'].apply(get_period)
period_df = df[df['Period'] > 0].copy()

markers = {'momentum': 'o', 'return': 's', 'volatility': '^', 'dist': 'D'}
colors_type = {'momentum': '#3498db', 'return': '#e74c3c', 'volatility': '#27ae60', 'dist': '#9b59b6'}

for ftype in ['momentum', 'return', 'volatility', 'dist']:
    subset = period_df[period_df['因子'].str.contains(ftype)]
    if len(subset) > 1:
        label = {'momentum': 'Momentum', 'return': 'Return', 'volatility': 'Volatility', 'dist': 'MA Distance'}[ftype]
        ax3.plot(subset['Period'], subset['IC'], markers[ftype], 
                label=label, markersize=10, linewidth=2, color=colors_type[ftype])

ax3.set_xlabel('Period (Days)', fontsize=10)
ax3.set_ylabel('IC', fontsize=10)
ax3.set_title('IC vs Period', fontsize=12, fontweight='bold')
ax3.axhline(y=0, color='black', linestyle='--', linewidth=0.5)
ax3.legend(loc='best', fontsize=9)
ax3.grid(alpha=0.3)
ax3.set_xticks([5, 10, 20, 60, 120])

# 4. 因子IC统计摘要
ax4 = fig.add_subplot(2, 2, 4)
ax4.axis('off')

neg_ic = (df['IC'] < 0).sum()
pos_ic = (df['IC'] > 0).sum()
sig_ic = (df['P值'] < 0.001).sum()

summary_text = f"""
╔═══════════════════════════════════════════════════════════════╗
║               Factor IC Summary (2022 Training Set)          ║
╠═══════════════════════════════════════════════════════════════╣
║  📊 Dataset: 1,144,854 records, 4,906 stocks                ║
║  📅 Period: 2022-01-01 to 2022-12-31                        ║
╠═══════════════════════════════════════════════════════════════╣
║  Total Factors: {len(df):<5}                                       ║
║  Significant (p<0.001): {sig_ic} (100%)                          ║
║  Negative IC: {neg_ic} (76%)  → Short-term Reversal           ║
║  Positive IC: {pos_ic} (24%)   → Momentum/Volatility          ║
╠═══════════════════════════════════════════════════════════════╣
║  🏆 Top 5 Factors:                                           ║
║    1. dist_ma10     IC = -0.0404  (MA Distance/Reversal)    ║
║    2. return_1d      IC = -0.0400  (1D Return/Reversal)     ║
║    3. momentum_5     IC = -0.0395  (5D Momentum/Reversal)    ║
║    4. return_5d      IC = -0.0395  (5D Return/Reversal)      ║
║    5. dist_ma60     IC = -0.0379  (MA Distance/Reversal)    ║
╠═══════════════════════════════════════════════════════════════╣
║  💡 Key Insight:                                             ║
║     Short-term reversal effect dominates in 2022             ║
║     Low IC magnitude (-0.02 to -0.04) suggests               ║
║     weak but statistically significant signal                 ║
╚═══════════════════════════════════════════════════════════════╝
"""
ax4.text(0.02, 0.98, summary_text, transform=ax4.transAxes, fontsize=9,
         verticalalignment='top', fontfamily='monospace',
         bbox=dict(boxstyle='round', facecolor='#f0f0f0', alpha=0.8))

plt.tight_layout()
plt.savefig('/tmp/factor_ic_analysis.png', dpi=150, bbox_inches='tight', facecolor='white')
print('✅ 图表已保存到 /tmp/factor_ic_analysis.png')
print('\\n🎉 图表生成完成!')
