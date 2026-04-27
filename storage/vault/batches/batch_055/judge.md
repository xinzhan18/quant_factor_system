---
batch_id: batch_055
direction: range_structure
judged_at: 2026-04-25T09:10:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: admit, factor_name: upper_shadow_disp_range_compress_rd_20}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 1, reserve: 0, reject: 5}
admit_count: 1
reject_count: 5
reserve_count: 0
candidate_count: 6
mt_bucket: high
---

# batch_055 Judge Summary

> [!abstract]+ batch_055 · [[directions/range_structure]] · 6 candidates
> ✅ **admit=1** (C005→F{next}) · ⏸ **reserve=0** · ❌ **reject=5**
> **核心发现**: **range_structure 首个 admit！P002 rank-diff geometry 在 range family 兑现第 6 跨 family admit。** C005 (upper-shadow position dispersion × range compression) 唯一通过严格准则 (mono_oos=+1.0 完美 + cum_mdd=-1.14 库内最浅 + ic_by_year 9 年单调增强 + max_corr=0.44@F020 反向互补 + incr_ic=+0.008 库增值)。其余 5 候选 (C001/C002/C003/C004/C006) 全部撞上"rank-diff 同向 vol_20d 簇 reducer"陷阱：incremental_ic 全负 (-0.013/-0.008/≈0/-0.007/-0.012)，验证 P005 RHS basis 共振饱和律的动态性——同样的 rank-diff 几何 6 次跨 family 成功后，本批 1/6 通过显示设计精度门槛已显著提升。
> **MT Budget**: cumulative 282 → **288** · direction 6 → **12** · bucket `high`（adj `medium`）· 本批 low=0 / med=0 / high=6

## 候选一览

| ID   | Verdict  | 档位 (CP2·3·4·5·6)       | Key Metric                                                           | 反思                                             | Detail                                |
| ---- | -------- | ---------------------- | -------------------------------------------------------------------- | ---------------------------------------------- | ------------------------------------- |
| C001 | ❌ reject | 🟢·🔴·🔴·🟠(incr-)·🔴  | ls_t=-0.40 incr=-0.013 vol20d_exp=38.8                               | range Std × volume 同 vol+liquidity 簇 reducer   | [[batches/batch_055/candidates/C001]] |
| C002 | ❌ reject | 🟢·🟡·🔴·🟠(incr-)·🔴  | ls_t=-2.92 mono=-1.0 incr=-0.008                                     | "看似强 alpha 但库减值"陷阱第 4 次复现                      | [[batches/batch_055/candidates/C002]] |
| C003 | ❌ reject | 🟡·🔴·🔴·🟠(incr≈0)·🔴 | ls_t=-1.39 vol20d_exp=58.1 str_1m=3.84 incr≈0                        | sign-RHS 未起独立维度 + 双 style 强吸收                  | [[batches/batch_055/candidates/C003]] |
| C004 | ❌ reject | 🟡·🔴·🔴·🟠(incr-)·🔴  | mono_paradox -1.0→-0.30 ls_t=-0.65 incr=-0.007                       | b043 C004 paradox 第 3 次复现 + F005 mirror trap   | [[batches/batch_055/candidates/C004]] |
| C005 | ✅ admit  | 🟢·🟡·🟡·🟡·🟢         | ic_oos=+0.043 mono=+1.0 cum_mdd=-1.14 incr=+0.008 ic_by_year 9 年单调增强 | range family 首 admit + intraday position 维度首突破 | [[batches/batch_055/candidates/C005]] · [[factors/F021]] |
| C006 | ❌ reject | 🟡·🔴·🔴·🟠(incr-)·🔴  | style_r²=**0.75 本批最高** ls_t=-0.62 mono collapse incr=-0.012          | Std60 长窗未替代 Kurt 稳健性，反而深陷 vol+size 双 style     | [[batches/batch_055/candidates/C006]] |

## 跨候选对比

**Style 聚合 (本批 6 候选共性)**：
- 全部 6 候选 `dominant_style_exposure = vol_20d`，exp 范围 **18.8 (C005) – 58.1 (C003)**
- C005 vol_20d exp 最低 (18.8)、style_r² 最低 (0.20)、style_crowding `medium`（其它 5 个全 `high`）——这是 C005 admit 的关键差分
- C003 + C006 是双 style 灾难：C003 vol_20d=58.1 + str_1m=3.84；C006 vol_20d=30.9 + log_circ_cap=0.586 + alpha_surv=0.71 假象
- C004 ep_ratio exp=1.94（最高 value 暴露），LHS (H-L)/prev_close 触 F005 algebraic mirror

**Incremental_ic 一览**（库增值真实性最关键指标）：
- ✅ C005 = **+0.008** (库增值)
- ❌ C001 = -0.013, C002 = -0.008, C003 ≈ 0, C004 = -0.007, C006 = -0.012
- **5/6 incremental_ic 负或 ≈0**——这是本批最强结构性发现：**rank-diff geometry 已饱和到这种程度，新候选不仅不能加 corr 独立性，连库 IC 增量都拿不到**。这是 P004 vol_20d 结构性吸收律 + P005 RHS basis 共振饱和律的联合表现：5 个 RHS (volume_60/pe_60/up_freq_20/VWAP_60/range_compress_60/circ_market_cap_60) 中只有 range_compress_60 (C005 RHS) 真正独立。

