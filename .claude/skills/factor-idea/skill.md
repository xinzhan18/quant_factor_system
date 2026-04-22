---
name: factor-idea
description: Phase 1 START+DESIGN — 选方向、设计候选、冻结 manifest
user_invocable: true
---

# /factor-idea — Phase 1 START+DESIGN

## 职责 & 产出

| 谁 | 做什么 |
|---|---|
| **LLM** | 读 INDEX → 选 direction → 定 batch_goal → 设计 5-10 候选（DSL 优先） |
| **Python** | 刷新 INDEX 下半段 → DSL 白名单验证 → Python AST 检查 → 冻结 manifest |

产出：
1. `vault/directions/{direction}.md`（若新建方向）
2. `batches/batch_{N}/manifest.yaml`（冻结候选清单）

**一个 batch 对应一个 direction**。跨方向融合 → 新开 direction，不混 batch。

**Paper intake 边界**：`/factor-idea` 不直接读 PDF 或 raw extract。若方向来自外部论文，先跑 `/factor-paper` 产出 `vault/papers/{paper_slug}.md` 与 `vault/directions/{tag}.md`，再由本 skill 消费 direction。

---

## 流程

### Step 1 — Python: snapshot vault（**必做**）

```bash
PYTHONPATH=src python3 -m research memory snapshot --recent 10
```

输出三张聚合 markdown 表（方向 / 因子库 / 近 10 batch），filter 语义与 Obsidian Bases 完全一致 —— 这是 LLM 看 vault 状态的**唯一入口**。INDEX.md 本身只有 Bases embed（给人看的，Read 读不到数据），不用再去读它的 body。

### Step 2 — LLM: select direction

1. 从 Step 1 的方向表里选目标 direction：优先 `status=productive/exploring` 且 `rounds` 最少；若无，读 `vault/lessons.md` 的 "Promising unexplored"（若有）或 **LLM 自判新开**
2. 跟随 wikilink 读 `vault/directions/{direction}.md` 全文。**按优先级看**：
   - `## Final Conclusion`（若存在）—— dead/saturated 方向的**元教训**，一眼判断假设是否已封闭
   - `## Threads` → 每个 `### T{n}` 的状态标签 + `**Evidence trail**` bullet（bullet 里 `[[batches/.../candidates/C{id}]]` 可点进去看 6-CP 深度判决，**候选设计有疑惑时必钻进去**）
   - `## Known Failures` —— 已 reject 候选的 pattern，避免重复
   - `## Related` —— 横向邻近方向列表（下一步 §3 的扫描入口）
3. **Adjacent scan（避免重造轮子）**：Step 1 方向表里凡是信号族跟你目标重叠的 🔴 dead / 🟡 saturated direction，**都要读其 `## Final Conclusion` + `## Known Failures`** 再设计。典型触发：
   - 设计 return/momentum 类 → 扫 `asymmetric_momentum`、`return_momentum_acceleration`、`return_distribution_signals`
   - 设计 volume/turnover 类 → 扫 `vol_shock_signals`、`liquidity_acceleration`、`turnover_structural_signal`
   - 任何时候点开 `## Related` 里的近邻条目
4. 需要看 insight / 系统状态：`Read vault/INDEX.md`
5. 若新建方向：创建 `vault/directions/{tag}.md`，结构见 §Direction.md schema

**语义约定（Thread 状态标签的权重）**：
- `[◉ ACTIVE]` → 可延续，设计类似候选前先看最新 Evidence trail
- `[✓ ANSWERED batch_X]` → 机制已确认，不需要再测相同形式
- `[✗ DISPROVEN batch_X]` → **该机制空间已封闭**，换角度或换字段，**不要**重设计同形状候选

### Step 3 — LLM: decide batch_goal + active threads
- `batch_goal` — 本 batch 要验证什么（≥30 chars，Python 审计长度）
- `active_threads_referenced: [T001, T002, ...]` — 本 batch 推进的 thread 编号

### Step 4 — LLM: design 5-10 candidates

**设计前的最后一道反射（R2 纪律，防止重造轮子）**：对每个候选，都必须能回答：
1. 本候选机制对应当前 direction 的哪个 **`[◉ ACTIVE]` thread**？（如对应 `[✗ DISPROVEN]` thread，**禁设计**；如跨 thread，在 rationale 里说明）
2. Step 2.3 adjacent scan 里有没有邻近 direction 已经 disprove 了同形状的候选？有则说明本候选如何绕开（换字段 / 换算子结构 / 换条件）

**DSL 优先（R8）**。Python escape hatch 仅限：
- DSL 无法表达的非平凡循环
- 复现已发表论文的 Python 参考实现
- 需跨截面但 DSL 没有对应算子

每个候选字段见 §Manifest schema `candidates[]`。**不看 validation 数据设计候选** — 基于 hypothesis + 先验知识，不基于回测结果。

