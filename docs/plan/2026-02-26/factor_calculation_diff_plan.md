# 因子计算逻辑差异分析 Plan

## 📌 问题

之前的因子表现（25号生成的图片）和现在用新脚本计算的结果差异很大：
- **之前**：IC较高，累计收益曲线看起来正常
- **现在**：IC接近0，分组收益反向

## ✅ 需要分析的内容

### 1. 收益率计算方式差异
- [ ] **旧逻辑**：`close.pct_change().shift(-1)` - 按日期计算当日收益率
- [ ] **新逻辑**：`groupby('symbol').pct_change().shift(-1)` - 按股票分组计算T+1收益率

### 2. 数据范围差异
- [ ] 旧脚本：可能只用了部分数据（如2023年）
- [ ] 新脚本：2015-2024全量数据

### 3. 分组逻辑差异
- [ ] 检查旧的分组逻辑是否正确

---

## 🔍 关键差异分析

### 收益率计算

**旧代码** (factor_report.py):
```python
future_return = close.pct_change().shift(-1)
```

**新代码** (gen_intraday_momentum_report.py):
```python
merged['future_return'] = merged.groupby('symbol')['close'].pct_change().shift(-1)
```

**问题**：旧代码没有按股票分组，会导致：
- 跨股票的收益率计算错误
- 可能计算出的是"当日收益"而非"次日收益"

### T+1 收益 vs 当日收益

根据 MEMORY.md 中的记录（2026-02-22）：
> **所有因子评估必须使用 T+1 收益**

正确的计算方式应该是：
```python
# T+1 收益：今天买入，明天卖出的收益
merged['return_1d'] = df.groupby(level='symbol')['close'].pct_change(1).shift(-1)
```

---

## 📋 验证任务

- [ ] 任务1：用旧逻辑重新计算，对比结果
- [ ] 任务2：确认差异来源
- [ ] 任务3：确定正确的计算逻辑

---

*Plan created: 2026-02-26*
