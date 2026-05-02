---
batch_id: batch_079
direction: cov_ratio_long_window
judged_at: 2026-05-02T07:45:00Z
candidates:
  - {candidate_id: C001, verdict: reject, thread_id: T001}
  - {candidate_id: C002, verdict: reject, thread_id: T001}
  - {candidate_id: C003, verdict: reject, thread_id: T002}
  - {candidate_id: C004, verdict: reject, thread_id: T002}
  - {candidate_id: C005, verdict: reject, thread_id: T002}
  - {candidate_id: C006, verdict: reject, thread_id: T003}
batch_summary: {total: 6, admit: 0, reserve: 0, reject: 6}
admit_count: 0
reserve_count: 0
reject_count: 6
candidate_count: 6
mt_bucket: medium
---

# batch_079 Judge — cov_ratio_long_window 首批反向证伪 + 数据契约 P019 升格候选

> [!warning]+ batch_079 · [[directions/cov_ratio_long_window]] · 6 candidates (round 79, NEW direction orchestrator-dispatched, 0 admit)
> ❌ **admit=0** · ⏸ **reserve=0** · ❌ **reject=6**
> **核心发现**: 首批反向证伪 cov_ratio_long_window 假设 — TsRank≥60d 包裹 long-window Corr 在 csi1000 daily 上 (a) 60d Corr OHLCV 子族 (C003/C004/C005) sign-stable 但 ic_oos 0.004-0.006 全部 sub-threshold; (b) 120d Corr (C006) 信号完全 collapse sign_flip; (c) baseline-first 强制 untouched fundamental TTM 单原子 (C001 PEG / C002 PCF_total) 也 sign_flip / ic_oos sub-threshold 全 reject.
> **数据契约 P019 升格候选**: 设计阶段意图覆盖 PIT valuation × liquidity × num_trades 全 frontier, 但 Qlib `Corr` 在 cross-field 时遭遇**字段 start_index 不齐 broadcast crash** (∼80% universe). 不可用字段族: $turnover_rate (与 OHLCV 不齐), 全部 PIT valuation ($pe/$pb/$ps/$pcf), 全部 TTM ratio ($dividend_yield/$peg/$pcf_total). Corr-safe 字段集仅 {$close, $open, $high, $low, $volume, $amount, $num_trades}.
> **MT Budget**: cumulative 432 → 438 · direction 0 → 6 · bucket `medium`
> **direction status**: 首批反向证伪即 `dead` 候选 (cov_microstructure_valuation b075 同套精神已 dead). 但本批 dead 律涵盖更广 (TsRank-Corr wrap + baseline single-atom TTM 双失败), 升格 P019 + 扩展 P018 边界.

## 候选一览

| ID | Verdict | Thread | Expression | 档位 (HG·sign·ic_oos·alpha_surv·max_corr) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|---|---|
| C001 | ❌ reject | T001 | `CsRank($peg_ratio_ttm)` | ❌·**flip**·sub-th·N/A·LOW | sign_flip +0.0021/-0.0027, ic_oos\|0.0027\|<0.008 | PEG_TTM 单原子 baseline 9-yr regime drift, csi1000 daily TTM 真饱和扩展至 single-atom | [[batches/batch_079/candidates/C001]] |
| C002 | ❌ reject | T001 | `TsRank($pcf_ratio_total_ttm, 60)` | ❌·stable·sub-th·**0.109 FAIL**·LOW(F009) | ic_oos\|0.0042\|<0.008, dom=vol_20d | TsRank-60 P008 律不适用 TTM ratio 字段, alpha_surv 0.11 三立 vol_20d | [[batches/batch_079/candidates/C002]] |
| C003 | ❌ reject | T002 | `TsRank(Corr($volume, $close, 60), 60)` | ❌·stable·sub-th·0.533 PASS·LOW(F009) | ic_oos\|0.0064\|<0.008, ls_t=-1.43 | 60d TsRank-Corr OHLCV 几何独立 + alpha_surv PASS 但 ic 强度天花板 | [[batches/batch_079/candidates/C003]] |
| C004 | ❌ reject | T002 | `TsRank(Corr($amount, $high, 60), 60)` | ❌·stable·sub-th·0.605 PASS·LOW(F007) | ic_oos\|0.0061\|<0.008, ls_t=-1.28 | 同 C003 模式 — 60d 长窗 daily 1d horizon 信噪比上限 | [[batches/batch_079/candidates/C004]] |
| C005 | ❌ reject | T002 | `TsRank(Corr($num_trades, $close, 60), 60)` | ❌·stable·sub-th·**1.165 GREEN(批最高)**·LOW(F009) | ic_oos\|0.0040\|<0.008(批最弱 60d), ls_t=-0.58 | alpha_surv 顶 + ic 微弱 — P004 解耦律第 N 个独立实证 | [[batches/batch_079/candidates/C005]] |
| C006 | ❌ reject | T003 | `TsRank(Corr($volume, $low, 120), 60)` | ❌·**flip**·sub-th·**4.194 GREEN(批最高)**·LOW(F021) | sign_flip -0.0008/+0.0011 collapse, ls_t=-0.22 | 120d 长窗频率 mismatch daily 短期 alpha, 信号 collapse | [[batches/batch_079/candidates/C006]] |

