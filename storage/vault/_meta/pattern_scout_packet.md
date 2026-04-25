# Pattern Scout Packet

> Generated at 2026-04-25T07:28:09+00:00 · recent=10 batches

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
| range_structure | exploring | low | 3 | 0 | batch_045 |
| return_distribution_signals | dead | low | 1 | 0 | batch_016 |
| return_momentum_acceleration | dead | medium | 1 | 0 | batch_029 |
| stochastic_position | saturated | low | 2 | 0 | batch_041 |
| trend_quality_gated | dead | low | 1 | 0 | batch_037 |
| turnover_structural_signal | saturated | low | 1 | 0 | batch_004 |
| value_liquidity_interaction | saturated | low | 9 | 1 | batch_052 |
| vol_shock_signals | dead | low | 1 | 0 | batch_024 |
| vwap_proxy_signals | productive | medium | 2 | 1 | batch_042 |

## Recent batches（judge.md 关键段摘录）

### batch_045 · direction=`range_structure` · admit=0 reserve=1 reject=5 total=6

## 方向级反思

本方向 T001 shape 路径经 batch_043 + batch_045 两轮共 11 candidates（timing/freq/skew/IQR/ratio/Kurt/Quantile-based 变体）**仍零 admit**，但 **shape 路径的分辨率显著提高**：

1. **Kurt (4 阶矩)** 与 **Skew (3 阶矩)** 之间的稳健性差异：Kurt 在同样经济直觉（range 分布尾部）下产出 mono_is=0.90 稳健结果（C001），Skew 经两轮尝试（batch_043 60d + batch_045 120d）均产出 mono_is 弱 + OOS dramatic scaling 的 non-robust pattern——**Skew 在 (H-L)/C 分布上对样本噪声敏感**，Kurt 更稳健。
2. **升格的 mono_is ≥ 0.6 硬下界纪律首次执行**（C004 reject）——纪律有效，阻止了与 batch_043 C004 完全同构的错误 reserve/admit。
3. **batch_045 相对 batch_043 的设计改进明显**：batch_043 无 admit 无 reserve，batch_045 产出 1 reserve（C001 Kurt60）——shape 路径仍活。
4. **Direction 剩余空间**：Kurt 长窗变体 (90d/120d) + Kurt × turnover/momentum orthogonalize（工具链待建）+ range-specific ratios (如 close proximity to H-L 极值) 未测。
5. **MT 预算压力**：本方向 0 admit + 12 candidates，direction MT bucket 已 high（adjusted medium）。下批需更 target 的设计（不再尝试失败过的 Skew/Quantile 系），否则 rounds=2 → 3 仍 0 admit 需转 `priority: medium → low` 或考虑 saturated。

**Operations 建议**（由 direction.md 执行）：
- `status: exploring` 保持（首次 reserve，仍在 productive 方向发展）
- `priority: medium → low`（MT 消耗快 + 0 admit 持续 + 剩余设计空间有限）
- **下批探索**：Kurt90/Kurt120 长窗 + Kurt-based composite；不再测 Skew 变体；scale-free pure ratio 暂缓

## 跨候选对比

- **Style 聚合**：6 候选全部 `dominant_style_exposure = vol_20d`——**本方向整体暴露于 vol_20d**；exposure 分布分为三组：magnitude 组（C002=47.0 / C003=44.7 极端）· 4 阶矩/3 阶矩/scale-free 组（C001=15.0 / C004=12.8 / C006=20.4 中等）· Sign-gated 组（C005=10.7 但 str_1m=2.49 主导）。**C001 Kurt 的 15.0 是 shape 组中最低吸收之一**。
- **相关度 cluster**：C002-C003 同根（Q90 & Q90-Med）预期高 corr（但未直接计算）；C001 与 C004 corr 约 0.095（Kurt 与 Skew 相关但机制分离）；C005/C006 与库内 F007/F001 分别 medium/low corr——**批内无跨候选高 corr 冗余**。
- **MT 预算推进**：direction_candidates 6 → **12**（`range_structure` 累计 12 candidates, 2 batches, 0 admits, 1 reserve）；cumulative 228 → 234；bucket `high` (adjusted `medium`)。本方向 MT 消耗速度正常但 admit 率 0% 持续，**下批再 0 admit 即到 saturated 边缘**。
- **Shape vs Magnitude 分裂**：清晰的三分法——**magnitude (Q90/Q90-Med) 全败**（vol_20d 吸收确诊）；**shape 高阶矩 (Kurt/Skew)** 部分成功（Kurt reserve，Skew 因 IS mono 弱 reject）；**scale-free ratio (IQR/Med) 失败**（rank-order OOS 崩塌）。

