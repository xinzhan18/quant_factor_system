---
direction_tag: overnight_intraday_split
status: productive
priority: high
rounds: 7
admits: 7
last_batch: batch_049
last_admits:
- F018
last_goal: 'T008 rank-diff 第四波兑现——测 rank-diff 范式跨 direction LHS 多元化泛化边界。

  batch_048 C003 admit F017 (overnight_5 × turnover_5 rank-diff) 成为 rank-diff 范式跨家族

  第 3 次兑现；若本批再有 1 admit = 第 4 次兑现可触发 Phase 5 consolidation 升格 lessons.md。

  cockpit 硬约束"每个候选 LHS 必须不同"——本批 6 候选 LHS 全部唯一且各来自独立 signal family：

  (C001) Mean|ret|(Amihud-style illiquidity w/o $amount) × overnight——LHS=Mean(Abs(daily_ret),20)，

  RHS=overnight_5；(C002) pb × overnight——LHS=Mean($pb_ratio,20)；

  (C003) turnover_cv × |intraday|——C006-rerun 非 overnight LHS，LHS=Std($turnover,20)/Mean($turnover,20)，

  RHS=|intraday|_5；(C004) volume HHI × overnight——LHS=Sum((volume/Sum(volume,20))²,20)
  自算 HHI 纯 DSL；

  (C005) L2 RealizedVol × overnight——LHS=Power(Sum(Power(daily_ret,2),20),0.5)，RHS=overnight_5；

  (C006) overnight_sign_freq × amount——LHS=Mean(Sign(overnight),20) 首探 direction.md
  复活条件 "overnight sign frequency"，

  RHS=amount_20。避开死模式：LHS 全唯一；不用 ratio；不 CsRank 外包已入库 raw-diff；

  不共享 raw numerator/denominator；无同字段跨窗口差。

  技术注释：所有 CsRank 内层使用**标准 qlib DSL 算子** (Mean/Abs/Sum/Power/Sign/Div/Sub/Ref)，

  避免 custom op (AmihudIlliq/HHI/RealizedVol) 的 __str__ 类名悬挂导致 CsRank 重建 cross-sectional

  cache 时找不到算子的 latent bug (见 operators.py:428 _build_cs_cache 调用 D.features 重新 parse)。

  目标 ≥1 candidate 满足 max_corr@lib<0.70 + alpha_surv>0.40 + ls_t>2 + incremental_ic>0.010。'
last_activity: '2026-04-24T21:27:21Z'
created_batch: batch_025
members:
- F009
- F010
- F011
- F017
- F{next}
- F018
retired_members: []
merged_into: null
---
# overnight_intraday_split

> [!abstract]+ 方向概要
> 🟢 **productive** · 6 rounds · 5 admits — batch_048 admit F17 (overnight × turnover rank-diff) 复活方向 + batch_049 admit C006 (sign_freq × amount rank-diff) 命中 direction.md hypothesis 文字级复活条件 "overnight sign frequency"，rank-diff 范式第 4 次跨家族兑现 tipping point 达到。
> **Members**: [[F009]] overnight_intraday_spread_5d · [[F010]] overnight_return_persistence_5d · [[F011]] overnight_return_persistence_3d · [[F017]] overnight_turnover_rank_diff_5 · overnight_sign_freq_amount_rank_diff_20 (F{id} 待 Phase 4 分配)

---

## Hypothesis

> [!success]+ 已验证（partial）
> 分解 daily return 为 **overnight** ((open-prev_close)/prev_close) 与 **intraday** ((close-open)/open) 两段，驱动因子不同：overnight = 隔夜消息 + 机构 pre-market；intraday = 日内散户 + 算法。**Aggregation 形式（spread / persistence）在 cross-section 上携带独立 alpha**——batch_025 DOUBLE ADMIT 打破整库 ls_t 记录（F010 ls_t=7.50）。
>
> **已封闭**：correlation 形式不稳（sign_flip）；pure intraday 镜像冗余（F009 = overnight - intraday 已隐式吸收 intraday 分量）。
>
> **复活条件**：
> - **新字段**：minute-bar session 分解（open auction / midday / close auction）突破 daily 二分
> - **更长 horizon**：20d+ overnight persistence 是否仍独立于 5d 版本
> - **正交 aggregation**：overnight sign frequency（方向而非 magnitude）、overnight × intraday 非线性交互

