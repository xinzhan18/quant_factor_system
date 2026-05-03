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

### T011 · overnight×intraday joint magnitude/sign 共方向交互 [✗ DISPROVEN batch_087]

> [!success]+ Thread 结论：magnitude-weighted product 救活短窗 — sign-only 路径在 1d primary_horizon 下封闭
>
> **Question**: `Mean(Sign(overnight) * Sign(intraday), N)` 共方向频率作为 LHS（非单边 sign 而是 product），在 cross-section rank-diff 几何下能否产生独立于 F009 (overnight-intraday spread magnitude) 与 F018 (overnight 单边 sign) 的新 alpha？窗口长度对 cross-section rank-order 的影响如何？
>
> **Answer**: **sign-only 路径在 1d primary_horizon 下根本性受阻** (b058 C003 短窗 mono 退化 + b058 C005 长窗 alpha_surv 不足 + b059 C003 跨 family RHS 1d IC=0.0016 → 20d IC=0.030 horizon mismatch)。**magnitude-weighted product (gap × body 直乘,无 Sign) 在 20d 短窗下兑现 admit** (b059 C004) — magnitude weighting 区分共振强弱日,让 cross-section rank 在 csi1000 1d horizon 显著清洁。**核心律**: `Sign(o)*Sign(i)` 是 long-horizon (10d-20d) 现象,1d 主 horizon 下被 noise 主导;`(o)*(i)` (保 magnitude) 在 1d horizon 下 ls_t=4.89 + mono=1.0 + anti-decay。
>
> **Evidence trail**:
> - [[batches/batch_058/candidates/C003|batch_058 C003]]　Mean(Sign(o)*Sign(i),20) × close/MA60, ic_oos=0.024 ls_t=1.09 **mono_oos=0.40 + Q5 反向**, max_corr=**0.216@F009 (本批最 library-clean)** + incr_ic=0.017 → **reject** (CP03 weak: ls_t<2 + rank-order 破坏；意外 library-clean 但信号强度不足)
> - [[batches/batch_058/candidates/C005|batch_058 C005]]　Mean(Sign(o)*Sign(i),60) × Mean(H/L,60), ic_oos=0.039 ls_t=1.91 **mono=0.9/0.9 完美** + 9/9 年逐年强化, alpha_surv=0.26<0.30 floor + max_corr=0.49@F021 + incr_ic=0.011<0.015 (F203) → **reserve**
> - [[batches/batch_059/candidates/C003|batch_059 C003]]　Mean(Sign(o)*Sign(i),60) × circ_mktcap_60, hard_gate fail (ic_oos=0.0016 < 0.008 + oos_decay=0.147), 但 ic_by_horizon 1d=0.0016 → 20d=0.030 + 9/9 年正 + cum_ic_mdd=-3.38 极浅 → **reject** (sign-product 在 1d horizon noise-bound;长 horizon 信号在 evaluation policy 不被 rewarded)
> - [[batches/batch_059/candidates/C004|batch_059 C004]]　Mean( (o)*(i), 20 ) × Mean(amount,60), ic_oos=**0.044** ICIR=**0.37** ls_t=**4.89** mono=1.0/1.0 + 9/9 年同号 + IC anti-decay (OOS>IS) + cum_ic_mdd=-1.72 库内最浅之一 + worst_quarter=+0.0019 永正 + max_corr=0.575@F012 + incr_ic=**0.018** (远超 F203 0.015) → **admit (gap_body_magnitude_amount_rd_20)**
> - [[batches/batch_080/candidates/C006|batch_080 C006]]　Mean(overnight × turnover_rate, 60) × Std($num_trades,60), ic_oos=**0.0295** ICIR=**0.300** ls_t=**4.06** mono=0.9 + 9/9 年同号正 (0.024-0.036) + cum_ic_mdd=-1.37 极浅 + worst_quarter=+0.0116 永正 + horizon anti-decay (1d=0.030→20d=0.078) + alpha_surv=0.61 PASS + max_corr=0.56@F018 borderline + 4 anchor cluster (F002+F012+F018+F023) + incr_ic=**0.0098 < F203 0.015 borderline gate** → **reserve** (T011 axis 60d turnover-weighted 镜像延伸 F023; 等 F018/F023 退役或 horizon policy 调整)
> - [[batches/batch_080/candidates/C001|batch_080 C001]]　overnight × volume_pct_delta 20d × num_trades_60, hard_gate fail (sign_flip + decay=-5.16 catastrophic) → **reject** (Forbidden Patterns rate/delta 作 weight 同律实证)
> - [[batches/batch_080/candidates/C002|batch_080 C002]]　|overnight| × turnover 20d × pcf_total_ttm_60, ic_oos=-0.040 mono=-0.9 9/9 年负 stable + cum_mdd=-67.5 深, alpha_surv=0.27 < 0.30 floor → **reject** (abs() 退化 vol-magnitude 载体 + RHS P010 macro 撞)
> - [[batches/batch_080/candidates/C003|batch_080 C003]]　overnight × intraday range 20d × dividend_yield_60, ic_oos=-0.008 ls_t=0.14 essentially zero → **reject** (range vs body 几何同位)
> - [[batches/batch_080/candidates/C004|batch_080 C004]]　overnight × Sign(intraday) 60d × peg_ratio_60, hard_gate fail ic_oos=0.0066<0.008 + ls_t=1.59 weak → **reject** (60d sign-asymmetric horizon mismatch, 同 b059 C003 律)
> - [[batches/batch_080/candidates/C005|batch_080 C005]]　Sub_inside_CsRank: Sub(Mean(overnight,5),Mean(overnight,20)) × num_trades_120, ls_t=3.62 mono=1.0 + 9/9 年正 但 alpha_surv=0.143 critical + max_corr=0.56@F010 + incr_ic=-0.003 → **reject** (加速度 vol_20d 二阶载体, 与 b066 T015/T014 同律)
>
> **Key finding (b080 update)**: **T011 axis 6 fresh atom 全失败 (1 reserve borderline) — ANSWERED-saturated 升格**. magnitude-weighted product 在 csi1000 daily-bar cross-section 上仅 (overnight × intraday body 短窗 20d × amount_60 RHS) 一种几何 admitted (F023 b059), 其他 weighting field (volume_delta / abs() / intraday range / Sign(intraday) / 加速度 / turnover 60d) 均 vol_20d-locked 或 horizon-mismatch 或 4 anchor cluster 占据. 仅 60d turnover-weighted overnight (b080 C006) 全 metric 绿但 incr_ic=0.0098 距 F203 0.015 borderline gate ~33% 缺口 → reserve 火种. **核心律**: T011 axis 已结构性饱和.
>
> **Key finding (b087) — DISPROVEN-comprehensive (n=10+ atom)**: b087 4 fresh probes (C002 standalone TsRank ratio / C003 signed flow density rank-diff / C004 |overnight| Rank-60 rank-diff / C005 Cov(o,i,20)) 再 0/4 admit, 累计 b080+b087 ≥ 10 fresh atom 跨 form (magnitude / ratio / signed-flow / Cov / TsRank wrap / standalone) 全失败. T011 axis 真饱和升级到 DISPROVEN-comprehensive. **C005 新升格 lessons 候选**: csi1000 daily zero-mean stationary return-pair 下 `Cov(X,Y,N) ≈ Mean(X*Y,N) - Mean(X,N)*Mean(Y,N) ≈ Mean(X*Y,N)` (Mean(return) ≈ 0 让 cov 二阶项消失), F023 (Mean of product) admit 后所有 Cov(overnight, intraday, N) atom 自动 cross-section near_dup (本批 C005 实测 0.927 与 F023). 与 P024 In-batch denominator equivalence 同律, 应升格 Phase 1 generator AST 自检第 9 条.

> **Key finding (b059)**: **magnitude weighting 是短窗 sign-product 失败的解药** — `(gap)*(body)` 直乘比 `Sign(gap)*Sign(body)` 频率在 csi1000 1d primary_horizon 下信噪比高 ~4×。原 "20d → 60d 长窗清洁 cross-section rank" 律 (b058 发现) 被 b059 C003 反例修正 — 长窗在跨 family RHS 下也未必脱 noise。**新升格 lessons 候选**: "sign-only product LHS 在 csi1000 1d evaluation 下 family-agnostic 不达标;magnitude-weighted product 在 20d 短窗即可 admit"。

---

### T012 · intraday close-position-in-range Mean LHS — 4 代几何穷尽 [✗ DISPROVEN batch_060]

