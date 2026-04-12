---
batch_id: batch_004
judged_at: 2026-04-13T01:30:00Z
direction: candlestick_liquidity

candidates:
  - candidate_id: C001
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: strong, CP04: borderline, CP05: high, CP06: stable}
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
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: weak, CP04: borderline, CP05: low, CP06: unstable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C005
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: weak, CP04: borderline, CP05: low, CP06: unstable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C006
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: strong, CP04: acceptable, CP05: high, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C007
    verdict: admit
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: strong, CP04: acceptable, CP05: low, CP06: stable}
    factor_id: F005
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C008
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: unclear, CP03: weak, CP04: acceptable, CP05: low, CP06: unstable}
    referenced_context: [lessons.md#Structural Constraints]

batch_summary:
  total: 8
  admit: 1
  reserve: 0
  reject: 7
  new_factors: [F005]
---

# batch_004 判决报告

> [!abstract] 总览
> 方向 [[../../directions/candlestick_liquidity|K线微观结构×流动性]] 第四轮。8 候选 → ==1 admit==, 0 reserve, 7 reject。
> T004 深化结果：momentum 窗口换 10d/20d 不改变与 F004 的排序（corr>0.99）。下影线×(-5日ret) ICIR=0.635 极强但冗余超标。==突破：C007 IdxMax(上影线,20)×(-5日ret) ICIR=0.386, style_r2=0.052, max_corr=0.233 — 全库最低冗余的新 timing 信号==。

| 候选 | 信号 | ICIR | style_r² | max_corr | 裁决 |
|---|---|---|---|---|---|
| C001 | 上影线×(-10日ret) | 0.422 | 0.136 | ==0.998== | reject (CP05 冗余 F004) |
| C002 | 上影线×(-20日ret) | 0.423 | 0.163 | ==0.996== | reject (CP05 冗余 F004) |
| C003 | 下影线×(-5日ret) | ==0.635== | 0.115 | ==0.771== | reject (CP05 冗余) |
| C004 | 简化上影线×(-5日ret) | 0.165 | 0.182 | 0.599 | reject (CP03 弱) |
| C005 | 双CsRank版 | 0.173 | 0.127 | 0.521 | reject (CP03 弱) |
| C006 | 上影线×相对volume | -0.538 | 0.101 | ==0.946== | reject (CP05 冗余) |
| **C007** | **IdxMax(上影线,20)×(-5日ret)** | 0.386 | ==0.052== | ==0.233== | ==**admit → [[../../factors/F005\|F005]]**== |
| C008 | 影线不对称性 | 0.062 | 0.031 | 0.666 | reject (CP03 无信号) |

---

## C001 — REJECT

### CP01
Hard gates: all_pass。

> [!danger] 拒绝：CP05 max_corr=0.998 vs F004
> 换 momentum 窗口 5→10 天不改变截面排序。上影线/close 是主导项，ret_5d 和 ret_10d 高度同源。

---

## C002 — REJECT

### CP01
Hard gates: all_pass。

> [!danger] 拒绝：CP05 max_corr=0.996 vs F004
> 同理 20 天。momentum 窗口对影线信号的调制效果不敏感。

---

## C003 — REJECT

### CP01
Hard gates: all_pass。

> [!danger] 拒绝：CP05 max_corr=0.771 (>0.70)
> 下影线×(-5日ret) ==ICIR=0.635 是 4 轮里最强的候选==。style_r2=0.115 干净。但与 F001/F003/F004 相关性超标。下影线和上影线在截面上高度共线（都是日内波幅的组成部分）。==如果 F001 retire，C003 是最佳替代==。

---

## C004 — REJECT

### CP01
Hard gates: all_pass。

> [!failure] 拒绝：CP03 弱
> 简化上影线 (high-close)/close 失去了阴阳线区分。ICIR=0.165。

---

## C005 — REJECT

### CP01
Hard gates: all_pass。

> [!failure] 拒绝：CP03 弱
> 双 CsRank 版 ICIR=0.173。rank 化杀死了 F004 的信号。

---

## C006 — REJECT

### CP01
Hard gates: all_pass。

> [!danger] 拒绝：CP05 max_corr=0.946
> 上影线×相对volume 与 F001(下影线×turnover) 高度冗余——shadow × liquidity 信号空间已被现有因子覆盖。

---

## C007 — ==ADMIT== → [[../../factors/F005|F005]] IdxMax(上影线,20) × 负5日收益

### CP01
Hard gates: ==all_pass==。coverage=0.95, sign=+1。

### CP02
机制对齐：**aligned**。IdxMax(上影线/close, 20) 返回"过去 20 天中上影线最长的那一天距今几天"。值越大=最大抛压发生在越久以前。乘以 (-5日ret)：如果近期在跌 且 最大抛压已经是很久以前的事 → 因子值大 → 高收益。机制：==抛压已经释放完毕 + 近期下跌 = 错杀后的反弹机会==。这是一个 timing signal（"抛压时机"）× momentum reversal 的复合信号。

### CP03
统计强度：**strong**。IC=0.021, ICIR=0.386。mt_bucket=low。ls_tstat=? D1 年度 IC 5/7 年同方向。IdxMax 是离散整数值（0-19），信号比较粗糙但稳定。

### CP04
风险干净度：**acceptable**。==style_r2=0.052==——**全库最干净**。Barra 风格几乎无法解释这个因子。IdxMax 是纯时序结构特征，不是 level（价格/成交量级别），所以天然正交于 Barra 的 level 因子。

### CP05
冗余：**low**。==max_corr=0.233==——**全库最低冗余**。IdxMax timing 信号与所有现有 shadow/turnover 因子截面排序完全不同。这是一个真正独立的新维度。

### CP06
稳定性：**stable**。split_bucket=high。IdxMax 的离散性使得 IC 序列波动较大（日级别），但方向一致。

---

## C008 — REJECT

### CP01
Hard gates: all_pass。

> [!failure] 拒绝：CP03 无信号
> 影线不对称性（上影线-下影线）/close IC=0.006, ICIR=0.062。差值信号太弱。
