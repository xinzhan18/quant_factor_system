---
batch_id: batch_039
direction: pv_covariance
judged_at: 2026-04-24T03:10:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 0, reserve: 0, reject: 6}
admit_count: 0
reserve_count: 0
reject_count: 6
candidate_count: 6
mt_bucket: medium
---

# batch_039 Judge Summary

> [!abstract]+ [[directions/pv_covariance]] · 6 candidates
> ❌ **admit=0** · ⏸ **reserve=0** · ❌ **reject=6**
> **核心发现**: pv_covariance 方向**完全证伪**——Cov(x, y, N) 形态在 csi1000 被 F001 amount_cv / F009 overnight spread / F012 amihud 整簇吸收。6/6 pass hard_gate 但 IC_OOS 全负 (-0.042 至 -0.051)，mono 全负，incr_ic 全负 (-0.025 至 -0.032) 做库 reducer。无论 x ∈ {turnover/amount/volume/amount_ratio}, y ∈ {ret/body}, 窗口 20/60，都同簇。
> **MT Budget**: cumulative 192 → **198** · direction 0 → **6** · bucket `medium`

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | 🔴·🔴·🟡·🔴·🟡 | IC_OOS=-0.049 mono=-0.7 incr=-0.029 | turnover×ret 20d → F001 反转 | [[batches/batch_039/candidates/C001]] |
| C002 | ❌ reject | 🔴·🔴·🔴·🔴·🟡 | IC_OOS=-0.042 alpha_surv=0.34 | amount×body → F012 amihud 簇 | [[batches/batch_039/candidates/C002]] |
| C003 | ❌ reject | 🔴·🔴·🟡·🔴·🟡 | IC_OOS=-0.043 turnover_20d exp=7.78 | C001 60d 窗口，无新通道 | [[batches/batch_039/candidates/C003]] |
| C004 | ❌ reject | 🔴·🔴·🔴·🔴·🟡 | IC_OOS=-0.048 alpha_surv=0.37 | volume×dClose → F012 簇 | [[batches/batch_039/candidates/C004]] |
| C005 | ❌ reject | 🔴·🔴·🟡·🔴·🟡 | **IC_OOS=-0.051** max_corr=0.33@F001 | amount_ratio×ret → F001 最清晰同簇 | [[batches/batch_039/candidates/C005]] |
| C006 | ❌ reject | 🔴·🔴·🟡·🔴·🟡 | IC_OOS=-0.042 max_corr@F009 | turnover×body → F009 intraday 簇 | [[batches/batch_039/candidates/C006]] |

## 跨候选对比

- **方向 hypothesis 完全证伪**：6/6 IC_OOS 负，incr_ic 全负 (-0.025 至 -0.032)，max_corr 击中 F001/F009/F012 三个已有反转簇因子。Cov 形态在 csi1000 不是独立 family，只是已有 Std/Mean/Div/Mul 因子的"协动包装"。
- **无论配对/窗口都同簇**：(turnover, amount, volume, amount_ratio) × (ret, body) × (20d, 60d) 组合里没有一个跳出 F001/F009/F012 的覆盖。C005 最强 IC_OOS=-0.051 正是**最清晰的 F001 协动同簇证据**（max_corr=0.33@F001，批内最高）。
- **CP04 降档信号**：C002 alpha_surv=0.34（<0.40 阈）、C004 alpha_surv=0.37 直接 poor；其它 borderline。表明 vol_20d + str_1m + turnover_20d 三 Barra 载体共同吞噬。
- **第 4 次跨方向 csi1000 反转簇重现**：本轮加上 trend_quality_gated、log_value_liquidity、batch_032 liquidity_acceleration reserve — **csi1000 小盘 universe 的 "volume × direction" 复合形态都倾向于归簇 F001/F009/F012 family，无论 DSL 形式如何变化**。这是 meta-lesson 级发现。

## Thread 进展

> [!failure]+ T001 [[directions/pv_covariance#T001]] — `[✗ DISPROVEN batch_039]`
> C001 20d + C003 60d + C005 amount_ratio 全部 reject。turnover-ret Cov 无独立 alpha。

> [!failure]+ T002 [[directions/pv_covariance#T002]] — `[✗ DISPROVEN batch_039]`
> C002 amount×body + C004 volume×dClose + C006 turnover×body 全部 reject。换 pair 不换簇。

## 方向级反思

`pv_covariance` hypothesis 完全证伪，direction `exploring → dead`。Cov 形态是 csi1000 第四个跨方向重现的"volume × direction 反转簇"载体，应升格为 lessons.md 系统性经验（下次 consolidation）。

**Calibration**：6/6 reject 全部 incr_ic 负 + CP04 multiple poor/borderline，不是错杀。不触发校准。
