---
name: factor-report
description: Phase 4 后台 subagent — 为 admitted 因子按 F005 模板生成 Obsidian 深度报告
user_invocable: true
---

# /factor-report — 因子深度报告（F005 模板）

## 职责

为每个 admitted 因子生成 `vault/factors/F{id}.md`。**金标准参考**：`storage/_legacy/vault_v1/F005 pv_amount_corr_20d_x_tur_rank.md`。新报告的深度、结构、叙事风格必须对齐 F005。

## 沙箱协议（5 条）

| # | 规则 |
|---|---|
| 1 | 唯一输入：`_packets/report_packet_F{id}.md` + `vault/factors/F{id}/report.json`（`render_factor` 产出，内含 `charts` 白名单 + `composite` 得分 + `scalars` 全量指标） |
| 2 | 唯一输出：`vault/factors/F{id}.md` |
| 3 | 禁止：读 Qlib / DB / 网络 / result.yaml / judge.md / factor.yaml 原文件；禁止自行算指标 |
| 4 | 图表白名单：`![[F{id}/<name>.png]]` 仅限 `report.json.charts` 里列出的 basename；白名单外绝不 embed |
| 5 | 失败：append `_subagent_failures.log`，主循环不受影响 |

## 数据源

### `report_packet_F{id}.md`（叙事上下文）

由 Phase 4 `report_packer` 打包，包含：
- factor YAML 摘要（`expression`, `family_tag`, `validation_metrics`, `risk_metrics`）
- Direction hypothesis 节选
- Judge Synthesis — C{id}.md 原文（6 CP 推理）
- Library context — 最近邻 F{近邻} 的关系摘要
- `## Available Charts` — 图表白名单

### `report.json`（结构化数据）

由 Phase 4 `render_factor` 产出。Schema：

```json
{
  "factor_id": "F042",
  "batch_id": "batch_009",
  "charts": {
    "ic_timeseries": "ic_timeseries",
    "quintile_bar": "quintile_bar",
    "radar": "radar",
    "...": "..."
  },
  "composite": {
    "predictive_power": 96.2,
    "signal_stability": 72.3,
    "profitability": 100.0,
    "monotonicity": 100.0,
    "oos_robustness": 60.3,
    "uniqueness": 0.0,
    "decay_resistance": 100.0,
    "score": 75.5,
    "grade": "A"
  },
  "scalars": {
    "ic_validation": {"ic_mean": -0.065, "ic_ir": -0.54, ...},
    "ic_train": {...},
    "quintile_validation": {...},
    "ls_stats_validation": {"sharpe": 3.66, "tstat": -6.27, ...},
    "uniqueness": {...},
    "barra": {...},
    "feasibility": {...},
    "distribution": {...}
  }
}
```

所有数字都在 `report.json.scalars` 里取；所有图名都查 `report.json.charts` 白名单。

## 输出 Markdown 结构（固定 11 节）

### 0. Frontmatter

```yaml
---
id: "F{id}"
name: <factor name>
tags: [factor, <family_tag>, grade-<A|B|C|D>]
category: <family_tag>
source_type: <dsl|python>
expression: <raw DSL>
direction: <direction tag>
batch: <batch_id>
admitted_at: <iso>
decision: admit
composite_grade: <A|B|C|D>
composite_score: <0-100>
ic_mean_validation: <float>
ic_ir_validation: <float>
monotonicity_validation: <float>
alpha_survival_ratio: <float>
max_lib_corr: <float>
---
```

### 1. 标题 + TL;DR + 指标快表

```markdown
# F{id} — {name}

> [!success] Verdict: ADMIT | Grade: =={grade}== ({score}/100)
> {1-3 句核心总结：这因子赚什么钱、靠什么机制、OOS 表现关键数字}

| Metric | In-Sample | Out-of-Sample |
|---|---|---|
| Rank IC Mean | ... | =={val}== |
| Rank ICIR | ... | =={val}== |
| Win Rate | ... | ... |
| t-stat | ... | =={val}== |
| Monotonicity (val) | — | =={val}== |
| L/S Sharpe | — | =={val}== |
| Alpha Survival | — | =={val}== |

> [!tip] 核心判断
> {3-5 句：从 judge synthesis + 近邻对比中抽取的独特性和风险}

![[F{id}/radar.png|500]]
```

### 2. Judge Verdict

```markdown
## Judge Verdict

> [!abstract] 6-Dimension Assessment
> Effect=**{strong|borderline|weak}**, Stability=**{stable|mixed|unstable}**,
> Redundancy=**{low|medium|high}**, Feasibility=**{ok|limited}**,
> Risk Model=**{good|acceptable|borderline|poor}**, Mechanism=**{aligned|mixed|misaligned}**

### Reason Codes

| Code | Severity | 含义 |
|---|---|---|
| {code} | {info|medium|high} | {1 句描述} |
```

