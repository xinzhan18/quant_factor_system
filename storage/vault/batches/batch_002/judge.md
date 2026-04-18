---
batch_id: batch_002
direction: amount_volatility_signal
judged_at: 2026-04-19T01:57:00Z
candidates:
  - {candidate_id: C001, verdict: reserve}
  - {candidate_id: C002, verdict: reserve}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
batch_summary: {total: 5, admit: 0, reserve: 2, reject: 3}
---

# batch_002 Judge Summary

> [!abstract]+ batch_002 · [[directions/amount_volatility_signal]] · 5 candidates
> ✅ **admit=0** · ⏸ **reserve=2** (C001 cv_5, C002 cv_20) · ❌ **reject=3** (C003 hard_gate·near_dup, C004 hard_gate·ic_oos_too_low, C005 hard_gate·ic_oos_too_low)
> **核心发现**: T001 的 CV 窗口扫描揭示 **10d 是全局最优**——5d (C001) 信号完整但换手 1.8× 且 rebalance_stress 升档；20d (C002) 在所有关键维度全面劣化（ICIR↓ / vol_20d 暴露×1.5 / alpha_survival↓）。MAD 版 (C003) 与 F001 corr=0.967 → 算子替换不开辟新信号子空间。T002 延长至 60d (C004) 彻底熄灭 → "延长窗口"不是 T002 出路，需转向稳健尾部指标 / 条件分组。T004 幅度版 Corr (C005) 丢失方向信息 → 保留符号的 NaN-safe 实现应优先。
> **MT Budget**: cumulative 8 → **13** · direction 8 → **13** · bucket 两 pass 均 `low`（search_adjusted=high 已边际化）· 本批 low=2 / med=0 / high=0 / hard_gate=3

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ⏸ reserve | 🟢·🟢·🟡·🟡·🟡 | ICIR_oos=-0.623 ls_t=-3.58 mono=-1.0 max_corr=0.57@F001 | cv_5 完整复现机制但只是敏感度变体；换手/半衰/压力全劣于 F001 | [[batches/batch_002/candidates/C001]] |
| C002 | ⏸ reserve | 🟡·🟡·🔴·🟡·🟡 | ICIR_oos=-0.579 ls_t=-3.43 vol_20d=37.5 alpha_surv=0.649 | cv_20 触发 anchor rule（同簇第二 vol_20d 主导）；明确证明 10d 是 T001 最优窗口 | [[batches/batch_002/candidates/C002]] |
| C003 | ❌ reject | hard_gate | near_duplicate: corr=0.967@F001 | MAD/Med 在右偏 $amount 分布上与 Std/Mean 几乎无差异；算子鲁棒性替换不开辟新空间 | [[batches/batch_002/candidates/C003]] |
| C004 | ❌ reject | hard_gate | ic_oos_too_low: ｜-0.0078｜<0.008 (regime-dep) | 60d Max/Mean 是典型 regime-dependent 尾部信号，OOS 量级衰至前期 1/5；延长窗口不是 T002 出路 | [[batches/batch_002/candidates/C004]] |
| C005 | ❌ reject | hard_gate | ic_oos_too_low: ｜-0.0037｜<0.008 (signal thin) | 幅度版 Corr 去方向后信号过薄；T004 下 sign-preserved NaN-safe 实现应优先 | [[batches/batch_002/candidates/C005]] |

**档位编码**：🟢 最优档 · 🟡 次档 · 🟠 边际 · 🔴 阻断档；`hard_gate` reject 该列直接写 `hard_gate` 不填色。

## 跨候选对比

- **T001 窗口扫描结论**：`cv_5 (C001) ≥ cv_10 (F001) > cv_20 (C002)` 在 |ICIR| 量级上 0.623 ≥ 0.716 > 0.579（注：F001 略高于 C001），但 C001 换手代价高、C002 vol_20d 被吞噬严重——**10d 是"alpha 强度 × 风格干净度 × 换手成本"三者平衡的最优点**。F001 的 anchor 地位经窗口扫描正式确立。
- **MAD / Mean-based CV 同构性**：C003 (MAD/Med_10) 与 F001 (Std/Mean_10) 相关 **0.967**——鲁棒算子替换在右偏 $amount 分布上**不开辟新信号子空间**。T001 "MAD 抗离群值" 这条 next probe 被批次内实证封闭。
- **vol_20d 暴露分布**：本批 5/5 候选 `dominant_style_exposure = vol_20d`，延续 batch_001 发现的方向级 8/8 vol_20d 主导。C002 (vol_20d=37.5) 暴露最重、C001 (14.1) 最轻、C004 (23.1) 中等。**T002 / T004 下一轮必须做 vol_20d orthogonalize**，不再继续扫同族窗口。
- **Reserve 冗余**：C001 vs C002 同为 T001 CV 窗口变体，若下轮 vol_20d 正交化无新发现，两者二选一（倾向 C001：更干净 style_r²=0.055 + 完整 ICIR_oos=-0.623）。
- **MT 预算推进**：cumulative 8 → 13（仍 low），direction 13（仍 low）；但两 pass 候选 search_adjusted=high（0.753）提示同方向 / 同 family 搜索已近饱和——下轮优先度应转向**新 family**（orthogonalize 残差 / 条件分组 / 跨字段组合）而非窗口扫描。

