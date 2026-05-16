"""Adapters between legacy manifests and Factor IR v1."""

from __future__ import annotations

from typing import Any

from research.ir.schema import DataLogic, FactorIR, FactorLogic, LabelSpec
from research.ir.validator import validate_many

PASS_THROUGH_KEYS: frozenset[str] = frozenset(
    {
        "rationale",
        "parent_batch",
        "parent_candidate_id",
        "transformation",
        "hypothesis",
        "expected_sign",
    }
)


def normalize_candidate(candidate: dict[str, Any]) -> FactorIR:
    """Normalize a legacy or IR-shaped candidate into :class:`FactorIR`."""
    if candidate.get("ir_version") or candidate.get("factor_logic"):
        return _from_ir_candidate(candidate)
    return _from_legacy_candidate(candidate)


def normalize_manifest(
    manifest: dict[str, Any],
    *,
    validate: bool = True,
) -> dict[str, Any]:
    """Return a manifest copy with normalized legacy-compatible candidates.

    Phase2 still consumes legacy candidate fields in P1.  This adapter makes
    backend intent explicit by adding ``ir_version`` / ``factor_logic`` /
    ``data_logic`` while preserving ``source_type`` + ``expression`` / ``path``.
    """
    out = dict(manifest)
    irs = [normalize_candidate(c) for c in manifest.get("candidates", []) or []]
    if validate:
        validate_many(irs)
    out["candidates"] = [to_execution_candidate(ir) for ir in irs]
    out["factor_ir"] = [ir.to_dict() for ir in irs]
    out["ir_version"] = "v1"
    return out


def to_execution_candidate(ir: FactorIR) -> dict[str, Any]:
    """Convert normalized IR to the legacy candidate shape Phase2 can run."""
    logic = ir.factor_logic
    entry: dict[str, Any] = {
        "candidate_id": ir.candidate_id,
        "ir_version": ir.ir_version,
        "factor_logic": logic.to_dict(),
        "data_logic": ir.data_logic.to_dict(),
        "primitive_dependencies": list(ir.data_logic.primitive_dependencies),
    }
    if logic.backend == "qlib":
        entry["source_type"] = "dsl"
        entry["expression"] = logic.expression
    elif logic.backend == "python":
        entry["source_type"] = "python"
        entry["path"] = logic.path
    else:
        # DailyPythonBackend lands in P3.  Keep the task explicit and let
        # execution fail early if someone tries to run it before P3.
        entry["source_type"] = "daily_python"
        entry["template"] = logic.template
        entry["params"] = dict(logic.params)

    if ir.hypothesis:
        entry["hypothesis"] = ir.hypothesis
    if ir.expected_sign:
        entry["expected_sign"] = ir.expected_sign
    if ir.canonical:
        entry["canonical"] = ir.canonical
    label = ir.label.to_dict()
    if label:
        entry["label"] = label
    for key, value in ir.metadata.items():
        if key not in entry and value is not None:
            entry[key] = value
    return entry


def _from_ir_candidate(candidate: dict[str, Any]) -> FactorIR:
    logic = FactorLogic.from_dict(candidate.get("factor_logic") or {})
    data_logic = DataLogic.from_dict(candidate.get("data_logic") or {})
    if not data_logic.primitive_dependencies:
        data_logic = DataLogic(
            primitive_dependencies=_dedupe_strings(
                candidate.get("primitive_dependencies") or []
            ),
            daily_fields=data_logic.daily_fields,
        )
    return FactorIR(
        candidate_id=str(candidate.get("candidate_id") or ""),
        ir_version=str(candidate.get("ir_version") or "v1"),
        data_logic=data_logic,
        factor_logic=logic,
        hypothesis=candidate.get("hypothesis") or candidate.get("rationale"),
        expected_sign=candidate.get("expected_sign"),
        label=LabelSpec.from_dict(candidate.get("label") or {}),
        legacy_source_type=candidate.get("source_type"),
        canonical=candidate.get("canonical"),
        metadata=_metadata(candidate),
    )


def _from_legacy_candidate(candidate: dict[str, Any]) -> FactorIR:
    source_type = str(candidate.get("source_type") or "dsl")
    if source_type == "dsl":
        logic = FactorLogic(
            backend="qlib",
            expression=candidate.get("expression"),
        )
    elif source_type == "python":
        logic = FactorLogic(
            backend="python",
            path=candidate.get("path") or candidate.get("python_ref"),
        )
    else:
        logic = FactorLogic(backend=source_type)

    return FactorIR(
        candidate_id=str(candidate.get("candidate_id") or ""),
        ir_version="v1",
        data_logic=DataLogic(
            primitive_dependencies=_dedupe_strings(
                candidate.get("primitive_dependencies") or []
            )
        ),
        factor_logic=logic,
        hypothesis=candidate.get("hypothesis") or candidate.get("rationale"),
        expected_sign=candidate.get("expected_sign"),
        label=LabelSpec.from_dict(candidate.get("label") or {}),
        legacy_source_type=source_type,
        canonical=candidate.get("canonical"),
        metadata=_metadata(candidate),
    )


def _metadata(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        key: candidate[key]
        for key in PASS_THROUGH_KEYS
        if key in candidate and candidate[key] is not None
    }


def _dedupe_strings(values: list[Any]) -> list[str]:
    out: list[str] = []
    for value in values:
        if value is None:
            continue
        text = str(value)
        if text and text not in out:
            out.append(text)
    return out