**MT 预算推进**：cumulative 282 → 288；direction 6 → 12；bucket high → search_adjusted medium。range_structure direction 在本批 admit 后 round=3, admits=1, status: exploring → **productive**。

**ls_t IS/OOS 翻号 / 衰减**（Validation regime stability）：
- C001: IS+2.42 / OOS-0.40 (翻号)
- C004: IS-3.02 / OOS-0.65 (大幅衰减 0.22)
- C006: IS+2.06 / OOS-0.62 (翻号)
- C003: IS-5.23 / OOS-1.39 (大幅衰减 0.27)
- C005: IS+1.61 / OOS+2.38 (**OOS 增强 1.5x，唯一 IS→OOS 同向且增强的候选**)

C005 在 train_validation_decay=1.96 是"信号增强型"（IS<OOS）而非 inflated——结合 ic_by_year 单调增强趋势，证明这是 regime-robust 的真实 alpha 而非 IS overfit 表象。

## Thread 进展

> [!success]+ T001 [[directions/range_structure#T001]] — `[✓ ANSWERED batch_055]`
> 答案：(1) 是的，range 结构化 transformation **能**在 cross-section 上逃 vol_20d——具体路径是 **upper-shadow position dispersion (Std of (H-C)/(H-L)) × long-window range compression (Mean of H/L) rank-diff**（C005 → admit）。(2) 但 admit 路径精度门槛极窄：6 候选只有 1/6 通过，5/6 因 incr_ic ≤ 0 库减值被拒。(3) Kurt-centric 路径在 DSL 下被 operators.py:428 bug 阻塞（C002/C006 用 Std 替代均失败），需要 Python escape hatch 或 bug 修复。
>
> **Evidence trail (本批新增)**:
> - [[batches/batch_055/candidates/C001|batch_055 C001]] range Std × volume_60 ls_t=-0.40 incr=-0.013 → **reject** (F012 reducer)
> - [[batches/batch_055/candidates/C002|batch_055 C002]] Garman range Std × pe_60 mono=-1.0 ls_t=-2.92 incr=-0.008 → **reject** (rank-diff cluster reducer)
> - [[batches/batch_055/candidates/C003|batch_055 C003]] H/L Std × sign_freq_20 vol_20d=58.1 incr≈0 → **reject** (sign-RHS 未起独立维度)
> - [[batches/batch_055/candidates/C004|batch_055 C004]] (H-L)/prev_close Mean × VWAP_60 mono paradox -1.0→-0.30 incr=-0.007 → **reject** (b043 C004 同 paradox)
> - [[batches/batch_055/candidates/C005|batch_055 C005]] (H-C)/(H-L) Std × H/L Mean_60 ic=+0.043 mono=+1.0 cum_mdd=-1.14 incr=+0.008 → **admit**
> - [[batches/batch_055/candidates/C006|batch_055 C006]] Std((H-L)/C, 60) × market_cap_60 style_r²=0.75 incr=-0.012 → **reject** (Std60 ≠ Kurt-equivalent)

## 方向级反思

**range_structure direction 实现首次 admit**（status: exploring → productive），结束 3 rounds 0-admit 历史。但应清醒认识本批 1/6 通过率说明的几件事：

1. **rank-diff geometry 7 律 + factor-anchored cluster 检查**已达到极高的设计门槛——5/6 candidate 在 max_corr 都 < 0.55 看似独立，incremental_ic 却全部 ≤ 0。这验证了 P005 RHS basis 共振饱和律的**动态性**：即使没有显式 RHS 重复，多个独立 RHS 通过 vol_20d common cause 仍构成"组合层冗余"。
2. **C005 admit 的成功要素**特别值得归纳：(a) LHS atom 是 close 在 H-L 范围内的位置（intraday position 维度），不是 range/body magnitude；(b) RHS Mean(H/L, 60) 是 long-window 几何 ratio (60d，与短窗 RHS 区分)；(c) style_crowding=medium 是 6 候选中唯一不 high 的；(d) cum_mdd=-1.14 是库内极罕见的"几乎从未失效"。这些条件**联合**才能通过门槛。
3. **下一步建议**:
   - **优先**：在 intraday position 维度沿 C005 atom 衍生（如 (C-L)/(H-L) Std, (C-prev_close)/(H-L) Std, body_position 等）× 不同 long-window scale-free RHS（不再尝试 short-window vol_20d-prone RHS）
   - **避免**：60d 长窗 + raw size/value RHS（C006 教训）；sign aggregation as RHS（C003 教训）
   - **TsKurt 路径**：operators.py:428 bug 阻塞了 P002 endorsed 的 higher-moment LHS 升级 — 需要 Python escape hatch 或修复 _build_cs_cache 让 D.features 接收已计算 LHS 数组而非 expression string
4. **status 调整**：`exploring → productive`（首次 admit），`priority: low → medium`（admit 验证 direction 仍有可挖空间）

若下一轮 (round 4) 沿 C005 衍生路径仍 0 admit + incremental_ic ≤ 0 ratio ≥ 80% → `productive → saturated`。
