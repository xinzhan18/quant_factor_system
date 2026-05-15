---
generated_at: 2026-05-15T22:55:26Z
round: 96
total_active_directions: 20
total_factors_admitted: 28
last_batch: batch_095
last_consolidation_round: null
---

# 🗺️ Factor Research Index

> [!info] MOC · Map of Content
> 路口页。人看下方 Bases 三表；**LLM 启动读此文件顶部 Cockpit 块**（派生状态 + 下一步指令）；拿数据用 `PYTHONPATH=src python3 -m research memory snapshot`。

<!-- BEGIN COCKPIT -->

> [!note]+ 🧭 LLM Cockpit
> **状态** · round=**96** · phase=`null` (idle) · no batch in flight
> **上一批** · [[batches/batch_095/judge|batch_095]] → [[directions/rank_diff_liquidity_microstructure]] · admit=**0**/6 (reserve=3, reject=3) · direction.status=`exploring`
> **健康** · rounds_since_consolidation=**5** · active_directions=**20** · zero-admit streak=**10**
> **⚠️ 预警** · 空 factor.md: F017.backtest · consolidation 触发: active_directions=20 ≥ 20
>
> **🎯 下一步（按优先级）**
> 1. ⚠️ **修空报告**：F017.backtest 的 `.md` 为空或缺 H1 → 对每个 F{id} 重新 dispatch `/factor-report` subagent
> 2. 📚 **触发 consolidation**：active_directions=20 ≥ 20 → 先调 `/factor-consolidate`，再进 Phase 1
> 3. 🧪 **阈值校准**：连续 10 批零 admit → 先按 `lessons.md#Threshold Calibration` 扫 reserve 候选识别错杀；确认有库空间独立错杀 → 调阈；否则继续
> 4. 🧭 **硬性前置**：`research doctor`（drift 检测）→ `snapshot`（数据）→ 读目标 `directions/{tag}.md` → 进 `/factor-idea`

<!-- END COCKPIT -->