**档位编码**: ✓ 通过 / ❌ 失败 / `stable` sign 同号 / `flip` sign 翻号 / `sub-th` ic_oos<0.008 阈值 / `LOW` max_corr<0.30 几何独立.

## Thread 进展

- **T001 (untouched fundamental TTM baseline)** `[✗ DISPROVEN batch_079]`: 2 候选 (C001 PEG / C002 PCF_total) 全 reject — peg_ratio_ttm 9-yr ic_by_year regime 翻转 + sign_flip; pcf_ratio_total_ttm TsRank-60 alpha_surv=0.109 + dom=vol_20d 三立 + ic_oos sub-threshold. 16 untouched fundamental TTM 字段中 2 个首测 disprove → confirm csi1000 daily TTM fundamental 真饱和不仅适用 composite, 也适用 single-atom baseline.
- **T002 (TsRank-Corr long-window pivot)** `[✗ DISPROVEN batch_079]`: 3 候选 (C003 volume×close / C004 amount×high / C005 num_trades×close) 全 reject — 60d TsRank-Corr OHLCV 子族几何独立 max_corr<0.05 + alpha_surv 0.53/0.61/1.17 PASS 0.40 floor + sign-stable double-NEG, 但 ic_oos 0.004-0.006 全 sub-threshold. 60d 协动 daily 1d primary horizon 信噪比上限 ~0.006-0.007. 升格 P018 边界扩展.
- **T003 (long-window 120d)** `[✗ DISPROVEN batch_079]`: 1 候选 (C006 volume×low,120) 完全 collapse — train ic ≈ 0, val ic sign-flip, alpha_surv 4.19 但 ic 完全无方向. 120d 频率 mismatch daily 短期 alpha. 升格 P008 适用边界.

## 跨候选对比 — TsRank-Corr long-window family 系统性失败

### 子族 1: 60d TsRank-Corr OHLCV (C003/C004/C005) — 几何独立 + 信号 sub-threshold

| 候选 | 表达式 | ic_oos | alpha_surv | dom_style | max_corr | 失败模式 |
|---|---|---|---|---|---|---|
| C003 | volume × close | -0.0064 | 0.533 PASS | vol_20d | 0.040@F009 | ic strong-noise <0.008 |
| C004 | amount × high | -0.0061 | 0.605 PASS | vol_20d | 0.041@F007 | ic strong-noise <0.008 |
| C005 | num_trades × close | -0.0040 | **1.165 GREEN** | vol_20d | 0.047@F009 | alpha_surv 顶 + ic 噪声 |

**模式**: 三候选 sign-stable double-NEG (-0.004 ~ -0.006), alpha_surv 全 PASS 0.40 floor (0.53 / 0.61 / 1.17), max_corr 全 < 0.05 几何独立性强. 但 ic_oos magnitude 全部 0.004-0.006 区间, 均 < 0.008 admission threshold. **60d 协动 daily 1d primary horizon 信噪比上限 ~0.006-0.007**.

