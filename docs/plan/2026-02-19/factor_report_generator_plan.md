# 因子研究报告生成计划

## 📌 需求

```
用户场景：
1. 创建因子进行探索性研究
2. 不存入数据库
3. 生成 HTML 报告
4. 保存到 output/ 目录
5. 文件名: {因子名}_{时间戳}.html
```

## ✅ 已完成

- [x] 创建 output/factors 目录
- [x] 创建 factors/report/ 目录
- [x] 实现 FactorReportGenerator
- [x] 支持 IC 分析可视化
- [x] 支持分组收益可视化
- [x] 生成 HTML 报告
- [x] 更新 factors/__init__.py

## 📋 任务列表

| 任务 | 状态 | 优先级 |
|------|------|--------|
| 创建 output/factors 目录 | done | high |
| 创建 factors/report/ 目录 | done | high |
| 实现 FactorReportGenerator | done | high |
| 支持 IC 分析可视化 | done | high |
| 支持分组收益可视化 | done | medium |
| 生成 HTML 报告 | done | high |
| 更新 factors/__init__.py | done | low |

## 📊 报告内容

| 模块 | 内容 |
|------|------|
| 因子基本信息 | 名称、参数、描述 |
| IC 分析 | IC时间序列、IC分布、统计信息 |
| 分组收益 | 各分位组收益、月度收益 |
| 因子统计 | 描述性统计、分布 |
| 图表可视化 | 图表嵌入 HTML |

## 💡 使用方式

```python
from quant_factor_system.factors import create_factor_report

# 创建因子
from quant_factor_system.factors import FactorFactory
momentum = FactorFactory.create('momentum', {'period': 20})

# 创建报告
report = create_factor_report(
    name='momentum_20',
    factor=momentum,
    price_data=price_data,
    output_dir='output/factors'
)

# 生成报告
report.analyze()
report.generate()

# 打开报告
report.open()
```

## 📁 输出文件

```
output/factors/
└── momentum_20_20260219_232839.html
```

---

*创建时间: 2026-02-19*
*更新时间: 2026-02-19*
