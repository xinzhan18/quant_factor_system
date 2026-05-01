---
batch_id: batch_068
direction: fundamental_quality_carry
judged_at: 2026-05-02T01:30:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 0, reserve: 0, reject: 6}
admit_count: 0
reject_count: 6
reserve_count: 0
candidate_count: 6
mt_bucket: medium
---

# batch_068 Judge Summary

> [!abstract]+ batch_068 · [[directions/fundamental_quality_carry]] · 6 candidates (NEW direction)
> ✅ **admit=0** · ⏸ **reserve=0** · ❌ **reject=6**
> **核心发现**: T001-T004 四 thread NEW direction born-near-disproven —— **TTM quality / institutional-flow-proxy / GARP / Sloan accruals 在 csi1000 daily-bar 上撞同一道 vol_20d 吸收墙**. 5/6 PASS hard_gate 候选全部 `dominant_style=vol_20d` + `style_r²>0.30` + `alpha_survival<0.30` 三立 (C001 borderline, C002/C005/C006 三立完整, C004 hg_fail). Mean(amount,20) / Mean(turnover_rate,20) 这两个 daily-aggregate liquidity proxy 本身 cross-section 嵌入 vol_20d, ratio 形式 (`Div(quality, liquidity)`) 不仅没绕开 vol_20d, 反而把 TTM quality 拉进 vol_20d basis. C002 单独 avg_trade_size 也是 vol_20d-locked. **第 9+ direction 复现 P004 vol_20d 结构性吸收律**, 首次在 fundamental TTM 字段族上.
> **MT Budget**: cumulative 366 → 372 · direction 0 → 6 · bucket `medium` (新方向 direction 项=0 拉低 score)

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | aligned·borderline·**poor**·medium(F002)·**unstable** | ic_oos=+0.027 ls_t=+1.83 mono=+0.7 alpha_surv=0.30 sty_r²=0.40 vol_20d_exp=**23.4** max_corr=0.47@F002 incr=+0.0057 | ROE/Mean(amount,20) 同 F002 (PB/amount) 套路, ic 健康但 vol_20d_exp=23.4 整库顶级 — Mean($amount,20) 本身就 vol_20d-locked, 把 ROE 拉进 vol_20d basis. asr=0.30 borderline + ls_t=1.83<2 + incr<0.008 floor 三立, 标准 vol_20d 吸收 + library reducer | [[batches/batch_068/candidates/C001]] |
| C002 | ❌ reject | aligned·strong·**poor**·medium(F012)·stable | ic_oos=-0.076 ls_t=-6.19 mono=-1.00 PERFECT alpha_surv=**0.13** sty_r²=0.40 max_corr=0.42@F012 incr=-0.008 | avg_trade_size = $amount/$num_trades, 看似机构 flow proxy 几何独立, 但 cross-section 上 \"高 amount/低 num_trades\" 同样指向高 vol stocks (机构集中 = 高 vol). asr=0.13 catastrophic + dom=vol_20d r²=0.40 三立完整. 强 PnL 但 alpha 不脱 vol_20d basis + max_corr=0.42@F012 dead zone + incr=-0.008 NEG library reducer | [[batches/batch_068/candidates/C002]] |
| C003 | ❌ reject | hard_gate | compute_error: preprocessed factor empty (all NaN) | Sub($eps_ttm, $operating_cash_flow_per_share_ttm) 全 NaN — 两 TTM 字段 scale 不同 (eps in CNY/share vs ocf in CNY/share 数值范围接近但 ref_financials TTM 同步可能在 csi1000 上有大量空 + 减法放大 NaN 比例). Sloan accruals proxy DSL 直接版本不可行, 需 Python rank 化或 cross-section z-score 后再做 Sub | [[batches/batch_068/candidates/C003]] |
| C004 | ❌ reject | hard_gate | sign_flip + ic_oos\|0.0040\|<0.008 + decay -2.145 catastrophic | growth × (1/pe) GARP, train ic=+0.0019 / val ic=-0.004 sign 翻号 + magnitude 不达 floor + decay 负值. growth_ttm 与 1/pe regime 切换敏感 (2015-2021 成长占优 → 2022-2023 价值回归). 经典 P003 fundamental signed 因子 regime drift | [[batches/batch_068/candidates/C004]] |
| C005 | ❌ reject | aligned·borderline·**poor**·medium(F017)·**unstable** | ic_oos=+0.038 ls_t=+2.50 mono=+0.9 alpha_surv=**0.12** sty_r²=0.31 vol_20d_exp=**31.1** max_corr=0.57@F017 incr=-0.005 | gross_margin/Mean(turnover,20), ic 看着最强 + mono=0.9, 但 vol_20d_exp=**31.1 整库历史最高** — 同 C001 机理 (Mean(turnover,20) 是 daily-aggregate liquidity, cross-section 嵌入 vol_20d). asr=0.12 三立完整 + incr=-0.005 library reducer. 比 C001 vol_20d 吸收更深 (margin 比 ROE 更窄 cross-section 分布) | [[batches/batch_068/candidates/C005]] |
| C006 | ❌ reject | aligned·strong·**poor**·low(F019)·stable | ic_oos=-0.029 ls_t=-3.58 mono=-0.9 alpha_surv=**0.16** sty_r²=0.42 max_corr=0.28@F019 incr=-0.0001 | ROIC × avg_trade_size, mono 强 + ls_t 强 + max_corr=0.28 几何独立, 但 alpha_surv=0.16 catastrophic + sty_r²=0.42 + incr 几乎为零. ROIC 与 C002 avg_trade_size 乘积**叠加 vol_20d 嵌入** (ROIC 与 size 弱负相关 + avg_trade_size 与 vol 强相关 → 合成跨 size+vol 双吸收) | [[batches/batch_068/candidates/C006]] |

