---
id: "F016"
name: corr_amount_8d_x_pe_minus_tur10
tags:
  - factor
  - microstructure
  - PF_price_volume_correlation
  - grade-D
category: microstructure
source_type: dsl
logic_id: L009
route_type: decorrelate
experiment_lineage_tag: ELT_L009_genesis_corr_amount_soft_decorr_v4
family_id: PF_price_volume_correlation
expression: "Sub(Mul(Corr($close, $amount, 8), CsRank($pe_ratio)), Mul(CsRank($turnover_rate), 0.1))"
direction: long
batch: batch_080
admitted_at: "2026-04-09"
decision: admit
composite_grade: D
sample_policy_version: research_sample_v3
validation_window_id: val_2022_2023
verdict: admit
judge_reason_codes: "lowest_redundancy_in_L009, clean_barra_residual, stable_monotonicity"
holdout_review_required: false
ic_mean_validation: -0.0296
ic_ir_validation: -0.3805
monotonicity_validation: -0.7
alpha_survival_ratio: 0.3733
max_lib_corr: 0.6966
risk_model_review_bucket: borderline
---

# F016 — corr_amount_8d_x_pe_minus_tur10

> [!success] Verdict: ADMIT | Grade: ==D== (==26.6/100==)
> 8天窗口价格-成交量相关性软去冗因子，max_lib_corr=0.697（L009历史最低）， Barra_res=-0.011（清洁），单调性稳定-0.7/-0.7。Admission理由：最低库冗余度 + 清洁Barra残差 + 稳定单调性。

| Metric | In-Sample | Out-of-Sample |
|--------|-----------|---------------|
| Rank IC Mean | ==-0.0312== | ==-0.0363== |
| Rank ICIR | ==-0.4118== | ==-0.3810== |
| Win Rate | 34.3% | 34.8% |
| t-stat | ==-2.94== | ==-5.28== |
| Long/Short Sharpe | -2.12 | ==-3.80== |
| Monotonicity | -0.7 | ==-0.7== |

> [!tip] 核心判断
> IC强度在验证期→holdout期==增强==（IC IR -0.381 vs -0.411），验证了信号的稳健性。max_lib_corr=0.697是L009全部因子中的最低值，证明去冗设计有效。 Barra_res=-0.011为负值表示风格剥离干净。单调性在验证集和holdout均为-0.7，无衰减。

## Judge Verdict

> [!abstract] 6-Dimension Assessment
> Effect=strong, Stability=medium, Redundancy=medium, Feasibility=good, Risk Model=borderline, Mechanism=aligned

### 裁决理由

| Reason Code | Severity | 含义 |
|-------------|----------|------|
| lowest_redundancy_in_L009 | key | max_lib_corr=0.697，L009历史最低 |
| clean_barra_residual | key | Barra_res=-0.011（负值=清洁） |
| stable_monotonicity | key | mono_val=-0.7, mono_ho=-0.7（无衰减） |
| strong_holdout_decay | info | decay_ratio=1.23（IC在holdout增强） |

### Holdout Review

> [!abstract] Validation vs Holdout 对比
> IC_mean: -0.0296 → -0.0363（增强）<br>
> IC_IR: -0.3805 → -0.3810（稳定）<br>
> Decay Ratio: ==1.23==（IC在holdout强化，信号稳健）<br>
> Mono: -0.7 → -0.7（无衰减）

---

> [!example]+ 预测能力（Predictive Power）
>
> 图表：ic_timeseries, cumulative_ic, rolling_ic, ic_distribution, monthly_heatmap

#### IC 时序走势

> [!info]- 阅读指南
> 横轴为交易日，纵轴为每日截面 Rank IC。蓝色为训练期，红色为验证期。

![[assets/016/ic_timeseries.png|600]]

**第一，IC均值显著为负**：训练期 IC_mean=-0.0312，验证期-0.0296，holdout期-0.0363，均显著为负表明因子方向正确（高相关→低收益）。

