# Data 模块重构计划 - 按职责拆分

## ✅ 重构完成

**新结构**：

```
data/
├── __init__.py              # 统一导出
├── ricequant_source.py      # 数据源
├── data_manager.py          # 数据管理
├── loaders.py             # 数据加载 ⭐
├── clean/                 # 数据清洗
│   ├── validator.py
│   └── __init__.py
├── storage/              # 存储层 ⭐ 新建
│   ├── timescale_storage.py
│   ├── factor_storage.py
│   ├── factor_version.py
│   ├── frequency.py       # 频率常量
│   ├── db_utils.py        # 数据库工具
│   └── __init__.py
└── utils/               # 工具类 ⭐ 新建
    ├── postgres_db.py
    ├── formatter.py
    ├── industry_source.py
    └── __init__.py
```

## 📋 完成的任务

| 任务 | 状态 |
|------|------|
| 创建 storage/ 子目录 | ✅ |
| 创建 utils/ 子目录 | ✅ |
| 移动 timescale_storage.py | ✅ |
| 移动 factor_storage.py | ✅ |
| 移动 factor_version.py | ✅ |
| 移动 postgres_db.py | ✅ |
| 移动 formatter.py | ✅ |
| 移动 industry_source.py | ✅ |
| 创建 storage/frequency.py | ✅ |
| 创建 storage/db_utils.py | ✅ |
| 创建 __init__.py 文件 | ✅ |
| 修复导入问题 | ✅ |
| 测试验证 | ✅ |

## 测试结果

```bash
✅ 所有模块导入成功
✅ Dashboard 页面导入成功
```

---

*创建时间: 2026-02-19*
*更新时间: 2026-02-19*
