---
direction_tag: overnight_intraday_split
status: productive
priority: high
rounds: 8
admits: 8
last_batch: batch_058
last_admits:
- F022
last_goal: 'T005 sign-aggregation 跨 axis 泛化 + 新 T011 overnight×intraday 非线性交互 (3 axes
  / 6 candidates)。Axis A: sign-aggregation LHS 扩窗 (Mean(Sign(overnight),60d)) + 新
  sign atom (Sign(intraday) 即 close-open 符号) 对接长窗 scale-free 几何 RHS (H/L_60 geometric
  ratio / Mean(H/L,60))。Axis B: intraday close-position-in-range (C-L)/(H-L) 是结构性
  vol_20d-orthogonal atom (cockpit constraint), 在 20d/60d 双窗下测。Axis C: overnight×intraday
  sign 共方向频率 (Mean(Sign(o)*Sign(i),N)) 是 T005 future_probe 3 (overnight×intraday 非线性交互)
  的 sign-space 实例化, 与 F018 单 sign 几何完全不同。RHS 全部避开 6 dead endpoints (overnight_5/body_ratio_20/pb_60/amount_60/price_vol_20/Std($close,5)*60)
  + F017/F018 共振 anchor (turnover_5/amount_20)。Bug-flag 规避: 不使用 TsKurt/TsSkew 内嵌 CsRank。anti-recap:
  zero_admit_streak=2 后, 6 候选 LHS atoms 4 类正交 (overnight_sign / intraday_sign / sign_product
  / close_position), RHS 4 类正交 (H/L_60 geo / Mean(H/L,60) / close/MA60 / amount_5_60_ratio)。预期
  ≥1 admit 推进 T005 跨 axis 泛化 + T011 共方向交互首兑现。'
last_activity: '2026-04-25T11:57:23Z'
created_batch: batch_025
members:
- F009
- F010
- F011
- F017
- F{next}
- F018
- F022
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

### T005 · rank-diff 跨 direction 泛化 [✓ ANSWERED batch_049] (升格 lessons; b048 起源 / b058 evidence 追加)

> [!success]+ Thread 结论：rank-diff = signal-family 几何范式（5 family / F015–F020）
>
> **Question**: rank-diff geometry 是否在 overnight_intraday_split 上独立兑现，跨 family 泛化为 6+ admit？sign-aggregation LHS 扩窗（Mean(Sign(overnight),20→60d)）是否产生新的独立 alpha？
>
> **Answer**: 是 — F017/F018 admit 即跨家族泛化首兑现；20d→60d 扩窗 (b058 C001) 兑现 OOS IC strong 但触 F203 cluster co-resonance with F018，结构上是 F018 的"长窗+几何 RHS"近镜像而非新独立 alpha。
>
> **Evidence trail**:
> - [[batches/batch_048/candidates/C003|batch_048 C003]]　overnight × turnover_5, ic_oos=0.054 ls_t=4.75 incr_ic=0.027 → **admit → [[factors/F017]]**
> - [[batches/batch_049/candidates/C006|batch_049 C006]]　overnight_sign_freq × amount, ic_oos=+0.051 ls_t=+5.98 → **admit → [[factors/F018]]**
> - [[batches/batch_058/candidates/C001|batch_058 C001]]　Mean(Sign(overnight),60) × H/L_60_geo, ic_oos=0.055 ls_t=3.73 mono=1.0/1.0 完美 + 9/9 年逐年强化, **alpha_surv=0.31 仅过 rank_diff floor + max_corr=0.576@F018 borderline + incr_ic=0.008<0.015 (F203)** → **reserve** (60d sign-freq 与 F018 20d 几何位置 ~57% 共享, 等待 F018 退役 / vol_20d Python residual)
> - [[batches/batch_058/candidates/C002|batch_058 C002]]　Mean(Sign(intraday body),20) × Mean(H/L,60), ic_oos=0.024 ls_t=0.65 alpha_surv=0.054 → **reject** (intraday body sign LHS 是 vol_20d/str_1m 载体, T003 disproof sign-space 实例化撞墙)

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

