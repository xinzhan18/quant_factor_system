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
> - **状态**　🟠 `saturated` · priority `low` · rounds = 2 · admits = 0
> - **最近**　[[batches/batch_041/judge|batch_041]]：0 admit / 2 reserve / 4 reject — T001+T002 两条主 thread 同批 DISPROVEN
> - **一句话**　close 在 rolling N 日范围内的位置——在 csi1000 OOS 下 rank-order 系统性崩塌，方向族被 vol_20d 吞噬

---

## Hypothesis

当前库未覆盖形态：TsMin/TsMax（时序极值）+ TsRank（时序排名）。classic stochastic %K = `(close - Min_N(low)) / (Max_N(high) - Min_N(low))` 捕获价格在 rolling N 日高低位置。经济直觉：高 %K (≥0.8) = momentum 状态；低 %K (≤0.2) = oversold；不同于 `intraday_price_formation` 单日 `(close - low) / (high - low)`，本方向**跨多日**。

**[batch_041 证伪]** 两条 hypothesis 都证伪：(1) %K 在 csi1000 OOS **不**是稳定反转信号；(2) 机制**不**独立于 OHLC shape 簇（与 F006-F009 相关 0.42–0.49）。日内"对称抵消律"在跨日 rolling 形式下**仍然成立**。

**Hypothesis ⚠️（F301 / F306 升格）**：
- **vol_20d 吞噬律**：%K / TsRank 与 magnitude / 2nd-moment / quantile / power-mean 同源，6/6 候选 dominant_style=`vol_20d` (exposure 8.7–16.5)。在 csi1000 daily-bar 本质是 vol 代理，`alpha_survival < 0.30` 是默认宿命。逃离路径仅三条：(a) 不同时间频率（intraday/minute），(b) 不同信号源（microstructure/fundamental/signed direction），(c) 非 rank 空间（true Barra residual / portfolio ensemble）。
- **price position 跨日仍失效**：与 `intraday_price_formation` 的"单日对称抵消默认律"互为对偶——price position 指标无论跨日与否都在 csi1000 失效。Phase 1 设计时默认期望 mono_sign_flip。

---

## Current Focus

方向已 saturated。唯一剩余的活路是 T003（vol_20d orthogonalization salvage），但依赖未实现的 `orthogonalize` 算子或 `barra_residual_signal` 工具链；且需先解决 F010 coverage<0.80 限制。短期不在 mining loop 范围内。

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
> **Conclusion**: 4 个子形式覆盖经典 %K 设计空间，全部在 OOS rank-order 崩塌（mono_oos ≤ 0.40）且 incremental_ic 全部为负。20d 窗口略好于 60d，close-only 边界略好于 low/high 边界，但都不达标。

### T002: TsRank 形态 [✗ DISPROVEN batch_041]

> [!failure]+ Thread 结论
> **Question**: TsRank($close, N) 是否与 %K 形态等价 or 正交？
>
> **Evidence trail**:
> - [[batches/batch_041/candidates/C003|batch_041 C003]]　TsRank($close, 20) — mono 0.7→0.0, Q2 独高奇异结构, incremental_ic=-0.021 → **reject**
> - [[batches/batch_041/candidates/C004|batch_041 C004]]　TsRank($close, 60) — mono 0.7→-0.3, residual_icir=-0.399 (本批最强), cum_mdd=-62.6 → **reserve**
>
> **Conclusion**: TsRank 与 %K **机制等价**（非正交），共享被 vol_20d + OHLC shape 簇吸收的宿命。C004 Barra residual_icir=-0.399 是本批最强残差信号，但 raw mono 翻号使 reserve 仅作 T003 的种子使用。

### T003: vol_20d orthogonalized %K 残差 [◉ BLOCKED]

> [!note]+ Thread 当前
> **Question**: 对 vol_20d 正交化后的 %K/TsRank 残差是否能在 csi1000 OOS 恢复 rank-order？
>
> **Evidence trail**:
> - 阻塞于 Python 端未实现的 `orthogonalize` 算子或 `barra_residual_signal` 工具链
> - 进一步阻塞：F010 Python residual coverage<0.80 限制；F301 明确"non-rank 空间"是逃离 vol_20d 的唯一途径
> - 线索：C005 alpha_survival=1.16（控 Barra 后 residual 反而更强）；C004 residual_icir=-0.399
>
> **Next probes**: 工具链建设 + coverage 修复双重阻塞；方向挂起。salvage 成功后仅作 "%K after vol 脱敏" 而非独立方向。

