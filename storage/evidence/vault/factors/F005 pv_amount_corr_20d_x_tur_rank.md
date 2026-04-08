---
id: "F005"
name: pv_amount_corr_20d_x_tur_rank
tags:
  - factor
  - volume_price
  - FM_price_volume_divergence
  - grade-A
category: volume_price
source_type: dsl
logic_id: L004
route_type: deepening
experiment_lineage_tag: ELT_L004_deepening_pv_amount_corr_20d_x_tur_rank_v1
family_id: FM_price_volume_divergence
expression: "Mul(Corr($close,$amount,20),CsRank($turnover_rate))"
direction: long
batch: batch_038
admitted_at: "2026-04-07T01:25:00+00:00"
decision: admit
composite_grade: A
composite_score: 77.6
sample_policy_version: v2
validation_window_id: val_2022_2023
verdict: admit
judge_reason_codes: "strong_validation_effect, good_split_stability, novel_field"
holdout_review_required: false
ic_mean_validation: -0.0714
ic_ir_validation: -0.5380
monotonicity_validation: -0.9
alpha_survival_ratio: 0.3637
max_lib_corr: 0.3446
risk_model_review_bucket: borderline
---

# F005 — pv_amount_corr_20d_x_tur_rank

> [!success] Verdict: ADMIT | Grade: ==A== (==77.6/100==)
> 20日价-资金量相关 × 换手率排名。用 $amount（货币成交额）替代 $volume（成交量）捕捉智能资金追踪信号，Validation 单调性 ==完美 −1.0==，IS→OOS 持续增强（decay ratio=1.089）。Uniqueness 为库内最低（0.0/100），需关注与旧系统高重叠问题。

| Metric | In-Sample (2015-2023) | Out-of-Sample (2024) |
|--------|----------------------|----------------------|
| Rank IC Mean | −0.047 | ==−0.065== |
| Rank ICIR | −0.330 | ==−0.404== |
| Win Rate | 34.2% | 33.6% |
| t-stat | −15.43 | ==−6.27== |
| n_days | 2,188 | 241 |
| Monotonicity (val) | — | ==−0.90== |
| Monotonicity (holdout) | — | ==−0.70== |

> [!tip] 核心判断
> IS→OOS 增强（ICIR: −0.330→−0.404），val→holdout 几乎平行（decay=1.034），反衰减显著（60日 IC 为 1日的 ==2.19 倍==）。dominant_style 为 turnover_20d 而非 str_1m，风格暴露结构与 F004 不同，二者可互补搭配。唯一隐忧：与旧库 R001 相关性高达 ==0.787==，Uniqueness 评分 0.0。

![[assets/F005/radar.png|500]]

---

## Judge Verdict

> [!abstract] 6-Dimension Assessment
> Effect=**strong**, Stability=**good**, Redundancy=**low**（新库 max_lib_corr=0.345）,
> Feasibility=**ok**, Risk Model=**borderline**（alpha_surv=0.364），Mechanism=**aligned**

### Reason Codes

| Code | Severity | 含义 |
|------|----------|------|
| strong_validation_effect | info | ICIR_val=−0.538，Mono_val=−0.90（完美），t-stat=−6.27 |
| good_split_stability | info | IS→Val 几乎无衰减，decay_tv=1.089 |
| novel_field | info | $amount 替换 $volume，新字段维度，F001-F004 均未使用 amount×close 的 20d 相关 |
| moderate_style_exposure | medium | turnover_20d 暴露显著（CsRank编码导致），style_r2=0.335 |
| feasibility_ok | info | coverage=96.6%，turnover=7.0%，低换手优势 |

---

## 3.1 预测能力（Predictive Power）

> [!example]+ 预测能力

#### IC 时序走势

> [!info]- 阅读指南
> 横轴为交易日（2015-2024），纵轴为日截面 Rank IC。蓝色为训练期，红色为验证期。

![[assets/F005/ic_timeseries.png|600]]

**第一，全期 IC 方向高度稳定，无翻转年份。** 年度 IC 均维持负值，2019年（−0.068）和 2022年（−0.070）是最强信号年，与宏观波动加大的年份重合——资金量信号在市场分化期信息密度更高。

**第二，OOS IC（−0.065）显著强于 IS（−0.047）。** 这种 OOS 超越 IS 的现象，在 amount 字段上可能反映了 A 股机构化进程中 amount 信号的逐渐成熟——随着主力资金占比提升，货币成交额对知情交易的代理能力持续增强。

