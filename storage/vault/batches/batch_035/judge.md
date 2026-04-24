---
batch_id: batch_035
direction: gap_acceptance_structure
judged_at: 2026-04-24T01:10:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reserve}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 0, reserve: 1, reject: 5}
admit_count: 0
reserve_count: 1
reject_count: 5
candidate_count: 6
mt_bucket: medium
---

# batch_035 Judge Summary

> [!abstract]+ batch_035 · [[directions/gap_acceptance_structure]] · 6 candidates
> ❌ **admit=0** · ⏸ **reserve=1** (C004) · ❌ **reject=5** (C001/C002/C003/C005/C006)
> **核心发现**: paper QuantaAlpha 的 CSI 300 大盘 "gap sign × body sign acceptance" 信号 (Rank IC 0.0744) **不 transfer 到 csi1000 小盘**——T001 纯 sign interaction 在 10d/20d/60d 三个窗口同步 sign_flip（2015-2020 正，2021-2023 反）；T003 TR-via-realized-vol 归一化 gap magnitude 与 F003 corr=0.964 near_duplicate（答完该子空间）；唯一活口是 T002 turnover 加权 (C004 reserve, ic_oos=0.0082 刚过闸)。Direction 在一轮内即完成 T001/T003/T004 封闭。
> **MT Budget**: cumulative 168 → **174** · direction 0 → **6** · bucket `medium`（C004 search_adjusted raw=0.591 → adjusted=0.422 bucket=medium）· 本批 low=0 / medium=6 / high=0

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | hard_gate | IC_OOS=-0.0033 sign_flip + oos_decay=-0.47 | T001 main line 20d——paper 主形状在 csi1000 机制失效（2015-2020 全正 → 2021-2023 全负） | [[batches/batch_035/candidates/C001]] |
| C002 | ❌ reject | hard_gate | IC_OOS=-0.0020 sign_flip + oos_decay=-0.24 | T001/T004 短窗 10d 同病，split 4/4 全负，非短记忆能救 | [[batches/batch_035/candidates/C002]] |
| C003 | ❌ reject | hard_gate | IC_OOS=-0.0058 sign_flip + oos_decay=-1.03 | T001/T004 长窗 60d 最严重——cum_dd=-4.18，长窗放大 regime 翻号 | [[batches/batch_035/candidates/C003]] |
| C004 | ⏸ reserve | 🟢·🔴·🟢·🟢·🟡 | IC_OOS=0.0082 ls_t=3.90 mono=0.30 incr=0.0098 | T002 turnover 加权——方向唯一正面证据，但 rank-order 为 "avoid worst" barbell 非 monotonic | [[batches/batch_035/candidates/C004]] |
| C005 | ❌ reject | hard_gate | near_duplicate corr=0.964@F003 | T003 答完——gap magnitude 换分母（Std(ret,20)）仍 collapse 到 F003，子空间关闭 | [[batches/batch_035/candidates/C005]] |
| C006 | ❌ reject | hard_gate | IC_OOS=0.0058 < 0.008 | T001 magnitude×sign 混合——diff 仅 0.002，mono=0.30；csi1000 实测 IC 已低于 direction.md 预估 0.02-0.04 下界一半 | [[batches/batch_035/candidates/C006]] |

**档位编码**：🟢 最优档 · 🟡 次档 · 🔴 阻断档 · `hard_gate` reject 不填色（CP01 闸门失败直接终止深度判决）。本批 5/6 hard_gate fail，仅 C004 进入 CP2-6 分析。

## 跨候选对比

- **纯 sign interaction 家族三连败 (C001/C002/C003)**：10d/20d/60d 三个窗口同时触发 `sign_flip + ic_oos_too_low + oos_decay_too_low` 三闸。共同 pattern —— `ic_by_year` 2015-2020 全正 (0.002-0.022)，2021-2023 全负（C001 2023: -0.005 · C003 2023: -0.0095）。`split_ic_means` 4/4 全负。这不是 outlier，是 A 股 csi1000 universe 在 2021 regime 转折后**整族信号反号**。paper CSI 300 大盘 Rank IC 0.0744 的结果已被 direction.md 预警不可迁移，实测结果比预估更糟——IC 量级不仅降，还反号。
- **C004 turnover 加权是方向生路**：T002 primary 假设在 C004 得到验证——加 turnover 权重后，pure sign product 的 regime 翻号被部分中和（`ic_by_year` 2015=0.016, 2023=0.0071 仍同号全正）。ls_tstat_oos=3.90 · ls_sharpe_oos=2.81 · cum_dd=-0.69 等 CP06 时序稳健指标 batch 内最优，库独立性 max_corr=0.054@F002 · incremental_ic=0.0098 干净。但 Q1=-0.00065, Q2=+0.00021, Q3=+0.00029, Q4=+0.00022, Q5=-0.00015 形成 "avoid worst" barbell：ls 的 alpha 主要来自 Q1 极端负，Q5 本身也是负——不是 monotonic alpha，long-Q5 实盘不可行。CP03 mono=0.3（weak）使其 verdict 从 admit 降为 reserve。
- **T003 TR 归一化 definitive closed (C005)**：paper 的 "true range 归一化" 构想，我们用 `Std($close-Ref($close,1), 20)` 做分母（结构不同于 F003 的 `Mean($high,5)` 分母），但横截面 corr=0.964@F003——说明 **gap magnitude 归一化的所有分母量纲变体都会被 F003 的"open-prev_close 分子主导"结构所吸收**。T003 以干净的 near_duplicate 方式 ANSWERED，比 hard_gate sign_flip 更有价值的"信息性 reject"。
- **Style exposure 一致**：6/6 候选 `dominant_style_exposure=vol_20d`（style_crowding_risk=medium），但 `style_r²` 全在 0.02-0.05 低段，`alpha_survival_ratio` 三个过 gate 的候选（C004/C005/C006）都 ≥1.0——风格暴露不是本批主要阻断轴，机制本身才是。
- **MT budget 推进**：direction_candidates 本方向首 6 候选全数进账（`direction 0 → 6`）；cumulative `168 → 174`。direction 低基数未触达 high bucket，C004 若下轮复投仍在 medium。

