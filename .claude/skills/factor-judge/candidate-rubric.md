---
name: candidate-rubric
description: Phase 3 JUDGE — single-candidate judging manual (subagent only)
---

# Candidate Judging Rubric（子代理手册）

你（子代理）为**一个候选因子**写一份 `candidates/C{id}.md`，按 6 个 checkpoint 打分并给出 verdict。本手册是你唯一的判决依据。

## 你读什么

| 来源 | 必读 | 说明 |
|---|---|---|
| 本文件 `candidate-rubric.md` | ✓ | 本手册，判决标尺 |
| `_hints.yaml` 里 `per_candidate.{CID}` 块 | ✓ | Python 已预拍平所有 rubric 数值 + 每个 hard gate 的独立结果 + MT 预算 |
| `directions/{DIRECTION}.md` | ✓ | 方向 hypothesis + 活跃 threads（CP02 用） |
| `factors/{nearest_factor_id}.md` | 可选 | 仅当 `metrics.cp05.nearest_factor_id` 非 null 时，用于 CP02/CP05 近邻机制对比 |

你**不读**：`result.yaml` / `lessons.md` / 父 `skill.md`。所有数字都在 `_hints.yaml` 里。

## 你写什么

一个文件：`storage/vault/batches/{BATCH_ID}/candidates/{CID}.md`。不写其它文件、不跑 Bash。

写完后**返回一段结构化摘要**给主 agent（不是整份 md，也不是一行）。主 agent 直接
拿你这段内容拼进 `judge.md` 的候选一览表 + 跨候选对比段，所以需要足够素材。
所有数值直接从 `hints.metrics` 抄，不要自己算。

### 非-reject 候选返回模板

```
【{CID}】verdict = {admit|reserve}  |  expr = {expression}
{admit 时额外加一行} factor_name: {snake_case_name}

档位: CP02={aligned|mixed|misaligned} · CP03={strong|borderline|weak} · CP04={good|acceptable|borderline|poor} · CP05={low|medium|high} · CP06={stable|mixed|unstable}

指标:
  CP03  ic_oos={} icir_oos={} ls_t={} | ic_is={} ls_sharpe={}
  CP04  style_r²={} alpha_surv={} extreme={} | dom_style={} crowding={}
  CP05  max_corr={}@{nearest_id} incr_ic={} near_dup={}
  CP06  sign_consist={} decay={} | worst_q={} best_q={}

反思: {1-2 句——这个候选告诉我们关于方向/hypothesis 的什么；值不值得沉淀}

风险旗标:  （如无风险则写"无"）
  - {若 CP 档位有任何 borderline/weak/poor/unstable/mixed/high 项，逐条列出并说明为何}
```

### reject 候选返回模板（简化）

```
【{CID}】verdict = reject  |  expr = {expression}
hard_gate fail: {hints.hard_gate.reasons 的第一条}
其它 gate 结果: {简述 hints.gate_results 里的其它值，说明这是数据/质量问题而非机制问题}
```

---

## `_hints.yaml` 数据结构

子代理读 `per_candidate.{CID}` 下这棵树：

```yaml
expression: "Std($close, 20)"
coverage: 0.989
hard_gate:
  passed: true
  reasons: []               # 若 passed=false，这里列原因
  gate_results:             # 8 项 gate 每项独立结果（passed=true 时也详尽）
    compute_error:  {passed: true}
    coverage:       {passed: true, value: 0.989, threshold: 0.80}
    sign_flip:      {passed: true, train_ic: -0.020, val_ic: -0.023}
    forbidden:      {passed: true}
    ic_oos_min:     {passed: true, value: -0.023, threshold: 0.008}
    oos_decay:      {passed: true, value: 1.12, threshold: 0.20}
    mono_flip:      {passed: true, train: -0.10, validation: -0.10}
    near_duplicate: {passed: true, max_corr: 0.25, nearest: F005}
mt_budget:                  # 仅 hard_gate.passed 才有
  score: 0.42
  bucket: medium             # low / medium / high
  terms: {family: ..., direction: ..., exposure: ...}
  search_adjusted:
    raw: 0.67
    adjusted: 0.53
    bucket: medium
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
    style_contributions:          # leave-one-out 归因，按 |delta_ic| 降序
      - style: vol_20d
        delta_ic: 0.025            # 若不控此 style，residual |IC| 会多 0.025
        pct: 65.8                  # 占 raw→residual 总衰减比例
        ic_without: -0.035
      - style: turnover_20d
        delta_ic: 0.008
        pct: 21.1
        ic_without: -0.018
      # ... 7 项 styles 全量
  cp05:
    max_lib_corr: 0.30
    is_near_duplicate: false
    nearest_factor_id: F005
    nearest_factor_expression: "Mul($turnover_rate, ...)"
    incremental_ic: 0.013
  cp06:
    sign_consistency: 1.0
    train_validation_decay: 0.89
```