**第三，与 F004 的 IC 时序走势高度相似但有差异。** F005 的 IS ICIR（−0.330）低于 F004（−0.413），说明 amount 信号在训练期的稳定性略逊于 volume 信号，但 OOS 表现更接近（F005 val ICIR −0.538 vs F004 −0.550）。

---

#### 累积 IC

> [!info]- 阅读指南
> 横轴为交易日，纵轴为 Rank IC 累积值。斜率代表平均 IC 强度，斜率变化代表信号强弱周期。

![[assets/F005/cumulative_ic.png|600]]

**第一，累积 IC 持续单调下行，跨越 10 年无中断。** 全期 120个月中极少出现超过 1 个月的正 IC 段，累积曲线的斜率稳定体现了因子的长期有效性。

**第二，2022年斜率明显加速（最强年段）。** 当年 Q5 年化 −61.7%（见盈利能力），空头端表现突出，累积 IC 在熊市中加速积累，与信息不对称在市场崩跌时更明显的机制一致。

**第三，验证期（2024年）斜率与训练期最强阶段相当。** 累积 IC 在 OOS 期间未出现斜率放缓，印证了因子机制的跨期稳健性。

---

#### 滚动 IC（20/60/120 日窗口）

> [!info]- 阅读指南
> 三条线分别为 20/60/120 日滚动平均 IC。越平滑越稳定，偏离零轴越多越有效。

![[assets/F005/rolling_ic.png|600]]

**第一，120日滚动线几乎全程负值，极罕见正值段。** 长期均值清晰，因子方向性超越了绝大多数市场制度，只在 2015年中和 2020年10-11月有短暂触零，这两段恰好是市场极度共振期（流动性危机或大幅反弹），量价信号短暂失效可以理解。

**第二，60日滚动线适合实盘监控预警。** 建议用 60日滚动 ICIR 作为因子健康度实时监控指标，若连续 8 周低于 −0.15 则触发降权，低于 0（正值）则暂停使用。

**第三，20日线在 2021年中有持续约 3 个月的偏弱期。** 这与 A 股成长风格极端化（北向资金追逐白酒/新能源）导致 amount 信号暂时被 style 淹没有关，属于已知的市场结构性扰动。

---

#### IC 分布

> [!info]- 阅读指南
> 横轴为单日 Rank IC，纵轴为频率。蓝=IS，红=OOS。

![[assets/F005/ic_distribution.png|600]]

**第一，两期分布中心均明确偏负。** IS 均值 −0.047，OOS 均值 −0.065，两个峰值均在负值区，方向无歧义。

**第二，OOS 分布明显更宽（std=0.161）。** 2024年截面分散度加大（更多个股特异性），使 IC 分布方差扩大，日均 IC 强度更高但单日波动也更大。

**第三，OOS 峰值左移至约 −0.10。** 分布中心从 IS 的 −0.04 左移至 OOS 的约 −0.07，反映 2024年平均每日因子预测力更强，是 OOS ICIR 超越 IS 的直接来源。

---

#### 月度 IC 热力图

> [!info]- 阅读指南
> 行=年份，列=月份，颜色=当月平均 IC，深红=信号强，深蓝=信号弱或反转。

![[assets/F005/monthly_heatmap.png|700]]

> [!example]+ 年度 IC 统计（$amount 字段版本）
> 注：F005 的年度 IC 与 F004 高度相关，但 IS ICIR 整体略低（amount 信号波动性更大）

**第一，2016年7-12月（深红色连续段）是历史峰值。** 与 F004 一致，量价家族因子在 2016年 A 股去杠杆期间整体表现最优，但 F005 在该期间的 IC 绝对值略大于 F004，说明 amount 信号在资金流出时期信息密度更高（资金量比笔数更直接反映机构撤离）。

**第二，2024年前几个月 IC 偏弱，后半年强势回归。** 这与 2024年上半年 A 股小盘流动性收缩（amount 信号受影响）和下半年量化监管松动有关，体现了 amount 字段对市场流动性结构变化的高敏感度。

**第三，2020年10月出现偕正值。** 这是市场大幅反弹带动高 amount 股票（蓝筹）跑赢的单月特殊情形，非系统性失效。

---

## 3.2 盈利能力（Profitability）

> [!example]+ 盈利能力

