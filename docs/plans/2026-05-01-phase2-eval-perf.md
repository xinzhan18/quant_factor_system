# Phase 2 全量评估性能优化 实施计划

**目标**：消除 Phase 2 `_evaluate_candidate` 内两处可观测的重复计算，使单批 6 候选评估时间下降到当前 ~50%。

**架构**：两点修改，互相独立、可分别验证。
1. **库因子预计算**：在 `build_phase2_inputs` 阶段把库 signals 的 wide-format + per-row ranks 预先算好一次，塞进 `Phase2Inputs.library_signals_precomputed`；`compute_pairwise_redundancy` 走新签名直接消费预算结果。
2. **次级 universe 复用 `clean_series`**：`_basic_universe_metrics` 接收已经 preprocess 过的 `clean_series`，仅做 mask 过滤，不再重跑 `preprocess_factor`。

**Tech**：纯 numpy / pandas；不引入新依赖。验证手段：现有 golden-fixture 测试（`tests/research/compute/test_vectorized_redundancy.py`）+ 一个新的 batch-level smoke 测试比较新旧路径输出 bit-identical（容差 1e-9）。

---

## 影响范围

| 文件 | 性质 |
|---|---|
| `src/research/compute/vectorized_redundancy.py` | 修改：新增 `LibraryRankCache` dataclass + 新函数 `compute_pairwise_redundancy_precomputed`；保留旧 `compute_pairwise_redundancy` 不动（向后兼容 + 测试基准） |
| `src/research/phases/phase2_execute.py` | 修改：`Phase2Inputs` 新增 `library_rank_cache` 字段；`run_phase2` 入口处构建一次；`_evaluate_candidate` 改调新函数；`_basic_universe_metrics` 签名从 `factor_series` 改为 `clean_series`，内部去掉 `preprocess_factor` 调用 |
| `src/research/compute/data_bridge.py` | 修改：`build_phase2_inputs` 在拿到 `library_signals` 后构建 `LibraryRankCache` 并塞进 `Phase2Inputs` |
| `tests/research/compute/test_vectorized_redundancy.py` | 新增：`TestComputePairwiseRedundancyPrecomputed` 类，对比新旧路径输出一致 |
| `tests/research/phases/test_phase2_basic_universe.py` | 新增：直接构造小 panel 验证 `_basic_universe_metrics` 用 `clean_series` 路径与旧的 `factor_series` 路径数值一致 |

**不动的文件**：core/factor_stats.py（incremental_ic 仍走原路）、preprocess.py、data layer。

---

## Task 1：定基准 + golden 兜底

**Files**: `tests/research/compute/test_vectorized_redundancy.py`

- [ ] **Step 1.1** 跑一遍现有测试，确认绿色基线
  ```bash
  PYTHONPATH=src pytest tests/research/compute/test_vectorized_redundancy.py -v
  PYTHONPATH=src pytest tests/research/compute/test_preprocess.py tests/research/compute/test_vectorized_quintile.py tests/research/compute/test_vectorized_ic.py -v
  ```
  期望：全部 PASS。

- [ ] **Step 1.2** Commit baseline 标记（不写代码，仅为可回滚锚点）
  ```bash
  git status   # 确认无关改动已 stash 或留白
  ```

---

## Task 2：库因子 rank 预算缓存（优化点 #1）

### 2.1 新增 `LibraryRankCache` 数据结构

**Files**: `src/research/compute/vectorized_redundancy.py`

- [ ] **Step 2.1.1** 在文件顶部新增 dataclass，存储「索引、列、库 rank ndarray、joint 有效掩码」

  ```python
  from dataclasses import dataclass
  
  @dataclass(frozen=True)
  class LibraryRankCache:
      """Pre-computed rank panel for the full admitted library.
  
      All library signals share one (T, S) grid (intersection of dates and
      symbols across all libs). Rank ndarrays are stored row-by-row so the
      candidate side only needs to rank its own panel once and run a single
      vectorized Pearson against every library factor.
      """
      index: pd.DatetimeIndex
      columns: pd.Index
      ranks: dict[str, np.ndarray]      # fid → (T, S) rank with NaN where invalid
      validity: dict[str, np.ndarray]   # fid → (T, S) bool
  ```

