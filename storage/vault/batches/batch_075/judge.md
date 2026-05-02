---
batch_id: batch_075
direction: cov_microstructure_valuation
judged_at: 2026-05-02T05:45:00Z
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
calibration_diagnosis:
  potential_over_rejection: false
  reason: "C001/C002/C003/C004 hard_gate 全 PASS 但 alpha_surv 0.06-0.30 全部 << 0.40 default min — 整批信号方向真实 (ic_by_year 9 年同号 NEG, mono OOS -0.4 至 -0.9, ls_t -2.0 至 -2.8) 但 alpha 70-95% 被 vol_20d basis 吸收。dom=vol_20d 全部立, exposure 5.34-22.06。max_corr 全部 < 0.40 库空间独立但 alpha 不独立 — Cov 形态在 csi1000 daily 上重蹈 b068-b072 fundamental absorption 同一陷阱。C005 hard_gate sign_flip + ic_oos<0.008 (TTM sparse 长窗口塌缩, lessons L 段律扩展)。C006 hard_gate ic_oos<0.008 但唯一 risk-clean (alpha_surv=1.94 火种, dividend_yield × institutional flow 在 Cov 上不撞 ep_ratio basis), 但绝对强度不足 reserve。所有 reject 都是 ≥1 hard_gate 或 alpha_surv 阈值生效, 无错杀候选。"
---

# batch_075 Judge Summary