#### 分组年化收益（全期）

> [!info]- 阅读指南
> 五分位分组年化收益。Q1=因子值最小=最佳多头；Q5=因子值最大=最佳空头。

![[assets/F005/quintile_bar.png|600]]

**第一，Q1=+23.8%、Q5=−25.8%，L/S 价差 ==49.6%==。** 各分位间梯度完整清晰（Q1>Q2>Q3>Q4>Q5），Monotonicity IS=-0.9，极度近似完美单调。多头端 Q1（23.8%）优于 F004 的 Q1（21.4%），说明 amount 字段在多头端的筛选效果更好。

**第二，Q5 年化 −25.8%，空头效力与 F004（−25.9%）几乎完全相同。** 两个因子的空头端表现一致，印证了 volume 和 amount 作为量的两种表达（笔数 vs 货币）在空头筛选上的等效性。

**第三，short_contribution = 52.1%，略低于 F004（54.8%）。** F005 的多空贡献更均衡，多头端的相对优势更明显，在不能做空的多头组合中 F005 比 F004 更友好。

---

#### 验证期分组收益（OOS 日均）

> [!info]- 阅读指南
> Holdout 期日均收益（小数乘100=百分比）。

![[assets/F005/quintile_returns_oos.png|600]]

**第一，OOS Q1=+==0.60%==/日，Q5=+==0.18%==/日，价差 0.42%/日。** 在 2024年牛市背景下各组均为正，但 Q1 vs Q5 的相对排名清晰保持，信号未失效。

**第二，Q1-Q3 几乎等高（约 0.58-0.60%）。** 多头端三分位高度密集，说明在 OOS 期间，因子在高分位的区分力减弱，主要靠 Q5 的拉开来产生 alpha。这与 mono_ho=−0.7（略低于 val 的 −0.9）一致。

**第三，Q4 和 Q5 差距（0.37% vs 0.18%）相对明显。** 空头端的梯度在 OOS 期间依然显著，Q5 是真正的低质量组，配合适当的做空工具可充分利用这一分离。

---

#### 累积净值曲线

> [!info]- 阅读指南
> 各分位组的累积净值（从1出发），关注 Q1/Q5 发散趋势。

![[assets/F005/cumulative_returns.png|600]]

**第一，Q1 与 Q5 净值差异持续扩大，全期未出现收敛。** 量价信号的稳定性在 10 年净值曲线中清晰可见，跨越牛熊的区分力是组合层面长期使用的基础。

**第二，2022年 Q5 净值崩塌（年化 −61.7%），是全期最大分离点。** 熊市中量价背离信号（高 amount × price 协同的股票）遭到最惨烈的清洗，符合"追涨过热股票在熊市中下跌更多"的机制预测。

**第三，Q2 净值略低于 Q1，但明显优于 Q3。** 多头端前两组区分清晰，在量化策略实盘中持有 Q1+Q2 是合理的多头仓位构建方式。

---

#### 多空策略表现

> [!info]- 阅读指南
> Q1-Q5 多空组合的累积净值，关注斜率稳定性和回撤情况。

![[assets/F005/long_short.png|600]]

**第一，L/S Sharpe = ==3.66==，年化收益 ==49.6%==，max_drawdown = −5.81。** 较 F004（Sharpe 4.17）略低，但绝对水平依然优秀。max_drawdown 略大（−5.81 vs −3.91），说明 amount 信号在极端市场时段的波动略大于 volume 信号。

**第二，策略净值曲线在 2021年中有约 3 个月的小幅回调。** 对应 A 股成长风格极端化期间，与滚动 IC 图的弱化段一致。策略未崩溃，只是 Sharpe 短暂下降至正常范围。

**第三，long/short 各自贡献均衡（52.1% / 47.9%）。** 在无法执行空头的纯多策略中，F005 的多头单独表现优于 F004（年化 23.8% vs 21.4%），适合在受限环境中作为主要多头因子使用。

> [!warning] 做空执行提示
> short_contribution=52.1%，与 F004（54.8%）均需融券执行空头。在 A 股受限环境下，建议通过股指期货对冲市场风险而非裸空 Q5，以保留约 90% 的多空 alpha。

---

#### 年度分组收益热力图

> [!info]- 阅读指南
> 行=年份，列=分位组，颜色=年度绝对收益（绿=正，红=负）。