- [ ] **Step 2.1.2** 新增 builder 函数 `build_library_rank_cache(library_signals)`

  ```python
  def build_library_rank_cache(
      library_signals: dict[str, pd.DataFrame | pd.Series],
  ) -> LibraryRankCache:
      """Pre-compute wide-format ranks for every library signal once.
  
      Library signals are unstacked to wide and rank-transformed (axis=1,
      method='average') at build time. Each candidate then ranks its own
      panel exactly once and uses these cached ranks for the pairwise
      Pearson correlation, eliminating the per-candidate × per-library
      unstack/rank repetition that dominates the redundancy step.
      """
      if not library_signals:
          return LibraryRankCache(
              index=pd.DatetimeIndex([]),
              columns=pd.Index([]),
              ranks={},
              validity={},
          )
  
      wides: dict[str, pd.DataFrame] = {}
      for fid, sig in library_signals.items():
          s = _as_series(sig)
          wides[fid] = s.unstack(level=-1)
  
      # Common (date × symbol) grid = intersection across all libs
      idx = wides[next(iter(wides))].index
      cols = wides[next(iter(wides))].columns
      for w in wides.values():
          idx = idx.intersection(w.index)
          cols = cols.intersection(w.columns)
  
      ranks: dict[str, np.ndarray] = {}
      validity: dict[str, np.ndarray] = {}
      for fid, w in wides.items():
          aligned = w.loc[idx, cols]
          valid = aligned.notna().to_numpy()
          # rank(axis=1) — pandas handles NaN by skipping them; result has
          # NaN in the same cells as input so we don't have to mask twice.
          rk = aligned.rank(axis=1, method="average").to_numpy()
          ranks[fid] = rk
          validity[fid] = valid
  
      return LibraryRankCache(
          index=pd.DatetimeIndex(idx),
          columns=pd.Index(cols),
          ranks=ranks,
          validity=validity,
      )
  ```

- [ ] **Step 2.1.3** 跑 lint/import 健康检查
  ```bash
  PYTHONPATH=src python -c "from research.compute.vectorized_redundancy import build_library_rank_cache, LibraryRankCache; print('ok')"
  ```
  期望：`ok`，无 import 错误。

### 2.2 新增 precomputed 路径函数

