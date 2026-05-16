# Factor IR 与 Planner 执行计划

> 日期：2026-05-04
>
> 状态：执行计划
>
> 范围：基于当前 skill-based 5-phase pipeline 和已落地的日内 primitive V0，继续把系统从“Qlib DSL / Python 文件驱动”升级为“Factor IR + Planner + 多 Backend 驱动”。

---

## 1. 为什么要改

当前系统已经具备三个事实：

```text
1. Qlib daily DSL 很快，适合批量执行简单日频表达式。
2. Python candidate 已存在，适合表达 Qlib DSL 很难表达的复杂日频逻辑。
3. 日内 primitive V0 已接入，分钟数据可以先物化成日频字段，再进入 Phase2。
```

但如果继续让 LLM 直接生成：

```text
Qlib DSL
Python 文件
primitive 字段名
```

系统会逐渐出现几个问题：

```text
1. LLM 容易引用不存在的字段。
2. LLM 容易漏写 primitive_dependencies。
3. 分钟 primitive 可能无限膨胀。
4. Python 因子不可复用、不可缓存、不可审计。
5. Qlib DSL 会被迫承载越来越复杂的日频逻辑。
6. Judge / Report / Consolidate 难以总结“哪类生成逻辑有效”。
```

因此新的中心不应该是 Qlib，也不应该是自由 Python，而应该是：

```text
Factor IR + Execution Planner
```

---

## 2. 核心分工

### 2.1 LLM 负责研究逻辑

LLM 决定：

```text
研究假设是什么
用哪些数据族
用哪些 primitive
用什么 daily factor logic
预期方向是什么
为什么应该有效
```

LLM 不直接负责：

```text
检查字段是否存在
判断 cache hit/miss
决定是否重扫分钟数据
决定写入哪个 Qlib store
判断未来函数
把任务拆给不同 backend
```

### 2.2 Planner 负责执行逻辑

Planner 不替 LLM 想因子。Planner 的职责是把 LLM 的研究设计变成可执行任务：

```text
解析 Factor IR / legacy manifest
收集 primitive dependencies
检查 registry / cache / materialization status
判断 backend：Qlib / Daily Python / Primitive Materializer
检查时间语义和 label 匹配
生成 Phase2 可消费的 CandidateInputs
把错误提前拦截，而不是等 Phase2 才失败
```

### 2.3 Backend 负责计算

至少保留三类 backend：

```text
PrimitiveMaterializer
  minute/tick/fundamental/event -> daily primitive

QlibBackend
  简单日频 DSL 批量计算

DailyPythonBackend
  复杂日频模板计算
```

---

## 3. 目标架构

目标链路：

```text
/factor-idea
  LLM 生成 Factor IR 或兼容旧 manifest
        |
        v
Execution Planner
  解析 IR
  收集依赖
  检查 primitive registry/cache
  选择 backend
  做 leakage / availability 检查
        |
        v
Pre-Phase2 Materialization
  缺失 primitive 批量物化
  导出 daily primitive
        |
        v
Daily Factor Execution
  QlibBackend 批量执行简单 daily DSL
  DailyPythonBackend 执行复杂 daily template
        |
        v
Phase2 Evaluator
  IC / RankIC / quintile / Barra / redundancy / feasibility
        |
        v
Judge / Archive / Report / Consolidate
  记录完整 IR、backend、primitive provenance、template provenance
```

---

## 4. Factor IR 规范

第一版 IR 不要过重，只需要覆盖当前系统的真实需求。

### 4.1 Qlib 类型候选

```yaml
candidate_id: C001
ir_version: v1
hypothesis: 早盘成交集中代表拥挤交易，后续可能反转。

data_logic:
  primitive_dependencies:
    - open_30m_volume_share_v1

factor_logic:
  backend: qlib
  expression: >
    Mul(
      CsRank($open_30m_volume_share_v1),
      CsRank(Div($volume, Mean($volume,20)))
    )

expected_sign: negative
label:
  horizon: 1
  decision_time: "T+1 open"
```

### 4.2 Daily Python 模板候选

```yaml
candidate_id: C002
ir_version: v1
hypothesis: 高价格位置的振幅高于低价格位置，说明高位多空博弈激烈，后续收益偏弱。

data_logic:
  daily_fields:
    - high
    - low
    - close

factor_logic:
  backend: daily_python
  template: quantile_split_spread
  params:
    value:
      expression: "Div($high,$low)-1"
    sorter:
      expression: "$close"
    window: 20
    top_quantile: 0.25
    bottom_quantile: 0.25
    output: top_mean_minus_bottom_mean

expected_sign: negative
label:
  horizon: 1
  decision_time: "T+1 open"
```