> [!failure]+ Thread 结论：close-position atom 4 代 LHS 设计全部失败 — 几何已彻底饱和
>
> **Question**: `Mean((C-L)/(H-L+ε), N)` close-position-in-range 一阶矩 LHS（与 F006 upper_shadow 5d / F019 body_ratio Std / F021 upper_shadow_disp Std 几何位置不同）能否在 cross-section rank-diff 几何下兑现独立 alpha？vol_20d 正交性是否与窗口长度负相关？**仿射变体 (center-position = close-position − 1/2) 是否构成新 atom？sign 离散化 (Sign(C-L vs H-C)) 是否脱 close-position cluster？跨窗 range normalization / 非线性 wrap / 不对称 reference 是否突破 close-position 几何饱和？**
>
> **Answer**: F022 admit 后 4 代 LHS 设计 (raw 仿射 / 跨窗 Min-Max normalization / Power-cubed 非线性 wrap / from-peak 不对称 reference) **全部失败**。close-position atom 在 csi1000 daily-bar 几何上已结构性饱和。具体 4 代失败机理: 仿射变体 (center-position) corr=0.93@F022 hard_gate near_dup;跨窗 normalization 让 atom 几何脱 F022 (max_corr<0.40) 但 incr_ic ≤0 + ls_t essentially zero (cross-section IC 健康但 long-short 不投资);Power-cubed 非线性 wrap 触发 train→val sign-flip catastrophic (P003 higher-moment regime sign-flip 律扩展到三阶 power moment);from-peak 不对称 reference cross-section 信号塌缩 noise (ic_oos hard_gate fail)。
>
> **Evidence trail**:
> - [[batches/batch_058/candidates/C004|batch_058 C004]]　Mean((C-L)/(H-L),20) × amount_5/60_ratio, ic_oos=0.029 ls_t=1.56 **mono_oos=0.6 + Q5 上升 + 9/9 年同号区间窄稳定**, **alpha_surv=0.43 (本批 admit 最高) + style_r²=0.13 (本批最低) + max_corr=0.283@F006 + incr_ic=0.012 + cum_mdd=-1.03 (本批最浅) + worst_quarter 永正** → **admit (close_position_amount_accel_rd_20)**
> - [[batches/batch_058/candidates/C006|batch_058 C006]]　Mean((C-L)/(H-L),60) × H/L_60_geo, ic_oos=0.044 ls_t=1.52 mono=0.3/0.9, **alpha_surv=0.19 (vol_20d exposure=44.15 本批最高极值) + max_corr=0.47@F021 + incr_ic=0.011<0.015 (F203)** → **reject** (60d 长窗放大 vol_20d 吞噬)
> - [[batches/batch_059/candidates/C001|batch_059 C001]]　Mean((C-mid)/(H-L),20) × Mean(circ_mktcap,60), hard_gate fail (ic_oos=-0.0004 + oos_decay=0.081), **alpha_surv=23.19 极端 + style_r²=0.57 + log_circ_cap=0.64** → **reject** (RHS=circ_mktcap_60 直接撞 Barra log_circ_cap style 完全吞噬)
> - [[batches/batch_059/candidates/C002|batch_059 C002]]　Mean((C-mid)/(H-L),20) × amount_60/20 减速比, ic_oos=-0.027 mono_is=0.0 / mono_oos=-1.0 ls_t=-2.24 **9/9 年同号负 + Q5 大幅下跌 "avoid worst" + max_corr=0.349@F006 + 与 F022 corr=0.07 仿射独立** → **reserve** (CP03 borderline + IS mono=0 异常 + cum_ic_mdd=-60 深;**库内首次 negative 方向 close-position rank-diff**)
> - [[batches/batch_059/candidates/C005|batch_059 C005]]　Mean(Sign((C-L)-(H-C)),20) × turnover_5/60, ic_oos=0.026 ls_t=1.88 mono=0.9/0.7 **max_corr=0.824@F022 (cluster ridge) + incr_ic=0.0049 紧贴 0.005 reserve 决策档下界** → **reserve** (CP05 high 决策档:incr_ic ∈ [0.003, 0.005];**sign 离散化未脱 F022 cluster**——与 b049 sign-magnitude corr=0.37 形成对比,验证 sign vs magnitude 几何正交律不可机械泛化)
> - [[batches/batch_059/candidates/C006|batch_059 C006]]　Mean((C-mid)/(H-L),20) × turnover_5/60, hard_gate fail (near_dup max_corr=0.933@F022) → **reject** (center=close_pos 仿射,差常数 1/2,CsRank 后等价)
> - [[batches/batch_060/candidates/C001|batch_060 C001]]　20d cross-window range norm × volume_CV, ic_oos=0.011 ls_t=0.26 Mono OOS 0.30 崩 + **incr_ic=-0.010 P006 reducer** → **reject** (跨窗 normalization 让 LHS 脱 F022 仿射但 cross-section IC 被库内 F015-F023 提前吸收)
> - [[batches/batch_060/candidates/C002|batch_060 C002]]　Power-cubed close-position 20d × pb_60/20, **IS=+0.018 OOS=-0.022 ls_t=-2.77 train→val sign-flip catastrophic** + alpha_surv=0.08 + cum_ic_mdd=-57.95 → **reject** (P003 higher-moment regime sign-flip 在 close-position cubic moment 首次实证复现)
> - [[batches/batch_060/candidates/C003|batch_060 C003]]　from-peak 不对称 reference 20d × ps_60, hard_gate fail ic_oos=0.0040 → **reject** (T012(c) DISPROVEN — 单边 channel reference cross-section 信号塌缩 noise)
> - [[batches/batch_060/candidates/C006|batch_060 C006]]　60d cross-window range norm × Std(turnover,60), ic_oos=0.019 ls_t=0.39 essentially zero + alpha_surv=0.93 健康 + **incr_ic=+0.0025 本批唯一正向** + max_corr=0.37@F017 cluster-clean → **reserve** (本批唯一火种;ls_t 不投资但 alpha_surv 与 incr_ic 双绿,等 F017 退役或 evaluation policy 调整后重测)
>
> **Key finding (b058)**: close-position **20d (alpha_surv=0.43) vs 60d (alpha_surv=0.19)** — 窗口翻倍让 vol_20d 吸收翻倍。
>
> **Key finding (b059)**: **close-position atom 仿射变体几何穷尽** — center-position `(C-mid)/(H-L)` = close-position − 1/2,CsRank 对常数偏移不敏感 (b059 C006 corr=0.933@F022 hard_gate),C001/C002 的 RHS 替换让原始 LHS-RHS 联合 corr 降到 0.07 (与 F022) 但单独 LHS rank-order 信号弱 (C002 IS mono=0 → OOS mono=-1.0 emergent regime),不构成稳健新 atom。**sign 离散化 (Sign(C-L vs H-C))** 在 csi1000 cross-section 上与 close-position-Mean corr=0.82 强相关 (b049 F018 sign-magnitude 0.37 弱相关不可泛化)。
>
> **Key finding (b060) — 4 代 LHS 设计全军覆没**:
> - **跨窗 normalization (Min/Max)** (C001 20d / C006 60d): 让 LHS 脱 F022 仿射 (max_corr<0.40) 但 incr_ic ≤+0.0025 (本批最高仅 C006) + ls_t essentially zero (0.26-0.39),cross-section IC 健康但 long-short portfolio 不投资 → C001 reject (incr_ic=-0.010 P006 reducer trap),C006 reserve (唯一火种,等 F017 退役或 horizon policy 调整)
> - **Power-cubed 非线性 wrap** (C002 `Mean(Power(close_pos-0.5, 3), 20)`): train→val sign-flip catastrophic (IS=+0.018 OOS=-0.022 ls_t=-2.77) + alpha_surv=0.08 critical + cum_ic_mdd=-57.95 灾难深渊。**P003 higher-moment regime sign-flip 跨 family 硬律在 close-position cubic 几何首次实证复现** — Power(p=3) 三阶 power-mean 与已记载的 Std/Var/Skew/Kurt 二/三阶聚合律同构
> - **from-peak 不对称 reference** (C003 `(Max($high,20)-C)/Max($high,20)`): hard_gate fail ic_oos=0.0040 < 0.008 floor,csi1000 cross-section 上 from-peak 分布过于均匀无显著区分度 → T012(c) DISPROVEN
> - **Lessons 升格候选**: "single-atom geometric exhaustion 律 — 当一个 atom 的 4+ 代 first-/second-order 几何变体 (raw 仿射 / 跨窗 normalization / 非线性 wrap / 不对称 reference) 都失败 (max_corr 各代 ≤0.50 但 incr_ic ≤0 + alpha_surv 在 vol_20d 吸收下衰减) 时,该 atom 已结构性饱和,需切换字段或聚合维度,不能继续微调"
>
> **Final state (b060 EXHAUSTED)**: 4 代 LHS 设计全部失败 → close-position atom 在本方向 closed。仅 C006 (60d cross-window normalization × Std(turnover,60)) reserve 为未来火种 (alpha_surv=0.93 + incr_ic=+0.0025 双绿),等 F017 退役或 evaluation policy 调整后重测。

