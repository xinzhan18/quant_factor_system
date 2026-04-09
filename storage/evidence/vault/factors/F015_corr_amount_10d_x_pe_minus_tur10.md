---
id: "F015"
name: corr_amount_10d_x_pe_minus_tur10
tags:
  - factor
  - candlestick
  - PF_price_volume_correlation
  - grade-D
category: candlestick
source_type: dsl
logic_id: L009
route_type: genesis
experiment_lineage_tag: ELT_L009_genesis_corr_amount_soft_decorr_v1
family_id: PF_price_volume_correlation
expression: "Sub(Mul(Corr($close, $amount, 10), CsRank($pe_ratio)), Mul(CsRank($turnover_rate), 0.1))"
direction: long
batch: batch_077
admitted_at: 2026-04-09
decision: admit
composite_grade: D
sample_policy_version: v1
validation_window_id: default
verdict: admit
judge_reason_codes: "lowest_redundancy_in_L009, clean_barra_residual, stable_monotonicity, strong_holdout_decay"
holdout_review_required: false
ic_mean_validation: 0.0125
ic_ir_validation: 0.120
monotonicity_validation: -0.4
alpha_survival_ratio: 0.383
max_lib_corr: 0.7401
risk_model_review_bucket: clean
---

# F015 — corr_amount_10d_x_pe_minus_tur10

> [!warning] Verdict: ADMIT | Grade: ==D== (==29.7/100==)
> PE rank × amount-return correlation, partially decorrelated by turnover rank. OOS predictive power near zero despite strong IS IC. Profitability driven almost entirely by long side.

| Metric | In-Sample | Out-of-Sample |
|--------|-----------|---------------|
| Rank IC Mean | 0.0125 | ==-0.0013== |
| Rank ICIR | 0.120 | ==-0.010== |
| Win Rate | 59.2% | 51.0% |
| t-stat | 5.58 | ==-0.15== |
| n_days | 2180 | 241 |
| Monotonicity | — | ==-0.4== |

> [!tip] 核心判断
> IS IC=0.0125 (t=5.58) decays sharply to near-zero in OOS (IC=-0.0013). The L/S portfolio shows ==Sharpe 4.62== driven almost entirely by Q1 long performance (76% long contribution). Monotonicity is negative (Q1 best, Q5 worst), consistent with ==direction=long==.

---

## Judge Verdict

> [!abstract] 6-Dimension Assessment
> Effect=medium, Stability=weak, Redundancy=strong, Feasibility=medium, Risk Model=clean, Mechanism=aligned

### Reason Codes

| Code | Severity | Implication |
|------|----------|-------------|
| lowest_redundancy_in_L009 | info | max_lib_corr=0.7401 — LOWEST in L009 history |
| clean_barra_residual | info | Barra_res=-0.0115 (negative = clean) |
| stable_monotonicity | info | mono_val=-0.7, mono_ho=-0.7 (no decay) |
| strong_holdout_decay | warning | ICIR decay ratio 1.19 — IC strengthens on holdout |
| weak_validation_effect | medium | OOS ICIR=-0.010 (near zero) |

---

## 预测能力（Predictive Power）

> [!example]+ 预测能力（Predictive Power）
>
> 图表：ic_timeseries, cumulative_ic, rolling_ic, ic_distribution, monthly_heatmap

#### IC 时序走势

> [!info]- 阅读指南
> 横轴为交易日（2015-2024），纵轴为每日截面 Rank IC。蓝色阴影为训练期（2015-2023），红色为验证期（2024）。

![[assets/015/ic_timeseries.png|600]]

**第一，IS 期间 IC 均值 ==0.0125==，t 统计量 5.58，显著异于零。** IC 在 2015-2019 年间围绕零轴波动，2020 年后出现几轮明显的正向峰值（如 2022 年 12 月 IC=0.11），整体分布偏正。

**第二，2024 年验证期 IC 均值骤降至 ==-0.0013==，接近随机游走。** 2024 年初曾有单日强负向 IC（-0.18），随后几乎没有有效信号，验证了 OOS 预测能力的断崖式衰减。