## Thread 进展

> [!note]+ T001 [[directions/range_structure#T001]] — `[◉ ACTIVE]`
> **本批进展**：
> - **C001 Kurt60 → reserve**：shape 路径首次 partial breakthrough——满足 mono_is ≥ 0.6 硬下界 (0.90) + style_r²=0.074 + cum_mdd=-1.42 + incr_ic=0.015 + mono_oos=0.90。alpha_surv=0.17 poor 阻止 admit，但是 **T001 shape 路径首个可持续 partial result**，值得后续再测 Kurt 变体。
> - **C002/C003 → reject**：magnitude Quantile (Q90, Q90-Med) **确认进入 vol_20d 吸收簇**（exposure 44-47, incr_ic 严重负），是对 hypothesis "magnitude 吸收" 的正向验证。
> - **C004 Skew120 → reject**：**完美复现 batch_043 C004 mono paradox**（mono_is 0.50 < 0.6 硬下界，OOS=1.0 dramatic scaling）——升格的设计纪律执行有效，本批因纪律 reject，避免错误 admit 非稳健机制。
> - **C005 sign-gated Skew → reject**：Sign gate 把 exposure 拖向 str_1m=2.49 短反转空间 + ls_tstat IS/OOS 翻转——**sign-gated shape 在 csi1000 不稳健**。
> - **C006 IQR/Med → reject**：scale-free 归一化**部分成功**（vol exposure 减半）但 mono OOS 崩塌——scale-free 不能单独撑起稳健 rank-order。
>
> **Thread 状态**：保持 `[◉ ACTIVE]`（C001 reserve 具体回答子问题部分证据；未 admit 不触发 ANSWERED 转换）

### batch_046 · direction=`microstructure_illiquidity` · admit=1 reserve=1 reject=4 total=6

## 方向级反思

`microstructure_illiquidity` 方向从 `saturated` 转 **revived-productive**：rank-diff 结构 (T006) 在被正式宣告 saturated 2 批后找到有效子空间，证实 saturated 定性不是**永久结论**，只是对当时探索范式的局部最优陈述。admit F013 → amihud_cv_rank_diff_20 是库第 14 个独立因子，max_corr 0.655 接近阈上限但 incremental_ic 0.031 证明库增值；9 年全正 + mono_oos=1.0 + ls_t=6.63 OOS 让质量档位 strong。

**设计范式升格到 lessons 候选**（Phase 5 consolidation 待确认）:
1. **"rank-diff 符合率 range"**: rank-diff 两端 **scale-invariant**（CV, ratio, correlation）时有效；scale-dependent（Std, Mean, 绝对 level）时退化为主因子近重复。C003/C004 对照是首个硬证据。
2. **"sign-conditional 在 20d 窗口保序"**: day-level If gate + 20d mean aggregation 的组合近完全抹平 sign asymmetry。未来 sign-conditional 设计需 ≤ 5d 窗或 quantile-based 非 mean 聚合。

**方向操作**: 本批 admit 后从 `saturated` 转回 `productive`（或 `revived`）;  priority 从 `low` 回升 `medium`；rounds = 3（batch_030 / batch_031 / batch_046）；admits = 2 (F012, F013-to-be)。T006 ANSWERED; T005 保留 ACTIVE；下轮可开 T007 "rank-diff 扩展到其他 signal family" 探索。

**Calibration**: 无错杀侦测——C006 reserve 非错杀（alpha_surv 真 poor + signed neg incr），reject 4 个均 hard_gate 近重复或保序 proof。C003 admit 符合所有阈值。**本批破除 5 批零 admit 警戒线**，cockpit zero_admit_streak 重置为 0。无需 calibration。

**MT budget**: cumulative 234 → 240, direction 12 → 18, bucket `high`（search_adjusted 0.9 → 0.54 降至 medium，C003 strong 档无需进一步降档）。

## 跨候选对比

- **C001/C002 sign-conditional 对偶结题**: max_corr 仅差 0.024 (0.942 vs 0.918)，**Amihud up/down 在 20d 平均下近完美对称**。A 股散户恐慌抛售 asymmetry 假设在日度数据 20d 窗口层级被平均化消除。升格教训: day-level sign gate + window mean aggregation 的组合会抹平 asymmetry——复活需 ≤ 5d 短窗 或 quantile-based asymmetry。

- **C003 vs C004 — rank-diff 设计范式的硬证据**: 同为 CsRank 差结构，C003 (Amihud vs amount_CV) 通过 (corr=0.655), C004 (Amihud vs Std_amount) 失败 (corr=0.935)。两者唯一差别: amount dispersion 端用 CV (scale-free) 还是 Std (scale-dep)。**结论**: rank-diff 结构 alpha 源于两端 signal family 都 **scale-invariant**；若一端 scale-dependent 会退化为主因子近重复。推广到其他方向: 设计 CsRank 差结构时两端必须都是 ratio/CV/correlation 等 scale-free 量。

- **C005 延续 batch_031 C004 保序教训**: SignedPower(F012, 0.5) max_corr=1.000, 与 CsZscore(F012)=1.000 形成"rank-preserving monotonic 变换对单因子零信息增量"第二个独立证据。lesson 升格建议: 把 DSL 层 `{Linear, SignedPower(p>0), Sigmoid, Tanh, Exp, Softmax}` 对已 admit 因子的单元包装 **hard_gate 预拦截**，省试错 slot。

- **C006 signed illiquidity proxy — 独立但弱**: max_corr=0.16 本批最低 + 9 年全负 sign_consistency=1.0 的 rank-order 真实，但 alpha_surv=0.17 严重 + signed incremental_ic=-0.031 (admit 反稀释库)。属 "真 signal 但 alpha 不达标 + 库稀释" 象限，归 reserve 负参考。

- **方向兑现**: 1 admit / 6 candidates, admit 命中率 17%；但 **C003 机制质量极高**——alpha_surv 比 F012 admit 时 (0.443) 高 48%；9 年全正；mono_oos=1.0；IC 随 horizon 单调递增至 20d=0.121 —— rank-diff alpha 质量优于 F012 raw level。

## Thread 进展

> [!success]+ T005 [[directions/microstructure_illiquidity#T005]] — `[✗ PARTIAL-DISPROVEN batch_046]`
> **sign-conditional Amihud (up/down 分离)**: C001/C002 对偶 max_corr 0.942/0.918 → 日频 20d 窗口对称性几乎完美。
> **Kyle-lambda signed turnover illiq (C006)**: 库空间独立 (max_corr=0.16) + 9 年同号，但 alpha_surv=0.17 + signed neg incr_ic → reserve 负参考。
> **结论**: T005 signed illiquidity 子空间 DSL 层 20d 窗口**本质为 symmetric space**; short-window / quantile-asymmetry / 更强 residualize 未测 → thread 保留 ACTIVE 等待 minute-bar 或 5d-window 变体。

> [!success]+ T006 [[directions/microstructure_illiquidity#T006]] — `[✓ ANSWERED batch_046]`
> **rank-diff symmetric interaction**: C003 admit → **amihud_cv_rank_diff_20** (Phase 4 F{id} 分配)。CsRank(Amihud) − CsRank(amount_CV) 兑现 direction 复活条件 (b)。C004 证伪提供设计范式: 两端 scale-invariance 是必要条件。Thread 第一子问题结题，后续可沿 "rank-diff 扩展"（vs F002, vs F003 等不同 signal family）继续探索。

### batch_047 · direction=`microstructure_illiquidity` · admit=1 reserve=1 reject=4 total=6

## 方向级反思

`microstructure_illiquidity` 方向**连续两批 productive (batch_046 + batch_047)**，admits 从 2→3 (F012, F015, C001-to-be)。核心驱动是 rank-diff 结构的可泛化性：

- **batch_046**: rank-diff 首次兑现（F015 Amihud × amount_CV）——"signal family 组合的几何性质"
- **batch_047**: rank-diff 泛化验证（C001 Amihud × turnover_CV）——"字段替换保持 scale-free 仍产出独立 alpha"

**风险旗标**:
- **库集中度**: F012 (Amihud level) + F015 (rank-diff amount_CV) + C001 (rank-diff turnover_CV) 三者都在 Amihud 轴 —— microstructure_illiquidity 方向库已占 3/14 slots 的 21%；若继续 admit Amihud 近亲，需 portfolio 层 Barra neutralize 或考虑 retire alpha_surv 最弱者（当前 F012 0.443 最弱）。
- **vol_20d exposure 逐步上升**: F012 exposure=5.9 → F015=18.3 → C001=30.2 — 单调上升，说明 rank-diff 引入更强 vol 耦合；portfolio 层 Barra neutralize 优先级升级。
- **MT bucket high** (cumulative 246, direction 24) — search_adjusted medium, C001 strong 档保留但需警觉多重检验通胀。

**设计范式升格到 lessons 候选**（Phase 5 consolidation 待确认）:
1. **"rank-diff Sub 方向对偶律"**: `Sub(A,B)` 和 `Sub(B,A)` 是数学完全反号对偶（|corr|=1），admit 两者等价于 double counting。generator 层应 pre-dedup。
2. **"rank-diff 跨 direction 泛化 2 约束"**:
   - raw field-level 独立（两端分母/分子不得共享 raw field 如 $amount）
   - 库内主导因子预测（若一端被已有库因子吸收主导，rank-diff 退化为主导端反号）

**方向操作**: status `productive` 保留；priority `medium` 保留；rounds 3→4；admits 2→3（F012, F015, C001-to-be）。T007 partial answered 保留 ACTIVE; T005 (a) 条件 disproven 保留 ACTIVE 等 quantile 测试。**下轮 T007 聚焦** Amihud × correlation-based 测度（如 `Corr($close, $amount, 20)`）或库内其他 scale-free 对的 rank-diff。

**Calibration**: 无错杀侦测——
- C006 reserve 非错杀（alpha_surv 0.484 边缘 + max_corr 0.862 实质库吸收）
- C005 reject 非错杀（alpha_surv 0.149 default 阈值 0.40 的 37%，距离 calibration 触发线甚远）
- C002 C004 hard_gate fail/数学对偶 清晰
- C003 signed negative incr_ic reject 清晰 (admit 会稀释库)

本批 admit=1 延续 direction productive 势头，zero_admit_streak 保持 0。**无 calibration 需求**。

**MT budget**: cumulative 240 → 246, direction 18 → 24, bucket `high`（search_adjusted 0.9 → 0.53 medium, C001 strong 档无需进一步降档）。

## 跨候选对比

- **C001 admit vs C004 reject — Sub 方向对偶硬证据**: 数学上 `Sub(A,B) = -Sub(B,A)`，两者数值完全反号（C001 mono=+1.0 IC=+0.050 vs C004 mono=-1.0 IC=-0.050）。同批 anchor rule 严格执行：选 signed-positive-incr_ic 的 C001 admit，C004 自动 reject。**升格教训**: 未来 rank-diff 候选设计只需枚举 Sub(A,B) 一个方向（按 hypothesis 方向约定），generator 层可 pre-dedup Sub 反向变体，节省候选 slot。

- **C001 admit vs C002/C003 reject — T007 范式边界收窄**: C001 (**同 direction 内字段替换**, Amihud × amount_CV → Amihud × turnover_CV) admit; C002 (**跨 direction 但分母 $amount 共振**, pb/amount vs Amihud) hard_gate noise; C003 (**最远跨 direction**, amount_CV × overnight_gap) signed negative incr_ic。三级退化证明 rank-diff 范式可行空间是**同 direction 内部 scale-free × scale-free 字段对换**；跨 direction 越远越容易被主导端吸收或分母共振抵消。

- **C001 admit vs C006 reserve — rank-diff 结构 > non-linear transform 结构**: C001 (rank-diff) max_corr=0.734@F015, incr_ic=0.023 admit; C006 (range = max-min) max_corr=0.862@F012, incr_ic=0.022 reserve。两者 incr_ic 几乎相等但 C006 corr 高 0.13——rank-diff 的信息提炼效率高于 non-linear level-transform。

- **C005 T005 短窗复活条件 (a) 硬证伪**: batch_046 升格教训 "≤ 5d 短窗可破 20d 对称化抹平" 本批第一锤**硬证伪**——5d up-day Amihud max_corr 从 20d 的 0.942 降到 0.754（asymmetry 部分存在），但 alpha_survival 反塌到 0.149 (F012 0.443 的 34%), ic_oos 仅 0.020 是 F012 的 60%。短窗**减少对称化抹平**但**放大 noise + 同样 vol-coupling**——trade-off 负面。T005 复活 (a) 条件建议升格为 disproven，仅留 (b) "quantile-based asymmetry (非 mean)" 待验证。

- **方向兑现**: 1 admit / 6 candidates, admit 命中率 17%（与 batch_046 同）；本批 C001 admit 质量**略弱于** F015 (alpha_surv 0.58 vs 0.66, mdd -1.57 vs -1.61 近似, split_dispersion 0.10 vs 0.11 略优); 但机制价值高——rank-diff 泛化首锤兑现。

## Thread 进展

> [!success]+ T007 [[directions/microstructure_illiquidity#T007]] — `[◐ PARTIAL-ANSWERED batch_047]`
> **rank-diff 跨 signal family 泛化验证**：
> - C001 (分母字段替换 amount_CV → turnover_CV) → **admit** → amihud_turnover_cv_rank_diff_20。证实 rank-diff 结构是 signal-family-组合的几何性质，不限于特定字段对。
> - C002 (跨 direction pb_amount vs Amihud) → hard_gate noise。T007 范式第一个约束：rank-diff 跨 direction 时需 raw field-level 独立（$amount 共分母会抵消）。
> - C003 (最远跨 direction amount_CV vs overnight) → signed negative incr_ic reject。T007 范式第二个约束：一端被已有库因子主导吸收时 rank-diff 退化为主导端反号，signed incr_ic 为负。
>
> **结论**: T007 范式可行空间**收窄**为"同 direction 内部 scale-free × scale-free 字段对换"。下轮可测:
> - Amihud × correlation-based 测度（如 `Corr($close, $amount, 20)`）—— 两端都是无量纲统计量
> - 库内其他 scale-free 对: F011 (overnight) × F015-scale；F007 (upper shadow) × F008 (open position) rank-diff 等
> - "field-level 独立 + scale-free" 双条件的跨 direction 候选（绕开 $amount 共分母）
>
> Thread 改 ACTIVE（partial answered），未关闭。

> [!failure]+ T005 [[directions/microstructure_illiquidity#T005]] — `[✗ FURTHER-DISPROVEN batch_047]`
> **≤5d 短窗 sign-conditional 复活条件 (a)**: C005 硬证伪——5d up-day Amihud alpha_survival=0.149 severe poor，max_corr 0.754 仍 high。减少 20d 对称化抹平但同步放大 noise + vol-coupling 不减。
> **非 mean aggregation 测度 (max-min range)**: C006 reserve——5d Amihud range 与 F012 level 共变 86%，range-based 测度不足以从 level 引力 escape。
> **T005 复活条件剩余**: (a) 短窗证伪；(max-min range 证伪)。仅 **quantile-based asymmetry (P90-P10)** 未测——这是 T005 唯一可能复活的 DSL 层路径；minute-bar 数据未来若接入可重开 symmetric vs sign 测试。
> Thread 建议改 ✗ DISPROVEN (a) 条件, 保留 ACTIVE 等 quantile 测试。

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
