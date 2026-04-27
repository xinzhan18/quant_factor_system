---
batch_id: batch_058
direction: overnight_intraday_split
judged_at: 2026-04-25T11:50:00Z
candidates:
  - {candidate_id: C001, verdict: reserve}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: admit, factor_name: close_position_amount_accel_rd_20}
  - {candidate_id: C005, verdict: reserve}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 1, reserve: 2, reject: 3}
admit_count: 1
reject_count: 3
reserve_count: 2
candidate_count: 6
mt_bucket: high
---

# batch_058 Judge Summary

> [!abstract]+ batch_058 · [[directions/overnight_intraday_split]] · 6 candidates
> ✅ **admit=1** (C004 → close_position_amount_accel_rd_20) · ⏸ **reserve=2** (C001/C005) · ❌ **reject=3** (C002/C003/C006)
> **核心发现**: T012 close-position-in-range LHS atom 兑现 cockpit 设计约束 "vol_20d 正交 atom" — C004 (20d) alpha_surv=0.43 是本批最高、style_r²=0.13 是本批最低、cum_ic_mdd=-1.03 本批最浅、max_corr=0.283@F006 library-clean、9/9 年区间窄稳定 → 本方向第 8 个 admit。**关键二律对比**：close-position 短窗 alpha 独立 (20d=0.43)、长窗放大 vol 吞噬 (60d=0.19)；sign-product 短窗 mono 失败 (20d=0.4) 长窗 mono 完美 (60d=0.9)——同方向两个新 LHS atom 对窗口扩展的 vol_20d 吞噬响应**不对称**。zero_admit_streak=2 终结。
> **MT Budget**: cumulative 306 → **312** · direction 21 → **27** · bucket `high`（封顶 search_adjusted 推回 `medium`）· 本批 6 候选全 high bucket（direction.exposure=57 完全饱和）

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ⏸ reserve | aligned·**borderline**·**poor**·medium·stable | ic_oos=0.055 ICIR=0.40 ls_t=3.73 mono=1.0/1.0 alpha_surv=0.31 max_corr=0.576@F018 incr_ic=0.008 | 指标层最强 (ic+icir+ls_t 三 strong) + 9/9 年逐年强化至 2023 IC=0.060；F203 cluster co-resonance + alpha_surv 仅过 rank_diff floor 0.30——结构上 F018 长窗近镜像 | [[batches/batch_058/candidates/C001]] |
| C002 | ❌ reject | mixed·**weak**·**poor**·medium·mixed | ic_oos=0.024 ls_t=0.65 alpha_surv=0.054 mono_oos=0.6 | intraday body sign LHS 是 vol_20d/str_1m 载体（exposure=40.3），T003 (intraday 镜像 DISPROVEN) sign-space 实例化撞墙 | [[batches/batch_058/candidates/C002]] |
| C003 | ❌ reject | aligned·**weak**·acceptable·**low**·stable | ic_oos=0.024 ls_t=1.09 mono_oos=0.4 + Q5 反向 max_corr=0.216@F009 incr_ic=0.017 | sign-product 20d **library-clean (max_corr=0.216 本批最低 + incr_ic=0.017)** 但 ls_t<2 + rank-order 破坏；非错杀（mono_oos<0.8） | [[batches/batch_058/candidates/C003]] |
| C004 | ✅ admit | aligned·**borderline**·acceptable·**low**·stable | ic_oos=0.029 ICIR=0.36 ls_t=1.56 mono=-0.10/+0.6 alpha_surv=0.43 max_corr=0.283@F006 incr_ic=0.012 cum_mdd=-1.03 | 本批最 balanced：style_r²=0.13 最低 + alpha_surv=0.43 admit 最高 + cum_mdd 最浅 + worst_quarter 永正 + 9/9 年区间窄；close-position-in-range LHS 兑现 vol_20d 正交 atom | [[batches/batch_058/candidates/C004]] · [[factors/F022]] |
| C005 | ⏸ reserve | aligned·**borderline**·**poor**·medium·stable | ic_oos=0.039 ls_t=1.91 mono=0.9/0.9 alpha_surv=0.26 max_corr=0.49@F021 incr_ic=0.011 | sign-product 60d 长窗 mono 完美 (vs C003 20d mono=0.4)；alpha_surv 略低 floor + F203 cluster——结构上同 RHS=Mean(H/L,60) 与 F021 部分重合 | [[batches/batch_058/candidates/C005]] |
| C006 | ❌ reject | aligned·**borderline**·**poor**·medium·stable | ic_oos=0.044 ls_t=1.52 mono=0.3/0.9 alpha_surv=0.19 vol_20d_exp=44.15 max_corr=0.47@F021 incr_ic=0.011 | close-position 60d 长窗放大 vol_20d 吞噬 (vs C004 20d alpha_surv=0.43)，**T012 重要发现：窗口翻倍让 vol_20d 吸收翻倍** | [[batches/batch_058/candidates/C006]] |

