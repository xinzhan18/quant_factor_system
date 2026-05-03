---
direction_tag: overnight_intraday_split
status: saturated
priority: medium
rounds: 16
admits: 9
last_batch: batch_087
last_admits: []
last_goal: 'Round 87 — overnight_intraday_split continue_direction (cockpit hint:
  唯一 productive direction, alpha191 saturated). zero_admit_streak=4 (b066/b080 + 跨方向
  b081-b086). T011 axis ANSWERED-saturated (b080); T012-T016 全 closed; 仅 T017 (Corr
  volume × overnight_gap atom) reserve 火种 (b066 C005 alpha_surv=1.16 Barra cleanest
  但 ls_t_oos=1.26 不投资). 本批 6 候选探索 P008 escape (TsRank window≥60d on ratio fields =
  vol_20d-escape) 与 T017 axis 双路径: (a) T017 extension 20d→60d Corr 长窗 + RHS axis swap
  (b066 C005 RHS=Std(volume,60) borderline F002 → 改 H-L_60 range RHS); (b) overnight/intraday
  body ratio TsRank 60d standalone (microstructure-only ratio, P008 escape 候选); (c)
  overnight signed-flow microstructure rank-diff (volume×ret/amount Inner ratio TsRank
  60d × num_trades_60); (d) overnight magnitude TsRank 60d × num_trades_60 fresh RHS
  (T011 axis 唯一未撞死 RHS); (e) Cov(overnight_gap, intraday_body, 20) microstructure
  rank-diff × amount_120 fresh RHS (双 OHLCV-derived 操作数, P019 Corr-safe 双端); (f) TsRank
  long-window ratio with $num_trades flow signal 镜像 — 测 P008 escape 是否 cross-direction
  复现. 全候选避 F010/F018/F023 anchor cluster (b080 4-anchor cluster), 严守 P019 Corr-safe
  数据契约 (双端均 ∈ OHLCV+amount+num_trades 集), 避 P016 cap-denominator, 避 P004/P021 Mul(overnight,
  vol_proxy) wrapper 跨字段塌缩. 刻意 skip baseline-first (15 untouched fields 全为 TTM fundamental
  字段, 与本 OHLC/microstructure direction 完全不相关). Hard targets: ≥1 admit alpha_surv≥0.30
  (rank_diff floor) + max_corr<0.50 + incr_ic≥0.015 (borderline gate) + ls_t≥2 + sign_consistency=1.0.
  Fail → 触 consolidation_trigger (rounds_since_consolidation=5+1=6 临近 10 阈值, zero_admit_streak=5
  强证据 T017/P008 escape 双路径在本方向真饱和).'
prev_goal: 'Round 80 zero_admit_streak=3, 6 closed threads (T012-T016) + T017 reserve.
  Probe T011 (magnitude-weighted product) extension axis with FRESH atom geometries
  not tried in 12 rounds: (a) overnight × volume-delta product (volume change as weight,
  distinct from F023 gap×body); (b) overnight magnitude × turnover (level product,
  distinct from F017 sign-magnitude rank-diff); (c) overnight × intraday range product
  (range vs body distinct geometry); (d) signed-asymmetric joint 60d (overnight ×
  Sign(intraday) — overnight magnitude survives, intraday only contributes direction,
  60d untried window); (e) acceleration: Mean_5 - Mean_20 short-vs-long overnight
  reversion premium; (f) overnight × turnover product 60d long-window. RHS uses 4
  fresh fundamental TTM endpoints (peg_ratio_ttm / dividend_yield_ttm / pcf_ratio_total_ttm
  / num_trades_60/120) NOT in dead RHS list (overnight_5/turnover_5/amount_20/body_ratio_20/price_vol_20/circ_mktcap_60/H_L_60).
  Hard targets: ≥1 admit alpha_surv≥0.30 (rank_diff floor) + max_corr<0.50 + incr_ic≥0.015
  borderline + ls_t≥2 + 9/9 sign_consistency. P019 data-contract obeyed: no Corr cross-field
  with TTM (Corr-safe set only OHLCV+amount+num_trades). Fail → escalate consolidation
  trigger ready (rounds_since=7 → 8 next).'
last_activity: '2026-05-03T08:25:26Z'
created_batch: batch_025
members:
- F009
- F010
- F011
- F017
- F018
- F022
- F023
retired_members: []
merged_into: null
---
# overnight_intraday_split

