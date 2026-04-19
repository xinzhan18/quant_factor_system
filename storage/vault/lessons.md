---
version: 1
last_consolidated_at: 2026-04-18T00:00:00Z
source: re-seeded for new iteration (engineering facts only)
---

# Research Lessons

系统级硬事实。每次挖掘循环开始前必读。
由 Phase 5 CONSOLIDATION 周期性重写。**不要**在这里追加单 batch 的教训 —— 那些写在 `directions/{direction}.md`。

## Data Facts

- **Data split (不可违反)**:
  - Train: `[2015-01-01, 2021-12-31]`
  - Validation: `[2022-01-01, 2023-12-31]`
  - Holdout: `[2024-01-01, 2024-12-31]`（Phase 2 / Phase 3 **永远看不到**；只有 `research holdout-review` 能读）
  - 2025+：永不触碰
- **主 universe**：所有 CP01-CP06 判定都在 `csi1000` 上跑；`csi300` / `csi500` / `all` 仅作参考
- **`$vwap` 字段全零**：当前数据源未填 —— precheck 里禁用
- **`$amount` 有数据**（已确认）—— 可用
- **`index_constituents` 表**：2.7M 行，含 `csi300` / `csi500` / `csi1000` 每日成分
- **A 股约束**：不做空头 alpha。因子必须从多头侧产生 alpha
- **市值代理红线**：`abs(corr)` > 0.3 对 `$market_cap` 或 `$circ_market_cap` 的因子直接 reject

## Operator Registry

- **白名单唯一**：DSL 算子 / 字段必须出现在 `src/research/execute/precheck.py` 白名单里（single source of truth）
- **可用字段**：`$open, $high, $low, $close, $volume, $amount, $pe_ratio, $pb_ratio, $ps_ratio, $market_cap, $circ_market_cap, $turnover_rate`
- **自定义算子**（需要 `C.kernels = 1`）：`TsRank`, `TsMax`, `TsMin`, `TsAutoCorr`, `TsDecay`, `TsMomentum`, `RealizedVol`, `CsRank`, `CsZscore`, `CsDemean`, `AmihudIlliq`, `HHI`, `SignedPower`, `Tanh`, `Exp`, `Sigmoid`
- **不可用 / 禁用算子**：`Neg`（用 `Mul($x, -1)` 替代），`SMA`（用 `EMA` 或 `Mean` 替代）
- **横截面算子**（`CsRank`, `CsZscore`, `CsDemean`）无论挖掘 universe 是什么，始终在 `D.instruments("all")` 上计算

## Path Selection (DSL vs Python)

- **默认走 DSL**。用 Qlib 表达式语言写因子，除非 DSL 表达不出来
- **Python 逃生口（R8）** 的触发条件：
  - 想法需要非平凡的循环，而 DSL 无法向量化（少见）
  - 想法需要 DSL 表达不了的横截面操作
  - 想法是对已发表 Python 参考实现的显式复刻
- **Python factor 契约**：
  - 函数签名：`def compute(df: pd.DataFrame) -> pd.Series`，df 的 MultiIndex 是 `(time, symbol)`
  - 模块级必须声明 `REQUIRED_FIELDS: list[str]` 和 `VECTORIZED: bool = True`
  - 必须是纯函数（不碰 I/O / DB / 网络）
  - 导入白名单：`numpy`, `pandas`, `scipy`；禁用：`subprocess`, `os`, `sys`, `eval`, `open`

## Structural Constraints

- **禁走市值捷径**：与 `$market_cap` 或 `$circ_market_cap` 强相关（`|corr| > 0.3`）的因子直接 reject —— 那是 size-factor 代理，不是 alpha
- **禁看 holdout**：Phase 2 / Phase 3 代码永远不能读 2024 年数据。Holdout 物理隔离在 `storage/_holdout_private/`
- **向量化（R5）**：禁止对行 / 日期 / 标的的 `for` 循环。用 `groupby` / broadcasting / `einsum` / `np.linalg.pinv`。同样禁用：`groupby.transform`（隐式按日期 for 循环）。标准套路：long → wide pivot → 在 `(n_dates × n_symbols)` 矩阵上做 row-level numpy 运算 → wide → long
- **Barra residual 基线**：因子 alpha 是在**剥离 Barra 风格暴露之后**度量的，不是之前。`style_r²` 和 `alpha_survival` 是 CP04 Risk Cleanness 的核心指标
- **冗余红线（CP05）**：对已 admitted 因子的 `max_lib_corr > 0.70` 直接 reject
- **Python 因子必须进 library 对比（2026-04-20 修复）**：`data_bridge.load_library_signals` 历史上只加载 DSL 因子，Python 因子被完全跳过 —— 后果是 F005 作为 F004 的 bit-for-bit 复刻，相关度检查时找不到 F004，`max_lib_corr=0.15` 通过 near_duplicate gate。修复后 Python 因子也按 `sha256(源码)` 缓存进库。教训：任何护栏新增源类型时，redundancy / incremental_ic / 指标计算三条路径都要同步覆盖，否则"首个新类型 admit"之后的复刻必然漏网
- **Sample policy 版本**：在 `config.yaml` 里升级 `sample_policy_version`（例如 `v3 → v4`）会重置 7.MT 多重检验预算的 `validation_exposure` 计数。不要轻易升

