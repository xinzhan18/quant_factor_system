---
batch_id: batch_104
direction: nonlinear_autocorr_entropy
judged_at: 2026-05-16T12:10:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reserve}
batch_summary: {total: 6, admit: 0, reserve: 1, reject: 5}
admit_count: 0
reject_count: 5
reserve_count: 1
candidate_count: 6
mt_bucket: medium
---

# batch_104 Judge Summary

> [!abstract]+ batch_104 · [[directions/nonlinear_autocorr_entropy]] · 6 candidates
> ✅ **admit=0** · ⏸ **reserve=1** (C006 RV ratio) · ❌ **reject=5**
> **核心发现**: 6 候选覆盖 5 种 0-admit op family (Tanh / TsAutoCorr / TsEntropy / SignedPower / WMA / RealizedVol)。**ratio 形式 (C006 RV 5d/20d) 是本批唯一打破 vol_20d Barra absorption 的结构** (alpha_surv=1.20, style_r²=0.072, max_corr=0.21 三角成立)，但 stat 强度仅 borderline (ls_t=2.12, Q5 一桨)，incr_ic=-0.009 微负 → reserve 锚点。其余 5 候选揭示三种 absorption 失败模式（详见跨候选反思）。
> **MT Budget**: cumulative 582 → **588** · direction 0 → **6** · bucket `medium`（首批本方向）· 本批 low=0 / med=3 / high=0（仅 hard_gate 过的 C004/C005/C006 进 MT 评分）

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 Tanh-envelope | ❌ reject | hard_gate | corr 0.934@F027 | 单调 envelope 不改 rank → 与 close-position 信号几何同构 | [[batches/batch_104/candidates/C001]] |
| C002 TsAutoCorr | ❌ reject | hard_gate | ic_oos -0.006 < 0.008 | 几何独立 (max_corr=0.13) 但无 cs-spread，autocorr 是 ts 级而非 cs 级 alpha | [[batches/batch_104/candidates/C002]] |
| C003 TsEntropy turnover | ❌ reject | hard_gate | sign_flip + decay -0.90 | 2020-2021 regime drift，IS 正 OOS 负，机制时变性极强 | [[batches/batch_104/candidates/C003]] |
| C004 SignedPower | ❌ reject | 🟡·🟢·🔴·🔴·🟢 | ic_oos -0.042 alpha_surv=0.236 max_corr=0.69 | sqrt 单调变换保 sign → 被 str_1m 更深吸收，与 F027 同源 | [[batches/batch_104/candidates/C004]] |
| C005 WMA-SMA bias | ❌ reject | 🟡·🟢·🔴·🔴·🟢 | ic_oos -0.034 alpha_surv=0.158 max_corr=0.79 | WMA-SMA 顶层差分被 vol_20d 吸收 + 与 F028 同源 | [[batches/batch_104/candidates/C005]] |
| C006 RV 5d/20d ratio | ⏸ reserve | 🟢·🟠·🟢·🟢·🟢 | ic_oos -0.017 alpha_surv=**1.20** style_r²=**0.072** max_corr=0.21 | **本批唯一打破 vol_20d absorption 的形式**；stat 强度不够 admit | [[batches/batch_104/candidates/C006]] |

**档位编码**：🟢 最优档 · 🟡 次档 · 🟠 边际 (CP03 borderline) · 🔴 阻断档 · `hard_gate` reject 列不填色。

## 跨候选对比

**1. Three absorption-failure modes 揭示**（这是本批最重要的结构发现）：

| Mode | 例 | 机制 | 失败位置 |
|---|---|---|---|
| **(a) 单调变换 ≡ rank 同构** | C001 Tanh(close/MA-1) | 单调 envelope (Tanh/Sigmoid) 不改 rank order → 与原信号 corr 高 | CP01 hard_gate near_duplicate |
| **(b) 单调变换保 sign 加深吸收** | C004 SignedPower(20d ret) | sqrt 改变 magnitude 权重但保 sign → 被 str_1m / vol_20d 更深吸收 | CP04 poor + CP05 high |
| **(c) Top-level diff/bias 仍同 family** | C005 WMA(10)-Mean(20) | 权重函数差异（weighted vs equal）在 cs-rank 层被抹平 → 与库内 close-position family 高度重合 | CP05 high (corr 0.79@F028) |

**唯一 break 模式 (d) ratio cancels common mode**: C006 RV(5)/RV(20) — 分子分母同含 vol baseline cancel 后保留 vol-of-vol residual。**confirmed structurally**，但 cs-rank 强度不够 admit。

**2. Style 聚合**：
- C001/C004/C005 dom=vol_20d 或 str_1m，crowding=high；C006 dom=vol_20d 但 crowding=medium（style_r² 仅 0.072）
- 6 候选里有 3 个 (C004/C005/C001) 与 F027 多窗口 close/MA 均值高 corr (0.69-0.93) → **csi1000 daily 上 short-term close-position rank 子空间已被库覆盖**

**3. 相关度 cluster**：
- C001 (Tanh close/MA) ↔ F027 (multi-window MA): corr 0.93（实质同信号）
- C004 (SignedPower 20d ret) ↔ F027: corr 0.69
- C005 (WMA-SMA bias) ↔ F028 (CMO up/down counting): corr 0.79
- C006 ↔ 库内最高仅 0.21 (F022)，**真正几何独立**

**4. MT 预算推进**：本方向首批，direction_candidates 0 → 6；cumulative 582 → 588。bucket medium。3 个 hard_gate-pass 候选的 search_adjusted 都在 medium bucket 上界（0.51-0.59）。