> [!abstract]+ 方向概要
> 🟡 **saturated** · 16 rounds · 9 admits — overnight/intraday 二段分解兑现 5 个 Mean/sign-freq atom + 2 个 rank-diff family + 1 个 magnitude-product。b066→b087 连续 3 轮 zero_admit + 6 thread DISPROVEN，仅 T017 (Corr volume × overnight_gap) reserve 火种待 horizon policy 调整。
> **Members**: [[F009]] · [[F010]] · [[F011]] · [[F017]] · [[F018]] · [[F022]] · [[F023]]

---

## Hypothesis

> [!success]+ 已验证
> 分解 daily return 为 **overnight** 与 **intraday** 两段，driver 不同 (overnight = 隔夜消息+机构 pre-market；intraday = 日内散户+算法)，aggregation (spread / persistence / sign-freq / magnitude-product) 在 cross-section 携带独立 alpha。F010 ls_t=7.50 整库记录；F017/F018 把 overnight 与独立 direction signal 组合升格 rank-diff 范式。

> [!failure]+ 已封闭 (b087 全面饱和)
> - **correlation** 形式不稳 (sign_flip)
> - **pure intraday 镜像** 冗余 (F009 已吸收 intraday)
> - **overnight/|intraday| ratio** 被 F010 吸收
> - **同字段跨窗口 rank-diff** 抵消
> - **signed×magnitude 异质结构** 脱 overnight LHS 后塌缩
> - **close-position atom** 4 代 LHS 几何穷尽 (T012)
> - **sign-离散化 hybrid** Sign×|magnitude| 双向探针 (T013)
> - **autocorr atom** lag-1 持续性 vol_20d-locked (T014)
> - **shape moment Skew/Kurt** 不 P003-flip 但 P004-absorb (T015)
> - **TsRank/Rank wrap** 仅 within-name normalization, 不脱 anchor cluster (T016)
> - **T011 axis (magnitude-weighted product)** ≥10 fresh atom 跨 form 全失败 (b080+b087 累计) — DISPROVEN-comprehensive

> [!info]+ 复活条件
> - **新数据**：minute-bar session 分解 (open auction / midday / close auction)
> - **长 horizon evaluation policy**：T017 reserve 在 20d horizon IC=0.073 显著
> - **anchor 退役**：F002/F012/F018/F019/F023 cluster 解锁后重测 T011/T017 火种

> [!warning]+ ⚠️ Rank-Diff 几何升格约束 (跨方向硬约束)
> rank-diff `Sub(CsRank(LHS), CsRank(RHS))` 在 6+ family 兑现后已升格 `lessons.md`。本方向新候选 7 条硬约束：
> 1. 两端 scale-invariant (CV/ratio/correlation；Std/Mean/绝对 level 退化为主因子近重复)
> 2. 两端 ≥1 raw field 独立 (共 numerator/denominator → Sub 抵消)
> 3. 不能同字段跨窗口
> 4. `Sub(A,B)` 与 `Sub(B,A)` pre-dedup
> 5. 同批 LHS 共享 anchor → 最多 admit 1
> 6. **RHS 不在已入库 rank-diff factors 占位端点上**——overnight_5 / turnover_5 / amount_20 / body_ratio_20 / price_vol_20 / circ_mktcap_60 / H_L_60 已成 dead RHS endpoints
> 7. saturated 方向 anchor (F002/F012/F018/F019/F020/F023) 形成 ±0.4–0.7 cluster, 新 rank-diff 无法绕开
>
> 阈值校准: rank-diff `alpha_surv_min=0.30`；`max_corr ∈ [0.30, 0.70]` borderline 区间需 `incr_ic ≥ 0.015`。**"Barra-clean ≠ library-clean"** 反向亦成立 (b066: 不存在双 clean 候选)。

---

## Threads

### T001-T010 · 早期 thread 集合 [✓ CLOSED batch_025-049]

> [!success]+ 5 admit + 5 DISPROVEN — overnight/intraday 二段分解的核心兑现期
> - **T001** overnight aggregation (spread+persistence) [✓ b025]: F009 spread (ic=0.047 ls_t=5.18) + F010 5d persistence (**ls_t=7.50 整库记录**)
> - **T002** overnight-intraday correlation [✗ b025]: 20d Corr sign_flip
> - **T003** intraday 镜像 aggregation [✗ b027]: 3/3 reject, F009=overnight−intraday 数学结构已吸收 intraday 分量
> - **T004** overnight/|intraday| ratio [✗ b048]: ic_oos=0.016 但 max_corr=0.898@F010, **rank-diff > ratio (incr_ic 13× 优势)**
> - **T005** rank-diff 跨 direction 泛化 [✓ b049, 升格 lessons]: F017 (overnight×turnover_5) + F018 (overnight_sign_freq×amount) — sign-aggregation 60d 扩窗 (b058 C001) reserve, F018 长窗近镜像
> - **T006** overnight horizon-diff rank [✗ b048]: 同字段跨窗口抵消律
> - **T008** rank-diff RHS 共享律 [✓ b049, 升格 lessons]: 共 RHS=overnight_5 全 reject → 硬约束第 6 条
> - **T009** signed×magnitude 脱 overnight LHS [✗ b049]: |intraday| 信号塌缩 noise → overnight signal >> |intraday|
> - **T010** overnight sign frequency 复活条件 [✓ b049]: Mean(Sign(overnight),20) → F018, sign vs magnitude 几何正交 (corr=0.37)
> - **T011** magnitude-weighted product [✓ ANSWERED b059] → 见下方 T011 final state

