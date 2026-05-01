---
batch_id: batch_063
direction: ohlc_temporal_aggregation
judged_at: 2026-04-28T08:30:00Z
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

# batch_063 Judge Summary

> [!abstract]+ batch_063 · [[directions/ohlc_temporal_aggregation]] · 6 candidates
> ❌ **admit=0** · ⏸ **reserve=0** · ❌ **reject=6** (C001-C006 全 reject)
> **核心发现**: T012 higher-moment OHLC × non-vol-cluster RHS 第二轮 — **6 candidate 跨四类 OHLC 三段 ratio 原子 (close_position / range_norm_prev_close / intraday_return_norm / open_position / upper_shadow / |gap|/range) 全军覆没**. 关键 finding: **higher-moment LHS atom-orthogonality 三件套 (P003) 第四种失败模式补全 — atom 自身即 vol_20d 直接 proxy (C002/C003 range/prev_close 与 (C-O)/prev_close 整库 vol_20d 新纪录 76.53)**; **OHLC algebraic mirror trap higher-moment 形态实证 (C001 close_position Std 与 F021 upper_shadow Std cluster=0.79)**; **rank-diff borderline 死区律第三次实证 (C004 max_corr=0.69 + incr_ic=0.006 < 0.015 双重 gate 不达)**; **strongest stat profile of batch (C004 ls_t=4.89 ls_sharpe=3.52 9/9 yr 全正) 但 library integration 仍 fail — 单维度 cleanness 不充分律重申**.
> **MT Budget**: cumulative 336 → **342** · direction 28 → **34** · bucket `high` 持续 (search_adjusted ≈ 0.49 → medium) · 本批 4/6 candidate high bucket. **zero_admit_streak 3 → 4** (b060/b061/b062/b063 四批连续 zero admit).

## 候选一览

