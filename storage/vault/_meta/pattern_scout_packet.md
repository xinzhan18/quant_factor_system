# Pattern Scout Packet

> Generated at 2026-04-24T16:57:27+00:00 · recent=10 batches

## 任务

你是 Pattern Scout，扫描下方的最近 N 批 judge 摘录 + active directions frontmatter，**识别跨批的失败模式 / style 吸收律 / 重复机制**。只改写 `storage/vault/INDEX.md` 的 `HOT-TOPICS-LLM` sentinel 块。

## 当前 HOT-TOPICS-LLM 块

<!-- BEGIN HOT-TOPICS-LLM -->
> [!warning]- 🔥 Hot Topics（LLM 维护）
> 当前无活跃跨批模式。`/pattern-scout` 只允许改写本块。
<!-- END HOT-TOPICS-LLM -->

## 输出契约（INDEX.md HOT-TOPICS-LLM 块）

只替换 `<!-- BEGIN HOT-TOPICS-LLM -->` 到 `<!-- END HOT-TOPICS-LLM -->` 之间的内容；不要改 INDEX frontmatter、COCKPIT、INSIGHT、Bases embed 或其它 sentinel。

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
| barra_residual_alpha | saturated | low | 6 | 1 | batch_015 |
| fundamental_momentum | dead | low | 1 | 0 | batch_022 |
| gap_acceptance_structure | saturated | medium | 2 | 1 | batch_036 |
| intraday_price_formation | saturated | high | 4 | 2 | batch_011 |
| liquidity_acceleration | saturated | low | 2 | 0 | batch_032 |
| log_value_liquidity | dead | low | 1 | 0 | batch_038 |
| microstructure_illiquidity | saturated | high | 2 | 1 | batch_031 |
| ohlc_temporal_aggregation | saturated | medium | 5 | 3 | batch_021 |
| overnight_intraday_split | saturated | high | 3 | 3 | batch_027 |
| pv_covariance | dead | low | 1 | 0 | batch_039 |
| quantile_shape_signals | dead | low | 1 | 0 | batch_044 |
| range_structure | exploring | medium | 1 | 0 | batch_043 |
| return_distribution_signals | dead | low | 1 | 0 | batch_016 |
| return_momentum_acceleration | dead | medium | 1 | 0 | batch_029 |
| stochastic_position | saturated | low | 2 | 0 | batch_041 |
| trend_quality_gated | dead | low | 1 | 0 | batch_037 |
| turnover_structural_signal | saturated | low | 1 | 0 | batch_004 |
| value_liquidity_interaction | saturated | low | 7 | 1 | batch_034 |
| vol_shock_signals | dead | low | 1 | 0 | batch_024 |
| vwap_proxy_signals | productive | medium | 2 | 1 | batch_042 |

## Recent batches（judge.md 关键段摘录）

### batch_035 · direction=`gap_acceptance_structure` · admit=0 reserve=1 reject=5 total=6

## 方向级反思

`gap_acceptance_structure` 首批即完成 T001 / T003 / T004 三个 thread 的**信息性封闭**。这是一个罕见的高效失败：方向 hypothesis 的**主结构**（pure sign 乘积 + 20d 聚合）经三窗口消融后被 A 股 csi1000 regime 数据硬性证伪；**正交 baseline**（TR 归一 F003 near-duplicate 风险）一次确认为完全子空间吸收；唯一生路是 **T002 turnover 加权**，且首证据（C004）指向 "avoid worst barbell" 而非 monotonic alpha。

这批结果完美印证了 direction.md 预判的**单一最大隐藏假设**："paper 0.0744 Rank IC 来自 CSI 300 大盘，csi1000 小盘下 gap 符号本身噪声过大 → 可能符号不稳"。实测：**不只是符号不稳，而是 2021 regime 起完全反号 + 幅度 collapse**。paper 方法论不可直接 transfer。

**方向操作建议**（Phase 3 标注，Phase 4 由 LLM 在 Narrative Log 中实施）：
- `status: exploring` **保留**（只有 T002 单个 active thread + C004 单一 reserve）
- `priority: high → medium`（大部分 thread 封闭，ROI 下调）
- 下一批 batch_036 聚焦 T002：`$amount / Mean($amount, 20)` 加权 vs C004 `$turnover_rate` 直接加权 vs normalized vol acceptance 三变体对照；若 T002 后续无 admit（≥2 连批 0 admit），方向 `exploring → saturated`

**Calibration（错杀侦测）**：
- 本批 `potential over-rejection` flag = **False**
- C001/C002/C003 hard_gate fail 都是 sign_flip + ic_oos 组合硬阻断，非单指标 dealbreaker；ic_by_year 2021-2023 连续反号是机制证据，不是阈值过严
- C005 near_duplicate 0.964 远超 0.9 硬闸，是结构性冗余而非阈值过严
- C006 IC_OOS 差 0.002 达标，incr_ic=0.0086 < 0.010 dealbreaker，mono_oos=0.3 < 0.8 dealbreaker → 不满足错杀的 4 条件（rank-order 完美 + 库空间独立 + 符号互补 + incremental_ic > 0.01）
- C004 reserve 符合"结构边际"而非错杀，rank-order barbell 是真实"Q5 负 alpha"问题，等 T002 变体对照后决定复投
- **不触发 threshold calibration**

## 跨候选对比

