# 量化因子系统 - 经典场景示例代码

> 生成时间: 2026-02-09

本文档包含量化因子系统的经典使用场景，每个场景都有完整的 Python 代码示例。

---

## 📁 生成图片

| 文件 | 说明 |
|------|------|
| `场景1_因子评估结果.png` | IC 分析、分组收益、统计指标 |
| `场景2_相关性热力图.png` | 因子相关性、IC 相关性 |
| `场景3_Pipeline结果.png` | Pipeline 构建、多因子组合 |
| `场景4_风险指标.png` | 收益曲线、回撤、风险指标 |

---

## 📊 场景 1: 因子评估

### 代码

```python
from quant_factor_system.evaluation import EnhancedEvaluator
from quant_factor_system.evaluation.risk_metrics import RiskAnalyzer

# 创建评估器
evaluator = EnhancedEvaluator(num_groups=5)

# 运行评估
result = evaluator.evaluate(
    factor_name='Momentum',
    factor=factor_data,      # MultiIndex (date, symbol) -> factor values
    returns=returns_data    # MultiIndex (date, symbol) -> returns
)

# 获取结果
print(f"IC: {result.ic:.4f}")
print(f"IC IR: {result.ic_ir:.4f}")
print(f"胜率: {result.ic_sign_ratio:.2%}")
print(f"多空收益: {result.long_short_return:.4f}")
print(f"IC 序列: {result.ic_series}")
print(f"IC 衰减: {result.ic_decay}")
```

### 输出示例

```
IC: 0.0245
IC IR: 0.82
胜率: 62.5%
多空收益: 5.2%
```

---

## 📈 场景 2: 相关性热力图

### 代码

```python
from quant_factor_system.evaluation.enhanced import FactorCorrelator

# 创建相关性分析器
correlator = FactorCorrelator(threshold=0.7)

# 获取因子数据
factors = {
    'Momentum': momentum_factor,
    'RSI': rsi_factor,
    'PE': pe_factor,
    'ROE': roe_factor,
    'Size': size_factor
}

# 计算 IC 相关性
ic_corr = correlator.calculate_ic_correlation(factors, returns)

# 找出高相关对
high_corr = correlator.find_high_correlation(ic_corr)

for f1, f2, corr in high_corr:
    print(f"{f1} <-> {f2}: {corr:.3f}")
```

### 输出示例

```
Momentum <-> Size: 0.85
RSI <-> PE: -0.78
```

---

## 🔧 场景 3: Pipeline 构建

### 代码

```python
from quant_factor_system.pipeline import (
    Pipeline, Momentum, RSI, MovingAverage,
    PercentileFilter
)

# 创建 Pipeline
pipe = Pipeline("MyPipeline")

# 添加因子
pipe.add_factor('momentum', Momentum(window=20))
pipe.add_factor('rsi', RSI(window=14))
pipe.add_factor('ma20', MovingAverage(window=20))

# 设置过滤
top_momentum = PercentileFilter(
    Momentum(window=20),
    min_percentile=80,
    max_percentile=100
)
pipe.set_screen(top_momentum)

# 运行 Pipeline
result = pipe.run(price_data)

# 结果包含:
# - momentum: 动量因子值
# - rsi: RSI 因子值
# - ma20: 移动平均值
# - top_momentum: 过滤掩码
print(result.head())
```

### 输出示例

```
                momentum       rsi      ma20  top_momentum
date       symbol                                   
2024-01-02 SH600000   0.05   45.2   52.3        True
           SZ000001   0.03   52.1   48.5       False
```

---

## 📉 场景 4: 风险指标

### 代码

```python
from quant_factor_system.evaluation.risk_metrics import RiskAnalyzer

# 创建分析器
analyzer = RiskAnalyzer(risk_free_rate=0.03)

# 计算所有风险指标
metrics = analyzer.calculate_all_metrics(returns)

print(f"夏普比率: {metrics.sharpe_ratio:.4f}")
print(f"索提诺比率: {metrics.sortino_ratio:.4f}")
print(f"卡玛比率: {metrics.calmar_ratio:.4f}")
print(f"最大回撤: {metrics.max_drawdown:.4%}")
print(f"VaR (95%): {metrics.value_at_risk:.4%}")
print(f"CVaR (95%): {metrics.conditional_value_at_risk:.4%}")
print(f"年化波动率: {metrics.volatility:.4%}")
```

### 输出示例

