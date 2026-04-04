````markdown id="1i6btr"
---
name: factor-execute
description: 按统一评估协议执行 batch candidates：单链路计算 base signal → pipeline transforms → final evaluation，并输出可供 judge 消费的结构化证据包
user_invocable: true
---

# 因子评估执行 — /execute v2

`factor-execute` 是整个自动因子研究系统的**正式执行与证据整理层**。  
它不负责决定研究主题，也不负责生成新候选，而负责：

- 读取 `/idea` 生成的 batch candidates
- 对 candidate 做 source-specific Full Precheck
- 只执行一次 candidate 主逻辑，生成 `base signal`
- 在统一 `evaluation pipeline` 下将 `base signal` 转成 `evaluation-ready signal`
- 计算正式评估指标
- 做批内去重、库内相似性检查、替换检查
- 输出给 `/judge` 消费的结构化结果文件
- 输出执行摘要与工程反馈，供后续经验回写

---

## 核心定位

在整条链路中：

- `logic` 决定：**研究什么大方向**
- `idea` 决定：**围绕这个方向，这一轮怎么做实验、产出哪些 candidate**
- `execute` 决定：**这些 candidate 在统一评估协议下到底表现如何**
- `judge` 决定：**录取什么，并把经验回写到系统**

所以 `execute` 的本质不是“跑回测脚本”，而是：

> **将 `idea` 产出的 candidates，转成可比较、可审计、可裁决的证据包。**

---

## 核心原则

### 原则 1：`execute` 只消费 batch candidates
`execute` 不负责创建新 logic，不负责生成新 route，不负责自由修改 candidate 结构。  
它的唯一输入是 `/idea` 产生的 `batch_XXX.yaml`。

### 原则 2：candidate 主逻辑只执行一次
无论 candidate 是 DSL 还是 Python，主逻辑只允许执行一次，生成 `base signal`。  
任何后续清洗、标准化、中性化都必须基于该次计算结果派生，不允许重新调用 candidate 主逻辑。

### 原则 3：统一评估口径由 profile 决定
股票池、可交易性、预处理、中性化、指标与 hard gate 都不应由 candidate 自己随意决定，  
而必须由 `evaluation_profile` 统一规定。

### 原则 4：默认只对最终评估信号做主评估
正式评估只对 `evaluation-ready signal` 做一次主评估。  
`base signal` 只允许提取少量 cheap diagnostics，不应再做一套完整评估流程。

### 原则 5：source-specific Full Precheck 是正式闸门
Probe 阶段只做 Lite Precheck；  
进入 `execute` 的正式 candidate 必须经过 source-specific Full Precheck 才能继续。

### 原则 6：支持 DSL 与 Python，但必须统一执行协议
`execute` 必须支持：
- `source_type: dsl`
- `source_type: python`

但两者最终都必须统一落到同一类 `base signal` / `evaluation-ready signal` 表达上。

### 原则 7：向量化是硬约束
当前架构下，candidate 必须可批量、可向量化、可统一调度。  
Python candidate 不是自由 Python，而必须是**helper-based vectorized Python**。  
不可向量化且不值得 helper 化的逻辑，不应进入自动批量主系统。

### 原则 8：`execute` 负责准备给 `judge` 的证据，而不是直接裁决
`execute` 输出结果必须保留：
- logic 上下文
- route 上下文
- implementation 上下文
- 评估指标
- precheck / performance 状态

以支持 `judge` 做 admit / reject / replace 以及逻辑回写。

---

# 一、输入对象

## Step 0：读取本轮执行上下文

读取：

```bash
cat storage/candidates/batch_XXX.yaml
cat storage/candidates/batch_XXX_idea_report.yaml
cat storage/system/capability_registry.yaml
cat storage/library/library.yaml
cat storage/evaluation_profiles/standard_eval_v2.yaml
````

## `batch_XXX.yaml` 至少包含

每个 candidate 必须包含：

* `candidate_id`
* `logic_id`
* `route_id`
* `family_id`
* `route_type`
* `source_type`
* `name`
* `expression` 或 `code`
* `implementation_reason`
* `rationale`
* `lineage`

Python candidate 还必须包含：

* `params`
* `param_space`

## `batch_XXX_idea_report.yaml` 的作用

`execute` 不依赖它来跑主流程，但建议读取它以便：

* 理解 batch 的 route 来源
* 生成 execute report 时做 route/context 聚合
* 支持后续问题定位（logic 问题 / route 问题 / implementation 问题）

---

# 二、评估协议：Profile 驱动

`execute` 不应把 universe、tradability、preprocess、neutralization 等规则散在代码里。
应由 profile 统一指定。

---

## 1. Universe Profile

定义“在哪个股票池上评估”。

例如：

```yaml
name: all_a_share
universe_type: all_listed_equities
membership_timing: point_in_time
rebalance_frequency: daily
```

或：

```yaml
name: csi1000
universe_type: index_constituents
index_code: CSI1000
membership_timing: point_in_time
rebalance_frequency: daily
```

### 作用

决定：

* 股票集合
* 时点成分处理方式
* universe membership 的时间逻辑

---

## 2. Tradability Profile

定义“哪些样本点虽然在 universe 中，但评估时不视为有效可交易样本”。

例如：

```yaml
name: china_a_daily_tradeable_v1
delay: 1
forward_return_horizon: 5