---

### T013 · sign-离散化 cross-section rank 普适性 [✗ DISPROVEN batch_060]

> [!failure]+ Thread 部分结论：hybrid Sign×|magnitude| 路径 DISPROVEN
> **Question**: csi1000 1d primary_horizon 下,sign-离散化 LHS (Sign(close偏向) / Sign(o)*Sign(i)) 在 cross-section rank-diff 几何下是否普遍未脱 magnitude cluster？b049 F018 (Mean(Sign(overnight)) × amount) 的 sign-magnitude corr=0.37 低相关是否为特定字段组合 (overnight + amount) 的 happy accident,而非 family-agnostic 律？sign 离散化在哪些字段组合下保留正交性,哪些下塌陷为 magnitude 镜像？**hybrid Sign×|magnitude| (即 Mul(Sign(field_A), Abs(field_B)) 形式) 是否兑现 sign-magnitude 混合的新独立 alpha?**
>
> **Evidence trail**:
> - [[batches/batch_058/candidates/C003|batch_058 C003]]　Sign(o)*Sign(i) 20d × close/MA60, mono=0.4 reject (sign-product 短窗 cross-section rank 退化)
> - [[batches/batch_058/candidates/C005|batch_058 C005]]　Sign(o)*Sign(i) 60d × H/L_60, mono=0.9 reserve (长窗清洁但 alpha_surv 不足)
> - [[batches/batch_059/candidates/C003|batch_059 C003]]　Sign(o)*Sign(i) 60d × circ_mktcap_60, hard_gate fail (1d horizon noise-bound + Barra 吞噬)
> - [[batches/batch_059/candidates/C005|batch_059 C005]]　Sign((C-L)-(H-C)) 20d × turnover_5/60, **max_corr=0.824@F022 (close-position cluster ridge)** + incr_ic=0.0049 → reserve
> - [[batches/batch_060/candidates/C004|batch_060 C004]]　Sign(overnight) × |intraday body| 20d × pe_60, ic_oos=0.017 ls_t=2.23 **alpha_surv=0.27 < 0.30 floor** + incr_ic=-0.0016 → reject (hybrid 形式不脱 vol_20d 吸收)
> - [[batches/batch_060/candidates/C005|batch_060 C005]]　Sign(intraday) × |overnight gap| 20d × turnover_60, ic_oos=0.023 ls_t=0.47 **alpha_surv=0.09 critical** + train_val_decay=10.88 极端 → reject (镜像方向无救,sign-side 互换不影响 magnitude-side Barra absorption)
>
> **Key finding (b059)**: **F018 sign-magnitude 0.37 低相关不是家族律** — 不同字段组合下 sign 离散化对 cross-section rank 的影响差异巨大: (a) `Sign(overnight)` × amount: corr 0.37 (b049 F018 admit);(b) `Sign(close-direction)` × turnover: corr 0.82 (b059 C005, 落 F022 cluster);(c) `Sign(o)*Sign(i)` 60d: ls_t<2 在 1d horizon noise-bound。
>
> **Key finding (b060) — hybrid 路径 DISPROVEN**: **hybrid Sign×|magnitude| 双向探针 0/2 admit** (C004 + C005)。镜像 sign-side 互换 (overnight vs intraday) 都 alpha_surv < 0.30 rank-diff floor。**机理**: hybrid 形式 sign-side 退化为 ±1 只贡献方向信息,但 **magnitude-side (|intraday body| 或 |overnight gap|) 仍嵌入 Barra vol_20d / turnover_20d basis** — 即使 RHS 是 fresh fundamental (pe_60 / turnover_60),LHS 内部 magnitude × sign mix 让 Barra basis 嵌入,无法脱 absorption。
>
> **Lessons 升格候选 (b060)**: "Mul(Sign(field_A), Abs(field_B)) where (A, B) ∈ {(overnight, intraday), (intraday, overnight)} 形式在 csi1000 cross-section 上 alpha 由 |B| magnitude side 主导,sign(A) side 仅贡献方向 — Barra residual 吸收度 ≈ |B| 单独之吸收度;hybrid 形式 alpha_surv 上限 ≈ pure |B| LHS 之 alpha_surv (库内 F019 body_disp_pricevol_rank_diff_20 alpha_surv=0.16 / F012 amihud_illiq_20d alpha_surv=0.41 等参考)"。
>
> **Final state (b060)**: T013 hybrid Sign×|magnitude| 路径 **DISPROVEN**。原始 question (sign-discretization 普适性) 部分保留 — sign-only 路径在 T011 已封闭,hybrid 路径在 b060 已 DISPROVEN,sign 离散化在本方向几何已 closed。
>
> **下一步**: T013 整体待退役。仅 C005 reserve (b060) 等 F017 退役或 horizon policy 修订后重测。本方向 sign-discretization 探索预算耗尽,不再投同形式候选。

---

### T014 · overnight/intraday autocorr atom (lag-1 持续性) [✗ DISPROVEN batch_066]

> [!failure]+ Thread 结论：autocorr atom 在 csi1000 daily-bar cross-section 上仍 vol_20d-locked
> **Question**: lag-1 autocorr (overnight_ret 与 intraday_ret 的 within-name 时序持续性, Corr(X, Ref(X,1), 20)) 作为 LHS atom 是否携带独立于 magnitude (F009/F010) / sign-freq (F018) / magnitude-product (F023) 的新 alpha?
>
> **Answer**: **autocorr atom 形式上 ordinal 持续性度量 (Corr ∈ [-1,1] scale-free) 但 cross-section rank 仍 monotone equivalent to vol_20d** — stocks with persistent overnight directionality 在 csi1000 上倾向于是 high-vol 名 (institutional accumulation 集中在小盘 vol-extreme), autocorr cross-section 排名与 vol_20d 排名共变.
>
> **Evidence trail**:
> - [[batches/batch_066/candidates/C001|batch_066 C001]]　Corr(overnight_ret, Ref(overnight_ret,1), 20) × Mean($volume,60), ic_oos=0.010 ls_t=1.92 mono_oos=1.0, alpha_surv=0.32 仅过 rank_diff floor 0.30, max_corr=0.527@F002 borderline + incr_ic=-0.002<0.015 (F203) → **reject** (P006 reducer borderline; vol_20d=7.20 absorption)
> - [[batches/batch_066/candidates/C002|batch_066 C002]]　Corr(intraday_ret, Ref(intraday_ret,1), 20) × Mean($pe_ratio,60), ic_oos=0.014 ls_t=2.46 mono_oos=1.0 + 9/9 年 7 positive + max_corr=**0.131@F002 库内最 clean** + incr_ic=+0.005 weak positive, alpha_surv=**0.06 critical** → **reject** (vol_20d=5.77 + book_to_price=0.62 + ep_ratio=1.22 共吞噬; T003 disprove "intraday body=random walk" 复现)
>
> **Key finding (b066)**: **autocorr atom 库内最 clean (C002 max_corr=0.13) 但 alpha_surv=0.06 critical** — autocorr 是 ordinal 持续性度量本质仍嵌入 vol_20d basis (intraday autocorr ~0 时只能借 vol_20d 形成 cross-section signal). T014 双侧探针 (overnight + intraday) 0/2 admit, atom 在 csi1000 daily-bar 1d primary_horizon 下封闭. 复活路径仅 (a) minute-bar 数据 / (b) 长 horizon admission 标准.

---

### T015 · overnight return shape moment LHS (Skew/Kurt) [✗ DISPROVEN batch_066]

