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
> 🟢 **productive** · 7 rounds · 7 admits — rank-diff 范式跨家族 4 次兑现（F017/F018）触发 Phase 5 consolidation 升格 `lessons.md` "Rank-Diff Geometry" 五律。
> **Members**: [[F009]] overnight_intraday_spread_5d · [[F010]] overnight_return_persistence_5d · [[F011]] overnight_return_persistence_3d · [[F017]] overnight_turnover_rank_diff_5 · [[F018]] overnight_sign_freq_amount_rank_diff_20

---

## Hypothesis

> [!success]+ 已验证（partial）
> 分解 daily return 为 **overnight** ((open-prev_close)/prev_close) 与 **intraday** ((close-open)/open) 两段，驱动因子不同：overnight = 隔夜消息 + 机构 pre-market；intraday = 日内散户 + 算法。**Aggregation 形式（spread / persistence / sign-freq）在 cross-section 上携带独立 alpha**——batch_025 DOUBLE ADMIT 打破整库 ls_t 记录（F010 ls_t=7.50）；batch_048/049 rank-diff 几何 (F017/F018) 把 overnight 与独立 direction signal 组合升格为系统级范式。
>
> **已封闭**：correlation 形式不稳（sign_flip）；pure intraday 镜像冗余（F009 已隐式吸收 intraday 分量）；overnight/|intraday| ratio 被 F010 吸收；同字段跨窗口 rank-diff 抵消；signed×magnitude 异质结构脱离 overnight LHS 后塌缩。
>
> **复活条件**：
> - **新字段**：minute-bar session 分解（open auction / midday / close auction）突破 daily 二分
> - **更长 horizon**：20d+ overnight persistence 是否仍独立于 5d 版本
> - **正交 aggregation**：overnight × intraday 非线性交互（sign_freq 已通过 F018 兑现）

> [!warning]+ ⚠️ Rank-Diff 几何升格约束（F002 / F305 跨方向硬约束）
> rank-diff `Sub(CsRank(LHS), CsRank(RHS))` 在 6 family 兑现 (F015–F020) 后已升格 `lessons.md` 顶级 section，本方向新候选必须满足 **7 条硬约束**：
> 1. 两端 scale-invariant（CV/ratio/correlation；Std/Mean/绝对 level 退化为主因子近重复）
> 2. 两端 ≥1 raw field 独立（共 numerator/denominator → Sub 抵消）
> 3. 不能同字段跨窗口
> 4. `Sub(A,B)` 与 `Sub(B,A)` pre-dedup
> 5. 同批 LHS 共享 anchor → 最多 admit 1
> 6. **RHS 不在已入库 rank-diff factors 占位端点上**——overnight_5 / turnover_5 / amount_20 / body_ratio_20 / price_vol_20 已成 dead RHS endpoints
> 7. saturated 方向 anchor factor (F002/F012/F020) 形成 ±0.4–0.7 cluster，新 rank-diff 无法绕开
>
> 配套阈值校准（F200 / F203）：rank-diff 候选 `alpha_surv_min=0.30`（structural vol_20d coupling 是几何宿命）；`max_corr ∈ [0.30, 0.70]` borderline 区间需 `incr_ic ≥ 0.015` 才 admit。
>
> **跨方向延伸律**："Barra-clean ≠ library-clean"（F007）——CP04 alpha_surv 高 ≠ CP05 库独立；admit 必须**联合**判断。

---

## Threads

### T001 · overnight aggregation (spread + persistence) [✓ ANSWERED batch_025]

> [!success]+ 机制确认：overnight 段独立 alpha 已吸收
> spread 5d → [[F009]] (ic=+0.047 ls_t=5.18 incr=+0.044)；5d overnight persistence → [[F010]] (ic=+0.024 **ls_t=7.50 整库记录** incr=+0.019)。

---

### T002 · overnight-intraday correlation [✗ DISPROVEN batch_025]

> [!failure]+ 机制封闭：correlation 形式不稳定
> 20d Corr → hard_gate sign_flip train +0.005 / val -0.006。

---

### T003 · intraday 镜像 aggregation [✗ DISPROVEN batch_027]

> [!failure]+ 机制封闭：F009 = overnight − intraday 已吸收 intraday 分量
> 5d/3d/volume-weighted intraday 3/3 reject，corr 0.65–0.89@F009 + incr_ic 负。

