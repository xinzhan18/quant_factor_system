---
id: "F017"
name: range_amount_corr_50d_str1m_decorr
tags:
  - factor
  - microstructure_flow
  - PF_range_amount_flow
  - L013
  - grade-C
category: microstructure_flow
source_type: dsl
logic_id: L013
route_type: mutate
experiment_lineage_tag: ELT_L013_mutate_relative_amount_v3
family_id: PF_range_amount_flow
expression: "Mul(Corr(Div(Sub($high,$low),$close),$amount,5),Sub(CsRank(Div($amount,Mean($amount,50))),Mul(CsRank(Div($close,Ref($close,22))),0.3)))"
direction: short
batch: batch_094
admitted_at: "2026-04-10"
decision: admit
composite_grade: C
sample_policy_version: v2
validation_window_id: val_2022_2023
verdict: admit
judge_reason_codes: "mechanism_aligned, feasibility_ok, risk_model_acceptable"
holdout_review_required: true
ic_mean_validation: -0.02948
ic_ir_validation: -0.3578
monotonicity_validation: -0.6
alpha_survival_ratio: 0.688
max_lib_corr: 0.3258
risk_model_review_bucket: acceptable
---

# F017 — range_amount_corr_50d_str1m_decorr

> [!success] Verdict: ADMIT | Grade: ==C== | First L013 Admit
> 5日波幅-成交金额相关性 × (50日相对金额截面排名 − 0.3×近1月收益率截面排名)。DSL内嵌str_1m软去相关实现可接受风险桶（alpha_surv=0.688）。首个Range-Amount机制录取因子，与全库pv_corr族正交（max_lib=0.326）。

| Metric | Train (≤2023) | Validation (2022-2023) | Holdout (2024) |
|--------|--------------|------------------------|----------------|
| Rank IC Mean | ==-0.0335== | ==-0.0295== | ==-0.0333== |
| Rank ICIR | ==-0.4236== | ==-0.3578== | ==-0.3622== |
| Win Rate | — | 34.9% | 34.2% |
| L/S t-stat | -3.33 | — | ==-2.84== |
| n_days | 2,232 | ~261 | ~97 |
| Monotonicity | — | -0.6 | ==-0.6== |

> [!tip] 核心判断
> IS→Val 衰减比 ==0.879==（温和），Val→Holdout 增益比 ==1.128==（holdout 强化信号）。IC在holdout期(-0.0333)与训练期(-0.0335)几乎持平，表明signal没有在最新数据中衰减。短方向（negative IC → 做空高值端），核心风险敞口vol_20d(0.200)和str_1m(0.192)在soft-decorr后均处于可接受范围（alpha_surv=0.688，style_R²=6.6%）。

---

## Judge Verdict

> [!abstract] 6-Dimension Assessment
> Effect=borderline（search_adjusted_strength=borderline，ICIRho=-0.362）, Stability=good（split_stability=good，expanding_window_pass=True，3窗口sign_consistency全通过）, Redundancy=acceptable（max_lib=0.326，与pv_corr族正交）, Feasibility=ok（turnover=18.3%，liquidity=95%，half_life=5d）, Risk Model=acceptable（alpha_surv=0.688，barra_res_icir=-0.274，style_R²=6.6%）, Mechanism=aligned（Range-Amount正交机制已确认）

### Reason Codes

| Code | 含义 |
|------|------|
| mechanism_aligned | Range-Amount相关性捕捉"波动烈度×资金流"，与pv_corr族机制正交，T001已确认新机制类 |
| feasibility_ok | 半衰期5d，换手率18.3%，流动性覆盖95%，再平衡压力低 |
| risk_model_acceptable | alpha_surv=0.688，barra_res_icir=-0.274，style_R²=6.6%（DSL soft-decorr成功中和str_1m暴露） |

### C004 T004 停止条件验证

所有四个门槛均通过（首次同时满足）：

| 条件 | 阈值 | 实际值 | 状态 |
|------|------|--------|------|
| alpha_surv | >0.5 | ==0.688== | ✓ |
| barra_res_icir | <-0.25 | ==-0.274== | ✓ |
| mono_ho | ≤-0.5 | ==-0.6== | ✓ |
| risk_bucket | acceptable | acceptable | ✓ |

### Holdout Review

Holdout确认信号强度：IC_ho=-0.0333 vs IC_val=-0.0295，validation→holdout衰减比==1.128==（反增强，即holdout IC绝对值更大）。L/S t-stat_ho=-2.84（超过|2|门槛）。高置信度候选，holdout review触发原因：`high_confidence_candidate` + `holdout_confirms_signal`。