## Language Policy

所有 LLM 生成的 vault 文档（INDEX / directions / judge / candidates / factor reports / narrative logs）按如下规则写，**保持 vault 风格一致**：

- **叙事主体：中文**。Hypothesis / Current Focus / Narrative Log / 反思 / verdict 理由 / 跨候选对比 / Thread 推理全部用中文写
- **术语保留英文**：IC / ICIR / Sharpe / Barra / monotonicity / style_r² / alpha_survival / long_short / hard_gate / mt_bucket / admit / reserve / reject / exploring / productive / saturated / aligned / strong / stable 等技术词和档位词不翻译
- **YAML / frontmatter 值：英文 snake_case**（机器优先，`direction_tag: volume_price_signal` 不是 `方向标签: 量价信号`）
- **Markdown 结构标题：英文**（`## Hypothesis` / `## Threads` / `## Current Focus` / `## Known Failures` / `## Narrative Log` / `## Related` / `## CP01` – `## CP06` 保持英文，Obsidian 导航 / audit grep 稳定）
- **例外**：INDEX.md 上半段的段落标题（`## 活跃方向` / `## 最近 Batch` / `## 因子库`）用中文 —— 这是人看的总览页，不是机器抓取

混用原则：段落内部可以自然夹英文术语（"CP04 alpha_survival=0.388 触发 dealbreaker，本候选的 edge 大头被 vol_20d 吸收"），但不要整段英文 prose 夹杂整段中文。

## Metric Semantics (消歧陷阱)

- **`ic.half_life_days`** —— **IC 衰减**半衰期。从多 horizon 的 train IC 曲线拟合出来，单位 = 持仓 horizon 天数。回答：alpha 随持仓期拉长衰减多快？
- **`feasibility.signal_half_life`** —— **signal 自相关**半衰期。每只标的的信号 ACF 在首阶跌到 0.5 的滞后，单位 = 交易日。回答：信号本身有多粘？
- **二者不可互换**。遗留的单名 `half_life` 字段已 deprecated

## Threshold Calibration (自纠错机制)

> Thresholds 不是公理，是**可证伪的经验值**。系统运行中如果发现自己在**系统性地错杀**某一类候选，必须主动触发阈值校准——这是避免"本地最优陷入局部搜索死循环"的关键机制。

### 何时触发（trigger conditions）

任一满足即应审视当前阈值是否过严：

1. **连续零 admit 警戒**：同方向 ≥ 3 批次 0 admit 且每批有 reserve 候选时，检查 reserve 候选中是否存在"rank-order 完美 + 库空间独立"但被**单指标 dealbreaker** 杀掉的；
2. **Reserve 积压**：累计 reserve / 累计 judged > 40% 且零 admit — 意味着系统对"信号真实但有结构瑕疵"过度保守；
3. **库规模停滞**：累计 batches ≥ 5 但 library size 未增 — 检查 reject 理由是否都指向同一个硬规则（自设的 direction-level 规则嫌疑最大）；
4. **悖论复现**：同一"反直觉指标组合"在 ≥ 2 个候选上独立出现（如 "低 style_r² + 低 alpha_survival"），说明单指标阈值不能表达问题全貌。

### 为什么放宽（the rationale）

- **Barra-clean ≠ library-clean**：rubric CP04 测的是与 **Barra 7-basis 的几何关系**；CP05 测的是与**已 admitted 因子的几何关系**。两者正交维度不同——**低 alpha_survival 但库内正交（max_corr<0.3 + incremental_ic>0.01）的因子是有库增值的**。
- **Portfolio-level orthogonalization**：多因子组合构建时 Barra 暴露可在 portfolio 层中和；单因子 Barra 脏不等于不可用。
- **"Static orthogonal vs dynamic orthogonal" 悖论**：低 `style_r²` 说明因子值横截面 ⊥ Barra basis；低 `alpha_survival` 说明 IC 生成的 L/S weights ∈ span(Barra)。两者可共存 — 对 library 增值判断的优先依据是**符号互补性 + 相关正交性**，不是 Barra residual 纯度。
- **硬规则 auto-reject 粒度过粗**：`alpha_survival < X 一律 reject` 会把 "rank 完美 + 9 年同号 + 符号唯一" 的真实 alpha 与"regime-dep 跨期翻号"同等处理——失去判断分辨率。

### 如何执行（remediation procedure）