### 子族 2: 120d TsRank-Corr OHLCV (C006) — 信号完全 collapse

C006 train_ic=-0.0008 几乎 0, val_ic=+0.0011 翻号, alpha_surv=4.19 整批最高但 ic 完全无方向. **120d 长窗口 → 频率 mismatch**: 长周期协动信号 (≥半年级别) 与 t+1 daily alpha 时间尺度不符, 信号成分被 daily reversion 淹没.

### 子族 3: TTM single-atom baseline (C001/C002) — Step 1.5 baseline-first 强制 + 双失败

| 候选 | 表达式 | ic_oos | alpha_surv | sign | 失败 |
|---|---|---|---|---|---|
| C001 | CsRank($peg_ratio_ttm) | -0.0027 | N/A | **flip** | ic_oos sub-th + sign flip + 9-yr regime drift |
| C002 | TsRank($pcf_ratio_total_ttm, 60) | -0.0042 | **0.109 FAIL** | stable | ic_oos sub-th + dom=vol_20d 三立 |

**模式**: 16-untouched-fundamental-fields 中两个 0-atom-experiment 字段 (peg_ratio_ttm, pcf_ratio_total_ttm) 在最纯 baseline 形式 (CsRank / TsRank-60) 上无独立 OOS alpha. 印证 lessons.md macro: csi1000 daily TTM fundamental 真饱和不仅适用 composite, 也适用 single-atom baseline.

## P004 alpha_surv-OOS-strength 解耦律重显

C005 alpha_surv=1.165 + max_corr=0.047 + sign-stable double-NEG = "三立于风险清洁高质量信号" — 但 ic_oos=-0.0040 几乎噪声水平; C006 alpha_surv=4.19 整批最高但 ic 完全 collapse. 两候选独立印证 P004 校准律 (round 73 升格): **alpha_survival 高 ≠ alpha 真存在**, 仅证明残差对 Barra style 线性独立; csi1000 daily 上信号本身就弱时, 残差再 clean 也不蕴含 OOS alpha magnitude.

## 升格候选

### P019 (新, 数据契约) — Qlib Corr cross-field start_index 不齐导致 broadcast crash

**机理**: Qlib 二进制 `[start_index:f32][data:f32×N]` 格式中, **PIT valuation 字段 / TTM ratio 字段 / $turnover_rate 字段** 与核心 OHLCV ($close/$open/$high/$low/$volume/$amount/$num_trades) **start_index 不一致** (因为 RiceQuant 同步时, valuation/turnover 数据从 sec 元年 ≠ price 数据起始点). 当 `Corr(safe_field, broken_field, N)` 在多股票 universe 评估时, 内部 `series_left.rolling.std()` 与 `series_right.rolling.std()` shape 不匹配 (e.g. 2620 vs 2674) → `np.isclose` broadcast crash, **整批 compute 终止**.

**实证证据**: 本批设计阶段 5 候选用 PIT valuation/TTM RHS 全部 crash; 替换 OHLCV-only RHS 后 Corr 工作. 排查显示 `$turnover_rate` 同样不可用于 Corr (与 OHLCV 不齐).

**Corr-safe 字段集** (csi1000 universe, 实证): `{$close, $open, $high, $low, $volume, $amount, $num_trades}`.

**Corr-unsafe 字段集** (实证 broadcast crash):
- 全部 PIT valuation: `$pe_ratio, $pb_ratio, $ps_ratio, $pcf_ratio`
- 全部 TTM ratio: `$peg_ratio_ttm, $pcf_ratio_total_ttm, $dividend_yield_ttm` (推论扩展所有 TTM 字段)
- `$turnover_rate`

**Generator 层硬阻断建议**: phase1 freeze 阶段对 `Corr(A, B, N)` / `Cov(A, B, N)` 候选检查 A, B 是否双方在 Corr-safe 字段集; 否则提前 reject 候选, 不让 Phase 2 compute crash.