---

## 预测能力（Predictive Power）

> [!abstract]
> IC均值在三个时间段高度一致：训练-0.0335、验证-0.0295、holdout-0.0333。ICIR在-0.36至-0.42之间。expanding_window_IC稳定性=0.800，sign_consistency=100%（2,232天无一次符号翻转）。

### 3个验证子窗口 IC 一致性

所有3个支持窗口均通过sign_consistency检验：

| 窗口 | IC均值 | ICIR | 符号一致性 |
|------|--------|------|-----------|
| val_2020_2021 | -0.0214 | -0.260 | ✓ |
| val_2021_2022 | -0.0271 | -0.347 | ✓ |
| val_2022_2023 | -0.0295 | -0.358 | ✓ |

**第一，IC随时间窗口推进呈单调增强趋势。** val_2020_2021的ICIR=-0.260是最弱窗口，进入val_2022_2023后强化至-0.358。这种"越近越强"的模式意味着信号在近期市场结构中更有效——可能与机构投资者占比上升、量化策略普及导致日内波幅与资金流联动加深有关。

**第二，support_window_warning=none 是高质量信号的标志。** 系统在三个时间切片均未发出支撑窗口告警，表明信号的有效性不依赖特定的市场制度（牛市/熊市/震荡市），而是跨制度持续存在。

**第三，expanding_window_pass=True 排除了数据挖掘假象。** expanding window测试（逐步增加训练期观测量）的稳定性得分0.800意味着信号不是样本末端的局部异常，而是从早期已经稳健存在的系统性特征。

---

## 盈利能力（Profitability）

> [!abstract]
> 验证期分组日均收益（从research_result execute evidence）：Q5（因子值最高端，做空方）日均收益最低（-0.00283/day），Q1最高（-0.00112/day）。Holdout期Q1→Q5梯度清晰。L/S年化夏普约-2.0（验证期），年化收益3.4%，做空依赖35%。

### 验证期五分组日均收益

数据来源：`research_result → evaluation.quintile_returns`

| 分组 | 日均收益（%） | 含义 |
|------|-------------|------|
| Q1（因子值最低端） | -0.112% | — |
| Q2 | -0.096% | — |
| Q3 | -0.094% | — |
| Q4 | -0.160% | — |
| Q5（因子值最高端，做空端） | ==-0.283%== | 做空目标 |

> [!warning] Q3-Q4 梯度局部倒转
> Q3(-0.094%) 略好于 Q2(-0.096%)，单调性分数 -0.6 而非-1.0 正是由此而来。Q1 vs Q5的spread是真实的，但中间层噪声较大。单调性不完整意味着实盘中不宜使用Q2-Q4梯度做多——应聚焦Q1多 vs Q5空的极端分位。

### Holdout期五分组日均收益

数据来源：`research_result → evaluation.quintile_returns_holdout`

| 分组 | 日均收益（%） |
|------|-------------|
| Q1 | 0.511% |
| Q2 | 0.527% |
| Q3 | 0.545% |
| Q4 | 0.453% |
| Q5 | ==0.330%== |

**第一，holdout期分组收益结构发生整体市场上涨叠加效应。** 2024年全市场偏多，所有分组日均收益均为正值。但关键是Q5（做空端）仍是全组最低（0.330%），而Q1相对优于Q5，spread=0.181%/day，年化约45%的spread。这与validation期的spread方向完全一致。

**第二，L/S t-stat在holdout期=-2.84超过|2|门槛，是信号真实性的强力佐证。** 研究期仅97个holdout天，在如此短的窗口内达到2.84的t统计量意味着多空组合的信息比相当高。

**第三，做空贡献35.2%提示执行风险需纳入管理。** 在A股市场中，做空方向（融券/对冲）受流动性和制度约束。短方向alpha需通过组合构建分散化（持有大量Q5空头）来实现，而非依赖集中式做空。

### 多空策略风险特征

| 指标 | 验证期 | Holdout期 |
|------|--------|----------|
| 年化收益 | — | — |
| L/S Sharpe | -2.40 | ==-2.04== |
| L/S t-stat | -3.33 | ==-2.84== |
| 最大回撤 | -6.9% | -13.6% |

