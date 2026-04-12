---
factor_id: F003
direction: candlestick_liquidity
admitted_in_batch: batch_002
---

# Report Packet — F003

## Factor YAML Summary

```yaml
name: F003
expression: Mul(Div(Sub(If(Lt($close, $open), $close, $open), $low), Sub($high, $low)),
  CsRank($amount))
source_type: dsl
family_tag: candlestick_liquidity
validation_metrics:
  ic_mean: -0.059081643515218184
  ic_ir: -0.6073363287130821
  ic_win_rate: 0.2830578512396694
  monotonicity: -0.8999999999999998
  long_short_mean: -0.002343968339990786
risk_metrics:
  style_r_squared: 0.22450011565134798
  alpha_survival_ratio: 0.5866
```

## Judge Synthesis

## C003 — ==ADMIT== → [[../../factors/F003|F003]] 下影线ratio × CsRank(amount)

### CP01
Hard gates: ==all_pass==。coverage=0.95, sign=-1。

### CP02
机制对齐：**aligned**。下影线 ratio × CsRank($amount) 用成交金额的截面排名替代 raw turnover_rate。CsRank 去掉了 amount 的绝对 scale（不同市值股票的成交额差异巨大），保留"该股票在全市场中的成交活跃度排名"。经济机制：==高成交排名 + 长下影线 = 机构资金积极参与下的探底试探==。

### CP03
统计强度：**strong**。IC_val=-0.059, ==ICIR=-0.607==（本系统目前最强）。mt_bucket=low, search_adjusted=0.75。D1 年度 IC 一致性强：所有 7 年 IC 均为负（-0.019 到 -0.056），无异号年份。ls_tstat=-9.01（高度显著）。D3 mono_IS=-0.9, mono_OOS=-0.9（一致）。

### CP04
风险干净度：**borderline → acceptable**（==override==）。style_r2=0.225, alpha_survival=0.587。alpha_survival < 0.60 门槛但仅差 0.013。

> [!warning] Override 理由
> (1) ICIR=-0.607 是目前全系统最强信号 (2) D1 ic_by_year 7 年全部同方向 (3) ls_tstat=-9.01 高度显著 (4) alpha_survival=0.587 仅差 0.013 到门槛
> **监控**：alpha_survival < 0.50 → 触发重审。

### CP05
冗余：**low**。max_lib_corr=0.684 vs [[../../factors/F001|F001]]（下影线×turnover_rate）。高相关但未超 0.70 阈值。D6 incremental_ic 为 None（库太小无法计算）。

### CP06
稳定性：**stable**。split_bucket=high, sign_consistency=1.0, dispersion=0.173。train_val_decay=1.467（OOS 更强）。factor_turnover=0.724（每天换 72% 持仓——偏高但对日频因子可接受）。

---

## Instructions

Write a deep analytical report on `F003`. Cover the economic mechanism, the validation evidence, the risk cleanness, and the library positioning. Use only the information in this packet — do not open other files, call Qlib, or reach the DB. Output path: `vault/factors/{factor_id}.md`.

