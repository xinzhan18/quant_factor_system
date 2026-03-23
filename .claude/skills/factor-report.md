---
name: factor-report
description: Generate a publication-quality HTML report for an admitted factor
user_invocable: true
---

# Factor Report Generator

Generate a comprehensive HTML factor analysis report with LLM narrative.

## Usage

```
/factor-report 001
```

## Three-Stage Pipeline

### Stage 1: Build report data (Python)

```bash
cd /Users/xinzhan/.openclaw/workspace/quant_factor_system
python3 -m mining.report.builder --factor-id FACTOR_ID --output-dir /tmp/factor_report_FACTOR_ID
```

This computes all metrics (IC, distribution, quintile, decay, composite scores) and generates Plotly charts.

### Stage 2: Write narrative (LLM)

Read `/tmp/factor_report_FACTOR_ID/report_data.json` using the Read tool.

Then write `/tmp/factor_report_FACTOR_ID/narrative.json` following this EXACT JSON schema. You must write as a **senior quantitative analyst** with deep industry knowledge. All narrative is in **Chinese** with English technical terms inline.

```json
{
  "factor_metadata": {
    "name_cn": "Chinese name for the factor",
    "expression_latex": "LaTeX formula for MathJax rendering, e.g. \\sigma_{20} = \\text{Std}\\left(\\frac{P_t}{P_{t-1}} - 1,\\; 20\\right)"
  },
  "construction_logic": {
    "formula_decomposition": "Step-by-step breakdown of the Qlib expression into mathematical operations. Show intermediate computations. 200+ words.",
    "parameter_rationale": "Why this specific window/parameter was chosen. Reference batch history if relevant. 150+ words.",
    "preprocessing_notes": "What preprocessing was applied and what was NOT applied (e.g., no neutralization). 100+ words."
  },
  "economic_interpretation": {
    "theoretical_foundations": "Core academic theory behind the factor. Not a textbook summary — explain why the anomaly persists and what market frictions sustain it. 200+ words.",
    "attribution_angles": [
      {"title": "角度名 English Name", "icon": "emoji", "body": "Mechanism explanation, key academic reference, A-share relevance. 80+ words."},
      {"title": "...", "icon": "...", "body": "..."},
      {"title": "...", "icon": "...", "body": "..."},
      {"title": "...", "icon": "...", "body": "..."}
    ],
    "china_context": "Institutional features of A-shares that amplify or attenuate the factor: T+1, price limits, short-selling constraints, retail dominance. 150+ words."
  },
  "section_interpretations": {
    "distribution": "Analyze distribution shape, stability across IS/OOS periods, extreme value characteristics. Reference SPECIFIC numbers from report_data. 100+ words.",
    "ic_annual": "Analyze year-over-year IC trends, which market regimes the factor works best/worst in. Reference SPECIFIC annual IC values. 100+ words.",
    "ic_monthly": "Seasonal patterns in the IC heatmap. Which months are strongest/weakest and why. 80+ words.",
    "quintile": "Monotonicity analysis, practical investability (can you short Q5 in A-shares?), IS/OOS consistency. Reference SPECIFIC quintile returns. 100+ words.",
    "decay": "Half-life estimation, turnover implications, recommended holding period. Reference SPECIFIC decay ratios. 100+ words.",
    "composite": "Holistic assessment — what role does this factor play? Alpha source or risk control tool? Reference SPECIFIC dimension scores. 100+ words."
  },
  "critical_review": {
    "one_liner": "One devastating sentence summarizing the factor's biggest flaw. Must be sharp and witty.",
    "body": "3-4 paragraphs of substantive criticism. MUST reference specific numbers from the report. Address: signal strength in practice, crowding/alpha decay, structural weaknesses, comparison with industry standards. 300+ words. Be harsh but data-backed.",
    "key_weaknesses": [
      {"title": "弱点标题", "detail": "One sentence with specific number"},
      {"title": "...", "detail": "..."},
      {"title": "...", "detail": "..."},
      {"title": "...", "detail": "..."}
    ],
    "improvement_directions": [
      "Actionable suggestion 1 with specific technique",
      "Actionable suggestion 2",
      "Actionable suggestion 3",
      "Actionable suggestion 4"
    ]
  }
}
```

**Critical rules for narrative quality:**
- Every paragraph MUST reference specific numbers from report_data.json
- Provide 3-4 DISTINCT theoretical angles for economic interpretation
- Include A-share market specific context (T+1, price limits, short-selling constraints)
- Critical review must be sharp, witty, data-backed — not generic criticism
- Each LLM interpretation box should draw a NON-OBVIOUS conclusion from the data
- The `expression_latex` must be valid LaTeX that MathJax can render

### Stage 3: Render HTML (Python)

```bash
python3 -m mining.report.renderer --input-dir /tmp/factor_report_FACTOR_ID --output-dir mining/reports/
```

### Stage 4: Open in browser

```bash
open mining/reports/factor_FACTOR_ID_report.html
```

Report the output path to the user.