filters:
  filter_suspend: true
  filter_limit_up_down: true
  filter_invalid_forward_return: true
```

### 作用

决定：

* 是否剔除停牌
* 是否剔除涨跌停
* delay
* forward return horizon
* invalid forward return mask

---

## 3. Factor Preprocess Profile

定义“candidate 生成的 base signal 如何被统一清洗和标准化”。

例如：

```yaml
name: default_preprocess_v1
inf_to_nan: true
winsorize_method: mad
winsorize_n: 5.0
standardize_method: zscore
min_valid_ratio: 0.30
constant_factor_variance_threshold: 1e-12
```

### 作用

决定：

* inf → NaN
* 去极值方式
* 标准化方式
* 最低有效覆盖率
* 近常数检查阈值

---

## 4. Neutralization Profile

定义“最终评估口径是否剥离风格暴露”。

例如：

```yaml
name: industry_cap_neutral_v1
mode: both   # none / market_cap / industry / both
```

### 作用

决定：

* 是否做市值中性化
* 是否做行业中性化
* 是否两者都做
* 或完全不做

---

## 5. Evaluation Profile

总 profile 组装上面几层，并定义 metrics 与 hard gates。

例如：

```yaml
name: standard_eval_v2

universe_profile: all_a_share
tradability_profile: china_a_daily_tradeable_v1
factor_preprocess_profile: default_preprocess_v1
neutralization_profile: none

metrics:
  - ic_mean
  - ic_ir
  - monotonicity
  - ls_return
  - ls_tstat
  - turnover
  - max_lib_corr

hard_gates:
  hard_gate_oos_decay_min: 0.2
  hard_gate_coverage_min: 0.3
  hard_gate_ic_oos_min: 0.008
