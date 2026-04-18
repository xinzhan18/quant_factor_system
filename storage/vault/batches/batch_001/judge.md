---
batch_id: batch_001
direction: amount_volatility_signal
judged_at: 2026-04-18T14:45:00Z
candidates:
  - {candidate_id: C001, verdict: admit, factor_name: amount_cv_10}
  - {candidate_id: C002, verdict: reserve}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reserve}
  - {candidate_id: C006, verdict: reject}
  - {candidate_id: C007, verdict: reject}
  - {candidate_id: C008, verdict: reject}
batch_summary: {total: 8, admit: 1, reserve: 2, reject: 5}
---

# batch_001 Judge Summary

> [!abstract]+ batch_001 · [[directions/amount_volatility_signal]] · 8 candidates
> ✅ **admit=1** (C001→F{next}) · ⏸ **reserve=2** (C002, C005) · ❌ **reject=5** (C003, C004, C006, C007, C008)
> **核心发现**：T001 短窗口 CV（C001 `amount_cv_10`）是方向首个 anchor —— OOS IC=-0.040 / ICIR=-0.716 / ls_t=-3.78 / Mono_OOS=-1.0（完美）/ 9 年 IC 同号负；T002 T003 均 baseline 失败（skew/kurt 高阶矩噪声大、Log-Slope 数据发散、Corr 分位翻转），仅 C005 max/mean 比值勉强保留观察。**全批 8/8 候选 dominant_style=vol_20d**（crowding=medium），下轮必做 vol_20d orthogonalize。
> **MT Budget**: cumulative 0 → **8** · direction 0 → **8** · bucket `low`（首批空库）· search_adjusted bucket `high`（单批 8 候选密集搜索，记入 CP03 讨论）

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ✅ admit | 🟢·🟢·🟠·🟢·🟢 | ICIR_OOS=-0.716 ls_t=-3.78 Mono=-1.0 | 方向首个 anchor；短窗口 CV 作为资金参与稳定性真信号，但 vol_20d 暴露 24.5 需下轮 orthogonalize | [[batches/batch_001/candidates/C001]] · [[factors/F001]] |
| C002 | ⏸ reserve | 🟡·🔴·🔴·🟢·🟡 | ICIR_OOS=-0.214 ls_t=-0.85 | 60d 过于缓慢基线，IS 单调-1.0 OOS 崩至 0.0（"一桨驱动"）；证明 alpha 集中在短窗口，留作未来 orthogonalize 对照 | [[batches/batch_001/candidates/C002]] |
| C003 | ❌ reject | hard_gate | Mono IS=0.10 → OOS=-1.00 | CV 比值 IS 单调近零 OOS 突变负完美 —— 样本巧合非真机制；下轮先复核 ratio 构造 | [[batches/batch_001/candidates/C003]] |
| C004 | ❌ reject | hard_gate | IC_OOS=-0.0033 Mono 翻转 | $amount 20d skew：小样本高阶矩噪声大；T002 下轮改稳健尾部指标（top-k mean / 分位比） | [[batches/batch_001/candidates/C004]] |
| C005 | ⏸ reserve | 🟢·🟡·🔴·🟢·🔴 | ICIR_OOS=-0.539 Mono=-1.0 cum_ic_mdd=-73.7 | T002 thread 首条"信号完整"（严格单调 + 4 段同号），但 vol_20d 暴露 32.0 几乎吞噬信号，cum_ic_mdd=-73.7 暴露 regime 脆弱；正交化后重测 | [[batches/batch_001/candidates/C005]] |
| C006 | ❌ reject | hard_gate | Mono IS=0.60 → OOS=-0.70 | Corr(amount, Δclose, 20)：线性 IC 稳定但分位结构跨期翻转 —— 机制 regime-dependent；下轮改 abs(Δclose) 或换窗口 | [[batches/batch_001/candidates/C006]] |
| C007 | ❌ reject | hard_gate | coverage=0.327 | Log($amount) 遇 0 成交额发散 + NaN 传播压缩样本；改 Slope($amount/Mean($amount,20), 20) 归一化规避 | [[batches/batch_001/candidates/C007]] |
| C008 | ❌ reject | hard_gate | 四重失败（sign+ic_min+decay+mono） | Kurt 20d 样本太小噪声过大；T002 延长到 60d+ 或做条件 kurt | [[batches/batch_001/candidates/C008]] |

**档位编码**：🟢 最优档 · 🟡 次档 · 🟠 边际 · 🔴 阻断档 · `hard_gate` reject 不填档位色。

## 跨候选对比

