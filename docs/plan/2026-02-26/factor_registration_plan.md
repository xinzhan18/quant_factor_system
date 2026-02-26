# 因子研究流程化 Plan

## 📌 目标

将日内动量因子完整注册到系统，并记录研究方法

---

## ✅ 需求列表

| 需求 | 状态 | 说明 |
|------|------|------|
| 注册因子到数据库 | todo | 在 factor_config 中注册 |
| 保存因子数据到数据库 | todo | 存入 factor_intraday_momentum 表 |
| Dashboard 显示因子 | todo | 在因子评估页面能看到 |
| 记录研究方法 | todo | 写文档说明流程 |

---

## 🎯 任务详情

### 1. 注册因子 (因子名: intraday_momentum)

```python
# 注册因子配置
db.register_factor(
    name='intraday_momentum',
    frequency='daily',      # 日线级别因子
    storage_type='timeseries',
    display_name='日内动量因子',
    category='technical',
    description='衡量日内形态的1日变化率，公式: -1 * delta((((close-low)-(high-close))/(high-low)), 1)'
)
```

### 2. 保存因子数据

- 生成 2015-2024 全量因子数据
- 保存到 `factor_intraday_momentum` 表
- 包含: symbol, time, value

### 3. Dashboard 集成

- 确保因子在 Dashboard 因子列表中可见
- 能够选择该因子进行 IC 分析

### 4. 记录研究方法

- 文档位置: `docs/因子研究流程.md`
- 包含:
  - 因子构建逻辑
  - 分析方法 (AlphaLens 风格)
  - 数据要求 (2015-至今)
  - 如何注册新因子
  - 如何在 Dashboard 查看

---

## 🔄 标准研究流程

```
1. 构建因子 → 2. 计算 IC → 3. 分组收益分析 → 4. 注册到数据库 → 5. Dashboard 查看
```

---

*Plan created: 2026-02-26*