### 4.3 Legacy manifest 兼容

短期不能废掉旧格式。Planner 必须能把旧格式转换成 IR-like task：

```yaml
candidates:
  - candidate_id: C001
    source_type: dsl
    expression: CsRank($open_30m_volume_share_v1)
    primitive_dependencies:
      - open_30m_volume_share_v1
```

转换后：

```yaml
factor_logic:
  backend: qlib
  expression: CsRank($open_30m_volume_share_v1)
```

---

## 5. Planner 要做什么

Planner 的输入：

```text
manifest.yaml
storage paths
config.yaml
sample range
label / horizon config
```

Planner 的输出：

```yaml
execution_plan:
  primitive_tasks:
    - feature_id: open_30m_volume_share_v1
      backend: minute_materializer
      status: cache_hit
      spec_hash: "..."

  qlib_tasks:
    - candidate_id: C001
      expression: CsRank($open_30m_volume_share_v1)

  daily_python_tasks:
    - candidate_id: C002
      template: quantile_split_spread
      params:
        window: 20
        top_quantile: 0.25

  errors: []
```

Planner 的必要检查：

```text
1. 候选是否有 candidate_id。
2. backend 是否受支持。
3. Qlib expression 引用的 primitive 是否声明在 primitive_dependencies。
4. primitive_dependencies 是否存在于 registry 或 proposed_primitives。
5. cache 是否覆盖 train/validation range。
6. cache miss 时是否有可用 raw data loader。
7. available_time 是否早于 label decision_time。
8. 每个 batch 新增 primitive 是否超过 budget。
9. Daily Python template 是否存在，参数是否合法。
10. 输出的任务是否能还原到 Phase2 CandidateInputs。
```

---

## 6. Daily Python 是什么

当前系统已有 Python candidate，但长期不能让 LLM 每次自由生成不同 `.py` 文件。

新的 Daily Python 不是取消 Python，而是把它规范成：

```text
受控模板 + 参数
```

它负责 Qlib DSL 不适合表达的复杂日频逻辑，例如：

```text
rolling 分位切割
rolling 条件均值
rolling 回归残差
行业/市值分组中性化
多步骤 winsorize / neutralize / aggregate
```

第一批模板建议只做两个：

```text
quantile_split_spread
conditional_rolling_mean
```

### 6.1 quantile_split_spread

用于理想振幅这类逻辑：

```text
过去 N 日
按 sorter 排序
取 top/bottom 分位样本
对 value 求均值
输出 top_mean - bottom_mean
```

参数：

```yaml
template: quantile_split_spread
params:
  value:
    expression: "Div($high,$low)-1"
  sorter:
    expression: "$close"
  window: 20
  top_quantile: 0.25
  bottom_quantile: 0.25
  output: top_mean_minus_bottom_mean
```

### 6.2 conditional_rolling_mean

用于条件 rolling 均值：

```text
过去 N 日
只保留 condition 为 true 的日期
对 value 求均值
```

参数：

```yaml
template: conditional_rolling_mean
params:
  value:
    expression: "$return_1d"
  condition:
    expression: "Gt($turnover_rate, Mean($turnover_rate,20))"
  window: 20
  min_count: 5
```

---

## 7. Primitive 治理

日内 primitive 不能无限增长。V1 必须把 primitive 当成受控资产管理。

### 7.1 Primitive Family

不是每个想法一个字段，而是：

```text
有限 family + 参数化实例
```

示例 family：

```yaml
family: open_window_share
template: window_share
allowed_params:
  field: [volume, amount]
  numerator_window:
    - "09:30-09:35"
    - "09:30-09:40"
    - "09:30-10:00"
    - "09:30-10:30"
  denominator_window:
    - "09:30-15:00"
```

### 7.2 Primitive Budget

每轮限制新增 primitive：

```yaml
primitive_budget:
  max_new_primitives_per_batch: 3
  allow_new_family: false
```

新 family 默认不进入高频 mining，需要人工或专门 review。

### 7.3 Primitive Archive

每个 primitive 需要积累表现：

```text
被引用次数
cache hit/miss 次数
最优 factor 表现
平均 IC / ICIR
与 turnover / volatility / size 的相关性
是否被 admit factor 使用
status: active / experimental / deprecated
```

