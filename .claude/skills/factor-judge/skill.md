---
name: factor-judge
description: 读取 judge_packet，对候选因子进行结构化 6 维裁决，通过 guarded_writer 回写治理对象
user_invocable: true
---

> **⚠️ 自主模式**：本 skill 执行时不得停下来询问用户。严格按 6 维标准裁决，不需人工复核。边界案例自行判断。只在系统级错误时停止。

# Factor Judge — 结构化裁决

## 目标

读取 `judge_packet`（主输入），对每个候选因子进行 6 维度结构化裁决，产出 admit/reserve/reject/replace verdict + reason codes。所有治理对象写入通过 guarded_writer。

## 输入

**每轮必读**（按顺序）：
```
storage/governance/research_lessons.md   # 禁忌 + 经验（必须先读，影响裁决标准）
storage/governance/ledger.yaml           # search_ledger + batch_usage + holdout + audit
storage/batches/batch_XXX/judge_packet.yaml  # 主输入
```

Drill-down（仅在需要时）：
```
storage/batches/batch_XXX/research_result.yaml
storage/batches/batch_XXX/execute_report.yaml
storage/batches/batch_XXX/manifest.yaml
storage/logic/cards/*.yaml
```

## 裁决流程

### Step 1：构建 CandidateEvidence

对 judge_packet 中每个 candidate_brief，使用 Python 工厂方法构建结构化证据：

```python
from research.judge.candidate_judge import CandidateEvidence
evidence = CandidateEvidence.from_judge_packet_brief(brief)
```

这确保 brief → evidence 映射在代码层闭环，不依赖 prompt 手动映射。

### Step 2：6 维度裁决

对每个 candidate 检查 6 个维度：

1. **Mechanism Alignment**（aligned / unclear / drifted）
   - logic_thesis_match: candidate 是否回答 logic hypothesis
   - route_question_match: 是否回答本批实验问题
   - sign_and_behavior_match: 方向/触发/行为是否一致
   - non_style_only_explanation: 不能主要由风格残留解释

2. **Statistical Strength**（strong / borderline / weak）
   - IC mean, ICIR, win_rate, monotonicity (validation)
   - expanding_window_pass 必须为 true

3. **Stability**（good / borderline / poor）
   - split_stability / regime_stability 不能为 low
   - support_window_warning ≠ repeated_sign_flip

4. **Redundancy**（low / acceptable / high）
   - max_lib_corr, family_overlap, subspace_redundancy

5. **Feasibility**（ok / borderline / poor）
   - turnover, liquidity_coverage, rebalance_stress

6. **Risk Model Review**（acceptable / borderline / poor）
   - alpha_survival_ratio, style_crowding_risk
   - poor → reason code `style_dominance_detected` (HIGH severity)
   - borderline → `moderate_style_exposure` (MEDIUM)

### Step 3：Candidate Verdict

- **admit**: gate pass + validation strong + expanding pass + stability ok + redundancy acceptable + feasibility ok + mechanism aligned + risk acceptable
- **reserve**: borderline + 或 multiple_testing_risk=high + 或 needs holdout review
- **reject**: gate fail + 或 validation collapse + 或 mechanism drifted + 或 feasibility poor
- **replace**: 与已有因子高度相近 + 无致命 regression + 5 维离散比较（stability/redundancy/mechanism 为主维，strength/feasibility 为辅）

### Step 4：Route Verdict

每个 batch-local 实验组：
- **continue**: ≥1 admit 或高质量 reserve
- **pause**: 证据不足但未证伪
- **kill**: 系统性失败
- **promote_family**: 跨 batch 持续产出

### Step 5：Logic Recommendation

**仅推荐**，不是最终裁决（logic 有最终权）：
active / warm / productive / saturated / parked / dead

### Step 6：回写（通过 guarded_writer）

**一级回写**（直接，附 audit receipt）：
- candidate verdict + route verdict + batch judge report
- Ledger 更新（见 Step 6a）

**二级回写**（需重复证据，由 guarded_writer 校验）：
- forbidden.yaml 升级
- logic lifecycle 最终状态

#### Admission Payload 完整性要求

**关键**：GuardedWriter 会将 payload 原样写入 factor detail YAML。admission 的 payload **必须**包含以下全部字段（从 research_result.yaml 提取）：

