# Consolidation Packet — directions/stochastic_position.md

## Current content

---
direction_tag: stochastic_position
status: saturated
priority: low
rounds: 2
admits: 0
last_batch: batch_041
last_admits: []
last_goal: 'T001+T002 classic stochastic oscillator family not yet in library. Probe
  %K (close position in rolling high-low range) at 20d/60d windows; TsRank variants;
  high-low range vs close-close range. Critical gate: max_corr@F009 < 0.7 to avoid
  reversal cluster near-dup.'
last_activity: '2026-04-24T01:21:05Z'
created_batch: batch_041
members: []
merged_into: null
---
# stochastic_position

> [!abstract]+ 方向概要
> - **状态**　🟠 `saturated` · priority `low` · rounds = 1 · admits = 0
> - **最近**　[[batches/batch_041/judge|batch_041]]：0 admit / 2 reserve / 4 reject — T001+T002 两条主 thread 同批 DISPROVEN
> - **一句话**　close 在 rolling N 日范围内的位置 — 在 csi1000 csi1000 OOS 下 rank-order 系统性崩塌，方向族被 vol_20d 吞噬

---

## Hypothesis

当前库 13 个 admits 形态覆盖：Std/Mean ratio, Div, Mean of body/return, Mul of sign/log, VWAP spread。**未覆盖形态**：TsMin/TsMax（时序极值）+ TsRank（时序排名）。

classic stochastic oscillator %K = `(close - Min_N(low)) / (Max_N(high) - Min_N(low))` 捕获**价格在 rolling N 日高低位置**。经济直觉：
- 高 %K (≥0.8)：close 接近 rolling high = momentum 状态，可能延续或回撤
- 低 %K (≤0.2)：close 接近 rolling low = oversold，可能反弹或继续下跌
- 不同于 `intraday_price_formation` T001 测过的单日 `(close - low) / (high - low)`——本方向 **跨多日** 范围

csi1000 特征：
- 单日内 close position 已证 mono_sign_flip（日内对称抵消律）
- 多日 rolling 范围可能 regime-dependent
- 2021-2023 regime shift 使 raw momentum 失效——%K 作为"位置"指标不直接是 momentum，可能躲过 2023 衰减

**[batch_041 证伪]** hypothesis 两条都证伪：(1) %K 在 csi1000 OOS **不**是稳定反转信号；(2) 机制**不**独立于 OHLC shape 簇（F006-F009 相关 0.42–0.49）。日内"对称抵消律"在跨日 rolling 形式下**仍然成立**——升格为 [[lessons]] 方向族级事实。

---

## Current Focus

方向已 saturated。唯一剩余的活路是 T003（vol_20d orthogonalization salvage），但依赖未实现的算子或 barra_residual_signal 工具链；短期不在 mining loop 范围内。

---

## Threads

### T001: 经典 stochastic %K [✗ DISPROVEN batch_041]

> [!failure]+ Thread 结论
> **Question**: (close - TsMin(N)) / (TsMax(N) - TsMin(N)) 在 20d/60d 窗口是否携带独立 alpha？
>
> **Evidence trail**:
> - [[batches/batch_041/candidates/C001|batch_041 C001]]　%K 20d low/high — mono 0.90→0.10, ls_t_oos=0.15, incremental_ic=-0.014 → **reject**
> - [[batches/batch_041/candidates/C002|batch_041 C002]]　%K 60d low/high — mono 0.6→-0.4, ls_t_oos=-0.20, cum_mdd=-55.9 → **reject**
> - [[batches/batch_041/candidates/C005|batch_041 C005]]　%K 20d close-only — mono 1.00→0.40 (本批最优), ls_t_oos=1.09, vol_20d exposure=16.5 → **reserve**
> - [[batches/batch_041/candidates/C006|batch_041 C006]]　Mean(%K 20d, 5) — mono 0.9→-0.4, ls_sharpe 2.13→-0.60 符号翻盘 → **reject**
>
> **Conclusion**: 4 个子形式（20d low/high, 60d low/high, 20d close-only, 5d 平滑）覆盖经典 %K 设计空间，全部在 OOS rank-order 崩塌（mono_oos ≤ 0.40）且 incremental_ic 全部为负。20d 窗口略好于 60d，close-only 边界略好于 low/high 边界，但都不达标。

### T002: TsRank 形态 [✗ DISPROVEN batch_041]

