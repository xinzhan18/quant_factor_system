"""Qlib initialization and universe resolution.

Extracted from cli/commands/batch.py and cli/commands/probe.py to eliminate
the duplicated init-qlib-then-resolve-universe boilerplate.
"""

from __future__ import annotations


def init_qlib(qlib_dir: str = "~/.qlib/qlib_data/cn_data_1d") -> None:
    """Initialize Qlib.  Safe to call multiple times."""
    import qlib
    from qlib.config import REG_CN, C

    qlib.init(provider_uri=qlib_dir, region=REG_CN)
    C.kernels = 1


def resolve_full_universe() -> list:
    """Resolve the full stock universe from Qlib.

    Must be called after :func:`init_qlib`.
    """
    from qlib.data import D

    inst_dict = D.instruments("all")
    df_temp = D.features(
        instruments=inst_dict,
        fields=["$close"],
        start_time="2024-06-01",
        end_time="2024-06-30",
    )
    return df_temp.index.get_level_values("instrument").unique().tolist()
