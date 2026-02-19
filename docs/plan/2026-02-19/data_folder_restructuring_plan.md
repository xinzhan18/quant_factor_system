# Data 模块重构计划 - 按职责拆分

## 📌 目前的状况

当前 data 文件夹结构混乱，职责不清晰：

```
data/
├── __init__.py              # 混合导出
├── ricequant_source.py      # 数据源 ✅
├── timescale_storage.py     # 存储层 ⚠️ 与 timescale_db 重复
├── timescale_db.py         # DB操作 ⚠️ 与 postgres_db 重复
├── postgres_db.py         # DB工具 ⚠️ 定位不清
├── data_manager.py        # 管理器
├── factor_storage.py      # 因子存储
├── factor_version.py     # 因子版本
├── formatter.py          # 格式化工具
├── industry_source.py    # 行业数据
├── loaders.py           # 数据加载 ⭐
└── clean/               # 数据清洗 ✅
    ├── validator.py
    └── __init__.py
```

## 🔍 问题分析

| 模块 | 当前职责 | 问题 |
|------|---------|------|
| `ricequant_source.py` | 米筐数据源 | 单一职责 ✅ |
| `timescale_storage.py` | TimescaleDB 存储 | 约 32KB，与 `timescale_db` 大量重复 |
| `timescale_db.py` | TimescaleDB 操作 | 约 21KB，与 `postgres_db` 重复 |
| `postgres_db.py` | PostgreSQL 工具 | 定位不清，职责与 timescale_db 重叠 |
| `data_manager.py` | 统一数据管理 | 约 7KB，管理逻辑 |
| `factor_storage.py` | 因子存储 | 约 26KB |
| `factor_version.py` | 因子版本 | 约 10KB |
| `formatter.py` | 数据格式化 | 约 23KB |
| `industry_source.py` | 行业数据 | 约 16KB |
| `loaders.py` | 数据加载 | 约 6KB ⭐ 已创建 |
| `clean/` | 数据清洗 | 单一职责 ✅ |

## ✅ 重构方案

按职责拆分为子目录：

```
data/
├── __init__.py              # 统一导出（保持不变）
├── sources/                # 数据源
│   └── ricequant_source.py
│
├── storage/               # 存储层
│   ├── timescale_storage.py   # 主存储（合并 timescale_db 功能）
│   ├── factor_storage.py     # 因子存储
│   └── factor_version.py     # 因子版本
│
├── loaders.py           # 数据加载 ⭐ (已有)
│
├── utils/              # 工具类
│   ├── postgres_db.py      # PostgreSQL 基础操作
│   ├── formatter.py        # 数据格式化
│   └── industry_source.py  # 行业数据
│
└── clean/              # 数据清洗 ✅ (保持不变)
    ├── validator.py
    └── __init__.py
```

## 📋 需求列表及状态

| 需求 | 状态 | 优先级 |
|------|------|--------|
| 创建 storage/ 子目录 | done | high |
| 创建 utils/ 子目录 | done | high |
| 移动 timescale_storage.py | done | high |
| 移动 factor_storage.py | done | high |
| 移动 factor_version.py | done | high |
| 移动 postgres_db.py | done | medium |
| 移动 formatter.py | done | medium |
| 移动 industry_source.py | done | medium |
| 创建 storage/frequency.py | done | medium |
| 创建 storage/db_utils.py | done | medium |
| 更新 storage/__init__.py | done | medium |
| 更新 utils/__init__.py | done | medium |
| 更新 data/__init__.py | done | medium |
| 更新 data_manager.py | done | medium |
| 测试验证 | done | low |

## 🎯 执行步骤

### Step 1: 创建目录结构

- [ ] 创建 `data/storage/` 目录
- [ ] 创建 `data/utils/` 目录

### Step 2: 移动存储相关文件

- [ ] 移动 `factor_storage.py` → `storage/`
- [ ] 移动 `factor_version.py` → `storage/`
- [ ] 移动 `timescale_storage.py` → `storage/`
- [ ] 更新 `storage/__init__.py`

### Step 3: 移动工具类文件

- [ ] 移动 `postgres_db.py` → `utils/`
- [ ] 移动 `formatter.py` → `utils/`
- [ ] 移动 `industry_source.py` → `utils/`
- [ ] 更新 `utils/__init__.py`

### Step 4: 更新导入路径

- [ ] 更新 `data_manager.py`
- [ ] 更新 `__init__.py`
- [ ] 更新其他引用

### Step 5: 测试验证

- [ ] 测试导入正常
- [ ] 测试 Dashboard 启动

## ⚠️ 注意事项

1. **保持向后兼容**：更新 `__init__.py` 导出，让旧导入路径继续工作
2. **相对导入**：移动后的文件需要更新相对导入路径
3. **测试优先**：每移动一个文件就测试一次

## 📝 改动示例

### 移动 factor_storage.py

```bash
# 创建目录
mkdir -p data/storage data/utils

# 移动文件
mv data/factor_storage.py data/storage/
mv data/factor_version.py data/storage/
mv data/timescale_storage.py data/storage/

mv data/postgres_db.py data/utils/
mv data/formatter.py data/utils/
mv data/industry_source.py data/utils/
```

### 更新导入路径

```python
# 更新 data_manager.py
from .storage.timescale_storage import TimescaleDB
from .storage.factor_storage import FactorStorage
from .utils.formatter import DataFormatter
```

---

*创建时间: 2026-02-19*
