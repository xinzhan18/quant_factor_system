---
batch_id: batch_030
direction: microstructure_illiquidity
judged_at: 2026-04-23T12:00:00Z
candidates:
  - {candidate_id: C001, verdict: admit, factor_name: amihud_illiq_20d}
  - {candidate_id: C002, verdict: reserve}
  - {candidate_id: C003, verdict: reserve}
  - {candidate_id: C004, verdict: reserve}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reserve}
batch_summary: {total: 6, admit: 1, reserve: 4, reject: 1}
admit_count: 1
reserve_count: 4
reject_count: 1
candidate_count: 6
mt_bucket: medium
---

# batch_030 Judge Summary

> [!abstract]+ batch_030 · [[directions/microstructure_illiquidity]] · 6 candidates · **方向首批**
> ✅ **admit=1** (C001 → `amihud_illiq_20d`) · ⏸ **reserve=4** (C002/C003/C004/C006) · ❌ **reject=1** (C005)
> **核心发现**: Amihud illiquidity 30 批后首次引入，20d horizon 打破连续 3 批 0 admit 僵局；同批 HHI 双孪生（C003/C004）incremental_ic 均为负 → F001 已吸收时序集中度维度；TsEntropy 与 HHI 符号相反且 ls_t 弱 → **T003 "单日极值 vs uniform 分布" 对比结题：单日极值驱动**。
> **MT Budget**: cumulative 140 → **146** · direction 0 → **6** · bucket `medium`（medium 档允许 strong 保留，adjusted 后 raw=0.9→0.66 仍 medium）· 本批 low=0 / medium=6 / high=0

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ✅ admit | 🟢·🟡·🟠·🔴·🟢 | IC=0.034 ls_t=4.48 mono=1.0 incr_ic=0.034 max_corr=0.754@F002 | T001 核心突破——Amihud (价格冲击/成交额) 29 批首触 DSL 原语。CP05 high 但 incr_ic 6.7× 阈值 rubric 允许 admit。 | [[batches/batch_030/candidates/C001]] · [[factors/F012]] |
| C002 | ⏸ reserve | 🟢·🟡·🔴·🟡·🟢 | IC=0.027 ls_t=3.58 mono=1.0 alpha_surv=0.43 incr_ic=0.025 | 60d 变体同 thread T001 anchor（与 C001 同源）不可双 admit；CP04 poor 双 style 吞噬。 | [[batches/batch_030/candidates/C002]] |
| C003 | ⏸ reserve | 🟢·🟢·🟡·🟡·🟡 | IC=-0.038 ls_t=-4.02 mono=-1.0 incr_ic=**-0.013** alpha_surv=0.58 | 单体 strong 但 signed incr_ic 负→库稀释；F001 已吸收 amount 时序集中度维度；保留为 T002 artifact。 | [[batches/batch_030/candidates/C003]] |
| C004 | ⏸ reserve | 🟢·🟢·🟡·🟡·🟢 | IC=-0.035 ls_t=-4.08 mono=-1.0 incr_ic=**-0.010** | 与 C003 同机制（HHI 字段替换）; 两者互 anchor。 | [[batches/batch_030/candidates/C004]] |
| C005 | ❌ reject | 🟢·🔴·🟠·🔴·🟡 | IC=0.011 ls_t=1.54 mono=0.8 incr_ic=**-0.001** | CP03 weak + CP05 incr_ic 近零→T003 Entropy 路径证伪；方向性 "HHI 赢 Entropy 输" 结论明确。 | [[batches/batch_030/candidates/C005]] |
| C006 | ⏸ reserve | 🟡·🔴·🔴·🟢·🟢 | IC=0.032 ls_t=1.84 mono=1.0/0.7 max_corr=0.111@F010 incr_ic=0.022 | 库空间独立度整批最佳但 ls_t<2 + CP04 poor；T001 turnover 分母路径次选。 | [[batches/batch_030/candidates/C006]] |

**档位编码**：🟢 最优档 · 🟡 次档 · 🟠 边际 · 🔴 阻断档；`hard_gate` reject 列填 `hard_gate` 不填色。

## 跨候选对比

