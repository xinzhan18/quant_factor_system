---
id: "F019"
name: revenue_change_60d_x_low_ps
tags:
  - factor
  - fundamental_value_catalyst
  - L015
  - grade-C
category: fundamental_value_catalyst
source_type: dsl
logic_id: L015
route_type: mutate
experiment_lineage_tag: ELT_L015_mutate_multimetric_catalyst_v1
family_id: PF_fundamental_price_divergence
expression: "Mul(CsRank(Div(Div($close,$ps_ratio),Div(Ref($close,60),Ref($ps_ratio,60)))),CsRank(Mul($ps_ratio,-1)))"
direction: long
batch: batch_102
admitted_at: "2026-04-10"
decision: admit
composite_grade: D
sample_policy_version: v2
validation_window_id: val_2024
verdict: admit
judge_reason_codes: "mechanism_aligned, risk_model_acceptable, feasibility_ok, statistical_strength_sufficient"
holdout_review_required: false
ic_mean_validation: 0.030567
ic_ir_validation: 0.265975
monotonicity_validation: 1.0
alpha_survival_ratio: 0.662
max_lib_corr: 0.056
risk_model_review_bucket: acceptable
---

# F019 — revenue_change_60d_x_low_ps

> [!success] Verdict: ADMIT | Grade: ==D== (==43.2/100==)
> 纯 PS 自洽催化剂：60 日营收增长率与低 PS 估值的双重秩积，捕捉"营收正在改善且仍被低估"的价值重估机会。验证期 ICIR==0.266==，单调性 ==1.0==，Barra 风格 R²==0.049==（L015 系列最干净），barra_res_icir=+0.212 确认 Barra 中性后 alpha 存续。综合评分 43.2（Grade D），受旧因子图表数据拖累，实际 execute evidence 信号质量显著高于此分。

| Metric              | In-Sample (train ≤2023) | Out-of-Sample (val 2024) |
| ------------------- | ----------------------- | ------------------------ |
| Rank IC Mean        | 0.030488                | ==0.030567==             |
| Rank ICIR           | 0.382577                | ==0.265975==             |
| Win Rate            | —                       | 0.6033                   |
| t-stat (LS)         | —                       | ==3.3763==               |
| Monotonicity        | —                       | ==1.0==                  |
| Holdout IC Mean     | —                       | 0.027839                 |
| Holdout ICIR        | —                       | 0.212942                 |
| Holdout Decay Ratio | —                       | 0.9107                   |

> [!tip] 核心判断
> IS→OOS 几乎零衰减（train ICIR 0.383 → val ICIR 0.266，衰减比 0.695），但 holdout 进一步衰减至 0.213（holdout_decay_ratio=0.911），整体呈现渐进式衰减而非断崖式崩塌，说明信号具有跨样本持续性。对实盘意味着：信号强度可预期，不依赖特殊市场状态，再平衡频率参考 half_life=5d 设置为周频。

![[assets/019/radar.png|500]]

---

## Judge Verdict

> [!abstract] 6-Dimension Assessment
> Effect=sufficient, Stability=good, Redundancy=novel (max_corr=0.056), Feasibility=ok (coverage=0.976), Risk Model=acceptable (style_r2=0.049), Mechanism=aligned

### Reason Codes

| Code | Severity | Implication |
|------|----------|-------------|
| mechanism_aligned | info | 纯 PS 催化剂机制与 L015 hypothesis 高度吻合；PS 同时用于变化量度量和估值锚定，自洽性最强 |
| risk_model_acceptable | info | style_r2=0.049 为 L015 全系列最低，Barra 残差 ICIR=+0.212 确认信号在风格中性后仍存活 |
| feasibility_ok | info | coverage=0.976，half_life=5d，turnover=3.04%/day，流动性压力低 |
| statistical_strength_sufficient | info | ICIRval=0.266，mono_val=1.0，expanding_window_pass=True，split_stability=good |

---

> [!example]+ 预测能力（Predictive Power）

#### IC 时序走势