### T011 · overnight×intraday sign 共方向频率 cross-section 几何 [◉ ACTIVE]

> [!note]+ Thread 当前
> **Question**: `Mean(Sign(overnight) * Sign(intraday), N)` 共方向频率作为 LHS（非单边 sign 而是 product），在 cross-section rank-diff 几何下能否产生独立于 F009 (overnight-intraday spread magnitude) 与 F018 (overnight 单边 sign) 的新 alpha？窗口长度对 cross-section rank-order 的影响如何？
>
> **Evidence trail**:
> - [[batches/batch_058/candidates/C003|batch_058 C003]]　Mean(Sign(o)*Sign(i),20) × close/MA60, ic_oos=0.024 ls_t=1.09 **mono_oos=0.40 + Q5 反向**, max_corr=**0.216@F009 (本批最 library-clean)** + incr_ic=0.017 → **reject** (CP03 weak: ls_t<2 + rank-order 破坏；意外 library-clean 但信号强度不足)
> - [[batches/batch_058/candidates/C005|batch_058 C005]]　Mean(Sign(o)*Sign(i),60) × Mean(H/L,60), ic_oos=0.039 ls_t=1.91 **mono=0.9/0.9 完美** + 9/9 年逐年强化, alpha_surv=0.26<0.30 floor + max_corr=0.49@F021 + incr_ic=0.011<0.015 (F203) → **reserve**
>
> **Key finding**: **20d → 60d 长窗显著清洁 cross-section rank-order**（C003 mono=0.4 + Q5 反向 → C005 mono=0.9 + Q5 单调正）。短窗 sign-product 在 csi1000 cross-section 上噪声大，长窗累积让 rank 稳定。但长窗版本被 F021 cluster co-resonance 锁死。
>
> **Next probes**: (a) 60d sign-product LHS × 非 H/L_60 RHS（替换 RHS 脱 F021 cluster, 如 amount_5/60 ratio / log(circ_mktcap) / pe_60 等）；(b) magnitude-weighted sign-product (e.g., gap×body 加权而非纯 sign) 是否在 20d 窗口下救活 mono。

---

### T012 · intraday close-position-in-range Mean LHS [◉ ACTIVE]

