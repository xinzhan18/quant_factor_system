---
batch_id: batch_006
direction: value_liquidity_interaction
judged_at: 2026-04-19T13:55:00Z
candidates:
  - {candidate_id: C001, verdict: reserve}
  - {candidate_id: C002, verdict: reserve}
  - {candidate_id: C003, verdict: reserve}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
batch_summary: {total: 5, admit: 0, reserve: 3, reject: 2}
---

# batch_006 Judge Summary

> [!abstract]+ batch_006 · [[directions/value_liquidity_interaction]] · 5 candidates
> ✅ **admit=0** · ⏸ **reserve=3** (C001 PB rate, C002 PS rate, C003 PB/turnover) · ❌ **reject=2** (C004 alpha_survival=0.0009 极端, C005 乘法结构第 5 次证伪)
> **核心发现**: **T006 通用性三点对照成立** — PE rate (C004_b5 alpha_surv=0.92) / PB rate (C001 =0.79) / PS rate (C002 =0.72) 均通过方向 dealbreaker + dom=**str_1m**，证明"基本面字段 `Div(Delta(X), X)` 自归一化速率"**跨 3 个 valuation 指标普适**跳出 vol_20d 天花板。**T001 分母去市值路径证伪**：C003 vs C005_b5 将 $amount 换 $turnover_rate 后 alpha_survival 0.30→0.28 未改善，vol_20d exposure 从 4.57 飙到 25.23——positive edge 真实（非 size 代理）但 `PB / liquidity` 结构与 vol_20d 天然共存。**C004 极端悖论**：style_r²=0.08 (clean) + alpha_survival=0.0009 同时出现，证明"低 style_r² ≠ Barra-clean"——因子 IC 完全在 Barra 子空间内运动。**乘法结构第 5 次证伪** (C005)：level 端量纲永远吞噬 rate 端独立性。
> **MT Budget**: cumulative 28 → **33** · direction 5 → **10** · 本批 bucket: C001/C002 low(search=medium), C003/C004 medium(search=high), C005 medium

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ⏸ reserve | 🟢·🔴·🟡·🟢·🟡 | ICIR_oos=-0.213 ls_t=-1.49 alpha_surv=**0.79** dom=**str_1m** | T006 通用性第 2 证据（PB rate）复刻 C004_b5 PE rate 结构；ls_t 弱 + Q5 一桨 | [[batches/batch_006/candidates/C001]] |
| C002 | ⏸ reserve | 🟢·🔴·🟡·🟢·🟢 | ICIR_oos=-0.208 ls_t=-1.47 alpha_surv=**0.72** dom=**str_1m** | T006 通用性第 3 证据（PS rate）与 C001/C004_b5 形态几乎全同 | [[batches/batch_006/candidates/C002]] |
| C003 | ⏸ reserve | 🟡·🟡·🔴·🟢·🟢 | ICIR_oos=**+0.238** ls_t=+1.85 alpha_surv=0.28 cum_dd=**-2.64** vol_20d=25.2 | C005_b5 denom fix — positive edge 真实（非 size 代理）但 vol_20d 暴露反增；T001 分母去市值路径证伪 | [[batches/batch_006/candidates/C003]] |
| C004 | ❌ reject | 🔴·🔴·🔴·🟡·🟢 | ICIR_oos=+0.284 ls_t=**+0.20** alpha_surv=**0.0009** style_r²=0.08 | 极端悖论：style_r² clean 但 alpha_survival 近零；IC 完全在 Barra 子空间运动 | [[batches/batch_006/candidates/C004]] |
| C005 | ❌ reject | 🔴·🔴·🔴·🟢·🟡 | ICIR_oos=-0.193 ls_t=-1.77 alpha_surv=**0.29** dom=vol_20d | 乘法 rate × level 第 5 次证伪：C004_b5 PE rate alpha_survival 从 0.92 崩塌到 0.29 | [[batches/batch_006/candidates/C005]] |

## 跨候选对比