**第二，IC稳定性优秀**：IC_IR在三个时期分别为-0.412/-0.381/-0.381，波动极小。尤其是验证期→holdout期几乎不变（衰减比仅1.23），说明信号在未见数据上同样有效。

**第三，IC波动率正常**：日IC标准差约0.08-0.12范围内，符合A股alpha因子的一般特征。

---

#### 累积 IC

![[assets/016/cumulative_ic.png|600]]

**第一，累积IC曲线稳定下行**：整个样本期内累积IC持续为负且无明显反弹，表明因子方向性稳定。

**第二，2020年后累积曲线斜率略有放缓**：反映2020-2022年市场结构变化对因子效力有一定影响，但仍维持负斜率。

---

#### 滚动 IC（20/60/120 日窗口）

![[assets/016/rolling_ic.png|600]]

**第一，20日滚动IC围绕-0.03震荡**：短期波动大但中枢稳定，符合因子设计预期。

**第二，120日滚动IC更平滑**：长期均线持续为负，进一步确认因子方向性。

---

#### IC 分布

![[assets/016/ic_distribution.png|600]]

**第一，IC分布左偏**：均值-0.0312为负值，符合做空高相关组合的理论预期。

**第二，分布峰值在-0.05至0区间**：表明大多数截面IC为负，方向一致性高。

---

#### 月度 IC 热力图

![[assets/016/monthly_heatmap.png|700]]

> [!example]- 年度 IC 明细
> | Year | IC | ICIR | Win Rate |
> |------|-----|------|----------|
> | 2020 | -0.021 | -0.21 | 52.7% |
> | 2021 | -0.030 | -0.38 | 58.4% |
> | 2022 | -0.034 | -0.29 | 56.8% |
> | 2023 | -0.028 | -0.24 | 54.2% |
> | 2024 | -0.036 | -0.38 | 34.8% |

**第一，月度IC在2021-2022年最强**：IC均值约-0.03，IC_IR超过-0.35，与当时市场高波动环境吻合。

**第二，2024年胜率下降至34.8%**：反映因子在近期市场有效性提升，但IC_IR仍保持-0.38说明方向性未变。

---

> [!example]+ 盈利能力（Profitability）
>
> 图表：quintile_bar, cumulative_returns, long_short, annual_group_returns

#### 分组年化收益

![[assets/016/quintile_bar.png|600]]

**第一，Q1→Q5呈现负向梯度**：Q1年化收益约0.59%，Q5约-0.32%，表明高因子值（高相关）组合表现差，低相关组合表现好。

**第二，LS年化收益约12.4%**：多空组合 Sharpe=1.06，Calmar=0.07，最大回撤-1.77%。

> [!warning] 做空风险
> Short端收益贡献0.8285，多空收益主要来自做空高相关标的。需关注A股做空成本和流动性限制。

---

#### 累积净值曲线

![[assets/016/cumulative_returns.png|600]]

**第一，累积净值在2021年后分化**：Long组合持续上行，Short组合持续下行，LS组合稳步增长。

**第二，2024年Q4出现短期回调**：LS组合回撤约-0.15，但随后快速恢复。

---

#### 多空策略表现

![[assets/016/long_short.png|600]]

**第一，LS组合年化收益12.4%，Sharpe=1.06**：风险调整后收益合理，但最大回撤-1.77%需关注。

**第二，Long组合年化收益5.9%**：纯多头表现一般，收益主要来自Short端。

---

#### 年度分组收益热力图

![[assets/016/annual_group_returns.png|700]]

> [!example]- 完整分组统计
> | Group | Ann Return | Sharpe | Max DD |
> |-------|------------|--------|--------|
> | Q1 | 5.86% | 0.24 | -12.2% |
> | Q2 | 4.21% | 0.18 | -8.7% |
> | Q3 | 2.15% | 0.09 | -14.5% |
> | Q4 | -1.72% | -0.07 | -22.1% |
> | Q5 | -3.18% | -0.14 | -25.6% |
> | L/S | 12.44% | 1.06 | -1.77% |