---

### T011 · overnight×intraday joint magnitude/sign 共方向交互 [✗ DISPROVEN-comprehensive batch_087]

> [!failure]+ Thread 结论：magnitude × magnitude 直乘 (F023 b059) 兑现唯一 admit；累计 ≥10 fresh atom 跨 form 全饱和
>
> **Question**: 共方向交互 (sign-product / magnitude-product / weight-product) 是否在 cross-section rank-diff 几何下产生独立 alpha？
>
> **Answer (multi-stage)**:
> - **sign-only 路径** (b058 C003 短窗 mono 退化 / b058 C005 长窗 alpha_surv 不足 / b059 C003 1d horizon noise-bound): csi1000 1d primary_horizon 受阻
> - **magnitude-weighted product 兑现 admit** (b059 C004): `Mean((O-Ref(C,1))*(C-O),20) × Mean(amount,60)` ic_oos=**0.044** ICIR=**0.37** ls_t=**4.89** mono=1.0/1.0 + 9/9 年正 + IC anti-decay + cum_ic_mdd=-1.72 库内最浅之一 + incr_ic=**0.018** → **F023**
> - **b080 6 fresh weighting 全失败** (1 reserve C006: 60d turnover-weighted overnight, alpha_surv=0.61 PASS 但 4 anchor cluster + incr_ic=0.0098 缺 F203 borderline gate ~33%)
> - **b087 4 fresh probes 0/4 admit** (C002 ratio TsRank standalone 撞 F003 0.828 / C003 signed-flow Rank-60 共享 amount denominator 撞 F012 0.586 / C004 |overnight| Rank-60 sign_flip + decay=-14.78 / C005 Cov(o,i,20) 0.927 near_dup F023)
> - **累计 b080+b087 ≥10 fresh atom** 跨 magnitude / ratio / signed-flow / Cov / TsRank wrap / standalone 形式全失败
>
> **Reserve 火种**:
> - [[batches/batch_080/candidates/C006|b080 C006]] `Mean(overnight × turnover, 60) × Std($num_trades,60)` — alpha_surv=0.61 PASS + 9/9 年正 + ls_t=4.06 + cum_mdd=-1.37 但 4 anchor cluster (F002/F012/F018/F023) + incr_ic=0.0098 缺 F203 0.015 ~33% → reserve 待 F018/F023 退役
>
> **Key finding (b087) — Cov ≈ Mean of product 等价律**: csi1000 daily zero-mean stationary return-pair 下 `Cov(X,Y,N) = Mean(XY,N) - Mean(X,N)*Mean(Y,N) ≈ Mean(XY,N)` (Mean(daily return)≈0 让 cov 二阶项消失)。F023 (Mean of product) admit 后所有 Cov(overnight, intraday, N) atom 自动 cross-section near_dup (b087 C005 实测 0.927)。**应升格 Phase 1 generator AST 自检第 9 条**, 与 P024 In-batch denominator equivalence 同律。
>
> **核心律**: sign-only 是 long-horizon (10d-20d) 现象, 1d 主 horizon 下 noise-dominated; magnitude-weighted 在 1d horizon 下 ls_t=4.89 + anti-decay。T011 axis 已结构性饱和。

---

### T012 · intraday close-position-in-range Mean LHS — 4 代几何穷尽 [✗ DISPROVEN batch_060]