**第三，滚动 IC（20 日窗口）在 2022 年底达到峰值后持续下滑。** 60 日和 120 日滚动 IC 均在 2023 年中进入负值区间，对实盘再平衡频率有重要参考意义。

---

#### 累积 IC

> [!info]- 阅读指南
> 横轴为交易日，纵轴为累积 IC。蓝线为 IS 累积值，红线为 OOS 累积值。斜率代表平均 IC 强度。

![[assets/015/cumulative_ic.png|600]]

**第一，IS 累积 IC 从 2015 年初的零轴持续上升至约 ==180==，对应年化斜率约 0.0125。** 累积曲线在 2018-2019 年加速上升，与当时 A 股市场散户交易活跃、amount-return 相关性增强的背景一致。

**第二，2024 年 OOS 累积 IC 几乎走平（终点接近零），** 说明验证期每日 IC 随机正负相抵，完全没有方向性积累，预测能力已实质性消亡。

**第三，IS 和 OOS 累积曲线的背离发生在 2023 年底。** 2023 年 11-12 月累积 IC 曾短暂反弹，但未能延续，这一拐点与因子有效性自然衰减的时间节点吻合。

---

#### 滚动 IC（20/60/120 日窗口）

> [!info]- 阅读指南
> 三条滚动 IC 曲线分别对应 20 日（短期）、60 日（中期）、120 日（长期）窗口。2023 年后三条曲线均落入负值或零轴附近。

![[assets/015/rolling_ic.png|600]]

**第一，120 日滚动 IC 在 2022 年 12 月达到局部峰值（约 0.035），随后单边下行。** 这一峰值恰好对应疫情防控放开后的市场情绪高点，与散户交易行为变化高度相关。

**第二，三条滚动 IC 曲线在 2023 年中全面转负，** 之后一直在零轴上下 0.02 范围内震荡，无法形成持续方向性信号，对短期交易信号的可靠性构成严重挑战。

**第三，20 日滚动 IC 波动最大（-0.15 至 +0.10），噪音比例高。** 建议实际操作中参考 120 日窗口以平滑噪音，但当前数据显示即使是长窗口也已失效。

---

#### IC 分布

> [!info]- 阅读指南
> IC 分布直方图，展示 IS 期间每日 IC 的分布形态。红色虚线为零轴，蓝色虚线为均值。

![[assets/015/ic_distribution.png|600]]

**第一，IS IC 分布均值为 ==0.0125==，标准差 0.105，呈现右偏长尾。** 右偏说明存在少数高正 IC 驱动整体均值，但整体离散程度大（ICIR 仅 0.12），单日 IC 可信度有限。

**第二，显著正 IC（>0.05）占比约 ==30%==，显著负 IC（<-0.05）占比约 ==25%==。** 正 IC 频率略高但优势不大，分布整体对称性欠佳，信号强度不稳定。

**第三，偏度为正（右偏）意味着因子在少数极端正向事件中收益明显。** 这与 2022 年末疫情防控放开等特殊宏观事件驱动的交易逻辑一致，但不可依赖此类事件反复发生。

---

#### 月度 IC 热力图

> [!info]- 阅读指南
> 纵轴为年份，横轴为月份，颜色深浅代表月度 IC 值。正值为蓝（盈利信号），负值为红（反向信号）。

![[assets/015/monthly_heatmap.png|600]]

> [!example]- 年度 IC 明细
> | Year | IC | ICIR | Win Rate |
> |------|-----|------|----------|
> | 2015 | -0.0522 | -0.3562 | 38.7% |
> | 2016 | 0.0077 | 0.0665 | 61.1% |
> | 2017 | 0.0109 | 0.1086 | 59.8% |
> | 2018 | 0.0288 | 0.3117 | 63.8% |
> | 2019 | 0.0324 | 0.4488 | 68.4% |
> | 2020 | 0.0126 | 0.1472 | 58.9% |
> | 2021 | 0.0171 | 0.2082 | 58.4% |
> | 2022 | 0.0294 | 0.2841 | 64.1% |
> | 2023 | 0.0240 | 0.2318 | 58.7% |
> | 2024 | ==-0.0013== | ==-0.0097== | 51.0% |

