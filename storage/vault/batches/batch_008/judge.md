---
batch_id: batch_008
direction: amount_volatility_signal
judged_at: 2026-04-19T20:35:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reserve}
  - {candidate_id: C003, verdict: reserve}
  - {candidate_id: C004, verdict: reserve}
  - {candidate_id: C005, verdict: reserve}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 0, reserve: 4, reject: 2}
---

# batch_008 Judge Summary

> [!abstract]+ batch_008 · [[directions/amount_volatility_signal]] · 6 candidates
> ❌ **admit=0** · ⏸ **reserve=4** (C002 C003 C004 C005) · ❌ **reject=2** (C001 C006)
> **核心发现**: 所有非 hard_gate 候选均被 vol_20d 共线性 + alpha_survival borderline 联合阻断；C003 是本批最干净的 rank-order 信号（mono=-1.0, max_corr=0.07@F001）但 alpha_survival=0.24 触 CP04 poor 档；C002/C005 near-duplicate（max_corr=0.60@F002，incremental_ic 负值）。
> **MT Budget**: cumulative 38 → **44** · direction 18 → **24** · bucket `medium` · 本批 low=0 / med=4 / high=0

## 候选一览

| ID   | Verdict   | 档位 (CP2·3·4·5·6) | Key Metric                                     | 反思                                                                                      | Detail                                |
| ---- | --------- | ---------------- | ---------------------------------------------- | --------------------------------------------------------------------------------------- | ------------------------------------- |
| C001 | ❌ reject  | hard_gate        | mono_sign_flip IS=0.70 OOS=-0.90               | 40d sign-only Corr 跨期翻号，horizon 延长未解决 regime 依赖                                         | [[batches/batch_008/candidates/C001]] |
| C002 | ⏸ reserve | 🟢·🟡·🔴·🟡·🟠   | icir=-0.156 ls_t=-3.26 mono=-1.0               | 完美单调但 Barra 吞噬 78% alpha（style_r²=0.784）；nearest F002 相关 -0.60 对冲而非叠加                   | [[batches/batch_008/candidates/C002]] |
| C003 | ⏸ reserve | 🟡·🟡·🔴·🟢·🟢   | icir=-0.240 ls_t=-2.21 mono=-1.0 max_corr=0.07 | 本批 rank-order 最强候选（mono=-1.0, 9年全负）但 alpha_survival=0.24 触 poor 档；mom_12_1 alpha killer | [[batches/batch_008/candidates/C003]] |
| C004 | ⏸ reserve | 🟢·🟡·🟠·🟢·🔴   | icir=-0.256 ls_t=-3.00                         | amount 动量机制正交（incr_ic=-0.032）；但 vol_20d=16.2 方向历史最高 + cum_ic_mdd=-73.3 突破硬阈值            | [[batches/batch_008/candidates/C004]] |
| C005 | ⏸ reserve | 🟢·🟡·🔴·🟡·🟠   | icir=-0.156 ls_t=-3.26                         | C002 几乎 duplicate（metrics 相同，max_corr=0.60@F002）；incremental_ic 负值                      | [[batches/batch_008/candidates/C005]] |
| C006 | ❌ reject  | hard_gate        | ic_oos=-0.0033 < 0.008 + mono_sign_flip        | 偏度重测：信号太弱（ic=-0.003）+ OOS 符号翻号，T002 高阶矩路径再次封闭                                           | [[batches/batch_008/candidates/C006]] |

## 跨候选对比

- **Style 聚合**：4/4 non-reject 候选 `dominant_style=vol_20d`——第 4 次确认方向级结构性瓶颈，DSL 无解
- **Near-duplicate cluster**：C002 vs C005 几乎 identical（metrics 相同，same nearest F002@0.60），C005 不开辟独立子空间
- **最佳独立信号**：C003（max_corr=0.07@F001, incr_ic=-0.011）是最接近库增值的候选，但 CP04 alpha_survival=0.24 触 poor dealbreaker
- **最差 Barra 暴露**：C002/C005 style_r²=0.784（78% alpha 被 Barra 吸收），C004 vol_20d=16.2（方向历史最高）
- **MT 预算**：direction_candidates 18→24（+6）；全部 4 个 reserve 落在 `medium` bucket

## Thread 进展

> [!note]- T001 [[directions/amount_volatility_signal#T001]] — `[✓ ANSWERED batch_002]`（本批无推进）

> [!note]- T002 [[directions/amount_volatility_signal#T002]] — `[◉ ACTIVE but DSL-bounded]`
> C003 (Q85 ratio) reserve：alpha_survival=0.24 触 CP04 poor dealbreaker；C006 skew 重测 ic=-0.003 hard_gate。**T002 DSL-native 路径 6 次证伪（batch_001 C004/C008 → batch_003 C003/C004 → batch_008 C003/C006）**，hypothesis 仍成立但 DSL 空间已物理封闭。
> **Next probes**: vol_20d residual（Python 逃生口）——唯一未被证伪的子路径。

> [!note]- T003 [[directions/amount_volatility_signal#T003]] — `[✗ DISPROVEN batch_001]`（本批无推进）

> [!note]+ T004 [[directions/amount_volatility_signal#T004]] — `[◉ ACTIVE but DSL-bounded]`（本批无新增）
> C001 (40d Corr) reject：mono_sign_flip；C003 sign-only Corr reserve 但 alpha_survival 0.24。**T004 sign-preserved 算子族全部失败**——C006 (Corr amount|Δclose|) 幅度版 / C001 (sign-only Corr) / C003 (mean sign×amount) / batch_003 C005 (sign-only Corr) 四条子路径全部证伪。
> **Next probes**: 同 T002：vol_20d residual（Python 逃生口）。

> [!note]+ T005 [[directions/amount_volatility_signal#T005]] 🆕 — `[◉ ACTIVE]`
> **Amount × turnover_rate 跨字段交互**：C002/C005 验证了"amount 波动率 / turnover_rate"机制的 Barra 高暴露问题（style_r²=0.78）；C003 "Corr(amount, volume)" 比值捕捉资金-持仓关系但被 mom_12_1 alpha killer 吞噬。**跨字段 DSL 路径 Bara 脏**。

## 方向级反思

**19/19 非 hard_gate 候选 dominant_style=vol_20d，方向结构性瓶颈第 4 次确认。**

三条逃脱路径本批结果：
1. **Horizon 扩展（C001 40d sign-only Corr）**：FAIL — mono_sign_flip，horizon 延长不解决 regime 依赖
2. **跨字段组合（C002/C003/C005）**：FAIL — style_r²=0.33~0.78，全部被 vol_20d 或 mom_12_1 吞噬
3. **新机制（C004 amount momentum / C006 skew）**：FAIL — momentum cum_ic_mdd=-73.3 突破硬阈值；skew 信号太弱

**C003 是本批最大矛盾**：mono=-1.0 / max_corr=0.07@F001 / 9年同号 — 完美的 rank-order 和正交信号，但 alpha_survival=0.24 触 CP04 poor。Barra residual IC=-0.004，残差 alpha 极薄。

**下轮唯一逃生口：Python vol_20d Barra residual**。C003 或 C002 的残差化验证独立 alpha。DSL 空间已物理探尽（19 候选 100% vol_20d），若 Python 残差版仍无独立 alpha，方向转 `saturated`。

若下一轮 admit 率仍 = 0%，`status: productive → saturated`。
