---
paper_slug: kysec_amp_2020_ideal_amplitude
source_pdf: external (开源证券研究所专题报告 2020)
source_kind: research_house_report
arxiv_id: null
status: converted
primary_frequency: daily
direction_tag: price_conditional_amplitude
authors: 魏建榕 / 高鹏 / 苏俊豪
publish_year: 2020
reviewed_at: 2026-05-04
---

# 开源证券 — 振幅因子的隐藏结构 / 理想振幅因子（V_high − V_low）

## Core Claim

日度振幅因子 `(高/低 − 1)` 衡量资金多空博弈激烈程度，但**裸振幅** alpha 弱（在不同价格段的振幅含义不同：高价段的高振幅 = 顶部博弈/分歧 / 低价段的高振幅 = 底部企稳/吸筹）。开源证券提出**收盘价 rank-conditional 切割**：

1. 取过去 N=20 个交易日数据
2. 计算每日振幅 `amp_t = $high / $low − 1`
3. 按收盘价排序，取**最高 λ 比例**有效日，平均其振幅 → `V_high(λ)`
4. 按收盘价排序，取**最低 λ 比例**有效日，平均其振幅 → `V_low(λ)`
5. λ=0.25：**理想振幅 = V_high(0.25) − V_low(0.25)**

paper 报全区间 csi500 月频回测：IC mean = **−0.051** / ICIR = **−2.39** / 5 分位多空年化 **17%**，OOS 相对稳健，近两年波动加大。

NEG 信号方向：**高价振幅 > 低价振幅 → 未来收益低**（顶部博弈剧烈预示反转）。

## Aha Moment

**Rank-conditional aggregation** 是当前库未覆盖的几何工艺。库内 27 admit 中：

- F001 `amount_cv_10` 是 second-moment NEG (无价格条件)
- F015/F016 amihud_cv_rank_diff 是 cross-section rank-diff (无时序条件)
- F024-F026 P008 escape 是 TsRank≥60d on dim-less ratio (无价格条件)

**没有任何因子做"在时序窗口内按某一字段排序后取子集均值"**——这正是 V_high/V_low 的几何骨架。等价于 Qlib DSL 里**缺失的 `MaskedMean(amp, condition_on_rank_close)` 算子**。

数学结构：`Σ_{t-19..t} amp_t · 𝟙{rank_close_t ≥ 0.75} / Σ 𝟙{rank_close_t ≥ 0.75}`，其中 `rank_close_t = TsRank($close, 20)`。

## Candidate Ideas

### Idea 1 — 原始 V_high - V_low (DSL 不可达 → Python wrapper 必走)

```python
# storage/python_factors/F029_ideal_amplitude.py（待生成）
def compute(df):
    """df 包含 $high $low $close 时序，per stock"""
    amp = df['$high'] / df['$low'] - 1
    close_rank = df['$close'].rolling(20).rank(pct=True)  # 0~1 within 20d window

    top_mask = (close_rank >= 0.75).astype(float)
    bot_mask = (close_rank <= 0.25).astype(float)

    v_high = (amp * top_mask).rolling(20).sum() / top_mask.rolling(20).sum().clip(lower=1)
    v_low  = (amp * bot_mask).rolling(20).sum() / bot_mask.rolling(20).sum().clip(lower=1)
    return v_high - v_low
```

**预期 metrics**（基于 paper 月频结果 + csi1000 daily 经验衰减系数 ≈ 0.5）：
- 期望 IC ≈ −0.025 ~ −0.040
- 期望 ICIR ≈ −0.30 ~ −0.50
- 关键 check: max_corr vs F001 (second-moment vol) / F025 (shadow_asymmetry_tsrank_60) — 应 < 0.30
- 关键 check: style_R² (vol_20d basis) — 应 ≤ 0.20（不被 vol_20d 吞噬）

### Idea 2 — DSL 软逼近（rank-weighted 替代 hard 25% 切割）

```
Mul(Sub(Div($high, $low), 1), Sub(Mul(TsRank($close, 20), 2), 1))
# = amp · (2 · close_rank − 1)，rank 转 [-1,+1] 取代 hard mask
```

弱于原始版（连续权重 vs 硬切），但**100% DSL** 可达，可作 Phase 1 自检 baseline。若 DSL-soft 跑出 |IC|≥0.015 + α_surv≥0.40，即可作为 Python-wrapper 版本的功效下界证明。

### Idea 3 — TsRank≥60d 化（P008 escape 复合）

把 N 从 20 调到 60 + 把 final 输出再 TsRank-60d：
```
TsRank(<Idea 2 expression>, 60)
```
形式上叠加 P008 完整三条件（dim-less ratio + microstructure-only-on-amp + TsRank≥60d），但**改写了 paper 原始时间尺度**——属探索性变体，与 Idea 1 形成 RHS 替代对照。

### Idea 4 — Cross-section 增强（rank-diff 工艺嵌套）

```
Sub(CsRank(<Idea 1 输出>), CsRank(F009))  # F009 overnight_intraday_spread
```
把理想振幅与 F009 做 CsRank 差，测是否在 rank 空间携带 F009 之外的 incremental signal。Phase 2 实测 incr_ic 决断。

## Direction Mapping

新建 direction `price_conditional_amplitude`（paper-vetted, exploring, priority=medium）。

**避坑**：
- N=20 落在 P008 边界外（P008 律要求 ≥60d）—— Idea 3 是 P008-aligned 变体
- "高/低 − 1" 是 dim-less ratio，规避 cap-denominator 律 (P016)
- close_rank 不会形成 cap-denominator
- Python wrapper 路径已 codify 但库 0 admit (library_gap/018) — 此候选若 admit 也是该路径首例

**风险**：paper 在 csi500 月频报 ICIR=-2.39 是月频聚合后的"放大"指标 — daily 实测大概率衰减到 ≤ -0.50。低于 admission floor 0.10 不奇怪（仍有 reserve 价值，可作 Idea 2/3/4 反复变体的基线）。