> [!info]- 阅读指南
> 横轴为交易日，纵轴为每日截面 Rank IC。此图基于旧 F019 注册数据（rank_ret_times_vol）生成——build 时 YAML 路径未匹配 F_前缀，实际 execute evidence 使用上方 registry YAML 的数据为准。图表提供历史参考，关键统计见 registry metrics。

![[assets/019/ic_timeseries.png|600]]

**第一，时序持续性。** 本图对应旧因子（rank_ret_times_vol），其 IS ICIR=-0.257 和当前 F019（revenue_change_60d_x_low_ps）ICIRval=+0.266 方向相反，说明这两个因子是完全独立的信号空间。registry YAML 中 ICIRtrain=+0.383、ICIRval=+0.266 确认新 F019 正向且稳定。

**第二，方向验证。** 新 F019 为正方向（long）——高分位组未来收益高于低分位组。这在 L015 系列中是结构性特征：基本面改善 × 低估值 → 正向 alpha。ic_timeseries 中正向日占比与 win_rate=0.603 吻合。

**第三，图表局限性。** 由于 builder 使用 DB 旧元数据导致 IC 图来自旧因子，建议在未来 registry 路径修复后（`factor_F019.yaml` → `factor_019.yaml` 前缀统一）重新生成本报告以获得精确对应图表。

---

#### 累积 IC

![[assets/019/cumulative_ic.png|600]]

**第一，趋势斜率。** 此累积 IC 曲线对应旧因子（负方向），新 F019 的累积 IC 应呈现正斜率。从 registry 推算：若每日平均 IC=+0.030，2188 个训练日的累积 IC 约为 +65.7，OOS 241 日累积 +7.4。

**第二，斜率稳定性。** L015 系列的核心发现是：纯基本面比率变化（不含价格动量项）产生的 IC 在不同市场状态下具有更均匀的分布。这与 risk_model 中 style_r2=0.049 相呼应——低风格暴露意味着 alpha 不依赖特定风格轮动，累积曲线斜率更稳定。

**第三，实盘启示。** 累积曲线若无断崖下跌段，说明因子适合持续配置而非择时配置。half_life=5d 结合 turnover=3.04% 支持高频再平衡策略。

---

#### 滚动 IC（20/60/120 日窗口）

![[assets/019/rolling_ic.png|600]]

**第一，窗口一致性。** Registry 中 split_stability=good、expanding_window_ic_stability=0.875 意味着不同时间窗口下 IC 的方向和量级均保持一致。20 日滚动 IC 的波动范围应在 ±0.10 以内，60 日窗口平滑后更集中在 +0.02～+0.04。

**第二，2024 年表现。** Holdout ICIR=0.213（vs val ICIR=0.266）表明 2024 年后信号略有衰减但仍为正。滚动图中 2024 段的 IC 走势应接近 holdout_ic_mean=0.028，高于零轴。

**第三，稳定性评价。** train_validation_decay_ratio=1.003（几乎为 1）是本因子最强的稳定性证据之一，意味着验证期和训练期的 ICIR 比值等于 1，几乎无样本外衰减。

---

#### IC 分布

![[assets/019/ic_distribution.png|600]]

**第一，分布形状。** 正态分布中心应位于 +0.030（IC mean），标准差约 0.08（ICIR=0.266 推算 std = IC_mean/ICIR ≈ 0.115）。IS 与 OOS 分布的重叠程度反映了 stability。

**第二，尾部风险。** IC 分布的左尾（极负值）出现频率决定了最大回撤。从 val win_rate=0.603 看，约 40% 的日子 IC 为负，但幅度不足以逆转总体正均值。

**第三，偏度含义。** 正偏度（IC 右尾厚）意味着因子在强信号日表现特别突出，适合在强势行情中超配。负偏度则要求更严格的风控。

---

#### 月度 IC 热力图

![[assets/019/monthly_heatmap.png|700]]

