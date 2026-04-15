---
factor_id: F010
direction: timing_signals
admitted_in_batch: batch_008
---

# Report Packet — F010

## Factor YAML Summary

```yaml
name: F010
expression: Mul(IdxMax($volume, 20), Mul(Div($close, Ref($close, 5)), -1))
source_type: dsl
family_tag: timing_signals
validation_metrics:
  ic_mean: 0.028465422347369672
  ic_ir: 0.3833130948951253
  ic_win_rate: 0.6611570247933884
  monotonicity: 0.8999999999999998
  long_short_mean: 0.0004896778414412671
risk_metrics:
  style_r_squared: 0.10356384523011963
  alpha_survival_ratio: 0.9995
```

## Judge Synthesis

## C008 — ==ADMIT== → [[../../factors/F010|F010]] IdxMax(volume, 20) × 负5日收益

### CP01
Hard gates: ==all_pass==。coverage=0.96, sign=+1（==正方向==）。

### CP02
机制对齐：**aligned**。IdxMax(volume,20) × (-5日ret) = "放量日距今天数 × 近期跌幅"。因子值大 → 放量很久以前 + 近期在跌 → 正收益。机制：==放量后经过时间消化 + 近期下跌 = 已充分调整，反弹概率高==。这是 F005（shadow timing × momentum）的 volume timing 版本。

### CP03
统计强度：**strong**。IC=0.029, ICIR=0.383。mt_bucket=low。正方向信号。与 F005 (ICIR=0.386) 几乎等强但使用不同特征（volume vs shadow）。

### CP04
风险干净度：**acceptable**。==style_r2=0.104==——低于 0.12 阈值。

### CP05
冗余：**low**。max_corr=0.375——与 F005(shadow timing×momentum) 的 corr 最高但远低于 0.70。两者虽然结构类似（timing × momentum）但特征来源不同。

### CP06
稳定性：**stable**。

## Instructions

Write a deep analytical report on `F010`. Cover the economic mechanism, the validation evidence, the risk cleanness, and the library positioning. Use only the information in this packet — do not open other files, call Qlib, or reach the DB. Output path: `vault/factors/{factor_id}.md`.

