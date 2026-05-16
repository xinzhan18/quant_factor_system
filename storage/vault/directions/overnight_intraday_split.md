---
direction_tag: overnight_intraday_split
status: dead
priority: medium
rounds: 18
admits: 9
last_batch: batch_094
last_admits: []
last_goal: 'Round 94 — reserve revival pool #3 (rank-diff axis escape via b080/C006
  跨 b091 finding 合成, calibration finding/013 续命). direction status=saturated, zero_admit_streak=6
  (b088/b089/b090/b091/b092/b093 累积). 原 pool #3 reserve = b080/C006 `Mean(overnight×turnover,60)
  × Std(num_trades,60)` alpha_surv=0.61 + ls_t=4.06 + 9/9 年正 + cum_mdd=-1.37 但 4 anchor
  cluster (F002/F012/F018/F023) + incr_ic=0.0098 缺 F203 0.015 ~33% → reserve。本批 把
  b091 finding (rank-diff axis Sub(TsRank,TsRank) 在 amount/num_trades/overnight 非
  close-position 域是真 escape, b091/C004 PASS) 应用到 overnight × turnover product 上，假设
  rank-diff atom + product LHS 联立可同时降 anchor cluster + 升 incr_ic 出 borderline。

  6 候选覆盖 rank-diff axis × overnight 域全谱: - C001 (single-field rank-diff): Sub(TsRank(overnight_gap,60),
  TsRank(overnight_gap,20)) — pure overnight 跨窗 TsRank diff, atom-class probe (overnight
  非 close-position 域, b091 finding 预测 escape 可能); - C002 (signed-product rank-diff):
  Sub(TsRank($turnover_rate × overnight_gap, 60), TsRank($turnover_rate × overnight_gap,
  20)) — overnight×turnover product 跨窗 rank-diff, b080/C006 reserve atom 直接套 rank-diff
  form; - C003 (cross-period product rank-diff): Sub(TsRank(overnight×turnover,30),
  TsRank(overnight×turnover,90)) — 短窗−长窗对称组 (30/90), 测 window-scale 不同效; - C004 (cross-field
  rank-diff): Sub(TsRank(overnight×volume,60), TsRank(overnight×turnover,60)) — 同窗
  cross-field rank-diff, RHS swap volume↔turnover 脱 F002 anchor (b093 RHS 锁源律启发: 改
  RHS family); - C005 (Cov form rank-diff): Sub(TsRank(Cov(overnight,$volume,60),60),
  TsRank(Cov(overnight,$volume,60),20)) — 时序+横截面 double TsRank, 测 Cov atom 在 rank-diff
  layer 是否独立; - C006 (anti-clamp single TsRank): TsRank(overnight × Mean($turnover_rate,5),
  60) — 单 TsRank 平滑分母 (turnover_5 trend), 作 sub-control 对比组 (非 rank-diff form, 测 smoothing
  vs raw 效果)。

  全候选 Phase 1 generator self-check 4 hard rule: - **P030** (alpha_surv>1.0 unilateral
  ≠ admit 充分): 本批 6/6 不依赖 alpha_surv 单边, multi-CP rationale 强制 (incr_ic + max_corr
  + ls_t + sign_consistency 至少 2/3); - **P004-deep** (N-day path-integral 累积 default
  reject): rank-diff Sub(TsRank,TsRank) 是 cross-window scalar diff (round 91 lessons
  已 codify NOT path-integral); product Mul(overnight, turnover) 是单步 cross-section,
  非累积; 全候选 pass; - **Cov-equiv律 (P030 升格)**: C005 `Cov(overnight, $volume, 60)` 与库内
  F023 `Mean(Mul(overnight, intraday), 20)` 几何不同 (RHS=volume vs intraday body), Cov
  跨字段 overnight×volume 与 F023 overnight×intraday 不构成 cross-section near_dup (验证 ≥0.9
  需 cross-corr 实测, 但 RHS field 不同概率不会撞); 全候选 pass; - **Reciprocal monotonic-invariant
  duplicates**: 全候选无 Div 形式, 无 reciprocal 镜像问题。

  **rank-diff axis atom-class 依赖律 (b091/b092 升格)** 应用: - b091/C004 (institutional_flow_proxy
  amount/num_trades 域) PASS — rank-diff Sub(TsRank,TsRank) 在非 close-position 域是真 escape;
  - b092 close-position 域 (tsrank_candlestick_ratio) fail — 同 rank-diff form 在 close-position
  域 self-cancellation; - **本批 overnight 域**: overnight gap = $open − Ref($close,1)
  是 cross-day momentum direct, 非 close-position (与 (C-L)/(H-L) close-position 几何 distinct);
  假设属 rank-diff escape 域 (与 b091 同类), 而非 close-position self-cancellation 域。

  **b093 RHS 锁源律 (T017 finding)** 应用: - b093 实证 T017 Corr atom F019 cluster anchor
  在 RHS `Mean(H-L,60)` 不在 LHS Corr; - 本批全候选 **不用 Mean(H-L) RHS** — C001/C002/C003
  是 single-LHS rank-diff (无独立 RHS); C004 cross-field rank-diff 用 volume/turnover RHS
  family (非 H-L 衍生); - 假设: 不接触 Mean(H-L,60) RHS = 不接触 F019 vol_20d basis 1st moment
  同源簇, cluster anchor 应不在 b093 锁源域内。

  **F024 anchor basin 宽度≥90d** 应用: - F024 是 TsRank-60 trade_density ratio (close-position
  域); 本批全候选 LHS = overnight × {turnover/volume} (cross-day momentum 域, 非 close-position);
  - C003 用 30/90 窗对, C004 用 60d, C005 用 60d Cov + 20/60 双 TsRank — 全候选 TsRank 窗口 ∈
  [20,90d] 范围内, 但 LHS atom geometry 与 F024 几何 distinct (overnight 非 close-position),
  F024 anchor basin 应不直接 cluster overlap。

  **reciprocal monotonic-invariant duplicates** (round 92 升格): 全候选无 Div 形式, 无 numer/denom
  互换问题; product Mul(overnight, turnover) 是 commutative 但 Mul(turnover, overnight)
  canonical equivalent (round 91 COMMUTATIVE_OPERATORS{Add,Mul} pre-dedup 自动处理)。

  Anti-recapitulation: - 不重试 b080/C006 raw form (`Mean(overnight×turnover,60) × Std(num_trades,60)`)
  — 那是被复活的 reserve 本身, 直接重计算 = 重复 b080/C006; - 不重试 b048/C001-C005 (overnight ratio
  各种 rank-diff form, 同字段跨窗口 / 共 RHS=overnight_5 全 reject — T004/T006/T008 disprove);
  - 不重试 b049/C001-C005 (共 RHS=overnight_5 / signed×magnitude 脱 LHS — T008/T009); -
  不重试 b059/C003 sign-product 60d rank-diff (T011 path); - 不重试 b066 Skew/Kurt/Autocorr
  rank wrap (T014/T015/T016 disprove)。

  本批 C001 (single-field overnight 跨窗 rank-diff) 与 b048/C001 (overnight ratio rank-diff)
  数学距离非零 (C001 是 TsRank overnight raw 跨窗, b048/C001 是 ratio LHS); 与 b066/C004 (Rank
  wrap of Mean(overnight,5)) 不同 (C001 是 raw overnight 跨窗 TsRank, b066/C004 是 single
  TsRank wrap aggregation atom)。

  Hard targets: - C002 或 C004 ≥1 admit (incr_ic≥0.015 + max_corr<0.40 + alpha_surv≥0.30
  + ls_t≥2 + sign_consistency=1.0) → 验证 b091 rank-diff axis escape 律在 overnight 域是否同样成立
  + pool #3 真红利; - 若 6/6 全 reject → rank-diff axis 在 overnight 域亦 self-cancellation
  (与 b092 close-position 域同律), 升格 `rank-diff axis 跨域适用律`: 仅 amount/num_trades 域 escape,
  overnight/close-position/其他域均 self-cancel; - calibration_trigger 候选: zero_admit_streak=6
  + 3 reserve revival pool 连续失败 (pool #1, #2 已失败, 若 pool #3 再失败) → 极可能触 calibration
  (累计 reserve 积压 + reserve revival 路径全谱探索后真红利仍未现, 需阈值校准 vs 真信号塌缩诊断)。'
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
last_activity: '2026-05-15T22:20:28Z'
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
> 🟡 **saturated** · 18 rounds · 9 admits — overnight/intraday 二段分解兑现 5 个 Mean/sign-freq atom + 2 个 rank-diff family + 1 个 magnitude-product。b066→b087→b093→b094 连续 5 轮 zero_admit + 7 thread DISPROVEN，T017 (Corr × overnight_gap) reserve 火种累计 3 个，**b093 揭示 RHS 锁源律 (F019 cluster 在 RHS Mean(H-L,60))**，**b094 揭示 cluster-breaking ↔ alpha-cancellation 律 + rank-diff escape 域精化 (overnight 是 geometrically-saturated, rank-diff form 不 escape)**。
> **Members**: [[F009]] · [[F010]] · [[F011]] · [[F017]] · [[F018]] · [[F022]] · [[F023]]

---

## Hypothesis

> [!success]+ 已验证
> 分解 daily return 为 **overnight** 与 **intraday** 两段，driver 不同 (overnight = 隔夜消息+机构 pre-market；intraday = 日内散户+算法)，aggregation (spread / persistence / sign-freq / magnitude-product) 在 cross-section 携带独立 alpha。F010 ls_t=7.50 整库记录；F017/F018 把 overnight 与独立 direction signal 组合升格 rank-diff 范式。

> [!failure]+ 已封闭 (b094 全面饱和升级)
> - **correlation** 形式不稳 (sign_flip)
> - **pure intraday 镜像** 冗余 (F009 已吸收 intraday)
> - **overnight/|intraday| ratio** 被 F010 吸收
> - **同字段跨窗口 rank-diff** 抵消 (ratio/Corr/TsRank 3 atom-class 全实证, 无例外)
> - **signed×magnitude 异质结构** 脱 overnight LHS 后塌缩
> - **close-position atom** 4 代 LHS 几何穷尽 (T012)
> - **sign-离散化 hybrid** Sign×|magnitude| 双向探针 (T013)
> - **autocorr atom** lag-1 持续性 vol_20d-locked (T014)
> - **shape moment Skew/Kurt** 不 P003-flip 但 P004-absorb (T015)
> - **TsRank/Rank wrap** 仅 within-name normalization, 不脱 anchor cluster (T016)
> - **T011 axis (magnitude-weighted product)** ≥10 fresh atom 跨 form 全失败 — DISPROVEN-comprehensive
> - **rank-diff axis 在 overnight 域 self-cancellation** (b094, geometrically-saturated family + 3 anchor 引力盆地 F018/F023/F003)

> [!info]+ 复活条件
> - **新数据**：minute-bar session 分解 (open auction / midday / close auction)
> - **长 horizon evaluation policy**：T017 reserve 在 20d horizon IC=0.073 显著 (CLI 不支持 `--horizon` override, 需 evaluation policy 改造)
> - **anchor 退役**：F002/F012/F018/F019/F023 cluster 解锁后重测 T011/T017 火种
> - **expression-rewrite revival** 或 anchor-retirement 路径 (b094 后唯一可行向量)

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
> - **T001** overnight aggregation [✓ b025]: F009 spread (ic=0.047 ls_t=5.18) + F010 5d persistence (**ls_t=7.50 整库记录**)
> - **T002** overnight-intraday correlation [✗ b025]: 20d Corr sign_flip
> - **T003** intraday 镜像 [✗ b027]: F009=overnight−intraday 数学结构已吸收 intraday
> - **T004** overnight/|intraday| ratio [✗ b048]: max_corr=0.898@F010, **rank-diff > ratio (incr_ic 13×)**
> - **T005** rank-diff 跨 direction 泛化 [✓ b049, 升格 lessons]: F017 + F018 兑现 rank-diff 范式
> - **T006** overnight horizon-diff rank [✗ b048]: 同字段跨窗口抵消律
> - **T008** rank-diff RHS 共享律 [✓ b049, 升格 lessons]: 共 RHS=overnight_5 全 reject (硬约束第 6 条)
> - **T009** signed×magnitude 脱 overnight LHS [✗ b049]: overnight signal >> |intraday|
> - **T010** overnight sign frequency [✓ b049]: → F018, sign vs magnitude 几何正交 (corr=0.37)

---

### T011 · overnight×intraday joint magnitude/sign 共方向交互 [✗ DISPROVEN-comprehensive batch_087 → +b094]

> [!failure]+ Thread 结论：magnitude × magnitude 直乘 (F023 b059) 兑现唯一 admit；累计 ≥10 fresh atom 跨 form 全饱和；b094 rank-diff revival 0/5 再 disprove
>
> **Question**: 共方向交互 (sign-product / magnitude-product / weight-product) 是否在 cross-section rank-diff 几何下产生独立 alpha？
>
> **Answer (multi-stage)**:
> - **sign-only 路径** (b058/b059): csi1000 1d primary_horizon 受阻
> - **magnitude-weighted product 兑现 admit** (b059 C004 → **F023** ic_oos=0.044 ls_t=4.89 incr_ic=0.018)
> - **b080+b087 累计 ≥10 fresh atom 全失败** (volume_delta / |abs| / range / signed×Sign / Cov / TsRank wrap / standalone)
> - **b094 rank-diff revival 0/5** — rank-diff form 把 max_corr 从 4 anchor cluster 降至 0.27@F018 ✓ 但同步 cancel alpha 到 hard_gate 以下 (C002 vs C006 控制对照实证: ic_oos 几乎相同 0.0067/0.0068, max_corr 差 0.59)
>
> **Reserve 火种**:
> - [[batches/batch_080/candidates/C006|b080 C006]] `Mean(overnight × turnover, 60) × Std($num_trades,60)` — alpha_surv=0.61 + 9/9 年正 + ls_t=4.06 + cum_mdd=-1.37 但 4 anchor cluster + incr_ic=0.0098 缺 F203 ~33% → reserve 待 F018/F023 退役
>
> **Key findings**:
> - **Cov ≈ Mean of product 等价律** (b087): csi1000 daily zero-mean stationary 下 `Cov(X,Y,N) ≈ Mean(XY,N)`, F023 admit 后所有 Cov(o,i,N) atom 自动 cross-section near_dup (b087 C005 实测 0.927)。应升格 Phase 1 generator AST 自检第 9 条。
> - **cluster-breaking ↔ alpha-cancellation trade-off 律** (b094, lesson 候选): rank-diff form 是真效 anchor-escape 路径但代价是 alpha 同步 cancel, 不能同时实现 (a) cluster 破除 + (b) alpha 保留 在 product LHS 上。b080/C006 reserve 真红利不在 rank-diff form, 在 raw form 但被 anchor cluster 阻断。
> - **rank-diff axis 跨域适用律精化** (b091/b092/b094, lesson 候选): rank-diff escape 域非"非 close-position 域"而是"高 noise dispersion + ungeometrically-saturated 域"。overnight 是 geometrically-saturated family (9 admit + F018/F023/F003 三 anchor 密集), 即使 rank-diff form 也无法 escape。
> - **核心律**: sign-only 是 long-horizon 现象, 1d horizon noise-dominated; T011 axis 已结构性饱和。

---

### T012-T016 · 早期 disproven thread 集合 [✗ DISPROVEN batch_060/066]

> [!failure]+ 5 thread 全 disprove — close-position / hybrid sign / autocorr / shape moment / Rank wrap 全 vol_20d-locked
> - **T012** close-position-in-range Mean LHS [✗ b060]: F022 admit 后 4 代设计 (仿射 / 跨窗 normalization / Power-cubed / from-peak) 全失败, geometric exhaustion。Reserve b060/C006 60d cross-window normalization × Std(turnover,60) alpha_surv=0.93 + incr_ic=+0.0025 + max_corr=0.37@F017 → 等 F017 退役。
> - **T013** sign-离散化 hybrid [✗ b060]: hybrid Sign×|magnitude| 0/2 admit。F018 0.37 是 happy accident, sign-side 仅贡献方向, magnitude-side 主导。Reserve b059/C005 sign×turnover_5/60 → 等 F022 退役。
> - **T014** autocorr atom (lag-1) [✗ b066]: ordinal scale-free 但 cross-section rank 仍 monotone-equivalent vol_20d。
> - **T015** shape moment (Skew/Kurt) [✗ b066]: regime stable 不 P003-flip 但 P004-absorb (3rd/4th 阶同律, heavy-tail ↔ daily-vol covariation)。
> - **T016** TsRank/Rank wrap [✗ b066]: within-name normalization, cross-section ordering 与原 X 高度相关 (corr=0.61 with F010)。

---

### T017 · 量价时序 covariance atom (Corr × overnight_gap) [✗ DISPROVEN batch_094]

> [!note]+ Thread 进展：跨 batch 火种续命 (b066→b087→b093, 3 reserve 火种), b094 Cov+double TsRank wash 律, **RHS 锁源律新揭示 + Pool #4 horizon-switch mechanism inconclusive**
>
> **Question**: Corr(X, overnight_gap, N) within-name 时序 covariance atom 是否独立于 magnitude/sign-freq？Barra-clean (alpha_surv>1.0) 候选能否 admit？LHS-swap 能否 escape F019 cluster？
>
> **Reserve 火种 (3 个)**:
> - [[batches/batch_066/candidates/C005|b066 C005]] volume LHS Corr-20 + Std(volume,60) — alpha_surv=**1.16 库内首 Barra residual IC > raw IC** 但 ls_t=1.26<2 + max_corr=0.46@F002
> - [[batches/batch_087/candidates/C001|b087 C001]] volume LHS Corr-60 + Mean(H-L,60) — ic_oos=**0.032** + ls_t=1.77 + horizon ladder 1d→20d 0.032→**0.073**; alpha_surv=0.20 + max_corr=0.45@F019 borderline
> - [[batches/batch_093/candidates/C005|b093 C005]] num_trades LHS Corr-60 + Mean(H-L,60) — ic_oos=**0.033** + ls_t=**1.94**; alpha_surv=0.20 + max_corr=0.45@F019 (与 b087 C001 几乎相同)
>
> **Key findings**:
> - **Barra-clean ≠ library-clean** (b066): 不存在双 clean 候选; "逃 vol_20d 必撞 anchor" 几何困境。
> - **RHS 选择 trade-off** (b087): b066 RHS=Std(volume,60) (alpha_surv=1.16 ls_t<2) vs b087 RHS=Mean(H-L,60) (ls_t=1.77 alpha_surv=0.20)。
> - **🚨 RHS 锁源律** (b093, 5/5 uniform 跨 atom-class): F019 cluster anchor **在 RHS `Mean($high-$low, 60)` 不在 LHS Corr atom** — Mean H-L 60d 是 vol_20d 1st moment 平滑同源。**真复活路径必须改 RHS**, 不是 LHS。
> - **🚨 Pool #4 horizon-switch mechanism inconclusive** (b093, CLI 限制): `research execute` 不支持 `--horizon` override, admit gate 锚定 1d。1d→20d 3.5× IC 放大 mechanism 真实存在但 admit 在 1d 仍 borderline reject。需 CLI 扩展或 evaluation policy 改造。
> - **b094 C005 Cov+double TsRank wash 律**: ic_oos=0.0006 essentially zero hard_gate fail, max_corr=0.035@F007 库最 clean 但 alpha 塌缩 — "库 clean ≠ tradable" 第 5 次跨方向复现。

---

## Known Failures

| Batch | Candidate | Pattern | 原因 |
|---|---|---|---|
| batch_025-049 | (汇总) | early disproves | T002 sign_flip / T003 intraday 镜像 / T004 ratio / T006 同字段跨窗 / T008 共 RHS / T009 signed×magnitude |
| batch_058-059 | (汇总) | sign-product / close-pos 仿射 / circ_mktcap_60 RHS | dead RHS endpoint 升格 + T011 sign-only 受阻 |
| batch_060 | C001-C005 | 4 代 close-position + hybrid sign×magnitude | T012 EXHAUSTED + T013 DISPROVEN |
| batch_066 | C001-C006 | autocorr / Skew / Rank wrap / Kurt | T014/T015/T016 全 vol_20d-locked |
| batch_080 | C001-C005 | volume_delta / |abs| / range / Sign(intraday) 60d / 加速度 | T011 axis 6 fresh atom 全失败 |
| batch_087 | C002-C006 | ratio TsRank / signed-flow / |overnight| Rank / Cov / num_trades×|Δret| | T011 ≥10 atom DISPROVEN-comprehensive + Cov-equiv 律升格 |
| batch_093 | C001-C006 | T017 LHS-swap 跨 4 fields + T006 Corr 跨窗 | RHS 锁源律 5/5 uniform · T006 跨 atom-class 普适 |
| batch_094 | C001-C006 | rank-diff revival × overnight 域 | 0/6 全 hard_gate fail (5 ic_too_low + 1 degenerate) · cluster-breaking ↔ alpha-cancellation 律 · rank-diff escape 域精化 · T006 TsRank atom 第三次实证 · 库 clean ≠ tradable 第 5 次 |

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
- **Forbidden Patterns rate/delta 作 weight 同律** (b080 C001 升格候选): rate/delta 作 weight 也 default-skip
- **Sub_inside_CsRank 加速度 vol_20d-locked 律** (b080 C005 升格候选): 同字段不同窗口的代数差仍 vol_20d 二阶载体
- **🚨 RHS 锁源律** (b093 升格候选, 强证据 5/5 uniform): T017 axis F019 cluster anchor 在 RHS `Mean($high-$low, 60)` 不在 LHS — 真复活路径必须改 RHS
- **🚨 T006 律跨 atom-class 普适** (b093 Corr + b094 TsRank 升格候选): rank-diff hard rule 第 3 条已在 ratio/Corr/TsRank 3 atom-class 全实证, 无例外
- **🚨 "库 clean ≠ tradable alpha"** (b059/b066/b087/b093 C004/b094 C005 5 例累计升格): max_corr 极低 (<0.10) 不 hint 信号强度, 反向警示信号塌缩可能
- **🚨 cluster-breaking ↔ alpha-cancellation trade-off 律** (b094 升格候选, C002 vs C006 控制对照实证): rank-diff form 是真效 anchor-escape 路径但代价是 alpha 同步 cancel — 不能同时实现 cluster 破除 + alpha 保留 在 product LHS 上
- **🚨 rank-diff axis 跨域适用律精化** (b091/b092/b094 升格候选, 3 方向证据综合): rank-diff escape 域 = "高 noise dispersion + ungeometrically-saturated 域"; saturated family 三 anchor 引力盆地密集时 rank-diff form 不 escape
- **Pool #4 horizon-switch mechanism inconclusive (CLI 限制)** (b093 升格候选): T017 axis 1d→20d 3.5× IC 放大真实但 admit gate 锚定 1d, 需 CLI 扩展或 evaluation policy 改造

---

## Related

- 🟢 [[intraday_price_formation]] (saturated) — F003 overnight gap 上游字段；F020 anti-anchor cluster 锁死该方向 rank-diff 泛化
- 🟡 [[ohlc_temporal_aggregation]] (productive) — F019 higher-moment LHS 同律；F007 corr=0.708@F009
- 🟢 [[microstructure_illiquidity]] (productive) — rank-diff 范式发源地 (F015/F016)
- 🟡 [[gap_acceptance_structure]] (productive) — F020 higher-moment LHS 跨家族复现

---

## Narrative Log

> [!quote]+ 2026-05-16 · [[batches/batch_094/judge|batch_094]] · zero admit (0 reserve) · **Pool #3 rank-diff axis × overnight 域 全谱失败 + 2 lesson 升格**
> admit=0 / reserve=0 / reject=6 (5 ic_oos_too_low + 1 degenerate)。
> - **🚨 cluster-breaking ↔ alpha-cancellation trade-off 律新升格**: C002 vs C006 控制对照 — rank-diff form max_corr=0.27@F018 ✓ / single TsRank max_corr=0.857@F003 ✗, ic_oos 几乎相同 (0.0067/0.0068)。rank-diff form 破 cluster 但同步 cancel alpha。
> - **🚨 rank-diff axis 跨域适用律精化** (3 方向证据): b091 amount/num_trades PASS · b092 close-position FAIL · b094 overnight FAIL。escape 域 = 高 noise + ungeometrically-saturated, overnight 是 geometrically-saturated family。
> - **🚨 T006 律 TsRank atom 第三次实证**: ratio/Corr/TsRank 3 atom-class 全无例外。
> - **"库 clean ≠ tradable" 第 5 次跨方向复现**: C005 max_corr=0.035@F007 库最 clean + alpha 塌缩。
> - **C003 informative finding (window-asymmetric momentum reversal)**: 30/90 短−长 = mean-reversion / 60/20 长−短 = momentum, 同 atom 不同 window pair 捕捉不同 regime。
> - **MT budget**: cumulative 492 → 528 · direction 63 → 69
> - **🚨 calibration_trigger 命中 (强信号)**: zero_admit_streak 6→**7** + 3 reserve revival pool 全谱失败 + 4 lesson 升格候选 + 累计 reserve 积压 5 个未消化。C001 差 0.0002 ≈ 2.5% 阈值是 over-rejection signal。
> - **Pool #3 全谱失败诊断**: overnight 是 geometrically-saturated family, rank-diff form 不是 escape 几何; b080/C006 reserve 真路径需 anchor retirement (F018/F023/F003)。
>
> **Operations**　status 保持 saturated · T011 DISPROVEN-comprehensive +5 evidence · T017 ACTIVE +b094 C005 Cov wash 律 · zero_admit_streak 6→**7** · **🚨 触 calibration_trigger 强信号** · commit `[mine] batch_094 | overnight_intraday_split | admits=0 reserves=0 rejects=6`

> [!quote]- 2026-05-15 · [[batches/batch_093/judge|batch_093]] · zero admit (1 reserve) · **reserve_revival_pool_4 horizon-switch 失败** + RHS 锁源律新揭示
> admit=0 / reserve=1 (C005 num_trades LHS) / reject=5。
> - **🚨 RHS 锁源律新发现**: 5 candidates LHS 跨 4 fields ($volume/$num_trades/$amount/normalized-vol) + 2 windows 全 alpha_surv=0.18-0.21 + max_corr=0.44-0.45@F019 + dom_style=vol_20d (5/5 uniform)。F019 cluster anchor **在 RHS Mean(H-L,60) 不在 LHS Corr atom**。真复活路径必须改 RHS。
> - **Pool #4 horizon-switch mechanism inconclusive (CLI 限制)**: 1d→20d ic 0.032→0.073 (3.5× 放大) 真实但 admit gate 锚定 1d。需 CLI 扩展或 evaluation policy 改造。
> - **C005 reserve 火种 (T017 第 3 个)**: num_trades LHS 首次, ls_t=1.94 (trail 2.0 仅 3%)。
> - **C004 T006 律跨 atom 普适**: Corr 同字段跨窗口 rank-diff 复现 hard_gate fail。
> - **num_trades atom-class 假设证伪 (scope refinement)**: Corr atom 内部 LHS-swap 不改 cluster, 仅在 rank-diff LHS 上层 close-position 域成立。
> - **MT**: cumulative 486→492 · direction 57→63
>
> **Operations**　status 保持 saturated · T017 ACTIVE (+b093 C005, 3 reserve 火种) · zero_admit_streak 5→6 · **触 consolidation_trigger 强信号** · commit `[mine] batch_093 | overnight_intraday_split | admits=0 reserves=1 rejects=5`

> [!quote]- 2026-05-03 · [[batches/batch_087/judge|batch_087]] · zero admit (1 reserve) · T011 DISPROVEN-comprehensive + status `productive → saturated`
> admit=0 / reserve=1 (C001) / reject=5。
> - **C001 T017 reserve 跨 batch 火种续命** (b066→b087): ic_oos=0.032 强化 3.5× + ls_t=1.77 + horizon ladder 1d→20d 0.032→0.073。
> - **T011 axis DISPROVEN-comprehensive** (≥10 atom 跨 form): b080+b087 累计 magnitude/ratio/signed-flow/Cov/TsRank wrap/standalone 全失败。
> - **C005 Cov ≈ Mean of product 等价律新升格**: 应升格 Phase 1 generator AST 自检第 9 条。
> - **C006 "库 clean ≠ tradable" 反例**: max_corr=0.13 库最 clean 但 train→val sign-flip + decay=-0.06。
> - **T017 RHS 选择 trade-off**: 不存在两端都满足的 RHS — 真复活路径是 Python OLS residualize / horizon policy / anchor 退役。
>
> **Operations**　direction `productive → saturated` · T011 升级 DISPROVEN-comprehensive · T017 ACTIVE (2 reserve 火种) · zero_admit_streak 4→5 · commit `[mine] batch_087 | overnight_intraday_split | admits=0 reserves=1 rejects=5`

> [!quote]- 2026-05-02 · [[batches/batch_080/judge|batch_080]] · zero admit (1 reserve) · T011 ANSWERED-saturated
> admit=0 / reserve=1 (C006) / reject=5。T011 axis 6 fresh atom 全受阻。C006 (60d turnover-weighted overnight × Std(num_trades,60)) alpha_surv=0.61 + ls_t=4.06 + 9/9 年正 + cum_mdd=-1.37 但 4 anchor cluster + incr_ic=0.0098 缺 F203 ~33% → reserve。**"逃 vol_20d 必撞 anchor cluster" 几何困境再实证**。MT 438→444。

> [!quote]- 2026-05-01 · [[batches/batch_066/judge|batch_066]] · zero admit (1 reserve) · T014/T015/T016 DISPROVEN + T017 ANSWERED-partial
> admit=0 / reserve=1 (C005) / reject=5。**核心律 — "逃 vol_20d 必撞 library anchor"**: 6/6 候选 dominant_style=vol_20d。整阶 moment family vol_20d-locked (跨阶律): 1st Mean (admit) → 2nd Std/Var (P003 flip) → 3rd/4th Skew/Kurt (P004 absorb) → Corr autocorr (P004 absorb)。MT 354→360。

> [!quote]- 2026-04-25-28 · [[batches/batch_058/judge|batch_058]]-[[batches/batch_060/judge|batch_060]] · F022/F023 admits + T012/T013 DISPROVEN
> **8th admit F022** (b058 C004 close_position_amount_accel_rd_20 IC_OOS=0.029 alpha_surv=0.43 max_corr=0.283@F006) · **9th admit F023** (b059 C004 gap_body_magnitude_amount_rd_20 ic_oos=0.044 ls_t=4.89 incr_ic=0.018 — 第一个 second-order interaction)。T011 sign-only 三次受阻; magnitude × magnitude 直乘在 20d 短窗兑现。b060 close-position 4 代 LHS 全军覆没 (跨窗 normalization / Power-cubed / from-peak) + hybrid Sign×|magnitude| 0/2。**single-atom geometric exhaustion 律** 升格 lessons 候选。priority `high → medium`。

> [!quote]- 2026-04-25 · [[batches/batch_048/judge|batch_048]]-[[batches/batch_049/judge|batch_049]] · F017/F018 admits + rank-diff 范式升格
> **F017 admit (rank-diff 复活)**: b048 C003 ic_oos=0.054 incr_ic=0.027 9/9yr+。**F018 admit (rank-diff 第 4 次跨家族)**: b049 C006 ic_oos=0.051 ls_t=5.98 incr_ic=0.015 cum_mdd=-1.53 整库最浅。Sign 聚合 vs magnitude 聚合**几何正交** (corr 0.37)。**触 Phase 5 consolidation 升格 lessons.md "Rank-Diff Geometry"**——4 次跨家族证据链完整 + 硬约束 6 条升格。

> [!quote]- 2026-04-21 · [[batches/batch_025/judge|batch_025]]-[[batches/batch_027/judge|batch_027]] · 首批 DOUBLE ADMIT + intraday 镜像封闭
> b025 admit=2: F009 spread (ic=+0.047, ls_t=5.18) + F010 persistence (**ls_t=7.50 整库记录**); C003 20d Corr sign_flip。b027 admit=0: Intraday 镜像 3/3 reject (corr 0.65–0.89@F009)。**定论**: F009 = overnight − intraday 数学结构已吸收 intraday 分量; aggregation 有效, correlation 不稳。productive → saturated 转入 b027。
