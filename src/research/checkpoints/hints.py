"""Phase 3 Python hints — the LLM's only Python-computed input.

The subagent that judges a single candidate reads **only** its own block
inside ``_hints.yaml`` (plus ``directions/{direction}.md`` for the
hypothesis narrative and optionally ``factors/{nearest}.md`` for the
nearest-factor comparison). It does NOT open ``result.yaml``,
``lessons.md``, or the parent ``factor-judge/skill.md``.

To make that self-contained, Python pre-loads every rubric-relevant
number from ``result.yaml`` into the hints file:

1. **Hard gate per-gate detail** (CP01) — value/threshold/pass for every
   one of the 8 gates in :mod:`research.checkpoints.hard_gates`.
2. **Flattened rubric metrics** (CP03–CP06) — ic_oos / icir_oos /
   ls_tstat_oos / style_r2 / alpha_survival / barra_residual_ic /
   dominant_style / extreme_ratio / max_lib_corr / is_near_duplicate /
   nearest_factor_id / nearest_factor_expression / incremental_ic /
   sign_consistency / train_validation_decay.
3. **MT budget** (CP03 adjustment) — bucket / score / search_adjusted.
4. **Cross-batch counts** — cumulative / direction / validation_exposure
   (for the judge.md MT Context segment).

Schema (abridged)::

    batch_id: batch_009
    direction: timing_signals
    generated_at: 2026-04-18T05:45:00Z

    mt_counts: { ... }

    per_candidate:
      C001:
        expression: "Std($close, 20)"
        coverage: 0.989
        hard_gate:
          passed: true
          reasons: []
          gate_results:
            compute_error:  { passed: true }
            coverage:       { passed: true, value: 0.989, threshold: 0.80 }
            sign_flip:      { passed: true, train_ic: -0.020, val_ic: -0.023 }
            forbidden:      { passed: true }
            ic_oos_min:     { passed: true, value: -0.023, threshold: 0.008 }
            oos_decay:      { passed: true, value: 1.12, threshold: 0.20 }
            mono_flip:      { passed: true, train: -0.10, validation: -0.10 }
            near_duplicate: { passed: true, max_corr: 0.25, nearest: F005 }
        mt_budget: { ... }
        metrics:
          cp03:
            # graded
            ic_oos, icir_oos, ls_tstat_oos
            # IS counterparts + sample size + IC volatility
            ic_is, icir_is, ic_std_is, ic_std_oos, n_days_is, n_days_oos
            ic_win_rate_is, ic_win_rate_oos
            # rank-order evidence
            monotonicity_is, monotonicity_oos
            quintile_returns_is: {q1, q2, q3, q4, q5}
            quintile_returns_oos: {q1, q2, q3, q4, q5}
            # long-short risk/return — IS + OOS
            ls_mean_is, ls_mean_oos
            ls_sharpe_is, ls_sharpe_oos, ls_sortino_oos, ls_calmar_oos
            ls_tstat_is, ls_max_dd_is, ls_max_dd_oos
          cp04:
            style_r_squared, alpha_survival_ratio, extreme_ratio
            barra_residual_ic, barra_residual_icir
            dominant_style_exposure, style_crowding_risk
            style_exposures: {style_name: coef, ...}
            distribution_skew, distribution_kurt, distribution_zero_ratio
          cp05:
            max_lib_corr, is_near_duplicate, incremental_ic
            nearest_factor_id, nearest_factor_expression
            all_correlations: {factor_id: corr, ...}
            exceeds_threshold
          cp06:
            sign_consistency, train_validation_decay, sign_consistent
            ic_by_year: {year: ic, ...}
            worst_quarter_ic, best_quarter_ic
            ic_autocorr_lag1, cum_ic_max_drawdown
            split_ic_means: [...], split_dispersion, n_splits
        feasibility:
          turnover_mean, liquidity_coverage,
          tail_concentration, small_cap_concentration,
          signal_half_life, signal_autocorr_lag1,
          ic_half_life_days,
          rebalance_stress: {...}
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from research.checkpoints.hard_gates import (
    HardGatesConfig,
    evaluate_hard_gates,
)
from research.checkpoints.mt_budget import (
    MtBudgetConfig,
    MtCounts,
    compute_mt_budget,
    scan_batches_for_mt,
)
from research.storage.yaml_io import load_yaml, save_yaml


def _extract_metrics(candidate: dict[str, Any]) -> dict[str, Any]:
    """Flatten the CP03-CP06 + feasibility metrics out of one result.yaml candidate.

    Goal: subagent has **all** judge-relevant numbers here so it never opens
    ``result.yaml``. Fields not used by any CP (``expression_depth`` /
    ``source_type`` / ``sign`` / ``diagnostics_relpath`` / ``ic.by_horizon``)
    are intentionally omitted — those are plumbing metadata, not judgement
    inputs.

    Missing fields are stored as ``None`` (or ``{}`` for dict-typed fields)
    rather than omitted so the LLM always sees which data the candidate lacks.
    """
    ic = candidate.get("ic") or {}
    train_ic = ic.get("train") or {}
    val_ic = ic.get("validation") or {}
    quintile = candidate.get("quintile") or {}
    q_tr = quintile.get("train") or {}
    q_val = quintile.get("validation") or {}
    ls = quintile.get("ls_stats") or {}
    ls_tr = ls.get("train") or {}
    ls_val = ls.get("validation") or {}
    stability = candidate.get("stability") or {}
    split = stability.get("split_stability") or {}
    uniqueness = candidate.get("uniqueness") or {}
    barra = candidate.get("barra") or {}
    distribution = candidate.get("distribution") or {}
    feasibility = candidate.get("feasibility") or {}

    def _quintile_returns(q_block: dict[str, Any]) -> dict[str, Any]:
        """Preserve just the per-bucket return keys (q1..qN), dropping the
        monotonicity / ls_mean / n_days metadata sibling fields."""
        return {k: v for k, v in q_block.items() if str(k).startswith("q")}

    return {
        "cp03": {
            # Core rubric (graded)
            "ic_oos": val_ic.get("ic_mean"),
            "icir_oos": val_ic.get("ic_ir"),
            "ls_tstat_oos": ls_val.get("tstat"),
            # IS counterparts — body can discuss IS vs OOS decay
            "ic_is": train_ic.get("ic_mean"),
            "icir_is": train_ic.get("ic_ir"),
            # Sample size + IC volatility (statistical significance context)
            "ic_std_is": train_ic.get("ic_std"),
            "ic_std_oos": val_ic.get("ic_std"),
            "n_days_is": train_ic.get("n_days"),
            "n_days_oos": val_ic.get("n_days"),
            # Win rate (hit ratio)
            "ic_win_rate_is": train_ic.get("ic_win_rate"),
            "ic_win_rate_oos": val_ic.get("ic_win_rate"),
            # Rank-order evidence (monotonicity across quintiles)
            "monotonicity_is": q_tr.get("monotonicity"),
            "monotonicity_oos": q_val.get("monotonicity"),
            # Per-quintile returns — raw spread evidence for ls_tstat
            "quintile_returns_is": _quintile_returns(q_tr),
            "quintile_returns_oos": _quintile_returns(q_val),
            # Long-short mean return (absolute level)
            "ls_mean_is": q_tr.get("ls_mean"),
            "ls_mean_oos": q_val.get("ls_mean"),
            # Long-short risk/return detail
            "ls_sharpe_oos": ls_val.get("sharpe"),
            "ls_sortino_oos": ls_val.get("sortino"),
            "ls_calmar_oos": ls_val.get("calmar"),
            "ls_max_dd_oos": ls_val.get("max_dd"),
            "ls_sharpe_is": ls_tr.get("sharpe"),
            "ls_tstat_is": ls_tr.get("tstat"),
            "ls_max_dd_is": ls_tr.get("max_dd"),
        },
        "cp04": {
            # core rubric
            "style_r_squared": barra.get("style_r_squared"),
            "alpha_survival_ratio": barra.get("alpha_survival_ratio"),
            "extreme_ratio": distribution.get("extreme_ratio"),
            # body detail
            "barra_residual_ic": barra.get("barra_residual_ic"),
            "barra_residual_icir": barra.get("barra_residual_icir"),
            "dominant_style_exposure": barra.get("dominant_style_exposure"),
            "style_crowding_risk": barra.get("style_crowding_risk"),
            # full style × coeff dict — body can discuss which styles specifically
            "style_exposures": dict(barra.get("style_exposures") or {}),
            # distribution detail
            "distribution_skew": distribution.get("skew"),
            "distribution_kurt": distribution.get("kurt"),
            "distribution_zero_ratio": distribution.get("zero_ratio"),
        },
        "cp05": {
            # core rubric
            "max_lib_corr": uniqueness.get("max_lib_corr"),
            "is_near_duplicate": bool(uniqueness.get("is_near_duplicate")),
            "incremental_ic": uniqueness.get("incremental_ic"),
            "nearest_factor_id": uniqueness.get("nearest_factor_id"),
            "nearest_factor_expression": None,  # filled in by caller from factors/{id}.yaml
            # all pairwise correlations — main agent uses this for cross-candidate
            # cluster analysis in judge.md
            "all_correlations": dict(uniqueness.get("all_correlations") or {}),
            "exceeds_threshold": bool(uniqueness.get("exceeds_threshold")),
        },
        "cp06": {
            # Core rubric (graded)
            "sign_consistency": split.get("sign_consistency"),
            "train_validation_decay": ic.get("train_validation_decay"),
            # Train/validation sign agreement (boolean) — complements sign_consistency
            "sign_consistent": ic.get("sign_consistent"),
            # Temporal stability detail
            "ic_by_year": dict(ic.get("by_year") or {}),
            "worst_quarter_ic": ic.get("worst_quarter"),
            "best_quarter_ic": ic.get("best_quarter"),
            # IC time-series properties (signal persistence / regime detection)
            "ic_autocorr_lag1": ic.get("autocorr_lag1"),
            "cum_ic_max_drawdown": ic.get("cum_ic_max_drawdown"),
            # Split-stability detail
            "split_ic_means": list(split.get("split_ic_means") or []),
            "split_dispersion": split.get("dispersion"),
            "n_splits": split.get("n_splits"),
        },
        # Feasibility — not a graded CP but useful for the main agent's
        # batch-level reflection (turnover budget, liquidity, small-cap skew,
        # signal persistence).
        "feasibility": {
            "turnover_mean": feasibility.get("turnover_mean"),
            "liquidity_coverage": feasibility.get("liquidity_coverage"),
            "tail_concentration": feasibility.get("tail_concentration"),
            "small_cap_concentration": feasibility.get("small_cap_concentration"),
            "signal_half_life": feasibility.get("signal_half_life"),
            "signal_autocorr_lag1": feasibility.get("signal_autocorr_lag1"),
            "rebalance_stress": dict(feasibility.get("rebalance_stress") or {}),
            # IC-persistence half-life (days to halve; distinct from signal_half_life
            # which measures factor-value autocorrelation)
            "ic_half_life_days": ic.get("half_life_days"),
        },
    }


def _lookup_nearest_expression(
    nearest_id: str | None,
    factors_dir: Path | None,
) -> str | None:
    """Read ``factors/{id}.yaml`` to grab the ``expression`` field.

    Returns ``None`` when the nearest id is missing or the YAML is absent
    (unit tests + early batches both exercise this path).
    """
    if not nearest_id or factors_dir is None:
        return None
    yaml_path = factors_dir / f"{nearest_id}.yaml"
    if not yaml_path.exists():
        return None
    data = load_yaml(yaml_path) or {}
    expr = data.get("expression")
    return str(expr) if expr is not None else None


def build_hints(
    batch_id: str,
    direction: str,
    result: dict[str, Any],
    batches_dir: Path,
    hard_gates_config: HardGatesConfig | None = None,
    mt_budget_config: MtBudgetConfig | None = None,
    factors_dir: Path | None = None,
) -> dict[str, Any]:
    """Build the ``_hints.yaml`` dict for one batch.

    Parameters
    ----------
    batch_id
        The batch being judged (excluded from MT cross-batch counts).
    direction
        The direction tag (for MT per-direction counter).
    result
        Parsed ``result.yaml`` — top-level dict with ``candidates`` list.
    batches_dir
        Path to ``storage/vault/batches/`` — scanned for §7.MT.
    hard_gates_config, mt_budget_config
        Configuration objects. ``None`` uses module defaults (which mirror
        ``config.yaml`` defaults).
    factors_dir
        Path to ``storage/vault/factors/`` — used to resolve
        ``metrics.cp05.nearest_factor_expression`` from the factor YAML.
        ``None`` leaves that field null (safe for unit tests + early
        batches with empty library).

    Returns
    -------
    dict
        The hints payload, ready for ``save_yaml``.
    """
    hg_cfg = hard_gates_config or HardGatesConfig()
    mt_cfg = mt_budget_config or MtBudgetConfig()

    gates = evaluate_hard_gates(result, hg_cfg)
    gate_by_id = {g.candidate_id: g for g in gates}

    counts: MtCounts = scan_batches_for_mt(
        batches_dir,
        current_batch_id=batch_id,
        current_direction=direction,
    )

    per_candidate: dict[str, Any] = {}
    for cand in result.get("candidates", []):
        cid = cand.get("candidate_id")
        if cid is None:
            continue
        gate = gate_by_id.get(cid)
        entry: dict[str, Any] = {
            "expression": cand.get("expression"),
            "coverage": cand.get("coverage"),
            "hard_gate": {
                "passed": bool(gate.passed) if gate else False,
                "reasons": list(gate.reasons) if gate else ["gate missing"],
                "gate_results": dict(gate.gate_results) if gate else {},
            },
        }
        if gate and gate.passed and not cand.get("compute_error"):
            val = (cand.get("ic") or {}).get("validation") or {}
            q_val = (cand.get("quintile") or {}).get("validation") or {}
            full = compute_mt_budget(
                counts,
                mt_cfg,
                ic_mean=val.get("ic_mean"),
                ic_ir=val.get("ic_ir"),
                monotonicity=q_val.get("monotonicity"),
                expanding_pass=False,
            )
            # Compact layout for hints: flatten + drop mt_breakdown (counts
            # already live at batch level under mt_counts).
            entry["mt_budget"] = {
                "score": full["mt_score"],
                "bucket": full["mt_bucket"],
                "terms": full["mt_breakdown"]["terms"],
                "search_adjusted": full["search_adjusted_strength"],
            }

        # Flattened rubric metrics — always emitted (even on compute_error,
        # the CP03-CP06 blocks will be all-null, making the failure visible).
        metrics = _extract_metrics(cand)
        nearest_id = metrics["cp05"].get("nearest_factor_id")
        metrics["cp05"]["nearest_factor_expression"] = _lookup_nearest_expression(
            nearest_id, factors_dir
        )
        entry["metrics"] = metrics

        per_candidate[cid] = entry

    return {
        "batch_id": batch_id,
        "direction": direction,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mt_counts": {
            "cumulative_candidates": counts.cumulative_candidates,
            "direction_candidates": counts.direction_candidates,
            "validation_exposure": counts.validation_exposure,
            "n_batches_scanned": counts.n_batches_scanned,
        },
        "per_candidate": per_candidate,
    }


def write_hints(path: str | Path, hints: dict[str, Any]) -> None:
    """Atomically write *hints* to *path* as YAML (parent dirs created)."""
    save_yaml(path, hints)
