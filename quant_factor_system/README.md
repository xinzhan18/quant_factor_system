# 量化因子系统 (Quant Factor System)

<div align="center">

![Version](https://img.shields.io/badge/Version-3.0.0-blue)
![Python](https://img.shields.io/badge/Python-3.9+-green)
![License](https://img.shields.io/badge/License-Apache-yellow)

**A 股多因子量化分析系统**

[English](./README_EN.md) | [中文](./README.md)

</div>

---

## 📋 目录

- [概述](#概述)
- [功能特性](#功能特性)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [核心模块](#核心模块)
- [使用示例](#使用示例)
- [依赖安装](#依赖安装)
- [贡献指南](#贡献指南)
- [更新日志](#更新日志)
- [许可证](#许可证)

---

## 概述

量化因子系统是一个**A 股多因子量化分析平台**，提供完整的因子研究、评估、选股和组合构建功能。

### 核心特性

- ✅ **完整的因子评估框架** (基于 Alphalens)
- ✅ **风险指标分析** (基于 QuantStats)
- ✅ **Pipeline 因子管道** (基于 Zipline)
- ✅ **交互式 Dashboard** (Streamlit)
- ✅ **A 股数据支持** (米筐、Tushare、本地 CSV)
- ✅ **工程化目录结构**

---

## 功能特性

### 1. 因子研究

| 功能 | 说明 |
|------|------|
| 因子计算 | Momentum, RSI, MA, Volatility, Returns |
| 因子组合 | 加权组合、因子变换 (rolling, rank, zscore) |
| 因子过滤 | PercentileFilter, FactorFilter |

### 2. 因子评估

| 功能 | 说明 |
|------|------|
| IC 分析 | IC, ICIR, IC decay, 滚动 IC |
| 分组回测 | 5组/10组分析, 等权/因子加权 |
| 换手率分析 | 分组换手率, 因子自相关 |
| 相关性分析 | 因子相关性, IC 相关性 |

### 3. 风险指标

| 功能 | 说明 |
|------|------|
| 收益指标 | CAGR, 夏普比率, 索提诺比率, 卡玛比率 |
| 风险指标 | 最大回撤, VaR, CVaR |
| 波动率 | 年化波动率, 下行波动率 |
| Monte Carlo | 破产概率, 目标达成概率 |

### 4. 报告输出

| 功能 | 说明 |
|------|------|
| Tearsheet | IC 分析图, 分组收益图, 换手率图 |
| HTML 报告 | 一键导出完整报告 |
| Pandas 扩展 | returns.quant.sharpe() 等 |

---

## 项目结构

```
quant_factor_system/
├── core/                      # 核心类
│   └── base.py               # Factor, FactorSystem 基类
├── factors/                   # 因子模块
│   ├── basic/               # 基础因子
│   │   └── factors.py       # Momentum, Value, Quality 等
│   └── barra/               # Barra 因子
│       └── extended_factors.py
├── data/                     # 数据模块
│   ├── source/              # 数据源
│   ├── processor/           # 数据处理
│   ├── formatter.py         # 数据格式化
│   ├── ricequant_downloader.py  # 米筐数据下载
│   └── csv_importer.py       # CSV 导入
├── evaluation/                # 评估模块
│   ├── factor_evaluator.py  # 基础评估
│   ├── enhanced.py          # 增强评估
│   └── risk_metrics.py       # 风险指标
├── trading/                   # 交易模块
│   └── selector.py           # 选股, 组合构建
├── pipeline/                  # Pipeline 引擎
│   └── pipeline.py          # Pipeline, Factor, Filter
├── automation/                # 自动化
│   └── scheduler.py         # 任务调度
├── visualization/             # 可视化
│   ├── visualization.py     # Dashboard
│   ├── tearsheet.py        # Tearsheet 报告
│   └── pandas_ext.py       # Pandas 扩展
├── storage/                   # 存储
│   └── database.py          # SQLite 数据库
├── dashboard/                 # Streamlit Dashboard
│   ├── Home.py              # 主入口
│   ├── config.py            # 配置
│   └── pages/               # 页面
│       ├── home.py          # 首页
│       ├── factor_evaluation.py  # 因子评估
│       ├── factor_screening.py   # 因子筛选
│       ├── factor_interaction.py # 因子交互
│       ├── pipeline_editor.py   # Pipeline 编辑器
│       ├── stock_selection.py   # 选股
│       └── backtest_history.py  # 历史回测
├── research/                  # 研究
│   ├── templates/           # 因子模板
│   └── workflow.py          # 研究工作流
└── storage/                   # 数据存储
    ├── database/            # SQLite 数据库
    ├── data/               # CSV 数据
    └── cache/              # 缓存
```

---

## 快速开始

### 1. 安装依赖

```bash
pip install pandas numpy scipy matplotlib plotly
pip install streamlit  # 可选，用于 Dashboard
```

### 2. 运行 Dashboard

```bash
cd quant_factor_system/dashboard
streamlit run Home.py
```

### 3. 使用 API

```python
from quant_factor_system import FactorSystem, MomentumFactor
from quant_factor_system.evaluation import EnhancedEvaluator
from quant_factor_system.pipeline import Pipeline, Momentum

# 创建因子系统
system = FactorSystem()
system.add_factor(MomentumFactor(20), weight=1.0)

# 运行评估
evaluator = EnhancedEvaluator()
result = evaluator.evaluate('Momentum', factor_values, returns)

# 使用 Pipeline
pipe = Pipeline("MyPipeline")
pipe.add_factor('momentum', Momentum(window=20))
result = pipe.run(price_data)
```

---

## 核心模块

### FactorSystem - 因子系统

```python
from quant_factor_system import FactorSystem, MomentumFactor, ValueFactor

# 创建系统
system = FactorSystem()

# 添加因子
system.add_factor(MomentumFactor(20), weight=0.5)
system.add_factor(ValueFactor(), weight=0.3)
system.add_factor(QualityFactor(), weight=0.2)

# 计算因子
factors = system.calculate_all(data)
```

### EnhancedEvaluator - 增强评估

```python
from quant_factor_system.evaluation import EnhancedEvaluator

evaluator = EnhancedEvaluator(num_groups=5)

# 完整评估
result = evaluator.evaluate('FactorName', factor_data, returns)

print(f"IC: {result.ic:.4f}")
print(f"IC IR: {result.ic_ir:.4f}")
print(f"胜率: {result.ic_sign_ratio:.2%}")
print(f"多空收益: {result.long_short_return:.4f}")
```

### Pipeline - 因子管道

```python
from quant_factor_system.pipeline import Pipeline, Momentum, RSI, MovingAverage

# 创建 Pipeline
pipe = Pipeline("MyPipeline")
pipe.add_factor('momentum', Momentum(window=20))
pipe.add_factor('rsi', RSI(window=14))
pipe.add_factor('ma20', MovingAverage(window=20))

# 添加过滤器
from quant_factor_system.pipeline import PercentileFilter
pipe.set_screen(PercentileFilter(Momentum(window=20), 80, 100))

# 运行
result = pipe.run(price_data)
```

### RiskMetrics - 风险指标

```python
from quant_factor_system.evaluation import RiskAnalyzer

analyzer = RiskAnalyzer(risk_free_rate=0.03)
metrics = analyzer.calculate_all_metrics(returns)

print(f"夏普比率: {metrics.sharpe_ratio:.4f}")
print(f"最大回撤: {metrics.max_drawdown:.4%}")
print(f"VaR (95%): {metrics.value_at_risk:.4f}")
```

### Tearsheet - 报告生成

```python
from quant_factor_system.visualization import TearsheetBuilder

builder = TearsheetBuilder()
builder.add_ic_series(ic_series)
builder.add_group_returns(group_returns)
builder.save_html('factor_report.html')
```

### Pandas 扩展

```python
from quant_factor_system.visualization import extend_pandas

extend_pandas()

# 直接调用
returns.quant.sharpe()
returns.quant.max_drawdown()
returns.quant.win_rate()
```

---

## 数据格式

### 日线数据 (MultiIndex)

```python
# Index: (date, symbol)
# Columns: open, high, low, close, volume, amount

import pandas as pd

data = pd.DataFrame({
    'open': [10.5, 10.8, ...],
    'high': [11.0, 11.2, ...],
    'low': [10.2, 10.5, ...],
    'close': [10.8, 11.0, ...],
    'volume': [5000000, 6000000, ...],
}, index=pd.MultiIndex.from_tuples([
    ('2024-01-02', '000001.XSHE'),
    ('2024-01-02', '600519.SH'),
    ...
], names=['date', 'symbol']))
```

### 因子数据

```python
# Index: (date, symbol)
# Columns: factor_name, value

factor_data = pd.DataFrame({
    'momentum_20d': [0.05, 0.03, ...],
    'pe': [8.5, 12.3, ...],
    'roe': [0.15, 0.20, ...],
}, index=pd.MultiIndex.from_tuples([
    ('2024-01-02', '000001.XSHE'),
    ('2024-01-02', '600519.SH'),
    ...
], names=['date', 'symbol']))
```

---

## 依赖安装

```bash
# 核心依赖
pip install pandas numpy scipy matplotlib

# 可视化
pip install plotly

# Dashboard
pip install streamlit

# 评估 (可选)
pip install alphalens

# 数据源 (可选)
pip install baostock akshare tushare
pip install ricequant
```

---

## 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

---

## 更新日志

### v3.0.0 (2026-02-09)

#### 新增功能

- ✅ Pipeline 引擎 (Zipline 风格)
- ✅ 增强评估模块 (Alphalens)
- ✅ 风险指标模块 (QuantStats)
- ✅ Tearsheet 报告
- ✅ Pandas 扩展方法
- ✅ Monte Carlo 模拟
- ✅ 因子交互分析 Dashboard
- ✅ Pipeline 编辑器 Dashboard
- ✅ 米筐数据下载器
- ✅ CSV 数据导入

#### 优化

- 🐛 修复分组回测多股票问题
- 🐛 修复模块导入错误
- 📈 优化 IC 计算性能
- 📈 增强 MultiIndex 支持

---

## 许可证

本项目采用 Apache License 2.0 许可证。

---

<div align="center">

**量化因子系统** - 让因子研究更简单

[GitHub](https://github.com/xinzhan18/quant_factor_system) | 
[文档](https://github.com/xinzhan18/quant_factor_system/wiki) | 
[问题反馈](https://github.com/xinzhan18/quant_factor_system/issues)

</div>
