---
batch_id: batch_077
direction: tsrank_candlestick_ratio
judged_at: 2026-05-02T06:30:00Z
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

# batch_077 Judge — tsrank_candlestick_ratio frontier 上限饱和铁证

> [!warning]+ batch_077 · [[directions/tsrank_candlestick_ratio]] · 6 candidates (round 77, 续探 hot streak 后首次全 reject)
> ❌ **admit=0** · ⏸ **reserve=0** · ❌ **reject=6**
> **核心发现**: b073/b076 hot streak 后首次全 reject — **frontier 上限饱和铁证** (b076 P019 升格 candidate 反向证伪). 三层 nested composition (C001/C005) max_corr 0.58-0.63@F025 库 overlap 阻断; cross-product Mul (C004) max_corr 0.70@F025 完全 collapse 到 F025; Std×TsRank 双量纲化 (C002) vol_20d_exp 42 反而吸 vol basis 加重; (H-L)/分母 替换 (C003/C006) sty_r² 0.13 over poor line 同 b076 C004 reject 模式 + C003/C006 是 in-batch near-duplicate (IC daily corr 0.9996). **方向 frontier 几何已饱和**.
> **MT Budget**: cumulative 420 → 426 · direction 6 → 12 · bucket `medium`
> **direction status**: `active` 维持 (admits=2 不变), 但 saturation 信号 — b078 切换 direction.

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | aligned·borderline·good·**high(F025)**·stable | ic_oos=+0.009 ls_t=+3.83 mono=+0.7 alpha_surv=1.91 sty_r²=0.027 vol_20d_exp=6.40 max_corr=**0.6272@F025** incr=+0.010 | TsRank shadow_asym/body 三层 nested 嵌套 — vol_20d_exp 6.40 frontier 顶级 (低于 F025), sty_r² 0.027 batch min, **但 max_corr 0.63@F025 库 overlap 完全 collapse** (三层化未破 F025 共线性). **frontier 上限饱和铁证 #1**: 三层 composition 仅深化 F025 几何, 未引入新维度 | [[batches/batch_077/candidates/C001]] |
| C002 | ❌ reject | misaligned·borderline·**poor(0.228)**·medium(F001)·stable | ic_oos=-0.024 ls_t=-3.13 mono=-0.7 alpha_surv=**0.418** ↓边缘 sty_r²=**0.228** vol_20d_exp=**42.03** ⚠ str_1m_exp=1.39 max_corr=0.32@F001 incr=-0.002 | TsRank Std((H-L)/C, 20), 60 — Std layer 把 range vol-of-vol 化, **反而加重 vol basis**: vol_20d_exp 42 (4× F024) + sty_r² 0.228 (2× poor line). incr_ic ≈ 0 表示 Std×TsRank 双量纲化无新信息. b076 C004 (sty_r²=0.133) 同 family reject 模式延伸. | [[batches/batch_077/candidates/C002]] |
| C003 | ❌ reject | aligned·strong·**borderline poor(0.132)**·**low(F022)**·stable | ic_oos=-0.038 ls_t=-3.54 mono=-0.7 alpha_surv=0.99 sty_r²=**0.132** vol_20d_exp=12.53 max_corr=0.27@F022 incr=-0.035 | TsRank (H-L)/(C+O), 60 — 信号强 sign-stable 9/9 NEG max_corr UNDER 0.30 line, **但 sty_r² 0.132 OVER 0.12 poor line + alpha_surv=0.99 边缘**. 与 b076 C004 (sty_r²=0.133, alpha_surv=0.99) 同失败模式 — (C+O) 分母替换未足够削弱 vol_20d basis (range/normalized-price 本质是 vol proxy). 同时与 C006 IC daily 相关性 **0.9996** in-batch near-duplicate (重选). | [[batches/batch_077/candidates/C003]] |
| C004 | ❌ reject | aligned·strong·good·**high(F025)**·stable | ic_oos=+0.024 ls_t=+5.73 mono=+0.7 alpha_surv=1.08 sty_r²=0.115 vol_20d_exp=8.48 max_corr=**0.6972@F025** incr=+0.007 | Mul(CsRank(F024_atom), CsRank(F025_atom)) — cross-product Mul 把两个 admit atom 在 cross-section 上乘积. **max_corr 0.70@F025 几乎完全 collapse 到 F025** (CsRank Mul 形式比 TsRank 维持更多 F025 几何信息). incr_ic 0.007 信号微弱新意, 不足 admit 阈值. **frontier 上限饱和铁证 #2**: cross-product Mul 不破共线性, F024×F025 = F025 复制 | [[batches/batch_077/candidates/C004]] |
| C005 | ❌ reject | aligned·strong·good·**medium-high(F025)**·**unstable(decay 5.81)** | ic_oos=+0.022 ls_t=+6.39 mono=+0.7 alpha_surv=0.728 sty_r²=0.025 vol_20d_exp=6.36 max_corr=**0.5817@F025** incr=+0.012 train_val_decay=**5.81** | TsRank Mul(body_ratio, shadow_asym), 60 — Mul 替换 Div 的 nested composition. vol_20d_exp 6.36 + sty_r² 0.025 frontier 顶级, ls_t 6.39 信号强, **但 max_corr 0.58@F025 库 overlap + train_val_decay 5.81 极高 (signal weakens OOS, b076 C001/C005 同 atom 路径同失败)**. **frontier 上限饱和铁证 #3**: Mul-form 与 Div-form composition 在几何上等价, 未引入新维度 | [[batches/batch_077/candidates/C005]] |
| C006 | ❌ reject | aligned·strong·**borderline poor(0.133)**·**low(F022)**·stable | ic_oos=-0.038 ls_t=-3.64 mono=-0.7 alpha_surv=0.99 sty_r²=**0.133** vol_20d_exp=12.56 max_corr=0.27@F022 incr=-0.035 | TsRank (H-L)/midprice, 60 — **与 C003 in-batch near-duplicate** (IC daily corr 0.9996, 数学上 (C+O)≈(H+L) 在常态下). 同 sty_r² OVER 0.12 + 同 alpha_surv 边缘 + 同 max_corr@F022 + 同 ic_by_year 9/9 NEG. **重选规则 reject 一**, 信号家族同 b076 C004 reject. | [[batches/batch_077/candidates/C006]] |