## Thread 进展

> [!failure]+ T001 [[directions/gap_acceptance_structure#T001]] — `[✗ DISPROVEN batch_035]`
> C001/C002/C003 三连败（hard_gate sign_flip + ic_oos_too_low + oos_decay），10/20/60d 三个窗口同家族塌陷。机制结论：**纯 Sign(gap) × Sign(body) 的 20d 聚合在 csi1000 上 2021-2023 regime 反号**，paper CSI 300 大盘结果不 transfer 到小盘端。直接关闭该 thread。

> [!note]+ T002 [[directions/gap_acceptance_structure#T002]] — `[◉ ACTIVE]`
> C004 reserve（首证据）。turnover 加权的 acceptance 在 csi1000 上通过 hard gate，库独立 max_corr=0.054 · incr_ic=0.0098，9 年 IC 同号全正但衰减 66%；rank-order 为 "avoid worst" barbell（mono=0.3）使其 reserve。下一步 probes：`$amount / Mean($amount, 20)` 加权 vs 当前 `$turnover_rate` 直接加权对照；测 abnormal vol 归一版本是否改善 mono。

> [!failure]+ T003 [[directions/gap_acceptance_structure#T003]] — `[✗ DISPROVEN batch_035]`
> C005 hard_gate near_duplicate（corr=0.964@F003）。回答方向自设阈值"corr < 0.7 则 TR 分母是新量纲"的问题：**否**。`Std($close - Ref($close,1), 20)` 作为分母（量纲与 F003 `Mean($high, 5)` 正交）并未打破与 F003 的近完全相关——gap magnitude 的分母量纲变体都会被 F003 开环吸收。T003 definitively closed。

> [!failure]+ T004 [[directions/gap_acceptance_structure#T004]] — `[✗ DISPROVEN batch_035]`
> C001 (20d) / C002 (10d) / C003 (60d) 三窗口同时给出 hard_gate fail。窗口敏感性探索结论：**csi1000 上纯 sign interaction 不存在 "sweet spot 窗口"，T001 family 不是窗口问题，是机制问题**。方向 T004 与 T001 同步关闭。

## 方向级反思

`gap_acceptance_structure` 首批即完成 T001 / T003 / T004 三个 thread 的**信息性封闭**。这是一个罕见的高效失败：方向 hypothesis 的**主结构**（pure sign 乘积 + 20d 聚合）经三窗口消融后被 A 股 csi1000 regime 数据硬性证伪；**正交 baseline**（TR 归一 F003 near-duplicate 风险）一次确认为完全子空间吸收；唯一生路是 **T002 turnover 加权**，且首证据（C004）指向 "avoid worst barbell" 而非 monotonic alpha。

这批结果完美印证了 direction.md 预判的**单一最大隐藏假设**："paper 0.0744 Rank IC 来自 CSI 300 大盘，csi1000 小盘下 gap 符号本身噪声过大 → 可能符号不稳"。实测：**不只是符号不稳，而是 2021 regime 起完全反号 + 幅度 collapse**。paper 方法论不可直接 transfer。

**方向操作建议**（Phase 3 标注，Phase 4 由 LLM 在 Narrative Log 中实施）：
- `status: exploring` **保留**（只有 T002 单个 active thread + C004 单一 reserve）
- `priority: high → medium`（大部分 thread 封闭，ROI 下调）
- 下一批 batch_036 聚焦 T002：`$amount / Mean($amount, 20)` 加权 vs C004 `$turnover_rate` 直接加权 vs normalized vol acceptance 三变体对照；若 T002 后续无 admit（≥2 连批 0 admit），方向 `exploring → saturated`

**Calibration（错杀侦测）**：
- 本批 `potential over-rejection` flag = **False**
- C001/C002/C003 hard_gate fail 都是 sign_flip + ic_oos 组合硬阻断，非单指标 dealbreaker；ic_by_year 2021-2023 连续反号是机制证据，不是阈值过严
- C005 near_duplicate 0.964 远超 0.9 硬闸，是结构性冗余而非阈值过严
- C006 IC_OOS 差 0.002 达标，incr_ic=0.0086 < 0.010 dealbreaker，mono_oos=0.3 < 0.8 dealbreaker → 不满足错杀的 4 条件（rank-order 完美 + 库空间独立 + 符号互补 + incremental_ic > 0.01）
- C004 reserve 符合"结构边际"而非错杀，rank-order barbell 是真实"Q5 负 alpha"问题，等 T002 变体对照后决定复投
- **不触发 threshold calibration**