<!-- BEGIN HOT-TOPICS-LLM -->
> [!danger]+ 🆕 系统级事件 · Phase 5 round 91 consolidation (2026-05-16)
> b086-b090 5 批跨方向 zero-admit streak (alpha191 / overnight_intraday / signed_money_flow / idiosyncratic_momentum / price_conditional_amplitude). 揭示 daily-bar frontier 三层结构性失败: (i) **alpha_surv > 1.0 单边形式独立 ≠ library 充分** (5 batch × 5 方向 × 7 candidates 实证 Barra-clean 但库 redundant); (ii) **P004-deep path-integral / N-day 累积形式失败** (path-memory β-shift, 3 方向 dead); (iii) **paper transferability 4 层失效律** (从 3 件套扩展, 4 papers × 4 方向). 4 lessons 升格 + 3 方向 dead + 5 reserve revival 候选打包. **当前 frontier 红色信号**: daily-bar 27 admit 已接近 saturated, intraday primitive layer (src/data/primitive + daily_python_backend) 工程已 untracked, 一旦 ready 是当前最大 unexplored 空间.
> - ✅ **4 lessons 升格**: (1) Rank-order ≠ Tradable Alpha 段加 **P030 alpha_surv > 1.0 单边形式独立不达 admit/reserve 充分性** — alpha_surv 必须配 incr_ic / max_corr / ls_t 三项至少 2/3; (2) vol_20d 律段加 **P004-deep path-integral 累积形式结构性失败** — single-step OK (F004), multi-day aggregation 默认 reject (path-memory β-shift); (3) Paper Transferability 从 3 件套扩展为 **4 层失效律** (新增 frequency mismatch + library overlap 层); (4) Path Selection 加 **P030 Cov ≈ Mean(X*Y, N) 等价律** — b087 实证 cross-section corr=0.927 (>0.9 hard_gate), Phase 1 generator AST 自检
> - 🟠 **方向状态变更 (3 dead, 元教训已升格)**: signed_money_flow_oscillator exploring → **dead** (b088 4/4 子路径 Chaikin/AD/PVT 全证伪) / idiosyncratic_momentum_residual exploring → **dead** (b089 4/4 子假设 全证伪) / price_conditional_amplitude exploring → **dead** (b090 4 路径全证伪). 三方向 dead → archived 预定一轮后转 (本 round 留 dead). 其它: alpha191_universal_subset productive → saturated (F027+F028 admit 维持); range_structure / anchor_proximity_momentum 维持 saturated; overnight_intraday_split productive → saturated (T011 axis 真饱和复证, 仅 T017 reserve 火种)
> - 📌 **Reserve revival 池 5 候选** (asset-driven, calibration/013 finding, 不调阈值靠改表达式): (1) **b072/C006** `TsRank($amount/$num_trades,60)` ls_t=-7.54 整库顶级 + alpha_surv=0.447 边缘卡 incr_ic=-0.018 → window sweep 30d/90d/120d + rank-diff form 减 F012 cluster + reducer reverse; (2) **b076/C005** `TsRank((h+l)/2 / close, 60)` 4 项 CP top max_corr=0.449 cluster → Python residualize on (F008, F026) + RHS swap close→Mean(close,5); (3) **b080/C006** overnight × turnover rank-diff 4 项 top max_corr=0.560 cluster + incr_ic=0.0098 边缘 → RHS basis swap 平滑 + 缩窗; (4) **b087/C001** T017 Corr(volume, overnight, 60) mono=1.0 + horizon 1d→20d IC 0.032→0.073 → 切换 evaluation horizon 1d→5d/10d; (5) **b082/C002** (h-c)/(h-l) TsRank60 ls_t=6.40 mono=1.0 PERFECT max_corr=0.471 → open-anchor RHS swap + Python residualize on (F025, F026)
> - 📌 **下一步 frontier (library_gap finding 提议 2 条)**: (a) `intraday_microstructure_python` **NEW direction** — 库内 27 admit 100% daily-bar, intraday primitive layer 工程已 untracked (src/data/primitive + daily_python_backend) 一旦 ready 是当前最大 unexplored 空间, 含 minute VWAP-vs-close drift / RV 1min/5min / order flow imbalance / opening-closing auction window; (b) 复活已 dead/saturated fundamental directions (pit_valuation_pure / fundamental_quality_carry) — 22 TTM 字段大空白, 用 Mul/Div/Sub 跨族组合 + TTM Delta 季度动量 + EP×growth Fama-French style; (c) 条件算子族空白 (IfElse/Mask/Gt/Lt) — F028 唯一例外 admit, 26 其它全线性, 建议测 vol-rank conditional / event-rate / Greater-truncation 等 4 类新条件
> - **calibration verdict**: 无 config.yaml 阈值数字调整. alpha_surv > 1.0 单边律升格为 lessons hard rule + judge rubric 自检条目 (非 config 数字调整). alpha_survival_min / incremental_ic / max_corr / library_reducer hard_gate 全部维持. **绝不放宽 hard_gate**