> [!failure]+ Thread 结论：形状 moment 不 P003-flip 但 P004-absorb (跨 3rd/4th 阶 同律)
> **Question**: shape moment (Skew/Kurt of overnight_ret 20d, scale-free 4th-standardized) 作为 LHS 是否与 magnitude moment (F019 body Std / F020 gap Std) 几何独立? P003 higher-moment regime sign-flip 律是否在形状 moment 上同样作用?
>
> **Answer**: **形状 moment regime stable 不 sign-flip (sign_consistency=1.0 + 9/9 年同号), 但 cross-section rank 仍 monotone equivalent to vol_20d (P004 absorb 同律)** — heavy-tailed 股票 ↔ high-vol 股票, Kurt cross-section rank 与 vol_20d rank 共变.
>
> **Evidence trail**:
> - [[batches/batch_066/candidates/C003|batch_066 C003]]　Skew(overnight_ret, 20) × Mean($pb_ratio,60), ic_oos=0.023 mono_oos=0.9 ls_t=1.07 weak + sign_consistency=1.0 + 9/9 年 7 positive (**不 P003-flip**), alpha_surv=**0.07 critical** (str_1m=1.99 + vol_20d=5.77 双吞噬), max_corr=0.323@F002 → **reject** (CP03 weak + CP04 P004 absorb)
> - [[batches/batch_066/candidates/C006|batch_066 C006]]　Kurt(overnight_ret, 20) × Mean($amount,120), ic_oos=0.024 ls_t=**3.22 本批最强** mono_oos=1.0 + horizon anti-decay (1d=0.024→20d=0.079) + sign_consistency=1.0 + 9/9 年 8 positive + 2023 IC=0.030 强势 + cum_ic_mdd=-2.23, alpha_surv=**0.07 critical** (vol_20d=9.49) + max_corr=0.602@F012 borderline + incr_ic=+0.006<0.015 (F203 borderline gate) → **reject** (CP04 P004 absorb + CP05 borderline cluster + F203 borderline gate)
>
> **Key finding (b066) — 形状 moment 边界律 (lessons 升格候选)**:
> - **不 P003-flip**: P003 raw return Std/Var 在 train→val regime 翻号是因为 train (低利率成长) 与 val (利率上行价值回归) 的横截面 vol-magnitude 重排; **形状 moment (Skew/Kurt) 度量分布形状, 在 regime 切换中形状稳定** (csi1000 个股 daily return 总是右偏 + 高峰度, 不随 regime drift). C003+C006 双侧 sign_consistency=1.0 + 9/9 年同号验证.
> - **仍 P004-absorb**: cross-section rank 与 vol_20d 仍 monotone-equivalent (heavy-tailedness ↔ daily-vol covariation). C003+C006 alpha_surv=0.07 双低 + dom=vol_20d. 跨阶证据: 3rd Skew (b066 C003) + 4th Kurt (b066 C006) 同律.
> - **升格 lessons 候选**: "Skew/Kurt of raw return 形状 moment 在 csi1000 train→val regime stable (不 P003-flip), 但 cross-section rank 与 vol_20d 仍 monotone-equivalent (P004 absorb 同律) — heavy-tailedness ↔ daily-vol covariation. 跨阶证据: 3rd (b066 C003) + 4th (b066 C006) 同律."
>
> **Final state (b066 DISPROVEN)**: 形状 moment LHS 在 csi1000 daily-bar 几何上虽 regime-stable 但被 P004 vol_20d basis absorbed. 仅 minute-bar / 长 horizon evaluation 可能复活, 当前 daily-bar 下封闭.

---

### T016 · TsRank/Rank wrap of admitted atom [✗ DISPROVEN batch_066]

> [!failure]+ Thread 结论：Rank wrapper 不脱 anchor cluster, 仅 within-name normalization
> **Question**: Rank(Mean(overnight_ret,5), 60) wrapper 把 F010 admitted atom 转换为 within-name historical rank (0-1), 是否生成新的 cross-section ordering, 独立于原 atom?
>
> **Answer**: **Rank wrapper 仅是 within-name normalization, 不脱 F010 anchor cluster** — Rank/TsRank 把 X 转换为 within-name historical 0-1 rank, cross-section ordering 与原 X 高度相关.
>
> **Evidence trail**:
> - [[batches/batch_066/candidates/C004|batch_066 C004]]　Rank(Mean(overnight_ret,5), 60) × Mean($ps_ratio,60), ic_oos=0.021 ls_t=1.53 mono_oos=0.7, max_corr=**0.611@F010 borderline cluster** + incr_ic=**-0.005 negative library reducer** + alpha_surv=**0.03 critical** (vol_20d=9.24 极值) → **reject** (CP05 cluster + reducer + CP04 P004 absorb)
>
> **Key finding (b066)**: **Rank wrap 是 "Rank-preserving 单算子变体零增量律" 的次级实例** — 不像 Linear/SignedPower/Sigmoid 等纯 monotone 变换 cross-section 完全保留 (max_corr=1.000), Rank wrap 通过 within-name normalization 改变 cross-section ordering 一些, 但仍 corr=0.61 with F010. 类比 lessons.md "Rank-preserving 单算子变体零增量律".

---

### T017 · 量价时序 covariance atom (Corr$volume × overnight_gap) [◉ ACTIVE]