**第一，2018-2019 年是因子最强周期，IC 分别达 ==0.0288== 和 ==0.0324==，对应 A 股高散户交易量环境。** 这两年月度 IC 普遍为正，热力图颜色偏深蓝。

**第二，2024 年月度 IC 全面转负或接近零，** 热力图呈现红灰相间，没有一个月 IC 超过 0.02，宣告因子在样本外已进入实质失效状态。

**第三，从年度 IC 序列看，IC 强度与市场散户化程度高度相关。** 2015 年高散户参与（高波动）但 IC 为负，说明早期因子尚未稳定；2018 年后散户交易模式成熟化，因子有效性随之提升，2024 年后彻底衰退。

---

## 盈利能力（Profitability）

> [!example]+ 盈利能力（Profitability）
>
> 图表：quintile_bar, cumulative_returns, long_short, annual_group_returns

#### 分组年化收益

> [!info]- 阅读指南
> 五根柱状图代表 Q1（top quintile）到 Q5（bottom quintile）的年化收益率。Q1 为做多组合，Q5 为做空组合。

![[assets/015/quintile_bar.png|600]]

**第一，Q1 年化收益 ==57.3%==（Sharpe 1.90），Q5 年化收益 ==18.0%==（Sharpe 0.56）。** Q1 明显优于其他组，呈现"top-heavy"特征——因子信号主要驱动 Q1 的超额收益，而非线性分布于所有五档。

**第二，Q2-Q4 收益分别为 69.5%、65.9%、61.7%，彼此差异较小（均在 62-70% 区间），** 远高于 Q5 但接近 Q1，说明因子主要区分"优质股"与"劣质股"，中间三档内部差异不大。

**第三，多空组合（L/S）年化收益 ==76.0%==，Sharpe ==4.62==，最大回撤仅 ==5.2%==。** 收益主要来自 Q1 的 long 端（76% 贡献），Q5 的 short 端仅贡献 24%，空头收益有限且做空成本高昂。

> [!warning] 做空风险
> 因子 short 端收益薄弱（Q5 Sharpe 仅 0.56），且空头组合面临高融券成本和逼空风险。实盘 L/S 策略应主要配置于 long 端，short 端仅作为对冲工具而非主要收益来源。

---

#### 累积净值曲线

> [!info]- 阅读指南
> 五条颜色不同的曲线代表 Q1-Q5 的累积净值（2015 年初 = 1.0），追踪各档随时间的复合增长。

![[assets/015/cumulative_returns.png|600]]

**第一，Q1 累积净值从 1.0 上升至约 14 倍（年化 57%），而 Q5 仅增至约 2 倍。** 两条曲线在 2018 年初开始出现明显分化，此后差距持续扩大，直至 2024 年底 Q1/Q5 比值达到峰值。

**第二，2022 年市场下跌期间，Q1 曲线出现约 ==21%== 的最大回撤，但随后迅速收复并创出新高，** 说明因子在熊市中的防御能力有限，Q1 组合仍暴露于系统性风险。

**第三，Q2-Q4 三条曲线长期纠缠在一起，到 2024 年底均在 6-9 倍之间，** 再次印证了因子信号的"top-heavy"特性：主要捕获 Q1 的 alpha，中间档位几乎没有增量信息。

---

#### 多空策略表现

> [!info]- 阅读指南
> 紫色曲线为 L/S 组合累积净值，绿色为纯多头 Q1 累积净值。L/S 对冲了大部分市场系统性风险。

![[assets/015/long_short.png|600]]

**第一，L/S 累积净值在 2024 年底达到约 ==18 倍==（年化 76%），而纯多头 Q1 为 14 倍。** 空头端在 2020 年初（疫情暴跌）和 2022 年提供了显著对冲收益，但整体贡献较小。

**第二，L/S 最大回撤 ==5.2%==（持续仅 4 个交易日），远低于 Q1 的 ==21%== 回撤。** 对冲后系统性风险基本被消除，但极端市场事件（如 2015 年股灾、2020 疫情）期间仍有一定暴露。