**档位编码**：🟢 最优档（aligned/strong/good/low/stable）· 🟡 次档（mixed/borderline/acceptable/medium）· 🟠 边际 · 🔴 阻断档（misaligned/weak/poor/high/unstable）· `hard_gate` reject 该列写 `hard_gate` 不填色.

## 跨候选对比

**Style 聚合**：5/5 PASS hard_gate 候选**全部** `dominant_style_exposure = vol_20d`. style_exposures.vol_20d 系数对比 (本批最大值是整库顶级):
- C005 gross_margin / Mean(turnover_rate,20): vol_20d=**31.10** ⚠️ 整库历史最高
- C001 ROE / Mean(amount,20): vol_20d=**23.42** ⚠️ 整库顶级 (与 C005 同机理)
- C002 $amount/$num_trades: vol_20d=9.75
- C006 ROIC × $amount/$num_trades: vol_20d=8.50
- C004 hg_fail; C003 compute_error

**P004 vol_20d structural absorption 第 9+ direction 跨族复现 (首在 fundamental TTM 字段族)**: 几何不变性显著 — daily-aggregate liquidity (Mean($amount,20) / Mean($turnover_rate,20)) **本身 cross-section 嵌入 vol_20d**, ratio 形式 (Div TTM_quality / liquidity) 不仅没绕开, 反而把 TTM quality (本应几何独立) 拉进 vol_20d basis. 这是个**反直觉发现**: 假设 fundamental TTM 与 OHLCV 几何独立 (lessons "新方向提示"), 实际是 daily-aggregate denominator 把 numerator 拉进 vol_20d basis.

**避开 vol_20d 拉拽的两条路径** (本批已识别但未测试):
1. **TTM quality LEVEL 单独** (不与 daily liquidity 做 ratio): 但单独 TTM ratio 受 size 共线性吞噬 (lessons 25 行 |corr|>0.3 to $market_cap 红线). 唯一出路是 Python OLS residualize on size.
2. **TTM quality × TTM liquidity** (e.g. ROE × inventory_turnover_ttm): 两边都 TTM, 不引入 daily vol. 但 inventory_turnover_ttm 是会计意义的 turnover 不是市场意义, mechanism 不对应"机构 flow"假设.

**P006 library-reducer trap**: C001/C005 incr_ic 接近 zero 或负值 (+0.0057 / -0.0049 / -0.0001). 三 PASS-hg 候选 incr_ic 都不达 0.008 floor — 当然在 vol_20d 吸收前提下 incremental 价值是空话.