**档位编码**：🟢 最优档（aligned/strong/good/low/stable）· 🟡 次档（mixed/borderline/acceptable/medium）· 🟠 边际 · 🔴 阻断档（misaligned/weak/poor/high/unstable）.

## 跨候选对比 — frontier 上限饱和三铁证

**三类 frontier 续探路径全部 reject — 方向几何空间已饱和**:

| 路径 | 候选 | max_corr | sty_r² | vol_20d_exp | alpha_surv | 失败模式 |
|---|---|---|---|---|---|---|
| 三层 nested composition (Div) | C001 | **0.6272@F025** | 0.027 ✓ | 6.40 ✓ | 1.91 ✓ | 库 overlap collapse |
| 三层 nested composition (Mul) | C005 | **0.5817@F025** | 0.025 ✓ | 6.36 ✓ | 0.728 | 库 overlap + decay 5.81 |
| Cross-product Mul (CsRank×CsRank) | C004 | **0.6972@F025** | 0.115 | 8.48 ✓ | 1.08 ✓ | 完全 collapse 到 F025 |
| Std × TsRank 双量纲化 | C002 | 0.32@F001 | **0.228** ✗ | **42.03** ✗ | 0.418 边缘 | Std layer 加重 vol basis |
| (H-L)/(C+O) 分母替换 | C003 | 0.27@F022 ✓ | **0.132** ✗ | 12.53 | 0.99 边缘 | sty_r² 同 b076 C004 reject |
| (H-L)/midprice 分母替换 | C006 | 0.27@F022 ✓ | **0.133** ✗ | 12.56 | 0.99 边缘 | C003 数学等价 + 同 sty_r² |

**关键洞察**:

1. **几何 saturation 律实证 (P021 升格 candidate)**: F025 几何 (shadow_asymmetry × TsRank60) 在三层 composition / Mul 替代 / cross-product 三种 frontier 续探下 **max_corr 全部 ≥0.58@F025**. 这表明 F025 atom 已成为该几何家族的 "absorbing factor" — 任何"更深 OHLC composition + 时序量纲化"几何路径在 cross-section 上仍 collapse 到 F025 (高阶 composition 本身已被 F025 占据为 prototype, 后续无新维度可加).

2. **range/normalized-price 是 vol proxy 不可解 (b076 P020 second实证)**: C003 (C+O 分母) / C006 (midprice 分母) / b076 C004 (close 分母) 三种分母替换尝试, sty_r² 全部 落 0.12-0.14 区间 OVER poor line, alpha_surv 全部 0.99-1.0 边缘. **range/normalized-price 本质是 vol proxy, 任何分母选择都无法把 sty_r² 压到 acceptable line**.

3. **double-quantization 反向加重 vol basis (P022 升格 candidate)**: C002 Std×TsRank 双量纲化 vol_20d_exp 42 (b076 C004 单 TsRank vol_20d_exp ≤22) — Std layer 不削弱反而**放大** vol basis. 双量纲化在 vol-proxy 信号上无收益, 反而加 noise.

4. **CsRank-Mul cross-product = factor identity collapse (P023 升格 candidate)**: F024 × F025 在 CsRank 后 Mul → max_corr 0.70@F025. 两个独立 admit factor 的 cross-product 在 cross-section 上**塌缩到其中一个** (近似几何 dominance), 不产生新维度. b078+ 续探需 directionally orthogonal atoms (e.g. fundamental × 价量) 而非 同 family 内 Mul.

5. **in-batch duplicate 检测**: C003/C006 IC daily corr 0.9996 — (H-L)/(C+O) 与 (H-L)/midprice 数学上近似等价 ((C+O)≈(H+L) 在 typical 日, 两个分母差异 1-2%). **设计阶段未察觉, 系统级别 P024 升格 candidate**: Phase 1 设计 checklist 加 "denominator family 等价性" 自检.