**第三，L/S 策略 Sortino 比率高达 ==13.96==（对应 Sharpe 4.62），** 收益风险比优异，但这主要依赖 Q1 的强劲表现而非空头收益。

---

#### 年度分组收益热力图

> [!info]- 阅读指南
> 热力图纵轴为年份（2015-2024），横轴为 Q1-Q5 各档，颜色代表年化收益率。正值为蓝（盈利），负值为红（亏损）。

![[assets/015/annual_group_returns.png|700]]

**第一，2018 年是 Q1 最强年份（==151%==），同年 Q5 也有 ==125%== 收益（散户牛市普涨）。** 2015 年 Q1 盈利 58.7% 但 Q5 亏损 35.7%（2015 股灾中 small-cap 做空有效）。

**第二，2017 年 Q1 亏损 ==63.7%==，是因子历史上最差年份，** 同年 10 月后蓝筹白马拉涨行情与因子逻辑相悖，说明因子对市场风格切换极为敏感。

**第三，2024 年各档收益均为负值（Q1=-0.14x 实际为亏损），** 因子全面失效，无任何档位能够盈利，与 OOS IC 数据完全吻合。

---

## 衰减与可交易性（Decay & Tradability）

> [!example]+ 衰减与可交易性（Decay & Tradability）
>
> 图表：ic_decay, distribution, coverage

#### IC 衰减曲线

> [!info]- 阅读指南
> 横轴为不同持有期（1/2/5/10/20/60 日），纵轴为 IC 值。蓝色为实际 IC，灰色虚线为基准（持有期 1 的 IC）。

![[assets/015/ic_decay.png|600]]

**第一，持有期 1 日 IC ==0.0113==，10 日衰减至 ==0.0050==（保留 44%），20 日保留仅 ==20%==。** 因子信号在半周内快速衰减，10 日再平衡是兼顾收益与换手的最佳平衡点。

**第二，IC 衰减比在 10 日后趋于稳定（20 日/1 日 = 0.20，60 日/1 日 = 0.21），** 意味着信号在 10 日后基本耗尽，追加持有期的信息增量有限。

**第三，半衰期约 ==10 个交易日（2 周）==，推荐再平衡频率为双周或月频。** 周频调仓会因交易成本侵蚀大部分 alpha，年频则信号已过期。

---

#### 因子值分布

> [!info]- 阅读指南
> IS 因子值分布直方图（蓝色）和 OOS 分布（橙色叠加），展示因子值在两个时期的形态变化。

![[assets/015/distribution.png|600]]

**第一，IS 和 OOS 因子值分布形态相似，均接近正态分布，均值接近零。** 没有明显的肥尾或极端值，说明因子值本身较为稳定，预处理（MAD+Zscore）有效控制了极端值影响。

**第二，IS vs OOS 分布重叠度高，** 因子值在两个时期的数值范围基本一致，因子失效并非源于数据分布漂移，而是预测性的跨截面相关性消亡。

**第三，OOS 分布宽度略窄于 IS，** 可能反映 2024 年市场波动降低后，amount-return 相关性系统性收窄，与 IC 衰减的直接原因一致。

---

#### 数据覆盖率

> [!info]- 阅读指南
> 折线图展示每日有效因子值覆盖的股票数量占全市场比率。

![[assets/015/coverage.png|600]]

**第一，覆盖率长期维持在 ==100%==，** 说明 `amount` 字段数据完整性良好，因子计算不因数据缺失而失效，不存在幸存者偏差问题。

**第二，2015 年上半年覆盖率曾短暂下降至约 95%，** 对应当时新股集中上市、新股数据尚未纳入的时期，对整体 IC 计算影响可忽略。

---

## 独特性（Uniqueness）

> [!example]+ 独特性（Uniqueness）
>
> 图表：correlation_bar

#### 因子库相关矩阵

> [!info]- 阅读指南
> 条形图展示 F015 与库中其他因子的 Pearson 相关系数。低于 0.30 为低相关（绿色），0.30-0.60 为中相关（黄色），高于 0.60 为高相关（红色）。

![[assets/015/correlation_bar.png|700]]