---

### T004 · overnight / intraday ratio [✗ DISPROVEN batch_048]

> [!failure]+ ratio 形式被 F010 吸收
> `Div(overnight_5, Abs(intraday_5))` → ic_oos=0.016 但 max_corr=0.898@F010 + incr_ic=0.002。**rank-diff > ratio**：incr_ic 13× 优势（rank 空间不受分母小值放大影响）。

---

### T005 · rank-diff 跨 direction 泛化 [✓ ANSWERED batch_048+049, 升格 lessons]

> [!success]+ Thread 结论：rank-diff = signal-family 几何范式（5 family / F015–F020）
> overnight × turnover_5 → [[F017]] (ic_oos=0.054, ls_t=4.75, incr_ic=0.027, 9/9yr+, max_corr=0.747@F010)；overnight_sign_freq × amount → [[F018]] (ic_oos=+0.051, ls_t=+5.98, incr_ic=+0.015, max_corr=0.616@F012, cum_mdd=-1.53 整库最浅, horizon 1d→20d IC 单调增强 0.051→0.127)。
> **下一步**: 避开 dead RHS endpoints，sign 聚合 × turnover/pb 泛化 + 20d+ sign_freq + overnight × intraday 非线性交互。

---

### T006 · overnight horizon-diff rank [✗ DISPROVEN batch_048]

> [!failure]+ 同字段跨窗口 rank-diff 抵消律
> `Sub(CsRank(overnight_20),CsRank(overnight_5))` → ic_oos=-0.0014（约束 3）。

---

### T008 · rank-diff RHS 共享已入库律 [✓ ANSWERED batch_049, 升格 lessons]

> [!success]+ Thread 结论：LHS 唯一 ≠ admit 独立——RHS 结构决定吸收强度
> batch_049 C001/C002/C004/C005 四候选共 RHS=overnight_5 全 reject（max_corr 0.71–0.83@F010/F017）→ rank-diff 设计硬约束第 6 条："RHS 不在已入库 rank-diff factors 占位端点上"。

---

### T009 · signed×magnitude 异质结构脱离 overnight LHS [✗ DISPROVEN batch_049]

> [!failure]+ batch_048 C006 reserve 的 alpha 主要来自 overnight LHS
> `Sub(CsRank(turnover_cv_20),CsRank(|intraday_5|))` → hard_gate fail ic_oos=-0.0069（style_r²=0.074 健康，纯**信号强度问题**）。反向证 overnight signal >> |intraday| signal。

---

### T010 · overnight sign frequency 复活条件首次探测 [✓ ANSWERED batch_049]

> [!success]+ sign 聚合与 magnitude 聚合几何正交——hypothesis 文字级复活条件兑现
> `Mean(Sign(overnight),20)` 完全丢弃 magnitude 只保留方向，与库内所有 overnight magnitude 聚合正交（F010 相关仅 0.37）→ [[F018]]。

---

## Known Failures

| Batch | Candidate | Pattern | 原因 |
|---|---|---|---|
| batch_025 | C003 | 20d Corr(overnight, intraday) | sign_flip |
| batch_027 | C001-C003 | intraday mean 镜像 (5d/3d/vw) | F009 已吸收 intraday |
| batch_048 | C001 | `Sub(CsRank(overnight_5),CsRank(intraday_5))` | near_dup 0.925@F009（CsRank 不 escape raw-diff）|
| batch_048 | C002 | `Sub(CsRank(overnight_3),CsRank(overnight_gap_norm))` | 共 numerator 抵消 |
| batch_048 | C004 | `Div(overnight_5, Abs(intraday_5))` | ratio 被 F010 吸收 |
| batch_048 | C005 | `Sub(CsRank(overnight_20),CsRank(overnight_5))` | 同字段跨窗口抵消 |
| batch_049 | C001 | `Sub(CsRank(Mean\|ret\|_20),CsRank(overnight_5))` | RHS=overnight_5 共 F017 |
| batch_049 | C002 | `Sub(CsRank(pb_20),CsRank(overnight_5))` | RHS 共 F010 |
| batch_049 | C003 | `Sub(CsRank(turnover_cv_20),CsRank(\|intraday_5\|))` | 信号强度塌缩 noise |
| batch_049 | C004 | `Sub(CsRank(volume_HHI_20),CsRank(overnight_5))` | RHS 饱和，让位 C006 |
| batch_049 | C005 | `Sub(CsRank(L2_RealizedVol_20),CsRank(overnight_5))` | 与 C001 同构（L1≈L2 在 csi1000 日频）|

