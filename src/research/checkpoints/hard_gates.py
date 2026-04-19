"""CP01 Hard Gates — Python-only rejection rules.

Eight hard-gate checks that run before any LLM judgment. Their defining
property: **LLM has no authority to override any of them**. If a
candidate fails a hard gate, the only legal verdict is ``reject``;
``checkpoints/audit.py`` enforces this invariant.

The eight gates:

1. **compute_error** — Phase 2 recorded an exception on this candidate.
2. **coverage** — too-low cross-sectional coverage.
3. **sign_flip** — train and validation IC have opposite signs.
4. **forbidden_field_or_op** — blacklisted field / operator.
5. **ic_oos_too_low** — OOS IC magnitude below minimum threshold.
6. **oos_decay_too_low** — OOS/IS IC decay ratio below minimum.
7. **mono_sign_flip** — IS and OOS monotonicity have opposite signs.
8. **near_duplicate** — ``uniqueness.is_near_duplicate`` is true, i.e.
   ``|max_lib_corr| > 0.9`` (threshold hardcoded in Phase 2's
   ``compute_pairwise_redundancy``). ``max_lib_corr ∈ (0.70, 0.90]`` is
   NOT a hard fail — CP05 soft-judges it against ``incremental_ic``.

Each gate is a pure function taking the ``result.yaml`` candidate dict
plus any relevant config. :func:`evaluate_hard_gates` runs all of them
and returns a structured result for the pre-pack layer to consume.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Default thresholds — kept in sync with ``config.yaml.thresholds.hard_gates``.
DEFAULT_MIN_COVERAGE = 0.80
DEFAULT_MIN_OOS_DECAY = 0.20
DEFAULT_MIN_IC_OOS = 0.008
# Only fail mono_sign_flip if both sides are genuinely monotonic. Prior
# behaviour rejected train=+0.1 / val=-0.1 as a "flip" — statistically
# meaningless noise that wiped out 5+ candidates per OHLCV batch
# (batches 010/011 post-mortem, 2026-04-20). We now require
# min(|train|, |val|) >= this floor in addition to the sign mismatch.
DEFAULT_MONO_FLIP_MIN_MAGNITUDE = 0.5
DEFAULT_FORBIDDEN_FIELDS: frozenset[str] = frozenset({"$vwap"})
DEFAULT_FORBIDDEN_OPERATORS: frozenset[str] = frozenset({"Neg", "SMA"})


@dataclass(frozen=True)
class HardGatesConfig:
    """Tunable thresholds for CP01 — loaded from ``config.yaml.thresholds.hard_gates``."""

    min_coverage: float = DEFAULT_MIN_COVERAGE
    min_oos_decay: float = DEFAULT_MIN_OOS_DECAY
    min_ic_oos: float = DEFAULT_MIN_IC_OOS
    mono_flip_min_magnitude: float = DEFAULT_MONO_FLIP_MIN_MAGNITUDE
    forbidden_fields: frozenset[str] = DEFAULT_FORBIDDEN_FIELDS
    forbidden_operators: frozenset[str] = DEFAULT_FORBIDDEN_OPERATORS

    @classmethod
    def from_config_dict(cls, cfg: dict[str, Any]) -> "HardGatesConfig":
        """Build from a ``config.yaml.thresholds.hard_gates`` sub-dict."""
        return cls(
            min_coverage=float(cfg.get("min_coverage", cls.min_coverage)),
            min_oos_decay=float(cfg.get("min_oos_decay", cls.min_oos_decay)),
            min_ic_oos=float(cfg.get("min_ic_oos", cls.min_ic_oos)),
            mono_flip_min_magnitude=float(
                cfg.get("mono_flip_min_magnitude", cls.mono_flip_min_magnitude)
            ),
            forbidden_fields=frozenset(
                cfg.get("forbidden_fields", DEFAULT_FORBIDDEN_FIELDS)
            ),
            forbidden_operators=frozenset(
                cfg.get("forbidden_operators", DEFAULT_FORBIDDEN_OPERATORS)
            ),
        )


@dataclass(frozen=True)
class HardGateResult:
    """Structured output of ``evaluate_hard_gates`` for one candidate.

    ``gate_results`` is the per-gate detail dict — e.g.::

        {
          "compute_error":  {"passed": True},
          "coverage":       {"passed": True, "value": 0.989, "threshold": 0.80},
          "sign_flip":      {"passed": True, "train_ic": -0.020, "val_ic": -0.023},
          "forbidden":      {"passed": True},
          "ic_oos_min":     {"passed": True, "value": 0.023, "threshold": 0.008},
          "oos_decay":      {"passed": True, "value": 1.12, "threshold": 0.20},
          "mono_flip":      {"passed": True, "train": -0.10, "validation": -0.10},
          "near_duplicate": {"passed": True, "max_corr": 0.25, "nearest": "F005"},
        }

    Consumed by ``hints.build_hints`` so the LLM sees each gate's actual
    number, not just ``reasons: []``. ``reasons`` is retained for direct
    human-readable display.
    """

    candidate_id: str
    passed: bool
    reasons: list[str]  # empty iff passed
    gate_results: dict[str, dict[str, Any]] = field(default_factory=dict)


def _has_compute_error(candidate: dict[str, Any]) -> str | None:
    err = candidate.get("compute_error")
    if err:
        return f"compute_error: {err}"
    return None


def _check_coverage(
    candidate: dict[str, Any], min_coverage: float
) -> str | None:
    coverage = candidate.get("coverage")
    if coverage is None:
        return f"coverage missing (min {min_coverage})"
    if coverage < min_coverage:
        return f"coverage {coverage:.3f} < min {min_coverage:.3f}"
    return None


def _check_sign_flip(candidate: dict[str, Any]) -> str | None:
    ic = candidate.get("ic")
    if not ic:
        return "ic block missing"
    train_ic = ic.get("train", {}).get("ic_mean")
    val_ic = ic.get("validation", {}).get("ic_mean")
    if train_ic is None or val_ic is None:
        return "ic_mean missing"
    # "Effectively zero" threshold — below this we cannot reliably
    # assign a sign. Using 1e-4 matches the legacy execution gate.
    if abs(train_ic) < 1e-4:
        return f"train ic_mean ~0 ({train_ic:.6f}) — sign undefined"
    if abs(val_ic) < 1e-4:
        return f"validation ic_mean ~0 ({val_ic:.6f}) — sign undefined"
    if (train_ic > 0) != (val_ic > 0):
        return (
            f"sign_flip: train {train_ic:+.6f} vs validation {val_ic:+.6f}"
        )
    return None


def _check_forbidden(
    candidate: dict[str, Any],
    forbidden_fields: frozenset[str],
    forbidden_ops: frozenset[str],
) -> str | None:
    expr = candidate.get("expression") or ""
    # Field check: grep for exact ``$name`` tokens (``$vwap`` catches
    # only ``$vwap``, not ``$vwap_close_ratio`` since we look for word
    # boundaries — but to keep the rule conservative we use simple
    # substring containment and require fields to include the $).
    for field in forbidden_fields:
        if field in expr:
            return f"forbidden_field: {field} in expression"
    for op in forbidden_ops:
        # Operators appear as ``OpName(`` in Qlib DSL
        if f"{op}(" in expr:
            return f"forbidden_operator: {op}(...) in expression"
    return None


def _check_oos_decay(
    candidate: dict[str, Any], min_decay: float
) -> str | None:
    """Reject if OOS IC decayed too much relative to IS.

    Uses the signed ratio ``ic.train_validation_decay = val / train``.
    Sign flips register as negative and fail the ``< min_decay`` gate.
    """
    ic = candidate.get("ic") or {}
    decay = ic.get("train_validation_decay")
    if decay is not None and decay < min_decay:
        return f"oos_decay_too_low: {decay:.3f} < {min_decay}"
    return None


def _check_mono_flip(
    candidate: dict[str, Any],
    min_magnitude: float = DEFAULT_MONO_FLIP_MIN_MAGNITUDE,
) -> str | None:
    """Reject if IS and OOS monotonicity have opposite signs AND both are strong.

    A shallow flip (train=+0.1 / val=-0.1) is statistical noise in the
    quintile rank-correlation, not a real regime change — rejecting those
    wiped out 5+ OHLCV candidates per batch with no signal-quality
    justification (batches 010/011 post-mortem). We now require
    ``min(|train|, |val|) >= min_magnitude`` for the flip to count.
    """
    q = candidate.get("quintile") or {}
    mono_is = (q.get("train") or {}).get("monotonicity")
    mono_oos = (q.get("validation") or {}).get("monotonicity")
    if (
        mono_is is not None
        and mono_oos is not None
        and mono_is != 0
        and mono_oos != 0
        and mono_is * mono_oos < 0
        and min(abs(mono_is), abs(mono_oos)) >= min_magnitude
    ):
        return f"mono_sign_flip: IS={mono_is:.2f} OOS={mono_oos:.2f}"
    return None


def _check_ic_oos_min(
    candidate: dict[str, Any], min_ic: float
) -> str | None:
    """Reject if OOS IC magnitude is below minimum threshold."""
    ic = candidate.get("ic") or {}
    ic_oos = (ic.get("validation") or {}).get("ic_mean")
    if ic_oos is not None and abs(ic_oos) < min_ic:
        return f"ic_oos_too_low: |{ic_oos:.4f}| < {min_ic}"
    return None


def _check_near_duplicate(candidate: dict[str, Any]) -> str | None:
    """Reject if Phase 2 flagged the candidate as a library near-duplicate.

    Reads ``uniqueness.is_near_duplicate`` — set by
    :func:`research.compute.vectorized_redundancy.compute_pairwise_redundancy`
    when ``|max_lib_corr| > 0.9`` against any admitted factor. The 0.9
    threshold is hardcoded there; we don't duplicate it here.

    ``max_lib_corr`` in the softer ``(0.70, 0.90]`` band is left for
    CP05 soft judgment against ``incremental_ic``.
    """
    uniq = candidate.get("uniqueness") or {}
    if uniq.get("is_near_duplicate"):
        corr = uniq.get("max_lib_corr")
        near = uniq.get("nearest_factor_id")
        corr_str = f"{corr:.3f}" if isinstance(corr, (int, float)) else str(corr)
        return f"near_duplicate: |corr|={corr_str} with {near} (>0.9)"
    return None


def evaluate_hard_gates(
    result: dict[str, Any],
    config: HardGatesConfig | None = None,
) -> list[HardGateResult]:
    """Run all hard gates on every candidate in a ``result.yaml`` dict.

    Parameters
    ----------
    result
        Parsed ``result.yaml`` (top-level dict with ``candidates`` list).
    config
        Thresholds + blacklists. ``None`` falls back to :class:`HardGatesConfig`
        defaults (kept in sync with ``config.yaml.thresholds.hard_gates``).

    Returns
    -------
    list[HardGateResult]
        One per candidate, in the order they appear in ``result["candidates"]``.
        Each result carries both the failure ``reasons`` (free-text) and the
        ``gate_results`` dict — the structured per-gate numbers that
        downstream ``hints.yaml`` exposes to the LLM.
    """
    cfg = config or HardGatesConfig()
    results: list[HardGateResult] = []
    for c in result.get("candidates", []):
        cid = c.get("candidate_id", "?")
        reasons: list[str] = []
        gate_results: dict[str, dict[str, Any]] = {}

        # compute_error — always runs
        ce = c.get("compute_error")
        gate_results["compute_error"] = {"passed": ce is None}
        if ce:
            gate_results["compute_error"]["error"] = str(ce)
            reasons.append(f"compute_error: {ce}")

        # forbidden field / operator — always runs (expression is independent of compute success)
        forb_msg = _check_forbidden(c, cfg.forbidden_fields, cfg.forbidden_operators)
        gate_results["forbidden"] = {"passed": forb_msg is None}
        if forb_msg:
            reasons.append(forb_msg)

        # The remaining gates require Phase 2 metrics — skip them on compute_error
        if ce is None:
            # coverage
            cov = c.get("coverage")
            cov_pass = cov is not None and cov >= cfg.min_coverage
            gate_results["coverage"] = {
                "passed": cov_pass,
                "value": cov,
                "threshold": cfg.min_coverage,
            }
            if not cov_pass:
                if cov is None:
                    reasons.append(f"coverage missing (min {cfg.min_coverage})")
                else:
                    reasons.append(f"coverage {cov:.3f} < min {cfg.min_coverage:.3f}")

            # sign_flip
            ic = c.get("ic") or {}
            train_ic = (ic.get("train") or {}).get("ic_mean")
            val_ic = (ic.get("validation") or {}).get("ic_mean")
            sf_msg = _check_sign_flip(c)
            gate_results["sign_flip"] = {
                "passed": sf_msg is None,
                "train_ic": train_ic,
                "val_ic": val_ic,
            }
            if sf_msg:
                reasons.append(sf_msg)

            # ic_oos_min
            ic_oos = (ic.get("validation") or {}).get("ic_mean")
            ic_pass = ic_oos is not None and abs(ic_oos) >= cfg.min_ic_oos
            gate_results["ic_oos_min"] = {
                "passed": ic_pass or ic_oos is None,  # missing → not flagged here (caught by sign_flip)
                "value": ic_oos,
                "threshold": cfg.min_ic_oos,
            }
            if ic_oos is not None and abs(ic_oos) < cfg.min_ic_oos:
                reasons.append(f"ic_oos_too_low: |{ic_oos:.4f}| < {cfg.min_ic_oos}")

            # oos_decay
            decay = ic.get("train_validation_decay")
            decay_pass = decay is None or decay >= cfg.min_oos_decay
            gate_results["oos_decay"] = {
                "passed": decay_pass,
                "value": decay,
                "threshold": cfg.min_oos_decay,
            }
            if decay is not None and decay < cfg.min_oos_decay:
                reasons.append(f"oos_decay_too_low: {decay:.3f} < {cfg.min_oos_decay}")

            # mono_flip (magnitude-gated; see _check_mono_flip)
            q = c.get("quintile") or {}
            m_is = (q.get("train") or {}).get("monotonicity")
            m_oos = (q.get("validation") or {}).get("monotonicity")
            mono_pass = not (
                m_is is not None
                and m_oos is not None
                and m_is != 0
                and m_oos != 0
                and m_is * m_oos < 0
                and min(abs(m_is), abs(m_oos)) >= cfg.mono_flip_min_magnitude
            )
            gate_results["mono_flip"] = {
                "passed": mono_pass,
                "train": m_is,
                "validation": m_oos,
                "min_magnitude": cfg.mono_flip_min_magnitude,
            }
            if not mono_pass:
                reasons.append(
                    f"mono_sign_flip: IS={m_is:.2f} OOS={m_oos:.2f} "
                    f"(both |·|≥{cfg.mono_flip_min_magnitude})"
                )

            # near_duplicate
            uniq = c.get("uniqueness") or {}
            is_near = bool(uniq.get("is_near_duplicate"))
            gate_results["near_duplicate"] = {
                "passed": not is_near,
                "max_corr": uniq.get("max_lib_corr"),
                "nearest": uniq.get("nearest_factor_id"),
            }
            if is_near:
                corr = uniq.get("max_lib_corr")
                corr_str = (
                    f"{corr:.3f}" if isinstance(corr, (int, float)) else str(corr)
                )
                reasons.append(
                    f"near_duplicate: |corr|={corr_str} with "
                    f"{uniq.get('nearest_factor_id')} (>0.9)"
                )

        results.append(
            HardGateResult(
                candidate_id=cid,
                passed=len(reasons) == 0,
                reasons=reasons,
                gate_results=gate_results,
            )
        )

    return results
