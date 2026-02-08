#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
量化因子系统 - 完整测试
支持真实A股数据和模拟数据
"""

import sys
import os
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 测试脚本
TEST_CODE = '''
import sys
sys.path.insert(0, "''' + PROJECT_ROOT + '''")
import pandas as pd
import numpy as np

print("")
print("="*70)
print("🚀 量化因子系统 - 完整测试")
print("="*70)

# ========== 1. 模块导入 ==========
print("")
print("📦 Step 1: 模块导入...")
from quant_factor_system import (
    FactorSystem, Factor,
    MomentumFactor, ValueFactor, QualityFactor,
    BarraSizeFactor, BetaFactor,
    DataProcessor, FactorNeutralizer,
    BacktestConfig, FactorEvaluator, ICAnalyzer,
    TransactionCostCalculator,
    get_a_stock_data
)
print("   ✅ 所有模块导入成功")

# ========== 2. 创建测试数据 ==========
print("")
print("📊 Step 2: 创建测试数据...")

np.random.seed(42)
dates = pd.date_range("2023-01-01", periods=500, freq="B")
n = len(dates)
stocks = ["STOCK_%%03d" %% i for i in range(1, 51)]
all_data = []

for stock in stocks:
    trend = np.linspace(0.01, 0.02, n)
    noise = np.random.randn(n) * 0.02
    returns = trend + noise
    
    # 添加涨跌停
    returns[np.random.choice(n, n//50)] = 0.10  # 涨停
    returns[np.random.choice(n, n//50)] = -0.10  # 跌停
    
    prices = 100 * np.cumprod(1 + returns)
    
    df = pd.DataFrame({
        "symbol": stock,
        "close": prices,
        "pct_chg": returns * 100,
        "pe": np.random.uniform(10, 50, n),
        "pb": np.random.uniform(1, 10, n),
        "roe": np.random.uniform(0.05, 0.25, n),
        "market_cap": prices * np.random.uniform(1e6, 1e7, n),
        "volume": np.random.randint(1e6, 1e8, n),
        "turnover": np.random.uniform(0.001, 0.05, n),
        "industry": np.random.choice(["银行", "医药", "消费", "科技", "制造"], n),
    }, index=dates)
    
    all_data.append(df)

data = pd.concat(all_data)
print("   ✅ 创建数据: %%d 条, %%d 只股票" %% (len(data), data["symbol"].nunique()))

# ========== 3. 涨跌停过滤 ==========
print("")
print("🚦 Step 3: 涨跌停过滤...")

processor = DataProcessor()
df_clean, stats = processor.filter_limit_stocks(data.copy(), remove=True)
print("   原始数据: %%d 条" %% len(data))
print("   涨停数量: %%d (%%.2f%%)" %% (stats["limit_up_count"], stats["limit_up_ratio"]))
print("   跌停数量: %%d (%%.2f%%)" %% (stats["limit_down_count"], stats["limit_down_ratio"]))
print("   过滤后: %%d 条 (%%.1f%%)" %% (len(df_clean), len(df_clean)/len(data)*100))

# ========== 4. 因子计算 ==========
print("")
print("🔢 Step 4: 因子计算...")

system = FactorSystem(name="TestSystem")
system.add_factor(MomentumFactor(20), 1.0)
system.add_factor(ValueFactor("pe"), 1.0)
system.add_factor(QualityFactor("roe"), 1.0)
system.add_factor(BarraSizeFactor(), 1.0)

factor_values = system.calculate_all(df_clean)
print("   因子数量: %%d" %% len(system.factors))
print("   因子列表: %%s" %% ", ".join(system.factors.keys()))

# ========== 5. 中性化 ==========
print("")
print("⚖️ Step 5: 因子中性化...")

neutralizer = FactorNeutralizer()
momentum = df_clean.groupby("symbol")["close"].pct_change(20)
m_cap = df_clean["market_cap"]

m = momentum.dropna()
cap = m_cap.loc[m.index]
neut = neutralizer.neutralize_market_cap(m, cap)

print("   原始均值: %%.6f" %% m.mean())
print("   中性化后: %%.6f" %% neut.mean())
print("   (中性化后均值接近0)")

# ========== 6. 因子评估 ==========
print("")
print("📈 Step 6: 因子评估...")

config = BacktestConfig(
    num_groups=5,
    winsorize=True,
    standardize=True,
    neutralize_market_cap=True,
    commission_rate=0.001,
    slippage_rate=0.001
)

evaluator = FactorEvaluator(config)

returns = df_clean.groupby("symbol")["close"].pct_change().dropna()

results = evaluator.evaluate_multiple(
    factor_values,
    returns,
    df_clean["market_cap"],
    df_clean["industry"]
)

print("   评估因子: %%d" %% len(results))
print("")
print("   📊 IC分析结果:")
print("   " + "-"*60)
print("   %%-12s %%-10s %%-10s %%-10s" %% ("因子", "IC", "IC_IR", "胜率"))
print("   " + "-"*60)

for name, r in results.items():
    status = "OK" if abs(r.ic) > 0.03 else ("~" if abs(r.ic) > 0 else "X")
    print("   %%-12s %%-10s %%-10s %%-10s" %% (
        "%%s" %% name,
        "%%.4f" %% r.ic,
        "%%.4f" %% r.ic_ir,
        "%%.2f%%" %% (r.ic_sign_ratio*100)
    ))

# ========== 7. 交易成本 ==========
print("")
print("💰 Step 7: 交易成本计算...")

calculator = TransactionCostCalculator(config)
cost = calculator.calculate_total_cost(1000000, 0.2)
print("   组合规模: 1,000,000 元")
print("   换手率: 20%%")
print("   佣金: %.2f 元" %% cost["commission"])
print("   滑点: %.2f 元" %% cost["slippage"])
print("   总成本: %.2f 元" %% cost["total_cost"])

# ========== 8. 高级统计 ==========
print("")
print("📉 Step 8: 高级统计分析...")

from quant_factor_system.evaluation import calculate_ic_stats, calculate_ic_decay

ic = pd.Series(np.random.randn(100))
ic_stats = calculate_ic_stats(ic)

print("   IC统计:")
print("     均值: %.4f" %% ic_stats["ic_mean"])
print("     t-stat: %.4f" %% ic_stats["t_statistic"])
print("     p-value: %.4f" %% ic_stats["p_value"])
print("     95%%置信区间: [%.4f, %.4f]" %% (ic_stats["ci_95_lower"], ic_stats["ci_95_upper"]))

# ========== 完成 ==========
print("")
print("="*70)
print("✅ 完整测试通过!")
print("="*70)
print("")
print("📝 说明:")
print("   - 当前使用模拟数据测试")
print("   - 真实A股数据: get_a_stock_data('000001', '2023-01-01', '2024-12-31')")
print("   - 安装AkShare: pip install akshare")
print("")
print("📁 项目结构:")
print("""
quant_factor_system/
├── core/              # 核心类
├── factors/           # 因子模块
│   ├── basic/       # 基础因子
│   └── barra/       # Barra因子
├── data/             # 数据模块
│   ├── source/      # 数据源
│   └── processor/   # 数据处理
├── evaluation/        # 评估模块
├── automation/       # 自动化模块
└── visualization/    # 可视化模块
""")
'''

# 运行测试
cmd = 'export PYTHONPATH="%s:$PYTHONPATH" && /Library/Developer/CommandLineTools/usr/bin/python3 -c "%s"' % (PROJECT_ROOT, TEST_CODE.replace('"', '\\"').replace('\\n', ' '))
result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=PROJECT_ROOT)

print(result.stdout)
if result.stderr and "Traceback" in result.stderr:
    print("错误:")
    print(result.stderr[-800:])