> [!warning]+ Thread 进展：Barra-clean 反例首兑现 (1 reserve), 但 ls_t_oos 不投资
> **Question**: Corr($volume, overnight_gap, 20) within-name 时序 covariance atom 是否独立于 magnitude (F023) / sign-freq (F018) 维度? Barra-clean (alpha_surv>1.0) candidate 是否能 admit?
>
> **Evidence trail**:
> - [[batches/batch_066/candidates/C005|batch_066 C005]]　Corr($volume, overnight_gap_raw, 20) × Std($volume,60), ic_oos=0.009 weak ls_t=1.26 + alpha_surv=**1.16 库内首 candidate Barra residual IC > raw IC** + sign_consistency=1.0 + mono=1.0/1.0 完美 + 9/9 年正 (0.004-0.033) + cum_ic_mdd=-1.66 浅; train→val IC decay 0.019→0.009 (52% 衰减) + ls_t_oos=1.26 < 2 + incr_ic=-0.001 + max_corr=0.461@F002 borderline (F002=0.46 / F012=0.38 / F018=0.37 三方向 ~0.4 cluster) → **reserve** (CP03 weak + CP05 cluster + 但 CP04 极致 Barra-clean + CP06 9/9 年同号 sign consistency=1.0)
>
> **Key finding (b066) — Barra-clean 与 library-clean 反向矛盾**:
> - C005 alpha_surv=**1.16** Barra cleanest in batch + max_corr=0.46 borderline anchor cluster
> - C002 max_corr=**0.13** library cleanest in batch + alpha_surv=0.06 critical
> - **不存在双 clean 候选** — F002/F012 anchor cluster 占据 vol_20d-orthogonal subspace, "逃 vol_20d 必撞 anchor" 几何困境
> - 验证 lessons.md "Barra-clean ≠ library-clean" 律反向亦成立
>
> **下一步**: T017 仅 reserve 火种待 evaluation policy 调长 horizon (10d-20d C005 IC 显著上升 0.016-0.025 + ICIR 0.17-0.27) 或 F002/F012 anchor 退役后重测.
>
> - [[batches/batch_087/candidates/C001|batch_087 C001]]　Sub(CsRank(Corr($volume, overnight_gap, **60**)), CsRank(Mean($high-$low, 60))) — 长窗 + RHS axis swap. ic_oos=**0.032** (b066 C005 0.009 → b087 C001 0.032 显著强化) + icir_oos=0.224 + ls_t=1.77 (still <2) + mono_oos=**1.00 完美** + 9/9 年正 (0.006-0.033) + IC anti-decay (IS=0.014 → OOS=0.032) + horizon ladder 1d=0.032→20d=0.073 强长 horizon 真信号 + cum_ic_mdd=-2.77, **alpha_surv=0.20 < rank_diff floor 0.30 (vol_20d_exp=17.78 dominant) + max_corr=0.45@F019 borderline + incr_ic=0.011 < F203 borderline gate 0.015 缺口 25%** → **reserve** (T017 跨 batch 火种续命第 2 reserve)
>
> **Key finding (b087) — Corr atom 长窗 + RHS swap 兑现强信号但 alpha_surv 退化**: C001 ic_oos 较 b066 C005 强化 ~3.5×, ls_t 1.26→1.77 但 alpha_surv 1.16→0.20 大幅退化 — RHS 从 Std(volume,60) (vol-magnitude basis 自然减除) 换为 Mean(H-L,60) (cross-section vol_20d basis 重新嵌入). **机理**: Mean(H-L,N) 是 daily 振幅 cross-section level, 与 vol_20d basis 共线; Std(volume,60) 虽 vol-magnitude 但 cross-section 上是 secondary basis. **新发现**: T017 axis 的 RHS 选择决定 alpha_surv vs ls_t 的 trade-off — 不存在两端都满足的 RHS, 真正复活路径不是"换 RHS"而是 (a) Python OLS residualize on vol_20d (但 b071 此路径 OOS sign-flip 风险高); (b) evaluation policy 调长 horizon 评估 (本候选 20d IC=0.073 显著); (c) F019/F002/F012 anchor 退役.

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
| batch_059 | C001 | `Sub(CsRank(Mean((C-mid)/(H-L),20)),CsRank(Mean($circ_market_cap,60)))` | hard_gate fail (ic_oos=-0.0004 + oos_decay=0.081) — circ_mktcap_60 RHS 直接撞 Barra log_circ_cap (alpha_surv=23.19 极端) — 升格 dead RHS endpoint 类目 |
| batch_059 | C003 | `Sub(CsRank(Mean(Sign(o)*Sign(i),60)),CsRank(Mean($circ_market_cap,60)))` | hard_gate fail (ic_oos=0.0016 + oos_decay=0.147) — sign-product 60d 在 csi1000 1d primary_horizon noise-bound (但 20d horizon IC=0.030 显示长 horizon alpha 真实存在) + circ_mktcap RHS Barra 吞噬 |
| batch_059 | C006 | `Sub(CsRank(Mean((C-mid)/(H-L),20)),CsRank(turnover_5/60))` | hard_gate fail (near_dup max_corr=0.933@F022) — center=(C-mid)/(H-L) 是 close-position 仿射 (差常数 1/2),CsRank 后等价 |
| batch_060 | C001 | `Sub(CsRank(Mean((C-Min(L,20))/(Max(H,20)-Min(L,20)),20)),CsRank(Std(V,20)/Mean(V,20)))` | CP03 ls_t_oos=0.26 + Mono IS=1.0→OOS=0.30 崩 + CP05 incr_ic=-0.010 P006 reducer (库已饱和到该 direction alpha 子空间) |
| batch_060 | C002 | `Sub(CsRank(Mean(Power((C-L)/(H-L)-0.5, 3),20)),CsRank(pb_60/pb_20))` | **P003 higher-moment regime sign-flip 在 close-position cubic moment 首次实证** — IS=+0.018 OOS=-0.022 ls_t=-2.77 + alpha_surv=0.08 + cum_ic_mdd=-57.95 — 升格 lessons: "Power(close_pos, 3+) Mean 形式 train→val regime 翻号" |
| batch_060 | C003 | `Sub(CsRank(Mean((Max(H,20)-C)/Max(H,20),20)),CsRank(ps_60))` | hard_gate fail ic_oos=0.0040 < 0.008 — **T012(c) from-peak 不对称 reference DISPROVEN** — 单边 channel reference cross-section 信号塌缩 noise |
| batch_060 | C004 | `Sub(CsRank(Mean(Sign(O-Ref(C,1))*Abs(C-O),20)),CsRank(pe_60))` | T013 hybrid Sign×\|magnitude\| 探针 — alpha_surv=0.27 < 0.30 floor + incr_ic=-0.0016 + ls_t=2.23 borderline — hybrid 形式 magnitude-side 嵌入 vol_20d basis,sign-side 退化无法脱 Barra |
| batch_060 | C005 | `Sub(CsRank(Mean(Sign(C-O)*Abs(O-Ref(C,1)),20)),CsRank(turnover_60))` | T013 hybrid 镜像 — alpha_surv=0.09 critical + ls_t=0.47 + train_val_decay=10.88 极端 — sign-side 互换 (overnight↔intraday) 无救,**T013 hybrid 路径 DISPROVEN** |
| batch_066 | C001 | `Sub(CsRank(Corr(overnight_ret, Ref(overnight_ret,1), 20)),CsRank(Mean($volume,60)))` | T014 overnight autocorr × volume — alpha_surv=0.32 仅过 rank_diff floor 0.30 + max_corr=0.527@F002 borderline + incr_ic=-0.002<0.015 (F203) — autocorr atom 仍 vol_20d 几何载体 |
| batch_066 | C002 | `Sub(CsRank(Corr(intraday_ret, Ref(intraday_ret,1), 20)),CsRank(Mean($pe_ratio,60)))` | T014 mirror — intraday autocorr × PE — **库内最 clean** (max_corr=0.13) + ls_t=2.46 + 9/9 年 7 positive 但 alpha_surv=**0.06 critical** (vol_20d=5.77 + book_to_price=0.62 + ep_ratio=1.22 共吞噬) — autocorr atom 也是 vol_20d 几何载体 |
| batch_066 | C003 | `Sub(CsRank(Skew(overnight_ret,20)),CsRank(Mean($pb_ratio,60)))` | T015 形状 moment — **不 P003-flip** (sign_consistency=1.0 + 9/9 年 7 positive) **但 P004 absorb** — alpha_surv=0.07 + ls_t=1.07 weak (str_1m=1.99 + vol_20d=5.77 双吞噬) |
| batch_066 | C004 | `Sub(CsRank(Rank(Mean(overnight_ret,5),60)),CsRank(Mean($ps_ratio,60)))` | T016 Rank wrap — max_corr=**0.611@F010 borderline cluster** + incr_ic=**-0.005 negative reducer** + alpha_surv=0.03 critical — TsRank wrapper 不脱 F010 anchor cluster |
| batch_066 | C006 | `Sub(CsRank(Kurt(overnight_ret,20)),CsRank(Mean($amount,120)))` | T015 mirror — Kurt 形状 moment — ls_t=**3.22 本批最强** + mono=1.0 + 9/9 年 8 positive + horizon anti-decay (1d=0.024→20d=0.079) **不 P003-flip** 但 alpha_surv=0.07 + max_corr=0.602@F012 borderline + incr_ic=+0.006<0.015 (F203 borderline gate) — **形状 moment cross-section rank 仍 vol_20d-locked** |
| batch_087 | C002 | `TsRank(Div(Sub($open,Ref($close,1)),Add(Abs(Sub($close,$open)),0.0001)),60)` | P008 escape standalone — overnight gap / |intraday body| ratio TsRank 60d — ic_oos=0.0017<0.008 + max_corr=0.828@F003 (single overnight geometry overlap) — P008 escape 不能在 overnight family standalone 兑现, 必须配 rank-diff + 跨段 RHS basis |
| batch_087 | C003 | `Sub(CsRank(Rank(Div(Mul($volume,Sub($close,Ref($close,1))),Add($amount,0.0001)),60)),CsRank(Mean($num_trades,60)))` | T017 cross-axis signed flow density — ic_oos=-0.0033<0.008 sub-threshold 反向 + max_corr=0.586@F012 borderline cluster (共享 amount denominator) — signed-flow 60d Rank wrap 不构成 cross-section 独立轴 |
| batch_087 | C004 | `Sub(CsRank(Rank(Mean(Abs(Div(Sub($open,Ref($close,1)),Ref($close,1))),20),60)),CsRank(Mean($num_trades,60)))` | T011 axis fresh RHS — \|overnight_ret\| 20d Mean → Rank 60d rank-diff × num_trades_60 — sign_flip catastrophic (train -0.0002 / val +0.0032 翻号) + ic≈0 + decay=-14.78 — P008 escape 不能拯救 magnitude form, vol_20d 二阶载体律 b066 复现 |
| batch_087 | C005 | `Sub(CsRank(Cov(Sub($open,Ref($close,1)),Sub($close,$open),20)),CsRank(Mean($amount,120)))` | hard_gate fail near_dup max_corr=**0.927@F023** — **Cov ≈ Mean of product 数学等价律新升格** (csi1000 daily zero-mean stationary return-pair 下 Cov(X,Y,N) ≈ Mean(X*Y,N), F023 已 admit 让所有 Cov(o,i,N) atom 必 near_dup) |
| batch_087 | C006 | `TsRank(Div(Mul($num_trades,Abs(Sub($close,Ref($close,1)))),Add($amount,0.0001)),60)` | T017 P008 escape mirror — num_trades × \|Δret\| / amount TsRank 60d — train→val regime sign-flip catastrophic (train -0.0176 / val +0.0011) + decay=-0.06 + max_corr=**0.133@F022 库最 clean** 但 OOS dead — "库 clean ≠ tradable alpha" 反例 |

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