---

## Threads

### T001 · overnight aggregation (spread + persistence) [✓ ANSWERED batch_025]

> [!success]+ 机制确认：overnight 段独立 alpha 已吸收
> **Question**: overnight return 与 intraday return 的 spread / 各自 aggregation 是否携带独立于现有 OHLCV 的 persistent alpha？
> **Answer**: 是。overnight 段在 cross-section 上独立于 intraday；spread 与 pure overnight persistence 两种 aggregation 均有效。
> **Evidence trail**:
> - [[batches/batch_025/candidates/C001|batch_025 C001]]: spread 5d → ic=+0.047 ls_t=5.18 mono=+1.00 incr=+0.044 corr=0.708@F007 → **admit → [[F009]]**
> - [[batches/batch_025/candidates/C002|batch_025 C002]]: 5d overnight persistence → ic=+0.024 **ls_t=7.50（整库记录）** mono=+1.00 incr=+0.019 corr=0.424@F003 → **admit → [[F010]]**

---

### T002 · overnight-intraday correlation [✗ DISPROVEN batch_025]

> [!failure]+ 机制封闭：correlation 形式不稳定
> **Question**: 20d Corr(overnight, intraday) 是否在 cross-section 上提供稳健预测力？
> **Answer**: 否。correlation 形式 sign_flip，无 cross-section 稳定性。
> **Evidence trail**:
> - [[batches/batch_025/candidates/C003|batch_025 C003]]: 20d Corr → hard_gate sign_flip train +0.005 / val -0.006 → **reject**

---

### T003 · intraday 镜像 aggregation [✗ DISPROVEN batch_027]

> [!failure]+ 机制封闭：F009 已吸收 intraday 分量
> **Question**: intraday return 5d/3d mean（镜像 F010/F011 的 overnight aggregation）是否携带独立于 F009 spread 的 alpha？
> **Answer**: 否。F009 = overnight - intraday 的数学结构已吸收 intraday 分量——pure intraday 是 (overnight - F009) 的线性组合，无独立信息。3/3 reject。
> **Evidence trail**:
> - [[batches/batch_027/candidates/C001|batch_027 C001]]: 5d intraday mean → corr 0.65-0.89@F009 + incr_ic 负 → **reject**
> - [[batches/batch_027/candidates/C002|batch_027 C002]]: 3d intraday mean → corr 0.65-0.89@F009 + incr_ic 负 → **reject**
> - [[batches/batch_027/candidates/C003|batch_027 C003]]: volume-weighted intraday → corr 0.65-0.89@F009 + incr_ic 负 → **reject**

---

### T004 · overnight / intraday ratio [✗ DISPROVEN batch_048]

> [!failure]+ Thread 结论：ratio 形式被 F010 吸收
> **Question**: overnight/intraday ratio（非 spread 非 correlation 的第三种函数形式）是否携带独立信号？
> **Answer**: 否。ratio 形式在 csi1000 日频被 F010 overnight persistence 吸收；|intraday| 分母未产生独立信息维度。
> **Evidence trail**:
> - [[batches/batch_048/candidates/C004|batch_048 C004]]: `Div(overnight_5, Abs(intraday_5)+0.001)` → ic_oos=0.016 mono=1.0 sign=1.0 但 **max_corr=0.898@F010 + incremental_ic=0.002** → reject（ratio 被 F010 吸收，|intraday| 分母无信息增值）

---

### T005 · rank-diff 跨 direction 泛化 [◉ ACTIVE] 🆕