从 packet 中的 Judge Synthesis 抽档位词和 reason codes。

### 3. 预测能力（Predictive Power）

对每个白名单内的图表，写一段**三段式叙事**（这是 F005 的核心模式）：

```markdown
#### {子标题}

> [!info]- 阅读指南
> {1-2 句说明横纵轴 + 色彩编码}

![[F{id}/{chart_name}.png|600]]

**第一，{观察点}。** {深度解读——不只是复述数字}

**第二，{观察点}。** {对比 IS/OOS 或同族因子}

**第三，{观察点}。** {失效场景 / 风险提示}
```

子图（白名单里有就写，没有就跳过整段）：
- IC 时序走势 (`ic_timeseries`)
- 累积 IC (`cumulative_ic`)
- 滚动 IC (`rolling_ic`)
- IC 分布 (`ic_distribution`)
- 月度 IC 热力图 (`monthly_heatmap`)

### 4. 盈利能力（Profitability）

- 分组年化收益 (`quintile_bar`)
- 验证期分组收益 (`quintile_returns_oos`)
- 累积净值曲线 (`cumulative_returns`)
- 多空策略表现 (`long_short`)
- 年度分组热力图 (`annual_group_returns`)

### 5. 风险归因（Risk Attribution）

- Barra 风格因子暴露 (`style_exposure_bar`)
- Alpha 存活瀑布 (`alpha_waterfall`)

### 6. 信号稳定性（Stability）

- 多验证窗口 IC (`support_window_ic`)
- 稳定性综合 (`stability_summary`)

### 7. 衰减与可交易性（Decay & Tradability）

- IC 衰减 (`ic_decay`)
- 因子值分布 (`factor_distribution`)
- 覆盖率 (`coverage`)

### 8. 独特性（Uniqueness）

- 因子库相关矩阵 (`correlation_bar`)

### 9. 综合评分（Composite Score）

```markdown
![[F{id}/radar.png|600]]

| 维度 | 得分 | 解读 |
|---|---|---|
| Predictive Power | {score} | {1 句} |
| Signal Stability | {score} | ... |
| Profitability | {score} | ... |
| Monotonicity | {score} | ... |
| OOS Robustness | {score} | ... |
| Uniqueness | {score} | ... |
| Decay Resistance | {score} | ... |
```

### 10. 研究脉络与经济机制

```markdown
> [!note]- 研究脉络与经济机制

### 市场假说
{1-2 段：对应的 L{id} logic / hypothesis}

### 经济机制
**第一，{机制点}。** {为什么会产生 alpha}
**第二，{机制点}。** {为什么会持续}
**第三，{机制点}。** {什么时候失效}

### 实验设计
{本因子在 batch 中的位置、同批对比因子、决策要点}
```

### 11. 批判性审查 + 系统意义 + Graph Links

```markdown
## 批判性审查

> [!danger]- 批判性审查

> [!danger] 一句话毒舌
> {尖锐揭露因子本质短板的一句话}

### 致命弱点

1. {编号深度分析}
2. ...
3. ...

### 改进方向

1. ...
2. ...

> [!warning] 使用警告
> {实盘部署必须注意的风险}

## 系统意义

> [!tip]- 系统意义
### 验证了什么 / 后续方向
{1-2 段：对整个 factor library 的贡献；可能衍生出的下一个方向}

## Graph Links
- **Hypothesis**: [[{logic_id}]]
- **Family**: [[{family_id}]]
- **Nearest**: [[factors/{nearest_fid}]]
- **See Also**: [[Factor Library]]

%%Report generated: {YYYY-MM-DD} | Source: report_packet + report.json%%
```

## 风格硬要求

- **语言**：分析叙述用中文；术语保留英文（IC / ICIR / Sharpe / Barra / Rank / Mono / L/S / Alpha / Barra Residual）
- **编号论证**：每张图的分析必须"**第一...** / **第二...** / **第三...**" 三段
- **关键数字**：用 `==highlight==` 突出 OOS ICIR、L/S Sharpe、Mono、alpha_survival 这类核心数字
- **尖锐判断**：只放进 `> [!warning]` / `> [!danger]` callout，不要混在正文
- **Callout 长度**：不超过 3 行；长分析拆到正文
- **绝不编造**：不存在的图名绝不 embed，不在 `report.json.scalars` 的数字绝不写

## 目标长度

300-450 行。比现在主流报告（~180 行）显著更深。F005 是 498 行 —— 以此为上限参考。

## 完成后

```bash
research commit-report F{id}
```
（独立 commit，不合并进 archive 主 commit）