> [!failure]+ Thread 结论：close-position atom 4 代 LHS 设计全部失败 — 几何已彻底饱和
>
> **Question**: `Mean((C-L)/(H-L+ε), N)` 一阶矩 LHS 能否在 rank-diff 下兑现独立 alpha？仿射变体 / 跨窗 normalization / 非线性 wrap / 不对称 reference 是否突破？
>
> **Answer**: F022 admit (b058) 后 4 代设计全部失败 — close-position atom 在 csi1000 daily-bar 几何已结构性饱和。
> - **仿射变体** center-position `(C-mid)/(H-L)` corr=0.93@F022 hard_gate near_dup
> - **跨窗 Min-Max normalization** (b060 C001/C006) 让 atom 脱 F022 (max_corr<0.40) 但 incr_ic ≤+0.0025 + ls_t essentially zero (cross-section IC 健康但 long-short 不投资)
> - **Power-cubed 非线性 wrap** (b060 C002): IS=+0.018 OOS=-0.022 ls_t=-2.77 + alpha_surv=0.08 + cum_ic_mdd=-57.95 — **P003 higher-moment regime sign-flip 在 close-position cubic moment 首次实证复现** (扩展到三阶 power moment)
> - **from-peak 不对称 reference** (b060 C003): hard_gate fail ic_oos=0.0040 — cross-section 信号塌缩 noise
>
> **Admit 与 reserve**:
> - [[factors/F022|F022]] (b058 C004) `Mean((C-L)/(H-L),20) × amount_5/60` — alpha_surv=0.43 (b058 admit 最高) + max_corr=0.283@F006 + incr_ic=0.012
> - b060 C006 60d cross-window normalization × Std(turnover,60), alpha_surv=0.93 + incr_ic=+0.0025 + max_corr=0.37@F017 cluster-clean → reserve (ls_t=0.39 不投资但双绿，等 F017 退役)
>
> **Key finding (b058)**: 20d (alpha_surv=0.43) vs 60d (alpha_surv=0.19) — 窗口翻倍让 vol_20d 吸收翻倍。
>
> **Lessons 升格候选**: "single-atom geometric exhaustion 律 — 当一个 atom 的 4+ 代 first-/second-order 几何变体 (raw 仿射 / 跨窗 normalization / 非线性 wrap / 不对称 reference) 都失败时, 该 atom 已结构性饱和，需切换字段或聚合维度"

---

### T013 · sign-离散化 cross-section rank 普适性 [✗ DISPROVEN batch_060]

> [!failure]+ Thread 结论：hybrid Sign×|magnitude| 双向探针 0/2 admit + sign-magnitude 0.37 低相关不是家族律
>
> **Question**: F018 (Sign(overnight)×amount) 的 sign-magnitude 0.37 低相关是否 family-agnostic？hybrid `Mul(Sign(field_A), Abs(field_B))` 是否兑现新 alpha？
>
> **Answer**: 否。
> - **F018 0.37 是特定 happy accident** — sign 离散化对 cross-section rank 影响因字段组合差异巨大: (a) Sign(overnight)×amount: corr 0.37 admit; (b) Sign(close-direction)×turnover: corr 0.82 落 F022 cluster (b059 C005); (c) Sign(o)*Sign(i) 60d: ls_t<2 在 1d horizon noise-bound
> - **hybrid 双向探针 0/2 admit** (b060): C004 Sign(overnight)×|body| alpha_surv=0.27<0.30 floor; C005 Sign(intraday)×|gap| alpha_surv=0.09 critical + train_val_decay=10.88
> - **机理**: hybrid sign-side 退化为 ±1 只贡献方向, magnitude-side (|intraday body| 或 |overnight gap|) 仍嵌入 Barra vol_20d / turnover_20d basis — sign-side 互换不影响 magnitude-side 吸收度
>
> **Reserve 火种**:
> - b059 C005 `Sign((C-L)-(H-C)) 20d × turnover_5/60` — max_corr=0.824@F022 cluster ridge + incr_ic=0.0049 紧贴 reserve 决策档下界 → reserve (sign 离散化未脱 F022 cluster)
>
> **Lessons 升格候选**: "Mul(Sign(A),Abs(B)) 形式 alpha 由 |B| magnitude side 主导, sign(A) 仅贡献方向; alpha_surv 上限 ≈ pure |B| LHS"

---

### T014 · overnight/intraday autocorr atom (lag-1 持续性) [✗ DISPROVEN batch_066]

> [!failure]+ Thread 结论：autocorr atom 仍 vol_20d-locked
>
> **Question**: lag-1 autocorr `Corr(X, Ref(X,1), 20)` 作为 LHS 是否独立于 magnitude/sign-freq/magnitude-product？
>
> **Answer**: 否 — autocorr 是 ordinal 持续性度量 (Corr ∈ [-1,1] scale-free), 但 cross-section rank 仍 monotone-equivalent vol_20d (high-vol 名 institutional accumulation 集中, autocorr rank 与 vol_20d 共变)。
> - **C001** overnight autocorr × volume_60: alpha_surv=0.32 仅过 floor + max_corr=0.527@F002 borderline + incr_ic=-0.002 → reject
> - **C002** intraday autocorr × pe_60: ls_t=2.46 + max_corr=**0.13 库内最 clean** + 9/9 年 7 positive 但 alpha_surv=**0.06 critical** (vol_20d=5.77 + book_to_price=0.62 + ep_ratio=1.22 共吞噬) → reject (T003 disprove 复现)
>
> 复活路径仅 (a) minute-bar 数据 / (b) 长 horizon admission 标准。

