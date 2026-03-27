---
name: factor-report
description: 为已录取因子生成出版级 HTML 分析报告
user_invocable: true
---

# 因子报告生成器

生成包含 LLM 叙事分析的综合 HTML 因子分析报告。

## 用法

```
/factor-report 001
```

## 三阶段管道

### 第1阶段：构建报告数据（Python）

```bash
cd /Users/xinzhan/.openclaw/workspace/quant_factor_system
python3 -m mining.report.builder --factor-id FACTOR_ID --output-dir /tmp/factor_report_FACTOR_ID
```

计算所有指标（IC、分布、五分位、衰减、综合评分）并生成 Plotly 图表。

### 第2阶段：撰写叙事分析（LLM）

使用 Read 工具读取 `/tmp/factor_report_FACTOR_ID/report_data.json`。

然后按照以下 JSON 结构写入 `/tmp/factor_report_FACTOR_ID/narrative.json`。你必须以**资深量化分析师**的视角撰写，具备深厚的行业知识。所有叙事使用**中文**，技术术语保留英文。

```json
{
  "factor_metadata": {
    "name_cn": "因子中文名称",
    "expression_latex": "MathJax 渲染用的 LaTeX 公式，如 \\sigma_{20} = \\text{Std}\\left(\\frac{P_t}{P_{t-1}} - 1,\\; 20\\right)"
  },
  "construction_logic": {
    "formula_decomposition": "逐步拆解 Qlib 表达式的数学运算，展示中间计算过程。200+ 字。",
    "parameter_rationale": "为什么选择这个特定窗口/参数。如相关，引用批次历史。150+ 字。",
    "preprocessing_notes": "应用了什么预处理，以及什么没有应用（如未做中性化）。100+ 字。"
  },
  "economic_interpretation": {
    "theoretical_foundations": "因子背后的核心学术理论。不是教科书摘要 — 解释为什么异象持续存在，什么市场摩擦支撑了它。200+ 字。",
    "attribution_angles": [
      {"title": "角度名 English Name", "icon": "emoji", "body": "机制解释、关键学术引用、A股相关性。80+ 字。"},
      {"title": "...", "icon": "...", "body": "..."},
      {"title": "...", "icon": "...", "body": "..."},
      {"title": "...", "icon": "...", "body": "..."}
    ],
    "china_context": "A股市场放大或削弱该因子的制度特征：T+1、涨跌停、融券限制、散户主导。150+ 字。"
  },
  "section_interpretations": {
    "distribution": "分析分布形态、样本内/外稳定性、极端值特征。引用 report_data 中的具体数字。100+ 字。",
    "ic_annual": "分析 IC 年度趋势，因子在哪些市场环境下表现最好/最差。引用具体年度 IC 值。100+ 字。",
    "ic_monthly": "IC 热力图中的季节性规律。哪些月份最强/最弱及原因。80+ 字。",
    "quintile": "单调性分析、实际可投资性（A股能做空 Q5 吗？）、样本内外一致性。引用具体五分位收益。100+ 字。",
    "decay": "半衰期估计、换手率影响、推荐持仓周期。引用具体衰减比率。100+ 字。",
    "composite": "整体评估 — 该因子扮演什么角色？Alpha 来源还是风控工具？引用具体维度评分。100+ 字。"
  },
  "critical_review": {
    "one_liner": "一句毒舌总结因子最大的缺陷。必须尖锐且机智。",
    "body": "3-4 段实质性批评。必须引用报告中的具体数字。涵盖：实际信号强度、拥挤度/Alpha 衰减、结构性弱点、与行业标准的对比。300+ 字。严厉但有数据支撑。",
    "key_weaknesses": [
      {"title": "弱点标题", "detail": "一句话附具体数字"},
      {"title": "...", "detail": "..."},
      {"title": "...", "detail": "..."},
      {"title": "...", "detail": "..."}
    ],
    "improvement_directions": [
      "可操作的改进建议1，附具体技术",
      "可操作的改进建议2",
      "可操作的改进建议3",
      "可操作的改进建议4"
    ]
  }
}
```

**叙事质量关键规则：**
- 每段必须引用 report_data.json 中的具体数字
- 经济解释提供 3-4 个不同的理论角度
- 包含 A 股市场特定背景（T+1、涨跌停、融券限制）
- 批评审查必须尖锐、机智、有数据支撑 — 不要泛泛而谈
- 每个 LLM 解读框应从数据中得出非显而易见的结论
- `expression_latex` 必须是 MathJax 可渲染的有效 LaTeX

### 第3阶段：渲染 HTML（Python）

```bash
python3 -m mining.report.renderer --input-dir /tmp/factor_report_FACTOR_ID --output-dir mining/reports/
```

### 第4阶段：在浏览器中打开

```bash
open mining/reports/factor_FACTOR_ID_report.html
```

向用户报告输出路径。
