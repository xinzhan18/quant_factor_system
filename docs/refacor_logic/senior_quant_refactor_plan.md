# 资深量化视角下的研究系统重构方案

## 1. 文档目标

这份文档只讨论一件事：

> 如何把当前 `docs/refacor_logic/` 这套自动因子研究逻辑，重构成一套更成熟、更可复现、更不容易自我污染的研究系统。

这里明确不讨论：

- 生产交易
- 实盘执行
- 真实冲击成本建模
- 真实容量测算

原因不是这些不重要，而是它们不属于当前这套“因子挖掘研究系统”的主问题。

你现在要解决的是：

1. 如何避免研究过程污染自己的样本外
2. 如何让统计判断更严谨
3. 如何让 `judge` 变成可复现的制度，而不是叙事型裁判
4. 如何让当前研究系统既能做 exploitation，也保留少量 discovery 能力

---

## 1.1 当前版本的额外架构收口

在完成前面的制度修补后，当前还必须进一步做 6 个架构收口：

1. 把系统从“单速审批流”改成“双速回路”
2. 把 `logic` 收缩回 hypothesis 管理，而不是全能治理层
3. 把 `route` 从长期对象降级成 batch 内设计标签
4. 把 `family` 从硬前置依赖改成渐进式软标签
5. 把分级回写从 prompt 约束改成程序化 guard rail
6. 把 judge 的输入从十几个原始文件收缩成一个 `judge_packet`

这里的总原则是：

- 保留正式 admission 流程
- 释放会话内快速试错回路
- 压缩 LLM 直接面对的对象数量
- 把治理升级交给程序化 writer，而不是 LLM 自觉

### 双速回路

系统不再只有一条：

`logic -> idea -> execute -> judge -> memory`

而是明确拆成两条：

1. 快速研究回路  
   `working_theme -> expression draft -> quick execute -> quick feedback -> rerun`

2. 正式录取回路  
   `frozen candidate batch -> research_execute -> research_judge -> guarded writeback`

前者用于半小时内反复试错，后者只用于候选冻结后的正式 admission。

### 必须保留的骨架

以下部分仍然必须保留：

- `logic`：但只做 hypothesis registry / lifecycle / high-level budget intent
- `research_execute` 与 `research_judge` 分离
- `sample_policy` 与 `search_ledger`
- `family/subspace redundancy` 的思想
- 分级回写思想

### 明确降级的部分

以下部分不再作为重对象治理：

- 长期 `route cards`
- `route lifecycle` 持久化
- 把 `family_id` 作为所有流程的强前置门槛
- 让 `logic` 同时兼任 family taxonomy 管理员、cycle controller、scheduler、仲裁官

### 执行约束

正式 writeback 不允许由 LLM 直接修改治理文件。

必须通过统一的 `guarded writer`：

- 校验允许写哪些对象
- 校验二级升级条件是否满足
- 拒绝越权写入 `forbidden.yaml / implementation_policy.yaml / final logic status`

否则所谓“分级回写制度”只是文字制度，不是执行制度。

---

## 2. 当前系统的 8 个核心问题

这一节把现有文档里的关键问题直接写清楚。

### 问题 1：样本外会被反复消费，最后变成伪 OOS

当前设计里：

- `probe` 只使用训练期
- `execute` 又直接把 validation 证据用于正式裁决
- `judge` 还是长期 memory 的主更新器，会回写 registry、logic、route、forbidden、policy、state

这意味着：

- 同一段 OOS 会被多轮反复查看
- 每轮又会据此更新 `logic`、`forbidden`、`policy`
- 长期看，OOS 不再是验证集，而变成“元训练集”

这不是小问题，而是当前制度里最大的统计污染源。

### 问题 2：统计标准太经验化，缺少多重检验控制

当前设计里：

- `probe` 直接用经验阈值做 fail 规则
- route 选择主要靠线性加权打分
- 正式 hard gate 也是固定阈值

问题在于：

- 阈值没有和 universe 规模绑定
- 没有和 holding horizon 绑定
- 没有和横截面 breadth 绑定
- 没有和 regime 差异绑定
- 没有多重检验控制

也就是：

- 没有 expanding-window IC stability
- 没有 bootstrap 稳健性检验
- 没有多重检验风险记账
- 也没有任何适配连续搜索场景的强度修正代理

这里还要补一句边界说明：