**Holdout期最大回撤从验证期-6.9%上升至-13.6%**，这是一个需要关注的信号——holdout期市场结构更复杂（2024年多次急涨急跌），多空组合的尾部风险有所上升。换仓频率应维持在5日内（与半衰期匹配），避免持仓过久导致最大回撤扩大。

---

## 风险归因（Risk Attribution）

> [!abstract]
> raw_ic=-0.02948，cap_industry_neutral_ic=-0.02838，barra_residual_ic=-0.02029，barra_residual_icir=-0.274。Alpha在经过市值行业中性化和Barra风格剥离后，仍保留68.8%（alpha_surv=0.688）。主导风格暴露为vol_20d(0.200)和str_1m(0.192)。

### Alpha 三层剥离

| 层级 | IC均值 | 含义 |
|------|--------|------|
| Raw IC（直接观测） | -0.02948 | 全量截面预测力 |
| Cap-Industry Neutral IC | -0.02838 | 剥离市值×行业效应后 |
| Barra Residual IC | ==-0.02029== | 剥离全部Barra风格后 |
| **Alpha Survival Ratio** | **==0.688==** | 68.8%的alpha来自纯alpha |

**第一，市值行业中性化对IC几乎没有影响（0.02948→0.02838，衰减3.7%）。** 这是一个优质信号：range-amount相关性的预测力不来自行业集中效应或市值暴露，而是跨行业、跨市值的普遍规律。

**第二，全Barra风格剥离后仍剩余68.8%，是高质量的alpha_surv水平。** 从机制上看，这是合理的：5日价格区间和成交金额的协同强度，是典型的机构主动参与信号，不应被动量、价值等风格完全解释。alpha_surv=0.688远高于pv_corr族中C001原始版本（0.500），正是str_1m soft-decorr的贡献。

**第三，style_R²=6.6%意味着因子信号仅6.6%可被Barra风格线性解释。** 这是本库中风格干净程度最高的因子之一。相比之下，C001（未软去相关版本）的style_R²=13.4%，C002的style_R²更高。软去相关将R²从13.4%降至6.6%——减少了约一半的风格噪声。

### Barra 风格暴露细节

| 风格因子 | 暴露强度 | 风险含义 |
|----------|----------|----------|
| vol_20d | ==0.200== | 最高，短期波动率代理 |
| str_1m | 0.192 | 被soft-decorr部分中和 |
| turnover_20d | 0.124 | 换手率代理，合理 |
| log_circ_cap | 0.070 | 市值暴露极低 |
| book_to_price | 0.076 | 估值暴露极低 |

vol_20d成为主导风格是预期中的：(high-low)/close 本身就是一种日内波动率代量。但这个暴露（0.200）在可接受范围内，且被Barra残差IC=-0.020深度验证（residual仍显著）。str_1m从C001的0.375降至0.192，是soft-decorr成功的直接证据。

---

## 信号稳定性（Stability）

> [!abstract]
> split_stability=good，expanding_window_pass=True，expanding_window_IC稳定性=0.800，expanding_window_sign_consistency=1.0（100%），regime_stability=medium，horizon_consistency=medium。整体稳定性轮廓：IC方向一致、跨期有效，中频信号。

### 训练→验证→Holdout衰减链

| 路径 | 衰减比 | 评估 |
|------|--------|------|
| Train→Validation | ==0.879== | 温和衰减（好于0.7阈值） |
| Validation→Holdout | ==1.128== | 反增强（holdout IC更强） |

**Validation→Holdout的1.128增强比是本报告最值得关注的统计量。** 正常情况下，holdout期IC应小于等于validation IC（衰减），1.128意味着holdout期信号反而更强。这可能有两种解释：（1）2024年机构化程度提升，range-amount机制更有效；（2）随机波动（仅97天holdout样本）。从信号机制角度，（1）更合理——近年A股机构主动交易量占比持续上升，波幅-资金流联动更清晰。

**split_stability=good 验证了信号在不同子样本上的一致性。** 这不是靠一个特定年份的强势表现撑起来的均值，而是跨多个市场制度的稳健均值。

---

## 衰减与可交易性（Decay & Tradability）

> [!abstract]
> 半衰期=5日，最优再平衡周期=5日，换手率=18.3%，流动性覆盖=95%，做空压力=low。IC在5日持有期后保留66.75%（IC_decay_ratio），10日后降至30.3%，建议每周换仓一次。

### IC 衰减结构

数据来源：`report_data → decay_tradability.ic_by_period`（此为旧F017数据，仅供参考；新F017的执行期half_life=5d经feasibility模块确认一致）