```

---

# 三、完整流程

## Step 1：source-specific Full Precheck

进入正式执行前，所有 candidate 都必须经过 source-specific Full Precheck。

---

## 1A. DSL candidate Full Precheck

至少检查：

* `parser_full_check`
* `operator_whitelist_full_check`
* `field_whitelist_full_check`
* `expression_depth_check`
* `constant_factor_check`
* `valid_ratio_precheck`
* `forbidden_pattern_check`

### 说明

这里检查的是：

* 表达式是否合法
* 是否只用了允许的 DSL operators
* 是否用了禁止字段
* 是否明显近常数
* 是否属于已知坏模板

---

## 1B. Python candidate Full Precheck

至少检查：

* `syntax_full_check`
* `helper_whitelist_full_check`
* `forbidden_pattern_full_check`
* `complexity_check`
* `smoke_test`
* `output_shape_index_check`
* `param_schema_check`
* `vectorization_check`

### 说明

Python candidate 必须满足：

* 只使用白名单 `ops.*` helper
* 不允许任意 import
* 不允许网络调用
* 不允许文件 IO
* 不允许显式逐股票 / 逐日期 / 逐元素慢路径

### 推荐 complexity 约束

可从 capability registry 读取，例如：

* `max_code_lines <= 30`
* `max_branch_count <= 3`
* `max_param_count <= 3`
* `max_intermediate_variable_count <= 6`

---

## 1C. Performance Full Check

除了合法性，还要做性能与执行形态检查。

### 至少检查

* `smoke_benchmark_check`
* `forbidden_slow_pattern_check`
* `materialization_risk_check`

### 典型 forbidden slow patterns

* `explicit_row_loop`
* `explicit_date_loop`
* `explicit_instrument_loop`
* `pandas_apply_axis_1`
* `rolling_apply_lambda`
* `groupby_apply_custom_python`
* `repeated_dataframe_merge`

### 结果

candidate 可以被标记为：

* `precheck_failed`
* `performance_rejected`
* `precheck_passed`

---

# 四、单链路计算：只计算一次 base signal

## Step 2：执行 candidate 主逻辑，生成 base signal

### DSL candidate

通过 expression evaluator 执行

### Python candidate

通过 helper-based vectorized compute runner 执行

### 输出

统一得到：

* `base_signal`

这是一份标准对齐后的因子矩阵 / panel，对后续 pipeline 透明。

---

## Step 3：提取 cheap diagnostics（可选但推荐）

对 `base_signal` 顺手提取少量 cheap diagnostics，不再额外重跑一套原始评估。

### 推荐 diagnostics

* `base_valid_ratio`
* `base_variance`
* `base_constant_flag`
* `base_outlier_ratio`
* `base_skew`
* `base_kurtosis`

### 原则

* 只做便宜 summary
* 不对 `base_signal` 做完整主评估
* 不保留多份大矩阵副本

---

# 五、统一 pipeline 处理

## Step 4：股票池与收益遮罩

在 `base_signal` 基础上，先应用 universe 与 tradability 相关处理。

### 处理内容

* universe membership mask
* suspend filter
* limit up/down filter
* invalid forward return mask
* delay 对齐
* return horizon 对齐

### 目的

确保后续评估基于统一、可交易的样本点。

---

## Step 5：因子清洗

对 `base_signal` 应用 preprocess profile。

### 处理内容

* `inf -> NaN`
* 缺失与非法值处理
* 极端值处理（winsorize）
* 基础覆盖率检查

### 说明

这些是**execute 的公共处理层**，不应由 candidate 随意自带。
只有当某个变换本身就是 signal definition 的核心时，candidate 才允许显式声明。

---

## Step 6：标准化

根据 preprocess profile 应用统一标准化。

### 常见方式

* `zscore`
* `rank`

### 原则

标准化默认属于 execute pipeline，
不应在 candidate 中随意重复实现。

---

## Step 7：中性化

根据 neutralization profile 对 signal 做统一中性化。

### 可选模式

* `none`
* `market_cap`
* `industry`
* `both`

### 原则

中性化属于评估制度的一部分，而不是 candidate 自己决定的东西。

---

## Step 8：得到 evaluation-ready signal

经过上面几步后，得到：

* `evaluation_ready_signal`

这才是正式进入指标计算的最终信号。

> **正式评估只对 `evaluation_ready_signal` 做一次主评估。**

---

# 六、正式评估

## Step 9：计算正式评估指标

只对 `evaluation_ready_signal` 计算统一 metrics。

### 推荐指标

* `ic_mean`
* `ic_ir`
* `ic_win_rate`
* `ic_mean_oos`
* `ic_ir_oos`
* `monotonicity_is`
* `monotonicity_oos`
* `ls_return`
* `ls_tstat`
* `turnover`
* `half_life_days`
* `coverage`
* `zero_ratio`
* `factor_skew`
* `incremental_ic`
* `max_lib_corr`
* `nearest_factor_id`

### 目的

为 `judge` 提供统一、可比较的证据包。

---

# 七、批内与库内比较

## Step 10：批内去重

对本 batch 内 candidate 做近似重复检查。

### 目的

防止同一轮里出现大量：

* 只是窗口微抖动
* 只是表达风格轻变化
* 实际信号高度近似

### 输出

可标记为：

* `duplicate_rejected`

---

## Step 11：库内相似性检查

将 candidate 与当前 library 做相似性比较。

### 核心输出

* `max_lib_corr`
* `nearest_factor_id`
* `overlap_risk`

### 目的

防止自动系统不断生成看起来有信号但与已有库高度相似的因子。

---

## Step 12：替换检查

如果 candidate 与已有库中某个因子高度相关，但：

* OOS 更稳
* 增量信息更高
* 更简单
* 更低 turnover

则可标记为：

* `replacement_candidate`

### 输出

* `replace_target_id`
* `replacement_score`
* `replacement_reason`

---

# 八、Hard Gates

## Step 13：应用 hard gates

hard gates 由 evaluation profile 统一定义。
典型包括：

* `ic_sign_consistent = false`
* `oos_decay_ratio < hard_gate_oos_decay_min`
* `coverage < hard_gate_coverage_min`
* monotonicity IS/OOS 符号相反
* `abs(ic_mean_oos) < hard_gate_ic_oos_min`

### 输出

被拦截的 candidate 应明确归类为：

* `hard_rejected`

---

# 九、结果分层输出

## Step 14：生成多层结果，而不只是 screened

建议 result 至少分成以下几类：

* `syntax_failed`
* `precheck_failed`
* `performance_rejected`
* `duplicate_rejected`
* `library_corr_rejected`
* `hard_rejected`
* `screened`
* `replacement_candidates`

### 原因

这样 `judge` 才能：

* 清楚知道谁真正进入裁决
* 区分研究失败与工程失败
* 做更干净的 logic / route / implementation feedback

---

# 十、结果 Schema

## Step 15：生成 `batch_XXX_result.yaml`

这是 `judge` 的主要输入文件。

每个 candidate 的 result 至少保留：

* `candidate_id`
* `logic_id`
* `route_id`
* `family_id`
* `route_type`
* `source_type`
* `implementation_reason`
* `precheck_status`
* `performance_status`
* `diagnostics`
* `evaluation`
* `similarity`
* `replacement_info`

### 推荐结构示例

```yaml id="hiqj84"
candidate_id: C042_03
logic_id: L021
route_id: R021_01
family_id: FM_breakout
route_type: genesis
source_type: dsl
implementation_reason: "simple conditional breakout; naturally supported by IfElse + TsRank + Std"

