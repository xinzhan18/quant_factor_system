---
name: factor-paper
description: 外部论文 / PDF intake —— 解析 raw paper，生成结构化 paper note，并在当前日频 DSL/Python 体系下创建可执行的 direction 或记录阻塞原因
user_invocable: true
---

# /factor-paper — 论文到方向

## 目标

把外部论文、slides、notes 接入当前 **direction-first** 挖掘体系。**不是**直接从 paper 生成因子代码；先产出 paper note，再决定是否生成 `directions/{tag}.md`。

参考来源：Claude 全局 skill `paper-analyze` / `extract-paper-images` 的方法论，但**只吸收与当前仓库相关的部分**：
- 吸收：更深的 paper note 结构、图表优先从源码/高质量来源提取、对论文 claim 做批判性审阅
- 不吸收：知识图谱 / canvas / 跨领域论文库维护 / 过重的 memo 模板

## 存储协议

| 类型 | 路径 | 谁写 |
|---|---|---|
| 原始文件 | `storage/vault/raw/papers/*.pdf` | 人工放入 |
| 确定性抽取 | `storage/vault/raw/paper_extracts/{paper_slug}.md` | Python |
| 结构化笔记 | `storage/vault/papers/{paper_slug}.md` | LLM |
| 可选图片 | `storage/vault/papers/{paper_slug}/images/*` | Python |
| 可执行方向 | `storage/vault/directions/{direction_tag}.md` | LLM |

**原则**：raw 与 processed 分离。PDF 永远保留原件；LLM **不直接读 PDF 二进制**，只读 `paper_extracts/*.md`。

## 来源识别与命名

`/factor-paper` 先识别 paper 属于哪一类，再决定后续处理：

- `arxiv`：输入里显式给出 arXiv ID，或文件名 / 标题里能识别出 `arXiv:2401.01234`、`2401.01234v2` 这类模式
- `generic_pdf`：普通本地 PDF，无法可靠识别为 arXiv

当前实现以本地文件为准，不维护“论文平台真相源”。也就是说：
- 真正的输入永远是 `storage/vault/raw/papers/<file>.pdf`
- `arxiv` 只是一个**增强标签**，主要用于图片提取时尝试下载 arXiv 源码包里的 figure
- 如果识别不到 arXiv ID，就按普通 PDF 处理；**不要**因为“像 arXiv”就杜撰来源信息

命名规则：
- `paper_slug` 默认取 `slugify(<pdf_stem>)`
- 如需稳定 slug，可显式传 `--paper-slug`
- `direction_tag` 不一定等于 `paper_slug`，它应该表达**本地化后的研究方向**，而不是论文题目本身

## 当前系统边界（做 feasibility，不做幻觉）

当前系统是：
- **日频优先**
- 数据字段以 Phase 1 白名单为准（source-of-truth: `src/research/phases/phase1_start.py:DSL_FIELD_WHITELIST`）：
  - 价量：`$open $high $low $close $volume $amount`
  - 微观：`$turnover_rate $num_trades`
  - 估值 PIT：`$pe_ratio $pb_ratio $ps_ratio $pcf_ratio $market_cap $circ_market_cap`
  - 基本面 TTM (20)：盈利 / 偿债 / 效率 / 成长 / 每股 / 估值（详见 `CLAUDE.md` "Available Fields"）
  - 2026-05-01 扩展 22 字段：基本面方向打开
- **DSL first**；DSL 不可表达但日频数据足够时，才走 Python escape hatch

因此每个 paper idea 必须被分到四类之一：
- `dsl_ready`
- `python_ready`
- `blocked_by_data`
- `blocked_by_architecture`

典型阻塞：
- 需要分钟 / tick / order-book / news / options / 另类数据 → `blocked_by_data`
- 需要当前 runtime 没有的 evaluation / neutralization / portfolio machinery → `blocked_by_architecture`

## 流程

### Step 1 — 放原文

把 PDF 放到：

```bash
storage/vault/raw/papers/<paper>.pdf
```

### Step 2 — Python 抽取成 markdown