> [!quote]+ 2026-05-03 · [[batches/batch_087/judge|batch_087]] · zero admit (1 reserve) · T011 DISPROVEN-comprehensive + T017 火种续命 · status `productive → saturated`
> **zero admit · T011 axis 4 fresh probes 再 0/4 admit 累计 ≥10 atom DISPROVEN-comprehensive + T017 Corr-60 长窗 RHS-swap 第 2 reserve 火种续命** · admit=0 / reserve=1 (C001) / reject=5 (C002/C003/C004/C005/C006)
>
> - **C001 T017 reserve 跨 batch 火种续命**: `Sub(CsRank(Corr($volume, overnight_gap_raw, 60)), CsRank(Mean(H-L, 60)))` — b066 C005 (Corr 20d × Std(volume,60) reserve, alpha_surv=1.16 但 ls_t=1.26<2 + IC 52% decay) 长窗 + RHS axis swap 兑现尝试. ic_oos=**0.032** 较 b066 强化 ~3.5× + ls_t=1.77 (still <2) + mono_oos=**1.00** + 9/9 年正 + IC anti-decay (IS=0.014 → OOS=0.032) + horizon ladder 1d→20d IC 0.032→0.073 长 horizon 真信号 + cum_ic_mdd=-2.77 浅, **alpha_surv=0.20 < rank_diff floor 0.30 (vol_20d_exp=17.78 dominant) + max_corr=0.45@F019 borderline + incr_ic=0.011 < F203 borderline gate 0.015 缺 25%** → **reserve** (4 项 risk flags 联立但 9/9 年同号 + horizon ladder + anti-decay 三好信号火种续命).
> - **T017 axis RHS 选择 trade-off (新发现)**: b066 C005 RHS=Std(volume,60) (vol-magnitude basis 自然减除) → alpha_surv=1.16 但 ls_t=1.26<2; b087 C001 RHS=Mean(H-L,60) (cross-section vol_20d basis 重新嵌入) → ls_t=1.77 但 alpha_surv=0.20. **不存在两端都满足的 RHS** — T017 axis 复活路径不是"换 RHS"而是 (a) Python OLS residualize on vol_20d basis (但 b071 此路径 OOS sign-flip 风险); (b) evaluation policy 调长 horizon (本候选 20d IC=0.073 显著); (c) F019/F002/F012 anchor 退役.
> - **T011 axis DISPROVEN-comprehensive (≥10 atom 跨 form 实证)**: b080 6 + b087 4 = 累计 ≥ 10 fresh atom 跨 magnitude / ratio / signed-flow / Cov / TsRank wrap / standalone 形式全失败. C002 (overnight/intraday body ratio TsRank-60 standalone) 撞 F003 0.828 max_corr; C003 (signed flow density Rank-60 rank-diff) 共享 amount denominator 撞 F012 0.586 cluster + 信号反向; C004 (|overnight| Rank-60 rank-diff) sign_flip + decay=-14.78 catastrophic; C005 (Cov(o,i,20)) 0.927 near_dup F023. T011 thread 状态升级 `[✓ ANSWERED batch_059] → [✗ DISPROVEN-comprehensive batch_087]`.
> - **C005 Cov ≈ Mean of product 等价律新升格 lessons 候选**: csi1000 daily zero-mean stationary return-pair 下 `Cov(X,Y,N) = Mean(XY,N) - Mean(X,N)*Mean(Y,N) ≈ Mean(XY,N)` (Mean(daily return) ≈ 0 让 cov 二阶项消失). F023 (Mean of product) admit 让所有 Cov(overnight, intraday, N) atom 自动 cross-section near_dup (本批实测 0.927). 应升格 Phase 1 generator AST 自检第 9 条, 与 P024 In-batch denominator equivalence 同律.
> - **C006 P008 escape "库 clean ≠ tradable alpha" 反例**: max_corr=**0.133@F022 库最 clean** + 库内 F012/F022/F024 三 cluster 全独立, 但 train→val regime sign-flip (train -0.0176 / val +0.0011) + decay=-0.06 catastrophic. 形态独立性不预测 OOS sign 稳定性, 与 b066 T014 形状 moment / b071 6/6 sign-flip 同律 (alpha_surv 顶级 PASS 但 OOS sign-flip).
> - **Status `productive → saturated`**: 14 rounds 9 admits + 连续 3 round zero-admit (b066/b080/b087) + 5/6 thread closed + 仅 T017 reserve 火种 — saturated 触发条件 (连续 2+ batch reject > 80%, 已超 3 倍).
> - **MT budget**: cumulative 480 → **486** · direction 51 → **57** · bucket `high` (search_adjusted=medium)
>
> **Operations**　direction `productive → saturated` (LLM 在 frontmatter status field 已翻 saturated) · `priority: medium` 保持 · T011 `[✓ ANSWERED batch_059] → [✗ DISPROVEN-comprehensive batch_087]` (累计 ≥10 fresh atom 跨 form 全失败) · T017 `[◉ ACTIVE]` 保持 (跨 batch 火种续命 b066→b087, 第 2 reserve) · zero_admit_streak 4→5 · 不触 calibration trigger (本批 reserve C001 不满足 over-rejection 4 条件: max_corr=0.45 不<0.30 + alpha_surv=0.20 不达 0.30 floor) · **触 consolidation_trigger 候选** (rounds_since_consolidation=5+1=6 临近 10 阈值, zero_admit_streak=5 + 多方向 saturated + lessons 升格累积 3 条: T011 comprehensive saturation + Cov ≈ Mean of product 等价律 + "库 clean ≠ tradable alpha" 又一反例) · Phase 4 archive 后 commit message: `[mine] batch_087 | overnight_intraday_split | admits=0 reserves=1 rejects=5`

> [!quote]- 2026-05-02 · [[batches/batch_080/judge|batch_080]] · zero admit (1 reserve) · T011 ANSWERED-saturated + T011 axis exhaustion 升格律
> **zero admit · T011 唯一未 disprove thread 6 fresh atom 全失败 + 1 reserve borderline** · admit=0 / reserve=1 (C006) / reject=5 (C001/C002/C003/C004/C005)
>
> - **T011 (magnitude-weighted product) ANSWERED-saturated 升格**: 6 fresh atom geometries 全部受阻. 历史 admit 路径仅 (overnight × intraday body 短窗 20d × amount_60 RHS) → F023 (b059); b066 Barra-clean reserve C005 (Corr atom); 本批 C006 60d turnover-weighted overnight reserve (ic_oos=0.0295 ls_t=4.06 mono=0.9 9/9 年正 cum_mdd=-1.37 浅 worst_q 永正 alpha_surv=0.61 PASS — 但 max_corr=0.56@F018 borderline + incr_ic=0.0098<0.015 F203 borderline gate + 4 anchor cluster F002 0.48 / F012 0.50 / F018 0.56 / F023 0.40). 其他 5 fresh weighting (volume_delta / abs() × turnover / intraday range / Sign(intraday) 60d / 短-长加速度 Sub_inside_CsRank) 全失败. **T011 axis 已结构性饱和**.
> - **C001 sign_flip catastrophic + Forbidden Patterns 实证**: `Mul(overnight, volume_pct_delta)` 短窗 20d → train +0.00064 / val -0.00330 sign_flip + decay=-5.16 极端. **rate/delta 形式作 weight (而非 standalone) 也 default-skip** — 即使 weight 形式 cross-section 上 noise-dominated 让 overnight signal 被 noise 主导. 升格 lessons: "Forbidden Patterns rate/delta 作 weight 同律".
> - **C002 完美 negative-direction 但 alpha_surv 不足**: `Mean(|overnight| × turnover, 20)` × pcf_total_ttm_60 → ic_oos=-0.040 mono=-0.9 ls_t=-2.57 9/9 年负 stable + cum_mdd=-67.5 深, **alpha_surv=0.27 < 0.30 floor** (vol_20d_exp=38.4 dominant + ep_ratio=0.49 + turnover_20d=4.93 共吞噬) + RHS 撞 P010 macro 真饱和.
> - **C005 Sub_inside_CsRank 加速度 vol_20d-locked 律**: `Sub(CsRank(Sub(Mean(overnight,5),Mean(overnight,20))),CsRank(Mean($num_trades,120)))` — Sub 在 CsRank 内部不违反 Rank-Diff 7-rule constraint #3 (该律仅禁外部 Sub(CsRank(X_5),CsRank(X_20))). LHS = overnight 短-长加速度. ic_oos=+0.020 ls_t=3.62 mono=1.0 完美但 **alpha_surv=0.143 critical** + incr_ic=-0.003 P006 reducer + max_corr=0.56@F010 borderline. **机理**: 同字段不同窗口的代数差仍 monotone-equivalent vol_20d basis (high-vol stocks 短期 overnight extreme >> 长期 mean → 加速度 rank 与 vol_20d rank 共变). 与 b066 T015 形状 moment / b066 T014 autocorr atom 同律 — 加速度也是 vol_20d 二阶载体. **新升格 lessons 候选**.
> - **C006 = 本批唯一火种 + 4 anchor cluster 占据**: 60d turnover-weighted overnight (T011 b059 20d 镜像延伸) — alpha_surv=0.61 PASS + 9/9 年正 + cum_mdd=-1.37 浅 + worst_quarter=+0.012 永正 + ls_t=4.06 强劲 + mono=0.9, 但 cross-section 几何撞 4 anchor cluster (F002 0.48 + F012 0.50 + F018 0.56 + F023 0.40), incr_ic=0.0098 缺 F203 borderline gate 0.015 ~33%. 等 F018 / F023 退役或 evaluation policy 调长 horizon 后重测.
> - **"逃 vol_20d 必撞 anchor cluster" 几何困境再实证**: C006 alpha_surv=0.61 PASS ✓ + max_corr=0.56 borderline ✗ → 既 vol_20d-locked 又 anchor cluster; C005 alpha_surv=0.14 critical ✗ + max_corr=0.56 borderline ✗ → 双失守; C002 alpha_surv=0.27 ✗ + max_corr=0.46 ✗ → 双失守. b066 律泛化, 仅 T017 reserve (Barra-clean alpha_surv=1.16 + max_corr=0.46) 是唯一突破方向, 等 horizon policy 调整.
> - **MT budget**: cumulative 438 → 444 · direction 45 → 51 · bucket `medium` (raw=high direction.exposure=1.0 满 + family=0.918 高位, search_adjusted ≈ 0.30 → low/medium)
>
> **Operations**　direction `productive` 保持但显著 saturated 化 (Phase 4 archive 后建议下批 LLM 翻 saturated) · `priority: medium` 保持 · T011 `[◉ ACTIVE → ANSWERED-saturated batch_080]` (唯一未 disprove thread 也已 saturated, 仅 C006 reserve 火种) · T017 `[◉ ACTIVE]` 保持 · zero_admit_streak 3→4 · 不触 calibration trigger (本批 reserve 是合理 borderline 决策, C006 max_corr=0.56 + incr_ic=0.0098 不满足 over-rejection signature) · rounds_since_last_consolidation 7→8 (距 10 阈值 2 批) — **临近 consolidation trigger**, 若下 2 批仍 zero_admit 应优先触 consolidation (lessons 升格 T011 axis exhaustion + Sub_inside_CsRank vol_20d-locked + Forbidden Patterns rate/delta weight 同律 三条) · Phase 4 archive 后 commit message: `[mine] batch_080 | overnight_intraday_split | admits=0 reserves=1 rejects=5`

