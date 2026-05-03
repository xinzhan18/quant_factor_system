---
batch_id: batch_086
direction: alpha191_universal_subset
judged_at: 2026-05-03T07:30:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reserve}
batch_summary: {total: 6, admit: 0, reserve: 1, reject: 5}
admit_count: 0
reject_count: 5
reserve_count: 1
candidate_count: 6
mt_bucket: high
---

# batch_086 Judge Summary

> [!abstract]+ batch_086 · [[directions/alpha191_universal_subset]] · 6 candidates
> ✅ **admit=0** · ⏸ **reserve=1** (C006 Alpha 022 P008 escape) · ❌ **reject=5** (C001/C002/C003/C004/C005)
> **核心发现**: paper-vetted 5×5 tail-sensitivity Alpha 022/031/006 全部 csi1000 daily 不兑现; vwap-proxy rank-spread Alpha 073 完全失效; Volume MACD ratio-form (T002b) DISPROVEN — dim-less 反而恶化 mono. **alpha_surv > 1.0 三连出现 (C001=1.59, C005=1.59, C006=1.21) 但 incr_ic 全负 (-0.016, -0.023, -0.007)** — Barra 真独立但库空间负增值, 升格 lessons 候选 "P008 形式层 ≠ library 充分条件".
> **MT Budget**: cumulative 474 → **480** · direction 6 → **12** · bucket `high` (search_adjusted=medium)

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | mixed·**weak**·acceptable·**high**·mixed | ic_oos=-0.024 mono=-0.40 alpha_surv=1.59 incr_ic=-0.016 | EMA-12 形式: alpha_surv 顶级独立 但与 F006-F009-F027 整族 -0.44~-0.46 cluster + library reducer | [[batches/batch_086/candidates/C001]] |
| C002 | ❌ reject | hard_gate | corr=0.954@F027 | BIAS-12 单窗 与 F027 multi-MA 几何等价 | [[batches/batch_086/candidates/C002]] |
| C003 | ❌ reject | hard_gate | ic_oos=0.0053<0.008 + sign-mono mismatch | weighted-price Δ4 sign rank: csi1000 daily 信号过弱 + sign 翻转 | [[batches/batch_086/candidates/C003]] |
| C004 | ❌ reject | hard_gate | sign_flip + ic≈0 + decay=-1.05 | vwap-proxy rank-spread 完全失效, paper Alpha 073 nested decayed Corr DSL 不可达 | [[batches/batch_086/candidates/C004]] |
| C005 | ❌ reject | mixed·**weak**·acceptable·**high**·mixed | ic_oos=-0.024 mono=-0.10 alpha_surv=1.59 incr_ic=-0.023 | Volume MACD ratio-form: dim-less 反而恶化 mono (-0.30→-0.10), incr_ic 本批最负 | [[batches/batch_086/candidates/C005]] |
| C006 | ⏸ reserve | mixed·borderline·acceptable·**high**·stable | ic_oos=-0.024 mono=-0.70 alpha_surv=1.21 incr_ic=-0.007 | Alpha 022 P008 escape: vol_20d_exp=8.80 显著低 + decay=1.21 OOS 强于 IS + 8 年稳定, 但 incr_ic 仍微负 | [[batches/batch_086/candidates/C006]] |

**档位编码**: 🟢 最优档 · 🟡 次档 · 🟠 边际 · 🔴 阻断档 (本批无 admit, 不画绿色, 直接用文字).

## 跨候选对比