precheck_status: passed
performance_status: passed

diagnostics:
  base:
    valid_ratio: 0.88
    variance: 1.42
    constant_flag: false
    outlier_ratio: 0.06
    skew: 3.8
    kurtosis: 11.4

pipeline_trace:
  tradability_profile: china_a_daily_tradeable_v1
  preprocess_profile: default_preprocess_v1
  neutralization_profile: none
  winsorized: true
  standardized: zscore
  neutralized: false

evaluation:
  ic_mean: 0.013
  ic_ir: 0.18
  ic_win_rate: 0.56
  ic_mean_oos: 0.011
  ic_ir_oos: 0.15
  monotonicity_is: 0.74
  monotonicity_oos: 0.41
  ls_return: 0.092
  ls_tstat: 2.1
  turnover: 0.34
  coverage: 0.86
  incremental_ic: 0.008

similarity:
  max_lib_corr: 0.62
  nearest_factor_id: F013
  overlap_risk: medium

replacement_info:
  replacement_candidate: false
  replace_target_id: null
  replacement_score: null
```

---

# 十一、缓存与一致性

## Step 16：生成 values cache（如需要）

对于通过 precheck 并进入正式评估的 candidate，可生成：

```text id="tzd3bs"
storage/candidates/batch_XXX_values.pkl
```

用于后续 `/judge` 中 admit / replace 时写库。

### 注意

必须增加 fingerprint / hash 校验，以避免：

* result 文件和 values cache 来自不同版本
* stale pkl 污染 commit

推荐至少校验：

* `batch_id`
* candidate list hash
* evaluation profile name
* generated timestamp

---

# 十二、执行摘要

## Step 17：生成 `batch_XXX_execute_report.yaml`

这是推荐新增的执行摘要文件。

### 至少记录

* batch 基本信息
* candidate 总数
* DSL / Python 数量与通过率
* precheck 失败原因分布
* performance reject 原因分布
* duplicate / corr / hard gate 的统计
* screened candidate 摘要
* replacement candidate 摘要

### 作用

支持后续：

* judge 的 implementation feedback
* capability / lessons 的回写
* 判断是否某类 route/systematic pattern 总是工程失败

---

# 十三、raw/final handling 原则

## 核心原则

不要把 `base signal` 和 `evaluation_ready_signal` 理解成“两次完整计算”或“两次完整评估”。

### 正确实现

* candidate 主逻辑只执行一次，得到 `base signal`
* 然后对 `base signal` 串行应用 pipeline transforms
* 最终得到 `evaluation_ready_signal`
* 正式评估只对 `evaluation_ready_signal` 做一次

### 诊断信息

只允许从 `base signal` 顺手提取少量 summary stats，
而不再单独对 `base signal` 做一整套完整评估。

---

# 十四、`execute` 的职责边界

## `execute` 负责

* 读取 batch
* source-specific Full Precheck
* 只执行一次 candidate 主逻辑
* 应用统一 pipeline
* 做正式评估
* 做去重/相似性/替换检查
* 输出结构化结果与执行摘要

## `execute` 不负责

* 生成新 logic
* 生成新 route
* 自由修改 candidate
* 最终录取
* 直接更新长期 memory

这些事情属于 `logic` 或 `judge`。

---

# 十五、最终目标

`factor-execute v2` 的目标不是“跑一个回测”，而是：

* 在统一协议下公平比较 candidates
* 保持 universe / tradability / preprocess / neutralization 一致
* 区分研究失败与工程失败
* 为 `judge` 提供干净、结构化、可回写的证据包
* 支持自动系统长期稳定迭代

---

# 十六、简短总结

> `factor-execute v2` 应该是一套“读取 `idea` 产出的 candidates，做 source-specific Full Precheck，在统一 evaluation profile 下单链路生成 evaluation-ready signal，并输出结构化结果供 `judge` 裁决”的正式执行系统。

```
```
