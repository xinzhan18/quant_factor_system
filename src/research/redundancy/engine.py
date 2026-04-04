"""RedundancyEngine: orchestrates 3-layer redundancy analysis.

Pure computation, no I/O.
"""

from __future__ import annotations

from research.redundancy.pairwise import compute_pairwise_redundancy
from research.redundancy.family import compute_family_overlap
from research.redundancy.subspace import compute_subspace_redundancy


def _get_family_status(family_id: str, family_registry: dict) -> str:
    """Look up the registration status for a family_id.

    Returns one of: registered, provisional, unknown, invalid.
    """
    if not family_id or family_id == "FM_unknown":
        return "unknown"

    entry = family_registry.get(family_id)
    if entry is None:
        return "unknown"

    return entry.get("status", "registered")


def _filter_family_members(
    library_signals: dict[str, object],
    library_meta: dict[str, dict],
    family_id: str,
) -> dict[str, object]:
    """Return signals for library factors belonging to *family_id*."""
    return {
        fid: library_signals[fid]
        for fid, meta in library_meta.items()
        if meta.get("family_id") == family_id and fid in library_signals
    }


def _select_basis(
    candidate_meta: dict,
    library_signals: dict[str, object],
    library_meta: dict[str, dict],
    family_id: str,
    pairwise_corrs: dict[str, float] | None = None,
    k: int = 3,
) -> dict[str, object]:
    """Select up to *k* basis factors for subspace regression.

    Priority order:
    1. Same family_id admitted factors
    2. Same logic_id closest factors (by pairwise |corr|)
    """
    basis: dict[str, object] = {}

    # Step 1: same family factors
    family_members = _filter_family_members(library_signals, library_meta, family_id)
    for fid, sig in family_members.items():
        if len(basis) >= k:
            break
        basis[fid] = sig

    if len(basis) >= k:
        return basis

    # Step 2: same logic_id factors not already selected, ordered by |corr|
    logic_id = candidate_meta.get("logic_id")
    same_logic = {}
    if logic_id:
        for fid, meta in library_meta.items():
            if (
                meta.get("logic_id") == logic_id
                and fid not in basis
                and fid in library_signals
            ):
                same_logic[fid] = library_signals[fid]

    if pairwise_corrs and same_logic:
        # Sort by absolute correlation descending
        sorted_ids = sorted(
            same_logic.keys(),
            key=lambda fid: abs(pairwise_corrs.get(fid, 0.0)),
            reverse=True,
        )
        for fid in sorted_ids:
            if len(basis) >= k:
                break
            basis[fid] = same_logic[fid]

    elif same_logic:
        for fid, sig in same_logic.items():
            if len(basis) >= k:
                break
            basis[fid] = sig

    return basis


class RedundancyEngine:
    """Orchestrates 3-layer redundancy analysis."""

    def analyze(
        self,
        candidate_signal,
        candidate_meta: dict,
        library_signals: dict[str, object],
        library_meta: dict[str, dict],
        family_registry: dict,
        forward_returns=None,
    ) -> dict:
        """Run all 3 redundancy layers.

        Parameters
        ----------
        candidate_signal : DataFrame
            MultiIndex (datetime, instrument), single value column.
        candidate_meta : dict
            Must have ``family_id``; may have ``logic_id``,
            ``structure_template``, ``conditioning_type``, ``horizon_bucket``.
        library_signals : dict[str, DataFrame]
            ``{factor_id: DataFrame}`` for admitted library factors.
        library_meta : dict[str, dict]
            ``{factor_id: meta_dict}`` with at least ``family_id``.
        family_registry : dict
            ``{family_id: {status, structure_template, conditioning_type, horizon_bucket, ...}}``.
        forward_returns : DataFrame or None
            Required for subspace layer.  If None, subspace is skipped.

        Returns
        -------
        dict with keys: pairwise, family_view, subspace_view
        """
        # Layer 1: pairwise duplication
        pairwise = compute_pairwise_redundancy(candidate_signal, library_signals)

        # Determine family status
        family_id = candidate_meta.get("family_id", "FM_unknown")
        family_status = _get_family_status(family_id, family_registry)

        # Layer 2: family-level redundancy
        family_view = None
        family_members = {}

        if family_status in ("registered", "provisional"):
            family_members = _filter_family_members(
                library_signals, library_meta, family_id,
            )
            # Provisional with no members falls through to the else below.
            if family_status == "registered" or family_members:
                reg_entry = family_registry.get(family_id, {})
                candidate_structure = {
                    "structure_template": candidate_meta.get("structure_template"),
                    "conditioning_type": candidate_meta.get("conditioning_type"),
                    "horizon_bucket": candidate_meta.get("horizon_bucket"),
                }
                family_view = compute_family_overlap(
                    candidate_signal,
                    family_members,
                    candidate_structure,
                    reg_entry,
                )
                family_view["family_assignment_status"] = family_status
                if family_status == "provisional":
                    family_view["family_registry_check"] = "degraded"

        if family_view is None:
            family_view = {
                "family_overlap_score": None,
                "family_assignment_status": family_status,
                "family_registry_check": "degraded",
            }

        # Layer 3: subspace redundancy
        subspace_view = None
        if forward_returns is not None:
            family_size = len(family_members)
            basis = _select_basis(
                candidate_meta,
                library_signals,
                library_meta,
                family_id,
                pairwise_corrs=pairwise.get("all_correlations"),
                k=3,
            )
            if len(basis) >= 2:
                subspace_view = compute_subspace_redundancy(
                    candidate_signal,
                    basis,
                    forward_returns,
                    family_size=family_size,
                )
            else:
                subspace_view = {
                    "subspace_redundancy_score": None,
                    "residual_incremental_ic": None,
                    "basis_factor_ids": list(basis.keys()),
                    "basis_factor_count": len(basis),
                    "validation_days": 0,
                    "subspace_confidence": "insufficient_basis",
                }

        return {
            "pairwise": pairwise,
            "family_view": family_view,
            "subspace_view": subspace_view,
        }