**5. zero_admit_streak**: 本批继续，5 → 6 (b099-b104)；C006 reserve 提供下批锚点候选，未升至 saturation。

## Thread 进展

> [!failure]+ T001 [[directions/nonlinear_autocorr_entropy#T001|T001 — Nonlinear envelope]] — `[✗ DISPROVEN batch_104]`
> C001 Tanh hard_gate near_duplicate F027；C004 SignedPower 被 str_1m 更深吸收 (alpha_surv=0.236)。**结论：单调 envelope (Tanh/Sigmoid/SignedPower) 顶层套在已存在信号上不破 absorption** — 因为 cs-rank 由 rank order 决定，单调函数保 rank（C001）或保 sign 加深 style 投影（C004）。**Thread disproven**。下次若探索非线性 envelope 必须 (a) 配合 cross-term 改变 rank（如 SignedPower(x) × y） 或 (b) 在被吸收 layer 之前做（如 Mean(SignedPower(ret_1d), 20) 而非 SignedPower(Mean(ret, 20))）。

> [!failure]+ T002 [[directions/nonlinear_autocorr_entropy#T002|T002 — 二阶/分布 statistics]] — `[✗ DISPROVEN batch_104]`
> C002 TsAutoCorr ic_oos -0.006 < 0.008（ts-level signal 无 cs-spread）；C003 TsEntropy regime drift（2020-2021 sign 翻转）。**结论：TsAutoCorr/TsEntropy 0-admit op 在 csi1000 daily forward return 上 cs-spread 不足或机制时变**。TsAutoCorr 真正问题是 60d lag-1 autocorr 在个股层面分布太窄无 cs 区分；TsEntropy 真正问题是 attention pulse → crowding 信号的 regime drift。**Thread disproven for daily forward return**。

> [!note]+ T003 [[directions/nonlinear_autocorr_entropy#T003|T003 — Weighted MA / Vol ratio]] — `[◉ ACTIVE]` (部分推进)
> C005 WMA-SMA bias hard rejected (max_corr=0.79@F028, alpha_surv=0.158)；**C006 RV ratio 是本批关键 win**：alpha_surv=1.20 + style_r²=0.072 + max_corr=0.21 首次结构性 confirm "ratio cancels common vol mode"。但 stat 强度仅 borderline (ls_t=2.12, Q5 一桨, incr_ic=-0.009 微负) → reserve。**Thread 仍 ACTIVE**：下批应在此机制基础上参数扫描 / cross-term 组合提升 cs-rank 强度。

> [!note]+ T004 [[directions/nonlinear_autocorr_entropy#T004|T004 — Vol-of-vol ratio family]] 🆕 — `[◉ ACTIVE]`
> 承接 T003 confirm 的 ratio-cancel-common-mode 机制。新 thread 专注 RealizedVol / Std ratio family 的参数扫描 + cross-term。candidates: RV(3)/RV(20), RV(5)/RV(60), RV(10)/RV(40), 以及 RV ratio × volume / amount 组合。

## 方向级反思

**本方向 edge**：T001/T002 disproven（单调 envelope + ts-level autocorr/entropy 在 csi1000 daily 上不携带独立 alpha）；T003 confirm "ratio cancels vol common mode" 但 cs-rank 强度不够；T004 新建作 vol-of-vol family 锚点 thread。

**核心发现写入 lessons.md 候选（待 Phase 5 升格）**：
1. **"Top-level monotonic transform ≡ rank-identity"**: 单调 envelope (Tanh/Sigmoid/SignedPower/Log) 顶层套用不改 cs-rank order，与原信号几何同构。要 break linear absorption 必须改变 rank（cross-term）或 transform 在 aggregator 之前。
2. **"Ratio of same-family statistics cancels common mode"**: RV(5)/RV(20) 这种"短/长同 op"结构 cancel 共同 vol component，是 vol absorption 的首个结构性突破口（C006 alpha_surv=1.20 vs 其它 vol_20d-dom 候选 alpha_surv 0.15-0.24）。

**下轮建议** (next_hint)：
- 走 T003/T004 vol-of-vol ratio family 参数扫描 + cross-term，目标 RV ratio × amount/turnover 组合，希望 cs-rank 强度 ls_t 从 2.12 推到 3+
- 如效果不够，考虑 paper-driven direction（[[directions/reserve_revival_paths]] 或 raw papers 队列）
- 不要再做 single-op monotonic envelope（T001 disproven）或 raw TsAutoCorr/TsEntropy on csi1000 daily（T002 disproven）

**zero_admit_streak**：5→6 batches；本批关键 reserve C006 + 新 thread T004 提供下批锚点，不触发 saturation。

**MT 预算**：direction 6/40 medium，仍宽松；可继续探索 T003/T004。

**校准触发检查**: 
- 错杀 flag: 无（C006 max_corr=0.21 < 0.30 但 incr_ic=-0.009 magnitude < 0.010，不满足错杀条件）
- 连续零 admit 警戒: 6 batches zero admit + 累计 reserve ≥ 9，但 reserve 是否满足"max_lib_corr<0.30 + incr_ic>0.010" 双独立条件，需 retro triage（建议下轮触发 `/factor-consolidate calibration` 全 reserve pool 复活筛选）
- Reserve 积压: 累计 reserve/judged 比例需查（cockpit_hints 提及 reserve ≥9） — 接近触发阈值
- 悖论复现: dom_style=vol_20d 但 style_r² 极低的"非典型 vol absorption"模式，C006 是第二次出现（前次 b068 vol_20d 直接吸收）
