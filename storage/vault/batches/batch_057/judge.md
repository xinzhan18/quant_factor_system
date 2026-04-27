---
batch_id: batch_057
direction: vwap_proxy_signals
judged_at: 2026-04-25T10:50:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reserve}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 0, reserve: 1, reject: 5}
admit_count: 0
reject_count: 5
reserve_count: 1
candidate_count: 6
mt_bucket: high
---

# batch_057 Judge Summary

> [!abstract]+ batch_057 · [[directions/vwap_proxy_signals]] · 6 candidates
> ✅ **admit=0** · ⏸ **reserve=1** (C005) · ❌ **reject=5** (C001/C002/C003/C004/C006)
> **核心发现**: T004 "higher-moment LHS × VWAP basis × non-saturated rank-diff RHS" 路径在 csi1000 上 **几乎完全证伪** — 4/6 hard_gate 失败 (IC_oos 太弱 ×2 / sign_flip ×1 / mono_flip ×1)，1/6 reject (vol_20d exposure=48.04 整库罕见极值)，仅 C005 (Skew 三阶矩) 在 rank-order 极优 (mono=0.9, cum_ic_mdd=-2.18 整库罕见) 但被 vol_20d (alpha_surv=0.157 << 0.30 rank-diff floor) + F017 cluster (max_corr=0.51, incr_ic=0.005 触 F203 cluster co-resonance) 双重夹击 → reserve。**F019/F020 paradigm transfer to VWAP basis 失败** — VWAP-prev/open gap 的 higher-moment LHS 在 cross-section 上要么是 noise，要么是 vol_20d 极端载体。
> **MT Budget**: cumulative 300 → **306** · direction 12 → **18** · bucket `high`（封顶 search_adjusted 推回 `medium`）· 本批 high=2 (C003/C005), 其余 hard_gate 不评 mt

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | hard_gate | ic_oos=-0.007 < 0.008 阈值 | turnover_rate Mean 10 RHS 与 VWAP-prev gap Std 配对 cross-section noise | [[batches/batch_057/candidates/C001]] |
| C002 | ❌ reject | hard_gate | sign_flip train -0.004/val +0.001 | 短窗口 (10d) LHS + Med((H-L)/close) RHS 不打开新轴 | [[batches/batch_057/candidates/C002]] |
| C003 | ❌ reject | mixed·**weak**·**poor**·**high**·mixed | ls_t=-0.14 mono_oos=0 style_r²=0.75 vol20d=48.04 incr_ic=-0.007 | VWAP-open anchor 同 session = vol_20d 结构性极值载体 (整库罕见 exp=48)；ic_by_year 2015 后 9 年单边翻号 | [[batches/batch_057/candidates/C003]] |
| C004 | ❌ reject | hard_gate | mono_sign_flip IS=0.7 OOS=-0.6 | amount/circ_mktcap RHS 与 LHS Std 配对 regime 翻盘 (turnover_structural "换 field ≠ 换维度" 律) | [[batches/batch_057/candidates/C004]] |
| C005 | ⏸ reserve | aligned·borderline·**poor**·medium·stable | ic_oos=0.030 ls_t=2.58 mono=0.9 alpha_surv=**0.157** max_corr=0.51@F017 incr_ic=+0.005 cum_mdd=-2.18 | rank-order 极优 (mono+sign_consist+cum_mdd 整库罕见) **vs** vol_20d 严重吸收 + F017 cluster (F203 触发) — 高张力候选，等待 F017 退役 / vol_20d Python residual 工具链 | [[batches/batch_057/candidates/C005]] |
| C006 | ❌ reject | hard_gate | ic_oos=0.0035 < 0.008 阈值 | within-VWAP 5d momentum dispersion 是 noise dominated；rank-diff 解耦救不回来 | [[batches/batch_057/candidates/C006]] |

**档位编码**：🟢 最优档 · 🟡 次档 · 🟠 边际 · 🔴 阻断档 · `hard_gate` reject 不填色。本批仅 C003/C005 进入软 CP；C003 整列飘红 (weak/poor/high) → 方向级警示（VWAP-open anchor 同 session 路径 dead end）。

## 跨候选对比

- **Hard_gate 失败率 4/6 (67%)**：本批最显著结构事实。failure 类型分布：
  - `ic_oos_too_low` ×2 (C001/C006) — 信号体量根本不足，cross-section noise 主导
  - `sign_flip` ×1 (C002) — 短窗口 + range/close RHS 配对 regime 不稳
  - `mono_flip` ×1 (C004) — RHS 换 amount/circ_mktcap 后真实 mono 翻盘
- **C001/C004/C005 共享 LHS** = `Std(VWAP-prev gap, 20)` 或 `Skew(...)` (C005)：同 LHS 不同 RHS 的实验组对比清晰：
  - C001 (turnover_rate Mean 10 RHS) → ic_oos_too_low hard_gate
  - C004 (amount/circ_mktcap Mean 20 RHS) → mono_sign_flip hard_gate
  - C005 (turnover_rate Mean 10 RHS, **Skew 三阶矩 LHS**) → 唯一 reserve（mono=0.9 + cum_mdd=-2.18 + ic_by_year 单调强化）
  - **结论**：相同 LHS 二阶矩 (Std) 形式在两个非饱和 RHS 上都失败；切换到三阶矩 (Skew) 才打通 rank-order — 暗示 VWAP basis 的 higher-moment 路径 **二阶矩 saturated, 三阶矩 partially active**