> [!fail]+ batch_075 · [[directions/cov_microstructure_valuation]] · 6 candidates (new_direction 首批)
> ❌ **admit=0** · ⏸ reserve=0 · ❌ **reject=6** — 首批反向证伪
> **核心发现**: **Cov(microstructure_LHS, valuation_RHS, 60-120d) 几何独立 (max_corr<0.40 to library) 但 alpha 真饱和** — 4 个 hard_gate-pass 候选 (C001-C004) 全部 alpha_surv 0.06-0.30 << 0.40 default min, dominant_style=vol_20d 全部立 (exposure 5.34-22.06), Barra basis 吸收 70-95% alpha. **P018 升格候选**: "Cov(.,.,N) 时间序列协动形态在 csi1000 daily 上仍走 vol_20d basis" — 形态独立性 ≠ alpha 独立性, 与 b068-b072 fundamental absorption 同源 (lessons "csi1000 daily fundamental + institutional flow 真饱和"). C005 (TTM RHS + 120d) hard_gate sign_flip — lessons L 段 "TTM × TTM DSL 不容错" 律扩展至 Cov(daily, TTM_sparse, long_window) 形式. C006 唯一 risk-clean 火种 (alpha_surv=1.94) 但绝对 ic 不足 — dividend_yield × num_trades 在 Cov 上不撞 ep_ratio basis 但 forward alpha 弱.
> **MT Budget**: cumulative 408→414 · direction 0→6 (new direction) · bucket `medium`
> **direction 状态变更建议**: probing → **dead** (首批反向证伪 6/6 reject + 失败机制非"窗口/算子细节"而是"Cov 形态在 daily 频率被 vol_20d basis 系统吸收"; lessons.md "首批反向证伪 → 当批 dead" 律 + "alpha 真饱和不是阈值过严" 律双立).

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | aligned·medium·**poor**·low·stable | ic_oos=-0.018 ls_t=-2.75 mono OOS=-0.90 alpha_surv=**0.295 FAIL** sty_r²=0.085 vol_20d_exp=7.85 max_corr=0.27@F017 incr=-0.005 | Cov(turnover, PE, 60) — mono 强 + ic_by_year 9 年同号但 alpha 70% 被 Barra 吸收。Cov 形态独立 atom 但 alpha 仍走 vol_20d basis — "几何独立 ≠ alpha 独立" 首次 Cov 实证 | [[batches/batch_075/candidates/C001]] |
| C002 | ❌ reject | aligned·medium·**poor**·low·**unstable** | ic_oos=-0.018 ls_t=-2.00 mono OOS=**-0.40** weak alpha_surv=**0.240 FAIL** sty_r²=0.049 vol_20d_exp=5.34 ep_ratio_exp=**2.99** max_corr=0.22@F017 incr=-0.005 | Cov(turnover, PCF, 60) — RHS PE→PCF 不脱 vol_20d, 反而引入 ep_ratio basis 强吸收 (2.99 vs C001 1.04). mono 弱化半 | [[batches/batch_075/candidates/C002]] |
| C003 | ❌ reject | misaligned·medium·**poor**·low·stable | ic_oos=-0.017 ls_t=-2.69 mono OOS=-0.70 alpha_surv=**0.152 deep FAIL** sty_r²=0.050 vol_20d_exp=**11.21** max_corr=0.20@F023 incr=-0.004 | Cov(num_trades, PE, 60) — LHS turnover→num_trades **强化 vol_20d 吸收** (5.34→11.21 +110%). num_trades × size 共线 (lessons P008), Cov 长窗口放大 | [[batches/batch_075/candidates/C003]] |
| C004 | ❌ reject | misaligned·strong·**poor**·**borderline**·stable | ic_oos=-0.038 ls_t=-2.82 mono OOS=-0.90 alpha_surv=**0.065 整批最低** sty_r²=**0.258 borderline poor** vol_20d_exp=**22.06 整批最高** max_corr=0.37@F023 incr=-0.009 | Cov(num_trades, PB, 60) — **整批最强 vol_20d 嵌入实证**. PB 是 Barra book_to_price 直接对应字段, num_trades × PB Cov 是 size × book_yield × vol_20d 三重 basis 重组合 | [[batches/batch_075/candidates/C004]] |
| C005 | ❌ reject | **hard_gate**·n/a·n/a·n/a·n/a | hard_gate FAIL: sign_flip (IS+0.0006/val-0.0012) + ic_oos_too_low (\|0.0012\|<0.008). coverage=0.90 (TTM sparse 影响) | Cov(amount, PCF_TTM, 120) — 长窗口 + TTM sparse RHS 信号塌缩。lessons L 段 "TTM DSL 不容错" 律扩展至 Cov(daily, TTM, long_window) | [[batches/batch_075/candidates/C005]] |
| C006 | ❌ reject | **hard_gate**·**weak**·**clean**·**borderline**·stable | hard_gate FAIL: ic_oos_too_low (\|0.0015\|<0.008). IS ic=+0.005/ls_t=+3.30 borderline alive. **alpha_surv=1.943 整批最强** + sty_r²=0.034 干净。max_corr=0.287 borderline | Cov(num_trades, dividend_yield_TTM, 60) — 整批唯一 **risk-clean 火种** 但 ic 不足 admission. dividend_yield_TTM × institutional flow 在 Cov 上不撞 ep_ratio basis (与 C002 PCF ep=2.99 对照 dividend_yield ep=干净). 长 horizon 单调加强 (h=20 ic=+0.012) 暗示 fwd-period 探索路径 | [[batches/batch_075/candidates/C006]] |

**档位编码**：🟢 最优档（aligned/strong/good/low/stable）· 🟡 次档（mixed/borderline/acceptable/medium）· 🟠 边际 · 🔴 阻断档（misaligned/weak/poor/high/unstable）· `hard_gate` reject 该列写 `hard_gate` 不填色.

## 跨候选对比 — Cov(microstructure, valuation) absorption 矩阵

| LHS | RHS | window | ic_oos | mono OOS | alpha_surv | vol_20d_exp | dom_style | Verdict |
|---|---|---|---|---|---|---|---|---|
| $turnover_rate | $pe_ratio | 60d | -0.018 | -0.90 | 0.295 | 7.85 | vol_20d | reject (alpha_surv) |
| $turnover_rate | $pcf_ratio | 60d | -0.018 | -0.40 | 0.240 | 5.34 | vol_20d | reject (alpha_surv) |
| $num_trades | $pe_ratio | 60d | -0.017 | -0.70 | 0.152 | 11.21 | vol_20d | reject (alpha_surv deep) |
| $num_trades | $pb_ratio | 60d | -0.038 | -0.90 | **0.065** | **22.06** | vol_20d | reject (alpha_surv 整批最低 + style_r² 0.258 borderline poor) |
| $amount | $pcf_ratio_total_ttm | 120d | -0.001 | +0.10 | n/a | n/a | n/a | reject (hard_gate sign_flip + ic_oos) |
| $num_trades | $dividend_yield_ttm | 60d | +0.0015 | +0.30 | **1.943** | 11.77 | vol_20d 但 alpha_surv >1 | reject (hard_gate ic_oos<0.008) |