---

## 8. 与 5-phase 的结合

### Phase1 START / factor-idea

新增输入：

```text
可用 primitive 列表
可用 primitive family
可用 daily python templates
已有表现摘要
backend 使用规则
```

输出：

```text
Factor IR 或兼容旧 manifest
```

### Pre-Phase2 Planner

新增步骤：

```text
manifest -> Factor IR normalization
IR -> execution plan
execution plan -> primitive materialization / backend task list
```

### Phase2 EXECUTE

保持现有 evaluator 不变。变化只在 factor_series 生成阶段：

```text
QlibBackend 生成一部分 factor_series
DailyPythonBackend 生成一部分 factor_series
PrimitiveMaterializer 只生成 daily primitive，不直接生成最终评估指标
```

### Phase3 JUDGE

Judge packet 必须看到：

```text
Factor IR
backend
daily template
primitive dependencies
primitive provenance
available_time / decision_time
```

### Phase4 ARCHIVE

factor.yaml 必须归档：

```text
完整 Factor IR
backend provenance
primitive provenance
daily template params
```

### Phase5 CONSOLIDATE

Consolidate 不只总结 expression，还要总结：

```text
哪些 primitive family 有效
哪些 daily template 有效
哪些参数区间有效
哪些 backend 产出的候选更稳定
哪些 primitive 应该 deprecated
```

---

## 9. 分阶段执行计划

### P0：当前已完成

状态：已落地。

内容：

```text
1. minute primitive registry/cache/materializer/exporter
2. Pre-Phase2 primitive materialization
3. result.yaml primitive_materialization
4. candidates[].primitive_dependencies / primitive_provenance
5. hints / factor.yaml / report packet 透传 primitive provenance
6. 中文 primitive 设计文档和 skill 契约
```

验收：

```text
focused tests 通过
minute primitive 可以被 manifest 引用并进入 Phase2
```

### P1：Factor IR Schema + Legacy Adapter

状态：已落地。

目标：

```text
让系统能读取新 IR，同时兼容旧 manifest。
```

新增文件：

```text
src/research/ir/
  __init__.py
  schema.py
  adapter.py
  validator.py
```

任务：

```text
1. 定义 FactorIR / DataLogic / FactorLogic / LabelSpec dataclass。已完成。
2. 实现 legacy candidate -> FactorIR adapter。已完成。
3. 实现 IR validator。已完成。
4. build_phase2_inputs() 先 normalize manifest。已完成。
5. result.yaml candidates[] 记录 ir_version / factor_logic.backend。已完成。
6. Phase1 freeze 保留 primitive_dependencies / data_logic / factor_logic。已完成。
7. Phase1 DSL 校验允许已声明 primitive 字段。已完成。
```

验收：

```text
旧 manifest 不受影响。
新 IR manifest 可以跑通 qlib backend。
validator 能发现缺 candidate_id、未知 backend、非法 template。
```

### P2：Execution Planner

状态：已落地。

目标：

```text
把 primitive 依赖解析、backend 选择、cache/materialization plan 从 data_bridge 中抽出来。
```

新增文件：

```text
src/research/planner/
  __init__.py
  execution_plan.py
  planner.py
  leakage_checker.py
```

任务：

```text
1. 定义 ExecutionPlan。已完成。
2. Planner 从 FactorIR 列表生成 primitive_tasks / qlib_tasks / daily_python_tasks。已完成。
3. 检查 expression 引用的 primitive 是否声明。已完成。
4. 接入 existing ensure_primitives_materialized()。已完成。
5. build_phase2_inputs() 改为消费 ExecutionPlan。已完成。
6. primitive cache miss 且未配置 minute loader 时提前失败。已完成。
7. result.yaml 记录 execution_plan。已完成。
```

验收：

```text
Planner 对无 primitive 的旧 Qlib DSL 是 no-op。
Planner 对 primitive 缺失能提前报错。
Planner 能输出 cache_hit/materialized provenance。
```

### P3：DailyPythonBackend + 模板注册

状态：已落地。

目标：

```text
把复杂日频 Python 因子从自由脚本改成受控模板。
```

新增文件：

```text
src/research/daily_templates/
  __init__.py
  registry.py
  quantile_split_spread.py
  conditional_rolling_mean.py

src/research/compute/daily_python_backend.py
```

任务：