| ID | Verdict | 档位 (CP3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | 🟢·🔴·🔴·🟢 | ic_oos=0.035 ls_t=2.00 mono=1.0/1.0 alpha_surv=0.31 incr_ic=**-0.0093** max_corr=**0.7914@F021** | T012 follow-up: Std(close_position,20) × turnover_60 — **CP05 红线超 0.70 (max_corr=0.79@F021) + library reducer (incr_ic=-0.009 NEG)**. close_position=(C-L)/(H-L) 与 F021 LHS upper_shadow=(H-C)/(H-L) **OHLC algebraic mirror higher-moment 形态** Std-of-each cross-section rank 高度同构. 验证 OHLC mirror trap higher-moment 也成立 (b018 C001 是 Mean 形态镜像). | [[batches/batch_063/candidates/C001]] |
| C002 | ❌ reject | 🟢·🔴·🟡·🟢 | ic_oos=-0.040 **ls_t=-3.88** mono=-1.0/-1.0 alpha_surv=**0.39** incr_ic=**-0.0086** max_corr=0.31@F016 vol_20d=**53.04** | T012 negative-direction signal (Std(range/prev_close,20) × pe_60). 强 stat (mono=-1.0/-1.0 perfect + 9/9 yr 同号负 regime-stable + cum_ic_dd=-82) 但 **vol_20d=53.04 整库罕见极端 + alpha_surv=0.39 just below 0.40 + incr_ic=-0.009 NEG**. **核心律**: range/prev_close LHS = realized vol direct proxy + Std 二阶聚合放大该 proxy → P003 vol_20d 吸收律核心; alpha-surv 三件套 atom-vol_20d 几何正交 ✗ (atom 自身就是 vol). **library reducer 复合检测**: 3/4 partial (mono ✓ ls_t ✓ incr_ic ✓ alpha_surv 0.39 不 ≤0.30) → 不 hard-block 但确认模式. | [[batches/batch_063/candidates/C002]] |
| C003 | ❌ reject | 🔴·🔴·🟢·🟡 | ic_oos=-0.023 **ls_t=-1.14** mono=-0.95/-0.85 alpha_surv=0.45 incr_ic=-0.006 max_corr=0.50@F002 vol_20d=**76.53** | T012 (C-O)/prev_close = signed daily intraday return Std × pb_60. **CP03 ls_t=-1.14<2.0 weak + style_r²=0.6991 整库新纪录 + vol_20d=76.53 整库新纪录 (超本批 C002=53.04)** + book_to_price=2.50 双 style 联合极端. signed price-normalized return Std = realized intraday vol → vol_20d 完全同构. **P003 vol_20d 边界第三次 escalate**: 76.53 > 53.04 (本批 C002) > 48.04 (b057 C003 前纪录). | [[batches/batch_063/candidates/C003]] |
| C004 | ❌ reject | 🟢·🟡·🔴·🟢 | ic_oos=0.032 **ls_t=4.89 ls_sharpe=3.52 ls_calmar=3.77** mono=1.0/1.0 alpha_surv=0.32 incr_ic=**+0.0062** max_corr=0.6873@F012 | T012 Std(open_position,20) × amount_60. **本批 strongest stat profile (ls_t=4.89 + ls_sharpe=3.52 + ls_calmar=3.77 + 9/9 yr 全正 + ic_by_horizon 1d→20d 0.032→0.095 strong cumulative + worst_quarter -0.001 几无负季度)** BUT **incr_ic=0.0062 < 0.015 (rank-diff borderline 死区律 incr_ic 双重 gate)** + alpha_surv=0.32 < 0.40 default + 6 lib factor corr ≥ 0.42 (F002=0.55 + F012=0.69 + F015=0.43 + F018=0.50 + F023=0.42 + F002=0.55) signal in F012 amihud anchor cluster center. **第三次 rank-diff borderline 死区律实证 (b049 C004 + b056 C001 + 本批)**. | [[batches/batch_063/candidates/C004]] |
| C005 | ❌ reject | hard_gate | mono=**-0.90/+1.00 FLIP** ic_oos=0.0064 ic_is=0.0073 | hard_gate mono_sign_flip — Std(upper_shadow_ratio,20) × pe_20 跨样本 **完全 reversal** (-0.90 → +1.00, 双侧 |·|≥0.5 hard_gate trigger). lower_shadow ≡ -upper_shadow algebraic mirror → C005 等价 Std(lower_shadow,20). **higher-moment LHS in OHLC 三段 ratio 跨样本 mono reversal 模式与 b062 C006 同律** (Std normalized |gap|): second_moment of bounded ratio 在 small sample 极端值频率不稳定. F006 upper_shadow Mean 5d 已 admit; F021 upper_shadow Std × range 已 admit; 本候选 Std × pe 跨字段也失败 → upper_shadow 维度全 moment + 多 RHS saturated. | [[batches/batch_063/candidates/C005]] |
| C006 | ❌ reject | 🟡·🔴·🔴·🟡 | ic_oos=0.031 ls_t=3.24 mono=1.0/0.95 alpha_surv=**0.0905** incr_ic=+0.0056 max_corr=0.6288@F012 vol_20d=8.30 | T012 Std(\|gap\|/range,20) × amount_60. **alpha_surv=0.0905 critical extreme (整库罕见, 仅次 b052 C006 / b062 C006)** + barra_residual_ic=0.003 (91% alpha 来自 Barra style) + str_1m=0.88 极强 + 死区双重不达 (max_corr=0.63 borderline + incr_ic=0.006<0.015). **higher-moment LHS atom-orthogonality 三件套违反第二+第三件**: range denom = realized vol proxy (b 不正交) + range 自身跨 regime drift (c normalizer 引 drift). **ratio-of-magnitudes higher-moment 跨样本失败 (b062 C006 同律复现)**: \|gap\|/range double-magnitude ratio Std 必然 alpha_surv 崩塌. **C006 vs F020 关键对比**: F020=Std(gap_ret,20) sign-preserved + price-normalized by Ref(close,1) → 兑现; C006=Std(\|gap\|/range,20) sign-stripped + range-normalized → 失败 → **OHLC Std 兑现两件必要条件: sign 保留 + price (非 range) normalizer**. | [[batches/batch_063/candidates/C006]] |

**档位编码**: 🟢 最优档 · 🟡 次档 · 🟠 边际 · 🔴 阻断档 · `hard_gate` reject 不填色.

## 跨候选对比

- **T012 higher-moment OHLC × non-vol-cluster RHS 第二轮 — 部分 disproven + 三件套精细化**: T012 active 时探问 "Std/Skew/Kurt of OHLC ratios 是否构成与 Mean-based 库因子独立的轴". F019 (b050) 兑现给出"higher-moment LHS independence axis"假设. 本批 6 candidate 全 reject 揭示 atom-orthogonality 兑现条件比 F019/F020 时识别的 "scale-free + ≤20d + 单层 moment" 更严格. **新升格三件套 (P003 atom-orthogonality)**: (a) atom multi-regime stable, (b) **atom 自身与 vol_20d 几何正交** (range/prev_close 与 (C-O)/prev_close 不满足 — 自身就是 vol proxy), (c) normalizer 无 regime drift. F019 body_ratio (intraday H-L denom 短期稳) + F020 gap_ret (Ref(close,1) normalize) 满足三件; 本批 C002/C003 (range/prev_close + signed return) 违反 (b); C006 (|gap|/range) 违反 (b)+(c); C001 (close_position) 违反 (... OHLC mirror).

- **OHLC algebraic mirror trap higher-moment 形态首次实证 (升格证据 1)**: C001 close_position=(C-L)/(H-L) 与 F021 upper_shadow=(H-C)/(H-L) 是 algebraic mirror (互补和=1). Std-of-each cross-section rank cluster=0.79 → **OHLC algebraic mirror trap 在 Std 形态成立**. 之前 mirror trap 仅在 Mean 形态 (b018 C001 lower_shadow Mean ≡ F006 upper_shadow Mean corr=1.000). **升格律**: lessons.md OHLC Family Defaults 段 "OHLC 派生 candidate 起手前必做 3 步 algebraic 检查" 新增第四件 — **Std/Var/Skew/Kurt of mirror-pair ratios 也 cluster** (Std 二阶矩对 algebraic mirror 不变, 三段 ratio 三对镜像 (C-L/H-L vs H-C/H-L) (O-L/H-L vs H-O/H-L) (C-O/H-L vs O-C/H-L) higher-moment 全 cluster).

- **vol_20d structural absorption 整库新纪录连刷 (升格证据 2)**: 本批 C003 style_r²=0.6991 + vol_20d=76.53 双双整库新纪录, 超 b057 C003 (style_r²=0.66 + vol_20d=48.04) 前纪录. **P003 vol_20d 边界**律持续 escalate: signed price-normalized return Std (C-O)/prev_close 比 range/prev_close 更直接是 realized vol. **跨方向 9-direction-confirmed law 第 10 次确认 (ohlc_temporal_aggregation 方向首次直接命中 vol_20d 极端吸收)** — 此前 ohlc_temporal_aggregation 因 F019/F020 兑现被认为相对 vol_20d 安全, 本批揭示**安全例外仅适用于 sign-preserved + price-normalized + 单层 moment**, OHLC 高阶 ratio Std 大量 form 仍落 vol_20d 几何.

- **rank-diff borderline 死区律第三次实证 (升格证据 3, 阈值已 codify)**: C004 max_corr=0.6873@F012 + incr_ic=0.0062 < 0.015 → reject. 与 b049 C004 (max_corr=0.725, incr=0.004 reject) + b056 C001/C004 retroactive 同律. **死区律已被 lessons.md Rank-Diff Geometry 段显式 codify** (config 已 set rank_diff alpha_surv_min=0.30 + max_corr ∈ [0.30, 0.70] borderline 时 incr_ic ≥ 0.015 双重 gate). 本批是该律执行后的第一个无争议命中 — 死区律执行清晰, 无系统性错杀风险.

- **library-reducer + 死区双律联合阻断本批最强 stat profile (升格证据 4)**: C004 是本批 ls_t=4.89 ls_sharpe=3.52 ls_calmar=3.77 9/9 yr 全正 ic_by_horizon 1d→20d 强 cumulative — **绝对 stat profile 整批最强**. 但 incr_ic=0.0062 死区不达 + 6 lib factor cluster center → reject. 与 b062 C005 (ls_t=4.52 ls_sharpe=3.26 9/9 yr 但 incr_ic=-0.002 NEG library reducer) 同律 → **强 stat ≠ tradable independence 律**重申: alpha quality 残量与 library marginal contribution 是两个独立 dim, 单维度强不充分.

- **Style 聚合**: 6/6 候选 dominant_style_exposure=`vol_20d` (5/6) 或 turnover_20d (C001=7.83). vol_20d 范围 5.96-76.53, 中位数 12 (C006=8.30). 本批 alpha_survival ∈ [0.09, 0.45], 中位数 ~0.32 — 与 b061/b062 microstructure/gap_acceptance 中位数 0.36/0.26 同等量级. **跨方向 alpha quality 持续滑落**: rank-diff geometry candidates 在 csi1000 daily-bar 当前 admitted 23 factor 库容下结构性饱和. P004 vol_20d 吸收覆盖 9+ direction → 第 10 个 direction 实证 (本批 ohlc_temporal_aggregation 直接命中).

## Thread 进展

> [!note]+ T012 [[directions/ohlc_temporal_aggregation#T012]] — `[◉ ACTIVE]` (维持但范围收窄)
> **higher-moment OHLC × non-vol-cluster RHS 第二轮 — 6/6 reject 揭示 atom-orthogonality 三件套精细化**:
> 1. **C001 close_position Std × turnover_60**: OHLC algebraic mirror trap higher-moment 形态 (corr=0.79@F021)
> 2. **C002 range/prev_close Std × pe_60**: vol_20d=53.04 极端 (range = realized vol proxy)
> 3. **C003 (C-O)/prev_close Std × pb_60**: vol_20d=76.53 整库新纪录 (signed return 直接 vol proxy) + ls_t weak
> 4. **C004 open_position Std × amount_60**: rank-diff 死区律 (max_corr=0.69 + incr_ic=0.006 < 0.015)
> 5. **C005 upper_shadow Std × pe_20**: hard_gate mono_sign_flip (-0.90 → +1.00)
> 6. **C006 |gap|/range Std × amount_60**: alpha_surv=0.09 critical (range denom + ratio-of-magnitudes regime drift)
>
> **Answer (部分)**: F019/F020 兑现的 higher-moment LHS independence axis **不能简单泛化到任意 OHLC ratio Std**. 兑现条件精细化为: (a) atom multi-regime stable; (b) **atom 与 vol_20d 几何正交** (排除 range/prev_close, signed return/prev_close 等 vol-direct-proxy 原子); (c) normalizer 无 regime drift; (d) sign 信息保留优于 sign-stripped (b062 C006 + 本批 C006 ratio-of-magnitudes 失败); (e) price normalizer (Ref(close,1)) 优于 range normalizer (H-L 跨 regime drift); (f) **避开 OHLC algebraic mirror pair atom** (close_position vs upper_shadow Std 同 cluster).
>
> **Next probes (剩余探索路径)**: F019 body_ratio + F020 gap_ret 是当前唯二兑现 atom; F008 upper_shadow 3d phase 可能仍有 Skew/Kurt 维度未测但需先核 F021 cluster. 主要剩 (1) **Skew (3rd moment, 不是 Std) of body_ratio / gap_ret 不同 RHS** 是否有差异化几何; (2) **F019 / F020 atom 的 signed Skew (跨 regime 偏度变化)** 是否 reveal 不同信号. 注意: 三阶矩对极端值更敏感, 需先核 b052 C006 compound moment IS over-fit 律不命中 (Skew 是单层不嵌套). 但 T012 范围已实质收窄至 "F019/F020 atom + Skew" 两 candidate 空间, **direction MT 34/70 approaching exhaustion**, 下批应切方向.

## 方向级反思

本方向第 8 批, 5 admit (F006/F007/F008/F019 OHLC ratio 单 anchor + 跨方向 retroactive). 本批 zero admit, **direction.score 0.89 (search_adjusted 0.49 → medium)**, MT bucket 持续 high (direction 34/70). **alpha_surv 中位数 0.32** (本批 0.09/0.31/0.32/0.39/0.45 vs b050 admit 时 0.16-0.40 + b052 fundamental 中位数 0.30) — ohlc_temporal_aggregation 方向 alpha quality 已收敛至 saturated zone.

**T012 partial disproven + atom-orthogonality 三件套精细化**: T012 active 但范围实质收窄. F019/F020 的 OHLC higher-moment 兑现路径不能简单泛化至任意 OHLC ratio Std — 必须严格满足 (a)-(f) 六件. 剩余 candidate 空间: F019/F020 atom Skew 形态 + 不同 RHS 组合, 估 ≤2-3 candidate.

**direction status 评估**: T012 partial disproven + 本批 zero admit + alpha quality 进一步 saturated → **建议 status 维持 productive (T012 仍 ACTIVE 但范围窄)**, priority medium → low (剩余空间稀薄, 优先级让位给其他 productive direction). 待 Phase 5 consolidation 升格 atom-orthogonality 三件套 + OHLC mirror higher-moment 律后再评估是否切 saturated.

**zero_admit_streak 3 → 4**: 全系统连续 4 批 zero admit (b060 overnight + b061 microstructure + b062 gap_acceptance + b063 ohlc_temporal_aggregation). **calibration trigger 检查**:
1. ❌ judge.md 跨候选反思未含 "potential over-rejection" — **本批所有 reject 理由结构性强 (CP04/CP05 阈值 + library reducer + vol_20d 极端) + 1 个 hard_gate, 无错杀嫌疑**
2. ⚠️ 4 批 zero admit 满足 ≥3 → 累计 reserve **本批 0**, 系统累计 (b060 reserve=1: C001 max_corr=0.20 ✓ incr_ic=0.012 ✓ 满足独立性; b061-063 全 reserve=0) → **仍仅 1 个独立 reserve, 不满足 calibration trigger 条件 #2 ≥1 的稳健最小值 (单 sample 不构成系统性错杀证据)**
3. ❌ 累计 reserve/judged ratio: 1/24=4.2% << 40% 阈值
4. ❌ 悖论复现 ≥2: 本批 2 个反直觉指标组合 (低 alpha_surv + 高 ls_t profile) 但 b062 C005 同律已记录, 这是 P006 library-reducer 律已识别的常态非 paradox

**calibration_trigger=false** (维持 b062 判定): 4 批 zero admit + 1 reserve 仍临界. 但 **建议 orchestrator 认真考虑触发 calibration**: zero_admit_streak=4 已超 ≥3 阈值, 仅 reserve 独立性件不达 ≥2 是稳健下限. **特殊建议**: 若下批仍 zero admit 则应**强制触发 calibration** (zero_admit_streak=5 + 0 跨方向 admit, 已无系统性错杀单 sample 防御理由).

**升格 lessons 候选** (本批共贡献 4 条, 待 Phase 5 consolidation 升格):
1. **higher-moment LHS atom-orthogonality 三件套精细化** (P003 升格证据): 兑现需 atom multi-regime stable + atom 与 vol_20d 几何正交 + normalizer 无 regime drift + sign 保留 + price normalizer + 避 OHLC mirror — 六件
2. **OHLC algebraic mirror trap higher-moment 形态首次实证**: lessons OHLC Family Defaults 段 algebraic 检查新增第四件 — Std/Var/Skew/Kurt of mirror-pair ratios cluster
3. **vol_20d structural absorption 第 10 方向直接命中 + 整库新纪录连刷 76.53/53.04**: P003 vol_20d 边界律持续 escalate; ohlc_temporal_aggregation 方向 "OHLC ratio Std 安全" 假设崩塌, 修正为 "sign-preserved + price-normalized + 单层 moment + 非 vol-direct-proxy atom" 严格条件
4. **rank-diff borderline 死区律 + library reducer 双律重申阻断 stat-strongest 候选**: alpha quality ≠ tradable independence; ls_t=4.89 + 9/9 yr 全正 这种"绝对最强 stat" 仍被 incr_ic=0.006 < 0.015 阻断 — 单维度 cleanness 不充分律 cross-batch 第 N 次实证

**consolidation 信号**: rounds_since_last_consolidation=3 → 仍 < 10 阈值, 不触发. 但 zero_admit_streak=4 + lessons 升格候选 4 条本批 + 4 条 b062 + 3 条 b061 = **累计 11 条升格候选** + ohlc_temporal_aggregation priority medium→low + alpha quality 持续滑落 → **distance to consolidation 缩短 (rounds 3/10) 但升格量已多**.

**next_hint**: 切方向. 候选: (1) **触发 calibration_trigger** (zero_admit_streak=4, 单 reserve 独立性 临界, orchestrator 决定); (2) 若跳过 calibration, 选剩余 productive direction — 但 active_directions=13 中扣除 avoid 3 个 + 已 saturated 8 个 + 本方向 saturated zone 后, 仅剩 ohlc_temporal_aggregation T012 残余 (Skew 探索, 1-2 candidate) 或新建 direction; (3) 触发 Phase 5 consolidation (升格量已 11 条, 升格紧迫性高于 rounds 阈值).