**Step 1 — 诊断（识别被错杀候选）**

```bash
# 扫描 reserve + reject 中触 single-dealbreaker 的候选
# 手动 grep：reject_reason_short 只含 alpha_survival / dom_style 等单项触发
# 并同时检查 CP05 max_lib_corr < 0.30 + incremental_ic > 0.010
```

识别标志：
- `max_corr@admitted < 0.30` 且 `incremental_ic > 0.010`（库空间独立）
- `monotonicity_oos` 绝对值 ≥ 0.8（rank-order 真实）
- `sign_consistency = 1.0` + `cum_ic_mdd` 相对 library 中位数更浅（时序稳健）
- reject_reason 只指向单一指标（如仅 `alpha_survival<threshold`）

**Step 2 — 阈值调整**（若诊断命中）

按影响范围由小到大：

```
direction-level 自设硬规则（direction.md Hypothesis）
       ↓ 第一步删除
rubric 档位阈值（candidate-rubric.md CP04 tier boundaries）
       ↓ 第二步调整
全局 config 阈值（config.yaml.thresholds.alpha_surv_min 等）
       ↓ 第三步兜底
```

**只调必须调的一层**。先删 direction 自设硬规则（通常过严）；仍不够再调 rubric 档位；最后才改 config。每调整后必须同步更新三处：
- `storage/config.yaml`（如果 config 级）
- `.claude/skills/factor-judge/candidate-rubric.md` CP04 表（如果 rubric 级）
- `storage/vault/directions/{direction}.md` 结构性约束（删除自设硬规则）

**Step 3 — 追溯 admit（retroactive admission）**

对诊断步骤中识别的真实被错杀候选：

```bash
# 1. 更新 batches/batch_{N}/judge.md frontmatter: verdict reject → admit + factor_name
# 2. 更新 batches/batch_{N}/candidates/C{id}.md frontmatter 同步
# 3. 在 batch md 顶部加 [!warning] Retroactive revision callout 说明放宽依据
# 4. 重置 state 到该 batch 重跑 archive:
PYTHONPATH=src python3 -m research state set current_batch batch_{N}
PYTHONPATH=src python3 -m research state set current_batch_phase judged
PYTHONPATH=src python3 -m research archive batch_{N}
# 5. archive 后 state.last_batch 会被覆盖为 batch_{N}；手动复原到原 last_batch
# 6. dispatch /factor-report F{new_id} subagent 生成深度报告
# 7. 验证 vault/factors/F{new_id}.md > 0 且含 '# F{new_id}' H1
```

**Step 4 — 审计 + 防止回归**

- 更新 `lessons.md` 末尾 Narrative Log（此节）记录本次校准的触发原因 + 新阈值
- 追加到 `direction.md` Narrative Log 说明"本方向追溯 admit F{id} 原因 + 新规则"
- 下次 Phase 5 consolidation 若看到本节"已稳定运行 N 轮"可升格为正式 Data Facts；若新阈值又出现系统性错杀，再次触发校准循环

### 绝对不做的事（anti-patterns）

- **不放宽 hard_gate**（coverage / sign_flip / ic_oos_min / mono_flip / near_duplicate）— 这些是 CP01 硬闸，代表数据质量 + 结构完整性的物理边界，放宽=让垃圾入库
- **不放宽市值代理红线** `|corr($market_cap)| > 0.3` — size factor 已占 Barra basis，放宽=双重计数
- **不放宽 holdout 保护** — 任何阈值调整不能让 Phase 3 代码读 2024 数据
- **不机械地在"连续零 admit"就放宽** — 必须先**诊断**是否真的是"错杀"而非"信号确实都不够好"；混淆这两种情况 = 库质量稀释

### 历史校准记录

- **2026-04-19** (R1 → R1-relaxed): `alpha_surv_min` 0.60 → 0.40；rubric CP04 poor 阈值 0.60 → 0.30；删除 value_liquidity_interaction direction.md 自设 "alpha_survival<0.60 一律 reject + dom=vol_20d 也 reject" 硬规则。触发：batch_005-007 连续 3 批 0 admit + reserve 积压率 60% + 诊断到 C005_b5（max_corr@F001=0.029 / incremental_ic=+0.027 / mono=+1.0 / cum_dd=-2.17 全库最浅 / 9 年全正 / 符号互补 F001）被单指标 alpha_survival=0.30 dealbreaker 错杀。追溯 admit 为 F002 `pb_amount_ratio_20`。

## Promising Unexplored

> 供 Phase 1 新开方向时参考。LLM 首轮启动时若 `INDEX.md` 里没有 `active/exploring` 方向，读这一段挑一个切入。Phase 5 consolidation 可补充或剪裁。

- _（尚未累积 —— 首批 consolidation 之后会从 `directions/*.md` 的 saturated / dead 条目反推"未走的路"写到这里）_