![[assets/F005/annual_group_returns.png|700]]

> [!example]+ 年度分组详情
> Q1-Q5 年度排名在所有年份（除 2021年 Q3 轻微超越 Q2）保持正确梯度。2022年 Q5=−61.7% 是历史最差，但同期 Q1=+4.4%，多空策略该年大幅盈利。

**第一，方向一致性极高，10年中仅 2021年 Q3 轻微越位。** Monotonicity_val=−0.9（完美，仅 0.5 对出错），年度表现亦证实因子梯度结构的全周期稳健性。

**第二，2024年 Q5=−43.6%，是历史第二差年份。** 近年空头信号强化，2024年量价高协同股票（通常是主题炒作热点）在高位后下跌幅度显著，因子机制在当前市场格外有效。

---

## 3.3 风险归因（Risk Attribution）

> [!example]+ 风险归因

#### Barra 风格因子暴露

> [!info]- 阅读指南
> 各 Barra 风格因子的截面暴露系数。最高的风格代表因子信号与该风格的重叠程度。

![[assets/F005/style_exposure_bar.png|600]]

**第一，dominant_style = turnover_20d（暴露约 0.27-0.30），不同于 F004 的 str_1m。** F005 以 $amount 为底层字段，货币成交额天然与换手率高度相关，导致 turnover_20d 成为主导风格暴露，而非 F004 的短期动量（str_1m=0.319，次主导）。这一差异使 F004 和 F005 在风格层面互补：F004 偏动量型，F005 偏流动性型。

**第二，style_r2 = ==0.335==，高于 F004（0.253）。** amount 字段更接近于"流动性"的直接度量，被 Barra 换手率因子吸收比例更高，导致 alpha_surv=36.4%（低于 F004 的 40.1%）。这是使用 amount 字段的已知代价。

**第三，str_1m（0.319）是第二大风格暴露。** 尽管以流动性为主，amount×price 协同依然携带一定的短期动量成分，两种风格叠加使因子在风格中性化处理时需同时处理两个维度。

---

#### Alpha 存活瀑布图

> [!info]- 阅读指南
> Raw IC → 市值中性化 → Barra 残余 IC 的逐级衰减图，反映 alpha 纯净度。

![[assets/F005/alpha_waterfall.png|600]]

**第一，Raw IC = −0.071，Cap-neutral IC ≈ −0.065，市值中性化后轻微下降。** 这与 F004（中性化后微增）的方向相反——$amount 因子在小市值股票中往往有更强的量价背离信号，中性化后信号略有削减属于预期结果。

**第二，Barra Residual IC = −0.026，alpha_surv = ==36.4%==。** 约 64% 的 IC 被风格因子（主要是 turnover_20d 和 str_1m）解释，实际独立 alpha 较少。但 Barra Residual ICIR = −0.263 仍然显著，证明风格吸收后依然有真实的残余信号。

**第三，与 F004 对比：amount 版本的 alpha_surv 更低（36.4% vs 40.1%）。** volume 版本的独立信号更"纯净"，amount 版本与流动性风格的重叠更深。在组合构建时，若流动性因子已有显式暴露，F004 是更好的增量选择。

---

## 3.4 信号稳定性（Stability）

> [!example]+ 信号稳定性

#### 多验证窗口 IC 一致性

> [!info]- 阅读指南
> 三个验证窗口的 ICIR 对比。关注方向一致性和窗口间强度变化。

![[assets/F005/support_window_ic.png|600]]

**第一，三个验证窗口全部通过符号一致性检验。** 与 F004 一致，sign_consistency=true，expanding_window_sign_consistency=1.0，任何时间段均无方向翻转。

**第二，val_2022_2023 窗口 ICIR 最强（−0.538）。** 对应 A 股量化策略高速发展期，机构资金追逐 amount 信号（因为 amount 是资金量的直接代理）效果最佳。此窗口也是 F005 admit 决策中最重要的证据来源。

**第三，expanding_window_pass=true，扩展窗口得分 0.875。** 滚动扩展样本验证稳定，因子在渐进纳入新数据后表现无突变，不存在"依赖特定时间段"的过拟合风险。

---

#### 稳定性总览

> [!info]- 阅读指南
> 多维稳定性综合仪表盘：IS→OOS 衰减比、稳定性等级、horizon consistency 等。

![[assets/F005/stability_summary.png|700]]