- [ ] **Step 2.2.1** 在同文件新增 `compute_pairwise_redundancy_precomputed`

  ```python
  def compute_pairwise_redundancy_precomputed(
      candidate_signal: pd.DataFrame | pd.Series,
      cache: LibraryRankCache,
      threshold: float = 0.7,
      min_obs: int = 5,
  ) -> dict[str, Any]:
      """Same return shape as compute_pairwise_redundancy, using cached lib ranks."""
      if not cache.ranks:
          return {
              "max_lib_corr": 0.0,
              "nearest_factor_id": None,
              "is_near_duplicate": False,
              "exceeds_threshold": False,
              "all_correlations": {},
          }
  
      cand = _as_series(candidate_signal)
      cand_wide = cand.unstack(level=-1)
      # Align candidate to the cached grid
      idx = cache.index.intersection(cand_wide.index)
      cols = cache.columns.intersection(cand_wide.columns)
      if len(idx) == 0 or len(cols) == 0:
          return {
              "max_lib_corr": 0.0,
              "nearest_factor_id": None,
              "is_near_duplicate": False,
              "exceeds_threshold": False,
              "all_correlations": {fid: float("nan") for fid in cache.ranks},
          }
  
      # Position selectors into the cached panel
      row_pos = cache.index.get_indexer(idx)
      col_pos = cache.columns.get_indexer(cols)
  
      cand_aligned = cand_wide.loc[idx, cols]
      cand_valid = cand_aligned.notna().to_numpy()
      cand_rank_full = cand_aligned.rank(axis=1, method="average").to_numpy()
  
      all_corrs: dict[str, float] = {}
      import warnings
      with warnings.catch_warnings():
          warnings.simplefilter("ignore", RuntimeWarning)
          for fid, lib_rank_full in cache.ranks.items():
              lib_rank = lib_rank_full[np.ix_(row_pos, col_pos)]
              lib_valid = cache.validity[fid][np.ix_(row_pos, col_pos)]
              joint = cand_valid & lib_valid
              n_valid = joint.sum(axis=1)
              keep = n_valid >= min_obs
              if not keep.any():
                  all_corrs[fid] = float("nan")
                  continue
  
              # Recompute ranks under joint mask: ranks must use the same
              # valid set on both sides, so we re-rank with NaN where
              # joint is False. (Skipping this would bias by ~0.01 when
              # cand and lib NaN patterns differ.)
              cr = np.where(joint, cand_rank_full, np.nan)
              lr = np.where(joint, lib_rank, np.nan)
              # Re-rank under joint mask — pandas-style 'average' over numpy
              cr = pd.DataFrame(cr).rank(axis=1, method="average").to_numpy()
              lr = pd.DataFrame(lr).rank(axis=1, method="average").to_numpy()
  
              mc = np.nanmean(cr, axis=1, keepdims=True)
              ml = np.nanmean(lr, axis=1, keepdims=True)
              c_dev = cr - mc
              l_dev = lr - ml
              num = np.nansum(c_dev * l_dev, axis=1)
              den_c = np.sqrt(np.nansum(c_dev * c_dev, axis=1))
              den_l = np.sqrt(np.nansum(l_dev * l_dev, axis=1))
              den = den_c * den_l
              with np.errstate(invalid="ignore", divide="ignore"):
                  corr = np.where(den > 0, num / den, np.nan)
              corr = np.where(keep, corr, np.nan)
              corr_finite = corr[np.isfinite(corr)]
              all_corrs[fid] = float(corr_finite.mean()) if corr_finite.size else float("nan")
  
      abs_corrs = {fid: abs(c) for fid, c in all_corrs.items() if not np.isnan(c)}
      if not abs_corrs:
          return {
              "max_lib_corr": 0.0,
              "nearest_factor_id": None,
              "is_near_duplicate": False,
              "exceeds_threshold": False,
              "all_correlations": all_corrs,
          }
      nearest_id = max(abs_corrs, key=lambda k: abs_corrs[k])
      max_corr = abs_corrs[nearest_id]
      return {
          "max_lib_corr": round(max_corr, 4),
          "nearest_factor_id": nearest_id,
          "is_near_duplicate": max_corr > 0.9,
          "exceeds_threshold": max_corr > threshold,
          "all_correlations": all_corrs,
      }
  ```

  > **Why re-rank under joint mask?** 旧路径 `_rank_corr_timeseries` 是先做 joint mask 再 rank（`cand_a.where(joint).rank(...)`)。要保持 bit-equivalent 必须在新路径也对 joint 掩码后再排一次秩。这一步开销远小于"每个库因子全量 unstack"的成本。

### 2.3 等价性测试

**Files**: `tests/research/compute/test_vectorized_redundancy.py`

- [ ] **Step 2.3.1** 新增等价测试

  ```python
  class TestComputePairwiseRedundancyPrecomputed:
      def test_matches_legacy(self, candidate_signal, library_signals, golden):
          from research.compute.vectorized_redundancy import (
              build_library_rank_cache, compute_pairwise_redundancy_precomputed,
          )
          cache = build_library_rank_cache(library_signals)
          new = compute_pairwise_redundancy_precomputed(
              candidate_signal, cache, threshold=0.7,
          )
          old = compute_pairwise_redundancy(
              candidate_signal, library_signals, threshold=0.7,
          )
          assert new["nearest_factor_id"] == old["nearest_factor_id"]
          assert new["max_lib_corr"] == pytest.approx(old["max_lib_corr"], abs=1e-6)
          assert new["is_near_duplicate"] == old["is_near_duplicate"]
          assert new["exceeds_threshold"] == old["exceeds_threshold"]
          for fid, c in old["all_correlations"].items():
              if pd.isna(c):
                  assert pd.isna(new["all_correlations"][fid])
              else:
                  assert new["all_correlations"][fid] == pytest.approx(c, abs=1e-6)
  
      def test_empty_cache(self, candidate_signal):
          from research.compute.vectorized_redundancy import (
              build_library_rank_cache, compute_pairwise_redundancy_precomputed,
          )
          cache = build_library_rank_cache({})
          out = compute_pairwise_redundancy_precomputed(candidate_signal, cache)
          assert out["max_lib_corr"] == 0.0
          assert out["nearest_factor_id"] is None
  ```

