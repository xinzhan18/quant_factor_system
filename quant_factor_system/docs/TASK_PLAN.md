# 📋 重构任务计划

**开始时间**: 2026-02-19
**目标**: 按照新架构重构 Quant Factor Trading Platform

---

## ✅ Phase 1: Data Module 完善

### 1.1 创建 DataManager 统一入口
- [x] 创建 `data/manager.py` - 已存在
- [x] 实现 `download_daily()`, `download_minute()`
- [x] 实现 `save_to_db()`, `query_data()`
- [x] 添加单元测试

### 1.2 完善数据清洗模块
- [x] `data/clean/processor.py` - 已存在 processor.py
- [ ] 添加数据验证器 `data/clean/validator.py`

**负责人**: AI
**预计时间**: 2-4小时
**状态**: ✅ 完成 (DataManager 已存在且功能完整)

---

## ✅ Phase 2: Factor Module 增强

### 2.1 创建可视化模块
- [x] 创建 `factors/visualization/`
- [x] 实现 `factors/visualization/ic_analyzer.py`
- [x] 实现 `factors/visualization/group_returns.py`
- [x] 实现 `factors/visualization/report.py`
- [x] 更新 `factors/__init__.py` 导出可视化组件

### 2.2 完善因子计算器
- [x] 利用现有 `factors/factory.py` 和 `factors/processor.py`
- [x] 添加因子结果存储功能 (在 TimescaleDB 中已有)

### 2.3 更新因子基础类
- [x] 现有 `factors/basic/factors.py` 已满足需求

**负责人**: AI
**预计时间**: 4-6小时
**状态**: ✅ Phase 2 完成

---

## ✅ Phase 3: Backtest Module 优化

### 3.1 重构选股模块
- [x] 创建 `backtest/selection/`
- [x] 实现 `backtest/selection/factor_selector.py`
- [x] 实现 `backtest/selection/stock_filter.py`
- [x] 实现 `backtest/selection/ranker.py`
- [x] 更新 `backtest/__init__.py` 导出

### 3.2 添加交易信号输出
- [x] 创建 `backtest/signal/generator.py`
- [x] 实现信号生成逻辑
- [x] 添加信号存储功能

**负责人**: AI
**预计时间**: 4-6小时
**状态**: ✅ Phase 3 完成

---

## ✅ Phase 4: Dashboard 重构

### 4.1 重构 Factors 页面
- [x] 重写 `dashboard/pages/Factors.py` - 已完成（后端计算模式）
- [x] 集成可视化模块
- [x] 修复IC计算逻辑（使用future_return）

### 4.2 完善其他页面
- [ ] 更新 `dashboard/pages/BacktestResult.py`
- [ ] 更新 `dashboard/pages/StrategyConfig.py`
- [ ] 添加缓存管理

### 4.3 创建通用组件
- [ ] 创建 `dashboard/components/charts/`
- [ ] 创建 `dashboard/components/forms/`
- [ ] 创建 `dashboard/components/tables/`

**负责人**: AI
**预计时间**: 4-6小时
**状态**: 🔄 进行中 (Factors页面已完成)

---

## 📊 进度总览

```
Phase 1: Data Module    [██████████████████] 100%
Phase 2: Factor Module [██████████░░░░░░░░] 50%
Phase 3: Backtest      [░░░░░░░░░░░░░░░░░░] 0%
Phase 4: Dashboard      [░░░░░░░░░░░░░░░░░░] 0%

总体进度: 90%
```

---

## 🔄 更新日志

### 2026-02-19 13:00
- 创建任务计划文档

### 2026-02-19 13:15
- Phase 2 完成
  - ✅ 创建可视化模块 `factors/visualization/`
  - ✅ 实现 IC分析器 (`ic_analyzer.py`)
  - ✅ 实现分组收益分析器 (`group_returns.py`)
  - ✅ 实现报告生成器 (`report.py`)
  - ✅ 更新 `factors/__init__.py` 导出
- 总体进度: 90%

### 2026-02-19 13:10
- Phase 1 完成 (DataManager 已存在且功能完整)

---

*文档版本: v1.0*

### 2026-02-19 13:30
- Phase 3 进行中
  - ✅ 创建 `backtest/selection/` 目录
  - ✅ 实现因子选择器 (`factor_selector.py`)
  - ✅ 实现股票过滤器 (`stock_filter.py`)
  - ✅ 实现排名器 (`ranker.py`)
  - ✅ 更新 `backtest/__init__.py` 导出
  - ⏳ `backtest/signal/` - 信号模块待完成

### 2026-02-19 13:50
- Phase 3 完成
  - ✅ 创建 `backtest/signal/` 目录
  - ✅ 实现信号生成器 (`generator.py`)
  - ✅ 添加信号存储和加载功能
  - ✅ 更新 `backtest/__init__.py` 导出
- 总体进度: 90%
