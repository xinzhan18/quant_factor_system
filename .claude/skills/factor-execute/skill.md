---
name: factor-execute
description: 评估最新的候选因子批次，运行多阶段筛选管道
user_invocable: true
---

# 因子评估执行 — /execute

找到待评估的候选批次，运行评估管道，生成结果文件。

## 第1步：查找待评估批次

扫描 `storage/candidates/` 目录：
- 找编号最大的 `batch_XXX.yaml`，且不存在对应的 `batch_XXX_result.yaml`
- 如果所有批次都已评估 → 提示用户："没有待评估的批次。请先运行 `/idea` 生成候选。"

## 第2步：运行评估

执行 CLI 命令（**注意：不加 `--admit`，加 `--skip-stage1`**）：

```bash
PYTHONPATH=src python3 -m mining batch storage/candidates/batch_XXX.yaml --skip-stage1
```

**`--skip-stage1` 说明**：候选因子在 `/idea` 的 Probe 阶段已经用全量股票 + 1年数据验证过 IC，不需要再用 50 只股票做快筛。跳过 Stage 1 直接进入 Stage 2（相关性检查）。

**其他参数：**
- `--train-start` / `--train-end` — 训练期（默认 2020-01-01 ~ 2024-12-31）
- `--test-start` — 测试期开始（默认 2024-07-01）

评估管道执行：
1. **Stage 0**：表达式语法验证
2. ~~Stage 1：快速 IC 筛选~~ — 已跳过（Probe 已验证）
3. ~~Stage 1.5：批内去重~~ — 已跳过
4. **Stage 2**：与因子库相关性检查（阈值 0.7）
5. **Stage 2.5**：替换检查（被拒因子是否能替换库中弱因子）
6. **Stage 3**：6 维报告卡计算（30 个指标）

## 第3步：验证结果

检查 `storage/candidates/batch_XXX_result.yaml` 已生成。

## 第4步：打印摘要

```
=== 评估完成: 批次 XXX ===
筛选通过: N 个
淘汰: M 个
替换候选: K 个
结果文件: storage/candidates/batch_XXX_result.yaml
```

**注意**：评估同时会生成 `batch_XXX_values.pkl` 缓存文件，存储 screened 因子的完整因子值。此缓存供 `/judge` 录取时写入 DB，judge 完成后会自动删除。

提示用户：

> 评估完成。运行 `/judge` 进行 LLM 审判，或 `/mine` 继续完整流程。

---

## 预处理说明

评估器自动进行预处理，无需手动配置：

- **股票池过滤**：排除停牌股和涨跌停股
- **因子清洗**：inf→NaN，MAD 缩尾（5倍），zscore 标准化
- **收益率遮罩**：不可交易股票的前向收益率设为 NaN

可通过 `MiningConfig` 调整：
- `filter_suspend` / `filter_limit` — 股票池过滤（默认 True）
- `winsorize_method` / `winsorize_n` — 异常值处理（默认 "mad" / 5.0）
- `standardize_method` — "zscore" 或 "rank"（默认 "zscore"）
- `neutralize_mode` — "none", "market_cap", "industry", "both"（默认 "none"）