**修复路径**: (a) 数据 loader 端 ffill / unify start_index 跨字段; (b) Python 包装 Corr 操作绕过 Qlib op (vectorized rolling cov / std with NaN-aware broadcast).

### P018 边界扩展 — TsRank-Corr 包裹也走 vol_20d basis (60d) + 120d 长窗信号 collapse

P018 (round 73 升格) 已封闭 raw `Cov(.,.,N)` form. 本批扩展两律边界:

1. **60d TsRank(Corr(.,.,60), 60) OHLCV**: 几何独立 (max_corr<0.05) + alpha_surv PASS 0.40 floor + sign-stable, 但 ic_oos 0.004-0.006 sub-threshold → **TsRank wrap 在 OHLCV-only 60d Corr 上提供 alpha_surv-pass 但不解决 ic 强度问题**. 长窗口协动信号 daily 1d primary horizon 信噪比天花板.
2. **120d TsRank(Corr(.,.,120), 60)**: 信号完全 collapse train ic ≈ 0 + sign flip → **120d 协动频率 mismatch daily 短期 alpha**.

**P008 适用边界确认**: TsRank window≥60d on **daily ratio fields** 是 vol_20d-escape 路径 (b072/b076/F024/F025 已实证) — 仅适用于 (a) 短窗口协动 (≤20d) 或 (b) 直接 ratio 字段单原子. 不适用于 (c) ≥60d Cov/Corr 内层包裹 (本批 60d sub-threshold), (d) ≥120d 长窗 (本批 120d collapse), (e) TTM ratio 字段 baseline (C002).

### Direction status 转 dead 候选

cov_ratio_long_window 首批反向证伪. 与邻近 dead direction `cov_microstructure_valuation` (b075) 形成 cluster: 两 direction 共同封闭 csi1000 daily 上 long-window 协动 family — 不论 raw Cov (b075) / TsRank-Corr wrap (b079) / 60d 短窗 (b079) / 120d 长窗 (b079) / OHLCV (b079) / valuation/TTM (b075/b079) — alpha 真饱和.

## Direction status 推进

`cov_ratio_long_window`: probing → **dead**. 元教训:

1. **TsRank-Corr 包裹是无效救援**: P018 raw Cov form vol_20d basis 律不能通过包裹 Corr (self-normalize σ) + 外层 TsRank (time-series quantile) 双层规避. 60d 子族 alpha_surv pass 但 ic 强度天花板 ~0.006; 120d 子族信号 collapse.
2. **数据契约边界**: 直接探索 PIT valuation × liquidity Corr 全 crash; OHLCV-only 退路 alpha 真饱和 — 假设无生路.
3. **TTM single-atom baseline 同样饱和**: peg_ratio_ttm + pcf_ratio_total_ttm 在最纯 CsRank/TsRank-60 形式上也无独立 alpha — 印证 lessons macro.

**唯一保留火种**: C005 `TsRank(Corr($num_trades, $close, 60), 60)` alpha_surv=1.165 GREEN + max_corr=0.047 几何独立 + sign-stable, 仅 ic 弱. 不 reserve (ic<0.008 hard_gate fail). 升格 lessons.md "alpha_surv-OOS-strength 解耦律" 段第 N 个独立证据.

## Reflection

- **未发现潜在错杀**: 6 候选 ic_oos 全在 0.001-0.006 范围, magnitude 真实低于 0.008 admission threshold, 不存在边缘 case 误判.
- **数据契约 P019 是阻碍设计空间最大单一因素**: 设计阶段意图测 dividend_yield/peg/pcf TTM × liquidity Corr 的 frontier, 但被 Qlib start_index 数据问题阻断. 修复后该 frontier 仍待探索 (但 P018 + P008 边界提示也大概率饱和).
- **direction lifecycle 触发"首批反向证伪 dead 律"** (lessons codified): 6/6 reject + 多重 lesson 升格证据 → 直接 dead, 不进 saturated.

## Sample policy

train: 2015-01-01 → 2021-12-31 (1665d), validation: 2022-01-01 → 2023-12-31 (484d). Holdout 2024 全程不接触.
