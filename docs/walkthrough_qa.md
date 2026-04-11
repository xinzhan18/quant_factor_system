# Factor System Walkthrough — Q&A Log

本文档记录在系统流程梳理过程中提出的**有价值问题**（即那些暴露真实设计空白、约束不清或执行漏洞的问题），以及对应的可行解决方案。只记"值得留下来"的问题——纯概念性疑问不入档。

每条记录结构：
- **Q**: 原始问题（尽量保留原话）
- **发现**: 这个问题暴露的真实现象（带证据）
- **为什么重要**: 不修会怎样
- **可行方案**: 具体、可落地的修复方向（不绑定时间）

---

## Q1 — manifest.yaml 与 idea_report.yaml 是什么关系？为什么同时存在两个？

**提问时间**: 2026-04-11
**相关阶段**: Phase 1 `/factor-idea` 产出

### 发现

设计上两者是刻意分离的：
- `manifest.yaml` 是**下游执行合同**（execute / validate / finalizer 读）
- `idea_report.yaml` 是**上游决策审计**（reflect 读 / 元分析读）
- 两者服务不同读者，内容不重叠：manifest 存"跑什么"，idea_report 存"为什么跑这个"。

但是，扫描 `storage/batches/batch_001..103`（2026-04-11）：

| batch | manifest | idea_report |
|---|---|---|
| batch_001 | ✅ | ✅ |
| batch_050 | ✅ | ❌ |
| batch_080 | ✅ | ✅ |
| batch_100 | ✅ | ❌ |
| batch_102 | ✅ | ❌ |
| batch_103 | ✅ | ❌ |

**最近几个 batch 的 idea_report 全部丢失**。skill.md 里"必须写"的约束在代码层没有任何强制校验——纯粹靠 LLM 自觉。

### 为什么重要

1. **reflect 下一轮失去决策过程证据**：reflect 本应通过 idea_report 知道"上一轮为什么选 deepen 而不是 broaden"、"为什么挑 T001 不挑 T002"。丢了之后，reflect 只能用 judge_report 倒推——但 judge_report 记的是"结果是否通过"，不是"决策是否合理"。两者不等价。
2. **元分析无法进行**："过去 30 batch 里 deepen 决策中 active_thread_has_clear_probe 出现了多少次" 这类问题需要 idea_report 才能回答，manifest 没有对应字段。
3. **静默失败**：idea_report 丢了，系统照常往下跑，没有任何警告。等哪天想复盘才发现数据没了。

### 可行方案

**方案 A（最小修复，推荐）**：在 `/factor-execute` 启动前，`validate_manifest_against_logic_cards()` 增加一条检查——对应 batch 目录下必须存在 `idea_report.yaml`，否则 execute 拒绝跑。把"自觉约束"升级为"硬门槛"。
- 实现位置：`src/research/execute/precheck.py` 或 `validate_manifest_against_logic_cards`
- 附带代价：如果 idea_report 缺失，需要给 LLM 一个明确的回写指令或允许一次性"reconstruct from manifest + card"

**方案 B（更严）**：`/factor-idea` 在 Step 7 把 manifest 和 idea_report **原子写入**——要么两个都写成功，要么都不写。防止 manifest 已写、idea_report 没写这种中间态。

**方案 C（辅助）**：加一条 consistency check 脚本，定期扫 `storage/batches/*` 报告缺失的 idea_report。不阻塞主流程，只报告。

---

## Q2 — `ledger.yaml` 的 `batch_usage` 在干什么？

**提问时间**: 2026-04-11
**相关阶段**: Phase 1 Step 8 + Phase 3 judge 读取

### 发现

`batch_usage` 是 ledger 5 个 section 之一（另四个：`global_escalations` / `holdout_reviews` / `search_ledger` / `write_audit_log`），本质是一张"validation budget 使用记录表"。

每条记录的核心字段：
```yaml
batch_XXX:
  candidate_count: 7                # 本 batch 用掉的 candidate slot 数
  holdout_used: true/false          # 是否动过 holdout 数据
  validation_window_id: val_2022_2023  # 哪一段 validation 被使用
  train_range: [...]
  validation_range: [...]
  phase: frozen/executed/judged/finalized
  logic_ids: [L001, ...]
```

**它在防的问题是多重检验（multiple testing）**：
- 102 个 batch × ~6 candidate = ~600 次在同一段 validation 上的独立检验
- 按 α=0.05，纯随机情况下能见到 ~30 个"显著"因子
- `batch_usage` 是 judge 做 Bonferroni / FDR 校正的分母

### 为什么重要

没有这张表，judge 的 `multiple_testing_risk_bucket` 无法计算。结果是：
- ICIR=0.25 这种 borderline 信号会被误判为强信号
- 长期积累下所有 admit 的因子都可能是假阳性
- 录取门槛随系统运行时间漂移，早期录取标准和后期不一致

**但这里有一个真问题**：我看到 batch_001 `holdout_used: true`，batch_002+ 全部 false。这说明 holdout 使用计数功能是**存在的**，但没有对应的"holdout 污染度"反馈机制——`holdout_used=true` 的累计次数并没有被哪里读取来升高后续 batch 的 evidence_threshold。换句话说，**记账有了，但记账的用处没落地**。

### 可行方案

**方案 A**：在 judge 层增加 `holdout_contamination_factor` 计算。每次 `holdout_used=true` 累计一个"污染度 +1"，达到阈值（比如 10 次）后，后续所有 batch 的 admit 门槛自动升高一档。实现时机：`src/research/judge/candidate_judge.py` 里读取 ledger 的部分。

**方案 B**：在 `/factor-judge` skill 每次启动时显式打印 "当前已消耗 validation budget X/Y" 给 LLM 看，让 LLM 自己在叙述性裁决中体现多重检验惩罚。低成本、软约束。

**方案 C（最彻底）**：引入真正的"validation 窗口滚动"——ledger 里 `validation_window_id` 字段已经存在但从未换过值（全是 `val_2022_2023`）。设计上应该允许在累计使用 N 次后切换到新窗口（比如 `val_2023_2024`），强制刷新检验分母。代价是需要重新评估历史因子。

### 关联观察

`batch_usage` 和 `search_ledger` 两个 section 看起来职责有重叠——一个记"batch 用量"，一个记"搜索次数"。需要后续梳理它们到底谁是 multiple testing 的权威计数器。（作为后续待核问题留档。）

---

## Q3 — candidate 里的 `lineage` 字段到底在干什么？谁读谁写？

**提问时间**: 2026-04-11
**相关阶段**: Phase 1 `/factor-idea` Step 6 candidate expansion / Phase 3 judge

### 发现

系统里有**两个**都叫 lineage 的东西，作用、读者、治理完全不同：

**(A) `experiment_lineage_tag` (ELT)** — 一个字符串
- 格式：`ELT_{logic_id}_{route_type}_{mechanism}_{conditioning}_{family}_v{N}`
- 有完整的 dataclass（`src/research/domain/experiment_lineage.py::ExperimentLineageTag`）
- 有 `generate / parse / next_version` 一套 API
- **代码层真读**：manifest_validator（genesis guard）、route_judge（promote_family 判定）、judge_packet_builder、pipeline 透传、holdout_queue 存字段
- 粒度：一个 route 一个 ELT，粗粒度，跨 batch 追踪实验脉络

**(B) `lineage` dict** — 一个嵌套字典
- 结构：`{parent_expression, parent_factor_id, transformation}`
- 在 100+ 个 batch manifest 里存在（grep 计数）
- 每个 candidate 自己一份，细粒度
- **代码层完全不读** —— grep `parent_expression` 在 src/ 下零结果。只出现在 manifest YAML 和 registry YAML 里。
- 只有 LLM 自己读（下一轮 /idea 复用、reflect 写叙事、复盘者追溯）

### 问题 3.1：Schema 分裂（核心问题）

Python dataclass `domain/schema.py::Lineage` 定义的字段：

```python
@dataclass
class Lineage:
    parent_logic: str = ""
    parent_experiment_tags: List[str] = field(default_factory=list)
    parent_routes: List[str] = field(default_factory=list)
    parent_factors: List[str] = field(default_factory=list)
    mutation_type: str = "genesis"
```

YAML 实际写入的字段：
```yaml
lineage:
  parent_expression: "..."       # dataclass 里没这个
  parent_factor_id: null         # dataclass 是 parent_factors (列表)
  transformation: "..."          # dataclass 里没这个，只有 mutation_type
```

**两套完全不同的字段**。既不是命名差异也不是子集关系，是两套独立设计从未对齐。

成因：因为没有代码读 `lineage` dict，所以没人触发反序列化错误，schema 不一致不会被发现；反之，正是 LLM 自由写 YAML 形成了事实 schema，替代了 dataclass 定义。

### 问题 3.2：没有任何代码读 `lineage` dict

`pipeline.py:66-70` 和 `:157-161` 在把 manifest 转成 evidence dict 时，只拷贝这些顶层字段：
```python
{
    "logic_id": candidate.get("logic_id"),
    "route_id": candidate.get("route_id"),
    "experiment_lineage_tag": candidate.get("experiment_lineage_tag"),
    "family_id": candidate.get("family_id"),
    "route_type": candidate.get("route_type"),
    ...
}
```

**`candidate.get("lineage")` 完全没出现**。lineage dict 是纯 write-only 的"LLM 间通讯通道"。

### 问题 3.3：parent_expression 没有任何校验

`parent_expression` 里写的是一整串 DSL 字符串。没有 parser 去校验：
- 它是不是语法合法的 DSL
- 它是不是真的在过去某个 batch 里出现过
- 它和当前 candidate 的 expression 差异是不是和 `transformation` 字段声称的一致

LLM 可以偷懒填错、填 null、甚至虚构一个"父表达式"——系统完全不会报警。

### 问题 3.4：ELT 和 lineage dict 语义有重叠但没有互校

`lineage.parent_expression` 应当能对应到上游某个 candidate，而那个 candidate 本该有自己的 ELT。两条信息本来可以 cross-check：
- "C001 声称 parent_expression 是 X"
- "X 在 batch_102 里是 C004，属于 ELT_L015_mutate_pb_ps_conditioning_v1"
- "C001 的 ELT 是 ELT_L015_mutate_pb_ps_conditioning_v2 → 合理（v1 → v2）"

但系统里没有任何地方做这个对齐。ELT 和 lineage dict 完全脱节，作为两条独立的"记账系统"并行存在。

### 为什么重要

1. **溯源能力其实是假的**：表面上"每个 candidate 都能追溯到父表达式"，但这个字段完全靠 LLM 自律维护，没有任何校验。一旦 LLM 写错或漏写，溯源链就断了。
2. **无法做重复实验检测**：batch_103 里 C003 和 batch_102 C003 是**完全相同的表达式字符串**——如果 parent_expression 有一个反向索引或校验（"如果某个候选的 expression 和过去某个 batch 的 expression 完全相同，必须把那个 batch 的 candidate_id 写进 parent_factor_id 并给出 reason_for_reprobe"），batch_103 C003 就会被挡下。现在没这个。
3. **Schema 分裂会污染未来迁移**：以后如果想把 lineage 数据用起来（比如做 family tree 可视化），会发现 YAML 里的字段和 dataclass 对不上，需要先做一次清洗/迁移。

### 可行方案

**方案 A（最小修复）**：让 `domain/schema.py::Lineage` 和 YAML 对齐。要么改 dataclass 字段，要么改 YAML 写法，**选一边**，保证两边字段名一致。建议改 dataclass，因为 100+ 历史 batch YAML 改不动。

**方案 B（增加校验）**：在 `/factor-idea` Step 7 写 manifest 前，对 lineage dict 做 sanity check：
- 如果 `parent_expression` 非空，必须和 `transformation` 字段一起出现
- 如果 `parent_factor_id` 非空，必须是 registry 里真实存在的因子 id
- `parent_expression` 必须是语法合法的 DSL（复用 precheck 的 parser）

**方案 C（治理级，真正有用）**：引入 **expression hash → batch/candidate 反向索引**。每次 /idea 冻结 candidate 前，对 `expression` 字符串计算 hash，在一个全局表里查：如果 hash 已存在 → 要求 LLM 显式填写 `parent_batch_id`、`parent_candidate_id`、`reason_for_reprobe`。这一条能彻底防止"同一表达式手工重投"（batch_103 C003 案例）。实现成本：一个简单的 `expression_index.yaml`，每轮 finalize-batch 时 append。

**方案 D（可选）**：把 ELT 和 lineage dict 在 execute 阶段做一次 cross-check——如果 `parent_expression` 能在历史找到对应 candidate，那个 candidate 的 ELT 必须和当前 candidate 的 ELT 在"同一族"（比如只差 version 号）。不匹配就 warn。

### 优先级

C > A > B > D。方案 C 是真正能帮"重新思考"链路闭环的动作，同时直接解决 batch_103 C003 问题。方案 A 纯粹是代码卫生。

---

## Q4 — 有没有机制防止"同一表达式换个 rationale 重投"？

**提问时间**: 2026-04-11（从 Q3 派生出的独立问题）
**相关阶段**: Phase 1 `/factor-idea` precheck + Phase 2 execute 前置校验

### 发现

batch_103 C003 的表达式：
```
Mul(CsRank(Sub(Div($close,$pe_ratio),Div(Ref($close,60),Ref($pe_ratio,60)))),CsRank(Mul($ps_ratio,-1)))
```

和 batch_102 C003 **完全相同**（字符字节级相同）。manifest 里 C003 的 rationale 自己承认是重投：
> "Same expression as batch_102 C003 (risk=borderline, crowd=medium). Re-evaluated here ... If the crowding was specific to the batch_102 evaluation window, fresh evaluation may show crowd=low."

现有校验机制：
- `precheck.py` 校验：DSL 语法 / 算子白名单 / 字段白名单 / forbidden pattern
- `manifest_validator.validate_manifest_against_logic_cards()`：thread 活性 / family guard / avoid patterns
- **都没有 "同一表达式是否在过去 N 个 batch 内出现过" 的检查**

所以 C003 这种操作完全合法，系统照常跑。

### 为什么重要

1. **multiple testing 防线被绕过**：`search_ledger` 和 `batch_usage` 计数只看"冻结了多少候选"，不看"这些候选是不是同一个表达式在换窗口重测"。同一表达式在两个不同 validation 窗口上分别过门槛，等于做了两次独立检验——每次都消耗一份 α 预算，但两次之间的相关性被忽略了。
2. **Reserve → Reject → 重投** 的退路被打通：一个候选被 reserve 过，没被 admit，LLM 下一轮手抄一遍当新候选继续尝试。没有次数限制。
3. **和 Q3 方案 C 是同一个修复点**：本质上都是"需要一个 expression → 历史 batch 的反向索引"。

### 可行方案

**方案 A（推荐，和 Q3 方案 C 合并）**：维护一个 `storage/state/expression_index.yaml`，每轮 finalize-batch 时把当前 batch 所有 candidate 的 `(expression_hash, batch_id, candidate_id, verdict)` append 进去。precheck 阶段：
- 计算新 candidate 的 hash
- 在索引里查过去 N 个 batch 的记录
- 若命中：
  - 若之前是 reject → 拒绝本次冻结（明确的 reject 后再投需要理由）
  - 若之前是 reserve → 必须填 `reason_for_reprobe` 字段，说明"这次哪里不一样"（新评估窗口？新 holdout？等）
  - 若之前是 admit → 直接拒绝（已经是 F0XX 了）

**方案 B（更严，不推荐）**：直接禁止同一 expression 在 N batch 内重投。代价是失去"评估窗口切换后真诚重评"的能力。

**方案 C（辅助）**：表达式归一化再 hash——对 DSL AST 做语义归一化后再算 hash，这样 `Mul(A,B)` 和 `Mul(B,A)` 会被识别为同一表达式。实现成本高，但能防止 LLM 通过微调顺序绕过。

### 优先级

A 必做，和 Q3 方案 C 合并实现。B 不推荐。C 可以后续加强。

---

## Q5 — batch 之间强耦合是问题吗？batch 边界的 6 条价值在什么情况下失效？

**提问时间**: 2026-04-11
**相关阶段**: 整个 batch 生命周期 / reflect 触发条件 / ELT 版本升级

### 提问的原始直觉

> "既然下一个 batch 的设计依赖上一个 batch 的结果，那 batch 之间是不是强耦合？那为什么还要用 batch 这个分割？直接连起来变成一条无限流不就行了？"

### 结论先行

**batch 抽象是必要的**，它做了 6 件没它就做不了的事。**但是，batch_099–103 这种强耦合的模式会让这 6 条价值被严重削弱**——问题不在抽象本身，而在"系统当前没有利用 batch 边界强制重置"。

### batch 提供的 6 条价值

1. **冻结纪律**：LLM 必须在不看 validation 结果的前提下一次性决定本轮跑哪 6 个候选。没有 batch 边界就没有"看不到结果"这个约束，会退化成边看边改的 p-hacking。
2. **多重检验分母**：`batch_usage` 以 batch 为单位累计检验次数，judge 做 Bonferroni/FDR 校正。candidate 级粒度太细（同 route 高度相关），expression 级无法定义"相似即同一次检验"。
3. **Holdout review 边界事件**：holdout 复审只在 batch 之间发生——这是 "决胜局时刻"。没有边界就没有自然的触发点。
4. **Reflect 同步点**：元认知更新需要"一组证据"作为输入单位，batch 天然提供这个单位。per-candidate reflect 没有跨候选比较基础；全流式 reflect 不知道何时运行。
5. **状态机转换原子性**：logic card 的 status 变更只在 finalize-batch 发生，避免状态机因单次 verdict 抖动。
6. **可恢复性**：`current_batch + current_batch_phase` 两个字段就能精确定位恢复点，git commit / state checkpoint 天然对齐。

### 但耦合度失控时，这 6 条价值被部分失效

对照 batch_099–103 的实际情况：

| 价值 | 正常情况 | batch_099–103 的实际情况 |
|---|---|---|
| 冻结纪律 | 强 | **弱**——5 个 batch 都在 L015 同一条 ELT 上微扰，LLM 冻结前已经有预判 |
| 多重检验分母 | 强 | **弱**——5 个 batch 强相关，不是独立检验；分母被高估，门槛被低估 |
| holdout review 边界 | 中 | **弱**——代码层 bug 导致几乎无人使用（见 Q2 / 前面 reserve 分析） |
| reflect 同步点 | 强 | **中等**——reflect 跑了但输入几乎一样，belief delta 很小 |
| 状态机转换 | 强 | **中等**——5 个 batch 里 L015 status 只变了 active → productive 一次 |
| 可恢复性 | 强 | **强**（和耦合度无关）|

### 深层观察

**batch 之间的耦合度本身是一个可测量的信号**：
- **低耦合** = 探索模式（每个 batch 尝试新方向）
- **高耦合** = 精炼模式（同一方向多轮迭代）

batch_099–103 是**极端精炼模式**，但系统里**没有任何机制测量这个耦合度**，也没有任何触发器在耦合过高时强制切换到探索模式。结果就是"浅呼吸" × 5，表面上有 5 个 batch 边界，实质上等于 1 个超大 batch。

### 为什么重要

1. **batch 边界是纪律的载体**。当它被"滥用"成行政手续（每 batch 只在做同一件事的微扰），系统等同于丧失冻结纪律和多重检验防线。
2. **reflect 在这种模式下产出极小的 belief delta**，等于变相失效。
3. **系统无法自知**：目前没有任何代码或 metric 在报告"最近 5 个 batch 高度耦合"——LLM 和人类都要靠肉眼观察才能发现。

### 可行方案

**方案 A（推荐）：ELT 连续性监控**
引入 metric `elt_stagnation_count`：同一 ELT 在连续 N 个 batch 未产生 `.next_version()` 升级，计数 +1。达到阈值（如 3）时：
- reflect 层强制写入一条 `global_escalation` 条目
- 下一轮 /factor-idea 在消费 escalation 时必须应对
- 实现位置：finalize-batch 时扫描最近 N 个 batch 的 ELT，计算升级率

**方案 B（推荐）：logic 轮换配额**
`factor-mine` Phase 0 读 state 后增加一条：同一 logic 连续被挖 ≥ K 次（推荐 K=4）且无新 admit → 当前轮必须从 `schedulable_logic_ids` 里选**不同**的 logic，如果 schedulable 只有一条则强制 escape（创建新 logic 或标记 saturated）。
- 直接防止 L015 这种"唯一出路被反复压榨"的局面
- 实现位置：`src/research/logic/scheduler.py` 增加轮换惩罚项

**方案 C（辅助）：新颖度分（novelty score）**
对每个 batch 的候选集合与前 N 个 batch 的候选集合做 expression distance 计算（DSL AST 距离或 token 集合 Jaccard）。距离过低 → 本 batch 标记为 `low_novelty`。连续 `low_novelty` → 触发同方案 A 的 escalation。
- 比 ELT 更细粒度，能捕捉"换了 ELT 但表达式几乎一样"的规避行为
- 实现成本较高，作为 A 的补强

**方案 D（辅助）：batch 耦合度可视化**
纯报表：每轮 finalize-batch 时在 `storage/state/coupling_dashboard.yaml` 写入最近 10 个 batch 的 (logic_id, ELT, novelty_score)。不阻塞流程，只给人类 / LLM 看。低成本高价值。

### 优先级

B > A > D > C。方案 B 是最直接能打破当前 batch_099–103 僵局的机制。方案 A 是长期稳定的结构性监控。方案 D 是低成本的观测基础设施，可以先于 A/B 落地。方案 C 实现复杂，可以作为后期加强。

### 关联观察

这条问题的解决和 Q4（表达式重投检测）是**互补**的：
- Q4 从 expression hash 层面挡住"同一字符串重投"
- Q5 从 ELT / logic 层面挡住"同一思路反复投"

两者都修才能真正恢复 batch 边界的纪律价值。

### 入档理由

这不是一个"代码 bug"问题，而是**关于研究节奏的元观察**——但它指向的几个可操作机制（ELT 连续性监控、logic 轮换配额、新颖度分、耦合度面板）是实打实可以写代码实现的。所以作为治理级改造入档。

---

## Q6 — `storage/batches/*/artifacts/` 为什么有的 batch 有、有的没有？

**提问时间**: 2026-04-11
**相关阶段**: Phase 2 `/factor-execute` 的 `_save_artifacts` + Phase 4 `/factor-report` 的 `_try_load_signal_artifact`

### artifacts 是什么

每个 `artifacts/CXXX/` 目录下有 2 个文件：
- `metadata.yaml` — batch_id / candidate_id / expression / time_start / time_end / row_count
- `signal_flat.parquet` — 原始因子信号，约 200-300 万行的扁平表 `(time, instrument, factor_value)`，每个文件几十 MB

**用途**：`src/report/builder.py:85` 会在生成 factor report 时调用 `_try_load_signal_artifact`，命中缓存直接读 parquet（几秒），未命中 fallback 到 Qlib 重新 evaluate 表达式（5-8 分钟）。纯性能优化，不是功能依赖。

### 有/没的真实状态（2026-04-11 扫描）

| batch 范围 | artifacts 情况 | 原因 |
|---|---|---|
| batch_001 – batch_069 | 全部没有 | 代码层 `_save_artifacts` 功能在 batch_070 前后才加入 |
| batch_070 – batch_102 | 全部有 | 代码已就位且正常 execute |
| batch_103 | 没有 | 刚冻结 manifest，还没 execute |

**"没有"至少有 5 种语义**，全部合法或半合法：
1. 还没 execute（正常）
2. 代码版本早于 batch_070（历史遗留）
3. 所有候选都 precheck fail
4. 候选是 Python source 类型 → `multiindex_to_flat` 转换静默失败（`pipeline.py:256` 的 `except: pass`）
5. execute 跑完但 `_save_artifacts` 抛异常

### 问题 6.1：Python source 候选会被静默丢弃

`pipeline.py:253-257`：
```python
try:
    from core.factor_stats import multiindex_to_flat
    signal_artifacts[cid] = multiindex_to_flat(base["base_signal"])
except Exception:
    pass  # non-standard signal format (e.g. Python source)
```

Python source 类型的候选（dsl_naturalness=low 时使用）**永远不会有 artifact**。这意味着：
- Python 类型候选的 report 必须每次从头重算
- 没有任何警告或日志——silent feature gap
- LLM 下一轮 /idea 看到"这个 logic 的候选都没 artifact"会以为是版本问题，不会意识到是类型问题

### 问题 6.2：artifacts 没有 TTL，也没有 GC

batch_070–102 大概 30 个 batch 都有 artifacts：
- 每个 batch 平均 6 个候选 × 每个 ~20-50 MB parquet = **每 batch 几百 MB**
- 30 个 batch 累计 **几个 GB**
- **大多数候选最终被 reject**——它们的 artifact 永远不会被 report builder 读取
- 但 artifact 依然占着磁盘

代码中没有任何 GC：
- `finalize-batch` 不会清理 rejected 候选的 artifact
- 没有 TTL 策略
- 没有磁盘占用监控

### 问题 6.3：表达式不匹配是"静默降级"

`builder.py:325-332`：
```python
if meta["expression"] != artifact_meta["expression"]:
    logger.warning("Artifact expression mismatch, skipping: %s", path)
    return None
```

如果 factor 的 registry YAML 里的 expression 和 artifact metadata 里的不一致（比如后续做了括号归一化、空格修改等），artifact 会被跳过，改用 Qlib 重算。**这只产生 warning，不抛错**——用户不看日志就不知道缓存没命中，只会觉得 "report 怎么又跑了 8 分钟"。

### 问题 6.4：metadata.yaml 信息不完整

扫 `batch_102/artifacts/C001/metadata.yaml`：
```yaml
batch_id: batch_102
candidate_id: C001
expression: "..."
name: C001
row_count: 2674000
source_type: dsl
time_start: '2015-01-05 00:00:00'
time_end: '2025-12-31 00:00:00'
generated_at: '2026-04-10T05:33:01.286234'
```

**缺少的字段**：
- `logic_id` — 无法反推"这是哪条假设的产物"
- `sample_policy_version` — 如果采样策略版本变了，缓存应该失效，但没记这个版本
- `qlib_data_version` — 如果底层数据刷新了，缓存应该失效，但也没记
- `expression_hash` — 用于和 Q4 的 expression_index 对齐

这导致 artifact 的"有效性"只能靠字符串比对 expression，无法对齐更深层的环境变更。

### 为什么重要

1. **磁盘占用失控**：累计 GB 级的 artifact 没人清理，长期运行会把磁盘打爆。
2. **缓存一致性脆弱**：只靠 expression 字符串比对，底层数据刷新 / 采样策略变化都不会触发失效，可能导致 report 用陈旧数据而不自知。
3. **Python 候选的隐式降级**：Python 类型候选永远无缓存且无警告，用户无法知道这条限制。
4. **半合法的多义性**："没有 artifacts" 有 5 种可能原因，运维排错时要人肉区分——应当有一个 `execute` 阶段的状态字段记录"artifact 是否应该存在"。

### 可行方案

**方案 A（GC，必做）**：在 `finalize-batch` 之后，对本 batch 内所有 verdict=reject 的 candidate，删除对应的 artifact 目录。admit/reserve 保留。实现位置：`src/research/storage/finalizer.py` 新增 `_gc_rejected_artifacts` 方法。
- 优点：直接解决磁盘占用问题
- 代价：几乎零（只删已确认不用的数据）

**方案 B（元数据增强）**：`_save_artifacts` 写 metadata.yaml 时增加 `logic_id / sample_policy_version / qlib_data_version / expression_hash` 字段。
- 优点：让缓存失效机制更准确
- 代价：小（只加字段）

**方案 C（状态字段）**：在 `research_result.yaml` 里为每个 candidate 加一个 `artifact_status` 字段：`saved / skipped_python / skipped_precheck_fail / skipped_error`。这样运维时可以直接查 research_result 回答"为什么这个候选没 artifact"，不用猜。
- 优点：消除"5 种语义"的多义性
- 代价：小

**方案 D（Python 候选支持，可选）**：给 Python source 类型候选也实现一套 artifact 序列化路径。评估价值不高——Python 候选本来就是 dsl_naturalness=low 时的备胎，数量很少。
- 优先级低

### 优先级

A > C > B > D。A 是直接省磁盘的操作性修复，C 是运维友好性提升，B 是正确性保障，D 可以后期再考虑。

---

## Q7 — runtime/cache 和 batches/*/artifacts 为什么是两套独立缓存？FactorValueCache.cleanup 其实没在工作

**提问时间**: 2026-04-11
**相关阶段**: Phase 2 `/factor-execute` 内部 compute + Phase 4 `/factor-report`

### 两套缓存的对比

| 维度 | `storage/runtime/cache/research/` | `storage/batches/*/artifacts/` |
|---|---|---|
| 类名 | `FactorValueCache` (`compute/cache.py`) | 无专门类（`batch_runner._save_artifacts`）|
| 粒度 | **子表达式级别**（memoization）| **完整 candidate 级别**（finalization）|
| key | `{slug}__{start_year}_{end_year}__{hash8}.parquet` | `{batch_id}/{candidate_id}/signal_flat.parquet` |
| 写入时机 | execute 内部，每次碰到新子表达式时 | execute 结束时，一次性批量写 |
| 读取者 | `DataProvider`（execute 内部加速计算）| `report.builder`（生成报告时跳过重算）|
| 频次 | 高频（一次 batch 几千次 get/put）| 低频（每个因子生成报告时最多一次）|
| 当前规模 | 588 文件，**5.2 GB** | 每 batch ~78 MB × 30 batch ≈ **2.3 GB** |
| Git 状态 | gitignored（明确 ephemeral）| 纳入 storage/batches（事实上持久化）|
| GC | 有 `cleanup(keep_batches=2)` 方法 | **没有**（见 Q6）|

### 为什么两套是合理的

这不是设计浪费，是服务两种不同场景：

1. **粒度不同**：runtime/cache 服务"同一子表达式在多 candidate 间复用"；artifacts/ 服务"已冻结 candidate 的最终信号在多次 report 间复用"。不能互相替代。
2. **key 策略不同**：runtime 以 `expression+date_range` 为 key（随输入变化失效）；artifacts 以 `batch_id+candidate_id` 为 key（跟着 batch 冻结后理论上永不失效）。
3. **读写时机和频次完全不同**：高频密集 vs 低频稀疏，合并会扯后腿。

### 问题 7.1：FactorValueCache.cleanup 事实上不工作

`cache.py:142-161` 的清理逻辑意图是"保留最近 N 个 batch，删更早的"。但时间戳来源选错了字段：

```python
cutoff_batch = completed_sorted[-(keep_batches + 1)]
val_range = cutoff_batch.get("validation_range", [])
if val_range:
    dt = datetime.strptime(val_range[-1], "%Y-%m-%d")
    return dt.timestamp()
```

- 它用 `validation_range[-1]`（validation 区间结束日期）作为 cutoff
- 但 validation_range 是**研究数据的时间窗口**，不是**batch 实际运行的时间**
- 当前系统里所有 batch 的 validation_range 都是 `['2022-01-01', '2023-12-31']`——从 batch_001 到 batch_102 这个字段永远不变
- 所以 `cutoff = datetime(2023, 12, 31)` 实际上是一个**常量**
- 而 parquet 文件的 mtime 是**真实系统时间**，早已超过 2023 年底
- 结果：**condition `f.stat().st_mtime < cutoff` 几乎总是 False，没有文件会被删**

**证据**：runtime/cache 已经长到 5.2 GB / 588 个文件。如果 cleanup 真的每次 execute 都在工作，应该只保留 ~2 个 batch 的子表达式数据（几百 MB 级别）。

有一条兜底路径：`_compute_cutoff_time` 任何异常都返回 `time.time() - 14 * 86400`（14 天前）。这条 fallback 是**唯一实际起作用的路径**——只有当 ledger 读不到、或 validation_range 字段缺失时，cleanup 才会真的删东西。正常情况下它走的是"死胡同"。

### 问题 7.2：两套缓存没有互相感知

理论上 `artifacts/` 里的完整信号可以作为 `runtime/cache` 的一个"一级命中层"：
- execute 计算新 candidate 时，如果它的表达式完整匹配某个历史 artifacts，直接返回
- 避免对同一表达式重复走子表达式分解 + 缓存组合

但当前 `DataProvider` 不知道 `artifacts/` 存在，`report.builder` 也不知道 `runtime/cache` 存在。两套系统信息完全隔离。

### 问题 7.3：GC 策略的口径漂移

- `FactorValueCache` 引入时明确考虑了 GC（设计了 `cleanup` 方法）
- `_save_artifacts` 引入时没加 GC
- 两者都在 `storage/` 下，但一个 gitignore 一个不 gitignore，一个 ephemeral 一个 persistent——设计心理定位不一致

这种口径漂移是**典型的演进期遗留问题**：新功能没按老功能的规约实现，但没人在 code review 时发现。

### 为什么重要

1. **runtime/cache 磁盘占用失控**：5.2 GB 且还会继续涨，因为 cleanup 不工作
2. **execute 的缓存加速效果其实一直在积累 debt**：随着老缓存条目越来越多，cache.get 的查找开销（尤其是 `cache.py:102-105` 那个 backward-compat 的 glob fallback）会变差
3. **两个问题都对运维不友好**：没有 `du` 就看不到问题，没人维护就会越来越糟

### 可行方案

**方案 A（必做，修 cleanup）**：`_compute_cutoff_time` 改用 **mtime-based** 或 **ledger entry timestamp-based** 逻辑。最简单的修复：让 ledger 的每条 batch_usage 记录增加 `finalized_at` 字段（真实系统时间），cleanup 用这个字段做 cutoff。实现位置：`src/research/compute/cache.py::_compute_cutoff_time`。

**方案 B（推荐，统一 GC 入口）**：在 `finalize-batch` 里统一调度两套 GC：
```python
def finalize_batch(batch_id):
    ...
    FactorValueCache().cleanup(keep_batches=2)     # runtime cache
    _gc_rejected_artifacts(batch_id, judge_report) # artifacts (Q6 方案 A)
```
这样所有缓存清理都在一个地方，不会再漂移。

**方案 C（可选，让两套缓存互相感知）**：`DataProvider` 在 compute 新 candidate 之前先查 `artifacts/` 是否已有完整匹配。代价是要做 expression_hash 全局索引（可以复用 Q4 方案 A 的 `expression_index.yaml`）。

**方案 D（可选，磁盘守卫）**：给两套缓存加一个组合大小阈值（比如 10 GB），超过就强制跑一次 GC 并警告。避免静默增长。

### 优先级

A 必做（当前 cleanup 是死代码）。B 强烈推荐（统一 GC 入口）。C 等 Q4 方案 A 落地后再加。D 是保险网。

### 关联观察

- Q6 和 Q7 都是"缓存 GC 缺失"的两种变体：Q6 是从没加 GC，Q7 是加了但不工作。这两个一起修比较经济。
- 如果 Q4 方案 A（expression_index.yaml）落地，Q7 方案 C 就自然可以做，三条连起来能形成一个真正有效的"表达式缓存 + 重投检测 + 复用"体系。

### 勘误（2026-04-11）

Q7 原文把 `FactorValueCache` 描述为"**子表达式级别**的 memoization"。**这是错的**。

实际粒度是 **"完整候选表达式级别"**：`cache.make_key(expression, start, end)` 以**整条顶层表达式字符串** + 日期范围为 key。两个 candidate 即使共享 80% 的子结构，它们的 cache key 也是完全不同的两条 entry。

因此 `runtime/cache/research/` 里那些"看起来像子表达式"的文件（如 `tsautocorr_amount_20__2019_2023__...`）**其实都是完整候选**——只不过这些 candidate 的表达式本身就很短（单节点表达式），看起来像子表达式。

这个勘误的含义：
- runtime/cache 无法为"共享子结构"提供加速
- 真正的子表达式共享优化只能发生在 **Qlib 内部的 AST 级 cache** 里
- 而 Qlib 的 AST 级 cache 只在**一次 `D.features` 调用内**有效
- 当前 pipeline 每次只传一个表达式（见 Q12），所以这条优化也没享受到

Q7 的其他结论（cleanup 坏死、GC 缺失、两套缓存设计合理性）依然成立。

---

## Q12 — Qlib 批量调用没被使用，每个候选独立触发 `D.features`

**提问时间**: 2026-04-11
**相关阶段**: Phase 2 `/factor-execute` Step 2 base signal 计算

### 发现

当前 pipeline 是**严格串行调用 Qlib**，每个 candidate 独立走一次 `D.features`：

**`pipeline.py:235-245`**：
```python
# Phase A: compute signals sequentially (Qlib not thread-safe)
for candidate in candidates:
    ...
    base = self._compute_signal(candidate, self.profile)    # 一次一个
    signal = self._preprocess_signal(base, self.profile)
    signals.append({...})
```

**`compute_implementations.py:207`**：
```python
signal_df = self.engine.compute_dsl(expression, start, end)   # 单个 expression
```

**`data_provider.py:129-134`**（真正调用 Qlib 的地方）：
```python
return D.features(
    instruments=inst_dict,
    fields=[expression],         # 只塞 1 个元素的列表
    start_time=start,
    end_time=end,
)
```

**Qlib 的 `D.features(fields=[...])` 本身设计支持多表达式批量**——这是 Qlib 的标准接口，`fields` 参数就是为一次传多个表达式设计的。但当前代码每次只传 1 个。

### 为什么 Qlib 批量更快

Qlib 内部的 `D.features` 多表达式调用会：
1. **一次扫盘**：对整个时间范围只做一次 qlib_data 加载
2. **AST 级 cache 共享**：同一次调用里，相同的 AST 子节点只计算一次（Qlib 内置 ExpressionOps 缓存）
3. **调度优化**：对多表达式做拓扑排序，先算共享底层节点，再组合

举例：batch_103 的 6 个 candidate 里 3 个都含 `Div($close, $pe_ratio)` 子表达式。如果批量调用，这个子表达式只计算一次；当前做法是被 Qlib 独立计算 3 次（因为每次 `D.features` 调用之间 AST cache 不共享）。

### `FactorValueCache` 能挡住这个损失吗？不能

原本以为 `FactorValueCache` 会在子表达式层做 memoization，实际不会（见 Q7 勘误）：
- `make_key(expression, start, end)` 以**整条顶层表达式** + 日期为 key
- 两个 candidate 即使共享子结构，cache key 完全不同
- FactorValueCache 只对"完整重复的候选"有用（比如 batch_103 C003 重投 batch_102 C003），对"共享子结构"零贡献
- 共享子结构的唯一优化路径是 Qlib 的 AST 级 cache，而这个 cache **只在单次 `D.features` 调用内生效**

所以批量调用是**唯一**能利用 Qlib AST cache 的方式。

### 性能损失估算

一个典型的 6-candidate batch：
- 如果 6 个表达式共享 40–60% 的子结构（对相似家族 —— 如 L015 微扰 batch —— 几乎必然如此）
- 理论上批量调用可以省掉 **30–50%** 的计算时间
- 对 10–20 分钟的 execute，那是 **3–10 分钟**的无谓浪费
- 每个 batch 都浪费一次

100 个 batch 累计大约 **5–15 小时**的冗余计算。

### 为什么当前代码是串行的

三个可能成因：

1. **历史遗留**：最早 pipeline 是 per-candidate 接口（probe 入口），后来扩展到 batch execute 时直接套 for 循环，底层接口没重构。
2. **误解注释**：`# Phase A: compute signals sequentially (Qlib not thread-safe)` 这句注释容易让后人以为"Qlib 不能一次处理多表达式"。实际上 "thread-safe" 讲的是多线程问题，和批量传表达式是两件事。
3. **错误隔离保守**：per-candidate 调用的好处是 "一个 candidate 的 expression 解析失败不影响其他"。批量调用需要设计 fallback 路径。

只有第 3 点有实质理由，其他都是疏忽。

### 可行方案

**方案 A（核心修复）**：在 `DataProvider` 里加一个 `compute_dsl_batch` 方法：

```python
def compute_dsl_batch(
    self,
    expressions: List[str],
    start: str,
    end: str,
) -> Dict[str, pd.DataFrame]:
    # 先查 FactorValueCache，把命中的 cached 的挑出来
    to_fetch = []
    cached = {}
    for expr in expressions:
        key = self.cache.make_key(expr, start, end)
        df = self.cache.get(key)
        if df is not None:
            cached[expr] = df
        else:
            to_fetch.append(expr)
    
    # 对未命中的做一次批量 D.features 调用
    if to_fetch:
        from qlib.data import D
        inst_dict = self.universe.resolve()
        batch_df = D.features(
            instruments=inst_dict,
            fields=to_fetch,              # 一次传多个
            start_time=start,
            end_time=end,
        )
        # 拆分结果并分别写入 cache
        for i, expr in enumerate(to_fetch):
            single_df = batch_df[[batch_df.columns[i]]]
            self.cache.put(self.cache.make_key(expr, start, end), single_df)
            cached[expr] = single_df
    
    return cached
```

**方案 B（pipeline 集成）**：修改 `pipeline.py` 的 Phase A 循环，先批量计算后逐个 preprocess：

```python
# 1. 先收集所有 precheck pass 的 DSL expressions
exprs = [c["expression"] for c in candidates 
         if run_precheck(c).passed and c["source_type"] == "dsl"]

# 2. 一次批量调用
batch_signals = self._compute_signal_batch(exprs, start, end)

# 3. 再逐个 preprocess（很快，不是瓶颈）
for candidate in candidates:
    base = batch_signals.get(candidate["expression"])
    signal = self._preprocess_signal(base, ...)
    ...
```

**方案 C（错误 fallback）**：批量调用遇到异常时，降级到 per-candidate 串行：

```python
try:
    batch_df = D.features(fields=to_fetch, ...)
except Exception as e:
    logger.warning(f"Batch D.features failed: {e}, falling back to per-expression")
    for expr in to_fetch:
        try:
            single_df = D.features(fields=[expr], ...)
            cached[expr] = single_df
        except Exception:
            cached[expr] = None
```

这保证 "一条错误表达式不会拖累整批"——和当前串行模式的错误隔离等价。

### 优先级

A + B + C 同时做。三者是一个完整修复，缺一个都不行：
- A 提供接口
- B 把 pipeline 接到新接口
- C 保证错误不会放大

这是**中等改动、高收益**的修复——代码改动约 100 行，直接带来 30–50% 的 Phase 2 性能提升。

### 关联观察

- Q12 + Q7 合起来揭示了一个事实：**这个系统里的缓存层和计算层之间有一条"看起来在加速但其实没加速"的假动线**。Q7 的 cleanup 死代码 + Q12 的批量未启用 = 两层叠加的性能 debt。
- Q12 不影响正确性，只影响速度。但因为它能省一半时间，值得在"研究循环加速"的方向上优先做——更快的 execute → 更密的 reflect → 更多尝试 → 更可能跳出 L015 的 local optimum（间接帮 Q11 的探索节奏）。
- 这个问题也是 **"Qlib API 被浅层封装"** 的一个案例：用了 Qlib 的最基础接口（`D.features` 传一个表达式），但没有利用它作为一个现代 DSL evaluator 的批量能力。类似的浅封装在 `operators.py`、`universe.py` 其他地方可能也存在，可以作为后续审计方向。

### 勘误 / 补充（2026-04-11）

原文没提到 `prepare_batch` 的存在。事实上这个系统**有一套部分批量化的逻辑**，但只覆盖了共享数据，没有覆盖表达式本身。

**`compute_implementations.py:82` 的 `prepare_batch` 在每个 batch 开始时被调用一次**（`pipeline.py:232-233`），预取所有 candidate 共享的数据：
- Returns（多 horizon：1d/5d/10d/20d）—— 1 次批量 `get_returns`
- Market cap（`$circ_market_cap`）—— 1 次批量 `get_market_data`
- **Library factor signals（已录取的 19 个 factor）** —— ⚠️ **for 循环串行调用 `compute_dsl` 19 次**
- Family registry —— 1 次 load
- Validation 期 MI 格式 returns —— 1 次批量

所以系统里其实有**两种独立的"批量化"**：

| 类型 | 谁在批量 | 现状 |
|---|---|---|
| **共享数据预取**（returns / market_cap / family registry）| `prepare_batch` | ✅ 正确批量，只一次 |
| **Library factor signals**（已录取 factor 的重算） | `prepare_batch` 内部循环 | ❌ 19 次独立 `D.features` 调用 |
| **候选表达式计算**（新 candidate 的 base signal）| `pipeline.py` Phase A | ❌ 6 次独立 `D.features` 调用 |

**Q12 讲的 gap 本来只涵盖第三类（candidate 串行）**。补充之后发现第二类也有同样问题——`prepare_batch` 里的 library signal 重建循环也是 per-expression serial，19 次独立调用，每次 Qlib 都从零 parse。

这两处 gap 是**同一个模式**：`for expr in exprs: D.features(fields=[expr])`。修复也是同一个方案——加一层 `compute_dsl_batch` 把 for 循环替换成单次 `D.features(fields=exprs)`。

修复后每个 batch 的 Qlib 调用次数从 **6 + 19 = 25 次**降到 **1 次**（共享 AST cache）或 **2 次**（如果要把 library 和 candidate 分开走不同日期范围）。实际收益可能比原 Q12 估计的 30-50% 更大，因为 library 那 19 次调用之间的子结构重合也能消除。

### 原 Q12 描述修正

原文说：
> "当前 pipeline 是**严格串行调用 Qlib**，每个 candidate 独立走一次 `D.features`"

**修正为**：
> "当前 pipeline 对**共享数据做了正确的批量**（returns / market_cap 只拉一次），但**对表达式本身**仍然是串行——既包括新 candidate（6 次），也包括已录取 library factors（19 次）。两者共用同一个 gap：没有利用 `D.features(fields=[list])` 的批量能力。"

### 二次修正（2026-04-11）：prepare_batch 的 library 循环**不一定**是 Qlib 重算

原文说"19 次独立 `D.features` 调用"——**这是最坏情况，不是典型情况**。

`DataProvider.get_factor_values` 实际走的是**三级 fallback**（data_provider.py:99-136）：
1. **runtime/cache parquet** → 命中返回
2. **DB `factor_values` 表** → 命中返回（factor_db.py:190-246）
3. **Qlib `D.features`** → 最后兜底

`GuardedWriter._persist_factor_to_db` 在每次 admit 时向 DB `factor_values` 表写入该 factor 的完整信号（guarded_writer.py:399-413）。所以理论上每个 admitted factor 在 DB 里都有记录。

**典型情况**：prepare_batch 的 library 循环中，19 个 factor 走 DB 查询（~200ms 每个），不是 Qlib 重算。总时间几秒而非几分钟。

**Q12 的核心性能问题仍然成立**：
- candidate 串行（6 次独立 Qlib 调用）这一块不受 DB 救助——新 candidate 没进过 DB
- library 循环虽然不是 Qlib 重算，但仍然是 19 次独立调用（parquet/DB read），无法利用 Qlib AST 级 cache
- 整体批量化收益依然存在，但从 "3-10 分钟/batch" 缩减到 "~1-3 分钟/batch"

**但 DB 命中路径有几个 silent failure 点**（详见 Q13）：
- 日期范围不匹配导致 runtime cache 永远 miss（admit 写的是 2015-2023，prepare_batch 读的是 2022-2023）
- DB 写入是 best-effort，失败只记 warning
- DB 查询是精确 expression 字符串匹配，任何格式差异会 miss

---

## Q13 — 因子信号有三个存储层，但它们互相不知道对方存在

**提问时间**: 2026-04-11（从 Q12 + 用户追问延伸出来）
**相关阶段**: Phase 2 `/factor-execute` 的 prepare_batch / Phase 4 `/factor-report` 的 artifact load / admit 流程的 DB 写入

### 三个互相不知道的存储层

对每个已录取 factor（F018 等），signal 数据至少被存在 **3 个地方**：

| 存储层 | 路径 | 写入者 | 读取者 | Key |
|---|---|---|---|---|
| **Artifact parquet** | `storage/batches/batch_XXX/artifacts/CXXX/signal_flat.parquet` | execute (`_save_artifacts`) | **仅 report.builder** | `(batch_id, candidate_id)` |
| **Runtime cache parquet** | `storage/runtime/cache/research/{slug}__{start}_{end}__{hash}.parquet` | compute 层（`FactorValueCache.put`）+ admit 时 GuardedWriter 再写一次 | `DataProvider.get_factor_values` | `(expression, start, end)` |
| **DB factor_values 表** | TimescaleDB `quant_data.factor_values` (147M rows) | admit 时 `_persist_factor_to_db` | `factor_db.read_factor_values` (作为 compute 的 2 级 fallback) | `(factor_name, time)` |

### 核心问题：三个层之间**没有统一的路径**

一条 signal 的生命周期：
1. **候选在 execute 时计算**：走 `D.features(fields=[expr])` → 写 runtime cache
2. **execute 收尾时**：`_save_artifacts` 把同一份数据写到 `batches/*/artifacts/*/signal_flat.parquet`
3. **candidate 被 admit 时**：`_persist_factor_to_db` 又调用 `provider.get_factor_values(expression, "2015-01-01", "2023-12-31")` 再算一次，写到 DB

步骤 3 有一个**奇怪的浪费**：admit 时明明 artifacts 里已经有 signal 了，`_persist_factor_to_db` 却不读 artifact，而是重新调用 `get_factor_values`——这次因为日期范围不同（2015-2023 vs execute 时的 validation 范围），runtime cache key 不同 → miss → 走 Qlib 重算或 DB 查询。

然后到**下一个 batch 的 prepare_batch**时：
1. 查 runtime/cache key `(expression, val_start, val_end)` → miss（因为之前存的是 `(expression, 2015-2023)`，key 不同）
2. 落到 DB 查询 → 命中（DB 里有 2015-2023 的数据，取 2022-2023 子区间）
3. 走 DB 路径返回数据，同时**写一份新的 `(expression, val_start, val_end)` 到 runtime/cache**

**结果**：同一个 factor 的 signal 数据在磁盘上至少存了 3-4 份：
- `batches/batch_102/artifacts/C001/signal_flat.parquet`（完整范围）
- `runtime/cache/research/{slug}__2015_2023__hash1.parquet`（admit 时写入）
- `runtime/cache/research/{slug}__2022_2023__hash2.parquet`（第一次 prepare_batch miss 后写入）
- DB `factor_values` 里的同一批数据（也是 2015-2023）

这是 `runtime/cache` 长到 5.2 GB 的另一个原因——同一个 factor 的 signal 被**不同日期范围 key** 存了多份。

### 读取侧的盲区

查 `prepare_batch`（compute_implementations.py:130-150）：
```python
for fid in registry.list_factor_ids():
    detail = registry.load_factor_detail(fid)
    expr = detail.get("expression", "")
    ...
    lib_processed_mi = self.engine.compute_dsl(expr, val_start, val_end)
```

它用 `compute_dsl(expr, val_start, val_end)` 去取数据。这个路径**只知道** runtime cache → DB → Qlib。**完全不知道** `storage/batches/*/artifacts/*/signal_flat.parquet` 的存在。

换句话说：
- prepare_batch 想要的数据**就躺在 artifacts 里**
- 但它绕着 artifacts 走，去查 DB
- 如果 DB 坏了，它会去 Qlib 重算
- **artifacts 作为本地 parquet 文件本应是最快的读取路径，但架构上对 compute 层不可见**

### 为什么 artifacts 没被接入

合理推测：artifacts 是为 report builder 设计的（Q6 讨论过），写入路径是 `BatchRunner._save_artifacts`，索引是 `(batch_id, candidate_id)`。compute 层用的是 `(expression, start, end)` 索引，两边 key 设计不兼容。

要让 compute 层能读 artifacts，需要一个**反向索引**：
- 从 expression → (batch_id, candidate_id) 映射
- 这正是 **Q4 / Q11 提到的 `expression_index.yaml`** 应该解决的问题
- 有了 expression_index 后，`compute_dsl` 可以在第 0 级（比 runtime cache 更早）先查 artifact

### 几个 silent failure 点

即便在当前架构下，DB 路径也有几个可能让缓存 miss 的坑：

**坑 1：日期范围 key 永久不匹配**

- admit 时 `_persist_factor_to_db` 用 `(data_start, val_end)` = `("2015-01-01", "2023-12-31")`
- prepare_batch 用 `(val_start, val_end)` = `("2022-01-01", "2023-12-31")`
- runtime cache key 永远不同 → 第一次 prepare_batch 永远 miss
- 之后 runtime cache 会补一份新 key 的副本——但这又是磁盘膨胀

**坑 2：DB 写是 best-effort**

`guarded_writer.py:393-394`：
```python
try:
    write_factor_meta(...)
except Exception as exc:
    logger.warning("DB factor_meta write failed for %s: %s", factor_id, exc)
```

失败**只记 warning，不抛，不回滚**。factor registry 里有 F018，但 DB 里可能空的。没有机制检测 "registry 和 DB 之间的差集"，所以一旦漏写就是永久漏。

**坑 3：DB 查询精确字符串匹配**

`factor_db.py:213-215`：
```python
cur.execute(
    "SELECT factor_id FROM factor_meta WHERE expression = %s AND status = 'admitted' LIMIT 1",
    (expression,),
)
```

- expression 必须完全相等（任何空格/括号差异就 miss）
- status 必须精确是 'admitted'
- 没有 fuzzy matching，没有 factor_id 反查兜底

如果 LLM 后续格式化了 registry YAML 里的 expression 字符串（比如加空格、规范化括号），DB 再也认不出来 → 永久 miss → 每次都走 Qlib 重算。

### 为什么重要

1. **磁盘冗余**：同一数据存 3-4 份（artifact + 2 份 runtime cache 副本 + DB），runtime/cache 膨胀的一大原因
2. **admit 时的浪费**：已经有 artifact 的数据，admit 流程还要再走一次 compute_dsl 才能写 DB
3. **prepare_batch 绕远路**：本地 parquet 不读，去查 DB
4. **silent failure 扩散**：坑 2 和坑 3 会随着时间积累让 DB 命中率下降，最终 fallback 到 Qlib 重算
5. **和 Q11 重构方向冲突**：要实现"自主探索"需要快速 execute，而当前 execute 时间的一部分被这种存储层的迷宫消耗掉了

### 可行方案

**方案 A（必做，和 Q4/Q11 联动）**：建立 `expression_index.yaml` 反向索引：
- key: `hash(normalized_expression)`
- value: `{batch_id, candidate_id, admitted_factor_id, artifact_path, db_factor_name}`
- 每次 finalize-batch 写入一条
- 这是 Q4 方案 A、Q11 方案 2、Q13 共同的基础设施

**方案 B（必做，artifact 接入 compute 层）**：在 `DataProvider.get_factor_values` 最前面加一级 artifact 查找：
```python
def get_factor_values(self, expression, start, end):
    # 【0 级：新增】查 expression_index → artifact_path
    artifact_path = self.expression_index.find(expression)
    if artifact_path and artifact_path.exists():
        df = pd.read_parquet(artifact_path)
        return _filter_date_range(df, start, end)  # 在本地切日期范围
    
    # 【1 级】runtime cache
    ...
    # 【2 级】DB
    ...
    # 【3 级】Qlib
    ...
```

优势：
- 最快的路径（本地 parquet 读）
- 不依赖 DB 可用性
- 完全避开日期 key 的不匹配问题（因为 artifact 是完整时间段，本地切范围）

**方案 C（必做，admit 时复用 artifact）**：`_persist_factor_to_db` 不再走 `provider.get_factor_values(expression, start, end)` 重新计算，而是直接读 artifact parquet：
```python
def _persist_factor_to_db(factor_id, payload):
    batch_id = payload["batch_id"]
    candidate_id = payload["candidate_id"]
    artifact_path = Path(f"storage/batches/{batch_id}/artifacts/{candidate_id}/signal_flat.parquet")
    if artifact_path.exists():
        factor_df = pd.read_parquet(artifact_path)
        write_factor_values(factor_id, factor_df)
    else:
        # fallback: 重新算
        ...
```

优势：省去 admit 时的一次 compute_dsl 调用（通常是几十秒）。

**方案 D（推荐，DB 写入失败自修复）**：加一个 `verify_db_consistency` 步骤：
- 每次 finalize-batch 之后，遍历 registry 里的 factor_ids
- 对每个检查 `factor_meta` 和 `factor_values` 是否存在
- 缺失的自动补写（从 artifact 读）
- 或者起码写一条警告到 `research_state.db_sync_issues`

**方案 E（可选，precheck 时的反向索引利用）**：有了 expression_index 后，precheck 就能检测 Q4 的"同表达式重投"——两个支点合二为一。

### 优先级

A + B 必做，一起做（Q4 + Q11 + Q13 的共同支点，建一次索引管多件事）。
C 次之（是额外的加速优化）。
D 推荐（DB 健康保障）。
E 是外溢收益。

### 关联观察

- Q13 和 Q7 的勘误是连续发现：Q7 以为 runtime cache 是子表达式级 memoization → 发现其实是完整表达式级 → 发现它和其他存储层完全脱节 → Q13
- Q13 和 Q6（artifacts 无 GC）是相反的视角：Q6 说"artifacts 占磁盘但没人清"，Q13 说"artifacts 存了但没人读"——**它们都是 artifacts 这个存储层被孤立的症状**
- Q13 是所有 Q 里最接近"显著存储浪费"的一个——磁盘层面的直接重复存储，而不只是治理漂移
- Q13 方案 A（expression_index）现在已经是 **5 个问题共享的支点**：Q3 / Q4 / Q7 / Q11 / Q13。把这一件事做完会直接解决这 5 个问题的大半症状

---

## Q14 — Preprocess 管道：docstring 撒谎，代码只做一半，tradability 被 4 处硬编码关掉

**提问时间**: 2026-04-11
**相关阶段**: Phase 2 `/factor-execute` Step 3 preprocess

### 发现：docstring 和代码不一致

`src/research/compute/preprocess.py` 的 docstring 声明 5 步：
```
1. universe_mask  -- filter to stocks in the target universe
2. tradability    -- drop stocks with NaN close or zero volume
3. winsorize      -- clip outliers at mean +/- n_sigma * std
4. zscore         -- standardize to mean=0, std=1
5. neutralize     -- (optional) subtract industry/size group means
```

实际 `run()` 方法（preprocess.py:53-90）只做：
```python
if tradability_check and market_df is not None:
    result = self._apply_tradability(result, market_df)
result = self._winsorize(result)
result = self._zscore(result)
if self.neutralize_col and market_df is not None:
    result = self._neutralize(result, market_df)
```

| docstring 说 | 代码实际 |
|---|---|
| 1. universe_mask | **❌ 方法根本不存在**。`grep universe_mask src/research/` 在 preprocess.py docstring 之外零匹配 |
| 2. tradability | ⚠️ 有代码，但默认被绕过（见问题 14.2）|
| 3. winsorize | ✅ 实际在跑 |
| 4. zscore | ✅ 实际在跑 |
| 5. neutralize | ⚠️ 默认关闭（`neutralize_col=None`），从没被启用 |

### 问题 14.1：`universe_mask` 是 docstring 撒谎

代码里**没有任何** `_universe_mask` 方法。也没有任何调用点处理过"universe mask"概念。

实际上 universe 过滤是在 **Qlib 层**发生的——`DataProvider` 调用 `D.features(instruments=inst_dict, ...)` 时已经传了 csi1000 的 instrument dict，返回的数据**本来就是** csi1000 only 的。docstring 里那句 "filter to stocks in the target universe" 应该被删除或改写成"universe filtering is handled upstream by Qlib"。

**影响**：纯误导。任何看 preprocess.py 顶部注释的人（包括写 walkthrough 文档的 LLM）都会以为这里会做 universe mask，实际上没有。

### 问题 14.2：`tradability_check=False` 在 **4 个调用点**硬编码

grep 结果：
```
execute/compute_implementations.py:146: self.preprocessor.run(lib_processed_mi, tradability_check=False)
execute/compute_implementations.py:251: self.preprocessor.run(base_signal, tradability_check=False)
compute/factor_engine.py:76:           self.preprocessor.run(df, tradability_check=False)
compute/factor_engine.py:139:          self.preprocessor.run(result_df, tradability_check=False)
```

**所有 4 个调用点都显式传 `tradability_check=False`**。

这意味着：
- 停牌日 / 涨跌停天 / 零成交量日的 factor value **不会被标为 NaN**
- Qlib 算出来的值（可能基于前一天收盘价的 freeze、可能是除零异常等）会**直接进入后续的 IC / mono / quintile 计算**
- 这部分"脏数据"会成为**噪声下限**——即使因子本身是好的，也会有一部分评估代价被浪费在这些无效日上

**`_apply_tradability` 方法本身实现是对的**（检查 `$close.isna()` 和 `$volume == 0`，把命中的行设为 NaN）——问题是从没被启用。

**最可能的原因**：启用需要给 `run()` 传 `market_df` 参数（包含 `$close` / `$volume` 字段），但当前调用路径没人传这个参数，所以直接用 `tradability_check=False` 绕过。

**这是一个真 bug**，不是设计选择。

### 问题 14.3：winsorize 是 σ-based 不是 percentile-based

代码（preprocess.py:124-134）：
```python
mean = g.transform("mean")
std = g.transform("std")
lower = mean - self.sigma * std
upper = mean + self.sigma * std
result[col] = df[col].clip(lower=lower, upper=upper)
```

默认 `sigma=3.0`，即 **mean ± 3σ 截断**。

量化社区更常用的是 **percentile-based winsorize**（1% / 99% 或 2.5% / 97.5%）。原因：
- σ-based 假设分布是 **近似正态**的
- 因子值的截面分布往往是**重尾**的
- 重尾分布里几个极端 outlier 会把 std 撑大 → 3σ 本身被拉得很远 → "3σ 之外"几乎没数据
- 结果是**实际上没有做什么截断**

这不算严重 bug，但是一个**次优选择**。在因子挖矿这种场景里 percentile-based 更稳。

### 问题 14.4：preprocess 的 neutralize ≠ Barra 中性化

preprocess.py 的 `_neutralize`（line 151-180）只做 **group demean**：

```python
def _demean_group(g):
    out = g.copy()
    out[col] = g[col] - g[col].mean()
    return out

result = combined.groupby(
    [combined.index.get_level_values("datetime"), "_group"],
    group_keys=False,
).apply(_demean_group)
```

它只能按一个**离散 group label**（industry / size bucket）去均值。做不了真正的 Barra 中性化——Barra 需要对所有 style 因子做**线性回归取残差**。

**系统里有两层"中性化"在打架**：

| 层 | 位置 | 类型 | 启用情况 |
|---|---|---|---|
| Preprocess 层 | preprocess.py `_neutralize` | Group demean | **从没启用**（`neutralize_col=None` 默认）|
| Risk engine 层 | Step 9 风险评审，`barra_residual_ic` | Linear regression residual | **每次都跑**，是 judge 的核心证据 |

**只有后者在实际工作**。前者是**孤儿代码**。

这引发的问题：如果 walkthrough 文档或新人以为"preprocess 里有中性化所以不用担心 style 污染"，那就错了——真正的 style 污染检测在 risk engine 里，preprocess 完全不做。

### 问题 14.5：产生雪崩效应的 walkthrough 错误

这个 Q 的发现起源于用户戳穿我在 Phase 2 walkthrough 里描述 preprocess 时的 **5 个错误**：

| 我之前说 | 真实情况 |
|---|---|
| 5 步：universe mask / tradability / winsorize / zscore / neutralize | **只有 2 步真的跑**：winsorize + zscore |
| universe mask 剔除非 csi1000 股票 | **这一步不存在**，universe 在 Qlib 层做完 |
| tradability 剔除停牌/涨跌停 | **所有调用点硬编码关闭**，此步从不执行 |
| winsorize 在 1%/99% 分位截断 | 实际是 **mean ± 3σ 截断**，不是 percentile-based |
| neutralize 剥除 book_to_price Barra style | preprocess 的 neutralize 只是 group demean，做不了 Barra 回归。默认关闭。真 Barra residual 在 Step 9 做 |

**5/5 都是错的**。我是看 docstring 讲的，docstring 是假的。

**这不只是一个文档问题**——它说明系统里所有看 preprocess docstring 的人（包括未来的 LLM reflect、新来的开发者、任何写 onboarding doc 的人）都会被**系统性误导**。

### 用户提出的一个设计想法：跨池子评估

用户问："我们有全市场的因子值了，我们是不是可以在不同的池子上 mask，这样可以看到因子跨池子的表现"

当前做不到，但**是一个好想法**。

当前限制：
- `D.features(instruments=csi1000_dict, ...)` 已经限定池子在 compute 阶段
- 想看 csi300 要重跑一遍 compute
- 没有"一次 compute，多池子评估"的路径

可行设计：
1. compute 阶段用 `universe="all"`
2. 产出的 full-market factor value 存到 artifact
3. Effect strength / Stability analyzer 支持 `mask_by_universe` 参数
4. 一次 compute 产出多个池子的 IC 结果

收益：
- **跨池子稳健性**成为一个新的证据维度
- 因子在 csi300 / csi500 / csi1000 都 work → 是真 alpha 的更强证据
- 因子只在 csi1000 work → 可能是 over-fit 到 csi1000 的特殊结构

这一条放进 Q11 的"自主探索"方向里也很合适——相当于给系统多一个内生的"稳健性检查"，不用额外投入 batch budget。

### 为什么重要

1. **数据正确性问题**：tradability 被关掉 → 停牌/涨跌停天的噪声被计入 IC → 所有 factor 的评估都带着这层噪声。虽然影响不大，但**系统性**偏差，无法被单个因子的评估发现。
2. **文档可信度问题**：docstring 是文档层面的 ground truth，但它与代码脱节 → 任何后续开发（包括 LLM 自主写代码或讲解代码）都会被误导。
3. **"neutralize 层"打架**：系统里有两个同名但做完全不同事的东西（preprocess demean vs barra residual），这种重名本身就是一个 source of confusion。
4. **Phase 2 walkthrough 的 5 处错误**：说明即使是"阅读代码"这件事也不可靠——你以为自己读了代码，实际是在读 docstring。这对文档撰写、新人 onboarding、LLM 自治都是危险的。

### 可行方案

**方案 A（必做，改 docstring）**：把 preprocess.py 的 docstring 改成真实的 5 条：
```
Pipeline steps (actual behavior):
    1. tradability (optional, disabled by default in current callers)  -- drop stocks with NaN close or zero volume
    2. winsorize   -- clip outliers at mean +/- n_sigma * std (NOT percentile)
    3. zscore      -- standardize to mean=0, std=1
    4. neutralize  (optional, disabled by default) -- group demean only, NOT Barra regression

    Note: universe filtering happens upstream at the Qlib D.features() call,
    not in this class. CsRank/CsZscore operators compute on full market regardless
    of the mining universe (see operators.py).

    Note: True Barra style neutralization happens in the Risk Engine (Step 9 of
    execute pipeline), not here. This neutralize() only subtracts a group mean.
```

成本：几分钟，零风险。立即阻止 walkthrough/onboarding 错误继续扩散。

**方案 B（必做，启用 tradability）**：改 4 个调用点：
1. 修改 `DataProvider` 或 `prepare_batch` 预取 `$close` 和 `$volume` 作为 shared batch data
2. 4 个调用点传入 `market_df=shared_market_df, tradability_check=True`
3. 其实 `prepare_batch` 已经在预取 `$circ_market_cap`（compute_implementations.py:122），顺手加两个字段即可

代价：小。收益：去掉所有因子评估的一个系统性噪声源。

**方案 C（推荐，winsorize 改 percentile）**：加一个参数 `winsorize_method: "sigma" | "percentile"`，默认改为 percentile（1% / 99%）。对 sigma 模式保留兼容。

代价：小。收益：对重尾因子分布更稳健。

**方案 D（推荐，preprocess 的 neutralize 重命名）**：
- 把 `_neutralize` 改名为 `_group_demean`
- docstring 明确说 "this is NOT Barra neutralization, for Barra residual see risk/engine.py"
- 或者直接删掉（反正从没被启用）

代价：改几行字。收益：消除重名带来的概念混淆。

**方案 E（设计，跨池子评估）**：Q11 规划里加一条"多池子 signal 复用"：
- compute 用 `universe="all"`
- 分析阶段支持多池子 mask
- 每个 factor 除了 csi1000 IC 还有 csi300/csi500 IC
- 作为 admit 判据之一：跨池子 IC 方向一致 → 更强证据

代价：中。需要改 analyzer 接口 + artifact 格式。但**收益极大**——给系统一个"免费的"稳健性检查维度。

### 优先级

- A 立即做（零成本阻止误导扩散）
- B 必做（是真 bug，但需要 10-20 行代码改动）
- D 必做（概念混淆比代码 bug 还麻烦）
- C 推荐（次优改优）
- E 放进 Q11 规划（长期设计）

### 关联观察

- Q14.1/14.3/14.5 都是同一类问题：**文档和代码脱节**。Q14 和 Q1（idea_report 丢失）、Q9.1（thread 字段名 drift）、Q10（proposals 化石目录）都是一个大家族——"写在文档里或代码注释里的约束，没有被代码执行"。
- Q14.4 和 Q6/Q7/Q13 是同一个 meta-问题：**系统里有多个同名但不同语义的缓存/中性化/存储层，它们互相不知道对方存在**。这种语义重叠是结构性复杂度，修复需要整体命名规约。
- Q14.5（walkthrough 5/5 错）说明 **"读代码"这个动作本身也不可靠**——你以为你在读代码，其实在读 docstring 或注释。对 LLM 自治尤其危险，因为 LLM 倾向于相信 docstring 作为"权威描述"。长期看应该考虑：**所有关键模块的 docstring 做 CI-level 校验**（docstring 里描述的步骤必须 grep 得到对应方法名，否则报错）。

### 补充（2026-04-11）：tradability 的根治方案

原方案 B 说 "启用 `tradability_check=True`"。这是**事后 mask**，对**截面算子**正确，但**对时序算子不够**。

时序污染的具体例子：如果 T-5 是停牌日，Qlib 用前一天 freeze 的 close 算 `Mean($close, 20)[T]`，T-5 的值污染了从 T 到 T+14 共 15 天的滚动窗口。事后只抹掉 T-5 自己不解决后 14 天的污染。

**正确的根治方案是 Q14 方案 F（新增）**：

**方案 F（根治，改 qlib binary）**：
1. 修改 `scripts/resync_qlib.py`，在写 binary 前对每只股票扫描停牌日：
   ```python
   stopped_mask = (df['volume'] == 0) | df['close'].isna()
   df.loc[stopped_mask, ['open','high','low','close','volume','amount']] = np.nan
   ```
2. 重新生成 qlib binary（~1 分钟）
3. 清空 runtime/cache 和 DB factor_values（需要重新计算所有已录取 factor 的数据）
4. 之后所有时序算子自动用 pandas rolling 的 `min_periods` 跳过 NaN——数学上正确
5. `_apply_tradability` 方法保留作为"冗余事后 mask"安全网

代价：一次性数据迁移 + 缓存清空。收益：所有时序算子都正确处理停牌。

**涨跌停是不同的子问题**：
- 涨跌停日的 close 价格**是合法的**（就是那个限价），不应设为 NaN
- 但"第二天 return"**是不可用的**（今天下不了单）
- 正确处理：在 `prepare_batch` 算 returns 时，把"下单日是涨跌停"的 return 设为 NaN
- 这一步应该加在 `get_returns` 层

### 补充（2026-04-11）：跨池子评估的完整设计

原方案 E 只给了大概，现在给完整设计（回应用户问题 5/6）。

**核心架构变更**：
```
当前: compute(universe=csi1000) → signal → analyze
新:  compute(universe=all)      → signal → [mask × N universes] → analyze × N
```

**7 个具体改造点**：

1. **DataProvider 默认 universe=all**：compute 阶段永远全市场，universe 是评估阶段概念
2. **CsRank 参数化**：
   ```python
   CsRank($pe_ratio)              # 默认用 compute universe（即 all）
   CsRank($pe_ratio, "csi1000")   # 显式池内 rank
   ```
3. **Analyzer 批量接口**：`analyze(factor_df, returns, universes=["csi300","csi500","csi1000"])`
4. **zscore 必须在 mask 之后做**：否则 csi1000 子集的 mean≠0, std≠1
5. **research_result.yaml 结构升级**：每个池子一份 metrics 块
6. **Judge 新维度"跨池子一致性"**：
   - 三池符号一致 → `consistent`（admit 加分）
   - 两池一致 → `mostly_consistent`
   - 三池不一致 → `inconsistent`（admit 减分）
7. **prepare_batch 的 library factor 只算一次全市场**，省掉 19 次重复

**收益**：
- 跨池子一致性成为新的证据维度（**直接回应 Q11 的自主探索方向**——给系统一个内生的稳健性检查，不额外投 batch budget）
- library factor 计算从 19 次降到 1 次
- Cache 命中率提升（key 不再需要 universe 维度）
- 能做"因子池外延"（csi300 vs csi1000 的表现差异揭示池子适配性）

**代价**：
- compute 慢 20-40%（数据量 ×5.4，但时序算子本来就在全市场跑，实际增量小）
- artifact 存储增加 5.4x
- 代码改动约 400-600 行

**和 Q11 的关系**：这是 Q11 "summarize → think → mutate → explore" 循环里 **summarize** 的一个具体落地——"跨池子表现差异"是一种免费的、跨候选的、可聚合的观察。

---

## Q15 — CsRank / CsZscore 永远在全市场计算，这是一个值得审视的隐含假设

**提问时间**: 2026-04-11
**相关阶段**: Phase 2 `/factor-execute` 的 compute 阶段 / 整个系统的 cross-sectional 语义

### 事实

CLAUDE.md 明确写：
> **Cross-sectional operators** (`CsRank`, `CsZscore` in `operators.py`) always compute over the full market (`D.instruments("all")`), regardless of the mining universe.

`operators.py:379` 实现：
```python
all_df = D.features(
    instruments=D.instruments("all"),
    ...
)
```

无论挖矿 universe 是 csi1000 还是别的，CsRank 的截面**永远**是全市场 5431 股。

### 为什么这是一个问题

系统的其他部分都以 **csi1000** 作为评估范围：
- IC / ICIR 计算在 csi1000 内
- Quintile 分组在 csi1000 内
- Factor value 最终只在 csi1000 行被使用

**但 CsRank 的 cross section 是全市场**。这意味着：
- 一只 csi1000 股票的 `CsRank($pe_ratio) = 0.8` 不代表它在 csi1000 里排 top 20%
- 它只代表在**全市场** 5431 股里排 top 20%
- 它在 csi1000 内部可能排 40% 或 60%

**语义不一致的后果**：
1. 因子值依赖了**不在交易池里的股票**的分布
2. 如果全市场结构变化（退市、科创板上市），csi1000 的因子值会被外部变化污染
3. Quintile Q1（csi1000 内最低 20%）和"全市场 rank 的 Q1"是两回事——评估时 Q1 其实是"全市场 rank 相对低 + 恰好在 csi1000"的股票，不是纯 csi1000 内部分位

### 两面的论据

**支持全市场**：
- Rank 更稳定（5431 vs 1000 样本）
- 捕捉"相对全市场的位置"语义
- 对 universe 组成变化不敏感

**反对全市场**：
- 评估窗口（csi1000 内 IC）和决策窗口（全市场 rank）不一致
- "universe leakage"：因子值依赖非交易池股票
- 和 quintile 分组的池子错配
- 如果要交易的是 csi1000，池内 rank 更符合"池内相对强弱"的决策语义

### 评价

这**不是一个严重 bug**，但是一个**值得 re-examine 的早期设计假设**。最可能的成因：系统最初是全市场挖矿，后来为 csi1000 适配时 CsRank 没跟着改，就留下了。

**个人倾向**：对大多数因子，**池内 rank 更能预测池内收益**——因为 rank、IC、quintile 都在同一个池子里，语义闭环。

### 可行方案

**方案 A（推荐）**：CsRank / CsZscore 参数化：
```python
CsRank(factor, scope="universe")   # 默认：当前 mining universe
CsRank(factor, scope="all")         # 显式：全市场
CsRank(factor, scope="csi300")      # 显式：特定池子
```

默认从 "all" 改为 "universe"（对齐 mining universe）。旧行为通过显式参数保留。

**方案 B（实验性）**：同时算两种 rank，给 judge 做对比：
- 对每个用到 CsRank 的表达式，自动生成"全市场 rank 版"和"池内 rank 版"两个候选
- judge 能看到两种 rank 下的 IC 差异
- 差异大的 → 说明这个因子对 universe 定义敏感 → warning

**方案 C（保守）**：不改行为，但在 docstring 和 skill.md 里**明确说明**这个选择的语义含义——避免 LLM 下一轮写表达式时误以为 CsRank 是在 mining universe 内 rank。

### 和 Q14.5（跨池子设计）的关系

Q15 和 Q14 补充的跨池子设计**高度耦合**：
- 如果实现跨池子评估（Q14 方案 E），**CsRank 必须参数化**——因为评估层要做多池子 mask，CsRank 的 scope 不能固定在 all
- 反过来：如果 CsRank 能参数化（方案 A），跨池子评估就能做到真正"每个池子独立 rank + 独立 IC"
- **两个方案一起做才完整**

### 优先级

A 推荐（和 Q14 方案 E 一起做）。C 最小成本（至少把语义说清楚）。B 实验性可选。

### 关联观察

- Q15 和 Q14.5（跨池子评估）是同一套架构重构的两个面：Q14.5 从"评估分析"角度切入，Q15 从"cross-sectional 算子"角度切入。两个一起修才真正让"多池子语义"闭环。
- Q15 是整个 Q 列表里**唯一一个"不是 bug，是隐含假设"**的条目。它提示我们：系统里可能还有其他类似的"从未被 re-examine 的早期决定"。Q11 的 meta-reflect 层应当把这种"结构性假设"也作为审视对象，而不只是 batch 层面的失败模式。

---

## Q16 — 停牌/涨跌停/ST/退市/科创板/北交所 过滤：配置存在、数据部分存在、代码**完全没消费**

**提问时间**: 2026-04-11
**相关阶段**: Phase 2 `/factor-execute` 数据清洗 / universe 定义 / future return 计算

### 背景

用户问："停牌/退市/ST/科创板/北交所 这些过滤逻辑都有吗？"

这是 Q14（preprocess docstring 撒谎）的延伸——如果连最基本的涨跌停识别都没做，那 Q14 说的"正确处理停牌"连前置条件都不具备。

### 三层证据

**配置层**（`src/research/domain/config.py:21-32`）：

```python
@dataclass
class UniverseConfig:
    universe_id: str = "csi1000"
    filter_suspend: bool = True      # 停牌过滤
    filter_limit: bool = True        # 涨跌停过滤
    min_listing_days: int = 60       # 新股 60 天冷却
```

3 个过滤 flag 存在，默认全启用。看起来一切正常。

**数据层**（`src/data/qlib_sync.py:27-28`）：

```python
FIELDS = ["open", "high", "low", "close", "volume", "amount"]
AUX_FIELDS = ["limit_up", "limit_down"]
```

✅ `limit_up` / `limit_down` **同步到 qlib binary 里了**
❌ `$is_st` **没同步**
❌ `$list_date_dist` **没同步**
❌ `$industry_code` **没同步**

`docs/superpowers/plans/2026-03-22-mining-preprocessing.md:24-35` 明确写这些是 "Future work (not in this plan)"，而且承诺 "**the config flags and neutralization logic are already in place**"——意思是"flag 准备好了，等数据到了就自动生效"。

**消费层**（grep 整个 `src/research`）：

```
filter_suspend   → 只在 config.py 定义里出现 1 次，无消费
filter_limit     → 只在 config.py 定义里出现 1 次，无消费
min_listing_days → 只在 config.py 定义里出现 1 次，无消费
```

**零消费**。没有一处代码在读这 3 个 flag。`_apply_tradability`（Q14 讨论过，被关闭）只检查 `$close.isna()` 和 `$volume == 0`，**不读 flag，也不比较 `close == limit_up`**。

`limit_up` / `limit_down` 字段**同步到 binary 了但没有任何代码用它们**。系统连"识别今天是涨跌停日"这个动作都做不到——因为：
- `$close` 在涨跌停日**既不是 NaN**（close 就是涨跌停价）
- `$volume` 在涨跌停日**也不是 0**（成交依然发生，只是被封住）
- 唯一的识别方法是比较 `close == limit_up` 或 `close == limit_down`——而**没人做这个比较**

### 完整过滤状态表

| 过滤维度 | 配置 flag | 数据字段 | 实际消费 | 真实生效 |
|---|---|---|---|---|
| **停牌** | ✅ `filter_suspend=True` | ⚠️ 靠 `volume=0` 推断 | ❌ flag 无人读，`_apply_tradability` 被关 | **❌ 不生效** |
| **涨跌停** | ✅ `filter_limit=True` | ✅ `$limit_up` / `$limit_down` 在 binary | ❌ 没有任何代码做 `close == limit_up` 检测 | **❌ 不生效** |
| **新股冷却** | ✅ `min_listing_days=60` | ❌ `$list_date_dist` 没同步 | ❌ 没代码 | **❌ 不生效** |
| **ST 过滤** | ❌ 无 flag | ❌ `$is_st` 没同步 | ❌ 没代码 | **❌ 不生效** |
| **退市** | ❌ 无 flag | 部分（靠 universe 成分股历史间接过滤）| ❌ 没显式代码 | ⚠️ **靠 universe 隐式过滤** |
| **科创板** (688*) | ❌ 无 flag | ❌ 没 `$market` 字段 | ❌ 没代码 | ⚠️ **靠 universe 隐式过滤** |
| **北交所** (8*) | ❌ 无 flag | ❌ 没 `$market` 字段 | ❌ 没代码 | ⚠️ **靠 universe 隐式过滤** |

### 问题 16.1："universe 隐式过滤"不是真过滤

表格里退市 / 科创板 / 北交所都标 "⚠️ 靠 universe 隐式过滤"。**这不是真过滤**——它只是 "当前 universe (csi1000) 的成分股定义**副作用**地不包含这些股票"。

3 个潜在问题：

**(a) 改 universe 就全失效**

如果你把挖矿 universe 从 `csi1000` 改成 `all`（比如为了 Q14 讨论的跨池子评估），所有这些隐性过滤**立刻全部失效**：
- 5431 股全部进来
- 科创板、北交所、ST、新股都混进去
- 没有任何代码挡住

**(b) CsRank 已经在全市场算了（Q15）**

即使 csi1000 的评估窗口看不到这些股票，**CsRank / CsZscore 的 cross section 已经用了全市场**（包括科创板和北交所）。所以：
- csi1000 股票的 `CsRank($pe_ratio)` 排名**已经包含了这些"被隐式过滤"的股票**
- 你的因子值里其实已经有科创板 + 北交所的影响
- 只是你没在评估结果里直接看到

这是一个**半半的污染**——表面上过滤了，实际计算里没过滤。

**(c) csi1000 成分股历史不够精细**

- csi1000 官方规则对 ST 的处理是"半年调整一次"
- 一只股票被标 ST 之后，可能在 csi1000 里挂 3-6 个月
- 系统不会知道它是 ST，还会把它的因子值和 return 当正常股票处理

### 问题 16.2：连"识别今天是涨跌停"都做不到

回到用户前一个问题——"涨跌停价格还在，为什么要 NaN"。现在你看到另一面：

**即使确定了"涨跌停 return 应该设为 NaN"这个策略，当前系统也根本识别不了"今天是涨跌停"**：

1. `$close` 在涨跌停日合法存在（就是涨跌停价本身）
2. `$volume` 在涨跌停日不为 0（成交仍在发生）
3. 唯一识别方法：比较 `$close == $limit_up` 或 `$close == $limit_down`
4. **没有任何代码做这个比较**

`$limit_up` / `$limit_down` 静静地躺在 binary 里，被同步、被存储、但**从未被读取**。是一组纯粹的 dead data。

### 问题 16.3：计划文档的"already in place"是承诺而非事实

`docs/superpowers/plans/2026-03-22-mining-preprocessing.md` 里那句：

> "the config flags and neutralization logic are already in place"

从字面上是说"flag 和逻辑都准备好了，等数据到了就自动生效"。但**事实是**：
- flag 确实"在 config.py 里已定义"
- **没有任何逻辑在消费这些 flag**
- 即使数据到了，还需要有人写消费代码

这是一个**文档承诺和代码实现的错位**——计划文档在"安抚"未来的读者"别担心，基础设施已经铺好了"，但实际没铺。这和 Q14.1（docstring 撒谎）、Q1（idea_report 丢失）是同一类问题的更严重版本——**文档声明的能力并未在代码中存在**。

### 为什么重要

1. **IC / 评估完整性**：所有过去 100+ batch 的 IC 计算里，涨跌停日的 return 都**当作正常 return 参与了统计**。这是一个**系统性 bias**，特别是对短期动量信号——涨停后第二天的继续涨跌会被因子"学会"当作 alpha。
2. **"改 universe 就炸"的脆弱性**：Q14 / Q15 提出的"跨池子评估"和"CsRank 池内化"，**在这个前提下根本做不得**——一旦动 universe，所有隐式过滤失效，脏数据涌入。修 Q14/Q15 的前置条件是先修 Q16。
3. **计划文档的可信度**：`mining-preprocessing.md` 这份计划承诺了一大堆"基础设施已就位"，但至少 `$is_st` / `$list_date_dist` / 过滤 flag 消费都没做。后续读计划文档的 LLM 和新人会继续被误导。
4. **limit_up / limit_down 字段成本被浪费**：数据同步链路真实地把这两个字段从 RiceQuant 拉到了 TimescaleDB 再到 qlib binary——这是一条有代价的数据管道。但下游完全没消费，等于白花钱。

### 背景补充：成熟的三层过滤框架

用户追问"一个成熟的因子挖掘逻辑应该怎么处理涨跌停"。答案是一个**三层框架**，这是实务里的标准做法。理解这个框架能让后续修复方向更清楚。

**核心认知**：当你说"过滤涨跌停"，可能指的是**两件不同的事**：

| 动作 | 操作 | 后果 |
|---|---|---|
| **动作 A**：剔除 factor value | `signal[T, stock] = NaN` | 这只股票在这一天**完全消失**——不在 quintile、不在 IC、不在 redundancy |
| **动作 B**：剔除 (factor, return) 对里的 return | `future_return[T, stock] = NaN`，factor 保留 | factor value 仍然存在，但这一对 (factor, return) 在 IC 计算时被跳过 |

不同情况要用不同的动作。**把所有情况都用动作 A 是错的**（破坏时序连续性），**都用动作 B 也是错的**（漏掉结构性剔除）。

成熟的分层：

**Tier 1：完全剔除**（factor = NaN，return = NaN）

特征："**这个股票在这一天不属于我的研究样本**"。

| 情况 | 为什么完全剔除 |
|---|---|
| **停牌** | 数据本身是 NaN / freeze，不是研究对象 |
| **ST / \*ST** | 结构性事件（财务问题），不是因子 alpha 能捕捉的。任何"变 ST 前股价下跌"都不是你的因子的功劳 |
| **退市** | 显然 |
| **新股 < 60 天** | IPO 之后有显著的过度反应（"新股效应"），和因子 alpha 无关 |
| **科创板 / 北交所**（如果只研究主板）| 市场结构不同（涨跌幅规则 20%、交易机制），不能混在一起统计 |

**共同特征**：这些不是"因子没预测对"的问题，是"这个股票在这一天不属于我在研究的这个市场"的问题。

**Tier 2：factor 保留，return 设 NaN**

特征："**factor value 是合法数据，但基于它的交易执行不了**"。

**涨跌停就在这一层**。

为什么涨跌停不该进 Tier 1？4 个理由：

1. **factor value 是真实数据**：涨停日的 `$close = 涨停价`，这个 close 不是错误，是真实的市场价。`Div($close, $pe_ratio)` 在这一天的结果完全合法
2. **时序算子依赖连续数据**：`Mean($close, 20)` 的滚动窗口里如果人为制造空洞，后 14 天的值都是错的（少了一个有效点）
3. **Redundancy 需要同一批股票-日组合**：如果因子 A 剔除了涨停日，因子 B 没剔除，max_lib_corr 做不出来——样本不一致
4. **涨停本身是信息**：某些因子就是要捕捉"涨停后续行为"的。如果剔除涨停日，这类因子根本算不出来

涨跌停的问题**不是 "factor value 不对"**，**是 "基于这个 factor value 的交易做不了"**。所以只动交易层面的东西（return），不动 factor。

**关键时序细节**：mask 的对象是 **T+1 的 entry 状态**，不是 T 的 signal 状态。

标准 factor → trade 时序：
```
T 收盘：算 factor value
T+1 开盘：按 factor 信号下单 (entry)
T+1+H 收盘：平仓 (exit)
future_return = close_{T+1+H} / close_{T+1} - 1
```

真正决定"能不能成交"的是 **T+1 的状态**：

- T+1 一字涨停（`close == high == low == limit_up`）→ long 做不了 → `future_return[T] = NaN`
- T+1 一字跌停 → short 做不了 → NaN
- T 涨停但 T+1 正常 → T+1 可能 gap up，但 entry 是**可执行**的 → `future_return` 合法，**不 mask**

**注意**：判断涨跌停**看下一日 T+1**，不是 signal 日 T。这是很多人会错的地方。

**Tier 3：正常处理**（factor 和 return 都合法）

剩下的一切。

**为什么"完全剔除涨跌停股票"是错的**

4 个具体问题：

1. **时序连续性被破坏**：`Mean($close, 20)` 在 T+1 要用 T-18 到 T+1 的 20 天价格。涨停日设 NaN 等于人为制造空洞
2. **同一股票在不同因子里样本不一致**：A 因子剔除的日子和 B 因子剔除的日子不同 → 两个因子的 max_lib_corr 做不出来
3. **Look-ahead bias**：如果规则是"如果明天涨停就剔除今天"，你**用了明天的信息**过滤今天的 factor——是偷看未来
4. **丢失涨停后续行为的信息**：涨停→连板是真实的市场现象，因子要识别它就必须看到涨停日的 factor value

**Tier 2（只 mask return）避免了全部 4 个问题**。

#### 对照表：谁进哪一层

| 情况 | Tier | 动作 |
|---|---|---|
| 停牌（volume=0 / close=NaN） | **1** | factor + return 都 NaN |
| ST / \*ST | **1** | factor + return 都 NaN |
| 退市 | **1** | factor + return 都 NaN |
| 新股 < 60 天 | **1** | factor + return 都 NaN |
| 科创板 / 北交所（如不研究） | **1** | factor + return 都 NaN |
| T+1 一字涨停（long 信号） | **2** | 保留 factor，return NaN |
| T+1 一字跌停（short 信号） | **2** | 保留 factor，return NaN |
| T 涨停 + T+1 正常 | **3** | 正常处理 |
| 持仓期中间日涨跌停 | **3** | 不管（影响日内流动性，不影响 next-day 价格）|
| exit 日涨跌停 | **2** 或 **3** | 细节问题，通常"顺延一天平仓"，影响小 |

#### 正确实现的 pseudo-code

```python
# Step 1: 构建 tier 1 mask
tier1_mask = (
    is_suspended(data)            # 停牌
    | is_st(data)                  # ST
    | is_new_stock(data, days=60)  # 新股 60 天
    | is_star_market(data)         # 科创板
    | is_bse(data)                 # 北交所
)

# Step 2: 应用 tier 1 到 factor value
factor_values = compute_factor(raw_data)
factor_values[tier1_mask] = np.nan   # 完全剔除

# Step 3: 单独计算 future_returns
future_returns = compute_future_returns(raw_data, horizon=5)

# Step 4: Tier 2 mask — 针对 RETURN 而不是 factor value
# 注意：看的是 T+1 的状态，不是 T
is_entry_limit_hit = (
    (close_T1 == limit_up_T1)      # T+1 一字涨停
    | (close_T1 == limit_down_T1)  # T+1 一字跌停
)
future_returns[is_entry_limit_hit] = np.nan

# Step 5: 算 IC
ic = compute_ic(factor_values, future_returns)
# pandas 的 corr 自动跳过任何 NaN pair
```

几个关键点：
1. **Tier 1 mask factor value**（`factor_values[mask] = NaN`）
2. **Tier 2 mask future_return**（`future_returns[mask] = NaN`）
3. **Tier 2 的条件是 T+1 的状态**
4. **IC 函数自动处理 NaN**—两者其中一个是 NaN 时这一对被跳过

### 针对本系统的实施路径（按 3 个 phase 落地）

上面的三层框架是理论。具体到当前 repo，实施有**数据可用性**和**历史兼容性**两个真实约束。下面是按"能力阶梯"设计的 3 个 phase 路径。

#### Phase 0：盘点当前实际能做的 vs 需要新数据的

对照三层框架对应到当前系统的数据可用性：

| 过滤条件 | 现在**能**做 | 缺什么 |
|---|---|---|
| 停牌 | ✅ 能——`$close.isna()` + `$volume == 0` 组合识别 | 无 |
| 涨跌停（T+1 entry） | ✅ 能——`$close == $limit_up / $limit_down`，**`limit_up/down` 已在 qlib binary** | 无 |
| 科创板（688*） | ✅ 能——`instrument.startswith("688")` | 无（用 instrument code 前缀）|
| 北交所（8*, 4*） | ✅ 能——`instrument.startswith(("8", "4"))` | 无（同上）|
| ST / \*ST | ❌ **不能**——qlib binary 里没有 `$is_st` 字段 | 需要同步 `$is_st` |
| 新股 < 60 天 | ❌ **不能**——没有 `$list_date_dist` | 需要同步 `$list_date_dist` |
| 退市 | ⚠️ 部分——靠 universe 成分股历史隐式处理 | 需要严格的时间对齐 index_constituents |

**Phase 1 可以立即做 4 个**（停牌 / 涨跌停 / 科创板 / 北交所），**Phase 2 需要数据同步**（ST / 新股）。

#### Phase 1：零新数据成本的修复（2–3 天）

**目标**：用现有数据把**能做的 Tier 1 + Tier 2** 都启用。

**⚠️ 关键分层原则**（在具体 Step 之前必须先理解）：

过滤不能全部放在一个层次。看每个过滤的**本质**，决定放在哪层：

| 过滤 | 本质 | 正确层 | 为什么 |
|---|---|---|---|
| **停牌** | 数据不存在 | **Qlib binary 层**（`resync_qlib.py`） | OHLCV 本来就该是 NaN，时序算子才能自动正确处理传播 |
| **涨跌停** | 数据合法，交易不可执行 | **Return 层**（`get_returns`） | close 价格是真实的，只 mask return 不动 factor |
| **科创板 / 北交所** | 数据合法，市场结构不同 | **Preprocess 层** | 靠 instrument code 前缀，mask factor value |
| **ST / 新股**（Phase 2） | 数据合法，不属于研究样本 | Preprocess 层 | 需要新的 aux 字段 |

**为什么停牌必须 binary 层**：如果在 preprocess 层事后 mask，`Mean($close, 20)` 已经被前一天的 freeze close 污染——mask 只能抹掉停牌日本身，**阻止不了污染向后传播 14 天**。只有在 binary 层把 OHLCV 设为 NaN，时序算子才能用 pandas rolling 的 `min_periods` 自动跳过。

**为什么涨跌停不能 binary 层**：涨停日的 close 是真实市场价。如果设为 NaN，任何用到"T-3 close"的时序算子都会少一个合法数据点。而且某些因子需要看到涨停信息（连板模式）。所以涨跌停只能在 return 层处理。

**以下 Step 分三个层次推进**：

##### Phase 1A：修改 `scripts/resync_qlib.py`（**binary 层 / 停牌**）

```python
# scripts/resync_qlib.py 的数据清洗步骤
def _clean_suspended_days(df):
    """
    停牌日的 OHLCV 设为 NaN，让 Qlib 时序算子自动正确处理传播。
    判断：volume=0 或 amount=0（没有真实交易额）。
    注意：不能用 close.isna()，因为当前 qlib binary 里停牌日的 close 是前一天 freeze 值，不是 NaN。
    """
    stopped = (df['volume'] == 0) | (df['amount'] == 0)
    df.loc[stopped, ['open', 'high', 'low', 'close', 'vwap', 'amount', 'volume']] = np.nan
    return df

# 在 DataSynchronizer.sync() 的数据处理链路里调用
df = self._clean_suspended_days(df)
```

**执行**：
```bash
PYTHONPATH=src python3 scripts/resync_qlib.py   # ~1 分钟
rm -rf storage/runtime/cache/research/*.parquet  # 作废旧缓存
# 下次 execute 时 DB factor_values 会自动重算
```

**影响**：
- Qlib 读到停牌日自动返回 NaN
- `Mean($close, 20)` 用 `min_periods=15`（可配置），自动跳过 NaN 点
- 时序污染**从根源上**被解决
- **此 Step 完成后 `_apply_tradability` 方法可以标记为 deprecated 或删除**——不再需要 preprocess 层的事后 mask

**代价**：数据迁移 + 缓存清空。~10 行代码 + 一次性 ~10 分钟操作。

##### Phase 1B：修改 `data_provider.py::get_returns`（**Return 层 / 涨跌停**）

```python
def get_returns(self, start, end, horizon=1, mask_limit_hit=True):
    ret = self._compute_raw_returns(start, end, horizon)
    
    if mask_limit_hit:
        close = self.get_market_data(["$close"], start, end)
        limit_up = self.get_market_data(["$limit_up"], start, end)
        limit_down = self.get_market_data(["$limit_down"], start, end)
        
        # 一字板检测（close == limit_up 就是一字涨停）
        is_limit_hit = (
            (close["$close"] == limit_up["$limit_up"])
            | (close["$close"] == limit_down["$limit_down"])
        )
        
        # 关键：mask 的是 **entry 日**的状态
        # 当前 get_returns 的语义是 return[T] = close[T+h]/close[T] - 1
        # entry 日就是 T 本身，所以检查 T 的一字板状态
        ret[is_limit_hit] = np.nan
    
    return ret
```

**关键：此 Step 只 mask return，不动 factor value**。涨跌停日的因子计算照常进行，只是对应的 future_return 变 NaN。

**代价**：~20 行代码。

##### Phase 1C：修改 `preprocess.run()`（**Preprocess 层 / 科创板 + 北交所**）

只处理 "合法数据但不该进研究样本" 的情况。**不再处理停牌**（已经在 Phase 1A 解决）。

```python
def _apply_tier1_mask(self, factor_df, config):
    """Tier 1: 合法数据但不在研究样本内——factor value 设为 NaN"""
    col = factor_df.columns[0]
    instruments = factor_df.index.get_level_values("instrument")
    
    # 科创板（688*）
    if config.exclude_star_market:
        star_mask = instruments.str.startswith("688")
        factor_df.loc[star_mask, col] = np.nan
    
    # 北交所（8*, 4*）
    if config.exclude_bse:
        bse_mask = instruments.str.startswith(("8", "4"))
        factor_df.loc[bse_mask, col] = np.nan
    
    # 注意：不处理停牌（已在 binary 层解决）
    # 注意：不处理涨跌停（在 return 层解决）
    
    return factor_df

def run(self, factor_df, config=None, ...):
    result = factor_df.copy()
    
    # Tier 1 首先——必须在 winsorize / zscore 之前
    if config is not None:
        result = self._apply_tier1_mask(result, config)
    
    result = self._winsorize(result)
    result = self._zscore(result)
    return result
```

**顺序关键**：Tier 1 必须在 zscore **之前**，否则被剔除股票的 factor value 会污染截面 mean / std。

**代价**：~40 行代码 + 4 个调用点改造（`compute_implementations.py:146`、`:251`、`factor_engine.py:76`、`:139`）。

##### Phase 1D：config flag 接通

新增 `UniverseConfig` 字段并在 `research_config.yaml` 显式配置：
```python
exclude_star_market: bool = True
exclude_bse: bool = True
# 注意：filter_suspend 保留但默认关闭（已由 binary 层处理）
# filter_limit 保留但改为只控制 Phase 1B 的 get_returns mask
```

```yaml
universe:
  universe_id: csi1000
  filter_suspend: false         # binary 层已处理，preprocess 层不再需要
  filter_limit: true             # 控制 get_returns 的 mask
  exclude_star_market: true
  exclude_bse: true
```

**代价**：~10 行代码 + 一个 yaml 更新。

##### Phase 1E：记录 filter_version 到 research_result

```yaml
batch_id: batch_104
filter_version: "v1"
filter_config:
  binary_level:
    suspended_masked: true          # Phase 1A 完成
  return_level:
    limit_hit_masked: true          # Phase 1B 完成
  preprocess_level:
    exclude_star_market: true       # Phase 1C 完成
    exclude_bse: true               # Phase 1C 完成
  tier1_complete: false             # ST / 新股 要到 Phase 2
```

字段结构显式反映**三层过滤**的分工，而不是把所有过滤混在一起。这样未来做 v0→v1→v2 的对比时能精确知道每个版本做了什么。

**代价**：~5 行代码。

##### Phase 1 完成后的状态总结

| 层次 | 处理的过滤 | 实现位置 |
|---|---|---|
| **Qlib binary** | 停牌（时序污染根治） | `scripts/resync_qlib.py` |
| **Return 层** | 涨跌停 | `data_provider.py::get_returns` |
| **Preprocess 层** | 科创板 / 北交所 | `compute/preprocess.py` |

**不做的事**（留给 Phase 2）：
- ST 过滤（需要 `$is_st` 数据同步）
- 新股 60 天冷却（需要 `$list_date_dist` 数据同步）
- 重新评估历史 19 个 factor

##### Phase 1 Step 5：记录 filter_version 到 research_result

在每份 `research_result.yaml` 里新增字段：

```yaml
batch_id: batch_104
filter_version: "v1"                    # ← 新增
filter_config:                           # ← 新增
  filter_suspend: true
  filter_limit: true
  exclude_star_market: true
  exclude_bse: true
  tier1_mask_applied: true
  tier2_return_mask_applied: true
```

**作用**：
- 区分 pre-filter 和 post-filter 的因子结果
- 未来做跨 batch 对比时知道哪些是可比的
- judge 层可以对 `v0` 和 `v1` 用不同的 admit 门槛（v0 的 IC 被涨跌停膨胀过，应该打个折扣）

**代价**：~5 行代码。

##### Phase 1 交付标准

完成 Phase 1 后：
- 新的 batch 启动 execute 会自动启用 Tier 1（停牌/科创/北交）和 Tier 2（涨跌停）
- 现有 19 个 library factor 还是 v0，下次 prepare_batch 时走 v0 的 IC（除非重算）
- `research_result.yaml` 带 `filter_version: "v1"` 标记

**不做的事**（留给 Phase 2）：
- ST 过滤
- 新股 60 天冷却
- 重新评估历史 19 个 factor

#### Phase 2：补齐数据同步（1 周左右）

**目标**：把 Phase 1 缺的两个字段同步到 qlib binary，然后接通 Tier 1 的剩余条件。

##### Phase 2 Step 1：ricequant → timescale 同步 `is_st` 和 `list_date_dist`

1. `src/data/ricequant_source.py`：在 `DAILY_FIELDS_WITH_LIMITS` 加入：
   ```python
   DAILY_FIELDS_WITH_LIMITS = [
       'open', 'high', 'low', 'close', 'volume',
       'limit_up', 'limit_down',
       'is_st',                    # ← 新增
       # listed_date 是股票级元数据，另外同步
   ]
   ```

2. `src/data/storage/timescale_storage.py`：在 `price_daily` 表定义加一列：
   ```sql
   is_st BOOLEAN,          -- ⭐ ST 状态
   ```
   
3. 新增一张 `stock_listing_date` 表（股票级，不是日度）：
   ```sql
   CREATE TABLE stock_listing_date (
       symbol VARCHAR(20) PRIMARY KEY,
       listed_date DATE NOT NULL
   );
   ```
   从 RiceQuant 的 `all_instruments` 一次性拉取。

##### Phase 2 Step 2：qlib binary sync 新字段

1. `src/data/qlib_sync.py`：在 `AUX_FIELDS` 加 `is_st`
2. 新增 `$list_date_dist` 作为**虚拟字段**——在 sync 时计算 `(current_date - listed_date).days` 并写入 binary

##### Phase 2 Step 3：接通 Tier 1 剩余过滤

在 `preprocess._apply_tier1_mask` 里加：

```python
# ST 过滤
if config.filter_st:
    mask = aux_fields["$is_st"] == True
    factor_df.loc[mask, col] = np.nan

# 新股冷却
if config.min_listing_days > 0:
    mask = aux_fields["$list_date_dist"] < config.min_listing_days
    factor_df.loc[mask, col] = np.nan
```

##### Phase 2 Step 4：升级 filter_version 到 v2

当 Phase 2 完成时，新的 batch 标记：
```yaml
filter_version: "v2"
filter_config:
  ...
  filter_st: true
  min_listing_days: 60
```

#### Phase 3：历史兼容性（可选，按需）

**问题**：过去 100+ batch 和 19 个 library factor 都是 `filter_version: "v0"`——在 pre-filter 的 IC 下 admit 的。这对系统的影响：

1. 新的 candidate（v1+）的 IC 和历史 factor 的 max_lib_corr **样本不一致**
2. Judge 做 replace 比较时，新老 factor 的门槛不对等
3. F018 / F019 等 admit 的合理性需要重新验证

##### 方案 3.1（推荐）：懒惰迁移

**不主动重评历史 factor**，但引入两条规则：

**规则 A**：max_lib_corr 计算时对 v0 的 library factor 做折扣：
- 如果一个新 v1 candidate 和 v0 F005 的相关性是 0.75，认为它们可能实际上是 0.70-0.80 区间（v0 IC 里含有涨跌停噪声）
- 不做严格折扣，但在 reserve 判据里宽一档

**规则 B**：judge 层对 v0/v1 跨比较做明确警告：
- 如果一个新 v1 candidate 的 IC 比 v0 的 F018 低但方向一致，**不直接判 replace**
- 先标记 "cross-version comparison uncertain"，让人工审阅

##### 方案 3.2（严格）：重评历史 factor

跑一个 `scripts/reevaluate_registry.py`：
1. 对 registry 里每个 factor，用 v1 过滤重新跑 execute
2. 更新 `factor_FXXX.yaml` 的 metrics 字段
3. 记录 `evaluation_version_history: [v0_2026_04_06, v1_2026_04_15]`
4. 如果新 metrics 不再达到 admit 门槛 → 状态转 `retired_by_filter_upgrade`

**代价**：19 个 factor × 每个几分钟 compute + analyze = ~1-2 小时。但需要手动审阅结果。

##### 推荐：方案 3.1（懒惰迁移）

除非你有特别理由相信涨跌停 bias 污染严重，否则懒惰迁移更经济。代价换来的是"新老不可完美比较"的治理复杂度。

#### 实施时序建议

```
第 1 天：Phase 1 Step 1-2   （prepare_batch + get_returns，涨跌停 Tier 2 启用）
第 2 天：Phase 1 Step 3-4   （Tier 1 mask + config 接通）
第 3 天：Phase 1 Step 5 + 测试  （filter_version 标记 + 跑一个新 batch 验证）
——— Phase 1 完成，新 batch 自动享受停牌/涨跌停/科创/北交过滤 ———

第 4-6 天：Phase 2 Step 1-2   （数据同步管道改造，ST + listing_date）
第 7 天：Phase 2 Step 3-4    （接通 Tier 1 剩余 + filter_version v2）
——— Phase 2 完成，新 batch 享受完整 7 层过滤 ———

第 8 天及以后：Phase 3 视情况处理历史兼容
```

#### 各 phase 能立即带来的改变

| 修复完成后 | Phase 1 | Phase 2 |
|---|---|---|
| 停牌日 IC 污染 | ✅ 修复 | ✅ |
| 涨跌停日虚假 return 参与 IC | ✅ 修复 | ✅ |
| 科创板 / 北交所不小心进 universe | ✅ 修复 | ✅ |
| ST 股票污染 | ❌ 仍未 | ✅ 修复 |
| 新股 IPO 异常污染 | ❌ 仍未 | ✅ 修复 |
| 可以安全做跨池子评估（Q14.5）| ❌ 不建议 | ✅ 可以 |
| 可以安全做 CsRank 池内化（Q15）| ❌ 不建议 | ✅ 可以 |

**Phase 1 就能解锁 4 个重要下游改造**（Q14/Q15/Q16 主体）。这是性价比最高的 3 天工作。

### 可行方案

**方案 A（必做，识别涨跌停）**：在 `prepare_batch` 或 `get_returns` 里加一步 limit_hit 检测：

```python
def get_returns_with_limit_mask(self, start, end, horizon=1):
    # 拉取 close / limit_up / limit_down
    close = self.provider.get_market_data(["$close"], start, end)
    limit_up = self.provider.get_market_data(["$limit_up"], start, end)
    limit_down = self.provider.get_market_data(["$limit_down"], start, end)
    
    # 识别一字板
    limit_hit = (close == limit_up) | (close == limit_down)
    
    # 算 return，然后 mask
    ret = (close.shift(-horizon) / close) - 1
    ret[limit_hit] = np.nan   # 一字板日的未来 return 设为 NaN
    
    return ret
```

代价：一次性 20 行代码。这是**最小代价最大收益**的修复——直接解决"IC 把涨跌停当正常日"的 bias。

**方案 B（必做，同步缺失字段）**：完成 `docs/superpowers/plans/2026-03-22-mining-preprocessing.md` 里承诺的 `$is_st` / `$list_date_dist` / `$industry_code` 同步：
1. 在 `ricequant_source.py` 的 `DAILY_FIELDS_WITH_LIMITS` 加入 `is_st`, `listed_date`, `industry_code`
2. 在 `timescale_storage.py` 的表定义加对应列
3. 在 `qlib_sync.py` 的 `AUX_FIELDS` 加对应字段
4. 重跑 `resync_qlib.py`

**方案 C（必做，消费 config flag）**：在 preprocess 或 prepare_batch 里真正读 `UniverseConfig.filter_suspend / filter_limit / min_listing_days`：

```python
def _apply_universe_filters(signal_df, market_df, config):
    if config.universe.filter_suspend:
        signal_df.loc[market_df["$volume"] == 0] = np.nan
    
    if config.universe.filter_limit:
        limit_hit = (market_df["$close"] == market_df["$limit_up"]) | \
                    (market_df["$close"] == market_df["$limit_down"])
        signal_df.loc[limit_hit] = np.nan
    
    if config.universe.min_listing_days > 0:
        # 需要 $list_date_dist 字段（方案 B 的前置）
        signal_df.loc[market_df["$list_date_dist"] < config.universe.min_listing_days] = np.nan
    
    return signal_df
```

这个调用点应该是**在 preprocess 的 run() 里**，且默认启用（不再用 `tradability_check=False` 绕过）。

**方案 D（推荐，显式 universe 过滤）**：不依赖"csi1000 副作用"，显式加一层 market-level 过滤：

```python
def _apply_market_filter(signal_df, config):
    # 股票代码前缀识别
    if config.universe.exclude_star_market:   # 科创板
        mask = signal_df.index.get_level_values("instrument").str.startswith("688")
        signal_df.loc[mask] = np.nan
    if config.universe.exclude_bse:             # 北交所
        mask = signal_df.index.get_level_values("instrument").str.startswith(("8", "4"))
        signal_df.loc[mask] = np.nan
    return signal_df
```

这样即使切换 universe 到 `all`，也能显式挡住不想要的 market。

**方案 E（推荐，index_constituents 时间对齐）**：
- 确保 `index_constituents` 表每天都有 csi1000 成分股
- 在 compute 阶段按**当天的**成分股列表过滤
- 避免"半年前的 csi1000 成分现在不在了"

### 优先级

A > C > B > D > E。

- **A 是最紧迫**的——一次 20 行代码，直接修复"涨跌停日参与 IC 计算"的系统性 bias。
- **C 紧跟**——读 config flag 这件事应该和 Q14 的"打开 tradability" 一起做。
- **B 是中等任务**——涉及数据同步管道改造。
- **D 和 E 是优化**——提升过滤精度和跨 universe 稳健性。

### 关联观察

- **Q16 是 Q14 的前置**：Q14 说"打开 tradability_check"，但当前 tradability 检查的条件（volume=0）识别不了涨跌停。Q16 方案 A + C 才是完整修复。
- **Q16 是 Q14.5（跨池子评估）和 Q15（CsRank 池内化）的前置**：不修 Q16，改 universe 就会让脏数据涌入。
- **Q16 揭示了一个"数据到了但没人用"的模式**：`limit_up / limit_down` 字段被完整地从 RiceQuant → DB → qlib binary 同步下来，但下游消费代码不存在。这是一个**纵向全链路但缺最后一步**的结构。类似地，`$is_st` 可能会重蹈覆辙——即使 Q16 方案 B 把数据同步上了，如果没人写消费代码，一样是 dead data。所以方案 B 必须和方案 C 配套。
- **Q16.3（计划文档撒谎）** 是 Q14.5 之后又一条证据：**文档声明的能力并未在代码中存在**。这个问题的频率和严重性都在增加。建议：在 skill.md / plan docs 里加一条规约：**任何"已就位"声明必须引用可 grep 的具体代码位置**，否则被视为未实现。

---

## Q17 — 市值/行业中性化：数据半缺、命名撒谎、架构位置正确但执行不完整

**提问时间**: 2026-04-11
**相关阶段**: Phase 2 `/factor-execute` Step 9 风险评审 / Step 3 preprocess / 整个研究框架的哲学

### 事实清单

**数据源**：

| 中性化类型 | 数据字段 | 同步状态 |
|---|---|---|
| **市值** | `$circ_market_cap` | ✅ RiceQuant → TimescaleDB → qlib binary 全链路存在 |
| **行业** | `$industry_code` / `$sector_code` | ❌ **完全没有**，`mining-preprocessing.md` 标为 "future work" |

**代码实现**：

市值中性化：`src/research/risk/neutralization.py::neutralize_cap`
- 数学做法：per-date OLS 回归 `y = a + b * log(cap) + residual`
- 向量化实现，数学正确
- 调用者：`risk/engine.py`（风险评审 Step 9）
- 输出：`cap_neutral_ic`，作为 judge packet 的辅助指标

行业中性化：**完全不存在**

**schema 撒谎的字段**（`src/research/risk/schema.py:16`）：
```python
cap_industry_neutral_ic: Optional[float] = None
# cap-only degradation; name kept for doc alignment
```

**字段名叫 `cap_industry_neutral_ic`，注释里承认 "cap-only"**。"name kept for doc alignment" 是一个**主动保留的谎言**——有人写文档时说"我们有 cap + industry 联合中性化"，后来只实现了 cap，字段名没改。任何读 schema 的人（包括 judge LLM）都会被误导。

**另一个孤儿 neutralize**（Q14 里提过）：

`src/research/compute/preprocess.py::_neutralize` 只做 group demean，默认关闭（`neutralize_col=None`），从没启用。和 `risk/neutralization.py::neutralize_cap` 完全不兼容，构成两套平行的"中性化"概念，命名重合但语义不同。

### 架构位置判断：**风险评审层是对的，preprocess 层是错的**

这里有一个**重要的架构决定**：中性化该放在哪一层？

**选项 1：preprocess 层（硬中性化）**

```
factor_value_raw
  → cap neutralize        ← 在 preprocess 里直接改 signal
  → industry neutralize
  → winsorize / zscore
  → 所有下游 IC / quintile / redundancy 都基于"已净化" signal
```

后果：
- 所有指标（ic_mean、ic_ir、mono、ls_tstat）都是中性化之后的
- 不存在"原始 IC"这个概念
- 历史评估不可回看到 raw view
- **研究框架隐式决定了"什么是 alpha"——这是一个重大承诺**

**选项 2：风险评审层（软中性化 / 当前做法）**

```
factor_value_raw
  → preprocess (只做 winsorize + zscore)
  → 计算 raw IC
  → 【独立】cap neutralize → 得 cap_neutral_ic
  → 【独立】barra residual → 得 barra_residual_ic
  → 三个 IC 并列呈现给 judge
```

后果：
- 主指标仍然是 raw IC
- 中性化 IC 是**辅助视角**，不替代 raw
- judge 层做组合判断：raw 强 + residual 也强 = 真 alpha；raw 强 + residual 弱 = style 重包装
- 每个因子都保留多个视角，便于复盘和框架演进

**当前系统用的是选项 2**——这是对的。cap_neutral_ic 和 barra_residual_ic 都是**独立的 judge packet 字段**，不替换 raw IC。

### 为什么选项 2 是对的

4 个理由：

1. **不提前决定"alpha"的定义**：一旦把 cap 硬中性化，任何"小市值溢价"这种真实市场 anomaly 就看不到了。而 size premium 在 A 股是非常真实的 alpha 来源
2. **可复盘**：历史数据里有 raw + neutral 多套 IC，想切换到不同的 risk model 也能做
3. **不依赖完美的 risk model**：A 股的行业划分本身就不稳定（GICS/申万/中信三套），risk model 不完美时 raw IC 仍然独立有价值
4. **让 judge 做组合判断**：这是 judge 最重要的能力——看多个视角对比，而不是"一个数字 pass/fail"

### 但当前执行有 3 个不足

**不足 1：行业中性化承诺了但完全没做**

`cap_industry_neutral_ic` 字段名暗示做了 cap + industry 联合中性化。实际只做 cap。这是命名层面的撒谎，和 Q14（docstring 撒谎）、Q16（config 撒谎）、Q10（plan 文档撒谎）同一个家族。

**不足 2：preprocess 层有孤儿 `_neutralize` 占位**

和 risk engine 层的 `neutralize_cap` 完全不兼容的另一套"中性化"概念。默认关闭，从没启用。应当：
- 删除（推荐）
- 或明确标注 deprecated，和 risk engine 的 neutralize 区分开

**不足 3：三个 IC 视角的关系没有结构化呈现**

当前 judge 看到的是孤立的三个数字：
```
ic_ir_validation: 0.338
cap_industry_neutral_ic: 0.25  (实际只是 cap)
barra_residual_icir: 0.251
```

没有告诉 judge "从 raw 到 cap-neutral 衰减了多少"、"从 cap-neutral 到 barra-residual 又衰减了多少"。判断能力被限制在"看这三个数是否都大于阈值"，而不是"看衰减曲线揭示了什么"。

### 理想的最终形态：中性化层次分解视图

```yaml
# judge packet 新增 neutralization_decomposition 段落
neutralization_decomposition:
  raw_ic: 0.046                         # 原始 IC
  after_cap_neutral: 0.040              # 剔除 log(cap)
  after_industry_neutral: 0.038         # 单独剔除行业均值
  after_cap_industry_neutral: 0.036     # 联合剔除 cap + industry
  after_full_barra_residual: 0.032      # 剔除所有 7 个 Barra style
  
  # 衰减分析
  cap_absorption: 0.13                  # (0.046 - 0.04) / 0.046
  industry_absorption: 0.17             # (0.046 - 0.038) / 0.046
  joint_absorption: 0.22
  full_barra_absorption: 0.30
```

这让 judge 能回答：
- 这个因子主要被哪类 risk 吸收？（cap / industry / 其他 style）
- 衰减曲线是否平缓？（平缓 = 真 alpha；某一步陡降 = 那类 risk 的重包装）
- 是否值得在 risk-neutral 框架下录取？（barra_residual 足够大就可以）

这比当前"三个孤立数字"的信息量大得多。

### 为什么重要

1. **行业中性化是 A 股因子研究的标准配备**。没有它，任何在行业间有显著差异的因子都无法区分 "stock selection alpha" vs "sector rotation alpha"
2. **字段名撒谎扩散到 judge 层**。judge 看到 `cap_industry_neutral_ic` 会以为系统已经做了 industry 剔除，实际没做——这会让 judge 对 F018 这种 "ep_ratio exposure=0.222" 的因子错判（以为 industry effect 已处理）
3. **孤儿 preprocess neutralize** 是未来 bug 的温床。如果有新 LLM 读代码发现它，可能会尝试启用它——结果会和 risk engine 层的中性化冲突
4. **三个 IC 孤立呈现**的现状限制了 judge 的判断能力。加衰减视图是**低成本高收益**的改进

### 可行方案

**方案 A（推荐，先修字段名）**：把 `cap_industry_neutral_ic` 改名为 `cap_neutral_ic`（已经有了），删掉误导性的字段名。代价：改 schema + 更新 judge packet 格式 + 迁移历史 batch（或标记旧版本）。

**方案 B（推荐，同步行业数据）**：
1. 在 `ricequant_source.py` 加 `industry_code` 字段（RiceQuant 的 `shenwan_instrument_industry` 或 `industry_code`）
2. 在 `timescale_storage.py` 的股票级表（不是日度表）加 `industry_code` 字段
3. 在 `qlib_sync.py` 或单独的 provider 里提供 `get_industry_map()` 方法
4. 新增 `risk/neutralization.py::neutralize_industry` 函数（按 industry dummy 做回归取残差，或更简单的 group demean）
5. 新增 `risk/neutralization.py::neutralize_cap_industry` 做联合中性化
6. 在 risk engine 里同时计算 cap / industry / cap+industry 三个视角

**方案 C（必做，删孤儿 neutralize）**：删除 `src/research/compute/preprocess.py::_neutralize` 方法，或明确改名为 `_group_demean` 并 deprecate。防止"两套不兼容的中性化"并存。

**方案 D（推荐，中性化衰减视图）**：在 judge packet 里增加 `neutralization_decomposition` 段落，显式呈现 raw → cap → industry → joint → full barra 的 5 层衰减。让 judge 看到"因子 alpha 被每层吸收了多少"。

**方案 E（可选，preprocess 层保持纯净）**：明确禁止 preprocess 层做任何中性化。所有中性化都在 risk engine 层作为"额外视角"产出。写进 `compute/preprocess.py` 的 docstring 和 skill.md。

### 优先级

A + C 立即做（修正撒谎字段名 + 删除孤儿代码，零成本）。
D 推荐（在现有 cap 中性化之上加衰减视图，不需要新数据）。
B 中等工作量（需要新的数据同步管道，类似 Q16 Phase 2）。
E 文档级，但应当和 A/C 同步完成。

### 背后的哲学：Research framework 的可演进性

这个问题最深的层次是：**一个研究框架应该在哪个时间点 "决定什么是 alpha"？**

- **选项 1（preprocess 硬中性化）**：在 data preprocessing 阶段就决定。简单、一致，但**不可逆**——一旦决定 cap 不是 alpha，所有历史数据都锁在这个框架里
- **选项 2（risk 软中性化 / 当前做法）**：在 judge 阶段用"多视角对比"决定。复杂、灵活，**框架可以演进**——同一批历史数据可以在不同 risk model 下被重新解读

量化研究里有一条重要的经验法则：

> **"让判断晚发生" (defer judgment)**

原因是你对市场的理解会演进，risk model 会更新，"什么是 alpha 什么是 risk" 会重新划分。如果你在 data pipeline 阶段就固化一个判断，后续任何 framework 升级都会付出巨大代价（所有历史数据要重评）。反之如果判断晚发生，历史 raw IC 始终保留，框架更新只需要"重新组合"而不是"重算"。

当前系统选了路径 2，这是**正确的哲学选择**。Q17 要解决的是**这条路径执行不彻底**的问题——视角不全、字段撒谎、孤儿代码没清理。

### 关联观察

- Q17 和 Q14.4（preprocess 的 neutralize 孤儿）是**同一个根因的两个面**。Q14.4 从 preprocess docstring 讲错的角度切入，Q17 从研究框架哲学的角度切入。两个合起来才是完整图景
- Q17 和 Q14 / Q16 / Q10 是同一个家族：**文档/字段名承诺了实际没做的能力**。这个家族的总数正在增加，建议加一条系统性约束：任何"承诺"都必须有可 grep 的代码证据
- Q17 方案 D（衰减视图）和 Q11（自主探索循环）的 meta-reflect 层相关——如果 judge 能看到 "因子被哪层 risk 吸收"，reflect 就能更好地总结"为什么一类假设反复被某个 risk 吸收"，从而提议新的正交方向
- Q17 的哲学原则（defer judgment）和 Q11 的设计目标是一致的——保留多视角、让框架可演进、不提前固化判断

---

## Q18 — IC 评估的两个隐含假设：固定 horizon=5 + 涨跌停 bias 对短/长期因子的反向偏差

**提问时间**: 2026-04-11
**相关阶段**: Phase 2 `/factor-execute` Stage C 维度 1（Effect Strength）+ Q16 涨跌停处理

### 用户原始问题

1. 涨停出现时 IC 计算会怎么样？
2. 我们是永远计算 T+1 的 IC 吗？会考虑长期 horizon 吗？

这两个问题看起来不相关，但指向同一个元问题：**IC 的计算有两个隐含假设没被充分检验**。

### 事实 1：主 IC 用 horizon=5，不是 T+1

代码证据（`compute_implementations.py:282`）：

```python
returns_flat = self._shared.returns_flat.get((full_start, full_end, 5))
```

主 effect_strength 计算用 `(full_start, full_end, 5)` 这个 key——即 **horizon=5 天**的 forward return。

具体定义（`data_provider.py:149`）：
```python
expr = f"Ref($close, -{horizon}) / $close - 1"
# horizon=5: close[T+5] / close[T] - 1
```

语义：**"T 收盘买入，持有 5 天，到 T+5 收盘卖出"** 的总收益。

这不是 T+1（次日）IC。**是 5 天持仓期 IC**。

### 事实 2：多 horizon 被预取但只部分使用

`prepare_batch` 预取了 5 个 horizon（`compute_implementations.py:99-106`）：

```python
for start, end, h in [
    (full_start, full_end, 5),       # 主 IC 用这个
    (val_start, val_end, 1),         # ← 预取了但 validation 不用
    (val_start, val_end, 5),
    (val_start, val_end, 10),        # ← 预取了但 validation 不用
    (val_start, val_end, 20),        # ← 预取了但 validation 不用
]:
    ...
```

各 horizon 的实际消费：

| horizon | 预取 | 实际用在哪里 |
|---|---|---|
| 5 day (full range) | ✅ | 主 effect strength + stability + reliability + redundancy |
| 1 day (validation) | ✅ | **仅 holdout 复审时的 auxiliary view** |
| 5 day (validation) | ✅ | redundancy 分析的 forward_returns |
| 10 day (validation) | ✅ | **仅 holdout auxiliary view** |
| 20 day (validation) | ✅ | **仅 holdout auxiliary view** |

**关键发现**：validation 期的主 IC **只在 horizon=5 上算一次**。h=1/10/20 的 returns 被预取并存在 shared data 里，**但 validation 评估完全不用它们**——只在 holdout 复审阶段作为多 horizon 对比视图。

这是一个**半成品设计**：数据路径铺好了，但消费代码没写。和 Q16 的 `limit_up` 同步了没人用、Q7 的 cleanup 跑空转、Q14 的 `_neutralize` 占位但从不启用——**同一类的半成品模式**。

### 事实 3：涨跌停没 mask 导致 IC 被膨胀（Q16 的延伸）

Q16 已经分析过：涨跌停日的 future return 没被 mask，直接进入 IC 计算。这里具体到每个 horizon：

| horizon | 涨跌停 bias 影响 |
|---|---|
| **h=1** | 最严重——T 涨停 → close[T+1] 很可能继续高 → 涨停股 return 被高估 |
| **h=5**（当前主 IC）| 中等——5 天内连板可能延续，也可能回落，bias 较小但仍存在 |
| **h=10** | 较小——10 天内多数涨停已经 play out |
| **h=20** | 很小——长期看涨跌停是噪声 |

**当前主 IC 是 h=5**，所以涨跌停 bias 不是最严重的情况。但仍然存在：csi1000 每天约 10-30 只涨跌停，一年 ~3000-7500 个涨跌停样本日。对短期动量因子，bias 可能让 IC 被高估 0.01-0.03（绝对值），足以让 borderline 因子跨过 admit 门槛。

### 问题 18.1：固定 h=5 对"慢信号"因子是系统性低估

不同类型因子有不同的自然 horizon：

| 因子类型 | 自然 horizon | 在 h=5 评估下的偏差 |
|---|---|---|
| 日内模式 / 短期反转 | 1-3 天 | h=5 太长 → IC 被低估 |
| 短期动量 / 跟随 | 3-10 天 | h=5 刚好 |
| 基本面 catalyst（如 F018 EPS 改变 × low PB）| 20-60 天 | **h=5 太短 → IC 被低估** |
| 反向价值 / mean reversion | 60-250 天 | h=5 完全不对 |

**F018 在 h=5 下 IC=0.046 是真实值**。但如果在 h=60 下看，IC 可能是 0.08+——因为 EPS 改变后的价格调整需要更长时间 play out。

**当前系统看不到 h=60 的视图**。F018 的 admit 决策只基于 h=5。这意味着：
- **所有慢信号因子都被系统性低估**
- L015 整个家族都是中长期价值催化剂类型，但被 h=5 评估框架压在 borderline
- batch_099-103 反复探索 L015 但指标总是 borderline，**可能部分原因是 horizon 选错了**

### 问题 18.2：涨跌停 bias 和 horizon 误选是**相反方向的偏差**

这两个偏差叠加起来产生一个系统性模式：

- **短期动量因子**（L001/L010/L011 家族）：涨跌停 bias **高估** IC，h=5 horizon **正好**合适 → 看起来比实际强
- **长期价值因子**（L015 家族）：涨跌停 bias 影响小（不到涨跌停股），h=5 horizon **太短** → 看起来比实际弱

**合起来：系统性地让短期因子在评估里显得比长期因子有优势**。但这个"优势"可能完全是评估框架的产物，不是因子本身的差异。

这可能解释了两个现象：
1. batch_099-103 反复在 L015 上挣扎——以为 L015 "borderline 可过"，其实 L015 在正确 horizon 下可能强得多
2. L001/L010/L011 这些短期因子 "validation 过了但 holdout 崩" 的反复现象——因为 validation 的涨跌停 bias 抬高了 IC，holdout 期涨跌停分布不同

### 问题 18.3：horizon 稳健性检查从不做

一个合理的 sanity check 是："主 horizon h=5 的 IC 在其他 horizon 下同号吗？"

- 如果 h=5 正但 h=1 / h=10 反号 → h=5 是特殊窗口，可能拟合
- 如果 h=1 / h=5 / h=10 都正且单调递减 → 短效因子，应用短 horizon
- 如果 h=5 < h=10 < h=20 → 慢效因子，应用长 horizon

**这个 check 在 validation 期完全不做**。数据都预取了（`returns_flat` 里有 h=1/10/20），但没有任何代码在 validation 期用它们。这就像买了一盒工具却只用最常见的那一把。

### 为什么重要

1. **F018 的 admit 合理性被低估**：它在 h=5 只能到 borderline，可能在正确 horizon 下是明显的强 alpha。当前评估可能让 L015 家族看起来比实际弱
2. **L010/L011 的 holdout 崩盘可能是涨跌停 bias**：validation 期被膨胀，holdout 期没那么多涨跌停，于是 holdout 崩
3. **挖矿方向被框架偏差引导**：如果系统能看到 "h=5 弱但 h=60 强" 的因子，挖矿会倾向于中长期方向；现在只看 h=5，系统倾向于短期因子——但短期因子的 bias 又让它们 holdout 崩。这是一个**恶性循环**
4. **预取的数据没用被浪费**：h=1/10/20 已经被计算并存在 memory 里，消费它们的代码成本接近零

### 可行方案

**方案 A（必做，先修 Q16 的涨跌停 mask）**：见 Q16 方案 A。涨跌停 bias 是主 IC 的直接污染源，必须先修。

**方案 B（推荐，validation 期多 horizon 展开）**：让 `compute_effect_strength` 返回多个 horizon 的 IC：

```python
def compute_effect_strength(factor_values, returns_dict, train_range, validation_range):
    """
    returns_dict: {1: returns_h1, 5: returns_h5, 10: returns_h10, 20: returns_h20}
    """
    result = {}
    for h, returns in returns_dict.items():
        ic_train = daily_cross_sectional_ic(...)
        ic_val = daily_cross_sectional_ic(...)
        result[f"ic_mean_validation_h{h}"] = ic_val.mean()
        result[f"ic_ir_validation_h{h}"] = ic_val.mean() / ic_val.std()
    
    # 主 IC 仍然是 h=5（保持向后兼容）
    result["ic_mean_validation"] = result["ic_mean_validation_h5"]
    result["ic_ir_validation"] = result["ic_ir_validation_h5"]
    
    # 新增：horizon 稳健性
    signs = [np.sign(result[f"ic_mean_validation_h{h}"]) for h in [1,5,10,20]]
    result["horizon_sign_consistency"] = all(s == signs[0] for s in signs if s != 0)
    result["horizon_peak"] = max([1,5,10,20], key=lambda h: abs(result[f"ic_mean_validation_h{h}"]))
    
    return result
```

代价：~40 行代码。数据已经预取，直接用。

**方案 C（推荐，加 horizon 稳健性到 judge packet）**：让 judge 看到：
- 主 IC h=5: 0.046
- IC h=1: 0.02
- IC h=10: 0.05
- IC h=20: 0.04
- horizon_sign_consistency: true
- horizon_peak: 10

judge 可以判断：
- "这个因子在 h=10 最强，建议在 productive 后用 h=10 再评估一次"
- "这个因子 h=1 反号，可能是窗口拟合"

**方案 D（长期，加长 horizon）**：把预取 horizon 扩展到 1/5/10/20/**40/60/120**。这涉及：
- `prepare_batch` 多预取几个 horizon
- `get_returns` 对长 horizon 的效率优化
- 存储层（runtime cache）可能需要更多空间

**方案 E（推荐，horizon 参数化配置）**：把主 horizon 从硬编码 5 改为 `UniverseConfig.primary_horizon`，可配置：

```yaml
universe:
  universe_id: csi1000
  primary_horizon: 5          # 可以改成 10 或 20
  secondary_horizons: [1, 10, 20, 60]   # auxiliary view
```

这让不同 logic 可以选不同的主 horizon——价值类用 h=20，短期类用 h=5。

### 优先级

A（Q16 的涨跌停 mask）>> B（validation 多 horizon）> C（judge packet 扩展）> E（参数化）> D（长 horizon 支持）

A 必须先做，因为没有它 h=5 主 IC 本身就是脏的。
B + C 一起做，一次性获得 "免费" 的多 horizon 视角（数据都已预取）。
E 是中期改进。
D 是长期能力扩展。

### 关联观察

- Q18 和 Q16 是同一条链路上的两个问题：Q16 是数据层的涨跌停未过滤，Q18 是评估层的 horizon 单点判断。修 Q16 不够，还需修 Q18 才能让 IC 完整可信
- Q18 和 Q11 自主探索循环高度相关：**一个只能看 h=5 IC 的系统，必然无法发现长 horizon 因子**。Q11 的 meta-reflect 层应当能识别这种"评估框架偏差"——观察到"所有 L015 类因子都在 borderline" 应该触发 "horizon 可能选错了" 的假设
- Q18 揭示的**"半成品优化"模式**（数据预取了但消费代码没写）是 Q6/Q7/Q14/Q16 共同的家族特征。这 5 个问题的 meta-pattern 是：**有人意识到该做但只做了一半，然后没人发现剩下一半没做**。这对 LLM 自治系统尤其危险——LLM 只会沿着现有路径 walk，不会主动检查"这条路径在底层是不是完整的"

### 补充（2026-04-11）：horizon 选择的粒度问题

用户追问："主 horizon 应该固定吗？还是 LLM 自主？还是跑全部再看？"

这个问题比 Q18 原方案更深——Q18 原方案 B 只说"展开多 horizon"，没说**谁决定主 horizon**。补充分析如下。

#### 四种选择路径的利弊

| 路径 | 粒度 | 谁决定 | 致命问题 |
|---|---|---|---|
| **全局固定** | 系统 | 代码写死 | 系统性偏差（慢信号低估、快信号被涨跌停 bias 膨胀）|
| **Candidate-level LLM 自由挑** | 每个候选 | /factor-idea 时 LLM 选 | ❌ **LLM 可以 cheat**（先跑所有 horizon 看哪个 IC 最高再宣布 "natural"），**同 batch 候选不可比**，**多重检验爆炸** |
| **全 horizon 跑** | 无选择 | 全部计算 | 计算成本 +60-100%，长 horizon 样本不足，judge 需要定义"主判据" |
| **Logic-level 声明**（推荐）| 每条 logic | logic 创建时声明 | 相对保守，需要给 logic 加字段 |

**Candidate-level LLM 自由挑是致命错误**。三条理由：
1. **LLM 可以 cheat**：先算几个 horizon 看结果，再宣布"这是自然 horizon"——这是 peeking，和 look-ahead bias 同性质
2. **同 batch 不可比**：C001 用 h=5，C002 用 h=20，max_lib_corr 算不出来
3. **多重检验爆炸**：自由挑 horizon 等于把搜索空间从 "expression" 扩展到 "expression × horizon"

**Logic-level 是正确粒度**：
- 每条 logic 在 contract 里声明 `primary_horizon` 和 `secondary_horizons`
- 新 logic 创建时走 4 维 review，horizon 声明**是 hypothesis 的一部分**（比如 "这是一个 60 天 catalyst"）
- candidate 被创建后，horizon 已经被 logic 决定，LLM 不能改
- execute 计算多 horizon 作为 sanity 视图，但**主判据是 logic 声明的那个**

这个方案的本质：**horizon 选择从"evaluation 阶段的自由"降级为"hypothesis 阶段的承诺"**。这是 "early commitment" 而不是 "late decision"——horizon 属于假设的一部分，不是评估的自由度。

#### 成本分析

**关键事实**：Factor value 计算不依赖 horizon。horizon 只影响 future return 和 5 维分析。

对一个 6-candidate batch：
```
当前 (h=5 only):
  Stage B (Qlib factor):    ~180 秒 (串行)
  Stage C (5 维 × 1 horizon): ~90 秒 (并行)
  总 ~5 min
  
路径 4 全 horizon (h=1/5/10/20):
  Stage B (Qlib factor):    ~180 秒 (不变)
  Stage C (5 维 × 4 horizon): ~270 秒 (并行)
  总 ~8 min (+60%)
  
Logic-level 3 horizon (如 primary=20, secondary=[5, 60]):
  Stage B:                  ~180 秒 (不变)
  Stage C (5 维 × 3 horizon): ~180 秒 (并行)
  总 ~6.5 min (+30%)
```

**增量成本来源 100% 是 5 维分析的 numpy 计算，不是 IO 或 Qlib。**

**长 horizon 的额外成本**：
- h=60 可接受（丢 2-3 个月 validation 样本）
- h=120 肉痛（丢 4 个月）
- h=250 几乎不可行（丢 1 年，样本腰斩）

#### 5 个可组合的成本控制策略

1. **Validation 期才多 horizon**：train 期保持 h=5，因为 train 主要用于算 decay_ratio。节省 ~70% 增量成本
2. **级联评估**：先 h=5 筛，borderline 再扩展。可能 50-70% 候选不需要跑全 horizon
3. **Logic 级 horizon 集**：每条 logic 只跑相关 3-4 个 horizon，不跑全 4
4. **Returns 复用**（已做到）：prepare_batch 已经预取所有 horizon 的 returns，增量成本全在 numpy 分析
5. **Filter_version 规避历史重评**：新 batch 跑多 horizon，老 batch 保持 h=5，judge 知道版本差异

#### 推荐的实施路径

**Phase A（立即，改 Q18 方案 B）**：
- 策略 1 + 策略 4：validation 期跑 h=1/5/10/20 四个 horizon，train 保持 h=5
- 主判据**仍然是 h=5**（保持历史可比）
- judge packet 新增 `horizon_sign_consistency` / `horizon_peak` 辅助字段
- 成本：+15-30% execute 时间
- 收益：能识别"h=5 正但 h=1 反 = 窗口拟合"、"h=5 borderline 但 h=20 强 = horizon 选错了"

**Phase B（中期，logic-level horizon）**：
- 给 `LogicCard.contract` 加 `primary_horizon` 和 `secondary_horizons` 字段
- 所有 15 条现有 logic 补声明（默认 h=5）
- 新 logic 创建时 4 维 review 强制要求声明 horizon
- execute 读 logic 声明，跑对应 horizon 集
- 主判据从"固定 h=5"改为"logic 声明的 primary_horizon"
- filter_version v2

**Phase C（长期，级联 + 长 horizon）**：
- 策略 2：级联评估
- 支持 h=60，可选 h=120
- execute 时间可能压回甚至低于当前

#### 有意思的副作用

Logic-level horizon 声明让 reflect 层能做新的 meta-check：

> "L015 声明 primary_horizon=20，但过去 5 个 batch 的 candidate 里，horizon_peak 有 4 次是 h=40 而不是 h=20。建议：logic 的 horizon 应该改为 40。"

**这是 Q11 meta-reflect 层的一个具体落地点**——系统自动发现自己的框架假设错了。

#### 和 Q18 原方案的关系

- Q18 方案 B 说"validation 多 horizon 展开" → 是 Phase A
- Q18 方案 E 说"horizon 参数化配置" → 等价于 Phase B 但放在 config 而不是 logic
- 本次补充的**新洞察**：应该放在 **logic 层而不是 config 层**，因为 horizon 是 hypothesis 的属性，不是系统配置
- Phase B 建议改为：**logic.contract 级**的 horizon 声明，而不是 config 级

### 二次补充（2026-04-11）：horizon 影响范围比原估更广 + 静默双真相 bug

用户追问"h 是只影响第一个评估指标还是所有"。这让我去完整梳理依赖链，发现：

#### Horizon 影响的完整依赖图

| 阶段 | 子任务 | 依赖 horizon？ |
|---|---|---|
| Stage A Precheck | — | ❌ |
| Stage B Base signal | 计算 factor value | ❌（factor value 和 horizon 无关）|
| Stage B Preprocess | winsorize / zscore | ❌ |
| Stage C Effect Strength | IC / ICIR / mono / ls_tstat | ✅ **硬编码 h=5** |
| Stage C Stability | split / regime / train_val decay | ✅ **共享同一份 returns_flat** |
| Stage C Reliability | expanding window / bootstrap | ✅ **共享** |
| Stage C Support Windows | 其他窗口 IC | ✅ **共享** |
| Stage C Multiple Testing | ledger 计数 | ❌（纯计数）|
| Stage D **Redundancy** | subspace residual IC | ⚠️ **部分依赖**（pairwise 不依赖，subspace 依赖）|
| Stage D **Risk Review** | raw IC / cap_neutral_ic / **barra_residual_ic** | ✅ **读 `profile.holding_horizon`**，默认 5 |
| Stage E Feasibility | turnover / coverage | ❌ |
| Stage E Feasibility | **half_life** | ✅ **已经用 h=1/5/10/20 多 horizon**（唯一用多 horizon 的地方）|
| Stage E Gate / Packet | — | ❌ |
| Holdout view | holdout IC / mono | ✅ **共享 h=5 returns_flat** |

**结论**：**h 不只影响 Stage C 的 effect strength 一个指标**。它影响：
- Stage C 的前 4 个维度（除了 multiple testing）
- Stage D 的 redundancy subspace residual IC
- **Stage D 的整个 Risk Review（cap_neutral + barra residual）**
- Holdout view
- 只有 Feasibility 的 half_life 已经在用多 horizon（但只用来算一个单一的 half_life 数字）

#### 问题 18.4：Horizon 有两个"真相来源"（silent bug）

**真相来源 1**：`compute_implementations.py:282` 硬编码 `5`
```python
returns_flat = self._shared.returns_flat.get((full_start, full_end, 5))
```
Effect Strength / Stability / Reliability / Support Windows 的 horizon **不读任何配置**。

**真相来源 2**：`risk/engine.py:78` 读 `profile.holding_horizon`
```python
horizon = profile.get("holding_horizon", 5)
```
Risk Review 的 horizon **是可配置的**，在 `EvaluationProfile.holding_horizon` 里。

**现在没炸，因为两个来源恰好都是 5**。但如果有人把 `EvaluationProfile.holding_horizon` 改成 20 想测试 20 天 horizon：
- Risk Review 跟着改到 h=20
- Effect Strength 仍然硬编码 h=5
- `ic_ir_validation` 是 h=5 下的数字
- `barra_residual_icir` 是 h=20 下的数字
- **两者被 judge 并列显示，但语义不可比**
- `alpha_survival_ratio = barra_residual_ic / raw_ic` 变成跨 horizon 的奇怪比值

**这是一个 silent bug**：改 profile.holding_horizon **不会报错**，会静默产生错误数据。

#### 成本估算修正

Q18 原方案说"validation 多 horizon +30% 时间"——**这个估算是错的**，因为只考虑了 Stage C 的 4 维。真实的成本：

```
当前 (h=5 only，per candidate):
  Stage C 4 维:              ~60 秒
  Stage D redundancy:        ~15 秒
  Stage D risk review:       ~20 秒 (Barra residual 是最贵的)
  Holdout:                  ~10 秒
  总:                        ~105 秒

多 horizon (4 horizons, per candidate):
  Stage C 4 维 × 4:          ~240 秒
  Stage D redundancy × 4:    ~60 秒
  Stage D risk review × 4:   ~80 秒  ← Barra residual 重算 4 次
  Holdout × 4:              ~40 秒
  总:                        ~420 秒
```

**单 candidate 从 105 秒涨到 420 秒（4x）**。对一个 6-candidate batch，从 ~5 分钟涨到 ~30 分钟（考虑并行后可能是 20 分钟）。

**不是 +30%，是 +200% - 300%**。

Barra residual 是最贵的——它要对所有股票-日做 7 维线性回归取残差，再算 IC。每个 horizon 都要重算整个 residual signal。

#### 修正后的成本控制策略

重新排序 Q18 原来的 5 条策略，以新的成本认知为准：

1. **最便宜**：**只让 Stage C 的 4 维跑多 horizon，Stage D 保持单 horizon**
   - Barra residual 只算 1 次（用主 horizon）
   - Stage C 多 horizon 只需要纯 numpy，便宜
   - 增量：~60 × 3 = 180 秒 / batch ≈ **+60%** execute 时间（不是 Q18 原说的 +30%，但也不是 +200%）
   - 代价：**Barra-clean IC 仍然只在主 horizon 下评估**，跨 horizon 的 risk 视图缺失

2. **级联 Barra**：先用主 horizon 跑 Stage D，borderline 的候选再用 alternative horizon 重跑 Stage D
   - 多数 candidate 只 1 次 Barra
   - borderline 的 2-3 次
   - 平均 ≈ **+40%** execute 时间

3. **Logic-level horizon 一致**：Logic 声明 primary + secondary，所有阶段都跑同一组 horizon
   - 每个 Candidate 跑 logic.primary_horizon + 1-2 个 secondary
   - 可控制在 ≈ **+50% - +100%** 之间
   - 但所有视角一致，无 silent bug

4. **先修 horizon 双真相**：在任何多 horizon 改造之前，**先把硬编码 5 改为读 profile**，让两个来源统一
   - 这是 bug fix，零功能增量但防止未来改造时触发 silent bug

#### 修正后的 Phase A 建议

不是 Q18 原来说的"直接 validation 多 horizon"，而是**三步**：

**Phase A1（前置修 bug）**：把 `compute_implementations.py:282` 的 `5` 改为 `profile.get("holding_horizon", 5)`。让两个真相来源统一。零功能增量，防未来 silent bug。

**Phase A2（最小多 horizon）**：Stage C 跑 h=1/5/10/20，Stage D 仍然只用 primary horizon。judge packet 新增 `horizon_sign_consistency` 和 `horizon_peak`。
- 成本：+60%
- 收益：能识别窗口拟合和 horizon mismatch

**Phase A3（完整多 horizon）**：级联 Barra，或 logic level horizon 声明（Phase B）。
- 成本：+40% 到 +100%
- 收益：Stage D 也有 horizon 视角

#### 关联观察（新增）

- **双真相 bug** 是 Q9.1（thread_id vs id）、Q14.1（universe_mask docstring）、Q16.3（plan 文档撒谎）的**同家族**：**同一概念在不同地方用不同方式表达**。修复模式：**建立 single source of truth**——要么硬编码、要么配置，不能两者都有
- **"Stage D 不在我之前的估算里"** 这个疏忽说明：对系统分层的理解本身不完整。之前我把 Stage C 和 Stage D 当作"独立的分析"，没意识到它们**共享 horizon 依赖**。这是我的 meta 错误
- **Feasibility 已经在用多 horizon 算 half_life** 但只当一个内部数字，**不暴露给 judge**。如果暴露了，judge 就能看到 "这个因子的 IC 衰减曲线"，做更好的组合判断。这是一个 low-hanging fruit

---

## Q19 — Effect Strength 代码审查：**2 维 5 子检查是假数据 + 5 个统计 bug + dual implementation**

**提问时间**: 2026-04-11
**相关阶段**: Phase 2 `/factor-execute` Stage C 的前 4 维 + 所有下游使用这些指标的 judge 层

**严重性**：**这是 Q 列表里最大的一个发现**。它说明整个 judge 层的 6 维裁决里，至少有 2 维（stability、reliability）的大部分子指标**都是硬编码的假数据**，而不是真实计算的结果。

### 发现 1：Dual Implementation——clean 版是死代码

系统里有两个并存的 "effect strength" 实现：

**版本 A（`src/research/stats/effect_strength.py`）**：
- 80 行，有文档，设计干净
- 返回 `ic_series_train` 和 `ic_series_validation` 供下游复用
- **被导出**在 `src/research/stats/__init__.py`
- **但从没被 import 到实际调用处**——是死代码

**版本 B（`src/research/execute/compute_implementations.py::compute_stat_evidence`，line ~270-365）**：
- 内联在 pipeline 里，和其他 stats 混在一个大函数里
- **这是 pipeline 实际在调用的版本**
- 不暴露 `ic_series` ——下游想做 stability/reliability 分析必须自己重算

**grep 证据**：
```
src/research/stats/__init__.py:6:   from research.stats.effect_strength import compute_effect_strength
src/research/stats/__init__.py:26:  "compute_effect_strength",
src/research/stats/effect_strength.py:28:def compute_effect_strength(
```

只在 `__init__.py` 里 export，**零调用点**。

### 发现 2：5 个维度 15 子检查里，6-7 个是硬编码假数据

看 `compute_implementations.py:338-364` 的 result dict：

| 字段 | Phase 2 walkthrough 我讲的 | 代码实际行为 |
|---|---|---|
| `ic_mean_*`, `ic_ir_*`, `ic_win_rate_*`, `monotonicity_validation` | 真实 IC 指标 | ✅ 真实计算 |
| `train_validation_decay_ratio` | train→val IC 衰减比 | ✅ 真实计算 |
| `split_stability` | "train 期切 4 段看一致性" | ❌ **只是 `_classify_stability(decay_ratio)`**——train_val decay ratio 的分类再包装 |
| `regime_stability` | "按市场 regime 分段看一致性" | ❌ **硬编码 `"medium"`**（line 348）|
| `horizon_consistency` | "多 horizon 一致性" | ❌ **硬编码 `"medium"`**（line 349）|
| `expanding_window_*` | "从训练期滚动扩展 N 次" | ⚠️ **实际是 2 段 split**（见 `_expanding_window_check` line 683-703），不是真正的扩展窗口 |
| `bootstrap_stability_score` | "IC 置信区间 bootstrap" | ❌ **`None`**（line 353）|
| `bootstrap_sign_consistency` | bootstrap sign | ❌ `None`（line 354）|
| `purged_walk_forward_score` | "滚动训练 + purge gap 的 walk forward" | ❌ **`None`**（line 355）|
| `purged_walk_forward_status` | 同上 | ❌ `None`（line 356）|
| `multiple_testing_risk_bucket` | "基于累计搜索次数的多重检验 bucket" | ❌ **硬编码 `"low"`**（line 357）|
| `search_adjusted_strength_bucket` | "多重检验调整后的强度" | ⚠️ **只看 ic_mean 和 ic_ir**，不看搜索历史 |

**汇总**：

| 维度 | Phase 2 讲的子检查数 | 真实实现数 | 硬编码 / None 数 |
|---|---|---|---|
| 1. Effect Strength | 5 | **5/5** | 0 |
| 2. Stability | 3 (split/regime/decay) | **1/3**（只有 decay）| 2 |
| 3. Reliability | 3 (expanding/bootstrap/purged) | **0.3/3**（expanding 是假的 2 段）| 2.7 |
| 4. Support Windows | 1 | **1/1** | 0 |
| 5. Multiple Testing | 1 | **0/1**（硬编码 low）| 1 |
| **合计** | **13** | **~7.3/13** | **~5.7** |

**我原本 Phase 2 walkthrough 讲的 13 个子检查里，大概 6 个是硬编码假数据或 None**。

### 发现 3：被实现的部分也有统计 bug

即使是真实计算的那一半，也有几个可见的统计问题：

#### Bug 3.1：LS t-stat 假设 IID（最严重）

`compute_implementations.py:641-642`：
```python
"ls_tstat": round(float(ls_arr.mean() / (ls_arr.std() / np.sqrt(len(ls_arr))))
                  if ls_arr.std() > 0 else 0.0, 4),
```

这是假设 daily long-short return 序列是**独立同分布**的 t 统计量。

**问题**：对 horizon=5 的 forward return，每天的 `future_return[T]` 对应 T→T+5 的 5 天 period return，**相邻天的 window 重叠 80%**。`ls[T]` 和 `ls[T+1]` 共享 4 天收益，强正相关。

**后果**：真实 std 比样本 std 大，t-stat 被系统性高估。对 h=5 horizon 的 overlapping return，正确的 t-stat 约为**当前值 / √5 ≈ 当前值 / 2.24**。

**具体影响**：F018 报告的 `ls_tstat = 3.8936`。经 Newey-West 修正后**真实值可能 ~1.74**——从"强显著（> 2.5）"降到"勉强显著（~1.7）"。**这可能改变 admit 决策**。

**正确做法**：
- Newey-West HAC 估计器，`lag = horizon - 1 = 4`
- 或 block bootstrap，block size = horizon
- 或 non-overlapping sampling（每 horizon 天取一个）

#### Bug 3.2：ICIR 没有 HAC 校正

同样问题，daily IC 序列也有自相关（短期动量持续）。`ic_std = np.std(arr, ddof=1)` 只做 sample std。

**后果**：ICIR 被系统性高估。对 F018 报告的 `icir_validation=0.338`，真实值可能 ~0.25-0.30。

#### Bug 3.3：Expanding window 实际是 2 段 split

`_expanding_window_check`（line 683-703）：

```python
def _expanding_window_check(factor_flat, returns_flat, train_start, train_end):
    mid = train_start + (train_end - train_start) / 2
    # 前半段 vs 后半段
    f1 = factor_flat[(factor_flat["time"] >= train_start) & (factor_flat["time"] < mid)]
    f2 = factor_flat[(factor_flat["time"] >= mid) & (factor_flat["time"] <= train_end)]
    ic1 = ic_summary(daily_cross_sectional_ic(f1, r1)).get("ic_mean", 0)
    ic2 = ic_summary(daily_cross_sectional_ic(f2, r2)).get("ic_mean", 0)
    
    stability = min(|ic1|, |ic2|) / max(|ic1|, |ic2|)
    sign_cons = 1.0 if sign(ic1) == sign(ic2) else 0.0
```

**这不是 expanding window**。这是 **2-segment split**。真正的 expanding window 应该是：
- 0-20% → IC
- 0-40% → IC
- 0-60% → IC
- 0-80% → IC
- 0-100% → IC
- 检查 IC 是否随窗口扩大而**收敛**

当前 2-segment split **发现不了"小样本下 IC 高但大样本下衰减"这种问题**——因为两半都是大样本。`expanding_window_pass = ew_sign >= 0.5` 只要两段同号就 True，是一个非常弱的 check。

#### Bug 3.4：Quintile 的 tie handling

`quintile_returns` line 261-263：
```python
pct = factor_wide.rank(axis=1, pct=True, na_option="keep").values
buckets = np.floor(pct * n_quantiles - 1e-9).astype(float)
```

`rank(pct=True)` 对 ties 用 `average` 排名。对稀疏因子（很多 0 或重复值），ties 会被 `floor` 切到相邻 buckets 或挤在一个 bucket，造成 bucket size 不均衡。

**影响**：稀疏因子的 quintile return 不稳定，mono 可能失真。

**修复**：用 `rank(method='first', pct=True)` 打破 ties，或用 `qcut(duplicates='drop')`。

#### Bug 3.5：effect_strength_bucket 的阈值是硬编码魔数

`_effect_strength_bucket`（line 714-722）：
```python
if ic_abs >= 0.03 and icir_abs >= 0.3:
    return "strong"
elif ic_abs >= 0.015 and icir_abs >= 0.15:
    return "borderline"
return "weak"
```

**问题**：
- 硬编码阈值，无文档说明
- 不随 horizon 变化（h=1 和 h=20 的典型 IC 量级不同）
- 不随 universe 变化（csi1000 和 csi300 的典型 IC 不同）
- **不随 search history 变化**——挖得越多，门槛应该越严（多重检验）

### 发现 4：性能问题

#### Perf 4.1：Merge + pivot 反复重算

每次 `daily_cross_sectional_ic` 或 `quintile_returns` 都独立做 merge + pivot。一个 candidate 的全套分析大约 **10+ 次 merge + pivot** 在同一份数据上，浪费 1-3 秒 / candidate × 6 = ~10-20 秒 / batch。

**修复**：merge + pivot 一次，缓存 `factor_wide / returns_wide`，所有 analyses 复用。

#### Perf 4.2：ThreadPool 受 GIL 限制

Stage C 用 `ThreadPoolExecutor(max_workers=4)` 并行分析 candidate。但纯 numpy 有 GIL（虽然 numpy 内部会释放），实际并行度不如预期。

**修复**：考虑 ProcessPoolExecutor，代价是 pickling 开销。

### 对整个系统的影响（最严重的含义）

这个发现的深层含义：

**判决层看到的数据里，至少 40% 是假数据**（硬编码 / None / 假实现）。

具体到 judge 的行为：
- judge 看到 `regime_stability: "medium"` → 以为算过了 regime 分析 → 认为"不是最好但也可以" → 不会用这个维度做 reject
- judge 看到 `bootstrap_stability_score: null` → 没信号说失败 → 默认跳过这个维度
- judge 看到 `multiple_testing_risk_bucket: "low"` → 以为搜索代价低 → 不做多重检验折扣
- **结果**：一个因子只要 `ic_mean + ic_ir + monotonicity + support_windows` 过了，就容易被 admit

**F018 / F019 之所以能 admit**——不一定是因为通过了严格的 5 维检验——**而是因为 5 维里的 60% 子检查根本没在跑**。它们"通过"了那些没被计算的维度。

这可能解释 L001/L010/L011 家族 "validation 过了但 holdout 崩" 的反复现象——**reliability 的真正检查（bootstrap / purged walk-forward）从来没做过**，validation 看起来 OK 但在严格 walk-forward 下会崩。

### 和 Q18 / Q16 的关系

- Q18（horizon 偏差）+ Q16（涨跌停 bias）= **真实数据上的偏差**
- Q19（硬编码假维度）= **有些维度根本没有数据**

Q19 比 Q18/Q16 更严重——它不是"数据算错了"，而是 "judge 在**假数据**上做判断"。

### 可行方案

按 **影响 × 成本** 排序：

**P0（立即做，低成本高影响）**：

**方案 A**：**接通 `effect_strength.py` 的 clean 版**
- 修改 `compute_stat_evidence` 调用 clean 版
- 确保 `ic_series_train / validation` 被下游获取
- 这是 #6-11 的根因修复——有了 ic_series 后，stability/reliability 才能真实计算
- 代价：~30 行代码，替换 inline 实现

**方案 B**：**修 LS t-stat Newey-West**
- `_long_short_stats` 加 HAC 估计器，lag = horizon - 1
- 代价：~20 行代码，引入 `statsmodels` 或手写
- 影响：F018 等的 ls_tstat 从 3.89 降到 ~1.7，可能改变 admit 决策
- **这是一个直接影响 admit 正确性的 bug**

**方案 C**：**真正实现 `multiple_testing_risk_bucket`**
- 从 `ledger.search_ledger.batch_usage` 读累计候选数
- 按 Bonferroni 或 FDR 校正
- 不硬编码 "low"
- 和 Q2（batch_usage 消费未落地）是同一个修复
- 代价：~40 行代码

**P1（中期，中等成本）**：

**方案 D**：**实现 regime_stability**
- 用 volatility 或 market return 划分 regime（高波动 vs 低波动）
- 每个 regime 内算 IC
- 看 IC 符号和量级是否一致
- 代价：~60 行代码

**方案 E**：**实现真正的 expanding window**
- 不是 2 段 split
- 真正做 5-10 段 expanding（例如 20%, 40%, 60%, 80%, 100%）
- 检查 IC 是否收敛
- 代价：~40 行代码

**方案 F**：**实现 bootstrap stability**
- Block bootstrap，block size = horizon
- 重采样 N 次（N=100-500），计算 IC 置信区间
- CI 不跨越 0 → stable
- 代价：~50 行代码 + 较高计算成本（+2-5 秒 / candidate）

**方案 G**：**ICIR 加 HAC 校正**
- Newey-West estimator for std
- 代价：~20 行代码

**P2（长期，较高成本）**：

**方案 H**：**Purged Walk-Forward**
- 滚动训练 + 滚动预测 + purge gap
- 模拟实盘
- 代价：~100 行 + 显著计算成本

**方案 I**：**Quintile tie handling**
- `rank(method='first')` 或 `qcut(duplicates='drop')`
- 代价：几行

**方案 J**：**effect_strength_bucket 动态阈值**
- 按 horizon × universe × search_history 调整
- 代价：~30 行代码

**方案 K**：**Merge + pivot 缓存**
- 在 compute_stat_evidence 开头做一次 merge + pivot，所有 analyses 复用
- 代价：~40 行代码，节省 10-20 秒 / batch

### 优先级

**P0 立即做**：A + B + C。这 3 个合起来直接修复 judge 决策层的"假数据"问题 + 一个统计正确性 bug。代价总计 ~100 行代码。

**P1 下一步**：D + E + F + G。让 stability/reliability 真正起作用。代价总计 ~170 行 + 计算成本。

**P2 长期**：H + I + J + K。完整化 + 性能优化。

### 关联观察

- **Q19 是 Q14.5 的极端版**：Q14.5 是 "walkthrough 5/5 错"，Q19 是 "walkthrough 15/13 错"（有些我讲的子检查根本不存在）。**这是我讲解能力的系统性局限**——倾向于相信代码的 docstring 和字段名，不验证是否真实计算
- **Q19 可能是 L015 挣扎的原因之一**：reliability 假检查让 L001/L010/L011 家族能假装通过 validation，但 holdout 是真实数据会暴露问题。L015 是唯一做到 holdout 也稳的，不是因为它更好——可能是因为其他家族的 validation 成绩是"假通过"
- **Q19 和 Q18 耦合**：h=5 + 假 reliability → 短期动量因子看起来比实际好；h=5 太短 + 假 reliability → 长期价值因子看起来比实际差。两个偏差合起来让系统**系统性地误判因子价值**
- **"ic_series 不暴露"是一个架构层面的根因**：它让所有需要 IC 序列的下游分析都被迫"先算一遍 / 用默认值"。修复它能一次性解锁 6 个硬编码维度的真实实现
- **Dual implementation 是 code smell**：clean 版和 inline 版并存，意味着曾经有人想重构但没完成。这是 Q1（idea_report 丢失）、Q10（proposals 化石）、Q14.1（universe_mask 不存在）的同家族——**未完成的重构留下的考古层**

### 补充（2026-04-11）：不止 effect_strength——**整个 `stats/` 和 `feasibility/` subpackage 都是死代码**

用户追问"为什么会有两个 IC 计算逻辑"。git archaeology + 跨 subpackage 扫描揭示了更大的问题：**Q19 原本描述的只是一个例子，真实情况是至少 5 组并行实现**。

#### Git archaeology

`git log` 还原的时间线：

```
commit d9d0b4b  2026-04-05  "feat(research): add statistical evidence engine (Unit 04)"
  ↓ 一次性加入 stats/ 整个 subpackage（7 文件 + 配套 tests）
  
commit 935abd8   "cleanup: simplify and fix after code review"
  ↓ stats/effect_strength.py 经过 code review 后简化
  
commit 1e8e789   "refactor all"
  ↓ 大 refactor（具体内容不详）
  
commit 36ff87f   "add iter"
commit 347128b   "fix skills"
  ↓ 快速迭代阶段，inline 版本可能在这里出现
```

**阶段 1**（Unit 04）：结构化交付，subpackage + tests + code review。
**阶段 2**（refactor all）：大 refactor。
**阶段 3**（add iter, fix skills）：快速迭代，inline 版本绕过 subpackage 出现，"先占位以后再补"。
**阶段 4**（现在）：两套并存，生产跑 inline 半成品，subpackage 孤儿。

#### 完整的"并行实现"清单

扫描 `from research.stats`, `from research.feasibility`, `FeasibilityEngine` 等 import：

| 子包 | Subpackage 是否存在 | 被 execute/judge 层 import | 实际运行的是谁 |
|---|---|---|---|
| **`research.stats`** | ✅ 7 个文件 + tests | ❌ **零 import** | inline `compute_stat_evidence` |
| **`research.feasibility`** | ✅ engine + liquidity + concentration + stress + proxy_portfolio | ❌ **零 import** | inline `compute_feasibility` |
| **`research.redundancy`** | ✅ engine / family / pairwise / subspace | ✅ `RedundancyEngine` 被 import | 子包 |
| **`research.risk`** | ✅ engine / factors / exposures / ... | ✅ `RiskEngine` / `RiskReview` 被 import | 子包 |

**两个完整 subpackage 是死代码。一半的 clean 实现没人用**。

#### 5 组并行实现

| 组 | Clean 版位置 | Inline 版位置 | Clean 版包含的额外能力 |
|---|---|---|---|
| 1. Effect Strength | `stats/effect_strength.py` (+151 行 test) | `compute_stat_evidence` 前半 | 暴露 `ic_series`（关键！）|
| 2. Stability | `stats/stability.py` (236 行 + test) | `_expanding_window_check` + `_classify_stability` + 硬编码 | 真正的 split/regime/sign consistency 算法 |
| 3. Reliability | `stats/reliability.py` (297 行 + test) | **不存在**（用 None / "medium" 占位）| bootstrap / purged walk-forward |
| 4. Multiple Testing | `stats/multiple_testing.py` (98 行 + test) | **不存在**（用 "low" 硬编码）| 真正的 search-adjusted bucket |
| 5. Feasibility | `feasibility/engine.py` + 4 子模块 | `compute_feasibility` 简化版 | 真正的 proxy portfolio / stress / concentration |

#### Inline `compute_feasibility` 的假数据也很严重

Q19 主要讲 `compute_stat_evidence` 的假数据，但 `compute_feasibility` 同样糟糕：

```python
return {
    "turnover": round(turnover, 4),                    # 真算
    "coverage": round(coverage, 4),                    # 真算
    "half_life": round(half_life, 2),                  # 真算
    "holding_period_proxy": holding,                    # 真算
    "liquidity_coverage_ratio": round(min(coverage, 0.95), 4),  # ← 退化实现！假装是 liquidity ratio 但其实是 coverage 的 cap
    "tail_trade_concentration": 0.15,                  # ← 硬编码！
    "small_cap_concentration": 0.25,                   # ← 硬编码！
    "rebalance_stress_proxy": "low",                   # ← 硬编码！
}
```

**8 个字段里 4 个是真算的，4 个是硬编码 / 退化实现**。

对比 `feasibility/engine.py` 的 clean 版（有 `proxy_portfolio.py`, `stress.py`, `concentration.py`, `liquidity.py`），它们**真正实现了**：
- 真的 liquidity coverage ratio（基于 top/bottom quintile 的实际成交额）
- 真的 tail concentration（基于分布的尾部集中度）
- 真的 small cap concentration
- 真的 rebalance stress test

这些**都躺在磁盘上无人调用**。

#### Testing Inversion（最严重的 meta 观察）

| | Clean 版 (stats/ + feasibility/) | Inline 版 (compute_implementations.py) |
|---|---|---|
| 有 tests | ✅ 完整的 unit test 套件 | ❌ 没有对应测试 |
| 过 code review | ✅（935abd8 有 cleanup after review）| ❌ 从 commit message 看没有 |
| 在生产跑 | ❌ 死代码 | ✅ 每轮 execute 都在跑 |
| 有假数据占位 | ❌ | ✅ stat 的 6 个维度 + feasibility 的 4 个字段 |

**被审查过、有测试的代码是死代码。没审查过、没测试、充满硬编码假数据的代码在做生产决策**。

这是一个完全倒转的质量分布——**任何 static analysis 会告诉你 subpackage 质量更高，但质量高的在磁盘上躺着，生产跑的是质量低的那份**。

#### 为什么会这样——根源答案

**这是一次未完成的重构的考古层**。

阶段 1 有人按教科书规划了 clean architecture（subpackage + tests）。
阶段 3 有人为了快速迭代，选择绕过 subpackage 在 pipeline 里内联——**本意很可能是"先 inline 一个最小可用版，以后再迁移回 subpackage"**。

但"以后迁移"从来没发生：
- 没人 delete 旧的 subpackage → 变成孤儿
- 没人补 inline 版的 tests
- 没人完成 inline 版里硬编码的假维度

Inline 版在 production 跑了 100+ batch，clean 版在磁盘上躺了 6 周无人调用。

**这个 pattern 属于一个大家族**：Q1（idea_report 丢失）、Q10（proposals 化石）、Q14.1（universe_mask docstring 撒谎）、Q14.4（preprocess _neutralize 孤儿）、Q16.3（plan 文档撒谎）都是同一种症状——

> **"先占位，以后再补" —— 然后"以后"从来没到**

在 LLM 自主维护的系统里这个 pattern**特别危险**，因为 LLM 看到"这里有个实现"就假设它完整，不会主动验证 subpackage 是否被真正 import，不会注意到 inline 版的硬编码假数据。**只有在用户追问细节时才会被动发现**。

#### 对修复方案的影响

Q19 原方案 A（接通 clean effect_strength）现在应当升级为 **"接通整个 clean `stats/` + `feasibility/` subpackage"**。

具体步骤：
1. 把 `compute_stat_evidence` 改为 thin wrapper，调用 `compute_effect_strength / compute_stability / compute_reliability / compute_multiple_testing`
2. 把 `compute_feasibility` 改为 thin wrapper，调用 `FeasibilityEngine.run()`
3. 彻底删除 inline 版本的硬编码假数据
4. 确保 ic_series 在 stats 层共享（avoid 重复计算）
5. 跑一次完整的 batch，验证指标数值合理

代价：中等（1-2 天）。收益：一次性解决 Q19 的 6 个硬编码假维度 + Q20 的分散阈值的大部分 + feasibility 的 4 个假字段。

### Stage C 走流程时发现的 4 个补充观察（2026-04-11）

下面 4 个观察是在 walkthrough Stability / Reliability / Support Windows / Multiple Testing 时顺手发现的，属于 Q19 领域的子问题。单独列出来便于修复时 follow-up。

#### 补充 19.1：`decay_ratio` 用绝对值掩盖符号翻转

`compute_implementations.py:319-321`：
```python
ic_train_abs = abs(ic_train_stats.get("ic_mean", 0) or 0)
ic_val_abs = abs(ic_val_stats.get("ic_mean", 0) or 0)
decay_ratio = float(ic_val_abs / ic_train_abs) if ic_train_abs > 1e-8 else 1.0
```

**用的是绝对值**。如果 `ic_train = +0.04, ic_val = -0.04`：
- `decay_ratio = 1.0`（看起来"完美不衰减"）
- 但信号方向**完全翻了** —— 这是 overfit 的最严重形式

代码旁边有 `sign_consistent = bool(train_sign == val_sign)` 补救，但这让 judge 必须**自己组合**两个字段判断，而不是看一个带符号的 decay ratio。

**修复**：
```python
# 改成带符号
decay_ratio_signed = ic_val / ic_train  # 可以是负数
# 判据调整:
#   > 0.7 and < 1.3: 稳定
#   0 < decay < 0.5: 衰减
#   < 0: 符号翻转（最危险）
```

**优先级**：P2。小改动，~10 行代码。

#### 补充 19.2：Split stability 和 Regime stability 不应该混同

Stability 维度里 split（时间 4 段）和 regime（市场环境）**应该是两个正交子维度**。但当前设计（即使接通 clean 版）把它们放在一起讨论——而且 `split_stability` 字段在内联版里甚至只是 decay_ratio 的 classification 再包装（见 Q19）。

**本质区别**：
- **Split stability**：时间维度的一致性。切 4 段 × 1.5-2 年，看 IC 是否 4 段同号。
- **Regime stability**：环境维度的一致性。按 bull/bear/sideways 切片，看 IC 是否 3 种环境同号。

这是两件不同的事。2015-2016 那一段时间内包含了牛市 + 熔断 + 暴跌——**split 说 "这 2 年 IC 是正的"，不代表 "在 regime 层面稳定"**。Split 混掉了 regime 变化。

**修复**：clean 版应该返回两个独立字段：
```python
{
    "split_stability_4seg": {sign_consistency, dispersion, ic_by_period},
    "regime_stability": {sign_consistency, ic_by_regime, n_flips},
    # 不要把两者混合到一个 "split_stability" 标签里
}
```

**优先级**：P2。属于 clean 版接通时的 API 设计选择。

#### 补充 19.3：Support windows 在 config 里可能是空列表（需验证）

Phase 2 Step 4 Support Windows 的实现 `_compute_support_window_checks`（`compute_implementations.py:647-681`）**本身是真实计算的**（不是假数据）：
```python
for window in support_windows:
    f_win = factor_flat[在 window 时间范围内]
    r_win = returns_flat[在 window 时间范围内]
    stats = ic_summary(daily_cross_sectional_ic(f_win, r_win))
    ...
```

**但 `support_windows` 参数从 `sample_policy.support_validation_windows` 读**：
```python
support_checks = _compute_support_window_checks(
    factor_flat, returns_flat,
    sample_policy.get("support_validation_windows", []),   # ← 默认空列表
    primary_ic_sign=val_sign,
)
```

**如果 config 没配置**，`support_windows = []` → `_compute_support_window_checks` 立即返回空 list → **Support Windows 这一维事实上等于没做**。

**2026-04-11 验证结果**：配置**不是空的**。`storage/governance/research_config.yaml` 里 `sample_policy.support_validation_windows` 至少有 3 个窗口：
```yaml
support_validation_windows:
  - window_id: val_2020_2021
    range: ["2020-01-01", "2021-12-31"]
  - window_id: val_2021_2022
    range: ["2021-01-01", "2022-12-31"]
  - window_id: val_2022_2023
    ...
```

**所以 Support Windows 维度是真实在工作的**，不是死维度。这是 Stage C 5 维里除了 Effect Strength 之外**第二个**确认真实的维度。

但需要注意两件事：
1. 窗口定义有**重叠**（2020-2021 和 2021-2022 都包含 2021 年）—— 不是完全独立的 support windows，相关性会推高 sign_consistency 的可信度
2. 窗口**只覆盖到 2022**，没有覆盖 holdout 前的 2023 独立窗口 —— 如果主 validation 是 2022-2023，support 窗口覆盖的都是**更早的历史**，没有真正独立的"相邻窗口"作对照

**优先级**：P3。当前可工作，可以增加 1-2 个更近的 support 窗口提升检查强度。

#### 补充 19.4：Purge gap 不随因子 look-back 参数化

Reliability 维度的 Purged Walk-Forward（即使 clean 版被接通），按 `stats/reliability.py` 的实现，purge gap 大小**可能是固定的**（需进一步 grep 验证具体实现）。

但不同因子的 look-back 窗口差距很大：
- 一个 `Mean($close, 5)` 的因子，5 天的 gap 就够
- 一个 `Sub(Div($close, Ref($close, 120)), ...)` 的因子，需要 120 天的 gap 才能彻底防止数据泄漏
- 使用固定 gap 对长窗口因子**数据泄漏**（gap 太小），对短窗口因子**浪费样本**（gap 太大）

**正确做法**：从 candidate 表达式静态分析 `Ref(..., n)` / `Mean(..., n)` / `Corr(..., n)` 的最大 n 值，把 gap 设置为这个 n（或稍大）。

**TODO 验证**：grep `stats/reliability.py` 确认 purge gap 是否参数化。

**优先级**：P2。接通 clean reliability 时一起处理。

---

---

## Q20 — 硬编码魔数扫描：40+ 处散落的阈值 + scheduler 权重组合，层与层之间互相矛盾

**提问时间**: 2026-04-11
**相关阶段**: 整个 Phase 2 执行管道 + 调度层

### 背景

Q19 里发现 `_effect_strength_bucket` 的阈值 `ic >= 0.03 AND icir >= 0.3` 是硬编码魔数。用户追问："类似的逻辑我们还有多少？另外有没有硬编码的权重？"

系统性扫描结果**至少 40 处硬编码阈值 + 1 套硬编码权重组合**。

### 分布表

| 类别 | 处数 | 严重性 | 代表文件 |
|---|---|---|---|
| **A. IC / ICIR 强度** | 10+ | **极高** (依赖 horizon/universe) | compute_implementations, pipeline, judge_packet_builder, probe |
| **B. Stability / regime** | 6+ | 高 | stats/stability.py |
| **C. Reliability** | 3 | 中 (死代码里) | stats/reliability.py |
| **D. Redundancy 相似度** | 4 | 高 (互相不一致) | redundancy/pairwise, family, compute_implementations |
| **E. Multiple testing** | 2 | 低 (死代码) | stats/multiple_testing.py |
| **F. Feasibility** | 4 | 中 | feasibility/stress.py |
| **G. Risk review** | 2 | 中 | risk/schema.py |
| **H. Scheduler 权重** | 7 项 | **高** (控制调度) | logic/scheduler.py |
| **I. Logic thresholds** | 5+ | 中 | logic/scheduler.py |

### 4 个根源问题

#### 问题 20.1：同一个 IC 值在不同阶段被标成不同等级（互相矛盾）

IC 强度阈值分布在 6 个地方：

```
Probe:              ic >= 0.005 / 0.01 / 0.02           (stats/probe.py:129-133)
CLI probe:          ic < 0.005 fail; < 0.01 weak        (cli/commands/probe.py:51)
Idea admit gate:    ic >= 0.015 AND icir >= 0.15         (pipeline.py:342-343)
Execute bucket:     ic >= 0.03 AND icir >= 0.3            (compute_implementations.py:717)
Judge packet strong: ic >= 0.015 AND icir >= 0.15 AND mono >= 0.30  (judge_packet_builder.py:29)
Holdout gate:       ic >= 0.01 AND icir >= 0.10           (pipeline.py:357)
```

**同一个 IC=0.02 的因子**：
- Probe 说：strong
- Execute bucket 说：borderline (strong 要 0.03)
- Judge packet 说：strong (阈值 0.015)
- Admit gate 说：pass (阈值 0.015)

**每个阶段独立判定，互相不知道对方的存在**。

#### 问题 20.2：阈值不随 horizon / universe / search history 变化

IC 量级强烈依赖 horizon：

- h=1 的典型 IC 在 0.005-0.02 范围
- h=5 在 0.01-0.04 范围
- h=20 在 0.02-0.08 范围
- h=60 可到 0.10+

`ic >= 0.03 = strong` 这套阈值：
- 对 h=1 → 几乎不可能达到（过严）
- 对 h=5 → 合理（系统当前主 horizon）
- 对 h=20 → 过松（不到 50% 分位就 strong）
- 对 h=60 → 任何正 IC 都是 strong

Feasibility 的 half_life 已经在用多 horizon（Q18 发现），它们共用同一套阈值——**hidden bug**。Q18 方案 B/C 扩展多 horizon 之前必须先修 Q20。

#### 问题 20.3：Redundancy 的 4 个"高相似度"阈值互相不一致

```
redundancy/pairwise.py:107:      max_corr > 0.9 → is_near_duplicate
compute_implementations.py:444:  max_lib_corr >= 0.5 → replacement_candidate_hint
redundancy/family.py:21-23:      score < 0.45 / <= 0.70 → family overlap buckets
judge_packet_builder.py:57-59:   max_corr >= 0.85 high; >= 0.60 medium
```

**4 个不同的"相似"判据**：0.9 / 0.85 / 0.70 / 0.60 / 0.50 / 0.45 散落在 4 个文件。没有 single source of truth。

一个因子和 F005 的 corr=0.70：
- pairwise 说：不是近重复
- judge_packet 说：medium similarity
- compute_implementations 说：replacement hint
- family 说：某一档 overlap

**静默矛盾**。

#### 问题 20.4：Scheduler 的 7 维权重是拍脑袋定的

`logic/scheduler.py:25-33`：
```python
WEIGHTS = {
    "priority": 0.20,
    "lifecycle": 0.15,
    "productivity": 0.20,
    "saturation": 0.15,
    "bottleneck": 0.10,
    "discovery_need": 0.10,
    "validation_exposure": 0.10,
}
```

这套权重**控制整个调度决策**，但：
- 没有文档说明为什么是这些数字
- 没有 A/B 实验证据
- 没有敏感性分析
- 没有和目标对齐的分析

**改 weights 不是改配置，是改代码**——这本身是 code smell。

相关的隐式权重：
```python
PRIORITY_SCORES = {"high": 1.0, "medium": 0.6, "low": 0.3}
LIFECYCLE_SCORES = {
    "proposed": 0.5,
    "active": 1.0,
    "warm": 0.7,
    "productive": 0.9,    # 为什么低于 active？
    "saturated": 0.2,
    "parked": 0.0,
    "dead": 0.0,
}
```

**productive = 0.9 < active = 1.0** 是有意的吗？L015 当前是 productive，被连续挖了 5 batch。如果 productive = 1.0 会怎样？系统可能更不愿意挖 L015 而更愿意挖其他 active logic。**这个 0.1 的差别可能改变整个探索/利用平衡**。

`ACTIVE_THRESHOLD = 0.45`、`WARM_THRESHOLD = 0.25` 同样没文档。

#### 问题 20.5：死代码里的魔数是静默埋雷

`stats/reliability.py:176-178`：
```python
if score >= 0.65:
    return "good"
elif score >= 0.45:
    return "medium"
```

这段代码从没被 pipeline 调用过（Q19 发现）。阈值看起来合理，但：
- 没人审核过
- 没有测试验证
- 如果 Q19 方案 A 接通了 clean 版，这些阈值**立即生效**——但那一刻没人会想起来去审核

**静默埋雷**。

### 完整 inventory

**Stats 层**：
- stability.py:65-67/104/137/172-178（split + regime 判据）
- reliability.py:89/176-178/290（死代码阈值）
- multiple_testing.py:38-40/87-89（死代码阈值）
- probe.py:129-133/144-148（probe bucket）

**Execute 层**：
- pipeline.py:342-345/357-359（admit + holdout gate）
- compute_implementations.py:352/444/706-710/717-720
- judge_packet_builder.py:29-32/57-59/75-77/90-92
- execution_gate.py:143

**Feasibility 层**：stress.py:55/103-105

**Risk 层**：schema.py:69/74

**Redundancy 层**：pairwise.py:107, family.py:21-23

**CLI 层**：cli/commands/probe.py:51-53

**Logic 层**：scheduler.py:25-49（权重 + 字典 + 阈值）

**合计**：**40+ 处阈值 + 1 套权重组合 + 2 个分数字典 + 2 个 pool 阈值**。

### 为什么重要

1. **Admit 决策不确定性**：同一个 IC=0.02 在不同阶段被标 weak/borderline/strong/pass，**系统里 "admit 标准" 没有单一答案**
2. **多 horizon 扩展被堵死**：Q18 需要阈值随 horizon 变化，当前硬编码改不动
3. **调度不可调优**：Q11 的 meta-reflect 想自主调度权重，当前 weights 在代码里 LLM 无法调
4. **经验被错误地编码为代码**：这些魔数是研究直觉，应该进 config 或文档，不是代码
5. **静默埋雷**：死代码里的阈值在某天被激活时立即生效，无 trigger 审核

### 可行方案

**方案 A（必做，单一真相）**：在 `src/research/domain/thresholds.py` 创建：

```python
@dataclass(frozen=True)
class EffectStrengthThresholds:
    horizon: int
    strong_ic: float
    strong_icir: float
    borderline_ic: float
    borderline_icir: float
    weak_ic: float
    
    @classmethod
    def for_horizon(cls, h: int) -> "EffectStrengthThresholds":
        table = {
            1:  (0.008, 0.15, 0.004, 0.08, 0.002),
            5:  (0.030, 0.30, 0.015, 0.15, 0.008),
            10: (0.045, 0.35, 0.020, 0.17, 0.010),
            20: (0.060, 0.40, 0.030, 0.20, 0.015),
            60: (0.100, 0.50, 0.050, 0.25, 0.025),
        }
        return cls(h, *table.get(h, table[5]))

@dataclass(frozen=True)
class RedundancyThresholds:
    near_duplicate: float = 0.90
    high_similarity: float = 0.85
    medium_similarity: float = 0.60
    replacement_hint: float = 0.50
    family_overlap_high: float = 0.70
    family_overlap_low: float = 0.45
```

所有 40+ 处调用点引用这个模块。代价：~200 行 + 修改 40 处，2-3 天。

**方案 B（必做，scheduler 权重进 config）**：移到 `research_config.yaml`：
```yaml
scheduler:
  weights:
    priority: 0.20
    ...
  pool_thresholds:
    active: 0.45
    warm: 0.25
```

**方案 C（推荐，敏感性分析脚本）**：`scripts/threshold_sensitivity.py`
- 取历史 judge_packet
- 枚举阈值组合
- 统计 admit 率如何随阈值变化
- 输出热力图

**方案 D（长期）**：清理死代码阈值（Q19 + Q20 一起做）

**方案 E（中期）**：按 universe 也参数化

### 优先级

P0：A + B（建立 single source of truth + 权重进 config）
- 前置：Q19 方案 A 必须先做，否则修正后的阈值作用于假数据
- 收益：大部分阈值问题一次解决

P1：D（清理死代码阈值）

P2：C + E

### 关联观察

- **Q20 是 Q19 的自然延伸**：Q19 发现一处魔数，Q20 发现是普遍现象
- **Q20 是 Q18 的前置**：Q18 的多 horizon 扩展要求阈值随 horizon 变化，当前做不到
- **Q20 是 Q11 的障碍**：LLM 无法通过改代码调优权重，调度权重必须进 config
- **"静默矛盾"比单一硬编码更危险**：不一致让决策依赖读取顺序——同一因子不同路径结果不同
- **"隐式编码的研究经验"是 code smell**：经验应该文档化，不应该代码化。文档可审查可更新，代码改动需要 review

---

## Q8 — storage/registry 的当前状态有多处不一致：命名、family 索引、升格机制

**提问时间**: 2026-04-11
**相关阶段**: Phase 3 `/factor-judge` 写入 + Phase 4 `/factor-report` 读取

### Registry 的设计意图（复习）

Registry 是系统唯一的"产品出口"：录取的 candidate 升格为永久 factor 之后存放的地方。

- **两个维度**：factors/ 和 families/
- **三层结构**：index（精简列表）/ detail（完整 40+ 字段 YAML）/ cluster（家族聚合）
- **CLAUDE.md 明确规定**：detail YAML 是 **metadata truth source**，DB 的 factor_meta 表是派生缓存
- **写入权限**：只有 `/factor-judge` 经 `GuardedWriter` 能写

### 问题 8.1：F014 文件命名不一致（幽灵 factor）

`storage/registry/factors/` 目录下 19 个 factor：
- F001–F013, F015–F019: 命名为 `factor_FXXX.yaml`
- **F014 单独命名为 `F014.yaml`（缺少 `factor_` 前缀）**

后果：
- `registry_store.load_factor_detail("F014")` 会调用 `paths.factor_detail_file("F014")`，几乎肯定返回 `factor_F014.yaml` 路径 → 读不到
- 但 `index.yaml` 里 F014 条目存在
- **F014 在清单里存在，detail 读不出来**——幽灵 factor

起因推测：手工操作或脚本漏了前缀。没有 schema 校验在写入时拦住。

### 问题 8.2：family 索引文件之间不一致

看 families/ 下的三个文件：

**(a) `families/family_registry.yaml`** — 空：
```yaml
families: []
```

**(b) `families/families_index.yaml`** — 只有 2 条：
```yaml
families:
  - family_id: PF_range_amount_flow
  - family_id: PF_volume_autocorrelation
count: 2
```

**(c) `families/*.yaml` 实际文件** — 只存在 2 个：`PF_range_amount_flow.yaml`、`PF_volume_autocorrelation.yaml`

**但 `factors/index.yaml` 里引用的 family_id 有 3 个不同的值**：
- `FM_microstructure_timing_range`（F013, F014）
- `PF_price_volume_correlation`（F015, F016）
- `PF_fundamental_price_divergence`（F018, F019）

**两边完全对不上**：
- registry 引用的 3 个 family_id 和 families/ 下实际存在的 2 个文件 **交集 = 空集**
- `family_registry.yaml` 完全是空的，但 `families_index.yaml` 有 2 条——这两个索引文件之间本身就不一致
- 如果下游按 family 聚合 factor，会读不到任何家族的 factor_ids

### 问题 8.3：family 升格机制从没被触发

`src/research/logic/family_registry.py:260-275` 有 `promote_to_registered()` 方法，`lifecycle.py::validate_promotion` 定义了升格条件：
- 至少 2 batch 证据
- subspace_redundancy < 0.7

但现实：
- 19 个 factor 引用的 family 里，**只有 1 个是 `FM_*` 前缀**（FM_microstructure_timing_range）
- 其他全是 `PF_*`
- 包括 `PF_fundamental_price_divergence`——这个家族已经有 2 个成员（F018, F019），按条件可以尝试升格，但没人主动触发

说明 family 升格是一个**存在的代码路径但没被任何 skill 调用的孤儿方法**。连带的 `FM_*`（registered）和 `PF_*`（provisional）的语义区分在实际系统里**事实上不存在**——所有家族永远停在 provisional 状态。

### 问题 8.4：index.yaml 和 detail 之间没有一致性校验

CLAUDE.md 说 detail 是 truth source，index 是派生。但：
- `upsert_factor_entry` 是**手动维护** index 的
- 没有 `rebuild_index_from_details()` 方法
- 如果改了 detail 忘了改 index，或反过来，会静默漂移
- 没有 consistency checker 会发现这种漂移

从代码看，`storage/consistency.py` 有几条一致性检查（都在 logic / research_state 层面），但没有 registry 的检查。

### 为什么重要

1. **幽灵 factor（F014）会让 report builder 静默失败或 fallback 重算**——用户看不到原因
2. **family 索引不一致意味着所有按 family 聚合的下游逻辑都坏了**——包括 redundancy 分析在 family 内做 subspace 回归时可能找不到家族成员
3. **没有一个 `FM_*` 家族说明升格机制死代码化**——系统永远停在"临时分类"状态，永远无法形成稳定的因子分类学
4. **index vs detail 漂移风险**是一个慢性病，长期会侵蚀 truth source 的可信度

### 可行方案

**方案 A（必做，修 F014 命名）**：一次性脚本把 `F014.yaml` 重命名为 `factor_F014.yaml`，并检查是否还有其他命名不一致的文件。然后加一条写入校验：`save_factor_detail` 必须通过 `paths.factor_detail_file(factor_id)` 拼路径，拒绝直接写 `F014.yaml` 这种。

**方案 B（必做，重建 family 索引）**：
1. 扫 `factors/index.yaml` 收集所有出现过的 family_id
2. 对每个 family_id 反查 `factors/factor_FXXX.yaml`，组装 `factor_ids` 列表和 `logic_ids` 列表
3. 重写 `families/*.yaml` detail 文件
4. 重写 `families_index.yaml` 和 `family_registry.yaml`，保证两个文件内容一致

这是一次性的数据修复，之后加 consistency check 防止再次漂移。

**方案 C（推荐）**：把 family 升格接入 `finalize-batch` 流程。每轮 finalize 时：
- 扫描所有 `PF_*` family
- 对每个 family 跑 `validate_promotion(batch_evidence, subspace_redundancy)`
- 通过条件的自动调用 `promote_to_registered()` 升格为 `FM_*`
- 记一条 audit entry

这条是 Q5（batch 边界价值）在 family 层面的落地——让"跨 batch 证据累积 → 升格"这件事真正发生。

**方案 D（consistency checker）**：给 `storage/consistency.py` 加 registry 一致性检查：
- 所有 `factor_FXXX.yaml` 的 factor_id 必须在 index 里出现
- 所有 index 里的 factor_id 必须有对应 detail 文件（防幽灵）
- 所有 factor 引用的 family_id 必须在 families/ 下有 detail 文件
- 所有 family YAML 里的 factor_ids 必须反向可达对应的 factor detail

定期在 finalize-batch 或 CI 里跑一次。

### 优先级

A 和 B 必做（是当前脏数据的清理）。D 紧跟（防止再次漂移）。C 是结构性改进，可以在 A/B 落地后做。

### 关联观察

- Q8.3（升格机制死代码）和 Q5（batch 边界失效）是同一个病：**系统有很多"跨 batch 证据累积"的机制被写出来了但从没被调用**。family 升格、ELT 版本升级、logic status 转 productive 等都属于这一类。修复它们的共同机制是在 finalize-batch 里加一个"statistics aggregator"阶段。
- Q8.1（幽灵 F014）和 Q1（idea_report 丢失）都是 "写入约束纯靠自觉" 的例证。Registry 这种 truth source 级别的数据，写入路径更应该有 schema 校验。

---

## Q9 — storage/logic/ 全面体检：9 处不一致

**提问时间**: 2026-04-11
**相关阶段**: Phase 0 读 card / Phase 1 thread 消费 / Phase 3.5b reflect 写入 / proposals 生命周期

### 背景

`storage/logic/` 是系统的"认知层"，包含三个子目录：
- `cards/` — 15 个 logic card（L001–L015）
- `proposals/` — 5 个 proposal 草稿
- `reflections/` — 15 个 reflection.md 叙事文件

对这三个子目录做了一次全面扫描，发现 **9 处不一致或治理空白**。

### 问题 9.1：card 的 thread 字段名和所有文档不一致（schema drift）

**文档**：skill.md / CLAUDE.md / 所有讨论都说 "thread_id"
**代码/YAML 实际**：`deepening_threads` 数组里每个元素的字段叫 **`id`**，不是 `thread_id`

验证：
- `grep -E "^- id: T" storage/logic/cards/L*.yaml` → **43 条匹配**
- `grep "thread_id:" storage/logic/cards/L*.yaml` → **0 条匹配**

唯一救场的是 `manifest_validator.py:88` 里手动兼容：
```python
thread_map = {
    str(t.get("id", "")): t
    for t in threads
    if isinstance(t, dict) and t.get("id")
}
```

后果：
- 任何看 skill.md 的新人都会认为字段叫 `thread_id`，写新 card 时可能填错
- 没有 dataclass/schema 强制字段名（`deepening_threads: List[Dict[str, Any]]` 是 free-form）
- 和 Q3（lineage dict schema 分裂）同病

### 问题 9.2：14/15 的 logic 零 active thread（系统耗尽前兆）

扫描所有 card 的 thread 状态分布：

| logic | active | answered | parked | card.status |
|---|---|---|---|---|
| L001 | 0 | 4 | 5 | parked |
| L002 | 0 | 0 | 1 | parked |
| L003 | 0 | 0 | 3 | parked |
| L004 | 0 | 1 | 1 | saturated |
| L005-L012 | 0 | — | — | 全 parked |
| L013 | 0 | 3 | 1 | saturated |
| L014 | 0 | 0 | 2 | parked |
| **L015** | **2** | **0** | **0** | **productive** |

**整个系统只有 L015 还有 2 个 active thread**。如果这 2 个跑完 `next_probes`，场景 E（全 logic 死）就会触发。这解释了为什么 batch_099–103 全是 L015 微扰——系统没有其他出路。

按 Phase 1 thread 消费协议，非 L015 的 14 条 logic 都应该 escape，事实上它们确实都是 parked 状态。这里自洽，但耗尽风险是真的。

### 问题 9.3：proposals/ 是孤儿垃圾场

5 个 proposal 文件：
- `L005_peer_relative_reversal.yaml`
- `L005_sector_relative_strength.yaml`（同一个 logic_id 的两份）
- `L006.yaml`、`L007.yaml`、`L008.yaml`

**全部对应已存在的 card**，且那些 card **都已经 parked**。

按设计 proposals 应当是 "card 创建前的草稿"，review 通过 → 创建 card → proposal 应移走或标 consumed。但 5 个文件从未清理。

更诡异：L005 有 **2 个打架的 proposal**，都写 `logic_id: L005` 且 `status: proposed`，但 L005 的 card 已经 parked。这些 proposal 是"改版提案"还是"历史草稿"？没有字段能回答。

### 问题 9.4：proposals schema 不统一

两种完全不同的 YAML 结构并存：

```yaml
# L005_peer_relative_reversal.yaml
proposal:                    # 外层 proposal dict
  logic_id: L005
  name: ...
  status: proposed

# L008.yaml
proposal_id: L008            # 扁平，无 proposal 外层
name: ...
status: proposed
```

任何代码读 proposals/ 都必须同时兼容两种 schema，或者只读其中一种会漏掉一半。

### 问题 9.5：reflection.md 长度差 45 倍，部分是 backfilled 薄记录

| logic | reflection 行数 | 说明 |
|---|---|---|
| L013 | 767 | 最大 |
| L001 | 696 | |
| L004 | 630 | |
| L009 | 394 | |
| L015 | 256 | |
| ... | ... | |
| L014 | 44 | |
| L010 | 30 | 大量段落重复 |
| L005 | 25 | |
| **L006** | **17** | backfilled 最薄 |

L006 的实际内容末尾明确写：
> `[Backfilled by repair_pipeline_state.py — original reflection was not generated during pipeline execution]`

说明 reflect 步骤**在那一轮根本没跑**，是后来修复脚本补的最低限度记录。这验证了 skill.md 里"允许退化"这条约束在现实中被触发过，而且不止一次。

L010 是另一种退化：reflection 看似 30 行但 `thesis_update / failure_boundary / bottleneck` 三段话几乎一模一样，是 LLM 复制粘贴同一段内容到不同 section——**叙事写了但没真写**。

### 问题 9.6：card thread 粒度和 reflection 叙事粒度不匹配

L001 的 card 里记录 9 个 thread（4 answered + 5 parked）。但 L001 的 reflection.md 有 696 行。

打开 reflection.md 看：里面提到的"已失败方向"远不止 9 个——很多失败方向只出现在自然语言里，**从未被结构化成 thread 条目**。

**含义**：
- card.deepening_threads = "已结构化的研究子问题"
- reflection.md = "所有思考过的东西"
- 两者粒度不一致，**如果你只读 card 的 thread，会严重低估 logic 实际尝试过的方向数**

这本身不完全算 bug（设计上 reflection 是 LLM 叙事的自由空间），但它意味着 **card 的 thread 无法作为"当前假设尝试过的空间"的权威视图**。

### 问题 9.7：parked 的 card 长期不更新（sleeping card）

`last_reflected_batch` 快照：

```
L003  parked        last_reflected=batch_003   ← 99 个 batch 没动过
L002  parked        last_reflected=batch_040
L001  parked        last_reflected=batch_062
L004  saturated     last_reflected=batch_061
L013  saturated     last_reflected=batch_098
L015  productive    last_reflected=batch_102
```

L003 的 reflection 冻结在 batch_003 的状态——之后 99 个 batch 的经验（比如其他 logic 撞到的类似 str_1m 陷阱）都**不会回写到 L003**。

后果：如果有一天想复活 L003，你看到的是一个 99 batch 前的快照，和当前系统知识水平严重脱节。**parked → 复活**这条路径实际上会很艰难，因为 card 里没有累积新知识。

### 问题 9.8：card 引用的 family 在 registry 不存在（和 Q8.2 耦合）

L015 的 `contract.preferred_families: [PF_fundamental_price_divergence]`
但 `storage/registry/families/` 下只存在 `PF_range_amount_flow.yaml` 和 `PF_volume_autocorrelation.yaml`。

**`PF_fundamental_price_divergence` 从没有对应的 family detail 文件**。L015 card 引用了一个不存在的 family ID。

这是 Q8.2 在 logic 层的另一种表现——没有 family 一致性校验，card、registry、family detail 可以互相引用不存在的对象。

### 问题 9.9：avoid_patterns 字段里混入了"VIABLE DIRECTIONS"

看 L015.yaml 的 `contract.avoid_patterns` 数组：

```yaml
avoid_patterns:
- "Pure value rank without price comparison..."
- "DO NOT use: relative amount conditioning..."
- "CONFIRMED DEAD ENDS:"                          # ← 这不是 pattern，是标题
- "Sub(CsRank(fundamental), ...): str_1m trap"
- "VIABLE PATH:"                                   # ← 这也不是 pattern
- "Pure fundamental change WITHOUT price component..."
- "VIABLE DIRECTIONS (to explore):"                # ← 这更不是 pattern
- "1. Revenue change × low PB (instead of low PE)..."
```

**`avoid_patterns` 字段里混入了 "VIABLE PATH" 和 "VIABLE DIRECTIONS" 两个语义相反的条目**——这些是"应该探索"的方向，不是"应该避免"的模式。

这是 LLM 写 reflect 时把所有想说的话都往 `avoid_patterns` 里塞。下游读 card 时：
- 如果代码层按字面语义使用 avoid_patterns 做禁忌过滤 → 会错误地把"viable direction"当作禁忌
- 如果只是 LLM 自己读 → LLM 可能还能理解，但结构化的可读性已经破坏

### 为什么重要

1. **schema drift**（9.1）会让新人写错 card，而且没有任何错误提示
2. **系统耗尽**（9.2）是现实问题，不是理论——batch_099–103 的强耦合直接源自此
3. **孤儿 proposals**（9.3、9.4）说明 proposal → card 的生命周期没有闭环
4. **reflection 退化**（9.5、9.6）意味着系统的"长期记忆"时好时坏，无法依赖
5. **sleeping card**（9.7）切断了 parked logic 的复活路径
6. **引用不存在的 family**（9.8）使下游聚合逻辑失效
7. **avoid_patterns 字段被污染**（9.9）让"硬禁忌"和"软建议"混在一起

### 可行方案

**方案 A（紧急，修 schema drift）**：统一 thread 字段名为 `id`（代码已兼容）或 `thread_id`（需要改代码）。选一边，更新所有文档（skill.md / CLAUDE.md / Q&A），并在 `LogicCard` dataclass 里用一个 `DeepeningThread` 结构化 dataclass 替代 `List[Dict]`，强制字段名。

**方案 B（必做，清理 proposals）**：
1. 扫 `proposals/` 下所有文件，检查对应 logic_id 的 card 是否已存在
2. card 存在且非 proposed 状态 → 把 proposal 移到 `proposals/archive/` 目录
3. 给 proposal 加一个 `purpose` 字段：`initial / revise / revive`，区分三种场景
4. 统一 YAML schema（选 `proposal:` 外层或扁平，一边统一）

**方案 C（推荐，card 清理老 thread）**：在 `/factor-reflect` 里加一条：当 thread 所有 next_probes 用完且 status=answered 超过 N batch，把该 thread 从 card 的 deepening_threads 里移到 `archived_threads` 子列表。保持 card 体积可控。

**方案 D（推荐，sleeping card 反刷新）**：每当 reflect 写入 global_escalation 时，识别 escalation 内容涉及的通用概念（如 str_1m、turnover_20d），自动在所有 parked card 的 `cross_logic_notes` 字段追加一条"这个教训也可能适用你"。让 parked card 也能被动学习。

**方案 E（必做，一致性校验器）**：给 `storage/consistency.py` 加 logic 层检查：
- 所有 card 引用的 family_id 必须在 registry/families 下有对应文件
- 所有 proposal 的 logic_id 必须和 card 的 logic_id 不冲突（或有明确 `purpose`）
- `avoid_patterns` 条目不能以 `VIABLE` / `DO USE` 等正向词开头（防污染）
- reflection.md 行数下限检查（< 30 行的警告 backfilled / 退化）

**方案 F（可选）**：把 `avoid_patterns` 拆成两个字段：`hard_avoid`（代码级禁忌）和 `viable_directions`（软建议）。让两类信息结构化分离。

### 优先级

A > E > B > C > D > F。A 必做（影响所有新 card 写入）。E 紧跟（防止问题扩散）。B 是一次性清理。C/D 是长期治理。F 是锦上添花。

### 关联观察

- Q9.1 和 Q3 都是 schema drift，修复共享同一个工具链（dataclass 化 + 校验器）
- Q9.2 和 Q5 是同一个症状的两个视角——Q5 从 batch 看，Q9.2 从 thread 看
- Q9.8 和 Q8.2 都是 family 引用不一致
- Q9.7（sleeping card）和 Q8.3（family 升格死代码）都是 "跨 batch 证据累积不工作"的表现

把 Q1–Q9 的所有问题按根因分类，发现它们指向的修复动作已经聚到了 **4–5 个共享支点**：
1. **Schema 校验 + dataclass 化**（Q1, Q3, Q8.1, Q9.1, Q9.4）
2. **Expression/family 反向索引**（Q3, Q4, Q7, Q8.2, Q9.8）
3. **缓存/数据 GC 统一**（Q6, Q7）
4. **跨 batch 证据聚合器**（Q5, Q8.3, Q9.7）
5. **Consistency checker**（所有 "两边不一致" 的问题）

修这 5 个共享支点就能一次性清掉大半症状。

---

## Q10 — `storage/logic/proposals/` 是一个完全孤儿的目录（化石层）

**提问时间**: 2026-04-11
**相关阶段**: Phase 0 logic 创建 / `/factor-logic new`

### 核心发现

**Proposal 作为概念是有意义的**——它是"logic 创建前的 4 维审查门槛"。但在当前架构里，proposal 有两条通道，**`storage/logic/proposals/` 不属于任何一条**。

两条真实通道：
- **(A) In-context proposal**：`/factor-logic new` 在单次对话里完成 proposal 草稿 + 4 维 review + 裁决 → 通过的直接写 `cards/LXXX.yaml`。**proposal 本身不落盘**。skill.md 里明确写："提案与审查在本轮上下文中完成，最终只把通过的 logic 落到 card。"
- **(B) Escalation proposal**：`/factor-reflect` 发现跨 logic 模式 → 构造 `GlobalEscalationDelta.logic_proposals` → 写到 `storage/state/global_escalation.yaml`（带 `status: pending`）→ 下一轮 `/factor-mine` Phase 0 消费。

**`storage/logic/proposals/` 目录不属于 A 也不属于 B**。

### 证据：零代码引用

```bash
grep "proposals/" src/       → 0 matches
grep "proposals_dir" src/    → 0 matches
grep "proposal_file" src/    → 0 matches
```

`.claude/skills/` 下唯一的 "proposals" 命中是 `factor-mine/skill.md:43`，但那里说的是 `global_escalation.logic_proposals` 字段，**不是**这个目录。

**Python 代码里没有任何地方读或写 `storage/logic/proposals/`。**

### 目录里的 5 个化石文件

- `L005_peer_relative_reversal.yaml` — outer `proposal:` dict，带完整 4 维 review
- `L005_sector_relative_strength.yaml` — 同结构，和上面同一个 logic_id，两个打架的草稿
- `L006.yaml` — 同结构
- `L007.yaml` — 同结构
- `L008.yaml` — **不同结构**，扁平 `proposal_id: L008`，无 `proposal:` 外层

所有 5 个文件对应的 card（L005/L006/L007/L008）**都已存在且都已 parked**。这些 proposal 早在 card 被创建时就应该被清理——但没人清理，因为：
- 没有代码路径会触发清理
- 没有 skill 文档把"清理 proposals"列为必做步骤
- LLM 在自主模式下可能还会偶尔往这里写（从 L005 的两份打架草稿可以推断）

### L005 两份 proposal 的"半成品"状态

看 `L005_sector_relative_strength.yaml`：

```yaml
proposal:
  logic_id: L005
  status: proposed
  review_status: pending         ← 还在等 review

4d_review:
  mechanism_review: |            ← 但 4 维 review 已经写完
    ...
  feasibility_review: |
    ...
  novelty_review: |
    ...
  research_value_review: |
    ...
```

**这是一个半成品**：LLM 把 proposal 和 review 都写下来了，但既没有从 review 走到 `create_logic` 裁决，也没写 card，也没清理 proposal。最终 L005 的 card 可能是从另一条路径创建的（比如通过 global_escalation），两个 proposal 就变成了孤儿。

### 与 Q9.3/9.4 的区别

- Q9.3 说 "proposals/ 里的 5 个文件是孤儿"
- Q9.4 说 "这 5 个文件的 schema 不统一"
- **Q10 说的是根源**：**整个目录就不应该存在**

Q9 是站在"目录合法、但文件坏了"的视角在报告症状；Q10 是站在"目录本身就是废弃架构的化石"的视角在报告根因。

### 历史成因推测

最可能的来源：**早期工作流原型**。在当前设计定稿之前，应该试过一个版本："proposal 落盘 → LLM 读盘做 review → review 通过才 promote 成 card"。后来简化为 "in-context proposal + 直接写 card"，但：
- 旧的 YAML 文件没人清理
- 目录结构（`storage/logic/proposals/`）没人删
- skill 文档里没有明确标注 "此目录已废弃"
- 新 LLM 在跑 `/factor-logic new` 时偶尔还会误以为要往这里写（从 schema 不一致可以看出是不同时期手写的）

### 为什么重要

1. **误导性**：新人看到 `storage/logic/proposals/` 会以为它是 proposal 工作流的一部分。实际上系统跑 100+ 个 batch 从没用过它。
2. **LLM 自主模式下可能继续写**：没有明确的"此路不通"警告，下一次 reflect 或 logic 工作流偶尔还会生成新的孤儿文件。
3. **Schema 漂移的温床**：没有代码约束的目录，schema 会随 LLM 写法漂移（Q9.4 就是这种漂移的副产品）。
4. **掩盖真正的 proposal 机制**：双通道已经足够复杂，再加一个"假的"目录让新人三重困惑。

### 可行方案

**方案 A（推荐，一步到位）**：物理删除整个 `storage/logic/proposals/` 目录。
- 前置：在 git 里确认这 5 个文件没有被任何生产工具引用（已验证 src/ 下零引用）
- 删除：`git rm -r storage/logic/proposals/`
- 同时在 `storage/logic/README.md` 或 skill.md 里加一条注释："proposals are in-context only; there is no persistent directory for them"
- 代价：近零

**方案 B（保守，归档）**：把 5 个文件移到 `storage/logic/_archive/proposals_legacy/` 并加 README 说明"早期工作流遗留，不再使用"。
- 优点：保留历史
- 缺点：仍然是一个"看起来像生产目录"的路径，新人可能仍然困惑

**方案 C（预防再生）**：在 `/factor-logic new` skill.md 里加一段明确指令："**不要**写 `storage/logic/proposals/`。Proposal 和 review 都在本轮会话上下文里完成。"
- 配合 A 或 B 使用，防止 LLM 未来又往相同或相似路径写文件

**方案 D（强制，code guard）**：在 `StoragePaths` 里加一个 property `proposals_dir` 并故意让它返回一个会报错的 sentinel 对象。任何试图写 proposals 的新代码会立即崩溃。
- 代价：小
- 效果：把"软规约"升级为"代码硬阻塞"

### 优先级

**A + C 必做**（删除 + 更新文档一次性搞定）。D 可选（防御性编程）。B 不推荐（保留反而制造混乱）。

### 关联观察

- Q10 和 Q9.3/9.4 同源：Q10 是根因，后两个是症状
- Q10 和 Q1（idea_report 丢失）都是 "skill.md 的约束没有代码层执行" 的例证——idea_report 应该写但 LLM 偷懒不写；proposals 不应该写但 LLM 偶尔还会写。**两个方向的漂移都存在**，说明"靠自律"在 LLM 维护的系统里是不可靠的。
- 修 A + D 同时也暴露了一个可操作的模式：**任何"不再使用"的目录都应该物理删除或代码层拦截**，而不是留着注释说"不要写"。对 LLM 自主模式尤其关键。

**[2026-04-11 更新]**：Q10 的结论被 Q11 修正。Q11 的设计要求 proposal **必须**落盘且必须走严格 schema。因此方案 A（删除目录）被撤销。正确方案是**保留目录但重新定义其职责**（见 Q11 方案 2）。

---

## Q11 — 系统需要"自我探索 → 自我假设 → 自我变异 → 自我总结"的能力（方向宣言）

**提问时间**: 2026-04-11
**性质**: **设计方向**，不是 bug 报告。和 Q1–Q10 的性质不同——前 10 个是"让现状不崩"，本条是"让系统真的具有自主性"。

### 两个触发这条讨论的直觉

**直觉 1**：proposal 应该落盘。当前 skill.md 把 proposal 设计为 in-context，是因为怕"proposal 目录变垃圾场"（见 Q10）。但真正的价值**不在备份**，而在"**一个东西只有被迫结构化写出来才能发现它是不是真的想清楚了**"。在场 hypothesis（如 L015 的 4 行 yaml）过于简单，完全没有论证 depth。

**直觉 2**：系统目前只会在一条路上挖到死。batch_099–103 全是 L015 微扰。缺少"summarize → think → mutate → explore"的主动循环。

这两个直觉其实是**同一件事的两面**：都是在要求"**系统具备元认知能力，能跳出当前执行循环去审视自己在干什么**"。

### 当前系统缺什么

对照"summarize → think → mutate → explore"四个动作：

| 动作 | 当前有的 | 当前缺的 |
|---|---|---|
| **Summarize** | per-batch per-logic 的 reflect | 跨 batch、跨 logic 的横向总结 |
| **Think** | 完全没有 | "为什么系统呈现这个形状" 的元认知 |
| **Mutate** | 参数微扰（60d→80d→120d）| 真正的结构性变异（换 field、换 scale、换因果方向）|
| **Explore** | `schedulable_logic_ids` + broaden/pivot 策略 | **硬约束**——当前全靠 LLM 自律，熟悉方向天然懒惰 |

核心问题：**reflect 是按 logic 处理的，它一次只看一条 logic 的结果**。它不问 "系统本身是不是有问题"。跨 batch 的比较、跨 logic 的共同失败模式识别、元认知跳出——**这些动作在当前 pipeline 里完全没有对应的 phase**。

### Hypothesis 为什么简单——不是写的问题，是强制的问题

看 L015 的 hypothesis 字段：

```yaml
hypothesis:
  condition: 个股基本面估值（PE/PB）的改善速度与价格动量的背离程度
  behavior: 当PE/PB比率改善...
  timeframe: 20-60d估值改善期，10-20d持有
  direction: 做多
```

4 行字就是整条假设的全部思考记录。**没有**：
- 竞争假设对比（为什么不是其他解释？）
- 数学形状推导（为什么是这个 operator 组合）
- 失败前提枚举（如果错了，哪里会先崩？）
- 和已知 Barra factor 的正交性论证
- novelty argument vs 已有 logic 和 academic literature

这不是 LLM 写作能力差的问题——**是 card schema 根本没有这些字段**。没字段就没压力就不写。补齐这些字段会强制 LLM 把思考推到底。

### 方向设计

下面 4 个机制合起来能真正实现"自主循环"。**它们是相互咬合的，缺一个整个循环就不成立**。

**方案 1：Meta-reflect 层**

- **触发时机**：每 N 个 batch 一次（建议 N=5），或者 `schedulable_logic_ids` 只剩 1 条时
- **输入**：过去 N 个 batch 的所有 judge_report + 所有 logic cards + reflection.md 的时序 + batch_usage + hypothesis journal
- **输出**：元认知报告，存 `storage/state/meta_reflection_XXX.md`，包含：
  - 过去 N batch 的失败模式聚类（上层抽象，不是单个 batch 的 failure_boundary）
  - 共同盲区（哪些 field / mechanism / style 从未被尝试）
  - 系统级可疑假设（"validation 窗口是否覆盖完整 regime" 这类问题）
  - 建议的新探索方向（作为 logic_proposals 的种子）
- **关键点**：这是一个**系统对自己的观察**，不是对单个 batch 的观察。是当前完全缺失的一层。

**方案 2：Hypothesis Journal（落盘的结构化 proposal 工作台）**

**撤销 Q10 方案 A**。改为：

- 保留 `storage/logic/proposals/` 目录但重新定义职责
- 所有 `/factor-logic new` 的输出**必须**先写到这里（不管通过与否）
- 所有 proposal **必须**填完强制 schema：
  ```yaml
  proposal_id: P_YYYYMMDD_NNN
  hypothesis:
    core_claim: "..."                    # 一句话命题（必填）
    mechanism:
      entities: [...]                    # 参与的经济实体（必填）
      causal_chain: [...]                # 因果链，至少 2 步（必填）
      time_scale: "..."                  # 时间尺度（必填）
    competing_explanations:              # 必填，至少 2 条
      - explanation: "..."
        why_rejected: "..."
    disconfirming_evidence:              # 必填
      if_wrong_first_sign: "..."
      failure_signature: "..."
    novelty_argument:                    # 必填
      vs_barra_factors: "..."
      vs_existing_logics: "..."          # 必须 reference 具体 LXXX 做对比
      vs_academic_literature: "..."      # 可以为 "unknown" 但必须明确声明
    mathematical_form:
      preferred_shape: "..."
      why_this_shape: "..."              # 必须解释为什么不是其他 operator 组合
    exploration_plan:
      first_batch_question: "..."
      stop_condition_if_successful: "..."
      stop_condition_if_failing: "..."
  lifecycle:
    status: drafted | under_review | accepted | rejected | parked | superseded
    created_at: ...
    reviewed_at: ...
    promoted_to: LXXX  # 若 accepted
    supersedes: P_YYY  # 若 superseded
  review:
    mechanism_review: {verdict, notes}
    feasibility_review: {verdict, notes}
    novelty_review: {verdict, notes}
    research_value_review: {verdict, notes}
  ```
- **所有 proposal 永久保留**，包括 rejected / parked。rejected 的 proposal 是非常有价值的失败记忆，防止半年后重复考虑同一方向
- 新 logic 创建前**必须** grep proposal journal 查是否有相同/相似命题
- meta-reflect 层读这个 journal 做 pattern recognition（比如 "过去 10 条 proposal 里有 6 条在 mechanism_review 失败，共同原因是..."）

**方案 3：Exploration Budget（代码级硬约束）**

不是软建议，是**拒绝性约束**：
- **本轮 1/3 法则**：每个 batch 至少 1/3 候选必须来自"非当前 dominant logic"的方向（比如 L015 占 4 个候选则必须有 ≥2 个来自别的 logic）
- **ELT 冻结规则**：同一 ELT 连续 3 个 batch 未升级 `.next_version()` → 下一轮该 ELT 被禁用一次，必须换方向
- **新颖度底线**：过去 5 batch 的 novelty score（expression AST 距离）低于阈值 → 下一轮强制调用 meta-reflect，且禁止 deepen 策略
- **永久探索税**：即便 schedulable 里只有 1 条 productive logic，也必须预留 1 个候选 slot 给 "adjacent exploration"（试完全不相关的方向）

这些都在 `src/research/logic/scheduler.py` 和 `/factor-idea` precheck 层实现。**LLM 不能通过偷懒绕过**。

**方案 4：Genuine Mutation Primitives（真变异操作符）**

在 `/factor-idea` Step 6 的 candidate expansion 模板里增加**结构性变异类型**：

| 变异类型 | 定义 | 合法性检查 |
|---|---|---|
| **field_swap** | 把某个字段换成**未使用过**的字段 | 新字段必须不在当前 logic 的历史 expression 里出现过 |
| **scale_flip** | 把日度信号变成季度（或相反）| lookback 必须跨过 60d 门槛 |
| **target_shift** | 单股观察变行业/截面偏离观察 | 必须引入 CsRank 或 industry aggregation |
| **causal_direction_flip** | A→B 变 B→A 或 A↔B 交互 | 表达式结构必须有明显重排 |
| **operator_family_swap** | 乘法 conditioning 变减法 decorrelation | 顶层 operator 必须变 |

当前的 `mutate` route type 只是泛指，没有细分模板。新增这些子类型后，每个 candidate 的 `mutation_subtype` 字段必须填，precheck 层会校验"声称的变异类型是否真的发生了"（比如 field_swap 声称换了字段但实际没换 → 拒绝冻结）。

### 为什么这 4 个机制必须一起做

它们是一个咬合循环，**缺一个就断链**：

```
Meta-reflect (think)          ← 发现 "系统在原地踏步"
     │
     ▼  产出新方向建议
Hypothesis Journal (write)    ← 把建议严苛地推敲成结构化 proposal
     │
     ▼  通过 4 维 review 的 proposal 落 card
Exploration Budget (force)    ← 强制本轮必须尝试新方向
     │
     ▼  candidate 必须带真变异类型
Genuine Mutation (vary)       ← 产出真正不同的候选
     │
     ▼  跑完 execute/judge/reflect
     │
     └──── 新的 batch 数据 ──── → 回到 Meta-reflect
```

- 没有 Meta-reflect → 没人发现系统需要变
- 没有 Hypothesis Journal → 新方向永远停在"想了几行字"级别
- 没有 Exploration Budget → LLM 永远选择熟悉方向
- 没有 Genuine Mutation → 就算"尝试新方向"也只是参数扰动

当前系统里**这 4 个全都缺或半成品**。修 Q1–Q10 的 bug 只是让现状不崩，但系统仍然会一直踏步。Q11 要解决的是"让系统真的会走路"。

### 与 Q1–Q10 的关系

| Q | 类型 | 修复完之后，Q11 是否仍然需要？|
|---|---|---|
| Q1–Q10 | bug / 数据治理 | 是。Q1–Q10 修完只是"数据一致了"，系统依然是踏步的 |
| Q11 | 设计方向 | **是最终目标**。Q1–Q10 是必要条件（数据基础），Q11 是充分条件（系统能力）|

具体耦合：
- Q11 方案 2（Hypothesis Journal）需要 Q9.1（thread schema 校验）先落地，否则 journal 会被 schema drift 污染
- Q11 方案 1（Meta-reflect）需要 Q5 / Q8.3 / Q9.7 里提到的 "cross-batch aggregator" 做基础
- Q11 方案 3（Exploration Budget）需要 Q4 的 expression_index（才能算 novelty score）
- Q11 方案 4（Genuine Mutation）需要 Q3 / Q4 的 lineage dataclass 规范化（才能校验变异类型声明）

**所以 Q1–Q10 的修复不是"可以延后的卫生工作"，是 Q11 的前置条件**。

### 优先级

这是整个 Q 列表里唯一标 **"方向"** 的一条。它本身不需要 "立即修"——它需要被**当作规划目标**。修 Q1–Q10 的动作都应该**朝向 Q11 的方向**设计，避免回头。

具体建议的推进顺序：
1. 先做 Q9.1 + Q3（schema 基础设施）
2. 再做 Q4（expression index）
3. 再做 Q11 方案 2（Hypothesis Journal——这一步会逼出 proposal schema 设计）
4. 再做 Q11 方案 1（Meta-reflect）
5. 最后做 Q11 方案 3 + 4（budget + mutation primitives）

### 重要备注：Q10 结论修正

Q10 原本建议"物理删除 `storage/logic/proposals/` 目录"。**Q11 撤销这个建议**。

正确做法：
- 保留目录
- 清理 5 个化石文件（或标记为 `legacy_rejected`）
- 按 Q11 方案 2 的 schema 重新定义目录职责
- proposal 不再是"in-context 临时草稿"，而是"永久假设工作台"

---

## Q21 — Meta 观察合集：系统的 3 个结构性 pattern 家族

**入档时间**: 2026-04-11
**性质**: 这不是一个单独的 bug，是**跨 Q 的 pattern 合集**——把散落在 Q1–Q20 的"关联观察"里反复出现的结构性问题集中表述，便于后续审查和修复规划。

### 为什么需要这个合集

过去 20 个 Q 里，我反复在"关联观察"小节里提到同一些 pattern（"半成品优化"、"文档撒谎"、"testing inversion"）。这些 pattern 分散在各 Q 里**没有集中表述**，导致：
1. 修复时只能针对单点，看不到 pattern 全貌
2. 新来的人（或未来的 LLM 实例）看不出"这些 Q 背后是不是同一个问题"
3. 难以设计**防御性 check**（比如"CI 里增加规则防止同类问题再发生"）

这里把它们明确列出，作为**系统审查的 check list**。

### Pattern 家族 A：**"半成品优化" (Half-done optimization)**

**核心定义**：有人意识到某个优化该做，做了**一半**，然后"以后再补"从来没发生。

**具体实例**（按 Q 索引）：

| Q | 半成品的部分 | 完整的部分 |
|---|---|---|
| **Q6** | artifacts 的生成代码 | **GC / 清理代码完全缺失** |
| **Q7** | `FactorValueCache.cleanup()` 方法写了 | cutoff 时间戳字段选错（用 `validation_range[-1]` 而非 mtime），**从不删** |
| **Q12** | `prepare_batch` 对 returns 做了批量 | library factor 仍然 for 循环 19 次独立 Qlib 调用 |
| **Q12** | Qlib 的 `D.features(fields=[list])` 支持批量 | 每次调用都只传 `fields=[one_expr]` |
| **Q14** | `_apply_tradability` 方法实现正确 | 所有 4 个调用点硬编码 `tradability_check=False` |
| **Q16** | `limit_up / limit_down` 字段全链路同步到 qlib binary | **零代码消费**——没有任何地方做 `close == limit_up` 比较 |
| **Q16** | 3 个 config flag (`filter_suspend / filter_limit / min_listing_days`) 存在 | **零代码读取**——flag 是摆设 |
| **Q18** | `prepare_batch` 预取 4 个 horizon (h=1/5/10/20) | validation 期**只用 h=5**，h=1/10/20 在 validation 期**完全没被消费** |
| **Q19** | 整个 `stats/` subpackage（7 文件 + tests + code review）存在 | **零 import**，是死代码 |
| **Q19** | 整个 `feasibility/` subpackage（engine + 4 子模块）存在 | **零 import**，是死代码 |
| **Q19** | `split_stability / regime_stability / bootstrap / purged_walk_forward / multiple_testing_risk_bucket` 的 clean 版实现存在 | inline 版用 `"medium"` / `None` / `"low"` 占位，**从不计算** |

**共 11 个确认实例**。

**为什么这个 pattern 危险**：

1. **对 LLM 自主维护尤其致命**：LLM 看到"这里有个实现"就假设它完整。不会主动 grep 调用链验证、不会注意到硬编码占位、不会比对声明与实现。**只有用户追问细节时才会被动发现**。
2. **症状不会自己暴露**：半成品的部分表面上看起来 "在运行"，指标能输出数字。只是数字是假的。没有 runtime error，没有 test failure，只有在外部审查时才暴露。
3. **技术债利息极高**：半成品阶段说 "先占位，以后再补"——但没有 ticket、没有 TODO 记录、没有 deadline。"以后"永远是 "不是现在"。

**防御性修复**：

- **CI rule**：所有 `subpackage.__init__.py` 里 export 的东西必须被 grep 到至少一个非自身的 import（否则是孤儿）
- **CI rule**：所有配置字段（`@dataclass` 或 yaml）必须被 grep 到至少一个读取点
- **Code review checklist**：新代码里凡是出现 `None` / `"medium"` / `"low"` 作为 return value 的位置，必须有注释说明为什么是默认值
- **Linter rule**：`_param=False` 作为默认参数的调用，必须明确注释理由
- **Meta-reflect 层**（Q11 方案 1）应当把"subpackage 孤儿检查"作为定期运行的 audit

### Pattern 家族 B：**"文档/字段名撒谎" (Documentation lie)**

**核心定义**：docstring / 字段名 / 注释 / 计划文档**声明了一个能力**，但代码里**实现不存在或与声明相反**。

**具体实例**：

| Q | 撒谎位置 | 真实情况 |
|---|---|---|
| **Q1** | `factor-idea/skill.md` 说 idea_report.yaml 必须写 | 最近几个 batch 的 idea_report 全部缺失 |
| **Q3** | `domain/schema.py::Lineage` dataclass 字段 | YAML 里实际写的字段完全不同（`parent_expression` vs `parent_factors`）|
| **Q9.1** | 所有文档说 thread 字段叫 `thread_id` | YAML 实际字段名是 `id` |
| **Q14.1** | preprocess.py docstring 说"5 步包括 universe_mask" | `universe_mask` 方法**根本不存在** |
| **Q14** | preprocess docstring 说 "winsorize at 1%/99% 分位" | 实际是 mean ± 3σ（σ-based，不是 percentile）|
| **Q14** | preprocess docstring 说 neutralize 剥除 Barra style | 实际只是 group demean，做不了 Barra 回归 |
| **Q16.3** | `mining-preprocessing.md` 说 "config flags and neutralization logic are already in place" | 逻辑根本不存在，只有 flag 占位 |
| **Q17** | `cap_industry_neutral_ic` 字段名暗示做了 cap + industry 联合中性化 | schema 注释直接承认 "cap-only degradation; name kept for doc alignment"——主动保留的谎言 |
| **Q19** | `regime_stability` 字段名暗示算过 regime 分析 | 硬编码 `"medium"`，永远是 "medium" |
| **Q19** | `bootstrap_stability_score` / `purged_walk_forward_score` 字段名 | 永远是 `None`，从不计算 |
| **Q19** | `multiple_testing_risk_bucket` 字段名 | 硬编码 `"low"`，不读 ledger |
| **Q19** | `search_adjusted_strength_bucket` 字段名（有"adjusted"）| 实际不做 search adjustment，只看 ic_mean 和 ic_ir |

**共 12 个确认实例**。

**为什么这个 pattern 危险**：

1. **文档是 LLM 的权威来源**：LLM 倾向于信任 docstring 作为 "单一真相"。撒谎的 docstring 会让 LLM 构建错误的系统心智模型，然后在这个错误模型上做决策。
2. **错误会传播**：我讲解 Phase 2 Preprocess 时把 docstring 当真，导致"5 步走"的错误描述传播到 Q14 的背景——**这是 Q14.5 发现的 5/5 walkthrough 错误**。任何看了前一版 walkthrough 的人都会被二次误导。
3. **无法被 static analysis 发现**：字段名 / docstring 本身是文本，没有类型检查能发现 "这个字段的值其实是硬编码占位"。只有运行时观察行为才能发现。
4. **名字本身是规约**：字段名叫 `multiple_testing_risk_bucket`，消费者（judge layer）会据此假设"这个值经过多重检验计算"。**名字就是对消费者的承诺**。命名撒谎 = 合同违约。

**防御性修复**：

- **规约**：任何 "能力已就位" 的声明**必须引用可 grep 的代码位置**（比如 "see `src/research/compute/preprocess.py::_apply_tradability`"）。否则 code review reject。
- **字段重命名**：硬编码 `None` / `"medium"` 的字段应该加前缀 `_placeholder_` 或 `_todo_`，让消费者立即知道"这是占位不是真值"
- **Schema 校验**：所有字段应该有对应的 dataclass/pydantic 模型。实际写入值必须通过模型——能过滤掉 "字段名说 float，实际填 'medium' 字符串" 这种情况
- **Docstring CI**：docstring 里提到的方法名（"calls self._universe_mask()"）必须能在同文件或 import 链里 grep 到，否则 CI 失败
- **Meta-reflect 层**应当定期扫 "docstring 声明 vs 实际代码" 的一致性

### Pattern 家族 C：**"Testing Inversion" (测试倒挂)**

**核心定义**：**被审查过、有测试的代码是死代码。没审查过、没测试、有大量硬编码假数据的代码在做生产决策。**

**具体实例**：

| Q | Clean 版（有 tests + 过 review） | Inline 版（生产在跑） |
|---|---|---|
| **Q19** | `stats/effect_strength.py` + `test_effect_strength.py` (151 行 test) | `compute_implementations.py::compute_stat_evidence` 内联 |
| **Q19** | `stats/stability.py` (236 行 + test) | inline + 硬编码 "medium" |
| **Q19** | `stats/reliability.py` (297 行 + test) | inline None / 假 2 段 split |
| **Q19** | `stats/multiple_testing.py` (98 行 + test) | inline 硬编码 "low" |
| **Q19** | `feasibility/engine.py` + 4 子模块 | `compute_feasibility` 内联，4 字段硬编码 |
| **Q14** | `preprocess._neutralize` 方法（可以 unit test） | 默认 `neutralize_col=None`，从不启用 |

**共 6 个确认实例**。

**为什么这个 pattern 危险**：

1. **质量感知完全倒转**：任何 static analysis 工具 / code review 都会说 subpackage 质量更高——但质量高的那份在磁盘上躺着，质量低的那份在做生产决策。**外部观察者会对系统质量产生错觉**。
2. **测试覆盖率误导**：pytest 跑一下会显示 "stats/ 有 XX% 测试覆盖率"，给人 "这个系统被测试了" 的错觉。**但被测试的是死代码，在跑的代码没测试**。
3. **重构阻力**：即使有人想把 inline 版迁移到 clean 版，clean 版的 API 和 inline 版的 data flow 可能已经不匹配（比如 clean 版返回 `ic_series`，inline 版不）。迁移成本越来越高。

**防御性修复**：

- **CI rule**：任何有对应 `test_*.py` 的函数必须被至少一处非 test 代码 import，否则警告
- **CI rule**：生产代码路径里出现的重要函数必须有对应的 test 覆盖（走 production trace，看哪些被真正调用）
- **治理规约**：重构新代码时必须**同步删除或明确标注 deprecated** 被替换的老代码。不允许 "两个版本并存"
- **代码 review 硬规则**：如果 PR 里出现一个新的 inline 函数，且存在同名或同功能的 subpackage 函数，必须说明为什么不直接调用 subpackage

### 三个家族之间的关系

这 3 个家族**互相关联**但**不完全重合**：

```
                 Pattern A               Pattern B               Pattern C
               半成品优化                 文档撒谎                Testing Inversion

实例重叠:
  Q14 preprocess ✓                          ✓                        ✓  (neutralize)
  Q16 limit_up   ✓                          ✓                         
  Q19 stats/     ✓                          ✓                        ✓
  Q19 feasi/     ✓                          ✓                        ✓
  Q18 horizons   ✓                          
  Q7  cleanup    ✓                          
  Q6  artifacts  ✓                          
```

**大多数 Q19/Q14 里的问题同时属于 A+B+C 三个家族**——这是"核心 rot"。Q18/Q16/Q12/Q7/Q6 主要属于 A（半成品）。

### 总体 meta 观察

**这 3 个 pattern 家族加起来描述了一种特殊的系统退化方式**：**"有人想做对的事，做了一半，留下一个看起来对但其实空洞的骨架。然后没人发现。"**

这种退化方式的 root cause 是：
1. **开发节奏碎片化**：快速迭代里没时间把每个优化完成
2. **审查脱离运行**：code review 看代码是否"正确"，但不验证代码是否"被调用"
3. **测试脱离数据路径**：test coverage 基于 static analysis，不跟 production trace 对齐
4. **LLM 倾向于信任文档**：对一个 LLM 主导维护的系统，文档撒谎的后果会被放大——因为 LLM 不会主动质疑文档

**修复 root cause 比修复任何单一 Q 都重要**。建议的治理层动作：

1. **增加 runtime audit**：跑一个脚本扫 "真正被 import 的 subpackage" vs "存在的 subpackage"，差集是孤儿。每月跑一次
2. **增加 docstring ↔ code 一致性检查**：用 AST 检查 docstring 里 claim 的 method 是否存在
3. **增加 config flag 消费检查**：所有 `@dataclass` 字段和 yaml key 必须有 grep 到的 reader
4. **Meta-reflect 层（Q11）** 应当把这 3 个 pattern 的 check 作为定期任务

### 关联观察

- **Q21 不是新问题**：它是 Q1–Q20 里已经散落的观察的集中归档。但**集中归档本身是价值**——它让"修 Q1 到 Q20" 从 20 个独立任务变成 3 个 pattern 家族的系统性修复。
- **优先级排序**：Pattern A > Pattern C > Pattern B。A 是直接影响决策的假数据，C 是可验证的测试结构问题，B 是慢性误导。
- **Meta-reflect（Q11）是唯一能长期防止这 3 个 pattern 重现的机制**——因为它是系统内生的"审查自己"的层，不依赖外部人工审查。当前系统没有这一层，所以 pattern 会继续累积。

---

## Q22 — Redundancy Layer 2（family overlap）的 30% 权重是死代码：schema drift 让 structure_overlap 永远为 0

**入档时间**: 2026-04-11
**相关阶段**: Phase 2 Stage D Step 8 Redundancy Analysis

### 背景

Stage D 的 Redundancy Analysis 设计了 3 层递进检查：
- Layer 1 pairwise: 新 factor vs 每个 library factor 的两两相关
- **Layer 2 family: 家族级组合 overlap**
- Layer 3 subspace: ridge 回归取残差看 incremental IC

这个 Q 揭示 **Layer 2 实际上几乎完全无效**——30% 的权重永远乘以 0，剩余部分和 Layer 1 重复。

### 证据：Schema Drift

`family.py:114-121` 的 `family_overlap_score` 公式：

```python
score = (
    0.50 * corr_p90              # 50%: 同 family member 的 90 分位相关
    + 0.30 * struct_overlap       # 30%: 结构模板重叠
    + 0.20 * (1.0 - clipped_residual)  # 20%: 残差生存补
)
```

`_compute_structure_overlap`（family.py:47-62）：

```python
def _compute_structure_overlap(candidate_structure, family_registry_entry):
    keys = ["structure_template", "conditioning_type", "horizon_bucket"]
    matches = 0
    for key in keys:
        cand_val = candidate_structure.get(key)
        reg_val = family_registry_entry.get(key)
        if cand_val is not None and reg_val is not None and cand_val == reg_val:
            matches += 1
    return matches / 3.0
```

**需要 3 个字段**：
- `structure_template`
- `conditioning_type`
- `horizon_bucket`

**实际的 candidate_meta**（`compute_implementations.py:418-422`）：

```python
candidate_meta = {
    "family_id": candidate.get("family_id", "FM_unknown"),
    "logic_id": candidate.get("logic_id", ""),
}
```

**3 个必需字段一个都没有**。

**实际的 family YAML**（`storage/registry/families/PF_range_amount_flow.yaml`）：

```yaml
family_id: PF_range_amount_flow
status: provisional
description: ''
structural_signature: ''       # ← 注意是 structural_signature, 不是 structure_template
typical_ops: []                # ← 不是 conditioning_type
typical_fields: []             # ← 不是 horizon_bucket
factor_ids: [F017]
```

**YAML 用 `structural_signature / typical_ops / typical_fields`，代码要 `structure_template / conditioning_type / horizon_bucket`**。**没有一个 key 对得上**，而且这些 YAML 字段本身也是空字符串/空列表。

### 后果

对**每一个** candidate：
- `candidate_structure.get("structure_template")` → `None`
- `family_registry_entry.get("structure_template")` → `None`
- 3 个 `if cand_val is not None and reg_val is not None` 全部 False
- `matches = 0`
- `struct_overlap = 0 / 3 = 0.0`

**30% 的权重永远乘以 0**。实际公式退化为：

```
score = 0.50 * corr_p90 + 0.20 * (1 - max_corr)
```

但 `residual_survival_ratio = 1 - max(abs_corrs)`（family.py:109）——**这只是 `max_corr` 的变形**，不是真正的"回归后残差的生存率"。

**Layer 2 的实际公式**（schema drift 生效后）：

```
score = 0.50 * corr_p90 + 0.20 * (1 - max_corr)
```

**这是 `max_corr` 和 `corr_p90` 的线性组合**——两者都来自 pairwise correlation 计算（Layer 1）。**Layer 2 和 Layer 1 在同一组原始信息上做不同变换**，几乎完全冗余。

### 真正能区分"Layer 2 vs Layer 1"的是什么？

**什么都没有**。在当前状态下：
- Layer 1 输出 `max_lib_corr`（= max_corr）和 `all_correlations`（所有 member 的相关分布）
- Layer 2 输出 `family_overlap_score = 0.5 * corr_p90 + 0.2 * (1 - max_corr)`

Corr_p90 是 family member 相关度的 90 分位——Layer 1 的 `all_correlations` 里按 family 筛选后取 p90 就能得到同样的数字。**Layer 2 不产出 Layer 1 不能给的任何独立信息**。

### 为什么这会被忽略

1. Layer 2 的**输出字段 `family_overlap_score` 看起来是一个合理的新指标**——judge 看到会以为系统做了"家族级重叠分析"
2. 它有 bucket（low/medium/high）和 family_size 等 metadata，看起来数据丰富
3. **字段名和 bucket 都在撒谎**——让消费者以为 Layer 2 提供了独立信息，实际没有

这是 Q21 Pattern A（半成品）+ Pattern B（命名撒谎）的典型案例。

### 核心问题 1：schema drift 根源

`_compute_structure_overlap` 想要的字段 (`structure_template / conditioning_type / horizon_bucket`) 可能是**早期设计里存在的字段**，后来重构时：
- candidate_meta 只保留了 family_id / logic_id（`compute_implementations.py`）
- family YAML 保留了不同的字段（`structural_signature / typical_ops / typical_fields`）
- 但 `family.py` 没跟着改

结果是 Layer 2 的核心输入**在数据源层不存在**。

### 核心问题 2：family_size >= 2 判 "sufficient"

```python
history_status = "sufficient" if family_size >= 2 else "insufficient"
```

**2 个成员就算"历史充分"**。家族统计至少需要 5+ 成员才有意义——2 个成员的 p90 相关根本是退化的（要么是两个数里的 max，要么插值）。

当前 registry 里大多数 family 的成员数是 1 或 2（Q8.2 发现），这个门槛让几乎所有 family 都被判"sufficient"。

### 核心问题 3：residual_survival_ratio 命名撒谎

```python
residual_ratio = float(1.0 - max(abs_corrs))
```

**名字是 "residual survival ratio"**（残差生存率），**实际是 `1 - max_corr`**。

真正的 residual survival ratio 应当是：
- 对 candidate 做 candidate ~ family_basis 的回归
- 取 residual
- 计算 residual 的 IC 或 variance 占原 signal 的比例
- 结果应该接近 Layer 3 subspace 做的事

**当前实现只是 `1 - max_corr` 的变形**——命名暗示的语义和代码实现完全不同。属于 Q21 Pattern B。

### 可行方案

**方案 A（立即，删死权重）**：
- 既然 `struct_overlap` 永远是 0，**删掉它**
- 把公式改成 `score = 0.70 * corr_p90 + 0.30 * (1 - max_corr)`
- 或者干脆**删掉整个 Layer 2** —— 它的信息量等同于 Layer 1 的子集
- 代价：几行代码删除

**方案 B（修 schema drift）**：
- 决定哪一边是 truth：要么改 candidate_meta 和 family YAML 加 3 个字段，要么改 family.py 用现有字段
- 如果要保留 structure check，至少要定义：
  - `structure_template`：表达式 AST 结构签名（比如 "Mul(CsRank(X), CsRank(Y))"）
  - `conditioning_type`：用什么做 conditioner（rank/zscore/industry-neutral/...）
  - `horizon_bucket`：主 horizon 分桶（fast/medium/slow）
- 在 idea 阶段让 LLM 或代码自动填这 3 个字段
- 代价：中等（~200 行跨多文件改动）

**方案 C（重新定义 Layer 2）**：
- 让 Layer 2 做它原本应该做的事：**family-level subspace regression**
- 对 family 内所有 member 堆成 basis matrix，对 candidate 做一次 regression
- 残差的 IC 就是"相对家族的 incremental IC"
- 这和 Layer 3 的 subspace 语义相似但 scope 更窄（family 内）
- 代价：中（~100 行），但这是"真 Layer 2"

**方案 D（归并，推荐）**：
- 承认 Layer 1 + Layer 3 已经覆盖 Layer 2 的所有意图
- Layer 1 抓 "vs 单个 factor 的相关度"
- Layer 3 抓 "vs library 子空间的残差 IC"
- **Layer 2 干脆合并进 Layer 3**：让 subspace 在选 basis 时优先选同 family，family_size >= 3 时就是"family subspace"
- 删除 `family.py` 文件
- 代价：小（~50 行删除 + subspace 的 basis 选择逻辑略改）

### 优先级

**方案 A + D 立即做**（几小时工作量，删除无用代码）。方案 B 和 C 是"如果想真的做 family-level 分析就这么做"的选项，工作量大。

### 关联观察

- **Q22 是 Q21 Pattern A + B 的集中体现**：Pattern A（半成品——有人写了 structure_template 字段但没在数据层实现）+ Pattern B（命名撒谎——`residual_survival_ratio` 不是残差生存率）
- **Q22 也属于 Q20 家族**：hardcoded 权重 `0.5 / 0.3 / 0.2` 散落在 family.py 里，没在 Q20 原清单里，但同样是"改权重要改代码"的问题
- **修复的意外收益**：删除 Layer 2 让 Stage D 的 Python for-loop 数量减少 33%（3 层里 2 层的循环）
- **最严重的 meta 教训**：Layer 2 从**第一次**被计算就产出错误数据，但 100+ batch 里没有任何警报——因为没人 grep 验证 `candidate_meta` 是否有那 3 个字段。**这是 "半成品优化" 最危险的形式**：代码运行不报错、指标输出数字、但数字是假的

---

## Q23 — Risk Review 的失败静默 + 3 个 Barra exposures 实现问题

**入档时间**: 2026-04-11
**相关阶段**: Phase 2 Stage D Step 9 Risk Review

### 问题 23.1：RiskReview.stub() 默认 `risk_model_review_bucket="acceptable"`（**permissive failure**）

`schema.py:41-54`：

```python
@classmethod
def stub(cls) -> RiskReview:
    return cls(
        raw_view_ic=None,
        cap_industry_neutral_ic=None,
        barra_residual_ic=None,
        ...
        risk_model_review_bucket="acceptable",  # ← 这里
    )
```

`engine.py` 在**多处**调用 `RiskReview.stub()` 作为失败 fallback：
- `factor_flat.empty` → stub
- `returns_flat.empty` → stub
- `style_matrix is None or empty` → 部分 stub（仅 raw IC）

**问题**：stub 的 bucket 默认是 `"acceptable"`——意思是"风险评审通过"。

**后果**：
- 因子数据异常 → risk engine 算不出 → 返回 stub
- stub 被 judge 读到 → 看到 `risk_model_review_bucket="acceptable"` 
- judge 以为"风险 OK"，可能走向 admit
- **一个本应被标 poor 的因子因为计算失败被静默放过**

这是一个典型的 **permissive silent failure**——失败默认通过比失败默认拒绝更危险。

**正确行为**：stub 应该返回 `bucket="unknown"` 或 `"poor"`，让 judge 看到"没有风险数据 → 保守拒绝"。

**修复**：
```python
@classmethod
def stub(cls) -> RiskReview:
    return cls(
        ...
        risk_model_review_bucket="unknown",  # 或 "poor"
    )
```

同步在 `candidate_judge.py` 里处理 `unknown` bucket → 降级到 reserve 或要求 retry。

**优先级**：P0。这是**可以立即改的几行代码**，直接修复一条 silent failure 路径。

### 问题 23.2：`style_exposures = mean(|beta|)` 丢失方向信息

`exposures.py:115-119`：

```python
beta_arr = np.array(betas_per_date)  # (n_dates, n_styles)
style_exposures = {}
for i, name in enumerate(style_cols):
    style_exposures[name] = float(np.mean(np.abs(beta_arr[:, i])))
```

**每天算一次 beta，然后取绝对值的跨天平均**。这丢掉了两个重要信息：

1. **方向一致性**：一个因子对 `str_1m` 的 beta 如果**每天都是 +0.1**，和**一半 +0.2 一半 -0.2**，在当前实现里：
   - 情况 A: `mean(|+0.1, +0.1, ...|) = 0.1`
   - 情况 B: `mean(|+0.2, -0.2, +0.2, -0.2, ...|) = 0.2`
   - 情况 B 的 "exposure" 看起来更大，但实际上它的 style 影响**互相抵消**，平均来看是 0
   - 真正稳定暴露于 str_1m 的是情况 A

2. **平均方向 vs 稳定性**：无法判断因子是"**持续正向 expose**"还是"**抖动的 expose**"

**更合理的做法**：同时报告两个：
```python
style_exposures_signed = {name: mean(beta_arr[:, i])}
style_exposures_abs = {name: mean(|beta_arr[:, i]|)}
style_exposure_stability = {name: 1 - (std / |mean|)}  # CV 的倒数
```

judge 可以看到：
- `signed = 0.15, abs = 0.15` → 稳定暴露（危险）
- `signed = 0.02, abs = 0.15` → 抖动暴露（可能没关系）

**优先级**：P1。~30 行代码，收益是 Barra 分析能精细区分"真正暴露"和"抖动"。

### 问题 23.3：OLS 对极端值敏感（不使用 robust regression）

`exposures.py:94`：

```python
beta, _, _, _ = np.linalg.lstsq(X, y_v, rcond=None)
```

普通最小二乘法对极端值敏感。金融数据截面分布是**重尾**的，极少数股票的极端 factor value 会显著影响 beta，导致 residual 不稳定，最终影响 `barra_residual_ic`。

**preprocess 已经做了 3σ winsorize**（Q14），但对 Barra regression 来说可能仍然不够——winsorize 保留了 3σ 内的值，但截面分布还是有重尾。

**更 robust 的做法**：
- Huber regression（`scipy.stats.huber`）
- 或者对 y 做更紧的 clipping（比如 2σ）再做 OLS
- 或者用 Theil-Sen estimator

**代价评估**：Huber 比 OLS 慢 2-3 倍。因为 Barra 回归已经是 Stage D 最慢的步骤（Python for loop），再慢 3 倍不可接受——**但批量化之后（方案见下）**，总时间还是会比当前串行 OLS 快。

**优先级**：P2。修复后影响 `barra_residual_ic` 的稳定性，间接影响 `alpha_survival_ratio`。

### 问题 23.4：Barra 回归是 Python for-loop，整个 Stage D 最慢

`exposures.py:65-110`：

```python
for date in common_dates:
    ...
    beta, _, _, _ = np.linalg.lstsq(X, y_v, rcond=None)
    resid = y_v - X @ beta
    r2 = ...
    betas_per_date.append(beta[1:])
    r2_per_date.append(r2)
    residual_wide.loc[date, syms] = resid
```

**每天独立做一次 OLS**，252 次 Python 循环 per candidate × 6 candidates = **1512 次** Python-level regression。

这是 Stage D（可能也是整个 Phase 2）里**最慢的单步**，估计 ~20 秒 per candidate。

**批量化方法**：
```python
# 把所有 date × instrument 的 y 和 X 堆成 3D tensor
y_3d = fv_wide.loc[common_dates, common_syms].values  # (n_dates, n_syms)
X_3d = style_matrix.loc[common_dates, common_syms, :].values  # (n_dates, n_syms, n_styles)

# 批量 solve: 对每个 date 的 (X^T X)⁻¹ X^T y
# 用 einsum 或 batch matmul
XTX = np.einsum('dij,dik->djk', X_3d, X_3d)  # (n_dates, n_styles, n_styles)
XTy = np.einsum('dij,di->dj', X_3d, y_3d)     # (n_dates, n_styles)
beta_3d = np.linalg.solve(XTX, XTy)           # (n_dates, n_styles)

# 批量算 residual
y_hat_3d = np.einsum('dij,dj->di', X_3d, beta_3d)
residual_3d = y_3d - y_hat_3d
```

**性能提升**：~20 秒 → ~2 秒 per candidate。Stage D 整体时间 **减少 60-70%**。

**需要小心处理的 edge case**：
- NaN mask 要对齐（每天不同股票有效）
- `min_obs` 过滤要向量化做
- 奇异矩阵的 fallback（`np.linalg.solve` 会抛异常，需要 pinv fallback）

**优先级**：P1 性能优化。这个修复的 ROI 极高——~200 行代码改动，Stage D 整体提速 60%+。

### 关联观察

- **23.1 permissive failure** 是 Q21 之外的一种新 meta pattern：**失败默认通过**。这在安全关键系统里是反模式。整个 quant 系统里可能还有其他 stub 或 fallback 也用了相同模式，值得系统扫描
- **23.2 style_exposures 绝对值** 属于 Q21 Pattern B（命名撒谎）的一种变体：字段名是 `style_exposures`，消费者会以为是"对某 style 的暴露程度"——但绝对值平均不是标准意义的 exposure
- **23.3 + 23.4** 和 Q19 里的"Python for-loop + 不 robust"是同一家族——需要**一次性批量化 + 统计鲁棒性**的改造
- **修复 23.4 是整个 Stage D 性能优化的最大收益点**：Barra 回归是唯一真正的计算瓶颈，修完后 Stage D 从 ~30 秒 per candidate 降到 ~10 秒

### 补充 23.5（2026-04-11）：Raw IC 在 Stage C 和 Stage D 被独立算两次，跨 horizon 时可能不一致

这是走流程时发现的具体 silent bug 的**一个具体表现**，属于 Q18 补充里 "horizon 双真相来源" 的下游后果。

#### 问题描述

Risk Review 的 "Raw IC" 视角（`raw_view_ic`）在语义上**等于** Stage C Effect Strength 的 `ic_mean_validation`——两者都是：
> "预处理后 factor_wide 在 validation 期的日度横截面 IC 均值"

但代码里它们**各自独立计算**：

**Stage C**（`compute_implementations.py:282, 307`）：
```python
returns_flat = self._shared.returns_flat.get((full_start, full_end, 5))  # ← 硬编码 5
...
ic_val_stats = ic_summary(daily_cross_sectional_ic(factor_val, returns_val))
```

**Stage D**（`risk/engine.py:78, 97`）：
```python
horizon = profile.get("holding_horizon", 5)   # ← 读 profile
...
returns_flat = self._get_returns_flat(val_start, val_end, horizon)
raw_ic_series = daily_cross_sectional_ic(factor_flat, returns_flat)
raw_view_ic = raw_ic_stats.get("ic_mean", np.nan)
```

#### 两种失败模式

**模式 1：正常情况**（horizon 都是 5）
- Stage C 和 Stage D 的 Raw IC 数值**相等**
- 但**被独立计算两次**，浪费 ~500ms per candidate
- **冗余但不影响正确性**

**模式 2：改了 `profile.holding_horizon`** 到非 5（比如 20）
- Stage C 的 `ic_mean_validation` 仍然是 h=5（硬编码）
- Stage D 的 `raw_view_ic` 变成 h=20（跟 profile）
- **两个数字数值不同，但都号称是 "Raw IC"**
- `alpha_survival_ratio = |barra_residual_ic(h=20)| / |raw_view_ic(h=20)|` —— 内部一致
- 但 judge 同时看到 Stage C 的 `ic_mean_validation(h=5)` 和 Stage D 的 `raw_view_ic(h=20)`，**会对因子"有多强"产生困惑**

#### 架构层面的修复

在新架构下（SharedDerivations），Raw IC 应该**只算一次**：

```python
# Layer 2b Shared Derivations
derivations.ic_series_by_h = {
    h: compute_ic_series_from_wide(factor_wide_clean, returns_wide_by_h[h])
    for h in horizons
}

# Stage C Effect Strength：消费 derivations
effect_result = compute_effect_strength(derivations)

# Stage D Risk Review：也消费 derivations（不重算！）
def compute_risk_review(derivations, market_cap_wide, style_matrix):
    # 视角 1: Raw IC 从 shared 拿 —— 共享 ic_series
    raw_view_ic = derivations.ic_series_by_h[primary_h].mean()
    
    # 视角 2/3: cap-neutral / barra residual 是新 factor，必须新算 IC
    factor_cap_neutral = neutralize_cap(derivations.factor_wide, market_cap_wide)
    cap_neutral_ic = compute_ic_series_from_wide(factor_cap_neutral, returns_wide).mean()
    
    factor_barra_residual = regress_out_styles(derivations.factor_wide, style_matrix)
    barra_residual_ic = compute_ic_series_from_wide(factor_barra_residual, returns_wide).mean()
    
    alpha_survival_ratio = abs(barra_residual_ic) / abs(raw_view_ic)
```

#### 哪些可共享 / 哪些必须重算

| 操作 | 是否重算 | 理由 |
|---|---|---|
| `factor_wide` pivot | ❌ 共享（1 次）| 同一个预处理后因子 |
| Raw IC (`ic_series`) | ❌ 共享（1 次）| Stage C 和 Stage D 语义相同 |
| Cap-neutral regression | ✅ 重算（1 次）| 新 factor（cap 残差）|
| Cap-neutral IC | ✅ 重算（1 次）| 新 factor 需要新 IC |
| Barra style regression | ✅ 重算（1 次）| 新 factor（Barra 残差）|
| Barra residual IC | ✅ 重算（1 次）| 新 factor 需要新 IC |

**不可避免的新计算**是 2 次新 regression + 2 次新 IC（cap 和 barra）。这是**Risk Review 的本质工作**——用新的正交化信号看 IC 还剩多少。

**可共享的部分**是 Raw IC + factor_wide pivot。这是**当前被浪费的部分**。

#### 节省估算（per candidate）

- Raw IC 重算：~500ms
- Pivot 重复：~1500ms (3 次多余 × 500ms)
- Flat/stack 来回转换：~800ms

合计 per candidate 节省 ~2.8 秒。batch 级别 ~17 秒。

**但 Q23.4 的 Barra 批量化节省 ~15 秒 per candidate**，比这个大得多。两个修复叠加后，Stage D 时间从 ~30 秒 per candidate 降到 ~10 秒左右。

#### 优先级

P1。和 Q19 方案 A（接通 clean subpackage）+ Q18 双真相修复一起做最经济——这三个问题**共享同一个根因**：缺少 `SharedDerivations` 层作为计算中间结果的单一真相。

如果只修这一个而不修前两个，意义有限（你省了 Raw IC 重算，但 Stage C 的 stability/reliability 仍然是假数据）。**这 3 个应当作为一个整体修复单元**。

---

## Q24 — Stage D 完整发现汇总：Layer 2 无效 + 多处性能/命名问题

**入档时间**: 2026-04-11
**相关阶段**: Phase 2 Stage D 总结

这个 Q 不是独立的新 bug，是 Stage D 走流程时所有小发现的**集中索引**——便于后续修复时不漏掉。

### 发现清单（按严重性）

**🔴 P0**
- D1.4 **Layer 2 schema drift 死代码**（→ Q22）
- D2.4 **RiskReview.stub() permissive failure**（→ Q23.1）

**🟠 P1**
- D2.1 Barra 回归 Python for-loop 是 Stage D 最慢瓶颈（→ Q23.4，批量化 ROI 最高）
- D2.2 style_exposures 用绝对值丢失方向信息（→ Q23.2）

**🟡 P2**
- D1.1 pairwise Python for-loop（可向量化）
- D1.2 pairwise min_obs=5 和主 IC min_obs=30 不一致
- D1.5 residual_survival_ratio 命名撒谎（→ Q21 Pattern B 案例）
- D1.6 family_size >= 2 判 "sufficient" 过低
- D1.7 subspace Python for-loop
- D1.8 subspace alpha=1.0 硬编码不随样本规模调整
- D2.3 OLS 不 robust（→ Q23.3）
- D2.6 `_compute_cap_neutral_ic` 重复 pivot/stack 转换
- Layer 2 的 `0.5/0.3/0.2` 权重硬编码（Q20 补充）

**🟢 P3**
- D1.3 pairwise threshold docstring 矛盾（0.7 vs 0.9）
- D1.9 subspace confidence 的 120/250/2/5/6 魔数
- D1.10 basis colinearity 未检查

### Stage D 的真实计算图

修正了 Q22 + Q23 发现后，Stage D 的**有效信息来源**是：

| Step | 真实输出 | 有效性 |
|---|---|---|
| **Layer 1 pairwise** | `max_lib_corr`, `nearest_factor_id`, `all_correlations` | ✅ 真实 |
| Layer 2 family | 30% struct_overlap 死代码，剩余 = Layer 1 的变形 | **❌ 冗余** |
| Layer 3 subspace | `subspace_redundancy_score`, `residual_incremental_ic` | ✅ 真实但慢 |
| Raw IC | `raw_view_ic` | ✅ 真实 |
| Cap-neutral IC | `cap_industry_neutral_ic`（命名撒谎）| ⚠️ 真实计算但字段名骗人 |
| Barra residual IC | `barra_residual_ic`, `alpha_survival_ratio` | ✅ 真实但最慢 |
| Style exposures | `style_exposures = mean(|beta|)` | ⚠️ 丢失方向 |
| Crowding risk | `style_crowding_risk`（基于 r² + exposures）| ✅ 真实 |
| Risk bucket | `risk_model_review_bucket` | ⚠️ stub 失败时默认 acceptable |

**真实可用的信号**：Layer 1 + Layer 3 + Raw IC + Barra residual IC + Crowding
**噪声/冗余**：Layer 2 完全、Cap-neutral（命名骗人）、style_exposures（丢方向）

### 修复后的 Stage D 最小改动清单

按 ROI 排序：

1. **删 Layer 2**（方案 D of Q22）——几小时，几十行代码
2. **RiskReview.stub 默认 "unknown"**（Q23.1）——5 行代码
3. **Barra 回归批量化**（Q23.4）——~200 行，Stage D 提速 60%
4. **style_exposures 报告 signed + abs**（Q23.2）——~30 行
5. **对齐 pairwise min_obs 与主 IC**（D1.2）——1 行
6. **修 `cap_industry_neutral_ic` 字段名**（Q17）——重命名 + 一次性字段迁移

前 3 个做完，Stage D 的正确性 + 性能就能显著改善。

---

## Q25 — 统一推导层架构：**所有**因子变形和 IC 序列都应当是 first-class 共享工件

**入档时间**: 2026-04-11
**相关阶段**: 整个 Phase 2 / 架构愿景
**性质**: 这是 Q19 方案 A + Q23.5 的**升级版**——更激进的共享原则。

### 用户原话指出的核心原则

> "在我们的新逻辑里面，**所有的值不应该重复计算**，因为会存在不一致的问题。我们必须保证数据的一致性 + 加速计算 + 避免重复计算。"

### 我之前的错误

在 Q23.5 里，我区分了"可共享"和"不可共享"：
- Raw IC → 可共享（Stage C 和 Stage D 相同）
- Cap-neutral IC → 不可共享（factor 变了）
- Barra residual IC → 不可共享（factor 变了）

**这个区分是错的**。正确的区分是"**值的来源**"而不是"值的**语义**"。

- `ic_series_raw` 是从 `factor_wide_clean + returns_wide` 推导出来
- `ic_series_cap_neutral` 是从 `factor_wide_cap_neutral + returns_wide` 推导出来
- `factor_wide_cap_neutral` 是从 `factor_wide_clean + market_cap_wide` 推导出来

**每一个都是从更上游的共享数据推导出来的**。它们都可以——也应该——放在共享推导层里，算一次，N 个分析消费。

我把"首次生成"和"必须局部计算"搞混了。

### 正确的架构原则

**任何从 `(factor_wide, aux_data)` 推导出来的值都是 first-class 共享工件**。具体规则：

1. **Layer 2 (Per-Candidate Derivations)** 必须包含**所有**可被多个分析消费的推导
2. **Layer 3 (Analyses)** **只做 3 件事**：
   - 从 derivations 读取
   - 做 bucket classification / threshold 比较
   - 做纯派生算数（除法、比值、slicing）
3. **Layer 3 永远不产生新的 factor_wide、不产生新的 ic_series、不做 regression**

**核心不变量**：整个 pipeline 里，每一个数值**只被算一次**。物理上不可能出现"两个字段号称同一个概念但数值不同"的情况。

### 具体的推导层设计

```python
@dataclass
class CandidateDerivations:
    """一个 candidate 在 execute 阶段的所有共享推导。
    
    Layer 2 一次性算完，Layer 3 只读不写。
    """
    
    # ==== 2a: Preprocessed factor ====
    factor_wide_clean: pd.DataFrame  # (datetime × instrument), 已 winsorize + zscore + tier1 mask
    
    # ==== 2b: Factor transformations ====
    factor_wide_cap_neutral: pd.DataFrame       # neutralize_cap(factor_wide_clean, market_cap_wide)
    factor_wide_barra_residual: pd.DataFrame    # regress_out_styles(factor_wide_clean, style_matrix)
    # 可扩展: factor_wide_industry_neutral (Q17 未来)
    
    # ==== 2c: Barra regression byproducts ====
    barra_betas_by_date: pd.DataFrame           # (dates × 7 styles) 
    barra_r2_by_date: pd.Series                 # (dates,)
    style_exposures_signed: Dict[str, float]    # 7 个 style 的 mean(beta)
    style_exposures_abs: Dict[str, float]       # 7 个 style 的 mean(|beta|)
    style_exposure_stability: Dict[str, float]  # |mean| / std，越高越稳定
    style_r_squared_median: float
    
    # ==== 2d: IC Series Derivations ====
    # 每种 factor variant × 每个 horizon 一份 ic 序列
    ic_series_raw_by_h: Dict[int, pd.Series]            # {1: ic_series, 5: ic_series, ...}
    ic_series_cap_neutral_by_h: Dict[int, pd.Series]
    ic_series_barra_residual_by_h: Dict[int, pd.Series]
    
    # ==== 2e: Quintile Derivations ====
    quintile_daily_ls_raw_by_h: Dict[int, pd.Series]
    # cap-neutral / barra-residual 的 quintile 通常不需要，因为 LS t-stat 是 raw 语义
    
    # ==== 2f: 元数据 ====
    primary_horizon: int          # 当前 logic 声明的主 horizon（Q18）
    secondary_horizons: List[int] # 辅助 horizons（Q18）
    validation_date_range: Tuple[str, str]
```

### Risk Review 变成纯消费者

```python
def compute_risk_review(d: CandidateDerivations) -> RiskReview:
    """Risk Review 作为纯 consumer——零新计算，零 pivot，零 regression"""
    
    h = d.primary_horizon
    
    # 视角 1: Raw IC —— 直接读
    raw_view_ic = d.ic_series_raw_by_h[h].mean()
    
    # 视角 2: Cap-neutral IC —— 直接读
    cap_neutral_ic = d.ic_series_cap_neutral_by_h[h].mean()
    
    # 视角 3: Barra residual IC —— 直接读
    barra_ic_series = d.ic_series_barra_residual_by_h[h]
    barra_residual_ic = barra_ic_series.mean()
    barra_residual_icir = barra_residual_ic / barra_ic_series.std() if barra_ic_series.std() > 0 else 0
    
    # 视角 4: Alpha survival —— 纯算数
    alpha_survival = abs(barra_residual_ic) / abs(raw_view_ic) if abs(raw_view_ic) > SURVIVAL_RAW_IC_MIN else None
    
    # Style exposures —— 直接读
    dominant_style = max(d.style_exposures_signed, key=lambda k: abs(d.style_exposures_signed[k]))
    
    # Crowding —— 纯 classification
    crowding = classify_crowding(d.style_r_squared_median, d.style_exposures_abs)
    
    # Bucket —— 纯 classification
    bucket = compute_risk_bucket(alpha_survival, crowding)
    
    return RiskReview(
        raw_view_ic=raw_view_ic,
        cap_neutral_ic=cap_neutral_ic,
        barra_residual_ic=barra_residual_ic,
        barra_residual_icir=barra_residual_icir,
        alpha_survival_ratio=alpha_survival,
        style_exposures_signed=d.style_exposures_signed,
        style_exposures_abs=d.style_exposures_abs,
        style_r_squared=d.style_r_squared_median,
        dominant_style_exposure=dominant_style,
        style_crowding_risk=crowding,
        risk_model_review_bucket=bucket,
    )
```

**这个函数里没有一个 `daily_cross_sectional_ic`、`pivot`、`regress_out_*` 调用**。全是读 + 判断 + 算数。

### 所有 Layer 3 分析都应该长这样

Effect Strength:
```python
def compute_effect_strength(d: CandidateDerivations) -> EffectStrength:
    h = d.primary_horizon
    ic_series = d.ic_series_raw_by_h[h]   # 直接读
    return EffectStrength(
        ic_mean_validation=ic_series.mean(),
        ic_ir_validation=ic_series.mean() / ic_series.std(),
        ...
    )
```

Stability:
```python
def compute_stability(d: CandidateDerivations) -> Stability:
    h = d.primary_horizon
    ic_series = d.ic_series_raw_by_h[h]   # 直接读
    # 切 4 段
    splits = np.array_split(ic_series, 4)
    ...
```

Reliability:
```python
def compute_reliability(d: CandidateDerivations) -> Reliability:
    ic_series = d.ic_series_raw_by_h[d.primary_horizon]  # 直接读
    # Block bootstrap on ic_series
    bootstrap_ics = block_bootstrap(ic_series, block_size=d.primary_horizon, n=500)
    ...
```

### 数据一致性的 4 个硬保证

**保证 1：Raw IC 只有一个数字**
- `d.ic_series_raw_by_h[h].mean()` 是单一表达式
- Effect Strength 和 Risk Review 都取这个值
- 物理上不可能不等

**保证 2：alpha_survival_ratio 分子分母同 horizon**
- 都是 `d.ic_series_*_by_h[d.primary_horizon]`
- 单一 horizon 变量，不可能跨 horizon

**保证 3：所有 factor variant 共享同一个 clean 源**
- `factor_wide_cap_neutral` 和 `factor_wide_barra_residual` 都从 `factor_wide_clean` 推导
- 完全相同的 NaN 模式、完全相同的 index

**保证 4：跨分析的数据对齐**
- Redundancy pairwise 和 Risk Review 都从 `d.factor_wide_clean` 读
- 不会出现"pairwise 用了 dropna 后的版本，risk 用了原版"这种错位

### 不可避免的"新计算"——真正局部的东西

**经过重新审视，只有 2 类计算必须保留在分析层**：

1. **Bucket / classification 逻辑**：每个分析把数值映射到 label（"strong / borderline / weak"）。这是**分析自己的概念**，不是共享的数据。
2. **窗口切片**：Support Windows 在 2020-2021 等**不同时间范围**上重新算 IC；Expanding Window 在 0-20%, 0-40% 等**不同子窗口**上算 IC。
   - 但即使是这个，也可以预计算到 Layer 2：`ic_series_raw_by_window = {window_id: ic_series}`
   - 如果把它放到 Layer 2，分析层连窗口切片都不用做——只是从 dict 取
   - 这取决于你要不要把 Layer 2 做得更重

**其他所有"感觉像新计算"的东西**（比如 bootstrap、regression、neutralize）**都属于 Layer 2 的推导**，不是 Layer 3 的计算。

### 性能和一致性收益

**一致性**（最重要）：
- Raw IC 在 Stage C 和 Stage D 物理上同一个数字
- alpha_survival_ratio 分子分母必然同 horizon
- 跨分析的 factor_wide 是同一个对象
- 修改 Layer 2 的逻辑会**原子地**影响所有消费者——不会出现"Stage C 和 Stage D 各看各的"

**性能**：
- Raw IC 重算省 ~500ms
- 多余 pivot 省 ~2000ms
- flat ↔ stack 转换省 ~1500ms
- Barra 批量化（Q23.4）省 ~15000ms
- **合计 ~19 秒 per candidate × 6 = ~114 秒 per batch**

Stage D 从 ~30 秒 per candidate 降到 ~10 秒，batch 总时间从 ~5 分钟降到 ~2 分钟（也结合 Q12 的 Qlib 批量修复）。

### 修复路径依赖

Q25 的实现**必须**作为一个整体 refactor，不能零散做。理由：

- 单独做 "接通 clean stats/" (Q19 方案 A) 但不做 Layer 2 derivations → stability 仍然自己算 IC，浪费了 Q19 接通的好处
- 单独做 "Barra 批量化" (Q23.4) 但不做 Layer 2 → barra_residual 是批量算了，但 Risk Review 还是自己走 pivot/stack 消费它
- 单独做 "horizon 双真相修复" (Q18 补充) 但不做 Layer 2 → Stage C 和 Stage D 仍然各自读 config，只是 config 来源统一了——一致性不是强制的

**正确做法**：一个 refactor unit，同时涵盖
1. 建立 `CandidateDerivations` 数据契约
2. Layer 2 实现（包含所有当前分散在各处的推导）
3. Layer 3 改写为纯 consumer（所有分析接通 derivations）
4. 批量化 Barra regression（作为 Layer 2c 的一部分）
5. 接通 clean `stats/` 和 `feasibility/` subpackage（作为 Layer 3 的消费者实现）
6. 删除 inline 版本（避免 dual implementation）

**代价**：~1-2 周集中开发。
**收益**：Q18 / Q19 / Q20 / Q22 / Q23 / Q24 的大部分症状**一次性消失**。

### 这是 Q11 的一个必要基础设施

Q11（自主探索循环）的 meta-reflect 层要做"系统对自己的观察"——但如果底层数据本身有不一致性（Raw IC 有两个版本、horizon 不一致、假数据占位），meta-reflect 看到的"系统行为"本身就是噪声。

**Q25 的推导层是 Q11 的前提**。先有"数据一致 + 无重复计算"的基础，才谈得上"元认知反思"。

### 关联观察

- **Q25 取代 Q23.5 的有限范围**：Q23.5 原本只讨论"共享 Raw IC"，Q25 扩展到"所有推导都共享"
- **Q25 的原则是 Q21 Pattern A 的反面**：Q21 Pattern A 讲"半成品优化"，Q25 讲"全成品共享层"。半成品的典型症状是"有人算了但只给自己用"——Q25 的原则是"算了就是全系统的资产，必须在共享层"
- **Q25 + Q11 合起来**描述系统的**最终理想状态**：Q25 让底层数据一致，Q11 让上层决策能基于一致数据做元认知反思
- **一个有趣的副作用**：Q25 的架构让所有"假数据硬编码"立刻 visible——因为共享层必须真实产出 `ic_series_barra_residual`，不能再用 `None` 占位。任何未实现的推导会在 Layer 2 构造时立即报错，而不是 Layer 3 静默读到 None

---

## Q26 — Stage E Judge Packet 构建里 4 个 silent bug：Stage C/D 真实数据在这一步被"静默消音"

**入档时间**: 2026-04-11
**相关阶段**: Phase 2 Stage E Step 11 ExecutionGate + Step 12 JudgePacketBuilder

### 背景

Stage E 的 `JudgePacketBuilder` 和 `ExecutionGate` 是"**压缩 + 分类**"层——从 Stage B-D 产出的详细数据里提取 judge 需要的字段和 bucket 分类。理论上应该是一层薄的 adapter。

走流程时发现 **4 个 silent bug**：consumer 读的 field name 和 value vocabulary 与 producer 写的不一致，**不会报错**，但**静默吞掉数据**。

### Bug F1：ExecutionGate 检查 `split_stability == "low"` —— 永远不可能触发

`execution_gate.py:120-122`：
```python
split_stability = evaluation.get("split_stability")
if split_stability == "low":
    reasons.append("poor_split_stability")
```

**Producer**（`compute_implementations.py:706-710` 的 `_classify_stability`）：
```python
def _classify_stability(decay_ratio):
    if decay_ratio >= 0.7:   return "good"
    elif decay_ratio >= 0.4: return "medium"
    return "poor"
```

**Vocabulary mismatch**：producer 词汇表是 `{good, medium, poor}`，consumer 检查 `"low"`——两者**没有交集**。

**后果**：`poor_split_stability` reason code **从来没被触发过**。ExecutionGate 的 stability 检查**等于不存在**。

### Bug F2：`_stability_bucket` 的 "good" 返回值永远不可达

`judge_packet_builder.py:37-47`：
```python
def _stability_bucket(evaluation):
    split = evaluation.get("split_stability", "medium")
    regime = evaluation.get("regime_stability", "medium")
    ew_pass = evaluation.get("expanding_window_pass", True)

    if split == "high" and regime == "high" and ew_pass:
        return "good"
    if split == "low" or regime == "low" or not ew_pass:
        return "poor"
    return "medium"
```

**3 个 mismatch 叠在一起**：
1. 检查 `split == "high"` — `split_stability` 永远是 "good/medium/poor"，**不可能是 "high"**
2. 检查 `regime == "high"` — `regime_stability` 硬编码 "medium"（Q19 已记录），**不可能是 "high"**
3. 检查 `split == "low"` / `regime == "low"` — 同上，永远 False

**结果**：`_stability_bucket` **只能返回 "medium" 或 "poor"**（取决于 `expanding_window_pass`），**永远不可能返回 "good"**。

**后果**：judge packet 里**所有因子**的 `stability_bucket` 要么是 "medium" 要么是 "poor"——**没有任何一个因子能在这一维得 "good"**，不管它实际表现多好。

### Bug F3：`_redundancy_bucket` 的 family_bucket 永远是 "low"

`judge_packet_builder.py:50-61`：
```python
def _redundancy_bucket(similarity):
    max_corr = abs(similarity.get("max_lib_corr", 0) or 0)
    family_bucket = similarity.get("family_redundancy_view", {}).get(
        "family_overlap_bucket", "low"
    )
    if max_corr >= 0.85 or family_bucket == "high":
        return "high"
    if max_corr >= 0.60 or family_bucket == "medium":
        return "medium"
    return "low"
```

**Consumer 读 `similarity["family_redundancy_view"]["family_overlap_bucket"]`**。

**Producer**（`compute_implementations.py:437-451` 的 `compute_redundancy` 返回值）：
```python
return {
    "max_lib_corr": pw.get("max_lib_corr", 0.0),
    "nearest_factor_id": pw.get("nearest_factor_id"),
    "is_near_duplicate": pw.get("is_near_duplicate", False),
    "family_overlap_score": fv.get("family_overlap_score") or 0.0,    # ← 扁平字段
    "subspace_redundancy_score": sv.get("subspace_redundancy_score") or 0.0,
    ...
}
```

**没有 `family_redundancy_view` 这个 key**——family_overlap_score 是**扁平**放在 similarity dict 里的。

**后果**：
- `similarity.get("family_redundancy_view", {})` → `{}`
- `.get("family_overlap_bucket", "low")` → **"low"**
- `family_bucket == "high"` 和 `== "medium"` **永远 False**

判定退化为只看 pairwise max_corr：
```python
if max_corr >= 0.85: return "high"
if max_corr >= 0.60: return "medium"
return "low"
```

**judge 看到的 redundancy_bucket 完全不看 family overlap**。

这是 **Q22（Layer 2 schema drift 死代码）在 Stage E 的延伸**——Layer 2 就算有产出，**consumer 也读不到**。Layer 2 是两层死：producer 端 30% 权重死代码（Q22），consumer 端字段名读错（F3）。

### Bug F4：`support_window_review` 字段名和 producer 的 `support_window_checks` 不匹配

`judge_packet_builder.py:107`：
```python
support_review = result.get("support_window_review", {})
...
"support_window_warning": support_review.get("support_window_warning", "none"),
```

Consumer 读 `result["support_window_review"]["support_window_warning"]`。

**Producer**（`compute_implementations.py:361`）：
```python
result = {
    ...
    "support_window_checks": support_checks,   # ← 这个名字，不是 support_window_review
    ...
}
```

**Producer 写 `support_window_checks`（list），Consumer 读 `support_window_review`（dict）**。完全不同。

**后果**：
- `result.get("support_window_review", {})` → `{}`
- `.get("support_window_warning", "none")` → **"none"**
- Judge packet 里每个 candidate 的 `support_window_warning` **永远是 "none"**

同时 packet builder 的 batch 级聚合（`build()` line 181-188）：
```python
warnings = [b.get("support_window_warning", "none") for b in briefs]
if "repeated_sign_flip" in warnings: agg_warning = "repeated_sign_flip"
elif "single_window_flip" in warnings: agg_warning = "single_window_flip"
else: agg_warning = "none"
```

因为所有 brief 都是 "none"，`agg_warning` **永远是 "none"**。

**这是 4 个 bug 里最严重的一个**：
- Stage C 的 Support Windows 维度**是真实计算的**（Q19 确认，config 里有 `val_2020_2021 / val_2021_2022 / val_2022_2023` 三个 support windows）
- **但它的结论到不了 judge**
- judge 看到的 `support_window_warning` 永远 "none"
- **Stage C 花力气算的 support window 数据在 Stage E 的 packet 构建时被静默丢弃**

### 现实影响：解释了 batch_099-103 的一个反常现象

L015 家族反复出现 "validation 通过但 holdout 崩" 的模式。Q18 讲 horizon 偏差 + Q19 讲 stability/reliability 假数据已经给出部分解释。Bug F4 给出**另一个解释**：

**Support Windows 的符号翻转检测在 Stage C 是真实跑的**。如果某个候选在 `val_2020_2021` 上已经 sign flip 了，按设计应该在 judge packet 里升起 `repeated_sign_flip` 警告，judge 就会**强制 holdout review**。

**但因为 F4，这个警告永远是 "none"**。Judge 从来没机会看到 "这个因子在另外两个窗口上已经 sign flip 了"。

**Support Windows 是一个被 Stage E 静默消音的 silent alarm**。

### 4 个 bug 合起来的后果

| 字段 | 应该是 | 实际永远是 |
|---|---|---|
| ExecutionGate 的 `poor_split_stability` reason | 条件触发 | 不可能触发（F1）|
| `stability_bucket` 的 "good" 值 | 条件触发 | 不可能返回（F2）|
| `redundancy_bucket` 里 family 贡献 | 有影响 | 永远是 "low"（F3）|
| `support_window_warning` | 反映 Stage C 计算 | 永远是 "none"（F4）|

**合起来让 Stage C/D 的真实数据在 Stage E 被进一步"静默消音"**：
- 前面 Q19 发现 Stage C 有 40-60% 数据是假的
- **剩下 40-60% 真数据在 Stage E 又有相当一部分被字段名 mismatch 吞掉**

Judge 最终看到的 packet 里，真正带**有意义信号**的字段比预期少得多。

### 为什么这 4 个都会 silent

Python 不会报错，因为：
- `dict.get(key, default)` 对不存在的 key 返回默认值
- 字符串 `==` 对不等比较返回 False
- 嵌套 `.get({}).get(default)` 优雅降级

**所有 4 个 bug 都是 "静默默认 + vocabulary mismatch"**。没有测试能自动发现（除非测试**明确检查** "应该是 good 的因子是否被标为 good"）。

这是 Q21 Pattern A（半成品）+ Q21 Pattern B（命名撒谎）的**消费者端**变体。Q19/Q20 讲的是 producer 端的撒谎和半成品，Q26 讲 consumer 端的**读不到**——producer 和 consumer 两端各自漂移了词汇表，互相 silent 地误解对方。

### 可行方案

**方案 A（立即，P0）**：修 4 个字段名 / vocabulary mismatch：

**F1 + F2 修复**：把 `_classify_stability` 的词汇表从 `good/medium/poor` 改成 `high/medium/low`，或者把所有 consumer 的检查改成 `poor`。**整个系统选一个词汇表**。

**F3 修复**：把 `_redundancy_bucket` 改成读扁平字段：
```python
family_score = similarity.get("family_overlap_score", 0.0) or 0.0
family_bucket = "high" if family_score >= 0.7 else "medium" if family_score >= 0.45 else "low"
```

**F4 修复**：把 consumer 读 `result["support_window_checks"]`（producer 的实际字段名），然后从 list 里聚合：
```python
checks = result.get("support_window_checks", [])
signs_not_ok = [c for c in checks if not c.get("sign_consistency_support", True)]
if len(signs_not_ok) >= 2: warning = "repeated_sign_flip"
elif len(signs_not_ok) == 1: warning = "single_window_flip"
else: warning = "none"
```

**代价**：~30 行代码改动，零架构变化。

**方案 B（中期，建立 dataclass 契约）**：把 `result` dict 改成 `CandidateResult` dataclass，字段名在一处定义。任何读写不存在的字段会抛错。

这是 Q21 Pattern B 的通用防御手段——**用类型系统代替字典约定**。代价中等，收益大（所有类似的 F1-F4 bug 会一次消失）。

**方案 C（对齐 Q25）**：在 Q25 的 `CandidateDerivations` 架构里，packet builder 直接从 derivations 读，不经过中间的 dict 转换。derivation 是 dataclass，字段名有编译时保证。

### 优先级

方案 A 立即做——几十行代码，直接修复 4 个 silent bug。**这是一次性恢复 judge 对 Stage C/D 真实数据可见性**的 minimum viable fix。

方案 B 和 C 属于 Q25 整体 refactor 的一部分。

### 关联观察

- **Q26 是 Q21 Pattern B 的 consumer 端表现**：Q21 原本聚焦 producer 端撒谎（字段名和实际计算不符），Q26 发现 consumer 端也会"撒谎"——读一个不存在的字段名，静默默认，看起来一切正常
- **Q26 + Q19 叠加放大**：Stage C 只有 ~40% 维度是真数据，Stage E 又把这 40% 里的相当一部分消音——judge 实际看到的有效信号比想象的**更少**
- **F4 是 Q22 + Q19 之外**的 Support Windows 数据丢失路径：Stage C 算了，Stage E 没传。**三处都修好才算 Support Windows 真正工作**
- **修 Q26 方案 A 是"最小代价最大收益"的修复之一**——30 行代码换回大量被消音的真实数据。应该优先于任何架构层 refactor
- **方法论教训**：**字段契约需要 schema 校验**。当前所有跨层数据传递用 dict，字段名漂移不会报错。这是整个系统质量的结构性缺陷，不只是 Stage E 的问题

### 2026-04-11 修正

走流程对照实际输出时发现 Q26 有两处需要更正：

#### F3 根因修正

原文写"family_redundancy_view 字段不存在，consumer 读默认 low"。**这个描述不准确**。

正确情况：`compute_redundancy`（`compute_implementations.py:445`）确实返回 `family_redundancy_view: fv`。`fv` 的内容取决于 family 是否在 registry：

**Path A（family 在 registry 且有成员）**：返回完整 dict，**包含 `family_overlap_bucket`**
**Path B（family 未知 / degenerate）**：只返回 3 字段 dict，**没有 `family_overlap_bucket`**

F018 实际走 Path B——因为 `PF_fundamental_price_divergence` 不在 `storage/registry/families/`（Q8.2）。于是 `family_redundancy_view = {family_assignment_status: unknown, family_overlap_score: null, family_registry_check: degraded}`，**没有 `family_overlap_bucket` 字段**，consumer `.get("family_overlap_bucket", "low")` 取默认值 `"low"`。

**所以 F3 的症状是对的，但根因是 Q8.2（family registry 缺失）+ Path B 退化**，而不是简单的字段名 mismatch。修 Q8.2 会让 F018 走 Path A，但 Path A 本身仍受 Q22 影响（structure_overlap 永远是 0）。

#### F4 撤回

原文写"`support_window_review` 字段名不匹配，consumer 永远读 'none'"。**这是错的**。

Pipeline 里有一个我之前漏看的 helper（`pipeline.py:369-380`）：

```python
def _compute_support_window_review(evaluation):
    checks = evaluation.get("support_window_checks", [])
    flip_count = sum(1 for c in checks if not c.get("sign_consistency_support", True))
    if flip_count >= 2:   warning = "repeated_sign_flip"
    elif flip_count == 1:  warning = "single_window_flip"
    else:                  warning = "none"
    return {"support_window_warning": warning}
```

这个函数**正确地**从 `evaluation.support_window_checks`（Stage C 写入的 list）聚合出 `support_window_warning`，并在 pipeline.py:131/213 写入 `result["support_window_review"]`。consumer 读到的是真实聚合值。

**F018 的 production 输出 `support_window_warning: none` 是正确结果**——它的 3 个 support windows 全部 `sign_consistency_support: true`，0 flip → "none"。

**F4 应当撤回**。Support Windows 维度在 Stage C + Stage E 都是正确工作的。

### 修正后的 Q26 有效 bug 数

| 原 | 修正后 |
|---|---|
| F1 ExecutionGate split_stability vocabulary mismatch | ✅ 仍然有效 |
| F2 _stability_bucket "good" 分支不可达 | ✅ 仍然有效 |
| F3 _redundancy_bucket family_bucket 永远 "low" | ⚠️ 症状有效，根因是 Q8.2 + Path B 退化 |
| F4 support_window_review 字段不匹配 | ❌ **撤回**——实际正确工作 |

**Q26 有效 bug 从 4 个降到 3 个**。但 F3 暴露了 Q8.2 + Q22 联合作用的一个具体后果路径。

---

## Q28 — 输出文件审计：research_result.yaml 和 judge_packet.yaml 的结构与 Q25 架构严重不对齐，且还有未分析的区域

**入档时间**: 2026-04-11
**相关阶段**: Phase 2 /factor-execute 最终输出 + Q25 架构对比

### 背景

用户问："整个 evaluate 模块最终保存什么文件？内容和我们的 Q25 优化架构对齐吗？还有什么没分析到？"

这个 Q 是对前面所有 Phase 2 findings 的**输出端总结**——具体看磁盘上的真实文件内容，对照 Q25 的 derivation 层架构，找出差异和未分析区域。

### 部分 1：输出文件清单

`batch_runner.py:144-146` 定义了 3 类输出：

```python
self._save_result(batch_id, result)        # research_result.yaml
self._save_artifacts(batch_id, result)     # artifacts/CXXX/signal_flat.parquet + metadata.yaml
self._save_packet(batch_id, result.get("judge_packet", {}))  # judge_packet.yaml
```

**存储位置**：`storage/batches/batch_XXX/`

| 文件 | 大小 | 作用 | 消费者 |
|---|---|---|---|
| `research_result.yaml` | ~1200 行 / 6 candidate | 所有评估细节，per-candidate 完整 dict | `/factor-reflect`（写 belief delta）、`/factor-report`（生成报告）、`/factor-judge`（二级细查）|
| `artifacts/CXXX/signal_flat.parquet` | ~30 MB per candidate | 原始因子信号（Q6 讨论） | `report.builder`（性能优化，缓存命中则跳过重算）|
| `artifacts/CXXX/metadata.yaml` | 几行 | artifact 元数据 | 同上 |
| `judge_packet.yaml` | ~125 行 / 6 candidate | 压缩版 candidate briefs | `/factor-judge`（主输入）|

### 部分 2：research_result.yaml 的结构

每个 candidate 是一个 top-level dict，包含以下子 dict：

| Section | 内容 | 问题 |
|---|---|---|
| `diagnostics` | base_valid_ratio, variance, outlier_ratio, skew, kurtosis | 和 feasibility.coverage 部分重复 |
| `precheck` | status + reason_codes | OK |
| `evaluation` | Stage C 的所有 5 维（真假混合）| Q19：~40-60% 是假 |
| `similarity` | Stage D Redundancy 3 层 | Q22 Layer 2 死代码，family_redundancy_view 对 F018 走 Path B |
| `risk_review` | Stage D Risk 4 视角 + style exposures | Q23：3 个新问题 + Q17 命名撒谎 |
| `feasibility` | 8 字段 | Q24：4 个字段硬编码假 |
| `execution_gate` | pass/warn/fail + reason_codes | Q26 F1：stability 检查永远不触发 |
| `support_window_review` | `{support_window_warning: ...}` | ✅ **真实工作**（Q26 F4 撤回）|
| `holdout_review` | `{recommended, trigger_reason_codes}` | 未分析，`_should_recommend_holdout` 逻辑没读 |
| `search_context` | `{}` | **永远是空 dict**——从没被填充 |
| `direction` | `null` | **永远是 null**——遗留或未实现 |

### 部分 3：judge_packet.yaml 的结构

```yaml
judge_packet:
  batch_id: batch_102
  candidate_briefs:
    - candidate_id / logic_id / route_id / family_id / experiment_lineage_tag
      execution_gate_status
      validation_effect_bucket / stability_bucket / redundancy_bucket
      feasibility_bucket / risk_model_review_bucket
      support_window_warning
      holdout_review_recommended
      holdout_effect_bucket
      holdout_ic_mean / ic_ir / monotonicity / decay_ratio
  logic_ids_in_batch
  search_context: {}
  support_window_review: {support_window_warning: ...}
  sample_policy_version / evaluation_profile_id
```

**关键特征**：只保留 bucket 分类 + 几个关键 holdout 数字。Stage C/D 的**丰富原始数据全部丢失**——judge 看不到 IC 序列、quintile returns、style exposures 的完整列表，只看最终 bucket。

### 部分 4：与 Q25 架构的对齐状况——**严重不对齐**

Q25 的理想架构是"Layer 2 derivations + Layer 3 analyses"两层分离。当前输出**按分析结果组织**（evaluation / similarity / risk_review / feasibility 各一段），**不是按推导层次组织**。

**3 个根本不对齐**：

#### 不对齐 1：没有 derivation 层的可见性

当前 research_result 里看不到 `ic_series` 这种中间推导——只有 aggregated 的 `ic_mean / ic_ir / win_rate`。后果：
- Stage C 的 stability / reliability 想做 split 或 bootstrap，**必须从原始 factor 和 returns 重算一遍 IC**——这正是 Q19 硬编码 "medium" 的根源（太贵了就偷懒）
- Stage D Risk Review 的 raw_view_ic 不得不**再算一次** Raw IC（Q23.5）

Q25 架构下，`derivations.ic_series_by_h` 会作为一等字段存在，下游 analysis 直接消费。

#### 不对齐 2：字段重复没有数据血缘

同一个数字出现在多处：
- `evaluation.ic_mean_validation: 0.046075`
- `risk_review.raw_view_ic: 0.046075`

**两者相等（我对 F018 验证过），但文件结构没告诉你它们是同一个推导的两个副本**。改其中一个不会破坏另一个的引用关系——换句话说，**不一致时不会被察觉**。

Q25 架构下：两个字段都应该是 `derivations.ic_series_raw_by_h[5].mean()` 的引用，物理上不可能不等。

另一个例子：
- `diagnostics.base_valid_ratio: 0.9759`（全局 non-NaN 比例）
- `feasibility.coverage: 0.9759`（每日 non-NaN 比例的跨日均值）
- 对 F018 两者相等，但**定义不同**——对不均匀分布的因子会有差异
- Q25 架构下应当统一为 `derivations.coverage` 一个字段

#### 不对齐 3：analyses 之间看不出数据依赖

当前 `evaluation` 和 `similarity` 是两个独立的 section——看不出 redundancy 的 `subspace.residual_incremental_ic` 依赖的是哪个 factor version（raw? cap-neutral?），也看不出 risk_review 的 `barra_residual_ic` 和 evaluation 的 `ic_mean_validation` 有没有用同一份 returns。

Q25 架构下 analyses 层应该**显式引用** derivations 层的字段——`risk_review.raw_view_ic: ref(derivations.ic_series_raw_by_h[5].mean())` 之类。这是"数据血缘可观测"的基础。

### 部分 5：还没分析到的 12 个点

分为 3 个优先级：

#### 🟠 P1（可能藏 bug）

1. **`_strip_non_serializable`**（batch_runner.py:251）
   - YAML dump 前的转换函数
   - **可能静默丢失 Series / DataFrame / numpy.float64** 等非 YAML 原生类型
   - 如果 ic_series 被保留到 result，可能在这里被剥离
   - **TODO**：读它的白名单逻辑

2. **`_should_recommend_holdout`**（pipeline.py 里的 helper，我没读）
   - 决定 `holdout_review.recommended: true/false`
   - F018 的 output 是 `true`，reason_codes 是 `[high_confidence_candidate, holdout_confirms_signal]`
   - **TODO**：验证是否硬编码或基于 IC 阈值

3. **`search_context` 永远是 `{}`**
   - `pipeline.py:218`：`result["search_context"] = search_context or {}`
   - 从 batch_runner 传入，但 batch_runner 从调用方接——**调用链没人填**
   - 本应从 `ledger.batch_usage + search_ledger` 构造，**和 Q2 "batch_usage 消费未落地" 是同一个根**
   - 对 judge 来说就是 "没有多重检验上下文"，所有 MT 判断退化为硬编码 "low"（Q19 已记录）

4. **`direction: null` 永远是 null**
   - research_result.yaml 每个 candidate 都是 `direction: null`
   - 从没被填充
   - 可能是 long/short 方向标识的遗留字段，或 Q11 hypothesis 层对应的 `direction` 概念
   - **TODO**：确认是死字段还是未实现字段

5. **`precheck.py` 的完整实现**
   - 我讲过功能但没读实际代码
   - `forbidden_patterns` 是否和 `governance/research_config.yaml` 的 forbidden_patterns 同步？
   - 是否有硬编码的表达式模式检查？
   - **TODO**：grep forbidden_patterns 的所有 reference

#### 🟡 P2（小重复计算）

6. **`diagnostics.base_valid_ratio` vs `feasibility.coverage`** —— 上面讲过，语义略不同但实质重复
7. **`support_window_checks` 里 3 次独立 IC 计算** —— 每个 window 独立 merge + pivot
8. **Pairwise redundancy 19 次独立迭代** —— Q24 D1.1 已记录
9. **Barra regression 252 次 Python loop** —— Q23.4 已记录
10. **`_long_short_stats` 的 IID t-stat** —— Q19 已记录

#### 🟢 P3（信息性）

11. **pipeline.run_batch vs batch_runner 的 orchestration 关系**
    - 我看了 prepare_batch + analyze_candidate + batch_runner.run_batch 的片段
    - 但完整的控制流没梳理一遍
    - **可能有重复的 state 管理**

12. **`compute_signal` 内部和 `_compute_diagnostics` 的关系**
    - compute_signal 调用 engine.compute_dsl，然后算 diagnostics
    - diagnostics 是每个 candidate 独立算的——如果多个 candidate 有相似 base_signal，diagnostics 有没有复用机会？（可能没有，因为 candidate-level 属性）

### 部分 6：重复计算的完整清单

把所有已知 + 新发现的重复计算合起来：

| # | 重复 | 位置 | Q 索引 |
|---|---|---|---|
| 1 | **Raw IC** 双算 | Stage C effect_strength vs Stage D risk_review | Q23.5 / Q25 |
| 2 | **factor_wide pivot** 3-4 次 per candidate | 各分析独立 pivot | Q19 / Q25 |
| 3 | **flat ↔ wide 转换** 6-8 次 per candidate | 多处 stack/unstack | Q19 |
| 4 | **Qlib D.features for library** 19 次 per batch | prepare_batch for 循环 | Q12 补充 |
| 5 | **Qlib D.features for candidates** 6 次 per batch | pipeline Phase A | Q12 |
| 6 | **pairwise correlation** 19 次独立 merge | redundancy/pairwise.py | Q24 |
| 7 | **Barra regression** 252 次 Python loop | exposures.py | Q23.4 |
| 8 | **`base_valid_ratio` vs `coverage`** 两次独立算 | diagnostics + feasibility | **新 Q28** |
| 9 | **support_window_checks** 3 次独立 IC | 每 window 独立 merge/pivot | **新 Q28** |
| 10 | **`_weighted_flag_ratio`** 2 次（clean feasibility） | liquidity + small_cap | Q27 |

### 修复路径

这个审计**不产生新的修复动作**，它**验证了 Q25 是必要的**：
- Q25 的 Layer 2 derivations 层是解决 #1-3 + #6-7 的**共同基础**
- Q28 发现的 #8-9 也需要在 Q25 架构下解决（统一 coverage 定义，共享 factor_wide slice 给 support windows）
- 剩下的 unanalyzed 点（P1 的 5 个）是**单独需要去看代码**的 TODO，**不应该等 Q25 refactor 才处理**——`_strip_non_serializable` / `search_context` / `direction` 这些可能本身就有独立 bug

### 关联观察

- **文件结构本身就是架构的外化**：research_result.yaml 的 schema 按"分析模块"组织，这**固化**了当前"分析模块各自为战"的架构。想做 Q25 refactor 就必须**同时改 research_result 的 schema**，否则新旧文件不兼容
- **Schema 版本标记是必需的**：和 Q14/Q16 的 `filter_version` 同理，research_result 应该带 `schema_version: v1 / v2` 标记。迁移时老 batch 保持 v1 结构，新 batch 用 v2（Q25 derivation 分层结构）
- **判决链路的"可见性"是系统健康的核心**：判决链路上每一步的数据血缘都应该可追溯。当前数据被拍扁成大 dict，无法回答 "raw_view_ic 和 ic_mean_validation 是同一数据源吗" 这种基本问题。这是一个**可观测性问题**，也是 Q11 meta-reflect 层的前提
- **Q28 新发现 2 个 未进 Q 列表的小 TODO**：`search_context: {}` 和 `direction: null`——都是"永远是某个默认值"的字段，**可能是小死字段也可能是未实现**。需要各自去 grep 验证

### 2026-04-11 重要修正：Q25 不是 schema refactor，是 runtime refactor

用户指出上面"Q25 架构下 derivations 会作为一等字段存在于 YAML"的描述**是错的**。**ic_series 这类中间量不应持久化到 YAML**，它们是运行时的共享对象。

#### 两个层次必须分清

**层次 A：运行时共享推导（Q25 的真实核心）**
- 在 Python 内存里建立 `CandidateDerivations` 对象
- 所有可共享的中间值（factor_wide_clean / ic_series_by_h / barra_residual_factor / quintile_daily_ls / ...）放在这里
- Layer 3 分析层从这个对象读，从不重算
- **对象在 scope 结束后被 GC，不持久化**

**层次 B：磁盘持久化（research_result.yaml）**
- **只保存评估的最终结论**——标量、小 dict、bucket 分类
- **不保存中间推导**
- 结构保持"按分析模块分组"（evaluation / risk_review / feasibility / ...），这对读者更可读
- 同一数字可以在多个 section 复制（比如 `evaluation.ic_mean_validation` 和 `risk_review.raw_view_ic`）——这**不是问题**，因为是标量复制不是重复计算

#### 数据一致性保证在运行时，不在 YAML schema

当前 `evaluation.ic_mean_validation == risk_review.raw_view_ic`（F018 验证过）**是一个物理巧合**——代码里 Stage C 和 Stage D 各算一次，恰好用的是同一份 factor 和同一份 returns，所以结果相等。

**Q25 修复之后**：两个字段都来自 `derivations.ic_series_raw_by_h[primary_h].mean()` 这个**同一个 Python 表达式**。计算只发生一次，两个 analysis 取同一个 Python 对象的 mean——**物理上不可能不等**。

**YAML 里依然写两个字段**（因为两个 analysis 模块各自的 output 都包含它）。读者不需要看 YAML 就知道它们相等——**因为代码保证了**。

#### 部分 4 的 "3 个根本不对齐" 需要修正

原文的 3 个不对齐部分对部分错：

**不对齐 1（错）**："没有 derivation 层的可见性 / Q25 架构下 ic_series 会作为一等字段"
- **修正**：YAML 里**本来就不该有** ic_series。问题不是 YAML 缺少 derivation section，是**代码里**分析层各自重新算 IC。修复对象是 Python 代码，不是 YAML schema。

**不对齐 2（半对）**："字段重复没有数据血缘，两个 IC 字段相等是巧合"
- **修正**：症状描述对的——当前**确实是巧合**相等，代码里没有同源保证。但**修复路径**不是 "YAML schema 加引用"，是 "**运行时让两个字段来自同一个 Python 对象的 method call**"。

**不对齐 3（基本对）**："analyses 之间看不出数据依赖"
- 这个批评基本成立，但修复也是在**代码层面**让依赖明确（通过函数签名 + dataclass 类型），不是 YAML 层面的引用语法。

#### Schema 版本是否必需

原文建议 "想做 Q25 refactor 必须同时改 research_result 的 schema"——**不必须**。

Q25 运行时 refactor 可以在**完全不改 YAML schema 的前提下**完成。现有结构保留：
- `evaluation: {...}` 依然存在
- `risk_review: {...}` 依然存在
- 各字段还是写各自的 section

改的只是：**Python 代码里这些字段的**来源**——从各自独立计算，变成都从 `derivations` 对象读**。

如果顺便做 schema cleanup（比如标记明显重复字段），那是锦上添花的**独立动作**，不是 Q25 的前置条件。

#### 正确的 YAML 输出 mental model

```yaml
# research_result.yaml —— 只保存评估结论（标量 / 小 dict / bucket）
candidate_id: C001
evaluation:
  ic_mean_validation: 0.046075          # ← derivations.ic_series_raw_by_h[5].mean()
  ic_ir_validation: 0.338                # ← 同一 ic_series 的 std/mean
  monotonicity_validation: 1.0
  quintile_returns: {q1: ..., q5: ...}   # 小 dict 可以存
  support_window_checks: [...]           # 小 list 可以存
risk_review:
  raw_view_ic: 0.046075                  # ← 同一个 derivations.ic_series_raw_by_h[5].mean()
  cap_industry_neutral_ic: 0.0474
  barra_residual_ic: 0.031819
  alpha_survival_ratio: 0.6906
  style_exposures: {ep_ratio: 0.1857, ...}  # 小 dict 可以存
  risk_model_review_bucket: acceptable
feasibility:
  coverage: 0.9759                        # ← derivations.coverage_by_day.mean()
  turnover: 0.029
  ...
```

**不存**：
- ic_series（完整序列）
- factor_wide（宽表）
- residual_factor_wide
- barra_betas_by_date（252 × 7 矩阵）
- quintile_daily_ls（daily 序列）

**存**：
- aggregated mean / std / ir / win_rate（标量）
- bucket 分类（字符串）
- 少量 summary dict（style_exposures / quintile_returns 这种 ~5-7 个键的 dict）
- 小 list（support_window_checks 这种 ~3-5 个 window 的 list）

---

## Q27 — Clean `feasibility/` subpackage 的质量审计：实现正确但未向量化 + half_life 语义不同 + 依赖未完成的 Q16

**入档时间**: 2026-04-11
**相关阶段**: Q19 补充的详细 audit / Q25 的依赖分析

### 背景

Q19 补充提到 `feasibility/` subpackage 是死代码，有真实实现但零 import。用户追问："如果接通，有没有真实代码？有没有重复计算？是不是向量化？"

实际读了 560 行代码后发现，答案比我原本的回答更细腻：**有真实代码**，但**质量不完美**，**不能直接接通**。

### 发现 1：Clean 版实现是正确的

`src/research/feasibility/` 的 560 行代码**完整实现**了 inline 版的所有 4 个假字段：

| inline 假字段 | clean 版的真实实现 |
|---|---|
| `liquidity_coverage_ratio = min(coverage, 0.95)` | `liquidity.py::compute_liquidity_coverage`：基于 20 日滚动中位数 amount + 横截面 30 分位阈值，算**真实 liquid stock 加权比例** |
| `tail_trade_concentration = 0.15` | `concentration.py::compute_tail_concentration`：**top-k 股票权重占比**，跨日均值 |
| `small_cap_concentration = 0.25` | `concentration.py::compute_small_cap_concentration`：**市值底部 30% 股票权重占比**，跨日均值 |
| `rebalance_stress_proxy = "low"` | `stress.py::compute_rebalance_stress`：**`turnover * tail / lcr`** 的派生量 + bucket 分类 |

Plus：
- **`coverage`**：clean 版考虑 `tradable_mask`（剔除停牌等），语义更严格
- **`turnover`**：clean 版用**真正的组合级 turnover**（相邻日权重变化绝对值之和），inline 版用 rank turnover
- **`half_life`**：clean 版用**信号自相关衰减**，inline 版用 IC-by-horizon decay——**语义完全不同**（见发现 3）

### 发现 2：顶层编排干净，但底层有 5 个 Python for-loop

**顶层（`FeasibilityEngine.analyze`）**编排正确：
```python
portfolio = build_proxy_portfolio(signal, tradable_mask, ...)   # 一次算
mean_turnover = portfolio.turnover.mean()                       # 从 portfolio 读
lcr = compute_liquidity_coverage(portfolio.abs_weights, ...)    # 读 portfolio
tail = compute_tail_concentration(portfolio.abs_weights, ...)   # 读 portfolio
small_cap = compute_small_cap_concentration(portfolio.abs_weights, market_cap, ...)
half_life = compute_half_life(signal)                           # 独立
stress = compute_rebalance_stress(mean_turnover, tail, lcr)     # 纯派生
```

**Proxy portfolio 算一次，3 个下游 metric 复用**——符合 Q25 的共享原则。

**但底层实现有 5 个 Python-level 循环**：

1. **`build_proxy_portfolio`** (proxy_portfolio.py:86): `groupby(level=0, group_keys=False).apply(_assign_weights)` —— 每日 Python-level apply 构建权重
2. **`build_proxy_portfolio`** (proxy_portfolio.py:97-108): turnover 计算用 `for dt in dates:` 逐日 reindex + diff
3. **`_weighted_flag_ratio`** (liquidity.py:76-90): `for dt in dates:` 遍历日期算加权比例——而且**被调用 2 次**（一次 liquidity 一次 small_cap），实际运行 2 × n_dates 次
4. **`compute_tail_concentration`** (concentration.py:44): `.groupby(level=0).apply(_date_tail)` —— Python apply
5. **`compute_half_life`** (stress.py:37-47): **嵌套双重循环**——外层 `for _inst, group in signal.groupby(level=1):` 遍历 ~1000 只股票，内层 `for lag in range(1, max_lag + 1):` 遍历 20 个 lag

**循环 5 是最慢的**：一个 candidate 要跑 ~20000 次 Python iteration，对每只股票独立算自相关序列。可以用 FFT-based 向量化 autocorrelation 或 `pd.DataFrame.apply` 替代，性能能提升 10-50x。

**总评**：clean 版在编排层**比 inline 版更干净**（不重复 compute proxy portfolio），但在底层**实现层**，Python 循环数量**多于 inline 版**。单就性能而言，clean 版比 inline 版**更慢**。

### 发现 3：Clean 版的 `half_life` 和 inline 版**语义完全不同**——不是直接替换的关系

这是最容易忽视的问题。两种 half_life 的数学定义不同，**数字在一般情况下不等**：

| 版本 | 语义 | 代码路径 |
|---|---|---|
| **Inline `compute_feasibility`** | IC-by-horizon decay —— **"预测能力"**的半衰期 | 对 h=1/5/10/20 算 IC mean，线性插值找 IC_1d 的一半 |
| **Clean `compute_half_life`** | Signal autocorrelation decay —— **"信号本身"** 的时间自相关半衰期 | 对每只股票的 signal 序列算 lag-k 自相关，跨股票均值 |

**举例说明差异**：

- **基本面因子**（如 F018 EPS change 60d）
  - Signal 自相关：EPS 变化序列慢，自相关半衰期可能 30-60 天
  - IC 半衰期：预测能力对 5 天收益强，对 60 天弱，IC 半衰期可能 5-10 天
- **短期动量因子**
  - Signal 自相关：1 天 return 序列几乎独立，自相关半衰期 1-2 天
  - IC 半衰期：对 1 天收益强，对 10 天弱，IC 半衰期 3-5 天

**两个数字可能差 5-30 倍**。

**下游影响**：`compute_holding_period_proxy` 基于 half_life 分 short/medium/long 桶：
```python
if half_life <= 3:   return "short"
if half_life <= 10:  return "medium"
return "long"
```

**换 half_life 语义会让下游分桶完全变化**——因为分桶阈值（3 / 10）对两种语义不等价。

**这意味着单纯"接通 clean feasibility"会改变系统的行为**——不仅数据变了，**下游 judge 看到的 `holding_period_proxy` 分类也会变**。这对跨 batch 的历史因子比较有影响（老因子的 proxy 是 inline 语义，新因子变成 clean 语义）。

**不能简单 switch——必须先决定哪一种 half_life 语义是对的**。

**倾向**：IC-by-horizon decay 更直接回答 "信号能用多长持仓期" 这个实盘问题。信号自相关是更泛化的"信号属性"指标，但**和实盘持仓决策没有直接关系**。推荐**保留 inline 的语义**（IC-by-horizon），把 clean 版的 signal autocorrelation 作为**辅助指标**独立命名（比如 `signal_autocorr_half_life`）。

### 发现 4：Clean 版依赖 `tradable_mask` —— 但 Q16 未落地

```python
def analyze(self, signal, market_cap, amount, tradable_mask):
    portfolio = build_proxy_portfolio(signal, tradable_mask, ...)
```

Clean feasibility 需要 `tradable_mask` 作为输入。但 Q16 已经发现**整个 tradability 检测系统基本没落地**：
- 停牌 / 涨跌停 / ST / 新股 / 科创 / 北交 过滤**零消费**
- `filter_suspend / filter_limit / min_listing_days` 三个 config flag 存在但**零读取**
- `limit_up / limit_down` 字段同步到 qlib binary 但**零使用**

**如果现在接通 clean feasibility**：
- `tradable_mask` 要么是空 DataFrame（feasibility 崩）
- 要么是全 `True`（退化成"假设所有股票都可交易"）——clean 版的 liquidity / tail concentration / small cap 分析**基于错误前提**

**"tradable_mask 为全 True"的 clean feasibility** ≈ "比 inline 更严格地算假数据"——**正确性反而可能比 inline 版更差**（inline 版的硬编码 0.15 / 0.25 至少是一个"粗略合理"的常数，clean 版在没有 tradable 信息时可能产出极端值）。

### 修复路径：**必须作为一个捆绑单元**

基于发现 1-4，接通 clean `feasibility/` 不能单独做。正确的依赖链：

```
Step 1: Q16 修复（tradable_mask 真实生成）
  ├── Phase 1A: resync_qlib.py 停牌日 OHLCV 设为 NaN
  ├── Phase 1B: get_returns 加涨跌停 mask
  ├── Phase 1C: preprocess 加科创/北交 mask
  └── 产出: 真实的 tradable_mask

Step 2: Q25 Layer 2b 架构（proxy_portfolio 作为共享推导）
  ├── build_proxy_portfolio 作为 Layer 2b 的一部分
  ├── 其他分析（比如未来的 risk review）如果需要组合权重，从这里读
  └── 避免"feasibility 自己 build portfolio + 别处又算一次"的风险

Step 3: 决定 half_life 语义
  ├── 保留 inline 的 IC-by-horizon decay 作为主 half_life
  └── Clean 的 signal autocorrelation 作为辅助，独立命名

Step 4: 向量化 clean 版的 5 个 Python 循环
  ├── 循环 5 (compute_half_life 嵌套) 最急——10-50x 提速
  ├── 循环 1+2 (build_proxy_portfolio) 中急
  └── 循环 3+4 次之

Step 5: 接通 compute_feasibility 作为 FeasibilityEngine 的 thin wrapper
  └── 删除 inline 版的硬编码假字段
```

**单独做任何一步都意义有限**。Step 1-3 是前置条件，Step 4 是性能修复，Step 5 是最终接通。

### 成本估算

- Step 1 (Q16 Phase 1): ~3 天
- Step 2 (Q25 Layer 2b 的一部分): ~2-3 天
- Step 3 (half_life 语义决策): ~几小时讨论 + ~1 天实现
- Step 4 (5 个循环向量化): ~2 天
- Step 5 (接通 wrapper): ~半天

总计约 **1.5-2 周**。但完成后：
- 4 个硬编码假字段变成真实计算
- tradable_mask 下游受益（不只是 feasibility，还有 Q16 所有过滤）
- proxy_portfolio 成为 Layer 2b 共享推导
- half_life 双语义明确

### 为什么重要

1. **"clean 版是真代码" 不等于 "clean 版可以接通"**——这是一个**条件真**的陈述，有多个前置依赖
2. **半成品代码的质量陷阱**：clean 版看起来比 inline 版好（实现更完整），但仔细看发现**向量化程度反而更差**。这提醒我们：**subpackage 的"clean"只是命名层面的，不代表运行性能或架构一致性**
3. **发现 3 的语义差异**是一个"深水区"——两个实现都叫 `half_life`，数字可能差 5-30 倍。没人去对比过两个数字的时候很容易出 silent bug
4. **发现 4 的依赖链**说明 Q16 / Q19 / Q25 必须捆绑修复。之前我给的"Q19 方案 A 接通 clean subpackage"过于乐观——实际接通需要 Q16 先落地

### 关联观察

- **Q27 修正 Q19 补充**里"接通 clean `feasibility/` 就能解决 4 个假字段"的简化说法。真实情况是需要同时做 Q16 修复、half_life 语义决策、5 个循环向量化
- **Q27 揭示一个新 meta pattern**：`subpackage vs inline` 不只是 "干净 vs 半成品" 的简单对立——**半成品 inline 可能在某些维度（比如性能、简洁性）优于 subpackage**。clean 的 inline 编排更简单，clean 的 subpackage 更正确但更慢
- **发现 3 的两种 half_life 语义**属于 Q21 Pattern B（命名撒谎）的一个变体——两段代码用同一个字段名，但计算的是不同的量。字段名本身就成了一个 source of confusion
- **Q27 的修复路径和 Q25 重度重叠**：proxy_portfolio 应该是 Q25 Layer 2b 的一部分，不是 feasibility 内部私有。修 Q27 就是修 Q25 的一个子任务

---

## Q29 — Judge 层 4 个结构性问题：evidence 构建不完整（silent 假阳性源头）+ vocabulary mismatch + LLM/代码边界不清

**入档时间**: 2026-04-11
**相关阶段**: Phase 3 `/factor-judge`

### 问题 29.1（🔴 P0）：`CandidateEvidence.from_judge_packet_brief()` 不完整，silent bypass 5 个 hard gate

`CandidateEvidence` dataclass（`candidate_judge.py:77-119`）有 13 个字段，**所有字段的默认值都是"安全/通过"的一侧**：

```python
@dataclass
class CandidateEvidence:
    candidate_id: str = ""
    mechanism: AlignmentEvidence = field(default_factory=AlignmentEvidence)
    statistical_strength: str = "borderline"
    stability: str = "borderline"
    sign_flip: bool = False                    # ← 默认 False
    redundancy: str = "acceptable"
    feasibility: str = "ok"
    risk_model_review: str = "acceptable"
    execution_gate_passed: bool = True
    expanding_window_pass: bool = True          # ← 默认 True
    known_bad_pattern: bool = False             # ← 默认 False
    multiple_testing_risk_bucket: str = "low"   # ← 默认 "low"
    support_window_warning: str = "none"
    replace_hard / replace_comparison / replace_target_id
```

**`from_judge_packet_brief(brief)` 只捕获 8 个字段**（`candidate_judge.py:121-137`）：

```python
return cls(
    candidate_id=brief.get("candidate_id", ""),
    statistical_strength=brief.get("validation_effect_bucket", "borderline"),
    stability=brief.get("stability_bucket", "borderline"),
    redundancy=brief.get("redundancy_bucket", "acceptable"),
    feasibility=brief.get("feasibility_bucket", "ok"),
    risk_model_review=brief.get("risk_model_review_bucket", "acceptable"),
    execution_gate_passed=brief.get("execution_gate_status") == "pass",
    support_window_warning=brief.get("support_window_warning", "none"),
)
```

**5 个关键字段没被捕获，silent 使用默认值**：

| 字段 | 默认值 | 后果 |
|---|---|---|
| `mechanism` | 空 `AlignmentEvidence()` | **永不判 "drifted"** → 永不 reject |
| `sign_flip` | `False` | **sign_flip hard gate 永远不触发** |
| `known_bad_pattern` | `False` | **known_bad_pattern hard gate 永远不触发** |
| `multiple_testing_risk_bucket` | `"low"` | **MT 风险永远是 low** → holdout_needed = False |
| `expanding_window_pass` | `True` | **expanding window gate 永远通过** |

**如果 LLM 只是 `evidence = from_judge_packet_brief(brief)` 然后 `judge.judge(evidence)`**——**5 个 hard gate 全部被 silent bypass**。

### skill.md 是否要求 LLM 手动填？

skill.md Step 1 说：
```python
from research.judge.candidate_judge import CandidateEvidence
evidence = CandidateEvidence.from_judge_packet_brief(brief)
```

**只说构造 evidence，没明确要求手动填补其余字段**。Step 2 描述"检查 6 维度"但没明确说这些字段必须从 research_result / research_lessons 手动填。

- **隐式期望**：LLM 手动填
- **显式要求**：没有
- **Python 级校验**：没有
- **LLM 偷懒不填**：judge 在"全是安全默认值"的 evidence 上做判决，**没有任何报错**

### 具体可能的 silent false positive

一个因子：
- IC = 0.02（borderline）
- 实际 train sign=+1，validation sign=-1（**sign flip**）
- 表达式命中 `research_lessons.forbidden_patterns` 的一条（**known bad pattern**）
- 累计搜索 500+ 次（**MT high**）
- expanding window 在小窗口 IC=0.08，大窗口 IC=0.005（**不收敛**）

LLM 不手动填：
- validation_effect_bucket = borderline → MEDIUM
- sign_flip = False（默认）→ hard gate 1 不触发
- known_bad_pattern = False（默认）→ hard gate 2 不触发
- mechanism = 空（默认）→ 不判 drifted
- multiple_testing_risk_bucket = "low"（默认）→ holdout_needed = False
- expanding_window_pass = True（默认）→ expanding gate 不触发
- has_fatal = False, has_high = False（可能），holdout_needed = False
- **Verdict: admit** ❌

**应该 reject 或 reserve 的因子被 admit**。

### 可能解释 batch_099-103 的反复假阳性

L001 / L010 / L011 家族的 "validation 过了但 holdout 崩" 模式，**可能部分原因是 Q29.1**：
- Q18（涨跌停 bias）+ Q19（Stage C 假数据）→ validation IC 被膨胀
- Q26（Stage E silent bug）→ bucket 被静默消音
- **Q29.1 → judge 的 5 个 hard gate 被 bypass**

三层叠加让"多重 silent bug 叠加的假阳性"成为系统的稳定失败模式。

### 修复方案

**方案 A（立即，P0）**：让 brief 扩展 + from_brief 强制校验

改 `judge_packet_builder._build_candidate_brief`：
```python
return {
    ...
    # 新增必填字段
    "multiple_testing_risk_bucket": evaluation.get("multiple_testing_risk_bucket", "low"),
    "expanding_window_pass": evaluation.get("expanding_window_pass", True),
    "sign_flip_detected": _compute_sign_flip(evaluation),
    "mechanism_alignment_summary": {...},
    "known_bad_pattern_match": _check_forbidden_patterns(result, research_lessons),
}
```

改 `from_judge_packet_brief`：
```python
@classmethod
def from_judge_packet_brief(cls, brief):
    required = [
        "validation_effect_bucket", "stability_bucket", "redundancy_bucket",
        "feasibility_bucket", "risk_model_review_bucket",
        "multiple_testing_risk_bucket", "expanding_window_pass",
        "sign_flip_detected", "mechanism_alignment_summary",
    ]
    missing = [k for k in required if k not in brief]
    if missing:
        raise ValueError(f"Brief missing required fields: {missing}")
    return cls(
        ...,
        multiple_testing_risk_bucket=brief["multiple_testing_risk_bucket"],
        expanding_window_pass=brief["expanding_window_pass"],
        sign_flip=brief["sign_flip_detected"],
        mechanism=AlignmentEvidence(**brief["mechanism_alignment_summary"]),
        ...
    )
```

**代价**：~40 行代码。**收益**：让 judge 的 5 个 hard gate 真正工作。

**方案 B（长期）**：删除 `CandidateEvidence` 所有字段的默认值，强制构造时提供所有字段。消除"默认都是安全值"的反模式。

---

### 问题 29.2（🟡 P2）：`feasibility` vocabulary mismatch

`candidate_judge.py:267-273`：
```python
feas_map = {
    "ok": ("feasibility_ok", INFO),
    "borderline": ("feasibility_borderline", MEDIUM),
    "poor": ("feasibility_poor", HIGH),
}
f_code, f_sev = feas_map.get(
    evidence.feasibility, ("feasibility_borderline", MEDIUM)
)
```

**Consumer 的 map key 是 `ok / borderline / poor`**。

但 `judge_packet_builder._feasibility_bucket`（`judge_packet_builder.py:64-79`）**producer 返回 `good / acceptable / poor`**：
```python
def _feasibility_bucket(feasibility):
    if stress == "high":   return "poor"
    if stress == "medium": return "acceptable"
    ...
    return "good"
```

**Vocabulary mismatch**：
- `"good"` → map 里没有 → default `MEDIUM`
- `"acceptable"` → map 里没有 → default `MEDIUM`
- `"poor"` → 匹配 → `HIGH`

**后果**：`feasibility = "good"` 的因子被 judge **当成 borderline**（MEDIUM severity）。F018 实际就是这种情况——它的 `feasibility_bucket: good`，但 judge 看到的是 "borderline"。

这是 Q26 家族又一例 producer/consumer vocabulary 不一致。

**修复**：统一两边的 vocabulary（推荐改 judge 的 map 为 `good / acceptable / poor`）。

---

### 问题 29.3（🟠 P1）：LLM 和代码的判决边界不清

`CandidateJudge.judge()` 是一个纯 Python 函数。但：
- **pipeline 里没有自动调用**——`compute_implementations.py` 和 `batch_runner.py` 都不 import 它
- skill.md 说 LLM "进行 6 维裁决"，**没明确说**必须调用 `judge.judge(evidence)`
- LLM 可能**自己按 skill.md 的规则走一遍**得出 verdict，和代码规则可能不一致
- **没有 single source of truth**

**同一个 candidate，LLM 走和代码走可能得到不同 verdict**。而且没有任何 trace 能说明哪个是"真实"判决。

**修复**：
- **强制** LLM 在 skill.md Step 2 必须调用 `CandidateJudge.judge(evidence)`，verdict 先由代码产出
- LLM 只做 contextual adjustment（基于 research_lessons / ledger 上下文加 reason codes 或调整 admit → reserve）
- **不允许** LLM 完全 override 代码判决，只允许 "downgrade"（admit → reserve，不允许 reject → admit）

---

### 问题 29.4（🟢 P3 设计层）：Judge 只看 bucket，无法看原始数字做细粒度判断

`CandidateEvidence` 的维度字段全是 bucket 字符串，**看不到**：
- `ic_mean_validation` 的实际数值
- `alpha_survival_ratio` 的具体比值
- `max_lib_corr` 的精确数字

**限制**：
- 无法区分 "IC=0.015 刚过 borderline 门槛" 和 "IC=0.029 接近 strong" —— 两者都是 borderline
- 无法做 "bucket 是 acceptable 但数值接近 borderline 阈值，建议 reserve" 这种判断
- judge 的判决空间被 bucket 化严重压缩

**修复**（长期）：在 `CandidateEvidence` 里同时保留 bucket 和原始数字，让 judge 有能力做细粒度 contextual 判断。

---

### 问题 29.5：RouteJudge 的跨 batch 字段也是空的

`route_judge.py:44-47`：
```python
cross_batch_family_admits: int = 0
cross_batch_family_batches: int = 0
family_attempt_count: int = 0
```

用于 `promote_family` verdict，但**谁填？** skill.md 说从 ledger 读，但和 candidate evidence 一样是 implicit 期望，LLM 可能忘了做。

**和 Q22 "family 升格机制死代码" 同根**——代码齐全，填数据的动作 implicit，`promote_family` 永远不触发。

---

### 4 + 1 个问题合起来的影响

| # | 严重性 | 影响 |
|---|---|---|
| 29.1 | 🔴 P0 | 5 个 hard gate silent bypass，silent 假阳性源头 |
| 29.2 | 🟡 P2 | feasibility vocabulary mismatch，降级而非 fail |
| 29.3 | 🟠 P1 | LLM/代码判决不一致，无 single source of truth |
| 29.4 | 🟢 P3 | bucket 化压缩判决空间（设计权衡） |
| 29.5 | —— | 和 Q22 同根的 promote_family 死代码 |

### 和前面 Q 的关系

**"让 judge 层真正看到真数据" 的最小修复单元**——必须同时做：

1. **Q19 方案 A**（接通 clean subpackage）→ Stage C 数据真
2. **Q26 方案 A**（修 3 个 bucket mismatch）→ Stage E 数据到 judge
3. **Q29.1 修 from_judge_packet_brief**（方案 A）→ judge 能看到完整 evidence

这 3 个构成一个整体修复。任何一个单独做都**不够**——因为三层都在"消音"真实数据。

### 关联观察

- **Q29.1 是"默认都是安全值"反模式的典型**：软件工程上这是 footgun——任何有 fallback 默认值的输入 schema，消费者都应该要求**必需字段强制提供**。dataclass 的默认值在这里是反模式
- **Q29.3 的"LLM/代码边界不清"是整个 skill-based 系统的通病**：只要 skill 是自然语言描述的 workflow，就很难保证"哪一步必须用代码，哪一步可以用 LLM"有单一真相
- **Q29 合起来证明 Q11（自主探索循环）的 meta-reflect 层必须能看穿 bucket**——只看 bucket 无法做"为什么这个因子看起来通过但实际 holdout 崩"这种 meta 分析。meta-reflect 需要访问原始数字和 evidence 完整性

---

## Q30 — Judge 层的 LLM/Python 分工没有显式设计,系统无法自动分辨哪些判决该在哪一层

**入档时间**: 2026-04-11
**相关阶段**: Phase 3 `/factor-judge` 的架构设计

### 用户提出的核心问题

> "评选他是不是 OK 的逻辑是纯 Python 逻辑吗?那 LLM 干什么?有很多的逻辑单纯的 Python 并不能直接决定吧。我们期望是 LLM 能从上一个环节阅读然后分析然后给出对应的评价。当前肯定是可以存在一些逻辑 Python 但是我没有看懂。那究竟什么样子是可以的什么样子是不可以的,他能分辨吗?"

这个问题戳中 Phase 3 最深层的设计模糊:**LLM 和 Python 的职责边界不清**。

### 当前系统的状态

**Python 侧**(`CandidateJudge.judge()` in `candidate_judge.py`):
- 是一个纯函数:输入 `CandidateEvidence` dataclass,输出 `CandidateVerdict`
- 逻辑:hard gates + bucket → severity → verdict
- **不读文件,不调 LLM,不看历史,决定性**
- 但**不被 pipeline 自动调用**——execute pipeline 写完 `judge_packet.yaml` 就结束,不 import `CandidateJudge`

**Skill.md 侧**(LLM 的工作):
- Step 1: 读 research_lessons + ledger + judge_packet
- Step 2: 构建 CandidateEvidence(通过 `from_judge_packet_brief`)
- Step 3: "对每个 candidate 检查 6 个维度"——**没说是 LLM 自己检查还是调用 `CandidateJudge.judge()`**
- Step 4-6: Route verdict / Logic recommendation / 回写

**边界模糊的具体表现**:
- `compute_implementations.py` 和 `batch_runner.py` **都不 import CandidateJudge**
- skill.md **没明确说** LLM 必须调用 `judge.judge(evidence)`
- LLM 可能**自己**按 skill.md 的规则走一遍,得出 verdict——和 `CandidateJudge.judge()` 走的规则**不一定一致**
- **同一 candidate,两种路径可能得到不同 verdict**
- **没有 single source of truth**

### 纯 Python 能做 / 做不了的判决

用户的直觉正确——**有很多判决单纯 Python 做不了**。

#### Python 能做的判决(numeric / 结构性)

| 维度 | 纯 Python 的判断逻辑 |
|---|---|
| Statistical strength | `ic_mean >= 0.015 AND ic_ir >= 0.15` → strong |
| Stability | `split_ic_consistency >= 0.75` → good |
| Redundancy | `max_lib_corr >= 0.85` → high |
| Feasibility | `turnover > 0.5` → poor |
| Risk review | `alpha_survival < 0.3` → poor |
| Sign flip | `sign(ic_train) != sign(ic_val)` → True |
| Execution gate | `valid_ratio < 0.1` → fail |

这些**都是阈值判断**。纯函数,可复现,可测试。

#### Python **做不了**的判决(需要 LLM 上下文)

1. **Mechanism Alignment** — 需要阅读 rationale 和 hypothesis 文本,判断表达式是否**语义上**回答了假设
2. **Known bad pattern matching** — 需要读 research_lessons 的自然语言描述,做 semantic matching
3. **跨 candidate 横向比较** — "C002/C003 是同一 ELT 的两个变体,按 Q4 只能 admit 一个"
4. **Contextual research_lessons override** — "dominant_style=turnover_20d + research_lessons 说过是陷阱" → 强化 reject
5. **Logic-level structural 判断** — "L001 的 candidate 都在 str_1m 上失败,这是**结构性边界**不是偶然" → parked 而不是 saturated
6. **Cross-batch ELT 脉络判断** — "这个 ELT 从 v1 到 v2 在优化 crowding,不是 kill 而是 continue"

**这些都需要阅读 + 理解 + 上下文 + 推理,纯 Python 做不了**。

### 正确的 4 层分工

```
Layer 1: Python Hard Gates(结构性失败)
  - execution_gate_passed == False → reject
  - factor_value 全 NaN → reject
  - valid_ratio < 0.1 → reject
  - variance == 0 → reject
  用途:防垃圾数据污染 judge
  特征:纯 Python,决定性,不可被 LLM override

Layer 2: Python Numeric Classification
  - 对每个维度用 thresholds 算 bucket
  - sign_flip detection(纯数字)
  - multiple_testing bucket from ledger
  - expanding_window convergence check
  用途:提供"客观 baseline"
  输出:numeric_evidence + initial_buckets + raw numbers
  特征:纯 Python,deterministic,测试友好

Layer 3: LLM Contextual Adjudication
  LLM 阅读:
    - Layer 2 的 numeric evidence(bucket + 原始数字)
    - research_lessons.md(已知失败模式、style 陷阱)
    - ledger(search 历史、family 历史、ELT 演化)
    - candidate rationale 和 expression
    - logic card hypothesis 和 threads
    - batch 内其他 candidate(横向对比)
  LLM 做的判断:
    1. Mechanism alignment(读 rationale 判断)
    2. Known bad pattern(读 lessons 判断)
    3. Logic saturation(结构性 vs 偶然)
    4. Cross-candidate 比较
    5. Contextual downgrade(不是 upgrade)
  输出:final_verdict + reasoning + adjusted reason_codes

Layer 4: Python Verdict Wrapping (GuardedWriter)
  - 校验 LLM 输出的 schema
  - 确保 admission_payload 完整
  - 检查 LLM 有没有 override fatal hard gate(不允许)
  - 写入 registry / ledger / card
```

### LLM 可以做什么 vs 不可以做什么

**可以**(在 Layer 3):
- ✅ 基于 research_lessons 的 contextual **downgrade**(admit → reserve, borderline → reject)
- ✅ 阅读 rationale 做 mechanism alignment 判断
- ✅ 跨 candidate 横向比较后决定 reserve 哪一个
- ✅ 基于 ledger 的 logic saturation / ELT 演化判断
- ✅ 上下文感知的 reserve(研究 lessons 说过类似结构 holdout 崩过,先 reserve)

**不可以**:
- ❌ **Override Layer 1 的 hard gate**(比如 valid_ratio=0.05 但因为 rationale 好就 admit)
- ❌ **Override numeric thresholds 直接 admit**(IC=0.005 但 mechanism 新颖就 admit)
- ❌ **Upgrade 超过 Layer 2 的 bucket**(Layer 2 判 borderline,LLM upgrade 到 admit)
- ❌ **在 evidence 不完整时 admit**(mechanism 字段空着就 admit)

**一句话规则**:

> **Layer 2 的 numeric 判决是 "admission 的上界"**。LLM 可以 downgrade(更保守),**不能 upgrade**(更激进)。
>
> **Layer 3 的 contextual 判断是 "reject 的额外来源"**。LLM 可以在 Layer 2 判 strong 的基础上 reject(因为 mechanism 不对或 lessons 警告),但不能反过来 upgrade。

这是**非对称权力分配**:
- Numeric(Python)**定上限**——再好也不能超
- Contextual(LLM)**定下限**——再好的数字也可能被 context 证据 reject

### 系统能自动分辨吗?——**不能,这是人类设计决定**

每一个维度都需要**显式决定**:
- 在 Layer 1(硬 gate)?
- 在 Layer 2(numeric bucket)?
- 在 Layer 3(LLM contextual)?

比如 "sign_flip" 这一维:
- **可以**放 Layer 2:`sign(train) != sign(val)` → 硬 reject
- **也可以**放 Layer 3:"sign flip 了,但如果 ic_train 是 +0.001 接近 0,这是噪声不是真翻号" → 不 reject
- 这是**架构决定**,不能让系统"自己分辨"

**当前系统的 6 个维度归属都是隐式的**,没有显式文档。这让:
- 修代码的人不知道"我改这里会不会破坏 LLM 的职责"
- 审查的人不知道"这个决定应该在哪一层做"
- LLM 不知道"我应该怎么处理这个字段"

### 建议的明确归属

```
mechanism_alignment:    Layer 3 (LLM only,需要读 rationale + hypothesis)
statistical_strength:   Layer 2 + Layer 3 downgrade
stability:              Layer 2
redundancy:             Layer 2 (numeric) + Layer 3 (semantic redundancy)
feasibility:            Layer 2
risk_model_review:      Layer 2 + Layer 3 (research_lessons style trap)
sign_flip:              Layer 2 (hard gate)
known_bad_pattern:      Layer 3 (LLM only,读 research_lessons)
multiple_testing:       Layer 2 (numeric from ledger)
execution_gate:         Layer 1 (hard gate)
```

### 当前系统 vs 理想状态

| 维度 | 理想 | 当前 |
|---|---|---|
| Layer 1 hard gate | 明确分离 | ⚠️ 和 Layer 2 混在 CandidateJudge.judge() 里 |
| Layer 2 numeric | 明确分离 | ⚠️ 有,但**很多字段没捕获**(Q29.1)|
| Layer 3 LLM contextual | 明确边界 | ❌ **完全依赖 LLM 自觉**,没 Python 约束 |
| Layer 4 schema 校验 | 明确 | ⚠️ GuardedWriter 部分实现,不检查 LLM override hard gate |

**最大问题是 Layer 3 没有边界**:
- LLM 可以读 research_lessons 吗?期望可以,没强制
- LLM 读完必须以什么形式 feed 回 judge?没规定
- LLM 的 downgrade 和 upgrade 有区别吗?没规定
- LLM 如果和 Python Layer 2 冲突,谁胜?没规定

### 可行方案

**方案 A(立即,P0)**:skill.md 里明确 LLM 和 Python 的分工

- 在 `factor-judge/skill.md` 里新增一节:"**Layer 分工与 LLM 权限**"
- 明确列出 6 个维度每个在哪一层
- 明确 LLM 可以 downgrade 不可以 upgrade
- 明确 LLM 必须先调用 `CandidateJudge.judge(evidence)` 拿 baseline,然后做 contextual adjustment

**方案 B(必做,P0)**:`CandidateJudge.judge()` 产出 **baseline verdict + contextual override space**

让 `judge()` 返回:
```python
{
    "baseline_verdict": "admit",      # Layer 2 的判决
    "numeric_summary": {...},          # 原始数字给 LLM 看
    "downgradable_to": ["reserve", "reject"],  # LLM 可以降级到的选项
    "locked_fatal": False,             # 如果 Layer 1 fatal,LLM 不能 upgrade
}
```

LLM 看到 `baseline = admit`,可以 contextual downgrade 到 reserve/reject,**不能 upgrade**(因为已经是最高了)。
LLM 看到 `baseline = reject`,如果 `locked_fatal = True`,**不能 upgrade**(Layer 1 不能被 LLM override)。

**方案 C(推荐,P1)**:GuardedWriter 校验 LLM 的 verdict 符合 Layer 规则

- 如果 LLM 输出的 verdict 是 admit 但 Layer 1 判 fatal → 拒绝写入
- 如果 LLM 输出的 verdict 比 Layer 2 baseline 更激进(baseline=reserve,LLM=admit)→ 拒绝写入
- 只允许 downgrade,不允许 upgrade

**方案 D(长期)**:把 skill.md 的 "6 维判决" 改成更明确的 pipeline

当前 skill.md 是自然语言描述,容易被不同 LLM 实例以不同方式解读。改为:
```
Step 1: 调用 CandidateJudge.judge() 拿 baseline_verdict
Step 2: 读 research_lessons.md 找可能的 contextual override 线索
Step 3: 读 ledger 确认 search 历史
Step 4: 对每个 candidate 做 contextual adjustment(只能 downgrade)
Step 5: 写 final_verdict,附 reasoning 和 baseline 对比
```

### 优先级

- 方案 A + B 立即做(明确分工 + 基础的 baseline/downgrade 机制)
- 方案 C 紧跟(GuardedWriter 校验)
- 方案 D 是长期架构目标

### 关联观察

- **Q30 是 Q29 的 meta-level 解释**。Q29 发现"`from_judge_packet_brief` 不完整",但没解释为什么会这样。**答案是 Q30 的 Layer 3 没定义**——如果 LLM 是 Layer 3,那么 Layer 2 的 `from_brief` 只需要提供 numeric bucket(这是它做的),剩下的 mechanism / sign_flip / known_bad_pattern 等应该由 Layer 3 LLM 从其他来源(research_lessons, research_result)手动读。**问题不是 from_brief 不完整**,是 **Layer 3 没有显式定义 LLM 要读什么**
- **Q30 + Q29 合起来揭示了 skill-based 系统的根本问题**:自然语言描述的 workflow 无法显式表达 "LLM 职责 vs 代码职责" 的边界。需要要么用 DSL 显式表达,要么用代码直接检查 LLM 是否履行了职责
- **Q30 和 Q11 深度相关**。Q11 的 meta-reflect 层本质上也是 Layer 3 contextual adjudication——只是在更高层面(对整个系统状态的反思,不是对单个 candidate)。如果 Q30 的 Layer 3 定义清楚了,Q11 的 meta-reflect 就是 "Q30 Layer 3 在 logic 和 batch 层的递归应用"
- **"系统能分辨吗"这个问题的深层含义**:用户直觉上期望系统有某种"智能"能自动判断哪些该代码哪些该 LLM。**这个直觉是错的**——架构决定只能人类做,系统不能也不应该"自己分辨"。Q30 的价值就在于**把这个不能自动化的决定显式写出来**,让后续修改有清晰的边界

### 2026-04-11 重要修正:Q30 的 "Python 上限" 模型太死板,正确是 "Checkpoint-driven LLM"

用户指出 Q30 原方案的核心问题:

> "某些 pattern 某些因子坑不是很好,但是 LLM 通过分析发现是可以的。所以本质上我们想要规范好然后 LLM 能够深入分析,可以基于 checkpoint 来固定从哪些方向思考的逻辑。"

**Q30 原版的错误假设**:
- Python 的 numeric 规则是"baseline",LLM 只能 downgrade
- 这隐含了 "Python 规则是正确的" 的前提
- 但实际上 Python 规则是**固化的经验**,不是真理
- 如果一个 candidate 有真正的 mechanism alignment 但 IC 恰好在阈值下,LLM 应当能 argue 并 upgrade

#### 正确的架构:**Checkpoint-driven LLM**

**Python 不是决策者,是思考提纲**。它的作用是"强制 LLM 对每个重要角度给出结构化答案",不是"替 LLM 做决定"。

```
Layer 1: Python Hard Structural Gates
  只处理"数据是不是坏的"——valid_ratio < 0.1 / variance = 0 / parse error
  这是**不可争议**的结构性失败,LLM 不能 override
  范围极小,不做 numeric 判决

Layer 2: Python Checkpoint Generator
  对每个 candidate 生成一份"结构化问题清单":
  [
    {checkpoint_id: "mechanism_alignment", question: ..., numeric_hint: None, output_schema: ...},
    {checkpoint_id: "statistical_strength", question: ..., 
     numeric_hint: {ic_mean: 0.012, python_baseline: "weak", threshold_ref: "0.015"},
     output_schema: {verdict, reasoning, agrees_with_hint, override_reason}},
    {checkpoint_id: "known_bad_pattern_check", required_inputs: [research_lessons], ...},
    ...
  ]
  numeric 是 **advisory hint**,不是硬约束

Layer 3: LLM Structured Reasoning
  LLM 对**每个 checkpoint 必须产出结构化答案**:
    - 不允许 skip
    - 不允许只给 verdict 不给 reasoning
    - disagree with numeric hint 必须写 override_reason + 可引用证据
  输出:checkpoint_responses (dict of structured answers)
  
  **LLM 有双向权力**:upgrade 或 downgrade 都可以,但必须给理由

Layer 4: LLM Synthesis
  综合所有 checkpoint 答案 → final verdict + reasoning trail
  输出包含:verdict, confidence, summary_reasoning, 
         blocker_checkpoints, overridden_hints

Layer 5: Python Audit Wrap (GuardedWriter)
  1. 所有 checkpoints 都有 response(没 skip)
  2. Response schema 合法
  3. disagree with hint 时有 override_reason
  4. Citations 真实存在(grep 验证 lesson_id 存在)
  5. Final verdict 和 blocker_checkpoints 一致
  6. Layer 1 的 fatal gate 不能被 override
```

#### 核心转变

| | Q30 原版(Python 上限)| 正确版(Checkpoint-driven)|
|---|---|---|
| Python 角色 | 决策者 | 监督者(确保 LLM 考虑了每个角度)|
| LLM 权力 | 只能 downgrade | **双向**调整,但必须给理由 |
| numeric 规则刚性 | 硬规则 | **advisory hint** |
| 防偷懒机制 | 依赖 LLM 自觉 | **强制 checkpoint 清单** + 强制 citation |
| 允许 LLM 纠正 Python | ❌ | ✅,需要可引用证据 |

#### 举例说明差异

**场景**:candidate IC=0.012(numeric: weak),但 rationale 清楚 + mechanism 合理 + lessons 无负面记录 + validation 期恰好包含 2020 新冠冲击

**Q30 原版**:
- Python baseline = weak → reject
- LLM 只能 downgrade,没机会 upgrade
- 直接 reject

**Checkpoint-driven**:
- Checkpoint 1 (statistical_strength):
  - numeric_hint: python_baseline=weak
  - LLM: "Agrees with hint: false. Override reason: validation 期包含 2020 新冠(ref: ledger.regime_markers), IC 可能被一次性冲击压低"
- Checkpoint 2 (mechanism_alignment):
  - LLM: "Aligned. Rationale 说明 Sub(EPS_t, EPS_t-60) 测试 EPS 改变率的差异,对应 L015.hypothesis.condition 的第 2 句 '改善速度与价格动量的背离'"
- Checkpoint 3 (known_bad_pattern):
  - LLM: "Clean. grep research_lessons 未找到针对 Sub(EPS change) 结构的 FP 记录"
- Checkpoint 4 (cross_candidate_comparison):
  - LLM: "其他 5 个 candidate 都是 PB conditioning 变体,这个是独立方向"
- Final: **reserve**(不 admit 因为 IC 确实弱,不 reject 因为 contextual 证据足够多)

**关键**:LLM 可以 argue "numeric 说 weak 但实际是 regime 噪声",但必须**给证据**(引用 ledger 或 research_lessons)。Python Layer 5 会校验证据真实存在。

#### 这个设计的 4 个真实风险

**风险 1:Checkpoint gaming(LLM 敷衍)**
- LLM 写 "mechanism is aligned" 而没有真思考
- **缓解**:强制 `reasoning` 包含至少一个 citation,Layer 5 grep 验证真实性
- **缓解**:每个 checkpoint 加 `what_would_change_my_mind` 字段,强制可证伪声明

**风险 2:跨 session 不一致**
- 同一数据在不同 LLM 调用下得到不同 verdict
- **缓解**:prompt 版本化 + reasoning trail 持久化
- **缓解**:meta-reflect 定期扫描"同类 candidate 的 verdict 漂移"

**风险 3:Gradual drift(累计系统性漂移)**
- 单个 batch 看起来合理,累计 100 batch 后系统整体 over-admit
- **缓解**:meta-reflect 统计 LLM override 的 holdout 验证率
- **缓解**:被 holdout 证伪的 override 模式生成 global_escalation 警告

**风险 4:Checkpoint 清单本身不全**
- LLM 思考被提纲限制,提纲漏了某个维度 LLM 也会漏
- **缓解 1**:checkpoint 清单可演进,reflect 发现新失败模式 → 新 checkpoint 提案
- **缓解 2**:允许 LLM 写 `extra_checkpoints` 补充主动发现的角度
- **缓解 3**:extra checkpoints 反复出现的话提炼为必填

#### 实施难点

**难点 1**:checkpoint 清单是系统最重要的设计产物
- 当前 skill.md 没有这个清单
- 需要列出 10-15 个 checkpoint + 版本化 + 每个的 schema

**难点 2**:Layer 5 audit 的 citation 校验
- research_lessons.md 里每条 lesson 需要明确 id(现在是 NM-L001-timing 这种,可 grep)
- LLM 的 reasoning 必须引用这个 id
- Python grep 验证 id 真实存在

**难点 3**:citation 语义真实性难完全校验
- LLM 可能引用 `lesson#FP-L004` 但内容和这条 lesson 无关
- **完全避免需要另一个 LLM 审查**(递归审查,成本高)
- **部分缓解**:机械校验 id 存在 + meta-reflect 定期人工抽查

**难点 4**:LLM upgrade numeric 的防御
- IC=0.012 (weak) 被 upgrade 到 admit,这是最危险的 override
- **必须**触发**强制 holdout review** —— holdout 作为 tiebreaker
- 跟踪 LLM override 的 holdout 验证率,长期低于 50% → LLM 判断不靠谱,警报

#### 和前面 Q 的关系

- **Q30 修正版替代原版**:原版的"Python 上限 + LLM 只能 downgrade"被撤回,正确版是"Python checklist + LLM 双向调整但强制 citation"
- **修 Q29.1 的正确方式变了**:原本是"扩展 brief,让 Python 看到所有字段"。正确版是"Python 产出 checkpoint 清单,让 LLM 被强制思考每个角度"。`CandidateEvidence` dataclass 本身过时了——应当被 `CheckpointResponse` list 替代
- **Q11 自主探索循环的 meta-reflect 层和 Q30 修正版深度相关**:meta-reflect 正是在跨 batch 层面做 "checkpoint-driven reasoning + citation audit" —— 在更高层对系统整体做同样的事
- **Q20 硬编码魔数的意义也变了**:在 checkpoint-driven 架构下,硬编码阈值是**advisory reference**,不是硬约束。LLM 看到 "numeric_hint: {threshold_ref: 0.015}" 可以 argue override,**只要 research_lessons 支持**

#### Meta 教训

这次修正揭示了一个重要的设计原则:

> **当规则来自"固化的经验",不要让规则成为"硬约束"。让规则成为"必须被 argue 的 advisory"**。

Python 里的所有 numeric threshold(Q20 的 40+ 魔数)本质上都是**固化的经验**,不是真理。强制它们成为硬约束会让系统失去 contextual 纠错能力。正确做法是让它们以 "hint" 形式出现,强制 LLM 对每个 hint 表态(agree / disagree + 理由),让经验在运行时被不断校验。

这也是 Q11 meta-reflect 的基础——**系统需要能质疑自己的规则**,质疑的机制就是"强制 LLM 对每个规则给出 contextual 表态,然后用 holdout 验证表态的正确性"。

---

## Phase 3.5 总览 — finalize-batch(3.5a)与 /factor-reflect(3.5b)的分工

**提问时间**: 2026-04-11
**相关阶段**: Phase 3.5(judge → card/state 写回)

### 分工设计(按 `.claude/skills/factor-mine/skill.md` 160 行)

| 维度 | 3.5a finalize-batch | 3.5b /factor-reflect |
|---|---|---|
| 执行主体 | 纯 Python(`BatchFinalizer`) | LLM 驱动 skill |
| 是否可跳过 | **否**(必须) | 是(允许退化) |
| 写入对象 | card.yaml(最小字段)、state.yaml、ledger.audit/batch_usage、holdout_queue | card.yaml(thread 细粒度补充)、reflection.md(叙事)、global_escalation.yaml、research_lessons.md(软经验) |
| 构造 delta 的逻辑 | 从 `logic_recommendations` + `candidate_verdicts` 机械推导 | LLM 综合 `logic_diagnostics` + card history 生成 |
| 定位 | "最小闭环" —— 保证结构一致性 | "增强层" —— 补充认知深度 |

**关键观察**:两阶段**调用同一个 `apply_belief_delta()` 和 `write_reflection_md()`**。这个"共享写入通道"是 Q31/Q32/Q33 的根源 —— 两个阶段设计上互补,但实现上**没有任何 handshake 标志**告诉对方"我已经写过了,你不要重复"。

这个设计模式之所以脆弱,是因为它假设:
1. 3.5b 的 LLM 记得"只补充不重复"(纯自觉)
2. `apply_belief_delta` 本身是幂等的(实际上不是 —— counter 字段是 `+=`)
3. reflection.md 的 header guard 在 3.5a 内部但不在 `write_reflection_md` 内部

下面 Q31-Q38 是从这个根因衍生出来的具体失败模式。

---

## Q31 — `apply_belief_delta` counter 字段是加法,3.5a+3.5b 双写会双倍计数

**提问时间**: 2026-04-11
**相关阶段**: Phase 3.5a + 3.5b

### 发现

`src/research/logic/reflect.py:175-188`:

```python
evidence["factors_generated"] = (
    evidence.get("factors_generated", 0) + delta.generated_this_batch
)
evidence["factors_admitted"] = (
    evidence.get("factors_admitted", 0) + delta.admits_this_batch
)
if delta.admits_this_batch > 0:
    evidence["rounds_without_admit"] = 0
else:
    evidence["rounds_without_admit"] = (
        evidence.get("rounds_without_admit", 0) + 1
    )
```

counter 字段全部是 **additive**(`+=`)。

现在看调用路径:
1. **3.5a** `BatchFinalizer._build_delta`(`finalizer.py:280-292`)从 `candidate_verdicts` 计算 `generated=len(candidates_for_this_logic)`, `admits=len(admit+replace)`,然后调 `apply_belief_delta` —— counter 被加一次
2. **3.5b** `/factor-reflect` skill 里 LLM 构造 delta,skill.md 明确要求:"`generated_this_batch` = 该 logic 在本 batch 的 **总候选数**",然后调 `apply_belief_delta` —— counter **又被加一次**

**两阶段按照各自 skill.md 描述跑,counter 一定会 × 2**。

同样的 bug 也发生在 `rounds_without_admit`:
- 假设某 logic 本 batch admits=0
- 3.5a 跑完 → `rounds_without_admit += 1`(比如从 2 → 3)
- 3.5b 跑 → 又 `+= 1`(3 → 4)

### 为什么重要

1. **所有依赖 counter 的调度/裁决逻辑都会被污染**:
   - `rounds_without_admit ≥ 2` 是 saturation 触发条件 → 错误 saturation → logic 被提前转 saturated → 被排除出 schedulable
   - `factors_admitted / factors_generated` 是 logic 健康度指标 → 下一轮 idea 策略选择(deepen vs broaden)基于它
2. **没有任何校验**:card schema 允许任意 int,看不出"这个数被双加了"
3. **L015 的数字看起来反而偏低(见 Q37)**,说明目前 3.5b 可能根本没跑,bug 还没被触发 —— 但一旦用户真的按 mine skill.md 完整执行两阶段,bug 立刻显现

### 可行方案

**方案 A(推荐)—— `apply_belief_delta` 幂等化**:增加 `batch_id` 参数,在 card 里记录 `applied_batches: [batch_102, ...]`,如果当前 batch_id 已存在则**跳过 counter 增量,其他字段仍可更新**。这个设计把幂等保证从"调用方自觉"变成"数据层硬约束"。

```python
def apply_belief_delta(card_path, delta):
    card = load_yaml(card_path)
    applied = card.setdefault("evidence_summary", {}).setdefault("applied_batches", [])
    counters_already_applied = delta.batch_id in applied
    # ... mutations ...
    if not counters_already_applied:
        evidence["factors_generated"] += delta.generated_this_batch
        evidence["factors_admitted"] += delta.admits_this_batch
        # rounds_without_admit update
        applied.append(delta.batch_id)
    # 其他字段(threads/families/avoid_patterns)正常 merge
```

**方案 B(最小改动)**:3.5b 的 LLM 强制 `generated_this_batch=0, admits_this_batch=0`,counter 只由 3.5a 负责。skill.md 当前没这个约束,需要补一条显式规则。

**方案 C**:两阶段合并 —— 取消 3.5a 的 counter 写入,等 3.5b 统一写。风险:如果 3.5b 被跳过(设计上允许),counter 永远不更新。

方案 A 最稳健,方案 B 最快。选 A 是因为它同时防御了 Q32(重入)。

---

## Q32 — `finalize-batch` 非幂等:同一 batch 再跑一次会重复累计

**提问时间**: 2026-04-11
**相关阶段**: Phase 3.5a

### 发现

`finalizer.py:83-91`:

```python
current_phase = bu.get(batch_id, {}).get("phase", "judged")
if current_phase != "finalized":
    try:
        validate_phase_transition(current_phase, "finalized")
    except ValueError:
        logger.warning(
            "Phase transition %s→finalized not standard, proceeding anyway",
            current_phase,
        )
# 继续往下跑 apply_belief_delta / recompute_state / ...
```

逻辑是:**如果当前 phase 已是 finalized,跳过 phase 转换校验,但继续执行后续 12 步**。换句话说,`finalize_batch(batch_102)` 执行两次:

- 第 2 次不会报错
- `apply_belief_delta` 再跑一遍 → counter 再 += 一遍
- `record_batch_usage_from_sources` 再写一遍
- `append_audit_entry` 写一条新的 audit(ledger 里会看到同一 batch 的两条 finalize 记录)
- reflection.md 有 header guard(`if f"## Batch {batch_id}" in content: continue`),第二次会跳过 ✓
- recompute_state 是幂等的(扫 cards) ✓
- 但 counter 和 audit 已经被污染

### 为什么重要

1. **自动化场景下极易触发**:mine 循环可能因为中断/retry 重跑 finalize。没有保护,每次重跑都是一次污染。
2. **"soft fail" warning 容易被忽略**:日志里只有一行 WARNING,没有 hard stop
3. **与 Q31 叠加**:如果 3.5a 重跑 + 3.5b 也跑,同一个 batch 的 counter 可能被加 3-4 次

### 可行方案

**方案 A**:如果 `current_phase == "finalized"`,直接 `return FinalizeResult(batch_phase="finalized", ...)` 早退,**不执行任何 mutation**。需要同时输出 INFO 级日志告诉用户"已经 finalized,什么也没做"。

**方案 B(更通用)**:和 Q31 方案 A 合并 —— `apply_belief_delta` 幂等,那 finalize_batch 即使重跑也不会污染 counter。剩下的 audit entry 单独 dedupe。

**方案 C(防御性)**:finalize 时记录 `finalized_at` timestamp,重跑时检查"如果 finalized_at 和 judge_report.completed_at 的时间差 < 某个阈值,跳过",但这是启发式不如方案 A 硬。

推荐方案 A + B 组合:**数据层幂等 + 函数层早退**。

---

## Q33 — `write_reflection_md` 本身没有 header guard,guard 只在 finalizer 里

**提问时间**: 2026-04-11
**相关阶段**: Phase 3.5a + 3.5b

### 发现

`reflect.py:241-270` 的 `write_reflection_md`:

```python
def write_reflection_md(reflection_path, delta, narrative):
    reflection_path.parent.mkdir(parents=True, exist_ok=True)
    header = f"\n## Batch {delta.batch_id} — {now_ts()}\n\n"
    # ... build body_lines ...
    section = header + "".join(body_lines)
    with open(reflection_path, "a", encoding="utf-8") as f:
        f.write(section)
```

**无条件 append,没有任何"这个 batch 已经写过吗"的检查**。

guard 只在 `BatchFinalizer.finalize_batch`(步骤 5):

```python
for delta in deltas:
    reflection_path = ...
    if reflection_path.exists():
        content = reflection_path.read_text(encoding="utf-8")
        if f"## Batch {batch_id}" in content:
            continue
    narrative = _build_structural_narrative(...)
    write_reflection_md(reflection_path, delta, narrative)
```

问题:guard **只保护 3.5a 自己重跑**。3.5b 调用 `write_reflection_md` 时:
- 如果 3.5a 先跑过 → reflection.md 里已经有 `## Batch batch_103`
- 3.5b 直接 append → **出现两个 `## Batch batch_103 — timestampA` / `## Batch batch_103 — timestampB`**

### 为什么重要

1. **reflection.md 是 LLM 下一轮 idea 的主要输入**:重复 header 让 LLM 认知混乱 ——"这个 batch 是不是被 reflect 了两次?我该信哪个?"
2. **guard 位置错误**:防御逻辑应该在**数据层**(`write_reflection_md` 自己),而不是在调用方
3. 3.5b skill.md 完全没提这个 guard,LLM 自然不会主动 dedupe

### 可行方案

**方案 A(必须做)**:把 guard 下沉到 `write_reflection_md` 内部:

```python
def write_reflection_md(reflection_path, delta, narrative, mode="merge"):
    """
    mode:
      - "merge"(默认):如果 ## Batch {batch_id} 已存在,追加到同一 section 末尾
      - "skip":如果已存在,跳过整个写入
      - "overwrite":重写 section(保留其他 batch)
    """
```

**方案 B**:让 finalize 和 reflect 明确约定一个"section 结构化" schema,比如 section 内部分两块:
```
## Batch batch_103 — {ts}

### Structural(finalize 写)
...

### Narrative(reflect 写)
...
```

各自只写各自的子 section,互不干扰。

方案 B 更干净,但改动更大。方案 A 可以立刻落地。

### 关联观察

这个 bug 是 Q31、Q32 的同构表现 —— **共享写入通道但没有 handshake**。同一个病根本在:两阶段设计时没有定义"谁负责防御重复"。

---

## Q34 — `_build_structural_narrative` 只用 2/12 个 delta 字段

**提问时间**: 2026-04-11
**相关阶段**: Phase 3.5a

### 发现

`finalizer.py:249-262`:

```python
def _build_structural_narrative(delta, diagnostics):
    parts = []
    thesis = diagnostics.get("thesis_update", "")
    if thesis:
        parts.append(f"Thesis update: {thesis}")
    boundary = diagnostics.get("failure_boundary", "")
    if boundary:
        parts.append(f"Failure boundary: {boundary}")
    if not parts:
        parts.append("[Structural reflection — no detailed narrative available]")
    return "\n".join(parts)
```

`LogicBeliefDelta` 有 **18 个字段**,`_build_structural_narrative` 只消费 **2 个**(`thesis_update` + `failure_boundary`,都来自 `diagnostics`,**完全不读 delta 本身**)。

`write_reflection_md`(`reflect.py:247-267`)额外拼接了 `status_change`, `bottleneck_update`, `next_actions`, `generated/admitted` —— 合计 6 个字段。剩下 12 个(`focus_question_update`, `families_to_*`, `new_productive`, `new_failed`, `threads_*`, `ops_to_add`, `avoid_patterns_to_add`, `status_reason`)被**静默丢弃**。

更严重的是:如果 `diagnostics` 缺失(judge_report 没写 `logic_diagnostics.*`,这在很多历史 batch 里真实发生),narrative 直接是字符串 `[Structural reflection — no detailed narrative available]`。

### 为什么重要

1. **3.5a 的 reflection.md 内容质量低**:如果用户跳过 3.5b(skill.md 允许退化),reflection.md 就是一堆几乎空的占位符
2. **既然信息都在 delta 里为什么不用**:`avoid_patterns_to_add`(从 failure_boundary 解析出的具体 pattern 列表)、`new_productive`(本 batch admit 的 family)、`next_actions`(probes)都是用户最关心的 —— 却被静默丢了
3. **违反 "structural safety net" 的承诺**:finalizer.py 注释声称 step 5 是 "structural safety net,skip if already written",但实际上这个 safety net 是空气

### 可行方案

**方案 A(最小改动)**:扩充 `_build_structural_narrative` 覆盖 delta 的核心字段:

```python
def _build_structural_narrative(delta, diagnostics):
    lines = []
    if diagnostics.get("thesis_update"): lines.append(...)
    if diagnostics.get("failure_boundary"): lines.append(...)
    if delta.new_productive:
        lines.append("New productive families: " + ", ".join(e["family_id"] for e in delta.new_productive))
    if delta.new_failed:
        lines.append("New failed families: " + ", ".join(...))
    if delta.avoid_patterns_to_add:
        lines.append("Avoid patterns added:\n" + "\n".join(f"- {p}" for p in delta.avoid_patterns_to_add))
    if delta.threads_to_park:
        lines.append("Parked threads: " + ", ".join(delta.threads_to_park))
    if not lines:
        return "[Structural — no content]"
    return "\n\n".join(lines)
```

**方案 B**:`write_reflection_md` 本身就应该尽可能消费 delta —— 把这个职责下沉,`_build_structural_narrative` 只提供 "人类叙事" 部分。

这两个其实应该一起做:数据层(`write_reflection_md`)负责把 delta 翻译成结构化文本,调用方(finalizer)只补充"来自 diagnostics 的叙事增量"。

---

## Q35 — GlobalEscalation 只通过 3.5b 写入:跳过 3.5b = 跨 logic 信号永久丢失

**提问时间**: 2026-04-11
**相关阶段**: Phase 3.5a / 3.5b

### 发现

查 `finalizer.py` —— **BatchFinalizer 完全不写 `global_escalation.yaml`**。搜索一遍:

```
grep global_escalation src/research/storage/finalizer.py
# 无匹配
```

唯一写入路径是 3.5b skill 里的 `save_global_escalation(path, escalation_delta)` —— 由 LLM 驱动。

现在看 `storage/state/global_escalation.yaml` 实际数据:
- batch_001/002/038/039/040/041/042/043/044/045:`status=applied` ✓
- batch_046/047/049/050/051/052/053/054/055/056/057/058:`status=pending` ❌

**近 12 个 batch 的 escalation 全部卡在 pending**,没有被 Phase 0 消费,也没有下一步动作。

这里有两层问题:
1. **3.5b 被跳过 / 部分执行**:上面的 pending 条目说明 3.5b 生成了 escalation 但没人消费
2. **3.5b 如果完全跳过**:连 pending 都不会出现 —— escalation 信号直接不存在

### 为什么重要

1. **Phase 0 消费机制失效**:mine skill.md Phase 0 明确说"读取 `global_escalation.yaml`,筛选 `status=pending` 的条目,saturation_signal 强 → 创建新 logic;logic_proposals 非空 → 逐条 review;proposed_forbidden ≥2 batch 证据 → 正式添加"。但实际运行里这些条目**堆积**,没有"下一步动作"
2. **跨 logic 饱和信号永远触发不了**:`saturation_signal: false` 是大多数 batch 的默认值 —— 但更根本的问题是没有代码 compute 这个 signal,完全依赖 LLM 在 3.5b 里判断
3. **"finalize-batch 是最小闭环" 是错的**:闭环只闭了 logic 内,**跨 logic 的外环没闭**

### 可行方案

**方案 A(结构性)**:把 GlobalEscalation 的**机械部分**(可计算的)从 3.5b 下沉到 3.5a:
- "所有 schedulable logic 的 `rounds_without_admit ≥ 2` 且 `active_threads == 0`" → 机械可计算 → finalizer 直接写 `saturation_signal`
- "本 batch 所有 candidate 都 reject 且 reason_codes 集中度 ≥ 70%" → 机械可计算 → finalizer 直接写 `proposed_lessons`(软经验)
- "跨 logic 的 reason_codes 模式识别" → 留给 3.5b LLM

**方案 B**:把 Phase 0 的消费逻辑**也**从 LLM 下沉到 Python:
- 专门的 `consume_pending_escalations(path)` 已经存在(`reflect.py:362`),但似乎没被 Phase 0 调用
- 需要一个 `EscalationConsumer` 负责"定期扫 pending 条目,转 consumed,根据 proposed_lessons 写 research_lessons.md,根据 proposed_forbidden 触发 ForbiddenManager"

**方案 C(最小)**:给每条 pending 加一个 TTL —— 比如"超过 10 batch 仍是 pending 的 escalation 自动降级为 dismissed",防止无限堆积。这不是修根因,但至少不让数据腐烂。

这三个是叠加的。方案 A 是根因修复,方案 B 是流程修复,方案 C 是防腐。

### 关联观察

- 这与 **Q11**(proposal 落库但没消费逻辑)同构 —— 系统到处都有"写入通道但没有消费通道"
- 与 **Q2**(ledger.batch_usage 没被 judge 消费做 Bonferroni 校正)也是同构
- **Meta 观察**:"数据生产方和数据消费方没有强制匹配" 是贯穿整个系统的核心脆弱性

---

## Q36 — 3.5a / 3.5b handshake 完全缺失,两阶段重叠区是静默 bug 温床

**提问时间**: 2026-04-11
**相关阶段**: Phase 3.5a / 3.5b 交接

### 发现

两阶段设计上互补,实现上**共享三个写入函数**:
1. `apply_belief_delta(card_path, delta)`
2. `write_reflection_md(reflection_path, delta, narrative)`
3. (间接)`recompute_research_state`

但**没有任何机制标注"谁已经写过了"**:
- card.yaml 没有 `last_finalized_batch` 和 `last_reflected_batch` 分离(只有 `last_reflected_batch` 一个字段,两阶段都会覆盖它)
- reflection.md 的 header guard 只在 finalizer 内部
- state.yaml 的 `current_batch_phase` 能记 `"finalized"` 但不能区分 `"finalized_structural"` / `"finalized_enriched"`

这意味着系统**无法回答**:
- "这个 batch 是不是只跑了 3.5a?"
- "reflect 叙事被 LLM 补充过了吗,还是只是机械 narrative?"
- "counter 被 3.5b 已经加过一次了吗,所以 3.5a 重跑会污染吗?"

### 为什么重要

这是 Q31 / Q32 / Q33 的**共同根因**。修好 handshake,这三个 bug 都会退化为"不可能触发"。

更重要的是:**设计假设"3.5b 允许被跳过"但代码没有任何 fallback 机制**。如果 3.5b 真的被跳过:
- reflection.md 只有空壳(Q34)
- global_escalation.yaml 不会被更新(Q35)
- research_lessons.md 不会追加软经验
- 认知深度"弱反射"从一个声明变成现实

### 可行方案

**方案 A:引入 `BatchReflectionStamp` 数据结构**,存在 card.yaml 里:

```yaml
reflection_stamps:
  - batch_id: batch_102
    structural_applied_at: '2026-04-10T05:42:44'  # 3.5a
    enriched_applied_at: '2026-04-10T06:15:20'    # 3.5b
    counters_applied: true  # 仅 3.5a 或 3.5b 之一设 true
```

`apply_belief_delta` 根据 stamp 决定:
- 如果 counters_applied 已是 true,本次跳过 counter 更新
- 否则更新并设 true
- 其他字段(threads/families/avoid_patterns)用 merge 语义,幂等

`write_reflection_md` 接收一个 `section_type` 参数(`"structural"` / `"enriched"`):
- `structural`:写 `### Structural` 子 section 到 `## Batch XXX`
- `enriched`:写 `### Narrative` 子 section

**方案 B(更彻底):取消 3.5a 的卡写 + reflection 写,只保留 state/ledger 写**。让 3.5b 成为 card/reflection 的唯一写入者。代价:如果 3.5b 跳过,card 的 status/counters 完全不更新 —— 这与"3.5b 允许跳过"的承诺冲突。

因此必须走方案 A:**结构化 handshake**,保留两阶段互补,但把重叠区的写入语义定死。

### 这是一个贯穿性 Meta 问题

我在 Q16 / Q22 / Q26 里已经看到几次"数据结构缺字段导致静默失败"。这次 Phase 3.5 又暴露一次。**系统缺失的不是代码而是 schema** —— schema 一旦定义了"哪个字段谁写、什么时候写",代码自然不会写错。

---

## Q37 — L015 card 的 `factors_generated=2` 反直觉低,疑似 counter 未被 3.5a 正确写入

**提问时间**: 2026-04-11
**相关阶段**: Phase 3.5a counter 写入
**状态**: TODO 验证

### 发现

`storage/logic/cards/L015.yaml:100-103`:

```yaml
evidence_summary:
  factors_generated: 2
  factors_admitted: 2
  admitted_factor_ids: [F018, F019]
  rounds_without_admit: 0
```

但 L015 的实际历史(从 git log 和 batch_usage):
- batch_099:L014+L015 跑了 N 个 candidate,0 admits
- batch_100:3 candidate,0 admits(EPS breakthrough 研究)
- batch_101:2 candidate,0 admits(value-catalyst barra-clean 确认)
- batch_102:6 candidate,2 admits(F018, F019)

按 `_candidate_counts` 逻辑(`finalizer.py:280-292`)每个 batch 的 `generated` 应该是 `len(candidate_verdicts_for_this_logic)`,累计 ≈ 11+。

**但卡里只有 2**。刚好等于 `factors_admitted`。这看起来像:
1. 可能 a)前面几个 batch 的 finalize 从未被执行,3.5a 只跑过 batch_102
2. 可能 b)counter 被人为手动设置(lifecycle transition 时 reset 了)
3. 可能 c)`_candidate_counts` 有 bug,只计数 admit 的 candidate

方案 c 可以排除 —— 读了代码,`generated` 每个 candidate 都 +1。

方案 a 最可能:L015 前期(batch_099-101)的 finalize 从未正式执行,只有 batch_102 的 2 个 admit 被写入。这间接证实 Q35 说的"finalize 被跳过很常见"。

### 为什么重要

如果真的是方案 a:
- L015 所有历史候选(rejected 的 9 个)**没进 card counter**
- `rounds_without_admit` 语义实际是"自从上次 finalize 以来的 round 数",不是"自从上次 admit 以来"
- 下游依赖这个字段做调度决策的逻辑全是错的

更大的问题:**如果 counter 不可靠,调度器打分不可靠,logic schedule 推荐的"最高优先级 logic"也不可靠**。

### 可行方案

**Step 1:先验证**。写一个 `scripts/audit_counters.py`:
- 扫每个 `L0XX.yaml` 的 `factors_generated/admitted/rounds_without_admit`
- 扫 ledger 的 `batch_usage` 获取每个 logic 在每个 batch 的 candidate 数
- 对比两者,报告不匹配

如果 L015 确实只有 batch_102 的 count,其他 logic 可能也一样。

**Step 2:修复策略取决于 Step 1 发现**:
- 如果是 "finalize 跳过" 问题 → 写 reconcile 脚本从 judge_report 回填 counter(不改 schema)
- 如果是 counter 语义本来就错 → 改 schema 增加 `per_batch_counts: {batch_102: {generated: 6, admits: 2}}`,让 counter 成为派生状态

**Step 3:和 Q31 的方案 A 合并** —— 一旦 `apply_belief_delta` 变成 batch_id-aware 幂等,reconcile 也能复用这个接口。

### 关联观察

这是**历史数据腐烂**的典型。系统在运行时看起来正常(`rounds_without_admit=0` 看起来合理),但实际是"刚好因为错误路径产生了一个看起来正确的结果"。这种 bug 最难发现,需要外部数据对账才能暴露。

也呼应 Q2 的观察:"数据存进去但没人核对"。

---

## Q38 — finalizer 的 consistency check 是 soft fail,错误被静默降级为 warning

**提问时间**: 2026-04-11
**相关阶段**: Phase 3.5a 步骤 12

### 发现

`finalizer.py:167-181`:

```python
consistency_errors: list[str] = []
consistency_ok = True
try:
    checker = StorageConsistencyChecker(self._paths)
    cr = checker.check(batch_id=batch_id)
    consistency_errors = cr.errors
    consistency_ok = cr.ok
    if not cr.ok:
        for err in cr.errors:
            logger.warning("Consistency: %s", err)
except Exception as e:
    logger.warning("Consistency check failed: %s", e)
    consistency_errors = [str(e)]
    consistency_ok = False

return FinalizeResult(
    ...
    consistency_ok=consistency_ok,
    consistency_errors=consistency_errors,
    ...
)
```

两个 soft fail:
1. **consistency check 真的发现问题** → 只 `logger.warning`,函数返回成功
2. **consistency check 本身抛异常** → 只 `logger.warning`,函数返回成功

CLI 层(`state.py:151-155`)会打印 warnings,但 **finalize 仍然视为成功**,不抛 SystemExit,不阻止下一轮 mine。

### 为什么重要

1. **"最小闭环" 的定义被稀释**:finalize 声称"保证 state 和 cards 一致",但 consistency check fail 不阻止返回成功 —— 也就是说 finalize 实际不保证一致性
2. **下游永远不会停**:mine skill.md 在 autonomous 模式下继续跑下一轮 —— 下一轮读着可能已经腐烂的 state 做决策
3. **warning 在 autonomous 日志里会被淹没**:mine 模式会产生大量日志,consistency warning 没有特殊标记,很难被注意到

### 可行方案

**方案 A(推荐)**:引入 **severity 分级**:
- `consistency.CRITICAL`:schema 破坏、ID 冲突、外键失效 → `raise SystemExit`,阻塞 mine
- `consistency.HIGH`:counter 不一致、孤儿文件 → 写到 escalation,flag pending,continue
- `consistency.INFO`:可观测的弱一致性 → 只 log

**方案 B**:mine skill.md autonomous 模式显式处理 consistency warning:
- finalize 返回 `consistency_ok=false` 时,mine 主循环暂停自主运行,进入"人工 review 模式"
- 或者自动触发 `research state reconcile --report-only` 生成更详细诊断

**方案 C**:consistency check 的结果写入 `state.yaml.last_consistency_report`,下一轮 Phase 0 读取并决定是否继续。

推荐 A + C:critical 直接停,其他写入 state 让 Phase 0 看见。

### 关联观察

Q38 和 Q35 / Q36 / Q37 共享一个 Meta pattern:**系统到处是"发现问题 → 只 log 不阻塞"**。代价是长期的数据腐烂和认知漂移。

---

## Meta 观察(Phase 3.5 小结)

把 Q31-Q38 串起来,Phase 3.5 的根因只有一个:

> **两阶段设计时只定义了各自的职责,没有定义交接协议**。

具体表现:
- **没有 handshake 标志**(Q36) → 共享通道的重复写(Q31/Q32/Q33)
- **没有默认 fallback**(Q35) → 3.5b 跳过时跨 logic 信号彻底丢失
- **没有消费闭环**(Q35) → pending 条目堆积腐烂
- **没有数据对账**(Q37) → counter 不可靠但看起来正常
- **没有 severity 分级**(Q38) → 问题被降级为 warning

修复方向也只有一个:**把"两阶段写同一份数据"的重叠区变成一个结构化 schema**,让每个字段有明确的 owner 和 ownership_phase。这和 Q25(CandidateDerivations runtime 共享层)是同一个 pattern —— 都是**给模糊共享区设置 ownership**。

Phase 3.5 不适合大改(因为两阶段的设计本身是合理的),但必须补:
1. **apply_belief_delta 幂等化**(方案 A 在 Q31 / Q32)
2. **write_reflection_md 内置 guard**(Q33)
3. **structural narrative 扩充**(Q34)
4. **EscalationConsumer 机制**(Q35)
5. **reflection_stamps schema**(Q36)
6. **counter audit 脚本**(Q37)
7. **consistency severity 分级**(Q38)

这七条是一个 bundle —— 任何一条单独做都修不干净。

---

## Q39 — **[LIVE BUG, 已实证]** finalizer 的 `logic_id` 读取路径与 judge_report schema 不一致,counter/productive_families/failed_families 全部静默失败

**提问时间**: 2026-04-11
**相关阶段**: Phase 3.5a `BatchFinalizer`
**严重度**: Critical
**状态**: 已用 batch_102 + L015 真实数据验证

### 发现

走读 Phase 3.5a 时带着 batch_102 / L015 真实数据对照,发现一个静默 bug:**finalizer 读不到 candidate_verdict 的 logic_id**。

#### 证据链

**1. judge_report.yaml 的实际 schema**(`storage/batches/batch_102/judge_report.yaml`):

```yaml
candidate_verdicts:
  - candidate_id: C001
    verdict: admit
    factor_id: F018
    reason_codes: [...]
    detail: "..."
    admission_payload:           # ← logic_id 埋在这下面
      factor_id: F018
      logic_id: L015
      family_id: PF_fundamental_price_divergence
      ...
  - candidate_id: C002
    verdict: reserve             # ← reserve/reject 连 admission_payload 都没有
    reason_codes: [...]
    detail: "..."
    # 完全没有 logic_id 字段
```

`grep logic_id storage/batches/batch_102/judge_report.yaml` 的结果:
- L4  `logic_ids_in_batch:`(顶层)
- L44 `        logic_id: L015`(C001.admission_payload)
- L131 `        logic_id: L015`(C005.admission_payload)

**其他 4 个 candidate(C002/C003/C004/C006)顶层和嵌套都没有 logic_id 字段。**

**2. finalizer 的读取逻辑**(`src/research/storage/finalizer.py`):

`_candidate_counts` line 280-292:
```python
def _candidate_counts(verdicts):
    counts = {}
    for item in verdicts:
        logic_id = str(item.get("logic_id", ""))  # ← 顶层读,永远是 ""
        if not logic_id:
            continue                                # ← 全部被 skip
        slot = counts.setdefault(logic_id, {"generated": 0, "admits": 0})
        slot["generated"] += 1
        if str(item.get("verdict", "")) in {"admit", "replace"}:
            slot["admits"] += 1
    return counts
```

`_build_delta` line 335-347 里也是同样的 bug:
```python
for v in candidate_verdicts:
    if str(v.get("logic_id", "")) != logic_id:
        continue
    # 分类到 new_productive / new_failed
```

**3. 构造的 delta 长这样**(batch_102 / L015):
```python
LogicBeliefDelta(
    logic_id="L015",
    batch_id="batch_102",
    status_change="productive",        # ✓ 从 logic_recommendations 取,正常
    avoid_patterns_to_add=[...],       # ✓ 从 failure_boundary 取,正常
    next_actions=[...],                # ✓ 从 next_best_probes 取,正常
    generated_this_batch=0,            # ❌ 应是 6,因 _candidate_counts 返回空 dict
    admits_this_batch=0,               # ❌ 应是 2
    new_productive=[],                 # ❌ 应有 PF_fundamental_price_divergence × 2
    new_failed=[],                     # ❌ 应有 C006 的 reject 条目
)
```

**4. 传到 `apply_belief_delta` 后的实际写入**:

- `factors_generated += 0` → 不变
- `factors_admitted += 0` → 不变
- `productive_families` 不被追加(new_productive 空)
- `failed_families` 不被追加(new_failed 空)
- `admits_this_batch == 0` → **`rounds_without_admit += 1`**(本来应该重置为 0!)

**5. 实际 L015.yaml 里的异常状态**:

```yaml
evidence_summary:
  factors_generated: 2
  factors_admitted: 2
  admitted_factor_ids: [F018, F019]
  rounds_without_admit: 0
  productive_families: []     # ← 即使 F018/F019 都属于这个 family,仍是空
  failed_families: []
```

搜索 `admitted_factor_ids` 的写入方:
```
grep -rn "admitted_factor_ids" src/ scripts/
# (无匹配)
```

**没有任何代码写 `admitted_factor_ids` 和 `factors_admitted=2`**。这两个字段是 LLM 在 `/factor-judge` 或 `/factor-reflect` skill 里**手动编辑 card.yaml 填进去的**。LLM 察觉 Python 路径死了,自己代偿了,掩盖了 bug。

**6. Reflection.md 的 bug 指纹**(`storage/logic/reflections/L015.md` 第 210 行附近):

```markdown
## Batch batch_102 — 2026-04-10 05:42:44

**Logic**: L015
**Generated**: 0  |  **Admitted**: 0        ← 这行是 delta 的真实值
**Status change**: → productive (...)
```

`write_reflection_md`(`reflect.py:252`)直接从 `delta.generated_this_batch` 和 `delta.admits_this_batch` 拼出这行字。**0/0 就是 finalizer bug 的直接指纹** —— LLM 在 card.yaml 里能代偿(因为它能直接编辑),但 reflection.md 是 append-only 的,LLM 不会回去改,bug 留在案发现场。

batch_099 那一节也是 `Generated: 0 | Admitted: 0`,bug 从 L015 的第一个 batch 开始就存在。

### 为什么重要

1. **`rounds_without_admit` 被系统性污染**:每跑一个 batch,即使真 admit 了,finalize 都会 `+=1`。调度器(`scheduler.py:282`)读这个字段给 logic 打分 —— **调度器排序是错的**
2. **`productive_families` / `failed_families` 永远空**:这两个字段是 card 的"家族级记忆",本应用于下一轮 idea 做"这个 family 上次跑成功过/失败过"的判断。现在完全不可用
3. **LLM 代偿掩盖了症状**:L015.yaml 表面看没问题(admit/status 都对),只有深挖 reflection.md 和 git log 才能看出 Python 路径死了。这种"功能性失败但结果看起来正确"是最危险的 bug pattern
4. **Q31 的 counter 双倍风险被 bug 抵消**:现在 3.5a 加 0,如果 3.5b 加 6,结果是 6(正确)。但修好 Q39 的瞬间,3.5a 加 6 + 3.5b 加 6 = 12,**Q31 立刻复现**。必须一起修
5. **`_close_superseded_holdouts`(步骤 9)也受影响**:同一个字段读取 bug 让 (logic_id, family_id) 匹配路径失效,只剩 candidate_id 匹配能工作

### 可行方案

**P0 方案 A(最小改动,立即可做)—— finalizer fallback 读取**:

```python
def _get_logic_id(verdict: dict) -> str:
    # 顶层
    lid = verdict.get("logic_id", "")
    if lid:
        return str(lid)
    # admission_payload(admit 的 candidate 才有)
    payload = verdict.get("admission_payload", {})
    if isinstance(payload, dict) and payload.get("logic_id"):
        return str(payload["logic_id"])
    return ""

def _get_family_id(verdict: dict) -> str:
    fid = verdict.get("family_id", "")
    if fid:
        return str(fid)
    payload = verdict.get("admission_payload", {})
    if isinstance(payload, dict) and payload.get("family_id"):
        return str(payload["family_id"])
    return ""
```

但这只能修 admit 的 candidate,reserve/reject 仍然读不到。需要第二层 fallback:

**P0 方案 B(完整)—— 从 manifest 反查**:

```python
def _build_candidate_lookup(batch_id, paths):
    """Build candidate_id → {logic_id, family_id} from manifest."""
    manifest = load_yaml(paths.batch_manifest_file(batch_id))
    return {
        c["candidate_id"]: {
            "logic_id": c.get("logic_id", ""),
            "family_id": c.get("family_id", ""),
        }
        for c in manifest.get("candidates", [])
    }
```

在 `_build_delta` 开头建一次 lookup,所有地方从 lookup 读。

**P0 方案 C(根治)—— 修 `/factor-judge` skill 写 judge_report 的契约**:

每个 `candidate_verdicts[i]` 顶层必须有 `logic_id` + `family_id` + `candidate_id` + `verdict`。这些字段在 manifest 里就存在,LLM 只需复制。加一个 schema validator 在 judge 结尾检查,不满足就报错重写。

**推荐组合**:P0 方案 B(finalizer 防御)+ P0 方案 C(judge 契约)。B 防御历史数据,C 防御未来数据。

**P1 —— 验证脚本**:写 `scripts/audit_card_counters.py` 扫全部 L*.yaml,对比 ledger.batch_usage,报告 counter 和 family 字段的不一致。运行一次看看哪些 card 被污染了(目前最少 L015)。

**P2 —— consistency checker 加硬规则**:
- "`admitted_factor_ids` 非空 → `productive_families` 必须非空"
- "reflection.md 最新 section 的 `Generated=X | Admitted=Y`,X 必须等于 `ledger.batch_usage[batch].candidate_count`"

### 和之前 Q 的关系

- **Q31 counter 双倍**:真实存在,但被 Q39 遮蔽(3.5a 加 0,3.5b 如果跑会正好凑成对的)。修 Q39 必须同时修 Q31
- **Q32 finalize 非幂等**:逻辑正确,但因 Q39 counter 是 0,重跑也加 0,目前污染不出来
- **Q34 narrative 太薄**:Q39 让可用字段更少(new_productive/new_failed 空),narrative 就算想写也没数据
- **Q35 GlobalEscalation 没条目**:batch_099-102 确认全部没进 global_escalation.yaml,说明 Phase 3.5b 对 L015 这条链**根本没跑**
- **Q37(L015 counter 异常)**:升级为 Q39 已确认,factors_admitted=2 是 LLM 代偿
- **Q38 consistency soft fail**:consistency checker 看不出 Q39,因为 `productive_families=[]` 是合法空列表。需要 P2 加硬规则才能检测

### Meta 观察 —— "LLM 代偿掩盖 Python bug" 是一种反模式

Q39 暴露一个更深的 pattern:**当 Python 代码路径失效时,LLM 倾向于直接编辑文件补数据**。结果:
- **bug 不可见**:在 card.yaml 表面层 L015 数据看起来正常
- **代偿不可审计**:LLM 什么时候补了什么字段没记录
- **修 bug 反而更难**:修好 Python 路径后,LLM 的代偿会和 Python 路径**双写同一字段**,产生新的不一致

根治方向:**对 LLM 可写的字段做 schema 白名单**,超出范围的字段 LLM 不能直接写,必须通过 Python API(如 `apply_belief_delta`)。这样 LLM 代偿会变成 "API 调用" 而不是 "直接文件编辑",至少可审计。

这和 Q11(proposal 落库)/ Q22(family schema drift)/ Q26(consumer 读不到字段)是同一类 bug —— **schema 没有强制约束,两头靠自觉**。

---

## Q40 — Phase 3 `/factor-judge` 新旧逻辑差距 + Checkpoint-Driven 落地方案

**提问时间**: 2026-04-11
**相关阶段**: Phase 3 `/factor-judge`
**类型**: 架构落地方案(Q30 修正版的实现细节)

### 老逻辑现状(当前实际运行的路径)

Phase 3 设计意图:读 `judge_packet.yaml`,对每个 candidate 做 6 维度裁决,写 `judge_report.yaml` + ledger。6 维度:mechanism alignment / statistical strength / stability / redundancy / feasibility / risk model review。

**但实际运行时:**

**A. `CandidateJudge` 类是死代码**
```bash
grep -rn "CandidateJudge" src/ --include="*.py"
# src/research/judge/__init__.py:14:  from research.judge.candidate_judge import CandidateJudge
# src/research/judge/__init__.py:23:      "CandidateJudge",
# src/research/judge/candidate_judge.py:169:class CandidateJudge:
```

只有类定义和 re-export。**没有 CLI、pipeline、test、subagent 调用它的 `.judge()` 方法**。

**B. `from_judge_packet_brief` 只读 8 个字段**(`candidate_judge.py:121-137`)
```python
return cls(
    candidate_id=brief.get("candidate_id", ""),
    statistical_strength=brief.get("validation_effect_bucket", "borderline"),
    stability=brief.get("stability_bucket", "borderline"),
    redundancy=brief.get("redundancy_bucket", "acceptable"),
    feasibility=brief.get("feasibility_bucket", "ok"),
    risk_model_review=brief.get("risk_model_review_bucket", "acceptable"),
    execution_gate_passed=brief.get("execution_gate_status") == "pass",
    support_window_warning=brief.get("support_window_warning", "none"),
)
```

13 个 `CandidateEvidence` 字段里只映射 8 个。剩下 5 个全部走默认值:
- `mechanism: AlignmentEvidence` → 默认 empty,alignment 永远 "aligned"
- `sign_flip: False` → Fatal gate 永远不触发
- `expanding_window_pass: True` → High gate 永远不触发
- `known_bad_pattern: False` → Fatal gate 永远不触发
- `multiple_testing_risk_bucket: "low"` → holdout review 永远不触发

**6 个 hard gate 里有 4 个被静默 bypass**(Q29.1 已经入档)。

**C. skill.md 要求的 Python 调用实际上没发生**
`factor-judge/skill.md` Step 1 说:
> 使用 Python 工厂方法构建结构化证据 `evidence = CandidateEvidence.from_judge_packet_brief(brief)`

但没有 `research judge` CLI 命令,没有 pipeline 入口,没有 subagent 脚本。当前流程实际是:
```
judge_packet.yaml
  → LLM 读
  → LLM 按 skill.md 的 6 维规则散装判断
  → LLM 直接写 judge_report.yaml
  → guarded_writer 把 admission_payload 写进 factor registry
```

**Python 在整个裁决环节只做 I/O 和 registry 写入,不做任何 verdict 计算。**

### 老逻辑的 5 个根本问题

1. **Python hard gate 完全失效**:`from_judge_packet_brief` 不读 4 个关键字段,即使 `CandidateJudge` 被调用,hard gate 也被 bypass
2. **LLM 不被强制思考每一维**:skill.md 是"建议看 6 维",不是"必须对每一维产出可审计响应"
3. **没有 citation 约束**:LLM 写 "mechanism_aligned" 不需要举证,没有 research_lessons grep 验证
4. **Python 规则是硬编码魔数**:`CandidateJudge.judge()` 里的 fatal/high → reject 是死规则,LLM 无法在 contextual 证据下 argue
5. **"LLM 看规则自主判断"的权力不受任何约束**:可以凭感觉把 weak 升级成 admit,没机制阻止

### 新逻辑:Checkpoint-Driven LLM Architecture(Q30 修正版)

5 层设计:

**Layer 1 — Python Hard Gates(Unarguable)**
- sign_flip_detected
- execution_gate_failed
- known_bad_pattern_match(grep forbidden.yaml)
- holdout_calendar_violation
- 命中任一条,直接 reject,LLM 无权 override

**Layer 2 — Python Checkpoint Generator(Advisory)**
- 从 judge_packet + research_result 机械计算 numeric baseline
- 生成 10-15 个 Checkpoint Questions,每个包含:
  - `question` — 必须回答的问题
  - `numeric_hint` — Python baseline 读数 + advisory bucket + threshold_ref
  - `relevant_evidence` — 从 research_result 摘的具体数字
  - `citation_requirements` — 必须引用哪类 lesson
  - `what_would_change_my_mind` — 可证伪声明
  - `severity` — advisory(非 hard gate)

**Layer 3 — LLM Structured Reasoning**
- 对每个 checkpoint 产出 `CheckpointResponse`:
  - `position`: agree / override_upgrade / override_downgrade
  - `reasoning`: 必须含 citation
  - `citations`: `["research_lessons#NM-L015-pb-conditioning-reduces-ep-ratio", ...]`
  - `concerns`: 未来 batch 需要复核的条件
- `extra_checkpoints`: LLM 主动补充的角度(可选)

**Layer 4 — LLM Synthesis**
- 综合所有 checkpoint responses → 最终 verdict
- `synthesis_reasoning` 必须说明如何从 responses 推到 verdict,不能只说"综合判断是 admit"

**Layer 5 — Python Audit Wrap**
- 每个 checkpoint 都有 response(完整性)
- 每个 citation 指向真实存在的 lesson id(grep 验证)
- 每个 override 伴随合格证据
- Layer 1 hard gate 命中必须 reject
- 写入 `judge_report.yaml`,schema_version: 2

### 新旧对比表

| 维度 | 老逻辑 | 新逻辑 |
|---|---|---|
| 裁决主体 | LLM 散装判断 + CandidateJudge 死代码 | LLM 按 checkpoint 清单强制回答 + Python 审计 |
| Hard gate | 2/6 生效,4/6 被 from_judge_packet_brief 默认 bypass | 4+ 独立实现,不依赖 brief 映射 |
| LLM 权力 | 无约束,可跳维度 | 必须回答每个 checkpoint,可双向调整但必 cite |
| Python 权力 | 魔数 hardcode,LLM 无法 argue | numeric_hint 是 advisory,LLM 可 contextual override |
| Citation 机制 | 无 | 强制 grep 验证 lesson id 真实存在 |
| 可审计性 | reason_codes 扁平列表 + detail 散文 | 完整 checkpoint trail + citation + audit result |
| 可学习性 | 无 | meta-reflect 可统计 override 被 holdout 证伪的比例 |
| CandidateJudge 类 | 死 | 被 CheckpointJudge / hard_gates / checkpoint_generator 替代 |

### 落地路径(6 步)

| P | 步骤 | 依赖 |
|---|---|---|
| **P0** | 修 Q39 finalizer logic_id 读取 bug + judge_report schema 契约(每个 candidate_verdict 顶层必须有 logic_id/family_id) | 无 |
| **P1** | 新文件 `src/research/judge/hard_gates.py`:`evaluate_hard_gates()` 独立实现 4+ 个 hard gate,不走 from_judge_packet_brief | P0 |
| **P2** | 新文件 `src/research/judge/checkpoint_schema.py`:`CheckpointDefinition` / `CheckpointResponse` / `CheckpointJudgeReport` dataclass | P0 |
| **P3** | 新文件 `src/research/judge/checkpoint_generator.py`:`generate_checkpoints(brief, research_result, logic_card)` 返回 10-15 个 checkpoint | P2 |
| **P4** | 新文件 `src/research/judge/citation_auditor.py`:Layer 5 audit — 读 judge_report,grep 验证 citation,检查完整性 | P2 |
| **P5** | 新 CLI:`research judge checkpoints <batch_id>` 和 `research judge audit <batch_id>` | P3 + P4 |
| **P6** | 改 `.claude/skills/factor-judge/skill.md`,切换到 checkpoint 流程 | P5 |

**最小 MVP**:P0 + P1 + P2 + P3 + P5 的 `checkpoints` 命令(不含 audit)。让 LLM 先拿到 checkpoint 清单并按清单回答 —— 即使 citation 审计还没实现,LLM 的判断已经变得可审计。

### 新 judge_report.yaml 的 schema 样例

```yaml
judge_report:
  batch_id: batch_102
  schema_version: 2                      # 新 schema 标记

  hard_gate_results:                     # Layer 1 独立输出
    - candidate_id: C001
      gates_triggered: []                # 通过
    - candidate_id: C006
      gates_triggered:
        - gate_id: weak_effect_bonferroni
          severity: high
          evidence: "icir_val=0.083, bonferroni_threshold=0.35"

  candidate_verdicts:
    - candidate_id: C001
      logic_id: L015                     # ★ 顶层强制必有(修 Q39)
      family_id: PF_fundamental_price_divergence
      verdict: admit

      checkpoint_responses:              # Layer 3 完整 trail
        - checkpoint_id: CP01_mechanism_alignment
          position: agree
          reasoning: "Candidate rationale 明确描述 EPS abs change × low PB,对应 L015.hypothesis.condition..."
          citations:
            - logic_card.L015.hypothesis.condition
            - research_lessons#NM-L015-pb-conditioning-reduces-ep-ratio
          concerns: []

        - checkpoint_id: CP06_barra_cleanness
          position: override_upgrade
          reasoning: |
            Python 建议 borderline(style_r2=0.100),但 barra_res_icir=+0.251 显著正,
            alpha_surv=0.691 证实 Barra 移除后机制仍存在。
          citations:
            - research_lessons#NM-L015-pb-conditioning-reduces-ep-ratio
            - batch_101.judge_report#C001.style_r2=0.257
          concerns:
            - "如果未来 batch 中同类 candidate 的 alpha_surv < 0.6,需重新审视此 override"

      synthesis_reasoning: |
        5/6 checkpoint agree,1 个 override_upgrade(CP06)based on cross-batch evidence.
        Hard gates 全部通过。可以 admit。

      final_verdict: admit

      audit_result:                      # Layer 5 输出
        status: ok
        missing_checkpoints: []
        invalid_citations: []
        override_evidence_check: ok
        fatal_override_attempts: 0

      admission_payload: {...}            # 保留
```

### 新 schema 顺带修掉的 bug

- **Q39**(finalizer logic_id 读取 bug):新 schema 强制顶层 logic_id / family_id,finalizer 直接读,不再 fallback
- **Q29.1**(from_judge_packet_brief 只读 8 字段):新 schema 不再走这条路径,hard_gates 和 checkpoint_generator 各自独立读 research_result
- **Q30 原版的"Python 上限 LLM 只能 downgrade"**:被 LLM 双向调整 + 强制 citation 替代
- **Q34**(structural narrative 太薄):finalizer 的 narrative 可以直接从 checkpoint_responses 提取 reasoning,不再只读 2 个字段

### 落地后 CandidateJudge 的命运

- `CandidateJudge.judge()` 里的魔数规则(`if has_fatal → reject` / `if weak + poor stability → reject`)退化为 **checkpoint 的 numeric_hint 生成器**。规则本身还在,但不是硬执行,而是作为 Python 向 LLM 提出的"建议"
- `CandidateEvidence` dataclass 被 `CheckpointResponse` list 替代
- `from_judge_packet_brief` 删除
- skill.md Step 1-5 的"6 维度规则"改成"checkpoint 响应填写规范"

---

## Q41 — 新 judge_report schema 下 Phase 3.5a/3.5b 的分工需要重新设计

**提问时间**: 2026-04-11
**相关阶段**: Phase 3.5a / 3.5b(在 Q40 新逻辑的假设下)
**类型**: 架构含义分析

### 核心观察

老 3.5a/3.5b 分工(Python 最小闭环 + LLM 每 batch 补叙事)是**一个补丁** —— 补丁存在的原因是老 Judge 产出不够结构化(`logic_diagnostics` 是散文),导致 finalizer 机械能提取的字段有限,只能让 LLM 在 3.5b 再跑一次补叙事。

Q40 的 Checkpoint-Driven Judge 让 judge_report 变成**结构化证据 trail**(`checkpoint_responses` + `citations` + `concerns`)。一旦上游结构化了,3.5b 的 LLM 价值在"每 batch 级别"几乎为零 —— 因为机械提取已经足够。LLM 的价值应该上移到**跨 batch meta-reflect**。

### 立即受益的 bug(顺带被修)

新 schema 强制 `candidate_verdicts[i]` 顶层有 `logic_id/family_id`(Q40 P0)→ Q39(finalizer 读取 bug)直接消失 → Q31/Q32/Q34 也连带受益:
- counter 首次能真实计数,`factors_generated += 6, factors_admitted += 2`
- `productive_families / failed_families` 开始有内容
- `avoid_patterns_to_add` 从 checkpoint_responses 的 citation 直接提取,带具体表达式 + 触发原因 + lesson id
- `rounds_without_admit` 逻辑终于正确

### 新 3.5a 的扩展职责(吃掉老 3.5b 的结构化部分)

老 3.5a:
```
status / counters / avoid_patterns / next_actions(最小闭环)
```

新 3.5a:
```
- status / counters / avoid_patterns / next_actions(同老)
- 从 checkpoint_responses.reasoning 聚合 evidence_for / evidence_against
- 从 checkpoint_responses.concerns 聚合 open_questions(自动生成 "future review trigger")
- 从 citations 提取本轮引用的 lesson 列表
- 从 override_upgrade.concerns 生成 card.reflection_stamps(未来复核条件)
- thread 更新:candidate 的 checkpoint 如果命中某个 thread 的 next_probes,机械更新 supporting_evidence
- 从 checkpoint trail 机械生成结构化 reflection.md narrative(替代 _build_structural_narrative 的 2 字段老路径)
```

**所有这些都是纯 Python 机械操作**。不需要 LLM 在 3.5a 环节再写一次散文。LLM 已经在上游 Phase 3 的 checkpoint response 把话说过了,3.5a 只负责结构化提取 + 聚合到 card。

### 新 3.5b 重新定位为跨 batch meta-reflect

**老 3.5b**:每 batch 必跑,输入 1 个 batch 的 judge_report,LLM 生成 GlobalEscalationDelta。

**问题**:1 个数据点根本不足以产生 meta 结论 —— 这就是为什么 batch_099-102 的 global_escalation 全部为空(Q35)。不是 LLM 没跑,而是 LLM 被要求每 batch 跑但**没有足够证据可写**。

**新 3.5b** = `/factor-reflect-meta`,**周期性触发**(不是每 batch):

触发条件:
- `rounds_since_last_meta_reflect ≥ 10`(积累足够 checkpoint trail)
- 或 `global_escalation.pending_count ≥ 5`
- 或手动触发

输入:**所有历史 checkpoint_responses**(跨 batch / 跨 logic)

LLM 任务:
1. **Checkpoint 级 calibration**
   - 扫每个 checkpoint_id 的 override 比例
   - "CP06_barra_cleanness 过去 8 个 admit 里有 5 个是 override_upgrade" → Python baseline 可能太严,提案调整 numeric_hint 阈值
   - "CP02_statistical_strength 的 override_upgrade 有 70% 被 holdout 证伪" → LLM 在此维度过于乐观,提案降低 override 权限或要求更强 citation

2. **Citation 频率分析**
   - 最常被引用的 lesson → 提名 promotion 为硬 forbidden 或 confirmed mechanism
   - 引用但从未被反驳的 lesson → 优先纳入 checkpoint citation_requirements

3. **Concerns 跟踪**
   - `concerns` 里反复出现但从未被解决的问题 → 生成新 logic 提案
   - 例:"crowding=medium" 反复出现在 L015 的 5 个 reserve → 提议开 L016 专门研究 anti-crowding conditioner

4. **Cross-logic pattern detection**
   - 多 logic 收敛到同一失败模式 → saturation_signal
   - 某个 family 在多 logic 下都失败 → 降级 FM 注册表

输出:
- GlobalEscalationDelta(跨 logic 信号,带跨 batch 证据)
- Python numeric_hint 调整提案(写到 `research_config.checkpoint_calibration.pending`)
- 硬 forbidden 提案(带 ≥3 batch 证据链)
- 新 logic 提案(带 cross-batch concerns 聚合)
- 追加软经验到 `research_lessons.md`

### 新 3.5a/3.5b 分工对比

| 维度 | 老 3.5a | 老 3.5b | 新 3.5a | 新 3.5b (/reflect-meta) |
|---|---|---|---|---|
| 主体 | Python | LLM | Python | LLM |
| 触发 | 每 batch | 每 batch | 每 batch | 每 10 batch 或手动 |
| 输入 | 1 个 judge_report | 1 个 judge_report | 1 个 judge_report(schema v2) | 所有历史 checkpoint_responses |
| 职责 | 最小 counter/status 闭环 | 补认知叙事 + GlobalEscalation | 完整结构化闭环(吃掉老 3.5b 的 per-batch 任务) | 跨 batch calibration + 新 logic 提案 + forbidden 提案 |
| 输出文件 | card / state / ledger | card 补充 / reflection.md / global_escalation | card / state / ledger / reflection.md(结构化) | global_escalation / research_lessons / checkpoint_calibration.pending |
| 跳过代价 | 系统崩溃 | 认知弱化(当时设计,实际是字段全空) | 系统崩溃 | 长期 calibration 漂移 |

### 新 reflection.md narrative 样例(机械生成)

```markdown
## Batch batch_102 — 2026-04-10 05:42:44

**Logic**: L015
**Generated**: 6  |  **Admitted**: 2  |  **Rejected**: 1  |  **Reserved**: 3
**Status change**: active → productive

### Admitted
- **F018** (C001, PF_fundamental_price_divergence)
  - 5/6 checkpoints agree, 1 override_upgrade (CP06 barra_cleanness)
  - Override evidence: batch_101 C001 style_r2=0.257 cross-batch improvement
  - Future review trigger: 如果后续 batch 同类 candidate alpha_surv < 0.6
- **F019** (C005, PF_fundamental_price_divergence)
  - 6/6 checkpoints agree
  - Highest citation: research_lessons#NM-L015-ps-conditioning-lowest-barra-loading

### Rejected
- **C006**: hard gate weak_effect_bonferroni (icir_val=0.083 < 0.35)

### Reserved (需关注)
- C002: CP07 feasibility override_downgrade — alpha_surv=0.503 below 0.6
- C003: CP08 crowding concern — max_lib=0.052 novel but crowding=medium
- C004: CP08 crowding concern — triple product universe too narrow

### Next Actions(从 concerns 自动提取)
- 监测未来 batch 中 F018 同类的 alpha_surv
- 探索 80d lookback 减少 C004 crowding
- 验证 PS conditioning 在 120d 的稳定性

### Avoid Patterns Added
- Sub(CsRank(fundamental), CsRank(price)) — C006 CP03 citation FP-L015-sub-form

### Citations Used This Batch
- research_lessons#NM-L015-pb-conditioning-reduces-ep-ratio (7 次)
- research_lessons#NM-L015-ps-conditioning-lowest-barra-loading (4 次)
- batch_101.judge_report#C001.style_r2 (2 次)
```

每行都机械可生成,不需要 LLM 二次写作。

### 架构含义(重要)

这个重新设计折射出一个更深的原则:

> **当上游产出从"散文"变成"结构化证据",下游的 LLM 环节应该上移到更高的抽象层。**

旧架构:
```
Execute(数字) → Judge(LLM 散装判断 + 散文诊断)
              → Finalize(Python 结构化 subset,能提取的有限)
              → Reflect(LLM 每 batch 补叙事,因为 subset 不够)
```

新架构:
```
Execute(数字) → Judge(LLM 结构化 checkpoint + Python audit)
              → Finalize(Python 完整聚合,narrative 机械生成)
              → Meta-Reflect(LLM 只在跨 batch 级别做 calibration)
```

每一层 LLM 的作用都更明确:
- **Phase 3 LLM**:对具体证据做**深度判断**,被 checkpoint 规程约束
- **Meta-Reflect LLM**:对**系统级趋势**做 calibration,有足够数据点避免单点脑补

老 3.5a/3.5b 分工是补丁。修好 Judge 后,补丁可以拆。

### 追加落地步骤(在 Q40 P0-P6 基础上)

| P | 步骤 |
|---|---|
| P7 | 修 finalizer `_build_delta`:从 checkpoint_responses 聚合 evidence/concerns |
| P8 | 修 `_build_structural_narrative`:从 checkpoint trail 生成结构化 narrative(替代老 2 字段路径) |
| P9 | 修 `LogicBeliefDelta` schema:新增 `checkpoint_derived_evidence` 字段 |
| P10 | deprecate `logic_diagnostics` 字段(schema_version=1 保留老 batch 兼容) |
| P11 | 新 skill `/factor-reflect-meta`,替代老 `/factor-reflect` |
| P12 | 触发条件:`rounds_since_last_meta_reflect ≥ 10` OR `global_escalation.pending_count ≥ 5` |

**最小落地**:P0-P8 = 3.5a 独立完整闭环。P9-P12(meta-reflect)可以延后,先观察 3.5a 聚合的 checkpoint trail 是否够用。

### 与其他 Q 的对齐

- **Q30 修正版** → **Q40**(实现方案) → **Q41**(下游的连锁变化)形成完整链路
- **Q35**(GlobalEscalation 空)的根因被修:不是"LLM 没跑",而是"LLM 被要求每 batch 跑但数据不足",改成周期性触发后这个问题消失
- **Q36**(3.5a/3.5b handshake 缺失)被消除:新 3.5a 独立完成所有 per-batch 写入,3.5b 作用域不重叠
- **Q31/Q32**(counter 双倍/非幂等)仍需要 `applied_batches` 幂等保护,但风险大幅降低因为 3.5b 不再写 counter
- **Q34**(structural narrative 太薄)被新 P8 修复

> **2026-04-11 修正**:本 Q41 的 "3.5a 机械生成 reflection.md narrative"(P8)和 "删除 `logic_diagnostics`"(P10)**被 Q43 推翻**。按 Q43 的 Rule A/B 元原则:
> - reflection.md 的 narrative 不应由 finalizer 机械生成,应该**留空等 consolidation**
> - `logic_diagnostics` 不是"重复"而是"混合" —— 应该拆成 yaml(结构化引用)+ md(LLM 深度叙事)
> - 3.5b 不是"被删除",而是重新定位为 `/factor-memory-consolidate` —— LLM 周期性整理 md 记忆的阶段
>
> 详见 Q43。

---

## Q43 — Memory 架构的两条元原则(Rule A YAML / Rule B MD)+ Forbidden 应被删除

**提问时间**: 2026-04-11
**相关阶段**: 贯穿整个系统(元原则)
**类型**: 架构元原则 + 对 Q40/Q41/Q42 的反向修正

### 用户 push back 的核心

在 Q40/Q41/Q42 设计完成后,用户提出两个关键质疑:
1. **research_lessons.md 为什么要 yaml 化?md 能承载更多 nuance,是更好的 LLM 认知载体**
2. **forbidden 为什么还是 yaml?LLM 在下一步探索时需要的"方向避坑",本质是 LLM context 的一部分,不应该分离出来机械化**

这两个 push back 戳中我之前设计的系统性偏差:**下意识往 yaml 化推,过度结构化了认知层**。用户的反问让我重新审视整个 memory 架构,最终明确出两条贯穿性元原则。

### Rule A — YAML for Structured State

**用途**:Python 需要机械读写 + 有稳定 schema + 被机械消费 + 频繁增量更新的地方。

**特征**:
- Python 是主要消费者,LLM 只是偶尔读
- 有明确的 field schema
- 需要 API 保证一致性(不能裸编辑)
- 通常频繁小幅更新(每 batch / 每 verdict)

**典型例子**:
- `research_state.yaml` — current_batch / schedulable_logic_ids
- `ledger.yaml` — batch_usage / audit_log / holdout_reviews / search_ledger
- `research_config.yaml` — sample_policy / thresholds / universe
- `manifest.yaml` / `research_result.yaml` / `judge_packet.yaml` — pipeline artifacts
- `global_escalation.yaml` 的状态机部分(pending/consumed/applied)
- `card.yaml` 的结构化状态部分(status / counter / thread id+status / contract quotas)

**写入约束**:LLM 只能通过 Python API(如 `apply_belief_delta`, `LedgerStore`, `StateStore`)修改,**不能直接编辑 yaml 文件**。

### Rule B — Markdown for Deep Cognition

**用途**:LLM 深度参与 + 深度反思 + 深度理解的地方,用于让 LLM 思考、理解、认知。

**特征**:
- LLM 是主要读者 + 主要写者
- 承载叙事、nuance、类比、修辞、跨段联系
- 没有稳定 schema 的好处(schema 反而会把 nuance 挤掉)
- 周期性被**重写**而非增量 append

**典型例子**:
- `research_lessons.md` — 跨 logic 经验池
- `L015.md` — logic 的研究叙事 + 深度反思(合并老 reflection.md)
- `judge_narrative.md` — judge 的 checkpoint reasoning + 深度思考
- `idea_narrative.md` — idea 的策略决策 + 为什么选这个方向

**写入约束**:LLM 在 **consolidation 阶段**自由重写。Python 只负责持久化(读/写文件),**不解析内容**。

### 判断一个新字段/文件该进哪边

问两个问题:
1. **Python 需要机械读这个内容做决策吗?** → 是 → A
2. **LLM 是这个内容的主要思考者吗?** → 是 → B

**如果两个都是**:拆成两部分。yaml 存可机械消费的 subset(id / status / pointer),md 存 LLM 思考的本体,两者通过 id 关联。

这是老架构最大的结构性错误:**把 Python 需要的粗粒度状态和 LLM 需要的细粒度理解塞进同一个文件**,导致两边都不舒服 —— Python 无法稳定机械读(因为嵌套了散文),LLM 无法自由表达(因为被 schema 挤压)。

### Forbidden 应该被完全删除(论证)

逐条对照现有 forbidden 条目:

| 现 forbidden 条目 | 本质是什么 | 按规则应该在哪 |
|---|---|---|
| `$vwap` 字段是 0 | LLM 应该知道的事实,写了会算出 NaN(自然 fail) | **MD**(lessons 里的 "Known Data Constraints") |
| `Neg` / `SMA` 算子未注册 | LLM 应该知道的事实,写了会 KeyError(自然 fail) | **MD**(lessons 里的 "Operator Gotchas") |
| 2025+ 数据不碰 | 不是 forbidden 而是 **sample_policy 配置**,LLM 无法通过 expression 绕过 | 已在 `research_config.sample_policy` |
| no-short-side alpha | 结构性理解 | **MD**(lessons 里的 "A-Share Constraints") |
| no-market-cap proxy | LLM 理解 + risk_review 业务检查 | **MD 给 LLM 读** + **risk_review 保留业务检查**(不叫 forbidden) |

**结论**:`forbidden.yaml` / `forbidden_patterns` / `ForbiddenManager` 整套可以删掉。

**为什么"没有 Python blacklist"反而更安全**:

1. $vwap:LLM 写了 → Python 算出全 NaN → 下一轮 judge 看到 coverage=0% 直接 reject → LLM 从失败反馈学
2. Neg/SMA:LLM 写了 → probe fail(KeyError) → LLM 重写
3. 科创/北交所:universe 配置层过滤,LLM 无法干预
4. 2025+ 数据:sample_policy 配置层,LLM 无法干预

所有"LLM 可能忘了"的场景都有**自然的 fail-fast 路径**。Python blacklist 是多余护栏 —— 它存在时 LLM 会以为"只要 Python 没拦就 OK",反而剥夺了从数据反馈学习的机会。

删掉 blacklist 后三层分工清晰:
- **Python whitelist**:保证输入合法(只允许已知安全的字段/算子)
- **运行时反馈**:保证执行合理(坏字段自然算错,LLM 从 coverage/KeyError 学)
- **LLM 经验**(research_lessons.md):保证方向明智(哪些方向不值得再试)

三者**不交叉**,signal 更清晰。

### 现有文件按规则归类的审计结果

| 文件 | 现定位 | 规则 | 处理 |
|---|---|---|---|
| `research_state.yaml` | 当前 batch 状态 | **A** | 保留 |
| `ledger.yaml` | 审计/计数/batch_usage | **A** | 保留 |
| `research_config.yaml` | 系统配置 | **A** | 保留,**不放 forbidden** |
| `manifest.yaml` | 冻结的 candidate 合同 | **A** | 保留 |
| `research_result.yaml` | 评估数据 | **A** | 保留 |
| `judge_packet.yaml` | judge 输入包 | **A** | 保留 |
| `judge_report.yaml` | 裁决结果 | **混合** | **拆** → `.yaml` + `judge_narrative.md` |
| `idea_report.yaml` | 决策审计 | **混合** | **拆** → `.yaml` + `idea_narrative.md` |
| `card.yaml` | 状态 + 叙事 | **混合** | **拆** → `L*.yaml`(A) + `L*.md`(B) |
| `reflection.md` (per logic) | 研究日志 | **B** | 并入新 `L*.md`,由 LLM consolidation 管理 |
| `research_lessons.md` | 经验池 | **B** | 保留,LLM consolidation 管理 |
| `global_escalation.yaml` | 状态机 + 散文 lessons | **混合** | **拆** → 状态机 yaml 引用 research_lessons.md anchor |
| `forbidden.yaml` / `ForbiddenManager` | 硬禁令 | **删除** | 合并进 `research_lessons.md` 的 "Known Constraints" |

### 关键文件的拆分设计

#### card.yaml 拆分

```
storage/logic/cards/L015.yaml        ← Rule A
  logic_id, name, category, status, priority
  evidence_summary: {counters, families, transitions}
  deepening_threads: [{id, status, priority}]  # 只结构化字段
  contract: {direction_quota, candidate_quota, preferred_families, suggested_ops, required_fields}
  next_actions: [...]  # 纯表达式列表
  last_reflected_batch
  updated_at

storage/logic/cards/L015.md          ← Rule B(合并老 reflection.md)
  # L015 — Fundamental-Price Momentum Divergence
  
  ## Current Focus Question
  (LLM 叙事)
  
  ## Hypothesis
  condition / behavior / mechanism(叙事)
  
  ## Research Narrative
  (老 reflection.md 内容并入,LLM 整理)
  
  ## Deepening Threads
  ### T001 — ep_ratio independence
  question / why_matters / current_status / stop_condition(叙事)
  
  ## Avoid Patterns
  (从 lessons 引用的相关失败边界 + L015 特定的补充)
```

**关系**:通过 `logic_id` 关联。Python scheduler 读 yaml 打分,LLM `/idea` 读 md 拿 context。

#### judge_report 拆分

```
judge_report.yaml     ← Rule A
  batch_id, schema_version
  candidate_verdicts[].{candidate_id, logic_id, family_id, verdict}
  hard_gate_results
  batch_summary
  audit_result
  admission_payload
  route_verdicts[].verdict

judge_narrative.md    ← Rule B
  ## Batch 102 — L015 Judge Narrative
  ### C001 (F018) Admit Rationale
  5/6 checkpoints agree. CP06 override_upgrade 因为...
  (LLM 深度思考,含 checkpoint reasoning / concerns / 跨 batch 对比)
```

**Q40 的 checkpoint_responses.reasoning 落在 judge_narrative.md 而不是 yaml**。yaml 只存结构化 verdict + citation pointer + audit status。

#### idea_report 拆分(顺便修 Q1)

```
idea_report.yaml      ← Rule A
  batch_id
  strategy_decision: {deepen|broaden, chosen_logic, chosen_thread}
  probe_results[].{expr, ic_hint, verdict, freeze_status}
  candidates_frozen_count

idea_narrative.md     ← Rule B
  ## Batch 102 — L015 Idea Narrative
  ### 为什么选 deepen T001
  ### 为什么 freeze C001 而不是 C007
  (LLM 深度思考)
```

结构化部分字段少,Python 有 API 强制写 → Q1(idea_report 丢失)自然修复。叙事部分缺失只影响 LLM 阅读质量,不影响 pipeline。

#### global_escalation 拆分

```
storage/state/global_escalation.yaml   ← Rule A 状态机
  entries:
    - id: esc_batch_102_001
      status: pending
      batch_id: batch_102
      created_at, consumed_at, resolved_at
      narrative_ref: research_lessons.md#NM-L015-pb-conditioning-reduces-ep-ratio

storage/governance/research_lessons.md  ← Rule B 实际内容
  ## NM-L015-pb-conditioning-reduces-ep-ratio
  (LLM 写的叙事,不需要稳定 id,只需要 md anchor 能被引用即可)
```

### Python 层只保留 whitelist,删除 blacklist

精简后 Python 硬门只剩:
- `DSL_FIELD_WHITELIST`(`$close`, `$volume`, ... 等 12 个已知字段)
- `DSL_OPERATOR_WHITELIST`(已知注册的算子)
- `MAX_EXPRESSION_DEPTH = 10`
- `sample_policy` 的日期范围(Qlib 配置层)
- `risk_review` 的业务规则(market_cap proxy 等)

**没有任何 blacklist / forbidden 概念**。"不要做 X" 完全由 LLM 从 research_lessons.md 学。

### LLM Consolidation 阶段(新)

**定位**:`/factor-memory-consolidate` —— 不是每 batch 跑的 skill,是**周期性记忆整理阶段**。

**触发条件**(任一满足):
- 距上次 consolidation ≥ 10 batch
- `research_lessons.md` 行数 > 400
- 单个 `L*.md` 行数 > 500
- `global_escalation.yaml` 有 ≥ 3 个 pending 条目
- 手动触发

**输入**:
- 当前 `research_lessons.md` 全文
- 最近 N 个 batch 的 `judge_report.yaml` + `judge_narrative.md`
- 所有 `L*.yaml` + `L*.md`
- `global_escalation.yaml` 的 pending 条目

**LLM 任务**:**完整重写 md 文件**(不是 append):

1. **合并同类** — 跨 batch 的同一机制发现整合成一条
2. **去除被证伪的** — 标注 superseded
3. **提升反复被引用的** — soft → confirmed
4. **重组叙事** — 从按 batch 组织改为按机制族组织
5. **产 changelog** — 自然语言 diff,保存为 `research_lessons_changelog.md`
6. **更新 L*.md** — 整理每个 logic 的研究叙事

**输出**:
- 新 `research_lessons.md`(完全重写)
- 新 `L*.md` 文件(完全重写)
- `research_lessons_changelog.md`(append-only 变更历史)
- `research_lessons.md.backup.{timestamp}`(上一版备份,防止 LLM 重写出错)

**LLM 自由度**:最高。Python 只提供输入视图 + 输出落盘,内容完全由 LLM 决定。这是"让 LLM 深度参与深度反思"的核心环节。

### Q40 / Q41 / Q42 的反向修正

这个元原则改动会回过头修正前面三条 Q:

**Q40 修正**:
- `citation_requirements` 不再是"强制引用稳定 lesson id",改为 **Hint Injection + Semantic Audit**
- `checkpoint_generator` 在生成 checkpoint 时,直接从 `research_lessons.md` 摘相关段落注入 checkpoint 的 `relevant_lessons_snippet` 字段
- Layer 5 audit 从 "grep lesson id 存在性" 改为 "语义检查 LLM reasoning 是否呼应 hint snippet 关键词"
- `checkpoint_responses.reasoning` 本体落在 `judge_narrative.md`,不在 yaml
- 结果:Q40 不再依赖"lesson id 稳定性",md 可以任意重写

**Q41 修正**:
- **3.5a 不再机械生成 reflection.md narrative**(老 P8 被推翻)—— narrative 部分留空,等 consolidation
- **3.5b 不是"被删除",而是重新定位为 `/factor-memory-consolidate`** —— LLM 整理 md 记忆的阶段
- 3.5a 只负责 yaml 部分:status / counter / families / avoid_patterns 引用 / thread id 状态更新
- Python 聚合 checkpoint trail 的工作减少,因为 reasoning 本体已经在 md 里

**Q42 修正**:
- `idea_checkpoint_generator` 同样从 `research_lessons.md` 摘 hint,不强制引用 id
- `IdeaCheckpointResponse.reasoning` 落在 `idea_narrative.md`
- 整个 Idea Checkpoint 的"机械约束"只保留"每个 IC 必须有 response + 不能全是 broaden"

### 最终简化后的落地步骤

| P | 任务 | 说明 |
|---|---|---|
| **P-1** | 修 Q39(finalizer logic_id schema 契约) | 所有 yaml 路径的前置 |
| **P-2** | 删除 `ForbiddenManager` + `forbidden_patterns` + `precheck.py FORBIDDEN_PATTERNS`(保留 whitelist) | Rule B 迁移 |
| **P-3** | `$vwap` / `Neg` / `SMA` / A-share 约束 合并进 `research_lessons.md` | 成为 LLM 读的经验 |
| **P-4** | 拆 `card.yaml` → `L*.yaml` + `L*.md`(合并老 reflection.md) | Rule A/B 拆分 |
| **P-5** | 拆 `judge_report.yaml` → yaml + `judge_narrative.md` | Rule A/B 拆分 |
| **P-6** | 拆 `idea_report.yaml` → yaml + `idea_narrative.md`(顺便修 Q1) | Rule A/B 拆分 |
| **P-7** | 拆 `global_escalation.yaml` → 状态机 yaml + research_lessons.md anchor | Rule A/B 拆分 |
| **P-8** | 新阶段 `/factor-memory-consolidate` skill + 触发条件定义 | LLM 整理机制 |
| **P-9** | Q40 checkpoint hint injection 实现(从 md 摘段落) | 替代 citation grep |
| **P-10** | Q40 Layer 5 语义 audit(不再 grep id) | |
| **P-11** | Q41 3.5a finalizer 只写 yaml,narrative 部分留空 | |
| **P-12** | Q42 idea checkpoint hint injection | |

### 与前面所有 Q 的对齐总结

| Q | 在 Q43 架构下的状态 |
|---|---|
| Q1 idea_report 丢失 | 顺带修复(P-6 拆分后 yaml 部分字段少,有 API 强制) |
| Q11 proposal 落库 | 同构问题,应按相同原则拆(yaml 状态 + md 叙事) |
| Q22 family schema drift | yaml 部分只存结构化,叙事部分走 md,消除 schema 断层 |
| Q26 consumer 读不到字段 | 通过 Rule A 的 "Python API 强制一致性" 修复 |
| Q29.1 from_judge_packet_brief 只读 8 字段 | Q40 新架构已替代,不再走这条路径 |
| Q30 原版 | 被 Q30 修正版 + Q40 + Q43 共同替代 |
| Q31/Q32 counter 双倍/非幂等 | Q43 的 yaml API 幂等性要求自然解决 |
| Q33 reflection.md header 分裂 | L*.md 的唯一 writer 是 LLM consolidation,自然消除 |
| Q34 structural narrative 太薄 | 不再需要机械生成 narrative,由 consolidation 整理 |
| Q35 GlobalEscalation 空 | consolidation 触发条件修了根因 |
| Q36 3.5a/3.5b handshake 缺失 | 两阶段作用域不重叠(3.5a 写 yaml,consolidation 写 md) |
| Q37 L015 counter 异常 | Q39 修好后自然修复 |
| Q38 consistency soft fail | 仍需要单独修,但在简化架构下风险降低 |
| Q39 finalizer schema 契约 bug | P-1 首个任务修 |

### Meta 观察 —— 这次修正揭示的元教训

1. **"结构化"不是万能药**。下意识把所有数据 yaml 化,会把 LLM 认知层的 nuance 挤走
2. **不同消费者需要不同粒度**。Python 要稳定 schema,LLM 要叙事理解 —— 一个文件服务两边会同时不满足
3. **黑名单是反模式**。白名单 + 自然 fail + LLM 经验,比"Python 硬拦"更清晰
4. **记忆需要整理,不只是积累**。append-only 到最后是一堆无法使用的堆积物,周期性 LLM 重写才是认知可用的
5. **设计的"机械性"应该匹配内容的"可机械性"**。结构化状态该机械,叙事认知该自由

这也是为什么 Q43 是**元原则** —— 它不是某个具体功能的 bug 修复,而是设计决策时的判断依据。以后每当考虑"这个新字段/新文件放哪里",都应该先过 Rule A/B 的判断,而不是默认 yaml 化。

---

## Q44 — Admit / Reject 路径的完整 bug 清单 + Failure Registry 缺口

**提问时间**: 2026-04-11
**相关阶段**: Phase 3 `/factor-judge` 的写入环节 + Phase 3.5 的下游
**类型**: 代码 bug 清单 + 架构缺口

### Admit 路径代码走读(以 F018 为例)

完整路径:`/factor-judge` LLM 判 C001 admit → 调 `GuardedWriter.write()` → `_write_factor_registry()` → 写 index/detail/DB/audit。

#### 没有 CLI 入口(隐形问题)

```bash
grep -rn "GuardedWriter\|guarded_writer" src/research/cli/ --include="*.py"
# 结果:无
```

**没有 `research judge admit` 命令**,也没有 subagent 脚本把 judge_report 里的 admit verdict 转成 `GuardedWriter.write()` 调用。实际流程依赖 LLM 自己正确构造 Python 调用。admit 的"开关"没有固化到 CLI,每次跑 /factor-judge 都靠 LLM 记得调用并传对参数。

#### Q44.1 — 字段缺失只 warning 不 fail

`guarded_writer.py:227-232`:
```python
_ADMISSION_REQUIRED_FIELDS = [
    "name", "expression", "direction", "batch_id", "logic_id",
    "route_id", "family_id", "ic_mean_train", "ic_mean_validation",
    "ic_ir_validation", "monotonicity_validation", "alpha_survival_ratio",
    "max_lib_corr",
]
```

`_write_factor_registry()` line 247-254:
```python
if action == "admit":
    missing = [f for f in self._ADMISSION_REQUIRED_FIELDS if f not in payload]
    if missing:
        logger.warning("Admission payload missing fields: %s. "
                       "Detail YAML will be incomplete.", missing)
    # ★ 继续执行,没有 raise
```

**问题**:13 个必填字段里任何一个没填,admit **继续执行**,detail YAML 写入但缺字段。后续 `report.builder` 读时会拿到空值或 KeyError。应该改为 **missing → raise ValueError**。

#### Q44.2 — DB 写入用后台线程,无错误处理无监控

`guarded_writer.py:274-281`:
```python
import threading
t = threading.Thread(
    target=self._persist_factor_to_db,
    args=(factor_id, dict(payload)),
    daemon=True,
)
t.start()
logger.info("DB persistence started in background")
```

**问题**:
- `daemon=True` → 主进程退出时线程被杀。如果 admit 后立刻 `clear-batch` + 退出,**DB 写入可能被截断**
- 没有返回状态,没有重试,没有监控
- GuardedWriter 返回 "accepted" **不代表 DB 写入成功**

#### Q44.2a — factor_meta 和 factor_values 独立 try,可能半写入

`guarded_writer.py:385-413`:
```python
try:
    write_factor_meta(factor_id, ...)
except Exception as exc:
    logger.warning("factor_meta write failed: %s", exc)

if not expression:
    return

try:
    ensure_qlib_init()
    provider = DataProvider(use_cache=True)
    factor_df = provider.get_factor_values(expression, start, end)
    write_factor_values(factor_id, factor_df)
except Exception as exc:
    logger.warning("factor_values write failed: %s", exc)
```

**问题**:两个独立 try/except,meta 成功 values 失败会产生 **"DB 里有 factor_meta 记录但没有 factor_values"** 的半写入状态。没有事务、没有回滚、没有 reconcile 脚本检测。

#### Q44.3 — factor_values 重新计算 Qlib(违反 Q25 原则)

`_persist_factor_to_db:410`:
```python
factor_df = provider.get_factor_values(expression, start, end)
```

**问题**:`provider.get_factor_values()` 在后台线程里**重新跑一遍 Qlib 表达式**。Phase 2 已经算过完整 factor 值(缓存在 `storage/runtime/cache/`),这里**不复用**,每个 admit 浪费几十秒到几分钟。

这是 Q25(runtime cache)/ Q41(不重复计算)原则的直接违反。修法:admit 时从 Phase 2 缓存读取 factor_df,如果缓存过期才重算。

#### Q44.4 — `upsert_factor_entry` 无幂等保护

`registry_store.py:31-41`:
```python
def upsert_factor_entry(self, factor_id, entry):
    items = index.setdefault("factors", [])
    for i, item in enumerate(items):
        if item.get("factor_id") == factor_id:
            items[i] = {**entry, "factor_id": factor_id}  # ★ 直接覆盖
            self.save_factor_index(index)
            return
    items.append(...)
```

**问题**:如果 LLM 对同一个 `factor_id` 调用两次 admit(脑抽 / 流程被重跑),第二次**直接 overwrite**,没有"该 factor_id 已存在且 status=active 就拒绝"的检查。F018 的 `admitted_at` 会被覆盖成新时间戳,看不出异常。

#### Q44.4b — `save_factor_detail` 也直接覆盖,不归档

`registry_store.py:60-62`:
```python
def save_factor_detail(self, factor_id, data):
    data["factor_id"] = factor_id
    save_yaml(self._paths.factor_detail_file(factor_id), data)
```

没有检查旧文件存在,没有归档到 `factors/history/`。

#### Q44.5 — 没有 factor_id 冲突检查

新 admit 时完全不检查"这个 factor_id 是不是已经 active"。应该加:
```python
existing = store.load_factor_detail(factor_id)
if existing and existing.get("status") == "active":
    raise ValueError(f"Factor {factor_id} already active. Use replace instead.")
```

#### Q44.6 — family_id 缺失 silent skip

`guarded_writer.py:338-340`:
```python
family_id = payload.get("family_id", "")
if not family_id:
    return   # ★ silent skip
```

**问题**:由于 Q44.1 只 warning 不 fail,如果 admission_payload 里 `family_id` 没填,这里直接 `return`,**因子被 admit 但不属于任何 family**。后续跨 family 统计、family 饱和判断全部失真。

#### Q44.6a — FamilyRegistry 所有错误吞成 warning

`guarded_writer.py:363-364`:
```python
except Exception as exc:
    logger.warning("Family assignment failed for %s: %s", factor_id, exc)
```

family creation 失败、add_factor 失败、add_logic 失败都只 log,factor 仍然被 admit。

#### Q44.7 — `lib.replace()` 归档逻辑是文档撒谎

CLAUDE.md 里明确写:
> **lib.replace()** archives old detail YAML to `factors/history/` before overwrite

但搜代码:
```bash
grep -n "history" src/research/storage/registry_store.py
# (无匹配)
```

`guarded_writer.py:291-309` 的 replace 分支:
```python
elif action == "replace":
    old_id = payload.get("replaced_factor_id")
    if old_id:
        # 只把 old 的 status 改成 retired,没有归档
        for f in index.get("factors", []):
            if f.get("factor_id") == old_id:
                f["status"] = "retired"
        store.save_factor_index(index)
    # Reuse admit logic → save_factor_detail 直接覆盖
    request_copy = WriteRequest(action="admit", ...)
    written.extend(self._write_factor_registry(request_copy))
```

**没有任何 history 归档逻辑**。replace 直接覆盖老 YAML。

修法:要么真的加归档(推荐),要么删 CLAUDE.md 里这一行。这属于 Q1 / Q9.1 / Q14 / Q17 同类的"文档 vs 代码分裂"meta pattern。

#### Q44.8 — `search_ledger` 计数更新完全靠 LLM 手动

`/factor-judge` skill.md 里写:
```yaml
L015:
  logic_attempt_count_to_date: +N
  admitted_count_to_date: +M
  ...
```

**问题**:没有代码从 `judge_report.candidate_verdicts` 自动聚合计数。完全依赖 LLM 在 skill 流程里记得手动调用 `LedgerStore.increment_search()`,LLM 可能:
- 只调一个 section(by_logic)忘了其他两个(by_family / by_experiment_tag)
- 数错数量
- 完全忘了调

和 Q39 / Q44 其他字段同构:**数据应该被写,但依赖 LLM 代偿**。在 Q41 新架构里,这应该在 finalizer 里机械聚合。

### Reject 路径代码走读(以 C006 为例)

C006 verdict=reject,`reason_codes=[weak_validation_effect]`,`detail="ICIRval=0.083..."`。

**实际发生的事**:
1. 写到 `judge_report.yaml.candidate_verdicts[5]` 一个条目
2. LLM 手动调 `search_ledger.increment_search("by_logic", "L015", field="rejected_count_to_date")`(大概率不全)
3. **结束**

**不发生**的事:
- ❌ 不写 registry
- ❌ 不写 DB
- ❌ 不写 `storage/rejected_candidates/`(这目录不存在)
- ❌ 不自动 append 到 `research_lessons.md`
- ❌ 不自动更新 `card.contract.avoid_patterns`

**C006 的失败信息只存在于**:
1. `batch_102/manifest.yaml` — 表达式 + rationale
2. `batch_102/research_result.yaml` — 完整评估数据
3. `batch_102/judge_report.yaml` — verdict + reason_codes + detail

**就这 3 处**,全部埋在 batch 目录里。

### Q44.9 —  失败经验没有专用沉淀通道(Critical)

这是整个系统最严重的架构缺口之一,而且 Q40/Q41/Q42/Q43 都没明确处理。

**核心不对称**:
- Admit 有 `storage/registry/factors/index.yaml` + `factor_F018.yaml` 作为"成功档案"
- Reject 什么都没有。失败经验**只能靠 `/factor-reflect` LLM 手动整理**到 `card.avoid_patterns` / `research_lessons.md`

而 Q35 证据显示 batch_099-102 的 /factor-reflect 根本没跑全 —— 意味着这 4 个 batch 里**所有被 reject 的 candidate 的失败原因,在 Python 层面没有任何自动沉淀**。

### Q44.10 — 跨 batch 查"某模式为什么失败"极其困难

想问"batch_099-102 之间所有 revenue×low PB 被 reject 的原因是什么"?LLM 需要:
1. 遍历 4 个 batch 目录
2. 每个 batch 打开 `judge_report.yaml`(几百行)
3. 逐个 candidate 匹配表达式里是否含 "revenue" + "pb_ratio"
4. 手动整理 detail 字段(散文)

**没有索引,没有查询,没有"失败档案"**。research_result.yaml 累积十几 MB 散文。

对比 admit 路径:`grep factor_id storage/registry/factors/index.yaml` 一行搞定。

### 补救方案:Failure Registry(Q43 Rule A/B 原则的延伸)

按 Q43 的拆分原则:

#### Rule A 层:`storage/registry/failures/index.yaml`

Python 自动聚合的失败索引:
```yaml
failures:
  - failure_id: FR_batch_102_C006
    candidate_id: C006
    logic_id: L015
    family_id: PF_fundamental_price_divergence
    batch_id: batch_102
    expression: '...'
    verdict: reject
    verdict_timestamp: '2026-04-10T05:45:00'
    primary_reason_code: weak_validation_effect
    severity: high

    key_metrics:
      ic_mean_validation: 0.0082
      ic_ir_validation: 0.083
      ls_tstat: 1.748
      holdout_decay_ratio: 2.228

    tags:
      - mechanism: dual_metric_no_conditioning
      - lookback: 60d
      - conditioner: none

    narrative_ref: storage/registry/failures/failures_L015.md#FR_batch_102_C006
    judge_report_ref: storage/batches/batch_102/judge_report.yaml#C006
```

#### Rule B 层:`storage/registry/failures/failures_L015.md`

LLM 在 consolidation 整理的失败叙事:
```markdown
# L015 Failure Archive

## FR_batch_102_C006 — dual-metric no conditioning
**Reject reason**: ICIRval=0.083 too weak; mono_val=1.0 but ls_tstat=1.748.

**Why it failed**: 原始 EPS×Revenue 乘法无任何估值条件,纯靠乘法
信号强度。对比 C001(EPS×low PB, 0.338)和 C005(Revenue×low PS, 0.266),
这次 reject 确认 **value conditioning 对 multi-metric catalyst 是结构必需**。

**Superseded by**: 作为 control 实验,不需要再试同类无条件组合。
```

#### 自动写入路径

新 3.5a finalize 增加一步:
1. 读 `judge_report.candidate_verdicts`
2. 所有 verdict ∈ {reject, kill} 的 candidate 自动写到 `failures/index.yaml`(Python)
3. narrative_ref 留空
4. LLM `/factor-memory-consolidate` 时,看到 narrative_ref 空的 failures 生成 md 叙事

#### 查询路径(Phase 0 / Phase 1 LLM 可用)

```
"查 L015 之前 failure 里 conditioner=none 的有哪些"
→ grep failures/index.yaml tags.conditioner:none logic_id:L015
→ 拿到 FR_batch_102_C006
→ 读 failures_L015.md 看叙事
→ 生成下一轮 candidate 时自动避开
```

这彻底修 Q44.9 + Q44.10:**失败经验和成功经验享有同等的存储结构**。

### Q44 问题对应 Q43 架构下的处理

| Q44 问题 | Q43 架构下 | 处理 |
|---|---|---|
| Q44.1 字段缺失 warning | 部分修 | admission_payload 加 schema validator,missing → raise |
| Q44.2 DB 后台线程 | 不修 | 独立问题:改同步 + 重试 + 事务(或显式 async/await) |
| Q44.2a meta/values 半写入 | 不修 | 独立问题:事务保护 |
| Q44.3 重复计算 Qlib | 可修 | Q25 Runtime cache 层:admit 时从 Phase 2 cache 读 |
| Q44.4/4b 无幂等 | 可修 | Q43 Rule A Python API 幂等要求 |
| Q44.5 无冲突检查 | 可修 | admit 前检查 status=active |
| Q44.6/6a family silent skip | 可修 | family_id 进入 required_fields |
| Q44.7 replace 无归档 | 可修 | 加 history 归档 OR 删 CLAUDE.md 这一行 |
| Q44.8 search_ledger 手动 | **大修** | Q41 finalizer 机械聚合,不再依赖 LLM |
| **Q44.9 失败无沉淀通道** | **新机制** | Failure Registry(见上) |
| **Q44.10 无失败档案索引** | **新机制** | 同上 |

### 落地优先级

| P | 任务 | 理由 |
|---|---|---|
| **P-1** | Q44.1 字段缺失 raise ValueError | 最简单,立即防止不完整 detail YAML |
| **P-2** | Q44.8 finalizer 机械聚合 search_ledger | 修数据污染 |
| **P-3** | Q44.9 + Q44.10 Failure Registry schema 设计 | 修最大缺口 |
| **P-4** | Q44.3 从 Phase 2 cache 读 factor_df(Q25 的延伸) | 性能 + 一致性 |
| **P-5** | Q44.2/2a DB 事务改造 | 半写入问题 |
| **P-6** | Q44.4/4b/5 幂等保护 | 防御性 |
| **P-7** | Q44.7 要么实现 history 归档要么改 CLAUDE.md | 文档对齐 |

### Meta 观察

Q44 揭示的 pattern:**admit / reject 这对语义双生,在系统设计上被严重不对称处理了**。admit 有完整的 registry + index + DB 持久化 + audit,reject 什么都没有。

这个不对称反映了一个认知偏差:**"成功是要记住的,失败是要遗忘的"** —— 但对一个因子探索系统,**失败经验的价值和成功经验完全相等**(甚至更高,因为可以防止重复犯错)。

所以 Q44 在架构上是对 Q43 的补充:Q43 定义了"状态 vs 叙事"的拆分原则,Q44 提醒我们同样要处理"成功 vs 失败"的对称性。Failure Registry 不是"新增一个功能",是**对完整认知闭环的补齐**。

---

## Q45 — Phase 4 `/factor-report` 的完整问题清单(灾难性身份错配 + 架构缺陷)

**提问时间**: 2026-04-11
**相关阶段**: Phase 4 `/factor-report`
**严重度**: 含 Critical / High / Medium / Low 四级
**状态**: 用户决定不立即修复(未来重构),此 Q 作为问题档案

### 核心发现:F015-F019 的 vault 报告是两个因子拼凑的

实证证据:

```bash
python3 -c "
import json
for fid in ['015','016','017','018','019']:
    d = json.load(open(f'storage/evidence/vault/assets/{fid}/report_data.json'))
    f = d['factor']
    print(f'{fid}: id={f[\"id\"]}, name={f[\"name\"]}, batch={f[\"batch\"]!r}')
"
```

输出:
```
015: id='015', name='alpha053',               batch=''
016: id='016', name='alpha010',               batch=''
017: id='017', name='alpha034',               batch=''
018: id='018', name='alpha017',               batch=''
019: id='019', name='rank_ret_times_rank_vol', batch=''
```

**5 个新因子的 report_data.json 全部装着老 Alpha101 因子的数据**。F018 的 report_data 里:
- `expression: 'Mul(Mul(Rank(Rank($close,10),60)...)'` — alpha017 的纯 momentum 表达式
- `IS rank_ic = 0.0095 / OOS rank_ic = 0.0056` — 弱信号
- `Q1→Q5 ann_return: 0.149 / 0.141 / 0.135 / 0.066 / -0.172`
- `monotonicity = -1.0`(负单调)

而 F018 eps_abs_change_60d_x_low_pb 的真实指标在 `storage/registry/factors/factor_F018.yaml`:
- `ic_ir_validation: 0.338`
- `monotonicity_validation: 1.0`
- `ls_sharpe: 2.8066`

Markdown 文件 `F018_eps_abs_change_60d_x_low_pb.md` 里:
- **Frontmatter 和 KPI 表** 从 registry YAML 读 → 正确(F018 数据)
- **图表** `![[assets/018/quintile_bar.png]]` → 错误(alpha017 视觉)
- **正文叙事** 混用两个来源 → Q1→Q5 具体数字是 alpha017 的(14.9%/-17.2%),但 Sharpe 是 F018 的(2.807 vs report_data 里的 2.577)

**用户读到的是两个不同因子拼凑的误导性报告**。LLM 写的所有"经济学机制分析"(空头贡献、不对称结构、熊市防御)**是在解读 alpha017 的数字当作 F018 的含义**。

### 根因

`src/report/builder.py:528-577` `_load_factor_metadata`:

```python
detail_path = Path(self.config.registry_dir) / "factors" / f"factor_{self.factor_id}.yaml"
if detail_path.exists():
    # 读 registry
    return {...}

# Fallback: DB factor_meta
try:
    sql = "SELECT ... FROM factor_meta WHERE factor_id = %s"
    ...
    # 返回 DB 里查到的数据
```

调用链:
1. `/factor-report` skill 或某脚本用 `--factor-id 018` 调用 builder(传了纯数字,不是 F018)
2. `factor_018.yaml` **不存在**(实际文件是 `factor_F018.yaml`)
3. Fallback 走 DB `factor_meta`
4. DB 里 `factor_id='018'` 对应**老的 Alpha101 alpha017**(历史 slot)
5. 返回 alpha017 数据,builder 正常往下跑
6. **没有任何 sanity check** 验证 "我返回的 name 和 --factor-id 预期的是否一致"

### 问题清单

#### Critical(生产灾难级)

**Q45.1 — Factor ID 命名不一致导致灾难性身份错配**
- 现象:F015-F019 vault 报告全错
- 根因:调用方传纯数字 ID + builder fallback 到 DB + DB 历史记录碰撞
- 影响范围:5 个最近因子的完整报告
- 修法:
  - 统一 factor_id 格式为 `F\d{3}`,拒绝其他格式
  - 删除 DB fallback(registry YAML 是唯一 metadata 来源)
  - 或 fallback 前加 sanity check 对比 name/expression

**Q45.2 — 没有任何 sanity check**
- `_load_factor_metadata` 返回数据后不检查 "factor_id matches"
- builder 组装 report_data 后不检查 "所有 section 引用同一个 factor"
- 输出 report_data.json 后不检查 "factor.name 和 registry 一致"

**Q45.7 — LLM 基于错误数据写经济学分析**
- skill.md 要求"所有数值必须来自结构化结果,不由 LLM 编造"
- LLM 遵守了这条规则,但**结构化结果本身是错的**
- 结果是 LLM 诚实地写了一份 alpha017 的分析挂在 F018 的标题下

#### High(架构缺陷级)

**Q45.3 — Execute evidence 和 judge data 全部丢失**
- 因为 factor.batch 空,`_load_execute_evidence` 和 `_load_judge_data` 都返回 `{}`
- 导致 9 张来自 execute/judge 的图完全不生成:
  - quintile_returns_oos, style_exposure_bar, alpha_waterfall
  - support_window_ic, stability_summary, feasibility_dashboard
  - verdict_radar_6d, reason_code_bar, holdout_comparison
- available_charts 只有 14 张(skill.md 要求的 23+ 张)

**Q45.4 — `admitted_at` 在 registry 和 report_data 里是两个不同日期**
- F018.yaml: `admitted_at: 2026-04-10`
- 018/report_data.json: `admitted_at: 2026-03-25`(老 alpha017 时间)
- 两个日期都出现在同一份报告里

**Q45.6 — LLM 混用多个数据源导致数字不一致**
- `factor_F018.yaml` 里 `ls_sharpe: 2.8066`
- `018/report_data.json` 里 `ls_stats.sharpe: 2.577`(alpha017 的)
- LLM 为了补 Q45.3 的洞,从 factor_F018.yaml 额外读数据
- 结果:同一份报告里 **ls_sharpe 既是 2.807 又是 2.577**,前后不一致

**Q45.9 — Judge Verdict tier 空 report_data 但 LLM 强行写出来**
- report_data.json 里 `judge: {}` 空
- skill.md 说 "judge 数据来自 report_data.json → judge section"
- LLM 没遵守这条,**从 judge_report.yaml 自己补读**写了 Tier 2
- 文字存在,但对应的图 (verdict_radar_6d / reason_code_bar) 没生成
- 结果:文字承诺的图表读者找不到

**Q45.10 — `_load_data_from_db` 重复计算 Qlib**
- 如果 signal_artifact 不存在,builder 走 `_load_data_from_db` 重跑完整 Qlib 表达式
- Phase 2 已经算过完整 factor 值(缓存在 signal_flat.parquet)
- 再次违反 Q25 "不重复计算" 原则

#### Medium(技术债)

**Q45.5 — `renderer.py` + `templates/factor_report.html.j2` 死代码**
- `src/report/renderer.py` (71 行) + `src/report/templates/factor_report.html.j2` (1423 行) 是老 HTML 路径
- 新 Obsidian 路径完全不用 Jinja template
- `src/report/__init__.py` 注释 "deprecated but kept for backward compat"
- 没有任何代码调用,应删除

**Q45.11 — `_load_library_factors` 从 DB 读但 DB 可能半写入(Q44.2 链接)**
- uniqueness 分析需要从 DB `factor_values` 表读整个因子库
- 但 Q44.2 证明 DB 是后台异步写,可能漏 factor
- 如果新 admit 的 factor 只写了 meta 没写 values,uniqueness 分析会漏掉它
- 没有检测机制

**Q45.12 — report_data 的 IS/OOS 字段和概念对齐不清**
- report_data 里有 `is` 和 `oos`
- skill.md 要求写 "IS / Validation / Holdout" 三段
- 但 report_data 只有两段
- LLM 需要推断 oos 代表 validation 还是 holdout
- 通常读 registry YAML 的 sample_policy 推断,但 report_data 里没 policy

**Q45.13 — LLM 需要读 6 个文件,任何一个漏读都产生不一致**
- report_data.json + factor_F018.yaml + research_result.yaml + judge_report.yaml + logic_card.yaml + manifest.yaml
- 每多一个数据源就多一次"数字不一致"的风险
- Q43 Rule A 的正确设计:**builder 应该把所有 LLM 需要的数据 pack 进一个 report_data.json,LLM 只读这一个文件**

#### Low(小问题)

**Q45.14 — `Factor Library.md` 总览页靠 LLM 手动维护**
- skill.md Step 4 要求每次生成完 factor 报告更新 Factor Library 总览
- 靠 LLM 手写 append
- 大概率漏更新、格式不一致、重复添加

**Q45.15 — Asset 路径硬编码到 md**
- `![[assets/018/quintile_bar.png]]` 写进 markdown
- 如果修复身份错配重新生成,每个 md 都要手动改引用
- 没有 symlink 或抽象层

### 为什么 Phase 4 问题扎堆出现

Phase 4 是 **Python 数据 → LLM 叙事** 的翻译层,同时暴露两边弱点:

1. **Python 侧弱契约**:builder 没有严格 factor_id 契约,fallback 太宽松
2. **LLM 侧补丁行为**:为补 Python 的洞从多源读数据,制造不一致
3. **双数据源违反 Rule A**:`report_data.json` 和 `factor_F018.yaml` 理论上应该是同一个 truth,但实际让 LLM 交叉读,产生三源冲突

按 Q43 Rule A/B 原则,Phase 4 正确架构应该是:
- **builder 是唯一数据源**,把所有 LLM 需要的数字全部 pack 进 `report_data.json`
- **LLM skill 只读 report_data.json**,绝不访问其他 yaml
- **schema 契约**:`report_data.factor.id` 必须和 `--factor-id` 参数严格匹配,失败就 raise

详细新架构见 Q46。

### 状态

**用户决定不立即修复现有 015-019 的 vault 报告**(未来要重构整个 report 系统)。此 Q 作为**问题档案**保留,作为 Q46 架构设计的输入。

---

## Q46 — 新 Report 架构规范(用户需求 + 强制约束)

**提问时间**: 2026-04-11
**相关阶段**: Phase 4 `/factor-report`(重构)
**类型**: 架构规范(重构的 north star)

### 用户核心需求(原话整理)

1. **基本信息 = 上一轮 evaluate 运行的结果** — "你要想办法拿到然后分析"
   - Phase 4 必须消费 Phase 2 的 evaluate 结果,不自己重新跑
2. **每一个过程都要有图都要有数据** — 不是光写文字结论
3. **分析维度参考当前 report.builder** — 不推翻现有 6 个 analyzer,但重新组织
4. **因子值不能重复计算** — Phase 4 不能调 Qlib 重跑
5. **builder 里面的维度都要向量化** — 禁 Python for loop 做数值计算
6. **架构结构清晰明确方便人来审计** — 不是 LLM 散文拼凑,是数据驱动 + 可追溯

### 强制约束(P0 level)

按 Q43 Rule A/B 原则 + 用户需求,新 Phase 4 必须满足以下强制约束:

**Builder 层(C1-C8)**:

| # | 约束 | 违反就 raise |
|---|---|---|
| C1 | factor_id 格式严格 `F\d{3}` | ✓ |
| C2 | 不调 Qlib 重跑 factor 表达式 | ✓ |
| C3 | 不访问 DB `factor_values` 表(uniqueness 除外且必须显式 flag) | ✓ |
| C4 | 所有数值计算必须向量化(pandas/numpy) | ✓ |
| C5 | LLM 只读 `report_data.json` 一个文件 | ✓(渲染层约束) |
| C6 | 每个数字必须有 provenance(指向来源文件 + 字段路径) | ✓ |
| C7 | `report_data.factor_id == --factor-id 参数`,否则 raise | ✓ |
| C8 | 所有从 YAML 读的字段必须走 registry / research_result / judge_report,不从 DB fallback | ✓ |

**LLM 渲染层(C9-C12,2026-04-11 新增)**:

| # | 约束 | 违反就 raise |
|---|---|---|
| C9 | 每张图必须有 LLM 解读(抓特点即可,不强求三层结构),禁止光放图不解读 | ✓(skill 层校验) |
| C10 | LLM 解读必须引用 report_data 里的具体数字(带高亮),禁空话 | ✓ |
| C11 | LLM 解读的数字必须在 report_data 里存在,禁编造、禁补读其他 yaml | ✓(grep 校验) |
| C12 | Section 0 必须写全文洞察 —— 经济学逻辑 + 基于因子公式的毒舌评论,不能只放 KPI 表 | ✓(结构校验) |

### 数据流(强约束)

```
Phase 2 execute (产出 canonical 数据):
  storage/batches/{batch_id}/
    artifacts/{candidate_id}/
      signal_flat.parquet      ← 预计算的 factor 值(time × symbol)
      metadata.yaml            ← expression + sample 范围
    research_result.yaml       ← 所有 evaluate 指标(IC / Barra / support / feasibility)
    judge_packet.yaml          ← judge 输入
    judge_report.yaml          ← judge 裁决 + checkpoint trail (Q40 新 schema)
  storage/registry/factors/
    factor_F{xxx}.yaml         ← admission payload

↓

Phase 4 builder (纯消费 + 向量化):
  1. factor_id → 查 registry 拿 batch_id + candidate_id
  2. 打开 signal_artifact.parquet 拿 factor_df(NO Qlib)
  3. Layer 1: 抽 core_metrics from research_result (零计算)
  4. Layer 2: 向量化算 derived_analytics from factor_df
  5. Layer 3: 可视化 research_result 的 evaluate evidence
  6. Layer 4: 读 judge_report 的 checkpoint trail
  7. Layer 5: 从 Layer 1 机械算 composite grade
  8. Layer 6: 读 logic_card + manifest 拿 research context
  9. Layer 7: (optional) 读 Failure Registry
 10. 写 report_data.json + PNG 到 assets/F{id}/

↓

Phase 4 renderer (LLM 主讲,但数据源单一):
  LLM 只读 report_data.json 一个文件
  Section 0 写"全文洞察":经济学逻辑 + 毒舌评论(基于因子公式)+ 核心 KPI
  Section 1-7 逐图解读:每张图写"特点"(不强求三层,抓重点即可)
  禁止编造、禁止补读其他文件,所有数字从 report_data 引用
```

> **2026-04-11 修正(覆盖原版)**:之前 Q46 把 LLM 压到 "Appendix A 唯一自由区",其他部分全部"机械渲染"。这违反了 Q43 Rule B("md 是 LLM 深度参与的地方")。**报告是给人看的,人看不懂图就要看解读,解读必须 LLM 写**。
>
> 修正后的核心变化:
> 1. **Section 0 变成 "Top Insight"**:开头写全文洞察 —— 经济学逻辑 + **基于因子公式的毒舌评论** + 核心 KPI 表
> 2. **每张图必须有 LLM 解读**,但不强求"数据层/机制层/实践层"三段式 —— 说清楚**特点**就够
> 3. **删除 Appendix A**:全文洞察已经在开头,不需要尾部再写一遍
> 4. **数据粒度用选项 B**:report_data 按年/月聚合,LLM 能讲"2015 年最强"但不能讲"某一天的 spike"
> 5. **Rule A/B 边界重新明确**:`report_data.json` 是 Rule A(builder 产出的结构化 canonical 数据),`report.md` 是 Rule B(LLM 主写,但单源 + 引用 provenance)

### Report 7-Layer 架构

#### Layer 1 — Core Metrics(零计算,只读 research_result.yaml)

所有 6 维度指标**已经在 research_result.yaml 里**,builder 只做结构化提取:

| Section | 字段来源 | 显示形式 |
|---|---|---|
| Effect Strength | `evaluation.{ic_mean_train, ic_mean_val, ic_ir_train, ic_ir_val, ls_tstat, mono_val}` | KPI 表 |
| Stability | `diagnostics.{split_stability, expanding_window_pass, regime_stability, horizon_consistency}` | KPI 表 + 小 icon |
| Redundancy | `similarity.{max_lib_corr, nearest_factor_id, subspace_redundancy}` | KPI 表 + 最相近 3 个 |
| Risk Model | `risk_review.{alpha_survival, barra_residual_ic, style_r2, dominant_style, crowding_bucket}` | KPI 表 |
| Feasibility | `feasibility.{coverage, turnover, half_life, liquidity_coverage_ratio}` | KPI 表 |
| Holdout | `evaluation.{holdout_ic_mean, holdout_ic_ir, holdout_decay_ratio, holdout_mono}` | KPI 表 + 醒目高亮 |

**provenance**:每个数字记录 `source: research_result.yaml#candidate_id.evaluation.ic_ir_validation`。

#### Layer 2 — Derived Analytics(向量化,从 signal_artifact 读 factor_df)

research_result 没存但 report 需要展示的"时间序列 / 分布"数据。必须从 `signal_flat.parquet` 读 factor_df + `market_daily` 读价格,**向量化计算**,不调 Qlib。

**数据粒度:选项 B(中等聚合)** — builder 产出的时间序列数据**按年或按月聚合**,不存每日原始值:

```json
"ic_timeseries": {
    "yearly": [
      {"year": 2015, "ic_mean": 0.08, "ic_std": 0.14, "n_days": 244},
      {"year": 2016, "ic_mean": 0.02, ...},
      ...
    ],
    "monthly": [
      {"month": "2015-01", "ic_mean": 0.09, ...},
      ...
    ]
}
```

这让 LLM 能讲"==2015 年 IC 最强(0.08)==,2019 年 IC 跌到 ==-0.01==",但不能讲"2015-06-15 有个 spike"。对报告的叙事**足够用**,对 report_data.json **不会膨胀**(保持 < 500KB)。

| Section | 计算 | 向量化要求 | 图 |
|---|---|---|---|
| IC timeseries | 每日截面 Rank IC 时序 | `groupby(time).corr()` 批量 | 折线图(训练/验证分色) |
| Rolling IC | 20/60/120 日滚动 IC | `df.rolling(w).mean()` | 多窗口折线 |
| IC distribution | Rank IC 分位数 + 直方图 | `np.histogram` | 直方图 + box |
| Monthly heatmap | 年×月 IC pivot | `df.pivot_table(year, month)` | 热力图 |
| Quintile returns | 分组年化收益 + 累积净值 | `groupby(time, quintile).mean()` | 柱状图 + 累积曲线 |
| Annual quintile | 年×分组 returns | `groupby(year, quintile).sum()` | 年度热力图 |
| Long-short | L/S 策略 sharpe / drawdown / 净值 | 向量化日收益 | 净值曲线 |
| IC decay multi-h | 1/3/5/10/20 日 forward IC | `shift(h).corr()` 批量 | 折线图 |

**禁止模式**:
- ❌ Python for loop over rows
- ❌ 调 Qlib `D.features`
- ❌ 调 DB 读 factor_values(只能读 market_daily 拿价格)
- ❌ 串行 shift 算 decay(应 batch 构造一个 shifted matrix)

**向量化示例**:
```python
# 错:串行
for h in [1, 3, 5, 10, 20]:
    ic_h = compute_ic(factor_df, price_df.shift(-h))  # 5 次 loop

# 对:批量
shifted = {h: forward_returns(price_df, h) for h in [1, 3, 5, 10, 20]}
ic_by_h = pd.concat([pd.Series({h: (factor_df.corrwith(shifted[h]))}) 
                     for h in horizons])  # 一次批量
```

#### Layer 3 — Evaluate Evidence Visualization(可视化 research_result,零计算)

Phase 2 已经算好的"证据"—— Barra 回归、support windows、expanding window、holdout —— 只需要画图:

| Section | 数据来源 | 图 |
|---|---|---|
| Barra style exposures | `risk_review.style_exposures` | 风格柱状图 + R² |
| Alpha survival waterfall | `risk_review.alpha_waterfall` | Raw IC → Cap-Neutral → Residual 瀑布 |
| Support window consistency | `diagnostics.support_window_ic` | 多窗口 IC + sign 一致性 |
| Expanding window | `diagnostics.expanding_window_series` | IC 随训练窗口扩展轨迹 |
| Holdout vs Validation | `evaluation.{validation, holdout}` | 对比条形图 + decay ratio |
| Feasibility dashboard | `feasibility.*` | 各项绿灯/红灯 |

这一层**完全没有计算**,只是把 research_result 里的数组画成图。如果 Phase 2 没算某个字段,图就不生成(`available_charts` 不包含)。

#### Layer 4 — Judge Verdict Trail(Q40 新 schema 下)

读 `judge_report.yaml`(Q40 的 schema_version: 2)拿完整 checkpoint trail:

```
judge_report.candidate_verdicts[F018]:
  hard_gate_results: [gate 通过 / 拦截]
  checkpoint_responses: [CP01-CP15 的完整 reasoning + citations]
  synthesis_reasoning: "..."
  audit_result: {...}
  final_verdict: admit
```

渲染:
- Hard Gate 表格(每 gate 一行,通过/拦截 icon + evidence)
- Checkpoint 卡片(每 checkpoint 一个,展示 question / numeric_hint / LLM position / reasoning / citations)
- Synthesis 段落(LLM 写的综合判断)
- Audit panel(Python audit 结果)

**这是新逻辑下整个报告最有信息量的部分** —— 读者能看到"为什么 admit",不只是"admit"。

#### Layer 5 — Composite Grade(机械合成,不是 LLM 评)

从 Layer 1 的 core_metrics 机械算 7 维度评分 + 综合 grade(S/A/B/C/D):

```python
# 公式固定,版本化
dimensions = {
    "effect":       score_effect(ic_ir_val, ls_tstat),
    "stability":    score_stability(split, expanding, regime),
    "profitability":score_profit(ls_sharpe, alpha_surv),
    "monotonicity": score_mono(mono_val, mono_ho),
    "oos_robust":   score_oos(decay_ratio, holdout_ic_ir),
    "uniqueness":   score_uniq(max_lib_corr, subspace),
    "feasibility":  score_feas(coverage, turnover, half_life),
}
total = weighted_sum(dimensions, weights)  # 固定权重
grade = grade_curve(total)
```

**关键**:LLM 不参与评分。公式和权重版本化(`formula_version: v2`)。雷达图展示 7 维。

#### Layer 6 — Research Context(读 logic + manifest + family)

- `logic_card.hypothesis` — 这个 factor 对应的 logic 是什么假设
- `manifest.candidates[cid].rationale` — 这个 candidate 是为什么设计的
- `manifest.candidates[cid].lineage` — parent_expression / transformation
- `experiment_lineage_tag` — 跨 batch 追溯同一条实验线
- `family_registry[family_id]` — 同 family 的其他 factor

展示:
- 假设卡片
- Route 类型(genesis/mutate/decorrelate/crossover)+ 选择理由
- Lineage 树(如果有 parent)
- Family siblings 表

#### Layer 7 — Failure Registry Cross-Reference(可选,Q44.9 落地后)

读 `failures/index.yaml` 找相关失败案例:

- 同 family 的 failure
- 类似机制的 reject candidate
- 本 candidate 触发过的 concern

展示:
- "本 family 已知陷阱" 表
- "类似机制失败案例" 链接

这一层**只在 Q44.9 Failure Registry 落地后才存在**,老数据没这部分。

### `report_data.json` 新 schema(canonical)

```json
{
  "schema_version": 2,
  "factor_id": "F018",
  "factor_name": "eps_abs_change_60d_x_low_pb",
  "batch_id": "batch_102",
  "candidate_id": "C001_102",
  "generated_at": "2026-04-11T...",

  "provenance": {
    "signal_artifact": "storage/batches/batch_102/artifacts/C001_102/signal_flat.parquet",
    "research_result_ref": "storage/batches/batch_102/research_result.yaml#C001",
    "judge_report_ref": "storage/batches/batch_102/judge_report.yaml#C001",
    "registry_ref": "storage/registry/factors/factor_F018.yaml",
    "manifest_ref": "storage/batches/batch_102/manifest.yaml#C001",
    "logic_card_ref": "storage/logic/cards/L015.yaml"
  },

  "layer1_core_metrics": {
    "effect": {
      "ic_mean_train": 0.041, "source": "research_result#C001.evaluation.ic_mean_train",
      "ic_ir_validation": 0.338, "source": "research_result#C001.evaluation.ic_ir_validation",
      ...
    },
    "stability": {...},
    "redundancy": {...},
    "risk": {...},
    "feasibility": {...},
    "holdout": {...}
  },

  "layer2_derived_analytics": {
    "ic_timeseries": {
      "data": [{"date": "...", "ic": 0.03}, ...],
      "computed_from": "signal_flat.parquet + market_daily",
      "method": "daily_cross_sectional_rank_ic_vectorized"
    },
    "rolling_ic": {...},
    "ic_distribution": {...},
    "monthly_heatmap": {...},
    "quintile_returns": {...},
    "annual_quintile": {...},
    "long_short": {...},
    "ic_decay": {...}
  },

  "layer3_evaluate_evidence": {
    "barra_exposures": {...},
    "alpha_waterfall": {...},
    "support_windows": {...},
    "expanding_window": {...},
    "holdout_vs_validation": {...},
    "feasibility_dashboard": {...}
  },

  "layer4_judge_trail": {
    "hard_gate_results": [...],
    "checkpoint_responses": [...],
    "synthesis_reasoning": "...",
    "audit_result": {...},
    "final_verdict": "admit"
  },

  "layer5_composite": {
    "grade": "B",
    "total_score": 78.3,
    "dimensions": [
      {"name": "effect", "score": 82, "grade": "A", "formula_version": "v2"},
      ...
    ],
    "formula_version": "v2"
  },

  "layer6_research_context": {
    "hypothesis": {...},
    "route": {...},
    "lineage": {...},
    "family_siblings": [...]
  },

  "layer7_failure_context": {
    "related_failures": [...],
    "known_traps": [...]
  },

  "charts": {
    "ic_timeseries": "F018/ic_timeseries.png",
    "rolling_ic": "F018/rolling_ic.png",
    ...
  },
  "available_charts": [...]
}
```

**关键点**:
- 每个 layer 是独立 section
- 每个 layer 内每个数字有 `source` 字段(provenance)
- 渲染层通过 provenance 可以给用户一个 "点击数字 → 看原始文件" 的审计路径
- charts 是字典(name → 相对路径),available_charts 是实际生成成功的 subset

### Markdown 渲染模板(LLM 主写,单一数据源)

```markdown
---
factor_id: F018
name: eps_abs_change_60d_x_low_pb
expression: "Mul(CsRank(Sub(Div($close,$pe_ratio),Div(Ref($close,60),Ref($pe_ratio,60)))),CsRank(Mul($pb_ratio,-1)))"
verdict: admit
grade: B
...frontmatter from Layer 1...
provenance:
  signal_artifact: storage/batches/batch_102/artifacts/C001_102/signal_flat.parquet
  research_result: storage/batches/batch_102/research_result.yaml#C001
  judge_report:    storage/batches/batch_102/judge_report.yaml#C001
  registry:        storage/registry/factors/factor_F018.yaml
schema_version: 2
---

# F018 — eps_abs_change_60d_x_low_pb

## Section 0 — Top Insight(全文核心洞察)

> [!success] Verdict: ADMIT | Grade: ==B==

### 经济学逻辑
<LLM 2-3 段基于因子公式的经济学解读:
 1. 这个公式在捕捉什么市场现象(CsRank(Sub(Div($close,$pe_ratio),Div(Ref($close,60),Ref($pe_ratio,60))))
    本质上是 60 日 EPS 绝对变化;CsRank(Mul($pb_ratio,-1)) 是低 PB 排名;两者相乘是"价值
    催化" —— 基本面改善 × 估值便宜);
 2. 为什么能产生 alpha(A 股市场的估值修复机制 + 机构识别基本面拐点的信息优势);
 3. 为什么不被套利(PB 的会计异质性 + 小盘价值股的流动性溢价)。>

### 毒舌评论(基于因子公式)
<LLM 1-2 段针对公式本身的尖锐点评:
 - 看出公式的**结构缺陷**(比如"`Div($close,$pe_ratio)` 实际上等于 `close / (close/eps) = eps`,
   所以这个"改善"其实就是 EPS 绝对变化,但用了一个绕弯的写法,可能不是故意的" —— 结构
   异味)
 - 或**结构巧思**("把 PB 作为 conditioner 而不是主维度 —— 避免了 F018 前身的 ep_ratio 陷阱,
   这是 L015 真正的突破点")
 - 诚实指出**可能的伪成功**("绝对 EPS 变化没有归一化,意味着信号偏好大市值股票,验证期的
   alpha_surv=0.691 可能部分是 size premium")>

### 核心指标
| Metric | In-Sample | Validation | Holdout |
|---|---|---|---|
| Rank IC Mean | ==0.041== | ==0.046== | ==0.038== |
| Rank ICIR | ==0.453== | ==0.338== | ==0.242== |
| Monotonicity | — | ==1.0 (perfect)== | ==0.7== |
| LS t-stat | — | ==3.89== | ==0.39== |
| Alpha Survival | — | ==0.691== | — |
| Style R² | — | ==0.100== | — |

![[assets/F018/radar.png|500]]

> [!tip] 一句话判断
> 价值催化机制已验证:PB 条件换 PE 后 style_r2 从 0.257 压到 0.100,barra_res_icir=+0.251 
> 确认剥风格后仍有 alpha。holdout decay=0.819 信号持续,但 ls_tstat_ho=0.39 说明
> 多空层面 holdout 较弱 —— 验证期强度主要来自 IC,不是分组 spread。

---

## Section 1 — 6 维度核心指标

> [!abstract] 指标总览
> <LLM 1-2 段跨维度分析:哪个维度最强?最弱?木桶效应?>

### 1.1 Effect Strength
| 字段 | IS | Validation | 来源 |
|---|---|---|---|
| IC Mean | 0.041 | 0.046 | research_result#C001.evaluation.ic_mean_* |
| ICIR | 0.453 | 0.338 | research_result#C001.evaluation.ic_ir_* |
| LS t-stat | — | 3.89 | research_result#C001.evaluation.ls_tstat |
| Mono | — | 1.0 | research_result#C001.evaluation.monotonicity_validation |

<LLM 1 段解读:这几个数字意味着什么,跨 IS/Val 的衰减或增强说明了什么>

### 1.2 Stability
<KPI 表 + LLM 1 段解读>

### 1.3 Redundancy
<KPI 表 + LLM 1 段解读(重点:max_lib_corr 和最相近因子)>

### 1.4 Risk Model
<KPI 表 + LLM 1 段解读(重点:style_r2, alpha_surv, barra_residual_ic, dominant_style)>

### 1.5 Feasibility
<KPI 表 + LLM 1 段解读>

### 1.6 Holdout
<KPI 表 + LLM 1 段解读(重点:decay_ratio,是否跨越 2024 年)>

---

## Section 2 — Derived Analytics(逐图解读,抓特点)

### 2.1 IC 时序

![[assets/F018/ic_timeseries.png|600]]

**特点**:<LLM 2-4 句话,说清楚:
 - 图的核心形态(训练期/验证期的斜率差异、有没有明显拐点、2018/2020/2022 这些关键年份表现)
 - 引用 1-2 个具体数字(比如 ==最高年 IC=0.08 在 2015==, ==最低 -0.01 在 2019==)
 - 一句经济含义或决策启示
不强求三层结构,核心是让读者快速抓住"这张图想说什么"。>

### 2.2 Rolling IC

![[assets/F018/rolling_ic.png|600]]

**特点**:<同上模板>

### 2.3 IC 分布 / 2.4 Monthly Heatmap / 2.5 Quintile Bar / 2.6 Cumulative Returns / 2.7 Long-Short / 2.8 IC Decay

<每张图一小节,同上模板>

---

## Section 3 — Evaluate Evidence(Phase 2 证据可视化)

### 3.1 Barra 风格暴露

![[assets/F018/style_exposure_bar.png|600]]

**特点**:<LLM 2-4 句抓重点 —— 哪个风格暴露最大?R² 说明了什么?剥掉风格后的 residual IC?>

### 3.2 Alpha Survival Waterfall
### 3.3 Support Window 一致性
### 3.4 Expanding Window
### 3.5 Holdout vs Validation
### 3.6 Feasibility Dashboard

<每张图 1 小节,抓特点>

---

## Section 4 — Judge Verdict Trail(Q40 新 schema)

### 4.1 Hard Gate Results
| Gate | 状态 | Evidence |
|---|---|---|
| execution_gate | ✓ pass | ... |
| sign_flip | ✓ pass | mono_val=1.0 |
| known_bad_pattern | ✓ pass | no forbidden pattern |

### 4.2 Checkpoint Responses
<每个 checkpoint 一个卡片:
  - Python 的 numeric_hint(baseline 建议)
  - LLM 的 position(agree / override_upgrade / override_downgrade)
  - LLM 的 reasoning(从 judge_report 直接取)
  - citations(reference 的 research_lessons 或历史 batch)
LLM 在这里做"翻译" —— 把 checkpoint trail 里的结构化数据换成人能读的段落,
不是二次创作。>

### 4.3 Synthesis Reasoning
<LLM 从 judge_report.synthesis_reasoning 取,格式化展示>

### 4.4 Audit Result
<Python Layer 5 audit 结果:citation 真实性 ✓ / override 合理性 ✓>

---

## Section 5 — Composite Grade

![[assets/F018/radar.png|500]]

| 维度 | 得分 | 等级 | 解读 |
|---|---|---|---|
| Predictive Power | 82 | A | <LLM 一句话> |
| Signal Stability | 75 | B | <LLM 一句话> |
| Profitability | 70 | B | <LLM 一句话> |
| Monotonicity | 85 | A | <LLM 一句话> |
| OOS Robustness | 72 | B | <LLM 一句话> |
| Uniqueness | 78 | B | <LLM 一句话> |
| Decay Resistance | 68 | B | <LLM 一句话> |

<LLM 1-2 段:最强维度 / 最弱维度 / 木桶效应>

---

## Section 6 — Research Context

### Hypothesis
<从 logic_card.hypothesis 格式化>

### Route 选择理由
<从 manifest.candidates[C001].rationale + implementation_reason 格式化>

### Lineage
<parent_expression → transformation → this factor 的追溯链>

### Family Siblings
<同 family 的其他 factor 表格(F019 revenue_change_60d_x_low_ps 是同期 sibling)>

---

## Section 7 — Known Failures & Traps(optional,来自 Failure Registry)

<如果 Failure Registry 落地(Q44.9),LLM 在这里写:
 - 同 family 的历史失败案例
 - 这个 factor 有没有踩过陷阱
 - 未来需要监测的风险点>

---

## Appendix — Provenance

| Section | 数据源 | 字段路径 |
|---|---|---|
| Section 1 Effect | research_result.yaml | #C001.evaluation.ic_ir_validation |
| Section 1 Risk | research_result.yaml | #C001.risk_review.style_r_squared |
| Section 2 IC timeseries | signal_flat.parquet + market_daily | derived, vectorized |
| Section 4 Checkpoints | judge_report.yaml | #C001.checkpoint_responses |
| ... | ... | ... |

%%Report generated: <date>. All numbers trace to provenance table above.%%
```

**这个模板的核心定位**:
- **Section 0 Top Insight 是读者第一眼看的地方**,必须承载全文最核心的判断 —— 经济学逻辑 + 毒舌评论(基于因子公式,不是基于指标)+ 核心 KPI 一屏看完
- **Section 1-7 的每张图都有 LLM 解读**,但写作要求是 **"抓特点"** —— 2-4 句说清楚图在讲什么,不强求"数据/机制/实践"三层式
- **LLM 只读 `report_data.json` 一个文件**,禁编造禁补读
- **每个数字可追溯 provenance**,审计友好
- **没有 Appendix A**(经济机制解读已经在 Section 0 了,不要重复)

### 删除的东西

重构时应该**删除**以下内容:

1. `src/report/renderer.py` + `src/report/templates/factor_report.html.j2` — 死代码(Q45.5)
2. `ReportDataBuilder._load_data_from_db` 的 Qlib fallback — 违反 Q25 + Q46 C2
3. `ReportDataBuilder._load_factor_metadata` 的 DB fallback — 违反 Q46 C8
4. `ReportDataBuilder._load_library_factors` 的 DB 读取 — 违反 Q46 C3(uniqueness 换成读 signal_artifact 目录)
5. 现有 `/factor-report` skill.md 的 "LLM 读 6 个文件" 模式 — 违反 Q46 C5
6. `Factor Library.md` 的 LLM 手动维护模式 — 改成 builder 自动生成

### 保留并改造

1. **6 个 analyzer**(IC / Profit / Decay / Uniqueness + execute_evidence_charts + judge_charts)的**计算逻辑**保留
2. 但它们的**数据源**必须改为:
   - IC/Profit/Decay → 从 signal_artifact.parquet 读 factor_df,不调 Qlib
   - Uniqueness → 从同目录的其他 signal_artifact 读(factors/index.yaml 列出所有 active factor 的 artifact 路径)
   - execute_evidence_charts → 保持读 research_result.yaml(本来就正确)
   - judge_charts → 改读 Q40 新 schema 的 checkpoint_responses

### 实施优先级

| P | 任务 | 依赖 |
|---|---|---|
| **P-1** | 统一 factor_id 格式为 `F\d{3}`,builder 拒绝其他格式 | 无 |
| **P-2** | 删除 `_load_factor_metadata` 的 DB fallback | P-1 |
| **P-3** | 删除 `_load_data_from_db`,改为强制从 signal_artifact 读 | Phase 2 保证 signal_artifact 被写 |
| **P-4** | 定义 `report_data.json` schema_version: 2 的 dataclass | 无 |
| **P-5** | 改写 6 个 analyzer 为严格向量化 + 从 factor_df 读 | P-3 |
| **P-6** | 加入 provenance 追踪(每个数字带 source) | P-4 |
| **P-7** | 删除死代码 renderer.py + templates | 无 |
| **P-8** | 改写 `/factor-report` skill 为固定模板渲染 + LLM 仅写 Appendix A | P-4, P-6 |
| **P-9** | 加 Layer 7 Failure Registry 引用 | Q44.9 落地 |
| **P-10** | 加 Section 4 Judge Trail 展示 | Q40 落地 |

### 这一 Q 的 meta 意义

Q46 是整个 Phase 4 重构的 **spec**。它明确了:

1. **数据所有权**:builder 是唯一 ETL 层,pack 所有 LLM 需要的数据进 report_data.json
2. **计算原则**:Phase 2 已算的必须被消费,只有新的衍生分析可以向量化重算,不允许任何 Qlib/DB 重算
3. **审计优先**:结构固定 + 每数字 provenance + LLM 自由度被限制在 Appendix A
4. **层次清晰**:7 layer 每层职责独立,易于人类审计

和 Q43(memory 架构 Rule A/B)对齐:Layer 1-6 是 Rule A(结构化),Appendix A 是 Rule B(LLM 深度参与)。整个 Phase 4 遵守同一元原则。

和 Q40(checkpoint-driven judge)对齐:Layer 4 直接展示 judge 的 checkpoint trail,让"为什么 admit"可审计。

和 Q44(failure registry)对齐:Layer 7 引用失败档案,让"同类 candidate 历史表现"可审计。

Q46 本质上是 **Q40 + Q43 + Q44 在 Phase 4 层的应用**,不是独立的新设计。它的价值是把这三个元原则在 report 层面具体化成一个可实施的 spec。

---






