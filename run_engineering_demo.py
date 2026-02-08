#!/usr/bin/env python3
# 工程化因子评估启动脚本

import subprocess
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

print("\n" + "="*70)
print("🚀 工程化因子评估框架启动器")
print("="*70)

# 创建演示脚本
demo_script = '''
import sys
sys.path.insert(0, "''' + PROJECT_ROOT + '''")

from quant_factor_system import (
    BacktestConfig, FactorEvaluator, FactorPreprocessor,
    MomentumFactor, ValueFactor, QualityFactor, FactorSystem
)
import pandas as pd, numpy as np

print("模块导入成功")

# 创建测试数据
print("")
print("="*70)
print("创建测试数据...")
print("="*70)

np.random.seed(42)
dates = pd.date_range("2020-01-01", periods=500, freq="B")
n = len(dates)
stocks = ["STOCK_%%03d" %% i for i in range(1, 51)]
all_data = []

for stock in stocks:
    trend = np.linspace(0.01, 0.02, n)
    noise = np.random.randn(n) * 0.02
    returns = trend + noise
    prices = 100 * np.cumprod(1 + returns)
    
    df = pd.DataFrame({
        "symbol": stock, "close": prices,
        "pe": np.random.uniform(10, 50, n),
        "roe": np.random.uniform(0.05, 0.25, n),
        "market_cap": prices * np.random.uniform(1e6, 1e7, n),
        "industry": np.random.choice(["银行", "医药", "消费", "科技", "制造"], n),
    }, index=dates)
    all_data.append(df)

data = pd.concat(all_data)
print("数据: %%d 条, %%d 只股票" %% (len(data), data["symbol"].nunique()))

# 计算因子
print("")
print("="*70)
print("计算因子...")
print("="*70)

system = FactorSystem(name="Test System")
system.add_factor(MomentumFactor(20), 1.0)
system.add_factor(ValueFactor("pe"), 1.0)
system.add_factor(QualityFactor("roe"), 1.0)

factor_values = system.calculate_all(data)
print("因子: %%d 个" %% len(system.factors))

# 计算收益率
returns = data.groupby("symbol")["close"].pct_change().dropna()

# 配置
print("")
print("="*70)
print("配置参数...")
print("="*70)

config = BacktestConfig(
    num_groups=5,
    winsorize=True,
    standardize=True,
    neutralize_market_cap=True,
    neutralize_industry=True,
    commission_rate=0.001,
    stamp_tax_rate=0.001,
    slippage_rate=0.001
)

print("  分组数: %%d" %% config.num_groups)
print("  手续费率: %.4f" %% config.commission_rate)
print("  印花税率: %.4f" %% config.stamp_tax_rate)
print("  滑点率: %.4f" %% config.slippage_rate)
print("  去极值: %s" % config.winsorize)
print("  市值中性化: %s" % config.neutralize_market_cap)

# 评估
print("")
print("="*70)
print("运行因子评估...")
print("="*70)

evaluator = FactorEvaluator(config)

results = evaluator.evaluate_multiple(
    factor_values, returns, data["market_cap"], data["industry"]
)

# 打印报告
evaluator.print_report()

print("")
print("="*70)
print("完成!")
print("="*70)
'''

# 写临时脚本
with open("/tmp/engineering_demo.py", "w") as f:
    f.write(demo_script)

# 运行
cmd = 'export PYTHONPATH="%s:$PYTHONPATH" && /Library/Developer/CommandLineTools/usr/bin/python3 /tmp/engineering_demo.py' % PROJECT_ROOT
result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=PROJECT_ROOT)

print(result.stdout)
if result.stderr and "Traceback" in result.stderr:
    print("错误:")
    print(result.stderr[-800:])