- **alpha_surv > 1.0 三连**: C001=1.59, C005=1.585, C006=1.21 — 三个 pass 候选**全部**Barra 真独立 (residual_IC > raw_IC), P008 escape 形式层证据本批集中爆发. 但 incr_ic 全部负 (-0.016 / -0.023 / -0.007) → **形式层独立 ≠ 库空间增值**, 升格证据 (n=3 in single batch).
- **mono_oos 退化谱**: C006 -0.70 (好) > C001 -0.40 > C005 -0.10 (退化). dim-less ratio-norm (C005) 反而消除 rank-order — T002b 假设证伪.
- **vol_20d exposure 差异**: C006 8.80 (P008 escape 显著降低) << C001 19.06 ≈ C005 16.65. **P008 TsRank-60 percentile transform 真正 vol-normalized**, EMA-12 / ratio-norm 不能.
- **Cluster 显化**: C001 与 F006/F007/F008/F009/F027 整族 -0.44~-0.46 corr cluster (5 个 admitted 因子). C006 与 F008 -0.444 + F026 +0.31 cluster (TsRank-60 family). 暴露**库内 sign-flipped reversion family + TsRank-60 family 已饱和**.
- **paper 5×5 tail-sensitivity 子集兑现率**: 3 候选 (C001 二阶 BIAS-6 EMA / C002 BIAS-12 单窗 / C003 weighted-price Δ4 sign rank) **全部 reject** (1 reject + 2 hard_gate fail). paper 警告"monthly aggregation 抹平 high-frequency dynamics" + "5×5 tail-sensitivity 在 retail-dominated universe 应更强" 的反向假设**部分证伪**: 5×5 tail 子集在 csi1000 daily **不兑现**, 与 3×2 子集 50% 兑现 (b085) 形成显著对照.
- **MT 预算推进**: direction_candidates 6 → 12 (翻倍); validation_exposure 85 → 91; mt_bucket=high 但 search_adjusted=medium. 本批是 alpha191_universal_subset 第 2 round, 无 admit, MT 预算消耗显著. cumulative 474 → 480 全库.

## Thread 进展

