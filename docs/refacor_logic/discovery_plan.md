---
name: factor-discovery
description: 轻量 discovery 协议：把重复异常升级成 logic review 输入，而不是维护独立 discovery 子系统
user_invocable: true
---

# Discovery Management

## 1. 目标

`discovery` 仍然存在，但它不再被设计成一条重型独立链路。

它现在只负责一件事：

> 把重复出现、值得关注的异常或失败案例，轻量升级成 `logic review` 的输入。

它不负责：

- 直接 admit factor
- 直接创建新 logic
- 维护独立对象系统
- 经营一套低频、慢反馈的平行研究子系统

一句话：

`discovery` 不是独立研究引擎，而是失败案例升级机制。

它不解决“真正无假设的全字段 bottom-up exploration”。

如果未来要做那类探索，应被视为另一类系统能力，
不属于当前 discovery 协议范围。

---

## 2. 为什么要收缩 discovery lane

原来的重型 discovery lane 收益比不高。

原因很直接：

1. 异常来源本来就主要来自 `research_execute` 和 `research_judge`
2. 这些异常本来就会进入 batch summary、lessons、direction memory
3. 新增 `pattern_buffer + discovery_ledger + promote 协议` 的边际收益有限
4. 当前 batch 频率低，跨 batch 证据积累本来就慢

所以更合理的做法不是继续加对象，而是：

- 沿用 `search_ledger`
- 沿用 batch summary
- 沿用 `logic review`
- 只补“何时升级、如何升级”的轻量规则

---

## 3. 新定位

### 3.1 discovery 不再是独立通道

旧表述：

```text
discovery_scan -> pattern_buffer -> mechanism_review -> logic review
```

新表述：

```text
execute / judge anomaly
-> batch summary / search_ledger discovery candidate
-> next logic review
-> direction_candidate or logic_proposal
```

也就是说：

- 不再维护单独 `pattern_buffer` 生命周期
- 不再维护单独 `discovery_ledger`
- 不再为 discovery 开一套独立审查工作流

### 3.2 discovery 变成 logic review 的一个输入源

正式 proposal 来源现在分两类：

1. top-down proposal
2. bottom-up anomaly escalation

但二者都统一收敛到：

- `logic review`

---

## 4. 哪些异常值得升级

当前版本不再维护很多 discovery 类型。

只保留 3 个宽类别：

1. `repeated_residual_anomaly`
2. `repeated_near_miss_cluster`
3. `unexplained_family_edge`

这里的关键不是“有趣”，而是：

- 重复出现
- 结构一致
- 现有 logic 解释不干净

---

## 5. 不再新增独立存储对象

### 5.1 默认不再要求

- `storage/discovery/pattern_buffer.yaml`
- `storage/discovery/discovery_ledger.yaml`

### 5.2 改为复用现有对象

discovery 证据统一挂到：

1. `storage/ledger/search_ledger.yaml`
2. `storage/evidence/vault/batches/batch_XXX summary.md`
3. `logic review` 的 proposal 附录

推荐形式：

```yaml
discovery_candidates:
  - discovery_id: DC001
    source_batch_ids: [batch_041, batch_042]
    source_logic_ids: [L021]
    source_route_ids: [R021_01, R021_04]
    pattern_type: repeated_residual_alpha
    summary: "size-neutral residual alpha repeatedly survives in compression family edge cases"
    repeated_count: 2
    escalation_status: watch
```

discovery 只是 `search_ledger` 里的一个 section，
不是新的平行 memory 系统。

---

## 6. 升级规则

当前版本只保留两档：

### 6.1 Watch

适用于：

- 单次异常
- 或重复次数不足
- 或机制解释仍然太弱

动作：

- 写入 batch summary
- 写入 `search_ledger.discovery_candidates`

### 6.2 Escalate

适用于：

- 至少 `2` 个 batch 出现相似异常
- 现有 logic 解释明显吃力
- 或更像 current logic 内漏掉的重要切片

动作：

- 在下一轮 `logic review` 中作为：
  - `direction_candidate`
  - 或 `logic_proposal`
  的输入附录

也就是说，discovery 本身不再维护三段升级流水线。

---

## 7. 机制回溯也要轻量化

原来的 `mechanism_backtrace_review` 太重了。

现在只要求一份短说明，放在 escalation note 里，回答 4 个问题：

1. 这个异常可能对应什么行为机制
2. 是否可能只是风格残留
3. 是否只是已有 logic 的漏写切片
4. 为什么值得升格

推荐格式：

```yaml
escalation_note:
  likely_mechanism: "volume compression with delayed participation release"
  style_repackaging_risk: low
  explainable_by_existing_logic: partial
  escalation_reason: "repeated across 3 batches and 2 route variants"
```

这份 note 是 proposal 附录，不是独立流程对象。

---

## 8. discovery 的预算

discovery 不再单独经营预算。

保留的只有：

- `adjacent_discovery_route_quota`

也就是说，discovery 的主要资源消耗仍然体现在：

- `logic schedule` 给多少相邻探索预算

而不是再维护一套：

- `discovery_scan_budget`
- `pattern_buffer_budget`
- `promote_budget`

---

## 9. 与现有文档的关系

### 9.1 与 batch summary 的关系

batch summary 负责：

- 记录本轮异常
- 记录失败案例
- 记录 implementation learning

discovery 只负责回答：

- 哪些失败案例值得进入下轮 logic review

### 9.2 与 lessons 的关系

lessons / forbidden / implementation policy 负责：

- 记录不该再犯的错

discovery 负责：

- 记录“虽然失败了，但可能值得变成新研究方向”的异常

### 9.3 与 logic review 的关系

logic review 仍然是唯一正式入口。

discovery 不单独立项，只提供：

- `direction_candidate`
- `logic_proposal`

---

## 10. 最小可执行协议

对当前规模，discovery 只需要做到这 4 步：

1. 在 `execute / judge` 后识别是否有重复异常
2. 写入 batch summary
3. 同步到 `search_ledger.discovery_candidates`
4. 在下一轮 `logic review` 时决定：
   - ignore
   - watch
   - direction_candidate
   - logic_proposal

这已经够了。

---

## 11. 一句话结论

当前系统不需要一个重型 discovery lane。

更合适的做法是：

> 把 discovery 收缩成“重复异常升级机制”，复用 `search_ledger + batch summary + logic review`，而不是再维护一套低频、重对象、慢反馈的独立子系统。