- **纯 sign interaction 家族三连败 (C001/C002/C003)**：10d/20d/60d 三个窗口同时触发 `sign_flip + ic_oos_too_low + oos_decay_too_low` 三闸。共同 pattern —— `ic_by_year` 2015-2020 全正 (0.002-0.022)，2021-2023 全负（C001 2023: -0.005 · C003 2023: -0.0095）。`split_ic_means` 4/4 全负。这不是 outlier，是 A 股 csi1000 universe 在 2021 regime 转折后**整族信号反号**。paper CSI 300 大盘 Rank IC 0.0744 的结果已被 direction.md 预警不可迁移，实测结果比预估更糟——IC 量级不仅降，还反号。
- **C004 turnover 加权是方向生路**：T002 primary 假设在 C004 得到验证——加 turnover 权重后，pure sign product 的 regime 翻号被部分中和（`ic_by_year` 2015=0.016, 2023=0.0071 仍同号全正）。ls_tstat_oos=3.90 · ls_sharpe_oos=2.81 · cum_dd=-0.69 等 CP06 时序稳健指标 batch 内最优，库独立性 max_corr=0.054@F002 · incremental_ic=0.0098 干净。但 Q1=-0.00065, Q2=+0.00021, Q3=+0.00029, Q4=+0.00022, Q5=-0.00015 形成 "avoid worst" barbell：ls 的 alpha 主要来自 Q1 极端负，Q5 本身也是负——不是 monotonic alpha，long-Q5 实盘不可行。CP03 mono=0.3（weak）使其 verdict 从 admit 降为 reserve。
- **T003 TR 归一化 definitive closed (C005)**：paper 的 "true range 归一化" 构想，我们用 `Std($close-Ref($close,1), 20)` 做分母（结构不同于 F003 的 `Mean($high,5)` 分母），但横截面 corr=0.964@F003——说明 **gap magnitude 归一化的所有分母量纲变体都会被 F003 的"open-prev_close 分子主导"结构所吸收**。T003 以干净的 near_duplicate 方式 ANSWERED，比 hard_gate sign_flip 更有价值的"信息性 reject"。
- **Style exposure 一致**：6/6 候选 `dominant_style_exposure=vol_20d`（style_crowding_risk=medium），但 `style_r²` 全在 0.02-0.05 低段，`alpha_survival_ratio` 三个过 gate 的候选（C004/C005/C006）都 ≥1.0——风格暴露不是本批主要阻断轴，机制本身才是。
- **MT budget 推进**：direction_candidates 本方向首 6 候选全数进账（`direction 0 → 6`）；cumulative `168 → 174`。direction 低基数未触达 high bucket，C004 若下轮复投仍在 medium。

## Thread 进展

