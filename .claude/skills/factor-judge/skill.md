---
name: factor-judge
description: 读取 judge_packet，对候选因子进行结构化 6 维裁决，通过 guarded_writer 回写治理对象
user_invocable: true
---

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
# 如果有 holdout review 触发，先更新计数
PYTHONPATH=src python3 -m research state set pending_holdout_count N

# 关闭当前 batch（自动记录 last_completed_batch）
PYTHONPATH=src python3 -m research state clear-batch
```

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

**写回经验教训**：如果本轮裁决发现了新的 forbidden pattern、style trap 或 near-miss 教训，追加到 `storage/governance/research_lessons.md` 对应的 section。

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
- judge 不直接修改 forbidden / final logic status
- 冷启动期（<5 batch 或 <10 因子）：不输出 promote_family / productive / saturated
