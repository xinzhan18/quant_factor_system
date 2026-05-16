---
batch_id: batch_103
direction: fundamental_ttm_cross_family
judged_at: 2026-05-16T08:35:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 0, reserve: 0, reject: 6}
admit_count: 0
reject_count: 6
reserve_count: 0
candidate_count: 6
mt_bucket: medium
---
# batch_103 Judge Summary

> [!abstract]+ batch_103 · [[directions/fundamental_ttm_cross_family]] · 6 candidates
> ✅ **admit=0** · ⏸ **reserve=0** · ❌ **reject=6**
> **核心发现**: fundamental TTM 字段在 csi1000 daily cross-section 上**三种 geometry 同时证伪** — (a) atomic CsRank baseline 全 regime sign-flip (C001/C002), (b) F029-framework binarize+event-rate aggregation 产生 cross-section degenerate quintiles (C003/C004/C005 三次独立复现), (c) PIT × $num_trades 非-amount-aggregate bridge 实质 = F012 amihud_illiq 同源 mean-reversion (C006, library reducer).
> **MT Budget**: cumulative 576 → **582** · direction 0 → **6** · bucket `medium`（C003/C005/C006 进 medium, C001/C002/C004 hard_gate reject 不进 MT）

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | hard_gate | sign_flip ±0.006 + mono ±1.00 + ic_oos -0.006 | CsRank(ROE) baseline regime 翻号: fundamental level cross-section sign-flip 在 2022-2023 强化 | [[batches/batch_103/candidates/C001]] |
| C002 | ❌ reject | hard_gate | sign_flip +0.003 → -0.008 + ic 平坦 | CsRank(gross_margin) baseline 同型证伪: 4/6 quality-level baselines 都被 macro regime 主导 | [[batches/batch_103/candidates/C002]] |
| C003 | ❌ reject | hard_gate-vacuous | ic_is/ic_oos = NaN (quintile degenerate) | F029-framework on TTM 字段产生 cross-section degeneracy (Q1/Q5 NaN), F029 framework 字段维度律严约束 = daily-resolution only | [[batches/batch_103/candidates/C003]] |
| C004 | ❌ reject | hard_gate | sign_flip train +0.026 / val NaN | 第 2 次 F029-on-TTM degeneracy 复现 (debt_to_asset) | [[batches/batch_103/candidates/C004]] |
| C005 | ❌ reject | hard_gate-vacuous | ic_is = -0.022, val NaN, incr_ic = **-0.048** | 第 3 次 F029-on-TTM degeneracy + 严重 library reducer; F029-framework + TTM 字段律闭合证伪 | [[batches/batch_103/candidates/C005]] |
| C006 | ❌ reject | mixed·borderline·**poor**·**high**·stable | ic_oos=-0.031 ls_t=-3.94 mono=-1.00/-1.00 alpha_surv=0.45 max_corr=0.614@F012 incr_ic=**-0.003** | hard_gate 全过的唯一真信号, 但 hypothesis 方向反 + style_r²=0.55 vol_20d 主吃 + library reducer; ROE×num_trades 实质 = amihud_illiq 同源 | [[batches/batch_103/candidates/C006]] |

**档位编码**：🟢 最优档 · 🟡 次档 · 🟠 边际 · 🔴 阻断档 · `hard_gate` reject 该列写 `hard_gate` 不填色。整列飘红 = 方向级警示——本批 4 个 `hard_gate` reject + 1 个 hard_gate-vacuous + 1 个 CP05 library reducer = **全列 hard 失败**, 方向级失败信号最强档.

## 跨候选对比

### Style 聚合
- 6 候选中仅 C006 计算到 CP04, 但 vol_20d=9.46 + ep_ratio=6.26 + turnover_20d=3.72 三 style 联合主吃 (style_r²=0.55) → 即使穿越 hard_gate 也被 Barra basis 吞噬
- C001/C002 atomic baseline 形式没机会展示 CP04 — sign_flip 在 hard_gate 阶段就被截
- C003/C004/C005 全 NaN CP04 (signal degenerate, Barra residualize 无意义)