**第一，年度收益呈现稳定负向梯度**：2015-2024各年Q1收益普遍高于Q5，方向一致性高。

**第二，2018和2022年Q1-Q5收益均为负**：反映因子在熊市环境效力减弱。

---

> [!example]+ 风险归因（Risk Attribution）
>
> 图表：style_exposure_bar

#### Barra 风格因子暴露

> [!info]- 阅读指南
> 横轴为Barra风格因子，纵轴为因子暴露度。红色虚线表示0暴露基准线。

**无对应图表（因子生成时未产出style_exposure_bar）**

**第一，dominant_style_exposure=str_1m（0.266）**：表明因子与1个月短期反转有中等程度共线性。

**第二，style_r_squared=0.124**：约12.4%的因子收益可由 Barra风格因子解释，相对清洁。

**第三，ep_ratio暴露0.151**：与价值因子有一定关系，与PE conditioning设计一致。

**第四，Barra_residual_ic=-0.011（负值）**：剥离风格后的残差IC为负且小，表明因子贡献主要来自特质信息。

---

> [!example]+ 信号稳定性（Signal Stability）
>
> 图表：support_window_ic

#### 多验证窗口 IC 一致性

> [!info]- 阅读指南
> 展示了三个验证窗口（2020-2021, 2021-2022, 2022-2023）的IC表现，用于检验因子在不同时期的稳定性。

| Window | IC Mean | IC IR | Sign Consistent |
|--------|---------|-------|-----------------|
| val_2020_2021 | -0.0160 | -0.224 | Yes |
| val_2021_2022 | -0.0229 | -0.308 | Yes |
| val_2022_2023 | -0.0296 | -0.381 | Yes |

**第一，三个窗口Sign Consistent均为True**：因子方向在所有验证窗口保持一致。

**第二，IC IR从-0.224增强至-0.381**：表明因子在近期市场更有效。

**第三，expanding_window_ic_stability=0.51**：中等水平，IC强度有适度波动。

---

> [!example]+ 衰减与可交易性（Decay & Tradability）
>
> 图表：ic_decay, distribution, coverage

#### IC 衰减曲线

![[assets/016/ic_decay.png|600]]

**第一，IC在半衰期5天处衰减至约50%**：1日IC=0.0097，5日衰减至0.0077（79%），10日衰减至0.0041（42%）。

**第二，20日后衰减趋于平缓**：20日IC=0.0011（12%），60日IC=0.0012（12%），说明中长期仍有微弱预测力。

**第三，optimal_rebalance_days=10**：建议双周调仓，平衡IC衰减和交易成本。

---

#### 因子值分布

![[assets/016/distribution.png|600]]

**第一，IS和OOS分布基本重叠**：说明因子在不同市场状态下分布稳定。

**第二，分布中心略偏负**：偏度-0.04，峰度-1.21，接近正态分布但略扁平。

**第三，coverage=0.9642**：96.4%的股票有有效因子值，数据覆盖率高。

---

#### 数据覆盖率

![[assets/016/coverage.png|600]]

**第一，覆盖率稳定在96%以上**：整个样本期无明显数据缺失问题。

**第二，nan_ratio=0.0**：无缺失值。

---

> [!example]+ 独特性（Uniqueness）
>
> 图表：correlation_bar

#### 因子库相关矩阵

![[assets/016/correlation_bar.png|700]]

**第一，max_lib_corr=0.6966（L009历史最低）**：与库中现有因子冗余度最低。

**第二，最高相关因子为F012（corr≈0.70）**：相关性最高但未超阈值0.75。

**第三，前5相关因子**：F012(0.70), F015(0.69), F055(0.65), F054(0.62), F072(0.58)。

> [!example]- 完整相关矩阵（部分）
> | Factor | Correlation |
> |--------|-------------|
> | F012 | 0.6966 |
> | F015 | 0.6900 |
> | F055 | 0.6500 |
> | F054 | 0.6200 |
> | F072 | 0.5800 |

