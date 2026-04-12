---
name: factor-execute
description: Phase 2 EXECUTE — 纯 Python 向量化计算，LLM 不参与
user_invocable: true
---

# /factor-execute — Phase 2 纯计算

## 职责

对冻结的 manifest 运行向量化评估管道，产出 `result.yaml`。**零 LLM 参与**。

## 流程

```
manifest.yaml → 加载数据 → DSL/Python 因子求值 → preprocess (MAD winsorize + zscore)
→ vectorized_{ic,quintile,stability,feasibility,redundancy,barra}.py → result.yaml
```

## 技术要点

- **R5 全向量化**：所有指标用 `compute/vectorized_*.py` 模块，禁止 for-loop over rows/dates/symbols
- **Barra**：`np.linalg.pinv + np.einsum` 3D tensor 批量（6× 加速）
- **Preprocess**：long → wide → matrix MAD winsorize → zscore → long（不用 `groupby.transform`）
- **Cache**：sha256 content-addressed parquet，key = `expression|sample_policy_version|preprocess_version`
- **Holdout 隔离**：Phase 2 **绝不** 计算 holdout 期（2024+）的指标
- **单候选失败不阻塞**：compute_error 记录在 result.yaml，其他候选继续

## result.yaml schema

每个候选包含：`effect_strength` / `quintile` / `stability` / `redundancy` / `feasibility` / `barra` / `compute_error`。
`multiple_testing_risk_bucket` 字段留 `null`，Phase 3 pre-pack 填充。
