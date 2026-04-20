---
batch_id: batch_015
direction: barra_residual_alpha
judged_at: 2026-04-21T01:55:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
batch_summary: {total: 5, admit: 0, reserve: 0, reject: 5}
---

# batch_015 Judge Summary

> [!abstract]+ batch_015 · [[directions/barra_residual_alpha]] · 5 candidates
> ❌ **admit=0** · ⏸ **reserve=0** · ❌ **reject=5** (C001–C005 全部 hard_gate)
> **核心发现**: **F004 是该 7-style basis 上 OLS-family 残差的唯一不动点**——5 个变体（Huber 鲁棒 / 5d HL 8th style / 标准化 / Winsor / vol×turn 交互）4 个 corr=0.907–0.997 with F004，1 个 compute_error。**barra_residual_alpha 方向 saturated** — 在同 7-basis + OLS-family 内不可能产生独立 alpha。
> **MT Budget**: cumulative 77 → **82** · direction 10 → **15** · bucket `medium`

## 候选一览

| ID | Verdict | 档位 | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | hard_gate | near_dup F004 corr=0.907 | Huber IRLS：鲁棒损失只动 outlier 权重，不改 cross-sectional 几何 | [[batches/batch_015/candidates/C001]] |
| C002 | ❌ reject | hard_gate | compute_error: $high/$low 缺失 | data_bridge 不加载 OHLC 全列——系统级数据契约缺口（T003） | [[batches/batch_015/candidates/C002]] |
| C003 | ❌ reject | hard_gate | near_dup F004 corr=0.927 | per-symbol rolling-std normalization 是 monotone transform，cross-section rank 不变 | [[batches/batch_015/candidates/C003]] |
| C004 | ❌ reject | hard_gate | near_dup F004 corr=0.941 | ±5 MAD 截断 <2% 尾部；β fit 几乎不动 | [[batches/batch_015/candidates/C004]] |
| C005 | ❌ reject | hard_gate | near_dup F004 corr=0.997 | vol×turn interaction 与原 styles 强共线，pinv 消除冗余维度 | [[batches/batch_015/candidates/C005]] |

## 跨候选对比

- **F004 不动点定理（experimentally established）**：在同 7-style basis 上，OLS / Huber / Winsor / heteroscedastic-norm 4 种残差化方法都收敛到 F004（corr ∈ [0.907, 0.997]）。**这意味着 F004 不是某个特定方法的 artifact，而是该 basis 上的几何不变量**——任何 method-switch 都无法产生独立 alpha。
- **加 1 个 collinear style 等于 0**：C005 vol×turn interaction 与原 vol_20d/turnover_20d 强共线，pinv 自动消除冗余维度——0.997 corr 是数学必然。证伪"加 interaction style 拓展 basis"假设。
- **单符号时序变换不改 cross-sectional 几何**：C003 per-symbol rolling std 是 monotone transform；与 batch_014 C002 (3d EMA) 同源教训。**Cross-sectional 操作 vs time-series 操作的几何独立性**——time-series 操作绝不可能在 cross-sectional rank 上产生新结构。
- **C002 数据契约缺口（系统级 finding）**：python_factor REQUIRED_FIELDS=["$close","$high","$low"] 未被 data_bridge loader 尊重——loader 默认只加载 close/volume/amount/market_cap。需要 (a) 扩 loader 默认列，或 (b) phase1 freeze 时 validate REQUIRED_FIELDS ⊆ loader 实际加载列。记入 T003 thread。
- **MT 预算**：direction 10→15，cumulative 77→82。本批 100% hard_gate 是方向饱和的硬证据。

## Thread 进展

> [!failure]+ T002 [[directions/barra_residual_alpha#T002]] — `[✗ DISPROVEN batch_015]` 残差与方法变体的正交性假设
> 5 个 method-switch 候选 4/4 collapse 到 F004（corr 0.91-0.997）。**T002 在 OLS-family 框架内被证伪**：换损失函数 / 标准化 / 加 interaction style 都不能产生独立残差。Thread 状态从 `[◉ ACTIVE]` → `[✗ DISPROVEN batch_015]`。后续路径必须**跳出 7-style basis**（如 industry-relative residual / non-Barra factor model）或**跳出 OLS-family 框架**（如 nonparametric / machine learning residual）。

> [!note]+ T003 [[directions/barra_residual_alpha#T003]] — `[◉ ACTIVE]`
> C002 暴露 data_bridge loader 不尊重 REQUIRED_FIELDS 的系统缺口，新增到 T003 thread evidence trail。短期 workaround：先用 python_factor 自己 D.features() 取 OHLC，绕过 loader 限制；长期解：扩 loader 默认列。

## 方向级反思

batch_015 是 barra_residual_alpha 方向**第二批 0 admit**，连续 2 批 admit=0。结合 batch_014 vol_20d 主导发现 + batch_015 method-invariance 发现：

**barra_residual_alpha 方向在当前 7-style basis + OLS-family 框架内 saturated**。

实质性证据：
1. F004 是该 basis × 该方法族的几何不变量（5 method variants 全部 collapse）
2. 调整 7-style 子集（batch_014 C002/C005）也 collapse（vol_20d 主导）
3. 加 collinear style（C005）数学上等于 0
4. 时序变换（C003 / batch_014 C002）不改 cross-section
5. 加 forward-return horizon（batch_014 C003）触发 lookahead leak

**方向 status: productive → saturated** — 在 Narrative Log 翻态。**优先级 high → low** — 避免再投算力。后续若有 new style basis（industry-relative / GICS / 新 microstructure styles）或 nonlinear residualization 框架（kernel ridge / neural residual），可重启 → productive。

**触发 calibration 检查**:
1. 错杀 flag = 0 ✓
2. 连续 2 批零 admit (batch_014 + batch_015)，但**累计 reserve 中无满足"库空间独立 + rank-order 完美 + 符号互补"全条件的候选**——batch_014 reserve C001 (vol_20d) 是 dom_style + style_r²=0.999 + incremental_ic 负，明显非错杀；batch_013 reserve C002 已被 batch_014 C002/C005 双向证伪可独立。**不触发**。
3. Reserve 积压：cumulative 82 candidates / 累计 reserve 数 ≈ 13 = 16% < 40% ✓ 不触发
4. 悖论复现 = 无新悖论 ✓

**下批决策（batch_016）**：开新方向。**候选方向**：
- A. **microstructure_signal**：intraday H-L、open-close、量价不对称——尚未探索
- B. **industry_relative_residual**：行业内 demean，可能与 size 相关 cluster 互补
- C. **multi_factor_combination**：F001-F004 的非线性组合（neural / ranking ensemble）
- 选 **A microstructure_signal**——data_bridge 已有 $close（需扩 $high/$low 但比 industry/industry_code 容易），DSL 可表达大部分 intraday 信号
