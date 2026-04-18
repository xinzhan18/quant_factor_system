---
name: factor-report
description: Phase 4 后台 subagent — 为 admitted 因子按 F005 模板生成 Obsidian 深度报告
user_invocable: true
---

# /factor-report — 因子深度报告（F005 模板）

为每个 admitted 因子生成 `vault/factors/F{id}.md`。**金标准**：`storage/_legacy/vault_v1/F005 pv_amount_corr_20d_x_tur_rank.md`——新报告的深度、结构、叙事风格对齐 F005。

## 沙箱协议

| # | 规则 |
|---|---|
| 1 | 唯一输入：`_packets/report_packet_F{id}.md` + `vault/factors/F{id}/report.json` |
| 2 | 唯一输出：`vault/factors/F{id}.md` |
| 3 | 禁止：读 Qlib / DB / 网络 / result.yaml / judge.md / factor.yaml 原文件；禁止自行算指标 |
| 4 | 图表白名单：`![[F{id}/<name>.png]]` 仅限 `report.json.charts` 里列出的 basename；**白名单外绝不 embed** |
| 5 | 失败：append `_subagent_failures.log`，主循环不受影响 |

## 数据源

### `report_packet_F{id}.md`（叙事上下文）

由 Phase 4 `report_packer` 打包：
- factor YAML 摘要（`expression` / `family_tag` / `validation_metrics` / `risk_metrics`）
- Direction hypothesis 节选
- Judge Synthesis（C{id}.md 6 CP 推理原文）
- Library context（最近邻 F{近邻} 关系摘要）
- `## Available Charts` 图表白名单

### `report.json`（结构化数据，来自 `render_factor`）

```json
{
  "factor_id": "F042",
  "batch_id": "batch_009",
  "charts": { "ic_timeseries": "ic_timeseries", "quintile_bar": "quintile_bar", ... },
  "composite": { "predictive_power": 96.2, ..., "score": 75.5, "grade": "A" },
  "scalars": {
    "ic_validation": {"ic_mean": -0.065, "ic_ir": -0.54, "ic_std": ..., "ic_win_rate": ..., "n_days": ...},
    "ic_train": {...},
    "ic_by_year": {"2015": -0.04, "2016": -0.05, ...},              // 年度 IC 序列
    "ic_autocorr_lag1": 0.03,                                         // IC 日独立性
    "cum_ic_max_drawdown": -86.23,                                    // 累计 IC 回撤
    "worst_quarter_ic": -0.066, "best_quarter_ic": 0.008,
    "train_validation_decay": 1.015, "sign_consistent": true,
    "ic_by_horizon": {"1": {"train": {...}, "validation": {...}}, "3": {...}, "5": ..., "10": ..., "20": ...},
    "quintile_train": {...}, "quintile_validation": {...},
    "ls_stats_train": {...},  "ls_stats_validation": {"sharpe": -2.65, "sortino": ..., "calmar": ..., "max_dd": ..., "tstat": -3.68, "n_days": ...},
    "uniqueness": {"max_lib_corr": 0.0, "nearest_factor_id": null, "all_correlations": {}, "incremental_ic": ...},
    "barra": {"style_exposures": {"vol_20d": 28.45, ...}, "style_r_squared": 0.28, "barra_residual_ic": ..., "alpha_survival_ratio": 0.378, "dominant_style_exposure": "vol_20d"},
    "feasibility": {"turnover_mean": 0.39, "liquidity_coverage": 0.77, "signal_half_life": 11, "signal_autocorr_lag1": 0.965, "rebalance_stress": 0.0036, ...},
    "distribution": {"zero_ratio": 0, "skew": 0.84, "kurt": 0.45, "extreme_ratio": 0.0009}
  }
}
```

**所有数字从 `report.json.scalars` 取；所有图名查 `report.json.charts` 白名单**。

---

## 数字表格硬要求（R3 单一数据源的落地）

除了"每图三段叙事"之外，报告**必须**在相关小节前给出数值表。表是"文档级单一真理源"——读者不需要翻 YAML/JSON 才知道这个因子在 2018 年 IC 多少。