- 当前系统不应把 `search_ledger.attempt_count` 误写成 independent trials
- 也不应把 `multiple_testing_risk_bucket` 误解释为严格的 Benjamini-Hochberg FDR
- `purged walk-forward` 只有在有效 split 数足够时才有参考意义

对当前 `2015` 起的日频样本，更应优先把 `expanding-window IC stability`、`split stability`、`regime stability` 做扎实。

这会系统性低估数据挖掘偏差。

### 问题 3：交易落地性只做了最浅的一层

当前 `execute` 对“可交易性”的定义，主要包括：

- universe mask
- suspend filter
- limit up/down filter
- invalid forward return mask
- delay 对齐
- horizon 对齐

指标层面主要保留了：

- `turnover`
- `coverage`
- `half_life`

这层不够的问题不是“没有做真实成本建模”。
那本来就不该在这里做。

真正的问题是：

- 没有明确定义研究阶段该做哪些“可实现性代理检查”
- 于是系统只能用 `turnover` 粗略表达交易难度

更合理的研究层代理应该至少包括：

- `liquidity_coverage_ratio`
- `tail_trade_concentration`
- `small_cap_concentration`
- `rebalance_stress_proxy`
- `holding_period_proxy`

这些不等于真实成本，但足以过滤明显不适合研究入库的信号。

### 问题 4：相似性和替换逻辑过于 pairwise

当前替换逻辑主要看：

- `max_lib_corr`
- `nearest_factor_id`
- `overlap_risk`
- 如果相似但更稳、更简单、turnover 更低，则考虑 replace

这只适合处理：

- 同构重复
- 窗口微调重复
- 表达式近重复

但对真正的 alpha library 来说，不够。

因为：

- 高相关不等于没有边际信息
- 低相关不等于有独立机制
- pairwise corr 不能替代子空间冗余判断

所以当前库管理容易出现两种偏差：

1. 错杀“相关但仍有边际贡献”的候选
2. 放过“相关不高但本质同一类风险暴露”的候选

### 问题 5：`judge` 是核心，但制度最不完整

现有文档里多次说：

- `judge` 决定录取什么
- `judge` 做 admit / reject / replace

但这个目录里并没有一份真正完整定义以下内容的 `judge` 协议：

- admit 的明确门槛
- replace 的明确门槛
- reject 的明确门槛
- near miss 的处理规则
- logic 降级规则
- route 停止规则
- forbidden 升级规则

`memory.md` 只写了它读什么、写什么。

这意味着：

- `execute` 的制度比 `judge` 完整
- 最关键的裁决层反而是半结构化的
- 系统长期会越来越依赖人工叙事

这是研究系统非常危险的状态。

### 问题 6：搜索过于偏 exploitation，discovery 空间太小

当前设计里：

- `idea` 不决定研究主题，只能消费 active logic contract
- 小库默认只开 1 个 logic
- 全局 route 不超过 3，总 candidate 不超过 6~8

这对控制搜索预算是有价值的。

但它的问题是：

- 太依赖已有 logic 是否立得对
- 太依赖早期 hypothesis 是否写得好
- 太容易形成路径依赖

系统会越来越擅长：

- 在既有叙事内精修

但越来越不擅长：

- 在临近区域发现新的机制切片

### 问题 7：风险模型视角前后不一致

`memory.md` 里已经出现：

- `style_barra/`
- `use_barra_view: true`

但 `execute` 的中性化设计仍停留在：

- `none`
- `market_cap`
- `industry`
- `both`

这会导致：

- memory 层假设研究会做更成熟的风格暴露分析
- execute 层实际只做了简化版中性化

对 A 股这种风格轮动强、Beta 结构复杂的市场，这个不一致会严重影响对“独立 alpha”的判断。

### 问题 8：文档边界混乱，研究制度和工程重构混写

旧的工程重构文档曾和研究制度文档混在同一目录里。

这说明当前目录里混了两类文档：

1. 研究制度文档
2. 代码架构文档

混写的坏处是：

- 研究规则改动和工程重构改动容易互相污染
- 同一个版本里既改评估口径又改代码分层
- 回头复盘时很难知道研究结果变化来自制度变了还是实现变了

---

## 3. 研究系统应重构成什么样

如果只站在“研究系统”角度，不引入生产层，那么建议重构成 5 段：

1. `logic`
2. `idea`
3. `execute_research`
4. `judge_research`
5. `memory`

关键不是名字，而是职责边界。

### 3.1 `logic`

负责：

- hypothesis proposal
- hypothesis review
- hypothesis scheduling
- hypothesis lifecycle

不负责：

