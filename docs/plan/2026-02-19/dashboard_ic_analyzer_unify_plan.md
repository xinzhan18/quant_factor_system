# Dashboard 与 ICAnalyzer 逻辑统一计划

## 📌 目前的状况

当前存在代码重复问题：
- **Dashboard** (`dashboard/pages/Factors.py`): 自己实现了一套 IC 计算逻辑
- **ICAnalyzer** (`factors/visualization/ic_analyzer.py`): 独立模块

## ✅ Step 1 & 2: 已检测逻辑

### Dashboard Factors.py 关键函数：
- compute_ic_analysis(): 自己实现 IC 计算
- compute_group_returns(): 分组收益计算

### ICAnalyzer 关键函数：
- compute_ic(): IC 计算逻辑完整
- 提供丰富的可视化方法

## ✅ Step 3: 逻辑差异分析

| 项目 | Dashboard | ICAnalyzer | 结论 |
|------|-----------|------------|------|
| future_return | `shift(-1)` | `shift(-1)` | ✅ 一致 |
| 涨跌停过滤 | `abs() < 0.11` | `abs() < 0.11` | ✅ 一致 |
| IC计算 | `spearman` | `spearman` | ✅ 一致 |
| 滚动IC | 60日窗口 | 60日窗口 | ✅ 一致 |
| 分组标识 | 中文 | 英文 | ⚠️ 已转换 |

## ✅ Step 4: 统一方案

**选择方案A**: Dashboard 调用 ICAnalyzer

**实施步骤**：
1. Dashboard 导入 ICAnalyzer
2. 调用 `analyzer.compute_ic()` 获取 IC 结果
3. 转换分组标识（train→训练集，test→测试集）
4. 调整返回格式兼容 UI

## ✅ Step 5: 已完成的改动

### Dashboard Factors.py 改动：

1. **导入 ICAnalyzer**：
```python
from quant_factor_system.factors.visualization import ICAnalyzer
```

2. **重构 compute_ic_analysis**：
```python
def compute_ic_analysis(factor_df, price_df, split_date, progress_bar=None):
    # 使用 ICAnalyzer 计算
    analyzer = ICAnalyzer()
    ic_result = analyzer.compute_ic(factor_df, price_df, split_date)
    
    # 转换分组标识（英文 → 中文）
    result['all'] = {...}
    result['训练集'] = {...}  # 从 train 转换
    result['测试集'] = {...}  # 从 test 转换
    
    return result
```

### ICAnalyzer 改动：

1. **添加 start/end 字段**：
```python
result[f'start_{period}'] = period_data['time'].min().strftime('%Y-%m-%d')
result[f'end_{period}'] = period_data['time'].max().strftime('%Y-%m-%d')
```

## 📋 需求列表及状态

| 需求 | 状态 | 优先级 |
|------|------|--------|
| 检测 Dashboard IC 计算逻辑 | done | high |
| 检测 ICAnalyzer IC 计算逻辑 | done | high |
| 分析逻辑差异 | done | high |
| 确定统一方案 | done | high |
| 重构 Dashboard 调用 ICAnalyzer | done | medium |
| 测试验证 | in_progress | low |

## 🎯 执行步骤

### ✅ Step 1-4: 已完成

### ✅ Step 5: 重构 Dashboard

- [x] 导入 ICAnalyzer
- [x] 重构 compute_ic_analysis 调用 ICAnalyzer
- [x] 转换分组标识（train→训练集）
- [x] ICAnalyzer 添加 start/end 字段

### Step 6: 测试验证

- [ ] 测试 IC 计算结果一致
- [ ] 测试 Dashboard 正常显示
- [ ] 测试图表渲染正常

## 📝 改动总结

**删除的代码**（Dashboard Factors.py）：
- ~40 行重复的 IC 计算代码

**复用的代码**：
- ICAnalyzer.compute_ic() 的全部逻辑

**添加的代码**：
- 导入语句
- 分组标识转换逻辑
- ICAnalyzer start/end 字段

**好处**：
1. 消除代码重复
2. 逻辑统一，一处修改处处生效
3. 更容易维护