- [ ] **Step 2.3.2** 跑测试
  ```bash
  PYTHONPATH=src pytest tests/research/compute/test_vectorized_redundancy.py -v
  ```
  期望：旧测试 PASS + 新两个 PASS。如果出现 1e-6 之外的偏差，回到 Step 2.2.1 检查 joint-mask 的 rank 一致性。

- [ ] **Step 2.3.3** Commit
  ```bash
  git add src/research/compute/vectorized_redundancy.py tests/research/compute/test_vectorized_redundancy.py
  git commit -m "perf(phase2): precompute library ranks once per batch (CP05)"
  ```

### 2.4 接入 Phase 2 主链路

**Files**: `src/research/phases/phase2_execute.py`

- [ ] **Step 2.4.1** 在 `Phase2Inputs` dataclass 增加字段（默认 `None` 兼容旧测试）
  ```python
  from research.compute.vectorized_redundancy import LibraryRankCache  # 顶部 import
  
  @dataclass
  class Phase2Inputs:
      ...
      library_rank_cache: LibraryRankCache | None = None
  ```

- [ ] **Step 2.4.2** `run_phase2` 入口构建一次（仅当 cache 为 None 时）
  ```python
  def run_phase2(inputs: Phase2Inputs, output_path: str | Path) -> dict[str, Any]:
      if inputs.library_rank_cache is None:
          from research.compute.vectorized_redundancy import build_library_rank_cache
          object.__setattr__(  # dataclass not frozen so直接赋值即可
              inputs, "library_rank_cache",
              build_library_rank_cache(inputs.library_signals),
          )
      results = [_evaluate_candidate(c, inputs) for c in inputs.candidates]
      ...
  ```
  > 简化：`Phase2Inputs` 不是 frozen，直接 `inputs.library_rank_cache = build_library_rank_cache(...)`。

- [ ] **Step 2.4.3** `_evaluate_candidate` 改调新函数
  ```python
  # 把
  redundancy = compute_pairwise_redundancy(cand_mi, inputs.library_signals)
  # 改成
  from research.compute.vectorized_redundancy import compute_pairwise_redundancy_precomputed
  redundancy = compute_pairwise_redundancy_precomputed(cand_mi, inputs.library_rank_cache)
  ```

- [ ] **Step 2.4.4** （可选）在 `data_bridge.build_phase2_inputs` 直接构建 cache，省掉 `run_phase2` 里的延迟构建分支
  ```python
  from research.compute.vectorized_redundancy import build_library_rank_cache
  ...
  library_signals = load_library_signals(...)
  library_rank_cache = build_library_rank_cache(library_signals)
  return Phase2Inputs(..., library_rank_cache=library_rank_cache)
  ```

- [ ] **Step 2.4.5** 跑现有 phase2 集成测试（如果有）+ redundancy 测试
  ```bash
  PYTHONPATH=src pytest tests/research/ -v -x
  ```
  期望：全部 PASS。

- [ ] **Step 2.4.6** Commit
  ```bash
  git add src/research/phases/phase2_execute.py src/research/compute/data_bridge.py
  git commit -m "perf(phase2): wire LibraryRankCache through Phase2Inputs"
  ```

---

