---
name: factor-judge
description: Phase 3 JUDGE — per-candidate deep analysis + batch summary, rubric-driven, bidirectional-linked knowledge graph
user_invocable: true
---

# /factor-judge — Phase 3 判决

## 核心架构

**一候选 = 一 markdown**。每个 candidate 产出 `batches/{batch_id}/candidates/C{id}.md`（深度 6 CP 分析）。batch 层面的 `judge.md` 做汇总 + 跨候选反思 + 方向级洞察。所有文件用 vault-root 相对 wikilink 互连，形成可导航的知识图。

```
result.yaml  ──(Python 预载)──▶  _hints.yaml（rubric 数值 + 每 gate 独立结果 + MT budget + nearest expression）
                                        │
                                        ▼
                             (并行 subagents 各写一个 C{id}.md — 只读 hints 自己那块 + direction + 近邻 factor)
                                        │
                                        ▼
                             candidates/C001.md  C002.md  ...
                                        │
                                        ▼
                        (主 agent 汇总 + 跨候选反思 → 写 judge.md)
                                        │
                                        ▼
                   (主 agent 更新 direction.md body + INDEX.md 方向条目)
                                        │
                                        ▼
                          Python audit (16 checks) → Pass
```

**数据边界（重要）**：
- `result.yaml` 所有被 rubric 用到的字段都已经被 Python 预载进 `_hints.yaml.per_candidate.{id}.metrics`，subagent **不读 result.yaml**
- `factors/{nearest}.yaml` 的 `expression` 也已被 Python 预载到 `metrics.cp05.nearest_factor_expression`
- `hard_gate.gate_results` 展示 8 项 gate 每一个的 value + threshold + passed，即使全过也详尽列出
- subagent 只读：`candidate-rubric.md`（本目录同级）+ 自己在 hints 里那块 + `direction.md`（CP02 用）+ 可选读 `factors/{nearest}.md`（CP02 近邻机制叙事）
- subagent **不读**：父 `skill.md`、`result.yaml`、`lessons.md`

## 职责分工

| 角色 | 职责 |
|---|---|
| **Python CLI** | (1) 扫历史 batches + 跑 hard gates + 算 MT + 扁平化 rubric 数值 + 解析 nearest expression → 写 `_hints.yaml`。(2) 批量审计 `candidates/*.md` + `judge.md` + `directions/{dir}.md` + `INDEX.md` 共 16 项结构 |
| **主 agent (你)** | (a) 并行派发 subagent (b) 收集 subagent 返回的 verdict (c) 写 `judge.md` 汇总 + 跨候选反思 + 方向级洞察 (d) 更新 `direction.md` body (e) 更新 `INDEX.md` 上半段方向条目 |
| **Subagent (并行)** | 按 `candidate-rubric.md` 对单个候选做 6 CP 推理，写 `candidates/C{id}.md`，返回短 verdict 摘要 |

## 完整工作流程

### Step 1 — Python: 写 `_hints.yaml`

```bash
PYTHONPATH=src python3 -m research judge batch_{N} pre-hint
```

产出 `storage/vault/batches/batch_{N}/_hints.yaml`（rubric 数值 + gate_results + MT + nearest expression）。

### Step 2 — 主 agent: 读批次级文件

主 agent Read 以下文件以获得全局视角：
- `storage/vault/batches/batch_{N}/_hints.yaml`（全部内容——批次级 `mt_counts` + 每候选 hard_gate/metrics 一览）
- `storage/vault/directions/{direction}.md`（hypothesis + 活跃 threads）

注意：主 agent **不读 `result.yaml`**（数值都在 hints 里）。`lessons.md` 也不需要（是 Phase 1 设计阶段的资料）。

### Step 3 — 主 agent: 并行派发 subagents

对每个 candidate_id 启动一个 subagent（Agent 工具，`subagent_type=general-purpose`），在**单条消息**里同时 call 多个以实现并行。

#### Subagent 调用 prompt（中文，逐字拷贝，替换 `{...}` 占位符）