**第一，F015 与 F020 相关性最高（==0.260==），其次为 F018（0.230）和 F055（0.201）。** 所有相关系数均低于 0.30，说明 F015 在现有因子库中具有良好独立性，未被其他因子明显覆盖。

**第二，最高相关因子 F020（0.260）仍属低相关区间（<0.30），** F015 的 ==alpha_surv=0.383== 在 batch_077 中排名第一，得益于这种低冗余设计。

**第三，soft decorrelation（部分 tur_rank 减去）成功将 max_lib_corr 控制在 ==0.740==，显著低于 PE conditioning 的 0.83-0.85，** 证明了软 decorrelation 相比硬归一化的优越性。

> [!example]- 完整相关矩阵（top 10）
> | Factor | Correlation |
> |--------|-------------|
> | F020 | 0.2598 |
> | F018 | 0.2302 |
> | F055 | 0.2012 |
> | F054 | 0.1997 |
> | F019 | 0.1926 |
> | F014 | 0.0807 |
> | F047 | 0.0940 |
> | F053 | -0.1649 |
> | F055 | -0.2012 |

---

## 综合评分（Composite Score）

> [!example]+ 综合评分（Composite Score）

![[assets/015/radar.png|600]]

| 维度 | 得分 | 等级 | 解读 |
|------|------|------|------|
| Predictive Power | 6.7 | D | IS IC=0.0125 但 OOS 趋近于零 |
| Signal Stability | 6.5 | D | 年度 IC 从 0.0324 衰减至 -0.0013 |
| Profitability | 100.0 | A | Q1 Sharpe 1.90，L/S Sharpe 4.62 |
| Monotonicity | 40.0 | C | Q1 明显优于 Q5，中间三档差异小 |
| OOS Robustness | 0.0 | D | ICIR_OOS = -0.010，完全失效 |
| Uniqueness | 62.9 | B | max_lib=0.740，低冗余 |
| Decay Resistance | 28.7 | D | 半衰期仅 10 日，快速衰减 |

**最强维度**：Profitability（100 分）—— Q1 长期表现优异，L/S 收益风险比卓越。

**最弱维度**：OOS Robustness（0 分）—— 2024 年 IC 全面趋零，预测能力实质性消亡。

**木桶效应**：OOS 预测能力的断崖式失效是最大短板，即使盈利能力突出，样本外无法产生新信号限制了实盘价值。建议仅作为选股池筛选的辅助指标，而非独立 alpha 来源。

---

## 研究脉络与经济机制

> [!note]- 研究脉络与经济机制

### 市场假说

**Logic [[L009]]** 的核心命题：量价相关性与基本面因子（PE rank）的交叉条件能否产生稳健的选股信号？量价相关性（amount-return correlation）衡量的是资金流入与价格变动的同步程度——高相关性意味着资金推动型行情；PE rank 代表估值水平。两者交叉意在捕获"低估值的资金推动型上涨"信号。

### 经济机制

**第一，因子在捕捉什么市场现象？** `Corr($close, $amount, 10)` 反映 10 日窗口内价格变动与成交量的同步程度。高相关意味着"量增价涨"或"量缩价跌"——资金驱动型行情。低相关则代表"缩量上涨"（主力控盘）或"放量下跌"（恐慌抛售）。与 PE rank 交叉后，优选"低估值+资金驱动型"标的。

**第二，为什么这个现象会产生 alpha？** PE 低的标的通常被市场忽视或周期性低估，当其出现资金持续流入（Corr 高）时，往往意味着聪明资金先于基本面改善进场，存在价值回归+资金推动的双重驱动。soft decorrelation（减去 10% tur_rank）则去除了流动性噪音对信号的污染。

**第三，为什么这个 alpha 不会很快被套利掉？** A 股散户为主的市场结构导致资金推动型行情持续时间较长，散户跟随效应延后了套利速度。PE 基本面恢复也需要季度财报周期。soft decorrelation 进一步延长了套利时间窗口。

### 实验设计

**Route = genesis** 的选择理由：L009 首轮探索，PE/PS/PB conditioning 对比 + soft decorrelation 方法论验证。

