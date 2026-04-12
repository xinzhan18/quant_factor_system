---
batch_id: batch_002
judged_at: 2026-04-13T00:30:00Z
direction: candlestick_liquidity

candidates:
  - candidate_id: C001
    verdict: reserve
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: weak, CP04: acceptable, CP05: low, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C002
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: strong, CP04: borderline, CP05: high, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C003
    verdict: admit
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: strong, CP04: borderline, CP05: low, CP06: stable}
    factor_id: F003
    overrides: [{checkpoint: CP04, from: borderline, to: acceptable}]
    referenced_context: [lessons.md#Structural Constraints]
    concerns: [{checkpoint: CP04, if: "alpha_survival < 0.50 in next batch", then: "重审 CP04 override"}]
  - candidate_id: C004
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: unclear, CP03: weak, CP04: poor, CP05: low, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C005
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: unclear, CP03: weak, CP04: acceptable, CP05: low, CP06: unstable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C006
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: borderline, CP04: poor, CP05: low, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C007
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: weak, CP04: poor, CP05: low, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C008
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: weak, CP04: acceptable, CP05: low, CP06: unstable}
    referenced_context: [lessons.md#Structural Constraints]

batch_summary:
  total: 8
  admit: 1
  reserve: 1
  reject: 6
  new_factors: [F003]
---

# batch_002 判决报告

> [!abstract] 总览
> 方向 [[../../directions/candlestick_liquidity|K线微观结构×流动性]] 第二轮。8 候选 → ==1 admit==, 1 reserve, 6 reject。
> 核心发现：CsRank 正交化成功降低 style_r2（C001: 0.031, C005: 0.023），但信号大幅减弱。range compression 和 body ratio Cov 都是 vol proxy。唯一亮点：C003 下影线×CsRank(amount) ICIR=-0.607，本系统目前最强信号。

| 候选 | 信号 | ICIR | style_r² | ls_tstat | 裁决 |
|---|---|---|---|---|---|
| C001 | CsRank(下影线ratio) | -0.213 | ==0.031== | -2.05 | reserve |
| C002 | CsRank(影线乘积) | -0.421 | 0.171 | -11.20 | ==reject (CP05 冗余)== |
| **C003** | **下影线ratio×CsRank(amount)** | ==-0.607== | 0.225 | -9.01 | ==**admit → [[../../factors/F003\|F003]]**== |
| C004 | Cov(body_ratio, ret) | -0.269 | 0.403 | -1.10 | reject (CP04) |
| C005 | Delta(body_ratio) | 0.098 | 0.023 | 4.23 | reject (CP03 无信号) |
| C006 | Range 10/60 | -0.284 | 0.314 | -2.67 | reject (CP04) |
| C007 | Range 20/120 | -0.240 | 0.407 | -1.84 | reject (CP04) |
| C008 | CsRank(上影线ratio) | -0.010 | 0.028 | -7.32 | reject (CP03 无信号) |

---

## C001 — RESERVE

### CP01
Hard gates: all_pass。coverage=0.95, sign=-1。

### CP02
机制对齐：**aligned**。CsRank 化的下影线 ratio 去掉了绝对价格 scale 的影响，保留了截面排序信息。

### CP03
统计强度：**weak**。IC_val=-0.018, ICIR=-0.213。mt_bucket=low, search_adjusted=0.72。CsRank 去 vol 效果显著（style_r2=0.031），但信号大幅减弱。D1 年度 IC 不稳定：2015 年 IC=+0.030（异号！），2018 年 IC=-0.026。oos_decay_ratio=4.1 表示 OOS 比 IS 强 4 倍——IS 几乎没信号（IC_IS=-0.004），OOS 突然出现信号。

> [!warning] 数据挖掘风险
> D1 ic_by_year 显示 IS 期间 IC 方向不一致（2015-2016 正，2017-2021 负）。oos_decay_ratio=4.1 异常高。Reserve 观察，不 admit。

### CP04
风险干净度：**acceptable**。==style_r2=0.031==——极度干净。CsRank 正交化的目标达成。但信号太弱，clean 无意义。

### CP05
冗余：**low**。max_lib_corr=0.596 vs F001。

### CP06
稳定性：**stable**。split_bucket=high, sign_consistency=1.0。但 factor_turnover=0.987（几乎每天完全换仓）——不可交易。

---

## C002 — REJECT

### CP01
Hard gates: all_pass。

> [!danger] 拒绝：CP05 冗余
> max_lib_corr==1.000== vs [[../../factors/F002|F002]]。CsRank(shadow_product) 与已有的 shadow_product(F002) 截面排名完全相同——CsRank 是单调变换，不改变排序。==同一因子的 rank 化不算新因子==。

---

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

## C004 — REJECT

### CP01
Hard gates: all_pass。

> [!danger] 拒绝：CP04 alpha_survival=0.072
> style_r2=0.403, alpha_survival=0.072——Barra 回归后 IC 基本消失。Cov(body_ratio, return) 本质上衡量"body ratio 与收益的短期协同"，这几乎完全被 vol_20d 和 str_1m 风格解释。D3 mono_IS=-0.1（无单调性），ls_tstat=-1.10（不显著）。机制不清晰。

---

## C005 — REJECT

### CP01
Hard gates: all_pass。

> [!failure] 拒绝：CP03 无信号
> IC=0.007, ICIR=0.098。Delta(body_ratio, 5-20) 的 IC 虽然为正方向且 style_r2=0.023（极干净），但信号强度不足。D2 oos_decay_ratio=0.528（IS→OOS 衰减近半）。

---

## C006 — REJECT

### CP01
Hard gates: all_pass。

> [!danger] 拒绝：CP04 vol proxy
> style_r2=0.314, alpha_survival=? (计算中)。Range compression 10/60 和 batch_001 的 5/60 (C007) 类似——都是 vol 的不同窗口度量。D3 mono_IS=0.0（无单调性——IS 期间分组完全无序）。

---

## C007 — REJECT

### CP01
Hard gates: all_pass。

> [!danger] 拒绝：CP04 vol proxy
> style_r2=0.407。Range 20/120 是更长期的 vol regime 指标——更慢但更脏。D3 mono_IS=-0.1, ls_tstat=-1.84（不显著）。

---

## C008 — REJECT

### CP01
Hard gates: all_pass。

> [!failure] 拒绝：CP03 无信号
> IC=-0.001, ICIR=-0.010。CsRank(上影线ratio) 几乎无预测力。但 ls_tstat=-7.32 很高——这是一个矛盾：IC 近零但 L/S 显著。D5 factor_skew=0.002（完美对称），说明 CsRank 确实去掉了分布偏态，但也去掉了信号。T001 的结论：==上影线的预测力主要来自绝对值的 scale（即 vol 本身），rank 化后消失==。
