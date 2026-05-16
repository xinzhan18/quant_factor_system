from __future__ import annotations

import pandas as pd

from data.primitive import PrimitiveCache, PrimitiveRegistry
from research.storage.yaml_io import save_yaml


def test_registry_resolves_specs_and_hash_is_stable(tmp_path):
    reg_dir = tmp_path / "registry"
    save_yaml(
        reg_dir / "open_10m_ret_v1.yaml",
        {
            "feature_id": "open_10m_ret_v1",
            "source_type": "minute_bar",
            "source_freq": "1min",
            "output_freq": "daily",
            "template": "window_return",
            "params": {"window": "09:30-09:40"},
            "status": "experimental",
        },
    )
    spec = PrimitiveRegistry(reg_dir).resolve_many(["open_10m_ret_v1"])[0]
    assert spec.feature_id == "open_10m_ret_v1"
    assert spec.spec_hash == PrimitiveRegistry(reg_dir).resolve_many(["open_10m_ret_v1"])[0].spec_hash


def test_cache_put_get_checks_date_coverage(tmp_path):
    spec = PrimitiveRegistry(tmp_path / "missing")
    del spec
    from data.primitive.schema import PrimitiveSpec

    primitive = PrimitiveSpec.from_dict(
        {
            "feature_id": "x_v1",
            "source_type": "minute_bar",
            "source_freq": "1min",
            "output_freq": "daily",
            "template": "window_return",
            "params": {"window": "09:30-09:40"},
        }
    )
    idx = pd.MultiIndex.from_tuples(
        [(pd.Timestamp("2024-01-02"), "SH600000")],
        names=["datetime", "instrument"],
    )
    values = pd.DataFrame({"x_v1": [0.01]}, index=idx)
    cache = PrimitiveCache(tmp_path / "cache")
    cache.put(primitive, values)

    assert cache.get(primitive, "2024-01-02", "2024-01-02") is not None
    assert cache.get(primitive, "2024-01-01", "2024-01-02") is None