- candidate 生成
- 因子录取
- 统计裁决

### 3.2 `idea`

负责：

- route planning
- probe form design
- candidate expansion

不负责：

- hypothesis 创建
- 正式研究录取
- 长期 policy 回写

### 3.3 `execute_research`

负责：

- 统一研究口径计算
- 统一 signal preprocess
- 统一 validation 证据生成
- 基础可实现性代理检查
- 相似性分析

不负责：

- 录取
- policy 升级
- logic 生命周期裁决

### 3.4 `judge_research`

负责：

- admit / reject / reserve / replace
- route 继续 / 暂停 / kill
- logic 升温 / 降级 / 饱和 / 停车
- 向 `memory` 回写结构化经验

### 3.5 `memory`

负责：

- research state
- logic cards
- route cards
- library registry
- forbidden patterns
- policy registry

---

## 4. 样本制度必须重构

这是最优先的部分。

### 4.1 不再使用单一 “train / OOS” 二分法

建议改成三层研究样本：

1. `train`
2. `validation`
3. `holdout`

定义如下：

### `train`

用途：

- `probe`
- route 粗筛
- 参数成形

允许高频查看。

### `validation`

用途：

- `execute_research`
- `judge_research`

它是研究录取的正式依据。

可以被多轮使用，但必须满足两个约束：

1. 每次使用必须记录到 batch history
2. 不能在同一轮里反复基于 validation 结果继续调 route 细节

### `holdout`

用途：

- 低频审查
- 只用于重要晋升、重要复核、阶段性 sanity check

约束：

- 不能进入日常 batch 循环
- 不能作为 route 调参反馈源
- 不能直接写入 forbidden/policy

### 4.2 `judge` 的回写必须分级

这一步很关键。

建议把 `judge_research` 的回写拆成两类：

#### 一级回写：允许来自 validation

可以写：

- route status
- candidate status
- admit/reject 记录
- logic 活跃度更新

#### 二级回写：禁止仅凭 validation 直接升级

不能直接改：

- forbidden 核心规则
- 全局 implementation policy
- 全局 hypothesis doctrine

这些只能在以下条件下升级：

1. 多轮重复出现
2. 跨 batch 重复出现
3. 必要时经过 holdout review

否则 validation 会被制度化污染。

---

## 5. 统计制度必须重构

### 5.1 `probe` 不再承担精细评分

当前 `probe` 做得太像一个轻量 judge。

更成熟的做法是：

- `probe` 只过滤垃圾
- 不做复杂 route 排名
- 不用 IC 小数点后几位来做精细优先级

建议 `probe` 只回答：

- 能不能算
- 覆盖率是否过低
- 是否接近常数
- train 内是否完全无信号
- 是否明显结构不稳定
- 是否命中已知坏模板

输出只保留：

- `pass`
- `reserve`
- `fail`

### 5.2 `execute_research` 才做正式统计证据

研究阶段的正式统计判断应从 `probe` 挪到 `execute_research`。

建议保留三组证据：

1. `effect strength`
2. `stability`
3. `redundancy`

#### effect strength

- `ic_mean`
- `ic_ir`
- `ic_win_rate`
- `monotonicity`

#### stability

- split stability
- regime stability
- sign consistency
- horizon consistency

#### redundancy

- `max_lib_corr`
- residual incremental value
- family overlap

### 5.3 固定阈值要降级为 baseline，不再作为唯一依据

像下面这类阈值：

- `abs(ic_mean_full) < 0.01`
- `hard_gate_ic_oos_min: 0.008`

可以保留，但只应当作为：

- 最低可接受 baseline

不能当成：

- 主裁决依据

更合理的是：

1. baseline gate
2. cohort-relative ranking
3. repeated-evidence confirmation

### 5.4 增加最少限度的数据挖掘修正

即使现在不做完整学术化统计，也建议至少加三件事：

1. `purged walk-forward validation`
2. `bootstrap stability check`
3. `multiple-testing ledger`

其中 `multiple-testing ledger` 很重要。

因为自动系统每一轮都在试很多 route 和 candidate。
即使当轮预算不大，长期累计也是高强度多重检验。

最少要记录：

- 本 logic 累计试过多少 route
- 本 family 累计试过多少 candidate
- 本 hypothesis 下累计 admit 率
- 当前 batch 相对历史的成功基线

---

## 6. 研究阶段的“交易相关检查”应如何定义

这里不做真实成本、冲击、容量。
但也不能只看 `turnover`。

