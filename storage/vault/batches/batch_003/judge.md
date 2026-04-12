---
batch_id: batch_003
judged_at: 2026-04-13T01:00:00Z
direction: candlestick_liquidity

candidates:
  - candidate_id: C001
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: unclear, CP03: weak, CP04: borderline, CP05: low, CP06: unstable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C002
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: strong, CP04: borderline, CP05: high, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C003
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: strong, CP04: acceptable, CP05: high, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C004
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: borderline, CP04: acceptable, CP05: high, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C005
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: strong, CP04: acceptable, CP05: high, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C006
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: unclear, CP03: borderline, CP04: poor, CP05: low, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C007
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: strong, CP04: borderline, CP05: high, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C008
    verdict: admit
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: strong, CP04: borderline, CP05: low, CP06: stable}
    factor_id: F004
    referenced_context: [lessons.md#Structural Constraints]

batch_summary:
  total: 8
  admit: 1
  reserve: 0
  reject: 7
  new_factors: [F004]
---

# batch_003 判决报告

> [!abstract] 总览
> 方向 [[../../directions/candlestick_liquidity|K线微观结构×流动性]] 第三轮。8 候选 → ==1 admit==, 0 reserve, 7 reject。
> 冗余是本轮的主要拒绝原因（C002/C003/C004/C005/C007 的 max_corr > 0.70）。新方向突破：C008（上影线×负动量）ICIR=0.418 + corr=0.607，是一个全新的"抛压×反转"信号。

| 候选 | 信号 | ICIR | style_r² | max_corr | 裁决 |
|---|---|---|---|---|---|
| C001 | 下影线×CsRank(-PB) | 0.101 | 0.245 | 0.530 | reject (CP03 弱) |
| C002 | 影线乘积×CsRank(-PE) | -0.440 | 0.157 | ==0.946== | reject (CP05 冗余 F002) |
| C003 | TsRank(shadow_product) | -0.499 | ==0.024== | ==0.743== | reject (CP05 冗余) |
| C004 | TsRank(下影线ratio) | -0.295 | 0.026 | ==0.708== | reject (CP05 冗余) |
| C005 | 下影线×相对换手 | -0.409 | 0.050 | ==0.744== | reject (CP05 冗余) |
| C006 | body_std×CsRank(-PB) | 0.287 | 0.682 | 0.343 | reject (CP04 vol proxy) |
| C007 | 影线乘积×(-5日ret) | 0.419 | 0.208 | ==0.994== | reject (CP05 冗余 F002) |
| **C008** | **上影线/close×(-5日ret)** | ==0.418== | 0.127 | 0.607 | ==**admit → [[../../factors/F004\|F004]]**== |

---

## C001 — REJECT

### CP01
Hard gates: all_pass。

> [!failure] 拒绝：CP03 弱信号
> IC=0.010, ICIR=0.101。下影线 × CsRank(-PB) 的 fundamental conditioning 没有增强信号。D1 ic_by_year 方向不一致。ls_tstat=-0.4（不显著）。

---

## C002 — REJECT

### CP01
Hard gates: all_pass。

> [!danger] 拒绝：CP05 max_corr=0.946 vs F002
> 影线乘积 × CsRank(-PE) 本质上仍是影线乘积的变体——PE conditioning 没有改变截面排序足够多。

---

## C003 — REJECT

### CP01
Hard gates: all_pass。

> [!danger] 拒绝：CP05 max_corr=0.743 (>0.70)
> TsRank(shadow_product, 20) 是最遗憾的 reject：style_r2=0.024 极度干净，ICIR=-0.499 强劲。但与现有因子库相关性超标。==如果 F002 被 retire，C003 是其最佳替代品==。D1 年度 IC 完全一致（7年全负）。

---

## C004 — REJECT

### CP01
Hard gates: all_pass。

> [!danger] 拒绝：CP05 max_corr=0.708 (>0.70)
> TsRank(lower_shadow_ratio) 与 F001 高度相关。ICIR=-0.295 也偏弱。

---

## C005 — REJECT

### CP01
Hard gates: all_pass。

> [!danger] 拒绝：CP05 max_corr=0.744 (>0.70)
> 下影线 × 相对换手率（当日/20日均）style_r2=0.050 非常干净，ICIR=-0.409 强劲。但与 F001/F003 冗余超标。==ratio 化换手率与 CsRank($amount) 的效果几乎等价==。

---

## C006 — REJECT

### CP01
Hard gates: all_pass。

> [!danger] 拒绝：CP04 style_r2=0.682
> body_ratio_std × CsRank(-PB) 本质上是 vol × value 交互——两个 Barra 因子的乘积。

---

## C007 — REJECT

### CP01
Hard gates: all_pass。

> [!danger] 拒绝：CP05 max_corr=0.994 vs F002
> 影线乘积 × 负动量——乘以动量并不改变与 F002 的排序足够多。

---

## C008 — ==ADMIT== → [[../../factors/F004|F004]] 上影线/close × 负5日收益

### CP01
Hard gates: ==all_pass==。coverage=0.95, sign=+1（正方向！）。

### CP02
机制对齐：**aligned**。上影线/close 衡量日内抛压的相对强度（normalized by close）。乘以负5日收益（-ret_5d）→ 因子值在"近期下跌 + 长上影线"时最大。经济机制：==连续下跌中出现的长上影线 = 反弹失败 = 下跌延续确认信号==。正 IC 意味着因子值高（近期跌+长上影）的股票反而表现好——这是一个**动量反转 × 微观结构确认**信号。

### CP03
统计强度：**strong**。IC=0.038, ICIR=0.418。mt_bucket=low。D1 年度 IC 一致性好（5/7年同方向）。ls_tstat=8.1（高度显著）。D3 mono_IS=0.5（中等——Q1-Q3 平坦，Q4-Q5 跳升，"pick winners"型信号）。

### CP04
风险干净度：**borderline**。style_r2=0.127——比 shadow/turnover 类候选干净很多（0.2-0.6）。dominant_style=vol_20d。alpha_survival 待确认。这是一个新机制方向（momentum reversal × candlestick），风格暴露模式应该和纯 shadow 信号不同。

### CP05
冗余：**low**。max_corr=0.607 vs F001。==低于 0.70 阈值==——与现有因子库有效正交。这是一个全新的信号方向。

### CP06
稳定性：**stable**。split_bucket=high, sign_consistency=1.0。factor_turnover=0.72（偏高但可接受）。