**横向规律**:
1. **LHS turnover→num_trades 切换**: vol_20d_exp 5.34/7.85 → 11.21/22.06 翻倍, alpha_surv 0.24/0.30 → 0.07/0.15 半. **num_trades LHS 强化 vol_20d 吸收**, 与 lessons P008 raw $num_trades CsRank max_corr=0.75@F012 size 共线性同源.
2. **RHS valuation 替换 PE/PCF/PB**: alpha_surv 全部 < 0.30, ep_ratio basis (PE/PCF) 与 book_to_price basis (PB) 都是 Barra 直接 style 字段, Cov 不消除此共线.
3. **dividend_yield_TTM 例外** (C006): alpha_surv=1.94 risk-clean 火种 — dividend_yield 在 Cov 上不撞 ep_ratio/b_to_p basis, 但 forward ic 弱 (0.0015) 不达 admission.
4. **TTM long-window 路径 (C005)**: 信号塌缩 (NaN sparse + Cov 不容错), 不可走 DSL.

## 失败机制确诊 — Cov 形态系统性 vol_20d 吸收

**机制 (P018 升格候选)**: 
- **Cov(daily_field_LHS, daily_field_RHS, N)** = `Mean((LHS - Mean(LHS,N)) × (RHS - Mean(RHS,N)), N)` 是两序列在窗口内**协动方向 + 波动联合幅度** 的乘积. 在 csi1000 daily 上:
  - `(LHS - Mean(LHS,N))` 项是去均值后的偏差, 与 vol_20d (横截面波动率) 强正相关 (高 vol 股票偏差大);
  - `(RHS - Mean(RHS,N))` 项同理, 但 RHS 是 valuation level (PE/PB/PCF), 也带 vol_20d 共线 (高 vol 股票估值波动大);
  - 两者乘积 + Mean(N) 累积 = **横截面层面被 vol_20d² 因子主导**.
- 即便 Cov 形态在算子层面与已 admit 24 因子完全不同 (max_corr<0.40), 在 alpha basis 层面**与 b068-b072 fundamental TTM × daily-aggregate 同质** — 都是 Barra style basis 重新组合.

**与 b068-b072 fundamental absorption 同源证据**:
- b068 C005 (ROIC × avg_trade_size) vol_20d_exp=31.1 整库历史最高 → 本批 C004 vol_20d_exp=22.06 二次复现
- b069/b070 PIT valuation rank composite alpha_surv 0.5-0.9 但 OOS sign-stable failure → 本批 alpha_surv 0.06-0.30 + sign-stable PASS (但太弱)
- b071 Python OLS residualize 不破 vol_20d 非线性吸收 → Cov 长窗口形态同样不破
- b072 raw $num_trades CsRank max_corr=0.75@F012 size 共线 → 本批 C003/C004 num_trades LHS Cov 仍带 size 共线

**结论**: **csi1000 daily 频率上, microstructure (turnover/num_trades/amount) × valuation (PE/PB/PCF/dividend_yield_TTM) 跨 cross-section level / Mean / Std / TsRank / Cov 5+ 形态全部走 vol_20d basis** — 这不是单形态阈值过严, 是 daily 频率下 microstructure 与 valuation 的 alpha 通道被 Barra style model 完全吃掉. 唯一未探路径与 b072 一致: minute/tick 数据 + 其它 universe (csi300/csi500).

## Thread 进展