## Thread 进展

> [!failure]+ T003 [[directions/tsrank_candlestick_ratio#T003]] — `[~ PARTIAL DISPROVEN batch_077]` (frontier 上限饱和)
> **Question**: 三层 OHLC composition / Std×TsRank 双量纲化 / cross-product Mul 是否破 F025 几何?
>
> **Answer**: **DISPROVEN**. 三种 frontier 续探路径全部 reject — F025 几何已成 absorbing factor (P021 升格), max_corr 0.58-0.70@F025 阻断 admission. 三层 composition (C001 Div / C005 Mul) 仅深化 F025 几何; cross-product Mul (C004) 完全 collapse; Std×TsRank (C002) 反向加重 vol basis. **方向 frontier 几何空间饱和铁证 — b078 切换 direction**.
>
> **Evidence trail**:
> - [[batches/batch_077/candidates/C001|b077 C001]] 三层 nested Div → reject (max_corr 0.63@F025)
> - [[batches/batch_077/candidates/C004|b077 C004]] CsRank Mul cross-product → reject (max_corr 0.70@F025)
> - [[batches/batch_077/candidates/C005|b077 C005]] Mul-form composition → reject (max_corr 0.58@F025 + decay 5.81)
> - [[batches/batch_077/candidates/C002|b077 C002]] Std×TsRank → reject (sty_r² 0.228 + vol_20d_exp 42)
> - [[batches/batch_077/candidates/C003|b077 C003]] (H-L)/(C+O) → reject (sty_r² 0.132)
> - [[batches/batch_077/candidates/C006|b077 C006]] (H-L)/midprice → reject (C003 数学等价 + sty_r² 0.133)

## 方向级反思

Round 77 续探 hot streak 后首次全 reject — **direction 几何饱和铁证**:

1. **direction 状态判定**: rounds=2, admits=2 (F024 b073 + F025 b076 维持), 本批 0 admit / 0 reserve / 6 reject. status 维持 `active` (因 admits=2 库内仍活跃因子) **but saturation 信号触发** — b078 切换 direction (推荐: python_ttm_residual_quality 复活 fundamental 路径 / overnight_intraday_split / cov_microstructure_valuation).

2. **核心 saturation mechanism PROVEN**: F025 (shadow_asymmetry_tsrank_60) 已成 "absorbing factor" — 同方向的 nested composition / cross-product / 替代 form 在 cross-section 上全部 collapse 到 F025 几何. 这是 admit 后方向局部饱和的典型模式 (类似 batch_044 范围内 turnover_vol family 在 F031 admit 后饱和).

3. **P021 升格 candidate**: **几何 absorbing factor 律** — 一个 admit factor 在其几何家族内成为 absorbing prototype, 同 family 后续 frontier 续探在 cross-section 上 max_corr ≥0.55@该 factor (b077 三铁证). admit 后该 family 续探优先级 ↓; 切换 cross-family.

4. **P022 升格 candidate**: **double-quantization 反向律** — Std/Mean × TsRank 双层 quantization 在 vol-proxy 信号上**反向加重** style basis (vol_20d_exp 4× 增加, sty_r² 2× 增加). 双量纲化只在 non-vol-proxy 信号上有收益.

5. **P023 升格 candidate**: **CsRank-Mul cross-product 塌缩律** — 两个同 family admit factor 的 CsRank Mul 在 cross-section 上塌缩到其中一个 (max_corr 0.70). cross-product 续探需 directionally orthogonal atoms.

6. **P024 升格 candidate (系统级)**: **denominator family 等价性自检** — Phase 1 设计 checklist 加 "若候选 atom 仅分母不同, 检查分母在常态下数学等价性 (e.g. (C+O) vs (H+L) vs midprice)". C003/C006 是该规则的 first 实证 (in-batch duplicate, 浪费 1 计算预算).

7. **zero_admit_streak**: 0 → 1 (b076 admit reset 后 b077 首次重置).

8. **rounds_since_last_consolidation**: 4 → 5 (距离 ≥10 触发还有 5 轮).

## 阈值校准段

- 无错杀风险 — 6/6 reject 全部命中 hard 红线: max_corr 高 (C001/C004/C005), sty_r² over poor (C002/C003/C006), in-batch duplicate (C006).
- 无 P008/P011 alpha_survival 红线踩踏 (C001/C004 alpha_surv ≥1.0 PASS; C002 0.418 边缘但 sty_r² 0.228 主因 reject).
- 无市值代理风险 (无 $market_cap atom).
- 无 P016 cap-denominator 几何 (无 cap 分母).
- 触发 saturation calibration discussion: 本批是 hot streak 后首次全 reject, 需 b078 切换 direction 验证是否真饱和 (若 b078 / b079 在其它 direction 也低 admit, 则 system-level frontier saturation; 若其它 direction 复活 admit, 则当前 direction 局部饱和).