**档位编码**：🟢 最优档（aligned/strong/good/low/stable）· 🟡 次档（mixed/borderline/acceptable/medium）· 🟠 边际 · 🔴 阻断档（misaligned/weak/poor/high/unstable）。本批所有 hard_gate 全过（首批 6/6 hard_gate pass + 含 admit）。

## 跨候选对比

- **本批最显著结构事实：6/6 hard_gate 全过 + 1 admit + 2 reserve**——zero_admit_streak=2 (b056+b057) 终结。Phase 1 的 4 道 anti-recap 闸（family-bucket / RHS-endpoint / library-reducer / dominant-style）+ cockpit 强约束（vol_20d 正交 atom + long-window scale-free RHS）有效——三种 LHS atom 类（sign-aggregation extension / sign-product co-aggregation / close-position）都过 hard gate，区别只在 CP04 (alpha_surv vs rank_diff floor) 与 CP05 (F203 cluster co-resonance) 上分化。
- **窗口长度 × LHS atom 二律 (T011 vs T012)**：
  - **T012 close-position**: 20d (C004 alpha_surv=**0.43**) → 60d (C006 alpha_surv=**0.19**) — 窗口翻倍 vol_20d 吞噬翻倍
  - **T011 sign-product**: 20d (C003 mono=**0.40** + Q5 反向, alpha_surv=**0.56**) → 60d (C005 mono=**0.9** 完美, alpha_surv=**0.26**) — 长窗清洁 mono 但放大 vol 吞噬
  - **共性**：长窗都让 alpha_surv 衰减；**差异**：close-position 短窗 mono 已稳, sign-product 必须长窗才稳。这是 csi1000 cross-section 上两类 LHS 的 sample-size 与 vol 共线性的结构性差异。
- **F203 cluster co-resonance 触发 3 次**：C001 (max_corr=0.576@F018 + incr_ic=0.008<0.015) / C005 (max_corr=0.49@F021 + incr_ic=0.011<0.015) / C006 (max_corr=0.47@F021 + incr_ic=0.011<0.015)。**F021 在本批是 RHS=Mean(H/L,60) 共享的 anchor**——3 候选 (C002/C005/C006) 都有此 RHS, 全部命中 F021 cluster。**F021 in cluster 风险升级**：未来 H/L_60 类 RHS 设计需注意 F021 已成 anchor。
- **Style 聚合**：6 候选 dominant_style 全部 vol_20d，但 vol_20d_exposure 范围广 (C003=11 → C006=44)——**LHS atom 类型决定 vol_20d 暴露强度**：
  - sign-product 20d (C003): exposure=11.17 (最低)
  - sign-product 60d (C005): exposure=26.01
  - close-position 20d (C004): exposure=31.79
  - sign-aggregation 60d (C001): exposure=36.67
  - intraday body sign 20d (C002): exposure=40.31
  - close-position 60d (C006): exposure=44.15 (本批历史第二高，仅次 b057 C003 VWAP-open=48.04)