---

### T015 · overnight return shape moment LHS (Skew/Kurt) [✗ DISPROVEN batch_066]

> [!failure]+ Thread 结论：形状 moment 不 P003-flip 但 P004-absorb (跨 3rd/4th 阶同律)
>
> **Question**: shape moment (Skew/Kurt of overnight_ret 20d, scale-free 4th-standardized) 是否与 magnitude moment 几何独立？
>
> **Answer**: regime stable 但 vol_20d-locked。
> - **C003** Skew × pb_60: ls_t=1.07 weak + sign_consistency=1.0 + 9/9 同号 (**不 P003-flip**) 但 alpha_surv=0.07 critical
> - **C006** Kurt × amount_120: ls_t=**3.22 本批最强** + mono=1.0 + horizon anti-decay (1d=0.024→20d=0.079) + sign_consistency=1.0 (**不 P003-flip**) 但 alpha_surv=0.07 + max_corr=0.602@F012 borderline + incr_ic=+0.006<0.015
>
> **Lessons 升格候选 — 形状 moment 边界律**: "Skew/Kurt 形状 moment 在 csi1000 train→val regime stable (不 P003-flip), 但 cross-section rank 与 vol_20d 仍 monotone-equivalent (P004 absorb 同律) — heavy-tailedness ↔ daily-vol covariation。跨阶证据: 3rd Skew (C003) + 4th Kurt (C006) 同律。"

---

### T016 · TsRank/Rank wrap of admitted atom [✗ DISPROVEN batch_066]

> [!failure]+ Thread 结论：Rank wrapper 仅 within-name normalization, 不脱 anchor cluster
>
> **C004** Rank(Mean(overnight_ret,5),60) × ps_60 — max_corr=**0.611@F010 borderline cluster** + incr_ic=**-0.005 reducer** + alpha_surv=0.03 critical → reject
>
> **机理**: Rank wrap 把 X 转换为 within-name historical 0-1 rank, cross-section ordering 与原 X 高度相关 (corr=0.61 with F010)。类比 lessons.md "Rank-preserving 单算子变体零增量律" 次级实例。

---

### T017 · 量价时序 covariance atom (Corr$volume × overnight_gap) [◉ ACTIVE — 2 reserve 火种]

> [!warning]+ Thread 进展：跨 batch 火种续命 (b066→b087), Barra-clean / library-clean 反向矛盾首兑现
>
> **Question**: Corr($volume, overnight_gap, N) within-name 时序 covariance atom 是否独立于 magnitude/sign-freq？Barra-clean (alpha_surv>1.0) 候选能否 admit？
>
> **Reserve 火种**:
> - [[batches/batch_066/candidates/C005|b066 C005]] `Corr($volume, overnight_gap_raw, 20) × Std($volume,60)` — alpha_surv=**1.16 库内首 candidate Barra residual IC > raw IC** + sign_consistency=1.0 + mono=1.0/1.0 + 9/9 年正; 但 IS 0.019 → OOS 0.009 (52% decay) + ls_t=1.26<2 + incr_ic=-0.001 + max_corr=0.461@F002 borderline → **reserve**
> - [[batches/batch_087/candidates/C001|b087 C001]] 长窗 + RHS swap `Corr($volume, overnight_gap, 60) × Mean($high-$low, 60)` — ic_oos=**0.032** (b066 强化 3.5×) + ls_t=1.77 + mono_oos=**1.00** + 9/9 年正 + IC anti-decay (IS=0.014→OOS=0.032) + horizon ladder 1d=0.032→20d=**0.073** + cum_ic_mdd=-2.77; 但 alpha_surv=0.20 < 0.30 floor (vol_20d_exp=17.78) + max_corr=0.45@F019 borderline + incr_ic=0.011 缺 F203 0.015 ~25% → **reserve**
>
> **Key finding (b066) — Barra-clean / library-clean 反向矛盾**: C005 alpha_surv=1.16 ✓ + max_corr=0.46 anchor cluster ✗; C002 max_corr=0.13 ✓ + alpha_surv=0.06 ✗ — **不存在双 clean 候选**。F002/F012 anchor cluster 占据 vol_20d-orthogonal subspace, "逃 vol_20d 必撞 anchor" 几何困境。验证 lessons.md "Barra-clean ≠ library-clean" 反向亦成立。
>
> **Key finding (b087) — RHS 选择 trade-off**: b066 RHS=Std(volume,60) (vol-magnitude basis 自然减除) → alpha_surv=1.16 但 ls_t<2; b087 RHS=Mean(H-L,60) (vol_20d basis 重新嵌入) → ls_t=1.77 但 alpha_surv=0.20。**不存在两端都满足的 RHS** — 真复活路径不是"换 RHS"而是: (a) Python OLS residualize on vol_20d (但 b071 路径 OOS sign-flip 风险); (b) evaluation policy 调长 horizon (本候选 20d IC=0.073 显著); (c) F019/F002/F012 anchor 退役。