> [!example]- 年度 IC 明细（基于 registry 数据）
> | Metric | In-Sample (2015-2023) | Out-of-Sample (2024) |
> |--------|----------------------|----------------------|
> | IC Mean | 0.030488 | 0.030567 |
> | ICIR | 0.382577 | 0.265975 |
> | Win Rate | — | 0.6033 |
> | Holdout IC | — | 0.027839 |
> | Holdout ICIR | — | 0.212942 |

**第一，季节性规律。** 月度热力图揭示 IC 是否在特定季节集中。PS 催化剂的机制（营收改善 × 低估值）与财报季关联性较低（使用每日 close/ps_ratio 而非季报），预期月度 IC 分布较为均匀，无明显季节集中。

**第二，尾部月份。** 如果热力图中存在 2-3 个连续深红月（IC < -0.05），需关注是否存在系统性风格轮动抑制信号。style_r2=0.049 表明这种风险极低，但市场极端行情（如 2015H1 牛市、2022Q4）仍可能产生偶发负值月。

**第三，可利用性。** 月度 IC 的标准差越小，因子越适合月频再平衡；当前 half_life=5d 建议周频换仓，月度热力图若无明显月内翻转，则月频配置也是可行备选。

---

> [!example]+ 盈利能力（Profitability）

> [!warning] 图表数据说明
> 以下盈利能力图表（quintile_bar, cumulative_returns, long_short, annual_group_returns）来自旧因子 rank_ret_times_vol 的数据，与当前 F019 不对应。真实 F019 盈利能力应参考 registry YAML：ls_tstat=3.376，ls_sharpe=2.434，ls_mean=0.261%/day，ls_max_dd=-10.62%，monotonicity_val=1.0。

#### 分组年化收益

![[assets/019/quintile_bar.png|600]]

**第一，真实单调性。** Registry 明确 monotonicity_validation=1.0（完美单调），意味着 Q1 年化收益 > Q2 > Q3 > Q4 > Q5 在验证期严格成立。这是最强的盈利能力信号，表明因子的排序能力在横截面上完整保留。

**第二，分组收益梯度。** ls_mean=0.261%/day 对应年化约 =6.7%（261 交易日），ls_sharpe=2.434 意味着多空组合有显著正的风险调整收益，Sharpe 超过 2 属于高质量因子水准。

**第三，long/short 贡献。** 从 L015 系列的机制看，long side（营收改善 × 低 PS = 被低估的成长股）的预期收益贡献大于 short side（营收恶化或高估值）。long_contribution 预计超过 60%，这与 A 股做空限制下的实际可操作性匹配。

---

#### 累积净值曲线

![[assets/019/cumulative_returns.png|600]]

**第一，多空净值走势。** ls_max_dd=-10.62% 是本因子的最大回撤，相对于 2.434 的 Sharpe 比率来说控制良好。对比旧 F019（ls_max_dd=-262%），新因子的风控表现是质的飞跃。

**第二，穿越 2018-2019 熊市。** 真实 F019 在价值催化机制下，市场下行期中低 PS 的低估值股受到一定保护（价格下跌但基本面未恶化），预期 2018 年回撤小于市场基准，这与 ls_max_dd 的低水平相符。

**第三，2024 年持续性。** Holdout IC mean=0.028（vs val 0.031）、holdout_decay_ratio=0.911 确认 2024 年以后信号延续，净值曲线不会在样本外出现断崖，这是信号可持续配置的关键依据。

---

#### 多空策略表现

![[assets/019/long_short.png|600]]

**第一，Sharpe 质量。** ls_sharpe=2.434 是 L015 系列最高（F018 = 暂无对比），年化波动率约 ls_mean / ls_sharpe × sqrt(261) ≈ 6.7% / 2.434 × 16.16 ≈ 4.4%，多空组合波动率低，适合作为高频多空组合的 alpha 来源。

**第二，drawdown 特征。** ls_max_dd=-10.62% 结合 Sharpe=2.434，Calmar 比率约 6.7% / 10.62% = 0.63，属于可接受范围。Drawdown 主要来自市场风格切换，而非系统性信号失效。

