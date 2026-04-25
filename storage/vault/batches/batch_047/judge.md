---
batch_id: batch_047
direction: microstructure_illiquidity
judged_at: 2026-04-25T04:00:00Z
candidates:
  - {candidate_id: C001, verdict: admit, factor_name: amihud_turnover_cv_rank_diff_20}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reserve}
batch_summary: {total: 6, admit: 1, reserve: 1, reject: 4}
admit_count: 1
reserve_count: 1
reject_count: 4
candidate_count: 6
mt_bucket: high
---

# batch_047 Judge Summary

> [!abstract]+ [[directions/microstructure_illiquidity]] · 6 candidates
> ✅ **admit=1** (C001 → amihud_turnover_cv_rank_diff_20) · ⏸ **reserve=1** (C006) · ❌ **reject=4**
> **核心发现**: **T007 rank-diff 范式泛化首锤兑现** —— C001 把 F015 `CsRank(Amihud) - CsRank(amount_CV)` 的分母端字段从 amount_CV 换成 turnover_CV，保留两端 scale-free 属性，产出 ic_oos=0.050 ls_t=6.76 mono_oos=1.0 incr_ic=0.023 alpha_surv=0.58 9/9 年全正，证实 rank-diff 结构是 signal-family-组合的几何性质，不限于特定字段对。
> **T007 范式边界同时被 C002/C003 收窄**：跨 direction rank-diff 泛化时若两端 **raw field 共振**（C002 $amount 共分母）或**一端被库因子吸收主导**（C003 amount_CV 端被 F001 占）会让 Sub 操作抵消主效应退化为 noise（C002）或 signed negative incr_ic（C003）。
> **T005 短窗复活条件 (a) 硬证伪**: C005 5d up-day Amihud alpha_surv=0.149 severe poor + max_corr 仍 0.754@F012；C006 5d range Amihud 9/9 年同号但 corr=0.862 逼近硬闸 reserve。短窗不 escape F012 引力。
> **设计范式升格 1**: rank-diff Sub(A,B) 与 Sub(B,A) 是数学对偶（C001/C004 完美反号），generator 层应 pre-dedup。
> **MT Budget**: cumulative 240 → **246** · direction 18 → **24** · bucket `high`（search_adjusted medium, C001 strong 档保留）

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ✅ admit | 🟢·🟢·🟡·🔴·🟢 | IC=+0.0495 mono=+1.0 ls_t=+6.76 incr=+0.023 max_corr=0.734@F015 | T007 字段替换泛化兑现 | [[batches/batch_047/candidates/C001]] · [[factors/F016]] · F{id}@Phase4 |
| C002 | ❌ reject | 🔴 hard_gate | ic_oos=\|-0.0074\|<0.008 noise | $amount 共分母让 rank-diff Sub 抵消 | [[batches/batch_047/candidates/C002]] |
| C003 | ❌ reject | 🟡·🟢·🟢·🔴·🟢 | IC=-0.043 mono=-1.0 incr=**-0.0038** max_corr=0.692@F001 | 跨 direction 最远 rank-diff 被 F001 吸收主导端 | [[batches/batch_047/candidates/C003]] |
| C004 | ❌ reject | — | C001 数学反号对偶 (incr=-0.0233) | Sub(A,B)=-Sub(B,A) 同批 anchor rule | [[batches/batch_047/candidates/C004]] |
| C005 | ❌ reject | 🟡·🟢·🔴·🔴·🟢 | IC=+0.020 alpha_surv=**0.149** max_corr=0.754@F012 incr=0.005 | T005 ≤5d 短窗 alpha_surv severe poor | [[batches/batch_047/candidates/C005]] |
| C006 | ⏸ reserve | 🟡·🟢·🟡·🔴·🟢 | IC=+0.041 ls_t=+5.77 alpha_surv=0.484 max_corr=**0.862**@F012 incr=0.022 | Amihud range 与 level 共变 86% 库集中度风险 | [[batches/batch_047/candidates/C006]] |

## 跨候选对比

