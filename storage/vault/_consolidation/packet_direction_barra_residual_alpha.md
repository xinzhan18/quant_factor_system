# Consolidation Packet — directions/barra_residual_alpha.md

## Current content

---
direction_tag: barra_residual_alpha
status: saturated
priority: low
rounds: 6
admits: 1
last_batch: batch_015
last_admits: []
last_goal: 'Round 4 of barra_residual_alpha: change residualization METHOD (not subset)
  per batch_014 finding that vol_20d dominates the 7-style basis. Test 5 alternatives
  — Huber regression, OLS+intraday-vol style, heteroscedastic-aware z-normalization,
  winsorized-input OLS, and vol×turnover interaction style. Goal: produce a residual
  sufficiently distinct from F004 (corr<0.7) while retaining IC>=0.015.'
last_activity: '2026-04-20T17:55:33Z'
created_batch: batch_012
members:
- F004
retired_members:
- F005
merged_into: null
---
# barra_residual_alpha

> [!abstract]+ 方向概要
> **状态**　🟡 saturated · priority=low · rounds=6 · admits=1
> **最近**　[[batches/batch_015/judge|batch_015]] · 2026-04-21 · admit=0 / reserve=0 / reject=5
> **一句话**　F004 是 7-style × OLS-family 残差的几何不变量；basis / 损失函数 / 标准化 / interaction / 时序后处理 5 类路径全部 collapse，框架内已穷尽。

---

## Hypothesis

> [!failure]+ ⚠️ 证伪后的 Hypothesis（2026-04-21 saturated）
> **原始假设**：Regress(Returns ~ 7 Barra styles) 的 residual 携带独立于风格因子的 idiosyncratic alpha。
>
> `Barra residual alpha = Regress(Returns ~ vol_20d + str_1m + turnover_20d + log_circ_cap + book_to_price + mom_12_1 + ep_ratio) → Residuals`
>
> **成立部分**：F004 admit 确认 residual IC=0.033 > raw IC=0.024 的 incremental alpha 存在。
>
> **⚠️ 证伪部分**：在 **7-style basis × OLS-family** 框架内，F004 是几何不变量——≥5 条独立路径（basis 子集调整 / 损失函数切换 / 标准化变换 / interaction style / 时序后处理）全部 collapse 到 corr ≥ 0.91。方向在当前框架内已穷尽。
>
> **复活条件**：
> (a) 加非 Barra style basis（行业 / GICS / microstructure factor model）
> (b) nonparametric residualization（kernel ridge / NN）
> (c) 与库其他因子的非线性 ensemble

---

## Threads

### T001: Barra residual 有效性 [✓ ANSWERED batch_012]

> [!success]+ Thread 结论
> **Question**: Barra residual returns 是否携带独立于风格因子的 alpha？
> **Evidence trail**:
> - [[batches/batch_012/candidates/C001|batch_012 C001]]　IC=0.024 ICIR=0.293 ls_t=7.34 Barra_residual_IC=0.033 > raw IC=0.024 → **admit → [[factors/F004]]**
> - [[batches/batch_012/candidates/C003|batch_012 C003]]　Barra_residual_IC=0.033 但 style_r²=0.289 + vol_20d exposure=15.6 → **reserve**
>
> **Answer**: Barra residual 携带 incremental alpha（residual IC=0.033 > raw IC=0.024），F004 admit 确认假设成立。

### T002: 7-style × OLS 框架内的可分离性 [✗ DISPROVEN batch_015]