- **Thread T001 (Amihud 家族 C001/C002/C006)**：**三候选同 dom_style=turnover_20d**，incremental_ic 依次 0.034/0.025/0.022 递减；max_lib_corr 依次 0.754@F002/0.677@F002/0.111@F010。C001 ($amount 分母 20d) 是"高库相关 + 高库增值"的极化组合（靠 incr_ic 硬救），C002 (60d) 是 C001 弱化版 + CP04 poor，C006 ($turnover 分母) 是"低库相关 + 统计弱"（ls_t=1.84 < 2）。**T001 唯一 admit 路径 = C001**；C002/C006 作为 horizon / 字段对照留 reserve。
- **Thread T002 (HHI 家族 C003/C004)**：**两候选 signed incremental_ic 均负**（-0.013 / -0.010），与 F001 相关 0.594/0.597——F001 (amount CV 10d) 已吸收 20d 时序集中度维度。HHI(amount) 和 HHI(turnover_rate) 机制同源（仅字段替换），二者互为 anchor。即使增量转正，按 rubric 也最多 admit 1 个。**T002 admit 路径封闭**。
- **Thread T003 (HHI vs Entropy 代数孪生对比)**：C003 (HHI amount) ls_t=-4.02 完美单调 vs C005 (TsEntropy amount) ls_t=+1.54 mono=0.7——**方向相反 + 量级相差 2.6×**，直接回答 hypothesis 三岔路。**T003 结论：该维度是"单日极端事件驱动"（HHI 赢），不是"分布均匀度驱动"（Entropy 输）**。T003 首批即可 ANSWERED，后续不再在 entropy 变体上追加候选。
- **Style 聚合**：C001/C002/C006（Amihud 族）dom=turnover_20d crowding=high；C003/C004/C005（HHI/Entropy 族）dom=vol_20d crowding=medium。**6/6 候选 dominant_style ∈ {vol_20d, turnover_20d}**——与 29 批累计观察一致，日频 DSL 空间仍被 Barra basis 覆盖。
- **库相关 cluster**：C001 (0.754@F002), C002 (0.677@F002), C003 (0.594@F001), C004 (0.597@F001) 四候选互为 F001/F002 派生；C005 (0.343@F001 符号反向) 是 HHI 的代数孪生；C006 (0.111@F010) 是整批最独立候选但统计弱。
- **MT 预算推进**：cumulative 140→146；direction 0→6；bucket 仍 medium 上界。方向首批直接打满 MT 预算（6/6 候选全通过 hard_gate，无 compute_error），资源效率高。

## Thread 进展

> [!success]+ T001 [[directions/microstructure_illiquidity#T001]] — `[◉ ACTIVE]`
> admit C001（Amihud 20d amount-denom）：29 批首个 DSL microstructure 原语。证实"Amihud illiquidity（price-impact per dollar）是独立于 F001 dispersion 和 vol_20d magnitude 的 alpha 维度"——但独立性来自 incremental_ic=0.034，不是 max_corr（0.754@F002 高）。C002 (60d horizon) / C006 (turnover-denom) 作为 thread 对照 reserve。**Next probes**：residualize C001 by turnover_20d + vol_20d 的纯化变体（因 CP04 borderline 主要被两 style 吞噬）。

> [!success]+ T002 [[directions/microstructure_illiquidity#T002]] — `[✓ ANSWERED batch_030]`
> reserve C003/C004（HHI amount / HHI turnover）：**机制确证存在但库已吸收**。两候选 signed incremental_ic 均负（-0.013/-0.010），F001 (amount CV 10d) 已吸收 20d 时序集中度维度。**Answer**：HHI 是 amount 变异信号的高阶矩孪生，当前库空间无增值位置。Thread 结题为 "机制真实，但冗余"；复活条件 = F001 retire 或 F001-residualized HHI refinement。

> [!failure]+ T003 [[directions/microstructure_illiquidity#T003]] — `[✗ DISPROVEN batch_030]`
> reject C005（TsEntropy amount 20d）：ls_t=1.54 < 2 + signed incremental_ic=-0.001（接近零，无库增值）。方向 hypothesis 设"HHI 赢、Entropy 输 → 单日极值事件驱动"三岔路，本 thread 走到结论：**TsEntropy 作为 HHI 代数孪生效果弱于 HHI 2.6× 量级 + 方向相反 + 库增值近零**，后续 microstructure 探索不再在 entropy 变体追加候选。

## 方向级反思

**方向首批 admit 率 17% (1/6)**，打破连续 3 批零 admit 僵局。首个 admit C001 (`amihud_illiq_20d`) 确证 Amihud illiquidity 是 29 批历史从未探过的独立维度——**29 批的教训"DSL 层剩余空间耗尽，所有路径都指向 Python Barra residual"** 被部分证伪：microstructure 原语（Amihud / HHI / Entropy）提供了新的 DSL-native 空间，只是 C001 admit 条件严苛（max_corr=0.754@F002 必须靠 incr_ic=0.034 硬救）。

**三 thread 产出**：
- T001（Amihud）：1 admit + 2 reserve，产出方向核心 edge，但 C001 CP04 borderline + CP05 high 的双压标记本方向"易受 Barra + F002 吸收"的结构特征；下轮必测 Amihud residualized variants。
- T002（HHI）：2 reserve + thread answered，证实机制但库已吸收——"代数独立 ≠ 库空间独立"教训第二次（前有 value_liquidity_interaction 相同模式）。
- T003（Entropy）：1 reject + thread disproven，HHI vs Entropy 孪生对比给出方向性结论"单日极值驱动"。

**下轮方向议题**（batch_031 候选方向）：
1. **T001 深化**：Amihud residualized by turnover_20d / vol_20d（DSL 层 CsZscore/CsDemean 可能实现）——目标 alpha_survival 从 0.44 → >0.7
2. **跨字段交互**：Amihud × amount_CV（F001） / Amihud × pb（F002）是否捕获 illiquidity-价值交互维度
3. **其他未探 DSL 原语**：`AmihudIlliq` 已用，`TsEntropy` 已证伪，`Scale` / `Softmax` / `Winsorize` / `Tanh` / `Sigmoid` 仍零使用

**何时 saturate**：若下 2 批 Amihud 深化 + 交互 admit 率 <20%，方向转 saturated。

**错杀侦测**：本批无候选满足"错杀全四条件"（库空间独立 + rank-order ≥0.8 + sign_consist=1.0 + 符号互补）。C006 接近（max_corr=0.111 + incr_ic=0.022 + sign_consist=1.0）但 monotonicity_oos=0.7 < 0.8，未触发 calibration。
