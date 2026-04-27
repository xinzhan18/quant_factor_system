# Pattern Scout Packet

> Generated at 2026-04-25T11:01:11+00:00 · recent=10 batches

## 任务

你是 Pattern Scout，扫描下方的最近 N 批 judge 摘录 + active directions frontmatter，**识别跨批的失败模式 / style 吸收律 / 重复机制**。只改写 `storage/vault/INDEX.md` 的 `HOT-TOPICS-LLM` sentinel 块。

## 当前 HOT-TOPICS-LLM 块

<!-- BEGIN HOT-TOPICS-LLM -->
> [!warning]+ 🔥 Hot Topics（LLM 维护 · 2026-04-25 scan recent=10）
> - 🔴 **P001 rank-diff geometry 范式边界已显形** · dirs: value_liquidity_interaction, intraday_price_formation, barra_residual_alpha → 连续 3 批 0-admit；rank-diff 不是万能钥匙。下设计须验证 (a) LHS atom 不与已 admit rank-diff 因子同源（F019/F020 anti-anchor）(b) RHS basis 不在饱和 endpoints（overnight_5/turnover_5/amount_20/body_ratio_20/price_vol_20）(c) 两端都 scale-free 且独立 raw field
>   evidence: [[batches/batch_052/judge|batch_052]], [[batches/batch_053/judge|batch_053]], [[batches/batch_054/judge|batch_054]]
> - 🟢 **P002 rank-diff geometry 6 跨家族成功 → lessons 升格已完成** · dirs: microstructure_illiquidity, overnight_intraday_split, ohlc_temporal_aggregation, gap_acceptance_structure → F015/F016/F017/F018/F019/F020 跨 4 family 6 admit；后续候选优先沿 "higher-moment LHS × 非饱和 RHS basis" 路径设计
>   evidence: [[batches/batch_046/judge|batch_046]], [[batches/batch_050/judge|batch_050]], [[batches/batch_051/judge|batch_051]]
> - 🔴 **P003 higher-moment LHS regime sign-flip 跨 3 大 family 硬律** · dirs: value_liquidity_interaction, intraday_price_formation, barra_residual_alpha → raw 基本面 / signed intraday / Barra residual 的 Std/Var/cumsum 类二阶聚合在 train(低利率) vs validation(利率上行) 系统性翻号；除非配 regime-aware gating，否则避免 second-moment LHS 单飞
>   evidence: [[batches/batch_052/judge|batch_052]], [[batches/batch_053/judge|batch_053]], [[batches/batch_054/judge|batch_054]]
> - 🟠 **P004 vol_20d 结构性吸收 8+ direction 不可剥离** · dirs: range_structure, overnight_intraday_split, ohlc_temporal_aggregation, gap_acceptance_structure, value_liquidity_interaction, intraday_price_formation, barra_residual_alpha, microstructure_illiquidity → 最近 10 批 60 候选几乎全部 dominant_style=vol_20d；CsRank ordinal 化无法剥离原子层 style；必须 portfolio 层 Barra neutralize 或显式 orth 设计
>   evidence: [[batches/batch_049/judge|batch_049]], [[batches/batch_053/judge|batch_053]]
> - 🟠 **P005 RHS basis 共振饱和律是动态的** · dirs: overnight_intraday_split, ohlc_temporal_aggregation, gap_acceptance_structure, value_liquidity_interaction → admit 一个 rank-diff 即消耗对应 RHS 类目余量（body_ratio_20 经 F020 admit 后从安全→饱和；overnight_5/turnover_5/amount_20/price_vol_20/Amihud_20 已全饱和）；新候选 RHS 须 max_corr@anchor < 0.30 + LHS 完全脱 family
>   evidence: [[batches/batch_051/judge|batch_051]], [[batches/batch_053/judge|batch_053]]
<!-- END HOT-TOPICS-LLM -->

## 输出契约（INDEX.md HOT-TOPICS-LLM 块）

只替换 `<!-- BEGIN HOT-TOPICS-LLM -->` 到 `<!-- END HOT-TOPICS-LLM -->` 之间的内容；不要改 INDEX frontmatter、COCKPIT、Bases embed 或其它 sentinel。

块内最多 5 条 bullet。每条包含 P{id}、confidence 图标、title、affected directions、action hint、1-2 个证据 wikilink。若无 active pattern，保留 sentinel 并写一行“当前无活跃跨批模式”。

## 识别启发

- 同一 `dominant_style`（如 `vol_20d`）在 ≥3 批、跨 ≥2 方向出现
- 同一 rejection 形态（magnitude/ratio/power-mean）反复失败
- 一个 direction 的 zero-admit 可以用另一 direction 已证伪的同族理由解释
- 硬 gate `max_corr` 到同一 F{id} 反复命中（库空间饱和）

## Active Directions（frontmatter 摘录）

| direction | status | priority | rounds | admits | last_batch |
|---|---|---|---|---|---|
| amount_volatility_signal | saturated | low | 6 | 1 | batch_033 |
| asymmetric_momentum | dead | medium | 1 | 0 | batch_028 |
| barra_residual_alpha | saturated | low | 8 | 1 | batch_054 |
| fundamental_momentum | dead | low | 1 | 0 | batch_022 |
| gap_acceptance_structure | productive | high | 4 | 3 | batch_051 |
| intraday_price_formation | saturated | high | 5 | 2 | batch_053 |
| liquidity_acceleration | saturated | low | 2 | 0 | batch_032 |
| log_value_liquidity | dead | low | 1 | 0 | batch_038 |
| microstructure_illiquidity | productive | medium | 5 | 4 | batch_047 |
| ohlc_temporal_aggregation | productive | medium | 7 | 5 | batch_050 |
| overnight_intraday_split | productive | high | 7 | 7 | batch_049 |
| pv_covariance | dead | low | 1 | 0 | batch_039 |
| quantile_shape_signals | dead | low | 1 | 0 | batch_044 |
| range_structure | saturated | medium | 6 | 2 | batch_056 |
| return_distribution_signals | dead | low | 1 | 0 | batch_016 |
| return_momentum_acceleration | dead | medium | 1 | 0 | batch_029 |
| stochastic_position | saturated | low | 2 | 0 | batch_041 |
| trend_quality_gated | dead | low | 1 | 0 | batch_037 |
| turnover_structural_signal | saturated | low | 1 | 0 | batch_004 |
| value_liquidity_interaction | saturated | low | 9 | 1 | batch_052 |
| vol_shock_signals | dead | low | 1 | 0 | batch_024 |
| vwap_proxy_signals | saturated | low | 3 | 1 | batch_057 |

## Recent batches（judge.md 关键段摘录）

### batch_048 · direction=`overnight_intraday_split` · admit=1 reserve=1 reject=4 total=6

## 方向级反思

`overnight_intraday_split` 方向从 **saturated 被正确结构部分复活 → partially productive**。admit 从 3（F009/F010/F011）→ 4（+C003），direction rounds 3→4，priority 维持 high。核心驱动是 rank-diff 范式跨家族泛化到 overnight × turnover 的成功——rank-diff 已成为**跨 3 个 direction 独立泛化验证的通用几何范式**（microstructure_illiquidity F015/F016, overnight_intraday_split F017-to-be），可作为 Phase 5 consolidation 升格到 lessons.md 的强候选教训。

**下轮建议**（若本方向继续）:
1. 测试 **rank-diff 第三波泛化**: overnight_rank × 其它独立 direction scale-free signal（如 Amihud illiquidity rank, pb_amount ratio rank）——注意避免 LHS 始终是 overnight_rank（同批 anchor rule 扩展约束）
2. C006 的 "signed × magnitude 异质函数结构" 可作为独立维度，在非 overnight LHS 上重新测试（如 turnover_signed × |price_magnitude| rank-diff）
3. direction 复活条件 (b) "20d+ overnight persistence" 仍未测——若引入 20d 窗口需避开本批 C005 确认的 "同字段跨窗口抵消律"，应与独立 RHS 结合

**方向复活 + rank-diff 三向泛化**: 若下一批新家族测试 rank-diff 再次兑现（如 OHLC temporal aggregation × liquidity rank-diff），可触发 Phase 5 consolidation 将 rank-diff 几何性质从 direction-level 升格为 lessons.md Data Facts 级别设计原则。

## 跨候选对比

- **C003 admit vs C006 reserve — 同批 anchor rule (LHS 共享 overnight_rank)**: 两者都是 rank-diff with overnight 5d LHS，C003 RHS=turnover_rank (跨 direction), C006 RHS=|intraday|_rank (同 direction 内部)。C003 全面占优：incr_ic 0.027 > 0.021, ls_t 4.75 > 3.77, ICIR 0.466 > 0.389, alpha_surv 0.431 borderline vs C006 0.552 acceptable (C006 CP04 略强)。LHS 共享导致 mutual corr 预期 0.6-0.8, 同时入库会形成 overnight×orth rank-diff 家族冗余——选 C003 admit，C006 reserve 等待 C003 入库后下轮以独立维度重评。**升格教训**: rank-diff 同批候选若 LHS 共享主信号端，同批最多 admit 1 个（extend batch_047 "Sub 反向对偶 dedup" 到 "LHS 共享也要 dedup"）。

- **C003 admit vs C004 reject — rank-diff vs ratio 结构比较**: 都 overnight × intraday 交互信号，C003 用 rank-diff (CsRank - CsRank), C004 用 ratio (Div(..,|..|))。C003 incr_ic=0.027 vs C004 incr_ic=0.002——**rank-diff 的信息提炼效率比 ratio 高 13 倍**。ratio 受分母数值主导（|intraday| 极小时放大不稳），rank-diff 对数值量级不敏感只看 cross-section 相对位置，结构上优于 ratio。T004 thread 证伪 ratio 路径后，rank-diff 成为 overnight × orth signal 交互的唯一存活形式。

