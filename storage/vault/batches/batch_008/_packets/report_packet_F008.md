---
factor_id: F008
direction: timing_signals
admitted_in_batch: batch_008
---

# Report Packet — F008

## Factor YAML Summary

```yaml
name: F008
expression: IdxMax($volume, 20)
source_type: dsl
family_tag: timing_signals
validation_metrics:
  ic_mean: -0.025593664193519657
  ic_ir: -0.37322015914721496
  ic_win_rate: 0.35537190082644626
  monotonicity: -0.7
  long_short_mean: -0.0004097824381791394
risk_metrics:
  style_r_squared: 0.07568498286109004
  alpha_survival_ratio: 1.0606
```

## Judge Synthesis

## C003 — ==ADMIT== → [[../../factors/F008|F008]] IdxMax(volume, 20)

### CP01
Hard gates: ==all_pass==。coverage=0.96, sign=-1。

### CP02
机制对齐：**aligned**。IdxMax(volume,20) 返回"过去 20 天中成交量最大的那天距今几天"。值大（如 15-19）→ 放量日已经是很久以前，当前成交在萎缩，市场关注度下降。值小（如 0-3）→ 刚刚放量，市场在积极交易。负 IC → ==放量距今越远的股票后续表现越差==。机制：放量后的资金枯竭导致价格支撑消失。

### CP03
统计强度：**strong**。IC=-0.026, ICIR=-0.373。mt_bucket=low。ls_tstat=-4.9（显著）。D1 年度 IC 6/7 年同方向。纯 timing 信号——不含任何 level 或 ratio 信息。

### CP04
风险干净度：**acceptable**。==style_r2=0.076==——极低。IdxMax 是离散整数（0-19），与连续 Barra 因子天然正交。Volume timing 比 close timing 干净 5 倍（0.076 vs 0.368）。

### CP05
冗余：**low**。max_corr=0.357。与现有 7 因子全部低相关。

### CP06
稳定性：**stable**。split_bucket=high, sign_consistency=1.0。

---

## Instructions

Write a deep analytical report on `F008`. Cover the economic mechanism, the validation evidence, the risk cleanness, and the library positioning. Use only the information in this packet — do not open other files, call Qlib, or reach the DB. Output path: `vault/factors/{factor_id}.md`.