- **T006 三点通用性确立**：PE rate (C004_b5: alpha_surv=0.92 ls_t=-1.22 dom=str_1m) / PB rate (C001: 0.79 / -1.49 / str_1m) / PS rate (C002: 0.72 / -1.47 / str_1m) — 三点形态几乎**精确复刻**。"基本面字段自归一化变化率跳出 vol_20d 天花板" **不是 PE 孤证**，而是**跨 valuation 指标的普适机制**。这是方向最重要的结构发现。**但 ls_t 三点都弱 (-1.2 到 -1.5)**：rank-order hypothesis 成立但 PnL 可交易性未证。下轮需合成（PE+PB+PS 等权 rank）+ str_1m 正交化升级。
- **T001 C003 vs C005_b5 诊断实验**：分母 $amount → $turnover_rate 后 IC/mono/cum_dd 全部保留（positive edge 真实），但 alpha_survival 0.30→0.28 未改善、vol_20d 暴露 **5.5×放大** (4.57→25.23)。诊断结论：**C005_b5 的 positive edge 不是市值代理，但 `PB / smoothed_liquidity` 结构天然与 vol_20d 共存**。分母去市值路径证伪。
- **乘法结构第 5 次证伪**：C001_b5/C002_b5/C003_b5 (三个 Mul 乘) + C005_b6 (Mul rate × level) — **任何 Mul(rate_or_orthogonal, level) 都被 level 端量纲吞噬独立性**。无一例外。这是跨 batches 的跨方向普适失败模式。
- **C004 极端悖论启示**：`Div($pe, Mean(turnover, 20))` 产出 style_r²=0.08（名义 clean）+ alpha_survival=0.0009（极端 poor）+ ls_sharpe 衰减 97%。教训：**低 style_r² ≠ barra-clean**。截面因子**值**的方差不被 styles 解释，不等于预测**方向**独立于 styles。直接看 alpha_survival 才是硬指标。
- **C003 稳定性悖论**：cum_dd=-2.64（全库最浅级）+ 9 年 IC 全正 + split_dispersion=0.087（顶级稳）——稳定性来自 vol_20d 风格的时序稳定性，是 Barra-tainted 因子的 anti-signal。
- **MT 预算**：cumulative 28→33（仍 low），direction family term 提升（5 候选全在"分子基本面字段"family）；search_adjusted 对 C003/C004 到 high。

## Thread 进展

> [!success]+ T006 [[directions/value_liquidity_interaction#T006]] — `[✓ ANSWERED batch_006]`（通用性 rank-order 层）
> 三基本面字段（PE/PB/PS）自归一化速率通用性验证：alpha_survival 0.92/0.79/0.72、dom=str_1m、ls_t 弱（-1.22/-1.49/-1.47）。hypothesis 在 rank-order 层成立；PnL 层待升级（合成 + str_1m 正交化）。

> [!failure]+ T001 [[directions/value_liquidity_interaction#T001]] — 分母去市值子路径 `[✗ DISPROVEN batch_006]`
> C003 vs C005_b5 诊断：分母 $amount→$turnover_rate 不改善 Barra ceiling（alpha_survival 0.30→0.28，vol_20d 反增 5.5×）。positive edge 真实但与 vol_20d 天然共存。

> [!failure]+ T003 [[directions/value_liquidity_interaction#T003]] — 乘法升级子路径 `[✗ DISPROVEN batch_006]`
> C005 `Mul(PE_rate, Mean(tr))` alpha_survival 从 C004_b5 的 0.92 崩塌到 0.29 — rate × level 乘法彻底摧毁 rate 独立性。T003 升级只能走秩差或双 rate 除法结构。

## 方向级反思

**方向达到重要转折点**（4 batches / 13 candidates / 0 admit）：
- **rank-order 层突破已确定**：T006 三点通用性 + C005_b5 positive edge 真实性 = 方向确实存在**独立于 Barra 流动性风格的 value alpha**
- **L/S PnL 层尚未兑现**：所有 rank-order 成立候选 ls_t < 2，不可独立 admit
- **机制清晰但工程未突破**：清楚哪些结构行（自归一化变化率）哪些不行（乘法、去市值分母），但需要"合成 + 正交化"工程步骤才能把 rank-order 优势转化为 PnL

**下轮决策树（batch_007）**：
- **方案 A**：T006 合成变体 —— `Sub(Add(Add(PE_rate, PB_rate), PS_rate), Mul(Mean(turnover), 3))` 类 3-基本面平均 rate + str_1m 近似正交化
- **方案 B**：秩差结构 —— `Sub(CsRank(PE_rate), CsRank(Mean(turnover)))` 秩差放大基本面 rate 相对于流动性的差异信号
- **方案 C**：高阶 positive signal 探索 —— `Div($ps, Mean($turnover, 20))` / `Div(Add($pe, $pb), Mean(turnover, 20))` 变 denominator fix
- **方案 D**：暂停方向，尝试 Python 逃生口做 C004_b5 + C005_b5 + C003 合成 Barra residual (R8 trigger)

**status**: exploring → 继续 exploring（rank-order 突破足够显著，不降 saturated）；priority 保持 high

**跨方向元教训（累计 5 batches / 3 directions / 33 candidates）**：
- **普适规则 1**: `Mul(A, B)` 结构 = level 量纲主导吞噬独立性（6 次独立证伪）
- **普适规则 2**: `Div(fundamental, smoothed_liquidity)` = 与 vol_20d 天然共存（非代理而是结构性）
- **普适规则 3**: `Div(Delta(X), X)` 自归一化速率 = 跳出 vol_20d 的唯一 DSL 结构（已 3 点验证）
- **普适规则 4**: 低 style_r² ≠ barra-clean；alpha_survival 才是硬判据
- **开始触发 R8 条件**：Python 逃生口做 Barra residual 的必要性累积到"不做就无法推进"水平
