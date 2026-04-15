---
factor_id: F007
direction: fundamental_technical_cov
admitted_in_batch: batch_006
---

# Report Packet — F007

## Factor YAML Summary

```yaml
name: F007
expression: Cov($turnover_rate, $pe_ratio, 20)
source_type: dsl
family_tag: fundamental_technical_cov
validation_metrics:
  ic_mean: -0.023458907586122665
  ic_ir: -0.3161499327520854
  ic_win_rate: 0.3925619834710744
  monotonicity: -0.7
  long_short_mean: -0.0007317915854303066
risk_metrics:
  style_r_squared: 0.09924187180298094
  alpha_survival_ratio: 0.4915
```

## Judge Synthesis

## C001 — ==ADMIT== → [[../../factors/F007|F007]] Cov(换手率, PE, 20天)

### CP01
Hard gates: ==all_pass==。coverage=0.95, sign=-1。

### CP02
机制对齐：**aligned**。Cov(turnover_rate, pe_ratio, 20) 衡量近 20 天内换手率与 PE 的协方差。负 IC → 高协方差（换手和估值同步上升）的股票后续表现差。机制：==换手率和 PE 同步上升 = "投机推升估值泡沫"——短期内看涨但中期反转==。20 天窗口比 60 天更灵敏，捕捉更快的投机脉冲。

### CP03
统计强度：**borderline**。IC=-0.024, ICIR=-0.316（刚过 0.30 阈值）。mt_bucket=low。ls_tstat=-6.2（显著）。D1 年度 IC 6/7 年同方向。不是最强的信号但方向一致性很好。

### CP04
风险干净度：**acceptable**。==style_r2=0.099==——低于 0.12 阈值，干净。协方差是二阶统计量，Barra 因子（一阶的 level/rank）解释不了。

### CP05
冗余：**low**。max_corr=0.234——与全部 6 个现有因子正交。这是一个全新的信号结构。

### CP06
稳定性：**stable**。split_bucket=high, sign_consistency=1.0。

---

## Instructions

Write a deep analytical report on `F007`. Cover the economic mechanism, the validation evidence, the risk cleanness, and the library positioning. Use only the information in this packet — do not open other files, call Qlib, or reach the DB. Output path: `vault/factors/{factor_id}.md`.