- **C001 admit vs C004 reject — Sub 方向对偶硬证据**: 数学上 `Sub(A,B) = -Sub(B,A)`，两者数值完全反号（C001 mono=+1.0 IC=+0.050 vs C004 mono=-1.0 IC=-0.050）。同批 anchor rule 严格执行：选 signed-positive-incr_ic 的 C001 admit，C004 自动 reject。**升格教训**: 未来 rank-diff 候选设计只需枚举 Sub(A,B) 一个方向（按 hypothesis 方向约定），generator 层可 pre-dedup Sub 反向变体，节省候选 slot。

- **C001 admit vs C002/C003 reject — T007 范式边界收窄**: C001 (**同 direction 内字段替换**, Amihud × amount_CV → Amihud × turnover_CV) admit; C002 (**跨 direction 但分母 $amount 共振**, pb/amount vs Amihud) hard_gate noise; C003 (**最远跨 direction**, amount_CV × overnight_gap) signed negative incr_ic。三级退化证明 rank-diff 范式可行空间是**同 direction 内部 scale-free × scale-free 字段对换**；跨 direction 越远越容易被主导端吸收或分母共振抵消。

- **C001 admit vs C006 reserve — rank-diff 结构 > non-linear transform 结构**: C001 (rank-diff) max_corr=0.734@F015, incr_ic=0.023 admit; C006 (range = max-min) max_corr=0.862@F012, incr_ic=0.022 reserve。两者 incr_ic 几乎相等但 C006 corr 高 0.13——rank-diff 的信息提炼效率高于 non-linear level-transform。

- **C005 T005 短窗复活条件 (a) 硬证伪**: batch_046 升格教训 "≤ 5d 短窗可破 20d 对称化抹平" 本批第一锤**硬证伪**——5d up-day Amihud max_corr 从 20d 的 0.942 降到 0.754（asymmetry 部分存在），但 alpha_survival 反塌到 0.149 (F012 0.443 的 34%), ic_oos 仅 0.020 是 F012 的 60%。短窗**减少对称化抹平**但**放大 noise + 同样 vol-coupling**——trade-off 负面。T005 复活 (a) 条件建议升格为 disproven，仅留 (b) "quantile-based asymmetry (非 mean)" 待验证。

- **方向兑现**: 1 admit / 6 candidates, admit 命中率 17%（与 batch_046 同）；本批 C001 admit 质量**略弱于** F015 (alpha_surv 0.58 vs 0.66, mdd -1.57 vs -1.61 近似, split_dispersion 0.10 vs 0.11 略优); 但机制价值高——rank-diff 泛化首锤兑现。

## Thread 进展