```text
1. 实现模板 registry。已完成。
2. 实现 quantile_split_spread。已完成。
3. 实现 conditional_rolling_mean。已完成。
4. DailyPythonBackend 根据 template + params 生成 factor_series。已完成。
5. 支持读取 market_df 已有字段，缺失字段从当前 Qlib provider 读取。已完成。
6. 将 DailyPythonBackend 输出并入 CandidateInputs。已完成。
7. Phase1 freeze 支持 backend=daily_python 的 IR candidate。已完成。
```

验收：

```text
理想振幅因子可以用 quantile_split_spread 表达并跑入 Phase2。已完成。
模板有单测。已完成。
自由 Python candidate 仍兼容，但新生成优先走 template。已完成。
```

### P4：factor-idea 菜单化

状态：已落地。

目标：

```text
让 LLM 看到可用 primitive family、primitive instance、daily template，而不是凭空发明字段。
```

修改：

```text
.claude/skills/factor-idea/skill.md
src/research/checkpoints/generator.py 或对应 packet builder
```

任务：

```text
1. idea packet 增加 available_primitives。已完成，通过 `research phase1 menu` 输出。
2. idea packet 增加 available_daily_templates。已完成。
3. idea packet 增加 primitive family 参数约束。已完成。
4. 规定新增 primitive 走 proposal，不直接无限生成。已完成，写入菜单 rules 和 factor-idea skill。
```

验收：

```text
Phase1 生成候选时能引用菜单项。已完成。
候选包含 backend / template / primitive_dependencies。已完成。
```

### P5：Archive 保存完整 IR

状态：已落地。

目标：

```text
admitted factor 不只保存 expression，还保存完整生成逻辑。
```

修改：

```text
src/research/archive/factor_writer.py
src/research/archive/report_packer.py
.claude/skills/factor-report/skill.md
```

任务：

```text
1. factor.yaml 增加 factor_ir。已完成。
2. factor.yaml 增加 backend_provenance。已完成。
3. report packet 展示 factor_ir / template params。已完成。
4. factor.md 要解释 primitive 和 daily template 的研究机制。已写入 report packet 输入，报告撰写由 /factor-report 消费。
```

验收：

```text
admitted qlib factor、daily_python factor、primitive factor 都能完整归档。已完成。
```

### P6：Consolidate 总结生成逻辑

状态：已落地。

目标：

```text
Phase5 不只总结因子表现，还总结生成逻辑表现。
```

修改：

```text
.claude/skills/factor-consolidate/skill.md
src/research/memory/ 或 consolidation 相关模块
```

任务：

```text
1. 汇总 primitive family 表现。已完成基础版：primitive_usage_counts / primitive_to_factors。
2. 汇总 daily template 表现。已完成基础版：daily_template_counts / template_to_factors。
3. 汇总 backend 产出质量。已完成基础版：backend_counts。
4. 标记 low-value primitive 为 deprecated。未自动改 registry，先由 consolidation 文档/人工判断。
5. 产出下一轮 /factor-idea 可用菜单摘要。已完成：phase1 menu 输出 historical_generation_summary。
```

验收：

```text
LLM 下一轮能看到哪些 primitive/template 应该优先用，哪些不要再用。已完成基础版。
```

---

## 10. 当前最优执行顺序

不要继续盲目扩 primitive 字段库。下一步应该先做：

```text
P1 Factor IR Schema + Legacy Adapter
P2 Execution Planner
P3 DailyPythonBackend 的两个模板
```

原因：

```text
1. V0 已经证明 primitive 能进 Phase2。
2. 现在最大的风险不是算不了，而是生成逻辑失控。
3. IR + Planner 是约束 LLM、复用 primitive、接入 Daily Python 的共同基础。
```

---

## 11. 不做什么

短期不做：

```text
1. 不替换 Qlib。
2. 不废掉旧 manifest。
3. 不允许 LLM 无限自由写 Python。
4. 不允许每个想法都新增一个 primitive 字段。
5. 不直接扩 tick / 新闻 / 财报。
6. 不让 Phase2 理解分钟数据。
```

---

## 12. 一句话总结

后续改造的核心不是“多加几个分钟字段”，而是：

```text
用 Factor IR 表达研究设计；
用 Planner 把研究设计转成安全、可缓存、可审计的执行计划；
用 Qlib / Daily Python / Primitive Materializer 作为不同 backend；
用 Archive / Consolidate 沉淀哪些生成逻辑真正有效。
```
