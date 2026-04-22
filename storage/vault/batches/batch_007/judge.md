---
batch_id: batch_007
direction: value_liquidity_interaction
judged_at: 2026-04-19T14:10:00Z
candidates:
  - {candidate_id: C001, verdict: reserve}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reserve}
  - {candidate_id: C004, verdict: reserve}
  - {candidate_id: C005, verdict: reject}
batch_summary: {total: 5, admit: 0, reserve: 3, reject: 2}
admit_count: 0
reject_count: 2
reserve_count: 3
candidate_count: 5
---

# batch_007 Judge Summary

> [!abstract]+ batch_007 · [[directions/value_liquidity_interaction]] · 5 candidates
> ✅ **admit=0** · ⏸ **reserve=3** (C001 合成 / C003 rank-diff PB / C004 60d-norm) · ❌ **reject=2** (C002 hard_gate sign_flip+decay, C005 alpha_surv=0.097 extreme)
> **重大发现**: **C005 `Div(PE_rate, turnover_rate)` 首次把方向 ls_t 推过 2 显著阈值**（ls_tstat_oos=**-2.92**, ICIR=-0.284, mono=-0.9, 9 年全负零翻转, cum_dd=-19.06）——rank-order 层 hypothesis 完全成立。**但 alpha_survival=0.097 极端**：这是 C004_b6 "低 style_r² (0.016) + 极低 alpha_survival" 悖论的**第 2 次独立复现**——证实**结构性机制**而非孤立故障。几何解释：self-normalized rate 的因子值横截面 ⊥ Barra basis，但其 IC 生成的 L/S weights 落在 Barra span 内 = "**static orthogonal ≠ dynamic orthogonal**"。合成 (C001) + rank-diff (C003) 各自局部优化但 PnL 天花板未破；60d-norm (C004) 与基线同强度。**DSL 边界已到**，方向下一步必须转 Python 逃生口 (方案 D / R8)。
> **MT Budget**: cumulative 33 → **38** · direction 10 → **15** · 本批 bucket 多为 medium+high，search 预算显著增加

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ⏸ reserve | 🟢·🔴·🟡·🟢·🟡 | ICIR=-0.197 ls_t=-1.27 alpha_surv=**0.86** dom=str_1m | 三基本面 rate 等权合成未改善 PnL；Q5 一桨驱动非合成可救；DSL 合成天花板标本 | [[batches/batch_007/candidates/C001]] |
| C002 | ❌ reject | hard_gate | sign_flip IS=-0.003/OOS=+0.021 + oos_decay=-5.95 | PE rate × turnover level 秩差 IS 无信号 OOS regime shift；非对称秩差结构失败 | [[batches/batch_007/candidates/C002]] |
| C003 | ⏸ reserve | 🟡·🔴·🟡·🟢·🟡 | ICIR=+0.107 ls_t=+0.33 alpha_surv=**0.71** (0.28→0.71 2.5×) dom=vol_20d | 秩差把 alpha_survival 拉升 2.5× 但 raw IC 削弱到 1/3；"秩差消 Barra 但削信号"权衡 | [[batches/batch_007/candidates/C003]] |
| C004 | ⏸ reserve | 🟢·🔴·🟢·🟢·🟢 | ICIR=-0.189 ls_t=-1.21 alpha_surv=**0.86** dom=str_1m | 60d-norm 稳化 CP04 但不改 PnL 瓶颈；"分母工程边际失败"诊断 | [[batches/batch_007/candidates/C004]] |
| C005 | ❌ reject | 🟡·🟢·🔴·🟢·🟢 | ICIR=**-0.284** ls_t=**-2.92** mono=-0.9 alpha_surv=**0.097** style_r²=**0.016** | **首次 ls_t>2 里程碑**，但"静态正交 vs 动态正交"悖论：因子值 ⊥ Barra，IC weights ∈ span(Barra) | [[batches/batch_007/candidates/C005]] |

## 跨候选对比

- **里程碑 1：首个 ls_t>2 信号**（C005）— 方向 15 候选首次跨过 PnL 显著阈值。但与 alpha_survival=0.097 极端 poor 并列 → 信号真实但 Barra 完全吃掉可交易残差。
- **悖论复现（C004_b6 + C005_b7）**：两次独立出现"低 style_r² (0.08 / 0.016) + 极低 alpha_survival (0.0009 / 0.097)"组合，**结构性机制**。几何含义：self-normalized rate 的因子值 cross-sectional 与 Barra 7-basis 近似正交（static），但 IC 生成的 L/S portfolio weights 落在 Barra span 主平面内（dynamic）。即"静态因子正交 ≠ 动态 alpha 正交"。
- **合成 (C001) 的天花板**：三基本面 rate 等权平均维持 alpha_survival=0.86 + dom=str_1m 但 ls_t=-1.27 ≈ 三单 rate 中位。Q5 一桨驱动不是"合成稀释"可修复的——而是 DSL 等权加权的**统一短端 alpha**缺失。
- **Rank-diff (C003) 的权衡**：alpha_survival 从 0.28 拉到 0.71（2.5×），但 raw IC 从 0.032 削到 0.011（1/3）。**Barra 吞噬与 raw signal 强度的定量 trade-off** 被清晰量化：消除 Barra 吞噬必须削弱 raw signal。
- **60d-norm (C004) 的边际**：分母从 $pe → Mean($pe, 60) 改善 extreme_ratio (0.014→0.0153 borderline→borderline) 但不改 PnL ls_t（-1.22→-1.21）。**分母工程已触底**。
- **C002 非对称秩差失败**：PE rate rank - turnover level rank 在量纲不匹配时 IS 信号归零，OOS 量级 6× IS 且反号 → regime-contingent 而非"delayed emergence"。rank-diff 必须两侧同级量纲（两 level 或两 rate）。
- **MT 预算**：cumulative 33→38（仍 low），direction family term 升至 ~0.55（基本面 rate 族已投 10/10）；下一批必须换结构。

