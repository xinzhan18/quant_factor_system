"""Schema helpers for daily primitives derived from higher-frequency data."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

import yaml


_HASH_EXCLUDE_TOP_LEVEL = {"status"}
_HASH_EXCLUDE_CACHE_KEYS = {"spec_hash"}


@dataclass(frozen=True)
class PrimitiveSpec:
    """Canonical definition of a materialized daily primitive."""

    feature_id: str
    source_type: str
    source_freq: str
    output_freq: str
    template: str
    params: dict[str, Any]
    time_semantics: dict[str, Any] = field(default_factory=dict)
    data_policy: dict[str, Any] = field(default_factory=dict)
    cache: dict[str, Any] = field(default_factory=dict)
    feature_type: str = "primitive"
    status: str = "experimental"
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PrimitiveSpec":
        required = [
            "feature_id",
            "source_type",
            "source_freq",
            "output_freq",
            "template",
            "params",
        ]
        missing = [k for k in required if not data.get(k)]
        if missing:
            raise ValueError(f"primitive spec missing required fields: {missing}")

        if data["output_freq"] != "daily":
            raise ValueError(
                f"{data['feature_id']}: only output_freq=daily is supported in V0"
            )
        if data["source_type"] != "minute_bar":
            raise ValueError(
                f"{data['feature_id']}: only source_type=minute_bar is supported in V0"
            )

        return cls(
            feature_id=str(data["feature_id"]),
            source_type=str(data["source_type"]),
            source_freq=str(data["source_freq"]),
            output_freq=str(data["output_freq"]),
            template=str(data["template"]),
            params=dict(data.get("params") or {}),
            time_semantics=dict(data.get("time_semantics") or {}),
            data_policy=dict(data.get("data_policy") or {}),
            cache=dict(data.get("cache") or {}),
            feature_type=str(data.get("feature_type", "primitive")),
            status=str(data.get("status", "experimental")),
            raw=dict(data),
        )

    def to_hash_payload(self) -> dict[str, Any]:
        payload = {
            k: v
            for k, v in self.raw.items()
            if k not in _HASH_EXCLUDE_TOP_LEVEL
        }
        cache = dict(payload.get("cache") or {})
        for k in _HASH_EXCLUDE_CACHE_KEYS:
            cache.pop(k, None)
        if cache:
            payload["cache"] = cache
        elif "cache" in payload:
            payload["cache"] = {}
        return payload

    @property
    def spec_hash(self) -> str:
        canonical = yaml.safe_dump(
            self.to_hash_payload(),
            allow_unicode=True,
            sort_keys=True,
            default_flow_style=False,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]

