---
direction_tag: price_conditional_amplitude
status: dead
priority: medium
rounds: 2
admits: 0
last_batch: batch_090
last_admits: []
last_goal: 'Round 90 — price_conditional_amplitude first batch (paper kysec_amp_2020_ideal_amplitude

  本地化 csi1000 daily). H1: V_high(0.25) − V_low(0.25) (按 close 在 N 日窗内 rank top/bottom

  25% 子集分别求振幅均值, 取差) 在 csi1000 daily 携带独立 NEG cross-section alpha — paper

  在 csi500 月频报 IC=−0.051 / ICIR=−2.39 / 多空年化 17%, 期望频率衰减 ×0.5 → daily IC ≈ −0.025.

  H2: rank-conditional aggregation (MaskedMean(numerator, condition_on_rank_field))
  是当前库 28

  admit 全部缺失的工艺空间 — F001 second-moment vol/F015 cross-section rank-diff/F024-F026
  P008

  TsRank 三族都不含"在时序窗口内按字段排序后取子集均值". 本批 6 候选覆盖三条核心 thread:

  (a) T001 paper-original Python wrapper 经 daily_python quantile_split_spread 模板执行

  (N=20 + N=60 两个时间尺度对照, λ=0.25 paper hard-切割);

  (b) T002 DSL-soft baseline Mul((H/L−1), (2·TsRank(close,20)−1)) — rank-weighted
  连续替代

  paper hard-mask 切割, 100% DSL 可达, 作 algorithmic 下界证明;

  (c) T002 N=60 DSL-soft (TsRank(close,60) replacement) — P008-aligned 时间尺度;

  (d) T005 P008 完整三条件复合 — 把 (b) 输出再 TsRank-60d 包一层, 同时具备 dim-less ratio +

  microstructure-only-on-amp + TsRank≥60d, 是当前库唯一已验证 vol_20d-escape 路径 (F024-F026
  prototype);

  (e) T003 RHS 替换 — numerator = $turnover_rate (替换 amp), 同样 quantile_split_spread
  N=20

  λ=0.25, 测"高价段成交激烈 vs 低价段成交激烈差值"是否携带独立 alpha (注意: turnover-family 已

  P005 锁死 F017 anchor cluster, 但 quantile-split 工艺与 turnover_rank_diff 几何不同).

  关键 hypothesis check: H1 真度 — 期望 ≥1 候选 |IC|≥0.015 + ICIR≥0.20 + max_corr<0.30 (vs
  F001

  amount_cv NEG, F025 shadow_asymmetry_tsrank_60, F008 upper_shadow_persistence_3d
  三个振幅族近邻);

  H2 工艺空间 — 即使 H1 不立, 若 ≥1 候选 alpha_surv≥0.40 + max_corr<0.50 → 工艺空间确认 reserve

  火种, 后续 T003 family 拓展; H3 paper transferability — 若全 6 候选 |IC|<0.005 → paper 跨频率/

  跨 universe transferability 信号衰减系数 < 0.1, 升格 lessons.md.

  Risk constraints: (1) 无 cap-denominator (P016 OK); (2) 无 cross-product Mul 跨字段塌缩

  (b074 dead 律) — DSL-soft Mul 是 same-row scaling 不是跨 atom-class 乘积; (3) vol_20d

  风险: H/L−1 是 dim-less ratio 不直接嵌 vol_20d basis, V_high−V_low 差值形态进一步剥离公共 vol;

  (4) candidate F001 amount_cv NEG 量级 cluster 必查 max_corr; (5) Barra residualization
  N-day

  cumulative form path-memory β-shift (b089 教训): 本批所有候选都不做 Sum/Mean/Cumulative

  residualized signal (T001/T003 是 conditional Mean 但不在 Barra residual 上聚合, 几何不同).

  Hard targets: ≥1 admit alpha_surv≥0.40 + max_corr<0.30 (库 redundancy 严控,

  振幅族 F001/F008/F025 cluster 严防) + incr_ic ≥ 0.010 + ls_t_oos ≥ 2 + sign_consistency=1.0.

  Fail (6/6 reject) → 升格 lesson "rank-conditional aggregation 工艺在 csi1000 daily NEG
  signal

  整体衰减", direction → dead, paper transferability 失败案例归档.

  Baseline-first 例外: 15 个 untouched 字段全为 TTM fundamental, 与本 direction (price/amp/turnover

  microstructure) 完全不相关 — 刻意 skip baseline-first.'
last_activity: '2026-05-15T19:31:10Z'
created_batch: batch_089
members: []
merged_into: null
---
# price_conditional_amplitude