### 相关度 cluster
C006 库相关谱: F012(-0.61), F002(-0.49), F015(-0.44), F016(-0.40), F018(-0.37), F023(-0.38) → 同时与 6 个 admitted 因子高相关 (反向) → 信号 = "整个 admit 库的反向 reducer"; incr_ic=-0.003 NEGATIVE → admit 它会让库 IC 衰减.

### MT Budget
- direction_candidates 0 → 6 (首次进 MT 计数)
- cumulative 576 → 582
- bucket per-candidate: C003/C005/C006 = medium (search_adjusted 0.586); C001/C002/C004 hard_gate fail 不进 MT 估算
- 本批不消耗 high-bucket budget — 首批 zero-admit 不推进 MT 至 high 风险段

### 三 geometry 同时证伪结构
三 thread × 3 geometry 各自独立失败模式:
- **T001 atomic baseline** (C001+C002): regime sign-flip — fundamental level cross-section 在 train/val 完全反号
- **T002 F029-framework binarize** (C003+C004+C005): cross-section degenerate quintiles — slow-moving TTM 字段在 20d windowed binarize 后取值集合极小, 5-quintile 分桶 Q1/Q5 大量 NaN
- **T003 PIT × non-vol microstructure** (C006): hypothesis 方向反 + 与 F012 机制同源 → $num_trades 不构成 vol_20d 安全替代 path

三 geometry 平行独立证伪 → **方向层面 hypothesis closure**: csi1000 daily cross-section 上 fundamental TTM 字段在所探三种 geometry 形态下都不携带 OOS-stable alpha. 这与 lessons.md "csi1000 daily fundamental 真饱和" 顶层 macro lesson 强一致, 本批是该 lesson 的**第 8 条独立证据路径**.

## Thread 进展

每个 thread 必须 wikilink 到 `[[directions/fundamental_ttm_cross_family#T{n}]]`。三 thread 本批全部转 DISPROVEN (没有任何候选通过 admit/reserve 门槛, 也没有错杀候选触发 calibration retry).