> [!quote]- 2026-05-01 · [[batches/batch_066/judge|batch_066]] · zero admit · T014/T015/T016 DISPROVEN + T017 ANSWERED-partial (1 reserve)
> **zero admit · 4 thread 全在 vol_20d basis 撞墙 (T014/T015/T016 DISPROVEN) + Barra-clean 反例首兑现 (T017 reserve)** · admit=0 / reserve=1 (C005) / reject=5 (C001/C002/C003/C004/C006)
>
> - **核心律 — "逃 vol_20d 必撞 library anchor" 几何困境**: csi1000 daily-bar cross-section 上 6/6 候选 dominant_style=vol_20d. 关键反例对照: **C002 max_corr=0.13 库内最 clean ✓ + alpha_surv=0.06 vol_20d 吞噬 ✗**; **C005 alpha_surv=1.16 Barra cleanest ✓ + max_corr=0.46@F002 anchor cluster ✗**. **不存在双 clean 候选** — F002/F012 anchor cluster 占据 vol_20d-orthogonal subspace. 验证 lessons.md "Barra-clean ≠ library-clean" 律反向亦成立.
> - **T014 (autocorr atom) DISPROVEN**: overnight + intraday 双侧 lag-1 autocorr (Corr(X, Ref(X,1), 20)) 0/2 admit. C001 (overnight): alpha_surv=0.32 仅过 rank_diff floor + max_corr=0.527 borderline + incr_ic=-0.002 (P006 reducer borderline). C002 (intraday): ls_t=2.46 + max_corr=0.13 库内最 clean + 9/9 年 7 positive 但 alpha_surv=0.06 critical (vol_20d=5.77 + book_to_price=0.62 + ep_ratio=1.22 共吞噬). **机理**: stocks with persistent overnight directionality 在 csi1000 倾向于 high-vol 名 (institutional accumulation 集中小盘), autocorr cross-section 排名与 vol_20d 共变. **T003 disprove "intraday body=random walk" 复现** (intraday autocorr ~0 时只能借 vol_20d basis 形成 cross-section signal).
> - **T015 (形状 moment Skew/Kurt) DISPROVEN — 形状 moment 边界律 lessons 升格候选**: C003 (Skew, ls_t=1.07 weak alpha_surv=0.07) + C006 (Kurt, ls_t=**3.22 本批最强** mono=1.0 + horizon anti-decay 1d=0.024→20d=0.079 + 9/9 年 8 positive 但 alpha_surv=0.07 + max_corr=0.602@F012 borderline + incr_ic=+0.006<0.015) 双侧探针. **关键发现**: 形状 moment **不 P003-flip** (sign_consistency=1.0 + 9/9 年同号验证, 形状 moment 度量分布形状, regime 切换中形状稳定) **但仍 P004 absorb** (heavy-tailedness ↔ daily-vol covariation, cross-section rank 仍 monotone-equivalent to vol_20d). **跨阶证据 (3rd Skew + 4th Kurt 同律)**.
> - **T016 (Rank/TsRank wrap) DISPROVEN**: C004 (Rank(overnight_5,60) × ps_60) max_corr=0.611@F010 borderline cluster + incr_ic=-0.005 negative reducer + alpha_surv=0.03. **机理**: Rank wrapper 是 within-name normalization 不改 cross-section ordering — F010 已 admit overnight_5 cross-section, Rank wrap 后只缩放但 rank 几乎保留. 类比 lessons.md "Rank-preserving 单算子变体零增量律" 次级实例.
> - **T017 (Corr atom) ANSWERED-partial (1 reserve)**: C005 (Corr($volume, overnight_gap_raw, 20) × Std($volume,60)) alpha_surv=**1.16 库内首 candidate Barra residual IC > raw IC** + sign_consistency=1.0 + mono=1.0/1.0 完美 + 9/9 年正; 但 train→val IC decay 0.019→0.009 (52% 衰减) + ls_t_oos=1.26 < 2 + incr_ic=-0.001 + max_corr=0.461@F002. **保留为火种**等 evaluation policy 调长 horizon (10d-20d IC 显著上升) 或 F002/F012 anchor 退役后重测.
> - **整阶 moment family vol_20d-locked (跨阶律)**: 1st Mean (F010/F011 admit, 本方向源头) → 2nd Std/Var (P003 sign-flip) → 3rd Skew (b066 C003 P004 absorb) → 4th Kurt (b066 C006 P004 absorb) → correlation moment autocorr/Corr (b066 C001/C002/C005 P004 absorb). operator family novelty 不解决 style 重表达, 形状 moment 边界律为 P003 与 P004 拼接补全的关键证据.
> - **Status 调整候选**: 鉴于 T012/T013 close-position+sign-discretization + T014/T015/T016 autocorr+Skew/Kurt+Rank wrap **6 thread 全 closed** + T017 仅 reserve 火种 + zero_admit_streak=6 (b061-b066 含跨方向 batch_063 ohlc_temporal_aggregation / batch_064 range_structure / batch_065 trend_residual_geometry), 信号设计层证据 ≥3 路径 cluster + 数据契约层 minute-bar 不可达, **触发双层 saturated 证据律**. 但 9 admit 历史 + T017 reserve, **不 dead** — 转 saturated 候选 (Phase 4 archive 后由 Python auto-status 或 LLM 在下批 narrative 翻).
> - **MT budget**: cumulative 354 → **360** · direction 39 → **45** · bucket `medium` (search_adjusted: C001/C005 low + C002/C003/C004/C006 medium) · 本批 6 candidates 全 hard_gate pass + raw bucket=high (direction.exposure=1.0 满 + family=0.918 高位)
>
> **Operations**　direction `productive` 保持 (待 Phase 4 status auto-update 或下批 LLM 翻 saturated) · `priority: medium` 保持 · T014 / T015 / T016 三 thread `[◉ ACTIVE] → [✗ DISPROVEN batch_066]` 一次性新建 + 关闭 · T017 `[◉ ACTIVE]` 部分 ANSWERED 保持 (1 reserve C005) · zero_admit_streak 5→6 · 不触 calibration trigger (本批无候选满足完整错杀 signature: max_corr<0.30 + incr_ic>0.010 + mono>0.8 + sign_consistency=1.0 五条件 — C002 仅满足 4/5, incr_ic=+0.005<0.010) · rounds_since_last_consolidation 6→7 (距 10 阈值 3 批) — 临近 consolidation trigger, 若下 3 批仍 zero_admit 应优先触 consolidation (lessons 升格 P003/P004 形状 moment 边界律 + autocorr P004 absorb + "逃 vol_20d 必撞 anchor" 律) · Phase 4 archive 后 commit message: `[mine] batch_066 | overnight_intraday_split | admits=0 rejects=5 reserves=1`

> [!quote]- 2026-04-28 · [[batches/batch_060/judge|batch_060]] · zero admit · T012 EXHAUSTED + T013 hybrid DISPROVEN
> **zero admit · T012 4 代 LHS 设计全军覆没 + T013 hybrid 双向探针 0/2 admit** · admit=0 / reserve=1 (C006) / reject=5 (C001/C002/C003/C004/C005)
>
> - **T012 EXHAUSTED · close-position atom 4 代 LHS 设计全军覆没**: F022 admit (b058) → b059 center-position 仿射 (corr=0.93 hard_gate near_dup) → b060 跨窗 normalization (C001 20d / C006 60d 改分母 scale) + Power-cubed 非线性 wrap (C002 train→val sign-flip catastrophic) + from-peak 不对称 reference (C003 hard_gate fail)。**4 代设计皆失败**: 跨窗 normalization 让 LHS 脱 F022 仿射但 incr_ic ≤+0.0025 + ls_t essentially zero;Power-cubed 触发 P003 higher-moment regime sign-flip 跨 family 硬律 (IS=+0.018 OOS=-0.022 ls_t=-2.77 + alpha_surv=0.08 + cum_ic_mdd=-57.95);from-peak cross-section 信号塌缩 noise (ic_oos=0.0040)。**Lessons 升格候选**: "single-atom geometric exhaustion 律 — 当一个 atom 的 4+ 代 first-/second-order 几何变体都失败时,该 atom 已结构性饱和,需切换字段或聚合维度,不能继续微调"。
> - **T013 hybrid Sign×|magnitude| DISPROVEN**: 双向探针 (C004 Sign(overnight)×|body| / C005 Sign(intraday)×|gap|) 镜像 sign-side 互换 0/2 admit。两候选 alpha_surv 0.27 / 0.09 都 < 0.30 rank-diff floor。**机理**: hybrid 形式 sign-side 退化只贡献方向信息但 **magnitude-side 仍嵌入 Barra vol_20d / turnover_20d basis** — sign-side 互换不影响 magnitude-side 吸收度。**T013 假说部分验证**: F018 (Sign(overnight) × amount) 的 sign-magnitude 0.37 低相关是 sign-source 与 RHS 跨 horizon 几何不同的特定 happy accident;hybrid 形式当 LHS 内部已 mix sign+magnitude 时,RHS 替换无救。
> - **C002 P003 复现升格**: Mean(Power(close_pos-0.5, 3), 20) — 三阶 power-mean 是 higher-moment LHS 等价形式,与 F019/F020 OHLC body / gap higher-moment 同律。csi1000 train (2015-2021 低利率成长) → val (2022-2023 利率上行价值回归) regime 切换在 close-position 三阶 power moment 上首次实证 sign-flip。**Lessons 候选**: "P003 higher-moment LHS regime sign-flip 跨 family 硬律扩展第 7 个 family — close-position cubic moment"。
> - **C006 reserve (本批唯一火种)**: 60d cross-window range normalization × Std(turnover,60),alpha_surv=0.93 健康 + incr_ic=+0.0025 唯一正向 + max_corr=0.37@F017 cluster-clean,但 ls_t=0.39 essentially zero (cross-section IC 健康但 long-short 不投资) + cum_ic_mdd=-8.82 偏深。等 F017 退役或 evaluation policy 调整后重测。
> - **direction-level alpha quality 趋势性衰减信号**: alpha_surv 中位数 b058=0.43 → b059=0.37 → b060=0.69 (表面回升因为 C001 vol_20d=28.74 极值 + C006 0.93 拉高,但 4/6 候选 alpha_surv<0.30 floor)。direction.score 0.84 历史新高 + cumulative 0.90 + exposure 满 → MT bucket 持续 high。
> - **Status 调整**: priority `high → medium`。close-position + sign-discretization 二大 thread 关闭,仅剩零碎探针空间 (second-order non-magnitude/non-sign 聚合 / 跨日 lag-shifted overnight 自相关 / amount/volume 衍生 avg trade price)。
> - **MT budget**: cumulative 318 → **324** · direction 33 → **39** · bucket `high` 持续 (search_adjusted ≈ 0.30 → low) · 本批 6 候选全 raw bucket=high (direction.exposure=1.0 满 + family score 0.901 高位)
>
> **Operations**　direction `productive` 保持 + `priority: high → medium` (close-position + sign 二大探索空间已尽,新角度需 second-order non-sign-non-magnitude 聚合/lag-shifted overnight/amount-derived avg-price 等零碎探针) · T012 `[◉ ACTIVE] → [✗ EXHAUSTED batch_060]` (4 代 LHS 设计皆败) · T013 `[◉ ACTIVE] → [✗ DISPROVEN-hybrid batch_060]` (hybrid 路径双向探针 0/2 admit) · zero_admit_streak 0→1 · 不触 calibration trigger (单批 zero,最近 3 批累计 admit=2,reserve/judged=28% 低于 40% 警戒) · 不触 consolidation trigger (rounds_since_last_consolidation=0+1 远 <10) · Phase 4 archive 后 commit message: `[mine] batch_060 | overnight_intraday_split | admits=0 rejects=5 reserves=1`

> [!quote]- 2026-04-25 · [[batches/batch_059/judge|batch_059]] · 9th admit · T011 ANSWERED + T013 新建
> **9th admit · T011 gap_body_magnitude_amount_rd_20** · admit=1 (C004) / reserve=2 (C002/C005) / reject=3 (C001/C003/C006)
>
> - **T011 ANSWERED · magnitude-weighted product 救活短窗**: C004 `Sub(CsRank(Mean((O-Ref(C,1))*(C-O),20)), CsRank(Mean($amount,60)))` ic_oos=**0.044** ICIR=**0.37** ls_t=**4.89** mono=1.0/1.0 完美 + 9/9 年同号正 (0.024-0.050,2023 IC=0.048 近年增强) + IC anti-decay (OOS 0.044 > IS 0.035) + cum_ic_mdd=**-1.72** 库内最浅之一 + worst_quarter_ic=**+0.0019 永正** + max_corr=0.575@F012 + incr_ic=**0.018** 远超 F203 0.015 borderline corr 阈值 → **admit**。**关键转折**: T011 sign-only path 在 b058 短窗 (mono 退化) + b058 长窗 (alpha_surv 不足) + b059 跨 family RHS (1d horizon noise-bound) 三次受阻;**magnitude × magnitude 直乘 (gap × body 乘积保留 magnitude)** 在 20d 短窗下兑现 — 这是 direction 第 9 个 admit + 第一个 second-order interaction (overnight × intraday joint magnitude,与 F009 spread / F018 sign-freq 几何正交)。
> - **T012 LHS atom 几何穷尽 (3 候选验证)**: center-position `(C-mid)/(H-L)` = close-position − 1/2 仿射,CsRank 后与 F022 corr=0.93 (b059 C006 hard_gate near_dup);仿射变体在 RHS 替换后 (C001 circ_mktcap_60 Barra 撞;C002 amount_60/20 倒置 IS mono=0 异常) 不构成稳健新 atom。**升格 lessons 候选**: "Phase 1 LHS 设计的有效绕开必须改 numerator 结构 / 分母 normalization,不能仅减常数"。
> - **T013 新建 (sign-离散化 cross-section rank 普适性)**: b059 C005 `Sign(C-L vs H-C) × turnover_5/60` corr=0.824@F022 (反例 b049 F018 sign-magnitude 0.37) → reserve。**关键发现**: F018 sign-magnitude 0.37 低相关不是家族律,是 (overnight + amount) 特定字段组合的 happy accident。sign 离散化保留正交性需 LHS atom 的 underlying drift 在 sign-space vs magnitude-space drivers <50% 重叠。
> - **新 dead RHS 类目 circ_mktcap_60**: C001 (Barra log_circ_cap exposure=0.64) + C003 (exposure=0.51) 双重验证 — 长窗 scale-free 市值类 RHS 在 rank-diff 几何下直接撞 Barra style → "**Barra-direct 字段不适合 rank-diff RHS**" 升格设计硬约束第 8 条。
> - **C002 reserve (库内首次 negative 方向 close-position rank-diff)**: ic_oos=-0.027 mono_oos=-1.0 完美 + 9/9 年同号负 + Q5 大幅下跌 "avoid worst" + max_corr=0.349@F006 + 与 F022 corr=0.07 仿射独立。**反向方向多样性候选**,但 IS mono=0 → OOS=-1.0 emergent regime + cum_ic_mdd=-60 深 + ls_t=-2.24 borderline 三压制。等待 RHS 替换 (vol_20d-orthogonal RHS) 后重评估。
> - **C005 reserve (sign 离散化 vs F022 仿射 cluster)**: max_corr=0.824@F022 + incr_ic=0.0049 落 CP05 high 档 reserve 决策档下界 (0.003-0.005)。验证 T013 假说 (sign 离散化在 close-direction 字段下塌陷为 close-position-Mean cluster)。
> - **MT budget**: cumulative 312 → **318** · direction 27 → **33** · bucket `high` (search_adjusted=0.505 → medium) · 本批 6 候选全 raw bucket=high (direction.exposure=1.0 满 + family=0.90 高位)
>
> **Operations**　direction `productive` 保持 + `priority: high` 保持 (本批 admit 强信号 + 第 9 admit + magnitude-product 新 thread 空间) · T011 `[◉ ACTIVE] → [✓ ANSWERED batch_059]` (sign-only 路径封闭, magnitude-weighted 路径兑现 admit) · T012 evidence trail 追加 (b059 C001/C002/C005/C006) 状态保持 ACTIVE 但 atom 几何已穷尽,需新 normalization 或非线性变换 · T013 新建 ACTIVE (sign-离散化 cross-section rank 普适性) · Python 在 Phase 4 backfill F{next} 链接

> [!quote]- 2026-04-25 · [[batches/batch_058/judge|batch_058]] · 8th admit · T011/T012 双新 thread 启动
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