- **Style 聚合**：**8/8 候选 dominant_style=vol_20d**（平均暴露 ~17，最高 C005=32.0）—— 这是本方向的结构性发现：`$amount` 的多数二阶统计量（CV / 偏度 / 峰度 / 尾部 / 趋势 / 相关）在 Barra 空间中都与 vol_20d 强共线。**下轮全方向议题：orthogonalize by vol_20d 后是否有残差 alpha**。
- **Thread 成败分层**：T001（C001/C002/C003）—— 短 CV 胜，长 CV 衰，比值"断层"被证伪；T002（C004/C005/C008）—— 仅 max/mean 比值（C005）是"信号完整"代表，skew 和 kurt 都是小样本噪声；T003（C006/C007）—— 两个 baseline 都因结构性问题挂掉（mono 翻转 / Log 发散），thread 需重设计算子族。
- **同批潜在冗余**：C001 (cv_10) 与 C005 (max/mean_20) 表达式不同但都是"20d 窗口的 amount 分散度"，且都 vol_20d 主导 —— 预期显著相关。首批 anchor rule：admit 档位更干净、IS/OOS 一致性更强的 C001；C005 留作 reserve 等 orthogonalization 验证。
- **MT 预算推进**：首批从 0 推至 direction_candidates=8，bucket 仍 `low`；但 search_adjusted.bucket 已到 `high`（raw=0.9），提示这一批次搜索密度已满，下批需收窄候选数 (≤5) 或切换 thread。

## Thread 进展

> [!success]+ T001 [[directions/amount_volatility_signal#T001]] — `[✓ ANSWERED batch_001]`
> admit C001 (cv_10)、reserve C002 (cv_60)、reject C003 (ratio)。回答 T001："$amount CV 在短窗口（10d）稳定产出 alpha，负号符号（CV 高 → 未来收益低）、9 年同号、mono_oos=-1.0 完美"；但子假设"短/长 CV 比值作为断层指标"被证伪（C003 hard_gate），说明 alpha 不来自比值结构而来自短窗口水平值本身。

> [!note]+ T002 [[directions/amount_volatility_signal#T002]] — `[◉ ACTIVE]`
> reserve C005 (max/mean_20)、reject C004 (skew)、reject C008 (kurt)。T002 thread 部分回答：高阶矩（skew/kurt）20d 窗口噪声过大不可用；仅尾部 max/mean 比值保留"真信号"体征但被 vol_20d 吞噬。**下一步**：对 C005 做 vol_20d 正交化（先 demean by Barra vol_20d 或 Std($close, 20) 再看残差 IC），同时 T002 新增探索延长 kurt 到 60d+ 或改 top-3/top-5 mean 的稳健变体。

> [!failure]+ T003 [[directions/amount_volatility_signal#T003]] — `[✗ DISPROVEN batch_001]` (partial)
> reject C006 (amount×Δclose corr)、reject C007 (log-slope)。两个 baseline 都因结构性问题挂掉：Corr 分位在 IS→OOS 翻号，Log-Slope 遇 0 成交额数据发散。T003 方向本身（价量方向一致性）未被证伪，但**当前算子实现被证伪**；下一步新建 T004 承接"非 NaN-safe 算子的替代实现"。

> [!note]+ T004 [[directions/amount_volatility_signal#T004]] 🆕 — `[◉ ACTIVE]`
> 承接 T003 的算子实现教训。新方向：`Slope($amount/Mean($amount,20), 20)` 归一化版本 + `Corr($amount, Abs(Delta($close, 1)), 20)` 幅度版本（放量即信息而非方向）+ 改窗口看 5d/60d Corr 稳定性。

## 方向级反思

- **方向当前状态**：`exploring → productive`（首次 admit 触发自动转换）。批次 admit 率 1/8 = 12.5%，略低于"首批初探"心理预期（20-30%），但 admit 质量高（C001 完美单调 + 9 年同号 + ICIR-0.72），单 anchor 已足够支撑方向立住。
- **Edge 评估**：T001 短窗口 CV 是 core edge，已确认；T002 尾部信号（max/mean 比值）可能是 vol_20d 变体，待正交化定性；T003 当前算子死路，T004 继续探索。**方向整体 edge 强度：medium，集中在 T001**。
- **下一批优先级**（降序）：
  1. **C005 正交化验证**：对 C005 做 `Resi(Div(Max($amount,20), Mean($amount,20)), Std(Log($close)-Ref(Log($close),1), 20))` 或类似 vol-orthogonalized 版本，看残差 alpha 是否独立于 vol_20d
  2. **C001 lookback 扫描**：cv_5 / cv_20 / cv_30，定位 ls_tstat 最大点；做 MAD 版本（抗离群值）
  3. **T004 新算子族**：归一化 slope + 幅度 corr
  4. **T002 稳健尾部**：top-3 mean / 分位比值 / 延长窗口 kurt
- **Saturated 阈值**：若下一轮 admit 率 < 10% 且无新 thread 推进，`status: productive → saturated`，方向休眠。
- **关键假设风险**：C001 的 cum_ic_max_drawdown=-87.7（本批唯一 <-50 红线），历史上存在显著失效段（推测 2021 小盘普涨 regime）。admit 不阻断但需监控；若下一轮出现类似 regime，此 anchor 需配对 regime-aware overlay 才能上盘。