```
你是子代理，负责判决候选因子 {CID}（来自 {BATCH_ID}，方向 `{DIRECTION}`）。
产出：在 storage/vault/batches/{BATCH_ID}/candidates/{CID}.md 写**一份**文件。
不要写其它文件、不要跑 Bash。

## 读这些文件（按顺序）

1. .claude/skills/factor-judge/candidate-rubric.md —— 你的判决手册，
   含 6 个 checkpoint 的 rubric 表 + C{id}.md 模板 + 自我校验清单。完整读完。
2. storage/vault/batches/{BATCH_ID}/_hints.yaml —— 定位 per_candidate.{CID}
   这一整块。里面有：
   - expression / coverage
   - hard_gate.passed + gate_results（8 项 gate 各自 value + threshold + passed）
   - mt_budget（仅 passed 才有）
   - metrics.cp03/cp04/cp05/cp06 —— 所有 rubric 用到的数值已扁平化
     （包括 nearest_factor_id 和 nearest_factor_expression）
3. storage/vault/directions/{DIRECTION}.md —— hypothesis 段 + 活跃 threads。
   CP02 第 2 问要引用 `[[directions/{DIRECTION}#Hypothesis]]`。
4. （可选）storage/vault/factors/{nearest_factor_id}.md —— 仅当你要写
   深度近邻机制对比时读。expression 已经在 hints 里，简单对比不用读。

**不要读**：result.yaml、lessons.md、父 skill.md。所有数值都在 hints 里。

## 写 candidates/{CID}.md

严格按 candidate-rubric.md 的模板写。每个 CP 的档位词必须是 rubric 列出的
那些词之一。每个数值引用都要给出具体数字。

## 写完前自我校验（audit 会查）

- frontmatter 齐全；candidate_id 与文件名一致
- verdict ∈ {admit, reserve, reject}；admit 时 factor_id = null
- thread_id 指向 direction.md 真实存在的 `### T{n}` H3
- CP03 body 包含 literal 字符串 `mt_bucket` 和 `search_adjusted`
- CP02 body 含 `[[directions/{DIRECTION}` 开头的 wikilink
- 每个 CP{2..6} body 含该 CP 的一个 rubric 档位词
- 所有 wikilink 用 vault-root 形式（`[[factors/F005]]`），禁止 `../` 前缀
- 非-reject 有 key_metrics_short，reject 有 reject_reason_short

## 返回给主 agent（结构化一段，不是一行，不返回整份 md）

用下面这个固定模板返回——主 agent 会把这段直接拼进 judge.md 的候选一览表
+ 跨候选对比段，所以需要足够素材。**所有数值都从 hints.metrics 里抄**，不要自己算。

```
【{CID}】verdict = {admit|reserve|reject}  |  expr = {expression}

档位: CP02={aligned|mixed|misaligned} · CP03={strong|borderline|weak} · CP04={good|acceptable|borderline|poor} · CP05={low|medium|high} · CP06={stable|mixed|unstable}

指标:
  CP03  ic_oos={} icir_oos={} ls_t={} | ic_is={} ls_sharpe={}
  CP04  style_r²={} alpha_surv={} extreme={} | dom_style={} crowding={}
  CP05  max_corr={}@{nearest_id} incr_ic={} near_dup={}
  CP06  sign_consist={} decay={} | worst_q={} best_q={}

反思: {1-2 句——这个候选告诉我们关于方向/hypothesis 的什么；值不值得沉淀}

风险旗标:  （如无风险则写"无"）
  - {若 CP 档位里有 borderline/weak/poor/unstable/mixed/high 的项，逐条列出并说明为何)
```

reject 候选简化返回（不需要 CP 档位/指标/反思段）：

```
【{CID}】verdict = reject  |  expr = {expression}
hard_gate fail: {reason（从 hints.hard_gate.reasons 抄第一条）}
其它 gate 结果: {简述其它 gate_results 里的值，证明不是机制问题，是数据/质量问题}
```
```

主 agent 在**单条消息**里一次性发 N 个 Agent 工具调用，实现并行。

### Step 4 — 主 agent: 收集 verdicts + 深度反思 → 写 `judge.md`

`judge.md` 不是简单的 verdict 列表——它是本批的**知识沉淀入口**，应当在汇总之上做四层思考：

1. **每候选一句 reflection**（表格里增设列）：除了 metric，还要一句"这个候选告诉我们什么"。
   例如：*"C001：第一次在本方向打出 strong+aligned 组合，机制有辨识性"*、*"C003：数据稀疏不是机制问题，下轮可以重新设计"*。
2. **跨候选对比**（单独一段）：
   - 聚合：几个候选是否共享 style 暴露？是否 mutually high corr?
   - 分化：哪些候选互补？
   - MT 消耗：本批把 direction 预算从什么档推到什么档？
3. **Thread 进展**（按 thread 分组）：每个 thread 本批的进展（ANSWERED / 仍 ACTIVE / DISPROVEN / 新增 T{n+1}）。
4. **方向级反思**（核心段）：本方向的 edge 还够不够？下轮该往哪走？什么时候该 saturated？

信息来源：
- 主 agent 已读 `_hints.yaml` 全部内容（Step 2），含 mt_counts 和每候选的 metrics
- subagent 返回的单行 verdict 摘要
- 必要时 Read 个别 `candidates/C{id}.md` 的 frontmatter（不读 body）

### Step 5 — 主 agent: 更新 `direction.md` + `INDEX.md`（audit 会强制校验）

按文末"Direction Body 更新"段把本轮结果写进 `directions/{direction}.md` 的 Threads / Known Failures / Narrative Log，并同步更新 `INDEX.md` 上半段对应方向的条目。**不再可选**——c14/c15/c16 会查。

### Step 6 — Python: 批量审计

```bash
PYTHONPATH=src python3 -m research judge batch_{N} audit
```

失败列出全部违规（不短路）。主 agent 按违规列表**重启对应 subagent**（只重写有问题的 C{id}.md）或自己重写 judge.md / direction.md / INDEX.md。最多 3 轮。

---

## `_hints.yaml` 完整 schema

```yaml
batch_id: batch_009
direction: timing_signals
generated_at: 2026-04-18T05:45:00+00:00

mt_counts:
  cumulative_candidates: 45
  direction_candidates: 8
  validation_exposure: 8
  n_batches_scanned: 8

per_candidate:
  C001:
    expression: "Std($close, 20)"
    coverage: 0.989
    hard_gate:
      passed: true
      reasons: []
      gate_results:
        compute_error:  {passed: true}
        coverage:       {passed: true, value: 0.989, threshold: 0.80}
        sign_flip:      {passed: true, train_ic: -0.020, val_ic: -0.023}
        forbidden:      {passed: true}
        ic_oos_min:     {passed: true, value: -0.023, threshold: 0.008}
        oos_decay:      {passed: true, value: 1.12, threshold: 0.20}
        mono_flip:      {passed: true, train: -0.10, validation: -0.10}
        near_duplicate: {passed: true, max_corr: 0.25, nearest: F005}
    mt_budget:                       # 仅 hard_gate.passed 有
      score: 0.42
      bucket: medium
      terms: {family: 0.45, direction: 0.38, exposure: 0.20}
      search_adjusted: {raw: 0.67, adjusted: 0.53, bucket: medium}
    metrics:
      cp03:
        ic_oos: 0.016
        icir_oos: 0.338
        ls_tstat_oos: 3.89
      cp04:
        style_r_squared: 0.08
        alpha_survival_ratio: 0.69
        barra_residual_ic: 0.013
        dominant_style_exposure: vol_20d
        extreme_ratio: 0.008
      cp05:
        max_lib_corr: 0.30
        is_near_duplicate: false
        nearest_factor_id: F005
        nearest_factor_expression: "Mul($turnover_rate, ...)"
        incremental_ic: 0.013
      cp06:
        sign_consistency: 1.0
        train_validation_decay: 0.89
  C002:
    expression: "..."
    hard_gate:
      passed: false
      reasons: ["coverage 0.65 < 0.80"]
      gate_results:
        coverage: {passed: false, value: 0.65, threshold: 0.80}
        ...
    # mt_budget omitted when hard_gate.passed=false
    metrics: { ... 仍然填，便于主 agent 看全局 ... }
```

`mt_bucket` / `search_adjusted` / `gate_results` / `metrics` 这些字段 **LLM 不能改**。CP03 body 里 subagent 必须引用 literal `mt_bucket` 和 `search_adjusted`。

---

## Decision Rubric（子代理判决标尺）

完整 rubric 表 + C{id}.md 模板见 [`candidate-rubric.md`](./candidate-rubric.md)。

6 个 checkpoint 档位词：
- **CP01** Hard Gates — Python 独占（subagent 不判）
- **CP02** Mechanism Alignment — aligned / mixed / misaligned
- **CP03** Statistical Strength — strong / borderline / weak
- **CP04** Risk Cleanness — good / acceptable / borderline / poor
- **CP05** Redundancy — low / medium / high
- **CP06** Validation Stability — stable / mixed / unstable

---

## `judge.md` Template

**frontmatter**：

```yaml
---
batch_id: batch_009
direction: timing_signals
judged_at: 2026-04-18T05:50:00Z
candidates:
  - candidate_id: C001
    verdict: admit
  - candidate_id: C002
    verdict: reserve
  - candidate_id: C003
    verdict: reject
batch_summary:
  total: 3
  admit: 1
  reserve: 1
  reject: 1
---
```

**body**（四层结构）：

```markdown
# batch_009 Judge Summary

## 候选一览

| ID | Verdict | Key Metric | 本候选的意义（一句 reflection） | Detail |
|---|---|---|---|---|
| C001 | admit | ICIR=0.338, ls_t=3.89 | 第一次在本方向打出 strong+aligned；机制辨识性强 | [[batches/batch_009/candidates/C001]] |
| C002 | reserve | ICIR=0.21, MT high | CP03 borderline，MT 预算已满；再观察一批 | [[batches/batch_009/candidates/C002]] |
| C003 | reject | coverage 0.65 | 数据稀疏导致 CP01 fail，非机制问题；下轮可重设计 | [[batches/batch_009/candidates/C003]] |

## 跨候选对比

- **Style 聚合**：6 个候选里 4 个 CP04 都暴露 vol_20d（style_r² 均在 0.07-0.10）——本方向容易被波动率因子吸收
- **相关度 cluster**：C001/C004 相关 0.72，内部冗余，下轮可考虑正交化
- **MT 预算变化**：direction_candidates 从 8 推到 11；bucket 仍在 medium 上界

## Thread 进展

- **T001** `[[directions/timing_signals#T001]]`：admit C001 → 状态 `[✓ ANSWERED batch_009]`
- **T002** `[[directions/timing_signals#T002]]`：reserve C002，仍 `[◉ ACTIVE]`，新增子问题 T004
- **T003**：本批无相关候选，仍 ACTIVE

## 方向级反思

本方向的 edge 逐步收窄：`incremental_ic` 中位数从 batch_007 的 0.013 降到本批 0.007。
6 候选中 4 个被 vol_20d style 吸收说明纯 vol 类信号饱和。下轮建议：
1. 切换到 short-window + volume 组合看残差 alpha
2. 或尝试用 vol_20d 正交化后的信号

如果下一轮 admit 率仍低于 20%，应把 direction status 从 `productive` 改为 `saturated`。

## MT Budget Context

- cumulative_candidates = 45 → 48（本批 +3）
- direction_candidates = 8 → 11
- validation_exposure = 8 → 9
- 本批 mt_bucket 分布：low=0, medium=3, high=0
```

audit c13 要求 `judge.md` body 里每个 candidate 都有 `[[batches/{batch_id}/candidates/{cid}]]` wikilink（表格里的 Detail 列已覆盖）。

---

## Python Audit（16 项结构检查）

完整实现在 `src/research/checkpoints/audit.py`。一次过，失败返回违规列表：

| # | 检查对象 | 规则 |
|---|---|---|
| 1 | judge.md frontmatter | 有 batch_id / candidates list / batch_summary |
| 2 | 每个 candidate 条目 | verdict ∈ {admit, reserve, reject, replace}（replace DEPRECATED） |
| 3 | 硬闸不可 override | `_hints.yaml.hard_gate.passed=false` → judge + C{id}.md verdict 必须 reject |
| 4 | candidates 完整性 | result.yaml 每个 candidate_id 都有对应 C{id}.md 文件 |
| 5 | C{id}.md frontmatter | 必填字段齐全，candidate_id 与文件名一致；`factor_id` 不强制（admit 时 null） |
| 6 | C{id}.md body sections | 非-reject 有 `## CP01` – `## CP06`；reject 有 `## CP01` |
| 7 | CP03 引用 mt_bucket | 非-reject C{id}.md CP03 段 literal 含 `mt_bucket` |
| 8 | CP03 引用 search_adjusted | 非-reject C{id}.md CP03 段 literal 含 `search_adjusted` |
| 9 | CP02 引用 hypothesis | 非-reject C{id}.md CP02 段含 `[[directions/{direction}` wikilink |
| 10 | rubric tier 引用 | 每个 CP{2..6} body 含该 CP 的 rubric 档位词之一 |
| 11 | wikilink 形状 | C{id}.md 的所有 wikilink 用 vault-root 形式，禁止 `../` |
| 12 | judge 候选集一致性 | judge.md frontmatter 的 candidate_id 集合 == candidates/*.md 的文件名集合 |
| 13 | judge body 有 candidate 链接 | judge.md body 每个 candidate 都有 `[[batches/{batch_id}/candidates/{cid}]]` |
| 14 | direction.md 更新 | 非-reject 候选的 `[[batches/{batch_id}/candidates/{cid}` 在 body；reject 写入 `## Known Failures`；`## Narrative Log` 有 `batch_{id}` 或 judge wikilink；direction.md 所有 wikilink vault-root |
| 15 | INDEX.md 方向条目 | `<!-- BEGIN AUTO-SECTION -->` 之上的 LLM 区里对应方向的 `### [[directions/{direction}` 段后 1–3 行有 `{batch_id}` |
| 16 | thread_id 跨文件有效 | C{id}.md frontmatter 的 `thread_id` 在 direction.md body 以 `### T{n}` 形式存在 |

失败时 Python 返回完整违规列表（不短路）。主 agent 按违规范围决定重派哪些 subagent（C{id}.md 违规）或自己修（judge.md / direction.md / INDEX.md 违规）。

---

## CLI 命令

```bash
# 生成 _hints.yaml（必须在 Phase 2 result.yaml 之后）
PYTHONPATH=src python3 -m research judge batch_{N} pre-hint

# 批量审计 candidates/*.md + judge.md + direction.md + INDEX.md
PYTHONPATH=src python3 -m research judge batch_{N} audit
```

`state.yaml.current_batch_phase` 必须是 `judged`（Phase 2 已产 result.yaml）才能跑 pre-hint。

---

## Direction Body 更新（Phase 3 收尾 — audit c14/c15/c16 强制）

在跑 `judge audit` **之前**就必须把 `directions/{direction}.md` body 和 `INDEX.md` 上半段更新好——c14/c15/c16 会校验，漏写直接红灯。所有 wikilink **必须 vault-root**（禁止 `[[../batches/...]]`）。

### 1. `## Threads` — evidence trail

对每个非-hard-gate-reject 候选，在其 `thread_id` 对应的 Thread 段 `**Evidence trail**` 下追加：

```markdown
- [[batches/{batch_id}/candidates/C{id}|batch_{N} C{id}]]: {key_metrics_short} → {verdict}
```

admit 示例（不写 `[[factors/F{id}]]`——id 由 Phase 4 分配，Phase 4 或后续 report 可回填链接）：
```markdown
- [[batches/batch_009/candidates/C001|batch_009 C001]]: ICIR=0.338 ls_t=3.89 → **admit**
```

reserve/reject 示例：
```markdown
- [[batches/batch_009/candidates/C002|batch_009 C002]]: ICIR=0.21 → reserve (CP03 borderline + mt_bucket=high)
```

Thread 状态标记（如适用）：
- admit 回答了 Question → `[◉ ACTIVE]` 改 `[✓ ANSWERED batch_{N}]`
- 证据反驳假设 → `[◉ ACTIVE]` 改 `[✗ DISPROVEN batch_{N}]`
- 新子问题 → Threads 段末尾新增 `### T{next}: ... [◉ ACTIVE]`

### 2. `## Known Failures` — reject 条目

对每个 reject 候选追加：
```markdown
- C{id} `{expression}` — {reject_reason_short}
```

### 3. `## Narrative Log` — 本轮总结

追加段：
```markdown
### {YYYY-MM-DD} [[batches/batch_{N}/judge|batch_{N}]]
{admit/reserve/reject 数 + 1-3 核心发现}

**Thread 进展**：
- T001：{进展一句话}

**下一步**：{基于结果的下一步}
```

### 4. （可选）Current Focus / Status 更新

- 首次 admit → `status: exploring` 改为 `productive`
- 连续 2+ batch reject > 80% → `status: productive` 改为 `saturated`
- 在 Narrative Log 里说明理由

### 5. INDEX 上半段 — 方向摘要

`vault/INDEX.md` 上半段（LLM 维护）更新该方向的 `###` 条目：
```markdown
### [[directions/{direction}|{中文名}]] `{status}` `{priority}`
{1-2 句当前状态：最近发现 + 下一步，须提及 {batch_id}}
```

---

## 恢复逻辑

如果 audit 返回违规列表：

1. 按违规定位受影响的 `C{id}.md` / `judge.md` / `direction.md` / `INDEX.md`
2. 对 C{id}.md 违规 → 重派该候选的 subagent，prompt 里加一段 "上一轮 audit 失败：{violations}。请针对性修正"
3. 对 judge.md / direction.md / INDEX.md 违规 → 主 agent 自己重写
4. 重跑 audit。最多 3 轮；超过 → 挂起，报系统级错误