---

## Rubric（判决标尺）

### CP01 Hard Gates（Python 独占，子代理不判）

- `hard_gate.passed == false` → verdict **只能**是 `reject`。直接写 reject 最小模板，CP02–06 全省略。
- `hard_gate.passed == true` → 在 `## CP01` 段**逐项列出** 8 个 gate 的结果（值 + 阈值），让读者看到全过。不要只写 "passed: true, reasons: []"。

### CP02 Mechanism Alignment —— 5 问 checklist（aligned / mixed / misaligned）

非-reject 候选 CP02 body **必须**逐项回答：

1. **机制是什么**：`expression` 捕捉什么市场行为？经济叙事，不要说"IC 高所以好"
2. **hypothesis 对齐**：和 `[[directions/{DIRECTION}#Hypothesis]]`（强制 wikilink）是否一致？
3. **为什么持续**：这个 edge 为什么不是一次性失效？
4. **失效场景**：什么时候失效？（熊市、涨停板、停牌、行业事件……）
5. **近邻差异**：和 `[[factors/{nearest_factor_id}]]`（`metrics.cp05.nearest_factor_expression` 的机制）哪里不同？

| 档位 | 标准 |
|---|---|
| **aligned** | 5 问全答、有实质、hypothesis fit 清晰 |
| **mixed** | 答了 3–4 问，或机制勉强说得通但 hand-waving |
| **misaligned** | 机制与 hypothesis 冲突，或纯经验拟合 |

### CP03 Statistical Strength —— 3 核心指标 + rank-order 证据 + MT 调整（strong / borderline / weak）

**核心 3 指标**（用来定档位）：

字段：`metrics.cp03.{ic_oos, icir_oos, ls_tstat_oos}`

| 指标 | strong | moderate | weak | 硬闸 |
|---|---|---|---|---|
| `\|ic_oos\|` | > 0.015 | 0.010 – 0.015 | < 0.010 | < 0.008 → CP01 已 reject |
| `\|icir_oos\|` | > 0.30 | 0.15 – 0.30 | < 0.15 | — |
| `\|ls_tstat_oos\|` | > 3 | 2 – 3 | < 2 | — |

| 档位 | 标准 |
|---|---|
| **strong** | IC **且** ICIR 都 strong **且** ls_tstat ≥ 2 |
| **borderline** | 至少一项 strong 其余 moderate；或全部 moderate 但 ls_tstat ≥ 2 |
| **weak** | 任一指标落到 weak 档 |

**Rank-order 验证**（不单独定档，但 body 必须讨论；三类问题会把档位 **下调一档**）：

字段：`metrics.cp03.{monotonicity_is, monotonicity_oos, quintile_returns_is, quintile_returns_oos}`

| 检查点 | 健康 | 异常（需降档） |
|---|---|---|
| `\|monotonicity_oos\|` | ≥ 0.8（强单调）| < 0.5 但 ls_tstat 却 > 2 → 可疑："高 t 值但不单调 = 尾部驱动 / 异常值" |
| `monotonicity_is` vs `monotonicity_oos` 同号 | 是 | 否（已被 hard_gate.mono_flip 拦）|
| 五档收益梯度（q1→q5）| 单调上升或下降，q1/q5 差值与 `ls_mean_oos` 量级一致 | q1-q4 平、Q5 独大 → "一桨驱动"；q1/q5 对称但中间反着 → "奇异结构" |

**IS/OOS 对比**（body 必须讨论）：
- 用 `ic_is` vs `ic_oos`、`ls_sharpe_is` vs `ls_sharpe_oos`、`ls_tstat_is` vs `ls_tstat_oos` 算 decay
- decay > 0.8 且单调性一致 → 健康
- decay 0.5-0.8 → 体现在 mt_adjustment 里（OK）
- decay < 0.5 → 已被 `hard_gate.oos_decay` 拦

**样本量注释**（body 可选提及）：`n_days_is` / `n_days_oos` 若 < 200 则 IC 统计显著性存疑，即使指标强也要降档 borderline。