```yaml
# 必填字段 — 缺任何一项都是不完整的写入
factor_id: R00X                          # 分配新 ID
candidate_id: C004_05                    # 溯源
name: <name>
expression: <expression>
direction: <short|long>
batch_id: batch_XXX
logic_id: LXXX
route_id: RX
route_type: <genesis|mutate|decorrelate|crossover>
family_id: <PF_*|FM_*>
experiment_lineage_tag: <ELT_*>
rationale: <from manifest>
# 统计指标 — 从 research_result.yaml 的 evaluation section 提取
ic_mean_train: <float>
ic_mean_validation: <float>
ic_ir_train: <float>
ic_ir_validation: <float>
monotonicity_validation: <float>
ls_tstat: <float>                        # long_short_stats.ls_tstat
alpha_survival_ratio: <float>            # risk_review.alpha_survival_ratio
barra_residual_ic: <float>              # risk_review.barra_residual_ic
max_lib_corr: <float>                   # similarity.max_lib_corr
# holdout 指标（如果 holdout_computed=true）
holdout_ic_mean: <float|null>
holdout_ic_ir: <float|null>
holdout_decay_ratio: <float|null>
```

**禁止**只传 name + expression + batch_id。如果 research_result 中缺少某字段，写 `null`，不要省略。

### Step 6a：Ledger 更新（`storage/governance/ledger.yaml`）

裁决完成后，**必须**更新以下 sections：

**search_ledger.by_logic**：对涉及的每个 logic_id 递增计数
```yaml
L021:
  logic_attempt_count_to_date: +N    # 本批该 logic 下的 candidate 数
  admitted_count_to_date: +M         # 本批 admit 数
  reserve_count_to_date: +K          # 本批 reserve 数
```

**search_ledger.by_family**：对涉及的每个 family_id 递增计数（同上结构）

**search_ledger.by_experiment_tag**：对每个 ELT 更新
```yaml
ELT_L021_breakout_compression_gate_v1:
  batches_seen: +1
  admitted_count_to_date: +M
  reserve_count_to_date: +K
  continue_count_to_date: +1         # 根据 route_verdict
  latest_verdict: continue           # continue / pause / kill / promote_family
```

**batch_usage**：将对应 batch 的 `phase` 更新为 `judged`

**holdout_reviews**：如果任何 candidate 触发 holdout review，追加条目：
```yaml
- review_id: HR_auto_increment
  batch_id: batch_XXX
  target_id: C_XXX_NN
  trigger_reason: high_data_mining_risk  # 或 reserve_for_replace_review
  status: pending
  outcome: null
```

**write_audit_log.entries**：每次写入治理对象时追加 receipt：
```yaml
- timestamp: "2026-04-05T10:00:00"
  actor: factor-judge
  action: admit                      # admit / reject / reserve / replace
  target: F076                       # 或 candidate_id
  level: 1
  reason_codes: [mechanism_aligned, feasibility_ok]
```

### Step 7：保存报告 + 关闭 State 周期

```
storage/batches/batch_XXX/judge_report.yaml
```

**裁决完成后必须关闭 state 周期**：
```bash
# 同步 holdout reviews 到 queue（从 ledger 读取 pending → 写入 queue + 更新 state 计数）
PYTHONPATH=src python3 -m research state sync-holdout

# 关闭当前 batch（自动记录 last_completed_batch）
PYTHONPATH=src python3 -m research state clear-batch
```

### Step 7a：为 Reflect 准备（Prepare for Reflect）

Judge **不更新**任何长期状态。所有长期状态更新由 `/factor-reflect` 负责。

Judge 需确保 `judge_report.yaml` 包含 reflect 需要的全部信息：
- `logic_recommendations`（含 recommended_status 和 reason）
- `new_lessons`（含 ST/FP/NM 标识符）
- `discovery_flags`（含 escalation_status）
- `route_verdicts`（含 verdict: continue/pause/kill 和 reason）
- `candidate_verdicts`（含 reason_codes 和 detail）
- `batch_summary`（含 total/admitted/rejected 计数）
- `logic_diagnostics`（每个 logic 的厚诊断 memo，供 reflect 编译）

Judge **仍然写** discovery_candidates 到 ledger（现有模式不变）：
- 通过 `LedgerStore.append_discovery_candidate()` 追加到 `search_ledger.discovery_candidates`

#### `logic_diagnostics` — Judge 的研究诊断层

Judge 不能只给出 20 个字的短评。为了让下一轮模型知道“我们到底在闻什么”，
每个涉及的 logic 都必须在 `judge_report.yaml` 中输出一份 **研究诊断 memo**。

目标不是写漂亮 report，而是给 reflect 和下一轮 /idea 提供足够厚的研究上下文：
- 这个 logic 当前最像什么机制
- 证据支持和反对什么判断
- 哪些边界已经证伪，不能再试
- 哪些问题还没回答完
- 下一轮最值得做的 probes 是什么

格式：