> [!fail]+ T001 [[directions/cov_microstructure_valuation#T001]] — `[✗ DISPROVEN batch_075 C001/C002]`
> **Question**: $turnover_rate × valuation_level (PE/PCF) 60d Cov 是否携带独立 forward alpha?
> **Answer**: 否. C001 alpha_surv=0.295 + C002 alpha_surv=0.240 双 FAIL < 0.40 默认阈值, dominant_style=vol_20d. RHS PE→PCF 替换不脱 vol_20d 反而引入 ep_ratio basis (2.99 vs 1.04 三倍). 信号方向真实 (mono OOS -0.40 至 -0.90, ic_by_year 9 年同号 NEG) 但 alpha 70-76% 被 Barra basis 吸收.

> [!fail]+ T002 [[directions/cov_microstructure_valuation#T002]] — `[✗ DISPROVEN batch_075 C003/C004/C006]`
> **Question**: $num_trades (institutional flow proxy) × valuation 60d Cov 是否独立于 F012 + 不撞 size 共线?
> **Answer**: 否, 但 C006 dividend_yield_TTM 是唯一例外火种. C003 alpha_surv=0.152 + C004 alpha_surv=0.065 整批最低 双 deep FAIL. **LHS turnover→num_trades 强化 vol_20d 吸收** (5.34/7.85→11.21/22.06 翻倍, 与 lessons P008 raw $num_trades size 共线律一致). C004 PB RHS vol_20d_exp=22.06 整批最高 (PB 是 Barra book_to_price 直接对应). C006 alpha_surv=1.94 risk-clean 但 ic_oos=0.0015 hard_gate fail — 升格 lessons.md.

> [!fail]+ T003 [[directions/cov_microstructure_valuation#T003]] — `[✗ DISPROVEN batch_075 C005]`
> **Question**: 长窗口 120d Cov + TTM RHS (sparse) 是否在容忍 NaN 后仍提供 alpha?
> **Answer**: 否. C005 hard_gate sign_flip (IS+0.0006/val-0.0012) + ic_oos_too_low (|0.0012|<0.008). 长窗口 + TTM sparse RHS + Cov 不容错 NaN → 信号塌缩 (coverage 0.90 vs 同批 ≥0.999). lessons L 段 "TTM × TTM DSL 不容错" 律扩展至 Cov(daily, TTM, long_window) 形式.

## next_hint 与 direction 状态变更

**direction cov_microstructure_valuation 首批反向证伪**:
- (1) reject_rate 100% (6/6); 
- (2) ≥2 候选独立命中 alpha_surv FAIL (C001-C004) + ≥2 候选 hard_gate FAIL (C005/C006);
- (3) 失败机制非"窗口/算子细节"而是"Cov 形态在 csi1000 daily 上系统被 vol_20d basis 吸收" (与 b068-b072 fundamental absorption 同源);
- (4) 方向尚无任何 admit (新方向首批) → **dead, priority 降到 low**, lessons.md "首批反向证伪 → 当批 dead" 律生效.

**唯一火种保留**: C006 (Cov(num_trades, dividend_yield_TTM, 60)) alpha_surv=1.94 risk-clean 但 forward ic 弱. 不入 reserve (hard_gate fail + 长 horizon 探索属未来 thread, 不在当前 direction 续探). 升格至 lessons.md Path Selection: "dividend_yield_TTM × institutional flow Cov 是 risk-clean 火种, 但 daily 1d primary 不达 alpha 阈值; 探索路径需 forward horizon 调整 + Python ffill rescue".

**next_hint**: 切换全新 direction. cov_microstructure_valuation dead. **csi1000 daily 频率上 microstructure × valuation 5 形态全 absorption 实证**, 不再分配预算到此方向族. 转向 OHLC microstructure / intraday signals 未饱和族, 或尝试: (a) Mul(microstructure_admit, OHLC_atom) cross-product (不带 valuation RHS); (b) Python higher-order 残差 (cross-section ffill + Cov 后 OLS residualize on size+vol_20d, 但 lessons P 段 "Linear OLS 不破 vol_20d 非线性吸收" 警示).

**升格候选 P018**: "Cov(.,.,N) 时间序列协动形态在 csi1000 daily 上仍走 vol_20d basis" — 几何独立 ≠ alpha 独立. 与 b068-b072 absorption 同源, 5+ 形态独立证伪 csi1000 daily microstructure × valuation 真饱和.