**MT 调整**（按 `mt_budget.bucket`）：

| bucket | 规则 |
|---|---|
| `low` | 原档保留 |
| `medium` | 原档保留但 body 须说明"经 search adjustment 后仍 ..." |
| `high` | 最高只能到 `borderline`，必须明说降档理由 |

**CP03 body 强制**：
1. 引用核心 3 数值 + 档位词
2. 引用 `monotonicity_oos` + 给出 Q1–Q5 梯度一句判断（"单调" / "一桨" / "异常"）
3. 引用 `ic_is` vs `ic_oos` 的 decay 比值
4. literal 字符串 `mt_bucket` 和 `search_adjusted`（audit c7/c8 查这两个字面值）

### CP04 Risk Cleanness —— 3 指标（good / acceptable / borderline / poor）

字段：`metrics.cp04.{style_r_squared, alpha_survival_ratio, extreme_ratio}`

| 指标 | clean | borderline | poor |
|---|---|---|---|
| `style_r_squared` | < 0.12 | 0.12 – 0.25 | > 0.25 |
| `alpha_survival_ratio` | > 0.50 | 0.30 – 0.50 | < 0.30 |
| `extreme_ratio` | < 0.01 | 0.01 – 0.03 | > 0.03 |

| 档位 | 标准 |
|---|---|
| **good** | 三项都 clean |
| **acceptable** | 至多一项 borderline |
| **borderline** | 两项 borderline，或一项 poor 其余 clean |
| **poor** | 任何两项 poor |

**CP04 body 强制**：cite `style_r_squared`、`alpha_survival_ratio`、`barra_residual_ic`，flag `dominant_style_exposure`；**Alpha killer 段**列 `style_contributions` 前 2-3 项（`{style}: delta_ic={…} ({pct}%)`），一句话总结"本因子主要被 `{top_style}` 吞噬，下轮需 orthogonalize / normalize by {top_style}"。

**CP04 与 verdict 关系**（2026-04-19 放宽）：
- CP04 档位纯粹**描述性**，不自动触发 reject。Verdict 由 CP02–CP06 + MT + 库增值综合判断。
- **Barra 吞噬不等价 alpha 无效**：因子可以同时 `alpha_survival<0.50` **且** `max_lib_corr<0.30` **且** `incremental_ic > 0.005` — 这说明"Barra 空间内载体"但"库空间独立"，仍有库增值价值。
- **Anchor rule**（防风格重复，规则不变）：当同批 ≥ 2 个候选 CP04 poor 且**同 `dominant_style_exposure`** 且**互相 `corr > 0.50`**（同源，非仅同风格），最多 admit 1 个。单点 poor + 低库相关不受限。
- 首批（empty library）例外：CP05 `max_lib_corr=0` 机械 low 不能单独支持 admit，admit 判断此时倾向更严格（同批 anchor rule 仍适用）。

### CP05 Redundancy —— 2 指标 + 硬闸（low / medium / high）

字段：`metrics.cp05.{max_lib_corr, is_near_duplicate, nearest_factor_id, nearest_factor_expression, incremental_ic}`

| 指标 | low | medium | high | 硬闸 |
|---|---|---|---|---|
| `max_lib_corr` | < 0.30 | 0.30 – 0.70 | 0.70 – 0.90 | `is_near_duplicate == true`（>0.9）→ CP01 已 reject |
| `incremental_ic` | > 0.005 | 0.003 – 0.005 | < 0.003 | — |

| 档位 | 标准 |
|---|---|
| **low** | low corr **且** `incremental_ic` ≥ 0.005 |
| **medium** | medium corr 且 `incremental_ic` 有意义；或 low corr 但 `incremental_ic` 边缘 |
| **high** | high corr（0.70–0.90）；body 必须明说：<br>  · `incremental_ic > 0.005` → 仍可 admit（库增值清晰）<br>  · `incremental_ic ∈ [0.003, 0.005]` → 建议 reserve<br>  · `incremental_ic < 0.003` 或 null → 建议 reject |

**CP05 body 强制**：cite `max_lib_corr`、`is_near_duplicate`、wikilink `[[factors/{nearest_factor_id}]]`、`incremental_ic`，1–2 句论"admit 是否为库增值"。

### CP06 Validation Stability —— 2 核心指标 + 时序稳健性辅助（stable / mixed / unstable）

**核心 2 指标**（用来定档位）：

字段：`metrics.cp06.{sign_consistency, train_validation_decay}`