> [!failure]+ T001 [[directions/fundamental_ttm_cross_family#T001]] — `[✗ DISPROVEN batch_103]`
> C001 (ROE) + C002 (gross_margin) atomic CsRank baseline 同型证伪 — sign_flip + ic_oos 低于 noise floor. **结论**: 单 atom TTM quality LEVEL cross-section rank 不携带 csi1000 forward IC. baseline-first 律强制扫描所得为 negative 结论.

> [!failure]+ T002 [[directions/fundamental_ttm_cross_family#T002]] — `[✗ DISPROVEN batch_103]`
> C003 (ROE Gt 0.10) + C004 (debt_to_asset Lt 0.45) + C005 (gross_margin Gt 0.30) 三 F029-framework + TTM 字段候选**同一 failure mode 独立 3 次复现**: cross-section degenerate quintiles (Q1/Q5 NaN). **结论**: F029 7-D 律字段维度新约束**升格** — `Mean(threshold-op($X, c), 20)` framework 仅适用于 daily-resolution 充分变动字段, TTM 字段在 20d windowed binarize 后产生 cross-section degeneracy. F029 7-D 律字段维度边界**严格收紧至 price-derived only**.

> [!failure]+ T003 [[directions/fundamental_ttm_cross_family#T003]] — `[✗ DISPROVEN batch_103]`
> C006 `Mul(CsRank(ROE), CsRank($num_trades))` 通过 hard_gate (mono perfect -1.00/-1.00 + ls_t=-3.94 + sign_consistency=1.0) 但 hypothesis 方向反 + CP05 library reducer (incr_ic=-0.003) + 与 F012 amihud_illiq corr=-0.614 实质同源. **结论**: $num_trades 在 cross-section composite 中扮演 amihud-illiq 同源信号, 不构成 vol_20d 隐藏路径的安全替代品. **TTM × non-amount-aggregate microstructure bridge 失效**.

## 方向级反思

本方向 `fundamental_ttm_cross_family` exploring round 1 即三 thread 全 DISPROVEN, 0 admit / 0 reserve / 6 reject. 评估方向边际 ROI:

**短期 (this batch)**: 三 geometry 平行独立证伪非常 informative — 不是阈值问题, 而是 csi1000 daily cross-section 上 fundamental TTM signal **结构性不存在 OOS-stable alpha** (与 lessons.md 顶层 macro lesson 一致).

**直接元教训** (待 Phase 5 升格 lessons.md):
1. **F029 framework 字段维度律收紧** — `Mean(threshold-op($X, c), 20)` 仅适用于 daily-resolution 充分变动字段; TTM (季度更新) / quarterly delta 字段 default-skip 该 framework (Phase 1 generator 可加自检: 若 binarize 内层 atom ∈ TTM 字段集 → reject "f029_framework_field_resolution_mismatch")
2. **fundamental atomic CsRank baseline default-skip** — 第 2-3 类 atom 全 regime sign-flip (b022 PE/PB/PS rate + b068 quality/amount ratio + b103 atomic level), 升格 lessons "csi1000 daily fundamental 真饱和" 第 8 条独立证据
3. **$num_trades 不是 vol_20d 隐藏路径的安全替代品** — 与 amihud_illiq 同源, F012 cluster 同源 (b072 institutional_flow_proxy 已局部证伪, 本批从 cross-family bridge 视角再次证伪)

**下轮建议**:
- 方向 status: `exploring → dead` (3 thread 全 DISPROVEN, first-batch 0 admit, 与 fundamental_quality_carry/fundamental_momentum/python_ttm_residual_quality 三方向同型 first-batch dead)
- 不复活路径: 当前 daily-bar + linear residualize + 单字段 / event-rate / cross-family bridge 三 geometry 都已证伪
- **真复活前置**: (a) intraday primitive layer 工程 ready 后 fundamental + intraday microstructure 桥接 (新数据基础设施); (b) cross-section ffill 工具链 ready 后 TTM × TTM Python 包装 (lessons.md "TTM × TTM DSL 数据契约失败" 解锁路径); (c) lessons.md 顶层 "csi1000 daily fundamental 真饱和" macro lesson 本身被推翻

**Calibration trigger 自检** (按 skill.md §阈值校准 4 条):
1. judge.md 跨候选反思段含"potential over-rejection"? **NO** — 详细自检表明 C006 不是错杀 (max_corr=0.614 高 + incr_ic=-0.003 库 reducer, 非库空间独立)
2. 连续零 admit + 累计 reserve 有 ≥1 个满足库空间独立? 本批后零 admit streak = 5 (b099/100/101/102/103), 但本批无 reserve 候选满足 max_lib_corr<0.30 + incr_ic>0.010 → **NO**
3. 累计 reserve/judged > 40% 且零 admit? 待累计计数 → 暂 **NO** (本批 0 reserve)
4. 悖论复现 (低 style_r² + 低 alpha_surv ≥ 2 次)? **NO** (C006 style_r²=0.55 高 + alpha_surv 0.45 边缘, 不是反直觉组合)

→ **calibration_trigger = false**, 进 Phase 4 archive (无 admit 不分配 F{id}, 仅记录 batch + 更新 direction.md).

**新 dead pattern 升格候选** (供 /pattern-scout 或 Phase 5 consolidate 评估):
- F029 framework 字段维度律 fundamental TTM 收紧 → P031 子条款扩展
- TTM atomic CsRank baseline regime sign-flip → 升格 "csi1000 daily fundamental 真饱和" 第 8 路径
- TTM × non-amount-aggregate microstructure bridge 失效 ($num_trades 同 amihud) → P004 vol_20d 律段附加观察
