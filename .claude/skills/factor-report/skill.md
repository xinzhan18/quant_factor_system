---
name: factor-report
description: 为已录取因子生成 Obsidian Markdown 分析报告（含 LLM 叙事分析和 PNG 图表）
user_invocable: true
---

# Factor Report — 资产报告生成

## 目标

仅对 **已录取因子**（admit / replace）生成正式 Obsidian Markdown 报告。reject / near_miss 不生成正式报告。

## 用法

单因子：`/factor-report 001`
全部因子：`/factor-report all`
批次摘要：`/factor-report summary batch_042`

## 流程

### Phase 1：构建报告数据 + PNG

```bash
PYTHONPATH=src python3 -m report.builder --factor-id FACTOR_ID --vault
```

输出：
- `storage/evidence/vault/assets/FXXX/report_data.json`
- `storage/evidence/vault/assets/FXXX/*.png`（18+ 张图表）

### Phase 2：生成 Obsidian Markdown

读取 `report_data.json` + factor registry + judge_report + logic card，生成：

`storage/evidence/vault/factors/FXXX <name>.md`

#### Frontmatter
```yaml
id: "XXX"
name: <name>
category: <category>
source_type: <dsl|python>
logic_id: <logic_id>
route_type: <route_type>
experiment_lineage_tag: <ELT>
family_id: <family_id>
expression: "<expression>"
batch: <batch>
admitted_at: <date>
decision: <admit|replace>
sample_policy_version: research_sample_v3
validation_window_id: val_2022_2023
ic_mean_validation: <value>
ic_ir_validation: <value>
risk_model_review_bucket: <acceptable|borderline|poor>
```

#### 章节结构
1. **基本信息** — 因子 ID / 表达式 / 类别 / ELT / route_type
2. **研究脉络** — logic hypothesis / research question / 为什么是这个 route_type
3. **评估制度** — universe / tradability / preprocess / neutralization / sample_policy
4. **KPI 摘要** — Train vs Validation 表格（IC/ICIR/胜率/Sharpe/单调性）
5. **预测能力** — IC 时序 / 分布 / rolling / expanding / 月度热力图
6. **盈利能力** — 分组收益 / 累积收益 / 多空 / 年度
7. **风险归因** — raw IC / cap-neutral IC / Barra 残差 IC / alpha_survival / dominant style
8. **条件分析** — regime IC / vol regime
9. **衰减与可交易性** — IC decay / autocorrelation / coverage / turnover
10. **独特性** — max_lib_corr / family_overlap / subspace_redundancy / residual_incremental_ic
11. **综合评分** — 雷达图 + 各维度分解
12. **批判性审查** — 一句话毒舌 + 关键弱点 + 改进方向
13. **系统意义** — 验证了什么 / 后续方向

### Phase 3：更新 Factor Library 总览页

`storage/evidence/vault/Factor Library.md`

## 关键约束

- report 不重新计算评估，只消费上游结构化结果
- frontmatter 只放稳定索引字段，不放 narrative
- 数值字段必须来自结构化结果，不由 LLM 总结
- composite_score 不进 frontmatter，只在正文展示
- report 只读取 **guarded_writer 落地后的最终状态**（不是中间 recommendation）
- quick_execute / freeze_recommendation 只作为研究脉络说明，不作为 admit 证据