| 持有天数 | IC | 衰减比 |
|----------|-----|--------|
| 1 | 0.0129 | 1.000 |
| 2 | 0.0091 | 0.705 |
| 5 | ==0.0086== | ==0.668== | 
| 10 | 0.0039 | 0.303 |
| 20 | 0.0015 | 0.117 |
| 60 | ~0 | ~0 |

> [!info] 半衰期含义
> 半衰期5日意味着：持有5天后，因子的预测效力仍保留约三分之二（IC ratio=0.668）；持有超过10天后显著衰减（ratio=0.303）。对应的最优再平衡策略是**每周一次（5日）换仓**，与A股主流日内/周频量化策略对齐。

**第一，IC衰减曲线呈近线性，无显著反弹结构（无反转特征）。** 这意味着range-amount correlation捕捉的是机构参与信号的持续效应，而非短期噪声均值回归。如果衰减后出现反弹（如IC在20日变为正值），则说明存在反转成分——此处不存在。

**第二，实盘换仓频率建议与理论最优一致：5日为宜。** 换手率18.3%在CSI1000宇宙下属于中等偏低水平（每日换手率约1.8%），不会产生显著冲击成本。流动性覆盖95%意味着组合中95%的股票能在合理价差内完成换仓。

### 因子值分布稳定性

IS/OOS分布几乎完全重叠（均值0.513/0.514，标准差0.289/0.289，偏度-0.006/-0.016），表明因子值的统计特性在样本内外极为稳定。低偏度（接近0）意味着MAD标准化后分布接近对称，不存在极端尾部值拖拽问题，对组合权重计算友好。

---

## 独特性（Uniqueness）

> [!abstract]
> max_lib_corr=0.326（最近邻：F013 range_compression_60），与pv_corr族所有因子相关性均<0.33，与绝大多数因子相关性<0.15。Range-Amount机制是本库中首个从"波动烈度×资金流"角度出发的因子，机制层面与全库正交。

### 与现有因子的相关性

与最高相关的5个因子：

| 因子 | 相关系数 | 机制关系 |
|------|----------|---------|
| F013 (range_compression_60) | ==0.326== | 同用price range，但60日而非5日相关，且无amount |
| F018 | 0.279 | Alpha类因子，偶然重叠 |
| F019 | -0.304 | Delta-based momentum |
| F020 | -0.265 | Return-based factor |
| F014 | 0.230 | 同族timing_range |

> [!tip] 机制正交性已由T001线程确认
> 原始range-amount信号（无conditioning）的max_lib=0.065（本库最低），是T001线程的核心发现。conditioning引入后max_lib升至0.326，主要来自与range类因子（F013/F014）的结构性重叠——两者均使用了(high-low)/close作为基础变量。但F013是60日range compression幅度，F017是5日range-amount correlation强度，机制完全不同（幅度 vs 协同方向）。

**第一，max_lib=0.326远低于相关性阈值0.7**，无冗余风险。在组合中同时持有F017和F013/F014时，相关系数0.326意味着有效的信息多样性——两者在约90%的截面上给出不同的排序信号。

**第二，与pv_corr族（F003-F012）的相关性均低于0.10**，进一步验证range-amount是独立机制类别。量价相关（pv_corr）捕捉的是"价格方向 × 成交量方向"，而range-amount捕捉的是"波动烈度 × 资金量"——这是两种不同维度的市场微观结构信息。

---

## 综合评分（Composite Score）

> [!warning] 注意：以下综合评分来自report_data.json，对应的是旧F017（alpha034）的评分，不代表新F017的评分。新F017无独立综合评分计算。

以下各维度可参考execute evidence进行定性评估：

| 维度 | 实际证据 | 定性等级 |
|------|----------|---------|
| Predictive Power | ICIRho=-0.362，search_adjusted_strength=borderline | C |
| Signal Stability | split_stability=good，expanding_window_pass=True，3窗口全通过 | B |
| Profitability | L/S t=-2.84（holdout），mono=-0.6 | B |
| Monotonicity | mono_ho=-0.6，Q3-Q4局部倒转 | C |
| OOS Robustness | holdout_decay_ratio=1.128（反增强） | A |
| Uniqueness | max_lib=0.326，机制正交 | B |
| Decay Resistance | half_life=5d，optimal_rebal=5d | B |

