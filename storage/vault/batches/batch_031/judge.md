---
batch_id: batch_031
direction: microstructure_illiquidity
judged_at: 2026-04-23T13:00:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reserve}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 0, reserve: 1, reject: 5}
admit_count: 0
reserve_count: 1
reject_count: 5
candidate_count: 6
mt_bucket: medium
---

# batch_031 Judge Summary

> [!abstract]+ batch_031 · [[directions/microstructure_illiquidity]] · 6 candidates · T001+T004 深化
> ❌ **admit=0** · ⏸ **reserve=1** (C003) · ❌ **reject=5** (C001/C002/C004/C005/C006)
> **核心发现**: **F012 是 DSL Amihud 空间的几何不变量**——horizon 扫描（10d/5d-return）与 rank-preserving 残差化（CsZscore/vol-residualize）4/4 触 `near_duplicate` 硬闸（corr 0.919-1.000@F012）；唯一结构真正不同的 PB/Amihud（C006）被自身 PB style 吞噬 + signed negative incr_ic；仅 C003 Amihud/mean_turnover 略出 near_dup 线（corr=0.707）但 CP04 alpha_survival 从 F012 的 0.443 塌至 0.137（vol_20d exposure 从 5.9 爆 3× 到 21.5）——**residualization 只搬家没减负**。方向快速逼近 saturated。
> **MT Budget**: cumulative 146 → **152** · direction 6 → **12** · bucket `medium` · 本批 low=0 / medium=2 / high=0（4 hard_gate reject 不计档）

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | hard_gate | 10d Amihud / max_corr=0.957@F012 | Horizon 缩短（20d→10d）保留 rank-order → F012 几何不变量首证 | [[batches/batch_031/candidates/C001]] |
| C002 | ❌ reject | hard_gate | Amihud/realized_vol / max_corr=0.919@F012 | Vol-residualize 把 F012 vol_20d 暴露从 5.9 放大到 32.6（退化为纯 vol 载体）→ residualization 搬家失败 | [[batches/batch_031/candidates/C002]] |
| C003 | ⏸ reserve | 🟢·🟢·🔴·🔴·🟢 | Amihud/mean_turnover / alpha_surv=**0.137** max_corr=0.707@F012 incr_ic=0.042 | Turnover-residualize 改善 style_r²（0.47→0.31）但 alpha_survival 崩塌（0.44→0.14），vol_20d 反而 3× 激活→ negative evidence 归档 | [[batches/batch_031/candidates/C003]] |
| C004 | ❌ reject | hard_gate | CsZscore(Amihud) / max_corr=**1.000**@F012 | CsZscore 是 rank-preserving 单调变换，横截面排序不变 → re-scale ≠ residualize，空对照 | [[batches/batch_031/candidates/C004]] |
| C005 | ❌ reject | hard_gate | 5d-return Amihud / max_corr=0.959@F012 | 5d return vs 1d return 在 20d Mean 聚合下代数几乎等价 → 分子 horizon 不打开独立轴 | [[batches/batch_031/candidates/C005]] |
| C006 | ❌ reject | 🟡·🟢·🔴·🔴·🟡 | PB/Amihud / alpha_surv=**0.025** incr_ic=**-0.044** max_corr=0.788@F012 | Div(PB, Amihud) ≈ F012 反向载体（PB 分子被自身 style 吞噬）；single strong 但库减值 → rubric CP05 high + signed negative incr_ic 决定性 reject | [[batches/batch_031/candidates/C006]] |

**档位编码**：🟢 最优档 · 🟡 次档 · 🟠 边际 · 🔴 阻断档；hard_gate reject 列填 `hard_gate` 不填色。

## 跨候选对比

- **F012 几何不变量证据链（5/6 候选）**：
  - Horizon 扫描（C001 10d / C005 5d-return）: corr 0.957 / 0.959 @ F012 — horizon 变化不改变 rank-order
  - Rank-preserving 变换（C004 CsZscore）: corr 1.000 @ F012 — CsZscore 保序
  - Vol 残差化（C002 Amihud/Std(ret,20)）: corr 0.919 @ F012 — vol 分母虽改变 scale 但不改排序
  - PB 分子交互（C006 Div(PB, Amihud)）: corr 0.788 @ F012 — Div 让分母 F012 主导
  - Turnover 分母残差化（C003 Amihud/Mean(turnover,20)）: corr 0.707 @ F012 — **唯一略出 near_dup 线但 CP04 塌陷**
- **T004 residualization 路径整体证伪**：C002 (vol) / C003 (turnover) / C004 (cs-normalize) 三种 DSL residualization 角度均失败——（a）CsZscore 保序零贡献；（b）vol-residualize 把 F012 变成更纯的 vol 载体（style_r²=0.47→worse）；（c）turnover-residualize 仅搬家（style_r² 0.47→0.31 改善但 alpha_surv 0.44→0.14 塌陷）。**DSL 层 residualization 不足以把 F012 变成 Barra-clean**——需要真正的 OLS Barra 残差（Python 逃生口）。
- **T004 cross-field 路径首证伪（C006）**：Div(fundamental, Amihud) 代数 ≈ -F012 × fundamental_weight；PB 分子被自身 style (book_to_price exposure=1.42) 吞噬；admit 会减库 IC ~4.4%。**Mul 和 Div 都撞量纲陷阱**——交互路径需走 rank-diff 或 residual 结构（value_liquidity_interaction 方向同样教训）。
- **风格暴露对比**：F012(5.9 vol_20d + 7.8 turnover_20d 双吞噬) → C002(32.6 vol_20d 压倒一切) / C003(21.5 vol_20d 放大 3×) / C006(turnover_20d 仍是 dominant)。所有 residualization 候选都使 vol_20d exposure **净增** —— 证 microstructure direction 的物理约束**就是 Barra vol_20d basis 本身**，不是某个特定 style。
- **MT 预算**：cumulative 146→152；direction 6→12；bucket 仍 medium。方向累计 12 候选全部 dominant ∈ {vol_20d, turnover_20d}，0/12 脱离 Barra basis。

