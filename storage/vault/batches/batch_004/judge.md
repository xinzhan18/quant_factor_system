---
batch_id: batch_004
direction: turnover_structural_signal
judged_at: 2026-04-19T02:40:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reserve}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
batch_summary: {total: 5, admit: 0, reserve: 1, reject: 4}
---

# batch_004 Judge Summary

> [!abstract]+ batch_004 · [[directions/turnover_structural_signal]] · 5 candidates (direction 首批)
> ✅ **admit=0** · ⏸ **reserve=1** (C003 acceleration) · ❌ **reject=4** (C001 hard_gate·near_dup 0.955, C002/C004/C005 soft-CP alpha_survival<0.60 dealbreaker)
> **核心发现 (方向级)**: **"turnover 避开 vol_20d 天花板"hypothesis 被证伪** — 5/5 候选 `dominant_style=vol_20d`；turnover 本身与 vol_20d 强耦合（同为流动性 × 波动率交互代理）。仅 C003 加速度比值 `alpha_survival=1.085` 突破 0.60 dealbreaker（残差 IC 反增强，少见），但 Q5 一桨驱动 + vol_20d 残留（9.07）+ mono_oos=-0.5 borderline → reserve 非 admit。**最大元结论**：换手/成交额/波动率三者在 Barra 空间高度共线，`dominant_style=vol_20d` 不是方向局部问题而是**现行 Barra 坐标系特征**，脱敏真正出路是 Python 逃生口 Barra residual。
> **MT Budget**: cumulative 18 → **23** · direction 0 → **5** (首批) · 本批 bucket: C003 medium, rest 对应 hard_gate/soft_reject · 跨方向累计 search_adjusted 仍 high

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | hard_gate | near_duplicate corr=0.955@F001 | turnover CV ≈ amount CV (shares 短期近常数)；T003 "turnover CV 独立 alpha" 证伪 | [[batches/batch_004/candidates/C001]] |
| C002 | ❌ reject | 🔴·🟡·🔴·🟢·🟢 | ICIR_oos=-0.280 alpha_surv=0.520 vol_20d=25.8 | TsAutoCorr max_corr=0.13 数值独立但 48% IC 被 vol_20d 吞；T001 持久性 hypothesis 证伪 | [[batches/batch_004/candidates/C002]] |
| C003 | ⏸ reserve | 🟢·🟡·🟡·🟢·🟡 | ICIR_oos=-0.320 ls_t=-3.08 alpha_surv=1.085 max_corr=0.27 | 加速度比值唯一突破 dealbreaker (残差反增强)；但 Q5 一桨 + cum_ic_mdd=-73.7 + vol_20d=9.07 残留 | [[batches/batch_004/candidates/C003]] |
| C004 | ❌ reject | 🟡·🔴·🔴·🟢·🟢 | ICIR_oos=-0.296 alpha_surv=0.446 style_r²=0.421 | 规避 amount mono_flip (turnover 对称性) 但引入 str_1m+turnover_20d 三簇共线；T004 耦合路径证伪 | [[batches/batch_004/candidates/C004]] |
| C005 | ❌ reject | 🟡·🔴·🔴·🟡·🔴 | ICIR_oos=-0.238 ls_t=-0.64 vol_20d=41.4 decay=0.46 | CsRank 嵌套 Std 产出批次最高 vol_20d 暴露；IS→OOS 塌方；T005 rank stability hypothesis 证伪 | [[batches/batch_004/candidates/C005]] |

## 跨候选对比

- **方向 hypothesis 全盘被证伪**：direction.md 首段明言"换手率的二阶结构有概率落在不同的 Barra 风格空间"——5/5 候选 dominant_style=vol_20d 证伪该 hypothesis。turnover_rate × 二阶算子（Std/Mean/AutoCorr/加速度/rank std）无一逃离 vol_20d 耦合。
- **Style exposure 量级**：C005=41.4（最大）> C002=25.8 > C003=9.07（最小）> C004=8.20（但叠加 str_1m=4.85 + turnover_20d=4.17 = 三簇共线）。**越是"看似高阶"的构造（AutoCorr、CsRank Std）反而 vol_20d 暴露越高**——因为它们隐式平滑出波动率基线。
- **alpha_survival 谱**：C003=1.08 (clean) > C005=1.59 (反增但触 style_r²=0.275 poor) > C002=0.52 > C004=0.45。注意 alpha_survival>1 不等于干净——C005 的 1.59 是"raw IC 被 vol_20d 部分抵消"的症状，不是独立 alpha 证据。
- **T003 turnover CV 与 T001 turnover CV 名义上冗余**：C001 corr=0.955 @ F001 说明在 A 股 10d 窗口 `Div(Std(X,10), Mean(X,10))` 对 $amount 和 $turnover_rate 产生近同信号——shares_outstanding 短窗近常数，相除抵消。这是**方向决策层的重要教训**：以为"换手率自带规模归一"就能开辟新方向 — 错，CV 构造把这层差异抹掉了。
- **C003 是方向唯一正面证据**：加速度比值 `5d/20d` 形状本身（非水平）产出 alpha_survival=1.08 残差 IC 反增强——指向"变化率"是独立维度而非"水平/波动率"维度。但 Q5 独跌一桨 + 长期回撤 -73.7 说明这个独立性未必实盘可用。
- **MT 预算**：首批方向 direction_candidates=5，family 新起点；跨方向累计 23 候选仍在 low bucket。