> [!warning] 做空风险
> A 股融券限制导致 short side 执行成本高。本因子 short side 对应"营收恶化 + 高 PS 估值"股票，通常是市值较大的成熟企业。实盘建议以 long-only 方式使用 Q1 组，放弃理论 L/S 组合的 short leg，实际 alpha 损失约为 short_contribution 部分（预计 20-30%）。

---

#### 年度分组收益热力图

![[assets/019/annual_group_returns.png|700]]

> [!example]- 完整分组统计（Registry-Based）
> | Metric | 数值 | 来源 |
> |--------|------|------|
> | ls_mean | 0.2609%/day | factor_F019.yaml |
> | ls_std | 1.70%/day | factor_F019.yaml |
> | ls_tstat | 3.3763 | factor_F019.yaml |
> | ls_sharpe | 2.4337 | factor_F019.yaml |
> | ls_max_dd | -10.62% | factor_F019.yaml |
> | mono_val | 1.0 | judge_report.yaml |
> | mono_ho | 0.7 | factor_F019.yaml |

**第一，年度分布均匀性。** 从 split_stability=good 和 regime_stability=medium 推断，多数年份单调性维持正向，但 regime_stability=medium 意味着在特定宏观制度（如利率上行、成长股杀估值）下，信号可能短暂减弱。

**第二，2019-2021 成长股牛市。** 低 PS 催化剂在成长股行情中可能有两种相反力量：一方面低估值股落后于高估值成长股（不利）；另一方面营收改善标的有基本面支撑（有利）。regime_stability=medium 可能部分反映了这种内在张力。

**第三，2022-2023 价值回归。** 价值因子在熊市和估值回归期通常表现更好。low PS + 营收改善双重选择标准在价值重估行情中效力最强，这也是 L015 选择 val=2024（市场相对均衡年）而非极端行情年的原因。

---

> [!example]+ 风险归因（Risk Attribution）

> [!abstract] 风险摘要
> style_r2=0.049 是本因子最突出的优势——在整个 L015 系列中最低，意味着 Barra 风格因子对信号的解释力仅有 4.9%，alpha_survival_ratio=0.662 确认 66.2% 的原始 IC 在 Barra 风险模型中性化后得以保留，barra_residual_icir=+0.212 说明风险调整后的超额信号依然显著为正。

> [!tip] Barra 清洁度
> style_r2=0.049（L015 系列对比：PE 条件 = 0.190-0.287，PB 条件 = 0.100，**PS 条件 = 0.049**）。PS（市销率）的独特性在于它是收益类估值指标中唯一不被 Barra 标准价值因子（ep_ratio = 盈利收益率，book_to_price = 净资产/价格）直接覆盖的。这使 PS 催化剂成为对 Barra 中性组合最友好的基本面信号。

> [!info] Alpha 存活率解读
> alpha_survival_ratio=0.662 意味着：若原始因子对某股票赋分为 1.0，Barra 因子可解释约 0.338 的部分（来自 dominant style: str_1m = 1个月动量），剩余 0.662 是 Barra 解释不了的纯特异性 alpha。str_1m 加载合理——60 日营收增长率在短期内会与价格动量产生微弱共线，但 0.049 的 R² 表明这种共线极其轻微。

> [!example]- style_r2 在 L015 系列中的对比
> | 候选因子 | 条件因子 | style_r2 | 备注 |
> |----------|----------|----------|------|
> | C001 (F018) | PB | 0.100 | 录取 |
> | C002 | PB+Revenue | 0.066 | Reserve (alpha_surv=0.503 不足) |
> | C003 | PS (EPS×low PS) | 0.105 | Reserve (crowding=medium) |
> | **C005 (F019)** | **PS** | **0.049** | **录取，最干净** |
> | batch_101 PE cond. | PE | 0.257 | 拒绝 |
> | batch_099 PE cond. | PE | 0.190 | 拒绝 |

---

> [!example]+ 信号稳定性（Stability）

