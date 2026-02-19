# Pipeline 和 Evaluation 重构计划

## 📌 目前的状况

```
pipeline/
├── pipeline.py       # Pipeline 引擎（~225行）
├── factors.py       # Pipeline 因子（~56行）⚠️ 与 factors/ 重复
└── __init__.py

evaluation/
├── risk_metrics.py  # 风险指标（~430行）⚠️ 与 backtest/analyzer.py 重复
└── __init__.py
```

## 🔍 问题分析

| 模块 | 问题 |
|------|------|
| `pipeline/factors.py` | 与 `factors/` 职责重复 |
| `evaluation/risk_metrics.py` | 与 `backtest/analyzer.py` 风险指标重复 |

## ✅ 重构方案

选择 **方案A**: 合并到现有模块

```
pipeline/          → factors/pipeline/
evaluation/risk_metrics.py → backtest/risk_metrics.py
删除 pipeline/factors.py（与 factors/ 重复）
```

## 📋 需求列表及状态

| 需求 | 状态 | 优先级 |
|------|------|--------|
| 创建 factors/pipeline/ 目录 | done | high |
| 移动 pipeline.py → factors/pipeline/ | done | high |
| 移动 risk_metrics.py → backtest/ | done | high |
| 删除 pipeline/factors.py | done | medium |
| 更新 __init__.py 导出 | done | medium |
| 更新引用 | done | medium |
| 测试验证 | done | low |

## 🎯 执行步骤

### Step 1: 创建目录

- [x] 创建 `factors/pipeline/` 目录
- [x] 创建 `backtest/risk/` 目录

### Step 2: 移动文件

- [x] 移动 `pipeline/pipeline.py` → `factors/pipeline/pipeline.py`
- [x] 移动 `pipeline/__init__.py` → `factors/pipeline/__init__.py`
- [x] 移动 `evaluation/risk_metrics.py` → `backtest/risk_metrics.py`

### Step 3: 删除重复

- [x] 删除 `pipeline/factors.py`
- [x] 删除空的 `pipeline/` 目录
- [x] 删除空的 `evaluation/` 目录

### Step 4: 更新引用

- [x] 更新 `factors/__init__.py`
- [x] 更新 `factors/pipeline/pipeline.py` 导入
- [x] 更新 `backtest/__init__.py`
- [x] 更新 `dashboard/pages/Pipeline.py`

### Step 5: 测试验证

- [x] 测试导入正常
- [x] 测试 Dashboard 页面正常

## 📁 新结构

```
factors/
├── basic/              # 基础因子
├── visualization/     # IC分析
├── registry.py        # 因子注册
├── factory.py         # 因子工厂
└── pipeline/          # ⭐ Pipeline 引擎
    ├── pipeline.py
    └── __init__.py

backtest/
├── engine.py          # 回测引擎
├── analyzer.py        # 绩效分析
├── selection/        # 选股模块
├── position/         # 仓位模块
├── stoploss/         # 止损模块
└── risk_metrics.py   # ⭐ 风险指标

evaluation/           # ⭐ 已删除
pipeline/             # ⭐ 已删除
```

---

*创建时间: 2026-02-19*
*更新时间: 2026-02-19*