```
夏普比率: 1.45
索提诺比率: 2.10
卡玛比率: 0.85
最大回撤: -15.2%
VaR (95%): -2.5%
CVaR (95%): -3.8%
年化波动率: 18.5%
```

---

## 🎲 场景 5: Monte Carlo 模拟

### 代码

```python
from quant_factor_system.visualization import MonteCarloSimulator

# 创建模拟器
mc = MonteCarloSimulator(
    returns=historical_returns,
    sims=1000,           # 模拟次数
    seed=42               # 随机种子
)

# 运行模拟
mc.run()

# 获取统计
stats = mc.get_statistics()

print(f"最终收益均值: {stats['final_returns_mean']:.2%}")
print(f"破产概率: {stats['bust_probability']:.2%}")
print(f"目标达成概率: {stats['goal_probability']:.2%}")

# 获取百分位路径
median_path = mc.get_percentile(0.5)   # 中位数
p5_path = mc.get_percentile(0.05)     # 5% 分位
p95_path = mc.get_percentile(0.95)     # 95% 分位

# 绘制结果
mc.plot(title="Monte Carlo 模拟结果")
```

### 输出示例

```
模拟次数: 1000
模拟天数: 252

最终收益均值: 14.8%
破产概率 (亏损20%): 12.5%
目标达成概率 (盈利50%): 35.2%
```

---

## 📊 场景 6: Tearsheet 报告

### 代码

```python
from quant_factor_system.visualization import TearsheetBuilder

# 创建报告构建器
builder = TearsheetBuilder(
    config=TearSheetConfig(title="动量因子 Tearsheet")
)

# 添加数据
builder.add_ic_series(ic_series)           # IC 序列
builder.add_ic_decay(ic_decay)              # IC 衰减
builder.add_group_returns(group_returns)    # 分组收益
builder.add_turnover(turnover_data)        # 换手率

# 保存 HTML 报告
builder.save_html("factor_tearsheet.html")

# 或渲染显示
builder.render()
```

### 输出

生成包含以下内容的 HTML 报告:
- 📊 因子统计表
- 📈 IC 分析图
- 📉 分组收益图
- 🔄 换手率分析
- 📝 评估结论

---

## 🔗 场景 7: Pandas 扩展

### 代码

```python
from quant_factor_system.visualization import extend_pandas

# 启用 Pandas 扩展
extend_pandas()

# 直接在 Series 上调用
returns.sharpe(rf=0.03)          # 夏普比率
returns.sortino()                 # 索提诺比率
returns.max_drawdown()            # 最大回撤
returns.cagr()                   # 年化收益
returns.volatility()              # 波动率
returns.win_rate()                # 胜率
returns.profit_factor()           # 盈利因子
returns.value_at_risk(0.95)       # VaR
returns.conditional_var(0.95)     # CVaR

# 完整统计
stats = returns.quant.describe()
print(stats)
```

### 输出示例

```
count          252.0
mean            0.02
std             0.015
min            -0.05
max             0.06
cagr            0.15
sharpe          1.45
sortino         2.10
max_drawdown   -0.08
win_rate        0.55
```

---

## 📋 完整使用流程

```python
# 1. 导入模块
from quant_factor_system import FactorSystem
from quant_factor_system.evaluation import EnhancedEvaluator
from quant_factor_system.pipeline import Pipeline, Momentum, RSI
from quant_factor_system.evaluation.risk_metrics import RiskAnalyzer

# 2. 创建因子数据
factor_data = create_factor_data()

# 3. 运行评估
evaluator = EnhancedEvaluator(num_groups=5)
result = evaluator.evaluate('Momentum', factor_data.momentum, factor_data.returns)

# 4. 创建 Pipeline
pipe = Pipeline("MyPipeline")
pipe.add_factor('momentum', Momentum(20))
pipe.add_factor('rsi', RSI(14))
result = pipe.run(price_data)

# 5. 风险分析
analyzer = RiskAnalyzer(rf=0.03)
metrics = analyzer.calculate_all_metrics(returns)

# 6. 生成报告
builder = TearsheetBuilder()
builder.add_ic_series(result.ic_series)
builder.save_html("report.html")

print("✅ 分析完成!")
```

---

## 📁 图片文件位置

所有生成图片保存在:

```
/Users/xinzhan/.openclaw/workspace/examples/
├── 场景1_因子评估结果.png
├── 场景2_相关性热力图.png
├── 场景3_Pipeline结果.png
└── 场景4_风险指标.png
```

---

*文档生成时间: 2026-02-09*
