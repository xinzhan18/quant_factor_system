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

## Promising Unexplored

> 供 Phase 1 新开方向时参考。LLM 首轮启动时若 `INDEX.md` 里没有 `active/exploring` 方向，读这一段挑一个切入。Phase 5 consolidation 可补充或剪裁。

- _（尚未累积 —— 首批 consolidation 之后会从 `directions/*.md` 的 saturated / dead 条目反推"未走的路"写到这里）_