> [!note]+ Thread 当前
> **Question**: `Mean((C-L)/(H-L+ε), N)` close-position-in-range 一阶矩 LHS（与 F006 upper_shadow 5d / F019 body_ratio Std / F021 upper_shadow_disp Std 几何位置不同）能否在 cross-section rank-diff 几何下兑现独立 alpha？vol_20d 正交性是否与窗口长度负相关？
>
> **Evidence trail**:
> - [[batches/batch_058/candidates/C004|batch_058 C004]]　Mean((C-L)/(H-L),20) × amount_5/60_ratio, ic_oos=0.029 ls_t=1.56 **mono_oos=0.6 + Q5 上升 + 9/9 年同号区间窄稳定**, **alpha_surv=0.43 (本批 admit 最高) + style_r²=0.13 (本批最低) + max_corr=0.283@F006 + incr_ic=0.012 + cum_mdd=-1.03 (本批最浅) + worst_quarter 永正** → **admit (close_position_amount_accel_rd_20)**
> - [[batches/batch_058/candidates/C006|batch_058 C006]]　Mean((C-L)/(H-L),60) × H/L_60_geo, ic_oos=0.044 ls_t=1.52 mono=0.3/0.9, **alpha_surv=0.19 (vol_20d exposure=44.15 本批最高极值) + max_corr=0.47@F021 + incr_ic=0.011<0.015 (F203)** → **reject** (60d 长窗放大 vol_20d 吞噬)
>
> **Key finding**: **close-position 短窗 (20d) 是 vol_20d 正交 atom 兑现** — C004 alpha_surv=0.43 vs C006 (60d) alpha_surv=0.19，**窗口翻倍让 vol_20d 吸收翻倍**。这与 T011 sign-product 趋势相反 (sign-product 60d alpha_surv=0.26 比 20d=0.56 衰减)——两个 LHS atom 对窗口扩展的 vol_20d 吞噬响应不对称。**T012 首兑现** F022 candidate close_position_amount_accel_rd_20。
>
> **Next probes**: (a) 维持 close-position 20d LHS, RHS 替换探索 (turnover-related / value-related 长窗 ratio); (b) 短窗 close-position 与 OHLC family 是否能形成新 anchor cluster (与 F006 corr=-0.28 已是 mirror).

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
| batch_058 | C002 | `Sub(CsRank(Mean(Sign(close-open),20)),CsRank(Mean($high/$low,60)))` | CP03 weak (ls_t=0.65) + CP04 alpha_surv=0.054 (vol_20d exposure=40 主吸收) — intraday body sign LHS 是 vol/str_1m 载体, T003 disproof sign-space 复现 |
| batch_058 | C003 | `Sub(CsRank(Mean(Sign(o)*Sign(i),20)),CsRank($close/MA60))` | CP03 weak (ls_t=1.09 + mono_oos=0.4 + Q5 反向) — sign-product 20d cross-section rank 信息退化, 即使 max_corr=0.216 库最 clean 也不救 |
| batch_058 | C006 | `Sub(CsRank(Mean((C-L)/(H-L),60)),CsRank(H/L_60_geo))` | CP04 alpha_surv=0.19 (vol_20d exposure=44.15 本批最高极值) + F203 cluster (max_corr=0.47@F021 + incr_ic=0.011<0.015) — close-position 60d 长窗放大 vol 吞噬 |

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

> [!quote]+ 2026-04-25 · [[batches/batch_058/judge|batch_058]] · 8th admit · T011/T012 双新 thread 启动
> **8th admit · T012 close_position_amount_accel_rd_20** · admit=1 (C004) / reserve=2 (C001/C005) / reject=3 (C002/C003/C006)
>
> - **T012 首兑现 (close-position-in-range × amount accel)**：C004 `Sub(CsRank(Mean((C-L)/(H-L),20)), CsRank(amount_5/60))` IC_OOS=0.029 ICIR=0.36 + alpha_surv=**0.43 (本批 admit 最高)** + style_r²=**0.13 (本批最低)** + max_corr=**0.283@F006 + incr_ic=0.012** + cum_ic_mdd=**-1.03 (本批最浅)** + worst_quarter_ic=+0.0017 **永正** + 9/9 年区间窄稳定 → **admit**。**LHS atom (C-L)/(H-L) 是结构性 vol_20d 正交 atom 兑现** (cockpit constraint)：0-1 normalization 让 alpha 不嵌入 vol 量级。
> - **T012 关键发现**：close-position **20d (alpha_surv=0.43) vs 60d (alpha_surv=0.19)** — 窗口翻倍让 vol_20d 吸收翻倍。短窗 close-position 是 vol 正交载体, 长窗放大 vol 吞噬。**Lessons 候选升格**："close-position-in-range Mean LHS 短窗化是 vol_20d 正交 axis"。
> - **T011 共方向 sign-product 启动（active）**：C003 (20d) **mono_oos=0.40 + Q5 反向 + ls_t=1.09 < 2** reject — sign-product 20d cross-section rank 信息退化；C005 (60d) **mono=0.9/0.9 完美 + 9/9 年逐年强化 + ls_t=1.91 接近 2** 但 alpha_surv=0.26 < rank_diff floor 0.30 + F203 cluster (max_corr=0.49@F021 + incr_ic=0.011<0.015) → **reserve**。**关键发现**：**20d → 60d 长窗显著清洁 sign-product cross-section rank-order**，与 close-position 趋势相反。
> - **T005 sign-aggregation 60d 扩窗 (C001)**：IC_OOS=0.055 ICIR=0.40 ls_t=3.73 mono=1.0/1.0 完美 + 9/9 年单调强化至 2023 IC=0.060。但 max_corr=0.576@F018 borderline + incr_ic=0.008<0.015 (F203) + alpha_surv=0.31 仅过 rank_diff floor → **reserve**。结构上是 F018 (20d sign-freq) 的"长窗+几何 RHS"近镜像，等待 F018 退役。
> - **C002 reject (intraday body sign LHS)**：alpha_surv=0.054 vol_20d/str_1m 载体, T003 (intraday 镜像 aggregation DISPROVEN) 的 sign-space 实例化也撞墙 — sign 离散化未脱 F009 吸收。
> - **zero_admit_streak=2 → 0**（连续两批 zero admit 终结）。**MT budget**：cumulative 306 → **312** · direction 21 → **27** · bucket `high`（封顶 search_adjusted 推回 `medium`）· 本批 6 候选全 high bucket（direction.exposure 已饱和）
>
> **Operations**　direction `productive` 保持 + `priority: high` 保持 · T005 evidence 追加 (b058 C001/C002) 状态保持 ANSWERED · T011 + T012 新建 ACTIVE · Python 在 Phase 4 backfill F022 (next id) 链接

