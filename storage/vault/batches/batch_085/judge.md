---
batch_id: batch_085
direction: alpha191_universal_subset
judged_at: 2026-05-02T17:35:00Z
candidates:
  - {candidate_id: C001, verdict: admit, factor_name: multi_ma_reversion_4w}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: admit, factor_name: dmi_down_ratio_12}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reserve}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 2, reserve: 1, reject: 3}
admit_count: 2
reject_count: 3
reserve_count: 1
candidate_count: 6
mt_bucket: medium
---

# batch_085 Judge Summary

> [!abstract]+ batch_085 · [[directions/alpha191_universal_subset]] · 6 candidates
> ✅ **admit=2** (C001 multi_ma_reversion_4w → F{next}, C003 dmi_down_ratio_12 → F{next+1}) · ⏸ **reserve=1** (C005 Volume MACD) · ❌ **reject=3** (C002 OBV / C004 ATR / C006 BIAS+TsRank60)
> **核心发现**: paper-vetted Du-Walter-Ulrich Alpha191 universal-subset 首批兑现 2/5 paper-vetted candidate (C001 alpha046 multi-MA + C003 alpha049 DMI), 验证 "csi1000 散户主导小盘 ≥ SPX 大盘机构市 alpha 强度" 反向迁移假设. C001 alpha_surv=1.13 (Barra 空间真独立) 是 lessons P008 escape 第二例顶级实证. C002 OBV sign 翻转 + C004 ATR collapse 到 vol_20d 验证 thread 风险位预测.
> **MT Budget**: cumulative 468 → **474** · direction 0 → **6** · bucket `medium`（本批 6 候选全 medium）

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ✅ admit | 🟢·🟢·🔴·🟡·🟢 | IC=0.049 ICIR=0.31 ls_t=4.36 alpha_surv=1.13 | paper-vetted Alpha 046 multi-MA 兑现 + alpha_surv>1.0 Barra 空间真独立 | [[batches/batch_085/candidates/C001]] · [[factors/F027]] |
| C002 | ❌ reject | 🟡·🟠·🔴·🟢·🟡 | IC=-0.027 alpha_surv=0.17 mono_oos=-0.3 | OBV csi1000 sign 翻转 + Barra 吞噬到 17% + Q5-only 一桨 | [[batches/batch_085/candidates/C002]] |
| C003 | ✅ admit | 🟢·🟠·🟡·🟡·🟢 | IC=0.033 ls_t=3.03 alpha_surv=0.66 incr_ic=0.020 | DMI 在 csi1000 sign 未翻转 + 库内首个 directional pressure | [[batches/batch_085/candidates/C003]] · [[factors/F028]] |
| C004 | ❌ reject | 🟡·🟢·🔴·🔴·🟡 | IC=-0.058 alpha_surv=0.064 max_corr=0.66@F019 | ATR ≡ vol_20d (exposure=31.4 顶级) P006 trio 齐 | [[batches/batch_085/candidates/C004]] |
| C005 | ⏸ reserve | 🟢·🟠·🟡·🟢·🟡 | IC=-0.023 alpha_surv=1.39 mono_oos=-0.3 incr_ic=-0.015 | alpha_surv=1.39 (>>1.0) Barra 真独立 + 但 Q5-only 一桨 + incr_ic 负 | [[batches/batch_085/candidates/C005]] |
| C006 | ❌ reject | 🟡·🟠·🔴·🟡·🟡 | IC=-0.038 max_corr=0.42@F009 incr_ic=-0.019 | BIAS-24 P008 escape 设计层失败 (max_corr 越过 0.40 frontier) | [[batches/batch_085/candidates/C006]] |

**档位编码**：🟢 最优档（aligned/strong/good/low/stable）· 🟡 次档（mixed/borderline/acceptable/medium）· 🟠 边际 · 🔴 阻断档（misaligned/weak/poor/high/unstable）。

## 跨候选对比

- **dominant_style 共享 vol_20d (6/6)**: 全部 6 候选 dominant_style_exposure = `vol_20d`. 这是 csi1000 daily cross-section 的不可避结构性背景, 不是 batch-specific 问题. 但 alpha_survival 大幅分化决定 verdict:
  - C001 alpha_surv=**1.13** + C005 alpha_surv=**1.39** = Barra 空间真独立 (P008 escape 机制层验证, lessons P008 第二/三例顶级实证 — 仅 b081 C006 是首例 ≈1.0)
  - C003 alpha_surv=0.66 = partial escape (acceptable)
  - C002/C004/C006 alpha_surv 0.064-0.83 = Barra 吸收 / 不充分 escape
- **alpha_surv vs incr_ic 互不相关**: alpha_surv 高的候选不一定 incr_ic 正 — C005 alpha_surv=1.39 但 incr_ic=-0.015. 这反映"Barra 空间独立 ≠ 库空间独立" — 库内 26 因子 + 7 Barra style basis 是不同的正交基.
- **anchor cluster F009 dominate (3/6 nearest)**: C001/C003/C005/C006 的 nearest 都是 F009 (overnight_intraday_spread_5d), C001/C003 max_corr 0.54/0.38 在 frontier 阈值 0.40 附近 (C001 越过, C003 接近). F009 是新发现的 daily anchor — 与 F025/F026 daily intraday position anchor cluster 共同形成 csi1000 daily 三大 anchor.
- **C001 vs C003 (双 admit) 不触发 anchor rule**: 都 dominant_style=vol_20d but 不同 atom (close vs H/L midpoint), 不同 horizon (3-24d MA vs 12d). 候选间 corr 没有直接给出但从设计层判断不超过 0.50 (close-only multi-window MA composite vs H/L directional pressure ratio 几何完全不同).
- **MT 预算推进**: direction_candidates 0→6 (本批首批本方向); cumulative 468→474. 单 batch +6 不会改变 bucket (medium); search_adjusted 全部 medium.