> [!success]+ Thread 当前：rank-diff 跨家族首锤兑现 (partial answered batch_048, 续测)
> **Question**: batch_046/047 在 microstructure_illiquidity 内部升格的 "rank-diff = signal-family 组合几何性质" 是否可跨 direction 泛化到 overnight × 独立 signal 组合？
> **Answer**: 是——但需两端 (a) 独立 direction 或独立 raw field (b) 都 scale-free (c) 同批 LHS 共享主信号端最多 admit 1。
> **Evidence trail**:
> - [[batches/batch_048/candidates/C003|batch_048 C003]]: `CsRank(overnight_5) − CsRank(turnover_5)` → **admit → overnight_turnover_rank_diff_5**（ic_oos=0.054, ls_t=4.75, incr_ic=0.027, mono_oos=0.9, 9/9 年全正且近年最强, alpha_surv=0.431, max_corr=0.747@F010）
> - [[batches/batch_048/candidates/C001|batch_048 C001]]: `CsRank(overnight_5) − CsRank(intraday_5)` → reject near_duplicate 0.925@F009（同-direction rank-diff 不 escape raw-diff F_parent=Mean(A-B,N) 吸收律）
> - [[batches/batch_048/candidates/C002|batch_048 C002]]: `CsRank(overnight_3) − CsRank(overnight_gap_normalized)` → reject ic_oos=0.004 noise（共 numerator 抵消律）
> - [[batches/batch_048/candidates/C006|batch_048 C006]]: `CsRank(overnight_5) − CsRank(|intraday_5|)` → **reserve**（同批 anchor rule, LHS 共享 overnight_rank 让位 C003，指标全面次于 C003 但机制上 signed × magnitude 异质结构有独立维度潜力）
>
> **Next probes**: 测试 overnight × 其它独立 direction scale-free signal 的 rank-diff（Amihud illiquidity rank, pb_amount ratio rank），避免 LHS 始终是 overnight_rank；或 C006 异质结构在非 overnight LHS 上重新测试。

---

### T006 · overnight horizon-diff rank [✗ DISPROVEN batch_048] 🆕

> [!failure]+ Thread 结论：同字段跨窗口 rank-diff 抵消律
> **Question**: 20d overnight mean 与 5d overnight mean 的 rank 差（类 MACD signal）是否独立于 F010 5d persistence？
> **Answer**: 否。两端完全同字段只差 aggregation 窗口，rank 高度相关使 Sub 抵消退化为 noise。
> **Evidence trail**:
> - [[batches/batch_048/candidates/C005|batch_048 C005]]: `CsRank(overnight_20) − CsRank(overnight_5)` → hard_gate fail ic_oos=|-0.0014|<0.008（两端共享 raw field 完整 + Sub 抵消律）

---

### T008 · rank-diff RHS 共享已入库律 [✓ ANSWERED batch_049] 🆕

> [!success]+ Thread 结论：已入库 rank-diff factors 占位的 RHS 对新候选有强吸收
> **Question**: cockpit 要求 "每个候选 LHS 必须不同" 是否足以 escape 已入库 rank-diff 吸收律？
> **Answer**: 否。LHS 唯一 ≠ admit 独立——RHS 结构决定吸收强度。当 F010/F017 都在 RHS=overnight_5 端已占位，新候选即使 LHS 多元化（Amihud/pb/HHI/RealizedVol）仍被 F010/F017 RHS 共享吸收。rank-diff admit 路径=RHS 换新 basis + LHS 几何正交。
> **Evidence trail**:
> - [[batches/batch_049/candidates/C001|batch_049 C001]]: `Sub(CsRank(Mean|ret|),CsRank(overnight_5))` → max_corr=0.826@F017 + incr_ic=-0.012 → reject（LHS=L1 vol，RHS 共 F017）
> - [[batches/batch_049/candidates/C002|batch_049 C002]]: `Sub(CsRank(pb_20),CsRank(overnight_5))` → max_corr=0.713@F010 + incr_ic=-0.006 → reject（LHS=pb，RHS 共 F010）
> - [[batches/batch_049/candidates/C004|batch_049 C004]]: `Sub(CsRank(volume_HHI),CsRank(overnight_5))` → max_corr=0.725@F010 + incr_ic=+0.004 → reject（LHS=vol_HHI，incr 勉强 >0.003 但 <0.005）
> - [[batches/batch_049/candidates/C005|batch_049 C005]]: `Sub(CsRank(L2_vol),CsRank(overnight_5))` → max_corr=0.824@F017 + incr_ic=-0.009 → reject（LHS=L2 vol，RHS 共 F017）
> - 四候选共 RHS=overnight_5 全部 reject = **rank-diff RHS 共享已入库律** 验证完整
>
> **升格教训**：rank-diff 设计硬约束扩展第 4 条——两端不仅需 "≥1 独立 raw field + 不单一窗口差 + 同批 LHS 共享最多 admit 1"（batch_047+048 三条），还需 **RHS 端不在已入库 rank-diff factors 占位的端点上**。

---

### T009 · asymmetric signed×magnitude 异质结构脱离 overnight LHS [✗ DISPROVEN batch_049] 🆕

