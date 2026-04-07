"""Tests for manifest validation against logic card constraints."""

from __future__ import annotations

from pathlib import Path

import pytest

from research.storage.manifest_validator import validate_manifest_against_logic_cards
from research.storage.paths import StoragePaths
from research.storage.yaml_io import save_yaml


def _setup(tmp_path: Path) -> StoragePaths:
    paths = StoragePaths(tmp_path / "storage")
    paths.ensure_dirs()
    return paths


def _card_with_threads(
    logic_id: str = "L001",
    threads: list | None = None,
    failed_families: list | None = None,
    exhausted_routes: list | None = None,
) -> dict:
    return {
        "logic_id": logic_id,
        "status": "productive",
        "contract": {
            "avoid_patterns": [],
        },
        "evidence_summary": {
            "factors_admitted": 1,
            "failed_families": failed_families or [],
            "exhausted_routes": exhausted_routes or [],
        },
        "deepening_threads": threads or [],
    }


def _candidate(
    source_thread_id: str = "T001",
    route_type: str = "mutate",
    family_id: str = "FM_test",
    **overrides,
) -> dict:
    d = {
        "candidate_id": "C001",
        "logic_id": "L001",
        "route_id": "R001",
        "route_type": route_type,
        "family_id": family_id,
        "expression": "Rank($close)",
        "source_thread_id": source_thread_id,
    }
    d.update(overrides)
    return d


# ===================================================================
# Thread alignment
# ===================================================================

class TestThreadAlignment:
    def test_valid_active_thread(self, tmp_path: Path) -> None:
        paths = _setup(tmp_path)
        save_yaml(
            paths.logic_card_file("L001"),
            _card_with_threads(threads=[
                {"id": "T001", "status": "active", "priority": "high"},
            ]),
        )
        manifest = {"candidates": [_candidate(source_thread_id="T001")]}
        # Should not raise
        validate_manifest_against_logic_cards(manifest, paths=paths)

    def test_missing_source_thread_id(self, tmp_path: Path) -> None:
        paths = _setup(tmp_path)
        save_yaml(
            paths.logic_card_file("L001"),
            _card_with_threads(threads=[
                {"id": "T001", "status": "active"},
            ]),
        )
        c = _candidate()
        del c["source_thread_id"]
        manifest = {"candidates": [c]}
        with pytest.raises(ValueError, match="missing source_thread_id"):
            validate_manifest_against_logic_cards(manifest, paths=paths)

    def test_source_thread_compat(self, tmp_path: Path) -> None:
        """Old-format source_thread field is accepted."""
        paths = _setup(tmp_path)
        save_yaml(
            paths.logic_card_file("L001"),
            _card_with_threads(threads=[
                {"id": "T001", "status": "active"},
            ]),
        )
        c = _candidate()
        del c["source_thread_id"]
        c["source_thread"] = "T001"
        manifest = {"candidates": [c]}
        # Should not raise
        validate_manifest_against_logic_cards(manifest, paths=paths)

    def test_thread_not_found(self, tmp_path: Path) -> None:
        paths = _setup(tmp_path)
        save_yaml(
            paths.logic_card_file("L001"),
            _card_with_threads(threads=[
                {"id": "T001", "status": "active"},
            ]),
        )
        manifest = {"candidates": [_candidate(source_thread_id="T999")]}
        with pytest.raises(ValueError, match="T999 not found"):
            validate_manifest_against_logic_cards(manifest, paths=paths)

    def test_parked_thread_blocks_mutate(self, tmp_path: Path) -> None:
        paths = _setup(tmp_path)
        save_yaml(
            paths.logic_card_file("L001"),
            _card_with_threads(threads=[
                {"id": "T001", "status": "parked"},
            ]),
        )
        manifest = {"candidates": [_candidate(source_thread_id="T001", route_type="mutate")]}
        with pytest.raises(ValueError, match="non-active threads"):
            validate_manifest_against_logic_cards(manifest, paths=paths)

    def test_parked_thread_allows_escape(self, tmp_path: Path) -> None:
        paths = _setup(tmp_path)
        save_yaml(
            paths.logic_card_file("L001"),
            _card_with_threads(threads=[
                {"id": "T001", "status": "parked"},
            ]),
        )
        manifest = {"candidates": [_candidate(source_thread_id="T001", route_type="escape")]}
        # Should not raise
        validate_manifest_against_logic_cards(manifest, paths=paths)

    def test_no_active_threads_blocks_genesis(self, tmp_path: Path) -> None:
        paths = _setup(tmp_path)
        save_yaml(
            paths.logic_card_file("L001"),
            _card_with_threads(threads=[
                {"id": "T001", "status": "answered"},
                {"id": "T002", "status": "parked"},
            ]),
        )
        manifest = {"candidates": [_candidate(source_thread_id="T001", route_type="genesis")]}
        with pytest.raises(ValueError, match="no active threads"):
            validate_manifest_against_logic_cards(manifest, paths=paths)