- **Style 聚合**：2 个进入 CP04 的候选 (C003/C005) 都 dominant_style=`vol_20d`：
  - C003 vol_20d exposure = **48.04** (整库罕见极值，超 b008 C005=32.0 历史最高)
  - C005 vol_20d exposure = 13.96 (高但温和)
  - VWAP basis 在 csi1000 上结构性等价于 vol_20d 高暴露载体 — F005 distillation 律再次验证
- **相关度 cluster**：C003/C005 都 nearest=F017 (overnight×turnover rank-diff)，corr=0.48 / 0.51 — 两个 VWAP-derived rank-diff 都被 F017 吸收 ~25%
- **MT 预算推进**：cumulative 300 → 306（首次破 300 大关）；direction 12 → 18（vwap_proxy_signals 方向 high bucket 巩固，仅次 saturated 边界 20）
- **bucket=high 触发的 verdict 收紧**：C003/C005 都 high bucket → search_adjusted 后 medium，但 high 上界限制本就压制 admit 概率

## Thread 进展

> [!note]+ T004 [[directions/vwap_proxy_signals#T004]] — `[◉ ACTIVE]` (本批启动 thread)
> 6 候选全部归入 T004。结论：**T004 hypothesis (higher-moment LHS on VWAP-derived scale-free × non-saturated rank-diff RHS) 在 cross-section 上几乎完全证伪**：
> - 二阶矩 (Std) 路径：3 候选 (C001/C002/C004) 全 hard_gate fail，证明 Std(VWAP-prev/open gap) 与已尝试的非饱和 RHS (turnover_rate Mean 10 / Med(range/close) / amount/circ_mktcap Mean 20) 配对在 cross-section 上无 stable rank-order
> - 三阶矩 (Skew) 路径：C005 唯一 reserve，rank-order 极优但 vol_20d 严重吸收 + F017 cluster 共振 → 暗示 Skew 是有信号但被 cluster + style 双重压制
> - within-VWAP momentum 路径：C006 ic_oos_too_low — 时间窗内 VWAP 自身相对变化 noise dominated
> - VWAP-open anchor 同 session 路径：C003 完全坍塌 + vol_20d exposure=48.04 整库罕见极值，证伪"开盘锚点 VWAP" 独立性
>
> **Next probes**: 仅有 1 条剩余路径 — 三阶以上矩 (Kurt) 或 Skew × 不同 RHS 探索；但本方向 rounds=3 + admits=1 + 2 batch reject>80% 已满足 saturated 转化条件，建议方向转 saturated。

> [!success]- T001 [[directions/vwap_proxy_signals#T001]] — `[✓ ANSWERED batch_040]` (本批无推进)

> [!failure]- T002 [[directions/vwap_proxy_signals#T002]] — `[✗ DISPROVEN batch_040]` (本批无推进)

> [!note]- T003 [[directions/vwap_proxy_signals#T003]] — `[⏸ SUSPENDED batch_042]` (本批无推进，仍阻塞工具链)

## 方向级反思

本方向 rounds = 3（batch_040 + batch_042 + 本 batch_057）·admits = 1 (F014, Grade D 37) · 最近 2 批 reject 率：batch_042 = 5/6 (83%) + batch_057 = 5/6 (83%) → 满足 "连续 2+ batch reject > 80%" 转 saturated 触发条件。

**核心证伪累积**：
1. T001 ANSWERED：跨 session VWAP-prev_close (F014) 是唯一 admit，level 形式
2. T002 DISPROVEN：同 session VWAP/close 偏离的 5d/20d 聚合 (level 形式) 全 fail
3. T003 SUSPENDED：daily-anchor VWAP HLC位置 5 子路径撞墙 max_corr@F014=0.79-0.89
4. **T004 (本批) 几乎完全证伪**：higher-moment LHS (Std/Skew) on VWAP-derived scale-free × rank-diff 路径在二阶矩、三阶矩、不同 anchor、不同 RHS 上全部失败或被 cluster+style 压制

**结构性结论**：A 股 csi1000 上 VWAP 基底 (synthesized $amount/$volume) 的可探索路径在日频 DSL 层基本耗尽。F014 是 level cross-session 形式的唯一兑现；higher-moment / momentum / different-anchor 路径都被 (a) F005 OHLC algebraic mirror 共动律 + (b) F001/F301 vol_20d 结构性吸收律 + (c) F017 cluster 共振律 三重夹击。

**下轮建议**：`status: productive → saturated` · `priority: medium → low`。复活条件：
- F017 退役（unlikely 短期）→ C005 可重测
- vol_20d Python residualization 工具链就绪 + coverage 修复 → T003 残差路径 + T004 Skew × residualized 重启
- 非 daily-bar 数据（minute/tick）→ VWAP 微观结构信号根本性逃离

**值得沉淀的元教训**（建议升格 lessons）：
- "higher-moment LHS independence axis on scale-free VWAP-derived ratios" **不能** 跨 family 迁移 — F019/F020 (OHLC body / gap_ret) → VWAP basis 失败。差异：F019/F020 的 atom 是直接价格 ratio（scale-free, vol_20d-independent），而 VWAP-prev gap 本身就嵌入了波动率信息（gap 大小 ≈ 日内波动率），导致 higher-moment 不是"独立 axis" 而是"vol_20d 极端载体"。**lessons.md "Promising Unexplored" 第 1 条需附 caveat**：family-agnostic 律仅在 atom 自身与 vol_20d 正交时成立。
- C003 vol_20d exposure=**48.04** 是整库历史新高（超 b008 C005=32.0），值得记录为方向级 anti-pattern：**VWAP-open 同 session 锚点是 vol_20d 极端载体**。