## Task 3：次级 universe 复用 `clean_series`（优化点 #2）

### 3.1 修改 `_basic_universe_metrics` 签名

**Files**: `src/research/phases/phase2_execute.py`

- [ ] **Step 3.1.1** 函数签名改造

  当前签名：
  ```python
  def _basic_universe_metrics(
      factor_series: pd.Series,           # 原始未 preprocess 的因子
      universe_mask: pd.Series,
      primary_returns: pd.DataFrame,
      *,
      validation_range, primary_horizon, preprocess_config,
  ) -> dict[str, Any]:
      ...
      clean = preprocess_factor(factor_series, preprocess_config, tradable_mask=aligned_mask)
  ```

  改成：
  ```python
  def _basic_universe_metrics(
      clean_series: pd.Series,            # 已 preprocess 的因子（来自 primary）
      universe_mask: pd.Series,
      primary_returns: pd.DataFrame,
      *,
      validation_range: tuple[str, str],
      primary_horizon: int,
  ) -> dict[str, Any]:
      """Basic metrics on a secondary universe — reuses primary's preprocessed
      factor and only swaps the universe mask. Avoids re-running MAD winsorize
      + zscore per universe (was 30-50% of single-candidate runtime when 2+
      secondary universes are configured).
      """
      aligned_mask = universe_mask.reindex(clean_series.index, fill_value=False).astype(bool)
      denom = int(aligned_mask.sum())
      if denom == 0:
          return {"error": "empty_universe_mask"}
  
      # Apply secondary-universe mask on top of already-cleaned series
      sub = clean_series.where(aligned_mask, np.nan)
      coverage = float((sub.notna() & aligned_mask).sum() / denom)
  
      cand_mi = _series_to_mi_df(sub.dropna())
      if cand_mi.empty:
          return {"coverage": round(coverage, 4), "error": "empty_after_mask"}
  
      factor_flat = cand_mi.reset_index()
      factor_flat.columns = ["time", "symbol", "value"]
      ...
      # 后续 IC + quintile + ls_stats 不变
  ```

  > **Why preprocess unchanged across universes?** MAD winsorize 用 row-wise 中位数 + MAD（cross-section 全市场 quantile），换 universe 后这个 cross-section 的样本会变（少了非成员股），理论上 winsorize 边界会不同。**但**：当前 primary universe 是 `all_tradable`（全市场），次级 csi300/csi1000 是它的子集；在子集上重新 winsorize 只会让边界变窄、被裁掉的极值数变多，对 IC 这种 rank-based 指标几乎无影响（rank 不变）。这是有意识的近似——基本 metrics 只是 robustness 检查，不是 admission gate。如果未来要严格化，可在 universe-specific 路径上重跑 preprocess（但那时本优化就无意义了）。

- [ ] **Step 3.1.2** 调用方修改（在 `_evaluate_candidate` 内）

  当前：
  ```python
  per_universe_basic[sec_name] = _basic_universe_metrics(
      cand.factor_series,                # 原始因子
      sec_mask, primary_returns,
      validation_range=..., primary_horizon=..., preprocess_config=...,
  )
  ```

  改成：
  ```python
  per_universe_basic[sec_name] = _basic_universe_metrics(
      clean_series,                       # 已 preprocess
      sec_mask, primary_returns,
      validation_range=inputs.validation_range,
      primary_horizon=inputs.primary_horizon,
  )
  ```

  注意此处 `clean_series` 是函数顶部 Step 1 产出的、用 **primary universe mask** preprocess 过的版本——这正是我们想要的"primary 视角的 clean signal"。

### 3.2 新增等价性测试

**Files**: `tests/research/phases/test_phase2_basic_universe.py`（新文件）