> [!success]+ T007 [[directions/microstructure_illiquidity#T007]] — `[◐ PARTIAL-ANSWERED batch_047]`
> **rank-diff 跨 signal family 泛化验证**：
> - C001 (分母字段替换 amount_CV → turnover_CV) → **admit** → amihud_turnover_cv_rank_diff_20。证实 rank-diff 结构是 signal-family-组合的几何性质，不限于特定字段对。
> - C002 (跨 direction pb_amount vs Amihud) → hard_gate noise。T007 范式第一个约束：rank-diff 跨 direction 时需 raw field-level 独立（$amount 共分母会抵消）。
> - C003 (最远跨 direction amount_CV vs overnight) → signed negative incr_ic reject。T007 范式第二个约束：一端被已有库因子主导吸收时 rank-diff 退化为主导端反号，signed incr_ic 为负。
>
> **结论**: T007 范式可行空间**收窄**为"同 direction 内部 scale-free × scale-free 字段对换"。下轮可测:
> - Amihud × correlation-based 测度（如 `Corr($close, $amount, 20)`）—— 两端都是无量纲统计量
> - 库内其他 scale-free 对: F011 (overnight) × F015-scale；F007 (upper shadow) × F008 (open position) rank-diff 等
> - "field-level 独立 + scale-free" 双条件的跨 direction 候选（绕开 $amount 共分母）
>
> Thread 改 ACTIVE（partial answered），未关闭。

> [!failure]+ T005 [[directions/microstructure_illiquidity#T005]] — `[✗ FURTHER-DISPROVEN batch_047]`
> **≤5d 短窗 sign-conditional 复活条件 (a)**: C005 硬证伪——5d up-day Amihud alpha_survival=0.149 severe poor，max_corr 0.754 仍 high。减少 20d 对称化抹平但同步放大 noise + vol-coupling 不减。
> **非 mean aggregation 测度 (max-min range)**: C006 reserve——5d Amihud range 与 F012 level 共变 86%，range-based 测度不足以从 level 引力 escape。
> **T005 复活条件剩余**: (a) 短窗证伪；(max-min range 证伪)。仅 **quantile-based asymmetry (P90-P10)** 未测——这是 T005 唯一可能复活的 DSL 层路径；minute-bar 数据未来若接入可重开 symmetric vs sign 测试。
> Thread 建议改 ✗ DISPROVEN (a) 条件, 保留 ACTIVE 等 quantile 测试。

## 方向级反思

`microstructure_illiquidity` 方向**连续两批 productive (batch_046 + batch_047)**，admits 从 2→3 (F012, F015, C001-to-be)。核心驱动是 rank-diff 结构的可泛化性：

- **batch_046**: rank-diff 首次兑现（F015 Amihud × amount_CV）——"signal family 组合的几何性质"
- **batch_047**: rank-diff 泛化验证（C001 Amihud × turnover_CV）——"字段替换保持 scale-free 仍产出独立 alpha"

**风险旗标**:
- **库集中度**: F012 (Amihud level) + F015 (rank-diff amount_CV) + C001 (rank-diff turnover_CV) 三者都在 Amihud 轴 —— microstructure_illiquidity 方向库已占 3/14 slots 的 21%；若继续 admit Amihud 近亲，需 portfolio 层 Barra neutralize 或考虑 retire alpha_surv 最弱者（当前 F012 0.443 最弱）。
- **vol_20d exposure 逐步上升**: F012 exposure=5.9 → F015=18.3 → C001=30.2 — 单调上升，说明 rank-diff 引入更强 vol 耦合；portfolio 层 Barra neutralize 优先级升级。
- **MT bucket high** (cumulative 246, direction 24) — search_adjusted medium, C001 strong 档保留但需警觉多重检验通胀。

**设计范式升格到 lessons 候选**（Phase 5 consolidation 待确认）:
1. **"rank-diff Sub 方向对偶律"**: `Sub(A,B)` 和 `Sub(B,A)` 是数学完全反号对偶（|corr|=1），admit 两者等价于 double counting。generator 层应 pre-dedup。
2. **"rank-diff 跨 direction 泛化 2 约束"**:
   - raw field-level 独立（两端分母/分子不得共享 raw field 如 $amount）
   - 库内主导因子预测（若一端被已有库因子吸收主导，rank-diff 退化为主导端反号）

**方向操作**: status `productive` 保留；priority `medium` 保留；rounds 3→4；admits 2→3（F012, F015, C001-to-be）。T007 partial answered 保留 ACTIVE; T005 (a) 条件 disproven 保留 ACTIVE 等 quantile 测试。**下轮 T007 聚焦** Amihud × correlation-based 测度（如 `Corr($close, $amount, 20)`）或库内其他 scale-free 对的 rank-diff。

**Calibration**: 无错杀侦测——
- C006 reserve 非错杀（alpha_surv 0.484 边缘 + max_corr 0.862 实质库吸收）
- C005 reject 非错杀（alpha_surv 0.149 default 阈值 0.40 的 37%，距离 calibration 触发线甚远）
- C002 C004 hard_gate fail/数学对偶 清晰
- C003 signed negative incr_ic reject 清晰 (admit 会稀释库)

本批 admit=1 延续 direction productive 势头，zero_admit_streak 保持 0。**无 calibration 需求**。

**MT budget**: cumulative 240 → 246, direction 18 → 24, bucket `high`（search_adjusted 0.9 → 0.53 medium, C001 strong 档无需进一步降档）。