```bash
PYTHONPATH=src python3 scripts/extract_paper_pdf.py \
  --pdf storage/vault/raw/papers/<paper>.pdf
```

产出 `storage/vault/raw/paper_extracts/<paper_slug>.md`。这个文件只做**逐页文本抽取**，不做研究判断。

### Step 2.5 — 可选：提取关键图（只在图比正文更关键时）

如果 paper 的核心信息主要体现在架构图、结果图、ablation 图，而纯文本抽取会丢信息，可以额外提图。

借鉴 `extract-paper-images` 的原则，图片提取按三层回退：
- **优先 arXiv 源码包中的原始 figure**
- 其次按页面 caption 做定向渲染
- 最后才是 PDF 嵌入图直接提取

其中“是否是 arXiv”按以下顺序判断：
1. 命令行显式传入 `--arxiv-id`
2. 从 PDF 文件名中解析出 `2401.01234` 这类 arXiv ID
3. 若以上都没有，则视为普通 PDF，不再猜

但本仓库当前**不要求**每篇 paper 都提图。默认只抽文本；只有当以下任一成立时才提图：
- 关键公式/方法主要靠图解释
- 主结论主要靠结果图支撑
- PDF 文本抽取明显破碎，难以还原方法结构

若提图，放到：

```bash
PYTHONPATH=src python3 scripts/extract_paper_images.py \
  --pdf storage/vault/raw/papers/<paper>.pdf
```

默认输出目录：

```bash
storage/vault/papers/<paper_slug>/images/
```

paper note 里只引用真正有用的 1-3 张图，不做图册。图像提取是**辅助手段**，不能替代正文 feasibility 分析。

### Step 3 — 用 subagent 写 `vault/papers/{paper_slug}.md`

Read：
- `storage/vault/raw/paper_extracts/{paper_slug}.md`
- `.claude/skills/factor-paper/paper-note-template.md`
- `.claude/skills/factor-idea/skill.md` 的 `Direction.md schema` / `DSL whitelist`
- `src/research/phases/phase1_start.py`（代码 whitelist 为最终真理）
- `PYTHONPATH=src python3 -m research memory snapshot --recent 10` 输出（避免重复造已有方向）

执行方式：
- 主 agent 负责发现新 paper、跑 Python 抽取、决定是否提图、准备上下文
- **研究判断必须交给独立 subagent**
- subagent 只拿以下输入：抽取后的 markdown、最多 1-3 张关键图、当前 direction schema / DSL whitelist、最近 memory snapshot
- subagent 先从 `.claude/skills/factor-paper/paper-note-template.md` 起稿，再删除占位符并填成最终 note
- 主 agent **不要**把整篇论文长内容直接吸进主线程记录，避免污染后续 `/factor-mine`
- subagent 的输出只回传两类产物：`vault/papers/{paper_slug}.md`，以及在可行时生成的 `vault/directions/{direction_tag}.md`

写一份结构化 paper note。风格借鉴 `paper-analyze`：不是流水账，不是填表，要像研究员写给同事的 paper intake memo。但目标仍是 **能否转成当前 direction**，而不是做通用论文读书笔记。

至少包含：

```markdown
---
paper_slug: <slug>
source_pdf: raw/papers/<file>.pdf
source_kind: arxiv | generic_pdf
arxiv_id: <id-or-null>
status: reviewed              # reviewed | partial | blocked | converted
primary_frequency: daily      # daily | intraday | mixed
direction_tag: <tag-or-null>
reviewed_at: <iso>
---

# <paper title>

## Core Claim
## Aha Moment
## Candidate Ideas
## Data Requirements
## Mapping To Current System
## Feasibility Assessment
## What The Paper Is Hiding
## Blocked Ideas For Future
## Direction Recommendation
```

如果提了图，frontmatter 里可额外写：

```markdown
images:
  - papers/<paper_slug>/images/figure1_method.png
  - papers/<paper_slug>/images/figure2_results.png
```

但不要为了“字段完整”硬塞图片路径。没有真正有用的图，就省略 `images`。