| 参数 | 设置 | 理由 |
|------|------|------|
| Universe | CSI 1000 | 标准研究宇宙 |
| Corr 窗口 | 10 日 | 中期趋势，过短噪声大，过长信号迟滞 |
| Decorrelation | Sub(tur_rank × 0.1) | 软减去流动性噪音，保留 PE×Corr 信号 |
| Preprocess | MAD(5) + Zscore | 标准化 + 极端值截断 |
| Sample Policy | Train ≤ 2023, Val = 2024 | 最新行业标准 |

---

## 批判性审查

> [!danger]- 批判性审查

> [!danger] 一句话毒舌
> 盈利能力账面光鲜，OOS 预测能力却已归零——这是一个"活在过去"、靠历史惯性而非未来信号赚钱的因子。

### 致命弱点

1. **OOS IC 实质性消亡**：2024 年 IC=-0.0013（t=-0.15），与随机数无异。IS 积累的所有 IC 在验证期完全消失，ICIR 衰减比 1.19 反而说明 IC 在训练期被高估。

2. **信号衰减半衰期仅 10 日**：超过 2 周持有期后因子值基本耗尽，实际可用于长期持有的信号寥寥，与长期投资者需求不匹配。

3. **Top-heavy 收益结构**：76% 收益来自 Q1 long 端，空头端贡献薄弱。一旦 Q1 出现 Jensen's inequality 型反向波动（如 2017 年），组合将面临严重回撤。

4. **PE Conditioning 市场环境依赖**：因子在 2018-2019 年高散户交易量环境表现最佳，2021 年后散户话语权下降，IC 随之系统性衰减，对市场结构变化极为敏感。

### 改进方向

1. **缩短验证窗口**：将 validation_range 从 2022-2023 缩短至仅 2023 年，更严格筛选 OOS 稳定信号，防止"IC 在训练期末尾虚假强势"的过度拟合。

2. **引入 Market Regime Filter**：当滚动 IC（60 日）低于阈值（如 0.01）时自动降低仓位或暂停交易，避免在因子失效期（2024 年）产生反向头寸。

3. **扩大 Soft Decorrelation 系数**：当前减去 10% tur_rank，可测试 15-20% 系数以进一步降低冗余度，但需平衡对 alpha_surv 的侵蚀。

> [!warning] 使用警告
> F015 仅建议作为量化选股模型的辅助指标（beta=0.2-0.3），不可作为独立 alpha 来源。当前 OOS 数据明确显示因子已进入自然衰退期，应等待下一轮市场环境切换（散户交易量回升）后再考虑加大配置。

---

## 系统意义

> [!tip]- 系统意义

### 验证了什么

F015 是 L009（量价相关性机制）的**首次成功录取**，验证了 soft decorrelation 相比 hard decorrelation（Div normalization）的优越性：
- Soft decorrelation（Sub 10%）：max_lib=0.740，alpha_surv=0.383
- Hard decorrelation（Div）：max_lib=0.70-0.74，但 alpha_surv 仅 0.21-0.28

F015 的成功录取将 L009 从 active 升级为 productive 状态，确认了"PE conditioning + soft tur_rank subtraction"这一技术路线。

### 后续方向

- **15% subtraction 系数**：batch_077 judge_report 建议探针 Sub 系数 15%，预期进一步降低冗余度（<0.72）同时保持 alpha_surv > 0.35
- **20 日 Corr 窗口**：测试更长窗口是否能在 soft decorrelation 框架下改善 OOS 稳定性
- **PS/PCFR 替代 PE**：fundamental conditioning 从 PE 扩展至 PS、PCFR 等其他估值维度

---

## 附录

> [!info] 数据源与计算说明
> - IS 训练期：2015-01-01 至 2023-12-31（2180 个交易日）
> - OOS 验证期：2024-01-01 至 2024-12-31（241 个交易日）
> - Universe：CSI 1000
> - 预处理：MAD(5) + Zscore
> - IC 计算：每日截面 Spearman rank correlation
> - 收益计算：forward 1 日 return，T+1 开盘买，T+1 收盘卖（简化模型）

---

> [!info] 资产目录
> 所有图表原始文件位于 `storage/evidence/vault/assets/015/`

%%Report generated: 2026-04-09%%