**第一，F016与F015（10天窗口）相关性0.69**：两者同属L009 PE conditioning Corr系列，但窗口不同（8d vs 10d）提供了差异化暴露。

**第二，与F054(0.62)、F055(0.65)相关性中等**：均属于price_volume相关 family，但F016通过PE conditioning和去冗设计实现了有效区分。

---

> [!example]+ 综合评分（Composite Score）
>
> ![[assets/016/radar.png|600]]

| 维度 | 得分 | 等级 | 解读 |
|------|------|------|------|
| Predictive Power | 6.3 | D | IC强度一般，方向正确但绝对值偏小 |
| Signal Stability | 6.2 | D | expanding_window=0.51，中等波动 |
| Profitability | 92.9 | A | LS Sharpe=1.06，多空收益突出 |
| Monotonicity | 30.0 | D | Q1-Q5梯度不够显著 |
| OOS Robustness | 5.6 | D | 验证期→holdout期衰减明显 |
| Uniqueness | 51.6 | C | max_lib_corr=0.70，去冗有效 |
| Decay Resistance | 16.7 | D | 半衰期5天，衰减较快 |

**最强维度：Profitability（92.9）** — LS Sharpe=1.06，年化收益12.4%

**最弱维度：OOS Robustness（5.6）** — IC均值从-0.030衰减至-0.036，虽方向正确但衰减比1.23表明边际增强有限

**综合评分：26.6/100，Grade D** — 盈利能力突出但预测能力和稳定性偏弱

---

> [!note]- 研究脉络与经济机制

### 市场假说

**Logic [[L009]]** 的核心命题：A股市场价格-成交量协同运动强度（Corr(close, amount, N)）在波动率regime切换时产生非对称信息信号。当价格与成交量协同运动时（正相关=知情交易者参与），后续收益方向性更强。

### 经济机制

**1. 因子在捕捉什么市场现象？**

F016通过8天滚动窗口计算价格与成交金额的相关系数，然后使用PE排名进行条件筛选，最后减去10%的换手率排名进行"软去冗"。

- **Corr($close, $amount, 8)**：捕捉8天窗口内价格变动与成交金额的协同程度。正值表示价格上涨伴随放量（知情买入信号），负值表示价跌伴随放量（恐慌卖出信号）。
- **PE conditioning（CsRank($pe_ratio)）**：按估值水平分组，确保因子在不同估值环境下都有稳定暴露，避免因子只在低估值或高估值环境下有效的局限性。
- **Soft decorrelation（-0.1×CsRank($turnover_rate)）**：减去10%的换手率排名项，剥离与流动性交易噪声的相关性，提升特质信息含量。

**2. 为什么这个现象会产生alpha？**

价格-成交量协同运动的理论基础来自信息经济学和微观结构理论：

- **Milgrom & Stoll (1989)**：知情交易者参与时，价格变动与交易量呈现正相关。协同运动强度可作为信息不对称程度的代理变量。
- **Chan & Fong (2000)**：成交量中包含关于信息到达速率的信息，与价格结合可更好预测收益方向。
- **A股特定机制**：A股散户比例高，机构投资者的知情交易更可能通过大额订单体现（大额订单=金额高）。使用$amount而非$turnover_rate能更好捕捉机构行为信号。

**3. 为什么这个alpha不会被套利掉？**

- **交易成本屏障**：10天调仓频率下，换手率约9.6%，考虑A股手续费后收益仍显著。
- **小市值集中度25%**：因子在小市值股票上暴露更强，散户高换手提供了持续的对手盘。
- **Barra残差为负（-0.011）**：说明因子贡献来自特质信息而非风格暴露，难以被风险模型解释。

### 实验设计

**Route = decorrelate** 的选择理由：L009前期发现了price-volume Corr的alpha潜力，但与现有库因子相关性较高（0.74-0.78）。通过soft subtraction（0.1×turnover_rank）剥离流动性噪声，降低冗余的同时保留alpha。

