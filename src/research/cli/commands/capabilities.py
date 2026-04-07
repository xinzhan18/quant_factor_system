"""CLI command: capabilities — print available operators, fields, and constraints.

Single source of truth: ``research.execute.precheck`` module constants.
"""

from __future__ import annotations

import argparse


def cmd_capabilities(args: argparse.Namespace) -> None:
    from research.execute.precheck import (
        DSL_OPERATOR_WHITELIST,
        DSL_FIELD_WHITELIST,
        UNAVAILABLE_OPERATORS,
        FORBIDDEN_FIELDS,
        MAX_EXPRESSION_DEPTH,
    )
    from research.compute.operators import _CUSTOM_OPS

    builtin_ops = sorted(DSL_OPERATOR_WHITELIST - set(_CUSTOM_OPS.keys()))
    custom_ops = sorted(_CUSTOM_OPS.keys())
    fields = sorted(DSL_FIELD_WHITELIST)
    forbidden = sorted(FORBIDDEN_FIELDS)
    unavailable = sorted(UNAVAILABLE_OPERATORS)

    print("=== DSL Operators (Qlib built-in) ===")
    print(", ".join(builtin_ops))

    print(f"\n=== DSL Operators (custom, {len(custom_ops)}) ===")
    print(", ".join(custom_ops))

    print(f"\n=== Unavailable Operators (not registered) ===")
    print(", ".join(unavailable))

    print(f"\n=== Base Fields ({len(fields)}) ===")
    print(", ".join(fields))

    print(f"\n=== Forbidden Fields ===")
    print(", ".join(forbidden))

    print(f"\n=== Constraints ===")
    print(f"  max_expression_depth: {MAX_EXPRESSION_DEPTH}")