- **C001 reject vs C003 admit — CsRank 外包是否 escape raw-diff 吸收**: C001 `Sub(CsRank(overnight_5), CsRank(intraday_5))` max_corr=0.925@F009，CsRank 外包 F009 raw-diff aggregation 失败（rank 空间在 overnight/intraday 这对小 pct return 上保序近似线性）；C003 `Sub(CsRank(overnight_5), CsRank(turnover_5))` max_corr=0.747@F010 成功 escape F009/F010。**升格教训**: rank-diff escape raw-diff 吸收的关键不在 CsRank 本身，而在 RHS 是否引入独立 direction 的 signal——同-direction rank-diff 仍被 raw aggregation 吸收（C001），跨-direction rank-diff 才能开辟新维度（C003）。

- **C002/C005 reject — shared-raw-field 抵消律三条证据链完整**:
  - C002: 两端共 numerator (`$open-Ref($close,1)`) → ic_oos=0.004 noise
  - C005: 两端完全同字段只差 aggregation 窗口 → ic_oos=-0.0014 noise
  - (batch_047 C002 历史对偶): 两端共 denominator ($amount) → ic_oos=0.007 noise
  - 三条合并升格到 lessons.md: rank-diff 设计硬约束 = 两端必须有 ≥1 个独立 raw field（numerator OR denominator）且不能是单一 aggregation 窗口差异。

- **方向兑现率**: 1 admit / 6 candidates = 17%（与 batch_046/047 同）；本批 admit 机制价值 ≈ batch_047（rank-diff 二次跨家族泛化兑现）但方向 priority 不同——overnight_intraday_split 原 saturated 被正确结构复活，microstructure_illiquidity 是 productive 持续。rank-diff 范式已跨 3 个方向（microstructure/value-liquidity 暗线/overnight_intraday）独立泛化成功，接近 lessons 通用几何性质地位。

## Thread 进展

