---
title: Factor Library
description: 中央因子库总览（已录取因子）
---

# Factor Library

> 自动化因子挖掘与评审系统的正式输出。已录取因子经6维结构化裁决（机制对齐、统计强度、稳定性、去冗余、可行性、风险模型）验证。

## 活跃因子一览

| ID | Name | Expression | Family | Batch | Admitted | Grade |
|----|------|------------|--------|-------|----------|-------|
| [[R005 vol_peak_timing_20]] | vol_peak_timing_20 | `IdxMax($volume, 20)` | PF_pv_timing | batch_003 | 2026-04-06 | B |
| R004 | atr_ratio_20 | `Mean(Div(Sub($high, $low), $close), 20)` | — | batch_002 | 2026-04-06 | — |
| R003 | turnover_vol_10 | `Std($turnover_rate, 10)` | — | batch_002 | 2026-04-06 | — |
| R002 | amount_cv_10_60 | `Div(Std($amount, 10), Mean($amount, 60))` | — | batch_002 | 2026-04-06 | — |
| R001 | pv_corr_times_vol_20 | `Mul(Corr($close, $volume, 20), Std($volume, 20))` | PF_pv_correlation | batch_002 | 2026-04-06 | — |

---

## 家族分类

### PF_pv_timing — 量价时序家族

| Factor | Expression | Route | Key Metric |
|--------|------------|-------|------------|
| **R005** vol_peak_timing_20 | `IdxMax($volume, 20)` | decorrelate | ICIR_OOS=-0.418, alpha_survival=0.498 |

**探索主题**：成交量峰值出现的时机模式，剥离风格暴露后的纯时序秩序信号。

### PF_pv_correlation — 量价相关家族

| Factor | Expression | Route | Key Metric |
|--------|------------|-------|------------|
| **R001** pv_corr_times_vol_20 | `Mul(Corr($close, $volume, 20), Std($volume, 20))` | genesis | ICIR=-0.373, Mono=-1.0 |

**探索主题**：量价相关性加权波动率，捕捉背离强度。

---

## 统计摘要

| 维度 | 指标 |
|------|------|
| Total Admitted Factors | 5 |
| Active Families | 2 |
| Composite Score Range | 71.1 (R005) |
| Lowest Style r² | 0.083 (R005) |
| Highest alpha_survival | 0.498 (R005) |

---

## 研究前沿（batch_003 结论）

### 录取因子

**R005 — vol_peak_timing_20**：`IdxMax($volume, 20)`
- **Route**: decorrelate
- **Key Strength**: style_r²=0.083（最低风格暴露），alpha_survival=0.498（最优），ICIR_OOS=-0.418（OOS增强）
- **Key Weakness**: 与F067 corr=0.627（高共线性）
- **Composite**: 71.1 / Grade B

### 拒绝因子

详见 `storage/batches/batch_003/judge_packet.yaml`

---

## 使用指南

### 调用因子

```python
from data.loaders import load_factor_expression
expr = load_factor_expression("R005")  # returns "IdxMax($volume, 20)"
```

### 因子相关性查询

```bash
PYTHONPATH=src python3 -m research capabilities
```

### 报告生成

```bash
PYTHONPATH=src python3 -m report.builder --factor-id R005 --vault
```

---

## 治理记录

- [[research_lessons]] — 禁忌模式与经验总结
- [[ledger]] — 搜索账本与审计追踪
- [[Factor Library|Factor Library]] — 本页

---

*Last updated: 2026-04-06*