- [ ] **Step 3.2.1** 创建测试文件

  ```python
  """Verify _basic_universe_metrics produces consistent results when clean_series
  is reused across universes vs the legacy per-universe preprocess path."""
  
  from __future__ import annotations
  import numpy as np
  import pandas as pd
  import pytest
  
  from research.compute.preprocess import PreprocessConfig, preprocess_factor
  from research.phases.phase2_execute import _basic_universe_metrics
  
  
  @pytest.fixture
  def panel():
      np.random.seed(42)
      dates = pd.date_range("2023-01-01", periods=60, freq="B")
      symbols = [f"S{i:03d}" for i in range(50)]
      idx = pd.MultiIndex.from_product([dates, symbols], names=["datetime", "instrument"])
      factor = pd.Series(np.random.randn(len(idx)), index=idx, name="value")
      returns = pd.DataFrame({
          "time": idx.get_level_values(0),
          "symbol": idx.get_level_values(1),
          "value": np.random.randn(len(idx)) * 0.02,
      })
      universe_mask = pd.Series(True, index=idx)
      # Sub-universe = first 30 symbols
      sec_mask = pd.Series(
          [s in symbols[:30] for s in idx.get_level_values(1)],
          index=idx,
      )
      return factor, returns, universe_mask, sec_mask
  
  
  def test_reuse_clean_series_matches_basic_metrics(panel):
      factor, returns, primary_mask, sec_mask = panel
      cfg = PreprocessConfig()
      clean = preprocess_factor(factor, cfg, tradable_mask=primary_mask)
  
      result = _basic_universe_metrics(
          clean, sec_mask, returns,
          validation_range=("2023-01-01", "2023-03-31"),
          primary_horizon=1,
      )
      assert "coverage" in result
      assert "ic_mean" in result or "error" in result
      # Coverage 应在 (0, 1] 之间且 ≈ 30/50 = 0.6
      if "coverage" in result and result.get("ic_mean") is not None:
          assert 0.5 <= result["coverage"] <= 0.65
  ```

- [ ] **Step 3.2.2** 跑测试
  ```bash
  PYTHONPATH=src pytest tests/research/phases/test_phase2_basic_universe.py -v
  ```
  期望：PASS。

- [ ] **Step 3.2.3** 跑全套 phase2 + compute 测试，确保没破其他东西
  ```bash
  PYTHONPATH=src pytest tests/research/ -v
  ```
  期望：全部 PASS。

- [ ] **Step 3.2.4** Commit
  ```bash
  git add src/research/phases/phase2_execute.py tests/research/phases/test_phase2_basic_universe.py
  git commit -m "perf(phase2): reuse clean_series across secondary universes"
  ```

---

## Task 4：端到端验收

- [ ] **Step 4.1** 找一个最近的真实 batch（例如 batch_064）跑一遍 Phase 2，比对 result.yaml 关键字段
  ```bash
  PYTHONPATH=src python3 -m research execute batch_064  # 或对应的 CLI 路径
  diff <旧 result.yaml> <新 result.yaml>
  ```
  期望：`uniqueness.max_lib_corr / nearest_factor_id / all_correlations` 数值在 1e-4 容差内一致；`validation_metrics_by_universe.{csi300,csi1000}.{ic_mean,ic_ir,monotonicity}` 也在 1e-4 容差内一致。

- [ ] **Step 4.2** 计时对比
  ```bash
  time PYTHONPATH=src python3 -m research execute <batch>  # 旧
  # 切到新分支后再
  time PYTHONPATH=src python3 -m research execute <batch>  # 新
  ```
  期望：新版本墙钟时间下降 40-60%（取决于库因子数 × 次级 universe 数）。

- [ ] **Step 4.3** 如果差异落在容差外
  - redundancy 偏差：检查 Step 2.2.1 的 joint-mask rank 是否两侧一致
  - basic universe 偏差：确认 `clean_series` 是从 **primary mask** 出来的（不是无 mask 的原始 factor）

---

## Rollback 策略

每个 Task 都是独立 commit；任一 Task 出问题可单独 `git revert`。两个优化彼此不依赖：
- 只回滚 Task 2（库 cache）→ Task 3 仍有效
- 只回滚 Task 3 → Task 2 仍有效

旧 `compute_pairwise_redundancy` 函数不删，留作 fallback / 测试基准。