### Step 5 — Python: validate
- **DSL 候选**：§DSL whitelist 检查算子/字段、表达式嵌套深度 ≤ 10；canonical 去重（交换律算子参数字典序排序）对比 admitted factors + 同 batch 内其他候选（retired 可重投）
- **Python 候选**：§Python contract 检查 AST import + 模块契约

### Step 6 — Python: freeze manifest（**一步到位**）

LLM 把 Step 2-4 的决策写成一个 spec 文件（任意临时路径），再调 CLI：

```bash
# spec.yaml 示例
cat > /tmp/p1_spec.yaml <<'YAML'
direction: volume_price_signal
batch_goal: "Baseline T001/T002/T003 on CSI1000 at 20d lookback: ..."   # ≥ 30 chars
active_threads_referenced: [T001, T002, T003]
candidates:
  - candidate_id: C001
    source_type: dsl
    expression: "Corr($close, $volume, 20)"
    rationale: "T001 baseline"
  - candidate_id: C002
    source_type: python
    path: "batches/batch_XXX/python_candidates/C002.py"   # 事先写好
    rationale: "..."
YAML

PYTHONPATH=src python3 -m research phase1 freeze /tmp/p1_spec.yaml
```

`research phase1 freeze` 内部做完这一整串：
1. `state.next_batch_id()` 自动分配 `batch_NNN`
2. `state.begin_batch()` 把 phase 从 `null` 推到 `designed`（若非 idle 立即 `InvalidPhaseTransition`）
3. 创建 `batches/batch_NNN/` + `candidates/` 子目录
4. `freeze_manifest()` 走全部白名单 / AST / canonical 去重 / `batch_goal` 长度校验
5. 写 `manifest.yaml`（见 §Manifest schema，全字段：`round / created_at / sample_policy / direction_md_ref / frozen_at / active_threads_referenced / candidates[]`）
6. `refresh_index()` 刷 INDEX 下半段

**任何一步失败**（候选不过白名单、batch_goal 太短、direction.md 不存在）→ state 自动回滚到 idle，LLM 可改 spec 重跑。**不需要 LLM 手写 Python**。

---

## Direction.md schema

### Frontmatter

```yaml
---
direction_tag: fundamental_price_divergence
status: exploring            # exploring | productive | saturated | dead | merged
priority: high               # high | medium | low
rounds: 0                    # Python auto
admits: 0                    # Python auto
last_batch: null             # Python auto
last_admits: []              # Python auto — F{id} list admitted in last_batch
last_goal: null              # Python auto — batch_goal of last_batch (human ref)
last_activity: null          # Python auto
created_batch: batch_099
members: []                  # Python auto
merged_into: null            # 仅 status=merged 时有值
---
```

| 字段 | 谁更新 | 何时 |
|---|---|---|
| `direction_tag` / `created_batch` | LLM | 新建时（不变） |
| `priority` / `merged_into` | **LLM** | Phase 4 Narrative Log 或 Phase 5 重写 |
| `status` | **Python auto** 首次 admit → `exploring → productive`；其余（`productive → saturated / dead / merged`）由 **LLM** 在 Narrative Log 翻 |
| `rounds` / `admits` / `members` / `last_batch` / `last_admits` / `last_goal` / `last_activity` | **Python** | Phase 4 archive 后自动 |

### Body（LLM 完全维护）

```markdown
## Hypothesis
<经济学逻辑 2-3 段>

## Current Focus
<当前最值得探索的角度 + 下一步计划>

## Threads
### T001: <子问题> [◉ ACTIVE]
**Question**: <1-2 句完整问题陈述>
**Evidence trail**:
- batch_101: C003 → style_r2=0.12（太脏）
- batch_102: C004 → style_r2=0.08（acceptable）
**Next probes**: ...

### T002: <子问题> [✓ ANSWERED batch_103]
**Question**: ...
**Answer**: ...
**Evidence trail**:
- batch_103: C001 → admit F{id}

## Known Failures
- <已证伪的 pattern + 为什么>

## Related
- [[../lessons#Structural Constraints]]
- [[<related_direction>]]

## Narrative Log
### 2026-04-11 batch_103
<admitted / rejected / thread 状态变化 / 下一步>
```

### Thread 约定

Thread = direction body 中的 `###` 子节，跨多 batch 逐步回答的开放问题。

| 状态 | 含义 | spelling（固定，c20 硬检查） |
|---|---|---|
| `[◉ ACTIVE]` | 正在探索 | 无 batch 编号 |
| `[✓ ANSWERED batch_X]` | 已回答（admit 或 conclusive refute） | 带 batch 编号 |
| `[✗ DISPROVEN batch_X]` | 子假设被证伪 | 带 batch 编号 |

