from __future__ import annotations

import pandas as pd

from research.compute.masks import build_tradable_mask, load_universe_mask


def test_build_tradable_mask_filters_market_status_and_new_listing() -> None:
    dates = pd.to_datetime(["2024-01-02", "2024-03-15"])
    symbols = ["A", "B", "C", "D", "E", "F"]
    idx = pd.MultiIndex.from_product([dates, symbols], names=["datetime", "instrument"])
    market = pd.DataFrame(
        {
            "$close": 10.0,
            "$volume": 100.0,
            "$amount": 1000.0,
            "$limit_up": 11.0,
            "$limit_down": 9.0,
        },
        index=idx,
    )
    # First date is within the 60-day listing buffer for every symbol.
    # Second date isolates the other filters.
    market.loc[(dates[1], "B"), "$volume"] = 0
    market.loc[(dates[1], "C"), "$amount"] = 0
    market.loc[(dates[1], "D"), "$close"] = 11.0
    market.loc[(dates[1], "E"), "$close"] = 9.0

    status = pd.DataFrame(
        {"is_st": False, "is_suspended": False},
        index=idx,
    )
    status.loc[(dates[1], "F"), "is_st"] = True

    mask = build_tradable_mask(market, stock_status=status)

    assert not mask.loc[(dates[0], "A")]
    assert mask.loc[(dates[1], "A")]
    assert not mask.loc[(dates[1], "B")]
    assert not mask.loc[(dates[1], "C")]
    assert not mask.loc[(dates[1], "D")]
    assert not mask.loc[(dates[1], "E")]
    assert not mask.loc[(dates[1], "F")]


def test_load_universe_mask_reads_qlib_instrument_intervals(tmp_path) -> None:
    qlib_dir = tmp_path / "qlib"
    inst_dir = qlib_dir / "instruments"
    inst_dir.mkdir(parents=True)
    (inst_dir / "csi1000.txt").write_text(
        "\n".join(
            [
                "A\t2024-01-01\t2024-01-31",
                "B\t2024-02-01\t2024-02-29",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    idx = pd.MultiIndex.from_tuples(
        [
            (pd.Timestamp("2024-01-15"), "A"),
            (pd.Timestamp("2024-02-15"), "A"),
            (pd.Timestamp("2024-01-15"), "B"),
            (pd.Timestamp("2024-02-15"), "B"),
        ],
        names=["datetime", "instrument"],
    )

    mask = load_universe_mask("csi1000", idx, qlib_dir=qlib_dir)

    assert mask.tolist() == [True, False, False, True]

