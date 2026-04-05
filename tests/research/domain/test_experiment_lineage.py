"""Tests for research.domain.experiment_lineage."""

import pytest

from research.domain.experiment_lineage import ExperimentLineageTag, _normalize_anchor


class TestNormalizeAnchor:
    def test_lowercase(self):
        assert _normalize_anchor("BreakOut") == "breakout"

    def test_whitespace_to_underscore(self):
        assert _normalize_anchor("volume price") == "volume_price"

    def test_hyphens_to_underscore(self):
        assert _normalize_anchor("high-low") == "high_low"

    def test_strip_edges(self):
        assert _normalize_anchor("  foo  ") == "foo"

    def test_special_chars(self):
        assert _normalize_anchor("hello@world!") == "hello_world"


class TestExperimentLineageTag:
    def test_generate_basic(self):
        tag = ExperimentLineageTag.generate(
            logic_id="L021",
            route_type="genesis",
            mechanism_anchors=["breakout"],
            family_anchor="FM_breakout",
        )
        assert tag.logic_id == "l021"
        assert tag.route_type == "genesis"
        assert tag.mechanism_anchors == ("breakout",)
        assert tag.conditioning_anchors == ()
        assert tag.family_anchor == "fm_breakout"
        assert tag.version == 1

    def test_generate_with_conditioning(self):
        tag = ExperimentLineageTag.generate(
            logic_id="L021",
            route_type="genesis",
            mechanism_anchors=["breakout", "compression"],
            conditioning_anchors=["volume_gate", "trend_filter"],
            family_anchor="FM_breakout",
        )
        # Anchors should be sorted
        assert tag.mechanism_anchors == ("breakout", "compression")
        assert tag.conditioning_anchors == ("trend_filter", "volume_gate")

    def test_generate_requires_mechanism(self):
        with pytest.raises(ValueError, match="mechanism anchor"):
            ExperimentLineageTag.generate(
                logic_id="L021",
                route_type="genesis",
                mechanism_anchors=[],
            )

    def test_generate_requires_positive_version(self):
        with pytest.raises(ValueError, match="Version"):
            ExperimentLineageTag.generate(
                logic_id="L021",
                route_type="genesis",
                mechanism_anchors=["breakout"],
                version=0,
            )

    def test_tag_format(self):
        tag = ExperimentLineageTag.generate(
            logic_id="L021",
            route_type="genesis",
            mechanism_anchors=["breakout"],
            conditioning_anchors=["compression"],
            family_anchor="FM_breakout",
        )
        assert tag.tag.startswith("ELT_")
        assert tag.tag.endswith("_v1")
        assert "l021" in tag.tag
        assert "genesis" in tag.tag

    def test_tag_without_conditioning(self):
        tag = ExperimentLineageTag.generate(
            logic_id="L001",
            route_type="mutate",
            mechanism_anchors=["reversal"],
            family_anchor="FM_reversal",
        )
        assert "none" in tag.tag  # conditioning is "none"

    def test_tag_without_family(self):
        tag = ExperimentLineageTag.generate(
            logic_id="L001",
            route_type="genesis",
            mechanism_anchors=["momentum"],
        )
        assert tag.family_anchor == "none"

    def test_str_returns_tag(self):
        tag = ExperimentLineageTag.generate(
            logic_id="L001",
            route_type="genesis",
            mechanism_anchors=["test"],
            family_anchor="FM_test",
        )
        assert str(tag) == tag.tag

    def test_next_version(self):
        tag = ExperimentLineageTag.generate(
            logic_id="L021",
            route_type="genesis",
            mechanism_anchors=["breakout"],
            version=1,
        )
        v2 = tag.next_version()
        assert v2.version == 2
        assert v2.logic_id == tag.logic_id
        assert v2.mechanism_anchors == tag.mechanism_anchors

    def test_frozen(self):
        tag = ExperimentLineageTag.generate(
            logic_id="L001",
            route_type="genesis",
            mechanism_anchors=["test"],
        )
        with pytest.raises(AttributeError):
            tag.version = 99

    def test_parse_roundtrip(self):
        original = ExperimentLineageTag.generate(
            logic_id="L021",
            route_type="genesis",
            mechanism_anchors=["breakout"],
            family_anchor="FM_breakout",
            version=3,
        )
        tag_str = original.tag
        parsed = ExperimentLineageTag.parse(tag_str)
        assert parsed.logic_id == original.logic_id
        assert parsed.route_type == original.route_type
        assert parsed.version == original.version

    def test_parse_invalid_prefix(self):
        with pytest.raises(ValueError, match="ELT_"):
            ExperimentLineageTag.parse("XYZ_l021_genesis_v1")

    def test_parse_missing_version(self):
        with pytest.raises(ValueError, match="_v<N>"):
            ExperimentLineageTag.parse("ELT_l021_genesis_breakout")

    def test_anchors_are_sorted(self):
        tag = ExperimentLineageTag.generate(
            logic_id="L001",
            route_type="genesis",
            mechanism_anchors=["zebra", "alpha", "middle"],
        )
        assert tag.mechanism_anchors == ("alpha", "middle", "zebra")