| 指标 | stable | mixed | unstable |
|---|---|---|---|
| `sign_consistency` | = 1.0 | 0.75 – 1.0 | < 0.75 |
| `train_validation_decay` | > 0.8 | 0.5 – 0.8 | < 0.5 |

| 档位 | 标准 |
|---|---|
| **stable** | 两项都 stable |
| **mixed** | 一项 stable 一项 mixed；或两项都 mixed |
| **unstable** | 任一项 unstable |

**时序稳健性辅助**（不单独定档，但异常会把档位下调一档，body 必须提及）：

| 字段 | 健康 | 需警觉 |
|---|---|---|
| `ic_autocorr_lag1` | `\|x\| < 0.15`：IC 日独立，ICIR 置信高 | `> 0.30`：IC 有强动量/regime，ICIR 可能高估 |
| `cum_ic_max_drawdown` | `> -30`：累计 IC 回撤温和 | `< -50`：有一段长期失效历史，即使现在恢复 |
| `worst_quarter_ic` / `best_quarter_ic` | 同号且量级 ≤ 2× OOS 均值 | 异号或 worst > 3× `\|ic_oos\|` → 依赖某季度 |
| `ic_by_year` | 近 3 年同号且量级稳定 | 早期年份强、近期年份弱 → edge 消失中 |
| `split_ic_means` / `split_dispersion` | dispersion < 0.3 且所有 split 同号 | dispersion > 0.6 → split 之间方差大 |

**CP06 body 强制**：
1. cite `sign_consistency` + `train_validation_decay` + 档位词
2. cite `ic_autocorr_lag1` 一句（是否独立）
3. cite `cum_ic_max_drawdown` 一句（累计回撤情况）
4. 若 `ic_by_year` 非空，讨论逐年趋势（正在增强 / 稳定 / 衰减）

---

### Feasibility（不单独评档，但影响 verdict 边界）

字段：`metrics.feasibility.{turnover_mean, liquidity_coverage, tail_concentration, small_cap_concentration, signal_half_life, signal_autocorr_lag1, ic_half_life_days, rebalance_stress}`

Verdict 使用规则：
- `turnover_mean > 2.0` + `ic_half_life_days < 5` → 高换手 + 短半衰期，即使 CP03 strong 也建议降 verdict 到 `reserve`（后续需做 turnover-aware backtest）
- `liquidity_coverage < 0.5` → 小盘/流动性受限，body 必须明说"样本仅覆盖 x% 可投标的"
- `small_cap_concentration > 0.4` → 因子偏向小盘，与 CP04 `log_circ_cap` style 暴露合并讨论
- `rebalance_stress.rebalance_stress_bucket == "high"` → admit 前必须经一轮 turnover 压力测试（暂不 block，但要记入风险旗标）

Body 是否必提：若有任何一条触发"需警觉"则 verdict 段必须明说；否则可省略。

---

## `C{id}.md` frontmatter

```yaml
---
candidate_id: C001                  # 必填，与文件名一致
batch_id: batch_009                 # 必填
direction: timing_signals           # 必填
expression: "Std($close, 20)"       # 必填（照抄 _hints.yaml.per_candidate.{CID}.expression）
verdict: admit                      # 必填：admit | reserve | reject（replace 枚举保留但 DEPRECATED，不用）
thread_id: T001                     # 必填；必须对应 direction.md 里 `### T001` H3（audit c16 交叉校验）
factor_id: null                     # admit 时留 null，Phase 4 分配
factor_name: pv_corr_20d_vol20d     # verdict=admit 必填；snake_case，3-40 字符，反映机制而非表达式细节
key_metrics_short: "ICIR=0.338 ls_t=3.89"     # verdict != reject 必填
reject_reason_short: null                      # verdict=reject 必填
---
```

**`factor_name` 命名准则**（verdict=admit 必填）：
- snake_case，3–40 字符，仅 `[a-z0-9_]`
- 反映**机制/经济含义**，不是表达式逐字翻译
  - 好：`pv_corr_20d`、`vol_of_vol_60`、`turnover_reversal_5`
  - 差：`mul_corr_close_volume_20_std_volume_20`（逐字复述）
- 同库内唯一；若已存在同名，加后缀区分参数（`pv_corr_20d` vs `pv_corr_60d`）
- 主 agent 会把 `factor_name` 同步写进 `judge.md` frontmatter 的 admit 条目；Phase 4 据此写 `factor.yaml.name` + `python_factors/F{id}_{name}.py`
```