> [!quote]- 2026-04-21 [[batches/batch_025/judge|batch_025]] · exploring → productive (DOUBLE ADMIT 首批)
> admit=2 / reject=1。F009 spread (ic=+0.047, ls_t=5.18) + F010 persistence (**ls_t=7.50 整库最强**)；C003 20d Corr sign_flip。核心：overnight 段携带独立于 intraday 的 persistent signal；aggregation 有效，correlation 不稳。

> [!quote]- 2026-04-21 [[batches/batch_027/judge|batch_027]] · productive → saturated
> admit=0 / reject=3。Intraday 镜像 3/3 reject（corr 0.65–0.89@F009 + incr_ic 负）。**定论**：F009 = overnight − intraday 数学结构已吸收 intraday 分量。家族 4 slot 达 bloat 上限。

> [!quote]- 2026-04-25 [[batches/batch_048/judge|batch_048]] · saturated → productive（rank-diff 复活）
> admit=1 / reserve=1 / reject=4。**rank-diff 范式 2 次跨家族兑现**——C003 `CsRank(overnight_5) − CsRank(turnover_5)` → F017 (ic_oos=0.054 incr_ic=0.027 9/9yr+)。同时 T004 ratio + T006 同字段跨窗口 DISPROVEN。**rank-diff 设计硬约束三条升格**（≥1 独立 raw field / 不单一窗口差 / 同批 LHS 共享 anchor rule）。

> [!quote]- 2026-04-25 [[batches/batch_049/judge|batch_049]] · productive (rank-diff 第 4 次跨家族兑现)
> admit=1 / reject=5。**hypothesis 文字级复活条件 "overnight sign frequency" 首次 ANSWERED**（T010）——C006 → [[F018]] (ic_oos=+0.051 ls_t=+5.98 incr_ic=+0.015 max_corr=0.616@F012 cum_mdd=-1.53 整库最浅 horizon IC 单调增强 0.051→0.127)。Sign 聚合 vs magnitude 聚合**几何正交**（F010 相关仅 0.37）。**T008 rank-diff RHS 共享律 ANSWERED**：四候选共 RHS=overnight_5 全 reject → 硬约束第 4 条扩展（RHS 不在已入库 rank-diff 占位端点）。**T009 DISPROVEN**（signed×magnitude 脱 overnight LHS 塌缩）。**触发 Phase 5 consolidation 升格 lessons.md "Rank-Diff Geometry" section**——4 次跨家族证据链完整（batch_046/047 microstructure + batch_048 overnight×turnover + batch_049 sign_freq×amount，后续 batch_050 OHLC F019 / batch_051 gap F020 加固至 6 family）。