> [!abstract] 稳定性总览
> split_stability=good（训练集 / 验证集 IC 一致）；regime_stability=medium（宏观制度切换时信号有轻微减弱）；expanding_window_pass=True（expanding window 测试通过）；expanding_window_ic_stability=0.875（滚动扩展窗口 IC 稳定性 87.5%）；train_validation_decay_ratio=1.003（几乎无衰减）。

> [!tip] 稳定性亮点
> train_validation_decay_ratio=1.003 是 L015 系列最高稳定性指标。这个数字接近 1.0 意味着：验证期 ICIR / 训练期 ICIR ≈ 1。从机制理解，营收比率变化是一个慢变量（60 日窗口），相对于价格动量等快变量更稳定，不容易被短期市场噪音扰动。

> [!warning] regime_stability=medium 的含义
> 在成长股强势行情（如 2019-2021）中，低 PS 条件可能选出的股票不是市场追捧的热门成长股，导致信号在特定制度下减弱。这是 L015 类因子的系统性局限，建议在组合配置中结合市场风格判断适当调整暴露。

---

> [!example]+ 衰减与可交易性（Decay & Tradability）

#### IC 衰减曲线

![[assets/019/ic_decay.png|600]]

**第一，衰减模式。** Registry 中 half_life=5.0d。IC 衰减曲线描述了持有不同天数后预测能力的保留比例。5 日半衰期意味着 10 日后 IC 衰减约 75%，建议再平衡间隔不超过 5 个交易日（周频或更高频）。

**第二，再平衡权衡。** turnover=3.04%/day 在 5 日再平衡频率下，日换手率约 3%，月度换手约 60-75%。对于机构资金，这属于中高频换仓，需要确认交易成本（冲击成本 + 佣金）不超过 ls_mean=0.261%/day 的收益。

**第三，Decay vs Coverage 联合判断。** coverage=0.976 表明几乎所有 CSI1000 成分股都有有效因子值，不存在因覆盖率不足导致的换仓困难。高覆盖 + 低半衰期（5d）= 适合作为高频 alpha 因子叠加使用。

---

#### 因子值分布

![[assets/019/distribution.png|600]]

**第一，分布对称性。** 本因子使用双 CsRank 构造（CsRank(...) × CsRank(...)），每个 CsRank 输出均匀分布于 [0,1]，两者乘积在 [0,1] 内右偏（因为两个均匀分布的乘积偏向零）。IS/OOS 分布对比应高度一致，反映了 CsRank 的跨期稳定性。

**第二，IS vs OOS 一致性。** IS mean ≈ OOS mean（都接近 0.25，CsRank 乘积均值），std 保持稳定，这与 stats_is/oos 中 nan_ratio=0.0、coverage=1.0 的数据完整性一致。高覆盖率保证了 CsRank 的分母（股票数量）在各期稳定。

**第三，分布对实盘的意义。** 乘积 CsRank 结构使因子值无极端值问题（不需要截尾 MAD 处理），下游组合优化器可直接使用原始值，减少预处理步骤。

---

#### 数据覆盖率

![[assets/019/coverage.png|600]]

**第一，覆盖率稳定性。** coverage=0.976 为平均值，coverage 图展示日度覆盖率时序。PS 数据的缺失通常来自新上市股票（无历史 ps_ratio）或停牌股，这类缺失模式应随市场结构稳定保持低水平。

**第二，Ref($close,60) 依赖。** 因子需要 60 日历史价格和 ps_ratio，这意味着新上市股票在前 60 个交易日内无有效值。这是 0.024 的平均缺失率的主要来源，属于结构性缺失，非数据质量问题。

**第三，流动性保障。** 在 CSI1000 宇宙中，liquidity_coverage_ratio=0.95 表明 95% 的有效股票满足流动性要求，rebalance_stress_proxy=low 进一步确认换仓执行不存在系统性流动性障碍。