---

## `C{id}.md` body — 视觉扫读约定

读者打开文件第一眼需要看到：verdict + 6 档位 + 3-5 核心指标 + 阻断项（若有）。下面的格式全部用 Obsidian callout + `==highlight==` 实现。**narrative 内容保持完整**，视觉脚手架只加不减。

关键规则：

- **TL;DR callout** 紧跟 H1，verdict 色差：`[!success]+` admit / `[!warning]+` reserve / `[!failure]+` reject
- **Breadcrumb** 用 `[!info]` callout（不要裸 `>`）
- **每个 CP H2 标题末尾带档位徽章** `· \`tier\``，阻断档加粗 `· **\`poor\`**` / `· **\`weak\`**` / `· **\`high\`**`
- **CP 正文末尾保留 `→ **tier**`** 行（audit c10 兼容；H2 + 末行双保险）
- **CP03 核心指标用紧凑表**（不要散文 bullets）
- **关键数字 `==highlight==`**：OOS IC / ICIR / ls_t / style_r² / alpha_survival / max_lib_corr / incremental_ic
- **Verdict 段用 callout 包**（与顶部 TL;DR 色号一致）

## `C{id}.md` body — 非-reject 模板

```markdown
# C001 — Std($close, 20)

> [!success]+ Verdict: **ADMIT** · thread [[directions/timing_signals#T001|T001]]
> **档位**: CP01 ✓ · CP02 `aligned` · CP03 `strong` · CP04 `acceptable` · CP05 `low` · CP06 `stable`
> **OOS**: IC=**==0.016==** · ICIR=**==0.338==** · ls_t=**==3.89==** · style_r²=0.08 · alpha_surv=**==0.69==** · max_corr=0.30 · mt_bucket=`medium`
> **机制一句话**: {1 句，≤40 字，对应表达式解读第一段提炼}

> [!info] Parent: [[batches/batch_009/judge|batch_009 judge]] · Direction: [[directions/timing_signals]] · Nearest: [[factors/F005]]

## 表达式解读

{1–3 段自然语言：表达式的经济含义。例如"Std($close, 20) = 20 日收盘价标准差，衡量近期波动率。"}

## CP01 Hard Gates ✓

8 项 gate 全过：
- ✓ compute_error
- ✓ coverage: 0.989 ≥ 0.80
- ✓ sign_flip: train -0.020 / val -0.023（同号）
- ✓ forbidden
- ✓ ic_oos_min: |-0.023| ≥ 0.008
- ✓ oos_decay: 1.12 ≥ 0.20
- ✓ mono_flip: train -0.10 / val -0.10（同号）
- ✓ near_duplicate: max_corr 0.25 < 0.9（nearest F005）

## CP02 Mechanism Alignment · `aligned`

**机制**：{回答第 1 问}

**与 hypothesis 一致性**：[[directions/timing_signals#Hypothesis]] 假设 …；本候选 {回答第 2 问}。

**持续性**：{回答第 3 问}

**失效场景**：{回答第 4 问}

**与近邻差异**：[[factors/F005]] 捕捉 {nearest_factor_expression 的机制}；本候选 {回答第 5 问}。

→ **aligned**

## CP03 Statistical Strength · `strong`

| 指标 | IS | OOS | 档位 | 阈值 |
|---|---|---|---|---|
| IC | 0.018 | **==0.016==** | strong | \|x\|>0.015 |
| ICIR | 0.22 | **==0.338==** | strong | \|x\|>0.30 |
| ls_t | 3.5 | **==3.89==** | strong | \|x\|>3 |
| decay | — | 0.89 | healthy | >0.8 |

**Rank-order 验证**：monotonicity_oos = 0.92（|x| > 0.8 → 强单调）。Q1..Q5 梯度 (OOS): q1=-0.00038, q2=0.00023, q3=0.00074, q4=-0.00050, q5=-0.00029 → 单调不完美（q3 最高），但 ls_mean 由 q5-q1 驱动，与 ls_tstat 一致（非"一桨驱动"）。

**样本量**：n_days_oos=476（>> 200，统计显著性充足）。

**MT 调整**：`mt_bucket = medium`；`search_adjusted = 0.41`（adjusted 档 medium）。medium 档允许 strong 保留，经 search adjustment 后系数仍在 strong 档下界以上，符合 MT budget 容忍阈值。

→ **strong**

## CP04 Risk Cleanness · `acceptable`

| 指标 | 值 | 档位 | 阈值 |
|---|---|---|---|
| style_r_squared | **==0.08==** | clean | <0.08 边界 |
| alpha_survival | **==0.69==** | borderline | clean>0.70 |
| extreme_ratio | 0.008 | clean | <0.01 |
| barra_residual_ic | 0.013 | — | — |
| dominant_style | `vol_20d` | — | — |

**Alpha killer**（按 `metrics.cp04.style_contributions` 排序前 2-3 项，每项写 `{style}: delta_ic={…} ({pct}%)`）：
- `vol_20d`: delta_ic=**==0.025==** (65.8%)
- `turnover_20d`: delta_ic=0.008 (21.1%)
- 总 killer 占比: ~87%，剩余 ~13% 分散在其它 styles 或 joint effect

两项 clean 一项 borderline → **acceptable**

## CP05 Redundancy · `low`

- `max_lib_corr` = **==0.30==** → low 档
- `is_near_duplicate` = false（硬闸未触发）
- nearest = [[factors/F005]]
- `incremental_ic` = **==0.013==**（> 0.005，库增值清晰）

→ **low**。admit 增值：{1–2 句为何能贡献增量 alpha}

## CP06 Validation Stability · `stable`

| 指标 | 值 | 档位 |
|---|---|---|
| sign_consistency | **==1.0==** | stable |
| train_validation_decay | **==0.89==** | stable (>0.8) |

**时序稳健**：
- `ic_autocorr_lag1` = -0.025（|x|<0.15 → IC 日独立，ICIR 置信高）
- `cum_ic_max_drawdown` = -34.69（在 -30 附近，轻度关注）
- `worst_quarter_ic` = -0.071 / `best_quarter_ic` = 0.015（异号但 worst ≈ 3× |ic_oos|）
- `ic_by_year`：{2020: 0.015, 2021: 0.012, 2022: 0.011}（缓慢衰减仍同号）

→ **stable**（核心两项都 stable；时序稳健项均在健康范围；cum_ic_mdd 轻度关注但不降档）

> [!success]+ Verdict: ADMIT
> **核心理由**: {1 段 — 综合 5 个软 CP 档位 + hypothesis 匹配度，为什么值得 admit}
>
> **风险旗标**: {若有 borderline/weak/poor/unstable/mixed/high 项，逐条列出；否则写"无"}
>
> F{id} 由 Phase 4 分配，本文件 frontmatter `factor_id: null`。
```

