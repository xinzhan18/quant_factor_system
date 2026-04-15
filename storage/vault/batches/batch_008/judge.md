---
batch_id: batch_008
judged_at: 2026-04-16T00:30:00Z
direction: timing_signals

candidates:
  - candidate_id: C001
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: weak, CP04: poor, CP05: low, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C002
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: weak, CP04: poor, CP05: low, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C003
    verdict: admit
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: strong, CP04: acceptable, CP05: low, CP06: stable}
    factor_id: F008
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C004
    verdict: admit
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: strong, CP04: acceptable, CP05: low, CP06: stable}
    factor_id: F009
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C005
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: weak, CP04: poor, CP05: low, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C006
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: unclear, CP03: weak, CP04: poor, CP05: low, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C007
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: unclear, CP03: weak, CP04: borderline, CP05: low, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C008
    verdict: admit
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: strong, CP04: acceptable, CP05: low, CP06: stable}
    factor_id: F010
    referenced_context: [lessons.md#Structural Constraints]

batch_summary:
  total: 8
  admit: 3
  reserve: 0
  reject: 5
  new_factors: [F008, F009, F010]
---

# batch_008 判决报告

> [!abstract] 总览
> ==新方向== [[../../directions/timing_signals|Timing Signals]] 首轮。8 候选 → ==3 admit==, 0 reserve, 5 reject。
> ==本系统目前最高产的 batch==。Volume/turnover 的 timing 信号比 close timing 干净得多。三个 admit 全部 style_r2 < 0.11 + max_corr < 0.40 — timing 方向验证成功。

| 候选 | 信号 | ICIR | style_r² | corr | 裁决 |
|---|---|---|---|---|---|
| C001 | IdxMax(close,20) | -0.202 | 0.368 | 0.253 | reject (CP04) |
| C002 | IdxMin(close,20) | 0.137 | 0.326 | 0.094 | reject (CP03+CP04) |
| **C003** | **IdxMax(volume,20)** | ==-0.373== | ==0.076== | 0.357 | ==**admit → [[../../factors/F008\|F008]]**== |
| **C004** | **IdxMax(turnover,20)** | ==-0.367== | ==0.079== | 0.286 | ==**admit → [[../../factors/F009\|F009]]**== |
| C005 | IdxMax(close)×5日ret | -0.241 | 0.403 | 0.268 | reject (CP04) |
| C006 | IdxMin(close)×负5日ret | -0.101 | 0.306 | 0.073 | reject (CP03+CP04) |
| C007 | IdxMax差(60-5) | -0.111 | 0.230 | 0.111 | reject (CP03) |
| **C008** | **IdxMax(volume,20)×负5日ret** | ==0.383== | ==0.104== | 0.375 | ==**admit → [[../../factors/F010\|F010]]**== |

---

## C001 — REJECT

### CP01
Hard gates: all_pass。

> [!danger] 拒绝：CP04 style_r2=0.368
> IdxMax(close,20) — 最高价位置被 str_1m + vol_20d Barra 因子大量解释。Close timing 不是独立信号。

---

## C002 — REJECT

### CP01
Hard gates: all_pass。

> [!failure] 拒绝：CP03 弱 + CP04 r2=0.326
> IdxMin(close,20) ICIR=0.137 太弱。但 max_corr=0.094——有史以来最正交的候选。信号方向有潜力，需更好表达式。

---

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

## C005 — REJECT

### CP01
Hard gates: all_pass。

> [!danger] 拒绝：CP04 style_r2=0.403
> IdxMax(close)×5日ret 被 momentum Barra 因子解释。Close timing + momentum 的乘积几乎就是 str_1m 本身。

---

## C006 — REJECT

### CP01
Hard gates: all_pass。

> [!failure] 拒绝：CP03 弱 + CP04 poor
> IdxMin(close)×负5日ret ICIR=-0.101。最低价 timing × 反转的信号太弱。

---

## C007 — REJECT

### CP01
Hard gates: all_pass。

> [!failure] 拒绝：CP03 弱
> IdxMax(close,60)-IdxMax(close,5) ICIR=-0.111。多窗口 timing 差异信号太弱。

---

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
