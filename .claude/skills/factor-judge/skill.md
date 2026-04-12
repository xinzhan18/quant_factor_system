---
name: factor-judge
description: Phase 3 JUDGE — 6 checkpoint 结构化判决 + §7.MT 多重检验预算
user_invocable: true
---

# /factor-judge — Phase 3 判决

## 职责

对 Phase 2 产出的每个候选执行 6 个 checkpoint 的结构化判决，写 `judge.md`。

## 6 个 Checkpoint

| CP | 名称 | 决策者 | Python numeric_hint 字段 |
|---|---|---|---|
| **CP01** | Hard Gates | Python（**不可 override**） | `coverage`, `sign` |
| **CP02** | Mechanism Alignment | LLM | _(无 Python hint，LLM 自行判断)_ |
| **CP03** | Statistical Strength | LLM + Python hint | `ic_mean_val`, `ic_ir_val`, `ic_win_rate_val`, `ls_mean`, `mono_val`, **`mt_score`**, **`mt_bucket`**, **`search_adjusted`** |
| **CP04** | Risk Cleanness | LLM + Python hint | `style_r2`, `barra_residual_ic`, `alpha_survival`, `crowding`, `dominant_style` |
| **CP05** | Redundancy | LLM + Python hint | `max_lib_corr`, `nearest`, `exceeds_threshold` |
| **CP06** | Validation Stability | LLM + Python hint | `split_bucket`, `split_sign_consistency`, `split_dispersion`, `train_val_sign_ok`, `train_val_decay` |

## CP01 Hard Gates（5 条，任一触发 → reject 不可 override）

1. **compute_error**：Phase 2 记录了异常
2. **coverage < 0.80**：因子在不足 80% 的截面有值
3. **sign_flip**：train IC mean 和 validation IC mean 异号（或任一 ≈ 0）
4. **forbidden_field_or_op**：表达式包含 `$vwap` / `Neg()` / `SMA()`
5. **sample_policy_violation**：result.yaml 的 `sample_policy_version` ≠ 当前 `config.yaml`

## §7.MT 多重检验预算

### 公式

```
mt_score =   0.50 × clip(log1p(cumulative_candidates) / log(600), 0, 1)
           + 0.30 × clip(log1p(direction_candidates)  / log(80),  0, 1)
           + 0.20 × clip(validation_exposure / 40, 0, 1)
```

### Bucket

| mt_score | bucket |
|---|---|
| < 0.40 | low |
| 0.40 ~ 0.70 | medium |
| > 0.70 | high |

### Search-adjusted strength

```
raw = 0.40 × clip(|ic_mean|/0.02) + 0.30 × clip(|ic_ir|/0.20) + 0.20 × clip(|mono|/0.40) + 0.10 × expanding_pass
adjusted = raw × (1 − 0.50 × mt_score)
```

### 三条硬约束

1. **Python 算，LLM 不能 override**：mt_bucket 通过 numeric_hint 注入，judge.md body 可以解释但不能修改值
2. **sample_policy_version 升版 → validation_exposure 清零**：必须在 config.yaml 里升版号，LLM 不能擅自重置
3. **只数 judged batches**：scan 跳过 current batch 和没有 judge.md 的 batch（防 self-correction 循环）

### 计数来源

Python 扫 `storage/batches/batch_*/manifest.yaml`（只要 `judge.md` 存在的 batch）：
- `cumulative_candidates`：所有历史 batch 的候选总数
- `direction_candidates`：同 direction 的历史候选数
- `validation_exposure`：当前 `sample_policy_version` 下被使用的 batch 数

## LLM 写 judge.md

### 输入

只读一份 `_packets/judge_packet.md`（R3 单一输入原则）。Packet 包含：
- Frontmatter：batch_id / direction / n_candidates / mt_budget 计数
- Direction Context：hypothesis + 最近 thread
- Lessons Excerpt：structural constraints
- Nearest Library Factor：最相近因子摘要
- 每个候选的 numeric hint（CP01-CP06 数值）

### judge.md frontmatter schema

```yaml
batch_id: batch_103
judged_at: 2026-04-10T05:45:00
direction: fundamental_price_divergence

candidates:
  - candidate_id: C001
    verdict: admit               # admit / reserve / reject / replace
    hard_gate_result: all_pass   # 或具体 reject reason
    checkpoint_positions:
      CP01: all_pass
      CP02: aligned
      CP03: strong               # strong / borderline / weak
      CP04: acceptable           # good / acceptable / borderline / poor
      CP05: low                  # low / medium / high (corr)
      CP06: stable               # stable / mixed / unstable
    overrides:                   # 如果 LLM override 了 Python 建议
      - checkpoint: CP04
        from: borderline
        to: acceptable
    factor_id: F020              # admit 才有
    referenced_context:
      - directions/fp_divergence.md#Hypothesis
      - lessons.md#Structural Constraints
    concerns:                    # 条件性警告
      - checkpoint: CP04
        if: "alpha_surv < 0.6 in future batch"
        then: "重审 override 合理性"

batch_summary:
  total: 6
  admit: 2
  reserve: 3
  reject: 1
  new_factors: [F020, F021]
```

### judge.md body 结构

每个候选一个 `## C{id}` H2 段。非 reject 候选必须有 6 个 `### CP{N}` H3 段。reject 只需 `### CP01`。

**CP03 段必须显式引用 `mt_bucket` 值**。例如：
> `mt_bucket = medium`（cumulative=612 / direction=47 / exposure=102）；search-adjusted strength = 0.41 仍在 strong 档下界以上...

## 6 个 Python Audit 检查

judge.md 写完后 Python 自动跑 6 个结构检查。任一失败 → `JudgeAuditError` → LLM 重写（最多 3 次）：

1. **Frontmatter schema**：必须有 `batch_id` / `candidates` / `batch_summary`；每个 candidate 必须有 `candidate_id` / `verdict` / `hard_gate_result`
2. **Verdict enum**：verdict ∈ `{admit, reserve, reject, replace}`
3. **Hard gate 不可 override**：`hard_gate_result ≠ "all_pass"` → `verdict` 必须 `reject`
4. **Body 章节覆盖**：每个候选有 `## C{id}` H2 段；非 reject 有全部 6 个 `### CP{N}` H3
5. **CP03 引用 mt_bucket**：非 reject 候选的 CP03 段 grep 到 `"mt_bucket"` 字符串
6. **Referenced context 真实性**：所有 `referenced_context` 条目必须是 judge_packet 里声明的引用子集（LLM 不能编造不在 packet 里的引用）