| 表 | 必放小节 | 数据来源 |
|---|---|---|
| **年度 IC 表**（9 列：年份 × IC）| §3 IC 时序图之前 | `scalars.ic_by_year`（dict 排序后转行）|
| **多持有期 IC 表**（1/3/5/10/20d × IS/OOS × IC/ICIR）| §3 IC 分布之前 | `scalars.ic_by_horizon`（5 × 2 × 2 = 20 格）|
| **五档分组收益表**（IS/OOS × Q1..Q5 + Mono + ls_mean，**年化 %，×252**）| §4 分组年化收益图之前 | `scalars.quintile_train` + `quintile_validation` |
| **L/S 完整统计表**（mean/std/sharpe/sortino/calmar/max_dd/dd_duration/tstat 各一行，IS+OOS 两列） | §4 L/S 净值图之前 | `scalars.ls_stats_train` + `ls_stats_validation` |
| **Barra 风格暴露表**（7 风格 × 暴露值，按 \|x\| 降序）| §5 style_exposure_bar 之前 | `scalars.barra.style_exposures` |
| **Alpha 瀑布分解表**（raw IC / residual IC / residual ICIR / alpha_survival_ratio 四行）| §5 alpha_waterfall 之前 | `scalars.barra` |
| **Alpha 归因表**（style / delta_ic / pct / ic_without 四列，按 \|delta_ic\| 降序，≤7 行）| §5 alpha_waterfall 之后 | `scalars.barra.style_contributions` |
| **时序稳健性表**（sign_consistent / decay / autocorr_lag1 / cum_ic_mdd / worst_q / best_q 各一行）| §6 stability_summary 之前 | 顶层 scalars 多字段 |
| **可交易性表**（turnover / liquidity / small_cap_conc / signal_half_life / signal_autocorr / rebalance_stress 各一行）| §7 factor_distribution 之前 | `scalars.feasibility` |
| **分布矩表**（zero_ratio / skew / kurt / extreme_ratio 各一行）| §7 factor_distribution 之前（与上一张合并或紧邻）| `scalars.distribution` |
| **相关度 top-N 表**（nearest / corr / incremental_ic 各列）| §8 correlation_bar 之前 | `scalars.uniqueness.all_correlations`（排序取前 5–10）|
| **综合评分表**（7 维度 + 总分 + grade）| §9 radar 图之后，作为 radar 的文字补全 | `composite` 全部字段 |

**单位规范**（避免科学计数法遮蔽量级）：
- **五档分组收益表** 和 **L/S 完整统计表的 mean** 一律 **年化 %**（daily mean × 252 × 100），保留 2 位小数，例：`-17.00%`
- 禁用 `7.64e-4` / `6.73e-4` 这类 raw daily mean 的科学计数法（量级不直观）
- 其它比率型指标（IC / ICIR / Mono / Sharpe / t-stat）保留 3–4 位小数，不做单位换算
- 明确单位已在表头或列名标注（如 `q1 年化 %`、`ls_mean 年化 %`）

**原则**（避免"表 + 图重复分析两次"）：
- 表在图**之前**（先把数摆出来，再用图解读），不要放在图后面作附录
- **数字缺 null 就写 `—`**，不伪造、不省略整行
- **表下只给 1 句总结**（整表在说什么的一句话结论，不是逐行复述），**分析放在对应图的"第一/第二/第三"里**。例：
  - ✗ 差：表下三段论 Q5 独塌 + Mono=-0.90 强单调 + IS→OOS 一致（然后图下又把这三点重写一遍）
  - ✓ 对：表下一句"OOS Mono=-0.90 + Q5 独塌 + IS→OOS 一致的三点结论"；图下三段讲**图里肉眼能看但表看不出来**的东西——形态、拐点、regime 切换、时序边界
- **图的三段叙事聚焦"视觉独有信息"**：表格给的是终点快照（均值、档位、总分），图给的是路径（何时发生、怎么演变、是否有断点）。重复"表里已经写过的那个数字是 -0.90" 无意义

---

## 输出结构（11 节，固定）

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
> {1-3 句核心总结：因子赚什么钱、靠什么机制、OOS 关键数字}

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
> {3-5 句：从 judge synthesis + 近邻对比抽取的独特性和风险}

![[F{id}/radar.png|100%]]
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
| {code} | {info\|medium\|high} | {1 句描述} |
```

档位词和 reason codes 从 packet 的 Judge Synthesis 抽取。

---

## 通用小节模板（Section 3-8 每张图都用这个）

```markdown
#### {中文子标题}

> [!info]- 阅读指南
> {1-2 句说明横纵轴 + 色彩编码 + 如何"读懂"}

![[F{id}/{chart_basename}.png|100%]]

**第一，{观察点}。** {深度解读——不只复述数字，要给出因子层面的洞察}

**第二，{观察点}。** {对比 IS vs OOS / 与近邻因子 / 年度或制度切片}

