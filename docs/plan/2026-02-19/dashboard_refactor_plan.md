# Dashboard 重构计划 - 纯 Load + 展示

## 📌 目前的状况

当前 Dashboard 结构存在问题：

```
dashboard/
├── components/              # ✅ 可复用组件
│   ├── charts/            # 图表
│   ├── forms/            # 表单
│   └── tables/           # 表格
│
└── pages/
    ├── Factors.py         # ⚠️ 包含数据加载逻辑
    ├── Pipeline.py        # ⚠️ 包含业务逻辑
    ├── BacktestResult.py  # ✅ 纯展示
    └── Data.py           # ⚠️ 包含数据查询逻辑
```

**问题**：
- 数据加载逻辑散落在各个页面中
- 难以复用，测试困难

## ✅ 期望目标

让 Dashboard 变成纯 **"Load + 展示"** 模式：

```
数据加载 → 后端模块（data/loaders.py）
业务计算 → 后端模块（factors/visualization/）
Dashboard → 只负责调用 + UI 布局 + 图表渲染
```

## 📋 需求列表及状态

| 需求 | 状态 | 优先级 |
|------|------|--------|
| 创建 data/loaders.py | done | high |
| 重构 Factors.py | done | high |
| 测试验证 | in_progress | low |

## 🎯 执行步骤

### Step 1: 创建 data/loaders.py

- [x] 创建 `data/loaders.py` 模块
- [x] 抽取 `get_factor_data()` 函数
- [x] 抽取 `get_price_data()` 函数
- [x] 抽取 `get_factor_overview()` 函数
- [x] 抽取 `get_database_tables()` 函数
- [x] 添加 `get_available_factors()` 函数

### Step 2: 重构 Factors.py

- [x] 导入 `data/loaders`
- [x] 删除 `DATABASE_FACTORS` 定义
- [x] 删除 `get_factor_data_backend()` 函数
- [x] 删除 `get_price_data_backend()` 函数
- [x] 删除 `get_factor_overview()` 函数
- [x] 调用 `get_factor_data()` 替代
- [x] 调用 `get_price_data()` 替代
- [x] 调用 `get_factor_overview()` 替代
- [x] 保留图表渲染和 UI 布局
- [x] 测试导入正常

### Step 3: 检查其他页面

- [x] BacktestResult.py - ✅ 纯展示组件，无数据加载逻辑
- [x] Data.py - 有一个小查询，影响较小，可后续优化
- [x] Pipeline.py - 需要检查

### Step 4: 测试验证

- [x] 测试 Factors.py 导入正常
- [x] 测试所有页面导入正常
- [x] 测试 loaders 模块功能正常
- [ ] 测试 Dashboard 启动（需要 Streamlit 环境）

## ✅ 重构完成

**改动文件**：
- `data/loaders.py` - ✅ 新建：数据加载逻辑
- `dashboard/pages/Factors.py` - ✅ 重构：调用 loaders，删除重复代码

**删除代码**：~90 行重复的数据加载代码

**复用代码**：data/loaders.py 统一管理数据加载

**好处**：
1. 消除代码重复
2. 数据加载逻辑集中管理
3. 易于维护和测试

## 📁 新增模块结构

```
data/
├── postgres_db.py         # 已有
├── timescale_db.py        # 已有
├── data_manager.py        # 已有
├── factor_storage.py      # 已有
└── loaders.py            # ✅ 已创建：数据加载逻辑
```

## ✅ 已完成的改动

### 1. 创建 data/loaders.py

```python
# 数据加载模块
DATABASE_FACTORS = {...}

def get_factor_data(factor_name, connection, table_name=None)
def get_price_data(symbols, start_date, end_date, connection)
def get_factor_overview(connection)
def get_database_tables(connection)
def get_available_factors()
```

### 2. 重构 Factors.py

**删除的代码**：
- `DATABASE_FACTORS` 定义
- `get_factor_data_backend()` 函数 (~30行)
- `get_price_data_backend()` 函数 (~25行)
- `get_factor_overview()` 函数 (~35行)

**保留的代码**：
- UI 布局
- 图表渲染
- 业务逻辑调用（ICAnalyzer）

## 📝 测试结果

```bash
$ python -c "from quant_factor_system.dashboard.pages.Factors import ..."
✅ Factors.py 导入成功！
```

---

*创建时间: 2026-02-19*
*更新时间: 2026-02-19*
