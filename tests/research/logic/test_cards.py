"""Tests for research.logic.cards."""
from __future__ import annotations

from pathlib import Path

import yaml

from research.logic.cards import LogicCard, LogicCardStore


class TestLogicCardNormalization:
    def test_category_alias_normalized(self):
        card = LogicCard(
            logic_id="L001",
            name="test logic",
            category="price_volume",
            status="active",
            priority="high",
        )
        assert card.category == "volume_price"

    def test_discovery_budget_int_normalized_to_dict(self):
        card = LogicCard(
            logic_id="L001",
            name="test logic",
            category="volume_price",
            status="active",
            priority="high",
            discovery_budget=3,
        )
        assert card.discovery_budget == {"adjacent_discovery_route_quota": 3}


class TestLogicCardStoreReflection:
    def test_create_also_creates_reflection_stub(self, tmp_path):
        store = LogicCardStore(tmp_path)

        card = store.create(
            name="volume_price_divergence",
            category="price_volume",
            status="active",
            priority="medium",
        )

        reflection_path = tmp_path / "logic" / "reflections" / f"{card.logic_id}.md"
        assert reflection_path.exists()
        text = reflection_path.read_text(encoding="utf-8")
        assert f"# {card.logic_id} {card.name}" in text
        assert "Initial reflection pending first judge/reflect cycle." in text
        assert card.category == "volume_price"


class TestRepositoryLogicConsistency:
    def test_every_logic_card_has_reflection(self):
        cards_dir = Path("storage/logic/cards")
        reflections_dir = Path("storage/logic/reflections")

        for card_path in sorted(cards_dir.glob("L*.yaml")):
            with open(card_path, "r", encoding="utf-8") as f:
                card = yaml.safe_load(f) or {}
            logic_id = card["logic_id"]
            reflection_path = reflections_dir / f"{logic_id}.md"
            assert reflection_path.exists(), f"missing reflection for {logic_id}"