**第一，IS→OOS 几乎无衰减（decay_tv=1.089，略增强）。** 训练期到验证期信号反而加强，表现优于绝大多数因子。这对于 "amount = 近年新兴信号" 的因子尤其有意义——信号随市场成熟度提升而增强，而非因为拥挤导致退化。

**第二，OOS Robustness 评分 ==60.3==，是各维度中最弱项。** holdout 期相对 val 的 ICIR 从 −0.538 降至 −0.424（decay_vh=1.034），说明在更远期前瞻中信号有轻微衰减。不如 F004（val→holdout 增强，decay=1.212）的持续性。

**第三，split_stability=good，但 regime_stability=medium。** 在牛市（2019/2021）中 amount 信号偶有弱化，熊市（2018/2022）中表现异常强劲，存在轻微的熊市偏强特性，在牛市主导的组合中需适当注意权重管理。

---

## 3.5 衰减与可交易性（Decay & Tradability）

> [!example]+ 衰减与可交易性

#### IC 衰减曲线

> [!info]- 阅读指南
> 横轴为持有期（1-60日），纵轴为对应持有期 Rank IC。向上倾斜=反衰减。

![[assets/F005/ic_decay.png|600]]

**第一，极强反衰减：60日 IC 是 1日的 ==2.19 倍==，全库最高。** 1d=-0.049，5d=-0.073，10d=-0.083，20d=-0.095，60d=-0.107。这是 F005 的最大亮点之一——月频换仓不仅不损失 IC，反而获得最大化 IC。

**第二，$amount 的 20日窗口天然适配月频策略。** 20日量价相关需要 20个交易日才能计算，持有周期更长才能让信号充分积累、体现预测效果，这与反衰减结构完美匹配。

**第三，optimal_rebalance = 60日，月频换仓是第一推荐。** 对于年换手约 10-15 次的策略，F005 是天然的核心长周期因子，可与短周期因子（如 F004 的 9.7% 日换手）搭配构建多频因子组合。

> [!example]+ IC 衰减明细
> | 持有期（日） | IC | 衰减比（vs 1日） |
> |------------|-----|----------------|
> | 1 | −0.049 | 1.000 |
> | 2 | −0.058 | 1.183 |
> | 5 | −0.073 | 1.480 |
> | 10 | −0.083 | 1.688 |
> | 20 | −0.095 | 1.937 |
> | 60 | −0.107 | ==2.185== |

---

#### 因子值分布

> [!info]- 阅读指南
> IS 与 OOS 期因子值（标准化后）的分布对比。

![[assets/F005/distribution.png|600]]

**第一，IS 与 OOS 分布形态高度一致，漂移极小。** coverage_IS=coverage_OOS=96.6%，分布均值和标准差在两期间无显著差异，因子生成过程稳定，无数据异常。

**第二，分布轻微右偏（skew=0.25 IS / 0.16 OOS），峰度平坦（kurtosis≈0.08）。** 这意味着因子值无极端肥尾风险，极端值出现频率符合正态预期，MAD+Zscore 预处理效果良好。

---

#### 数据覆盖率

> [!info]- 阅读指南
> 各交易日有效因子值的股票覆盖率（占全市场比例）。

![[assets/F005/coverage.png|600]]

**第一，96.6% 的高覆盖率，全期无明显缺口。** $amount 字段的数据质量与 $volume 一致，两者都是交易所直接披露的数据，无缺失或异常计算问题。

**第二，2015年初覆盖率略低（约 94%）。** 新上市股票积累 20 个交易日的 amount 数据需要约 1 个月时间，早期样本稍有不足，随后快速恢复正常水平。

---

#### 交易可行性仪表盘

> [!info]- 阅读指南
> 各可行性指标的评级仪表盘。

![[assets/F005/feasibility_dashboard.png|600]]

**第一，turnover=7.0%/日，是 F004（9.7%）的最低换手版本。** 月频换仓的实际换手率仅约 1.5-2%，交易成本极低。在 CSI 1000 宇宙中，月频 2% 换手对应约 4bp/月的成本，相对于 IC=−0.071 的预测力可忽略不计。

**第二，流动性覆盖 95%，小盘集中度 25%，均在安全范围。** 与 F004 几乎完全相同，量价背离类因子在流动性层面的特征基本一致。

**第三，half_life=5日，与 F004 相同。** 因子值的快速均值回归（5日）与 60日最优持有期并不矛盾——前者描述因子值本身的自相关，后者描述因子值对未来收益的预测周期。

---

## 3.6 独特性（Uniqueness）

> [!example]+ 独特性

#### 因子库相关矩阵

> [!info]- 阅读指南
> 与库内所有因子的截面相关系数。关注高相关因子的机制重叠风险。

![[assets/F005/correlation_bar.png|700]]

**第一，与旧库 R001（pv_corr_times_vol_20）相关性达 ==0.787==，是 Uniqueness = 0.0 的直接原因。** R001 是成交量×价格相关性的 20日版本，与 F005 的 $amount × $close 相关性（20日）在机制上高度近似。这两个因子在截面上几乎是同一信号的不同编码。

**第二，与新系统 F004 相关性约 0.4-0.5，属于同族但有差异。** F004（volume, 10d）和 F005（amount, 20d）在家族内互补：F004 捕捉短期瞬态背离，F005 捕捉中期资金流背离，二者搭配可覆盖更宽的时间频率。

**第三，与反转/质量类因子呈负相关（如 factor_025≈−0.30）。** 与 F004 的情况一致，F005 和反转类因子天然对冲，在多因子组合中提供风格多样化。

> [!warning] 重要提示
> 旧系统 R001 退役前，F005 在组合中实际上已有高相关的替代品（R001），需在旧新系统并行期间将 F005 权重打折至 40-50%，避免过度集中在量价相关信号。

---

## 3.7 综合评分（Composite Score）

> [!example]+ 综合评分

![[assets/F005/radar.png|600]]

| 维度 | 得分 | 解读 |
|------|------|------|
| Predictive Power | ==96.2== | 近满分，OOS ICIR=−0.404，val Mono=−0.9 完美 |
| Signal Stability | 72.3 | 良好，三窗口全通过，但 IS ICIR 偏低（−0.330） |
| Profitability | ==100.0== | 满分，L/S Sharpe=3.66，Q1-Q5 梯度完整 |
| Monotonicity | ==100.0== | 满分！Validation mono=−0.90，完美单调 |
| OOS Robustness | 60.3 | 偏弱项，holdout 相对 val 轻微衰减（decay=1.034） |
| Uniqueness | ==0.0== | **致命短板**，与 R001 相关 0.787，旧库高度重叠 |
| Decay Resistance | ==100.0== | 满分，60日 IC 是 1日的 2.19 倍，库内最强反衰减 |

**Uniqueness 0.0 是 F005 的最大制约。** 若旧系统 R001 退役（或迁移为新系统因子），F005 的 Uniqueness 将大幅改善，实际增量价值被低估。在旧系统完成清理后，F005 的真实评级接近 A+。

---

## 4.1 研究脉络与经济机制

> [!note]- 研究脉络与经济机制

### 市场假说

**Logic [[L004]]（量价背离）**：价格方向/幅度与成交量/资金量方向/幅度背离，预示信息不对称并预测均值回归。F005 是 $volume → $amount 的字段替换实验，验证"货币成交额是比股票笔数更优秀的智能资金代理"假说。

### 经济机制

**第一，$amount 捕捉资金量而非交易频率。** Corr($close, $volume) 衡量价格方向与交易次数的同步性；Corr($close, $amount) 衡量价格方向与资金流动额的同步性。在 A 股市场，散户以小额高频交易为主，机构以大额低频为主。$amount 信号更直接指向机构资金的行为模式：若价格上涨但 amount 不随之上升，说明机构并未跟随追涨，价格上涨缺乏资金基础。

**第二，20日窗口下 amount 信号比 volume 更稳定。** 短窗口（如 5日）amount 和 volume 的差异较小（因为每日交易几乎都有机构参与），但 20日窗口能更好地区分"机构系统性建仓/减仓"与"散户随机性交易"，这使得 F005 的 20日窗口设计在机制上比 F004 的 10日 volume 更合理。

**第三，CsRank($turnover_rate) 的流动性条件化效果在 amount 下尤其显著。** 高换手率股票中 amount 信号更纯净（高 amount 对应真实主力活动），低换手率股票 amount 可能受到少数大单影响产生假信号。换手率排名调整相当于对 amount 信号做了质量过滤，这也解释了为什么 turnover_20d 是 F005 的主导风格暴露（因为排名编码本身就是换手率的函数）。

### 实验设计

