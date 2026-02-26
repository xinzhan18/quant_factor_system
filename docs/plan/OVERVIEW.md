# 📋 项目任务总览

**最后更新**: 2026-02-26

---

## 🎯 当前架构

```
quant_factor_system/
├── core/                    # 核心基类
├── data/                   # 数据层 ⭐ 重构完成
│   ├── ricequant_source.py   # 米筐数据源
│   ├── data_manager.py      # 数据管理
│   ├── loaders.py          # 数据加载
│   ├── clean/              # 数据清洗
│   ├── storage/            # 存储层
│   └── utils/              # 工具类
├── factors/                # 因子层
│   ├── basic/              # 基础因子
│   └── visualization/       # IC分析、分组收益
├── backtest/              # 回测层 ⭐ 重构完成
│   ├── engine.py           # 回测引擎
│   ├── analyzer.py         # 绩效分析
│   ├── selection/          # 选股模块
│   ├── position/           # 仓位模块
│   ├── stoploss/          # 止损模块
│   └── signal/             # 信号生成
├── dashboard/             # Dashboard ⭐ 重构完成
│   ├── components/         # 图表、表单、表格组件
│   └── pages/              # 页面
├── pipeline/               # Pipeline
└── docs/                   # 文档
    └── plan/              # Plan 文档
```

---

## 📝 已完成的 Plan

| 日期 | Plan | 状态 |
|-----|------|------|
| 2026-02-19 | position_selector_stoploss_refactor | ✅ 完成 |
| 2026-02-19 | dashboard_ic_analyzer_unify | ✅ 完成 |
| 2026-02-19 | dashboard_refactor | ✅ 完成 |
| 2026-02-19 | delete_mock_data | ✅ 完成 |
| 2026-02-19 | data_folder_restructuring | ✅ 完成 |

---

## ⏸️ 暂停的 Plan

| 日期 | Plan | 状态 | 原因 |
|-----|------|------|------|
| 2026-02-26 | ambiguous_amount_ratio | ⏸️ 暂停 | 缺分钟级数据 |

---

## 📋 Plan 详情

### 1. position_selector_stoploss_refactor ✅

**目标**: selector/position/stoploss 移到 backtest/ 下

**改动**:
- selector/ → backtest/selection/
- position/ → backtest/position/
- stoploss/ → backtest/stoploss/

### 2. dashboard_ic_analyzer_unify ✅

**目标**: Dashboard 调用 ICAnalyzer，消除代码重复

**改动**:
- Dashboard Factors.py 调用 factors/visualization/ICAnalyzer
- 删除重复的 IC 计算代码

### 3. dashboard_refactor ✅

**目标**: Dashboard 变成纯 "Load + 展示"

**改动**:
- 创建 data/loaders.py
- 抽取数据加载逻辑
- 删除重复代码

### 4. delete_mock_data ✅

**目标**: 删除所有模拟数据相关代码

**改动**:
- 删除 data/simulator.py
- 删除 data/sample_price.csv
- 删除相关调用

### 5. data_folder_restructuring ✅

**目标**: data/ 拆分为 storage/ + utils/

**改动**:
- data/storage/ → 存储相关模块
- data/utils/ → 工具类模块

---

## 🔄 重构历史

| 日期 | 重构项 | 状态 |
|-----|------|------|
| 2026-02-19 | selector/position/stoploss → backtest/ | ✅ |
| 2026-02-19 | Dashboard 调用 ICAnalyzer | ✅ |
| 2026-02-19 | 抽取 data/loaders.py | ✅ |
| 2026-02-19 | 删除模拟数据 | ✅ |
| 2026-02-19 | data/ 拆分为 storage/ + utils/ | ✅ |

---

## 📚 文档

- [项目概览](PROJECT_OVERVIEW.md)
- [架构文档](ARCHITECTURE.md)

---

*最后更新: 2026-02-26*