**Sub 直接版本 NaN 陷阱**: C003 `Sub($eps_ttm, $operating_cash_flow_per_share_ttm)` 全 NaN. 两个 TTM per-share 字段 sparsity (报表期外 NaN) + Sub 不容错 (任一边 NaN → 结果 NaN) 复合致 preprocessed empty. **升格 lessons 候选**: TTM × TTM 直接 Sub/Mul/Div 在 ref_financials sparse 字段上需 ffill 或 cross-section z-score 包装, 不能裸用 (规避 b068 C003 retread).

**MT 预算推进**: cumulative 366→372; direction 0→6; bucket `medium` (新方向 direction 项=0 强力拉低 family 项).

## Thread 进展

> [!failure]+ T001 [[directions/fundamental_quality_carry#T001]] — `[✗ DISPROVEN batch_068]` (NEW thread, born-disproven)
> **Question**: TTM quality LEVEL × daily liquidity ratio (同 F002 套路) 是否在 csi1000 cross-section 提供超出 size + value Barra style 的增量 IC?
>
> **Answer**: **本形式证伪**. C001 (ROE/Mean(amount,20)) + C005 (gross_margin/Mean(turnover,20)) 两候选 ic=+0.027/+0.038 看健康但 vol_20d_exp=23.4/31.1 整库顶级, asr=0.30/0.12 三立, incr_ic 不达 floor. **机理**: daily-aggregate liquidity denominator 本身 cross-section 嵌入 vol_20d, ratio 形式把 TTM quality 拉进 vol_20d basis. F002 (PB/amount) 之所以 admit, 是 PB 本身已是 cross-section 主成分 (value Barra basis), 与 vol_20d 抗衡, ROE/margin 没有同等 Barra basis 抗衡能力.
>
> **Evidence trail**:
> - [[batches/batch_068/candidates/C001|batch_068 C001]] ROE/Mean(amount,20) → ic=+0.027 vol_20d_exp=23.4 asr=0.30 incr=+0.0057 → reject
> - [[batches/batch_068/candidates/C005|batch_068 C005]] gross_margin/Mean(turnover,20) → ic=+0.038 vol_20d_exp=31.1 asr=0.12 incr=-0.0049 → reject
>
> **复活路径**: (a) Python OLS residualize TTM_quality on (size, vol_20d, value) 后再做 ratio; (b) TTM × TTM (避开 daily liquidity); (c) 等 F002 anchor 退役.

> [!failure]+ T002 [[directions/fundamental_quality_carry#T002]] — `[✗ DISPROVEN batch_068]` (NEW thread, born-disproven)
> **Question**: $amount / $num_trades = avg_trade_size 作为机构占比代理, cross-section level 是否携带独立 forward IC?
>
> **Answer**: **DSL 直接版本证伪**. C002 单独 avg_trade_size: ic=-0.076 强 + mono=-1.00 perfect, 但 alpha_surv=0.13 catastrophic + dom=vol_20d r²=0.40. 机理: 高 avg_trade_size = 单笔大额成交集中 = 机构集中 = **同时**指向高 vol stocks (机构关注的高波动股). C006 ROIC × avg_trade_size 也 alpha_surv=0.16 + sty_r²=0.42 共证. 单独 avg_trade_size 与 quality 交互不能脱 vol_20d basis.
>
> **Evidence trail**:
> - [[batches/batch_068/candidates/C002|batch_068 C002]] $amount/$num_trades level → ic=-0.076 ls_t=-6.19 mono=-1.0 vol_20d_exp=9.75 asr=0.13 → reject (vol_20d 三立)
> - [[batches/batch_068/candidates/C006|batch_068 C006]] ROIC × avg_trade_size → ic=-0.029 ls_t=-3.58 mono=-0.9 vol_20d_exp=8.50 asr=0.16 → reject (vol_20d 三立 + library reducer)
>
> **复活路径**: (a) avg_trade_size 跨 universe 替换 ($num_trades 在 csi300 vs csi1000 cross-section 形态可能不同, 需独立 universe robustness); (b) Python residualize on vol; (c) intraday avg_trade_size (需 minute-bar).

> [!failure]+ T003 [[directions/fundamental_quality_carry#T003]] — `[✗ DISPROVEN batch_068]` (NEW thread, born-disproven, 数据契约层失败)
> **Question**: $eps_ttm - $operating_cash_flow_per_share_ttm 作为应计盈余近似 (Sloan accruals proxy), cross-section level 是否携带反向 forward IC?
>
> **Answer**: **DSL 直接 Sub 不可行**. C003 compute_error: preprocessed factor empty (all NaN). 两个 ref_financials TTM per-share 字段 sparse (报表期外 NaN) + Sub 不容错 → 全样本 NaN. 信号设计未到 Phase 3 6CP 评估.
>
> **Evidence trail**:
> - [[batches/batch_068/candidates/C003|batch_068 C003]] Sub(eps, ocf) → compute_error all NaN → hg fail
>
> **复活路径**: 必走 Python: (a) 先 cross-section ffill TTM 字段; (b) cross-section z-score 后再 Sub; (c) 直接计算 Python `(eps - ocf) / |eps + ocf|` 标准化形式. 不复活 DSL 直接版本.

> [!failure]+ T004 [[directions/fundamental_quality_carry#T004]] — `[✗ DISPROVEN batch_068]` (NEW thread, born-disproven, regime drift)
> **Question**: $net_profit_growth_ratio_ttm × Div(1, $pe_ratio) GARP level 是否优于单 PEG?
>
> **Answer**: **regime drift 否决**. C004 train ic=+0.0019 / val ic=-0.004 sign 翻号 + magnitude 不达 floor + decay -2.145 catastrophic. growth × (1/pe) 对 2015-2021 成长占优 → 2022-2023 价值回归 regime 切换敏感 — 经典 P003 fundamental signed signal regime drift.
>
> **Evidence trail**:
> - [[batches/batch_068/candidates/C004|batch_068 C004]] growth × 1/pe → train +0.0019 vs val -0.004 sign_flip + ic_too_low + decay neg → reject (hard_gate)
>
> **复活路径**: (a) 单独 1/pe (value carry, 但 fundamental_momentum b022 已证 PE rate 失败, level 需独立测); (b) 单独 growth_ttm + cross-section rank (不依赖乘积 + regime-stable rank).

## 方向级反思

**核心律 (本方向 born-near-disproven)**: 6 候选覆盖 4 子机制全部失败:
- T001 quality × daily liquidity → vol_20d 吸收 (反直觉, daily-aggregate liquidity denominator 把 TTM quality 拉进 vol_20d)
- T002 institutional flow proxy → vol_20d 吸收 (机构资金集中 = 高 vol 双重指向)
- T003 Sloan accruals → 数据契约失败 (DSL Sub 不可行)
- T004 GARP → regime drift (signed fundamental 翻号)

**与 cockpit 假设的对比** (cockpit 推荐这四方向):
- ✅ TTM quality 与 OHLCV 字段几何上**确实**不同 (字段族独立)
- ❌ 但 cross-section rank 在 csi1000 daily-bar 上**仍被 vol_20d 吸收**, 通过 daily-aggregate liquidity denominator 这条隐藏路径
- 升级 cockpit 提示: "TTM quality × daily liquidity ratio 默认会被 vol_20d 拉拽, 不算独立 frontier"

**升格 lessons 候选** (本方向贡献 3 条, 待 Phase 5 consolidate 决议):
1. **TTM-quality / daily-aggregate-liquidity ratio 默认 vol_20d 吸收**: Mean($amount,window) / Mean($turnover_rate,window) 作 denominator 把 numerator (TTM quality) 拉入 vol_20d basis. F002 admit 是 PB Barra value basis 抗衡的特例, ROE/ROA/margin/ROIC 没有同等 Barra basis. 应升格至 lessons.md `Forbidden Patterns`: "Div(TTM_quality_field, daily_aggregate_liquidity)" default-skip.
2. **TTM × TTM 直接 Sub/Mul/Div 在 ref_financials sparse 字段需 Python 包装**: C003 retread 警示, eps/ocf/per_share TTM 字段 sparse + DSL Sub 不容错. 应升格 lessons.md `Path Selection`: "Sub($eps_ttm, $ocf_per_share_ttm) DSL 不可行, 必走 Python ffill/zscore"
3. **Signed fundamental signal regime drift in 2022-2023 转折**: C004 sign 翻号是第 N 次实证. growth × value_reciprocal 类 signed fundamental 因子在 train (2015-2021 成长占优) → val (2022-2023 价值回归) 切换敏感. 这条 lessons 已存在 ("Train→Validation regime 切换" 段), 本批 add 一份 fundamental cross-product 实证.

**zero_admit_streak**: b067=7 → b068=8 (连续 8 批 zero admit) → 系统连续 8 批未 admit, 临近 calibration 触发条件 (本 skill `阈值校准 trigger #2`).

**rounds_since_consolidation**: 8 → 9 (距 10 阈值还有 1 批, 极近触发).

**错杀侦测** (calibration trigger #1 检查):
- C002 max_corr=0.42 (>0.30) — 不属错杀
- C006 max_corr=0.28 (<0.30 ✓) + incr_ic=-0.0001 (<0.010 floor 不合) → 不属错杀
- C001 max_corr=0.47 (>0.30) — 不属错杀
- 无候选满足 "错杀 flag" 完整条件 (max_lib_corr<0.30 + incremental_ic>0.010 + mono>0.8 + sign=1.0 全立). 本批 alpha 真实在 vol_20d 吸收下不足, **不属错杀**.

**Calibration trigger 评估**:
- Trigger #1 (judge.md "potential over-rejection"): 不存在 — 全部 6 reject 都有明确机制理由 (vol_20d 三立 / hg_fail / regime drift)
- Trigger #2 (连续零 admit 警戒): zero_admit_streak=8 + 累计最近 3 批 (b066/b067/b068) admit=0+0+0 = 0 ✓; 但 reserve 候选 (b066 C006 path-eff×ps_rd / b066 C006 b066 C006) 未达"max_lib_corr<0.30 + incremental_ic>0.010"双立 → trigger #2 第二条件**不立** (没有真实被错杀 reserve 火种)
- Trigger #3 (Reserve 积压): 累计 reserve/judged 比例 (近 10 批 reserve=10 / total=60 = 16.7%) — **远低于 40%** → 不立
- Trigger #4 (悖论复现): 不立
- **结论**: calibration_trigger = false. 当前是 alpha 真实饱和 (vol_20d 吸收 + library anchor cluster 双重锁), 不是阈值过严.

**direction status 提议**:
- 现状: exploring(high) · 0 round before · 0 admits
- 本批 6/6 reject (T001-T004 NEW direction born-near-disproven)
- 4 thread 全 DISPROVEN (T001/T002 vol_20d 吸收 / T003 数据契约 / T004 regime drift)
- 信号设计层证据: 4 子机制覆盖完整 ✓
- 数据契约层证据: T003 数据契约失败 ✓
- 双层证据律满足 → 但 NEW direction first-batch dead 律应用 (lessons 8 行 "first-batch dead 律")
- **status 提议: exploring → dead** (first-batch all-reject + 4 thread 全 disproven)
- priority: high → low

**MT Budget 状态**: cumulative 366→372 · direction 0→6 · bucket `medium` (新方向 direction 项=0 拉低 score, 但 cumulative 已逼近 high 阈值)

**下轮建议** (orchestrator 级):
1. **本方向 dead**: 转 dead, 四 thread 全闭. 复活路径: Python OLS residualize TTM quality on (size, vol_20d) 后再 ratio; 或 TTM × TTM 不引入 daily liquidity.
2. **下批方向切换**: zero_admit_streak=8, 距 10 警戒还有 2 批. 当前剩余 productive: ohlc_temporal_aggregation (5 admits, 8 rounds, 2026-04-28 last batch) / overnight_intraday_split (9 admits, 12 rounds, 2026-05-01 last batch). 优先 overnight_intraday_split (rounds 多 admits 多 hot streak), 但需查其最近 b066 reserve 1 候选状态. 严避 saturated direction.
3. **consolidation 极近触发** (rounds_since_consolidation=9, 1 批后达 10 阈值): 升格教训累积 — TTM-quality / daily-liquidity 吸收律 + TTM × TTM Sub DSL 数据契约陷阱 + fundamental cross-product regime drift 三条值得 lessons.md 升格.
4. **新 frontier 调整**: cockpit 在 round=68 提的"TTM × OHLCV ratio 是新 frontier"假设**部分被本批证伪**. 真正新 frontier 应转向: (a) TTM × TTM 内部交互 (e.g. ROE × inventory_turnover_ttm, ROIC × debt_to_asset, growth × margin); (b) Python OLS Barra residualize TTM 单字段 (后接 cross-section ranking); (c) PIT $dividend_yield_ttm 单独 (未测).