**reserve 只需把顶部 callout 和底部 callout 换成 `[!warning]+`，verdict 字段写 RESERVE**；结构完全一致。

## `C{id}.md` body — reject 最小模板

```markdown
# C001 — Std($close, 20)

> [!failure]+ Verdict: **REJECT**
> **阻断**: CP01 hard_gate fail — {hints.hard_gate.reasons[0]}
> 其它 gate 结果: {简述 gate_results 里的其它值，证明这是数据/质量问题而非机制问题}

> [!info] Parent: [[batches/batch_001/judge|batch_001 judge]] · Direction: [[directions/volume_price_signal]]

## CP01 Hard Gates

未通过：
- ✗ coverage: 0.65 < 0.80

其它 gate 结果：
- ✓ compute_error
- ✓ forbidden
- （若 coverage 失败则 sign_flip / ic_oos_min 等可能未评估，但仍照实写出 gate_results 中的值）

> [!failure]+ Verdict: REJECT
> {1–2 句具体说明，对应 frontmatter.reject_reason_short。}
```

---

## 写完前自我校验 checklist

- [ ] Frontmatter 字段齐全，`candidate_id` 与文件名一致
- [ ] `verdict` ∈ {admit, reserve, reject}，`thread_id` 指向 direction.md 真实存在的 H3
- [ ] admit 时 `factor_id: null`（不要猜 F{id}）
- [ ] CP03 body 包含 literal 字符串 `mt_bucket` 和 `search_adjusted`
- [ ] CP02 body 含 `[[directions/{DIRECTION}` 开头的 wikilink
- [ ] 每个 CP{2..6} body 包含该 CP 的一个 rubric 档位词
- [ ] 所有 wikilink 用 vault-root（`[[factors/F005]]`），禁止 `../` 前缀
- [ ] `key_metrics_short`（非 reject）或 `reject_reason_short`（reject）已填
- [ ] 返回主 agent 用**结构化一段**格式（含档位 + 指标 + 反思 + 风险旗标），不是一行