> [!failure]+ Thread 结论
> **Question**: 在 7-style Barra basis + OLS 家族内，能否通过调整 basis 子集 / 损失函数 / 标准化 / interaction / 时序后处理产生与 F004 独立（corr<0.7）的残差？
> **Evidence trail**（5 类路径全部证伪）:
>
> **路径 A · basis 子集调整**
> - [[batches/batch_014/candidates/C002|b014 C002]]　vol-20d-keep + 3d EMA → corr=0.987；时序平滑不改 cross-sectional 结构
> - [[batches/batch_014/candidates/C004|b014 C004]]　strip only momentum (str_1m+mom_12_1) → sign_flip + ic_oos_too_low
> - [[batches/batch_014/candidates/C005|b014 C005]]　strip 6 styles, keep log_circ_cap → corr=0.906；size 仅边际贡献
>
> **路径 B · 损失函数**
> - [[batches/batch_015/candidates/C001|b015 C001]]　Huber IRLS residual → corr=0.907；鲁棒损失不动 cross-sectional 几何
> - [[batches/batch_015/candidates/C004|b015 C004]]　winsorized OLS (±5 MAD) → corr=0.941；截断 <2% 尾部 β fit 几乎不动
>
> **路径 C · 标准化变换**
> - [[batches/batch_015/candidates/C003|b015 C003]]　heteroscedastic-norm (F004 / rolling20d-std) → corr=0.927；per-symbol time-series transform 不改 cross-section rank
>
> **路径 D · interaction style**
> - [[batches/batch_015/candidates/C005|b015 C005]]　OLS + vol×turn interaction style → corr=0.997；collinear style pinv 自动消除
>
> **路径 E · 后处理调制**
> - [[batches/batch_014/candidates/C006|b014 C006]]　F004 residual × Sign(Δvolume_5d) → ic_oos=0.0071 < 0.008；volume-confirmation 在 daily 频率证伪
>
> **旁证**
> - [[batches/batch_014/candidates/C001|b014 C001]]　纯 vol_20d 本体（无 residual）→ |IC|=0.063 但 style_r²=0.999 + incremental_ic=-0.046 → magnitude ≠ tradability；residualization 是 12× 清洁度 value-add
> - [[batches/batch_013/candidates/C002|b013 C002]]　vol-20d-only residual → reserve（ICIR=0.243 ls_t=7.28 alpha_surv=1.62）；vol_20d 单独剥离即捕获大部分 alpha
> - F005（20d window 变体）admit → 2026-04-20 retired（bit-for-bit duplicate of F004；near_duplicate gate 对 Python factors 盲区）
>
> **Answer**: **F004 是 7-style basis × OLS-family 残差的几何不变量**。basis 子集 / 损失函数 / 标准化 / interaction / 时序后处理 5 类路径全部 collapse 到 corr ≥ 0.91。后续探索必须跳出该框架。

### T003: Lookahead detection + 数据契约缺口 [◉ ACTIVE]

> [!note]+ Thread 进度
> **Question**: hard_gate 是否充分检测 Python 候选的时序泄漏？REQUIRED_FIELDS 契约是否被 loader 遵守？
>
> **Evidence trail**:
> - [[batches/batch_014/candidates/C003|b014 C003]]　`close.shift(-HORIZON)/close - 1` 把 t+5 累计收益作为 t 因子值；hard_gate 8 项全过，但 ic_oos=0.386 / icir=4.63 / ls_t=83 / ls_max_dd=0 / win_rate=1.0 / sortino=inf 是构造性 leak artifact
> - [[batches/batch_015/candidates/C002|b015 C002]]　Python 候选 REQUIRED_FIELDS=["$close","$high","$low"] 触发 `compute_error: market_df missing $high/$low`——data_bridge loader 默认只准备 close/volume/amount/market_cap，不尊重契约
>
> **系统盲区**:
> 1. Barra residualize 只剥截面风格，不防时序 leak
> 2. hard_gate 当前无 negative-shift 检测、无"too good to be true"哨兵
> 3. loader 忽视 Python factor 的 REQUIRED_FIELDS 声明
>
> **Next probes**:
> - **短期**：主 agent 对 |ic_oos|>0.10 候选 manual review
> - **中期**：loader 扩默认列加 OHLC 全集 / phase1 freeze 时 validate REQUIRED_FIELDS ⊆ loader 列
> - **长期**：hard_gate 增 AST 扫描禁 `shift(-k)` in factor value path + 哨兵指标（ls_max_dd=0 / win_rate=1.0 / sortino=inf 任一触发 → suspicion queue）

---

## Lessons 升格（反复出现经验）

1. **时序平滑/标准化不改 cross-sectional rank**：EMA / rolling-std / heteroscedastic-norm 对截面秩零贡献（T002 路径 A+C 三证）。
2. **鲁棒损失 ≈ OLS 在低尾部污染数据上**：Huber / winsor ±5 MAD 对 A 股日频 β 估计几乎零修正（T002 路径 B 二证）。
3. **共线 style 被 pinv 自动消除**：interaction/duplicate basis 不产生新自由度（vol×turn corr=0.997）。
4. **magnitude ≠ tradability**：|IC|=0.063 的纯 vol_20d style_r²=0.999，residualization 才是 value-add。
5. **Python factor 构造安全必须纳入 hard_gate**：negative-shift / forward-cumulative 等构造性 leak 无法被 IS/OOS 统计指标捕获。

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_012/candidates/C002\|b012 C002]] | Barra residual variant | sign_flip + oos_decay |
| [[batches/batch_012/candidates/C004\|b012 C004]] | 5d rolling residual | IC=0.007 < 0.008 |
| [[batches/batch_012/candidates/C005\|b012 C005]] | 20d momentum residual | IC=-0.0035（方向反转） |
| [[batches/batch_013/candidates/C003\|b013 C003]] | residual × turnover interaction | sign_flip + oos_decay=-1.648 |
| [[batches/batch_013/candidates/C004\|b013 C004]] | 10d Barra styles | redundant with C001 |
| [[batches/batch_013/candidates/C005\|b013 C005]] | size-neutral quintile | compute_error |
| [[batches/batch_014/candidates/C002\|b014 C002]] | vol-20d-keep + 3d EMA | corr=0.987 with F004 |
| [[batches/batch_014/candidates/C003\|b014 C003]] | 5d forward cumulative residual | **lookahead leak** |
| [[batches/batch_014/candidates/C004\|b014 C004]] | strip only momentum cluster | sign_flip + ic_oos_too_low |
| [[batches/batch_014/candidates/C005\|b014 C005]] | strip all except log_circ_cap | corr=0.906 with F004 |
| [[batches/batch_014/candidates/C006\|b014 C006]] | F004 × Sign(Δvolume_5d) | ic_oos=0.0071（volume confirmation 证伪） |
| [[batches/batch_015/candidates/C001\|b015 C001]] | Huber IRLS residual | corr=0.907 |
| [[batches/batch_015/candidates/C003\|b015 C003]] | heteroscedastic-norm | corr=0.927 |
| [[batches/batch_015/candidates/C004\|b015 C004]] | winsorized OLS (±5 MAD) | corr=0.941 |
| [[batches/batch_015/candidates/C005\|b015 C005]] | OLS + vol×turn interaction | corr=0.997 |

