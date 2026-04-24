---
direction_tag: overnight_intraday_split
status: productive
priority: high
rounds: 5
admits: 5
last_batch: batch_048
last_admits:
- F017
last_goal: 方向 saturated 后测试 T007 rank-diff 范式 (microstructure 两批 admit 升格) 在 overnight
  家族 的跨方向泛化 + T004 overnight/intraday ratio 悬挂复活。batch_047 升格教训：rank-diff 结构 alpha
  = signal-family 组合几何性质，约束 (1) 两端 scale-free (2) raw 字段独立不共振 (3) 两端不被单一库因子主导吸收 (4)
  Sub 反向对偶同批 dedup。本批六候选按此范式覆盖：(C001) rank-diff 核心——CsRank(overnight_5d mean) − CsRank(intraday_5d
  mean)，overnight vs intraday 是结构 complement (分子 Δ 字段不同 + 分母字段不同)， 测 CsRank 外包是否 escape
  F009 spread 的 raw-diff aggregation 吸收；(C002) 同家族跨窗口跨 norm rank-diff ——F010 overnight
  3d persistence (prev_close 分母) vs F003 overnight gap normalized (MeanHigh 分母)； (C003)
  跨 direction rank-diff——overnight 5d × turnover_rate 5d，两端独立 direction 且不共享 raw field，
  测 overnight signal × liquidity signal 是否产新 alpha；(C004) T004 悬挂复活——Div(overnight_5,
  |intraday_5|) 非 rank 形式 ratio，signal-to-noise 结构；(C005) overnight horizon-diff——CsRank(20d
  mean) − CsRank(5d mean)， 捕捉 overnight 长短期 acceleration (类 MACD)；(C006) asymmetric
  rank-diff——CsRank(overnight_5) − CsRank(|intraday_5|)， signed vs magnitude 函数结构异质。避开死模式：Sub
  反向对偶 (不测 B−A); 两端共享 raw 分母 (C002 分母 Ref($close,1) vs Mean($high,1) 独立); rank-preserving
  DSL 变换 (本批无纯保序候选)。目标 ≥1 candidate 满足 max_corr@lib <0.70 + alpha_surv >0.40 + ls_t
  >2 + incremental_ic >0.010，兑现"rank-diff 是通用几何性质"在 overnight 家族的二次泛化。
last_activity: '2026-04-24T20:41:49Z'
created_batch: batch_025
members:
- F009
- F010
- F011
- F017
retired_members: []
merged_into: null
---
# overnight_intraday_split

> [!abstract]+ 方向概要
> 🟢 **productive** · 4 rounds · 4 admits — overnight 家族 4 slot (F003/F007/F009/F010) 历史 saturated，但 batch_048 C003 (overnight × turnover rank-diff) 正确结构**部分复活**方向——rank-diff 跨 direction 泛化引入第 5 维度（待 Phase 4 分配 F{id}）。
> **Members**: [[F009]] overnight_intraday_spread_5d · [[F010]] overnight_return_persistence_5d · [[F011]] overnight_return_persistence_3d · overnight_turnover_rank_diff_5 (F{id} 待 Phase 4 分配)

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