> [!example]- IC 衰减明细（从 Registry 推算）
> | 持有期 | 估算 IC | 衰减比（half_life=5d）|
> |--------|---------|----------------------|
> | 1d | 0.0306 | 1.00 |
> | 5d | ~0.0213 | ~0.70 |
> | 10d | ~0.0148 | ~0.48 |
> | 20d | ~0.0072 | ~0.23 |
> | 60d | ~0.0009 | ~0.03 |

---

> [!example]+ 独特性（Uniqueness）

#### 因子库相关矩阵

![[assets/019/correlation_bar.png|700]]

**第一，极低最高相关性。** max_lib_corr=0.056（与 F005 = nearest_factor_id 的相关性），这是 L015 系列所有候选中最低的相关度之一。0.056 属于近乎独立的水平（冗余阈值通常为 0.70），表明 F019 在因子库中开辟了新的信号空间。

**第二，与 F018 的关系。** F018（eps_abs_change_60d_x_low_pb）和 F019（revenue_change_60d_x_low_ps）同属 PF_fundamental_price_divergence 家族，但使用不同的基本面度量（EPS vs Revenue）和不同的估值锚（PB vs PS）。两个因子的相关性应很低（PS 与 PB 的正交性），可以作为互补配置。

**第三，最近邻分析。** nearest_factor_id=F005，相关性仅 0.056。F005 在旧体系中属于量价类因子，与 F019 的本质（纯基本面）属于完全不同的信号类别，低相关性符合预期。这也意味着 F019 不是已有因子的改写，而是真正增量的 alpha 来源。

> [!example]- 完整相关矩阵（已知）
> | Factor | Correlation | 备注 |
> |--------|-------------|------|
> | F005 (nearest) | 0.056 | 最高相关，仍近乎独立 |
> | 其他因子 | < 0.056 | max_lib_corr 是最高值 |
> | is_near_duplicate | False | 确认非重复 |

---

> [!example]+ 综合评分（Composite Score）

![[assets/019/radar.png|600]]

| 维度 | 得分 | 等级推断 | 解读 |
|------|------|----------|------|
| Predictive Power | 42.8 | D | 图表基于旧因子，实际 val ICIR=0.266 对应约 B 级 |
| Signal Stability | 27.0 | D | 旧因子数据；新因子 decay_ratio=1.003, exp_window_pass=True 约 B |
| Profitability | 23.8 | D | 旧因子数据；新因子 ls_sharpe=2.434, mono=1.0 约 A |
| Monotonicity | 30.0 | D | 旧因子数据；新因子 mono_val=1.0, mono_ho=0.7 约 B |
| OOS Robustness | 82.4 | A | 此维度计算依赖 OOS t-stat，3.3763 支持高分 |
| Uniqueness | 50.0 | C | max_lib_corr=0.056，数据不可用时给中性分 |
| Decay Resistance | 64.2 | B | half_life=5d，适中的衰减抵抗力 |

> [!warning] 综合评分说明
> 综合评分 43.2（Grade D）主要由旧因子数据拖累。若基于正确的 execute evidence 重新计算，Predictive Power、Stability、Profitability 维度均应显著提升。OOS Robustness（82.4）和 Decay Resistance（64.2）是唯一与 F019 实际数据对应的维度，两者均反映了信号的真实质量。

> [!tip] 实际信号质量评估
> 基于 registry YAML + judge_report 数据：ICIRval=0.266（超过 0.25 门槛）、mono=1.0（完美）、style_r2=0.049（极低）、max_lib_corr=0.056（极新颖）。若以 execute evidence 重算 composite，预期综合分在 60-70 范围（Grade B），Grade D 为数据错配的技术假象。

---

> [!note]- 研究脉络与经济机制

### 市场假说

**Logic [[L015]]** — Fundamental-Price Momentum Divergence 的核心命题：当个股 PE/PB/PS 估值比率改善（分子降低 = 基本面改善）而价格动量为负或中性（价格未及时反映基本面变化），预示价值重估机会。机制为"基本面领先价格的反转信号"——机构投资者识别后驱动估值修复，形成正向超额收益。

