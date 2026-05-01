---
direction_tag: python_ttm_residual_quality
status: dead
priority: low
rounds: 1
admits: 0
last_batch: batch_071
last_admits: []
last_goal: 'Round 71 首批 — Python R8 escape hatch — 6 候选验证 OLS residualize TTM quality

  on (size, vol_20d, [book_to_price]) Barra basis 后再 CsRank 是否能脱

  b068/b070 的 vol_20d 吸收陷阱 (lessons.md L1 "逃离正路径 b")。所有候选 source_type=python，

  使用 numpy.linalg.pinv + einsum vectorized OLS。Quality numerator 覆盖 ROE/ROIC/

  gross_margin/ROA/growth/operating_margin 6 类。窄 basis (size+vol_20d) vs 宽 basis

  (+book_to_price) 形成对照。目标 ≥1 admit 否则 mechanism 死区。Anti-recap:

  与 b068-b070 全部 18 候选不重叠（那些是 DSL Div/Mul 路径）。'
last_activity: '2026-05-02T04:30:00Z'
created_batch: batch_071
members: []
retired_members: []
reserves: []
merged_into: null
created_from: library_gap_proposal_2026_05_02
dead_at: '2026-05-02T04:30:00Z'
dead_reason: first-batch dead — b071 6/6 alpha_surv ∈ [0.93, 7.23] 全 PASS 但 6/6 OOS sign_flip + 5/6 vol_20d_exp 仍 dom (Linear OLS 不破非线性吸收) + 2022-2023 regime drift 独立失活；mechanism dead zone 无残余探索路径无 reserve 火种；3 条元教训已升格 lessons.md (round 73)
---
# python_ttm_residual_quality

