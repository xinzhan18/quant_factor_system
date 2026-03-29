---
name: factor-logic
description: 创建或查看市场逻辑假设（L4 外循环）
user_invocable: true
---

# /logic — Market Logic Management

## /logic new — 生成新的市场逻辑（外循环）

### Step 1: 读取当前状态

```bash
PYTHONPATH=src python3 -m mining logic coverage
PYTHONPATH=src python3 -m mining logic list
cat storage/memory/forbidden.yaml
```

### Step 2: 识别空白区域

基于 coverage map，找出哪些 taxonomy categories 覆盖不足：
- market_structure, volume_price, volatility, microstructure, cross_sectional, tail_risk, multi_scale

优先为覆盖为 0 的 category 生成逻辑。

### Step 3: 生成市场逻辑

对每个空白 category，提出 2-3 个具体的市场逻辑假设，结构化为：
- **condition**: 什么市场状态会触发这个信号
- **behavior**: 触发后会发生什么
- **timeframe**: 在什么时间尺度上
- **direction**: 做多还是做空

示例:
```yaml
name: 缩量横盘后放量突破
category: volume_price
hypothesis:
  condition: "成交量连续 N 天低于均值，价格振幅收窄"
  behavior: "后续放量突破，方向跟随突破方向"
  timeframe: "5-20 交易日"
  direction: long_on_breakout
constraints:
  required_fields: [volume, close, high, low]
  suggested_ops: [Std, Mean, CsRank, TsDecay]
  window_range: [5, 60]
```

### Step 4: 写入逻辑文件

对每个审批通过的逻辑：

```python
from mining.logic_library import MarketLogicLibrary
lib = MarketLogicLibrary("storage/logic")
lib.create(name=..., category=..., hypothesis=..., constraints=...)
```

### Step 5: 确认

```bash
PYTHONPATH=src python3 -m mining logic list
PYTHONPATH=src python3 -m mining logic coverage
```

## /logic review — 查看逻辑状态

```bash
PYTHONPATH=src python3 -m mining logic schedule
PYTHONPATH=src python3 -m mining logic list
PYTHONPATH=src python3 -m mining logic coverage
```

展示调度器建议，帮助用户决定下一步行动。
