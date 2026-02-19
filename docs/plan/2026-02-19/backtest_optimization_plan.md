# Backtest 模块优化计划

## 📌 目前的状况

```
backtest/
├── engine.py           # 回测引擎
├── analyzer.py         # 绩效分析
├── risk_metrics.py     # ⚠️ 风险指标（与 analyzer.py 重复）
├── risk/             # ⚠️ 空目录
├── selection/         # 选股模块
├── position/          # 仓位模块
├── stoploss/          # 止损模块
└── signal/            # 信号生成
```

## 🔍 问题分析

| 问题 | 说明 |
|------|------|
| 空目录 `risk/` | 目录存在但为空，应删除 |
| `risk_metrics.py` 与 `analyzer.py` 重复 | 两者都在计算风险指标 |

## ✅ 优化方案

```
backtest/
├── engine.py           # 回测引擎
├── analyzer.py         # ⭐ 绩效 + 风险分析（合并 risk_metrics）
├── selection/         # 选股模块
├── position/          # 仓位模块
├── stoploss/          # 止损模块
└── signal/            # 信号生成
```

## 📋 需求列表及状态

| 需求 | 状态 | 优先级 |
|------|------|--------|
| 删除空目录 risk/ | done | low |
| 合并 risk_metrics.py 到 analyzer.py | done | medium |
| 更新 __init__.py 导出 | done | low |
| 测试验证 | done | low |

## 🎯 执行步骤

### Step 1: 删除空目录

- [x] 删除 `backtest/risk/` 目录

### Step 2: 合并 risk_metrics.py

- [x] 分析 analyzer.py 和 risk_metrics.py 的重复部分
- [x] 在 PerformanceMetrics 添加缺失字段
- [x] 添加 calculate_all_metrics 方法到 PerformanceAnalyzer
- [x] 删除 risk_metrics.py

### Step 3: 更新导出

- [x] 更新 `backtest/__init__.py`

### Step 4: 测试验证

- [x] 测试导入正常
- [x] 测试功能正常

## 📝 合并总结

**PerformanceMetrics 新增字段**:
- `downside_volatility`
- `value_at_risk`
- `conditional_value_at_risk`

**PerformanceAnalyzer 新增方法**:
- `calculate_all_metrics()` - 一键计算所有风险指标

**删除的文件**:
- `backtest/risk_metrics.py`
- `backtest/risk/` 目录

---

*创建时间: 2026-02-19*
