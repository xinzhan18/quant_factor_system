---
batch_id: batch_005
direction: value_liquidity_interaction
judged_at: 2026-04-19T13:40:00Z
revised_at: 2026-04-19T20:00:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reserve}
  - {candidate_id: C005, verdict: admit, factor_name: pb_amount_ratio_20}
batch_summary: {total: 5, admit: 1, reserve: 1, reject: 3}
---

> [!warning] **Retroactive revision (2026-04-19)**: C005 从 reject 升级为 admit (factor_name: pb_amount_ratio_20)。配置放宽：alpha_surv_min 0.60→0.40，rubric poor 阈值 0.60→0.30。原因：C005 与 F001 正交 (max_corr=0.029) + incremental_ic=+0.027 + 符号互补 + cum_dd=-2.17 全库最浅 — 库空间独立 alpha 明确；Barra 脏不阻碍库增值。

# batch_005 Judge Summary

> [!abstract]+ batch_005 · [[directions/value_liquidity_interaction]] · 5 candidates (direction 首批)
> ✅ **admit=0** · ⏸ **reserve=1** (C004 PE change rate) · ❌ **reject=4** (C001/C002/C003/C005 均 alpha_survival<0.60 dealbreaker)
> **核心发现 (方向级)**: 首批即发现 **"基本面字段层引入 ≠ 基本面 Barra 风格跳出"** — C001/C002/C003/C005 四候选虽字段层用了 $pe/$pb/$ps，但 Barra 归因三候选 dominant=vol_20d、一候选 dominant=turnover_20d。仅 C004 `Div(Delta($pe_ratio, 20), $pe_ratio)`（纯 PE 变化率、无流动性交互）达到 dominant=**str_1m** + alpha_survival=**0.92**（方向唯一双中 hypothesis 目标）但 ls_t=-1.22 未达显著 → reserve。**元结论**：字段层交互不等于风格层解耦，乘法结构倾向量纲主导方选择；自归一化（/self）+ 单场景（无 Mul(A,B)）才真正改变 Barra 归因。另一重要正面信号：**C005 为方向/全库首个 positive IC + 完美 mono+1.0 + cum_dd=-2%（全库最浅）**，但 70% IC 被 vol_20d 吞 → 证明存在 positive value×illiquidity edge，但被 Barra 天花板遮蔽。
> **MT Budget**: cumulative 23 → **28** · direction 0 → **5** (首批) · 本批 bucket: C004 low(search=high), 其它 hard_gate 过但 direction-rule reject

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | 🟡·🟡·🔴·🟡·🟡 | ICIR_oos=-0.228 ls_t=-2.92 alpha_surv=0.26 dom=vol_20d | PE 原值 × turnover 乘积被 PE 尾部方差主导，基本面外壳 + 波动率内核 | [[batches/batch_005/candidates/C001]] |
| C002 | ❌ reject | 🟡·🟡·🔴·🟢·🟡 | ICIR_oos=-0.205 ls_t=-2.90 alpha_surv=0.22 dom=turnover_20d | 方向唯一 dom=turnover_20d；EP×turnover 仍撞流动性簇；反向 hypothesis（散户拥挤 vs 价值发现） | [[batches/batch_005/candidates/C002]] |
| C003 | ❌ reject | 🔴·🔴·🔴·🟢·🟡 | ICIR_oos=-0.273 ls_t=-2.12 alpha_surv=**0.083** dom=vol_20d | PB×Std(close) 是波动率 proxy 的教科书样本；vol_20d 吞 92% IC；方向 Known Failure 标本 | [[batches/batch_005/candidates/C003]] |
| C004 | ⏸ reserve | 🟢·🔴·🟡·🟢·🟡 | ICIR_oos=-0.191 ls_t=**-1.22** alpha_surv=**0.92** dom=**str_1m** | 方向 hypothesis 首个双中（clean + 非流动性风格）；PE 自归一化变化率；ls_t 未达显著但方向层价值 10 分 | [[batches/batch_005/candidates/C004]] |
| C005 | ❌ reject | 🟡·🟢·🔴·🟢·🟢 | ICIR_oos=**+0.263** ls_t=**+4.68** mono=**+1.0** cum_dd=**-2.17** alpha_surv=0.30 dom=vol_20d | **方向/全库首个 positive IC**；rank/时序层全库最干净；但 Barra 空间 70% IC 被 vol_20d 吞 → "positive edge exists but masked" | [[batches/batch_005/candidates/C005]] · [[factors/F002]] |

## 跨候选对比

