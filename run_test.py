#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
量化因子系统 - 完整功能测试
"""

import subprocess
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

print("\n" + "="*70)
print("🚀 量化因子系统 - 完整功能测试")
print("="*70)

# 测试脚本
test_script = '''
import sys
sys.path.insert(0, "''' + PROJECT_ROOT + '''")
import pandas as pd
import numpy as np

print("1. 测试模块导入...")
from quant_factor_system import (
    Factor, FactorSystem,
    MomentumFactor, ValueFactor, QualityFactor,
    BarraSizeFactor, BetaFactor,
    DataProcessor, FactorNeutralizer,
    BacktestConfig, FactorEvaluator, ICAnalyzer,
    TransactionCostCalculator,
    FactorDashboard
)
print("   ✅ 所有模块导入成功")

print("")
print("2. 测试因子计算...")
system = FactorSystem(name="Test")
system.add_factor(MomentumFactor(20), 1.0)
system.add_factor(ValueFactor("pe"), 1.0)
print("   ✅ 因子系统创建成功")
print("   因子数:", len(system.factors))

print("")
print("3. 测试数据处理...")
np.random.seed(42)
dates = pd.date_range("2023-01-01", periods=100, freq="B")
data = pd.DataFrame({
    "symbol": "TEST",
    "close": np.cumsum(np.random.randn(100) * 2 + 0.05) + 100,
    "pct_chg": np.random.randn(100) * 2,
}, index=dates)

processor = DataProcessor()
df_clean, stats = processor.filter_limit_stocks(data.copy(), remove=True)
print("   ✅ 数据处理成功")

print("")
print("4. 测试评估配置...")
config = BacktestConfig(
    num_groups=5,
    winsorize=True,
    neutralize_market_cap=True,
    commission_rate=0.001
)
print("   ✅ 配置创建成功")

print("")
print("5. 测试交易成本...")
calculator = TransactionCostCalculator(config)
cost = calculator.calculate_total_cost(1000000, 0.2)
print("   ✅ 交易成本:", round(cost["total_cost"], 2), "元")

print("")
print("="*70)
print("✅ 所有功能测试通过!")
print("="*70)
print("")
print("📁 项目结构:")
print("""
quant_factor_system/
├── core/              # 核心类
├── factors/           # 因子模块
│   ├── basic/        # 基础因子
│   └── barra/        # Barra因子
├── data/             # 数据模块
│   ├── source/       # 数据源
│   └── processor/   # 数据处理
├── evaluation/       # 评估模块
├── trading/          # 交易模块
├── automation/       # 自动化模块
└── visualization/    # 可视化模块
""")
'''

# 运行测试
cmd = 'export PYTHONPATH="%s:$PYTHONPATH" && /Library/Developer/CommandLineTools/usr/bin/python3 -c "%s"' % (PROJECT_ROOT, test_script.replace('"', '\\"'))
result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=PROJECT_ROOT)
print(result.stdout)
if result.stderr and "Traceback" in result.stderr:
    print("错误:")
    print(result.stderr[-600:])