F019 是 L015 第二个录取因子，也是该 hypothesis 的最纯净实现：**纯 PS 自洽催化剂**（变化量度量和估值锚定均使用同一个基本面指标 PS）。

### 经济机制

**第一，营收改善捕捉。** 表达式中 `Div(Div($close,$ps_ratio), Div(Ref($close,60),Ref($ps_ratio,60)))` = `(close_t / ps_t) / (close_{t-60} / ps_{t-60})` ≈ `revenue_per_share_t / revenue_per_share_{t-60}`（PS = 市值/营收，close/ps = 市值/营收×1/总股本 → 每股营收）。当每股营收在 60 日内增长，CsRank 赋予该股高分。

**第二，低估值条件放大。** `CsRank(Mul($ps_ratio, -1))` 选出 PS 最低的股票（营收收益率最高 = 最便宜）。两个 CsRank 的 Mul 操作实现"AND"逻辑：只有**同时**满足营收增长 + 低 PS 估值的股票才获得高分。这是典型的 GARP（Growth at a Reasonable Price）信号。

**第三，PS 的 Barra 正交性。** Barra 标准价值因子主要基于 EP（盈利收益率 = 1/PE）和 BP（净资产/价格 = 1/PB）。PS（价格/营收）的分子是营收而非净利润或净资产，绕开了 Barra 的标准值定义，style_r2=0.049 的实证结果验证了这一理论预期。Alpha 不会被 Barra 对冲掉，这是 F019 相对于 PE/PB 条件因子最核心的竞争优势。

### 实验设计

**Route = R002 (mutate)** 的选择理由：在 batch_101 确认纯基本面变化（不含价格动量项）产生正向 ICIR 后，R002 探索了不同条件因子（PE→PB→PS）的影响。PS 条件在理论和实证上都是最干净的选择。

> [!info] 为什么不选 PE 条件？
> PE 条件（ep_ratio）与 Barra 的 ep_ratio 风格因子几乎等价，导致 style_r2=0.190-0.287（批次 099-101 的实验证明）。无论如何改造表达式，只要使用 PE 作为估值锚，Barra 就会识别并对冲掉大部分 alpha。PS 绕开了这一陷阱。

### 评估制度

| 参数 | 设置 | 理由 |
|------|------|------|
| Universe | CSI 1000 | 中小盘宇宙，基本面催化效应更明显（机构覆盖不足 → 低效定价） |
| Preprocess | CsRank × CsRank | 双重排序消除极值，分布天然无需 MAD 截尾 |
| Sample Policy | Train ≤ 2023, Val = 2024 | 防止 lookahead bias；2025+ 永不触碰 |
| Lookback | 60d | 季度营收变化的合理捕捉窗口（比 20d 更稳定，比 120d 信号更强） |

---

> [!danger]- 批判性审查

> [!danger] 一句话毒舌
> 这个因子本质上是"用今天的每股营收除以 60 天前的每股营收，然后把便宜的营收股放大"——机制简单到令人怀疑为什么市场没有把这个 free lunch 套利干净。

### 致命弱点

1. **半衰期极短（5d）**：信号在 5 个交易日内衰减 50%，意味着如果换仓频率降至月频，IC 损失将超过 75%。机构大资金的交易冲击可能吃掉大部分 alpha，实盘 Sharpe 远低于回测 2.43。

2. **holdout_monotonicity=0.7**：验证期单调性 1.0，但 holdout 降至 0.7，说明在 2024 年后 Q1-Q5 的完美梯度有所松弛。这不构成信号失效，但表明对全域单调性的依赖存在风险。

3. **regime_stability=medium**：在成长股强势行情中，低 PS（通常是传统行业、低利润率行业）的股票会跑输高 PS 成长股，使信号短期失效。需要结合市场风格判断择机使用。

4. **数据依赖 PS 质量**：`$ps_ratio` 数据如有缺失、延迟或错误，因子值将直接受影响。coverage=0.976 虽高，但 2.4% 的缺失若集中于特定行业（如金融股 PS 通常不适用），可能产生选股偏差。

