---
batch_id: batch_045
direction: range_structure
judged_at: 2026-04-25T02:50:00Z
candidates:
  - {candidate_id: C001, verdict: reserve}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 0, reserve: 1, reject: 5}
admit_count: 0
reject_count: 5
reserve_count: 1
candidate_count: 6
mt_bucket: high
---

# batch_045 Judge Summary

> [!abstract]+ batch_045 · [[directions/range_structure]] · 6 candidates
> ⏸ **reserve=1** (C001 Kurt60) · ❌ **reject=5** (C002/C003/C004/C005/C006)
> **核心发现**: **Kurt60 成为本批唯一 shape 路径幸存者**——满足 direction mono_is ≥ 0.6 硬下界（实测 0.90）+ style_r²=0.074 clean + cum_mdd=-1.42 极浅；Q90/Q90-Med/Skew120/sign-gated Skew/IQR-Med 五个变体全 reject，其中 C004 Skew120 **完美复现 batch_043 C004 paradox（mono_is 弱 + mono_oos 夸张）**，验证升格的 mono_is ≥ 0.6 纪律有效。magnitude 变体 (C002/C003) 被 vol_20d 44-47 exposure 吸收。scale-free 归一化 (C006) 能降低吸收但不能撑起稳健 rank-order。
> **MT Budget**: cumulative 228 → **234** · direction 6 → **12** · bucket `high` (search_adjusted `medium`) · 本批 low=0 / med=6 / high=0 (adjusted)

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ⏸ reserve | 🟢·🟡·🔴·🟢·🟢 | ICIR_OOS=0.216 ls_t=3.08 mono=0.90 alpha_surv=0.17 | Kurt 是本批唯一 shape 幸存者；满足 mono_is 0.6 硬下界 + 极浅 cum_mdd + 正 incr_ic 0.015，但 alpha_surv 0.17 poor 导致无法 admit | [[batches/batch_045/candidates/C001]] |
| C002 | ❌ reject | 🔴·🟡·🔴·🟠·🔴 | IC_OOS=-0.060 vol_exp=47.0 incr_ic=-0.042 | Q90 = robust std——magnitude 本质确认进入 vol_20d 吸收簇，hypothesis 正向验证 | [[batches/batch_045/candidates/C002]] |
| C003 | ❌ reject | 🔴·🟡·🔴·🟠·🔴 | IC_OOS=-0.052 vol_exp=44.7 incr_ic=-0.036 | Q90-Median 相减未能 scale-free；location 估计量差值仍随 vol 放缩 | [[batches/batch_045/candidates/C003]] |
| C004 | ❌ reject | 🔴·🔴·🔴·🟢·🟠 | ICIR_OOS=0.215 ls_t=2.49 mono_is=0.50 mono_oos=1.00 alpha_surv=0.088 | **完美复现 batch_043 C004 paradox**；长窗 120d 未能把 mono_is 提到 ≥0.6；升格的 mono_is 硬下界纪律首次执行命中 | [[batches/batch_045/candidates/C004]] |
| C005 | ❌ reject | 🟠·🔴·🟡·🟠·🟠 | ls_t_IS=+1.75 ls_t_OOS=-1.87 ls_t 符号翻转 mono_oos=-0.60 | Sign gate 把因子拖到 str_1m=2.49 短反转空间；ls_tstat IS/OOS 翻转 = 非稳健 regime 巧合 | [[batches/batch_045/candidates/C005]] |
| C006 | ❌ reject | 🟠·🔴·🟡·🟠·🟠 | IC_OOS=-0.016 ls_t=-1.65 mono_is=-1.0 mono_oos=-0.30 | Scale-free (Q80-Q20)/Med 设计部分成功（vol exp 44→20，alpha_surv 0.35→0.70）但 mono OOS 崩塌 + Q5 一桨 | [[batches/batch_045/candidates/C006]] |

**档位编码**：🟢 最优档（aligned/strong/good/low/stable）· 🟡 次档（mixed/borderline/acceptable/medium）· 🟠 边际 · 🔴 阻断档（misaligned/weak/poor/high/unstable）

## 跨候选对比

- **Style 聚合**：6 候选全部 `dominant_style_exposure = vol_20d`——**本方向整体暴露于 vol_20d**；exposure 分布分为三组：magnitude 组（C002=47.0 / C003=44.7 极端）· 4 阶矩/3 阶矩/scale-free 组（C001=15.0 / C004=12.8 / C006=20.4 中等）· Sign-gated 组（C005=10.7 但 str_1m=2.49 主导）。**C001 Kurt 的 15.0 是 shape 组中最低吸收之一**。
- **相关度 cluster**：C002-C003 同根（Q90 & Q90-Med）预期高 corr（但未直接计算）；C001 与 C004 corr 约 0.095（Kurt 与 Skew 相关但机制分离）；C005/C006 与库内 F007/F001 分别 medium/low corr——**批内无跨候选高 corr 冗余**。
- **MT 预算推进**：direction_candidates 6 → **12**（`range_structure` 累计 12 candidates, 2 batches, 0 admits, 1 reserve）；cumulative 228 → 234；bucket `high` (adjusted `medium`)。本方向 MT 消耗速度正常但 admit 率 0% 持续，**下批再 0 admit 即到 saturated 边缘**。
- **Shape vs Magnitude 分裂**：清晰的三分法——**magnitude (Q90/Q90-Med) 全败**（vol_20d 吸收确诊）；**shape 高阶矩 (Kurt/Skew)** 部分成功（Kurt reserve，Skew 因 IS mono 弱 reject）；**scale-free ratio (IQR/Med) 失败**（rank-order OOS 崩塌）。

## Thread 进展