建议把这一层统一叫做：

- `implementation_feasibility_checks`

### 6.1 应保留的检查

- `turnover`
- `coverage`
- `half_life`
- `liquidity_coverage_ratio`
- `tail_trade_concentration`
- `small_cap_concentration`
- `rebalance_stress_proxy`

### 6.2 这些检查的作用

不是为了回答：

- 这个因子真实成本是多少

而是为了回答：

- 这个因子是否明显不适合作为当前研究频率下的 alpha 对象

### 6.3 建议的裁决方式

不要写成：

- `cost_passed`
- `capacity_passed`

而写成：

- `feasibility_ok`
- `feasibility_borderline`
- `feasibility_poor`

因为这里本质上只是研究阶段的可实现性分层。

---

## 7. library 相似性制度如何重构

### 7.1 保留 pairwise，但不止于 pairwise

当前的：

- `max_lib_corr`
- `nearest_factor_id`

仍然有用，应保留。

但应补两层判断：

### 第一层：pairwise duplication

处理：

- 近重复表达式
- 窗口轻微抖动
- 同一结构的小改写

### 第二层：family-level redundancy

处理：

- 同一 hypothesis / family 下是否已经堆了太多近似信号
- 新 candidate 是否只是给已有 family 再加一个相同风险切片

### 第三层：subspace novelty

处理：

- 虽然 pairwise corr 不高，但是否仍然只是同一风险源的变体

在只做研究的范围下，不需要把这一层做成完整组合优化。
但至少要在 `judge_research` 里有这样的判断槽位。

---

## 8. `judge_research` 应该怎么正式化

这是当前最该补的文档。

建议单独新建一份 `research_judge.md`，至少定义下面这些对象。

### 8.1 candidate verdict

每个 candidate 必须落在以下之一：

- `admit`
- `reserve`
- `reject`
- `replace`

### 8.2 route verdict

每个 route 必须落在以下之一：

- `continue`
- `pause`
- `kill`
- `promote_family`

### 8.3 logic verdict

每个 logic 必须落在以下之一：

- `active`
- `warm`
- `productive`
- `saturated`
- `parked`
- `dead`

### 8.4 裁决依据必须结构化

至少写明 5 类依据：

1. mechanism alignment
2. statistical evidence
3. stability evidence
4. redundancy evidence
5. feasibility evidence

### 8.5 不能直接用叙事替代规则

允许写文字说明。
但裁决必须至少先有结构化字段，例如：

```yaml
candidate_verdict: reserve

reason_codes:
  - borderline_strength
  - good_stability
  - high_family_overlap
  - feasibility_ok

judge_summary: >
  信号稳定但边际新意不足，先 reserve，等待同类 family 的后续比较。
```

这样长期 memory 才能真正被机器消费。

---

## 9. `logic` 和 `idea` 该怎么改

### 9.1 `logic` 要补 discovery 通道

当前 `logic` 太偏 exploitation。

建议在 schedule 里强制保留一小部分预算给：

- `adjacent discovery routes`

意思是：

- 不完全跳出当前 logic
- 但允许探索相邻 family、相邻 proxy、相邻机制切片

这样能减少路径依赖。

### 9.2 `idea` 要降评分、升约束

当前 `idea` 的 `route_select_score` 太细。

更成熟的做法是：

- 减少复杂加权评分
- 加强 fail/reserve/pass 三段式规则

也就是：

- 少一点伪精度
- 多一点明确约束

---

## 10. 文档结构也要重构

建议这个目录最后只保留研究制度文档。

### 建议保留

- `logic_plan.md`
- `idea_plan.md`
- `research_execute.md`
- `research_judge.md`
- `memory.md`
- `senior_quant_refactor_plan.md`

### 建议移走

- 工程结构重构文档

因为它本质上是工程结构重构，不是研究制度。

---

## 11. 推荐落地顺序

### P0

先修最大的制度问题：

1. 重写样本制度：`train / validation / holdout`
2. 把 `judge` 单独写成正式协议
3. 限制 validation 的回写权限

### P1

然后修统计制度：

1. `probe` 降级为垃圾过滤器
2. `execute_research` 成为正式统计证据层
3. 加入 `multiple-testing ledger`

### P2

然后修研究可实现性和相似性：

1. 增加 `implementation_feasibility_checks`
2. 把 redundancy 从 pairwise 扩展到 family/subspace 级别

### P3

最后修搜索制度：

