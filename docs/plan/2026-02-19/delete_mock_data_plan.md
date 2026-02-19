# Data 模块重构计划 - 删除模拟数据逻辑

## 📌 目前的状况

当前 data 文件夹包含一些**模拟数据**相关的文件和代码：

| 文件 | 类型 | 说明 |
|------|------|------|
| `data/simulator.py` | 文件 | 生成模拟股票数据用于测试 |
| `data/sample_price.csv` | 文件 | 示例价格数据 (~43KB) |
| `data/data_manager.py` | 文件 | 包含 `create_multi_stock_data` 调用 |

**问题**：
- 模拟数据逻辑与真实数据逻辑混在一起
- 占用空间（sample_price.csv ~43KB）
- 可能造成混淆

## ✅ 决策

**删除所有模拟数据相关代码和文件**

## 📋 需求列表及状态

| 需求 | 状态 | 优先级 |
|------|------|--------|
| 删除 data/simulator.py | todo | high |
| 删除 data/sample_price.csv | todo | high |
| 删除 data_manager.py 中的模拟数据调用 | todo | high |
| 更新 data/__init__.py 导出 | todo | medium |
| 更新其他引用 | todo | medium |
| 测试验证 | todo | low |

## 🎯 执行步骤

### Step 1: 删除模拟数据文件

- [x] 删除 `data/simulator.py`
- [x] 删除 `data/sample_price.csv`

### Step 2: 重构 data_manager.py

- [x] 删除 `from .simulator import create_multi_stock_data`
- [x] 删除 `create_multi_stock_data()` 调用
- [x] 删除相关注释

### Step 3: 更新 __init__.py

- [ ] 检查并更新 `data/__init__.py` 导出

### Step 4: 检查其他引用

- [x] 检查无其他引用（只有 data_manager.py）

### Step 5: 测试验证

- [x] 测试导入正常
- [x] 测试 Dashboard 导入正常

## 📝 改动总结

**删除的文件**：
- `data/simulator.py` - 模拟数据生成器
- `data/sample_price.csv` - 示例数据 (~43KB)

**修改的文件**：
- `data/data_manager.py` - 删除模拟数据调用

**删除的代码**：
- `from .simulator import create_multi_stock_data`
- ~25 行模拟数据生成逻辑

**好处**：
1. 减少代码体积
2. 消除模拟/真实数据的混淆
3. 简化 DataManager 逻辑

---

*创建时间: 2026-02-19*
*更新时间: 2026-02-19*