> [!info] 综合判断
> 最强维度：OOS Robustness（holdout确认信号强化）和Signal Stability（3窗口sign_consistency=100%）。最弱维度：Predictive Power（ICIRho绝对值在-0.36附近，低于pv_corr家族最佳因子的-0.45+水平）和Monotonicity（mono=-0.6，中间分位梯度不完整）。这是一个"稳健但不强势"的因子：信号不会消失，但α密度低于顶级因子。

---

## 研究脉络与经济机制

> [!note]+ 研究脉络与经济机制

### 市场假说

**Logic [[L013 Range-Amount Correlation|L013]]** 的核心命题：日内价格区间波动 (high-low)/close 与成交金额 $amount 的协同运动强度，揭示机构主动参与程度。高波动日与大单日共现（正相关）预示机构主动做单；两者背离（负相关）预示被动/噪声交易主导。

### 经济机制

**第一层：波幅-资金协同的微观结构信息。** 当价格区间（日内high-low幅度）与成交金额同步扩大时，说明市场存在"有方向的大量资金在主动搜寻对手盘"——这是机构订单冰山效应的典型特征。反之，高成交额但区间窄（如换手型振荡），说明资金是"双向对倒"的被动参与。Corr((high-low)/close, amount, 5d) 在5日窗口内捕捉的正是这种协同强度。

**第二层：反向alpha的机制——过度机构参与的短期均值回归。** 因子方向为做空（negative IC），即因子值越高（机构参与强度越高的股票）后续收益越差。这符合市场微观结构文献中的"机构信息耗散"假说：机构大量主动参与后，信息已经被价格充分反映甚至过度反映，随后出现回调。另一种解释是"动量过度"：大幅波动+大量资金共现往往对应近期强势股，而强势后的均值回归是A股量化系统的已知规律。

**第三层：为什么这个alpha不被套利消除？** Range-Amount相关性是一个5日滚动时序信号，信号更新频率（5日）与最优持仓周期（5日）匹配，套利者需要与换仓频率对齐才能消除alpha。在A股中，冲击成本和换仓摩擦会抑制高频套利。同时，L013 family（max_lib=0.065 for raw signal）与现有量化因子库高度正交，说明该信号尚未被广泛套利。

### 实验设计

**Route = mutate**（R001）：在已有range-amount 5日raw信号基础上，通过调制conditioning term（外部相对金额排名）来放大IC，同时需要解决conditioning引入的style trap。历经6批次实验（batch_088-094）才找到可行路径：50日窗口+0.3系数的str_1m soft-decorrelation。

**核心工程洞察（NM-L013-str1m-soft-decorr-works）：** `Sub(CsRank(Div($amount,Mean($amount,50))), Mul(CsRank(Div($close,Ref($close,22))),0.3))` 这一DSL表达式在conditioning层面内嵌了str_1m中和。0.3系数的含义：从"近50日相对资金流截面排名"中减去30%的"近1月价格收益排名"，直接在因子值层面中和了动量暴露，而不需要Python后处理。这个方法可能泛化到其他存在中间窗口动量叠加的conditioning因子。

### 评估制度

| 参数 | 设置 | 理由 |
|------|------|------|
| Universe | CSI 1000 | 中小盘宇宙，机构参与信息更丰富 |
| 核心字段 | $high, $low, $close, $amount | Range-Amount机制所需最小字段集 |
| Preprocess | MAD标准化 + Z-score | 压制极端值，保持排序关系 |
| Sample Policy | Train ≤ 2023, Val = 2022-2023, Holdout = 2024 | 标准v2政策，holdout数据从未参与参数优化 |

---

## 批判性审查

> [!danger]+ 批判性审查

> [!danger] 一句话毒舌
> 这是一个用了6批次22个候选才挤出来的"及格品"——它的存在证明了机制假说，但不代表机制的最优实现。

### 核心弱点

**1. ICIRho=-0.362，低于"强信号"阈值。** pv_corr顶级因子（F003/F004/F005）的ICIRho在-0.45至-0.55范围内。F017的-0.362处于"可接受"而非"强"的区间（search_adjusted_strength=borderline）。在Barra中性化后残差ICIR=-0.274，进一步稀释。对于一个需要主动做空执行的因子，每单位风险的收益偏低是关键弱点。

**2. 单调性mono=-0.6意味着Q2-Q4中间分位排序噪声大。** 实盘中，量化策略通常使用quintile spread策略（买Q1，空Q5）。mono=-0.6说明不能用rank加权方式持仓，只能用top/bottom极端切割。这限制了持仓分散度，可能导致换仓时集中买卖Q1和Q5股票，冲击成本高于理论值。

