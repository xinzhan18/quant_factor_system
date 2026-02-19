# Factors 模块重构计划

## 📌 目前的状况

```
factors/
├── basic/              # 基础因子
├── visualization/     # 可视化
├── pipeline/          # Pipeline（刚移入）
├── aggregator.py     # 聚合器
├── factory.py        # 工厂
├── processor.py      # 处理器
└── registry.py       # 注册表
```

## 🔍 问题分析

| 问题 | 说明 |
|------|------|
| 频率定义重复 | `Frequency` 在 data/storage/frequency.py 和 factors/pipeline/pipeline.py 都有定义 |
| 文件分散 | aggregator, processor, factory, registry 都在根目录 |

## ✅ 优化方案

```
factors/
├── basic/              # 基础因子
├── visualization/     # 可视化
├── processing/       # ⭐ 处理模块（新）
│   ├── aggregator.py
│   ├── processor.py
│   └── factory.py
├── core/             # ⭐ 核心模块（新）
│   ├── registry.py
│   └── pipeline.py
```

## 📋 需求列表及状态

| 需求 | 状态 | 优先级 |
|------|------|--------|
| 创建 factors/processing/ 目录 | todo | medium |
| 移动 aggregator.py | todo | medium |
| 移动 processor.py | todo | medium |
| 移动 factory.py | todo | medium |
| 创建 factors/core/ 目录 | todo | medium |
| 移动 registry.py | todo | medium |
| 移动 pipeline.py | todo | medium |
| 更新导入路径 | todo | medium |
| 测试验证 | todo | low |

---

*创建时间: 2026-02-19*