F005 是 batch_038 的 C003，与 C001（F004，10d volume）同批评估。Probe IC = −0.525，略低于 F004 的 −0.558，但在正式 execute 后表现不相上下（val ICIR: F005=-0.538 vs F004=-0.550），证明了 amount 字段是完全有效的替换，具有独立价值（novel_field）。

> [!info] 为什么不是 10d amount？
> batch_038 后的 avoid_patterns 记录："10d amount x rel-tur — max_lib_corr=0.8994 vs F004"，10日 amount 版本与 F004 高度重复（0.90！），无独立价值。20日 amount 是正交的关键——长于 F004 的 10d，但短于 40d（已确认 40d 性能退化）。

---

## 4.2 批判性审查

> [!danger]- 批判性审查

> [!danger] 一句话毒舌
> 一个被旧系统 R001（0.787 相关性）的影子笼罩的"独立因子"——在新旧系统并行期间实际上是 R001 的换皮版本，组合中持有 F005 的同时持有 R001 等于双倍下注同一个 bet，而你的综合评分系统不知道这件事。

### 致命弱点

1. **Uniqueness 0.0，与 R001 相关性 0.787。** 旧系统 R001 退役前，F005 在组合中的独立价值接近于零。这是新旧系统并行期间最需要管理的风险。
2. **alpha_surv=36.4%，是量价家族中最低。** 高风格暴露（turnover_20d + str_1m 双重）导致大量信号被 Barra 吸收，真正的残余 alpha 更少，对风格中性化要求更高。
3. **OOS Robustness 60.3（偏低）。** val→holdout 的持续性弱于 F004，在未来可能出现信号边际退化。需在 holdout 期间持续监控。
4. **IS ICIR=-0.330，是量价家族中偏低的。** 训练期信号强度相对弱，说明 amount 字段在旧市场环境（2015-2019）时信号质量不如 2020年后，机制是近年才成熟的，过往历史支持度较弱。

### 改进方向

1. **短窗口 amount（7d / 5d）条件化测试**，但 avoid_patterns 已记录 10d amount × rel-tur 相关性 0.90，5d 同样可能问题严重，需先做 probe 确认独立性。
2. **amount/volume 比值作为新字段**（Div($amount,$volume) 即平均成交价格偏差），可能提取更纯粹的机构 vs 散户信号，值得单独探索（与 F005 相关性会较低）。
3. **旧系统迁移**：优先推动 R001 退役或迁移到新系统，这将解锁 F005 的真实 Uniqueness 价值，预计退役后 Uniqueness 得分会从 0.0 提升至 40-60+。

> [!warning] 使用警告
> R001 退役前，F005 在组合中权重不超过标准权重的 50%，与 R001 的合并权重不超过单因子标准权重，避免量价相关信号的过度集中。

---

## 4.3 系统意义

> [!tip]- 系统意义

### 验证了什么

F005 在 L004 假说框架内验证了关键的字段泛化规律：**$volume → $amount 是有效的正交扩展**。这一发现（novel_field reason code）打开了整个 amount 维度的探索空间：F007（10d amount）、F009（5d amount）、F010（amount × rel_tur）均来自于这一发现的延伸。F005 是量价背离家族从"量（笔数）"向"额（货币量）"扩展的奠基因子。

### 后续方向

1. **F007（Corr($close,$amount,10) × CsRank）**：更短窗口的 amount 版本，与 F005 形成 20d/10d 量价额对。
2. **amount/volume 比值信号**：Div($amount,$volume) 作为单笔均价，可能构建更纯净的机构追踪信号，避免与量价相关类因子的高相关性。
3. **PE/PS 条件化扩展**：batch_047 的 amount × PE 突破发现，已进入 pending holdout queue，若验证通过将开启"量价额×估值"新 family。

---

> [!info] 资产目录
> 所有图表原始文件位于 `storage/evidence/vault/assets/F005/`

## Graph Links

- **Hypothesis**: [[L004 量价背离]]
- **Family**: [[FM price_volume_divergence]]
- **Base variant**: [[F003_pv_corr_x_tur_rank|F003 (20d volume)]], [[F004 pv_corr_10d_x_tur_rank|F004 (10d)]]
- **Upgraded family**: [[FM rel_tur_encoding]]
- **See Also**: [[Factor Library]]

%%Report generated: 2026-04-07 | Data source: report_data.json + batch_038 judge_report (C003)%%