1. 给 `logic` 预留 discovery 预算
2. 让 `idea` 从细粒度打分改成更强约束的分段裁决

---

## 12. 结论

如果只站在你当前“研究系统”的范围里，最该重构的不是去硬加实盘层，而是把下面四件事做扎实：

1. 样本制度重构，避免 OOS 被反复污染
2. 统计制度重构，减少经验阈值和多重检验偏差
3. `judge` 正式化，变成可复现的结构化裁决层
4. 研究可实现性代理补齐，但不假装做真实成本和容量分析

所以你的判断可以明确写成一句制度原则：

> 成本、冲击、容量不是当前因子挖掘研究系统需要精确解决的问题；当前系统只需要做研究层面的可实现性代理过滤。

在这个前提下，当前系统最急需修的，是样本、统计和裁决制度，而不是再继续加更多工程层细节。

还要补一条治理原则：

> score 只能做排序工具，不能做主裁决器。

原因很简单：

- 权重本身是研究政策参数，不是统计真值
- 当前库规模还不足以可靠校准一套稳定权重
- 若让 score 主导 admit / reject，只是把经验阈值换成了经验加权

---

## 13. 所有问题的最终修复方案

要把前面的 8 个问题真正补齐，必须补足以下制度能力。

### 13.1 样本污染问题

至少要做到：

1. 三层样本：`train / validation / holdout`
2. `holdout` 不进入日常批处理主循环
3. 增加 `validation_window_id`
4. 增加 `validation_exposure_count`
5. 增加 `holdout_review_ledger`

但三分法不能被实现成“永远固定一刀切的 6 年 train + 3 年 validation + 2 年 holdout”。

更合理的实现是：

- `train` 使用 anchored expanding
- `validation` 使用预定义 roster 轮换
- `holdout` 只做 release review / veto

这样才能同时兼顾：

- 样本独立性边界
- IS 覆盖长度
- validation 被过度消费时的可轮换性
- holdout 统计效力有限这一现实

### 13.2 统计标准问题

不能再写成“所有学术检验都必须同时做到”的清单。

更合适的协议是分层：

1. 基础必做：
   - `expanding_window_ic_stability`
   - `split_stability`
   - `regime_stability`
   - `bootstrap_stability`（若样本量允许）
   - `multiple_testing_ledger`
   - `multiple_testing_risk_bucket`
2. 高级可选：
   - `purged_walk_forward`
   - `search_adjusted_strength_bucket`

其中：

- `purged_walk_forward` 只有在有效 split 数足够时才启用
- `search_adjusted_strength_bucket` 只是连续搜索场景下的研究风险代理，不宣称具有原始 deflated t-stat 的严格统计含义

### 13.3 研究层交易代理问题

至少要做到：

1. `turnover`
2. `holding_period_proxy`
3. `liquidity_coverage_ratio`
4. `tail_trade_concentration`
5. `small_cap_concentration`
6. `rebalance_stress_proxy`

### 13.4 冗余问题

在当前数据条件下优先做到：

1. `pairwise overlap`
2. `family_overlap_score`
3. `subspace_redundancy_score`
4. `residual_incremental_ic`
5. `family` 必须采用规则化 taxonomy，而不是事后按相关性聚类
6. `subspace` 必须采用 local basis，而不是全库黑盒 PCA

### 13.5 风险模型问题

至少要做到：

1. `raw view`
2. `cap_industry_neutral view`
3. `barra_residual view`
4. `alpha_survival_ratio`

### 13.6 search / discovery 问题

至少要做到：

1. exploitation budget
2. adjacent discovery budget
3. productive / saturated logic 的 discovery 最低配额
4. 轻量 bottom-up anomaly escalation
5. discovery candidate 进入 `search_ledger`
6. anomaly 不能直接立项，只能进入下一轮 `logic review`

### 13.7 裁决问题

至少要做到：

1. `candidate / route / logic` 三层 verdict
2. `reason codes`
3. 分级回写
4. policy 升级只能走 `policy_upgrade_ledger`

### 13.8 文档边界问题

至少要做到：

1. 研究制度文档和工程重构文档分离
2. 目录里只保留研究主线文档

---

## 14. 最终判断

如果以上协议全部进入正式规范，那么这套研究设计就可以说：

- 已经针对 `senior_quant_refactor_plan` 里提出的问题给出成体系的解决方法
- 虽然不是生产交易系统，但已经是一个足够成熟的研究系统制度

剩下的风险就不再是“规范没定义”，而是后续实现时是否严格遵守这些协议。
