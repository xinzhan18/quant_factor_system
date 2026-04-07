"""Manifest validation against reflected logic constraints."""

from __future__ import annotations

from typing import Any

from research.storage.paths import StoragePaths
from research.storage.yaml_io import load_yaml


def validate_manifest_against_logic_cards(
    manifest: dict[str, Any],
    *,
    paths: StoragePaths | None = None,
) -> None:
    paths = paths or StoragePaths()
    cards = {
        path.stem: load_yaml(path)
        for path in sorted(paths.logic_cards_dir.glob("L*.yaml"))
    }
    violations: list[str] = []

    for candidate in manifest.get("candidates", []):
        if not isinstance(candidate, dict):
            continue
        cid = candidate.get("candidate_id", "?")
        logic_id = str(candidate.get("logic_id", ""))
        if not logic_id:
            continue
        card = cards.get(logic_id)
        if not card:
            continue

        expression = str(candidate.get("expression", ""))
        route_type = str(candidate.get("route_type", ""))
        family_id = str(candidate.get("family_id", ""))

        # --- Avoid patterns ---
        for pattern in card.get("contract", {}).get("avoid_patterns", []):
            pattern_text = str(pattern).strip()
            if pattern_text and pattern_text in expression:
                violations.append(
                    f"{cid} violates {logic_id} avoid_pattern: {pattern_text}"
                )

        # --- Genesis route guard ---
        if card.get("evidence_summary", {}).get("factors_admitted", 0) and route_type == "genesis":
            lineage = str(candidate.get("experiment_lineage_tag", ""))
            if "genesis" in lineage and "conditional" not in lineage and "regime" not in lineage:
                violations.append(
                    f"{cid} uses genesis route for admitted logic {logic_id}"
                )

        # --- Thread alignment ---
        _validate_thread_alignment(candidate, card, violations)

        # --- Family guard ---
        _validate_family_guard(candidate, card, violations)

    if violations:
        raise ValueError(
            "Manifest violates reflected logic constraints:\n- "
            + "\n- ".join(violations)
        )


def _get_source_thread_id(candidate: dict[str, Any]) -> str:
    """Read source_thread_id or source_thread (backward compat)."""
    return str(
        candidate.get("source_thread_id")
        or candidate.get("source_thread")
        or ""
    )


def _validate_thread_alignment(
    candidate: dict[str, Any],
    card: dict[str, Any],
    violations: list[str],
) -> None:
    """Validate that the candidate references an active thread."""
    cid = candidate.get("candidate_id", "?")
    logic_id = str(card.get("logic_id", ""))
    route_type = str(candidate.get("route_type", ""))

    threads = card.get("deepening_threads", []) or []
    thread_map = {
        str(t.get("id", "")): t
        for t in threads
        if isinstance(t, dict) and t.get("id")
    }

    # If the card has no threads at all, skip thread validation
    # (early-stage logic cards may not have threads yet)
    if not thread_map:
        return

    # Check if any thread is still active
    active_threads = [
        tid for tid, t in thread_map.items()
        if t.get("status") == "active"
    ]

    source_tid = _get_source_thread_id(candidate)

    if not source_tid:
        # Missing source_thread_id — require it when card has threads
        violations.append(
            f"{cid} missing source_thread_id (logic {logic_id})"
        )
        return

    if source_tid not in thread_map:
        violations.append(
            f"{cid} references thread {source_tid} not found in {logic_id}"
        )
        return

    thread = thread_map[source_tid]
    thread_status = str(thread.get("status", ""))

    if thread_status != "active":
        # Allow escape/decorrelate on non-active threads
        if route_type not in ("escape", "decorrelate"):
            violations.append(
                f"{cid} references thread {source_tid} (status={thread_status}) "
                f"in {logic_id} — only escape/decorrelate allowed for non-active threads"
            )

    # If NO active threads exist AND this candidate is not escape/decorrelate
    if not active_threads and route_type not in ("escape", "decorrelate"):
        violations.append(
            f"{cid} uses route_type={route_type} but {logic_id} has no active threads "
            f"— only escape/decorrelate allowed"
        )


def _validate_family_guard(
    candidate: dict[str, Any],
    card: dict[str, Any],
    violations: list[str],
) -> None:
    """Block genesis/mutate into failed families and non-escape into exhausted routes."""
    cid = candidate.get("candidate_id", "?")
    logic_id = str(card.get("logic_id", ""))
    route_type = str(candidate.get("route_type", ""))
    family_id = str(candidate.get("family_id", ""))

    if not family_id:
        return

    evidence = card.get("evidence_summary", {})

    # Failed families: block genesis/mutate, allow repair/decorrelate/escape
    failed_fids = {
        str(f.get("family_id", ""))
        for f in evidence.get("failed_families", [])
        if isinstance(f, dict)
    }
    if family_id in failed_fids and route_type in ("genesis", "mutate"):
        violations.append(
            f"{cid} uses {route_type} into failed family {family_id} "
            f"in {logic_id} — only repair/decorrelate/escape allowed"
        )

    # Exhausted routes: only escape allowed
    exhausted_fids = {
        str(f.get("family_id", ""))
        for f in evidence.get("exhausted_routes", [])
        if isinstance(f, dict)
    }
    if family_id in exhausted_fids and route_type != "escape":
        violations.append(
            f"{cid} uses {route_type} into exhausted route {family_id} "
            f"in {logic_id} — only escape allowed"
        )
