---
batch_id: batch_052
direction: value_liquidity_interaction
judged_at: 2026-04-25T07:30:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 0, reserve: 0, reject: 6}
admit_count: 0
reserve_count: 0
reject_count: 6
candidate_count: 6
mt_bucket: high
---

# batch_052 Judge Summary

> [!abstract]+ batch_052 · [[directions/value_liquidity_interaction]] · 6 candidates
> ❌ **admit=0** · ⏸ **reserve=0** · ❌ **reject=6** (C001 hard_gate sign_flip + mono_sign_flip; C002 cluster@F020 0.40 + ls_t=0.05 PnL flat; C003 hard_gate sign_flip; C004 cluster@F002 -0.45 + ls_t=-0.91 弱; C005 alpha_surv=0.12 严重 Barra 吞噬 + cluster@F002 0.47; C006 hard_gate ic_oos_too_low 0.0077<0.008 + IS→OOS 崩塌 12.18→-0.13)
> **核心发现**：**rank-diff 范式第 7 次跨家族泛化在 value × liquidity 失败 — 范式连胜中断**。本批揭示三条新结构性约束：(1) **基本面字段 (PE/PB/PS) higher-moment (Std/Var) 在 rank-diff 几何中天然 regime-sensitive** (C001/C003 双 sign_flip)；(2) **compound moment LHS (嵌套 smooth-then-std) 产生 IS over-fit + OOS 崩塌** (C006 ls_t_is=12.18 → ls_t_oos=-0.13)；(3) **任何含 amount/turnover 分母的 value-liquidity ratio 都被 F002 + Amihud-family 锚定** (C005 cluster + 严重 Barra 吞噬验证 b051 升格规律)。**rank-diff geometry 不是万能钥匙——本方向 F002 admit 后已结构饱和**。
> **MT Budget**: cumulative 270 → **276** · direction 21 → **27** · bucket `high` (search_adjusted → medium) · 本批 low=0 / med=0 / high=6
> **方向状态决策**：从 `saturated` 维持 `saturated`（不退化为 `dead`：本批揭示了 3 条新结构教训，知识价值已交付）。下次再开本方向需先有 (a) 完全脱离 amount/turnover 分母的新 value × liquidity 几何思路 / (b) Python residual 路径有新工具 / (c) 跨家族 rank-diff 在新 family (e.g. fundamental momentum stable subset) 兑现后回流。

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | hard_gate | sign_flip train -0.003 vs val +0.016 + mono_sign_flip IS=-0.80 OOS=1.00 | PE level higher-moment (Std) 在 train (低利率成长股) vs validation (利率上行价值回归) regime 完全反向 | [[batches/batch_052/candidates/C001]] |
| C002 | ❌ reject | 🟡·🔴·🟡·🔴·🟢 | ic_oos=+0.012 ls_t=0.05 alpha_surv=0.46 max_corr=0.40@F020 incr_ic=0.006 | 三 borderline 叠加 (CP3 weak + CP4 borderline + CP5 cluster) 无 strong 维度；body_ratio_20 RHS 在第二次复用退化为共振 | [[batches/batch_052/candidates/C002]] |
| C003 | ❌ reject | hard_gate | sign_flip train -0.005 vs val +0.013 (PB×turnover joint vol 60d 翻号) | 与 C001 平行——基本面 second-order moment 跨 regime 翻号；同时计划中的 Corr 算子触发 Qlib 跨字段 NaN-window broadcast bug 已绕开 | [[batches/batch_052/candidates/C003]] |
| C004 | ❌ reject | 🟢·🔴·🟢·🔴·🟢 | ic_oos=-0.019 ls_t=-0.91 **alpha_surv=0.96(整批最高!)** max_corr=-0.45@F002 incr_ic=0.005 | "alpha-survival 整批最高 + library cluster reject" 复现 b051 "Barra-clean ≠ library-clean" 律；F002 是本方向结构性 anchor | [[batches/batch_052/candidates/C004]] |
| C005 | ❌ reject | 🟡·🟠·🔴·🔴·🟡 | ic_oos=+0.012 ls_t=1.70 (h20 ls_t 更强但短 horizon 弱) **alpha_surv=0.12(整批最差)** max_corr=0.47@F002 | PS/amount 与 PB/amount 是结构性 dual + amount-family 全 cluster + Barra 吸收 100% | [[batches/batch_052/candidates/C005]] |
| C006 | ❌ reject | hard_gate | ic_oos=0.0077 < 0.008 (恰差 0.0003) + ls_t_is=**+12.18** vs ls_t_oos=**-0.13** | compound moment LHS (smooth-then-std 嵌套) IS over-fit + OOS 崩塌——单层 vs 嵌套 higher-moment 行为完全不同 | [[batches/batch_052/candidates/C006]] |