> [!warning]+ 🔥 Hot Topics（LLM 维护 · 2026-05-16 scan recent=13 round 91 findings + 历史 round 73-82 keep-alive）
> - 🔴 **P030 alpha_survival > 1.0 单边形式独立 ≠ library 充分条件 (round 91 升格 hard rule)** · dirs: alpha191_universal_subset (saturated), overnight_intraday_split (saturated), signed_money_flow_oscillator (dead), idiosyncratic_momentum_residual (dead), price_conditional_amplitude (dead) → 跨 5 batch (b086-b090) × 5 方向 × 7+ candidates 独立复现: Barra-residual IC ≥ raw IC (alpha_surv 1.05-1.59) + max_corr<0.30 LOW + sign_consistency=1.0 三立完美 form 独立, 但 incr_ic NEG (-0.005~-0.023). 机理: alpha_surv 衡量 vs Barra 9-style basis 残差, **不**衡量 vs admitted library 残差; close-position cluster (F006-F008-F026) + multi_ma_reversion (F027) + amount_cv (F001) 都是 non-Barra 几何 — **Barra-clean ≠ library-clean** 两独立 gate. 实操律: alpha_surv > 1.0 必须配 (a) incr_ic ≥ +0.005 + (b) max_corr<0.40 + (c) ls_t ≥ 1.5 至少 2/3 才可 reserve, 否则默认 reject
>   evidence: [[batches/batch_086/judge|batch_086]], [[batches/batch_088/judge|batch_088]], [[batches/batch_089/judge|batch_089]], [[_consolidation/findings/pattern_analyst/027]], [[_consolidation/findings/calibration/012]], [[_consolidation/findings/hypothesis_promoter/020]], [[lessons#Rank-order ≠ Tradable Alpha 判别律]]
> - 🔴 **P004-deep path-integral / N-day 累积形式结构性失败 (round 91 升格, P004 vol_20d 律深层扩展)** · dirs: signed_money_flow_oscillator (dead), idiosyncratic_momentum_residual (dead), price_conditional_amplitude (dead) → 跨 3 batch 跨 3 方向 13 候选: Barra cross-sectional residualization 是 single-step 线性算子 (F004 single-day ε alpha_surv=1.41 admit 反例), 但任何 N-day path-integral / 累积 / EMA-差 / rank-diff / IVOL-gated 累积形式 dom_style 全部恢复=vol_20d (exposure 7.4-35.3). 机理: path-memory β-shift — 累积让内层 β(t-i) 不是 t 时刻常数, vol_20d basis 暴露重新涌现. 比已知 "non-linear absorption (Linear OLS Polynomial 不破)" 更深一层. 实操: 若需 isolate residual alpha, stay at single-step + 用 multi-day evaluation horizon 替代 multi-day LHS aggregation; Phase 1 hard precheck `Sum(residual_X,N)` / `Mean(Cumulative_signed_flow,N)` / `Sum(signed_return × Vol,N)` (N>1) 自动 reject
>   evidence: [[batches/batch_088/judge|batch_088]], [[batches/batch_089/judge|batch_089]], [[batches/batch_090/judge|batch_090]], [[_consolidation/findings/pattern_analyst/028]], [[_consolidation/findings/hypothesis_promoter/020]], [[lessons#vol_20d 结构性吸收律]]
> - 🟠 **Paper transferability 4 层独立失效律 (round 91 升格, 从 round 73 3 件套扩展)** · dirs: alpha191_universal_subset (saturated), signed_money_flow_oscillator (dead), idiosyncratic_momentum_residual (dead), price_conditional_amplitude (dead) → 4 papers (海通-37 IMom / 广发金工-42 Chaikin/AD/PVT / Du-Walter-Ulrich 2026 Alpha191 / paper rank-conditional aggregation) × 4 directions × 26+ candidates 4 层独立失效机制实证: (1) 方向反号 paper momentum → csi1000 mean-reversion; (2) frequency mismatch monthly Barra residualization → daily path memory 律不对称; (3) universe weakness paper 自承大盘 IC 衰减 2.4x; (4) library overlap csi1000 admitted 27 因子 non-Barra 几何 capture 同质 alpha. 任 1 yes 进 round 1 前需 risk-review. /factor-paper workflow 必须在 frontmatter 写 transferability_risk 4 项 yes/no
>   evidence: [[batches/batch_086/judge|batch_086]], [[batches/batch_088/judge|batch_088]], [[batches/batch_089/judge|batch_089]], [[batches/batch_090/judge|batch_090]], [[_consolidation/findings/pattern_analyst/029]], [[_consolidation/findings/hypothesis_promoter/021]], [[lessons#Paper Transferability]]
> - 🆕 **Reserve revival 池 5 候选 (round 91 calibration asset-driven, 4+CP top 仅 1 边缘卡)** · dirs: tsrank_candlestick_ratio (b076/C005), institutional_flow_proxy (b072/C006), overnight_intraday_split (b080/C006 + b087/C001), anchor_proximity_momentum (b082/C002) → trigger-driven 永远漏掉的强候选 (单边卡 max_corr 0.44-0.56 cluster border / incr_ic NEG / alpha_surv 0.20 floor), 必须 asset-driven 显化. 每个 candidate 给具体 revival_path: Python residualize on cluster anchor / RHS basis swap / window sweep 30d-120d / evaluation horizon 1d→5d-20d / open-anchor 替 close-anchor / rank-diff form. **不动 config.yaml 阈值** — 复活靠改表达式. 优先级 b072/C006 (ls_t=-7.54 整库顶级) > b076/C005 > b087/C001 (evaluation horizon 工程成本中) > b080/C006 = b082/C002
>   evidence: [[batches/batch_072/judge|batch_072]], [[batches/batch_076/judge|batch_076]], [[batches/batch_080/judge|batch_080]], [[batches/batch_082/judge|batch_082]], [[batches/batch_087/judge|batch_087]], [[_consolidation/findings/calibration/013]]
> - 🆕 **Library gap: intraday microstructure 空白 + TTM 财务字段大空白 + 条件算子族空白 (round 91 library_gap)** · dirs: NEW intraday_microstructure_python proposed → 库内 27 admit 100% daily-bar, intraday primitive layer 工程已 untracked (src/data/primitive + src/research/compute/daily_python_backend.py 已 dev), 一旦 ready 是当前最大 unexplored 空间 (>100x scale-up); 同时 22 TTM 字段 + 27+ 基本面字段在库内仅 F002 用 $pb_ratio, ROE/ROA/毛利率/资产负债率/营收增长 完全 0 admit; 条件算子 (IfElse/Mask/Gt/Lt/Greater) 仅 F028 用 — 26 其它 100% 线性算术. 三族新空间各有 idea hint
>   evidence: [[_consolidation/findings/library_gap/019]], [[_consolidation/findings/library_gap/020]], [[_consolidation/findings/library_gap/021]]
> - 🟠 **P031 P008 完整 3 条件 (round 91 精细化, 从 round 75 圈定边界)** · dirs: range_structure (saturated), anchor_proximity_momentum (saturated), alpha191_universal_subset (saturated), price_conditional_amplitude (dead) → P008 escape mechanism 是 atom-specific 不是 wrap-pattern-general. 跨 4 batch 跨 4 方向 7 种变形全失败 (raw range / outer Std / cross-day envelope / Sum-of-product / CsRank wrapper / z-score / rank-conditional). 完整 3 必要条件: (a) atom 是 daily-resolution dim-less fraction-of-range ([0,1] bounded), (b) outer wrap 是 TsRank window ≥ 60d, (c) 几何脱 F025/F026 anchor cluster (max_corr<0.40). 三条件之一缺失即 fail. Phase 1 design 时 P008-stack 候选必须自检 max_corr@F025 + max_corr@F026 双检
>   evidence: [[batches/batch_083/judge|batch_083]], [[batches/batch_084/judge|batch_084]], [[batches/batch_086/judge|batch_086]], [[batches/batch_090/judge|batch_090]], [[_consolidation/findings/pattern_analyst/031]]
> - 🟠 **Cov ≈ Mean(X*Y, N) 等价律 P028 升格 hard rule (round 91)** · dirs: overnight_intraday_split (saturated), range_structure (saturated), anchor_proximity_momentum (saturated) → b087 C005 `Cov($open-Ref($close,1), $close-$open, 20) × Mean($amount, 120)` 与 F023 `Mean(Mul(o,i),20)` cross-section corr=**0.927** (>0.9 hard_gate fail). 数学: csi1000 daily zero-mean stationary return-pair 下 Cov=E[XY]-E[X]E[Y]≈E[XY]=Mean(X*Y). Phase 1 generator AST 自检 — candidate 含 `Cov(return_A, return_B, N)` + 库内已 admit 含 `Mean(A*B, M∈[N/2, 2N])` → design-time reject
>   evidence: [[batches/batch_087/judge|batch_087]], [[_consolidation/findings/pattern_analyst/030]], [[_consolidation/findings/hypothesis_promoter/022]], [[lessons#Path Selection]]
<!-- END HOT-TOPICS-LLM -->

## 🎯 方向总览 (Bases)

![[_bases/directions.base]]

## 📚 因子库 (Bases)

![[_bases/factors.base]]

## 📊 最近 Batch (Bases)

![[_bases/recent_batches.base]]

---

> [!abstract]- 系统状态
> - Round: **96** · Admitted: **28** · Active directions: **20**
> - Last batch: **batch_095**
> - Last consolidation: **—**
> - 格式 audit：运行 `research audit index` 检查漂移