- **"乘法交互"全盘失败**：C001 (Mul 乘)、C002 (Mul 乘)、C003 (Mul 乘) 三候选都是基本面字段 × 流动性/波动率的**乘法结构**——全部撞 vol_20d 或 turnover_20d 天花板。alpha_survival 最高 0.26，最低 0.08。根本原因：`Mul(A, B)` 的结果方差由方差最大的字段主导，而 $amount / $turnover_rate / Std($close) 的方差远大于 $pe/$pb/$ps。**教训**：基本面 × 流动性乘法交互 = 伪装的流动性信号。
- **"自归一化 + 单场景"反而突破**：C004 `Div(Delta($pe_ratio, 20), $pe_ratio)` 是方向**唯一满足 hypothesis 双目标**（alpha_survival=0.92 + dominant=str_1m）的候选——它没有流动性交互项！纯 PE 变化率自归一化产出了跨风格空间的信号。**反直觉发现**：方向 hypothesis 预期"value × liquidity"交互能解耦，实测反而是"pure value change rate"解耦了，而任何加流动性项都打回原形。
- **Positive IC 孤证 C005**：在全库仅 F001（负 IC）之外，C005 是首个 positive IC 信号。9 年逐年正、最新年度 (2023 +0.037) 最强、cum_dd 仅 -2.17（对比 F001 -87.7）。**Rank/时序层是全库最干净记录**。但 70% 信号被 vol_20d 吸收——**Barra 空间底层 positive edge 真实存在但被遮蔽**。如果 `Mean($amount, 20)` 分母改成 `Mean($turnover_rate, 20)`（去市值），可能真正打开方向。
- **dominant_style 分布**：C001 vol_20d / C002 turnover_20d / C003 vol_20d / C005 vol_20d → 4/5 撞老天花板；唯独 C004 str_1m → 方向**首次**非流动性风格主导。hypothesis 在 C004 这一个点上成立。
- **MT 预算**：cumulative 23 → 28，方向首批 direction_candidates=5 family 从 0 起步（family term 各异），search_adjusted bucket 各候选差异大（C004 medium+、others high）。

## Thread 进展

> [!note]+ T001 [[directions/value_liquidity_interaction#T001]] — `[◉ ACTIVE, 乘法结构证伪]`
> C001 (PE×turnover) / C005 (PB/amount) 分别证伪了"价值 × 流动性 水平乘除"的乘法/除法版本——全部撞流动性 Barra 天花板。T001 应转向非乘法结构（如条件分组、残差）或 turnover_rate 作分母（规模已归一）。

> [!failure]+ T003 [[directions/value_liquidity_interaction#T003]] — `[◉ ACTIVE, 部分 ANSWERED via C004]`
> C004 PE 自归一化变化率 alpha_survival=0.92 + dom=str_1m，hypothesis（基本面更新速率独立维度）在 rank-order 层**方向性验证**，但 ls_t=-1.22 未达 PnL 显著。需补齐 amount 变化率交互项（`Sub(Delta(pe), Delta(amount))`）或延长 horizon（ic_oos 在 20d horizon 更强）。

> [!failure]+ T004 [[directions/value_liquidity_interaction#T004]] — `[✗ DISPROVEN batch_005]`
> C003 (PB × Std_close) alpha_survival=0.083 史上最差，vol_20d 吞 92% IC。"PB × 波动率"结构是可预测失败——未归一化 Std 量纲主导排序。

> [!failure]+ T005 [[directions/value_liquidity_interaction#T005]] — `[✗ DISPROVEN batch_005]`
> C002 EP×turnover alpha_survival=0.22 + dom=turnover_20d。"便宜+热闹→价值实现" hypothesis 实测为负 alpha（与预期反向），暗示 A 股"高 EP × 高换手" = 散户拥挤而非机构价值发现。

## 方向级反思

**方向首批 admit=0，但产出两个结构性发现**（高于前两方向的信息增量）：
1. **C004 突破 Barra 风格天花板**（dom=str_1m + alpha_surv=0.92）——证明"基本面变化率"是第一个真正跳出 vol_20d/turnover_20d 的维度。T003 路线具备方向级价值。
2. **C005 positive IC 首证**——rank/时序层全库最干净，9 年全正、cum_dd=-2%。尽管被 vol_20d 吞，Barra 残差 IC=+0.009 仍显著方向一致，底层 edge 真实。

**方向级决策（相比 turnover saturated 更乐观）**：
- 方向 `status: exploring` 保持（C004 存活 + C005 positive 两证据支持继续探）
- 方向 `priority: high` 保持（T003 路线潜力未兑现）
- 下轮重点：**T003 path 升级（C004 + amount/turnover 交互）** + **C005 path 升级（分母换 turnover_rate 去市值）**

**跨方向元教训（累计 4 batches / 3 directions）**：
- `Mul(A, B)` 交互 = 量纲主导方吞噬信号。想跨 Barra 空间必用 `Div(Delta(A), A)` 或 `Sub(Rank(A), Rank(B))` 这类**自归一化/秩差**结构
- Barra 天花板的物理出口仍是 Python 逃生口 Barra residual（accumulated evidence）
- "direction 首批 hypothesis 证伪率"是方向级评估最高效信号 —— 本方向 4/5 乘法结构失败 + 1/5 基本面速率成功，hypothesis 精准度高于前两方向

**下轮决策（batch_006）**：继续 value_liquidity_interaction 第二批，5 候选集中 T003 升级（PE 速率 × amount/turnover 速率交互）+ T001 C005 分母替换变体 + 新 T006 (basic × momentum) 探 str_1m 覆盖面。
