---
batch_id: batch_048
direction: overnight_intraday_split
judged_at: 2026-04-25T04:30:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: admit, factor_name: overnight_turnover_rank_diff_5}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reserve}
batch_summary: {total: 6, admit: 1, reserve: 1, reject: 4}
admit_count: 1
reserve_count: 1
reject_count: 4
candidate_count: 6
mt_bucket: high
---

# batch_048 Judge Summary

> [!abstract]+ [[directions/overnight_intraday_split]] · 6 candidates
> ✅ **admit=1** (C003 → overnight_turnover_rank_diff_5) · ⏸ **reserve=1** (C006) · ❌ **reject=4**
> **核心发现**: **rank-diff 范式二次跨家族泛化兑现 + T004 ratio 形式 DISPROVEN**——C003 `CsRank(overnight_5d) − CsRank(turnover_rate_5d)` 把 batch_046/047 在 microstructure 内部升格的 "rank-diff = signal-family 组合几何性质" 成功外推到 overnight_intraday_split × turnover 跨 direction 组合 (ic_oos=0.054 ls_t=4.75 incr_ic=0.027 mono_oos=0.9 9/9 年全正且近年 2022/2023 最强)。方向从 saturated 被正确结构 **partially 复活**——复活条件 (c) "overnight × 其它 signal 非线性交互"首次命中。
> **T004 悬挂复活假设证伪**: C004 `Div(overnight_5, |intraday_5|)` ratio 形式 incremental_ic=0.002 + max_corr=0.898@F010——ratio 在 csi1000 日频被 F010 吸收，|intraday| 分母未产生独立信息维度。
> **rank-diff 设计硬约束三条证据链完整**: C001 (同信号对偶吸收律) + C002 (共 numerator 抵消律) + C005 (同字段跨窗口 rank-diff 抵消律) 三条 reject，合并升格到 lessons.md："rank-diff 两端必须有 ≥1 独立 raw field (num OR denom) 且不能是单一 aggregation 窗口差异"。generator 层应 pre-filter。
> **MT Budget**: cumulative 246 → **252** · direction 9 → **15** · bucket `high`（search_adjusted medium, C003 原档 strong 降到 borderline）

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | 🔴 hard_gate | max_corr=**0.925**@F009 | CsRank 外包无法 escape raw-diff aggregation F009 吸收律 | [[batches/batch_048/candidates/C001]] |
| C002 | ❌ reject | 🔴 hard_gate | ic_oos=\|0.004\|<0.008 noise | 共 numerator (open-prev_close) 让 Sub 抵消，shared-denom 抵消律对偶 | [[batches/batch_048/candidates/C002]] |
| C003 | ✅ admit | 🟢·🟡·🟡·🔴·🟢 | IC=+0.054 mono=+0.9 ls_t=+4.75 incr=+0.027 max_corr=0.747@F010 | rank-diff 跨 direction 泛化首锤兑现 | [[batches/batch_048/candidates/C003]] · [[factors/F017]] · F{id}@Phase4 |
| C004 | ❌ reject | 🟢·🟡·🟡·🔴·🟢 | IC=+0.016 alpha_surv=0.34 incr=**0.002** max_corr=0.898@F010 | T004 ratio 形式证伪——被 F010 吸收 | [[batches/batch_048/candidates/C004]] |
| C005 | ❌ reject | 🔴 hard_gate | ic_oos=\|-0.0014\|<0.008 | 同字段跨窗口 rank-diff 抵消退化 noise | [[batches/batch_048/candidates/C005]] |
| C006 | ⏸ reserve | 🟢·🟡·🟡·🔴·🟢 | IC=+0.034 ls_t=+3.77 alpha_surv=0.552 incr=+0.021 max_corr=0.722@F010 | 同批 anchor rule 次于 C003（LHS 共享 overnight_rank） | [[batches/batch_048/candidates/C006]] |

**档位编码**：🟢 最优档（aligned/strong/clean/low/stable）· 🟡 次档（mixed/borderline/acceptable/medium）· 🔴 阻断档（misaligned/weak/poor/high/unstable）· `hard_gate` reject 该列写 `hard_gate` 不填色。

## 跨候选对比

- **C003 admit vs C006 reserve — 同批 anchor rule (LHS 共享 overnight_rank)**: 两者都是 rank-diff with overnight 5d LHS，C003 RHS=turnover_rank (跨 direction), C006 RHS=|intraday|_rank (同 direction 内部)。C003 全面占优：incr_ic 0.027 > 0.021, ls_t 4.75 > 3.77, ICIR 0.466 > 0.389, alpha_surv 0.431 borderline vs C006 0.552 acceptable (C006 CP04 略强)。LHS 共享导致 mutual corr 预期 0.6-0.8, 同时入库会形成 overnight×orth rank-diff 家族冗余——选 C003 admit，C006 reserve 等待 C003 入库后下轮以独立维度重评。**升格教训**: rank-diff 同批候选若 LHS 共享主信号端，同批最多 admit 1 个（extend batch_047 "Sub 反向对偶 dedup" 到 "LHS 共享也要 dedup"）。

- **C003 admit vs C004 reject — rank-diff vs ratio 结构比较**: 都 overnight × intraday 交互信号，C003 用 rank-diff (CsRank - CsRank), C004 用 ratio (Div(..,|..|))。C003 incr_ic=0.027 vs C004 incr_ic=0.002——**rank-diff 的信息提炼效率比 ratio 高 13 倍**。ratio 受分母数值主导（|intraday| 极小时放大不稳），rank-diff 对数值量级不敏感只看 cross-section 相对位置，结构上优于 ratio。T004 thread 证伪 ratio 路径后，rank-diff 成为 overnight × orth signal 交互的唯一存活形式。