## Thread 进展

> [!success]+ T001 [[directions/amount_volatility_signal#T001]] — `[✓ ANSWERED batch_002]`
> 窗口扫描完成：**10d (F001) 是 CV 机制全局最优窗口**。5d (C001 reserve) 信号同样完整但换手×1.8 + half-life 减半 + rebalance_stress medium；20d (C002 reserve) 全维劣化 + vol_20d 吞噬升级。MAD 变体 (C003 reject) 与 Std/Mean 同族相关 0.967，算子替换空间封闭。T001 已答，下一步由 T002/T004 或新 thread 接棒。

> [!failure]+ T002 [[directions/amount_volatility_signal#T002]] — 60d 延长窗口路径 `[✗ DISPROVEN batch_002]`（hypothesis 未被整体证伪）
> C004 (max/mean_60) OOS ic_oos=-0.0078 触 hard_gate；IS/OOS 衰减 69%、ls_tstat_oos ≈ 0、quintile_oos 无梯度、2021+ 年份 IC 仅为前期 1/5 量级。**延长窗口**不是 T002 的出路。T002 整体 hypothesis（尾部异常大单信息含量）仍 ACTIVE——下一步转向 robust tail indicators（top-3/top-5 mean over window）或条件分组（skew 正负分层看条件 IC）。

> [!failure]+ T004 [[directions/amount_volatility_signal#T004]] — 幅度版 Corr 子路径 `[✗ DISPROVEN batch_002]`（hypothesis 未被整体证伪）
> C005 (Corr amount × |Δclose|) OOS ic=-0.0037 信号过薄；去方向化丢失 T003 原本希望保留的"资金与价格方向一致性"信息。T004 整体 hypothesis（NaN-safe 算子族实现 T003）仍 ACTIVE——下一步优先保留符号的归一化 Slope 和 Sign(Δclose)×amount 条件均值实现，降权幅度-only 分支。

## 方向级反思

本批**零 admit**——并非方向熄火，而是 T001 的窗口扫描完成后对"F001 anchor 地位"的统计正式验证：窗口变体（C001 cv_5、C002 cv_20）和算子变体（C003 MAD/Med）都在同一机制簇内不开辟新维度；T002 / T004 的延伸尝试（60d 尾部、幅度 Corr）触硬闸。

**方向级发现（接续 batch_001）**：
- 方向内 13/13 候选 (batch_001 8 + batch_002 5) 全部 `dominant_style=vol_20d` → **方向结构性主导因子已明确**。下轮若不做 vol_20d orthogonalize，几乎必然撞 anchor rule 或进一步 crowding。
- `incremental_ic` 中位数：batch_001 reserve 候选 (C002_b1 / C005_b1) vs batch_002 reserve 候选 (C001_b2 / C002_b2) 均在 -0.03 ~ -0.04 量级——**方向内"增量预测力"已稳定**，但增量来源主要是敏感度差异而非机制多样性。

**下轮建议**：
1. **T002 改 robust tail 指标**：`Div(Mean(TsMax($amount, 3), 20), Mean($amount, 20))`（top-3 mean 替换 single max）、或按 20d 内 Skew($amount) 正负分组看条件 CV
2. **T004 sign-preserved NaN-safe**：`Slope(Div($amount, Mean($amount, 20)), 20)` 归一化后 Slope、`Mul(Sign(Delta($close, 1)), $amount)` 条件均值
3. **新 Family：vol_20d residual 信号**：明确跨方向借鉴 cross-sectional Barra residual（若 DSL 能表达）或走 Python 逃生口实现 vol_20d 正交化
4. **候选数 ≤ 5**（search_adjusted=high 持续，收窄搜索空间）

若下批继续零 admit，方向 `status: productive → saturated` 待考；目前保持 productive（T002 hypothesis 未被整体证伪、T004 仍可探）。
