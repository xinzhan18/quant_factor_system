# Storage 目录重构计划

## Context

当前 `storage/` 有 **13 个顶层目录** 承载 **14 个文件**，其中 **10 个目录是空的**。批次生命周期散落在 candidates/ + results/ + packets/ 三个目录；memory/、notes/、evaluation_profiles/、ledger/ 各只有 1 个文件。此外 `ledger_store.py` 仍引用已删除的 4 个独立 ledger 文件。

**目标**：13 个顶层目录 → 7 个，消除代码/文件不一致。

## 新结构

```
storage/
  state/                     # 运行时状态（不变）
    research_state.yaml
    pending_holdout_queue.yaml

  logic/                     # 假设管理（不变）
    registry.yaml
    cards/ | proposals/ | reviews/ | snapshots/

  registry/                  # 因子注册（不变）
    factors/index.yaml + factor_*.yaml
    families/family_registry.yaml

  governance/                # 治理配置（合并 5 个目录）
    ledger.yaml              #   ← ledger/ledger.yaml
    forbidden.yaml           #   ← memory/forbidden.yaml
    eval_profile_v1.yaml     #   ← evaluation_profiles/research_eval_v1.yaml
    mining_lessons.md        #   ← notes/mining-lessons.md
    policy/                  #   ← policy/（4 files，保留子目录）
      capability_registry.yaml
      implementation_policy.yaml
      failure_taxonomy.yaml
      policy_upgrade_ledger.yaml

  batches/                   # 批次全生命周期（合并 3 个目录）
    batch_042/               #   每批一个子目录
      manifest.yaml          #   ← candidates/batch_042.yaml
      idea_report.yaml       #   ← candidates/batch_042_idea_report.yaml
      research_result.yaml   #   ← results/batch_042_result.yaml
      execute_report.yaml    #   ← results/batch_042_execute_report.yaml
      judge_packet.yaml      #   ← packets/batch_042_judge_packet.yaml
      context_snapshot.yaml  #   ← packets/batch_042_context_snapshot.yaml
      judge_report.yaml      #   ← results/batch_042_judge_report.yaml

  evidence/vault/            # Obsidian 产物（不变）
    assets/ | factors/

  runtime/cache/             # 临时缓存，gitignored（不变）
```

## 实施步骤

### Step 1：更新 `paths.py`（核心，所有路径从这里派生）

**文件**: `src/research/storage/paths.py`

删除旧属性：`ledger_dir`, `memory_dir`, `notes_dir`, `evaluation_profiles_dir`, `candidates_dir`, `results_dir`, `packets_dir`, `policy_dir`

新增/替换：
```python
# 新顶层
governance_dir      → root / "governance"
governance_policy_dir → governance_dir / "policy"
batches_dir         → root / "batches"
vault_dir           → root / "evidence" / "vault"   # 补 config.py 的缺口
cache_dir           → root / "runtime" / "cache"     # 同上

# 文件属性迁移
ledger_file         → governance_dir / "ledger.yaml"        # 替换 4 个旧属性
forbidden_file      → governance_dir / "forbidden.yaml"
research_eval_v1_file → governance_dir / "eval_profile_v1.yaml"
policy 4 files      → governance_policy_dir / "*.yaml"

# 批次动态路径
batch_dir(batch_id)       → batches_dir / batch_id           # 新方法
batch_manifest_file(bid)  → batch_dir(bid) / "manifest.yaml"
idea_report_file(bid)     → batch_dir(bid) / "idea_report.yaml"
result_file(bid)          → batch_dir(bid) / "research_result.yaml"
execute_report_file(bid)  → batch_dir(bid) / "execute_report.yaml"
judge_packet_file(bid)    → batch_dir(bid) / "judge_packet.yaml"
context_snapshot_file(bid)→ batch_dir(bid) / "context_snapshot.yaml"
judge_report_file(bid)    → batch_dir(bid) / "judge_report.yaml"
```

更新 `all_dirs()` 列表。

### Step 2：重写 `ledger_store.py`（修复 4 文件→1 文件不一致）

**文件**: `src/research/storage/ledger_store.py`