- **C001 reject vs C003 admit — CsRank 外包是否 escape raw-diff 吸收**: C001 `Sub(CsRank(overnight_5), CsRank(intraday_5))` max_corr=0.925@F009，CsRank 外包 F009 raw-diff aggregation 失败（rank 空间在 overnight/intraday 这对小 pct return 上保序近似线性）；C003 `Sub(CsRank(overnight_5), CsRank(turnover_5))` max_corr=0.747@F010 成功 escape F009/F010。**升格教训**: rank-diff escape raw-diff 吸收的关键不在 CsRank 本身，而在 RHS 是否引入独立 direction 的 signal——同-direction rank-diff 仍被 raw aggregation 吸收（C001），跨-direction rank-diff 才能开辟新维度（C003）。

- **C002/C005 reject — shared-raw-field 抵消律三条证据链完整**:
  - C002: 两端共 numerator (`$open-Ref($close,1)`) → ic_oos=0.004 noise
  - C005: 两端完全同字段只差 aggregation 窗口 → ic_oos=-0.0014 noise
  - (batch_047 C002 历史对偶): 两端共 denominator ($amount) → ic_oos=0.007 noise
  - 三条合并升格到 lessons.md: rank-diff 设计硬约束 = 两端必须有 ≥1 个独立 raw field（numerator OR denominator）且不能是单一 aggregation 窗口差异。

- **方向兑现率**: 1 admit / 6 candidates = 17%（与 batch_046/047 同）；本批 admit 机制价值 ≈ batch_047（rank-diff 二次跨家族泛化兑现）但方向 priority 不同——overnight_intraday_split 原 saturated 被正确结构复活，microstructure_illiquidity 是 productive 持续。rank-diff 范式已跨 3 个方向（microstructure/value-liquidity 暗线/overnight_intraday）独立泛化成功，接近 lessons 通用几何性质地位。

## Thread 进展

> [!success]+ T005 [[directions/overnight_intraday_split#T005]] 🆕 — `[◐ PARTIAL-ANSWERED batch_048]`
> **rank-diff 跨 direction 泛化在 overnight 家族兑现**：
> - C003 (overnight × turnover rank-diff) → **admit** → overnight_turnover_rank_diff_5。证实 rank-diff 结构 alpha 可在 overnight × orth direction signal 上产出独立 alpha。
> - C001 (CsRank overnight − CsRank intraday) → reject near_duplicate F009。升格约束：CsRank 外包 F_parent=Mean(A-B,N) 型已入库因子仍被吸收，同-direction rank-diff 不 escape。
> - C002 (overnight 3d vs overnight_gap norm) → reject ic_oos noise。升格约束：共 numerator 抵消律。
> - C006 (overnight_signed × |intraday|) → reserve（同批 anchor rule，LHS 共享 overnight_rank 让位 C003）。
>
> **结论**: T005 约束完善——(a) 两端必须独立 direction 或独立 raw field；(b) 两端都 scale-free; (c) 同批若 LHS 共享主信号端最多 admit 1 个。

> [!failure]- T004 [[directions/overnight_intraday_split#T004]] — `[✗ DISPROVEN batch_048]`
> **overnight/intraday ratio 形式证伪**: C004 `Div(overnight_5, |intraday_5|)` max_corr=0.898@F010 + incremental_ic=0.002 < 0.003。ratio 在 csi1000 日频被 F010 overnight persistence 吸收——|intraday| 分母未产生独立信息维度。T004 悬挂复活失败，关闭。

> [!failure]+ T006 [[directions/overnight_intraday_split#T006]] 🆕 — `[✗ DISPROVEN batch_048]`
> **overnight horizon-diff rank (CsRank(20d) − CsRank(5d)) 证伪**: C005 ic_oos=-0.0014 noise——两端完全同字段只差 aggregation 窗口，rank 高度相关使 Sub 抵消。**新开 thread 立即 disproven**——值得升格到 lessons 作为 rank-diff 设计约束第三条证据。

## 方向级反思

`overnight_intraday_split` 方向从 **saturated 被正确结构部分复活 → partially productive**。admit 从 3（F009/F010/F011）→ 4（+C003），direction rounds 3→4，priority 维持 high。核心驱动是 rank-diff 范式跨家族泛化到 overnight × turnover 的成功——rank-diff 已成为**跨 3 个 direction 独立泛化验证的通用几何范式**（microstructure_illiquidity F015/F016, overnight_intraday_split F017-to-be），可作为 Phase 5 consolidation 升格到 lessons.md 的强候选教训。

**下轮建议**（若本方向继续）:
1. 测试 **rank-diff 第三波泛化**: overnight_rank × 其它独立 direction scale-free signal（如 Amihud illiquidity rank, pb_amount ratio rank）——注意避免 LHS 始终是 overnight_rank（同批 anchor rule 扩展约束）
2. C006 的 "signed × magnitude 异质函数结构" 可作为独立维度，在非 overnight LHS 上重新测试（如 turnover_signed × |price_magnitude| rank-diff）
3. direction 复活条件 (b) "20d+ overnight persistence" 仍未测——若引入 20d 窗口需避开本批 C005 确认的 "同字段跨窗口抵消律"，应与独立 RHS 结合

**方向复活 + rank-diff 三向泛化**: 若下一批新家族测试 rank-diff 再次兑现（如 OHLC temporal aggregation × liquidity rank-diff），可触发 Phase 5 consolidation 将 rank-diff 几何性质从 direction-level 升格为 lessons.md Data Facts 级别设计原则。