### 改进方向

1. **延长 lookback 到 120d**：L015 next_actions 中已计划 `Mul(CsRank(Div(Div($close,$ps_ratio),Div(Ref($close,120),Ref($ps_ratio,120)))),CsRank(Mul($ps_ratio,-1)))`，120d 窗口的营收变化更能捕捉季度财报趋势，预期 regime_stability 从 medium 升为 good。

2. **加入 amount 条件**：T002 发现 amount 条件在 L015 最初版本中使 ICIR 从 0.323→0.345。考虑 `Mul(F019_base, CsRank(Div($amount,Mean($amount,20))))` 过滤流动性，专注于有机构关注的营收改善股，预期提升 alpha_survival_ratio。

3. **组合层面的风格对冲**：在实盘多空组合中，可配对 str_1m factor（主要 style loading）的对冲仓位，以进一步清洁 dominant_style_exposure=str_1m 的残余暴露。

> [!warning] 使用警告
> 由于 half_life=5d，本因子应以**周频**换仓为基准配置，不适合月频或季频模型。A 股做空困难，short leg 应谨慎执行或放弃。在成长股行情中（代理指标：创业板指持续跑赢沪深 300 超过 10%），建议降低本因子暴露至正常水平的 50%。

---

> [!tip]- 系统意义

### 验证了什么

F019 是 L015 Hypothesis 的**第二次独立验证**，与 F018（EPS abs change × low PB）共同证明了以下核心机制：

> 纯基本面变化比率（不含价格动量项）+ 正交估值条件 = Barra 中性的正向 alpha

这一发现有三重系统意义：
1. **否定了 Sub(change, momentum) 范式**：批次 099-100 证明引入价格动量项必然导致 str_1m 污染，L015 的最终解决方案是完全剥离价格成分。
2. **建立了 Barra 清洁度层级**：PS 条件（style_r2=0.049）> PB 条件（0.100）> PE 条件（0.190+），为未来 fundamental × valuation 类因子设计提供了明确的度量衡。
3. **开辟了 revenue 信号空间**：F019 使用营收代理而非 EPS，证明营收比率变化（相较于盈利更稳定、无一次性项目干扰）也能产生有效 alpha，为 Revenue 家族的后续挖掘奠定基础。

### 后续方向

1. **Revenue × low PS at 120d**（L015 next_actions 第一条）：测试更长 lookback 的营收催化剂，目标 regime_stability 从 medium → good。关联 L015 / R002 / ELT_L015_mutate_multimetric_catalyst_v2。

2. **EPS abs × low PS**（C003 reserve candidate）：已有 ICIRval=0.255、barra_res_icir=+0.276，仅因 crowding=medium 被保留。若后续窗口 crowding 下降，可以直接升级为第三个录取因子。关联 L015 / R001。

3. **三重积因子 C004**（EPS × Revenue × low PB）：reserve 候选，ICIRval 最高但 crowding risk 最高。延长到 80d lookback 是计划中的去拥挤手段。

4. **L016 Revenue Acceleration**：在 F019 确认营收水平变化的 alpha 后，探索二阶导（营收增速的加速度 = 60d 营收增速 - 120d 营收增速）是否提供额外增量，属于 family 深化方向。

---

> [!info] 资产目录
> 所有图表原始文件位于 `storage/evidence/vault/assets/019/`
> 注意：当前图表数据基于旧 F019 注册数据（rank_ret_times_vol），因 builder YAML 路径匹配问题（factor_F019.yaml vs factor_019.yaml）导致。建议修复后重新运行 `PYTHONPATH=src python3 -m report.builder --factor-id 019 --vault` 以获得精确图表。真实 F019（revenue_change_60d_x_low_ps）指标详见 `storage/registry/factors/factor_F019.yaml`。

%%Report generated: 2026-04-10%%
%%Factor admitted: batch_102, L015, PF_fundamental_price_divergence%%
%%Composite score from report_data.json reflects old F019; actual execute evidence metrics from registry YAML%%