```yaml
logic_diagnostics:
  L001:
    thesis_update: |
      当前证据表明 PF_pv_timing 更像“事件位置编码”而不是量价幅度信号。
      R005 证明 timing 维度有独立信息，但 alpha 仍部分寄生于短期动量，
      且收益高度依赖空头端，因此它不是纯净的独立 alpha。

    evidence_for:
      - "R005 alpha_surv=0.498, style_r2=0.083"
      - "corr(R005, R001)=0.002，说明与幅度类 pv 信号近乎正交"

    evidence_against:
      - "73.2% 的 long-short 收益来自 short 端"
      - "Barra residual IC 仅 -0.0087，独立 alpha 边际化"
      - "与 F067 corr=0.627，存在显著组合共线风险"

    failure_boundary: |
      不再继续做跨量纲的 IdxMax(amount/turnover_rate) decorrelate；
      它们已被证明与 R005 高度同构。纯 amplitude pv 路线也继续受 style 吸收，
      不应再作为 L001 的主方向。

    open_questions:
      - "有效的是 peak timing 本身，还是更一般的 event-position encoding？"
      - "timing 家族能否降低对 short-side 的依赖？"
      - "与 F067 的重叠是表达式层面的，还是机制层面的？"

    next_best_probes:
      - expr: "IdxMin($volume, 20)"
        why: "验证 timing encoding 是否从 peak 扩展到 trough"
      - expr: "Sub(IdxMax($volume, 20), IdxMin($volume, 20))"
        why: "验证峰谷间距是否比单点 timing 更 fundamental"

    factor_roles:
      - factor_id: R005
        role: core_positive_anchor
        summary: "证明 timing encoding 是 L001 唯一明确成立的正交工具"
      - candidate_id: C004_01
        role: failed_cross_dimension_variant
        summary: "amount 维度 IdxMax 未 decorrelate，说明机制未变"
```

字段约束：
- `thesis_update` / `failure_boundary`：允许长文本，必须是完整段落
- `evidence_for` / `evidence_against`：每条都必须引用具体指标或已观测事实
- `open_questions`：必须是尚未回答的问题，不能只是“继续优化”
- `next_best_probes`：必须带 `expr` 和 `why`
- `factor_roles`：用于把关键因子/候选在当前 logic 中的意义讲清楚

Judge 的这层输出是 **research-grade diagnostic memo**，不是 marketing 文案。
如果 diagnosis 不足以支持下一轮 /idea 设计 probes，就说明写得不够厚。

### Step 8：异常发现检查（Discovery）

裁决完成后，检查是否有重复异常模式需要升级：

**检查 3 类异常：**
1. **repeated_residual_anomaly** — 不可解释的残留 alpha 重复出现
2. **repeated_near_miss_cluster** — 反复接近但未通过的同类 candidate
3. **unexplained_family_edge** — family 边缘的异常表现

**升级规则：**
- **watch**（单次异常）：写入 `ledger.yaml` 的 `search_ledger.discovery_candidates`，status=watch
- **escalate**（≥2 batch 出现）：更新 status=escalated，在下一轮 `/factor-logic` review 时作为 logic_proposal 输入

**escalation_note 格式：**
```yaml
- anomaly_type: repeated_near_miss_cluster
  first_seen_batch: batch_002
  description: "..."
  likely_mechanism: "..."
  style_repackaging_risk: low/medium/high
  explainable_by_existing_logic: full/partial/no
  escalation_status: watch/escalated
```

关键约束：discovery 不直接立项 logic、不单独经营预算——只负责观察和升级到 ledger。

## Reason Codes

| Code | Severity | 触发条件 |
|------|----------|---------|
| sign_flip_detected | fatal | validation sign flip |
| known_bad_pattern | fatal | 命中 forbidden |
| mechanism_drifted | fatal | thesis/route 不匹配 |
| style_dominance_detected | high | risk bucket = poor |
| poor_split_stability | high | split stability = poor |
| high_subspace_redundancy | high | subspace redundancy = high |
| weak_validation_effect | high | IC/ICIR 过弱 |
| moderate_style_exposure | medium | risk bucket = borderline |
| regime_instability | medium | regime stability weak |
| feasibility_borderline | medium | feasibility borderline |
| high_data_mining_risk | medium | multiple testing = high |
| mechanism_aligned | info | mechanism ok |
| feasibility_ok | info | feasibility ok |
| risk_model_acceptable | info | risk bucket = acceptable |

## 关键约束

- judge 基于 **validation** 证据裁决，不做新实验
- Score/bucket 不能单独触发 admit/reject，只能辅助排序
- **judge 只写 batch artifacts + ledger**（search_ledger 计数、audit_log、holdout_reviews、batch_usage、discovery_candidates）
- **judge 不写** logic cards、research_state、research_config、research_lessons
- 所有长期状态更新由 /factor-reflect 负责
- 冷启动期（<5 batch 或 <10 因子）：不输出 promote_family / productive / saturated / dead
