---
paper_slug: <paper_slug>
source_pdf: raw/papers/<file>.pdf
source_kind: <arxiv_or_generic_pdf>
arxiv_id: <arxiv_id_or_null>
status: reviewed
primary_frequency: daily
direction_tag: <direction_tag_or_null>
reviewed_at: <iso_timestamp>
# Delete this field if no image is actually useful.
# images:
#   - papers/<paper_slug>/images/<optional_image>.png
---

# <Paper Title>

## Core Claim

- 这篇论文到底声称抓住了什么机制？
- 结论依赖的核心实验设定是什么？

## Aha Moment

- 最值得借走的一件事是什么？
- 这件事为什么对当前日频因子挖掘仍有启发？

## Candidate Ideas

### Idea 1 — <short name>
- **Paper mechanism**:
- **Target frequency**: daily | intraday | mixed
- **Current readiness**: dsl_ready | python_ready | blocked_by_data | blocked_by_architecture
- **Required fields**:
- **Why it may survive daily downsampling**:
- **Main distortion risk**:
- **Suggested direction tag**:

## Data Requirements

- 原论文依赖了哪些字段、频率、标签或市场结构信息？
- 哪些是我们当前没有的？

## Mapping To Current System

- 对应到当前白名单字段时，最接近的代理变量是什么？
- 更适合 DSL 还是 Python escape hatch？

## Feasibility Assessment

### Idea 1 — <short name>
- **Original dependency**:
- **Coverage in current system**:
- **Can it be downgraded to daily?**:
- **Implementation path**: dsl | python | blocked
- **Missing piece**:

## What The Paper Is Hiding

- 作者默认了什么强假设？
- 哪个结论迁到 A 股日频后最可能失真？

## Blocked Ideas For Future

- 只记录未来可重跑的 blocked 想法和最小 unblock 条件。

## Direction Recommendation

- **Decision**: create_direction | do_not_create_direction
- **Selected idea**:
- **direction_tag**:
- **Initial threads**:
- **First candidate families**:
- **Minimum unblock condition**:
