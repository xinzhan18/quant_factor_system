# 日内 Primitive 的 Skill 流程契约

> 日期：2026-05-02
>
> 状态：V0 已接入，继续作为 skill 流程契约
>
> 范围：说明日内 primitive 层如何接入当前 skill-based 5-phase 因子挖掘流程。

---

## 1. 背景

当前系统是 skill-based 流程，而不是单纯的 Python pipeline。

实际流程是：

```text
/factor-mine
  -> /factor-idea
  -> /factor-execute
  -> /factor-judge
  -> /factor-report
  -> /factor-consolidate
```

Codex 侧 bridge skills：

```text
quant-factor-mine
quant-factor-idea
quant-factor-judge
quant-factor-report
quant-factor-consolidate
```

这些 skill 桥接到 `.claude/skills/.../skill.md`，所以真实流程由以下部分共同驱动：

```text
skill instructions
Python CLI
storage/vault 状态
Phase artifacts
LLM packets
```

新增日内 primitive 层后，不能只改 Python。必须明确每个 skill 的输入输出契约怎么变化。

---

## 2. 总体原则

不改变 5-phase 主流程：

```text
START -> EXECUTE -> JUDGE -> ARCHIVE -> CONSOLIDATE
```

只增加一个 Pre-Phase2 契约：

```text
Phase1 manifest
  -> Pre-Phase2 MATERIALIZE primitives
  -> Phase2 EXECUTE daily evaluation
```

也就是说：

```text
/factor-idea
  允许提出或引用 primitive

/factor-execute
  在 Phase2 前确保 primitive 已物化

/factor-judge
  判决时能看到 primitive provenance 和时间语义

/factor-report
  admitted factor 报告里记录 primitive dependencies

/factor-consolidate
  总结 primitive family，而不只是 expression family
```

---

## 3. Manifest 契约变化

MVP 阶段不强制切换到完整 Factor IR。先扩展当前 manifest。

当前候选大致是：

```yaml
candidates:
  - candidate_id: C001
    source_type: dsl
    expression: Rank($amount)
```

新增后允许：

```yaml
candidates:
  - candidate_id: C001
    source_type: dsl
    expression: Rank($tail_amount_share_20m_v1)
    primitive_dependencies:
      - tail_amount_share_20m_v1
    hypothesis: "尾盘成交额占比高可能代表拥挤交易，次日存在反转风险。"
```

如果 Phase1 提出一个新 primitive，manifest 可以包含：

```yaml
proposed_primitives:
  - feature_id: tail_amount_share_20m_v1
    source_type: minute_bar
    source_freq: 1min
    output_freq: daily
    template: window_share
    params:
      field: amount
      numerator_window: "14:40-15:00"
      denominator_window: "09:30-15:00"
    time_semantics:
      available_time: "T 15:00"
    data_policy:
      min_bar_ratio: 0.8
```

MVP 可先要求 `primitive_dependencies` 必须引用 registry 中已存在的 primitive。`proposed_primitives` 可以作为 V1/V2 能力。

---

## 4. /factor-idea 契约

### 当前职责

```text
选择方向
生成候选表达式
冻结 manifest
```

### 新增职责

`/factor-idea` 可以设计两类内容：

```text
1. daily expression
   例如 Rank($tail_amount_share_20m_v1)

2. primitive dependency
   例如 tail_amount_share_20m_v1
```

它不直接写原始分钟处理代码。

### 输出要求

每个引用 primitive 的候选必须包含：

```text
primitive_dependencies
hypothesis
expected_sign 或方向解释
```

示例：

```yaml
candidates:
  - candidate_id: C001
    source_type: dsl
    expression: Rank($tail_amount_share_20m_v1)
    primitive_dependencies:
      - tail_amount_share_20m_v1
    hypothesis: "尾盘成交额占比高反映收盘前拥挤或冲击交易，未来可能反转。"
    expected_sign: negative
```

### Phase1 packet 需要补充

给 LLM 的 idea packet 应包含：

```text
可用 primitive 列表
每个 primitive 的一句话机制
source_freq / available_time
过去表现摘要
相关方向或已 admit factor
```

避免 LLM 每轮重新发明同一个 primitive。

---

## 5. /factor-execute 契约

### 当前职责

```text
读取 manifest
构造 Phase2Inputs
调用 run_phase2()
写 result.yaml
```

### 新增 Pre-Phase2 步骤

在现有 `build_phase2_inputs()` 之前或内部新增：

```text
ensure_primitives_materialized(manifest, paths, config)
```

执行内容：

```text
1. 收集 candidates[].primitive_dependencies
2. 解析 storage/vault/primitive_registry
3. 检查 primitive cache 是否覆盖 train/validation range
4. 缺失或过期时批量 materialize
5. 导出到 isolated Qlib daily store
6. 记录 materialization summary
```

当前实现位置：

```text
src/research/compute/data_bridge.py
  build_phase2_inputs()

src/research/compute/primitive_bridge.py
  collect_primitive_dependencies()
  ensure_primitives_materialized()
```

执行配置来自 `storage/config.yaml`：

```yaml
primitive:
  minute_parquet: /path/to/clean_minute.parquet
  qlib_data_dir: /path/to/qlib_with_primitives
```

`minute_parquet` 可以为空；为空时，如果 primitive cache miss，则本轮会失败并提示需要配置分钟数据源。

### result.yaml 建议新增字段

```yaml
primitive_materialization:
  qlib_data_dir: "~/.qlib/qlib_data/cn_data_1d_exp"
  features:
    tail_amount_share_20m_v1:
      status: cache_hit
      spec_hash: "..."
      available_time: "T 15:00"
      source_freq: 1min
    reverse_imp_pos_v1:
      status: materialized
      spec_hash: "..."
      rows: 1234567
```

V0 实际还会在每个 candidate 下写：

```yaml
candidates:
  - candidate_id: C001
    primitive_dependencies:
      - tail_amount_share_20m_v1
    primitive_provenance:
      tail_amount_share_20m_v1:
        status: cache_hit
        spec_hash: "..."
        available_time: "T 15:00"
```

Phase2 指标仍然保持现有 daily result schema。

---

## 6. /factor-judge 契约

### 当前职责

```text
读取 result.yaml / candidate packet
结合 checkpoint 进行判决
写 judge.md
```

### 新增判断维度

Judge packet 必须展示：

```text
primitive dependencies
primitive construction summary
available_time
allowed_label
cache/materialization status
是否存在未来函数风险
是否与传统换手/波动/市值暴露高度相关
```

### 新增检查问题

`/factor-judge` 需要回答：

```text
1. primitive 的日内逻辑是否与 hypothesis 一致？
2. available_time 是否晚于 label 的 decision_time？
3. 这个 primitive 是真正新增信息，还是只是换手率/波动率 proxy？
4. daily expression 是否过度简单但仍合理？
5. 如果有效，应该 admit primitive family 还是 admit 当前 factor 组合？
```

### judge.md 建议新增段落

```markdown
## Primitive Provenance

- `tail_amount_share_20m_v1`
  - source: 1min amount
  - construction: tail 20m amount / full-day amount
  - available_time: T 15:00
  - spec_hash: ...
  - risk: may proxy turnover / liquidity
```

---

## 7. /factor-report 契约

### 当前职责

```text
对 admitted candidate 写 factor.md / factor.yaml
```

### 新增归档字段

`factor.yaml` 建议增加：

```yaml
primitive_dependencies:
  - feature_id: tail_amount_share_20m_v1
    source_type: minute_bar
    source_freq: 1min
    output_freq: daily
    template: window_share
    spec_hash: "..."
    available_time: "T 15:00"
```

`factor.md` 建议增加：

```markdown
## Primitive Dependencies

### tail_amount_share_20m_v1

- Source: 1min amount bars
- Construction: tail 20m amount divided by full-day amount
- Availability: T 15:00
- Expected mechanism: tail crowding / reversal
- Known risk: liquidity and turnover exposure
```

### Primitive Card

每个 primitive 也应该有自己的 LLM-readable card：

```text
storage/vault/primitive_registry/minute/tail_amount_share_20m_v1.md
storage/vault/primitive_registry/minute/tail_amount_share_20m_v1.yaml
```

YAML 给 Python 读，MD 给 LLM 读。

---

## 8. /factor-consolidate 契约

### 当前职责

```text
整理 directions、lessons、factor memory
```

### 新增总结对象

Consolidation 需要总结：

```text
1. 哪些 primitive family 有效
2. 哪些 primitive family 只是换手/波动 proxy
3. 哪些窗口有效：open_10m / open_30m / tail_20m / tail_30m
4. 哪些字段有效：amount / volume / return / volatility
5. 哪些 mask 有效：ret>0、ret<0、volume_up、amount_up
6. 哪些 smoothing 有效：raw / MA5 / EWMA15
```

可以在 memory 中增加：

```text
Primitive Families
  window_share
  window_ratio
  masked_return_mean
  intraday_distribution_stats
  price_volume_corr
```

---

## 9. Primitive Design Card 规范

每个 primitive 的 MD 卡片建议格式：

```markdown
# tail_amount_share_20m_v1

## Hypothesis

尾盘成交额占比高可能代表收盘前拥挤交易、流动性冲击或资金被迫成交，未来存在反转风险。

## Construction

Use 1min amount bars. For each date and symbol:

```text
tail_amount_share_20m =
  Sum(amount from 14:40 to 15:00) / Sum(amount from 09:30 to 15:00)
```

## Availability

Available after T 15:00. Safe for T+1 close-to-close labels.

## Expected Sign

Higher value is expected to predict lower future return.

## Known Risks

- May proxy turnover or liquidity.
- Sensitive to closing auction/session definition.
- Needs neutralization and redundancy check.

## Related Reports

- 华安证券：高频视角下成交额蕴藏的 Alpha，APL20 尾盘成交额占比。
```

---

## 10. Skill 文件后续需要更新的位置

后续实现时需要同步更新：

```text
.claude/skills/factor-idea/skill.md
  允许 primitive dependency / primitive proposal

.claude/skills/factor-mine/skill.md
  在 EXECUTE 前加入 Pre-Phase2 materialization

.claude/skills/factor-judge/skill.md
  judge packet 和检查项加入 primitive provenance / leakage

.claude/skills/factor-report/skill.md
  factor report 加 primitive dependencies

.claude/skills/factor-consolidate/skill.md
  memory consolidation 加 primitive family 总结
```

Codex bridge skills 不应另写业务规则，只继续桥接 source-of-truth skill。

---

## 11. 总结

日内 primitive 层不会推翻现有 skill-based 5-phase 流程。

它改变的是每个 phase 的契约：

```text
START:
  从只生成 Qlib DSL，扩展为引用/提出 primitive + daily expression

EXECUTE:
  增加 Pre-Phase2 materialization

JUDGE:
  增加 primitive provenance、时间语义、未来函数风险判断

ARCHIVE:
  归档 primitive dependencies 和 spec_hash

CONSOLIDATE:
  总结 primitive family 的有效性
```

最终目标：

```text
LLM 研究重点从“写复杂日频 Qlib DSL”
扩展为“设计可复用的日内 daily primitive，并用简单日频表达式评估”。
```