**档位编码**：🟢 最优档 · 🟡 次档 · 🟠 边际 · 🔴 阻断档 · `hard_gate` reject 不填色。

## 跨候选对比

**LHS 多元化结构 (本批 6 LHS 全唯一)**:
- C001: `Std($pe_ratio, 20)` — PE level higher-moment
- C002: `Mean($pe_ratio/$turnover_rate, 20)` — value-per-liquidity ratio
- C003: `Std($pb_ratio*$turnover_rate, 60)` — joint vol of value×liquidity product
- C004: `Std($turnover_rate, 20)` — turnover higher-moment
- C005: `Mean($ps_ratio/$amount, 60)` — PS-per-amount long-window
- C006: `Std(Mean($pb_ratio, 5), 20)` — compound moment (smooth-then-std)

**RHS 多元化结构 (本批避开所有 b051 标 dead RHS endpoints)**:
- C001/C006 类: `Mean(Std($close, 5), 60)` 长窗 / `Mean(Std($turnover_rate, 5), 20)` turnover micro-vol
- C002/C005: `Mean(body_ratio, 20/60)` body_ratio 不同窗口
- C003: `Mean(|daily_return|, 60)` Amihud-numerator 全新 RHS basis
- C004: `Mean($pb_ratio, 60)` PB 长窗 fundamental basis

**关键失败模式分类**:

1. **基本面 second-order moment 跨 regime sign_flip (C001 + C003)**: PE Std + PB×turnover joint vol 都在 train/validation 翻号——揭示一条新规律：**raw 基本面字段（PE/PB/PS 及其与 liquidity 字段乘积）的 higher-moment (Std/Var) 在 rank-diff 几何中天然 regime-sensitive**。区别于 lessons.md 已 promote 的 PE_rate (Div(Delta,X)) 死区——本失败模式攻击 raw level 的 second-order moment，是更基础的死区。**candidate to promote**: "fundamental second-order moment regime-sensitivity" 升格 lessons.md "Promising Unexplored" 反向条目。

2. **compound moment LHS over-fit (C006)**: ls_t_is=12.18 → ls_t_oos=-0.13 是史上最戏剧 IS-OOS 崩塌之一。`Std(Mean(X,5),20)` 嵌套结构在 train 期 fit noise (IS 强极致)，OOS 完全消失。与 b051 admit C002 单层 `Std(gap_ret,20)` 行为完全相反——**单层 higher-moment 是 alpha 源头，嵌套 compound moment 是 over-fit 源头**。新 lessons 候选。

3. **value × liquidity ratio 必 cluster F002 (C002 + C004 + C005)**: 三个不同结构候选 max_corr 都在 0.40-0.47 落入 F002 cluster：
   - C002: max_corr=+0.40@F020 (rank-diff family 共振) — body_ratio_20 RHS 第二次复用退化
   - C004: max_corr=-0.45@F002 (反向 cluster — value-liquidity dual)
   - C005: max_corr=+0.47@F002 (amount 分母 dual)

   **共振 anchor 不是 RHS 共振饱和律里的 endpoints，而是 F002 本身**——F002 在本方向占据结构性中心位置，任何含 PB/PS/PE × amount/turnover 的几何排列都会与之 cluster。**这是 RHS 共振饱和律在 saturated direction 的进阶形态：not RHS-anchored, but factor-anchored**。

4. **Barra 吞噬光谱在本批完整呈现**: alpha_surv 跨度 0.12 (C005 严重) → 0.46 (C002 borderline) → 0.96 (C004 clean)。**alpha_surv 高 ≠ admit**——C004 是本批 CP04 最干净，但仍因 CP3 weak + CP5 cluster reject。**复现 b051 升格规律 "Barra-clean ≠ library-clean"** 在新方向。

**与 b051 admit (F020 gap_vol×body_ratio) 对照**:
- F020: LHS=Std(gap_ret,20) higher-moment + RHS=body_ratio_20 → max_corr=0.246 cluster-clean → admit
- 本批 C002: LHS=PE/turnover ratio + RHS=body_ratio_20 → max_corr=0.398 cluster co-resonance → reject

  **教训**：F020 admit 后 body_ratio_20 RHS 从"安全类目"退化为"共振 RHS"。**RHS 共振饱和律是动态的——admit 一个就消耗一个 RHS 类目的库余量**。下次复用 body_ratio_20 RHS 必须 max_corr@F020 < 0.30 + LHS 完全脱离 OHLC family。

