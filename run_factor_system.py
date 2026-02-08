#!/usr/bin/env python3
# 量化因子系统启动脚本

import subprocess
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

print("\n" + "="*60)
print("🚀 量化因子分析系统启动器")
print("="*60)

# 安装依赖
print("\n📦 安装依赖...")
for dep in ["akshare", "statsmodels", "schedule", "matplotlib"]:
    subprocess.run('/Library/Developer/CommandLineTools/usr/bin/python3 -m pip install %s --quiet' % dep, shell=True)
print("✅ 依赖安装完成")

# 创建Python脚本
script = '''
import sys
sys.path.insert(0, "''' + PROJECT_ROOT + '''")

from quant_factor_system import (
    DataProcessor, FactorNeutralizer, FactorSystem,
    MomentumFactor, ValueFactor, QualityFactor, FactorEvaluator
)
import pandas as pd, numpy as np

print("模块导入成功")

# 创建示例数据
print("创建示例数据...")
np.random.seed(42)
dates = pd.date_range(start="2023-01-01", periods=500, freq="B")
stocks = ["STOCK_%03d" % i for i in range(1, 31)]
all_data = []

for stock in stocks:
    trend = np.linspace(0.01, 0.02, len(dates))
    noise = np.random.randn(len(dates)) * 0.02
    returns = trend + noise
    returns[np.random.choice(len(dates), 10)] = 0.10
    returns[np.random.choice(len(dates), 10)] = -0.10
    prices = 100 * np.cumprod(1 + returns)
    
    df = pd.DataFrame({
        "symbol": stock, "close": prices, "pct_chg": returns * 100,
        "pe": np.random.uniform(10, 50, len(dates)),
        "roe": np.random.uniform(0.05, 0.25, len(dates)),
        "market_cap": prices * np.random.uniform(1e6, 1e7, len(dates)),
        "turnover": np.random.uniform(0.001, 0.05, len(dates)),
        "industry": np.random.choice(["银行", "医药", "消费", "科技", "制造"], len(dates)),
    }, index=dates)
    all_data.append(df)

data = pd.concat(all_data)
print("数据: %d 条, %d 只股票" % (len(data), data["symbol"].nunique()))

# 涨跌停过滤
print("")
print("="*50)
print("涨跌停过滤")
print("="*50)
p = DataProcessor()
df_clean, s = p.filter_limit_stocks(data.copy(), remove=True)
print("涨停: %d (%.2f%%)" % (s["limit_up_count"], s["limit_up_ratio"]))
print("跌停: %d (%.2f%%)" % (s["limit_down_count"], s["limit_down_ratio"]))
print("过滤后: %d 条" % len(df_clean))

# 中性化
print("")
print("="*50)
print("因子中性化")
print("="*50)
n = FactorNeutralizer()
mom = df_clean.groupby("symbol")["close"].pct_change(20)
m = mom.dropna()
cap = df_clean["market_cap"].loc[m.index]
neut = n.neutralize_market_cap(m, cap)
print("原始动量 - 均值: %.6f, 标准差: %.6f" % (m.mean(), m.std()))
print("中性化后 - 均值: %.6f, 标准差: %.6f" % (neut.mean(), neut.std()))

# 因子评估
print("")
print("="*50)
print("因子评估")
print("="*50)
sys1 = FactorSystem(name="专业系统")
sys1.add_factor(MomentumFactor(20), 1.0)
sys1.add_factor(ValueFactor("pe"), 1.0)
sys1.add_factor(QualityFactor("roe"), 1.0)

f = sys1.calculate_all(df_clean)
rets = df_clean.groupby("symbol")["close"].pct_change().dropna()
e = FactorEvaluator(sys1)
ic = e.evaluate_ic(rets)

print("")
print("IC分析结果:")
for name, v in ic.items():
    status = "OK" if v["ic"] > 0.03 else ("~" if v["ic"] > 0 else "X")
    print("  [%s] %s: IC=%.4f, IR=%.4f, 胜率=%.1f%%" % (status, name, v["ic"], v["ic_ir"], v["ic_sign_ratio"]*100))

print("")
print("="*50)
print("完成!")
print("="*50)
'''

# 写临时脚本
with open("/tmp/factor_demo.py", "w") as f:
    f.write(script)

# 运行
cmd = 'export PYTHONPATH="%s:$PYTHONPATH" && /Library/Developer/CommandLineTools/usr/bin/python3 /tmp/factor_demo.py' % PROJECT_ROOT
result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=PROJECT_ROOT)
print(result.stdout)
if result.stderr and "Traceback" in result.stderr:
    print("错误:")
    print(result.stderr[-600:])