- **MT 预算推进**：cumulative 306 → 312（持续推进）；direction 21 → 27（overnight_intraday_split 已是 direction 数最高方向，bucket=high 封顶但 search_adjusted 仍 medium）。本批所有候选 MT bucket=high。
- **Library-clean candidates**：C003 (max_corr=0.216@F009) + C004 (max_corr=0.283@F006) 是本批两个 library-clean 候选；其中 C003 因 ls_t<2 + mono_oos=0.4 reject, C004 满足综合条件 admit。**incremental_ic 0.012 (C004) 与 0.017 (C003)**：C003 的库增值更高但 rank-order 破坏使其无法用 — confirms C204 律（library-clean 是必要不充分条件）。

## Thread 进展

> [!success]- T005 [[directions/overnight_intraday_split#T005]] — `[✓ ANSWERED batch_048+049, 升格 lessons]`（本批 evidence 追加）
> C001/C002 作为 T005 sign-aggregation 跨 axis 泛化的两个延伸：(a) C001 60d 窗口扩展兑现 mono+IC 但 F203 cluster co-resonance reserve；(b) C002 intraday body sign LHS 切换是 vol/str_1m 载体 reject。Thread 维持 ANSWERED（已升格 lessons），新 evidence 不重启 thread。

> [!note]+ T011 [[directions/overnight_intraday_split#T011]] 🆕 — `[◉ ACTIVE]`
> sign-product co-aggregation 新 thread。C003/C005 两候选共同回答："Mean(Sign(o)*Sign(i),N) cross-section rank-diff 几何"——20d cross-section rank-order 退化, 60d 长窗清洁 mono 但 alpha_surv<floor + F203 cluster。**Next probes**：60d sign-product LHS × 非 H/L_60 RHS（脱 F021 cluster）；magnitude-weighted sign-product 短窗。

> [!note]+ T012 [[directions/overnight_intraday_split#T012]] 🆕 — `[◉ ACTIVE]`
> intraday close-position-in-range Mean LHS 新 thread。C004/C006 两候选共同回答："Mean((C-L)/(H-L),N)" 在 20d 是 vol_20d 正交 atom (C004 admit), 60d 长窗放大 vol 吞噬 (C006 reject)。**首兑现** F022 candidate close_position_amount_accel_rd_20。**Next probes**：维持 close-position 20d, RHS 替换探索 (turnover/value 长窗 ratio)。

## 方向级反思

本方向第 8 个 admit (F022 candidate)，rounds=8，admits=8（**100% admit/round 比 — 整库最高**）。incremental_ic 中位数本批 0.011 (C001/C005/C006) 到 0.017 (C003), 与 batch_049 (F018 incr_ic=0.015) 持平——**方向 edge 仍 productive**，但已基本探尽 LHS atom 类目（overnight magnitude / overnight sign / intraday spread / sign-product / close-position 5 类已覆盖）。

**结构演进**：本方向已从 b048 的"rank-diff 范式发现期"（F017）→ b049 的"sign-aggregation paradigm"（F018）→ b058 的"close-position vol-orthogonal axis 发现期"（C004 admit）。下一步 T011/T012 follow-up 设计已 enumerate 完毕（见 thread Next probes）。

**何时该 saturated？**：本方向 admit/round=100% + 仍有 2 个 ACTIVE thread + cluster co-resonance 主导 reject 而非 hard_gate fail——明显仍 productive。但已经 21 candidates 累积 (direction.exposure=57 完全饱和)，MT bucket=high 是结构性。下一批 follow-up 应优先探**新 LHS atom 类**（如 turnover 在 cross-section 的高阶矩 / order-flow 不平衡 proxy 等）以避免在已知 5 类内的 micro-iteration。

**zero_admit_streak**: 2 → **0**（终结）。consolidation_trigger: rounds_since_last=3 < 10，**不触发**。calibration_trigger: 本批 admit=1，**不触发**。