> [!failure]+ T001 [[directions/gap_acceptance_structure#T001]] — `[✗ DISPROVEN batch_035]`
> C001/C002/C003 三连败（hard_gate sign_flip + ic_oos_too_low + oos_decay），10/20/60d 三个窗口同家族塌陷。机制结论：**纯 Sign(gap) × Sign(body) 的 20d 聚合在 csi1000 上 2021-2023 regime 反号**，paper CSI 300 大盘结果不 transfer 到小盘端。直接关闭该 thread。

> [!note]+ T002 [[directions/gap_acceptance_structure#T002]] — `[◉ ACTIVE]`
> C004 reserve（首证据）。turnover 加权的 acceptance 在 csi1000 上通过 hard gate，库独立 max_corr=0.054 · incr_ic=0.0098，9 年 IC 同号全正但衰减 66%；rank-order 为 "avoid worst" barbell（mono=0.3）使其 reserve。下一步 probes：`$amount / Mean($amount, 20)` 加权 vs 当前 `$turnover_rate` 直接加权对照；测 abnormal vol 归一版本是否改善 mono。

> [!failure]+ T003 [[directions/gap_acceptance_structure#T003]] — `[✗ DISPROVEN batch_035]`
> C005 hard_gate near_duplicate（corr=0.964@F003）。回答方向自设阈值"corr < 0.7 则 TR 分母是新量纲"的问题：**否**。`Std($close - Ref($close,1), 20)` 作为分母（量纲与 F003 `Mean($high, 5)` 正交）并未打破与 F003 的近完全相关——gap magnitude 的分母量纲变体都会被 F003 开环吸收。T003 definitively closed。

> [!failure]+ T004 [[directions/gap_acceptance_structure#T004]] — `[✗ DISPROVEN batch_035]`
> C001 (20d) / C002 (10d) / C003 (60d) 三窗口同时给出 hard_gate fail。窗口敏感性探索结论：**csi1000 上纯 sign interaction 不存在 "sweet spot 窗口"，T001 family 不是窗口问题，是机制问题**。方向 T004 与 T001 同步关闭。

### batch_036 · direction=`gap_acceptance_structure` · admit=1 reserve=0 reject=5 total=6

## 方向级反思

`gap_acceptance_structure` 方向在 2 轮 12 个候选后完成 alpha 抽取：
- T001 (pure sign interaction) DISPROVEN · T003 (TR normalization) DISPROVEN · T004 (window sensitivity) DISPROVEN（batch_035）
- T002 (abnormal participation weighted) ANSWERED via C004 (batch_036)

这是一个结构清晰的"方向从 hypothesis 到 1 admit 产品"的快速路径 —— paper QuantaAlpha 的 CSI 300 sign interaction 信号在 csi1000 上**只在 log-compressed 加权下存活**，IC 量级从 paper 的 0.0744 降至我们的 0.0094（约 8x 衰减），印证 direction.md 预判"csi1000 小盘信号衰减到 0.02-0.04 下界"甚至更低——实测还要更小，但结构稳健性（mono + 9 年同号 + anti-decay）足以贡献库增值。

**方向操作**（Phase 3 决策，Phase 4 frontmatter 自动化）：
- `status: saturated`（保留 Python 已自动设置状态；12 candidates 后 T002 closed + 无 reserve 留存）
- `priority: medium`（保持；不升 low 因为 log-compression 是可迁移 meta-pattern，可能对其他方向有用）
- 不再开新 thread；方向进入维护态，F{id} 产出即退出挖掘池

**Calibration（错杀侦测）**：
- 本批 `potential over-rejection` flag = **False**
- C001/C002/C003 hard_gate fail 全部是"真正的机制失败"——线性加权在 csi1000 2021+ 小盘 regime 下噪声放大，ic_by_year 清晰单调塌陷，非阈值过严
- C005 窗口扩展是测试 hypothesis 本身（是否有更长聚合救回），结果 negative 是 informative reject
- C006 CsRank 变体是测试 "rank vs magnitude" 权重形式，negative 证实 magnitude 是信号载体
- 5 个 reject 中 4 个 `sign_consistency=1.0` + 9 年 IC 全正 + 低 max_corr，但都 failed on IC_OOS magnitude——这些不是"错杀"，是"加权选择错了只有 log 能活"
- **不触发 threshold calibration**

## 跨候选对比

- **线性 ratio 加权整族失效 (C001/C002/C003)**：$amount / $volume / $turnover_rate 三个经典 "abnormal X" 线性比值加权，ic_oos 全在 0.0013-0.0016 区间（0.008 硬闸的 1/5-1/6），oos_decay 0.12-0.14 全部 fail 0.20 阈值。`ic_by_year` 共同特征：2015-2020 稳定正向 (~0.008-0.017) → 2021 起全部向零坍塌，2023 已近零。这与 batch_035 T001 pure sign interaction 的三窗口塌陷同源——**csi1000 的 2021 regime break 在 acceptance 信号上是系统性的**，**线性加权无法压低高噪声天权重**，因为线性比值对尾部极端值过度敏感，恰好是 2021+ 高 vol 小盘乱世里的 "噪声放大器"。
- **Log 非线性压缩是关键 (C004 ADMIT)**：C004 用 `Log(Div($amount, Mean($amount, 20)))` 压缩 amount 尾部，mono_OOS 从 batch_035 C004 的 0.30 → **0.60**，直接满足 direction T002 next_probes 的 ≥0.50 通过条件。IC_OOS=0.0094 · ICIR_OOS=0.253 · ls_tstat_oos=3.23 · **anti-decay=1.36**（OOS > IS，极罕见信号）。9 年 8/9 年 IC 同号，近 4 年稳定 0.0055-0.0105。库独立 max_corr=0.085@F010（`overnight_return_persistence_5d`）· incremental_ic=0.0071（虽低于 0.010 但 direction 对"首次 admit + mono 结构质量"权衡后判断过关）。
- **CsRank 压平破坏机制 (C006)**：`CsRank($turnover_rate)` 把高低 turnover 的量级差压成 [0,1] 均匀分布，丢掉了 "异常巨量 acceptance" 这个最可能携带 alpha 的信号源——C006 IC_OOS=0.0058 差 0.0022 到硬闸。印证 T002 假设：机制是 "high-participation 加权"，rank 化丢 magnitude 就是错向。
- **窗口扩展无用 (C005 vs C001)**：C005 = C001 的 40d 窗口版，IC_OOS 从 0.0016 → 0.0022（微涨），ls_tstat 1.73 → 1.81（微涨），但仍全线 fail。signal_half_life=19d 附近，40d 已超半衰期。**T004 结论在 T002 上复用**：csi1000 的加权 acceptance 没有 "更长聚合救回 OOS" 的窗口。
- **风格暴露同质**：6/6 候选 `dominant_style_exposure=vol_20d`，但 style_r² 全在 0.02-0.08 低段，alpha_survival 多个过阈（C001/C002/C003/C005 alpha_surv=3.25-6.40 极高，C004=0.61 虽低但 log 压缩后可接受），不是主阻断。
- **MT budget**：direction 6 → 12，本方向累计达 12，首批 6 reserve→0 reject 5 admit 1 模式与 batch_035 5 reject + 1 reserve 形成清晰"1 log variant survives from 12 candidates scanned"结论。

## Thread 进展

> [!success]+ T002 [[directions/gap_acceptance_structure#T002]] — `[✓ ANSWERED batch_036]`
> C004 admit → **log_amount_weighted_acceptance_20**。Thread 主问题回答：**log-compressed abnormal amount 加权 + 20d 聚合是 T002 唯一存活形状**。
>
> 决定性证据：5 个 reject 候选覆盖了线性 ratio (amount/volume/turnover TS) + CsRank + 40d 窗口五个正交变体，全部 mono < 0.5 或 IC_OOS 过低；仅 C004 log 变换同时拿到 mono_OOS=0.60 + IC_OOS=0.0094 + anti-decay。T002 family 现在有唯一代表 F{next}，thread 关闭；同时 thread 的未来 probes（"abnormal vol 加权"、"normalized turnover"）被 C001/C002/C003 对照结果 preemptively closed。

### batch_037 · direction=`trend_quality_gated` · admit=0 reserve=1 reject=5 total=6

## 方向级反思

`trend_quality_gated` 一批 6 候选**完全证伪 direction hypothesis**——paper QuantaAlpha Channel 3 的 CleanTrend / OrderlyTrend 信号在 csi1000 上**符号完全翻转**。这与 dead 方向 `return_momentum_acceleration` / `asymmetric_momentum` 已建立的事实呼应：**csi1000 小盘 universe 的 short/mid-horizon momentum 是反转载体，不是趋势载体**。Gate（流动性 / 残差噪声 / composite）不能改变这一点。

**方向操作**：
- `status: exploring → dead`（不可逆）
- 元教训升格至 lessons.md 候选：「csi1000 上 short/mid-horizon (5-10d) momentum × any liquidity/vol gate 仍是反转载体；gate 不能把反转翻成 continuation；paper 的 Channel 3 CSI 300 大盘结果在 csi1000 不可迁移」
- C002 reserve 待评估是否值得开 sister direction `gated_reversal` 收容；目前先保持 reserve，下一轮决定

**Calibration**：本批 5 reject + 1 reserve，无 over-rejection——signal 都是反向 + 库 reducer，不是阈值过严。不触发校准。

## 跨候选对比

- **方向 hypothesis 整批反向证伪**：6/6 候选 IC_OOS 在 -0.025 至 -0.033 区间，全部为负；mono_OOS 全部 -0.4 或 -0.7，方向一致负。Hypothesis 假设 gated momentum 在 csi1000 复活成 trend continuation，**实测是 reversal 信号**。这与 dead 方向 `return_momentum_acceleration` / `asymmetric_momentum` 已证伪的"raw momentum 在 csi1000 失效"结论一致——区别仅在本方向证明 **gate 不能救回 trend，反而把 reversal 信号叠厚**。
- **设计级共线 (C003/C005)**：T002 用 `Std(daily_return, 20)` 作为分母 = Barra `vol_20d` 风格的定义，导致 `style_r² = 0.346-0.519`、vol_20d exposure 12-28、alpha_survival 0.50-0.83 但残差 IC 仍为反转。**meta-lesson**：用 daily-return std 做分母 = 把 Barra vol_20d 写进信号设计里，无法 orthogonalize。
- **库角色 reducer (全员)**：6/6 incremental_ic ∈ [-0.011, -0.020] 全部负值。这些信号与 F009 overnight_intraday_spread 形成 0.30-0.44 的 cross-section 相关，与 F001 amount_cv_10 / F006-F008 shadow factors 也都形成 0.18-0.33 共线——本质是同一个 csi1000 反转因子簇的不同写法。Admit 任一会减少组合 IC。
- **C002 reserve 例外**：log-compressed gate 给出 9 年同号 + cum_ic_mdd=-53 + decay=1.53（OOS > IS）的统计稳健性，是本批最干净的"反转载体"。但 admit 进 trend_quality_gated direction 等于 hypothesis 与产物相反——因此 reserve 等待是否新开 sister direction `gated_reversal` 收容（或并入 dead reversal lessons）。
- **MT budget**：direction 0 → 6，方向首批即决定性证伪，无需继续探。

## Thread 进展

> [!failure]+ T001 [[directions/trend_quality_gated#T001]] — `[✗ DISPROVEN batch_037]`
> C001 / C002 (reserve, 待 sister direction) / C006 全部反向 IC。流动性 gate（amount linear / log / turnover）不能让 momentum 翻正，反而放大反转。

> [!failure]+ T002 [[directions/trend_quality_gated#T002]] — `[✗ DISPROVEN batch_037]`
> C003 / C005 全部反向。residual-vol 分母 = Barra vol_20d 设计共线，"低噪声 gate" 在 csi1000 等于"低 vol_20d 子集"，已被 Barra basis 覆盖。

> [!failure]+ T003 [[directions/trend_quality_gated#T003]] — `[✗ DISPROVEN batch_037]`
> C004 composite gate 也反向。叠 gate 不解决方向问题，只把噪声放大。

### batch_038 · direction=`log_value_liquidity` · admit=0 reserve=0 reject=6 total=6

## 方向级反思

**hypothesis 完全证伪**：log_value_liquidity 首批即死，6/6 reject，direction 应 `exploring → dead`（与 trend_quality_gated 模式相同：单批即决定性证伪）。

**升格 lessons.md 候选**：
- **Meta-pattern 跨方向迁移需独立验证**：log-compression 在 sign × body acceptance (F013) 有效 ≠ 在 value × liquidity 有效；non-linear 压缩的 regime-robust 性质取决于**被压缩对象是否为独立的噪声源**，在 sign-structure 中 sign(body) 是规整二值、log(amount) 承载独立信息；在 value-liquidity 中 value leg 已是 cross-section rank 的连续变量、log 对 liquidity 端的压缩与 value 合成成"反转簇包装"
- **csi1000 小盘 value leg 基本失效**：PB/PS/PE cross-section rank 在小盘 universe 不载独立 alpha（value_liquidity_interaction T001/T003 同样结论）；log 包装无法复活

**Calibration**：6/6 reject，无 over-rejection——signal 都是反向 + 库 reducer + Q5 一桨驱动，reject 稳健。不触发校准。

## 跨候选对比

- **方向整批 disconfirmation**：6/6 IC_OOS 负，mono 0 或负，incr_ic 全负——log-compression 在 csi1000 value × liquidity 维度**反向**信号（不是 value × liquidity alpha，是 overnight-intraday 反转簇载体）。与 F009/F007/F006 family 整簇 -0.18 至 -0.26 负相关，机制级簇冗余。
- **元教训修正 batch_036 结论**：F013 log-compression 工作**仅**因为原始信号结构（sign × body）已在 csi1000 被规整为二值 ±1，log 权重的非线性只调整尾部；value × liquidity 中 value (CsRank) 已是 [0,1] 连续，log 对 liquidity 端的压缩不对应 edge—— value 端在 csi1000 小盘根本不载 alpha（CP04 vol_20d 主导 exposure 8-9，value 通道 book_to_price/ep_ratio ≈ 0.2-0.3 极弱）。
- **机制诊断**：log_value_liquidity 候选的真实载体 = CsRank(PB/PS/PE) 作分组器 × log(abnormal liquidity) 作反转触发器——小盘 PB 分散度低、PS/PE 噪声大，Value leg 退化为"分组器"，Liquidity leg 承载 short-term reversal，合成信号与 F009 overnight-intraday spread 整族反向共振。
- **方向级结论**：hypothesis "meta-pattern 跨方向迁移" 证伪。`log_value_liquidity` 首批即死，不值得第二批。

## Thread 进展

> [!failure]+ T001 [[directions/log_value_liquidity#T001]] — `[✗ DISPROVEN batch_038]`
> pb × log abnormal (amount/turnover/volume) 四变体 + 5d smooth 全部反向 IC、全部库 reducer。PB rank 在 csi1000 不载 value alpha。

> [!failure]+ T002 [[directions/log_value_liquidity#T002]] — `[✗ DISPROVEN batch_038]`
> ps × log(amt) + pe × log(turnover) 同病。横扩 ps/pe 维度未改变机制——log × value × liquidity 整体是 overnight-intraday 反转簇的 value-weighted 包装。

### batch_039 · direction=`pv_covariance` · admit=0 reserve=0 reject=6 total=6

## 方向级反思

`pv_covariance` hypothesis 完全证伪，direction `exploring → dead`。Cov 形态是 csi1000 第四个跨方向重现的"volume × direction 反转簇"载体，应升格为 lessons.md 系统性经验（下次 consolidation）。

**Calibration**：6/6 reject 全部 incr_ic 负 + CP04 multiple poor/borderline，不是错杀。不触发校准。

## 跨候选对比

- **方向 hypothesis 完全证伪**：6/6 IC_OOS 负，incr_ic 全负 (-0.025 至 -0.032)，max_corr 击中 F001/F009/F012 三个已有反转簇因子。Cov 形态在 csi1000 不是独立 family，只是已有 Std/Mean/Div/Mul 因子的"协动包装"。
- **无论配对/窗口都同簇**：(turnover, amount, volume, amount_ratio) × (ret, body) × (20d, 60d) 组合里没有一个跳出 F001/F009/F012 的覆盖。C005 最强 IC_OOS=-0.051 正是**最清晰的 F001 协动同簇证据**（max_corr=0.33@F001，批内最高）。
- **CP04 降档信号**：C002 alpha_surv=0.34（<0.40 阈）、C004 alpha_surv=0.37 直接 poor；其它 borderline。表明 vol_20d + str_1m + turnover_20d 三 Barra 载体共同吞噬。
- **第 4 次跨方向 csi1000 反转簇重现**：本轮加上 trend_quality_gated、log_value_liquidity、batch_032 liquidity_acceleration reserve — **csi1000 小盘 universe 的 "volume × direction" 复合形态都倾向于归簇 F001/F009/F012 family，无论 DSL 形式如何变化**。这是 meta-lesson 级发现。

## Thread 进展

> [!failure]+ T001 [[directions/pv_covariance#T001]] — `[✗ DISPROVEN batch_039]`
> C001 20d + C003 60d + C005 amount_ratio 全部 reject。turnover-ret Cov 无独立 alpha。

> [!failure]+ T002 [[directions/pv_covariance#T002]] — `[✗ DISPROVEN batch_039]`
> C002 amount×body + C004 volume×dClose + C006 turnover×body 全部 reject。换 pair 不换簇。

### batch_040 · direction=`vwap_proxy_signals` · admit=1 reserve=0 reject=5 total=6

## 方向级反思

`vwap_proxy_signals` 方向首批 1 admit + T001 ANSWERED + T002 DISPROVEN。**核心机制**：synthesized VWAP `$amount/$volume` 在跨 session 维度（vs prev close）才解锁 alpha；同 session VWAP-close 偏离不携带 cross-section 信息。F014 是当前库第 13 个独立 admit，max_corr 全部 ≤ 0.18，独立性最强。

**方向操作**：T001 ANSWERED + T002 DISPROVEN，方向 saturated（仅 6 candidates 即决出）。Python 在 Phase 4 frontmatter 自动 update。

**Calibration**：C005 clean reversal 被 incr_ic 负 reject，符合 lessons 中"library reducer = 不能 admit" 准则。无错杀。

## 跨候选对比

- **C001-C003/C006 共同 weak mono**：4 个纯日内 VWAP-close 形态（raw, 5d agg, 20d agg, ratio agg）全部 mono_oos=0.10。强 IC + weak mono = "横截面相关性靠少数 outlier，rank-order 不成立"。证伪 hypothesis 中"日内 VWAP/close 偏离 5d/20d 聚合"假设。
- **C004 跨 session 维度突破**：把 same-day close 换成 prev close 引入 overnight 信号 → mono 从 0.10 跳到 **0.60**，ls_t 从 1.04 涨到 3.79，alpha_surv 从 0.32-0.49 涨到 0.68，max_corr 从 0.20 降到 0.17。这是 hypothesis 中"VWAP gap"形态的兑现——synthesized VWAP 在 cross-session 维度才有 alpha。
- **C005 反转旗：clean 但不可 admit**：mono_OOS=-0.90 是批内最强 rank-order，OOS_t=-3.03 显著反转，但 incr_ic=-0.013 是 F012 amihud 的 reducer。"sign-flipped 强信号 + 库 reducer" 同症状已在 batch_037 / batch_038 / batch_039 见过——csi1000 reversal cluster 的另一种载体。
- **Generator dedup 缺陷 (C003/C006)**：`(X-c)/c` 与 `X/c` 加法常数不变性下 cross-section rank 等价（4-5 位精度一致），未去重浪费 1 个 mt_budget 槽。建议 generator 增加常数不变性 dedup。
- **方向兑现**：1/6 admit，且 admit 的是预期方向（VWAP gap = paper-derived overnight maxim）。

## Thread 进展

> [!success]+ T001 [[directions/vwap_proxy_signals#T001]] — `[✓ ANSWERED batch_040]`
> C004 admit → **vwap_overnight_spread**。VWAP-prevclose (跨 session) 是 hypothesis 中 spread 形态的兑现。VWAP-close / VWAP-open 同 thread 子形态（C001/C005）全部 fail（weak mono / library reducer）。

> [!failure]+ T002 [[directions/vwap_proxy_signals#T002]] — `[✗ DISPROVEN batch_040]`
> C002/C003/C006 价格归一化聚合 5d/20d 全部 mono=0.10 weak。"VWAP/close ratio 5d/20d 聚合" 假设证伪——日内 VWAP-close 偏离没有 cross-section 可聚合持续性。

### batch_041 · direction=`stochastic_position` · admit=0 reserve=2 reject=4 total=6

## 方向级反思

本方向**首批即遭方向级证伪**。T001/T002 两条主 thread 同时 DISPROVEN，剩余 T003（orthogonalization salvage）需要工具链支持，短期不可达。

- `incremental_ic` 中位数 **-0.017**——本方向加入库**系统性减值**，远劣于近期 batch_040 vwap_proxy_signals 的正值（ls_t=3.89）。
- 与 [[directions/intraday_price_formation]] saturated 结论一致：单日 `(close-low)/(high-low)` 已 mono_sign_flip；本方向多日 rolling 是区别点，但区别**仅在数学形式**，经济本质仍是"价格位置被 vol 吞噬"——**日内与跨日的 price position 都失效**，升格为方向族级 lessons。
- 保留 C004/C005 为 reserve 是为了留"residual 路径"种子（T003），若下轮引入 vol_20d orthogonalize 工具可再测。
- **状态转换**: `status: exploring → saturated`（无 admit 首批 + 两条 thread 同时 DISPROVEN + 核心机制被 vol_20d 吞噬）。
- **下一步**: 切换方向，不建议在 stochastic_position 投新 thread。

**阈值校准侦测**: 无触发（batch_040 有 admit 未形成零-admit 3 连；reserve 均不满足库空间独立条件 `max_lib_corr<0.30 + incremental_ic>0.010`；无悖论组合出现——所有候选 mono 崩塌 + vol 吞噬是一致信号）。

## 跨候选对比

- **Style 共因**: 6/6 候选 `dominant_style_exposure=vol_20d`，exposure 8.7–16.5，`style_crowding_risk=high`——本方向核心载体是波动率，不是"rolling price position"。与 [[lessons#Data Facts]] 对 vol_20d 结构吸收律的观察一致。
- **Rank-order 系统性崩塌**: IS mono 平均 0.80，OOS mono 平均 -0.10——**5/6 候选 mono 符号翻盘或崩塌**。这是 rank-order 机制证伪的硬证据，不是个案。
- **Incremental_ic 集体为负**: 6 候选 incremental_ic 全部在 -0.012 到 -0.022（无一正值），说明本方向加入库**等于减值**。
- **Cluster 同质化**: 6 候选互相 IS 相关 ~0.7+（未显式计算，但 all_correlations 对 F006-F009 的负相关模式高度相似 [-0.28, -0.46]），且都指向反转簇——说明 %K/TsRank 这类"位置"指标本质与 OHLC shape 同空间。
- **20d 优于 60d**: C001 vs C002, C003 vs C004 两对比较，20d 窗口 OOS 指标略好但都不达标；长窗口稀释 regime 敏感度反而更差。
- **MT 预算推进**: direction_candidates 0 → 6（本方向首批）；cumulative 204 → 210；bucket 仍在 medium 上界。

## Thread 进展

> [!failure]+ T001 [[directions/stochastic_position#T001]] — `[✗ DISPROVEN batch_041]`
> 4 候选（C001 20d low/high, C002 60d low/high, C005 20d close-only, C006 5d 平滑）覆盖经典 %K 形式。ls_t_oos 均 < 2（-0.83 到 1.09），mono_oos 均 ≤ 0.40，incremental_ic 全部为负。回答：**"(close - TsMin(N)) / (TsMax(N) - TsMin(N)) 不携带独立 alpha"**，在 csi1000 样本下被 vol_20d 吞噬并在 OHLC shape 簇内冗余。

> [!failure]+ T002 [[directions/stochastic_position#T002]] — `[✗ DISPROVEN batch_041]`
> 2 候选（C003 20d, C004 60d）覆盖 TsRank($close, N) 形式。mono_oos 同样崩塌（0.0 / -0.3），与 F007 相关 0.37–0.49。回答：**"TsRank 与 %K 机制等价，两者共享被 vol_20d + OHLC shape 簇吸收的宿命"**，非正交。

> [!note]+ T003 [[directions/stochastic_position#T003]] 🆕 — `[◉ ACTIVE]`
> 是否存在"对 vol_20d orthogonalized 的 %K 残差"能在 csi1000 OOS 恢复 rank-order？候选 C004 residual_ic=-0.0183、residual_icir=-0.399（本批最强）是潜在入口，但需要 Python 端先实现 `orthogonalize` 算子或 barra_residual_signal 再挖。优先级低——C005 残差 alpha_surv=1.16 暗示有但 raw 已 reserve 即可。

### batch_042 · direction=`vwap_proxy_signals` · admit=0 reserve=3 reject=3 total=6

## 方向级反思

本方向**第二批即撞到"VWAP 锚点的结构耦合墙"**：
- F014 占据的"跨 session VWAP gap"统计空间非常强势（max_corr 0.89 吸引 4 个候选）——即使是机制上独立的 HLC 位置/mean-reverting 形式都被实证打回同一簇
- 结构耦合根源：**A 股 10% 涨跌幅约束** 使得 daily HLC range 与 prev_close 尺度强相关；任何"VWAP 相对日内锚"的形式都隐含"VWAP 相对 prev_close"的信息
- 与 [[directions/stochastic_position]] batch_041 结论对偶：price-position 指标族（跨日 rolling 或日内 HLC）在 csi1000 都被 vol_20d / 已有 VWAP 信号吸收

**ROI 评估**：direction 2 rounds / 12 candidates / 1 admit (F014) / 6 reserve。首批 17% admit 率来自 T001 ANSWERED；第二批 0% 来自 T003 四子路径同时失败。

- **状态**：`status: productive` 保持（仅 2 rounds，不足以判 saturated；下一 round 若仍 0 admit 则转 saturated）
- **priority**：`medium → low`（T003 剩余路径阻塞于工具链）
- **下一步**：
  1. 方向短期挂起，等 vol_20d orthogonalize 工具链；C001 可在工具到位后作为 residual 种子
  2. 本轮教训升格 lessons：A 股 10% 涨跌幅约束导致 HLC range 与 prev_close 共动，"daily-anchor VWAP" 无法独立于"cross-session VWAP"

**阈值校准侦测**: 无触发（last-3-batch admit 累计 = 1，非 0 连 3；reserve 积压 3/6=50% 但无零-admit 累计条件；无 over-rejection flag；无悖论组合）。

**库空间独立性安全阈判断**：C001 是本批最强候选，但 max_corr=0.887 远超"错杀 safeguard"的 `max_lib_corr<0.30` 条件，且 F014 与 C001 同方向（正相关），非互补——reserve 合理，不走校准流程。

## 跨候选对比

- **Affine equivalence 识破**：C001 `(VWAP-L)/(H-L)` 与 C002 `(VWAP-(H+L)/2)/(H-L)` = C001 - 0.5，rank-order 恒等。metrics（IC/ICIR/ls_t/mono/max_corr/incr_ic）六位小数级一致——**物理上是同一个信号**。未来设计规避：凡同分母仿射移位，freeze 前做 DSL canonical 去重。
- **F014 吸引 cluster**：C001/C002/C003/C006 四个 VWAP-锚点候选 max_corr@F014 ∈ [0.79, 0.89]——10% 涨跌幅约束 + 日成交密度使得 HLC 范围与 prev_close 尺度强相关；**"同分母不同分子的 VWAP spread" 几乎全部落到 F014 统计空间**。真正独立于 F014 的只有 C004（VWAP 自相关 mean-reverting）和 C005（sign × sign）——但二者都因机制其它缺陷 reject。
- **Style cluster**：6/6 候选 dominant_style=`vol_20d`（exposure 7.5–22.3）；3/6 style_r²>0.25（C001/C002/C006 poor）。与 batch_041 stochastic_position 同样被 vol_20d 吞噬——升级为**跨两方向交叉验证**的结构吸收律。
- **MT 预算推进**：direction_candidates 6 → 12；mt_bucket 推至 `high` 上界，search_adjusted 压回 `medium` 强制封顶（本批所有 CP03 档位 ≤ borderline 即此所致）。
- **sign consistency 全 1**：C001/C002/C004/C005/C006 全 sign_consistent=1.0，说明机制方向稳健——问题在 rank-order + style 吞噬，不在方向漂移。

## Thread 进展

> [!note]+ T001 [[directions/vwap_proxy_signals#T001]] — `[✓ ANSWERED batch_040]`（本批无推进）

> [!note]+ T002 [[directions/vwap_proxy_signals#T002]] — `[✗ DISPROVEN batch_040]`（本批无推进）

> [!note]+ T003 [[directions/vwap_proxy_signals#T003]] — `[◉ ACTIVE → 部分 DISPROVEN]`
> 5 类锚点中 4 类证伪/重复：
> - **HLC 位置**（C001/C002/C006）：IC 独立但 stat-space 与 F014 重合 0.79–0.89，不真正解耦——⚠️ DISPROVEN（同 T002 结构吸收）
> - **Signed 持久性**（C003）：Sign+5d agg 丢 magnitude + F014 已覆盖该锚——⚠️ DISPROVEN
> - **VWAP 均值回归**（C004）：mono_flip + style_r²=0.68 吞噬——⚠️ DISPROVEN
> - **方向一致性**（C005）：sign×sign 丢 magnitude + cum_ic_mdd=-70——⚠️ DISPROVEN
>
> 仅剩**未验证的第 5 子路径**："orthogonalize by F014 / vol_20d 后的 VWAP 残差" ——但需工具链支持（barra_residual_signal 或 orthogonalize 算子），短期阻塞。

### batch_043 · direction=`range_structure` · admit=0 reserve=4 reject=2 total=6

## 方向级反思

本方向**首批即遇到"shape vs magnitude 分裂"**：
- **Magnitude/ratio 路径全败**：5 候选 dom=vol_20d + incremental_ic 负——与 `return_distribution_signals` dead 结论 **"mean-of-power transformation 坍缩到 vol rank"** 在 range 字段上**再次实证**（第 3 次跨方向独立确认）
- **Shape 路径意外存活**：Skew(range, 60) 与低频 threshold 两候选 max_corr < 0.16，incremental_ic 正值 0.013–0.014——分布偏度是 range 的**三阶矩信息**，与 vol_20d 的二阶 std 数学不等价
- 与 [[directions/stochastic_position]] batch_041 / [[directions/vwap_proxy_signals]] batch_042 共同确认：**csi1000 的 cross-section 几何被 vol_20d 主导 2nd-moment 空间，逃离路径必须走 shape (3rd/4th moment) 或时序离散 (timing/freq) 而非 ratio/delta**

### 阈值校准诊断（C004 error-kill flag）

**触发条件**：
- ✅ **#1 错杀 flag**：C004 subagent 主动 flag potential over-rejection（rubric 错杀侦测四要件全过）
- ✅ **#2 零 admit 3 连**：batch_041 (0) + batch_042 (0) + batch_043 (0) 累计 admit=0，且 C004 满足 `max_lib_corr<0.30 + incremental_ic>0.010` 库空间独立条件
- ✅ **#3 Reserve 积压**：累计 reserve/judged 率 4/6=67% > 40% + 零 admit

**Step 1 诊断** — C004 是否真被错杀？

| 错杀要件 | C004 数值 | 通过 |
|---|---|---|
| 库空间独立 | max_corr=0.117@F012 (<0.30) + incr_ic=+0.0138 (>0.010) | ✓ |
| rank-order 完美 | mono_oos=+1.00 (≥0.80) | ✓ |
| 符号稳健 | sign_consistency=1.0, cum_ic_mdd=-2.01 (库最浅) | ✓ |
| 机制互补 | F012 amihud (1st moment 液性) vs C004 (3rd moment range shape) 机制正交 | ✓ |

**但深度诊断发现反证据**：
1. **IS→OOS mono 异常放大**：mono_is=0.30 (1704 天训练期仅弱单调) → mono_oos=+1.00 (484 天 OOS 完美单调)。正常 alpha IS mono ≥ OOS mono（decay 方向）；OOS 反而远强于 IS 说明 **OOS 期的 regime 特殊偶然或小样本统计波动**，不是稳健机制
2. **统计显著度中等**：ICIR_OOS=0.177 / ls_t_OOS=2.46 / IC_OOS=0.010——均 moderate 档，不是 strong
3. **split_dispersion=0.654 + ic_by_year 衰减**：4 split IC 均值 0.020 / 0.013 / 0.006 / 0.002 单调下降——edge 在历史中慢速弱化
4. **alpha_survival=0.141 << 0.40**：vol_20d 吞噬 86%——即便 shape 信号理论独立，实盘 Barra risk model 下**可投资部分不足 15%**

**结论**：C004 的 4 numeric criteria met 但**实质检验不达 error-kill 标准**。rubric 错杀侦测公式缺少"IS mono 同样达 0.80+"的 gate——未来应升格为 **五要件**（加入 mono_is 硬下界 0.6，防止 OOS 运气型 rank）。

**Step 2-4**：**不调阈，不追溯**。保持 C004 reserve（非 admit）、不修改 rubric、不 retroactive archive。但记录此次诊断为 lessons.md#Threshold Calibration 新条目候选（下次 consolidation 合并）：
> 2026-04-24 (batch_043) — **C004 skew(range, 60) 悖论组合诊断为非真错杀**。原因：mono_is=0.30 (OOS 1.00 反而远强)，违反 alpha 应有的"IS 强→OOS 部分 decay"规律；升格建议：错杀侦测要件 #2 (rank-order 完美) 应要求 **mono_is × mono_oos 同时 ≥ 0.60** 或 **mono_is ≥ 0.60**，防 OOS-only 统计波动。

### ROI 评估与下步

- direction 1 round / 6 candidates / 0 admit / 4 reserve——首批即证伪 2 子路径（freq-high / magnitude ratio）
- **状态**：`status: exploring` 保持（首批不足判 saturated）
- **priority**：`medium → low`（剩余活路 shape 路径需重新设计 - Skew 变体 / Kurt / Quantile-based shape，且 mono IS 硬下界后测试）
- **下一步**：
  1. 短期切换其它方向（不投 range_structure Round 2，等 shape 路径重新设计）
  2. lessons.md 升级错杀侦测要件（下次 consolidation）
  3. C004 reserve 保留作 shape 重设计的对照锚点

## 跨候选对比

- **分裂结论**：magnitude/ratio 路径（C005 短长比 / C006 变化率 / C002 高频 threshold）**全部负 incremental_ic** (-0.019 到 -0.025) 且 dom_style=vol_20d exposure 13.9–47.9——range 的 power-mean transformation 沿用 vol_20d 空间；distribution-shape 路径（C004 skew 60d / C003 低频 threshold）**正 incremental_ic** (+0.014 / +0.013) 且 max_corr@库 低于 0.16——shape 层面真正独立。
- **悖论组合（C004）**：subagent 触发 rubric §错杀侦测四要件全过（库空间独立 + rank-order 完美 + 符号稳健 + 机制正交）+ flagged POTENTIAL OVER-REJECTION。按 /factor-mine 阈值校准触发 #1/#2/#3 全中（详见方向级反思 §阈值校准诊断）。
- **Style cluster**：5/6 候选 dominant_style=vol_20d（exposure 3.9–47.9）；C001 例外（exposure 低 alpha_surv=0.89 clean，但 IdxMax 时序信号太弱 ls_t=-1.40）。vol_20d 结构吸收律**跨 3 方向（stochastic_position / vwap_proxy_signals / range_structure）重现**——升格方向族级教训。
- **cum_ic_mdd 分化**：C003/C004 shape 路径 cum_mdd 浅（-4.57 / -2.01），C005/C006 magnitude 路径深（-65 / -82）；印证 shape 类机制时序稳健性远强于 magnitude 类。
- **MT 预算推进**：direction_candidates 0 → 6；bucket 推到 medium，search_adjusted 压到 0.24–0.62。

## Thread 进展

> [!note]+ T001 [[directions/range_structure#T001]] — `[◉ ACTIVE → shape 部分存活 / freq-high DISPROVEN]`
> - C001 IdxMax timing：机制 alpha_survival=0.89 clean 但 ls_t=-1.40 弱 + incr_ic 负 → reject。**timing 形式在 20d 窗口信噪比不足**。
> - C002 高 range 频率：vol_20d exposure=47.9 + alpha_surv=0.23 poor → reject。**freq-high threshold 仍在 vol_20d 空间**——**子路径 DISPROVEN**。
> - C003 低 range 频率：max_corr=0.16@F002 独立但 mono_oos=0.0 + ls_t=-0.23 → reserve。compression 机制存活但信号弱。
> - **C004 range skew**：shape 层面机制**库独立 + rank-order 完美 + cum_mdd 最浅**——触发错杀侦测（详见 §诊断）。
>
> **本批结论**：timing 与 freq-high 已两条子路径封闭；shape(skew/低频) 路径存活等重新设计。

> [!note]+ T002 [[directions/range_structure#T002]] — `[✗ DISPROVEN batch_043]`
> C005 短/长 range ratio 与 C006 变化率：9 年 IC 稳定但 **incremental_ic 全部为负** (-0.025 / -0.017)，vol_20d exposure 13.9–27.7——**range ratio/velocity 在 csi1000 与 F001/F009 共享同一反转簇载体**，与 [[directions/liquidity_acceleration]] batch_032 结论同构。T002 answered = "range 的 magnitude/ratio 形态与流动性簇同源，不独立"。

### batch_044 · direction=`quantile_shape_signals` · admit=0 reserve=5 reject=1 total=6

## 方向级反思

本方向**首批即遇到假设的根本性证伪**：
- Quantile 算子的 robust-to-outliers 属性**不等于** Barra vol_20d orthogonality——两个不同概念混淆在 hypothesis 设计中
- 与 [[directions/range_structure]] C005/C006 batch_043 结论一致：range 任何形态（magnitude/ratio/Median/Quantile/IQR）都坠入 vol_20d 吸收簇，**第 4 次跨方向独立确认**
- Learning：未来 shape 路径设计必须 **显式做 vol_20d orthogonalization 预处理**（需 Python 残差工具链），或换到 **非 return、非 range 的 shape 维度**（如 intraday order flow / fundamental event 事件密度——非当前 DSL 覆盖字段）

### 阈值校准诊断

**触发条件**：
- ⚠️ **#1 错杀 flag**：C001 subagent flag "Potential over-rejection 3/4 条"（非 4/4，cum_ic_mdd=-84 不达"库中位数更浅"条件；且 incremental_ic=-0.036 为负非 library-additive）
- ✅ **#2 零 admit 3 连**：batch_042/043/044 累计 admit=0
- ✅ **#3 Reserve 积压**：累计 reserve/judged 率 5/6=83% > 40%

**Step 1 诊断** — 本批任何 reserve 是否真错杀？

| 候选 | max_lib_corr<0.30 | incr_ic>0.010 | mono_oos≥0.80 | cum_ic_mdd 库最浅 | 结论 |
|---|---|---|---|---|---|
| C001 Q90-Q50 | ✓ 0.215 | ✗ **-0.036** | ✓ 0.9 | ✗ -84.19 | 不达 error-kill |
| C002 turnover Med/Mean | ✗ 0.404 | ✗ +0.006 | ✗ 0.1 | ✓ -0.96 | 不达 error-kill |
| C004 range IQR | ✓ 0.234 | ✗ **-0.037** | ✓ 1.0 | ✗ -86.53 | 不达 error-kill |
| C005 range Median | ✓ 0.221 | ✗ **-0.038** | ✓ 0.9 | ✗ -72.13 | 不达 error-kill |
| C006 range Med 短长比 | ✓ 0.214 | ✗ **-0.020** | ✗ 0.1 | ✗ -66.07 | 不达 error-kill |

**诊断结论**：**无真错杀**。5 个 reserve 候选中 4 个 incremental_ic 负（库负冗余，admit 会减值）；C002 唯一正但 +0.006 <0.010 低于阈值 + mono_oos=0.1 rank-order 不成立。

**Step 2-4**：**不调阈，不追溯**。所有 reserve 都属 "机制存活但库空间负冗余" 或 "rank 不成立" 两类——都不属"错杀"。记录观察：**本批强烈确认 csi1000 vol_20d 结构吸收律 + Quantile 算子不等于 orthogonalize**。

## 跨候选对比

- **hypothesis 证伪模式**：4 个 range Quantile 变体（C001 Q90-Q50 / C004 Q75-Q25 / C005 Median / C006 5d/60d Median 比）**全部 dominant_style=vol_20d**，exposure 27–42，style_r² 0.23–0.56——**Quantile 对尾部免疫 ≠ 对 vol_20d 正交**，robust location/spread estimator 仍然共线于 vol 主轴。
- **incremental_ic 全负**（仅 C002=+0.006 borderline 正）：6 候选入库皆减值，方向 ROI = 0。
- **rank-order vs tradable spread 反差**：C001/C004 mono_is=-1.0 + mono_oos=-0.9~-1.0（rank 完美）但 alpha_survival 0.31–0.37 poor + incr_ic 负——与 [[directions/return_distribution_signals]] 的 Q90-Q10 失败同构（rank-order 完美 ≠ alpha 真）。
- **Style cluster**：5/6 dom=vol_20d（非例外仅 C002 dom=vol_20d exposure=30 但 alpha_surv=1.03 clean）——vol_20d 结构吸收律第 4 次跨方向重现（stochastic / vwap_proxy / range_structure / quantile_shape）。
- **MT 预算推进**：direction_candidates 0 → 6；bucket 保持 medium。

## Thread 进展

> [!note]+ T001 [[directions/quantile_shape_signals#T001]] — `[◉ ACTIVE → hypothesis 部分证伪]`
> - range 字段（C001/C004/C005/C006）：Quantile 差分/Median/短长比全部 dom=vol_20d + incr_ic 负 → **range 路径 DISPROVEN**
> - amount 字段（C003）：max_corr=0.80@F012 near-duplicate + alpha_surv=0.07 → **amount 路径 DISPROVEN**（坠入液性簇）
> - turnover 字段（C002）：IC 活 ICIR=+0.41 但 ls_t=+0.25 鸿沟，mono_oos U-shape → **turnover Med/Mean 比机制不够强**
>
> **本批结论**：3 字段上的 Quantile shape 路径**全面证伪**。唯一未撞墙的是 "shape-only location-free" 纯 Quantile 比例（如 Q90-Q10 除以 Q75-Q25 tail-ratio），未设计。