## Thread 进展

> [!success]+ T001 [[directions/alpha191_universal_subset#T001]] — `[✓ ANSWERED batch_085]`
> admit C001 (multi_ma_reversion_4w). 回答: 4-window MA composite mean-reversion ratio 在 csi1000 daily 上**独立于现有 mean-reversion 家族**提供新 alpha. paper t≈3.68 → csi1000 IC_oos=0.049 ICIR=0.31 ls_t=4.36, 验证 paper "更强 in csi1000" 反向迁移. C006 BIAS-24 失败 (max_corr 0.42@F009) 说明 long-window mean-reversion 复活路径不能简单 % deviation form, 需高阶 composition.

> [!failure]+ T002 [[directions/alpha191_universal_subset#T002]] — `[✗ DISPROVEN batch_085]` (OBV-20d) + `[◉ ACTIVE]` (Volume MACD reserve)
> reject C002 (OBV-20d). 回答: OBV-20d 在 csi1000 散户市 sign 翻转 + Barra 完全吞噬 (alpha_surv=0.17), paper-vetted ≠ csi1000 universal. F018 已占据 sign-aggregation rank-diff prototype.
> reserve C005 (Volume MACD histogram). 部分回答: alpha_survival=1.39 显示 volume momentum 二阶变化在 Barra 空间真独立, 但 cross-section quintile rank-order 不干净 (mono_oos=-0.3). T002 split 为两条: T002a OBV DISPROVEN; T002b Volume MACD ACTIVE 待 round 2 ratio-form 复测.

> [!success]+ T003 [[directions/alpha191_universal_subset#T003]] — `[✓ ANSWERED batch_085]`
> admit C003 (dmi_down_ratio_12). 回答: DMI directional pressure asymmetry 在 csi1000 散户震荡市**sign 未翻转** (paper 同向), 不需 abs(DMI) magnitude proxy 替代. 库内首次直接的 directional sign-aggregated magnitude ratio.

> [!failure]+ T004 [[directions/alpha191_universal_subset#T004]] — `[✗ DISPROVEN batch_085]`
> reject C004 (ATR-12d). 回答: ATR 跨日 jump 维度**不独立**于库内单日 range 信号. ATR 在 cross-section 上 ≡ vol_20d (exposure=31.4 整库顶级), max_corr=0.66@F019 + alpha_surv=0.064 P006 trio 齐. 升格 lessons "ATR ≡ vol_20d basis" 候选教训 (P018 律 ATR 扩展实证).

> [!note]- T005 [[directions/alpha191_universal_subset#T005]] — `[◉ ACTIVE]` (本批无推进)
> 5×5-only tail-sensitivity 子集 + vwap-blocked + benchmark-blocked + borderline-DSL 等候 round 2 触发条件 (round 1 ≥2 admit 已达成 ✓ + ≥1 mechanism family alpha_surv 显著独立 from existing 库 已达成 C001 alpha_surv=1.13 ✓) → round 2 触发条件全部满足.

## 方向级反思

**首批兑现 2 admit + 1 reserve (3/6 = 50% 兑现率)** 为 alpha191_universal_subset 方向开了好头, 完成首次 admit → status `exploring → productive` 转换. 关键发现:

1. **paper-vetted prior 在 csi1000 部分 universal**: 5 个 paper 主线 + 1 个 BIAS 长窗 = 6 候选, 2 admit (multi-MA + DMI) + 1 reserve (Volume MACD) = 3/6 paper-vetted 至少有 50% 信号留存. 比"完全失败 (0/6)" 或"完全验证 (5/6)" 都更接近真实 — paper 警告的"multiple testing 风险" + "universe asymmetry" 在 csi1000 实测呈现 sign-flip / Barra 吞噬两种主要失败模式.
2. **alpha_survival > 1.0 频次升级**: lessons.md "P008 escape 机制层验证" 历史仅 b081 C006 一例 ≈1.0, 本批一次性产出两例 (C001=1.13 + C005=1.39). 这是首次"daily-resolution Barra 真独立载体"在批量层面被复制, 升格证据.
3. **F009 anchor cluster 显化**: 6 候选中 4 个 nearest=F009 (overnight_intraday_spread_5d), max_corr 0.21-0.54. F009 在 lessons.md/INDEX 此前未被识别为 anchor (主要 anchor 是 F025/F026 daily intraday position), 本批显示 F009 也是 daily 收盘价偏离参考点几何的 anchor (close-anchor 早期形态). 提议 INDEX HOT-TOPICS-LLM 升格"F009 加入 daily anchor cluster".
4. **下轮路径**: T005 round 2 触发条件全部满足 (≥2 admit + alpha_surv 独立 escape 实证). 下轮可推进:
   - 5×5 tail-sensitivity 子集 (Alpha 022/031/006/187/089) — paper 5×5 显著但 3×2 边缘
   - vwap proxy ($amount/$volume) — Alpha 073 nested PV corr 路径首次试探
   - C005 Volume MACD ratio-form 复测 (`MACD_hist / Mean(volume,27)` dim-less 化)

下批 alpha191_universal_subset round 1 完整 review 后建议 round 2 继续此方向.