---

## Known Failures

| Batch | Candidate | Pattern | 原因 |
|---|---|---|---|
| batch_025 | C003 | 20d Corr(overnight, intraday) | sign_flip |
| batch_027 | C001-C003 | intraday mean 镜像 (5d/3d/vw) | F009 已吸收 intraday |
| batch_048 | C001/C002/C004/C005 | 各种 ratio + 同字段跨窗口 + 共 RHS | 见 T004/T006/T008 |
| batch_049 | C001-C005 | 共 RHS=overnight_5 / signed×magnitude 脱 LHS | T008 + T009 |
| batch_058 | C002/C003/C006 | intraday body sign / sign-product 20d / close-pos 60d | T003/T011/T012 |
| batch_059 | C001/C003/C006 | circ_mktcap_60 RHS Barra 撞 / sign-product 60d / center=close-pos 仿射 | dead RHS endpoint 升格 |
| batch_060 | C001-C005 | 4 代 close-position + hybrid sign×magnitude | T012 EXHAUSTED + T013 DISPROVEN |
| batch_066 | C001-C006 | autocorr / Skew / Rank wrap / Kurt | T014 / T015 / T016 全 vol_20d-locked |
| batch_080 | C001-C005 | volume_delta / abs() / range / Sign(intraday) 60d / 加速度 | T011 axis 6 fresh atom 全失败 (1 reserve C006) |
| batch_087 | C002 | overnight/intraday body ratio TsRank-60 standalone | 撞 F003 0.828 — P008 escape 不能 standalone |
| batch_087 | C003 | signed-flow Rank-60 rank-diff × num_trades_60 | 共 amount denominator 撞 F012 0.586 cluster |
| batch_087 | C004 | \|overnight\| Rank-60 × num_trades_60 | sign_flip + decay=-14.78 catastrophic |
| batch_087 | C005 | Cov(overnight, intraday, 20) × amount_120 | **0.927 near_dup F023 — Cov ≈ Mean of product 等价律新升格** |
| batch_087 | C006 | num_trades×\|Δret\|/amount TsRank-60 | sign_flip catastrophic + max_corr=0.13 库最 clean 但 OOS dead — "库 clean ≠ tradable alpha" 反例 |

---

## Lessons (本方向贡献至 lessons.md)

- **数学结构吸收律**：F_parent = A − B 被 admit 后, pure A / pure B 镜像必为线性组合 → 先做代数展开
- **aggregation > correlation**：cross-section 稳健性上 aggregation 优于 Corr
- **rank-diff > ratio**：incr_ic 13× 优势 (rank 空间不受分母小值放大)
- **rank-diff 设计 7 条硬约束** (本方向 b048+b049 证据贡献, 升格 lessons.md "Rank-Diff Geometry")
- **RHS 共振饱和动态**：每 admit 一个 rank-diff 就消耗一个 RHS 类目
- **L1 vs L2 vol 冗余**：csi1000 日频低 kurt 样本 Mean|ret| ≈ sqrt(Σret²)
- **Barra-clean ≠ library-clean** (反向亦成立, b066)
- **single-atom geometric exhaustion 律** (T012 升格候选): 4+ 代几何变体都失败 → atom 结构性饱和
- **形状 moment 边界律** (T015 升格候选): 不 P003-flip 但 P004-absorb (3rd/4th 阶同律)
- **hybrid Sign×|magnitude| 律** (T013 升格候选): alpha_surv 上限 ≈ pure |B| LHS
- **Cov ≈ Mean of product 数学等价律** (b087 升格候选): csi1000 daily zero-mean stationary 下 `Cov(X,Y,N) ≈ Mean(XY,N)` — 应升格 Phase 1 generator AST 自检第 9 条 (与 P024 同律)
- **Forbidden Patterns rate/delta 作 weight 同律** (b080 C001 升格候选): rate/delta 作 weight (非 standalone) 也 default-skip
- **Sub_inside_CsRank 加速度 vol_20d-locked 律** (b080 C005 升格候选): 同字段不同窗口的代数差仍 vol_20d 二阶载体