## Thread 进展

> [!failure]+ T001 [[directions/microstructure_illiquidity#T001]] — `[✓ ANSWERED batch_031]`
> horizon 扫描（10d / 5d-return / 60d batch_030 C002）均撞 near_duplicate 或 CP04 poor：**F012 (Amihud 20d amount-denom) 是 T001 DSL 空间的局部+全局最优**，horizon 缩短/拉长/分子 return 步长调整全部维持与 F012 高相关（≥0.677）。**T001 答案**：Amihud illiquidity 作为独立 alpha 轴存在且被 F012 单点最优完全占据；DSL 层该 thread 封闭。Next probes 全部 Python 层（Barra residualized Amihud 在 [[directions/barra_residual_alpha]] 方向跑）。

> [!failure]+ T004 [[directions/microstructure_illiquidity#T004]] — `[✗ DISPROVEN batch_031]`
> residualization (C002/C003/C004) 与 cross-field (C006) 两条子路径**同批 4/4 失败**：
> - CsZscore 保序零贡献（C004 corr=1.00）
> - vol-residualize 放大 vol_20d 暴露（C002 corr=0.92 + exposure 5.9→32.6）
> - turnover-residualize 搬家（C003 corr=0.71 + alpha_surv 塌 69%）
> - PB/Amihud 撞 Div 量纲陷阱（C006 incr_ic=-0.044）
>
> **DSL 层 residualization 物理封闭**，真正的 orthogonalization 必须走 Python Barra OLS。Cross-field 交互走 Div 与走 Mul 同样被量纲吞噬——symmetric rank-diff 是唯一未试路径，但当前 direction 已进入 ROI 衰退区。

## 方向级反思

**方向快速 saturated 证据链**（batch_030 admit + batch_031 零 admit 双证）：
1. **T001 局部最优锁定**：F012 作为 Amihud 20d amount-denom 是 DSL 空间几何不变量（5/5 近邻候选 corr≥0.707）；admit 率从 17%（1/6）降至 0%（0/6）
2. **T002 已 ANSWERED**（batch_030 HHI 家族：机制真实库已吸收）
3. **T003 已 DISPROVEN**（batch_030 Entropy 弱于 HHI 2.6×）
4. **T004 已 DISPROVEN**（batch_031 residualization + cross-field 4/4 失败）

**方向操作**（由 LLM 在 Phase 4 Narrative Log 翻 status）：建议 `productive → saturated` · priority `high → low`。5 个 Python-native 复活条件：
- (a) Barra residualized F012 走 [[directions/barra_residual_alpha]] 方向
- (b) rank-diff 结构 `Sub(CsRank($pb), CsRank(Amihud))` 类 symmetric 交互（下一 batch 最后尝试空间）
- (c) 更精细 microstructure 原语（minute-bar / tick-level 数据进入后）
- (d) 与 overnight_intraday_split 成员交互（F010 overnight persistence × Amihud）
- (e) 非线性 Sigmoid/Tanh 压扁 variants（预期也保序，ROI 低）

**系统级新教训**（候选升格 lessons.md）：
1. **Rank-preserving 变换（CsZscore / Scale / Sigmoid / Tanh）在 cross-section 空间对 IC 零贡献** — 下轮任何 direction 首轮 skip 这类候选
2. **DSL 层 residualization `Div(factor, proxy)` 不是真 orthogonalization** — rank-order 保留或 style exposure 搬家，非减负；真 residualize 必走 Python OLS
3. **Amihud 20d amount-denom 是 A 股 csi1000 日频 DSL 空间的 microstructure illiquidity 局部最优** — 同家族 horizon/residualize 扫描 ROI ≈ 0

**错杀侦测**：本批无候选满足错杀全四条件。C003 接近（ls_t=5.12 + mono=1.0 + sign_consist=1.0 + cum_mdd=-1.18 浅），但 max_lib_corr=0.707 > 0.30 不满足"库空间独立"第一条；且 nearest=F012 同向（非符号互补）。不触发 calibration。

**下一步**（Round 3）：microstructure_illiquidity 转 saturated 后，下轮应选另一个 productive 方向。根据 snapshot，候选：
- `value_liquidity_interaction` (productive, 6 rounds)—— DSL 空间已穷尽
- `amount_volatility_signal` (productive, 5 rounds) —— 同样 DSL 空间穷尽
- `liquidity_acceleration` (exploring, 1 round) —— 等 F001 退役
- 或根据新教训开启新 DSL-native 方向——基于"rank-preserving 变换空集" 与"DSL residualization 非真 orth"负向经验，探 `asymmetric_rank_diff` 或 `tail_extremes` 等未触原语