---

## Lessons (本方向贡献至 lessons.md)

- **数学结构吸收律**：F_parent = A − B 被 admit 后，pure A / pure B 镜像必为线性组合 → 先做代数展开
- **aggregation > correlation**：cross-section 稳健性上 aggregation 优于 Corr(.,.,N)
- **rank-diff > ratio**：incr_ic 13× 优势（rank 空间不受分母小值放大）
- **rank-diff 设计硬约束**（本方向贡献 batch_048+049 证据，已升格至 lessons.md "Rank-Diff Geometry" 五律 + F002 / F305 7 条扩展）
- **RHS 共振饱和动态**：每 admit 一个 rank-diff 就消耗一个 RHS 类目（overnight_5 现已 dead endpoint）
- **L1 vs L2 vol 冗余**：csi1000 日频低 kurt 样本 Mean|ret| ≈ sqrt(Σret²)，未来不应同批组合

---

## Related

- 🟢 [[intraday_price_formation]] (saturated) — F003 overnight gap 上游字段；F020 anti-anchor cluster 锁死该方向 rank-diff 泛化
- 🟡 [[ohlc_temporal_aggregation]] (productive) — F019 higher-moment LHS 同律；F007 corr=0.708@F009
- 🟢 [[microstructure_illiquidity]] (productive) — rank-diff 范式发源地（F015/F016）
- 🟡 [[gap_acceptance_structure]] (productive) — F020 higher-moment LHS 跨家族复现

---

## Narrative Log

> [!quote]- 2026-04-21 [[batches/batch_025/judge|batch_025]] · exploring → productive (DOUBLE ADMIT 首批)
> admit=2 / reject=1。F009 spread (ic=+0.047, ls_t=5.18) + F010 persistence (**ls_t=7.50 整库最强**)；C003 20d Corr sign_flip。核心：overnight 段携带独立于 intraday 的 persistent signal；aggregation 有效，correlation 不稳。

> [!quote]- 2026-04-21 [[batches/batch_027/judge|batch_027]] · productive → saturated
> admit=0 / reject=3。Intraday 镜像 3/3 reject（corr 0.65–0.89@F009 + incr_ic 负）。**定论**：F009 = overnight − intraday 数学结构已吸收 intraday 分量。家族 4 slot 达 bloat 上限。

> [!quote]- 2026-04-25 [[batches/batch_048/judge|batch_048]] · saturated → productive（rank-diff 复活）
> admit=1 / reserve=1 / reject=4。**rank-diff 范式 2 次跨家族兑现**——C003 `CsRank(overnight_5) − CsRank(turnover_5)` → F017 (ic_oos=0.054 incr_ic=0.027 9/9yr+)。同时 T004 ratio + T006 同字段跨窗口 DISPROVEN。**rank-diff 设计硬约束三条升格**（≥1 独立 raw field / 不单一窗口差 / 同批 LHS 共享 anchor rule）。

> [!quote]+ 2026-04-25 [[batches/batch_049/judge|batch_049]] · productive (rank-diff 第 4 次跨家族兑现)
> admit=1 / reject=5。**hypothesis 文字级复活条件 "overnight sign frequency" 首次 ANSWERED**（T010）——C006 → [[F018]] (ic_oos=+0.051 ls_t=+5.98 incr_ic=+0.015 max_corr=0.616@F012 cum_mdd=-1.53 整库最浅 horizon IC 单调增强 0.051→0.127)。Sign 聚合 vs magnitude 聚合**几何正交**（F010 相关仅 0.37）。**T008 rank-diff RHS 共享律 ANSWERED**：四候选共 RHS=overnight_5 全 reject → 硬约束第 4 条扩展（RHS 不在已入库 rank-diff 占位端点）。**T009 DISPROVEN**（signed×magnitude 脱 overnight LHS 塌缩）。**触发 Phase 5 consolidation 升格 lessons.md "Rank-Diff Geometry" section**——4 次跨家族证据链完整（batch_046/047 microstructure + batch_048 overnight×turnover + batch_049 sign_freq×amount，后续 batch_050 OHLC F019 / batch_051 gap F020 加固至 6 family）。