> [!abstract]+ 方向概要
> - **状态**　🔴 `dead` (round 73 consolidation，2026-05-02 first-batch dead) · priority `low` · rounds = 1 · admits = 0 · reserves = 0
> - **一句话**　Python OLS residualize TTM quality on Barra basis 工艺正确执行（alpha_survival 0.93~7.23 全 PASS）但 6/6 OOS sign_flip — **不是 vol_20d 吸收问题，是 csi1000 daily TTM quality 类信号在 2022-2023 全 regime sign-flip alpha 真不存在**。Mechanism dead zone。
> - **升格 lessons (round 73)**　[[lessons#Path Selection]] "alpha_survival ≥ 0.40 必须配 ic_by_year 后期同号 check"（CP02 校准律）+ "Linear OLS residualize 不破 csi1000 vol_20d 非线性吸收"（限定逃离正路径 a 语义边界）+ 顶层 macro lesson "csi1000 daily fundamental + institutional flow 真饱和" 路径 c。
> - **关联 findings**　[[_consolidation/findings/pattern_analyst/011]] · [[_consolidation/findings/pattern_analyst/014]] · [[_consolidation/findings/hypothesis_promoter/008]] · [[_consolidation/findings/hypothesis_promoter/010]] · [[_consolidation/findings/calibration/006]]
> - **复活前置**　仅当 (a) lessons.md "Linear OLS 不破非线性 vol_20d 吸收"被推翻（Polynomial/Kernel 工艺接入 + 跨方向独立验证）；或 (b) minute/tick 数据接入推翻 csi1000 daily TTM quality 真饱和；或 (c) cross-universe (csi300/csi500) 验证 TTM quality alpha 在其它 universe 仍 alive。

---

## Hypothesis

**经济学逻辑**：
1. **真 quality alpha 存在但被 daily-liquidity proxy 吸收**：ROE/ROA/ROIC/gross_margin/operating_margin TTM 在 csi1000 上携带"真盈利能力 cross-section signal"，但当用 daily-aggregate liquidity (Mean(amount/turnover, N)) 作 denominator 时，该 denominator 在 cross-section monotone-equivalent vol_20d，把 numerator 拉进 vol_20d basis（lessons.md L1）。
2. **解法 = 源头剔除**：先把 quality 字段对 (log_market_cap, vol_20d, book_to_price) 做 cross-sectional OLS regress，残差就是"剔除 size/vol/value 共线性后的纯 quality cross-section ranking"。
3. **再 CsRank → long-short**：残差再做 cross-section rank，避免 raw 残差 scale 异常引入 outlier；rank 是 Barra-style 公认的 robust packaging。

**技术路径（R8 escape hatch）**：
- DSL 不能表达 daily cross-sectional OLS pinv → Python only。
- 用 `numpy.linalg.pinv + einsum` 三维张量 OLS（barra_residual_alpha 方向已用同款架构）。
- 输入：TTM quality field + 3 Barra styles (log_circ_cap, vol_20d, book_to_price)；输出：daily cross-section residual 排名。

## Threads

### T001: Python OLS residualize TTM quality on Barra basis 是否破 vol_20d 吸收 [✗ DISPROVEN batch_071]

> [!failure]+ Thread 结论
> **Question**: Python OLS residualize($TTM_quality, [log_circ_cap, vol_20d, [book_to_price]]) → CsRank 路径是否能让 TTM quality (ROE/ROIC/gross_margin/ROA/growth/-debt_to_asset) 携带独立于 Barra basis 的 OOS-stable cross-section alpha？
>
> **Answer**: **完全证伪**。6/6 候选 hard_gate sign_flip (train +α 0.001~0.014 / val -α -0.001~-0.009 全部翻号) + 2/6 oos_decay 也 fail。alpha_survival 6/6 PASS 红线 (0.93~7.23) 证明 OLS 工艺充分剔除 Barra style 线性 component；但 5/6 dominant_style 仍 vol_20d (exp 11~22) 证明 linear OLS 不破非线性 vol_20d 吸收；且 IC by year 完整 regime drift profile (2015 +0.025 → 2021 +0.003 → 2022 -0.003 → 2023 -0.014) 证明 csi1000 daily 上 TTM quality 类 alpha 在 2022-2023 全 regime sign-flip — **不是 vol_20d 吸收问题，是 alpha basis 在 OOS 不存在**。
>
> **Evidence trail**: b071 C001 (ROE narrow basis, alpha_surv=0.93, vol_20d_exp=22.9, sign_flip), C002 (ROIC 3-basis, alpha_surv=2.40, vol_20d_exp=17.3, sign_flip), C003 (gross_margin, IS IC<0.002 极弱), C004 (ROA 3-basis, sign_consistency=1.0 但 OOS 翻号), C005 (growth winsorize, ep_ratio dom 替代 vol_20d, OOS 仍翻号), C006 (-debt_to_asset solvency, alpha_surv=7.23 整批最高, val_ic=-0.0007 边缘但仍反号).
>
> **机制层判断**: lessons.md L1 提供的"逃离正路径 b" (Python OLS residualize) 通过本批被验证为**死路**。同款 Python pinv+einsum 架构在 [[directions/barra_residual_alpha]] F004/F005 上是 admit 的 — 工艺本身有效；本批失败是 **TTM quality numerator 在 csi1000 daily 上无 OOS-stable alpha basis**，与工艺无关。

**Anti-recap (本方向已探完)**:
- ROE/ROIC/ROA/gross_margin/growth/-debt_to_asset 6 个 quality numerator 类型全测
- narrow basis (size+vol) vs wide basis (+book_to_price) 对照覆盖
- 不重做 b068/b069/b070 已 reject 的 18 DSL Div/Mul 候选
- 不复用 b070 的 rank × rank Mul（已穷举）

## Known Failures

| Batch | Candidate | Expression | Reject reason |
|---|---|---|---|
| [[batches/batch_071/candidates/C001\|batch_071 C001]] | C001 | `Python: residualize(ROE_ttm, [size, vol_20d]) → CsRank` | hard_gate sign_flip (train +0.014/val -0.009) + oos_decay=-0.61. alpha_surv=0.93 PASS, vol_20d_exp=22.9 dom-high — OLS 剔除线性 βvol 但非线性载荷残留 |
| [[batches/batch_071/candidates/C002\|batch_071 C002]] | C002 | `Python: residualize(ROIC_ttm, [size, vol_20d, b/p]) → CsRank` | hard_gate sign_flip + oos_decay=-0.28. alpha_surv=2.40 整批第二高，3-basis 全控制仍 vol_20d_exp=17.3 dom |
| [[batches/batch_071/candidates/C003\|batch_071 C003]] | C003 | `Python: residualize(gross_margin_ttm, [size, vol_20d]) → CsRank` | hard_gate sign_flip + IS IC=+0.0012 极弱（C001 ROE 是 +0.014, 10x 差）. gross_margin 在 csi1000 daily 几乎无 cross-section 信号 |
| [[batches/batch_071/candidates/C004\|batch_071 C004]] | C004 | `Python: residualize(ROA_ttm, [size, vol_20d, b/p]) → CsRank` | hard_gate sign_flip. **sign_consistency=1.0 整批唯一**（IS 4/4 split 全同号）但 OOS 翻号 — IS 内一致 ≠ OOS sign-stable |
| [[batches/batch_071/candidates/C005\|batch_071 C005]] | C005 | `Python: residualize(winsorize_5MAD(growth_ttm), [size, vol_20d]) → CsRank` | hard_gate sign_flip. **dominant_style=ep_ratio=11.2 整批唯一非 vol_20d** — winsorize+narrow basis 让 ep_ratio 替代 vol_20d；max_corr=0.10 库内最独立但 OOS 翻号 |
| [[batches/batch_071/candidates/C006\|batch_071 C006]] | C006 | `Python: residualize(-debt_to_asset_ttm, [size, vol_20d, b/p]) → CsRank` | hard_gate sign_flip + oos_decay=-0.11. **alpha_surv=7.23 整批最高**（solvency 与 size/vol/value 几何独立） + val_ic=-0.0007 整批最弱反号；sign_consistency=0.5 IS 内本就 unstable |

## Narrative Log

### 2026-05-02 — batch_071 (round 71) · ✗ DISPROVEN T001

**结论**: 6/6 候选 hard_gate sign_flip — Python OLS residualize TTM quality on (size, vol_20d, [book_to_price]) → CsRank 路径**完全证伪**。

**关键发现**:
1. **alpha_survival 全部 ≥ 0.93**（C001=0.93, C002=2.40, C003=1.20, C004=1.49, C005=1.95, C006=7.23）— 工艺执行充分，OLS 确实剔除 Barra style 线性 component
2. **dominant_style 仍 vol_20d 5/6**（C001=22.9, C002=17.3, C003=11.6, C004=18.6, C006=14.4）— **Linear OLS 不破 csi1000 vol_20d 非线性吸收**
3. **完整 IC by year regime drift**：2015-2018 强正 → 2019-2021 衰减 → 2022-2023 翻号；C001 ROE: +0.0256 → ... → -0.0138
4. **alpha_survival 与 OOS sign-stable 完全解耦** — alpha_surv 高（7.23）也不预测 OOS alive（C006 val_ic=-0.0007）

**机制层判断**: **不是 vol_20d 吸收问题，是 csi1000 daily 上 TTM quality 类信号 2022-2023 全 regime sign-flip**。lessons.md L1 提供的"逃离路径 b" (Python residualize) 通过本批被验证为**死路**。

**direction status**: 建议 `probing → dead`（mechanism dead，无残余探索路径，无 reserve 火种）。

**lessons.md 升格候选**:
- "csi1000 daily TTM quality OLS-residualized signal 2022-2023 全 regime sign-flip — fundamental quality 类 alpha 在 A 股小盘 2022 后死区"
- "Linear OLS residualize 不破 csi1000 vol_20d 非线性吸收 — 5/6 残差仍 vol_20d_exp 11~22"
- "alpha_survival 与 OOS sign-stability 解耦 — alpha_surv >5 也不预测 OOS alive，不可单独依赖作 admission gate"

> [!success]+ 2026-05-02 · Phase 5 round 73 consolidation · 方向状态 probing → dead
> **3 条元教训已升格至 lessons.md**：
> 1. `Path Selection` 新增 "alpha_survival ≥ 0.40 必须配 ic_by_year 后期同号 check"（[[_consolidation/findings/pattern_analyst/011]] + [[_consolidation/findings/calibration/006]] 升格）— CP02 判据 composition 显化，alpha_surv 不可独立作 admission gate
> 2. `Path Selection` 新增 "Linear OLS residualize 不破 csi1000 vol_20d 非线性吸收"（[[_consolidation/findings/hypothesis_promoter/010]] 升格）— 限定 lessons L1 "逃离正路径 (a) Python Barra residual orthogonalize" 语义边界：仅在 numerator 自身 OOS-stable alpha 时该路径生效
> 3. `Path Selection` 顶层 macro lesson 段 "csi1000 daily fundamental + institutional flow 真饱和" 路径 c（Python OLS residualize TTM quality）作为 5 路径独立证伪之一（[[_consolidation/findings/pattern_analyst/014]] + [[_consolidation/findings/hypothesis_promoter/008]] 升格）
>
> **状态机变更**：probing → **dead** (first-batch dead 律：6/6 reject + ≥2 候选独立命中 hard_gate sign_flip + 失败机制是 alpha 真不存在不是窗口/算子细节)；priority `high → low`；T001 `[✗ DISPROVEN batch_071]`，无续探 thread。
>
> **复活前置**：(a) lessons.md "Linear OLS 不破非线性 vol_20d 吸收"被推翻（Polynomial/Kernel 工艺接入 + 跨方向独立验证）；或 (b) minute/tick 数据接入推翻 csi1000 daily TTM quality 真饱和；或 (c) cross-universe (csi300/csi500) 验证 TTM quality alpha 在其它 universe 仍 alive。
>
> **下批 frontier 替代**：library_gap/011 提出 `python_residualize_non_quality`（工艺已验证有效 - F004/F005 admit；但 numerator 选择是关键 unknown，需先验 cross-section 独立证据再投预算避免 b071 retread - low 优先级）。