## Thread 进展

> [!failure]+ T001 [[directions/turnover_structural_signal#T001]] — `[✗ DISPROVEN batch_004]` 持久性 hypothesis
> C002 TsAutoCorr max_corr=0.13 独立于 F001 但 alpha_survival=0.52 + vol_20d=25.8 被吞。20d 持久性统计被 vol_20d 风格平滑——持久性维度不独立于波动率维度。

> [!note]+ T002 [[directions/turnover_structural_signal#T002]] — `[◉ ACTIVE, ONLY SURVIVOR]` 加速度 hypothesis
> C003 加速度比值 `5d/20d` 是方向唯一突破 dealbreaker 的候选 (alpha_survival=1.085)。保留探索——下轮可尝试 vol_20d residual 版 + Q1-Q4 结构修复（改 long-side 加权）。

> [!failure]+ T003 [[directions/turnover_structural_signal#T003]] — `[✗ DISPROVEN batch_004]` turnover CV hypothesis
> C001 hard_gate near_dup 0.955@F001。A 股 10d 窗口下 turnover CV ≡ amount CV（shares 短窗近常数抵消）。本 thread 作为"独立 alpha 源"被彻底证伪。

> [!failure]+ T004 [[directions/turnover_structural_signal#T004]] — `[✗ DISPROVEN batch_004]` 方向耦合 hypothesis
> C004 Sign(Δclose)×turnover 均值规避了 C006_b1 mono_flip（turnover 对称性生效），但引入 str_1m + turnover_20d 三簇共线 + alpha_survival=0.45 dealbreaker。Mean-of-Signed 不是无代价规避。

> [!failure]+ T005 [[directions/turnover_structural_signal#T005]] — `[✗ DISPROVEN batch_004]` CS-rank stability hypothesis
> C005 Std(CsRank(turnover))_20 产出方向最高 vol_20d 暴露 41.4（讽刺反向）+ IS→OOS decay 0.46 + ls_t=-0.64 塌方。"CS 归一化 + 时序 Std" 组合反而放大了 vol 风格暴露。

## 方向级反思

**方向首批即接近 saturated 边缘**：5 threads → 1 survivor (T002)。整体 hypothesis 的核心前提（"turnover 能脱离 vol_20d 风格空间"）被**证伪**。方向首批就发现核心前提错误，是方向研究效率上的重要一课——**field 切换（amount → turnover）在 Barra 空间里并不对应维度切换**，因为 Barra style 是通过 cross-sectional regression 得到的"风格基"，任何流动性/波动率派生量都会映射到 vol_20d / turnover_20d 这些已有 basis vector。

**方向级决策**：
- 本方向 `status: exploring → saturated`（首批即触发：hypothesis 核心前提证伪，5 threads 4 死）—— 在 Narrative Log 翻态
- 保留 C003 作为 reserve 证据；若后续引入 Python 逃生口 Barra residual，可复活 T002 加速度子路径
- 方向 `priority: high → low`（避免再投算力）

**跨方向元教训（供 Phase 5 consolidation）**：
1. **"field 换方向"是伪装的搜索**：$amount / $turnover_rate / $volume 的二阶统计量在 Barra 空间里是同一维度，开新方向只是换字段不换维度
2. **脱 vol_20d 天花板的唯一物理路径**：Python 逃生口 Barra residual（R8），或跨字段乘法 (e.g. `pe_ratio × turnover_CV`) 引入基本面风格
3. **首批拒否率 = 方向底层 hypothesis 信号**：方向首批 admit 率 0% + alpha_survival<0.60 率 60% 应触发"方向级 hypothesis 检讨"而非"继续尝试变体"

**下轮决策（batch_005）**：暂停本方向，开辟第三个方向 **`value_liquidity_interaction`** — 使用基本面字段 (`$pe_ratio / $pb_ratio / $ps_ratio`) × 流动性 (`$turnover_rate / $amount`) 交互项，目标是引入 ep_ratio / book_to_price / log_circ_cap 风格维度，至少让 dominant_style 摆脱 vol_20d / turnover_20d / str_1m 三元天花板。