> [!abstract]+ 方向概要
> - **状态**　🔴 `dead` · priority `medium` · rounds = 1 · admits = 0
> - **种子**　seeded from [[papers/kysec_amp_2020_ideal_amplitude|开源证券 2020 — 振幅因子的隐藏结构 / 理想振幅因子]]
> - **一句话**　把振幅 `($high/$low − 1)` 按收盘价在 20d 窗口的 rank 切成"高价段振幅 V_high"与"低价段振幅 V_low"，差值 V_high − V_low 测顶部博弈 - 底部企稳的 NEG signal
> - **dead 结论**　batch_090 6/6 候选全 reject；rank-conditional aggregation 工艺整体被 vol_20d (Barra 残差吞噬 63-75%) + 库内 F001/F017/F027 cluster 共同覆盖；incremental_ic 5/6 显著负

---

## Hypothesis

> [!note]+ Hypothesis · 价格条件切割振幅（开源证券 2020 在 csi1000 daily 上的本地化）

**核心假设（H1）**：日度振幅 `(H/L − 1)` 在 20d 窗口的**收盘价 rank-conditional 子集均值**携带独立 NEG cross-section alpha——具体而言 `V_high(0.25) − V_low(0.25)` 度量「股票在自己历史价格高位时的博弈剧烈度 减去 历史价格低位时的博弈剧烈度」，**正值越大 → 顶部分歧 → 未来收益越低**。

paper 在 csi500 月频报 IC=-0.051 / ICIR=-2.39 / 多空年化 17%。本地化要求：

1. **频率衰减**：月频聚合 → 日频 cross-section，IC 量级期望衰减系数 ≈ 0.5 → 期望 IC ≈ -0.025
2. **universe 切换**：csi500 → csi1000，small-cap 振幅扰动更大但 mean-reversion 更强，方向应保留 NEG，量级未必衰减
3. **vol_20d 风险**：振幅本身 = `H/L − 1` 是 dim-less ratio，**不直接** 嵌入 vol_20d basis（与 F001 amount_cv 的 second-moment 形式正交）；理论上 V_high - V_low 的"差值"形态进一步剥离公共 vol 成分
4. **库 redundancy 风险**：candidate F001（amount_cv NEG ICIR=-0.74）& F025（shadow_asymmetry_tsrank_60）都涉及"振幅类"，max_corr 必查

**核心假设（H2）**：「rank-conditional aggregation」工艺本身（无论 amp 还是其它 numerator）是当前库 27 admit 全部缺失的新几何空间，该方向的真正价值是**首次穿透 MaskedMean(numerator, condition_on_rank_field) 算子家族**——即使 H1 不立，工艺空间也值得展开测序。

---

## Threads

