from __future__ import annotations

from research.papers.image_extract import (
    caption_to_filename_stub,
    detect_page_captions,
    infer_arxiv_id,
)


def test_infer_arxiv_id() -> None:
    assert infer_arxiv_id("arXiv:2602.23784v2") == "2602.23784"
    assert infer_arxiv_id("TradeFM_2602.23784.pdf") == "2602.23784"
    assert infer_arxiv_id("not_a_paper") is None


def test_detect_page_captions() -> None:
    text = """
    Figure 2: Rank correlation by horizon
    Some body text.
    Table 4. Ablation on daily proxies
    """
    captions = detect_page_captions(text)
    assert captions == [
        {
            "kind": "figure",
            "number": "2",
            "description": "Rank correlation by horizon",
        },
        {
            "kind": "table",
            "number": "4",
            "description": "Ablation on daily proxies",
        },
    ]


def test_caption_to_filename_stub() -> None:
    assert (
        caption_to_filename_stub("figure", "2", "Rank correlation by horizon")
        == "figure2_rank_correlation_by_horizon"
    )
    assert caption_to_filename_stub("table", "A1", "") == "tablea1"
