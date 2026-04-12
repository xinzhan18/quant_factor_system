---
name: factor-execute
description: Phase 2 EXECUTE — 纯 Python 向量化计算，LLM 不参与
user_invocable: true
---

# /factor-execute — Phase 2 纯计算

## 职责

对冻结的 manifest 运行向量化评估管道，产出 `result.yaml`。**零 LLM 参与**。

## 命令

```bash
PYTHONPATH=src python3 -m research execute batch_{N}
```

## 流程

```
manifest.yaml
  → 加载 cache/market_daily.parquet（一次）
  → 加载 cache/barra_factors.parquet（一次）
  → 对每个候选：
      DSL: Qlib D.features() 求值 / Python: python_runner.load + compute
      → preprocess（MAD winsorize + z-score，矩阵化）
      → vectorized_{ic,quintile,stability,feasibility,redundancy,barra}.py
  → 写 result.yaml
```

## Multi-horizon + Multi-universe

- **Multi-horizon**：对 `config.yaml.evaluation.horizons`（默认 `[1, 5, 10]`）每个 horizon 算完整 metrics（IC / mono / Barra / feasibility_turnover）。`primary_horizon`（默认 5）是 Phase 3 判决基准。
- **Multi-universe**：primary (csi1000) 跑 full metrics，reference (csi300 / csi500 / all) 跑 lite metrics（IC / mono / ls_tstat，不跑 Barra）。成本增量 ~10%。
- **Universe mask**：通过 `D.instruments()` 从 Qlib instruments 文件加载，不查 DB。

## Preprocess 参数（`config.yaml.preprocess`）

| 参数 | 值 | 算法 |
|---|---|---|
| `winsorize_mad_k` | 5 | clip 到 `median ± 5 × 1.4826 × MAD`（per row） |
| `winsorize_mad_scale` | 1.4826 | MAD → std 正态换算系数 |
| `zscore` | true | `(x - row_mean) / row_std`（ddof=0） |
| `neutralize` | false | 关闭（CP04 Barra 残差做事后检验） |

**向量化要求（R5）**：
- long → wide pivot → 对整个 `(n_dates × n_symbols)` matrix 做行级 numpy 运算 → wide → long
- **禁止 `groupby.transform`**（隐式 for-loop over dates）
- **禁止 `for date in dates:` / `for symbol in symbols:`**

## Barra OLS（§11 3D tensor 批量）

```python
X_masked = np.where(valid[..., None], X, 0.0)      # (d, s, 8)
XtX = np.einsum("dsp,dsq->dpq", X_masked, X_masked) # (d, 8, 8)
Xty = np.einsum("dsp,ds->dp", X_masked, y_masked)    # (d, 8)
XtX_inv = np.linalg.pinv(XtX)                        # (d, 8, 8)
beta = np.einsum("dpq,dq->dp", XtX_inv, Xty)         # (d, 8)
```

无效位置零化后不影响 Gram 矩阵。日均 OLS 93ms（legacy 600ms，6× 加速）。

## Holdout 隔离

Phase 2 **绝对不计算 holdout 期（2024-01-01 以后）的任何指标**。result.yaml 没有 holdout 字段。holdout 只在独立的 `research holdout-review` CLI 中使用。

## result.yaml schema（冻结版 v1）

```yaml
schema_version: "1"
batch_id: batch_103
sample_policy_version: v3
preprocess_version: p1
train_range: [2015-01-01, 2021-12-31]
validation_range: [2022-01-01, 2023-12-31]
n_candidates: 6
n_ok: 5
n_errors: 1

candidates:
  - candidate_id: C001
    expression: "Mul(Corr($close,$volume,20),Std($volume,20))"
    source_type: dsl
    coverage: 0.97
    sign: 1                          # primary IC sign (+1/-1)
    compute_error: null              # 或 "ValueError: ..."

    effect_strength:
      train:
        ic_mean: 0.018
        ic_std: 0.06
        ic_ir: 0.30
        ic_win_rate: 0.58
        n_days: 1500
      validation:
        ic_mean: 0.016
        ic_std: 0.05
        ic_ir: 0.338
        ic_win_rate: 0.607
        n_days: 480

    quintile:
      quintile_returns_validation:
        q1: -0.005
        q2: -0.003
        q3: -0.001
        q4: 0.001
        q5: 0.004
      monotonicity_validation: 0.95
      long_short_mean_validation: 0.007
      long_short_n_days: 480

    stability:
      split_stability:
        split_ic_means: [0.013, 0.015, 0.012, 0.018]
        sign_consistency: 1.0
        dispersion: 0.15
        bucket: high                 # high / medium / low
        n_splits: 4
      support_windows:
        checks: [{window_id: ..., ic_mean_support: ..., sign_consistent: true}]
        warning: none                # none / single_flip / repeated_flip
      sign_consistency_train_validation: true
      train_validation_decay: 0.89

    redundancy:
      max_lib_corr: 0.30
      nearest_factor_id: F012
      is_near_duplicate: false
      exceeds_threshold: false
      all_correlations: {F001: 0.05, F012: 0.30, ...}

    feasibility:
      turnover_mean: 1.2
      liquidity_coverage: 0.80
      tail_concentration: 0.10
      small_cap_concentration: 0.25
      half_life: 8.0
      holding_period: medium         # short / medium / long
      rebalance_stress:
        rebalance_stress_proxy: 0.15
        rebalance_stress_bucket: low # low / medium / high

    barra:
      style_exposures:
        log_circ_cap: 0.12
        book_to_price: 0.08
        mom_12_1: 0.05
        str_1m: 0.04
        vol_20d: 0.15
        turnover_20d: 0.10
        ep_ratio: 0.06
      style_r_squared: 0.08
      barra_residual_ic: 0.013
      barra_residual_icir: 0.251
      alpha_survival_ratio: 0.691
      dominant_style_exposure: vol_20d
      style_crowding_risk: low       # low / medium / high

    multiple_testing_risk_bucket: null  # Phase 3 填充，Phase 2 留 null
```

## 错误处理

单候选 compute_error → 记录到该候选的 `compute_error` 字段，其他候选继续。不会因为一个候选的异常中断整个 batch。