---

## Related

- 🟢 [[intraday_price_formation]] (saturated) — F003 overnight gap 上游字段；F020 anti-anchor cluster 锁死该方向 rank-diff 泛化
- 🟡 [[ohlc_temporal_aggregation]] (productive) — F019 higher-moment LHS 同律；F007 corr=0.708@F009
- 🟢 [[microstructure_illiquidity]] (productive) — rank-diff 范式发源地 (F015/F016)
- 🟡 [[gap_acceptance_structure]] (productive) — F020 higher-moment LHS 跨家族复现

---

## Narrative Log

> [!quote]+ 2026-05-03 · [[batches/batch_087/judge|batch_087]] · zero admit (1 reserve) · T011 DISPROVEN-comprehensive + T017 火种续命 · status `productive → saturated`
> admit=0 / reserve=1 (C001) / reject=5。
> - **C001 T017 reserve 跨 batch 火种续命** (b066→b087): Corr-60 长窗 + RHS axis swap, ic_oos=0.032 强化 3.5× + ls_t=1.77 + mono=1.00 + 9/9 年正 + horizon ladder 1d→20d 0.032→0.073, 但 alpha_surv=0.20 + max_corr=0.45 + incr_ic=0.011 三 borderline 联立。
> - **T011 axis DISPROVEN-comprehensive** (≥10 atom 跨 form 实证): b080+b087 累计跨 magnitude/ratio/signed-flow/Cov/TsRank wrap/standalone 全失败。Thread `[✓ ANSWERED b059] → [✗ DISPROVEN-comprehensive b087]`。
> - **C005 Cov ≈ Mean of product 等价律新升格 lessons 候选**: csi1000 daily zero-mean stationary 下 `Cov(X,Y,N) ≈ Mean(XY,N)`, F023 admit 让所有 Cov(o,i,N) atom 自动 cross-section near_dup (本批 0.927)。应升格 Phase 1 generator AST 自检第 9 条, 与 P024 同律。
> - **C006 "库 clean ≠ tradable alpha" 反例**: max_corr=0.13 库最 clean + 库内 F012/F022/F024 三 cluster 全独立, 但 train→val sign-flip + decay=-0.06。
> - **T017 RHS 选择 trade-off 新发现**: 不存在两端都满足的 RHS — 真复活路径是 Python OLS residualize / horizon policy 调长 / anchor 退役。
> - **MT budget**: cumulative 480 → 486 · direction 51 → 57 · bucket high (search_adjusted=medium)
>
> **Operations**　direction `productive → saturated` · T011 升级 DISPROVEN-comprehensive · T017 ACTIVE 保持 (2 reserve 火种) · zero_admit_streak 4→5 · **触 consolidation_trigger 候选** (rounds_since=6 临近 10, lessons 升格累积 3 条) · commit `[mine] batch_087 | overnight_intraday_split | admits=0 reserves=1 rejects=5`

> [!quote]- 2026-05-02 · [[batches/batch_080/judge|batch_080]] · zero admit (1 reserve) · T011 ANSWERED-saturated
> admit=0 / reserve=1 (C006) / reject=5。T011 axis 6 fresh atom 全受阻。仅 C006 (60d turnover-weighted overnight × Std(num_trades,60)) alpha_surv=0.61 PASS + ls_t=4.06 + 9/9 年正 + cum_mdd=-1.37 浅, 但 4 anchor cluster (F002/F012/F018/F023) + incr_ic=0.0098 缺 F203 0.015 ~33% → reserve。**"逃 vol_20d 必撞 anchor cluster" 几何困境再实证**。新升格 lessons 候选: rate/delta 作 weight 同律 (C001) + Sub_inside_CsRank 加速度 vol_20d-locked (C005)。MT 438→444 · direction 45→51。

> [!quote]- 2026-05-01 · [[batches/batch_066/judge|batch_066]] · zero admit (1 reserve) · T014/T015/T016 DISPROVEN + T017 ANSWERED-partial
> admit=0 / reserve=1 (C005) / reject=5。**核心律 — "逃 vol_20d 必撞 library anchor" 几何困境**: 6/6 候选 dominant_style=vol_20d。关键反例对照 C002 (max_corr=0.13 ✓ + alpha_surv=0.06 ✗) vs C005 (alpha_surv=1.16 ✓ + max_corr=0.46 ✗) — 不存在双 clean 候选。形状 moment 边界律 (3rd Skew + 4th Kurt 同律 不 P003-flip 但 P004 absorb) 升格 lessons 候选。整阶 moment family vol_20d-locked (跨阶律): 1st Mean (admit) → 2nd Std/Var (P003 flip) → 3rd/4th Skew/Kurt (P004 absorb) → Corr autocorr (P004 absorb)。MT 354→360 · direction 39→45。