**Thread block 三件套（audit c20 硬检查，仅对被本 batch 候选引用的 thread 生效）**：

1. H3 行带上表三个状态标签之一
2. Body 有 `**Question**:` 行
3. Body 有 `**Evidence trail**:` 标题（**禁用** bare `**Evidence**:`）

**Thread 完全由 LLM 维护**——Python 不管理 thread 状态/数量/内容，只 audit 三件套形状 + `thread_id` 存在（c16）。LLM 在 Phase 1 创建，在 Phase 3 更新 evidence 与状态标记。

### Direction 生命周期

| 状态 | 定义 | 转换条件 |
|---|---|---|
| **exploring** | 新方向，未 admit | 首次 admit → productive |
| **productive** | 有 admit，持续产 alpha | 连续 2+ batch reject > 80% → saturated |
| **saturated** | ROI 低 | 发现新角度 → productive（可复活）|
| **dead** | 假设被证伪 | **不可逆** |
| **merged** | 并入他方向 | 设 `merged_into: {target_tag}` |

LLM 改 frontmatter（Narrative Log 写理由），Python 只校验值合法。

---

## Manifest schema

```yaml
batch_id: batch_103
round: 5
created_at: "2026-04-11T14:30:00+08:00"
direction: fundamental_price_divergence
direction_md_ref: vault/directions/fundamental_price_divergence.md
batch_goal: "验证 80d lookback 是否减少 C004 triple product crowding..."
active_threads_referenced: [T001, T002]
sample_policy:
  train_start: "2016-01-01"
  train_end: "2023-12-31"
  test_start: "2024-01-01"
  test_end: "2024-12-31"
candidates:
  - candidate_id: C001
    source_type: dsl
    expression: "Mul(Corr($close, $volume, 20), Std($volume, 20))"
    rationale: "测试 PV 相关性 × 波动率交互信号"
    # 可选承袭字段：
    # parent_batch: batch_102
    # parent_candidate_id: C004
    # transformation: "extend_lookback_60d_to_80d"
  - candidate_id: C002
    source_type: python
    python_ref: "batches/batch_103/python_candidates/C002.py"
    dependencies: [numpy, pandas]
    rationale: "复现论文中的 cross-sectional dispersion 因子"
frozen_at: "2026-04-11T14:31:00+08:00"
```

---

## DSL whitelist

**字段**：`$open $high $low $close $volume $amount $pe_ratio $pb_ratio $ps_ratio $market_cap $circ_market_cap $turnover_rate`

**算子**：
- 数学/逻辑：`Add Sub Mul Div Abs Log Power Sign Not And Or Eq Ne Gt Ge Lt Le`
- 滚动统计：`Mean Std Var Skew Kurt Med Mad Sum Prod Count Quantile Min Max`
- 时间序列：`Ref Delta IdxMax IdxMin Correlation Corr Cov Rank Mask EMA WMA Slope Rsquare Resi`
- 条件：`If IfElse Greater Less`
- 自定义注册：`SignedPower Tanh Exp Sigmoid Softmax Scale Zscore Winsorize TsDecay TsMomentum TsAutoCorr RealizedVol TsEntropy TsMax TsMin TsRank TsSkew TsKurt CsRank CsZscore CsDemean AmihudIlliq HHI`

**禁止**：
- `$vwap`（数据为零）
- `Neg()` → 用 `Mul($x, -1)`
- `SMA()` → 用 `EMA` 或 `Mean`
- 嵌套深度 > 10

---

## Python contract

```python
REQUIRED_FIELDS: list[str] = ["$close", "$volume"]   # 必须 $ 前缀
VECTORIZED: bool = True                              # 必须 True（R5）

def compute(df: pd.DataFrame) -> pd.Series:          # 唯一签名
    ...  # df.index = MultiIndex(time, symbol)
```

**Import 白名单**：`numpy pandas scipy math typing dataclasses functools itertools __future__`

**禁止调用**：`eval exec compile __import__ open input breakpoint getattr setattr delattr`

---

## Wikilink 约定

| 场景 | 格式 |
|---|---|
| Direction → Factor | `[[../factors/F020\|F020]]` |
| Direction → Lessons | `[[../lessons#Structural Constraints]]` |
| Direction → Direction（同目录）| `[[timing_range]]` |
| Factor → Direction | `[[../directions/{tag}#Hypothesis]]` |
| Judge → Thread | `directions/{tag}.md#T001`（referenced_context 格式）|
| INDEX → Direction | `[[{tag}]]` |

---

## 关键约束（R2）

- **Python validates and freezes. LLM decides and creates.** Python 不校验 hypothesis 内容、thread 数量、narrative 质量——那是 LLM judgment。
- **A-share / market-cap / vectorization 等全局约束在 `lessons.md`**，factor-mine 循环会在 Phase 1 前读取，此处不复述。