其中 `Candidate Ideas` / `Feasibility Assessment` 不是散文列表，必须按**单 idea 一条**组织。推荐格式：

```markdown
### Idea 1 — <short name>
- **Paper mechanism**: ...
- **Target frequency**: daily | intraday | mixed
- **Current readiness**: dsl_ready | python_ready | blocked_by_data | blocked_by_architecture
- **Required fields**: `$close`, `$amount`, ...
- **Why it may survive daily downsampling**: ...
- **Main distortion risk**: ...
- **Suggested direction tag**: <slug-or-null>
```

`Feasibility Assessment` 必须逐条写清：
- 论文原始依赖
- 我们现有字段能否覆盖
- 能否降阶到日频
- 应做 DSL 还是 Python
- 若不能做，缺什么

`Direction Recommendation` 必须只输出一个最终决策：
- `create_direction`
- `do_not_create_direction`

若是 `create_direction`，必须明确：
- 选中的 `idea`
- `direction_tag`
- 2-4 个初始 threads
- 第一批最该试的 3-5 个 candidate family（不是具体 manifest）

若是 `do_not_create_direction`，必须明确最小 unblock 条件，例如：
- 需要分钟频 OHLCV
- 需要 order-book / trade-flow
- 需要新增 DSL operator
- 需要 Phase 2/4 额外评估视角

`Aha Moment` 要回答：这篇 paper **最值得借走的一件事**是什么。

`What The Paper Is Hiding` 要回答至少一条：
- 作者默认了什么强假设？
- 哪个实验对比缺了？
- 哪个结果只能在分钟频/订单流数据下成立，迁到我们这里就会失真？
- 哪个 claim 看起来强，但本质只是“换数据频率/换标的就不成立”？

### Step 4 — 只有“当前可做”时才生成 direction

若 note 中至少有一个 `dsl_ready` 或 `python_ready` 的核心想法：

1. 选 **一个** 最值得做的方向
2. 写 `storage/vault/directions/{direction_tag}.md`
3. 结构严格复用 `/factor-idea` 的 `Direction.md schema`
4. `## Related` 里必须链回 `[[papers/{paper_slug}]]`

生成 direction 时的 subagent 输出边界：
- 只创建 **一个** 最值得做的 direction
- 只写方向，不进入 candidate manifest 生成
- 方向必须是“论文机制在本仓库数据/DSL约束下的本地化版本”，不能原样复刻论文章节结构

若全部 blocked：
- **不要**硬造 direction
- 只把未来可重试条件写进 `Blocked Ideas For Future`

direction 的 `## Hypothesis` 不要照抄论文。要完成一次**本地化重写**：
- 从论文语言改写为 A 股 / 当前日频 / 当前字段白名单下可检验的假设
- 把分钟频、order flow、LOB、事件流等高频对象降阶成我们真的有的数据代理；降不了就不要造
- 每个 thread 都必须是当前系统下能被 batch 逐轮回答的问题，而不是论文目录的章节名

## 动态复评（关键）

这个 skill 不是一次性 intake。以后当以下条件变化时，必须允许**重跑**：
- 新增日频字段
- 引入分钟频或更细粒度数据
- DSL whitelist 扩展
- Python runtime / evaluation / report 架构升级

重跑时：
1. 重读旧的 `vault/papers/{paper_slug}.md`
2. 重新对照当前代码和白名单
3. 更新 `Feasibility Assessment`
4. 若原先 blocked 现在可做，则新建 direction 或在原 note 里升级状态 `blocked -> converted`

## 边界

- `/factor-paper` 负责 **paper → note → direction**
- `/factor-idea` 负责 **direction → candidate batch**
- `/factor-paper` 不直接写 `manifest.yaml`，不直接生成 admitted factor code
- 不为了“保留论文信息”而引入与当前挖掘系统无关的 graph/canvas 维护逻辑
- `/factor-paper` 默认使用 subagent 吃掉长论文上下文；主线程只保留最终 note / direction / 简短结论