# ===================================================================
# Family guard
# ===================================================================

class TestFamilyGuard:
    def test_failed_family_blocks_mutate(self, tmp_path: Path) -> None:
        paths = _setup(tmp_path)
        save_yaml(
            paths.logic_card_file("L001"),
            _card_with_threads(
                threads=[{"id": "T001", "status": "active"}],
                failed_families=[{"family_id": "FM_dead", "reason": "style trap"}],
            ),
        )
        manifest = {"candidates": [
            _candidate(source_thread_id="T001", route_type="mutate", family_id="FM_dead"),
        ]}
        with pytest.raises(ValueError, match="failed family"):
            validate_manifest_against_logic_cards(manifest, paths=paths)

    def test_failed_family_allows_repair(self, tmp_path: Path) -> None:
        paths = _setup(tmp_path)
        save_yaml(
            paths.logic_card_file("L001"),
            _card_with_threads(
                threads=[{"id": "T001", "status": "active"}],
                failed_families=[{"family_id": "FM_dead", "reason": "style trap"}],
            ),
        )
        manifest = {"candidates": [
            _candidate(source_thread_id="T001", route_type="repair", family_id="FM_dead"),
        ]}
        # Should not raise
        validate_manifest_against_logic_cards(manifest, paths=paths)

    def test_failed_family_allows_decorrelate(self, tmp_path: Path) -> None:
        paths = _setup(tmp_path)
        save_yaml(
            paths.logic_card_file("L001"),
            _card_with_threads(
                threads=[{"id": "T001", "status": "active"}],
                failed_families=[{"family_id": "FM_dead"}],
            ),
        )
        manifest = {"candidates": [
            _candidate(source_thread_id="T001", route_type="decorrelate", family_id="FM_dead"),
        ]}
        validate_manifest_against_logic_cards(manifest, paths=paths)

    def test_exhausted_route_only_allows_escape(self, tmp_path: Path) -> None:
        paths = _setup(tmp_path)
        save_yaml(
            paths.logic_card_file("L001"),
            _card_with_threads(
                threads=[{"id": "T001", "status": "active"}],
                exhausted_routes=[{"family_id": "FM_done"}],
            ),
        )
        # decorrelate should be blocked for exhausted
        manifest = {"candidates": [
            _candidate(source_thread_id="T001", route_type="decorrelate", family_id="FM_done"),
        ]}
        with pytest.raises(ValueError, match="exhausted route"):
            validate_manifest_against_logic_cards(manifest, paths=paths)

        # escape should pass
        manifest2 = {"candidates": [
            _candidate(source_thread_id="T001", route_type="escape", family_id="FM_done"),
        ]}
        validate_manifest_against_logic_cards(manifest2, paths=paths)

    def test_productive_family_not_blocked(self, tmp_path: Path) -> None:
        """productive_families should NOT trigger any guard."""
        paths = _setup(tmp_path)
        card = _card_with_threads(threads=[{"id": "T001", "status": "active"}])
        card["evidence_summary"]["productive_families"] = [{"family_id": "FM_good"}]
        save_yaml(paths.logic_card_file("L001"), card)
        manifest = {"candidates": [
            _candidate(source_thread_id="T001", route_type="genesis", family_id="FM_good"),
        ]}
        validate_manifest_against_logic_cards(manifest, paths=paths)
