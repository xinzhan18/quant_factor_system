---
factor_id: F009
direction: timing_signals
admitted_in_batch: batch_008
---

# Report Packet — F009

## Factor YAML Summary

```yaml
name: F009
expression: IdxMax($turnover_rate, 20)
source_type: dsl
family_tag: timing_signals
validation_metrics:
  ic_mean: -0.02518973225971973
  ic_ir: -0.3667754647477209
  ic_win_rate: 0.359504132231405
  monotonicity: -0.7
  long_short_mean: -0.0004924722830043366
risk_metrics:
  style_r_squared: 0.0785218976079114
  alpha_survival_ratio: 0.9553
```

## Judge Synthesis

## C004 — ==ADMIT== → [[../../factors/F009|F009]] IdxMax(turnover_rate, 20)

### CP01
Hard gates: ==all_pass==。coverage=0.96, sign=-1。

### CP02
机制对齐：**aligned**。IdxMax(turnover_rate,20) 和 C003(volume) 机制类似但度量不同——turnover_rate 是 normalized by 流通股本的换手率，消除了市值效应。负 IC → 高换手日距今越远 → 表现越差。

### CP03
统计强度：**strong**。IC=-0.025, ICIR=-0.367。mt_bucket=low。ls_tstat=-8.3（==非常显著==）。比 C003 的 tstat 更高。

### CP04
风险干净度：**acceptable**。==style_r2=0.079==。

### CP05
冗余：**low**。max_corr=0.286。==与 F008(C003) 的 corr 需要后续确认==——两者可能高度共线（volume 和 turnover 的 IdxMax 可能在同一天）。但当前全库 max_corr=0.286 < 0.70。

### CP06
稳定性：**stable**。

---

## Instructions

Write a deep analytical report on `F009`. Cover the economic mechanism, the validation evidence, the risk cleanness, and the library positioning. Use only the information in this packet — do not open other files, call Qlib, or reach the DB. Output path: `vault/factors/{factor_id}.md`.

