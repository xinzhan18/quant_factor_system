"""Pre-Phase2 bridge for materialized daily primitives."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from data.exporters import QlibDailyFeatureExporter
from data.materializers import MinuteMaterializer
from data.primitive import PrimitiveCache, PrimitiveRegistry, PrimitiveSpec
from research.storage.paths import StoragePaths

logger = logging.getLogger(__name__)

MinuteDataLoader = Callable[[str, str, list[str]], pd.DataFrame]


def collect_primitive_dependencies(manifest: dict[str, Any]) -> list[str]:
    deps: list[str] = []
    for cand in manifest.get("candidates", []) or []:
        for fid in cand.get("primitive_dependencies", []) or []:
            if fid not in deps:
                deps.append(str(fid))
    return deps


def load_manifest_primitive_specs(
    manifest: dict[str, Any],
    registry: PrimitiveRegistry,
) -> dict[str, PrimitiveSpec]:
    """Resolve registry specs plus optional batch-local proposed primitives."""
    specs = registry.load_all()
    proposed = manifest.get("proposed_primitives", []) or []
    for item in proposed:
        spec = PrimitiveSpec.from_dict(dict(item))
        if spec.feature_id in specs and specs[spec.feature_id].spec_hash != spec.spec_hash:
            raise ValueError(
                f"proposed primitive conflicts with registry spec: {spec.feature_id}"
            )
        specs[spec.feature_id] = spec
    return specs


def ensure_primitives_materialized(
    manifest: dict[str, Any],
    paths: StoragePaths,
    config: dict[str, Any],
    start: str,
    end: str,
    minute_loader: MinuteDataLoader | None = None,
) -> dict[str, Any]:
    """Ensure all manifest primitive dependencies are cached and exported.

    This is intentionally a no-op when the manifest has no
    ``primitive_dependencies`` so existing daily-only batches keep the same path.
    """
    feature_ids = collect_primitive_dependencies(manifest)
    if not feature_ids:
        return {"features": {}, "status": "no_dependencies"}

    registry = PrimitiveRegistry(paths.minute_primitive_registry_dir)
    all_specs = load_manifest_primitive_specs(manifest, registry)
    missing_specs = [fid for fid in feature_ids if fid not in all_specs]
    if missing_specs:
        raise FileNotFoundError(
            f"primitive specs missing from registry/proposed_primitives: {missing_specs}"
        )
    specs = [all_specs[fid] for fid in feature_ids]
    cache = PrimitiveCache(paths.minute_primitive_store_dir)

    cached: dict[str, pd.DataFrame] = {}
    missing: list[PrimitiveSpec] = []
    status: dict[str, dict[str, Any]] = {}
    for spec in specs:
        hit = cache.get(spec, start=start, end=end)
        if hit is not None:
            cached[spec.feature_id] = hit
            status[spec.feature_id] = {
                "status": "cache_hit",
                "spec_hash": spec.spec_hash,
                "source_freq": spec.source_freq,
                "available_time": spec.time_semantics.get("available_time"),
            }
        else:
            missing.append(spec)

    materialized: dict[str, pd.DataFrame] = {}
    if missing:
        if minute_loader is None:
            minute_loader = _loader_from_config(config)
        if minute_loader is None:
            raise RuntimeError(
                "primitive cache miss and no minute_loader configured; "
                f"missing={ [s.feature_id for s in missing] }"
            )
        panel = MinuteMaterializer(minute_loader).materialize_many(missing, start, end)
        for spec in missing:
            cache.put(spec, panel[[spec.feature_id]])
            materialized[spec.feature_id] = panel[[spec.feature_id]]
            status[spec.feature_id] = {
                "status": "materialized",
                "spec_hash": spec.spec_hash,
                "source_freq": spec.source_freq,
                "available_time": spec.time_semantics.get("available_time"),
                "rows": int(panel[spec.feature_id].notna().sum()),
            }

    panels = list(cached.values()) + list(materialized.values())
    qlib_dir = _primitive_qlib_dir(config)
    if panels:
        export_panel = pd.concat(panels, axis=1).sort_index()
        if qlib_dir:
            QlibDailyFeatureExporter(qlib_dir).export_panel(export_panel)
            logger.info("exported primitive panel to Qlib daily dir: %s", qlib_dir)

    return {
        "status": "ok",
        "features": status,
        "qlib_data_dir": qlib_dir,
    }


def _loader_from_config(config: dict[str, Any]) -> MinuteDataLoader | None:
    primitive_cfg = config.get("primitive") or {}
    path = config.get("primitive_minute_parquet") or primitive_cfg.get("minute_parquet")
    if not path:
        return None
    root = Path(path).expanduser()

    def _load(start: str, end: str, columns: list[str]) -> pd.DataFrame:
        df = pd.read_parquet(root)
        cols = [c for c in columns if c in df.columns]
        df = df[cols].copy()
        df["time"] = pd.to_datetime(df["time"])
        dates = df["time"].dt.normalize()
        mask = (
            (dates >= pd.Timestamp(start).normalize())
            & (dates <= pd.Timestamp(end).normalize())
        )
        return df.loc[mask]

    return _load


def _primitive_qlib_dir(config: dict[str, Any]) -> str | None:
    primitive_cfg = config.get("primitive") or {}
    return (
        config.get("primitive_qlib_data_dir")
        or primitive_cfg.get("qlib_data_dir")
        or config.get("qlib_data_dir")
    )
