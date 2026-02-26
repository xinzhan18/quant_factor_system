# 模糊金额比因子研究计划

## 📌 目前的状况
- 因子逻辑已明确：商频因子-成交分布类
- 需要使用分钟级数据（1分钟K线）计算
- 数据源：TimescaleDB (RiceQuant)

## ⚠️ 已暂停

**原因**: 数据库里没有分钟级历史数据，无法获取真实分钟级成交额数据。

### 已完成的工作
1. 因子构建脚本: `scripts/build_ambiguous_amount_ratio.py`
2. 分析脚本: `factors/visualization/analyze_ambiguous_amount_ratio.py`
3. 修复了 TimescaleDB 连接密码问题

### 待解决的问题
- 需要从 RiceQuant 导入历史分钟数据（但有每天1G流量限制）

---

## 📋 需求列表及状态

| 需求 | 状态 |
|------|------|
| 构建模糊金额比因子 | 暂停（缺分钟数据） |
| 因子分析 | 暂停（缺分钟数据） |
| 因子落库 | 待定 |