> [!quote]- 2026-04-28 · [[batches/batch_060/judge|batch_060]] · zero admit (1 reserve) · T012 EXHAUSTED + T013 hybrid DISPROVEN
> admit=0 / reserve=1 (C006) / reject=5。close-position atom 4 代 LHS 设计全军覆没 (跨窗 normalization / Power-cubed / from-peak)。P003 higher-moment regime sign-flip 在 close-position cubic moment 首次实证 (C002 IS=+0.018 OOS=-0.022)。hybrid Sign×|magnitude| 双向探针 0/2 admit (C004/C005)。**single-atom geometric exhaustion 律** 升格 lessons 候选。priority `high → medium`。MT 318→324。

> [!quote]- 2026-04-25 · [[batches/batch_059/judge|batch_059]] · 9th admit · T011 ANSWERED + T013 新建
> **9th admit · F023 gap_body_magnitude_amount_rd_20**。C004 `Sub(CsRank(Mean((O-Ref(C,1))*(C-O),20)), CsRank(Mean($amount,60)))` ic_oos=0.044 ICIR=0.37 ls_t=4.89 mono=1.0/1.0 + 9/9 年正 + IC anti-decay + cum_ic_mdd=-1.72 + worst_q=+0.0019 永正 + incr_ic=0.018 → admit。**关键转折**: T011 sign-only 三次受阻; magnitude × magnitude 直乘在 20d 短窗兑现 — direction 第 9 admit + 第一个 second-order interaction。新 dead RHS 类目 circ_mktcap_60 (C001/C003 双重验证 Barra 撞)。MT 312→318。

> [!quote]- 2026-04-25 · [[batches/batch_058/judge|batch_058]] · 8th admit · T011/T012 双新 thread 启动
> **8th admit · F022 close_position_amount_accel_rd_20**。C004 `Sub(CsRank(Mean((C-L)/(H-L),20)), CsRank(amount_5/60))` IC_OOS=0.029 + alpha_surv=0.43 (本批最高) + style_r²=0.13 (本批最低) + max_corr=0.283@F006 + incr_ic=0.012 + cum_ic_mdd=-1.03 + worst_q=+0.0017 永正 → admit。LHS atom (C-L)/(H-L) 是结构性 vol_20d 正交 atom 兑现。MT 306→312。

> [!quote]- 2026-04-25 · [[batches/batch_049/judge|batch_049]] · F018 admit (rank-diff 第 4 次跨家族兑现)
> admit=1 / reject=5。**hypothesis 复活条件 "overnight sign frequency" 首次 ANSWERED** (T010) — C006 → F018 (ic_oos=0.051 ls_t=5.98 incr_ic=0.015 cum_mdd=-1.53 整库最浅)。Sign 聚合 vs magnitude 聚合**几何正交** (corr 0.37)。T008 rank-diff RHS 共享律 ANSWERED (硬约束第 6 条)。T009 DISPROVEN。**触 Phase 5 consolidation 升格 lessons.md "Rank-Diff Geometry"**——4 次跨家族证据链完整。

> [!quote]- 2026-04-25 · [[batches/batch_048/judge|batch_048]] · F017 admit (rank-diff 复活)
> admit=1 / reserve=1 / reject=4。**rank-diff 范式 2 次跨家族兑现** — C003 → F017 (ic_oos=0.054 incr_ic=0.027 9/9yr+)。T004 ratio + T006 同字段跨窗口 DISPROVEN。**rank-diff 设计硬约束三条升格** (≥1 独立 raw field / 不单一窗口差 / 同批 LHS 共享 anchor rule)。

> [!quote]- 2026-04-21 · [[batches/batch_027/judge|batch_027]] · productive → saturated
> admit=0 / reject=3。Intraday 镜像 3/3 reject (corr 0.65–0.89@F009 + incr_ic 负)。**定论**: F009 = overnight − intraday 数学结构已吸收 intraday 分量。

> [!quote]- 2026-04-21 · [[batches/batch_025/judge|batch_025]] · DOUBLE ADMIT 首批
> admit=2 / reject=1。F009 spread (ic=+0.047, ls_t=5.18) + F010 persistence (**ls_t=7.50 整库记录**)；C003 20d Corr sign_flip。核心: overnight 段携带独立于 intraday 的 persistent signal；aggregation 有效, correlation 不稳。
