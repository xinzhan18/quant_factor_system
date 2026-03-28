---
title: Factor Library
tags:
  - index
---

# Factor Library

> 24 factors | Last updated: 2026-03-28

## 因子总览

```dataview
TABLE
  category AS "类别",
  round(ic_mean_oos, 4) AS "IC (OOS)",
  round(icir_oos, 2) AS "ICIR",
  round(ls_sharpe, 2) AS "L/S Sharpe",
  round(monotonicity, 2) AS "单调性",
  composite_grade AS "评级",
  round(composite_score, 1) AS "评分"
FROM "factors"
WHERE contains(tags, "factor")
SORT id ASC
```

## 按类别统计

```dataview
TABLE length(rows) AS "数量",
  round(avg(rows.ic_mean_oos), 4) AS "平均 IC",
  min(rows.file.link) AS "代表因子"
FROM "factors"
WHERE contains(tags, "factor")
GROUP BY category AS "类别"
SORT length(rows) DESC
```

## 按评级分布

```dataview
TABLE length(rows) AS "数量",
  join(map(rows.file, (f) => f.link), ", ") AS "因子"
FROM "factors"
WHERE contains(tags, "factor")
GROUP BY composite_grade AS "评级"
SORT key DESC
```

## 信号空间状态

> [!abstract] 覆盖情况
> - **Alpha101**: ~45 OHLCV 可翻译公式已评估，12 录取 + 1 替换
> - **相关性阈值**: 0.7
> - **待解锁**: $vwap / 行业 / 市值数据（~55 个 Alpha101 因子被阻塞）
> - **最强因子**: [[F011 williams_r_variant]] (IC +0.071), [[F009 pv_corr_times_vol]] (IC -0.053)
> - **最弱因子**: [[F012 up_day_count_20]] (IC +0.004), [[F006 resi_close_5]] (IC -0.012)