> [!failure]+ **Round 91 consolidation outcome — 全方向 dead, 元教训升格 P004-deep**
> b090 6/6 reject + T001/T002/T003/T005 4 条主线全证伪. rank-conditional aggregation 工艺 (按 close-rank quantile 切分聚合 amp/turnover numerator) 在 csi1000 daily 上**整体被 vol_20d cluster 覆盖** (4 路径 paper-original / DSL-soft / P008-stack / RHS-swap 一致失败, 残差吞噬 63-75%, 6/6 dom=vol_20d). 与 signed_money_flow_oscillator + idiosyncratic_momentum_residual 共享同一 **P004-deep 律** (path-integral / N-day 累积形式失败), round 91 升格至 `lessons.md#vol_20d 结构性吸收律` 段. **本方向无残余探索价值, 建议下次 consolidation dead → archived**. 元教训详见 [[_consolidation/findings/pattern_analyst/028]] + [[_consolidation/findings/hypothesis_promoter/020]] + [[lessons#vol_20d 结构性吸收律]].

### T001 — 原始 V_high(0.25) − V_low(0.25) Python wrapper [✗ DISPROVEN batch_090]

> [!failure]+ Thread 结论
> **Question**: paper-original V_high(λ=0.25) − V_low(λ=0.25) 在 csi1000 daily 是否携带独立 NEG cross-section alpha？
>
> **Evidence trail**:
> - [[batches/batch_090/candidates/C001|batch_090 C001]]　N=20 paper-original: IC_oos=-0.053 mono_oos=-1.0 ls_t=-6.04 alpha_surv=0.34 incr_ic=-0.011 → **reject**
> - [[batches/batch_090/candidates/C002|batch_090 C002]]　N=60 P008-aligned: IC_oos=-0.040 mono_oos=-1.0 alpha_surv=0.25 incr_ic=-0.012 → **reject**
>
> **结论**: raw 信号 sign-aligned 且 mono 完美，但 Barra vol_20d 吞噬 66-75%，alpha_surv 0.25-0.34 远低方向阈 0.40，incremental_ic 5/6 显著负 → 加入库后**反向降低组合 alpha**。决断点 0/3 全 fail (`incr_ic>0`/`max_corr<0.30`/`style_R²(vol_20d)≤0.20`)。T001 paper transferability 彻底否定。

### T002 — DSL 软逼近 baseline [✗ DISPROVEN batch_090]

> [!failure]+ Thread 结论
> **Question**: rank-weighted DSL-soft `Mul((H/L-1), 2·TsRank($close,N)-1)` 是否能作为 paper 工艺的 100% DSL 替代实现？
>
> **Evidence trail**:
> - [[batches/batch_090/candidates/C003|batch_090 C003]]　DSL-soft N=20: IC_oos=-0.043 ls_t=-4.23 mono=-0.60 max_corr=**0.86@F027** incr_ic=-0.013 → **reject (high redundancy with reversal cluster)**
> - [[batches/batch_090/candidates/C004|batch_090 C004]]　DSL-soft N=60: IC_oos=-0.041 mono=-0.30 alpha_surv=0.27 incr_ic=-0.004 → **reject**
>
> **结论**: 数值上达成"|IC|≥0.015"决断点，但 max_corr=0.63-0.86 表明 DSL-soft 本质是 F027 close/MA 反转 cluster 的几何变形。`Mul((H/L-1), 2·TsRank($close,N)-1)` 在 cross-section 等价于"价格相对 MA 高出多少"反转信号，**工艺不创造独立信号家族**。N=20 mono=-0.60 + N=60 mono=-0.30 一致提示 Q5 一桨驱动。

### T003 — RHS 替换（amp → 其它 numerator） [✗ DISPROVEN batch_090]

> [!failure]+ Thread 结论
> **Question**: 把 numerator 从振幅换成其它（turnover_rate / return / body_ratio）是否能让 rank-conditional aggregation 工艺产生独立信号？
>
> **Evidence trail**:
> - [[batches/batch_090/candidates/C006|batch_090 C006]]　numerator=$turnover_rate, N=20: IC_oos=-0.051 mono=-0.90 ls_t=-3.64 alpha_surv=0.38 incr_ic=-0.010 → **reject**
>
> **结论**: 即使原计划"T001 admit 后才推进 T003"被打破，提前验证 turnover RHS-swap 也卡在 alpha_surv=0.38（方向阈 0.40 下方）+ incremental_ic=-0.010 负值 + vol_20d=29× / turnover_20d=9.45 双重风格主导。**工艺本身（按 close-rank 切割聚合）不创造独立性** — 无论 numerator 是 amp(C001) 还是 turnover(C006)，alpha_surv 都在 0.25-0.38 区间 + incr_ic 都负。其余 numerator 选项 (return / body_ratio) 不再值得测试。

### T004 — Cross-section rank-diff 嵌套 [✗ DISPROVEN batch_090]

> [!failure]+ Thread 结论
> **Question**: 当 T001 信号被 F001 cluster 部分吞噬时，rank-diff 嵌套形式 `Sub(CsRank(T001), CsRank(F009))` 能否救援 incr_ic 转正？
>
> **Evidence trail**:
> - 触发条件未达成（T001 直接 reject 而非 reserve）；本批未冻结 T004 候选
>
> **结论**: T001/T002/T003 三条主线全 disproven，T004 救援路径无意义——若 raw 工艺信号完全被 vol_20d 吞噬 + 库内反转/turnover cluster 共同覆盖，rank-diff 嵌套不会改变本质几何。T004 随方向 dead 一并关闭。

### T005 — TsRank-60d 包装（P008 完整三条件复合） [✗ DISPROVEN batch_090]

> [!failure]+ Thread 结论
> **Question**: P008 完整 escape stack 三条件（dim-less ratio × micro-only × TsRank≥60d）叠加 rank-conditional aggregation 能否构成 vol_20d-escape？
>
> **Evidence trail**:
> - [[batches/batch_090/candidates/C005|batch_090 C005]]　TsRank-60 wrap of (amp × rank-60): IC_oos=-0.027 ICIR=-0.21 ls_t=-2.47 alpha_surv=0.29 incr_ic=+0.003 → **reject**
>
> **结论**: TsRank 包装让 IC 从 C004 的 -0.041 衰减到 -0.027（**60% loss**），ICIR 落到 weak 档 0.21；vol_20d 暴露反而从 8.84 升到 10.77。P008 律 ≥60d 在该方向**不构成 vol_20d-escape**——TsRank 包装把 alpha 稀释而非 crowding 剥离。需在 [[lessons]] 记录"P008 不适用 rank-conditional aggregation 方向"。

## Known Failures

- C001 `quantile_split_spread(amp, sort=$close, w=20, λ=0.25)` — alpha_surv=0.34 < 0.40 + incr_ic=-0.011 + vol_20d 暴露 35×
- C002 `quantile_split_spread(amp, sort=$close, w=60, λ=0.25)` — alpha_surv=0.25 远低阈 + incr_ic=-0.012
- C003 `Mul((H/L-1), 2·TsRank($close,20)-1)` — max_corr=0.86@F027 (与反转 cluster 同源) + incr_ic=-0.013
- C004 `Mul((H/L-1), 2·TsRank($close,60)-1)` — alpha_surv=0.27 + mono=-0.30 (Q5 一桨驱动) + incr_ic=-0.004
- C005 `TsRank(Mul((H/L-1), 2·TsRank($close,60)-1), 60)` — ICIR=-0.21 weak + alpha_surv=0.29 + P008 包装稀释 alpha
- C006 `quantile_split_spread($turnover_rate, sort=$close, w=20, λ=0.25)` — alpha_surv=0.38 (阈下) + incr_ic=-0.010

---

## Narrative Log

### 2026-05-04 · 方向种子（rounds=0）

paper intake 完成 (`papers/kysec_amp_2020_ideal_amplitude.md`)。Hypothesis 二条：
- H1：V_high − V_low 在 csi1000 daily 携带 NEG cross-section alpha (期望 IC≈-0.025)
- H2：rank-conditional aggregation 是库未覆盖的工艺空间，首次穿透 `MaskedMean(num, cond_on_rank)` 算子家族

**下一步**: 下批 /factor-batch 时，主 agent 应把 T001 + T002 作为 2 candidate 冻结（Python wrapper + DSL 软逼近对照），T005 作为第 3 candidate（P008 完整三条件复合）。N=20 paper-original 与 N=60 P008-aligned 形成正交对照。

**避坑**：
- max_corr 必查 F001 (amount_cv NEG) / F025 (shadow_asymmetry_tsrank) / F008 (upper_shadow_persistence) — 振幅族近邻
- 若 N=20 raw IC 强于 N=60 → P008 律需限定边界（rank-conditional aggregation 可能放宽 ≥60d 硬约束至 ≥20d）
- 若 N=20 / N=60 都弱 → 退回 T002 DSL-soft 看 paper transferability 是否系统失败

### 2026-05-16 [[batches/batch_090/judge|batch_090]] · 方向证伪（rounds=1, admits=0）

admit=0 / reserve=0 / **reject=6** — 6/6 候选全 reject，方向 `exploring → dead`。

**核心发现**：
1. rank-conditional aggregation 工艺**整体被 vol_20d 重度吞噬**：6/6 候选 dominant_style=vol_20d，Barra 残差吞噬 63-75%，无候选实现 alpha_survival ≥ 0.40
2. 库覆盖完备：F001 amount_cv + F017 turnover_rank_diff + F027 close/MA 反转 + F025 shadow_asymmetry 共同覆盖本方向所有几何形态；6 候选 incremental_ic = [-0.013, -0.012, -0.011, -0.010, -0.004, +0.003]，5/6 显著负
3. P008 律 ≥60d **不适用** rank-conditional aggregation 方向：TsRank 包装让 alpha 衰减 60% 而非 crowding 剥离 (C005 vs C004)

**Thread 进展**：
- T001: paper-original V_high−V_low [✗ DISPROVEN]
- T002: DSL-soft 等价 F027 反转 cluster [✗ DISPROVEN]
- T003: turnover RHS-swap 同样卡在 alpha_surv 阈下 [✗ DISPROVEN]
- T004: 救援路径无意义（T001 直接 reject 不触发）[✗ DISPROVEN]
- T005: P008 stack 不构成 vol_20d-escape [✗ DISPROVEN]

**升格 lessons 候选**（待 /factor-consolidate 处理）：
- "rank-conditional aggregation 工艺（按 close-rank 切割聚合 amp/turnover）在 csi1000 daily 上整体被 vol_20d cluster 覆盖；signal 本质是'价格相对位置'的二次衍生，与库内 close/MA 反转 cluster 共享几何空间"
- "P008 escape stack (dim-less × micro-only × TsRank≥60d) 不普适——对 rank-conditional aggregation 方向，TsRank 包装稀释 alpha 而非剥离 crowding"

**下一步**：方向 dead，不再产生新 batch；orchestrator 应在下轮换新 direction。本方向 [[papers/kysec_amp_2020_ideal_amplitude]] paper transferability 三件套 NEG 信号衰减完整验证。