## Thread 进展

> [!failure]+ T006 [[directions/value_liquidity_interaction#T006]] — 合成子路径 `[◉ ACTIVE, DSL 合成 PnL 天花板]`
> C001 三基本面 rate 等权合成 alpha_survival=0.86 保持 + PE/PB/PS 通用性再验证，但 ls_t=-1.27 未改善。**DSL 等权合成不产生信噪比增益**（Q5 一桨驱动是单边结构）。复活需 Python 逃生口做加权 residual 合成。

> [!failure]+ T001 [[directions/value_liquidity_interaction#T001]] — rank-diff 子路径 `[◉ ACTIVE, 部分成立]`
> C003 秩差结构把 alpha_survival 2.5× 改善（0.28→0.71）但 raw IC 削弱到 1/3；C002 非对称 rank-diff 失败。**秩差只降吞噬不消灭**（dom=vol_20d 仍违反方向硬闸）。复活需 Python Barra residual + 秩差组合。

> [!failure]+ T003 [[directions/value_liquidity_interaction#T003]] — 两 rate 除法子路径 `[◉ ACTIVE, 首个 ls_t>2 但悖论]`
> C005 Div(PE_rate, turnover_rate) 首次把方向 ls_t 推过 2 + 9 年全负零翻转，**rank-order 层突破**；但 alpha_survival=0.097（悖论第 2 次复现），**"静态正交 ≠ 动态正交"**。DSL 无法解决；transition to 方案 D。

## 方向级反思

**方向达到 DSL 空间边界**。4 batches / 15 候选 / 0 admit，但产出**三项里程碑发现**（信息密度远超前两方向）：
1. **T006 三点通用性**（batch_006）：基本面字段 `Div(Delta(X),X)` 速率跨 PE/PB/PS 普适跳出 vol_20d
2. **rank-diff 权衡定量**（batch_007）：alpha_survival 2.5× 改善 vs raw IC 1/3 削弱
3. **首个 ls_t>2 signal + 静态-动态正交悖论**（batch_007）：rate ratio 结构产出可交易 PnL 但被 Barra 完全吃掉残差

**R8 触发条件累积完成**：Python 逃生口做 Barra residual 不再是"可选优化"，而是"**唯一可推进路径**"——所有 DSL 结构化尝试（乘法、除法、合成、秩差、分母工程、两 rate 除法）均已被系统性证伪或触悖论。下批 batch_008 必须进入方案 D：实现 Python 逃生口做 C004_b5 + C001_b7 + C005_b7 三候选的 Barra residual，验证残差化后 PnL 是否兑现。

**status: exploring 保持**（rank-order 层突破 + 里程碑持续产出，不降 saturated）；priority 保持 high。

**下轮决策（batch_008）**：
1. 切换到 Python 逃生口（R8 - lessons.md "Path Selection" 明确支持该路径）
2. 实现 3 个候选的 Barra residual 版：
   - C004_b5 PE rate residual（alpha_surv 0.92 baseline → 残差后 Barra exposure 应降为 0）
   - C001_b7 三基本面 rate 合成 residual（Q5 一桨驱动观察是否解除）
   - C005_b7 两 rate 除法 residual（悖论是否消解）
3. 如果残差版 ls_t>2 + alpha_survival 保留 → admit 方向首个 F{id}
4. 如果残差版 ls_t 仍<2 → 方向 `saturated`，转向开辟第 4 方向（如 momentum × fundamental）

**跨方向元教训（累计 6 batches / 3 directions / 38 候选）**：
- **DSL 空间对 vol_20d 天花板已探尽**：乘法、除法、合成、秩差、自归一化、分母工程全部尝试
- **rate 族独立 alpha 存在且真实**：C005_b5 positive IC + C005_b7 ls_t>2 + cum_dd 全库最浅三重证据
- **Barra 吞噬是几何性而非代数性**：静态 ⊥ 不保证动态 ⊥，需 Python residual 物理剥离