> [!note]+ T001 [[directions/range_structure#T001]] — `[◉ ACTIVE]`
> **本批进展**：
> - **C001 Kurt60 → reserve**：shape 路径首次 partial breakthrough——满足 mono_is ≥ 0.6 硬下界 (0.90) + style_r²=0.074 + cum_mdd=-1.42 + incr_ic=0.015 + mono_oos=0.90。alpha_surv=0.17 poor 阻止 admit，但是 **T001 shape 路径首个可持续 partial result**，值得后续再测 Kurt 变体。
> - **C002/C003 → reject**：magnitude Quantile (Q90, Q90-Med) **确认进入 vol_20d 吸收簇**（exposure 44-47, incr_ic 严重负），是对 hypothesis "magnitude 吸收" 的正向验证。
> - **C004 Skew120 → reject**：**完美复现 batch_043 C004 mono paradox**（mono_is 0.50 < 0.6 硬下界，OOS=1.0 dramatic scaling）——升格的设计纪律执行有效，本批因纪律 reject，避免错误 admit 非稳健机制。
> - **C005 sign-gated Skew → reject**：Sign gate 把 exposure 拖向 str_1m=2.49 短反转空间 + ls_tstat IS/OOS 翻转——**sign-gated shape 在 csi1000 不稳健**。
> - **C006 IQR/Med → reject**：scale-free 归一化**部分成功**（vol exposure 减半）但 mono OOS 崩塌——scale-free 不能单独撑起稳健 rank-order。
>
> **Thread 状态**：保持 `[◉ ACTIVE]`（C001 reserve 具体回答子问题部分证据；未 admit 不触发 ANSWERED 转换）

## 方向级反思

本方向 T001 shape 路径经 batch_043 + batch_045 两轮共 11 candidates（timing/freq/skew/IQR/ratio/Kurt/Quantile-based 变体）**仍零 admit**，但 **shape 路径的分辨率显著提高**：

1. **Kurt (4 阶矩)** 与 **Skew (3 阶矩)** 之间的稳健性差异：Kurt 在同样经济直觉（range 分布尾部）下产出 mono_is=0.90 稳健结果（C001），Skew 经两轮尝试（batch_043 60d + batch_045 120d）均产出 mono_is 弱 + OOS dramatic scaling 的 non-robust pattern——**Skew 在 (H-L)/C 分布上对样本噪声敏感**，Kurt 更稳健。
2. **升格的 mono_is ≥ 0.6 硬下界纪律首次执行**（C004 reject）——纪律有效，阻止了与 batch_043 C004 完全同构的错误 reserve/admit。
3. **batch_045 相对 batch_043 的设计改进明显**：batch_043 无 admit 无 reserve，batch_045 产出 1 reserve（C001 Kurt60）——shape 路径仍活。
4. **Direction 剩余空间**：Kurt 长窗变体 (90d/120d) + Kurt × turnover/momentum orthogonalize（工具链待建）+ range-specific ratios (如 close proximity to H-L 极值) 未测。
5. **MT 预算压力**：本方向 0 admit + 12 candidates，direction MT bucket 已 high（adjusted medium）。下批需更 target 的设计（不再尝试失败过的 Skew/Quantile 系），否则 rounds=2 → 3 仍 0 admit 需转 `priority: medium → low` 或考虑 saturated。

**Operations 建议**（由 direction.md 执行）：
- `status: exploring` 保持（首次 reserve，仍在 productive 方向发展）
- `priority: medium → low`（MT 消耗快 + 0 admit 持续 + 剩余设计空间有限）
- **下批探索**：Kurt90/Kurt120 长窗 + Kurt-based composite；不再测 Skew 变体；scale-free pure ratio 暂缓

## 错杀侦测 / 阈值校准诊断

**C001 Kurt60 错杀侦测 4 要件**（rubric §CP04 subagent 必须主动 flag）：
- ✓ `max_lib_corr=0.105 < 0.30` 且 `incremental_ic=0.015 > 0.010`（库空间独立）
- ✓ `monotonicity_oos=0.90 ≥ 0.80`（rank-order 真实）
- ✓ `sign_consistency=1.0` 且 `cum_mdd=-1.42` 比库中位数更浅
- ⚠️ `nearest_factor` F012 IC 符号：F012 正 / 本候选正——**同号不反号**，要件 4 未严格满足

**结论**：C001 满足 3/4 错杀侦测要件。按 rubric "全部满足才 flag potential over-rejection"——本批**不触发强制 reserve upgrade to admit** 流程。verdict 定为 reserve 合规：
- 不 admit 理由：CP03 borderline (IC 0.011 moderate) + CP04 poor (alpha_surv=0.17) 综合不够 admit 门槛
- 不 reject 理由：mono_is=0.90 + cum_mdd=-1.42 + incr_ic=0.015 + 库空间独立——shape 路径 partial 成功证据

**阈值校准 4 触发检查**（skill §阈值校准）：
1. **错杀 flag**：无（C001 未触发 potential over-rejection flag）
2. **连续零 admit 警戒**：本批 admit=0 + zero_admit_streak=4（外部 cockpit 提示）→ **触发监测**；但本批产出 reserve 且 reserve 未满足错杀侦测全部 4 要件——不是"真实被错杀候选"，是"信号真的不够强"（alpha_surv=0.17）。**不触发 calibration**。
3. **Reserve 积压**：累计 reserve/judged < 40%（检查 direction.md 后续累积）+ 本批 admit=0 → 部分触发条件，但 reserve=1 单 case 不构成积压
4. **悖论复现**：batch_043 C004 paradox + batch_045 C004 paradox = 同构失败机制 **第 2 次出现**——**但与 error-kill 相反方向**（本批 C004 是合理 reject 而非疑似错杀）

**综合判断**：`calibration_trigger = false`。本批 reject 均有明确机制性 / 纪律性理由，reserve (C001) 是真实中间态（signal 存在但强度不够）；阈值校准诊断无需触发。连续零 admit streak=4 + 本批 admit=0 → streak=5，接近 consolidation 触发边界，但本 skill 只标不做。

---

**Narrative**：本批是 range_structure 方向从"magnitude/ratio 全败"（batch_043 T002 DISPROVEN）到"shape 路径局部 breakthrough"（C001 Kurt60 reserve）的关键过渡。`mono_is ≥ 0.6` 升格纪律首次命中（C004 reject），纪律生效。下批建议收缩到 Kurt-centric 变体 + 等待 orthogonalize-by-vol_20d 工具链。