> [!failure]+ Thread 结论
> **Question**: TsRank($close, N) 是否与 %K 形态等价 or 正交？
>
> **Evidence trail**:
> - [[batches/batch_041/candidates/C003|batch_041 C003]]　TsRank($close, 20) — mono 0.7→0.0, Q2 独高奇异结构, incremental_ic=-0.021 → **reject**
> - [[batches/batch_041/candidates/C004|batch_041 C004]]　TsRank($close, 60) — mono 0.7→-0.3, residual_icir=-0.399 (本批最强), cum_mdd=-62.6 → **reserve**
>
> **Conclusion**: TsRank 与 %K **机制等价**（非正交），两者共享被 vol_20d + OHLC shape 簇吸收的宿命。C004 Barra residual_icir=-0.399 是本批最强残差信号，但 raw mono 翻号使 reserve 仅作 T003 的种子使用。

### T003: vol_20d orthogonalized %K 残差 🆕 [◉ ACTIVE]

> [!note]+ Thread 当前
> **Question**: 对 vol_20d 正交化后的 %K/TsRank 残差是否能在 csi1000 OOS 恢复 rank-order？
>
> **Evidence trail**:
> - _依赖 Python 端未实现的 `orthogonalize` 算子或 `barra_residual_signal` 工具链_
> - 线索: C005 alpha_survival=1.16（控 Barra 后 residual 反而更强）; C004 residual_icir=-0.399
>
> **Next probes**: 阻塞于工具链建设；在工具可用前方向挂起。若 salvage 成功，仅作为"%K after vol 脱敏"而非独立方向。

---

## Known Failures

- batch_041 C001 `Div(Sub($close, TsMin($low, 20)), Sub(TsMax($high, 20), TsMin($low, 20)))` — mono_oos 崩塌 + incremental_ic 负
- batch_041 C002 `Div(Sub($close, TsMin($low, 60)), Sub(TsMax($high, 60), TsMin($low, 60)))` — mono_oos 翻号, cum_ic_mdd=-55.9
- batch_041 C003 `TsRank($close, 20)` — mono_oos 扁平, 奇异"中间独大" Q-pattern, incremental_ic 负
- batch_041 C006 `Mean(Div(Sub($close, TsMin($low, 20)), Sub(TsMax($high, 20), TsMin($low, 20))), 5)` — mono_oos 翻号, ls_sharpe 符号翻盘

---

## Narrative Log

### 2026-04-24 [[batches/batch_041/judge|batch_041]]
0 admit / 2 reserve (C004 C005) / 4 reject — 方向首批即 saturated。

**核心发现**：
1. **rank-order 系统性崩塌**：6 候选 IS mono 平均 0.80，OOS mono 平均 -0.10；5/6 candidates mono_oos ≤ 0.40，3/6 符号翻盘。这不是个案，是方向机制级证伪。
2. **vol_20d 吞噬定律**：6/6 候选 dominant_style=`vol_20d`，exposure 8.7–16.5（压倒性），style_crowding_risk=high。%K 在 csi1000 本质是波动率代理。
3. **OHLC shape 簇冗余**：6 候选对 F006-F009 相关 0.28–0.49，同空间非独立 — 与 `intraday_price_formation` saturated 结论对偶（单日 price position 失效）共同升格为方向族级 lessons："price position" 指标无论跨日与否都在 csi1000 失效。

**Thread 进展**：
- T001 经典 %K：DISPROVEN（4/4 子形式都崩）
- T002 TsRank：DISPROVEN（2/2 子形式崩，与 %K 机制等价非正交）
- T003 🆕：vol_20d 正交化残差 salvage — 阻塞于工具链

**下一步**：
- `status: exploring → saturated` · `priority: medium → low` · 切换方向
- 本方向升格经验写入 [[lessons]]：price position 指标族在 csi1000 被 vol_20d 吞噬
- 保留 C004/C005 reserve 等 orthogonalize 工具到位后取残差再测

---

## Related

- 🟡 [[intraday_price_formation]] `saturated` — 单日 `(close - low)/(high - low)` mono_sign_flip；与本方向互为对偶
- 🟡 [[ohlc_temporal_aggregation]] `saturated` — F006-F008 是 body/shadow 聚合；本方向与其 cluster 相关 0.28–0.49
- 📖 [[lessons#Operator Registry]] — TsMin/TsMax 自定义算子，C.kernels=1 保证
- 📖 [[lessons#Threshold Calibration]] — 本批无校准触发（batch_040 admit 破零-admit streak；reserve 未达独立性条件）


## Instructions

Rewrite this direction md to compress long narrative logs, dedupe threads, and preserve Hypothesis + active Threads + Narrative Log (truncated to most recent 20 entries). Do not touch the frontmatter — Python manages that.