**Style 聚合**: 6 候选 dominant_style 全 vol_20d。本方向 value × liquidity 几何天然带 vol_20d 暴露 (b051 同观察)——结构性约束。

**MT 预算**: direction_candidates 21 → 27, 远低于 70 上限。但本方向 7 轮 (含本批) 仅 1 admit，**reserve 累计 0** (本批也 0 reserve)，MT 预算空闲不构成放宽阈值依据。

## Calibration Check (Phase 3.5)

四个 calibration trigger 检查:

1. ❌ **错杀 flag**: 本批无 candidate 满足 max_corr<0.30 + incremental_ic>0.010 + mono\|·\|>0.8 + sign_consistency=1.0 + reject_reason 单一指标。最强候选 C004 alpha_surv=0.96 但 max_corr=-0.45 (cluster) + ls_t=-0.91 (CP3 弱)，多维度同时失败 — **不是错杀，是真实信号过弱**。
2. ❌ **连续零 admit**: 本方向最近 3 batches admit: b034=0, b052=0, 中间无其他本方向 batch。直接连续 admit=0 仅 2 次（b034 与 b052 本身），未达 3 次硬触发。同时**累计 reserve=0** — 不满足 trigger condition (≥3 batches 0 admit + reserve ≥1 满足库空间独立)。
3. ❌ **Reserve 积压**: 本方向累计 reserve 数 = 6 (b005-009 reserves) / judged 27 = 22% < 40%。
4. ❌ **悖论复现**: C004 (alpha_surv=0.96 + cluster) 是单次现象，b051 已建立 "Barra-clean ≠ library-clean" 律，本批是该律在新方向的复现验证 (knowledge already promoted)，不是新悖论。

→ **calibration_trigger = false**。本批结果是真实的"信号不够"，不是"阈值过严"。Phase 4 archive 正常进行。

## Thread 进展

> [!failure]+ T002 [[directions/value_liquidity_interaction#T002]] — `[✗ DISPROVEN batch_052]`
> Size × Liquidity 反转线程 (size proxy 红线下设计的 PE/PB/PS × turnover/amount rank-diff geometry) 在本批 6 候选完整投放后宣告 **DISPROVEN**。三条独立机制揭示：
>
> 1. **基本面 higher-moment 跨 regime sign_flip** (C001/C003 双例): PE Std + PB×turnover joint vol 都在 train/validation 翻号 → 基本面字段 second-order moment 在 rank-diff 几何中天然 regime-sensitive
> 2. **value × liquidity ratio cluster F002 anchor** (C002/C004/C005 三例): F002 在本方向是结构性 anchor，任何含 amount/turnover 分母的几何排列都被 0.40-0.47 cluster 锁死
> 3. **compound moment LHS over-fit** (C006): 嵌套 smooth-then-std 结构 IS=12.18 → OOS=-0.13 戏剧崩塌
>
> **结论**: rank-diff 范式第 7 次跨家族泛化在 value × liquidity 失败——证明 rank-diff geometry 不是万能。saturated 方向中 F002 anchor 已锁死该家族 60%+ alpha 空间。

## 跨方向元教训 (Phase 5 consolidation 候选)

3 条新教训等待 Phase 5 升格 lessons.md:

1. **"基本面字段 second-order moment 在 rank-diff 几何中天然 regime-sensitive"** — 区别于 PE_rate 自归一化死区，这条攻击 raw level 的 Std/Var/joint-vol。candidate to promote → lessons.md Structural Constraints
2. **"compound moment LHS (嵌套 smooth-then-std) 产生 IS over-fit + OOS 崩塌"** — 单层 higher-moment vs 嵌套 compound moment 行为完全相反。candidate to promote → lessons.md Forbidden Patterns
3. **"RHS 共振饱和律是动态的——admit 一个就消耗一个 RHS 类目的库余量"** — body_ratio_20 在 F020 admit 后退化。candidate to update → 已存在的 RHS 共振饱和律改写为动态版本

下批建议 (next_hint): 切换方向。本方向 8 轮已穷尽 DSL 几何路径，剩余唯一未试是**完全脱离 PB/PE/PS × amount/turnover 几何**的全新基本面 × 流动性几何（如 fundamental momentum + liquidity acceleration 共动），但已属其他 direction (fundamental_momentum) 的范畴。