---

## Known Failures

- batch_041 C001 `Div(Sub($close, TsMin($low, 20)), Sub(TsMax($high, 20), TsMin($low, 20)))` — mono_oos 崩塌 + incremental_ic 负
- batch_041 C002 `Div(Sub($close, TsMin($low, 60)), Sub(TsMax($high, 60), TsMin($low, 60)))` — mono_oos 翻号, cum_ic_mdd=-55.9
- batch_041 C003 `TsRank($close, 20)` — mono_oos 扁平, 奇异 Q2-独大 pattern, incremental_ic 负
- batch_041 C006 `Mean(Div(Sub($close, TsMin($low, 20)), Sub(TsMax($high, 20), TsMin($low, 20))), 5)` — mono_oos 翻号, ls_sharpe 符号翻盘

---

## Narrative Log

### 2026-04-24 [[batches/batch_041/judge|batch_041]]
0 admit / 2 reserve (C004 C005) / 4 reject — 方向首批即 saturated。

**核心发现**：
1. **rank-order 系统性崩塌**：6 候选 IS mono 平均 0.80，OOS mono 平均 -0.10；5/6 mono_oos ≤ 0.40，3/6 符号翻盘——方向机制级证伪。
2. **vol_20d 吞噬定律**：6/6 dominant_style=`vol_20d`，exposure 8.7–16.5（压倒性）。%K 在 csi1000 本质是波动率代理。
3. **OHLC shape 簇冗余**：6 候选对 F006-F009 相关 0.28–0.49，与 `intraday_price_formation` saturated 结论对偶共同升格为方向族级 lessons。

**Thread 进展**：T001 经典 %K DISPROVEN（4/4 崩）；T002 TsRank DISPROVEN（与 %K 机制等价非正交）；T003 vol_20d orthogonalize salvage 阻塞于工具链。

**下一步**：`status: exploring → saturated` · `priority: medium → low` · 切换方向；保留 C004/C005 reserve 等 orthogonalize 工具到位后取残差再测。

### 2026-04-25 Consolidation 升格
- **F301 (high)** Magnitude/2nd-moment/quantile/power-mean 全部坍缩到 vol_20d——第 5+ 次跨方向独立确认（return_distribution / vol_shock / quantile_shape / amount_volatility / range_structure / 本方向）。已写入 Hypothesis ⚠️。
- **F306 (medium)** OHLC algebraic mirror + 单日对称抵消默认律——price position 跨日仍失效，与 intraday_price_formation 对偶。已写入 Hypothesis ⚠️。
- **F001 (high)** vol_20d 结构性吸收 2nd-moment 空间（跨 8 方向）——T003 路径需先解决 F010 coverage<0.80。
- 建议 status: saturated → archived（F306 promoter 建议）；当前保持 saturated 直到工具链显式 dead。

---

## Related

- 🟡 [[intraday_price_formation]] `saturated` — 单日 `(close - low)/(high - low)` mono_sign_flip；与本方向互为对偶（F306）
- 🟡 [[ohlc_temporal_aggregation]] `saturated` — F006-F008 是 body/shadow 聚合；与本方向 cluster 相关 0.28–0.49
- ⚫ [[return_distribution_signals]] `dead` · [[vol_shock_signals]] `dead` · [[quantile_shape_signals]] `dead` — 同 vol_20d 吞噬律证据链（F301）
- 🟡 [[amount_volatility_signal]] `saturated` · [[range_structure]] `exploring` — 同 F001 律
- 📖 [[lessons#Structural Constraints]] — vol_20d 吸收律（待升格）
- 📖 [[lessons#OHLC Family Defaults]] — 单日对称抵消默认律（待升格 F306）
- 📖 [[lessons#Operator Registry]] — TsMin/TsMax 自定义算子，C.kernels=1 保证
