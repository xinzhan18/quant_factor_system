---
name: factor-execute
description: 对冻结的候选因子批次运行正式研究评估管道，生成结构化证据和 judge_packet
user_invocable: true
---

> **⚠️ 自主模式**：本 skill 执行时不得停下来询问用户。pipeline 报错跳过该因子继续处理其余。只在系统级错误（DB 挂、磁盘满）时停止。

# Factor Execute — 正式研究评估

## 目标

对冻结在 `manifest.yaml` 中的候选因子运行完整评估管道，产出结构化统计证据和压缩的 judge_packet。

## 流程

### Step 1：找到最新未评估批次

读取 state 确认当前 batch：
```bash
PYTHONPATH=src python3 -m research state
```

如果 `current_batch` 有值且 `current_batch_phase = frozen`，直接用它。
否则扫描 `storage/batches/` ��到有 manifest 但无 research_result 的批次。

### Step 2：���行评估管道

```bash
PYTHONPATH=src python3 -m research execute storage/batches/batch_XXX/manifest.yaml
```

管道内部步骤：
1. **Precheck**：DSL 语法/算子白名单/字段白名单/深度/forbidden pattern；Python 语法/白名单/向量化检查
2. **Base signal**：通过 Qlib 计算因子值
3. **预处理**：universe mask → tradability → winsorize → zscore → neutralization
4. **统计证据**（6 维）：
   - Effect strength (IC/ICIR/胜率/单调性，train + validation)
   - Stability (split 4 段稳定性 / regime 稳定性 / train-validation 衰减)
   - Reliability (expanding window IC / bootstrap / purged walk-forward)
   - Support window checks (辅助 window sign flip 检测)
   - Multiple testing context (搜索强度风险 bucket)
5. **冗余分析**（3 层）：pairwise / family / subspace ridge
6. **风险评审**：raw IC / cap-neutral IC / Barra 残差 IC / alpha_survival_ratio / dominant style / crowding risk
7. **可实现性**：turnover / coverage / half_life / liquidity_coverage / tail_concentration / rebalance_stress
8. **Execution gate**：pass / warn / fail_technical
9. **Holdout review trigger**
10. **构建 judge_packet**

### Step 3：验证输出

确认生成：
- `storage/batches/batch_XXX/research_result.yaml`
- `storage/batches/batch_XXX/judge_packet.yaml`

### Step 4：更新 Ledger + State

在 `storage/governance/ledger.yaml` 中更新对应 batch 的 `batch_usage` 条���：
- 将 `phase` 从 `frozen` 更新为 `executing`��开始时）→ `executed`（完成时）
- 如果 idea 阶段没有写入 batch_usage 条目，则在此补写完整条目

**更新 research state**：
```bash
# 管道开始前
PYTHONPATH=src python3 -m research state set current_batch_phase executing
# 管道完成后
PYTHONPATH=src python3 -m research state set current_batch_phase executed
```

### Step 5：打印摘要

- 总候选数
- Precheck 失败数
- Gate pass / warn / fail 分布

## 样本制度

所有日期范围、宇宙、阈值从 `storage/governance/research_config.yaml` 读取：
- **universe**: `config.universe`
- **Train**: `config.sample_policy.active_train_range`
- **Validation (primary)**: `config.sample_policy.active_validation_range`
- **Support windows**: `config.sample_policy.support_validation_windows`
- **Holdout**: `config.sample_policy.holdout_pool_range`

CLI 命令不需要传 `--universe` 或日期参数，除非要 override。

## 关键约束

- execute 不做 admit/reject 决策，只产出证据
- risk_model_review_bucket 由 RiskEngine 子系统产出，不由下游重算
- 所有计算向量化（numpy/pandas），无逐行循环
- 因子数据通过 parquet 缓存加速