**第三，{观察点}。** {失效场景 / 风险提示 / 与 hypothesis 的呼应}
```

**图在白名单外 → 整个小节（embed + 三段叙事）全部跳过**，不留空占位，不伪造图名。

---

### 3. 预测能力（Predictive Power）

| 子标题 | chart basename | 读图要点 |
|---|---|---|
| IC 时序 + 累积（双面板）| `ic_timeseries` | 上：日 IC（IS/OOS）方向稳定、拐点；下：累积 IC 斜率稳定性 = 长期有效性 |
| 滚动 IC (20/60/120d) | `rolling_ic` | 短中长三窗口一致性；120d 近 0 = 失效预警 |
| IC 分布 | `ic_distribution` | IS/OOS 均值是否同号；OOS 分布是否更宽 |
| 月度 IC 热力图 | `monthly_heatmap` | 季节性、最强/最弱年段、制度相关性 |

### 4. 盈利能力（Profitability）

| 子标题 | chart basename | 读图要点 |
|---|---|---|
| 分组年化收益（IS/OOS）| `quintile_bar` | Q1..Q5 梯度完整性、多空贡献均衡、IS/OOS 一致性 |
| 累积净值 + L/S 叠加 | `cumulative_returns` | Q1-Q5 发散情况 + 黑色虚线 L/S 策略曲线；熊/牛市冲击 |
| 年度分组热力图 | `annual_group_returns` | 年度方向一致性、最差年错位情况 |

### 5. 风险归因（Risk Attribution）

| 子标题 | chart basename | 读图要点 |
|---|---|---|
| Barra 风格因子暴露 | `style_exposure_bar` | 主导风格（dominant_style_exposure）、与近邻因子互补/重叠 |
| Alpha 归因瀑布 | `alpha_waterfall` | Raw \|IC\| → 每个 style 的 leave-one-out 剥离损失 → Barra Residual \|IC\|；killer 按 \|delta_ic\| 降序排在前 |

Alpha waterfall 三段叙事重点：
1. **原始 IC 强度** — 起点 Raw \|IC\| 是裸信号的 rank 预测力
2. **Alpha killer 归因** — 按 `style_contributions` 的 \|delta_ic\| 降序点名前 2–3 个 killer + %；结合 `style_exposure_bar` 看是否与高 exposure 系数吻合（exposure 大但 delta_ic 小 = 该 style 本身预测力弱；exposure 小但 delta_ic 大 = 该 style 与 fwd return 同向共振）
3. **残余 alpha 是否显著** — 终点 Residual \|IC\|，若 `alpha_survival_ratio` < 0.60 叙事必写一条 actionable "下轮需 orthogonalize / normalize by `{top_killer}`"

### 6. 信号稳定性（Stability）

| 子标题 | chart basename | 读图要点 |
|---|---|---|
| 稳定性双面板 | `stability_panel` | 左：各子窗口 ICIR 是否同号；右：IS→Val decay / sign consistency / dispersion 三项总结 |

### 7. 衰减与可交易性（Decay & Tradability）

| 子标题 | chart basename | 读图要点 |
|---|---|---|
| IC 衰减曲线 | `ic_decay` | 持有期 1→60d IC 轨迹；反衰减是稀缺特性 |
| 因子值分布（IS vs OOS）| `factor_distribution` | 分布漂移、极端值占比、偏度/峰度对比 |
| 覆盖率 | `coverage` | 全期稳定性、低覆盖段（新上市/停牌潮） |

### 8. 独特性（Uniqueness）

| 子标题 | chart basename | 读图要点 |
|---|---|---|
| 因子库相关矩阵 | `correlation_bar` | 最高相关的前 N、是否 0.7+ 高重叠、哪些家族天然对冲 |

三段叙事重点：(1) 最高相关是谁、意味着什么 (2) 与近邻的**机制差异** (3) 基于已有库的增量价值（`incremental_ic`）

### 9. 综合评分（Composite Score）

```markdown
![[F{id}/radar.png|100%]]

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
{1-2 段：对应 L{id} logic / hypothesis}

### 经济机制
**第一，{机制点}。** {为什么产生 alpha}
**第二，{机制点}。** {为什么持续}
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
{1-2 段：对 factor library 的贡献；可能衍生的下一个方向}

## Graph Links
- **Hypothesis**: [[{logic_id}]]
- **Family**: [[{family_id}]]
- **Nearest**: [[factors/{nearest_fid}]]
- **See Also**: [[Factor Library]]

%%Report generated: {YYYY-MM-DD} | Source: report_packet + report.json%%
```

---

## 风格硬要求

- **语言**：叙述中文，术语保留英文（IC / ICIR / Sharpe / Barra / Rank / Mono / L/S / Alpha / Barra Residual）
- **编号论证**：每张图的分析"**第一...** / **第二...** / **第三...**" 三段
- **关键数字**：`==highlight==` 突出 OOS ICIR / L/S Sharpe / Mono / alpha_survival 等
- **尖锐判断**：只放 `> [!warning]` / `> [!danger]` callout，不混正文
- **Callout 长度**：≤ 3 行；长分析拆正文
- **绝不编造**：不存在的图绝不 embed；不在 `scalars` 的数字绝不写

## 目标长度

300-450 行。F005 是 498 行——以此为上限参考。

## 完成后

```bash
research commit-report F{id}
```

独立 commit，不合并进 archive 主 commit。
