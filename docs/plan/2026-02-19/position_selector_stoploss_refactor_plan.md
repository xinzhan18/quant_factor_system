# Position/Selector/StopLoss 模块重构计划

## 📌 目前的状况

当前项目存在模块冗余：

```
quant_factor_system/
├── selector/              # ⭐ 已删除
├── position/             # ⭐ 已删除
├── stoploss/             # ⭐ 已删除
└── backtest/             # 回测模块（含选股、仓位、止损）
    ├── engine.py
    ├── analyzer.py
    ├── selection/        # ⭐ 已合并 selector 功能
    ├── position/         # ⭐ 已移动到此
    ├── stoploss/         # ⭐ 已移动到此
    └── signal/           # 信号生成
```

**重构完成**: selector, position, stoploss 已合并到 backtest 模块下。

## ✅ 决策

**选择方案A**: 合并到 backtest 模块
- selector → backtest/selection（合并 selection 目录）
- position → backtest/position
- stoploss → backtest/stoploss
- 理由: 结构清晰，符合"只在回测用到"的现状

## 📋 需求列表及状态

| 需求 | 状态 | 优先级 |
|------|------|--------|
| 移动 position 到 backtest/position | done | high |
| 移动 stoploss 到 backtest/stoploss | done | high |
| 处理 selector/ 与 backtest/selection/ 合并 | done | high |
| 更新 __init__.py 导出 | done | medium |
| 更新所有导入路径引用 | done | medium |
| 删除旧的顶层目录 | done | low |
| 测试导入正常 | done | low |

## 🎯 执行步骤

### Step 1: 创建 backtest/position 和 backtest/stoploss 目录

- [x] 创建 `backtest/position/` 目录
- [x] 创建 `backtest/stoploss/` 目录
- [x] 创建对应的 `__init__.py`

### Step 2: 移动文件

- [x] 复制 `position/*.py` → `backtest/position/`
- [x] 复制 `stoploss/*.py` → `backtest/stoploss/`
- [x] 验证文件完整性

### Step 3: 处理 selector 与 selection 合并

- [x] 分析 selector/ 和 backtest/selection/ 的功能
- [x] 确定合并方案（保留 backtest/selection/，合并 selector 功能）
- [x] 复制 selector/*.py → backtest/selection/
- [x] 更新 backtest/selection/__init__.py

### Step 4: 更新 __init__.py 导出

- [x] 更新 backtest/position/__init__.py
- [x] 更新 backtest/stoploss/__init__.py
- [x] 更新 backtest/selection/__init__.py
- [x] 更新 backtest/__init__.py 添加新模块导出
- [x] 更新顶层 `__init__.py` 移除已移动模块

### Step 5: 更新导入引用

- [x] 更新 backtest/selection/*.py 的内部导入
- [x] 验证 dashboard 没有引用旧模块

### Step 6: 删除旧目录（最后）

- [x] 删除顶层 `selector/` 目录
- [x] 删除顶层 `position/` 目录
- [x] 删除顶层 `stoploss/` 目录

### Step 7: 测试

- [x] 测试项目导入正常
- [ ] 测试 dashboard 正常启动
- [ ] 测试回测功能正常

## 📝 测试结果

```
from quant_factor_system.backtest import (
    BacktestEngine,
    # 选股
    SingleFactorSelector,
    MultiFactorCombiner,
    IntersectionFilter,
    # 仓位
    EqualWeightManager,
    FixedWeightManager,
    FactorWeightedManager,
    KellyManager,
    # 止损
    FixedStopLoss,
    ATRStopLoss,
)
✅ 导入成功！
```