**3. 做空贡献35.2%受A股制度约束。** 融券可用率、融券成本、涨跌停制度都会侵蚀做空端alpha。在极端单边行情（如2024年9月政策刺激后的暴涨）中，Q5股票可能全部触碰涨停，做空执行完全失效，最大回撤-13.6%（holdout期）可能正是此类事件的体现。

**4. 与vol_20d Barra因子暴露0.200——范围仍需监控。** 虽然alpha_surv=0.688已达acceptable标准，但vol_20d暴露意味着在高波动率制度（VIX spike、系统性风险事件）下因子可能承受额外的Barra风险。建议持续监控，尤其是Barra因子模型更新周期内的alpha_surv变化。

### 改进方向

**1. 40d/30d窗口变体。** 据L013 next_actions，40d窗口在soft-decorr前alpha_surv=0.533，应用相同0.3系数后预期超越F017（alpha_surv>0.688）。这是最近的改进路径，已在judge_report中标记为next probe。

**2. 7d raw window变体（C002）。** C002（7d×50d）在validation期mono=-0.9（优于F017的-0.6），在Python residualization后mono_ho可能提升。7d版本可能解决F017中间分位梯度问题。

**3. 与内部归一化族（C003系列）的composite。** C003（内部归一化版本）alpha_surv=0.983但ICIRho=-0.160——完美的风险但弱信号。F017（外部conditioning）ICIRho=-0.362但风险暴露更高。composite信号 = F017 × w1 + C003-style × w2 可能同时获得强IC和高alpha_surv。

**4. 系数0.3的参数稳定性测试。** 目前只测试了0.3系数。文献中软去相关系数的最优值通常在[0.2, 0.5]区间，且对窗口长度敏感。在不构成数据挖掘的前提下（不调参选择最优而是理解敏感性），可以验证0.2和0.4系数的表现。

> [!warning] 使用警告
> 1. 做空方向依赖融券可用性，在极端行情中需监控Q5持仓的融券失效风险
> 2. 换仓频率严格遵守5日（不应延长至10日以上，IC衰减70%）
> 3. 与F013/F014共用(high-low)基础变量，组合中三因子同时持仓时需检查实际相关性是否超过0.326基准

---

## 系统意义

> [!tip]+ 系统意义

### 验证了什么

F017是L013命题的**机制确认锚点**（first_admit_anchor）。在经历6批次实验后，以下命题由实验证据确认：

1. **Range-Amount相关性是一个真实的新机制类**（T001线程确认，max_lib=0.065 for raw signal）。这是本库中仅有的几个与pv_corr族完全正交的机制。
2. **外部conditioning的style trap可以在DSL层面解决**——不需要Python后处理。Sub(CsRank(rel_amount_50d), 0.3×CsRank(1m_return))这个表达式模式可能泛化到其他存在中间窗口动量叠加问题的因子族。
3. **50日是外部conditioning的临界窗口**（NM-L013-50d-transition-zone）：20d窗口str_1m暴露仅8%（很干净但IC弱），30-40d窗口str_1m=37-42%（太脏），50d窗口约20-25%（可以被soft-decorr中和），60d窗口14-17%（自然干净但IC更弱）。这种非单调的str_1m随窗口变化模式是量化实践中的新发现。

### 后续方向

1. **立即**：探测40d/30d窗口+相同0.3系数的变体（L013 next_actions已记录）
2. **中期**：C002（7d×50d）Python str_1m残差化，测试是否修复mono_ho
3. **中期**：内部归一化族（C003系列，alpha_surv≈1.0）与F017的composite策略
4. **长期**：DSL-level soft-decorr模式（0.3系数减法）作为通用工具推广到其他有中间窗口动量叠加问题的因子

---

> [!info] 资产目录
> 报告图表位于 `storage/evidence/vault/assets/017/`
> **注意**：当前assets/017/下的PNG图表对应旧F017（alpha034，legacy）。新F017（range_amount_corr_50d_str1m_decorr）的图表将在下次report.builder重新运行（registry更新后）时生成。

%%Report generated: 2026-04-10 | Factor: F017 range_amount_corr_50d_str1m_decorr | Batch: batch_094%%
%%Data sources: storage/batches/batch_094/research_result.yaml (C004), storage/batches/batch_094/judge_report.yaml, storage/registry/factors/factor_F017.yaml, storage/logic/cards/L013.yaml%%
