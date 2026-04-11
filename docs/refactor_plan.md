# 因子挖掘系统重构方案 v2

> 本文档是基于 `docs/walkthrough_qa.md` 中 Q1-Q47 所有问题和讨论后,
> 系统的完整重构规范。是未来重构工作的 north star。
>
> 重构原则:**不兼容旧代码,不做渐进迁移**。现有因子归档保留,新系统从 F020 开始。
>
> 生效日期:2026-04-11

---

## 目录

0. [背景与目标](#0-背景与目标)
1. [系统宪法](#1-系统宪法-元原则)
2. [整体流程](#2-整体流程-top-down)
3. [词汇与状态](#3-词汇与状态)
4. [文件与目录结构](#4-文件与目录结构)
5. [Phase 1 — START + DESIGN](#5-phase-1--start--design)
6. [Phase 2 — EXECUTE](#6-phase-2--execute)
7. [Phase 3 — JUDGE](#7-phase-3--judge)
   - [§7.MT 多重检验预算](#7mt-pre-pack-阶段的派生统计多重检验预算)
8. [Phase 4 — ARCHIVE](#8-phase-4--archive)
9. [Phase 5 — CONSOLIDATION](#9-phase-5--consolidation)
10. [核心文件 Schema](#10-核心文件-schema)
11. [缓存与向量化](#11-缓存与向量化)
12. [Holdout 隔离](#12-holdout-隔离)
13. [LLM / Python 职责矩阵](#13-llm--python-职责矩阵)
14. [CLI 清单](#14-cli-清单)
15. [代码清理清单](#15-代码清理清单)
16. [迁移步骤](#16-迁移步骤)
17. [CLAUDE.md 更新要点](#17-claudemd-更新要点)

---

## 0. 背景与目标

### 背景

老系统在 47 条 Q 的走读中暴露了系统性问题,可归纳为 3 个 meta pattern:

1. **半成品优化**:代码往某个方向重构到一半就停了,新旧路径并存导致静默失败(Q14 / Q18 / Q19 / Q39 / Q45)
2. **文档/字段名撒谎**:代码实际做的和 skill.md / 字段名说的不一致(Q1 / Q17 / Q37 / Q44.7 / Q45.9)
3. **Rule A/B 边界模糊**:yaml 塞散文,md 塞 schema,两边消费者都不满意(Q22 / Q25 / Q26)

### 目标

构建一个**自动化因子挖掘系统**,满足:

1. **LLM 主驾,Python 护栏** — LLM 决定方向/判决/整理,Python 负责计算/校验/状态机
2. **单一数据源** — 每个数据只有一个 canonical 位置,LLM 只读主输入不跨文件 grep
3. **不重复计算** — 连续流程内存共享,跨阶段走缓存
4. **向量化优先** — 禁 for-loop over rows,numpy/pandas 向量化
5. **代码极简** — 删除所有冗余抽象、死代码、过度工程
6. **跨 batch 学习** — LLM 周期性整理 memory,系统具备自我反省能力

---

## 1. 系统宪法(元原则)

这是所有设计决策的最高约束。**违反任何一条即设计错误**。

### R1 — Rule A/B 数据二分法

- **Rule A (YAML)**:Python 需要机械读写 + 有稳定 schema + 频繁增量更新 → 使用 YAML
- **Rule B (MD)**:LLM 深度思考 + 叙事 + 周期性重写而非 append → 使用 Markdown

**混合文件**:一个 md 内部可以有 `frontmatter` (Rule A) + `body` (Rule B),只要**写入权责清晰**:
- Python 只读写 frontmatter 的部分字段
- LLM 读整个文件,写整个文件(但遵守 frontmatter schema)

**不允许**:
- yaml 字段里塞大段散文叙事(老系统的 `detail`, `reasoning` 等)
- md 正文里塞需要 Python 机械 parse 的结构化表格(脆弱)

### R2 — LLM 主驾,Python 护栏

- **LLM 的职责**:决定探索方向 / 生成候选 / 深度判决 / 整理经验 / 写深度报告
- **Python 的职责**:表达式求值 / 统计指标向量化计算 / schema 验证 / 状态机 / cache 管理 / git 自动化
- **LLM 不维护 workflow** 本身 — 如果一个任务是"按规则转换状态",应该是 Python
- **Python 不做语义判断** — 如果一个任务是"判断这个机制是否合理",应该是 LLM

### R3 — 单一数据源

每个数据只有一个 **canonical** 位置。其他地方只能通过 `id` 或 `[[link]]` 引用,不允许复制。

**LLM 的单一主输入原则**:
- LLM 做 judge 时只读一份 `candidate_packet.md`
- LLM 写 factor.md 时只读一份 `report_packet.md`
- LLM 做 consolidation 时只读一份 `consolidation_packet.md`
- **禁止 LLM 跨多个文件 grep 拼凑数据**(Q45.6/Q45.13 的根源)

所有 LLM 需要的 context 由 Python **pre-pack** 成一份主输入文件。

### R4 — 不重复计算

- **连续流程(同一 Phase 内)**:market_df / barra_df / factor_df 等大对象只加载一次,通过参数传递共享
- **跨 Phase**:走文件缓存(`cache/factor_values/{hash}.parquet`)
- **Phase 4 的报告层不再算 IC**,直接消费 Phase 2 的 result.yaml

### R5 — 全程向量化

**硬禁令**:
- ❌ `for i, row in df.iterrows()`
- ❌ `for date in unique_dates: ...`
- ❌ `for cand in candidates: compute_metric(cand)`
- ❌ `np.linalg.lstsq` in Python for-loop

**必须用**:
- `groupby(level="time").transform(...)` 或 `.apply(vectorized_fn)`
- `np.einsum` / `np.linalg.pinv` 批量处理 3D tensor
- `corrwith` / `matmul` 批量相关/回归

### R6 — 代码极简,不做向后兼容

- **不做过度抽象**(删除所有"以防万一"的通用接口)
- **不做 silent fallback**(失败就 raise,不 log warning 继续)
- **现有因子归档保留,不迁移**,新系统从 F020 开始
- **不保留已经不用的代码**(例如 `renderer.py` / `FamilyRegistry` / `LifecycleManager`)

### R7 — Autonomous 但可审计

- LLM 自主推进主循环,**不在 mine 循环里问用户**
- 但每个决策点留下 provenance(来源 + 原因),人工随时可回溯
- **commit 失败硬 fail**(不静默跳过,Q47.3 的教训)

### R8 — DSL 优先,Python escape hatch(LLM 自主选择)

因子有两条构建路径:**DSL(Qlib 表达式字符串)** 和 **Python(源码文件)**。

**核心原则**:
- **DSL 是 default**。绝大多数因子都应该用 DSL
- **Python 是 escape hatch**,只在 DSL 无法表达时使用
- **LLM 在 Phase 1 DESIGN 时自主选择**,不是用户或 Python 强制决定
- **场景判断依据**在 `lessons.md` 的 "Path Selection: DSL vs Python" 段,LLM 每次 Phase 1 前必读

**安全边界**:
- Python 因子有严格的**静态 validation**(AST 扫描 import 白名单 + 禁用危险函数 + 签名契约)
- Python 因子有严格的**运行时 contract**(shape + 计时警告)
- 依赖 "LLM 生成代码 + Phase 1 静态 validate + Phase 4 commit 前人工 git review" 作为安全网
- **不做完整 process sandbox**(ROI 不够)

**默认流程**:autonomous mine 允许 Python 因子。如果用户想强制纯 DSL,用 `research mine --dsl-only`。

---

## 2. 整体流程 (top-down)

一轮迭代 = 5 个 Phase(从老系统的 9 步收敛而来)。

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  Phase 1  START + DESIGN  ──  LLM 选方向 + 出候选 + 冻结       │
│     ↓                                                        │
│  Phase 2  EXECUTE         ──  Python 批量向量化计算 (hold on │
│     ↓                          不算 holdout)                  │
│  Phase 3  JUDGE           ──  LLM + checkpoint 判决,写 judge.md │
│     ↓                                                        │
│  Phase 4  ARCHIVE         ──  Python 归档 + 后台 subagent 写  │
│     ↓                          factor.md + 主 commit          │
│                                                              │
│       (跨 batch 条件触发)                                     │
│         ↓                                                    │
│  Phase 5  CONSOLIDATION   ──  LLM 并行重写 memory md          │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 对比老架构(9 阶段 → 5 阶段)

| 老阶段 | 新位置 |
|---|---|
| Phase 0 Schedule(7 维 scheduler)| 并入 Phase 1:LLM 读 INDEX 直接选方向 |
| Phase 1 /factor-idea | Phase 1 START + DESIGN |
| Phase 2 /factor-execute | Phase 2 EXECUTE |
| Phase 3 /factor-judge | Phase 3 JUDGE |
| Phase 3.5a finalize-batch | 并入 Phase 4 ARCHIVE(Python 部分)|
| Phase 3.5b /factor-reflect | 重定位为 Phase 5 CONSOLIDATION |
| Phase 4 /factor-report | 并入 Phase 4 ARCHIVE(后台 subagent)|
| Phase 5 git commit | 并入 Phase 4 ARCHIVE 末尾 |

被删除的概念:
- LogicCard + 7 维 Scheduler + Lifecycle state machine(Q1-Q39)
- FamilyRegistry + PF/FM 两级 + promotion rules(Q22)
- `forbidden_patterns` yaml + `ForbiddenManager` + 3-state lifecycle(Q44.7)
- `guarded_writer` level_1/level_2 区分(过度工程)
- `holdout_queue` + `holdout_reviews` 状态机(Q2)
- `global_escalation` pending/consumed/applied(Q35)
- `search_ledger` by_logic/by_family/by_experiment_tag 计数(Q44.8)
- `ledger.write_audit_log`(git history 就是 audit log)
- probe 机制(Q12 的伪过滤)
- Phase 2 的 `preprocess.py` 的 4 处死代码(Q14)
- `src/report/renderer.py` + `templates/`(Q45.5)

---

## 3. 词汇与状态

### 核心词汇

| 词 | 含义 |
|---|---|
| **direction** | 一个研究方向(替代老词 "logic")。承载跨 batch 的假设追问 |
| **thread** | direction 内部的一个 open question,持续多个 batch 被追问 |
| **batch** | 一轮完整迭代的单位,对应**单一** direction |
| **candidate** | batch 内的一个具体因子表达式 |
| **factor** | admitted candidate,分配 `F{id}`,归档到 `factors/` |
| **mechanism** | 跨 direction 的归纳分类,落在 factor.yaml 的 `family_tag` 字符串 |
| **evidence** | Phase 2 产出的所有指标(result.yaml)|
| **checkpoint** | Phase 3 judge 的"必答题",共 6 个:CP01-CP06 |

### Direction 的 5 个状态

```
  exploring   → 新方向,还没 admit
  productive  → 有 admit,继续追
  saturated   → ROI 低,不再选(可被 LLM 复活)
  dead        → 假设被证伪(单向终结)
  merged      → 合并到另一个方向(原方向指向新方向)
```

**状态转换**:由 LLM 在 Phase 4 或 Phase 5 改 frontmatter 字符串,**无 Python state machine**。

### Batch / Direction 关系

- 一个 batch 只对应**一个** direction(不支持混方向)
- 一个 direction 可以跨多个 batch(持续追问)
- 融合候选 → 创建**新 direction**(不是混 batch)
- 跨方向对比 → 通过 Phase 3 pre-pack 主动注入参考数据

---

## 4. 文件与目录结构

### Vault 根(Obsidian 友好)

```
storage/evidence/vault/               ← Obsidian vault 根
  INDEX.md                            ← MOC,所有 direction 总览
  lessons.md                          ← system-level facts (小而稳)
  
  directions/                         ← 所有研究方向(不分 archive)
    fundamental_price_divergence.md
    volume_autocorrelation.md
    timing_range.md
    ...                               ← status 在 frontmatter 里区分
  
  factors/                            ← admitted factor 的归档
    F020.yaml                         ← Python 读
    F020.md                           ← LLM 读
    F020/                             ← 图表 assets
      ic_timeseries.png
      quintile_bar.png
      ...
    F021.yaml
    F021.md
    F021/
  
  _meta/
    consolidation_log.md              ← append-only changelog
```

### 系统状态与配置

```
storage/
  state.yaml                          ← 唯一系统状态(A)
  config.yaml                         ← 系统配置(A)
  
  python_factors/                     ← admitted Python 因子源码
    __init__.py
    F022_shadow_kalman_v2.py          ← 一个 admitted Python factor 一个文件
    F025_triple_filter_rerank.py
    ...
  
  batches/batch_{NNN}/                ← 每轮迭代的档案
    manifest.yaml                     ← 冻结的候选 + 设计理由(A)
    result.yaml                       ← Python 评估指标(A)
    judge.md                          ← LLM 判决 (Rule A frontmatter + Rule B body)
    python_candidates/                ← 本 batch 的 Python 候选源码(未 admit)
      C003.py                         ← 以 candidate_id 命名
      C007.py
    signals/                          ← factor 值缓存(per candidate,两路统一)
      C001.parquet                    ← DSL 候选
      C003.parquet                    ← Python 候选
    _packets/                         ← Pre-pack 临时文件(commit 后可清)
      judge_packet.md
      report_packet_F020.md
  
  cache/                              ← Runtime 缓存(可重建)
    market_daily.parquet              ← 已清洗过的价格数据
    barra_factors.parquet             ← 预计算 Barra 因子
    factor_values/
      {hash}.parquet                  ← 按 hash 索引(DSL: expression hash,Python: file content hash)
  
  _holdout_private/                   ← 严格隔离区,vault 外
    review_{date}.md                  ← holdout review 结果(LLM 看不到)
    .gitignore                        ← 或单独标记
```

### 文件对比(老 → 新)

| 老路径 | 新路径 / 命运 |
|---|---|
| `storage/logic/cards/L*.yaml` | 删除 → `vault/directions/*.md` |
| `storage/logic/reflections/L*.md` | 删除 → 并入 direction md 的 Narrative Log |
| `storage/logic/proposals/` | 删除(Q10 孤儿)|
| `storage/logic/reviews/` | 删除 |
| `storage/logic/snapshots/` | 删除 |
| `storage/logic/registry.yaml` | 删除 |
| `storage/governance/ledger.yaml` | 删除(git + state.yaml 替代)|
| `storage/governance/research_config.yaml` | 改名 `storage/config.yaml`,简化 |
| `storage/governance/research_lessons.md` | 搬到 `vault/lessons.md`,内容大幅精简 |
| `storage/registry/factors/factor_F*.yaml` | 搬到 `vault/factors/F*.yaml` |
| `storage/registry/families/` | 删除(降级为 factor.yaml.family_tag)|
| `storage/state/global_escalation.yaml` | 删除(并入 memory)|
| `storage/state/pending_holdout_queue.yaml` | 删除(holdout 重设计)|
| `storage/batches/batch_*/judge_packet.yaml` | 删除(并入 result.yaml + packet)|
| `storage/batches/batch_*/idea_report.yaml` | 删除(并入 manifest.yaml)|
| `storage/batches/batch_*/judge_report.yaml` | 改为 `judge.md`(新 schema)|
| `storage/evidence/vault/factors/` | 迁移到 `vault/factors/`(重组)|
| `storage/evidence/vault/assets/` | 迁移到 `vault/factors/F{id}/` |
| `storage/runtime/cache/` | 搬到 `storage/cache/` |

---

## 5. Phase 1 — START + DESIGN

### 职责

读 memory → 选方向 → 定目标 → 出候选 → 冻结 manifest。

### 流程

```
Step 1  Python: refresh INDEX 下半段统计表
Step 2  LLM: 读 INDEX → 选 direction → follow link 读 direction md
Step 3  LLM: 决定本轮 batch_goal + 推进哪个 thread
Step 4  LLM: 写 5-10 个候选因子表达式 + rationale
Step 5  Python: DSL whitelist 验证
Step 6  Python: 冻结 manifest.yaml,state.current_batch = batch_{N}
```

### 输入(LLM 只读)

- `vault/INDEX.md`(必读,overview)
- `vault/directions/{tag}.md`(选中的方向,1-2 个)
- `vault/lessons.md`(可选)
- 最近 3 个 batch 的 `judge.md` frontmatter 摘要(可选)

### 产出

- `batches/batch_{N}/manifest.yaml`(frozen,不可变)
- `state.yaml` 更新(`current_batch`, `current_batch_phase: designed`)

### 关键决策

1. **单 direction batch**:一个 batch 只对应一个 direction。跨方向融合 → 新建 direction。
2. **删除 probe**:Phase 2 向量化足够快,Phase 1 不做 IC 预筛。
3. **batch_goal 强制非空**:Python 在冻结 manifest 时 audit,长度 < 30 字符 → raise。
4. **DSL 只有 whitelist**:字段/算子必须在 whitelist,**没有 blacklist / forbidden**。违禁直接 raise,LLM 重写。

### DSL 验证逻辑

```python
DSL_FIELD_WHITELIST = {
    "$open", "$high", "$low", "$close", "$volume", "$amount",
    "$pe_ratio", "$pb_ratio", "$ps_ratio",
    "$market_cap", "$circ_market_cap", "$turnover_rate",
}

DSL_OPERATOR_WHITELIST = {
    "Mean", "Std", "Corr", "Cov", "Sub", "Div", "Mul", "Add",
    "Ref", "CsRank", "CsZscore", "TsRank", "TsMax", "TsMin",
    "Rank", "Delta", "Log", "If", "Less", "Greater",
    "IdxMax", "IdxMin", "TsAutoCorr", "Abs", "Power", "Sign",
}

MAX_EXPRESSION_DEPTH = 10

def validate_dsl(expression: str) -> None:
    parsed = parse(expression)
    for field in parsed.fields:
        if field not in DSL_FIELD_WHITELIST:
            raise ValueError(f"forbidden field: {field}")
    for op in parsed.operators:
        if op not in DSL_OPERATOR_WHITELIST:
            raise ValueError(f"unknown operator: {op}")
    if parsed.max_depth > MAX_EXPRESSION_DEPTH:
        raise ValueError(f"depth {parsed.max_depth} > {MAX_EXPRESSION_DEPTH}")
```

### Python 候选的 validation(修 R8 escape hatch)

如果某个 candidate 的 `source_type: python`,Phase 1 Step 5 除了 DSL validation 外,还要对 Python 文件做静态检查。

```python
ALLOWED_IMPORTS = {
    "pandas", "numpy", "math", "functools",
    "itertools", "collections", "typing",
}

FORBIDDEN_CALLS = {
    "open", "eval", "exec", "compile", "__import__",
    "globals", "locals", "getattr", "setattr", "delattr",
    "input", "breakpoint",
}

def validate_python_candidate(py_path: Path) -> None:
    """静态 AST 检查 + import 扫描 + 签名契约,不执行 compute()"""
    source = py_path.read_text()
    tree = ast.parse(source)
    
    # 1. Import 白名单
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root not in ALLOWED_IMPORTS:
                    raise ValueError(f"{py_path}: forbidden import: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root not in ALLOWED_IMPORTS:
                raise ValueError(f"{py_path}: forbidden import from: {node.module}")
    
    # 2. 禁用危险 builtins
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in FORBIDDEN_CALLS:
                raise ValueError(f"{py_path}: forbidden call: {node.func.id}")
    
    # 3. 签名契约(通过 import module 执行 top-level 代码获取常量)
    spec = importlib.util.spec_from_file_location("_candidate", py_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # REQUIRED_FIELDS
    assert hasattr(module, "REQUIRED_FIELDS"), f"{py_path}: missing REQUIRED_FIELDS"
    assert isinstance(module.REQUIRED_FIELDS, list)
    for f in module.REQUIRED_FIELDS:
        assert f.startswith("$"), f"{py_path}: field must start with $"
        assert f in DSL_FIELD_WHITELIST, f"{py_path}: forbidden field: {f}"
    
    # VECTORIZED 自声明
    assert hasattr(module, "VECTORIZED"), f"{py_path}: missing VECTORIZED"
    assert module.VECTORIZED is True, f"{py_path}: non-vectorized factor not allowed"
    
    # compute 签名
    assert hasattr(module, "compute"), f"{py_path}: missing compute()"
    sig = inspect.signature(module.compute)
    assert list(sig.parameters.keys()) == ["market_df", "params"], \
        f"{py_path}: compute() must have signature (market_df, params)"
```

### Python 因子的模板(LLM 必须遵守的签名)

```python
"""
Factor: <name>
Created: <batch_id>
Rationale: <为什么这里必须用 Python 而不是 DSL,指向 lessons.md 的哪个场景>
"""
import pandas as pd
import numpy as np

# 必填:声明依赖的 market data 字段
REQUIRED_FIELDS = ["$close", "$pe_ratio", "$pb_ratio", "$volume"]

# 必填:自声明是否向量化(False 会被 reject)
VECTORIZED = True

# 可选:可配置参数,默认值
PARAMS = {
    "lookback_days": 80,
    "top_pct": 0.2,
}

def compute(market_df: pd.DataFrame, params: dict) -> pd.Series:
    """
    Args:
        market_df: MultiIndex (time, symbol) DataFrame,
                   已经过 universe filter 和 tradability mask。
                   columns 包含 REQUIRED_FIELDS。
        params: PARAMS 的拷贝(可能被 config 覆盖)。
    
    Returns:
        pd.Series indexed by (time, symbol),factor value。
    
    Constraints:
        - 完全向量化:禁 `for` over rows/dates/symbols
        - 只用 pandas/numpy/stdlib math
        - 不访问 filesystem / network / subprocess
        - 不使用全局 state
        - 正确处理 NaN
    """
    # implementation ...
    return result
```

### Duplicate expression check(修 Q4)

**防止同一表达式换 rationale 重投**。Phase 1 Step 5 的 DSL 验证后,还要检查:

```python
def check_duplicate_expression(candidates: list, existing_factors_dir: Path) -> None:
    """
    拒绝任何和已 admit factor 完全相同的表达式。
    一个 expression 的 canonical 归档位置只有一个 F{id},不允许重复 admit。
    """
    existing_exprs = {}
    for f in existing_factors_dir.glob("F*.yaml"):
        meta = load_yaml(f)
        canonical = canonicalize_expression(meta["expression"])
        existing_exprs[canonical] = meta["factor_id"]
    
    for cand in candidates:
        canonical = canonicalize_expression(cand.expression)
        if canonical in existing_exprs:
            raise ValueError(
                f"Candidate {cand.candidate_id} expression duplicates "
                f"already-admitted {existing_exprs[canonical]}. "
                f"If you want to revisit the factor, use `research regenerate-report {existing_exprs[canonical]}`."
            )

def canonicalize_expression(expr: str) -> str:
    """规范化表达式(移除空格、统一算子顺序、规整括号)。"""
    # 简单实现:解析 AST,按规范序列化
    ...
```

**说明**:
- 不是 cache 层面的防御(cache 只是避免重算),而是 Phase 1 冻结前的显式拒绝
- 支持"撤销 + 重新 admit":如果确实想重判,先 `research factor retire F018`,再在新 batch 里提同一表达式
- `canonicalize_expression` 对 `Mul(A, B)` 和 `Mul(B, A)` 视为相同(交换律),对 `A + B + C` 和 `A + (B + C)` 视为相同

---

## 6. Phase 2 — EXECUTE

### 职责

纯 Python 批量向量化计算。零 LLM 参与。

### 流程

```
Step 1  Python: 加载 market_daily / barra / library(一次性)
Step 2  Python: 批量算 factor values(Qlib 单次调用多 expression)
Step 3  Python: 向量化算所有指标
Step 4  Python: 预处理(winsorize + zscore)
Step 5  Python: 写 result.yaml 和 signals/*.parquet
```

### 数据加载(不重复)

```python
def load_data():
    # 一次 Phase 2 只加载一次,参数传递共享
    market_df = pd.read_parquet("cache/market_daily.parquet")   # 已清洗
    barra_df  = pd.read_parquet("cache/barra_factors.parquet")  # 预计算
    library_df = load_library_signals()  # 从 factors/F*.yaml 的 signal_ref 读 parquet
    return market_df, barra_df, library_df
```

**关键**:
- 不调 Qlib 读 market(用 cache parquet)
- 不调 DB 读 factor_values(用 factors/F*.yaml 的 signal_ref 指向的 parquet)
- cache 不做 24h 自动失效,只在 `research cache refresh` CLI 触发时重建

### 批量计算 — DSL + Python 两路汇合(修 Q12 + R8)

```python
def compute_all_factor_values(manifest, market_df):
    factor_wide = {}
    dsl_to_compute = []      # DSL 候选
    python_to_compute = []   # Python 候选
    
    # Step 1: 分离 cache hit / miss,按 source_type 分组
    for cand in manifest.candidates:
        if cand.source_type == "python":
            py_path = resolve_python_ref(cand.python_ref)
            cache_key = sha256(py_path.read_bytes() + sample_policy_version.encode())
        else:
            cache_key = sha256(
                (cand.expression + sample_policy_version).encode()
            )
        
        path = f"cache/factor_values/{cache_key}.parquet"
        if exists(path):
            factor_wide[cand.candidate_id] = pd.read_parquet(path)
            # 同时在 batch signals/ 建引用
            symlink(path, f"batches/{batch_id}/signals/{cand.candidate_id}.parquet")
        else:
            if cand.source_type == "python":
                python_to_compute.append((cand.candidate_id, py_path, cache_key))
            else:
                dsl_to_compute.append((cand.candidate_id, cand.expression, cache_key))
    
    # Step 2: DSL 批量 — 一次 D.features() 调用所有 miss 的 expression
    if dsl_to_compute:
        expressions = [e for _, e, _ in dsl_to_compute]
        raw = D.features(
            instruments="all",
            fields=expressions,
            start_time=train_start,
            end_time=validation_end,   # 不加载 holdout 范围
        )
        for cid, expr, ckey in dsl_to_compute:
            series = raw[expr]
            factor_wide[cid] = series
            series.to_parquet(f"cache/factor_values/{ckey}.parquet")
            series.to_parquet(f"batches/{batch_id}/signals/{cid}.parquet")
    
    # Step 3: Python 逐个 — 每个 Python 因子独立 compute()
    for cid, py_path, ckey in python_to_compute:
        series = run_python_factor(py_path, market_df)
        factor_wide[cid] = series
        series.to_parquet(f"cache/factor_values/{ckey}.parquet")
        series.to_parquet(f"batches/{batch_id}/signals/{cid}.parquet")
    
    return factor_wide


def run_python_factor(py_path: Path, market_df: pd.DataFrame) -> pd.Series:
    """加载并执行 Python 因子,带运行时契约检查"""
    spec = importlib.util.spec_from_file_location("_factor", py_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # 切片:只给声明的字段
    sliced = market_df[module.REQUIRED_FIELDS]
    
    # 参数
    params = dict(module.PARAMS) if hasattr(module, "PARAMS") else {}
    
    # 计时(向量化的间接证据)
    t0 = time.perf_counter()
    result = module.compute(sliced, params)
    elapsed = time.perf_counter() - t0
    
    # 运行时契约
    assert isinstance(result, pd.Series), \
        f"{py_path}: compute() must return pd.Series, got {type(result)}"
    assert list(result.index.names) == ["time", "symbol"], \
        f"{py_path}: wrong index: {result.index.names}"
    assert len(result) > 0, f"{py_path}: empty result"
    assert not result.index.duplicated().any(), \
        f"{py_path}: duplicated index"
    
    # 向量化间接检测(软警告)
    n_rows = len(sliced)
    expected_max_seconds = max(1.0, n_rows * 1e-5)
    if elapsed > expected_max_seconds:
        logger.warning(
            f"{py_path}: took {elapsed:.2f}s for {n_rows} rows, "
            f"may not be properly vectorized(expected < {expected_max_seconds:.1f}s)"
        )
    
    return result
```

**说明**:
- DSL 候选走批量 Qlib 调用,Python 候选逐个 import + 运行
- 两路产出的 Series 汇合到同一个 `factor_wide` dict
- 后续所有指标计算(IC / monotonicity / Barra / redundancy / feasibility)**完全不区分来源**
- Cache 也统一:key 不同(expression hash vs file content hash),目录相同

### 预处理(应用 Q14-Q17 修正)

**两层处理**:

#### 层 1 — Cache 构建层(一次性,写 parquet 时)

这是 `research cache refresh market_daily` CLI 调用时执行的完整清洗。

**注意**:老 `scripts/resync_qlib.py` 只复制数据不清洗,所有 tradability 逻辑**都没实现**。
新 `cache refresh` CLI 必须补齐。

```python
def rebuild_market_daily_cache():
    """从 DB 读原始数据,应用所有清洗,落盘到 cache/market_daily.parquet"""
    
    # Step 1: 从 DB 读(含 limit_up/limit_down)
    raw = read_from_db("""
        SELECT time, symbol, open, high, low, close, volume, amount,
               limit_up, limit_down, adj_factor
        FROM market_daily ORDER BY symbol, time
    """)
    
    # Step 2: Symbol 前缀过滤(一次性,删除不在研究范围的)
    raw = raw[~raw["symbol"].str.startswith("688")]    # 科创板
    raw = raw[~raw["symbol"].str.startswith("8")]      # 北交所
    raw = raw[~raw["symbol"].str.startswith("43")]     # 老三板
    raw = raw[~raw["symbol"].str.startswith("9")]      # B 股
    
    # Step 3: 构造 tradable mask 列(核心!)
    raw["tradable"] = True
    
    # (a) 停牌:volume == 0(近似,DB 无 suspended 字段)
    raw.loc[raw["volume"] == 0, "tradable"] = False
    
    # (b) 涨停:收盘 >= limit_up * 0.999
    #     含义:t 日顶到涨停 → 次日 buy 不了 → factor 在 t 日该股不参与统计
    raw.loc[raw["close"] >= raw["limit_up"] * 0.999, "tradable"] = False
    
    # (c) 跌停:收盘 <= limit_down * 1.001
    raw.loc[raw["close"] <= raw["limit_down"] * 1.001, "tradable"] = False
    
    # (d) ST 过滤(需要 ref_stock_status 表,见下方"数据工程 TODO")
    if table_exists("ref_stock_status"):
        st = read_from_db("""
            SELECT time, symbol FROM ref_stock_status 
            WHERE is_st = TRUE
        """)
        raw = raw.merge(st.assign(_is_st=True), 
                        on=["time", "symbol"], how="left")
        raw.loc[raw["_is_st"] == True, "tradable"] = False
        raw = raw.drop(columns="_is_st")
    
    # (e) 新股缓冲:上市 60 日内不参与(流动性不稳)
    first_trade = raw.groupby("symbol")["time"].min()
    raw = raw.merge(first_trade.rename("_first"), on="symbol")
    raw["days_since_listing"] = (raw["time"] - raw["_first"]).dt.days
    raw.loc[raw["days_since_listing"] < 60, "tradable"] = False
    raw = raw.drop(columns=["_first", "days_since_listing"])
    
    # Step 4: 落盘
    raw.to_parquet("storage/cache/market_daily.parquet")
```

#### 数据工程 TODO(refactor_plan 之外)

新系统 cache 清洗需要 DB 有以下字段,**目前缺失**,需要独立的数据工程任务补齐:

| DB 表 | 字段 | 现状 | 需要 |
|---|---|---|---|
| `market_daily` | `limit_up`, `limit_down` | ✅ 已有 | — |
| **`ref_stock_status`** | `time, symbol, is_st, is_suspended` | ❌ 不存在 | 新建表,从 RiceQuant/Tushare sync |
| `market_daily` | `first_listing_date` | ❌ 不存在 | 新加列 OR 从 RiceQuant 拉 |
| `ref_delisted` | `symbol, delist_date` | ❌ 不存在 | 新建表 |

**一次性数据工程任务**(不属于 refactor 主线):
1. 从 RiceQuant 拉取历史 ST 数据 → `ref_stock_status`
2. 从 RiceQuant 拉取上市日期 → 新加 `market_daily.first_listing_date` 或单独表
3. 退市股名单 → `ref_delisted`
4. 建立日更新任务

在这些数据到位**之前**,`cache refresh` 只做 (a)/(b)/(c)(volume + limit_up/down)+ 前缀过滤 + 新股缓冲(用 df.groupby 近似)。ST 和退市暂时不做。

### Barra factor cache 的构建

Plan 多次提到 "Barra 预计算存 `cache/barra_factors.parquet`",这里给具体实现。

**7 个 Barra 因子定义**:

| Barra factor | 定义 | 数据源 |
|---|---|---|
| `log_circ_cap` | `log(circ_market_cap)` | `ref_valuation.circ_market_cap` |
| `book_to_price` | `1 / pb_ratio` | `ref_valuation.pb_ratio` |
| `ep_ratio` | `1 / pe_ratio` | `ref_valuation.pe_ratio` |
| `mom_12_1` | `close(t-21) / close(t-252) - 1`(skip 1 月,留 11 月动量) | `market_daily.close` |
| `str_1m` | `close(t) / close(t-21) - 1`(1 月反转) | `market_daily.close` |
| `vol_20d` | `std(daily_return, 20)` | `market_daily.close` |
| `turnover_20d` | `mean(turnover_rate, 20)` | `ref_shares.turnover_rate` |

**向量化构建脚本**(`research cache refresh barra_factors`):

```python
def build_barra_factors_cache():
    # Step 1: 读市场数据(cache 层已清洗)
    market_df = pd.read_parquet("storage/cache/market_daily.parquet")
    
    # Step 2: 读估值和换手数据(DB)
    ref_val = read_from_db("""
        SELECT time, symbol, market_cap, circ_market_cap, pe_ratio, pb_ratio
        FROM ref_valuation
    """)
    ref_turn = read_from_db("SELECT time, symbol, turnover_rate FROM ref_shares")
    
    # Step 3: Join + pivot 成 wide matrices (time × symbol)
    df = (market_df
          .merge(ref_val, on=["time", "symbol"], how="left")
          .merge(ref_turn, on=["time", "symbol"], how="left"))
    
    def to_wide(col):
        return df.pivot(index="time", columns="symbol", values=col)
    
    close = to_wide("close")
    circ_cap = to_wide("circ_market_cap")
    pb = to_wide("pb_ratio")
    pe = to_wide("pe_ratio")
    turnover = to_wide("turnover_rate")
    
    # Step 4: 纯矩阵运算,7 个因子一次算完
    barra = {}
    barra["log_circ_cap"] = np.log(circ_cap)
    barra["book_to_price"] = 1.0 / pb
    barra["ep_ratio"] = 1.0 / pe
    barra["mom_12_1"] = close.shift(21) / close.shift(252) - 1.0
    barra["str_1m"] = close / close.shift(21) - 1.0
    daily_ret = close.pct_change()
    barra["vol_20d"] = daily_ret.rolling(20).std()
    barra["turnover_20d"] = turnover.rolling(20).mean()
    
    # Step 5: 堆叠成 long format + factor 列,落盘
    long_frames = []
    for name, wide in barra.items():
        long = wide.stack().rename("value").reset_index()
        long["barra_factor"] = name
        long_frames.append(long)
    barra_long = pd.concat(long_frames, ignore_index=True)
    barra_long.to_parquet("storage/cache/barra_factors.parquet")
```

**成本**:单次构建 ~30s。手动刷新,服务所有后续 batch,均摊成本 ≈ 0。

**Phase 2 加载**:
```python
def load_barra_factors_wide() -> dict[str, pd.DataFrame]:
    barra_long = pd.read_parquet("storage/cache/barra_factors.parquet")
    return {
        name: barra_long[barra_long["barra_factor"] == name]
                       .pivot(index="time", columns="symbol", values="value")
        for name in ["log_circ_cap", "book_to_price", "ep_ratio",
                     "mom_12_1", "str_1m", "vol_20d", "turnover_20d"]
    }
```

返回 wide matrices dict,供后续 Barra 残差 IC 的 einsum 批量回归使用。

#### 层 2 — Phase 2 计算层(每次 execute 都跑)

**不要用 `groupby.transform`**。那只是隐式 for-loop over dates,不是真向量化。
正确做法:long → wide pivot,对整个 matrix 做 row-wise numpy 批量运算,再 wide → long。

```python
def preprocess_factor(factor_long: pd.Series, tradable_mask: pd.Series) -> pd.Series:
    """
    完全矩阵向量化的预处理:winsorize + zscore。
    对整个 (n_dates × n_symbols) matrix 一次性操作,不按日期 groupby。
    
    Args:
        factor_long: MultiIndex (time, symbol) 的 Series
        tradable_mask: 同 index,True = 可交易
    
    Returns:
        preprocessed Series(同 index)
    """
    # Step 1: 应用 tradable mask(不可交易日 → NaN)
    factor_long = factor_long.where(tradable_mask, np.nan)
    
    # Step 2: Long → Wide (time × symbol)
    factor_wide = factor_long.unstack(level="symbol")
    # factor_wide.shape = (n_dates, n_symbols)
    
    # Step 3: Winsorize MAD 5 — 纯矩阵运算
    #   对每行算 median 和 MAD,然后 clip
    row_median = factor_wide.median(axis=1, skipna=True)           # (n_dates,)
    abs_dev = factor_wide.sub(row_median, axis=0).abs()
    mad = abs_dev.median(axis=1, skipna=True)                      # (n_dates,)
    
    # MAD → approximate std(1.4826 是正态分布下的换算系数)
    scale = config["preprocess"]["winsorize_mad_scale"]            # 1.4826
    k = config["preprocess"]["winsorize_mad_k"]                    # 5
    upper = row_median + k * mad * scale                           # (n_dates,)
    lower = row_median - k * mad * scale
    
    factor_wide = factor_wide.clip(lower=lower, upper=upper, axis=0)
    
    # Step 4: Z-score — 纯矩阵运算
    row_mean = factor_wide.mean(axis=1, skipna=True)               # (n_dates,)
    row_std  = factor_wide.std(axis=1, skipna=True, ddof=0)        # (n_dates,)
    factor_wide = factor_wide.sub(row_mean, axis=0).div(row_std, axis=0)
    
    # Step 5: 中性化:默认关闭(R8 + 第 6 节说明)
    # 理由:CP04 Risk Cleanness 事后 Barra 检验更严格,预先中性化会吃掉原始信号
    
    # Step 6: Wide → Long(下游需要 MultiIndex 格式)
    return factor_wide.stack(dropna=False)
```

**为什么这是真向量化**:
- `factor_wide.median(axis=1)` 是 pandas 内部 C 实现,一次算所有 row 的 median
- `factor_wide.sub(row_median, axis=0)` 是 broadcasting,没有 for loop
- `factor_wide.clip(lower=lower, upper=upper, axis=0)` 也是 broadcasting
- 整个预处理对 (2000 dates × 5000 symbols) 矩阵耗时 < 1s
- 对比 `groupby.transform`:2000 次 per-group apply,每次 ~1ms,累计 ~2s

**唯一的代价**:内存需要完整的 wide matrix。(2000 × 5000 × 8 bytes = 80 MB),可接受。

### 指标计算(全部向量化)

见 [第 11 节 缓存与向量化](#11-缓存与向量化) 的详细规范。

核心指标(全部在一个 tensor 上批量算):
- IC mean / std / ir / win_rate(rank corr,cross-sectional)
- Monotonicity(quintile 单调性)
- Alpha survival + Barra residual IC(批量 OLS)
- Redundancy(batch corrwith library)
- Feasibility(coverage / turnover / half_life)
- Stability(split_stability + expanding_window)

**holdout 完全不算**(见 [第 12 节 Holdout 隔离](#12-holdout-隔离))。

### 错误处理

单候选计算失败:
- 记录到 `result.yaml` 该候选的 `compute_error` 字段
- 其他候选继续跑
- Phase 3 judge 看到 `compute_error` 非空直接 reject

---

## 7. Phase 3 — JUDGE

### 职责

LLM 对每个 candidate 做 6 个 checkpoint 的结构化判决,写 `judge.md`。

### 流程

```
Step 1  Python: 跑 hard gates(CP01),标记 fatal reject
Step 2  Python: 扫 batches/ 算多重检验预算(见 §7.MT)
Step 3  Python: Pre-pack candidate_packet.md
         - 从 result.yaml 摘指标
         - 从 direction.md 摘 Hypothesis + relevant thread
         - 从 lessons.md 摘 structural constraints
         - 从 factors/F{nearest}.md 摘最相近因子 summary
         - 附上 Python 的 numeric_hint per checkpoint
           (CP03 的 hint 强制包含 mt_bucket + adjusted_strength)
Step 4  LLM: 读 _packets/judge_packet.md,写 judge.md
         - frontmatter: structured verdicts, positions, references
         - body: 6 CP × N candidates 的深度 reasoning
Step 5  Python: audit judge.md
         - schema check
         - 章节存在 check
         - reference 真实性 check (grep)
         - hard gate 不可 override check
         - CP03 body 必须显式引用 mt_bucket(防视而不见)
         - 若 fail:raise,LLM 重写
Step 6  Python: 清理 _packets(可选保留 debug)
```

### 7.MT Pre-pack 阶段的派生统计(多重检验预算)

**问题**。102 个 batch × ~6 candidate ≈ 600 次在同一 validation 窗口上的独立
检验。α=0.05 时纯随机也能见到 ~30 个"显著"因子。没有分母,CP03 的
"Bonferroni 校正"就是一句空话,ICIR=0.25 的 borderline 信号会被长期当强信号
admit,录取门槛随系统运行时间漂移。

**为什么要写在 plan 里单独一节**。老系统 `ledger.yaml::batch_usage` 想做这件
事,但写入通道和消费通道从来没连起来——`src/research/stats/multiple_testing.py`
里的 `compute_multiple_testing_risk()` 定义了却没人调,
`src/research/execute/compute_implementations.py:357` 直接硬编码 `"low"`。
refactor 删除 ledger 是对的,但如果不明确替代方案,这个 bug 会被新架构原样继承
(见 docs/walkthrough_qa.md Q2)。

**替代方案的核心洞察**。多重检验的三个 counter 都是 `storage/batches/` 目录
的纯函数,不需要任何新的持久化状态——git 里已经有全部数据。把它做成 Phase 3
pre-pack 的强制步骤即可,完全符合"git 即 audit log"的主哲学。

#### 接口

```python
# src/research/stats/mt_budget.py

def scan_batches_for_mt(
    batches_dir: Path,
    current_batch_id: str,
    current_direction: str,
    sample_policy_version: str,
) -> dict:
    """扫 batches/ 算多重检验 counter。纯函数,无副作用。

    Returns:
        {
            "cumulative_candidates": int,   # 所有已 judged batch 累计 candidate 数
            "direction_candidates": int,    # 同 direction 历史 candidate 数
            "validation_exposure": int,     # 当前 sample_policy_version 下
                                            # 被使用过的 batch 数(换 policy 重置)
            "n_batches_scanned": int,       # debug 用
        }
    """
    entries = []
    for manifest_path in sorted(batches_dir.glob("batch_*/manifest.yaml")):
        m = yaml.safe_load(manifest_path.read_text())
        # 只数"已 judged"的 batch(避免把本轮自己算进去)
        if m["batch_id"] >= current_batch_id:
            continue
        # judge.md 存在才算完整一轮检验
        if not (manifest_path.parent / "judge.md").exists():
            continue
        entries.append(m)

    cum = sum(len(m["candidates"]) for m in entries)
    per_dir = sum(
        len(m["candidates"])
        for m in entries
        if m.get("direction") == current_direction
    )
    val_exp = sum(
        1 for m in entries
        if m.get("sample_policy_version") == sample_policy_version
    )
    return {
        "cumulative_candidates": cum,
        "direction_candidates": per_dir,
        "validation_exposure": val_exp,
        "n_batches_scanned": len(entries),
    }


def compute_mt_budget(counts: dict) -> dict:
    """包 compute_multiple_testing_risk + search_adjusted_strength,
    返回可直接塞进 numeric_hint 的 dict。

    Formula(沿用 src/research/stats/multiple_testing.py,常数按新粒度标定):
        mt_score = 0.50 * clip(log1p(cumulative) / log(600), 0, 1)
                 + 0.30 * clip(log1p(direction)  / log(80),  0, 1)
                 + 0.20 * clip(validation_exposure / 40,     0, 1)

        bucket:  score < 0.40 → low
                 score ≤ 0.70 → medium
                 else         → high
    """
    # 注:老公式 log(25)/log(60)/12 是 logic-attempt / family-attempt 粒度。
    # 新粒度(candidate / direction)数量级高一个档,所以常数写进
    # config.yaml.thresholds.mt_budget(§10),首次 PR 里用 batch_001-102 回拟。
    ...
```

**所有常量都在 `config.yaml.thresholds.mt_budget`**(见 §10),包括 600/80/40 的
scale,3 个 weight,和 low/medium bucket 分界线。禁止在 Python 代码里硬编码。

#### CP03 的 numeric_hint 必包字段

```yaml
# 每个 candidate 的 numeric_hint.CP03
CP03:
  ic_mean_validation: 0.016
  ic_ir_validation: 0.338
  ls_tstat: 3.89
  # ↓ 新增 4 个字段
  mt_score: 0.52                 # 0-1 连续
  mt_bucket: medium              # low / medium / high
  search_adjusted_strength: 0.41 # raw * (1 - 0.5 * mt_score)
  mt_breakdown:
    cumulative_candidates: 612
    direction_candidates: 47
    validation_exposure: 102
```

LLM 在 CP03 body 必须显式引用 `mt_bucket` 值;audit_judge_md 对 CP03 段
加一条 grep 检查 `assert "mt_bucket" in cp03_section`,漏写就 raise
让 LLM 重写。

#### 三条硬约束

1. **mt 预算由 Python 算,LLM 不能 override**。LLM 只能在 CP03 body 里
   解释"我看到 mt=medium,因此即便 ICIR=0.25 看似不弱,我给 borderline 而
   不是 strong"这类推理,但不能修改 mt_bucket 本身。
2. **sample_policy_version 变更 → validation_exposure 清零**。这是唯一
   合法的"重置预算"路径,必须在 config.yaml 里升版号(例如 `v3` → `v4`),
   git 历史可查。LLM 不能擅自重置。
3. **扫描范围只到"已 judged 的 batch"**,不含 current batch 自身的其他
   candidate(避免 self-correction 的数值循环,也避免 designed 但没跑完的
   batch 被重复计入)。

#### 为什么不放 state.yaml

- state.yaml 的职责是"当前系统处于哪个状态"(轮次、phase、last_batch 等),
  不是"历史累计计数"。把派生量塞进 state.yaml 会污染状态语义,并引入
  finalize-batch 的原子写负担。
- git 里已经有 batches/ 全部历史,扫描成本 O(100) 个小 yaml 文件,毫秒级。
  加一层缓存都不值。
- 派生量每次 pre-pack 现算,和 R3(单一数据源)+ R4(不重复计算)并不冲突
  ——R4 说的是"不要在单次流程里重复计算",跨流程按需派生是允许的。

#### 手工复盘入口

新增 CLI `research audit mt-budget`(见 §14),打印当前 cumulative /
direction / validation_exposure 以及预测下一个 batch 的 mt_bucket,供
人工 sanity check 和发现"某个 direction 快到硬门槛了该换方向"之类的
宏观信号。

### 6 个 Checkpoint

| ID | 名称 | 谁决定 | 内容 |
|---|---|---|---|
| **CP01** | Hard Gates | Python(LLM 无权 override)| sign_flip / coverage / forbidden field/op / sample_policy violation / compute_error |
| **CP02** | Mechanism Alignment | LLM | expression 是否对应 direction.hypothesis |
| **CP03** | Statistical Strength | LLM(Python hint)| IC / ICIR / Bonferroni 校正(分母见 §7.MT) |
| **CP04** | Risk Cleanness | LLM(Python hint)| Barra residual / style_r2 / alpha_survival |
| **CP05** | Redundancy | LLM(Python hint)| max_lib_corr / nearest factor |
| **CP06** | Validation Stability | LLM(Python hint)| split_stability + expanding_window(**不是 holdout!**)|

**CP06 明确不看 holdout**。CP01-CP06 全部只用 train + validation 数据。

### `judge.md` 结构

```markdown
---
batch_id: batch_103
judged_at: 2026-04-10T05:45:00
direction: fundamental_price_divergence

candidates:
  - candidate_id: C001
    verdict: admit
    hard_gate_result: all_pass
    checkpoint_positions:
      CP01: all_pass
      CP02: aligned
      CP03: strong
      CP04: acceptable      # override
      CP05: low
      CP06: stable
    overrides:
      - checkpoint: CP04
        from: borderline
        to: acceptable
    factor_id: F020         # admit 才有
    referenced_context:
      - directions/fundamental_price_divergence.md#T001
      - lessons.md#Structural Constraints
      - batches/batch_102/judge.md#C001
    concerns:
      - checkpoint: CP04
        if: "alpha_surv < 0.6 in future batch"
        then: "重审 override 合理性"

  - candidate_id: C006
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions:
      CP01: all_pass
      CP03: weak            # fatal
    referenced_context: []

batch_summary:
  total: 6
  admit: 2
  reserve: 3
  reject: 1
  new_factors: [F020, F021]
---

# Judge Report — batch_103

## C001 — ADMIT → [[../../factors/F020]]

### CP01 Hard Gates
All pass.

### CP02 Mechanism Alignment → **aligned**
这个 candidate 的 expression... 对应 [[../../directions/fundamental_price_divergence#Hypothesis]]
的"基本面改善 × 便宜估值"双元素。

### CP03 Statistical Strength → **strong**
ICIR_val = ==0.338==, ls_tstat = 3.89。
`mt_bucket = medium`(cumulative_candidates=612 / direction_candidates=47 /
validation_exposure=102);search-adjusted strength = 0.41 仍落在 strong 档的
下界之上,因此即便扣掉多重检验折扣,本候选的统计强度仍可判 strong。

### CP04 Risk Cleanness → **acceptable** (override from borderline)

> [!warning] Override
> Python 按阈值判 borderline (style_r2=0.100)。我 override 为 acceptable。

三个支持证据:
1. `barra_residual_icir = +0.251`(正)→ 剥 Barra 后机制仍存活
2. `alpha_survival_ratio = 0.691` > 0.6
3. [[../../directions/fundamental_price_divergence#T001]] 显示 PB 比 PE 已 2× 改善

**Concern**: if 后续 batch 同类 alpha_surv < 0.6,重审 override。

### CP05 Redundancy → **low**
`max_lib_corr = 0.076` vs [[../../factors/F005]]

### CP06 Validation Stability → **stable**
split_stability = good, expanding_window_pass = true, IC 一致性 0.87

### Synthesis
5/6 positive, 1 override_upgrade (CP04) with cross-batch evidence。ADMIT。

---

## C006 — REJECT
...
```

### Python Audit 检查

```python
def audit_judge_md(path):
    md = parse_md(path)
    fm = md.frontmatter
    body = md.body
    
    # 1. Schema
    for cand in fm["candidates"]:
        assert cand["verdict"] in {"admit", "reserve", "reject", "replace"}
    
    # 2. Body 章节存在
    for cand in fm["candidates"]:
        section = extract_h2(body, cand["candidate_id"])
        expected = ["CP01"] if cand["verdict"] == "reject" \
                   else ["CP01", "CP02", "CP03", "CP04", "CP05", "CP06"]
        for cp in expected:
            assert f"### {cp}" in section
    
    # 3. Reference 真实性(grep 目标 section)
    for cand in fm["candidates"]:
        for ref in cand.get("referenced_context", []):
            assert section_exists(ref)
    
    # 4. Hard gate 不可 override
    for cand in fm["candidates"]:
        if cand["hard_gate_result"] != "all_pass":
            assert cand["verdict"] == "reject"
    
    # 5. Reference 必须来自 packet(LLM 不能自己编不在 packet 里的引用)
    packet_refs = load_packet_references(...)
    for cand in fm["candidates"]:
        for ref in cand.get("referenced_context", []):
            assert ref in packet_refs

    # 6. CP03 body 必须显式引用 mt_bucket(见 §7.MT)
    #    防止 LLM 看到 numeric_hint 但在 reasoning 里视而不见
    for cand in fm["candidates"]:
        if cand["verdict"] == "reject":
            continue  # reject 只要求 CP01
        section = extract_h2(body, cand["candidate_id"])
        cp03 = extract_h3(section, "CP03")
        assert "mt_bucket" in cp03, \
            f"{cand['candidate_id']}: CP03 must cite mt_bucket"
```

不做**语义检查** — LLM 的 reasoning 写得对不对由 LLM 的直觉负责,Python 只防漏答和造假。

---

## 8. Phase 4 — ARCHIVE

### 职责

把 judge 结果落地:归档 admit、写深度报告、更新 direction、commit。

### 流程

```
Step 1  Python(阻塞): 归档 factor.yaml
          - 分配 F{id}
          - 写 factors/F{id}.yaml
          - 创建 signal_ref 指向 batches/.../signals/

Step 2  Python(阻塞): 生成 report packet + 画 PNG
          - 算 Layer 2 derived analytics(按年/月聚合)
          - 画所有图表到 factors/F{id}/*.png
          - pack 到 _packets/report_packet_F{id}.md

Step 3  Subagent(后台,不阻塞): 写 factor.md
          - 每个 admit 一个 subagent
          - 读 packet,写 factors/F{id}.md
          - 完成时调 `research commit-report F{id}` 独立 commit

Step 4  LLM(主,阻塞): 更新 direction md
          - 追加 Narrative Log
          - 更新 thread evidence trail
          - (可能)改 frontmatter status

Step 5  Python(阻塞): 主 commit
          - refresh INDEX 下半段
          - update state.yaml
          - research commit {batch_id}
          - 不含 factor.md(后台生成,独立 commit)
```

### Python 因子归档(R8 补充)

Step 1 归档时,如果 candidate 是 `source_type: python`,额外做:

```python
def archive_python_factor(candidate, new_factor_id):
    src = Path(f"batches/{batch_id}/python_candidates/{candidate.candidate_id}.py")
    dst = Path(f"python_factors/{new_factor_id}_{factor_name}.py")
    shutil.copy(src, dst)
    # factor.yaml 里记录 python_ref 指向 dst(相对于 storage/)
```

DSL 因子没有这一步(expression 字符串直接在 factor.yaml 里)。

### `factor.yaml` schema

```yaml
factor_id: F020
name: triple_product_80d_pb
source_type: dsl                          # dsl | python
expression: "Mul(Mul(CsRank(...)),CsRank(Mul($pb_ratio,-1)))"
# 如果 source_type=python,没有 expression,改为:
# python_ref: python_factors/F022_shadow_kalman_v2.py

direction: fundamental_price_divergence
family_tag: fundamental_value_catalyst    # 字符串,无 registry

# Lineage
parent_batch: batch_102
parent_candidate_id: C004
lineage_transformation: "extend_lookback_60d_to_80d"

# Verdict trace
admitted_at: 2026-04-11T11:30:00Z
admitted_batch: batch_103
judge_ref: batches/batch_103/judge.md#C001
result_ref: batches/batch_103/result.yaml#C001
signal_ref: batches/batch_103/signals/C001.parquet

status: active   # active / retired / under_review

metrics:
  effect: {ic_ir_validation: 0.338, ...}
  risk: {style_r_squared: 0.100, alpha_survival: 0.691, ...}
  redundancy: {max_lib_corr: 0.076, nearest_factor_id: F005}
  feasibility: {coverage: 0.976, turnover: 0.029, half_life: 5.0}
  # 没有 holdout 字段!
```

### `factor.md` 结构(Q46 修正版)

```markdown
---
factor_id: F020
name: triple_product_80d_pb
direction: fundamental_price_divergence
status: active
verdict: admit
---

# F020 — triple_product_80d_pb

## Section 0 — Top Insight(全文核心洞察)

> [!success] Verdict: ADMIT

### 经济学逻辑
<LLM 2-3 段:这个公式在捕捉什么 + 为什么有 alpha + 为什么不被套利>

### 毒舌评论(基于因子公式本身,不是基于指标)
<LLM 1-2 段:结构缺陷 / 结构巧思 / 可能的伪成功>

### 核心指标
[KPI 表]

![[F020/radar.png]]

## Section 1 — 6 维度指标
[LLM 逐维度 1-2 段解读]

## Section 2 — 逐图解读(抓特点)
### IC 时序
![[F020/ic_timeseries.png]]
**特点**: <LLM 2-4 句,引用具体数字>

### 分组收益
![[F020/quintile_bar.png]]
**特点**: ...

(每张图一节)

## Section 3 — Judge Verdict Trail
[引用 batches/batch_103/judge.md#C001]

## Section 4 — Research Context
See [[../directions/fundamental_price_divergence]] for hypothesis, 
  thread evidence trail, and siblings.

Lineage: [[../../batches/batch_102/manifest#C004]] (60d parent)
Siblings: [[F018]], [[F019]]
```

**关键**:Section 4 只用 `[[link]]` 引用 direction,不复制内容。direction 一变 link 跟着变,不需要重写 factor.md。

### Direction md 更新

**Python 自动更新**(frontmatter):
```yaml
rounds: 5               # ++
admits: 3               # ++
last_batch: batch_103
last_activity: 2026-04-11
members: [F018, F019, F020]   # append
```

**LLM 更新**:
- `status` 字段(如果转换)
- `priority` 字段(如果调整)
- Narrative Log 段(追加本轮总结)
- Thread evidence trail(本 batch 相关的 thread)

**Reject 的处理**:在 Narrative Log 里一行摘要,完整 reasoning 留在 `judge.md`。**不开独立 Failure Registry**。

### Git commit(主 + report)

**主 commit**(Python 同步):
```
[mine] batch_103 | fundamental_price_divergence | admits=1 rejects=3 reserves=2

Admitted: F020 (triple_product_80d_pb)
Direction: fundamental_price_divergence (rounds=5, total admits=3)
Batch goal: 验证 80d lookback 减少 C004 crowding

Co-Authored-By: Claude ...
```

**Report commit**(subagent 后台,每个 factor 一条):
```
[report] F020 triple_product_80d_pb report generated
```

### 后台 subagent 协议

```yaml
subagent_report_F020:
  inputs: [_packets/report_packet_F020.md]   # 唯一输入
  outputs: [factors/F020.md]                  # 唯一输出
  allowed_reads: [_packets/report_packet_F020.md]
  allowed_writes: [factors/F020.md]
  forbidden:
    - 读任何其他文件
    - 调 Qlib / DB / 网络
    - Follow [[link]](packet 已内嵌所有必要段落)
  on_complete:
    run(f"research commit-report F020")
  on_failure:
    log to _subagent_failures.log
    主循环不受影响(factor.yaml 已 committed)
```

### Commit 失败处理

**硬 fail**(修 Q47.3):
- pre-commit hook 失败 → raise,下一轮 mine 不启动
- 用户手动处理完再继续
- 不静默跳过

### 幂等性保证(修 Q32)

Phase 4 ARCHIVE **必须幂等**。重跑同一 batch 不应该产生副作用:

```python
def phase4_archive(batch_id: str) -> None:
    state = load_state()
    
    # 前置检查:batch 必须是 "judged",不能是已 archived
    bu = ... # 从 state 或目录存在性推断
    current_phase = state.get("current_batch_phase")
    if current_phase == "archived" and state.get("last_batch") == batch_id:
        raise ValueError(
            f"Batch {batch_id} already archived. "
            f"Use `research state rollback` to undo."
        )
    if current_phase != "judged":
        raise ValueError(f"Batch {batch_id} not in judged phase (current: {current_phase})")
    
    # ... 执行 5 步 ...
    
    # 完成后状态转换
    state["current_batch_phase"] = "archived"
    state["last_batch"] = batch_id
    state["current_batch"] = None
    save_state(state)
```

**保证**:
- 同一 batch 第二次调 archive → raise
- 如果用户真的想重跑,必须显式 `research state rollback` 先回退
- 所有 Python 写入(factor.yaml 新分配 F{id}、direction counter ++ 等)都依赖 "current_phase == judged" 这个前置,不会被重复应用

---

## 9. Phase 5 — CONSOLIDATION

### 职责

LLM 周期性重写 memory/md,合并 / 压缩 / 提升 / 归档。**整体重构,非增量**。

### 触发

**自动触发**(任一满足):
```yaml
consolidation:
  auto_triggers:
    rounds_since_last: 10           # 每 10 个 batch
    lessons_max_lines: 400          
    direction_max_lines: 500        
    total_active_directions: 20
  parallelism:
    max_concurrent_subagents: 6
```

**手动触发**:
```bash
research consolidate                              # 整体
research consolidate --target lessons             # 只 lessons
research consolidate --target directions          # 只所有 direction
research consolidate --target direction:{tag}     # 只某个 direction
research consolidate --dry-run                    # 生成 packet 不写
```

### 流程

```
Step 1  Python: 前置检查
          - git status clean(上一轮 Phase 4 commit 完成)
          - 没有 pending _subagent_failures.log
          - state.current_batch is None
          - 检查触发条件(manual / auto)

Step 2  Python: 并行 pre-pack
          - _consolidation/packet_lessons.md
          - _consolidation/packet_direction_{tag}.md  × N
          - (index packet 在 Step 4 才生成)

Step 3  Subagent(并行): 重写所有 lessons + direction
          - 每个 md 一个 subagent
          - 只读一份 packet,只写一份目标 md
          - 等所有 subagent 完成

Step 4  Subagent(同步,最后一步): 重写 INDEX
          - pack_index_packet(读刚重写的 direction md)
          - 单个 subagent 写 INDEX 上半段
          - Python 写 INDEX 下半段统计

Step 5  Python: 单一 commit
          - git add storage/evidence/vault/
          - commit msg: [consolidate] round N: ...
          - LLM 顺手 append _meta/consolidation_log.md
          - state.rounds_since_last_consolidation = 0
          - 清理 _consolidation/ 临时目录
```

### Subagent 协议(sandbox)

每个 consolidation subagent:
- 读一份独立 packet.md
- 写一份独立目标 md
- 禁止跨文件读写
- 失败 → 整个 consolidation 硬 fail,已完成的产物也不保存(用户 `git reset --hard HEAD^` 回退)

### Factor.md 不进 consolidation

`factors/F*.md` **不被 consolidation 重写**。Section 4 "Research Context" 只用 `[[link]]` 指向 direction,direction 一变 link 自动跟着。factor.md 是"一次性归档产物"。

### 回滚

Consolidation 是**独立 commit**。用户不满意 → `git reset --hard HEAD^` 即可回退。不需要额外备份机制。

### 不变量:Phase 4 和 Phase 5 永不并发(修 Q33 + Q36)

**系统保证**:
- Phase 4 在一个 batch 的 lifecycle 内执行,每 batch 一次
- Phase 5 只在 `git status clean + state.current_batch is None` 前置下启动
- 因此 Phase 4 的 "LLM 写 direction Narrative Log" 和 Phase 5 的 "LLM 重写 direction.md" **不会并发**
- Narrative Log 段落的写入只有一个 writer at any time,无 handshake 风险

这是老系统 3.5a/3.5b 并发 bug(Q33 + Q36)的根因修复。通过"**用 git commit 边界隔离 phase**"替代"**用文件锁隔离 writer**"。

### `consolidation_log.md`(append-only)

```markdown
## 2026-04-15 round 45(auto-trigger: rounds_since_last=10)

**Rewrite targets**: lessons.md + 8 directions/*.md + INDEX.md

**Key changes**:
- lessons.md: 新增 "Rank on denominator 注意" 一行
- fundamental_price_divergence.md: T001 answered, narrative 6→2 段, rounds 4→5
- volume_autocorrelation.md: productive → saturated(9 rounds 无新 insight)
- pv_corr_short_term.md: merged into [[fundamental_liquidity_interaction]]
- INDEX: 新增 Saturated 区

**Commit**: abc1234
**Rollback**: `git reset --hard HEAD^`
```

---

## 10. 核心文件 Schema

### `state.yaml`(系统唯一状态)

```yaml
# Current
current_batch: null                  # 或 batch_103 / null
current_batch_phase: null            # designed / executing / judged / archived / null
last_batch: batch_102
round: 43

# Direction tracking
last_activity: 2026-04-11T11:45:00Z

# Consolidation
rounds_since_last_consolidation: 3
```

### `config.yaml`(系统配置)

```yaml
universe: csi1000
qlib_data_dir: ~/.qlib/qlib_data/cn_data_1d

sample_policy:
  sample_policy_version: v3
  train_range: [2015-01-01, 2021-12-31]
  validation_range: [2022-01-01, 2023-12-31]
  holdout_range: [2024-01-01, 2024-12-31]   # 只 research holdout-review 用

universes:
  primary: csi1000                          # 判决基准 — CP01-CP06 只看这个
  reference:                                # 参考 universe — 对比 context,不影响 admit
    - csi300
    - csi500
    - all                                   # 全市场(所有 tradable symbols)

evaluation:
  # 每个 horizon 都做完整 metrics(effect / mono / risk / ls_tstat),给 LLM 看多状态
  horizons: [1, 5, 10]                # 完整 metrics 的 horizon 列表
  primary_horizon: 5                  # 判决基准 — CP01-CP06 只看 h5 的 metrics
  
  # IC decay 曲线(更细的 horizon 序列,只产出 ic 数字,不是完整 metrics)
  decay_horizons: [1, 3, 5, 10, 20, 30]
  
  quintile_bins: 5

preprocess:
  winsorize_mad_k: 5
  winsorize_mad_scale: 1.4826        # MAD → std 近似系数(正态分布)
  zscore: true
  neutralize: false                  # 默认关,Barra 事后检验足够
  
  tradability:
    volume_zero_means_suspended: true
    limit_up_tolerance: 0.999        # close >= limit_up * 0.999 → 涨停
    limit_down_tolerance: 1.001      # close <= limit_down * 1.001 → 跌停
    new_stock_buffer_days: 60        # 上市未满此日不参与评估

thresholds:
  # CP03 Statistical Strength
  icir_strong: 0.30                  # primary horizon ICIR 阈值(raw,未 search-adjusted)
  icir_weak: 0.15
  # Bonferroni / multiple testing 不在这里配置!
  # 完整方案见 §7.MT,由 compute_mt_budget() 从 git batches/ 扫出
  # log1p 加权公式的常量:
  mt_budget:
    cumulative_scale: 600            # log(600),累计 candidate 数的归一化
    direction_scale: 80              # log(80),单 direction 内累计
    validation_exposure_scale: 40    # 线性,当前 sample_policy 下被复用的 batch 数
    weight_cumulative: 0.50
    weight_direction: 0.30
    weight_validation_exposure: 0.20
    bucket_low_max: 0.40             # mt_score < 0.40 → low
    bucket_medium_max: 0.70          # 0.40 ≤ mt_score ≤ 0.70 → medium
    search_adjusted_factor: 0.5      # search_adjusted_strength = raw * (1 - 0.5 * mt_score)
  
  # CP04 Risk Cleanness
  style_r2_acceptable: 0.08
  style_r2_poor: 0.12
  alpha_surv_min: 0.60
  barra_residual_icir_min: 0.10      # 残差 ICIR 正值门槛
  
  # CP05 Redundancy
  max_lib_corr_low: 0.30             # < low → 完全独立
  max_lib_corr_high: 0.70            # > high → 近重复,reject
  
  # CP06 Validation Stability
  expanding_window_ic_stability_good: 0.75
  expanding_window_ic_stability_poor: 0.40
  
  # Feasibility(不按 horizon 分)
  coverage_min: 0.80                 # factor value 覆盖率
  half_life_max: 25.0                # 自相关推导的半衰期上限(日)

consolidation:
  auto_triggers:
    rounds_since_last: 10
    lessons_max_lines: 400
    direction_max_lines: 500
    total_active_directions: 20
  parallelism:
    max_concurrent_subagents: 6
```

### `manifest.yaml`(Phase 1 冻结)

```yaml
batch_id: batch_103
round: 43
created_at: 2026-04-11T10:00:00Z
direction: fundamental_price_divergence
direction_md_ref: vault/directions/fundamental_price_divergence.md

batch_goal: |
  验证 80d lookback 是否减少 C004 triple product crowding。
  推进 T002 multi-metric amplification open question。

active_threads_referenced: [T002]

sample_policy: {...from config snapshot...}

candidates:
  # DSL 候选(default 路径)
  - candidate_id: C001
    source_type: dsl
    expression: "Mul(Mul(CsRank(Sub(...80d...)),CsRank(...80d...)),CsRank(Mul($pb_ratio,-1)))"
    rationale: |
      80d lookback 版本的 triple product。60d 版本(batch_102 C004)
      有 crowding=medium,80d 窗口应该扩散 qualifying universe。
    parent_batch: batch_102
    parent_candidate_id: C004
    transformation: "extend_lookback_60d_to_80d"
  
  # Python 候选(escape hatch)
  - candidate_id: C003
    source_type: python
    python_ref: python_candidates/C003.py    # 相对于 batches/batch_103/
    dependencies: ["$close", "$pe_ratio", "$pb_ratio"]   # 冗余声明(与 .py 里的 REQUIRED_FIELDS 必须一致)
    rationale: |
      多步 conditional rerank: 先按 EPS change 过滤 top 20%,再在子集内按 PB rerank。
      DSL 无法表达 "先 filter 再 rerank" 的两阶段 pipeline(If 只能对每行独立条件)。
      引用 lessons.md#Path Selection 场景 3(多步条件 pipeline)。

  - candidate_id: C002
    ...

frozen_at: 2026-04-11T10:15:00Z
```

### `result.yaml`(Phase 2 产出)

```yaml
batch_id: batch_103
computed_at: 2026-04-11T11:00:00Z
sample_policy:
  train_range: [2015-01-01, 2021-12-31]
  validation_range: [2022-01-01, 2023-12-31]
  sample_policy_version: v3
  # 注意:没有 holdout_range(LLM 看不到 holdout 存在)

candidate_results:
  - candidate_id: C001
    source_type: dsl                   # dsl | python
    expression: "..."
    signal_ref: batches/batch_103/signals/C001.parquet
    compute_error: null

    primary_horizon: 5                 # 判决基准
    primary_universe: csi1000

    # === 不依赖 forward return 的字段(只算一次,不按 horizon 分)===
    redundancy:
      max_lib_corr: 0.076
      nearest_factor_id: F005
      second_nearest: {factor_id: F009, corr: 0.043}
    
    feasibility_static:
      coverage: 0.976                  # factor value 覆盖率(和 horizon 无关)
      half_life_autocorr: 5.0          # 从 factor value 自相关推导
    
    stability_meta:                    # 单 horizon 的稳定性(取 primary)
      split_stability: good
      expanding_window_pass: true
      expanding_window_ic_stability: 0.87

    # === Per-horizon × primary universe:完整 metrics(CP01-CP06 判决基础)===
    per_horizon:
      h1:
        effect:
          ic_mean_train: 0.029
          ic_mean_validation: 0.024
          ic_ir_train: 0.312
          ic_ir_validation: 0.198
          ic_win_rate_validation: 0.542
          ls_tstat: 2.15
        monotonicity:
          validation: 0.7
        risk:
          alpha_survival_ratio: 0.412
          barra_residual_ic: 0.011
          barra_residual_icir: 0.089
          style_r_squared: 0.087
          dominant_style: str_1m
        feasibility_turnover: 0.18     # 短期因子换手高
      
      h5:                              # ← primary_horizon
        effect:
          ic_mean_train: 0.041
          ic_mean_validation: 0.046
          ic_ir_train: 0.453
          ic_ir_validation: 0.338
          ic_win_rate_validation: 0.607
          ls_tstat: 3.89
        monotonicity:
          validation: 1.0
        risk:
          alpha_survival_ratio: 0.691
          barra_residual_ic: 0.032
          barra_residual_icir: 0.251
          style_r_squared: 0.100
          dominant_style: ep_ratio
          style_exposures:
            ep_ratio: 0.232
            book_to_price: 0.045
            ...
        feasibility_turnover: 0.029
      
      h10:
        effect:
          ic_mean_validation: 0.051
          ic_ir_validation: 0.312
          ls_tstat: 3.48
        monotonicity:
          validation: 0.9
        risk:
          alpha_survival_ratio: 0.704
          barra_residual_icir: 0.212
          style_r_squared: 0.095
        feasibility_turnover: 0.011

    # === Derived analytics(只对 primary horizon 做,按年月聚合)===
    derived_analytics:
      ic_yearly:
        - {year: 2015, ic_mean: 0.082, ic_std: 0.14, ic_ir: 0.58}
        - {year: 2016, ic_mean: 0.031, ...}
      quintile_by_year:
        - {year: 2015, Q1: 0.174, Q2: 0.096, Q3: 0.078, Q4: 0.046, Q5: 0.004}
      ic_decay_by_horizon:                # 细粒度 decay 曲线
        - {h: 1, ic: 0.024}
        - {h: 3, ic: 0.041}
        - {h: 5, ic: 0.046}
        - {h: 10, ic: 0.051}
        - {h: 20, ic: 0.036}
        - {h: 30, ic: 0.022}
    
    # === Reference universes × primary horizon:lite metrics(对比用)===
    universe_comparison:
      csi300:
        h5:
          ic_ir_validation: 0.412
          ls_tstat: 4.21
          mono_validation: 1.0
      csi500:
        h5:
          ic_ir_validation: 0.287
          ls_tstat: 2.98
          mono_validation: 0.8
      all:
        h5:
          ic_ir_validation: 0.198
          ls_tstat: 2.34
          mono_validation: 0.6
    
    # 绝对没有 holdout 字段(Q18 + holdout 隔离)
```

### `direction.md`(Rule A frontmatter + Rule B body)

```markdown
---
direction_tag: fundamental_price_divergence
status: productive           # exploring | productive | saturated | dead | merged
priority: high               # high | medium | low
rounds: 5
admits: 3
last_batch: batch_103
last_activity: 2026-04-11
created_batch: batch_099
members: [F018, F019, F020]
---

# Direction: Fundamental-Price Divergence

## Hypothesis
基本面改善速度 × 便宜估值 conditioner → barra-clean 价值重估 alpha。
<详细叙述...>

## Current Focus
验证三元乘积 (EPS × Revenue × low PS) 能否突破单指标 ICIR 上限,
同时保持 style_r2 < 0.15。

## Threads

### T001: Conditioner Barra cleanliness [✓ ANSWERED batch_102]
**Question**: PE/PB/PS 三种 conditioner 哪种最 barra-clean?
**Evidence trail**:
- batch_099: PE,证伪
- batch_101: PB,style_r2=0.187 不足
- batch_102: PS,style_r2=0.049 confirmed
**Answer**: PS < PB < PE 的层级已确认。

### T002: Multi-metric amplification [◉ ACTIVE]
**Question**: 三元乘积能否突破单指标 ICIR 上限?
**Evidence trail**:
- batch_102: C004 (60d) ICIR=0.352, crowding=medium (blocker)
- batch_103: F020 (80d) ICIR=0.340, crowding=low ← ✓
**Next probes**:
- triple 80d PS variant
- 120d exploration
- Sector neutralization

## Known Failures
- `Sub(CsRank(fundamental), CsRank(price))` → str_1m trap
- PE conditioner → 永久排除
- Book value CHANGE metric → dominated by book_to_price

## Related
- [[../lessons]] for system constraints
- [[timing_range]] - similar conditioner issue

## Narrative Log

### 2026-04-11 batch_103
Admitted [[../factors/F020|F020]] triple 80d PB。80d 减少 crowding(medium → low),
ICIR 维持 0.34。T002 部分回答:80d 是正确方向,下一轮探索 PS 变体。

Rejected: C002 (weak), C005 (style contamination).

### 2026-04-10 batch_102
双 admit (F018, F019)。PS conditioning 确认为最干净。T001 answered.

...
```

### `lessons.md`(Rule B,system-level facts only)

```markdown
# Research Lessons (system-level facts)

> 这个文件记录系统级不变约束。不记录方向级机制洞察 —— 那些在
> [[INDEX]] 和各 direction md 里。
> 
> 修改这个文件意味着你发现了系统的一个事实。

## Data Facts
- **`$vwap`**: 字段永远是 0,source 未填充。任何使用 → NaN
- **`$amount`**: 人民币金额(不是股数)
- **`$volume`**: 股数(不是金额)
- **Universe**: csi1000(csi1000 约 1000 只,主板 + 中小板 + 创业板)
- **科创板 / 北交所**: cache 构建时已过滤,不在 universe 内

## Operator Registry
- **Available**: Mean, Std, Corr, Sub, Div, Mul, Add, Ref, CsRank, CsZscore, 
                 TsRank, TsMax, TsMin, Rank, Delta, Log, If, Less, Greater, 
                 IdxMax, IdxMin, TsAutoCorr, Abs, Power, Sign, Cov
- **UNAVAILABLE**: `Neg`(用 `Mul($x, -1)`)、`SMA`(用 `Mean`)
- **CsRank / CsZscore 全市场行为**:永远在全市场(~5000 symbols)计算,不受 universe 限制。
  含义:`CsRank($value)` 对一个 csi1000 因子来说,rank 的分母是**全市场**不是 csi1000。
  如果想在 universe 内 rank,需要显式构造:`Rank($value, window)` 或在 post-process 层过滤。
  这是 Qlib 的固定行为,系统接受它(Q15)。

## Evaluation Horizon
- **Primary horizon**: `t+1 到 t+5` 累计收益(config.yaml 默认)
- **涨跌停 bias**:因子值在涨跌停日被 mask 为 NaN(tradable=False),但前向 return 的计算
  基准是 close-to-close。对**长期因子**(half_life > 10d)这个 bias 可以忽略,对**短期因子**
  (half_life < 3d)要警惕:t 日涨停导致的价格 overshoot 可能污染 t+1 的 IC。
  建议:短期因子应该在 rationale 里说明是否已考虑此问题。

## Path Selection: DSL vs Python

> ⚠️ **LLM 在 Phase 1 DESIGN 时必读本节**。用于自主判断每个候选是用 DSL 还是 Python。

### 默认规则
**DSL 是 default。Python 是 escape hatch**。写候选时先假设用 DSL,只在确认 DSL 无法表达时才用 Python。

### 决策流程(LLM 必须按顺序过这 4 步)

```
Step 1  我想做什么(机制层面)?
        ↓
Step 2  DSL 的算子能直接表达吗?
        (Mean/Std/Corr/Cov/Sub/Div/Mul/Add/Ref/CsRank/CsZscore/
         TsRank/TsMax/TsMin/Rank/Delta/Log/If/Less/Greater/
         IdxMax/IdxMin/TsAutoCorr/Abs/Power/Sign)
        → 能 → 用 DSL ✅
        → 不能 → Step 3
        ↓
Step 3  通过 DSL 算子的组合(即使表达式很长)能表达吗?
        → 能 → 用 DSL ✅(写长一点无妨,比 Python 安全)
        → 不能 → Step 4
        ↓
Step 4  属于下面 5 类"真必须 Python"的场景吗?
        → 是 → 用 Python ✅
        → 否 → 回到 Step 1 重想,可能漏了 DSL 方案
```

### 必须用 Python 的 5 类场景

**场景 1 — 多步条件 pipeline**
先按 X 过滤 top/bottom N%,再在过滤后的子集里按 Y rank,再用 Z 加权。
- DSL 的 `If(cond, a, b)` 只能对每行独立条件,不能做"先选 top-K 再 rank"的两阶段
- 例子:"先按 EPS change 选 top 20%,再在这 20% 里按 PB rerank"

**场景 2 — 迭代状态**
需要跨时间传递状态的算法。
- EMA 自适应 decay(decay rate 动态调整)
- Kalman filter(状态递推)
- Online regression(滚动更新系数)
- DSL 没有 state-passing 机制,Mean/Std 都是 window-based 的无状态计算

**场景 3 — 跨 asset 聚合**
需要在 symbol 之间做非 rank-based 的复杂聚合。
- "Top 50 市值股的平均 EPS 作为基准,再让每个 symbol 减掉它"
- Sector-level 聚合再 broadcast 回 symbol
- DSL 的 CsRank 是 rank-based 的,没有 top-N selection 的语义

**场景 4 — 复杂数学变换**
需要矩阵/线性代数运算。
- FFT,PCA,eigenvalue decomposition
- 回归残差(非 Barra 的自定义回归)
- DSL 没有矩阵运算

**场景 5 — Legacy 复杂因子**
某些 Alpha101 公式包含复杂 conditional,无法纯 DSL 表达。
- alpha005 / alpha033 / alpha043 等
- 如果是直接移植老代码,允许用 Python

### Red Flags — 不允许用 Python 的理由

这些**不是**用 Python 的正当理由,看到就要回到 DSL:

- ❌ "Python 写起来更方便"
- ❌ "我对 DSL 不熟"
- ❌ "这样更灵活"
- ❌ "DSL 表达式太长"(长没关系,长过 MAX_EXPRESSION_DEPTH=10 才是问题)
- ❌ "我想用某个 pandas 的特殊方法"(大多数有 DSL 等价)

### 看起来需要 Python 但 DSL 其实能做的反例

| 看起来需要 Python | 实际用 DSL |
|---|---|
| Rolling correlation | `Corr(x, y, window)` |
| Rolling rank | `TsRank(x, window)` |
| Cross-sectional z-score | `CsZscore(x)` |
| Conditional factor("if A then B else 0") | `Mul(f, If(cond, 1, 0))` |
| EMA(近似) | `Mean(x, window)` |
| Lagged value | `Ref(x, lag)` |
| Absolute change | `Sub(x, Ref(x, lag))` |
| Percentage change | `Div(Sub(x, Ref(x, lag)), Ref(x, lag))` |
| 自相关 | `TsAutoCorr(x, lag)` |

### Python 因子的硬约束

如果最终用 Python:
- **完全向量化**:禁 `for` over rows/dates/symbols
- **Imports 白名单**:只允许 `pandas`, `numpy`, `math`, `functools`, `itertools`, `collections`, `typing`
- **禁危险 builtins**:`open`, `eval`, `exec`, `compile`, `__import__`, `getattr`, `setattr`
- **签名契约**:必须有 `REQUIRED_FIELDS: list[str]`, `VECTORIZED = True`, `compute(market_df, params) -> pd.Series`
- **不访问外部状态**:无 filesystem / network / subprocess / 全局变量

## Structural Constraints (A-share)
- **No short-side alpha**: Factor alpha 必须来自 Q1(long),不能依赖 Q5 空头
- **No market-cap proxy**: 拒绝 abs(corr) > 0.3 to `$market_cap` / `$circ_market_cap`

## Expression Construction Notes
- **Long lookback warmup**: `Ref(X, 250)` 在 2015 年初数据不足,会产生 NaN 前缀
- **Zero-variance traps**: `Corr(x, y, w)` 在 0 方差日返回 NaN
- **CsRank on denominators**: 对 `Div(a, CsRank(b))` 注意 b=0 的情况
```

### `INDEX.md`(MOC)

```markdown
# Research Directions Index

> 本文档是研究系统的 MOC。每轮 Phase 1 START 时 LLM 只读这个 +
> 可能选中的 1-2 个 direction md。不要一次读全部 direction。

## Active Directions(按 priority)

### [[directions/fundamental_price_divergence]]  ★ high
- Status: productive | Rounds: 5 | Admits: 3 (F018, F019, F020)
- **Current focus**: PS variant of triple product, 120d exploration
- Last: batch_103

### [[directions/timing_range]]  ★ medium
- Status: productive | Rounds: 7 | Admits: 3
- ...

## Saturated / Retired

- [[directions/volume_autocorrelation]] — saturated batch_058, ICIR ceiling 0.32, 2 members
- [[directions/shadow_amihud]] — saturated, anchored by F002

## Dead / Merged

- [[directions/pv_corr_short_term]] — dead (batch_042 证伪)

## Cross-Reference
- See [[lessons]] for system-level facts
- See [[factors/F018]], [[factors/F019]], ... for admitted members

---
<!-- Auto-generated by Python. LLM do not edit below. -->

## Statistics
| direction | status | rounds | admits | last_batch |
|---|---|---|---|---|
| fundamental_price_divergence | productive | 5 | 3 | batch_103 |
| volume_autocorrelation | saturated | 9 | 2 | batch_058 |
| ... | ... | ... | ... | ... |
```

---

## 11. 缓存与向量化

### 缓存层次

| 层 | 位置 | 刷新方式 | 生命周期 |
|---|---|---|---|
| L1 内存 | Phase 内传递 | 每次 Phase 2 开始加载一次 | 一轮迭代 |
| L2 Market cache | `cache/market_daily.parquet` | 手动 `research cache refresh` | 永久,按需刷新 |
| L2 Barra cache | `cache/barra_factors.parquet` | 手动 | 永久 |
| L3 Factor value cache | `cache/factor_values/{hash}.parquet` | 按 expression hash 自动 | 永久(无 eviction)|
| Batch signal 副本 | `batches/batch_{N}/signals/{cid}.parquet` | Phase 2 生成 | 永久(和 batch 同寿)|
| Library signal | `factors/F{id}.signal_ref` 指向 batch 目录 | 随 factor 创建 | 永久 |

### Cache key 策略

```python
factor_value_cache_key = sha256(
    f"{expression}|{sample_policy_version}|{preprocess_version}"
)
```

`sample_policy_version` 或 `preprocess_version` 变化 → cache 自动失效(hash 变)。

### 向量化规范

#### 硬禁令

```python
# ❌ 以下模式在 Phase 2 代码里禁用
for i, row in df.iterrows(): ...
for date in df.index.get_level_values("time").unique(): ...
for cand in candidates: compute_metric(cand)
for h in horizons: compute_decay(h)
```

#### 必须向量化的运算

| 运算 | 向量化方法 |
|---|---|
| Cross-sectional rank | `df.groupby(level="time")["value"].rank()` |
| Daily Rank IC | `df.groupby(level="time").corr(method="spearman")` 批量 |
| Rolling IC | `pd.concat([fdf, rdf]).groupby("time").rank().rolling(w).mean()` |
| Quintile return | `groupby(["time", pd.qcut(value, 5)])["ret"].mean()` |
| Multi-horizon IC decay | 构造 shifted matrix 一次 `corrwith` |
| Redundancy(vs library)| `factor_wide.corrwith(library_wide, method="spearman")` batch |
| Barra OLS(252 日)| `np.linalg.pinv` + `np.einsum` 批量 3D tensor |
| Feasibility(coverage/turnover/half_life)| `groupby + agg` 批量 |

#### 多 universe 评估("算一次,切多次")

**核心原则**:factor value 在**全市场**算一次,指标统计按不同 universe 分别做。**不增加计算成本的 bottleneck**(factor value 和 market load 只一次)。

```python
def compute_metrics_multi_universe(factor_tensor, returns, barra_df, config):
    universes = config["universes"]
    primary = universes["primary"]                # csi1000
    references = universes.get("reference", [])   # [csi300, csi500, all]
    
    # 一次性加载所有 universe 的成分股 mask(从 DB index_constituents 读)
    masks = {}
    for uname in [primary] + references:
        masks[uname] = load_universe_mask(uname)   # (time × symbol) bool,None 表示全市场
    
    result = {}
    
    # Primary universe:full metrics(含 Barra)
    result["primary"] = compute_full_metrics(
        factor_tensor, returns, barra_df,
        universe_mask=masks[primary],
    )
    
    # Reference universe:lite metrics(只 IC/mono/ls_tstat,不算 Barra 省时间)
    result["reference"] = {}
    for ref_uname in references:
        result["reference"][ref_uname] = compute_lite_metrics(
            factor_tensor, returns,
            universe_mask=masks[ref_uname],
        )
    
    return result


def apply_universe_mask(factor_tensor, mask):
    """把非 universe 内的 symbol 设 NaN,vectorized groupby 会自动忽略 NaN"""
    if mask is None:
        return factor_tensor
    return factor_tensor.where(mask, np.nan)


def compute_lite_metrics(factor_tensor, returns, universe_mask):
    """简化版,只算核心统计,不做 Barra 回归"""
    masked = apply_universe_mask(factor_tensor, universe_mask)
    return {
        "ic_ir_validation": vectorized_rank_ic(masked, returns)["ir"],
        "ls_tstat": vectorized_ls_tstat(masked, returns),
        "mono": vectorized_monotonicity(masked, returns),
    }
```

**成本 breakdown**(假设 primary + 3 个 reference):

| 步骤 | 成本 |
|---|---|
| Load market_daily | 1× fixed(几秒) |
| Compute factor value(全市场) | 1× fixed(最贵,~30s batch)|
| Primary full metrics(含 Barra) | 1× ~10s |
| Reference lite metrics × 3 | 3× ~2s = 6s |
| **总耗时增量** | **~6s(≈ 10% overhead)** |

**结论**:多 universe 对比的成本是**次线性增长**,可以接受。

#### Universe mask 的构建(用 Qlib 内建机制)

**重要**:universe 定义的 canonical source 是 **Qlib 的 instruments 文件**
(`~/.qlib/qlib_data/cn_data_1d/instruments/{name}.txt`),不是 DB。

`scripts/sync_index_constituents.py` 已经把 DB `index_constituents` 同步到
Qlib instruments 文件(格式:`symbol\tstart_date\tend_date`,每个 symbol 一行或多行断续 interval)。
Phase 2 直接用 Qlib 的 `D.instruments()` 读取,不再查 DB。

```python
from qlib.data import D

def load_universe_mask(uname: str, time_index: pd.DatetimeIndex) -> pd.DataFrame | None:
    """
    从 Qlib instruments 文件加载 universe 定义,转成 (time × symbol) bool mask。
    
    Args:
        uname: universe 名称(csi300/csi500/csi1000/all)
        time_index: 目标时间索引(用于构造 mask shape)
    
    Returns:
        (time × symbol) bool DataFrame, True = 该日该股在 universe 内
        None 表示全市场(下游跳过 mask 应用,等价于全 True)
    """
    if uname == "all":
        return None
    
    # Qlib 的 instruments dict
    insts = D.instruments(uname)
    
    # 展开 dict 到 {symbol: [(start, end), ...]}
    active_intervals = D.list_instruments(
        insts,
        start_time=time_index[0],
        end_time=time_index[-1],
        as_list=False,
    )
    
    # 向量化构造 bool matrix
    symbols = sorted(active_intervals.keys())
    mask = pd.DataFrame(False, index=time_index, columns=symbols)
    for sym, intervals in active_intervals.items():
        for start, end in intervals:
            start_ts = pd.Timestamp(start)
            end_ts = pd.Timestamp(end)
            mask.loc[start_ts:end_ts, sym] = True
    
    return mask
```

**为什么用 Qlib 而不是查 DB**:
- **Qlib instruments 是 canonical source**(sync 脚本已经从 DB 同步过来)
- 避免第二次 DB 连接,纯内存 + 文件读取
- 和 Qlib 的其他 API 一致(`D.features` 也用同样的 instruments dict)
- 未来如果 universe 定义从 Qlib 变了,不需要改 research 代码

**Universe refresh 的 CLI**:
```bash
research cache refresh universes        # 重跑 sync_index_constituents 更新 Qlib instruments
```

实际上就是调用 `scripts/sync_index_constituents.py --all` 的新封装。

#### Barra 残差 IC 批量解法(修 Q23)

```python
def vectorized_barra_residual_ic(factor_tensor, barra_df, returns):
    """
    factor_tensor: DataFrame (time, symbol) × candidates
    barra_df: DataFrame (time, symbol) × barra_factors
    returns: Series (time, symbol)
    
    一次 OLS 处理所有 (date, candidate),用 np.linalg.pinv + einsum
    """
    dates = factor_tensor.index.get_level_values("time").unique()
    n_dates = len(dates)
    n_barra = barra_df.shape[1]
    n_cand = factor_tensor.shape[1]
    
    # Reshape to 3D tensors
    X = reshape_barra_to_3d(barra_df)        # (n_dates, n_symbols, n_barra)
    Y = reshape_factor_to_3d(factor_tensor)  # (n_dates, n_symbols, n_cand)
    
    # Batch pseudo-inverse and OLS
    pinv = np.linalg.pinv(X)                 # (n_dates, n_barra, n_symbols)
    beta = np.einsum("dbs,dsc->dbc", pinv, Y)  # (n_dates, n_barra, n_cand)
    fitted = np.einsum("dsb,dbc->dsc", X, beta)
    residual = Y - fitted                    # (n_dates, n_symbols, n_cand)
    
    # 对 residual 做 Rank IC,cross-sectional
    residual_df = rebuild_df_from_3d(residual, factor_tensor.index)
    return compute_rank_ic(residual_df, returns)
```

---

## 12. Holdout 隔离

### 原则

**Holdout 是系统的事后检查,不是 candidate 的判决依据**。一旦 LLM 看到 holdout,holdout 就不再 out-of-sample。

### 实现

**Phase 2 EXECUTE 完全不算 holdout**:
- `result.yaml` 没有 holdout 字段
- `derived_analytics.ic_yearly` 只到 2023 年
- LLM 在 Phase 3 看到的任何数据都不含 holdout

**CP06 换成 Validation Stability**(不是 Holdout Durability):
- 基于 split_stability + expanding_window(都在 validation 期内)
- 彻底和 holdout 无关

### `research holdout-review` 独立流程

```bash
research holdout-review
```

这是**和 mine 主循环平行的独立流程**,用户手动触发:

```python
def holdout_review():
    # 1. 读所有 factors/F*.yaml(status=active)
    active_factors = load_active_factors()
    
    # 2. 对每个 factor 算 holdout 指标
    for f in active_factors:
        signal = load_signal(f["signal_ref"])
        holdout_metrics = compute_metrics_vectorized(
            signal, market_df, date_range=sample_policy.holdout_range
        )
    
    # 3. 聚合统计 — 系统级信号
    aggregate = {
        "n_factors_reviewed": len(active_factors),
        "n_decay_above_1_5": count_over_threshold,
        "over_fit_rate": ...,
        "by_direction_decay": {...},
    }
    
    # 4. 写到 vault 外的私有目录
    write("storage/_holdout_private/review_{date}.md", report)
```

### Holdout review 的输出规则

**✅ LLM 可以看的 aggregate signal**:
- "过去 10 admit 里 7 个 decay > 1.5"
- "Fundamental 方向 durability 好于 Momentum"
- "整体 over-fit rate 70%,系统判决偏乐观"

**❌ LLM 绝对不能看的 individual signal**:
- "F018 的 holdout_ic_ir = 0.242"
- "C005 在 holdout 里 mono 翻转"

原因:一旦 LLM 知道具体哪个 factor 失败,会倒推 pattern,下一轮候选设计反向污染 holdout。

### 物理隔离

- `storage/_holdout_private/` **在 vault 外**
- 不被 `/factor-mine` 的任何 LLM 阶段读取
- 只在 Phase 5 consolidation 时 LLM 可读**聚合 brief**,并且 brief 内容受限(只 aggregate,不 individual)
- 可以加 gitignore pattern 或 README 标记 "隔离区"

---

## 13. LLM / Python 职责矩阵

| 任务 | 谁 | 说明 |
|---|---|---|
| 选 direction | **LLM** | 读 INDEX + memory |
| 生成候选表达式 | **LLM** | 创造任务 |
| DSL whitelist 验证 | **Python** | 机械检查 |
| 冻结 manifest | **Python** | 走 atomic_yaml_write |
| Qlib 表达式求值 | **Python** | 批量调用 |
| Factor value 缓存 | **Python** | hash-indexed |
| 预处理(winsorize / zscore) | **Python** | 向量化 |
| IC / mono / Barra / redundancy / feasibility 统计 | **Python** | 全部向量化 |
| Hard gate(CP01)判断 | **Python** | 事实检查 |
| Checkpoint packet 组装 | **Python** | 机械 pre-pack |
| CP02-CP06 reasoning | **LLM** | Contextual 判断 |
| Synthesis + final verdict | **LLM** | 综合判断 |
| Judge.md audit | **Python** | schema + reference 真实性 |
| 分配 factor_id | **Python** | 自动递增 |
| 写 factor.yaml | **Python** | 从 result+judge pack |
| 生成 report packet | **Python** | 从多源 pre-pack |
| 画 PNG | **Python** | plotly + kaleido |
| 写 factor.md | **LLM(subagent 后台)** | 深度报告 |
| 写 direction.md 的 frontmatter 机械字段 | **Python** | counter 自增 |
| 写 direction.md 的 status / priority | **LLM** | 状态转换判断 |
| 写 direction.md Narrative Log | **LLM** | 叙事 |
| 更新 INDEX 下半段统计 | **Python** | 从 direction frontmatter 聚合 |
| 更新 INDEX 上半段 summary | **LLM**(Phase 5)| 手工维护 |
| 主 commit | **Python** | CLI: research commit |
| Report commit | **Python**(subagent 完成时调)| CLI: research commit-report |
| Consolidation 触发判断 | **Python** | 读 config + state |
| Consolidation 重写 lessons/directions | **LLM** 并行 subagent | 单一输入 packet |
| 重写 INDEX 上半段 | **LLM** subagent(最后一步)| |
| Holdout 计算 | **Python**(独立 CLI)| 严格隔离 |
| Holdout aggregate 给 LLM | **Python** | 过滤 individual 信号 |

---

## 14. CLI 清单

### 主流程

```bash
research mine                        # Autonomous 主循环,按 5 phase 推进
research mine --once                 # 只跑一轮
research mine --direction {tag}      # 强制本轮探索某个方向
research mine --dsl-only             # 严格模式,拒绝 Python 候选(R8)
```

### 单阶段 CLI(手动触发)

```bash
research start {batch_id}            # Phase 1 START(手动)
research design {batch_id}           # Phase 1 DESIGN(手动)
research execute {batch_id}          # Phase 2(纯 Python,无 LLM)
research judge {batch_id}            # Phase 3(LLM 参与)
research archive {batch_id}          # Phase 4(LLM + Python)
research consolidate                 # Phase 5(条件触发 或 手动)
research consolidate --target ...    # 指定目标
research consolidate --dry-run       # 预演
```

### Commit

```bash
research commit {batch_id}           # 主 commit(Phase 4 Step 5 调用)
research commit-report {factor_id}   # report commit(subagent 完成时调用)
```

### Cache

```bash
research cache refresh all
research cache refresh market_daily
research cache refresh barra_factors
research cache purge factor_values   # 手动清 factor_values/*.parquet
research cache status                # 打印 cache 使用情况
```

### Audit / Maintenance

```bash
research audit reports               # 检查 factor.yaml 没有对应 factor.md 的
research regenerate-report {fid}     # 补生成缺失的 factor.md
research audit links                 # 扫 vault 所有 [[link]] 确保目标存在
research audit state                 # 检查 state.yaml 和 batches/ 一致
research audit failures              # 扫 batches/*/judge.md 聚合 reject 统计
                                      # 供人工复盘,不自动写入 vault
research audit duplicates            # 扫 factors/F*.yaml 检查 expression 重复
research audit mt-budget             # 见 §7.MT,打印当前多重检验预算
                                      #   cumulative / per-direction / val_exposure
                                      #   以及预测下一个 batch 的 mt_bucket
research audit mt-budget --direction {name}   # 按 direction 细分
research factor retire {fid}         # 撤销一个 factor(允许同表达式在新 batch 重判)
```

### Holdout(严格隔离)

```bash
research holdout-review                   # 跑所有 active factor 的 holdout
research holdout-review --factor {fid}    # 单个 factor
# 产出在 storage/_holdout_private/,LLM 不读
```

### State

```bash
research state                       # 打印当前 state.yaml
research state set {key} {value}     # 强制修改(debug)
research state rollback              # git reset --hard HEAD^ + state 恢复
```

---

## 15. 代码清理清单

### 完全删除(不保留)

#### `src/research/logic/` 整个目录
- `cards.py` — LogicCard / contract / evidence_summary
- `reflect.py` — apply_belief_delta / LogicBeliefDelta
- `scheduler.py` — 7 维打分
- `lifecycle.py` — 7 状态转换
- `family_registry.py` — FamilyRegistry / PF/FM
- `proposals`, `reviews`, `snapshots` 相关

#### `src/research/governance/` 大部分
- `guarded_writer.py` — level_1/level_2 区分(过度工程)
- `forbidden_manager.py` — 3-state lifecycle
- `permissions.py` — actor / write level
- `audit.py` — WriteAuditLog(git 替代)
- `holdout_queue.py` — 老 holdout 队列
- `cycle_controller.py`
- `batch_scheduler.py`
- `cold_start.py`

#### `src/research/storage/` 大部分
- `finalizer.py` — BatchFinalizer(Q39 的 bug 所在)
- `consistency.py` — 过度工程
- `candidate_store.py` / `packet_store.py` / `result_store.py` — 合并到新的 `yaml_io.py`
- `state_store.py` — 简化到 `state.py`
- `ledger_store.py` — 整个删除(ledger 废弃)
- `registry_store.py` — 简化到 factors 目录操作

#### `src/research/judge/`
- `candidate_judge.py` — CandidateJudge 整个类(死代码,Q40 替代)
- `mechanism_alignment.py` — 合并到新 checkpoint 模块
- `replace_protocol.py` — 过度工程

#### `src/research/execute/` 大改
- `precheck.py` — 简化到只保留 DSL whitelist
- `execution_gate.py` — 合并进 Phase 3 CP01
- `pipeline.py` — 重写为新 5 phase 流程
- `compute_implementations.py` — 重写所有指标计算为向量化
- `judge_packet_builder.py` — 废弃(Q26 的 bug),替换为 pre-packer
- `sample_policy.py` — 简化

#### `src/research/feasibility/`
- 整个子包 — 老的 5 个文件的 Python for loop 实现,废弃
- 重写到 Phase 2 compute 里,向量化

#### `src/research/redundancy/`
- `family.py` — Q22 死代码,废弃
- `subspace.py` — 过度工程,废弃
- 保留 `pairwise.py` 的核心逻辑,简化到 compute 里

#### `src/research/risk/`
- `exposures.py` — Q23 的 Python for-loop 252 OLS,重写为向量化
- `engine.py` — 重写到 Phase 2 compute 里

#### `src/research/stats/`
- 大部分模块 — 老的 5 dim effect strength / reliability / support_windows 等,重写到新 compute

#### `src/report/` 大部分
- `renderer.py` — 死代码(Q45.5)
- `templates/factor_report.html.j2` — 1423 行死代码
- 老 `builder.py` — 重写为新 Phase 4 的 pack + subagent
- `analytics/` 6 个 analyzer — 重写成向量化的 stateless 函数

#### `src/research/cli/` 大部分
- `main.py` — 重写命令路由
- 所有 commands/ — 重写(research 命令完全换一套)

#### 所有 skill.md
- `factor-mine/skill.md` — 重写为新 5 phase
- `factor-idea/skill.md` — 重写为 Phase 1
- `factor-execute/skill.md` — 几乎是空文档,因为 Phase 2 无 LLM
- `factor-judge/skill.md` — 重写为 checkpoint-driven
- `factor-reflect/skill.md` — 删除(重定位为 consolidate)
- `factor-report/skill.md` — 重写为 subagent 协议
- `factor-logic/skill.md` — 删除(logic 概念废弃)

### 保留改造

#### `src/research/compute/`
- `operators.py` — 保留(Qlib 自定义算子)
- `data_provider.py` — 保留,简化
- 其他重写

#### `src/research/domain/`
- 简化到只剩 `ResearchConfig` 和新的 dataclass

### 新增

```
src/research/
  phases/
    __init__.py
    phase1_start.py         # Phase 1 START + DESIGN
    phase2_execute.py       # Phase 2 EXECUTE(纯 Python)
    phase3_judge.py         # Phase 3 JUDGE audit + pre-pack
    phase4_archive.py       # Phase 4 ARCHIVE
    phase5_consolidate.py   # Phase 5 CONSOLIDATION
  
  compute/
    vectorized_ic.py
    vectorized_barra.py
    vectorized_quintile.py
    vectorized_feasibility.py
    cache.py                # factor_value cache
  
  checkpoints/
    __init__.py
    generator.py            # 生成 CP01-CP06 的 packet
    hard_gates.py           # CP01 Python 规则
    audit.py                # judge.md audit
  
  memory/
    packer.py               # pre-pack 各种 packet
    vault_io.py             # 读写 vault/ 的 md + frontmatter
    direction_updater.py    # Python 更新 direction frontmatter
    index_refresher.py      # 刷新 INDEX 下半段
  
  archive/
    factor_writer.py        # 写 factor.yaml
    report_packer.py        # 生成 report packet
    commit.py               # research commit CLI
  
  storage/
    yaml_io.py              # 基础 load/save
    paths.py                # 路径常量
    state.py                # state.yaml 操作
  
  cli/
    mine.py                 # research mine 主循环
    single_phase.py         # 单阶段 CLI
    cache.py                # cache 管理
    holdout.py              # holdout-review
    audit.py                # audit 命令
```

---

## 16. 迁移步骤

### Step 0 — 归档现有数据

```bash
# 现有因子 F001-F019 归档到 legacy 目录,不迁移到新 schema
mv storage/registry/factors storage/_legacy/factors_v1
mv storage/evidence/vault/factors storage/_legacy/vault_factors_v1
mv storage/evidence/vault/assets storage/_legacy/vault_assets_v1

# 老 logic / governance / ledger 目录
mv storage/logic storage/_legacy/logic_v1
mv storage/governance storage/_legacy/governance_v1
mv storage/batches storage/_legacy/batches_v1
```

### Step 1 — 新目录结构

```bash
mkdir -p storage/evidence/vault/directions
mkdir -p storage/evidence/vault/factors
mkdir -p storage/evidence/vault/_meta
mkdir -p storage/batches
mkdir -p storage/cache/factor_values
mkdir -p storage/_holdout_private

# 从 _legacy/governance_v1 提取有用的 config,写 storage/config.yaml
# 从 _legacy/logic_v1 提取 lessons 相关 md 片段到 vault/lessons.md
```

### Step 2 — 初始化 state 和 vault

```bash
cat > storage/state.yaml <<EOF
current_batch: null
current_batch_phase: null
last_batch: null
round: 0
rounds_since_last_consolidation: 0
last_activity: null
EOF

# 手工创建初始 INDEX.md 和 lessons.md(参考第 10 节)
# directions/ 初始为空,LLM 在第一轮 Phase 1 START 时创建第一个 direction md
```

### Step 3 — 删除老代码

按照 [第 15 节代码清理清单](#15-代码清理清单) 执行:

```bash
# 完全删除
rm -rf src/research/logic
rm -rf src/research/governance
rm -rf src/research/feasibility
rm -rf src/research/redundancy
rm -rf src/research/stats
rm -rf src/research/risk
rm src/research/judge/candidate_judge.py
rm src/research/judge/mechanism_alignment.py
rm src/research/judge/replace_protocol.py
rm src/research/storage/{finalizer,consistency,candidate_store,packet_store,result_store,ledger_store,registry_store}.py
rm src/research/execute/{judge_packet_builder,execution_gate,compute_implementations}.py
rm -rf src/report/templates
rm src/report/renderer.py
rm -rf .claude/skills/factor-reflect
rm -rf .claude/skills/factor-logic
```

### Step 4 — 新代码骨架

按照 [第 15 节新增部分](#新增) 创建空骨架。每个新模块先写 docstring 和函数签名,不实现。

### Step 5 — 按 Phase 实现(有依赖顺序)

建议顺序(因为有依赖):

1. **Phase 2 Execute 基础**(向量化 compute + cache)
   - 这是最核心的计算层,其他 phase 依赖它产出的 result.yaml
2. **Phase 3 Judge checkpoint 生成器 + audit**
   - 依赖 Phase 2 的 result.yaml schema
3. **Phase 1 Start + Design**
   - 可以在 Phase 2/3 没完成时就开发,产出 manifest
4. **Phase 4 Archive**
   - 依赖 Phase 3 的 judge.md
5. **Phase 5 Consolidation**
   - 依赖 Phase 4 的产物
6. **Mine 主循环编排 + skill.md 更新**

### Step 6 — 跑第一个 batch(batch_001)

```bash
# 手动创建第一个 direction md(例如就叫 bootstrap)
cat > storage/evidence/vault/directions/bootstrap.md <<EOF
---
direction_tag: bootstrap
status: exploring
priority: medium
rounds: 0
admits: 0
---
# Direction: Bootstrap (first direction)
## Hypothesis
First direction just to validate the pipeline end-to-end.
EOF

# 跑一轮 mine
research mine --once --direction bootstrap
```

### Step 7 — 验证

- [ ] Phase 2 result.yaml 产出正确
- [ ] Phase 3 judge.md 带 6 个 CP 章节
- [ ] Phase 4 主 commit 成功
- [ ] Phase 4 后台 subagent 生成 factor.md 成功
- [ ] INDEX 自动刷新
- [ ] direction md 自动更新 Narrative Log

---

## 17. CLAUDE.md 更新要点

需要改写 `CLAUDE.md` 以反映新架构。保留:

- 环境变量 / DB 连接 / Python 版本
- Qlib 包名(pyqlib)
- `C.kernels = 1` 技术要求

删除:
- 所有过时的 factor 数量 / grade 列表
- v1/v2 双版本描述
- 老的 logic/family 概念
- 老 9 阶段流程描述
- skill-driven workflow 的老描述

新增:
- **系统宪法 R1-R7**(第 1 节内容摘要)
- 新的 5 phase 流程总览
- 新 CLI 清单
- 核心文件结构(第 4 节摘要)

建议新 CLAUDE.md 的大纲:

```markdown
# CLAUDE.md

## Quick Commands

```bash
research mine                     # 自动化因子挖掘主循环
research mine --once              # 单轮
research consolidate              # memory 整理
research cache refresh all        # 数据缓存刷新
research holdout-review           # holdout 检查(隔离)
```

## 系统宪法(不可违反)

1. Rule A (YAML) vs Rule B (MD) 数据二分法
2. LLM 主驾,Python 护栏
3. 单一数据源,LLM 不跨文件 grep
4. 不重复计算,向量化优先
5. 代码极简,失败硬 fail
6. Autonomous 但可审计

## 一轮迭代的 5 个 Phase

Phase 1 START + DESIGN:LLM 选方向 + 出候选
Phase 2 EXECUTE:Python 向量化计算(holdout 不算)
Phase 3 JUDGE:LLM + 6 checkpoint 判决
Phase 4 ARCHIVE:归档 + 后台 report + commit
Phase 5 CONSOLIDATION:周期性 memory 整理

## 核心目录

storage/
  state.yaml                    ← 唯一状态
  config.yaml                   ← 系统配置
  evidence/vault/               ← Obsidian vault
    INDEX.md                    ← MOC
    lessons.md                  ← system facts
    directions/*.md             ← 研究方向
    factors/F*.{yaml,md}        ← admitted 因子
  batches/batch_*/              ← 每轮档案
  cache/                        ← 计算缓存
  _holdout_private/             ← holdout 隔离区(LLM 禁读)

## 关键技术约束

- Qlib: `pip install pyqlib`
- Custom operators: `Operators._ops[name] = cls`
- `C.kernels = 1`(workers 不继承 custom ops)
- 不调 `factor_values` DB 表(已废弃)
- 向量化 compute,禁 Python for-loop over rows

## 细节见 docs/refactor_plan.md
```

---

## 附录 A — 决策溯源表

每个设计决策对应的原始讨论 Q:

| 决策 | 来源 |
|---|---|
| Rule A/B 数据二分法 | Q43 |
| 删除 forbidden.yaml,只用 whitelist | Q43 / Q44.7 |
| Logic 系统 → direction md | Q1 / Q9 / Q11 / Q39 |
| 删除 Scheduler 7 维打分 | Q20 / Q39 |
| Family 降级为字符串 tag | Q22 / Q26 |
| Ledger 拆散到 git + state | Q2 / Q44.8 |
| Probe 删除 | Q12 |
| Checkpoint-driven judge | Q30 / Q40 |
| judge.md frontmatter + body | Q29 / Q40 修正 |
| Pre-pack LLM 单一输入 | Q46 / Q45.13 |
| 删除后台 subagent 交叉读 | Q45.1 / Q45.6 |
| factor.yaml + factor.md 拆 | Q46 修正 |
| Section 0 毒舌评论基于公式 | Q46 修正 |
| 逐图抓特点(不要三层强制)| Q46 修正 |
| Holdout 完全隔离 | 本次讨论 |
| 单 direction batch | 本次讨论 |
| lineage 通过 parent_batch 字段 | 本次讨论 |
| Qlib 批量调用单次 | Q12 / 本次讨论 |
| Barra 预计算,Phase 2 只读 | Q23 / 本次讨论 |
| Cache 手动刷新,不自动 | 本次讨论 |
| 向量化规范 R5 | Q23 / Q25 / Q46 |
| Commit 新 CLI,硬 fail | Q47 |
| Consolidation 并行 subagent | 本次讨论 |
| Consolidation 整体重写 + git 回退 | 本次讨论 |
| Duplicate expression check(Phase 1) | Q4 |
| CsRank 全市场行为作为 system fact | Q15 |
| Primary horizon + 涨跌停 bias 文档化 | Q18 |
| research audit failures / duplicates / factor retire CLI | Q44.9 / Q44.10 |
| Phase 4 ARCHIVE 幂等性保证 | Q32 |
| Phase 4 / Phase 5 不并发不变量(git commit 边界) | Q33 / Q36 |
| DSL / Python 双路径 + LLM 自主选择(R8) | 本次讨论(之前遗漏) |
| Python 因子静态 validation + 运行时 contract | 本次讨论 |
| lessons.md 的 Path Selection 决策流程 | 本次讨论 |
| Cache refresh 的 tradability mask 实现(含涨跌停/停牌/新股) | 本次讨论(Q14/Q16 的数据层延续) |
| 多 universe 评估(primary + reference)"算一次切多次" | 本次讨论(之前遗漏) |
| ST / 退市数据工程 TODO(独立任务,refactor 之外) | 本次讨论 |
| Universe 用 Qlib instruments(不查 DB) | 本次重审(之前我设计成查 DB,错) |
| Multi-horizon 完整 metrics(h1/h5/h10)per-horizon 分组 | Q18 补齐(之前只有 decay 曲线) |
| Winsorize/Zscore 真矩阵向量化(不用 groupby.transform) | Q14 补齐(之前用了 groupby) |
| config.yaml 补齐散落硬编码(tradability/MAD scale) | Q20 补齐 |
| MT budget 常量移到 config.yaml.thresholds.mt_budget | Q20 补齐(§7.MT 原方案 + 常量外置) |
| Barra 预计算脚本具体实现(7 个因子向量化) | 本次重审(之前只说"预计算",没给代码) |

完整细节见 `docs/walkthrough_qa.md` 的 Q1-Q47。