---

## Related

- 🔴 [[lessons#Structural Constraints]] `reference` — Barra style coupling 教训汇编
- 🟡 [[amount_volatility_signal]] `saturated` — vol_20d 天花板同源；本方向残差化证实 vol_20d 主导
- 🟡 [[value_liquidity_interaction]] `saturated` — DSL 空间穷尽；两方向均指向需跳出 OHLCV+Barra 基底
- 🔴 [[fundamental_momentum]] `dead` — 其 ep_ratio 已是 Barra style；证伪"变化率"形式后强化本方向 basis 穷尽结论

---

## Narrative Log

> [!quote]+ 2026-04-21 · [[batches/batch_015/judge|batch_015]]
> **admit=0 / reserve=0 / reject=5** — 方向 saturated。
>
> **F004 不动点定理（实验性建立）**：5 method-switch 候选全部 collapse——Huber=0.907 / hetero=0.927 / winsor=0.941 / vol×turn=0.997。F004 是 7-style basis × OLS-family 上的几何不变量。
>
> **跨 batch_014+015 saturation 证据链**：
> 1. basis 子集调整 → vol_20d 主导
> 2. 损失函数切换 → 几何不变
> 3. 时序后处理（EMA/std）→ cross-section rank 不变
> 4. interaction style → collinear pinv 消除
> 5. forward horizon → lookahead leak
>
> **状态转移**：`productive → saturated`，`priority: high → low`。
> **下一步**：batch_016 开新方向 **microstructure_signal**（intraday H-L / open-close / 量价不对称），先解决 loader $high/$low 问题。

> [!quote]- 2026-04-21 · [[batches/batch_014/judge|batch_014]]
> **admit=0 / reserve=1 / reject=5**。三大发现：
> 1. vol_20d 主导残差空间（C002+C005 双向证明）：strip 6 keep vol_20d corr=0.987；strip 6 keep log_circ_cap corr=0.906。其余 6 styles 合计贡献 <10% 可分离方差。
> 2. C003 暴露 hard_gate 时序检测盲区（`close.shift(-5)/close - 1` lookahead leak，8 项 gate 全过但全是 artifact）。新建 T003 thread。
> 3. C001 纯 vol_20d reserve：|IC|=0.063 但 style_r²=0.999 + incremental_ic=-0.046——residualization 是 12× 清洁度 value-add。
>
> **下一步**：batch_015 换残差化方法，若仍 0 admit 则方向 saturated。

> [!quote]- 2026-04-19 · [[batches/batch_013/judge|batch_013]]
> **admit=1 / reserve=1 / reject=3**。C001 admit（F005，60d 变体，后因 F004 duplicate 于 2026-04-20 retired）replicate batch_012 结果；vol_20d dominant (coef=4.44) 但 residual IC > raw IC。C002 reserve：vol-20d-only residual（ICIR=0.243 ls_t=7.28 alpha_surv=1.62）比全剥离 survival 更高。C003 reject（sign_flip + oos_decay）；C004 reject（identical to C001）；C005 reject（compute_error）。

> [!quote]- 2026-04-19 · [[batches/batch_012/judge|batch_012]]
> **admit=1 / reserve=1 / reject=3** — 方向首批验证假设成立。C001 admit（F004 barra_residual_return）：IC=0.024 ICIR=0.293 ls_t=7.34；Barra_residual_IC=0.033 > raw IC=0.024；incremental_ic=0.032 全新机制空间。C003 reserve（style_r²=0.289 + vol_20d exposure=15.6 耦合严重）。C002/C004/C005 reject（IC 不足或 sign_flip）。T001 answered；T002 active。


## Instructions

Rewrite this direction md to compress long narrative logs, dedupe threads, and preserve Hypothesis + active Threads + Narrative Log (truncated to most recent 20 entries). Do not touch the frontmatter — Python manages that.
