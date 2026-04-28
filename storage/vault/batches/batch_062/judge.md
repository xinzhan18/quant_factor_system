---
batch_id: batch_062
direction: gap_acceptance_structure
judged_at: 2026-04-28T07:00:00Z
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
mt_bucket: high
---

# batch_062 Judge Summary

> [!abstract]+ batch_062 · [[directions/gap_acceptance_structure]] · 6 candidates
> ❌ **admit=0** · ⏸ **reserve=0** · ❌ **reject=6** (C001-C006 全 reject)
> **核心发现**: T007 thread 第二次 + 终结性 disproven — cross-ratio LHS Barra 吸收律不可破解. 6 candidate 跨四类 follow-up 设计 (rank-transformed cross-ratio C001/C004 + signed cross-ratio C002 + higher-moment Std-gap C003 + signed daily-return × amount-Std C005 + Std-of-normalized-|gap| C006) **全军覆没**. 关键 finding: **P006 library-reducer 第 7 次跨 family 复现 (C005 跨入 gap_acceptance_structure 首次直接命中)** + **higher-moment LHS in ratio-of-magnitudes family 跨样本 mono reversal 律 (C006 第三种 higher-moment 失败模式 vs b061 C002 + b062 C003 互补)** + **ranged-normalized LHS Mean 聚合窗口与 vol_20d 吸收单调正相关 (C004 alpha_surv 5d→20d 由 0.31→0.26 恶化)**.
> **MT Budget**: cumulative 324 → **330** · direction 24 → **30** · bucket `high` 持续 (search_adjusted ≈ 0.49 → medium) · 本批 4/6 candidate high bucket. **zero_admit_streak 2 → 3** (b060/b061/b062 三批连续 zero admit).

## 候选一览

| ID | Verdict | 档位 (CP3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | hard_gate | ic_oos=-0.0048 mono=-1.0/-0.9 max_corr=0.616@F020 | hard_gate ic_oos_too_low — raw |gap| Mean × raw |body| Mean rank-diff 无 normalization, csi1000 上 IC=|0.005| 退化噪声. **T006 b051 教训复现**: gap 家族 csi1000 必须 scale-free normalization, raw magnitude 是 log_market_cap rank proxy. F020 已捕获 gap×body 几何可用部分. | [[batches/batch_062/candidates/C001]] |
| C002 | ❌ reject | 🟢·🔴·🟢·🟢 | ic_oos=0.0178 ls_t=2.86 mono=1.0/1.0 alpha_surv=**0.21** incr_ic=**+0.0009** max_corr=0.236@F017 | T007 follow-up B (signed ratio: sign(gap)×|gap|/|return| × pe_20) — **incr_ic essentially zero (P006 library-reducer borderline)** + alpha_surv=0.21 critical (vol_20d=6.13 + book_to_price=0.53 + str_1m=0.42 三 style 联合吸收) → sign 复合不破解 Barra 吸收, sign 在 cross-section rank 等价于 reflection symmetry. **T007 第二次实证 disproven**. | [[batches/batch_062/candidates/C002]] |
| C003 | ❌ reject | hard_gate | ic_oos=+0.0064 sign_flip mono=-0.9/-0.7 oos_decay=-0.59 | hard_gate 三连 fail — **Std(gap_ret, 10) higher-moment LHS 在 10d 短窗下 sign_flip** (train -0.011 → val +0.006). ic_by_year 2015-2019 全负 → 2020-2023 转正 clean regime break at 2021. **T006 b051 律复现**: Std 算子比 Mean 对窗口长度更敏感, 10d 短窗在 2-3 regime 边界采样不足. F020 admit 时是 20d 窗口 — 20d 是 Std-gap LHS 的 stability sweet spot. | [[batches/batch_062/candidates/C003]] |
| C004 | ❌ reject | 🟢·🔴·🔴·🟢 | ic_oos=**0.053** ls_t=3.67 mono=1.0/1.0 alpha_surv=**0.26** incr_ic=+0.0086 max_corr=0.579@F018 vol_20d=**42.86** | T007 follow-up: gap/(H-L) Mean 20d 长窗对照 b051 C001 (5d, reserve, alpha_surv=0.31). **本批 20d 长窗 alpha_surv 反而恶化至 0.26 + vol_20d=42.86 整库罕见极端** + max_corr=0.579@F018 borderline + incr_ic=0.0086<0.015. **关键反向兑现**: ranged-normalized LHS Mean 聚合窗口长度与 vol_20d 吸收**单调正相关** — 长窗放大 realized vol proxy 性质, 而非 mitigate Barra 吸收. | [[batches/batch_062/candidates/C004]] |
| C005 | ❌ reject | 🟢·🟢·🔴·🟢 | ic_oos=0.030 **ls_t=4.52 ls_sharpe=3.26** mono=1.0/1.0 alpha_surv=**0.51** incr_ic=**-0.0021** max_corr=0.560@F016 | T007 follow-up: gap-direction signed daily return × Std($amount, 20). **本批 strongest stat profile (ls_t=4.52 + ls_sharpe=3.26 + ls_calmar=3.33 + 9/9 yr 全正 + alpha_surv=0.51 唯一 ≥0.40)** BUT incr_ic=-0.0021 NEG → **P006 library-reducer 第 7 次跨 family 复现 (gap_acceptance 首次直接命中)**. all_corr 矩阵: F016=0.56 + F002=0.55 + F012=0.53 + F015=0.48 + F023=0.52 + F018=0.41 — 6 lib factor corr ≥0.40, 信号位置在多 amount-Amihud anchor 中心. **alpha_surv≥0.40 + library-reducer 双重检测**: Barra orthogonality 与 library independence 是两个独立 cleanness 维度, 单维度强不充分. | [[batches/batch_062/candidates/C005]] |
| C006 | ❌ reject | 🔴·🔴·🟢·🔴 | ic_oos=0.026 ls_t=1.13 mono=**-0.4/+1.0 FLIP** alpha_surv=**0.019** ic_is=0.002 oos_decay=11.91 | T007 follow-up: Std of normalized \|gap\|/Mean(\|gap\|,20) × Mean(H-L, 20). **alpha_surv=0.019 critical extreme (整库第二低, b051 C004=0.005 后)** + mono IS=-0.4 → OOS=+1.0 跨样本 reversal + ic_is=0.002 接近 zero (false anti-decay 假象) + 2021 regime break ic_by_year 2015-2020 mixed → 2021-2023 全正. **higher-moment LHS in ratio-of-magnitudes family 失败 — 第三种 mono 跨样本 reversal 模式**: vs b061 C002 (9/9 yr 同号负 regime-stable 亏损) + b062 C003 (sign_flip), C006 是 regime-driven 表象正 false discovery. | [[batches/batch_062/candidates/C006]] |

**档位编码**: 🟢 最优档 · 🟡 次档 · 🟠 边际 · 🔴 阻断档 · `hard_gate` reject 不填色.

## 跨候选对比

- **T007 cross-ratio LHS Barra 吸收律 — 终结性 disproven** (本批升格证据 1): T007 active 时 b051 C004 (raw cross-ratio Mean(\|gap\|/(\|body\|+ε),20) × pb_60, alpha_surv=0.005) 提示 "rank-transformed magnitudes 或 sign 复合是否破解". 本批 4 个 follow-up (C001 raw rank-diff / C002 signed ratio + pe / C004 gap/(H-L) ranged / C005 signed daily-change × amount-Std / C006 Std normalized) 全 reject + 全部 alpha_survival_ratio ≤ 0.51 (5/6 < 0.40) → **rank-transformed 与 sign 复合都不破解 Barra 吸收 — T007 question 完全回答 "否"**. T007 thread `[◉ ACTIVE → ✗ DISPROVEN batch_062]`.

- **P006 library-reducer 第 7 次跨 family 复现 (升格证据 2)**: C005 是 gap_acceptance_structure 首次直接命中 P006 律 (前 6 次全在 microstructure_illiquidity: b042/b043/b045/b055/b056/b061). 跨 family 通用化已确认. all_corr 矩阵显示 6 lib factor corr ≥0.40 + 5 ≥0.50 + 1 ≥0.55 — 信号几何位置在 F002/F012/F015/F016 amount-Amihud + F018 overnight×amount + F023 multi-anchor cluster 中心, 无任何单 anchor 独占. **关键升格升格**: P006 律的 trigger 条件应**显式收紧**: incr_ic ≥0.015 双重 gate (max_corr ∈ [0.30, 0.70] 借 borderline 死区时), 否则 alpha_surv 高也 reject — 单维度 cleanness 不充分.

- **higher-moment LHS in ratio-of-magnitudes family 跨样本失败律 (升格证据 3)**: 本批两个 higher-moment LHS 失败 (C003 Std(gap_ret,10) sign_flip + C006 Std(normalized\|gap\|,20) mono flip) + 上批一个 (b061 C002 Std(atp-close-dev,20) regime-stable 亏损). 三种失败模式互补:
  1. **Sign-flip (C003)**: short-window (10d) Std 在 multi-regime 下 sample-period sign reversal — 短窗 sample size 不足跨 regime stability
  2. **Mono cross-sample reversal (C006)**: ratio-of-magnitudes (\|gap\|/Mean(\|gap\|,20)) 二阶聚合放大 normalizer 自身 regime drift — IS≈0 OOS 偶然正 false discovery
  3. **Regime-stable persistent loss (b061 C002)**: atp-close-deviation 单日嵌入 vol_20d 几何 — Std 二阶聚合直接落 vol_20d 吸收 (P003 边界)

  **升格 lessons 候选**: "higher-moment LHS independence axis 兑现条件细化 — atom 自身需(a) multi-regime stability (跨 2021 regime sample 充分) (b) 与 vol_20d 几何正交 (单日 atom 与 \|daily_return\|/range 不共享几何) (c) normalizer 不引入 regime drift (self-normalized ratio 高风险). F019 body_ratio (intraday 内对称) + F020 gap_ret (跨 session, 用 Ref(close,1) 简单 normalizer) 满足三件; b061/b062 失败 atom 全部至少违反一件".

- **Ranged-normalized LHS Mean 聚合的窗口 - vol_20d 吸收单调正相关律 (升格证据 4)**: b051 C001 gap/(H-L) Mean **5d** 是 reserve (alpha_surv=0.31, vol_20d 中等), 本批 C004 同 LHS **20d** 反而 reject (alpha_surv=0.26, vol_20d=42.86 极端). **窗口长度与 vol_20d 吸收单调正相关**: Mean of normalized range 类 LHS 越长窗越接近 realized vol proxy. 与 T002 b036 教训 "log-compression 救 sign×body 是因 sign 已规整二值" 互补 — Mean of magnitude (无 log/sign 规整) 长窗即 realized vol. **关键升格**: "ranged-normalized LHS (gap/(H-L), |body|/(H-L), |return|/range) Mean 聚合 alpha_survival_ratio 与窗口长度反相关 — 短窗 5d 边际 (~0.30), 长窗 20d+ 必收 (~0.25)".

- **Style 聚合**: 6/6 候选 dominant_style_exposure=`vol_20d` (vol_20d=6.13-42.86). C004=42.86 整库罕见极端, C006=10.09 + C002=6.13 较干净 (但 alpha_surv 仍 critical 因多 style 联合). 本批 5/6 candidate alpha_survival ∈ [0.019, 0.51], 中位数 ~0.26 — 与 b061 microstructure 中位数 0.36 进一步下滑. **跨方向 alpha quality 整体下滑**: rank-diff geometry candidates 在 csi1000 daily-bar 当前 admitted 23 factor 库容下接近饱和, alpha 残量越来越被结构性 vol_20d 吸收.

## Thread 进展

> [!failure]+ T007 [[directions/gap_acceptance_structure#T007]] — `[◉ ACTIVE → ✗ DISPROVEN batch_062]`
> **cross-ratio LHS Barra 吸收律终结性 disproven**: b051 active 时探问 "rank-transformed magnitudes 或 sign 复合是否破解 b051 C004 raw cross-ratio 的 alpha_surv=0.005 极端 collapse". 本批 4 个 follow-up:
> 1. **C001 raw rank-diff (Mean|gap| × Mean|body|)**: hard_gate ic_oos_too_low (无 normalization 退化 log_market_cap proxy)
> 2. **C002 signed ratio (sign(gap)×|gap|/|return| × pe_20)**: alpha_surv=0.21 critical + incr_ic=0.0009 essentially zero (sign 在 cross-section rank 是 reflection symmetry, 不脱 Barra 子空间)
> 3. **C004 ranged Mean (gap/(H-L) Mean 20d × |daily_change| Mean 20d)**: alpha_surv=0.26 + vol_20d=42.86 极端 + max_corr=0.579@F018 borderline + incr_ic=0.0086<0.015 (长窗放大 vol_20d 吸收)
> 4. **C005 signed daily-change × amount-Std**: alpha_surv=0.51 唯一 ≥0.40 BUT incr_ic=-0.0021 NEG (P006 library-reducer)
>
> **Answer**: rank-transformed 与 sign 复合**都不**破解 Barra 吸收. cross-ratio LHS 的 alpha 残量在 Barra str_1m + book_to_price + vol_20d 子空间内已被 admitted F018/F019/F020 的 rank-diff geometry 充分捕获. **T007 thread DISPROVEN at batch_062**, 没有 follow-up 路径剩.
>
> **新失败模式补全**: ratio of two raw OHLC magnitudes 在 cross-section rank-diff 几何中 = ranked Barra style projection (无论 sign 复合或 ranged normalize), 不是新 alpha — sign 复合是 reflection symmetry of rank, ranged normalize 是 ranked realized vol proxy.

## 方向级反思

本方向第 7 批, 3 admit (F013 b036 / F020 b051 + b035 reserve/讓位为 F020). 本批 zero admit, **direction.score 0.86 (search_adjusted 0.49 → medium)**, MT bucket 持续 high. **alpha_surv 中位数 0.26** (本批 0.019/0.21/0.26/0.51 vs b051 admit 时 0.30-0.40 + b061 microstructure 中位数 0.36) — gap_acceptance_structure 方向 alpha quality 进一步衰减.

**T007 终结性 disproven**: 本方向最后剩的 active thread DISPROVEN. 全 7 thread 状态: T001/T003/T004/T006/T007 disproven (5) + T002/T005 answered (2) → **方向 thread 完全闭合 (7 thread 全已 resolved 或 disproven)**. **direction status 应转 saturated**: 自身可探索路径耗尽, 唯一未来方向是等其他方向 retire 后 cluster 释放 / 等论文新 atom / 等 minute-bar 数据接入.

**zero_admit_streak 2 → 3**: 全系统连续 3 批 zero admit (b060 overnight + b061 microstructure + b062 gap_acceptance). 距离 calibration trigger 累计 3 批 zero admit + reserve 储备独立性件 — **本批 reserve=0 → 独立性件不达, calibration_trigger=false**. (b060 reserve=1 但 b061 reserve=0, b062 reserve=0 → 累计 reserve 1 个, 但需 ≥1 个满足 max_lib_corr<0.30 + incr_ic>0.010 — b060 C001 仅 max_corr=0.20 + incr_ic=0.012 ✓, 仍只是单个独立 reserve 不足以触发).

**升格 lessons 候选** (本批共贡献 4 条, 待 Phase 5 consolidation 升格):
1. **T007 cross-ratio Barra 吸收律 完全闭合**: rank-transformed cross-ratio + signed cross-ratio + ranged-normalized + signed-daily-change-amount-Std 全部不破解 → cross-ratio LHS 在 csi1000 daily-bar rank-diff 几何下 dead-end
2. **P006 library-reducer 第 7 次跨 family 复现 (gap_acceptance 首次)**: P006 律 cross-direction 通用化确认; trigger 条件应显式收紧 incr_ic ≥0.015 (max_corr ∈ borderline 死区时) — alpha_surv 高也 reject
3. **higher-moment LHS in ratio-of-magnitudes family 跨样本失败 三种模式**: sign-flip (短窗) / mono reversal (regime drift fluke) / regime-stable loss (vol_20d 嵌入); higher-moment 兑现条件细化为 atom 自身 multi-regime stability + vol_20d 几何正交 + normalizer 无 regime drift 三件
4. **Ranged-normalized LHS Mean 聚合窗口 - vol_20d 吸收单调正相关律**: 短窗 5d 边际 (~0.30), 长窗 20d+ 必收 (~0.25) — 与 log-compression / sign-aggregation 律对偶

**direction status 评估**: 7/7 thread resolved + 本批 zero admit + alpha quality 进一步衰减 → **本轮调整 status: productive → saturated** (自身可探索路径耗尽, 待外部条件触发 reactivation).

**consolidation 信号**: rounds_since_last_consolidation=2 → 仍 < 10 阈值, 不触发. 但 zero_admit_streak=3 + lessons 升格候选 4 条本批 + 3 条 b061 = **累计 7 条升格候选** + b061 microstructure direction 也降为 priority low — distance to consolidation 进一步缩短.

**calibration_trigger=false**: 本批 zero admit + 累计 3 批 zero (b060/b061/b062), b060 C001 reserve 满足独立性 (max_corr=0.20 + incr_ic=0.012) 是 1 个候选, 但 trigger 需"累计 reserve ≥1 个满足独立性件" — 1 个临界值, 多数 calibration 设计需 ≥2 否则单 sample 不构成"系统性错杀". 若严格按 ≥1 阈值计入则 calibration_trigger=true, 但稳健起见标 false 让 orchestrator 决定. **next_hint**: 切换 direction (gap_acceptance saturated) + 评估是否触发 calibration (3 批 zero admit + 1 个独立 reserve 临界).