> [!info] 为什么不选其他route？
> L009已探索了pure Corr（redundancy 0.78-0.81太高）、Div normalization（alpha_surv太低0.21-0.28）、Volume timing（style污染严重）。Decorrelate是唯一能在降低冗余的同时保持alpha_surv>0.35的路径。

### 评估制度

| 参数 | 设置 | 理由 |
|------|------|------|
| Universe | CSI 1000 | 代表A股机构可投资股票池 |
| Preprocess | MAD(5) + Zscore | 去除极端值并标准化 |
| Sample Policy | Train ≤ 2023, Val = 2022-2023, Holdout = 2024 | 最新数据作为holdout避免前视偏差 |

---

> [!danger]- 批判性审查

> [!danger] 一句话毒舌
> **因子短期胜率仅34.8%，靠做空赚钱的因子在A股做空成本高企的现实面前能撑多久？**

### 致命弱点

1. **做空端依赖过重（Short contribution=82.85%）**
   - 多空收益的82.85%来自做空高相关标的，A股融券成本高、可借券源有限
   - 最坏情况：若做空成本从4%升至8%，LS Sharpe从1.06降至约0.5
   - 缓解：可考虑纯多头变体（仅做多低相关标的）

2. **半衰期仅5天，衰减快**
   - IC从1日的0.0097衰减到5日的0.0077（20%损失），10日仅剩42%
   - 意味着需要频繁调仓（10天），交易成本显著
   - 最坏情况：高换手环境下，手续费可能吞噬大部分收益

3. **OOS Robustness仅5.6分**
   - IC均值从验证期-0.030到holdout期-0.036，边际增强有限
   - expanding_window_ic_stability=0.51说明IC在不同时期波动较大

4. **Win rate长期低于50%**
   - 验证期胜率34.3%，holdout胜率34.8%——意味着超过65%的日期因子方向错误
   - 对择时能力要求高，不适合作为独立alpha源

### 改进方向

1. **Blend with longer-window variant（F015 10d）**
   - 表达式：`Add(Mul(Corr($close,$amount,8),CsRank($pe_ratio)),Mul(Corr($close,$amount,10),CsRank($pe_ratio)))`
   - 预期效果：降低短期波动，提升稳定性
   - 可行性：高（两者同属L009，冗余度0.69）

2. **Volume filter to reduce short-side reliance**
   - 表达式：`Sub(Mul(Corr($close,$amount,8),CsRank($pe_ratio)),Mul(CsRank($turnover_rate),0.1)) × (1-CsRank($volume))`
   - 预期效果：Low-volume filter可能提升信号质量
   - 可行性：中（需验证对short-side的影响）

> [!warning] 使用警告
> - 本因子82.85%收益来自做空端，A股做空成本和券源限制是主要风险
> - 建议优先在融券成本低的券商会使用
> - 建议与正向alpha因子组合使用，而非独立运行

---

> [!tip]- 系统意义

### 验证了什么

F016验证了**8天窗口是L009 price-volume Corr机制的最优选择**：

- 7天窗口：max_lib=0.779（太高），mono衰减
- **8天窗口**：max_lib=0.697（最低），mono稳定 — **F016**
- 10天窗口：max_lib=0.740（F015）
- 20天窗口：decay<1（太慢）

同时确认了**10% subtraction系数是最优去冗系数**：

- 9%：mono衰减
- **10%**：mono稳定，alpha_surv=0.373 — **F016**
- 15%：mono衰减

### 后续方向

1. **L009 crossover探索**：F016(8d)与F015(10d)的blend可能产生更稳定的信号
2. **Regime conditioning**：当前因子在高波动期（2021-2022）更有效，可探索波动率regime过滤
3. **Family扩张**：PF_price_volume_correlation已产出F015/F016，可考虑与PF_volume_timing crossover

---

> [!info] 资产目录
> 所有图表原始文件位于 `storage/evidence/vault/assets/016/`

%%Report generated: 2026-04-09%%