> [!success]+ T005 [[directions/overnight_intraday_split#T005]] 🆕 — `[◐ PARTIAL-ANSWERED batch_048]`
> **rank-diff 跨 direction 泛化在 overnight 家族兑现**：
> - C003 (overnight × turnover rank-diff) → **admit** → overnight_turnover_rank_diff_5。证实 rank-diff 结构 alpha 可在 overnight × orth direction signal 上产出独立 alpha。
> - C001 (CsRank overnight − CsRank intraday) → reject near_duplicate F009。升格约束：CsRank 外包 F_parent=Mean(A-B,N) 型已入库因子仍被吸收，同-direction rank-diff 不 escape。
> - C002 (overnight 3d vs overnight_gap norm) → reject ic_oos noise。升格约束：共 numerator 抵消律。
> - C006 (overnight_signed × |intraday|) → reserve（同批 anchor rule，LHS 共享 overnight_rank 让位 C003）。
>
> **结论**: T005 约束完善——(a) 两端必须独立 direction 或独立 raw field；(b) 两端都 scale-free; (c) 同批若 LHS 共享主信号端最多 admit 1 个。

> [!failure]- T004 [[directions/overnight_intraday_split#T004]] — `[✗ DISPROVEN batch_048]`
> **overnight/intraday ratio 形式证伪**: C004 `Div(overnight_5, |intraday_5|)` max_corr=0.898@F010 + incremental_ic=0.002 < 0.003。ratio 在 csi1000 日频被 F010 overnight persistence 吸收——|intraday| 分母未产生独立信息维度。T004 悬挂复活失败，关闭。

> [!failure]+ T006 [[directions/overnight_intraday_split#T006]] 🆕 — `[✗ DISPROVEN batch_048]`
> **overnight horizon-diff rank (CsRank(20d) − CsRank(5d)) 证伪**: C005 ic_oos=-0.0014 noise——两端完全同字段只差 aggregation 窗口，rank 高度相关使 Sub 抵消。**新开 thread 立即 disproven**——值得升格到 lessons 作为 rank-diff 设计约束第三条证据。

### batch_049 · direction=`overnight_intraday_split` · admit=1 reserve=0 reject=5 total=6

## 方向级反思

本方向的 edge 结构进一步清晰：

**已确认饱和的 rank-diff 子空间**：
- RHS=overnight_5 + 任意 LHS（4 候选证据，F010/F017 双占位）
- 同字段跨窗口 rank-diff（batch_048 C005 DISPROVEN）
- signed×magnitude 异质结构脱离 overnight LHS（本批 C003 DISPROVEN）

**仍开放的 rank-diff 子空间**：
- sign 聚合 × 非 overnight RHS（C006 admit 首探，下一步泛化）
- overnight 长 horizon（20d+）sign_freq 是否 escape 5d magnitude
- overnight × intraday 非线性交互（hypothesis 复活条件 (c) 第二条，尚未探测）

**方向状态**：productive（连续 2 批 admit，batch_048 F017 + batch_049 F{new}——**5 slot 达到**）。下轮若 sign 聚合范式再 admit 则方向 status→可能重新定位为 **high-yield** 重点；若 reject 则 saturated。

**Library 健康度**：overnight_intraday_split = 5/(17+1) ≈ 28%（本批 admit 后），已成库最大方向。需警觉方向内冗余 —— C006 max_corr@F017 = 0.427 属可接受（<0.70）。

**T008 rank-diff tipping point**：
- batch_046/047 microstructure 内部 2 admit（F015/F016）
- batch_048 overnight_turnover 1 admit（F017）
- batch_049 本批 sign_freq × amount 1 admit（C006→F{new}）
- **4 次跨家族兑现**达到 consolidation 触发阈值 → 建议 Phase 5 升格 lessons.md 新 section "rank-diff geometry"

**下一轮 direction-specific next_step**：
1. 避开 RHS=overnight_5 rank-diff（饱和证明）
2. 测试 sign_freq × 其它 basis（turnover / pb / volume）泛化 T010
3. 测试 overnight × intraday **非线性交互**（hypothesis 复活条件 (c) 第二条，如 `overnight_5 * Sign(intraday_5)` 或 `overnight_5 * TsRank(intraday_magnitude, 20)`）

## 跨候选对比

**共 RHS=overnight_5 饱和证据**（C001/C002/C004/C005 全部 RHS = `Mean(overnight_pct, 5)`）：
- max_corr 都落在 0.71-0.83 区间（F010 或 F017）
- incremental_ic 或负（C001 -0.012, C002 -0.006, C005 -0.009）或勉强过 0.003（C004 +0.004）
- → rank-diff RHS=overnight_5 在当前库状态（F010 overnight persistence + F017 overnight×turnover rank-diff）下**已饱和**，4 候选共占位。

**LHS 多元化失败原因**：cockpit 硬约束"每个候选 LHS 必须不同"在本批被严格执行（Amihud/pb/turnover_cv/HHI/RealizedVol/sign_freq 6 LHS 唯一）——但 **LHS 独立 ≠ admit 独立**，真正决定 admit 的是 **RHS 结构是否共已入库因子**（F010/F017 RHS=overnight_5）。本批 5/6 RHS 共享 overnight_5 → 4 reject + 1 hard_gate fail。

**C006 成功的结构学**：
1. RHS 换成 `Mean($amount, 20)` 流动性 basis（非 overnight_5）→ 绕过 F010/F017 RHS 饱和
2. LHS 换成 `Mean(Sign(overnight), 20)`（sign 聚合而非 magnitude）→ 与 F009/F010/F011 几何正交（不仅数值正交）
3. 文字级命中 direction.md hypothesis 列出的"复活条件"——非随机组合

**L1 vs L2 vol-family 冗余揭示**（C001 vs C005）：
- C001 `Mean(|daily_ret|, 20)` vs C005 `sqrt(Σdaily_ret², 20)` 
- 两者指标几乎完全相同（IC -0.055 / -0.055，max_corr 0.826 / 0.824）
- 说明 **在 csi1000 日频 + 低 kurt 样本下，L1 和 L2 vol 等价**
- 未来不应同批 AmihudIlliq + RealizedVol 组合（浪费候选预算）

**Style 聚合**：6 候选中 4 个 dominant_style=vol_20d（C001/C004/C005/C006），但只有 C001/C005 crowding=high；C004/C006 medium。本方向天然与 vol_20d 暴露相关。

**MT 预算推进**：direction_candidates 15 → 21；bucket 仍 high（search_adjusted medium）——本方向 rank-diff 探测预算接近上限，下轮应暂停 rank-diff 模式改探其它结构。

## Thread 进展

> [!success]+ T008 [[directions/overnight_intraday_split#T008]] 🆕 — `[✓ ANSWERED batch_049]`
> rank-diff 范式第 4 次跨家族兑现——但关键发现不是"admit"本身，而是**RHS 共享饱和律**：当已入库 factors 占据 rank-diff RHS（F010/F017 均 RHS=overnight_5），新候选 LHS 再多元化也会被 RHS 端吸收。C001/C002/C004/C005 四候选 5/6 全共 RHS=overnight_5 全部 reject 证明此律。**rank-diff admit 路径=RHS 换新 basis + LHS 几何正交**（本批 C006 admit = 换 RHS=amount + 换 LHS=sign 聚合）。

> [!failure]+ T009 [[directions/overnight_intraday_split#T009]] 🆕 — `[✗ DISPROVEN batch_049]`
> asymmetric signed×magnitude 异质结构脱离 overnight LHS 后塌缩到 noise——batch_048 C006 reserve 的 signed×magnitude 潜在 alpha 主要来自 overnight LHS 端，而非 signed×magnitude 函数形式本身。反向证据：overnight signal 强度 >> |intraday| signal 强度。

> [!success]+ T010 [[directions/overnight_intraday_split#T010]] 🆕 — `[✓ ANSWERED batch_049]`
> direction.md Hypothesis 复活条件 "(c) overnight sign frequency（方向而非 magnitude）" 首次 ANSWERED——C006 Mean(Sign(overnight),20) rank vs amount rank-diff = ic_oos=+0.051 ls_t=+5.98 mono=+1.0 incr=+0.015，cum_ic_mdd=-1.53 整库最浅级别 + 9/9 年全正 + 近年最强。证明 **sign 聚合与 magnitude 聚合几何正交**——F010 overnight_magnitude_5d 相关仅 0.37。

> [!note]- T005 [[directions/overnight_intraday_split#T005]] — `[◉ ACTIVE]`（本批 partial-answered → 继续 active）
> rank-diff 跨 direction 泛化仍 ACTIVE。本批 C001/C002/C004/C005 rank-diff 跨 direction 尝试全 reject（RHS=overnight_5 饱和），但 C006 用 sign 聚合 + amount RHS 达成第二种跨 direction 路径。T005 下一步：避开 RHS=overnight_5，转攻 sign 聚合 × 其它 basis。

### batch_050 · direction=`ohlc_temporal_aggregation` · admit=1 reserve=1 reject=4 total=6

## 方向级反思

**direction 状态变化**: `saturated → productive` (5 round 0-admit 后突破). admit 率从 14% (3/21) 调整为 4/27=15%, 但本次突破依赖 rank-diff geometry 而非传统 OHLC 设计. 

**已确认饱和的 OHLC 子空间**:
- standalone OHLC ratio (b017-021 全 reject 除 F006/F007/F008 admit)
- 5d Mean of body_ratio / close_position / upper_shadow magnitude (Mean-based 已饱和)
- intraday return / intraday body sign (random walk 不可救)

**仍开放的 OHLC 子空间**:
- **higher moment OHLC** (Std/Skew/Kurt of body_ratio, upper_shadow, open_position) — C005 首探
- **OHLC × price_vol cross-family rank-diff** (本批 C005 RHS) vs **OHLC × turnover/amount** (C001/C002/C004 共振)
- **OHLC 标量化与 fundamental basis** (C004 失败 + C002 边界——pb 与 OHLC LHS 共振 size)
- **3d/7d rolling Std body_ratio** (本批 only 20d，window sweep 待探)

**Library 健康度**: ohlc_temporal_aggregation 4/(18+1)=21%, 仍可控. F019 (C005) 独立性 max_corr=0.27 优于 F018 (0.62), 库结构性更健康.

**5 次 rank-diff cross-family tipping point 触发 Phase 5 consolidation**:
- **建议升格 lessons.md 新 section "rank-diff geometry"**: 内容包括 (1) RHS 端共振饱和律 (b049 lesson); (2) higher-moment LHS 是独立轴 (本批 lesson); (3) sign aggregation 需 underlying drift (本批 lesson); (4) cross-family generalization 需 LHS+RHS 都跳出 cluster.
- **跨 5 direction**: microstructure (F015/F016) + overnight (F017/F018) + ohlc_temporal_aggregation (F019) — rank-diff 已成系统级 paradigm.

## 跨候选对比

**LHS 多元化结构 (本批 6 LHS 全唯一)**:
- C001: `Mean(body_ratio, 5)` — magnitude mean
- C002: `Mean($close/$high, 5)` — close ratio mean
- C003: `Mean(intraday_return, 5)` — return mean (random walk)
- C004: `Mean(gap_to_range, 5)` — overnight gap mean (与 F010/F011 共振)
- C005: `Std(body_ratio, 20)` — **higher moment (Std, 整批唯一)**
- C006: `Mean(Sign(body), 5)` — sign mean (与 F018 sign 几何 LHS=overnight 不同 — random walk)

**关键 admit 路径分析**: 6 LHS 中只有 C005 在两个维度上同时超越饱和：(1) **OHLC 家族** higher moment (Std vs 库内全 Mean-base)；(2) **rank-diff RHS 端** price-vol (vs F015/F016/F017/F018 的 amount/turnover/overnight 基准)。两个新维度叠加 → max_corr=0.270 整库唯一<0.30。

**reject 模式分类**:
- **library cluster 共振 reject (C002, C004)**：max_corr 0.61/0.66 + 与 5 库因子 ≥0.45 — `cross-family rank-diff 必须 LHS+RHS 都跳出已饱和 cluster`，半数失败 → reject
- **random walk LHS reject (C003, C006)**：纯 intraday return / intraday body sign 在 csi1000 5d 无 persistent drift；rank-diff 几何不能转 random walk 为 alpha
- **alpha_surv 单 dealbreaker reserve (C001)**：rank-order 真实但库空间 borderline 0.50 + alpha_surv 单 flag — calibration §Step 1 标志，pending

**与 b049 C006 admit 范式对照**: 
- b049 C006 (admit F018): LHS=Mean(Sign(overnight),20) — overnight 有 institutional accumulation drift
- 本批 C006 (reject): LHS=Mean(Sign(close-open),5) — intraday body 是 random walk
- **教训**: sign 聚合 paradigm 的 alpha 来源是 underlying field 的 persistent drift, 而非 Sign() 操作本身. 不能盲目跨字段泛化 sign aggregation.

**与 b049 C001/C005 (Mean|ret| vs L2 RealizedVol) 对照**:
- b049: L1 vs L2 vol family 同批冗余（IC -0.055/-0.055 几乎相同）
- 本批: Mean(body_ratio,5) (C001) vs Std(body_ratio,20) (C005) - 不同 moment, 不同 corr structure (C001 IC=0.044 / C005 IC=0.039 但 max_corr 0.50 vs 0.27 完全不同)
- **新教训**: **不同 moment of same atomic signal 不冗余** (Mean vs Std 是不同 family); 但 L1 vs L2 of same moment 冗余 (b049). **moment 选择是 rank-diff LHS 设计的独立轴**.

**Style 聚合**: 6 候选 dominant_style 全 vol_20d. C005 crowding=medium (整批唯一非 high), 其余 high. **OHLC 5d aggregation 天然 vol_20d 暴露** — direction structural constraint.

**MT 预算**: direction_candidates 22 → 28 接近 70 上限; 本方向 saturated → 重启 productive (C005 admit 突破), 但 MT 高位需注意下批暂停或换 direction.

## Thread 进展

> [!success]+ T010 [[directions/ohlc_temporal_aggregation#T010]] 🆕 — `[✓ ANSWERED batch_050]`
> rank-diff 范式第 5 次跨家族兑现且首次在 OHLC 家族——LHS=Std(body_ratio,20) higher moment OHLC + RHS=price_vol 双新维度。max_corr=0.270 整库唯一<0.30 + incr_ic=0.020 健康. **T010 5th cross-family tipping point 正式确认**: F015/F016 (microstructure) + F017 (overnight×turnover) + F018 (overnight_sign×amount) + 本批 C005 (OHLC×price_vol) 跨 4 family 5 admit. → 触发 Phase 5 升格 lessons.md 通用 rank-diff geometry 规则.

> [!failure]+ T011 [[directions/ohlc_temporal_aggregation#T011]] 🆕 — `[✗ DISPROVEN batch_050]`
> sign aggregation paradigm 不能盲目跨字段泛化——LHS 的 underlying field 必须有 persistent drift (overnight ✓ / intraday body ✗). C006 hard_gate 三 fail 验证 b017 C003 教训, 同时反向证 b049 C006 admit 的 alpha 来源是 overnight field 的 institutional accumulation drift, 而非 Sign() 操作几何.

> [!info]+ T012 [[directions/ohlc_temporal_aggregation#T012]] 🆕 — `[◉ ACTIVE]`
> **不同 moment of same atomic signal 不冗余**: Mean(body_ratio) vs Std(body_ratio) 是 rank-diff LHS 设计的独立轴 (C001 vs C005 max_corr 0.50 vs 0.27 显示 moment 改变 corr structure 完全). 下批可探: Skew/Kurt of body_ratio, Std/Mean of upper_shadow / open_position 等 higher-moment OHLC 变体.

> [!note]- T003 [[directions/ohlc_temporal_aggregation#T003]] — `[✓ ANSWERED batch_017-021 + batch_050]`
> direction 从 saturated 重启 productive: 本批 C005 admit 突破 b020 之后 4 batch 0-admit. ohlc_temporal_aggregation 因子库 3→4 (F006/F007/F008 + F019).

### batch_051 · direction=`gap_acceptance_structure` · admit=1 reserve=1 reject=4 total=6

## 跨候选对比

**LHS 多元化结构 (本批 6 LHS 全唯一)**:
- C001: `Mean(gap/(H-L), 20)` — gap acceptance ratio (range-norm)
- C002: `Std(gap_ret, 20)` — **higher moment of F010/F011 atomic** (admit)
- C003: `Mean(|gap|, 60)` — raw |gap| 长窗 (reject hard_gate)
- C004: `Mean(|gap|/|body|, 20)` — cross-session magnitude ratio
- C005: `Mean(gap/(H-L), 5)` — C001 短窗对照
- C006: `Std(gap_ret, 60)` — C002 长窗对照 (reject hard_gate)

**关键 admit 路径分析**: 6 LHS 中只有 C002 在三个维度上同时脱 cluster：(1) **higher moment** (Std vs F010/F011 Mean，验证 b050 T012 律在 gap 家族复现)；(2) **RHS basis 类目** body_ratio (非 amount/turnover/overnight/price_vol 共振 RHS)；(3) **窗口适中 20d** 在 signal_half_life 内。三个维度叠加 → max_corr=0.246 整库最 library-clean。

**reject 模式分类**:
- **hard_gate dilution reject (C003, C006)**：长窗 60d 超 signal_half_life 19d 导致 (a) raw magnitude 被磨损 (C003 ic≈0) / (b) Std 算子在多 regime 窗口失稳 (C006 sign_flip)。**T002 b036 教训第 N 次复现**
- **Barra absorption reject (C004)**：cross-ratio LHS 折叠两个 OHLC magnitude → alpha_survival=0.005 (本批最低)。**rank-diff geometry 不能挽救 LHS 已被 style basis 吸收的因子**
- **rank-diff cluster co-resonance reject (C005)**：max_corr=0.696@F017 + 4 因子 cluster 0.43-0.70。**短窗 price_vol RHS + 短窗 gap LHS 与 F017 (overnight×turnover_5) + F010/F011 (overnight Mean) 必然 cluster — RHS 共振饱和律在 gap 家族首次复现**
- **rank-diff cluster co-resonance reserve (C001)**：max_corr=0.553@F018 + incr_ic=0.008 边际。比 C005 cluster 程度浅 (0.55 vs 0.70)，但仍未脱 — reserve 等待 (a) 与 C002 库独立后再测 / (b) 换 RHS 维度

**与 b050 admit (F019 body_disp×price_vol) 对照**: 
- F019: LHS=Std(body_ratio,20) higher moment OHLC × RHS=price_vol → max_corr=0.270 cluster-clean
- C002: LHS=Std(gap_ret,20) higher moment gap × RHS=body_ratio → max_corr=0.246 cluster-clean
- **跨方向同律**: higher-moment LHS (Std vs Mean) 是 rank-diff geometry 脱 cluster 的关键，b050 在 OHLC 家族验证、本批在 gap 家族复现 — **"higher-moment LHS independence axis" 律横跨 family 兑现**

**与 b049 (F018 overnight_sign × amount_20) RHS 共振对照**:
- b049/b050 已标"RHS 共振饱和律"endpoints: overnight_5 / turnover_5 / amount_20
- 本批 C002 RHS=body_ratio_20 (新 RHS 类目首次 admit) — **扩展 RHS 安全 basis 到 body_ratio_20** (non-resonant 类目)
- C005 RHS=price_vol_20 cluster 共振 reject — **新 dead RHS 类目: short-window price_vol_20** 加入 RHS 共振饱和律 endpoints

**Style 聚合**: 6 候选 dominant_style 全 vol_20d。C002 crowding=medium (整批唯一非 high)，其余 high。**gap 家族 rank-diff 天然 vol_20d 暴露** — direction structural constraint。C002 vol_20d=21.96 < C001 30.5 < C005 38.88 (随窗口收紧 vol 暴露上升).

**MT 预算**: direction_candidates 12 → 18, 远低于 70 上限. 本方向 saturated → productive 重启 (C002 admit + C001 reserve 两个非 reject + 6 跨家族 tipping point 确认).

## Thread 进展

> [!success]+ T005 [[directions/gap_acceptance_structure#T005]] 🆕 — `[✓ ANSWERED batch_051]`
> rank-diff 范式第 6 次跨家族泛化首次在 gap 家族兑现——C002 LHS=Std(gap_ret,20) higher-moment gap atomic + RHS=body_ratio_20 新 basis 类目。max_corr=0.246@F016 整库唯一 <0.30 + incr_ic=-0.013 健康. **6 跨 5 family tipping point 已超 b050 标记的 5-family** (microstructure×2 + overnight×2 + OHLC×1 + gap×1)，**Phase 5 consolidation 升格 lessons.md "rank-diff geometry" 通用规则的硬证据完整**.
>
> 同步揭示三个新教训:
> 1. **higher-moment LHS independence axis 横跨 family 兑现**: Std vs Mean 的 corr structure 完全不同律在 OHLC (F019) 和 gap (C002) 家族独立成立
> 2. **新 RHS 安全类目 body_ratio_20**: 扩展 RHS 共振饱和律白名单 — body_ratio (OHLC structural) 非 vol-class basis 可脱 cluster
> 3. **新 dead RHS 类目 price_vol_20**: 短窗 price-vol RHS (Mean(Std($close,5),20)) 与 F017/F010/F011 短窗 overnight cluster 共振 — 加入 RHS 共振饱和律 endpoints

> [!failure]+ T006 [[directions/gap_acceptance_structure#T006]] 🆕 — `[✗ DISPROVEN batch_051]`
> raw |gap| 长窗 60d (C003) + Std(gap_ret) 60d (C006) 双 hard_gate fail. **T002 b036 教训第 N 次复现**: gap 家族信号在 csi1000 上必须 (a) scale-free normalization (raw |gap| 被股价水平 dominate → ic≈0) (b) 窗口 ≤20d (60d 包含 2-3 regime cycle → Std 算子失稳更甚 Mean)。**Std 算子比 Mean 算子对窗口长度更敏感**.

> [!info]+ T007 [[directions/gap_acceptance_structure#T007]] 🆕 — `[◉ ACTIVE]`
> cross-ratio LHS (C004 |gap|/|body|) **不能挽救 Barra 完全吸收**: alpha_surv=0.005 极端 collapse — 两个 OHLC magnitude 折叠后投影完全在 Barra book-to-price + vol_20d 子空间. rank-diff geometry 不替代 Barra orthogonality. **新失败模式**: ratio of two raw magnitudes (cross-session 或 within-session) 在 rank-diff 几何中是 style projection 的 rank rotation, 非新 alpha. 下批可探: ratio of two **rank-transformed** magnitudes 是否同病; 或 ratio + sign 复合是否破解.

### batch_052 · direction=`value_liquidity_interaction` · admit=0 reserve=0 reject=6 total=6

## 跨候选对比

**LHS 多元化结构 (本批 6 LHS 全唯一)**:
- C001: `Std($pe_ratio, 20)` — PE level higher-moment
- C002: `Mean($pe_ratio/$turnover_rate, 20)` — value-per-liquidity ratio
- C003: `Std($pb_ratio*$turnover_rate, 60)` — joint vol of value×liquidity product
- C004: `Std($turnover_rate, 20)` — turnover higher-moment
- C005: `Mean($ps_ratio/$amount, 60)` — PS-per-amount long-window
- C006: `Std(Mean($pb_ratio, 5), 20)` — compound moment (smooth-then-std)

**RHS 多元化结构 (本批避开所有 b051 标 dead RHS endpoints)**:
- C001/C006 类: `Mean(Std($close, 5), 60)` 长窗 / `Mean(Std($turnover_rate, 5), 20)` turnover micro-vol
- C002/C005: `Mean(body_ratio, 20/60)` body_ratio 不同窗口
- C003: `Mean(|daily_return|, 60)` Amihud-numerator 全新 RHS basis
- C004: `Mean($pb_ratio, 60)` PB 长窗 fundamental basis

**关键失败模式分类**:

1. **基本面 second-order moment 跨 regime sign_flip (C001 + C003)**: PE Std + PB×turnover joint vol 都在 train/validation 翻号——揭示一条新规律：**raw 基本面字段（PE/PB/PS 及其与 liquidity 字段乘积）的 higher-moment (Std/Var) 在 rank-diff 几何中天然 regime-sensitive**。区别于 lessons.md 已 promote 的 PE_rate (Div(Delta,X)) 死区——本失败模式攻击 raw level 的 second-order moment，是更基础的死区。**candidate to promote**: "fundamental second-order moment regime-sensitivity" 升格 lessons.md "Promising Unexplored" 反向条目。

2. **compound moment LHS over-fit (C006)**: ls_t_is=12.18 → ls_t_oos=-0.13 是史上最戏剧 IS-OOS 崩塌之一。`Std(Mean(X,5),20)` 嵌套结构在 train 期 fit noise (IS 强极致)，OOS 完全消失。与 b051 admit C002 单层 `Std(gap_ret,20)` 行为完全相反——**单层 higher-moment 是 alpha 源头，嵌套 compound moment 是 over-fit 源头**。新 lessons 候选。

3. **value × liquidity ratio 必 cluster F002 (C002 + C004 + C005)**: 三个不同结构候选 max_corr 都在 0.40-0.47 落入 F002 cluster：
   - C002: max_corr=+0.40@F020 (rank-diff family 共振) — body_ratio_20 RHS 第二次复用退化
   - C004: max_corr=-0.45@F002 (反向 cluster — value-liquidity dual)
   - C005: max_corr=+0.47@F002 (amount 分母 dual)

   **共振 anchor 不是 RHS 共振饱和律里的 endpoints，而是 F002 本身**——F002 在本方向占据结构性中心位置，任何含 PB/PS/PE × amount/turnover 的几何排列都会与之 cluster。**这是 RHS 共振饱和律在 saturated direction 的进阶形态：not RHS-anchored, but factor-anchored**。

4. **Barra 吞噬光谱在本批完整呈现**: alpha_surv 跨度 0.12 (C005 严重) → 0.46 (C002 borderline) → 0.96 (C004 clean)。**alpha_surv 高 ≠ admit**——C004 是本批 CP04 最干净，但仍因 CP3 weak + CP5 cluster reject。**复现 b051 升格规律 "Barra-clean ≠ library-clean"** 在新方向。

**与 b051 admit (F020 gap_vol×body_ratio) 对照**:
- F020: LHS=Std(gap_ret,20) higher-moment + RHS=body_ratio_20 → max_corr=0.246 cluster-clean → admit
- 本批 C002: LHS=PE/turnover ratio + RHS=body_ratio_20 → max_corr=0.398 cluster co-resonance → reject

  **教训**：F020 admit 后 body_ratio_20 RHS 从"安全类目"退化为"共振 RHS"。**RHS 共振饱和律是动态的——admit 一个就消耗一个 RHS 类目的库余量**。下次复用 body_ratio_20 RHS 必须 max_corr@F020 < 0.30 + LHS 完全脱离 OHLC family。

**Style 聚合**: 6 候选 dominant_style 全 vol_20d。本方向 value × liquidity 几何天然带 vol_20d 暴露 (b051 同观察)——结构性约束。

**MT 预算**: direction_candidates 21 → 27, 远低于 70 上限。但本方向 7 轮 (含本批) 仅 1 admit，**reserve 累计 0** (本批也 0 reserve)，MT 预算空闲不构成放宽阈值依据。

## Thread 进展

> [!failure]+ T002 [[directions/value_liquidity_interaction#T002]] — `[✗ DISPROVEN batch_052]`
> Size × Liquidity 反转线程 (size proxy 红线下设计的 PE/PB/PS × turnover/amount rank-diff geometry) 在本批 6 候选完整投放后宣告 **DISPROVEN**。三条独立机制揭示：
>
> 1. **基本面 higher-moment 跨 regime sign_flip** (C001/C003 双例): PE Std + PB×turnover joint vol 都在 train/validation 翻号 → 基本面字段 second-order moment 在 rank-diff 几何中天然 regime-sensitive
> 2. **value × liquidity ratio cluster F002 anchor** (C002/C004/C005 三例): F002 在本方向是结构性 anchor，任何含 amount/turnover 分母的几何排列都被 0.40-0.47 cluster 锁死
> 3. **compound moment LHS over-fit** (C006): 嵌套 smooth-then-std 结构 IS=12.18 → OOS=-0.13 戏剧崩塌
>
> **结论**: rank-diff 范式第 7 次跨家族泛化在 value × liquidity 失败——证明 rank-diff geometry 不是万能。saturated 方向中 F002 anchor 已锁死该家族 60%+ alpha 空间。

### batch_053 · direction=`intraday_price_formation` · admit=0 reserve=1 reject=5 total=6

## 跨候选对比

**LHS 多元化结构 (本批 6 LHS 全唯一)**:
- C001: `Std((close-open)/(high-low), 20)` — signed body-position higher moment (区别于 F019 Abs(body_disp) Std)
- C002: `Mean((close - OHLC4_mean)/(high-low), 20)` — VWAP-proxy 4-field mean deviation (hard_gate fail)
- C003: `Mean((high-low)/prev_close, 20)` — true_range/prev_close level
- C004: `Std((high-low)/prev_close, 20)` — true_range/prev_close higher moment
- C005: `Mean((close-open)/close, 20)` — signed intraday return level
- C006: `Std((close-open)/close, 20)` — signed intraday return higher moment

**RHS 多元化结构**:
- C001/C003/C005: `Mean(|ret|, 60)` 或 `Mean(Amihud, 60)` Amihud-numerator/denominator family 长窗
- C002: `Std/Mean amount, 60` amount_cv 长窗
- C004/C006: `Mean(Std($close,5), 60)` RV_60 (b051 admit C002 同款)

**关键失败模式分类**:

1. **F020 anti-anchor cluster (C001 例)**: F020 = `Sub(CsRank(Std(gap_ret,20)), CsRank(Mean(body_disp,20)))`，C001 = `Sub(CsRank(Std(body_pos,20)), CsRank(Mean(|ret|,60)))` — LHS 都是 intraday OHLC higher-moment，但因 CsRank Sub 算子是反对称的 + LHS 同源 + RHS 不同 → 形成 ρ=-0.694 强反向 cluster。**新律候选**：rank-diff 几何中 LHS atomic 同源会形成跨候选 anti-cluster，admit 一个就锁死同源 LHS 的整片几何空间。

2. **F012 anchored RHS cluster (C003 + C005 双例)**: F012 = Amihud_20。本批 C003/C005 都用 Amihud-numerator 长窗 60d 作 RHS → 都被 F012 反向 cluster -0.69~-0.73。**新律候选**: 同 atomic 不同窗口 RHS 与同 atomic 因子形成强负向 cluster — RHS 共振饱和律的"窗口家族"扩展形态：饱和不仅是同窗口同 atom，是同 atom 整窗口家族。

3. **vol_20d structural absorption 在 intraday family 不可剥离 (C003 0.66 + C006 0.37 + C004 0.28)**: 三个 LHS (true_range vol/level, signed_ret Std) 都在 dominant_style=vol_20d high crowding。**rank-diff geometry 通过 CsRank 把 ordinal 化但 vol_20d 暴露在 LHS 字段层就已固化** — CsRank 不能剥离原子层的 style exposure。F019 admit (style_r²=0.23) 比本批 C003/C006 低很多，证 F019 LHS body_disp 比本批 LHS 在 vol_20d 上更轻量。

4. **OHLC algebraic mirror 在 OHLC4-mean 复现 (C002)**: 4-field arithmetic mean (O+H+L+C)/4 在 csi1000 上 ≈ close (4 字段中位数集中度高)，导致 (close - OHLC4_mean)/range ≈ 0 + 高频噪声。**升格教训**: OHLC algebraic mirror 律不仅在两字段反相关 (上影线 vs close/high)，多字段 arithmetic mean 也是同律的 degenerate 形态。

**与 b052 反思对照**:
- b052 揭示"基本面 higher-moment regime sign_flip" + "factor-anchored cluster RHS 动态律 (F002 anchor)" + "compound moment LHS over-fit"
- b053 在 OHLC family 揭示**结构对称形态**: F020 anti-anchor (LHS 同源) + F012 RHS 窗口家族 anchored cluster + vol_20d 不可剥离
- **rank-diff 范式两次连续中断 (b052 + b053) 共揭示 6 条新限制**: rank-diff 不是万能钥匙的边界正在迅速被定义清楚。Phase 5 consolidation 升格 lessons.md 的硬证据进一步累积。

**Style 聚合**: 6 候选 dominant_style 全 vol_20d。**intraday OHLC family 天然 vol_20d 重暴露 — 与 b051 C001/C002 不同 (gap_ret 是 intraday-overnight 边界, vol_20d 暴露轻**)。

**MT 预算**: direction_candidates 16 → 22, 远低于 70 上限。本方向 5 轮 (含本批) 仅 2 admit + 0 reserve (本批 reserve 为方向首个), MT 预算空闲不构成放宽阈值依据。

## Thread 进展

> [!failure]+ T003 [[directions/intraday_price_formation#T003]] — `[✗ DISPROVEN batch_053]`
> rank-diff geometry × intraday family 第 7 次跨家族泛化 **失败**。本批 6 候选完整投放后揭示三条独立机制：
>
> 1. **F020 anti-anchor cluster** (C001): 同源 LHS atomic 在 rank-diff 中形成跨候选 anti-cluster, admit 一个锁死同源几何整片
> 2. **F012 anchored RHS 窗口家族 cluster** (C003 + C005): Amihud_20 与 Amihud-numerator_60 跨 atomic-family 而非仅同窗口的 RHS 共振饱和律
> 3. **vol_20d 在 intraday OHLC family 不可剥离** (C003 0.66 + C006 0.37): CsRank ordinal-化无法剥离 LHS 字段层固化的 style exposure
>
> **结论**: rank-diff geometry 不是万能。intraday_price_formation 在 OHLC scale-invariant atom 几何空间已穷尽 (b011 标 saturated 时是 raw level Mean 死区, b053 现在 rank-diff geometry 同 family 死区)。下次再开本方向需 (a) Python residual 路径剥离 vol_20d 暴露 / (b) 引入 minute-bar / tick 数据 / (c) 与 fundamental-momentum 全新 family 复合。

### batch_054 · direction=`barra_residual_alpha` · admit=0 reserve=0 reject=6 total=6

## 跨候选对比

**LHS 多元化结构 (本批 6 LHS 全唯一)**:
- C001: CsRank(Mean(\|residual\|, 20)) — 残差 dispersion 水平
- C002: CsRank(Std(residual_ret, 20)) — 残差 second-moment
- C003: CsRank(Sum(residual_ret, 5)) — 残差短窗动量
- C004: residual lag-1 autocorr_20 — 残差时序结构
- C005: EMA(res,5) − EMA(res,20) — 残差多周期 decay 差
- C006: \|Sum(res,20)\| / Sum(\|res\|,20) — 残差 SNR

**RHS 多元化结构 (rank-diff 候选)**:
- C001: CsRank(Mean($turnover_rate, 20)) — 流动性原子
- C002: CsRank(Mean($amount, 60)) — amount 长窗
- C003: CsRank(Mean(Std($close, 5), 60)) — RV_60 (b051 admit C002 RHS)
- C004/C005/C006: 无 RHS（pure residual-only 路径）

**关键失败模式分类**:

1. **residual + rolling 数据契约层 fail (5/5 可计算候选 coverage<0.80)**: 这是**新发现**——F004 admit (batch_012) 时 coverage=0.999 因 F004 是 residual 本身（无后续 rolling），本批所有候选都对 residual 做 rolling Std/Sum/EMA → coverage 暴跌至 0.71-0.73。机理：(a) cross-sectional Barra residual 已有 ~1% NaN（style 缺失传播）；(b) rolling 算子 min_periods≥10 要求每只标的连续历史；(c) csi1000 上市日异质性；(d) 三者复合后早期日期 ~30% 标的 NaN，全期均值 coverage = 0.71 << 0.80。**升格 lessons.md 候选**："Python residual + rolling 在 csi1000 系统性 coverage ≈ 0.71，hard_gate 0.80 阈值与 residual paradigm 结构性不兼容"。

2. **Python factor 数据契约缺口二次复现 (C001)**: T003 thread 揭示的"loader 忽视 Python factor REQUIRED_FIELDS 声明"在 b015 C002 之后第二次独立触发——本 C001 missing $turnover_rate。**T003 thread 推进到 [已二次复现 待系统修复]**，升格 lessons.md "Python factor 数据契约 hard_gate 候选" Promising Unexplored 反向条目。

3. **残差 higher-moment regime sensitivity 第三次跨方向复现 (C002 + C003)**: C002 mono_sign_flip + C003 sign_flip 都在 train/validation 翻号——同律 b052 C001 (PE Std)、b053 C001 (signed body-pos Std)。**3 次独立确认 → 升格 lessons.md**: "higher-moment LHS（Std/Var/cumsum 类二阶聚合）在 train (低利率) vs validation (利率上行) regime 系统性翻号——这是跨方向（fundamental/intraday/residual）三层独立证实的硬律"。

4. **残差路径几何 statistic 在日频是 noise (C004 + C006)**: residual autocorr 和 directional efficiency 都 IC magnitude < 0.01。机理：残差已剥离 alpha-bearing component，对其再做 path coherence/persistence 类 transformation 不能再生 alpha。**与 [[directions/barra_residual_alpha#Lessons]] 第 1 条"时序平滑/标准化不改 cross-sectional rank"互补**：本批进一步——残差时序 statistic 本身在 IC magnitude 上 sub-threshold。

**与 b052/b053 反思对照**:
- b052 揭示"基本面 higher-moment regime sign_flip" + "factor-anchored cluster RHS 动态律 (F002 anchor)" + "compound moment LHS over-fit"
- b053 揭示"F020 anti-anchor cluster" + "F012 anchored RHS 窗口家族 cluster" + "vol_20d 在 intraday family 不可剥离"
- b054 在 residual family 揭示**4 条独立机制**：(1) residual+rolling coverage 数据契约层 + (2) loader REQUIRED_FIELDS 缺口 + (3) 残差 higher-moment regime sensitivity (跨方向三层) + (4) 残差路径几何 noise
- **rank-diff 范式三次连续中断 (b052 + b053 + b054)** 共揭示 **9-10 条新限制律**：rank-diff 不是万能钥匙的边界正在迅速被定义清楚。**Phase 5 consolidation 升格 lessons.md 的硬证据进一步累积**。

**Style 聚合**: 6 候选 dominant_style 全 vol_20d。残差化未能剥离 vol_20d cluster——验证 [[directions/barra_residual_alpha#T002]] 已 promote 的 lesson"vol_20d 主导残差空间"在残差 rolling statistic 上仍成立（不仅 residual 本身）。

**MT 预算**: direction_candidates 21 → 27, 远低于 70 上限。本方向 7 轮 (含本批) 仅 1 admit (F004)，**reserve 累计 0 + 本批也 0 reserve**，MT 预算空闲不构成放宽阈值依据。

## Thread 进展

> [!failure]+ T014 [[directions/barra_residual_alpha#T014]] — `[✗ DISPROVEN batch_054]`
> rank-diff geometry × residual signals paradigm（barra_residual_alpha 复活路径）在本批 6 候选完整投放后宣告 **DISPROVEN**。四条独立机制揭示：
>
> 1. **数据契约层结构性 coverage<0.80**: residual + rolling 在 csi1000 系统性 coverage=0.71-0.73 (5/5 候选), 与 hard_gate 0.80 阈值结构性不兼容。这一层失败不能通过信号设计修复——必须 (a) 修改 loader 使 residual 不传播 NaN / (b) 改用 cross-sectional 算子代替 rolling 算子 / (c) 接受残差 base 信号（不做 rolling，但那就是 F004 本身）。
> 2. **Python factor 数据契约 (T003) 二次复现**: C001 missing $turnover_rate, 9 批之后第二次同律失败, **T003 升格为系统级修复优先级 high**.
> 3. **残差 higher-moment regime sensitivity (跨方向三次确认)**: 残差 Std/cumsum 在 train (低利率) vs validation (利率上行) 翻号——加上 b052/b053 的 fundamental + intraday family，**这是跨 3 大 family 独立证实的硬律**。
> 4. **残差路径几何 statistic 是 noise**: autocorr / directional efficiency 类信号 IC < 0.01 量级，残差已剥离 alpha-bearing component 后无法再生。
>
> **复活路径再次缩窄**：[[directions/barra_residual_alpha#Hypothesis|hypothesis 复活条件]] (a) 非 Barra style basis / (b) nonparametric residualization / (c) 与库非线性 ensemble 三条仍未尝试。**rank-diff × residual 路径 (T014) 已穷尽**。

> [!warning]+ T003 [[directions/barra_residual_alpha#T003]] — `[已二次复现 → 升格修复优先级 high]`
> Python factor REQUIRED_FIELDS loader 缺口在 C001 missing $turnover_rate 第二次独立触发（首次 b015 C002 missing $high/$low）。**T003 thread 中期方案推进至必须优先实施**: (a) Phase 1 freeze 静态 validate `set(REQUIRED_FIELDS) ⊆ load_market_data` 默认列；(b) load_market_data 接受 candidates union(REQUIRED_FIELDS) 动态扩列。

### batch_055 · direction=`range_structure` · admit=1 reserve=0 reject=5 total=6

## 方向级反思

**range_structure direction 实现首次 admit**（status: exploring → productive），结束 3 rounds 0-admit 历史。但应清醒认识本批 1/6 通过率说明的几件事：

1. **rank-diff geometry 7 律 + factor-anchored cluster 检查**已达到极高的设计门槛——5/6 candidate 在 max_corr 都 < 0.55 看似独立，incremental_ic 却全部 ≤ 0。这验证了 P005 RHS basis 共振饱和律的**动态性**：即使没有显式 RHS 重复，多个独立 RHS 通过 vol_20d common cause 仍构成"组合层冗余"。
2. **C005 admit 的成功要素**特别值得归纳：(a) LHS atom 是 close 在 H-L 范围内的位置（intraday position 维度），不是 range/body magnitude；(b) RHS Mean(H/L, 60) 是 long-window 几何 ratio (60d，与短窗 RHS 区分)；(c) style_crowding=medium 是 6 候选中唯一不 high 的；(d) cum_mdd=-1.14 是库内极罕见的"几乎从未失效"。这些条件**联合**才能通过门槛。
3. **下一步建议**:
   - **优先**：在 intraday position 维度沿 C005 atom 衍生（如 (C-L)/(H-L) Std, (C-prev_close)/(H-L) Std, body_position 等）× 不同 long-window scale-free RHS（不再尝试 short-window vol_20d-prone RHS）
   - **避免**：60d 长窗 + raw size/value RHS（C006 教训）；sign aggregation as RHS（C003 教训）
   - **TsKurt 路径**：operators.py:428 bug 阻塞了 P002 endorsed 的 higher-moment LHS 升级 — 需要 Python escape hatch 或修复 _build_cs_cache 让 D.features 接收已计算 LHS 数组而非 expression string
4. **status 调整**：`exploring → productive`（首次 admit），`priority: low → medium`（admit 验证 direction 仍有可挖空间）

若下一轮 (round 4) 沿 C005 衍生路径仍 0 admit + incremental_ic ≤ 0 ratio ≥ 80% → `productive → saturated`。

## 跨候选对比

**Style 聚合 (本批 6 候选共性)**：
- 全部 6 候选 `dominant_style_exposure = vol_20d`，exp 范围 **18.8 (C005) – 58.1 (C003)**
- C005 vol_20d exp 最低 (18.8)、style_r² 最低 (0.20)、style_crowding `medium`（其它 5 个全 `high`）——这是 C005 admit 的关键差分
- C003 + C006 是双 style 灾难：C003 vol_20d=58.1 + str_1m=3.84；C006 vol_20d=30.9 + log_circ_cap=0.586 + alpha_surv=0.71 假象
- C004 ep_ratio exp=1.94（最高 value 暴露），LHS (H-L)/prev_close 触 F005 algebraic mirror

**Incremental_ic 一览**（库增值真实性最关键指标）：
- ✅ C005 = **+0.008** (库增值)
- ❌ C001 = -0.013, C002 = -0.008, C003 ≈ 0, C004 = -0.007, C006 = -0.012
- **5/6 incremental_ic 负或 ≈0**——这是本批最强结构性发现：**rank-diff geometry 已饱和到这种程度，新候选不仅不能加 corr 独立性，连库 IC 增量都拿不到**。这是 P004 vol_20d 结构性吸收律 + P005 RHS basis 共振饱和律的联合表现：5 个 RHS (volume_60/pe_60/up_freq_20/VWAP_60/range_compress_60/circ_market_cap_60) 中只有 range_compress_60 (C005 RHS) 真正独立。

**MT 预算推进**：cumulative 282 → 288；direction 6 → 12；bucket high → search_adjusted medium。range_structure direction 在本批 admit 后 round=3, admits=1, status: exploring → **productive**。

**ls_t IS/OOS 翻号 / 衰减**（Validation regime stability）：
- C001: IS+2.42 / OOS-0.40 (翻号)
- C004: IS-3.02 / OOS-0.65 (大幅衰减 0.22)
- C006: IS+2.06 / OOS-0.62 (翻号)
- C003: IS-5.23 / OOS-1.39 (大幅衰减 0.27)
- C005: IS+1.61 / OOS+2.38 (**OOS 增强 1.5x，唯一 IS→OOS 同向且增强的候选**)

C005 在 train_validation_decay=1.96 是"信号增强型"（IS<OOS）而非 inflated——结合 ic_by_year 单调增强趋势，证明这是 regime-robust 的真实 alpha 而非 IS overfit 表象。

## Thread 进展

> [!success]+ T001 [[directions/range_structure#T001]] — `[✓ ANSWERED batch_055]`
> 答案：(1) 是的，range 结构化 transformation **能**在 cross-section 上逃 vol_20d——具体路径是 **upper-shadow position dispersion (Std of (H-C)/(H-L)) × long-window range compression (Mean of H/L) rank-diff**（C005 → admit）。(2) 但 admit 路径精度门槛极窄：6 候选只有 1/6 通过，5/6 因 incr_ic ≤ 0 库减值被拒。(3) Kurt-centric 路径在 DSL 下被 operators.py:428 bug 阻塞（C002/C006 用 Std 替代均失败），需要 Python escape hatch 或 bug 修复。
>
> **Evidence trail (本批新增)**:
> - [[batches/batch_055/candidates/C001|batch_055 C001]] range Std × volume_60 ls_t=-0.40 incr=-0.013 → **reject** (F012 reducer)
> - [[batches/batch_055/candidates/C002|batch_055 C002]] Garman range Std × pe_60 mono=-1.0 ls_t=-2.92 incr=-0.008 → **reject** (rank-diff cluster reducer)
> - [[batches/batch_055/candidates/C003|batch_055 C003]] H/L Std × sign_freq_20 vol_20d=58.1 incr≈0 → **reject** (sign-RHS 未起独立维度)
> - [[batches/batch_055/candidates/C004|batch_055 C004]] (H-L)/prev_close Mean × VWAP_60 mono paradox -1.0→-0.30 incr=-0.007 → **reject** (b043 C004 同 paradox)
> - [[batches/batch_055/candidates/C005|batch_055 C005]] (H-C)/(H-L) Std × H/L Mean_60 ic=+0.043 mono=+1.0 cum_mdd=-1.14 incr=+0.008 → **admit**
> - [[batches/batch_055/candidates/C006|batch_055 C006]] Std((H-L)/C, 60) × market_cap_60 style_r²=0.75 incr=-0.012 → **reject** (Std60 ≠ Kurt-equivalent)

### batch_056 · direction=`range_structure` · admit=0 reserve=1 reject=5 total=6

## 方向级反思

**range_structure direction 在 batch_056 round 4 后**：admit=0 / reserve=1 / reject=5；累计 admits=1 (F021 from b055 C005), reserves=2 (b043 C003 + 本批 C001), 已封闭路径增加到 5+ atom variants。本批揭示几个关键动态：

1. **rank-diff geometry library reducer 第 5 次复现** (b042 C005 / b043 C005-C006 / b045 C006 / b055 C002 / 本批 C004)：mono_oos=+1.0 + ls_t_oos=4.62 strong 但 incr_ic=-0.0024 + alpha_surv=0.27——"strong-but-negative-incr"陷阱第 5 次独立确认，应升格 lessons.md 的 Promising Patterns 反例段。该模式的判别要件已稳定：mono_oos≥0.9 + |ls_t_oos|≥3.0 + incr_ic<0 + alpha_surv<0.30。

2. **C006 alpha_survival 极端 poor (0.0725)** + ic_oos 表面 strong (+0.025) 揭示"vol_20d IC 假象"诊断要件的细化：当 alpha_survival << 0.10 (而非接近 threshold 0.40) 时，IC 几乎完全由 vol_20d + turnover_20d + str_1m 三大 style 解释——本批 vol_20d_exposure=30.67 + style_r²=0.21 仅 borderline，但 alpha_survival 跌至 0.0725——表明 style_r² 单一指标不充分（C006 style_r² 仅 borderline 但 alpha 全被 style 占走），alpha_survival 是更敏感的"残余 alpha 真实性"指标。

3. **C001 reserve 是否真错杀 (calibration trigger 候选)**：C001 满足 6 项 alpha-side 健康指标 (ic_oos=0.021 strong / mono_oos=+1.0 完美 / sign_consistency=1.0 / cum_mdd=-4.06 极浅 / incr_ic=+0.0085 库增值 / ic_by_year U-shape 近 3 年同号加强)；但 alpha_survival=0.24 < threshold 0.40 (CP04 poor) + style_r²=0.17 边界 + ICIR=0.17 weak (CP03 borderline) + max_lib_corr=0.50 medium 阻止 admit。**诊断**：dominant_style=vol_20d (exp=7.96) 在本 family 是最低 vol_20d exp，但 alpha_survival 仍仅 0.24——可能是真实"vol_20d 残余 alpha"被吞噬，或库重叠 (与 F019 max_corr=0.50) 把残余信号也分走。**建议**：等待 round 2 沿 C001 atom 衍生 1-2 个独立 RHS 候选 (避开 amount/volume，试 H/L 60d 几何 ratio 等)，再判断 C001 是否系统性错杀。

4. **下一步建议**:
   - **优先**：sub-path A — 沿 C001 (O-L)/(H-L) atom 衍生 × 不同 long-window scale-free RHS (H/L 60d 几何 / 其它 turnover-orthogonal 长窗 ratio)，验证 open lower-shadow position 维度是否可继续扩展
   - **优先**：sub-path B — (C-L)/(H-L) Std (lower-shadow-close-position) × C001 同款 long-window scale-free RHS，对比 close-anchored vs open-anchored 在 lower-shadow 几何上的差异
   - **避免**：daily return / overnight gap as numerator (b056 C003/C004/C005 教训)；composite midpoint deviation (b056 C006 教训)；pe/pb / pe/ps / turnover/pb 60d 类 fundamental 复合 RHS (b056 C002/C004/C005 三连 reject)
   - **TsKurt 路径**：operators.py:428 bug 仍阻塞——可考虑 Python escape hatch 路径在 sub-path A/B 完成后启动

5. **status 调整**：`status: productive` 保持（C001 reserve 维持 family 可扩展嫌疑 + 库增值数据点）；`priority: medium` 保持（admit=0 但 reserve 数据点真实，未达 saturated 触发）。

若 round 5 沿 C001/C005 衍生路径仍 0 admit + 80%+ candidate incremental_ic ≤ 0 → `productive → saturated`。

## 跨候选对比

**Style 聚合 (本批 6 候选共性)**：
- 6 候选 `dominant_style_exposure` 全部 = `vol_20d`，exposure 范围 **7.96 (C001) – 47.2 (C003)**
- C001 vol_20d exp 最低 (7.96)、style_r²=0.17 borderline、alpha_surv=0.24 poor 但 incr_ic=+0.0085 正——这是 reserve 与全 reject 的关键差分
- C003 vol_20d=47.2 极端 + str_1m=1.15 + ep_ratio=1.78 → 三 style 灾难
- C006 vol_20d=30.67 极端 + turnover_20d=4.13 + str_1m=0.98 → 双 style + IC 假象典型
- C004 ep_ratio exp=1.30 + alpha_surv=0.27 poor + incr_ic=-0.0024 → "strong-mono + strong-ls_t but library reducer" 第 5 次复现 (b042 C005 / b043 C005-C006 / b045 C006 / b055 C002 / 本批 C004)

**Incremental_ic 一览**（库增值真实性最关键指标）：
- ⏸ C001 = **+0.0085** (库增值, 唯一)
- ❌ C002 = N/A (hard_gate fail)
- ❌ C003 = -0.006, C004 = -0.0024, C005 = N/A (hard_gate fail), C006 ≈ +0.001
- **5/6 incremental_ic ≤ 0 或不适用**——本批延续 batch_055 P005 RHS basis 共振饱和律的动态性 (b055: 5/6 ≤ 0)。但 C001 incr=+0.0085 > 0 **打破"全负"模式**，表明在 (O-L)/(H-L) atom + amount/volume RHS 这条具体路径上库增值仍真实——open lower-shadow position 维度尚未饱和。

**MT 预算推进**：cumulative 288 → 294；direction 12 → 18；bucket high → search_adjusted medium。range_structure direction 在本批后 round=4, admits=1, reserves=1, status: `productive` 保持。

**ls_t IS/OOS 翻号 / 衰减**（Validation regime stability）：
- C001: IS+5.52 / OOS+2.51 (衰减 0.45，但同号且 OOS 仍 moderate)
- C002: IS+3.35 / OOS-2.13 (**翻号** + hard_gate fail)
- C003: IS-1.67 / OOS-0.86 (大幅衰减 0.51 + mono 崩塌)
- C004: IS+5.40 / OOS+4.62 (**OOS 增强 ratio 0.85**, 但 incr_ic 负 — strong-but-reducer)
- C005: IS-3.02 / OOS-3.78 (OOS 反向增强 + ic_oos 量级不足)
- C006: IS+2.56 / OOS+0.90 (大幅衰减 0.35 + ls 信号 weak)

C001 是**唯一同号且 OOS 仍 moderate** 的候选，配合 incr_ic+ + cum_mdd=-4.06 + ic_by_year U-shape 近 3 年同号加强 — 真实 alpha 嫌疑高于其他 5 个，但 alpha_survival=0.24 < threshold 0.40 阻止 admit → reserve。

## Thread 进展

> [!note]+ T003 [[directions/range_structure#T003]] — `[◉ ACTIVE]`
> **本批结果 (round 1 of T003)**：T003 假设"intraday position dispersion family 沿 C005 衍生"在本批 6 候选首轮**部分验证、部分证伪**。验证：C001 (Std((O-L)/(H-L), 20) × Mean(amount/volume, 60)) reserve，open-anchored lower-shadow position dispersion atom 拿到 incr_ic=+0.0085 + cum_mdd=-4.06 + 9 年 U-shape 同号 — 证实 family 在 open-anchored 维度可扩展。证伪：C003 (return-per-range) / C004 (overnight-gap-per-range) / C006 (composite midpoint) 三种 numerator 全部 reject，证明并非所有 LHS atom 变体都能逃脱 vol_20d；特别 C002/C005 双 hard_gate fail 表明 RHS basis (pe/pb 60d ROE proxy / turnover/pb 60d composite) 即使设计纪律到位仍可能在 csi1000 IS/OOS 完全反转。
>
> **Evidence trail (本批新增)**:
> - [[batches/batch_056/candidates/C001|batch_056 C001]] Sub(CsRank(Std((O-L)/(H-L),20)), CsRank(Mean(amount/volume,60))) — ic_oos=+0.021 mono=+1.0 cum_mdd=-4.06 incr=+0.0085 max_corr=0.50@F019 alpha_surv=0.24 → **reserve**
> - [[batches/batch_056/candidates/C002|batch_056 C002]] Sub(CsRank(Std((H-O)/(H-L),20)), CsRank(Mean(pe/pb,60))) — hard_gate fail (sign_flip + oos_decay=-4.34) → **reject**
> - [[batches/batch_056/candidates/C003|batch_056 C003]] Sub(CsRank(Std((C-prev_C)/(H-L),20)), CsRank(Mean(amount/(close*volume),60))) — mono collapse -0.90→-0.10 + incr=-0.006 + vol_20d=47.2 + max_corr=0.65@F014 → **reject**
> - [[batches/batch_056/candidates/C004|batch_056 C004]] Sub(CsRank(Std((O-prev_C)/(H-L),20)), CsRank(Mean(pe/ps,60))) — ls_t=4.62 + mono=+1.0 但 incr=-0.0024 + alpha_surv=0.27 (library reducer 第 5 次复现) → **reject**
> - [[batches/batch_056/candidates/C005|batch_056 C005]] Sub(CsRank(Std((H-prev_C)/(H-L),20)), CsRank(Mean(turnover/pb,60))) — hard_gate fail (ic_oos=-0.0042 < 0.008) → **reject**
> - [[batches/batch_056/candidates/C006|batch_056 C006]] Sub(CsRank(Std(((C+O)-(H+L))/(H-L),20)), CsRank(Mean(amount/market_cap,60))) — ic_oos=+0.025 表面 strong 但 alpha_surv=0.0725 极端 + ls_t=0.90 weak + vol_20d=30.67 → **reject** (vol_20d IC 假象典型)
>
> **下一步**：T003 thread 仍 ACTIVE，但应在 C001 reserve 真错杀诊断后再决定 round 2 方向。如 C001 是真实可 admit 信号 (诊断 alpha_survival=0.24 是否 vol_20d Barra orthogonalize 后改善)，则 round 2 沿 (O-L)/(H-L) atom 衍生其它 long-window scale-free RHS；如 C001 是 vol_20d 吸收伪 alpha (与 C006 同模式)，则 T003 sub-path "open-anchored position × VWAP magnitude" 封闭，转 (C-L)/(H-L) Std lower-shadow-close-position 等其它 anchor。

### batch_057 · direction=`vwap_proxy_signals` · admit=0 reserve=1 reject=5 total=6

## 方向级反思

本方向 rounds = 3（batch_040 + batch_042 + 本 batch_057）·admits = 1 (F014, Grade D 37) · 最近 2 批 reject 率：batch_042 = 5/6 (83%) + batch_057 = 5/6 (83%) → 满足 "连续 2+ batch reject > 80%" 转 saturated 触发条件。

**核心证伪累积**：
1. T001 ANSWERED：跨 session VWAP-prev_close (F014) 是唯一 admit，level 形式
2. T002 DISPROVEN：同 session VWAP/close 偏离的 5d/20d 聚合 (level 形式) 全 fail
3. T003 SUSPENDED：daily-anchor VWAP HLC位置 5 子路径撞墙 max_corr@F014=0.79-0.89
4. **T004 (本批) 几乎完全证伪**：higher-moment LHS (Std/Skew) on VWAP-derived scale-free × rank-diff 路径在二阶矩、三阶矩、不同 anchor、不同 RHS 上全部失败或被 cluster+style 压制

**结构性结论**：A 股 csi1000 上 VWAP 基底 (synthesized $amount/$volume) 的可探索路径在日频 DSL 层基本耗尽。F014 是 level cross-session 形式的唯一兑现；higher-moment / momentum / different-anchor 路径都被 (a) F005 OHLC algebraic mirror 共动律 + (b) F001/F301 vol_20d 结构性吸收律 + (c) F017 cluster 共振律 三重夹击。

**下轮建议**：`status: productive → saturated` · `priority: medium → low`。复活条件：
- F017 退役（unlikely 短期）→ C005 可重测
- vol_20d Python residualization 工具链就绪 + coverage 修复 → T003 残差路径 + T004 Skew × residualized 重启
- 非 daily-bar 数据（minute/tick）→ VWAP 微观结构信号根本性逃离

**值得沉淀的元教训**（建议升格 lessons）：
- "higher-moment LHS independence axis on scale-free VWAP-derived ratios" **不能** 跨 family 迁移 — F019/F020 (OHLC body / gap_ret) → VWAP basis 失败。差异：F019/F020 的 atom 是直接价格 ratio（scale-free, vol_20d-independent），而 VWAP-prev gap 本身就嵌入了波动率信息（gap 大小 ≈ 日内波动率），导致 higher-moment 不是"独立 axis" 而是"vol_20d 极端载体"。**lessons.md "Promising Unexplored" 第 1 条需附 caveat**：family-agnostic 律仅在 atom 自身与 vol_20d 正交时成立。
- C003 vol_20d exposure=**48.04** 是整库历史新高（超 b008 C005=32.0），值得记录为方向级 anti-pattern：**VWAP-open 同 session 锚点是 vol_20d 极端载体**。

## 跨候选对比

- **Hard_gate 失败率 4/6 (67%)**：本批最显著结构事实。failure 类型分布：
  - `ic_oos_too_low` ×2 (C001/C006) — 信号体量根本不足，cross-section noise 主导
  - `sign_flip` ×1 (C002) — 短窗口 + range/close RHS 配对 regime 不稳
  - `mono_flip` ×1 (C004) — RHS 换 amount/circ_mktcap 后真实 mono 翻盘
- **C001/C004/C005 共享 LHS** = `Std(VWAP-prev gap, 20)` 或 `Skew(...)` (C005)：同 LHS 不同 RHS 的实验组对比清晰：
  - C001 (turnover_rate Mean 10 RHS) → ic_oos_too_low hard_gate
  - C004 (amount/circ_mktcap Mean 20 RHS) → mono_sign_flip hard_gate
  - C005 (turnover_rate Mean 10 RHS, **Skew 三阶矩 LHS**) → 唯一 reserve（mono=0.9 + cum_mdd=-2.18 + ic_by_year 单调强化）
  - **结论**：相同 LHS 二阶矩 (Std) 形式在两个非饱和 RHS 上都失败；切换到三阶矩 (Skew) 才打通 rank-order — 暗示 VWAP basis 的 higher-moment 路径 **二阶矩 saturated, 三阶矩 partially active**
- **Style 聚合**：2 个进入 CP04 的候选 (C003/C005) 都 dominant_style=`vol_20d`：
  - C003 vol_20d exposure = **48.04** (整库罕见极值，超 b008 C005=32.0 历史最高)
  - C005 vol_20d exposure = 13.96 (高但温和)
  - VWAP basis 在 csi1000 上结构性等价于 vol_20d 高暴露载体 — F005 distillation 律再次验证
- **相关度 cluster**：C003/C005 都 nearest=F017 (overnight×turnover rank-diff)，corr=0.48 / 0.51 — 两个 VWAP-derived rank-diff 都被 F017 吸收 ~25%
- **MT 预算推进**：cumulative 300 → 306（首次破 300 大关）；direction 12 → 18（vwap_proxy_signals 方向 high bucket 巩固，仅次 saturated 边界 20）
- **bucket=high 触发的 verdict 收紧**：C003/C005 都 high bucket → search_adjusted 后 medium，但 high 上界限制本就压制 admit 概率

## Thread 进展

> [!note]+ T004 [[directions/vwap_proxy_signals#T004]] — `[◉ ACTIVE]` (本批启动 thread)
> 6 候选全部归入 T004。结论：**T004 hypothesis (higher-moment LHS on VWAP-derived scale-free × non-saturated rank-diff RHS) 在 cross-section 上几乎完全证伪**：
> - 二阶矩 (Std) 路径：3 候选 (C001/C002/C004) 全 hard_gate fail，证明 Std(VWAP-prev/open gap) 与已尝试的非饱和 RHS (turnover_rate Mean 10 / Med(range/close) / amount/circ_mktcap Mean 20) 配对在 cross-section 上无 stable rank-order
> - 三阶矩 (Skew) 路径：C005 唯一 reserve，rank-order 极优但 vol_20d 严重吸收 + F017 cluster 共振 → 暗示 Skew 是有信号但被 cluster + style 双重压制
> - within-VWAP momentum 路径：C006 ic_oos_too_low — 时间窗内 VWAP 自身相对变化 noise dominated
> - VWAP-open anchor 同 session 路径：C003 完全坍塌 + vol_20d exposure=48.04 整库罕见极值，证伪"开盘锚点 VWAP" 独立性
>
> **Next probes**: 仅有 1 条剩余路径 — 三阶以上矩 (Kurt) 或 Skew × 不同 RHS 探索；但本方向 rounds=3 + admits=1 + 2 batch reject>80% 已满足 saturated 转化条件，建议方向转 saturated。

> [!success]- T001 [[directions/vwap_proxy_signals#T001]] — `[✓ ANSWERED batch_040]` (本批无推进)

> [!failure]- T002 [[directions/vwap_proxy_signals#T002]] — `[✗ DISPROVEN batch_040]` (本批无推进)

> [!note]- T003 [[directions/vwap_proxy_signals#T003]] — `[⏸ SUSPENDED batch_042]` (本批无推进，仍阻塞工具链)