> [!note]+ T002 [[directions/alpha191_universal_subset#T002]] — `[✗ DISPROVEN batch_086]`
> reject C005. **T002b Volume MACD ratio-form 复测 DISPROVEN**: dim-less 化使 mono_oos 从 -0.30 (b085) 退化到 -0.10 几乎无 rank-order, alpha_surv 1.585 顶级独立但 incr_ic=-0.023 本批最强负 library reducer. ratio-norm 反向恶化原始信号. T002 全部 split (T002a OBV ✗ + T002b Volume MACD ratio ✗) DISPROVEN, **整 thread 关闭**.

> [!note]+ T005 [[directions/alpha191_universal_subset#T005]] — `[◉ ACTIVE]`（部分推进）
> reject 4 + reserve 1. round 2 三条续探路径全检验:
> - **path (a) 5×5 tail-sensitivity 子集 (Alpha 022/031/006)**: 全部 reject. C001/C006 是 Alpha 022 两种形式 (EMA-12 vs TsRank-60), C002 是 Alpha 031 BIAS-12 单窗 (与 F027 等价), C003 是 Alpha 006 weighted-price Δ4 sign. 仅 C006 P008 escape 形式获得 reserve.
> - **path (b) vwap proxy via $amount/$volume**: C004 reject (sign_flip + ic≈0 + decay=-1.05). Alpha 073 nested decayed Corr 在 daily DSL 不可达, **vwap-blocked permanently** 升格.
> - **path (c) Volume MACD ratio-form**: T002b 已 DISPROVEN (见上).
> 仅 path (a) 的 P008 escape 路径产生 reserve (C006). 下一步: T005 收窄到 P008 escape 单变量优化 (字段替换 $turnover_rate/$amount/$volume + 窗口 90/120).

> [!note]+ T006 🆕 [[directions/alpha191_universal_subset#T006]] — `[◉ ACTIVE]`
> 新建. 来源: 本批 alpha_surv > 1.0 三连 (C001/C005/C006) + incr_ic 全负观察, 暴露 "P008 escape 形式层独立 (alpha_surv 高) ≠ library 充分条件 (incr_ic 正)" 律. 子问题: csi1000 daily 库内 sign-flipped reversion family + TsRank-60 family 是否已结构性饱和? P008 escape 是否需要 admit 阈值 incr_ic > 0.005 + max_lib_corr < 0.30 双条件? (现有 b082 F026 admit 是 incr_ic 正; b085 F027 admit 是 max_lib_corr 0.544 高但 incr_ic 正且 alpha_surv > 1.0).

## 方向级反思

本方向 round 2 (b086) 兑现率 0/6 admit + 1/6 reserve, **较 round 1 (b085 2/6 + 1/6) 显著下滑**. 主要发现:

1. **paper 5×5 tail-sensitivity 子集在 csi1000 daily 系统失效** (n=3 reject in batch_086). 与 3×2 子集 b085 50% admit (C001 multi-MA + C003 DMI 兑现) 形成 sharp contrast. 教训: paper 把 5×5 子集列为"扩展存活集合"是因为 5×5 增加 sort granularity 但**保留** monthly aggregation, 在 daily 频率信号已被噪声主导, paper 警告"monthly aggregation 抹平 high-frequency dynamics" 在 5×5 子集表现尤强.

2. **alpha_surv > 1.0 不再罕见** — 本批 3/3 pass 候选全部 alpha_surv ≥ 1.21 (b085 仅 C001=1.13 + C005=1.39 两例), P008 escape 形式层在 paper-vetted 候选中**普遍兑现**. 但**incr_ic 全负** (-0.007 ~ -0.023) — 形式层独立 ≠ library 增值, 升格元教训候选.

3. **vwap-proxy rank-spread 路径全失效** (C004): paper Alpha 073 nested decayed Corr 16d 形式在 DSL 简化为 rank-spread 完全丢失原 paper 信号. 后续若仍想测 Alpha 073, 必须走 Python escape hatch 实现 nested decayed correlation, 或放弃.

4. **Volume MACD T002b ratio-form 假设证伪**: dim-less 化预期改善 mono 反而恶化 (-0.30 → -0.10). 原因可能是: Mean(volume, 27) 分母在 cross-section 注入 size 横截面差异 (small-cap 低 mean / large-cap 高 mean), ratio 反而消除了 raw signal 的 rank-order. P016 cap-denominator 风险扩展到 volume_mean denominator (size-vol 联合 basis 注入).

**Edge 评估**: round 1 batch_085 incremental_ic 中位数 ≈ 0.020 (admit C001+C003 都正且 > 0.010); round 2 batch_086 incremental_ic 中位数 ≈ -0.016 (全部负). edge 急剧收窄, 5×5 tail-sensitivity 路径已**结构性饱和**.

**下一步建议**:
- (a) **专一推 P008 escape 单变量优化** (T005 收窄): 用 C006 形式作 baseline, 切换字段族 ($turnover_rate / $amount / $num_trades) 替代 $close 减少与 OHLC reversion family cluster; 同时测 90/120 窗口
- (b) **放弃 paper 5×5 tail-sensitivity 子集剩余 9 个** (Alpha 187/089/052/002/044/011/026/136/170): 全部基于 OHLC + price-only 的 cross-section rank 几何, 与本批 C001/C002/C003 失败模式同源
- (c) **若 round 3 仍 0 admit + 0 reserve**, 升格 `status: productive → saturated`. 当前仍 productive (round 1 admit 2 + round 2 reserve 1), 但 ROI 下降明显.

**Calibration trigger 检查** (本 batch 0 admit + 1 reserve):
- 错杀 flag 跨候选反思: 无 (C001/C005/C006 incr_ic 均负 + max_lib_corr 均 ≥ 0.40 临界, 不满足 over-rejection 4 条件)
- 连续零 admit 警戒: 本批 0 admit, 但前 3 批 (b083 0 + b084 0 + b085 2) 有 admit; 不触发
- Reserve 积压: 不评估 (无系统级数据)
- 悖论复现: alpha_surv>1.0 + incr_ic<0 三连出现 (C001/C005/C006 in batch_086) — 需要追溯 b072/b081/b082 是否同模式. 若历史已有 ≥ 1 次, 触发 calibration

无明确 calibration trigger, 推进 Phase 4 archive.
