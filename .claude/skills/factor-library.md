---
name: factor-library
description: 查看和管理因子库
user_invocable: true
---

# 因子库管理

查看和管理已录取的因子。

## 命令

- `/factor-library` 或 `/factor-library status` — 显示因子库概览
- `/factor-library detail <id>` — 显示因子详情
- `/factor-library remove <id>` — 移除因子（需确认）

## 概览视图

```bash
cd /Users/xinzhan/.openclaw/workspace/quant_factor_system
python -m mining.cli library
```

同时读取 `mining/library/library.yaml` 展示完整索引。

## 详情视图

读取 `mining/library/factors/factor_<id>.yaml` 展示完整因子详情，包括：
- 表达式
- 类别
- 所有指标（IC、ICIR、分位数收益）
- 金融逻辑
- 与因子库中其他因子的相关性
