# Dashboard 模块优化计划

## 📌 目前的状况

```
dashboard/
├── Home.py              # 首页
├── config.py            # ⚠️ 未使用
├── start_dashboard.sh   # 启动脚本
├── pages/              # 页面
├── components/         # ✅ 组件已抽取
│   ├── charts/
│   ├── forms/
│   └── tables/
└── factors_registry.csv  # ⚠️ 临时文件
```

## 🔍 问题分析

| 问题 | 说明 | 优先级 |
|------|------|--------|
| config.py | 存在但未使用 | medium |
| factors_registry.csv | 临时文件，应移到 temp/ | medium |
| Pipeline 硬编码因子 | 硬编码因子列表 | medium |

## ✅ 优化方案

```
dashboard/
├── Home.py              # 首页
├── start_dashboard.sh   # 启动脚本
├── pages/              # 页面
├── components/         # 组件
└── page_template.py     # ⭐ 页面模板
```

## 📋 需求列表及状态

| 需求 | 状态 | 优先级 |
|------|------|--------|
| 删除 dashboard/config.py | done | medium |
| 移动 factors_registry.csv → temp/ | done | medium |
| 修复 Pipeline 页面硬编码因子 | done | medium |
| 创建 page_template.py | done | low |

---

*创建时间: 2026-02-19*
*更新时间: 2026-02-19*
