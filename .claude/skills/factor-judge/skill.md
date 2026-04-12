---
name: factor-judge
description: Phase 3 JUDGE — 6 checkpoint 结构化判决 + §7.MT 多重检验预算
user_invocable: true
---

# /factor-judge — Phase 3 判决

## 职责

对 Phase 2 产出的每个候选执行 6 个 checkpoint 的结构化判决，写 `judge.md`。

### 分工

| 角色 | 职责 |
|---|---|
| **Python** | 运行 hard gates (CP01)、扫描 batches 计算 §7.MT 预算、预打包 `judge_packet.md`、审计 `judge.md`（6 个结构检查） |
| **LLM** | 只读 `judge_packet.md`（R3 单一输入）、写 CP02-CP06 推理、做出裁决、写 `judge.md` |

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

## CLI 命令（单独调用时）

```bash
# 完整 Phase 3（hard-gates → pre-pack → [LLM 写 judge.md] → audit）
PYTHONPATH=src python3 -m research judge batch_{N}

# 只跑前置 Python 步骤（生成 _packets/judge_packet.md）
PYTHONPATH=src python3 -m research judge batch_{N} pre-pack

# 只跑审计（检查已写好的 judge.md 是否通过 6 个结构检查）
PYTHONPATH=src python3 -m research judge batch_{N} audit
```

**前置条件**：`state.yaml.current_batch_phase == "judged"`（注意：`judged` 的语义是 "Phase 2 EXECUTE 已完成，等待 judge"——名字表示下一步的动作者，不是过去完成时。result.yaml 必须存在）。

## 6 维评估 (report_card) — LLM 判决的核心数据

judge_packet 的每个候选都包含完整的 **36 字段 FactorReportCard**，分为 6 个维度。LLM 在做 CP02-CP06 判决时**必须参考**这些数据：

| 维度 | 包含什么 | 对应哪个 CP | LLM 如何使用 |
|---|---|---|---|
| **D1 预测力** | ic_mean/ir IS, ic_by_year (逐年 IC), ic_by_month (月度分布) | CP03 | 年度 IC 一致性 → 判断信号是否依赖特定市场制度 |
| **D2 稳健性** | oos_decay_ratio, ic_autocorr, ic_max_drawdown, worst/best_quarter | CP06 | decay_ratio > 1 = OOS 更强（好）; ic_max_drawdown 大 = 有 IC 崩溃期（差） |
| **D3 经济一致** | quintile IS+OOS, mono IS+OOS, ls_return, ==ls_tstat== | CP02+CP03 | ls_tstat > 2 = 统计显著; mono IS≈OOS = 稳定; quintile IS→OOS 形状一致 = 好 |
| **D4 衰减** | ic_decay (多期), half_life, factor_turnover, factor_autocorr | CP03 补充 | turnover 高 = 换仓成本高; half_life 短 = 短期信号 |
| **D5 分布** | coverage, zero_ratio, skew, kurtosis, extreme_ratio | CP01 补充 | skew 高 = 分布偏态（可能少数极端值驱动 IC）; extreme_ratio 高 = 不稳定 |
| **D6 独特性** | max_lib_corr, incremental_ic, lib_corr_profile | CP05 | incremental_ic = 在已有因子基础上的增量预测力 |

### 判决规范

LLM 在 judge.md 的 CP 段中**必须引用** report_card 的关键字段来支持判断：

- **CP02 (机制对齐)**：引用 D3 `ls_tstat`、`mono_IS`/`mono_OOS` 一致性、D1 `ic_by_year` 的趋势
- **CP03 (统计强度)**：引用 D1 `ic_ir_IS`、D2 `oos_decay_ratio`、D4 `factor_turnover`
- **CP04 (风险)**：引用 Barra 字段 + D5 `skew`/`extreme_ratio`（分布畸形 = 风险）
- **CP05 (冗余)**：引用 D6 `incremental_ic`（即使 max_corr 低，如果 incremental_ic ≈ 0 则无增量价值）
- **CP06 (稳定性)**：引用 D2 `ic_max_drawdown`、`worst_quarter`、D1 `ic_by_year` 波动

## Multi-horizon + Multi-universe（judge 层可见性）

judge_packet.md 里会包含：
- **Per-horizon 对比表**（h1/h5/h10 的完整 metrics）—— LLM 可以讨论"h1 强 h10 弱 → short-term reversal"
- **Per-universe 对比表**（primary csi1000 + reference csi300/csi500/all）—— LLM 可以讨论"csi300 更强 → 大盘股效应"

**但 CP01-CP06 的判决只看 `primary_horizon`（h5）× `primary_universe`（csi1000）**。multi-horizon/universe 只作为 context hint。

## LLM 写 judge.md

### 输入

只读一份 `_packets/judge_packet.md`（R3 单一输入原则）。Packet 包含：
- **Frontmatter**：batch_id / direction / n_candidates / mt_budget 计数
- **Direction Context**：hypothesis + 相关 thread（作为上下文摘录，非结构化数据）
- **Lessons Excerpt**：structural constraints
- **6 维评估 (report_card)**：每个候选的完整 FactorReportCard（36 字段）
- **Nearest Library Factor**：最相近因子摘要
- **每个候选的 numeric hint**（CP01-CP06 数值）

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
    overrides:                   # 可选，如果 LLM override 了 Python 建议
      - checkpoint: CP04
        from: borderline
        to: acceptable
    factor_id: F020              # 仅 admit 时有
    referenced_context:
      - directions/fp_divergence.md#Hypothesis
      - lessons.md#Structural Constraints
    concerns:                    # 可选，条件性警告
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