> [!failure]+ Thread 结论：batch_048 C006 reserve 的 signed×magnitude 潜在 alpha 主要来自 overnight LHS
> **Question**: batch_048 C006 `Sub(CsRank(overnight_5), CsRank(|intraday_5|))` 的 signed×magnitude 异质结构脱离 overnight LHS 后能否独立兑现？
> **Answer**: 否。在 LHS=turnover_cv_20 × RHS=|intraday_5| 组合上信号强度塌缩到 noise 边界（ic_oos=-0.0069 差 0.0011 未过 hard_gate）。反向证明 overnight signal 强度 >> |intraday| signal 强度，batch_048 C006 的潜在 alpha 主要来自 overnight LHS 端，非 signed×magnitude 函数形式本身。
> **Evidence trail**:
> - [[batches/batch_049/candidates/C003|batch_049 C003]]: `Sub(CsRank(turnover_cv_20),CsRank(|intraday_5|))` → hard_gate fail ic_oos=|-0.0069|<0.008（max_corr=0.422@F016, incr_ic=+0.021, style_r²=0.074 健康——不是机制问题而是**信号强度问题**）

---

### T010 · overnight sign frequency 复活条件首次探测 [✓ ANSWERED batch_049] 🆕

> [!success]+ Thread 结论：sign 聚合与 magnitude 聚合几何正交——hypothesis 文字级复活条件兑现
> **Question**: direction.md Hypothesis "正交 aggregation：overnight sign frequency（方向而非 magnitude）" 复活条件是否携带独立于现有 magnitude 聚合（F009/F010/F011）的 alpha？
> **Answer**: 是。`Mean(Sign(overnight),20)` rank 相对 amount rank 的 rank-diff 是 F010 相关仅 0.37 几何独立维度——sign 聚合完全丢弃 magnitude 只保留方向，与库内所有 overnight magnitude 聚合正交。整库 cum_ic_mdd 最浅级别（-1.53）+ 9/9 年全正 + 近年增强（2022/2023 最高 IC）证明 edge 在当前市场仍在增强。
> **Evidence trail**:
> - [[batches/batch_049/candidates/C006|batch_049 C006]]: `Sub(CsRank(Mean(Sign(overnight),20)),CsRank(Mean($amount,20)))` → **admit → [[factors/F018]]** ic_oos=+0.051, ls_t=+5.98, mono=+1.0, ICIR=+0.473, incr_ic=+0.015, max_corr=0.616@F012, 9/9 yr + (近年最强), cum_mdd=-1.53 (整库最浅), horizon 1d→20d IC 单调增强 (0.051→0.127)，factor_name=`overnight_sign_freq_amount_rank_diff_20`
>
> **Next probes**：sign 聚合泛化——`sign_freq × turnover` / `sign_freq × pb` / `overnight 长 horizon (20d+) sign_freq` / `overnight × intraday 非线性交互`（hypothesis 复活条件 (c) 第二条尚未探测）。

---

## Known Failures

| Batch | Candidate | Pattern | 原因 |
|---|---|---|---|
| batch_025 | C003 | 20d Corr(overnight, intraday) | hard_gate sign_flip train +0.005 / val -0.006 |
| batch_027 | C001 | 5d intraday mean | corr 0.65-0.89@F009 + incr_ic 负（F009 已吸收 intraday 分量）|
| batch_027 | C002 | 3d intraday mean | 同上 |
| batch_027 | C003 | volume-weighted intraday | 同上 |
| batch_048 | C001 | `Sub(CsRank(overnight_5),CsRank(intraday_5))` | near_duplicate 0.925@F009（CsRank 外包未 escape raw-diff 吸收律）|
| batch_048 | C002 | `Sub(CsRank(overnight_3),CsRank(overnight_gap_norm))` | ic_oos=0.004 noise（共 numerator 抵消律）|
| batch_048 | C004 | `Div(overnight_5, Abs(intraday_5))` | T004 ratio 证伪，incr_ic=0.002 + max_corr=0.898@F010 |
| batch_048 | C005 | `Sub(CsRank(overnight_20),CsRank(overnight_5))` | ic_oos=-0.0014 noise（同字段跨窗口 rank-diff 抵消律）|
| batch_049 | C001 | `Sub(CsRank(Mean\|ret\|_20),CsRank(overnight_5))` | max_corr=0.826@F017 + incr_ic=-0.012（RHS=overnight_5 共 F017 rank-diff 被吸收）|
| batch_049 | C002 | `Sub(CsRank(pb_20),CsRank(overnight_5))` | max_corr=0.713@F010 + incr_ic=-0.006（RHS=overnight_5 共 F010 被吸收）|
| batch_049 | C003 | `Sub(CsRank(turnover_cv_20),CsRank(\|intraday_5\|))` | hard_gate fail ic_oos=-0.0069 差 0.0011（signed×magnitude 异质结构脱离 overnight LHS 塌缩）|
| batch_049 | C004 | `Sub(CsRank(volume_HHI_20),CsRank(overnight_5))` | max_corr=0.725@F010 + incr_ic=+0.004（同批 C006 主导让位，RHS=overnight_5 饱和）|
| batch_049 | C005 | `Sub(CsRank(L2_RealizedVol_20),CsRank(overnight_5))` | max_corr=0.824@F017 + incr_ic=-0.009（与 C001 几乎同构，L1/L2 vol 在 csi1000 日频数值等价）|

