---
name: factor-judge
description: Phase 3 JUDGE — 6 checkpoint 结构化判决 + §7.MT 多重检验预算
user_invocable: true
---

# /factor-judge — Phase 3 判决

## 职责

对 Phase 2 产出的每个候选执行 6 个 checkpoint 的结构化判决，写 `judge.md`。

## 6 个 Checkpoint

| CP | 名称 | 决策者 | 内容 |
|---|---|---|---|
| **CP01** | Hard Gates | Python（不可 override） | sign_flip / coverage / forbidden / sample_policy / compute_error |
| **CP02** | Mechanism Alignment | LLM | expression 是否对应 direction.hypothesis |
| **CP03** | Statistical Strength | LLM + Python hint | IC / ICIR + **mt_bucket + search_adjusted_strength** |
| **CP04** | Risk Cleanness | LLM + Python hint | Barra residual / style_r² / alpha_survival |
| **CP05** | Redundancy | LLM + Python hint | max_lib_corr / nearest factor |
| **CP06** | Validation Stability | LLM + Python hint | split_stability + expanding_window（**不是 holdout**）|

## §7.MT 多重检验预算

- Python 扫 `batches/batch_*/manifest.yaml`（judged-only），算 `cumulative_candidates / direction_candidates / validation_exposure`
- 公式：`mt_score = 0.50*clip(log1p(cum)/log(600)) + 0.30*clip(log1p(dir)/log(80)) + 0.20*clip(val/40)`
- bucket：`< 0.40 → low`, `≤ 0.70 → medium`, `> 0.70 → high`
- **CP03 body 必须显式引用 `mt_bucket` 值**（audit grep 验证，漏写 → rewrite）

## judge.md 结构

- **Frontmatter**：`batch_id / candidates[{candidate_id, verdict, hard_gate_result, checkpoint_positions}] / batch_summary`
- **Body**：每个候选一个 `## C{id}` H2 段 + 6 个 `### CP{N}` H3 段（reject 只需 CP01）
- **Verdict**：`admit / reserve / reject / replace`

## 硬约束

- **Hard gate 不可 override**：hard_gate_result ≠ all_pass → verdict 必须 reject
- **CP06 不看 holdout**：只用 train + validation 数据
- **LLM 只读 `judge_packet.md`**（R3），不自行打开其他文件