所有方法改为对单一 `ledger_file` 做 section 读写：
```python
def _load_ledger(self) -> dict:
    return load_yaml(self._paths.ledger_file)

def _save_ledger(self, data: dict) -> None:
    save_yaml(self._paths.ledger_file, data)

def load_search_ledger(self) -> dict:
    return self._load_ledger().get("search_ledger", {})

def save_search_ledger(self, data: dict) -> None:
    ledger = self._load_ledger()
    ledger["search_ledger"] = data
    self._save_ledger(ledger)
# batch_usage, holdout_reviews, write_audit_log 同理
```

公开 API 不变，调用方无需改动。

### Step 3：更新 store listing 方法

**文件**:
- `src/research/storage/candidate_store.py` — `list_manifests()` 改为扫描 `batches_dir` 子目录
- `src/research/storage/result_store.py` — `list_results()` 改为扫描子目录内 `research_result.yaml`
- `src/research/storage/packet_store.py` — `list_packets()` 改为扫描子目录内 `judge_packet.yaml`

### Step 4：更新 CLI 硬编码路径

**文件**:
- `src/research/cli/commands/batch.py:14` — `CANDIDATES_DIR` → 使用 `StoragePaths().batches_dir`
- `src/research/cli/commands/state.py:15` — `STATE_PATH` → 使用 `StoragePaths().research_state_file`
- `src/research/cli/commands/execute.py:15,27-28` — profile 默认值 + results_dir/packets_dir → 新路径

### Step 5：清理 `config.py`

**文件**: `src/research/domain/config.py`

删除过时字段：`routes_dir`, `history_dir`, `reports_dir`, `memory_dir`
更新/新增：`governance_dir`, `batches_dir`
补齐缺失：`vault_dir`, `cache_dir`（paths.py 也要对应添加）

### Step 6：更新测试

**文件**: `tests/research/storage/test_ledger_store.py`

重写测试验证 4 个 section 共存于同一文件且互不覆盖。其他 store 测试因使用 `StoragePaths(tmp_path)` 自动适配。

### Step 7：更新 Skills（纯文本替换）

**7 个 skill 文件**中的路径引用全部替换：

| 旧路径 | 新路径 |
|---|---|
| `storage/candidates/batch_XXX.yaml` | `storage/batches/batch_XXX/manifest.yaml` |
| `storage/candidates/batch_XXX_idea_report.yaml` | `storage/batches/batch_XXX/idea_report.yaml` |
| `storage/results/batch_XXX_*` | `storage/batches/batch_XXX/*` |
| `storage/packets/batch_XXX_*` | `storage/batches/batch_XXX/*` |
| `storage/ledger/ledger.yaml` | `storage/governance/ledger.yaml` |
| `storage/memory/forbidden.yaml` | `storage/governance/forbidden.yaml` |
| `storage/policy/*.yaml` | `storage/governance/policy/*.yaml` |
| `storage/evaluation_profiles/*` | `storage/governance/eval_profile_v1.yaml` |

### Step 8：更新 CLAUDE.md

重写 Storage Layout 章节为新的 7 目录结构。

### Step 9：迁移磁盘文件 + 清理

```bash
mkdir -p storage/governance/policy storage/batches
mv storage/ledger/ledger.yaml storage/governance/
mv storage/memory/forbidden.yaml storage/governance/
mv storage/evaluation_profiles/research_eval_v1.yaml storage/governance/eval_profile_v1.yaml
mv storage/notes/mining-lessons.md storage/governance/mining_lessons.md
mv storage/policy/*.yaml storage/governance/policy/
rmdir storage/{ledger,memory,evaluation_profiles,notes,policy,candidates,results,packets}
```

更新 `.gitignore`：`storage/candidates/*_result.yaml` → `storage/batches/*/research_result.yaml`（如果需要 ignore）。

## 验证

```bash
# 1. 运行全部测试
pytest

# 2. 确认 ensure_dirs() 创建正确目录
python3 -c "from research.storage import StoragePaths; sp=StoragePaths(); sp.ensure_dirs(); import os; os.system('find storage -type d | sort')"

# 3. 确认 CLI 正常
PYTHONPATH=src python3 -m research state
PYTHONPATH=src python3 -m research batch list

# 4. 确认无残留旧路径引用
grep -r 'storage/candidates\|storage/results\|storage/packets\|storage/memory\|storage/notes\|storage/evaluation_profiles\|storage/policy/' src/ .claude/skills/ CLAUDE.md
```