---

## Lessons (升格)

- **数学结构吸收律**：当 F_parent = A - B 被 admit 后，pure A / pure B 的镜像 aggregation 会是 parent 的线性组合，corr 必然高 → **先跑代数展开检查，再决定是否生成镜像候选**。
- **aggregation > correlation**：cross-section 稳健性上，aggregation（spread / persistence / mean）优于 Corr(.,.,N)；本方向 correlation 1/1 sign_flip，相关形式需审慎上排。
- **家族 bloat 可被正确结构突破**：overnight 家族 4 slot 历史 saturated，但 rank-diff 跨 direction 结构 (C003) 部分复活方向——bloat 上限是 signal-family 内部结构的，不是方向绝对上限。
- **rank-diff 设计硬约束三条** (本方向贡献 batch_048 升格证据)：
  1. CsRank 外包 F_parent=Mean(A-B,N) 型已入库因子 → 仍被吸收（C001: max_corr=0.925@F009）
  2. 两端共 raw numerator OR denominator → Sub 数值抵消退化 noise（C002 shared-numerator, batch_047 C002 shared-denominator 是对偶证据）
  3. 两端完全同字段只差 aggregation 窗口 → rank 高度相关 Sub 抵消（C005: ic_oos=-0.0014）
  - **generator 层 pre-filter 规则**: rank-diff 候选两端必须有 ≥1 个独立 raw field 且不能是单一 aggregation 窗口差异
- **同批 anchor rule 扩展到 LHS 共享** (本批 C003/C006 经验)：rank-diff 同批候选若 LHS 共享主信号端 (mutual corr 预期 > 0.5)，最多 admit 1 个（extend batch_047 Sub(A,B) vs Sub(B,A) 对偶 dedup 规则）
- **rank-diff > ratio 结构** (T004 vs T005 对比)：overnight × orth signal 交互上，rank-diff incr_ic=0.027 vs ratio incr_ic=0.002，rank-diff 信息提炼效率 13 倍于 ratio；rank 空间对数值量级不敏感，不受分母小值放大影响

---

## Related

- 🟢 [[intraday_price_formation]] (productive) — F003 overnight gap admit，本方向 overnight 段的上游字段依赖
- 🟡 [[ohlc_temporal_aggregation]] (saturated) — F007 open-position admit，与 F009 spread corr=0.708

---

## Narrative Log

> [!quote]- 2026-04-21 [[batches/batch_025/judge|batch_025]] · exploring → productive (DOUBLE ADMIT 首批)
> admit=2 / reject=1。C001 admit → [[F009]] overnight_intraday_spread_5d (ic=+0.047, ls_t=5.18, incr=+0.044)；C002 admit → [[F010]] overnight_return_persistence_5d (ic=+0.024, **ls_t=7.50 整库最强**)；C003 reject — 20d 相关性 sign_flip。核心发现：overnight 段携带独立于 intraday 的 persistent signal；aggregation 有效，correlation 不稳。

> [!quote]+ 2026-04-21 [[batches/batch_027/judge|batch_027]] · productive → saturated
> admit=0 / reject=3。Intraday 镜像 3/3 reject（5d/3d/volume-weighted），全部 corr 0.65-0.89@F009 + incr_ic 负。**定论**：F009 = overnight - intraday 的数学结构已吸收 intraday 分量，pure intraday 是 (overnight - F009) 的线性组合。overnight 家族 4 slot 达 bloat 上限，方向 saturated。

> [!quote]+ 2026-04-25 [[batches/batch_048/judge|batch_048]] · saturated → productive（方向被正确结构部分复活）
> admit=1 / reserve=1 / reject=4。核心：**rank-diff 范式二次跨家族泛化兑现**——C003 `CsRank(overnight_5) − CsRank(turnover_5)` 把 batch_046/047 microstructure 内部升格的 "rank-diff = signal-family 组合几何性质" 成功外推到 overnight × 独立 direction turnover 组合（ic_oos=0.054 ls_t=4.75 incr_ic=0.027 9/9 年全正且近年最强），同时 **T004 ratio 形式 DISPROVEN**（C004 incr_ic=0.002 被 F010 吸收）+ **T006 同字段跨窗口 rank-diff DISPROVEN**（C005 ic_oos=-0.0014 noise）。
>
> **Thread 进展**：
> - T005 🆕 rank-diff 跨 direction 泛化：PARTIAL-ANSWERED（C003 admit，C001 同-direction 不 escape F009，C002 共 numerator 抵消，C006 同批 anchor reserve）
> - T004 ✗ DISPROVEN：overnight/|intraday| ratio 被 F010 吸收
> - T006 🆕 ✗ DISPROVEN：同字段跨窗口 rank-diff 抵消律
>
> **rank-diff 设计硬约束三条升格**（跨 batch_047+batch_048 证据链完整）：两端必须 ≥1 独立 raw field、不能单一 aggregation 窗口差、同批 LHS 共享最多 admit 1。
>
> **下一步**：方向 productive 后续 overnight × 其它独立 scale-free signal rank-diff 测试（Amihud/pb_amount rank）；C006 signed × magnitude 异质结构在非 overnight LHS 重测。

> [!quote]+ 2026-04-25 [[batches/batch_049/judge|batch_049]] · productive (5 admits，rank-diff 第 4 次跨家族兑现)
> admit=1 / reject=5。核心：**hypothesis 文字级复活条件 "overnight sign frequency" 首次 ANSWERED**（T010）——C006 `Sub(CsRank(Mean(Sign(overnight),20)),CsRank(Mean($amount,20)))` = ic_oos=+0.051 ls_t=+5.98 mono=+1.0 incr_ic=+0.015 max_corr=0.616@F012，整库 cum_ic_mdd 最浅级别（-1.53）+ 9/9 年全正 + 近年最强 + horizon 1d→20d IC 单调增强。Sign 聚合与 magnitude 聚合**几何正交**（F010 相关仅 0.37），rank-diff 范式第 4 次跨家族兑现达 tipping point。
>
> 同时 **T008 rank-diff RHS 共享律 ANSWERED**：cockpit 约束 "LHS 全唯一" 本批严格执行但 C001/C002/C004/C005 四候选 RHS 共 overnight_5 全 reject——LHS 唯一 ≠ admit 独立，RHS 结构决定吸收强度。rank-diff 设计硬约束扩展第 4 条：**RHS 端不在已入库 rank-diff factors 占位端点上**。
>
> **T009 DISPROVEN**：batch_048 C006 reserve 的 signed×magnitude 潜在 alpha 主要来自 overnight LHS，脱离 overnight 后塌缩 noise——反向证 overnight signal >> \|intraday\| signal 强度。
>
> **L1 vs L2 vol 冗余揭示**（C001 vs C005）：在 csi1000 日频低 kurt 样本上 Mean\|ret\| ≈ sqrt(Σret²)，未来不应同批组合两者。
>
> **下一步**：避开 RHS=overnight_5（饱和证明），sign 聚合 × 其它 basis 泛化（sign_freq × turnover / sign_freq × pb / 20d+ sign_freq）；或 overnight × intraday **非线性交互**（复活条件 (c) 第二条尚未探测）。**建议 Phase 5 consolidation 升格 lessons.md "rank-diff geometry" section** —— 4 次跨家族兑现证据链完整（batch_046/047 microstructure + batch_048 overnight_turnover + batch_049 sign_freq × amount）。
