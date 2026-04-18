from pathlib import Path
import pytest
from research.archive.backfill import (
    backfill_candidate_md, backfill_judge_md, backfill_direction_md,
)


@pytest.fixture
def sample_candidate_md(tmp_path):
    p = tmp_path / "C001.md"
    p.write_text(
        "---\n"
        "candidate_id: C001\n"
        "batch_id: batch_009\n"
        "direction: timing\n"
        "expression: Std($close, 20)\n"
        "verdict: admit\n"
        "factor_id: null\n"
        "key_metrics_short: 'ICIR=0.3 ls_t=3.2'\n"
        "thread_id: T001\n"
        "---\n\n# C001\n"
    )
    return p


def test_backfill_candidate_md_sets_factor_id(sample_candidate_md):
    backfill_candidate_md(sample_candidate_md, "F042")
    text = sample_candidate_md.read_text()
    assert "factor_id: F042" in text
    assert "factor_id: null" not in text


def test_backfill_candidate_md_is_idempotent(sample_candidate_md):
    backfill_candidate_md(sample_candidate_md, "F042")
    before = sample_candidate_md.read_text()
    backfill_candidate_md(sample_candidate_md, "F042")
    after = sample_candidate_md.read_text()
    assert before == after


def test_backfill_candidate_md_does_not_touch_already_set(tmp_path):
    p = tmp_path / "C002.md"
    p.write_text("---\ncandidate_id: C002\nfactor_id: F007\n---\n")
    original = p.read_text()
    backfill_candidate_md(p, "F007")
    assert p.read_text() == original


def test_backfill_judge_md_inlines_factor_ids(tmp_path):
    p = tmp_path / "judge.md"
    p.write_text(
        "---\n"
        "batch_id: batch_009\n"
        "candidates:\n"
        "  - candidate_id: C001\n"
        "    verdict: admit\n"
        "  - candidate_id: C002\n"
        "    verdict: reject\n"
        "---\n\n"
        "| C001 | admit | ICIR=0.3 | [[batches/batch_009/candidates/C001]] |\n"
        "| C002 | reject | cov=0.6 | [[batches/batch_009/candidates/C002]] |\n"
    )
    backfill_judge_md(p, {"C001": "F042"})
    text = p.read_text()
    assert "admit → F042" in text
    assert "[[factors/F042]]" in text
    # reject rows untouched — the table row containing C002 must still have
    # exactly "| reject |" with no F{id} inlined
    assert "| C002 | reject | cov=0.6 | [[batches/batch_009/candidates/C002]] |" in text
    assert "reject →" not in text


def test_backfill_judge_md_is_idempotent(tmp_path):
    p = tmp_path / "judge.md"
    p.write_text(
        "| C001 | admit | ICIR=0.3 | [[batches/batch_009/candidates/C001]] |\n"
    )
    backfill_judge_md(p, {"C001": "F042"})
    once = p.read_text()
    backfill_judge_md(p, {"C001": "F042"})
    twice = p.read_text()
    assert once == twice


def test_backfill_direction_md_appends_factor_link(tmp_path):
    p = tmp_path / "timing.md"
    p.write_text(
        "---\nname: timing\nstatus: active\n---\n\n"
        "## Threads\n\n### T001\n\n**Evidence trail**\n\n"
        "- [[batches/batch_009/candidates/C001|batch_009 C001]]: ICIR=0.3 → **admit**\n"
        "- [[batches/batch_009/candidates/C002|batch_009 C002]]: cov=0.6 → reject\n"
    )
    backfill_direction_md(p, {"C001": "F042"}, batch_id="batch_009")
    text = p.read_text()
    assert "→ **admit → [[factors/F042]]**" in text
    # reject line untouched
    assert "→ reject" in text


def test_backfill_direction_md_is_idempotent(tmp_path):
    p = tmp_path / "timing.md"
    p.write_text(
        "- [[batches/batch_009/candidates/C001|batch_009 C001]]: ICIR=0.3 → **admit**\n"
    )
    backfill_direction_md(p, {"C001": "F042"}, batch_id="batch_009")
    once = p.read_text()
    backfill_direction_md(p, {"C001": "F042"}, batch_id="batch_009")
    twice = p.read_text()
    assert once == twice


def test_backfill_candidate_md_noop_on_missing_frontmatter(tmp_path):
    # File without frontmatter must not crash
    p = tmp_path / "C003.md"
    p.write_text("# just a heading\n")
    backfill_candidate_md(p, "F042")  # no exception; file unchanged
    assert p.read_text() == "# just a heading\n"
