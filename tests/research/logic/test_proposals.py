"""Tests for research.logic.proposals — LogicProposal creation and persistence."""
import pytest
import yaml

from research.logic.proposals import (
    LogicProposal,
    VALID_ORIGIN_TYPES,
    create_proposal,
    list_proposals,
    load_proposal,
)


class TestLogicProposal:
    """Unit tests for the LogicProposal dataclass."""

    def test_create_minimal(self):
        p = LogicProposal(
            proposal_id="P001",
            name="test logic",
            origin_type="canonical",
            category="volume_price",
            thesis="A thesis",
            mechanism="A mechanism",
        )
        assert p.proposal_id == "P001"
        assert p.origin_type == "canonical"
        assert p.submitted_at  # auto-set

    def test_invalid_origin_type_raises(self):
        with pytest.raises(ValueError, match="Invalid origin_type"):
            LogicProposal(
                proposal_id="P001",
                name="bad",
                origin_type="invented",
                category="x",
                thesis="x",
                mechanism="x",
            )

    def test_all_valid_origin_types(self):
        for ot in VALID_ORIGIN_TYPES:
            p = LogicProposal(
                proposal_id="P001",
                name="test",
                origin_type=ot,
                category="x",
                thesis="x",
                mechanism="x",
            )
            assert p.origin_type == ot

    def test_roundtrip_dict(self):
        p = LogicProposal(
            proposal_id="P042",
            name="roundtrip test",
            origin_type="empirical",
            category="momentum",
            thesis="thesis text",
            mechanism="mechanism text",
            novelty_claim="novel",
            observable_proxy={"required_fields": ["close"]},
        )
        d = p.to_dict()
        p2 = LogicProposal.from_dict(d)
        assert p2.proposal_id == p.proposal_id
        assert p2.name == p.name
        assert p2.origin_type == p.origin_type
        assert p2.observable_proxy == p.observable_proxy


class TestCreateProposal:
    """Integration tests for create_proposal / load / list."""

    def test_create_and_load(self, tmp_path):
        p = create_proposal(
            tmp_path,
            name="test proposal",
            origin_type="canonical",
            category="volume_price",
            thesis="test thesis",
            mechanism="test mechanism",
        )
        assert p.proposal_id == "P001"

        # Verify file exists
        path = tmp_path / "logic" / "proposals" / "proposal_P001.yaml"
        assert path.exists()

        # Verify YAML content
        with open(path) as f:
            data = yaml.safe_load(f)
        assert data["proposal_id"] == "P001"
        assert data["origin_type"] == "canonical"

        # Load back
        loaded = load_proposal(tmp_path, "P001")
        assert loaded is not None
        assert loaded.proposal_id == "P001"
        assert loaded.name == "test proposal"

    def test_auto_increment_id(self, tmp_path):
        p1 = create_proposal(
            tmp_path,
            name="first",
            origin_type="canonical",
            category="x",
            thesis="x",
            mechanism="x",
        )
        p2 = create_proposal(
            tmp_path,
            name="second",
            origin_type="empirical",
            category="y",
            thesis="y",
            mechanism="y",
        )
        assert p1.proposal_id == "P001"
        assert p2.proposal_id == "P002"

    def test_list_proposals(self, tmp_path):
        create_proposal(
            tmp_path,
            name="a",
            origin_type="canonical",
            category="x",
            thesis="x",
            mechanism="x",
        )
        create_proposal(
            tmp_path,
            name="b",
            origin_type="near_miss",
            category="y",
            thesis="y",
            mechanism="y",
        )
        proposals = list_proposals(tmp_path)
        assert len(proposals) == 2
        assert proposals[0].proposal_id == "P001"
        assert proposals[1].proposal_id == "P002"

    def test_load_nonexistent_returns_none(self, tmp_path):
        assert load_proposal(tmp_path, "P999") is None

    def test_list_empty(self, tmp_path):
        assert list_proposals(tmp_path) == []
