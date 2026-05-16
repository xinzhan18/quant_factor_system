"""Small expression evaluator for controlled daily templates."""

from __future__ import annotations

import math
import re
from typing import Any

import numpy as np
import pandas as pd

_TOKEN_RE = re.compile(r"\s*([A-Za-z_][A-Za-z0-9_]*|\$[A-Za-z_][A-Za-z0-9_]*|-?\d+(?:\.\d+)?|[(),])\s*")
_FIELD_RE = re.compile(r"\$[A-Za-z_][A-Za-z0-9_]*")


class ExpressionError(ValueError):
    """Raised when a template expression cannot be evaluated."""


def extract_fields(obj: Any) -> list[str]:
    """Return unique ``$field`` references found in a nested object."""
    fields: list[str] = []

    def visit(value: Any) -> None:
        if isinstance(value, str):
            for field in _FIELD_RE.findall(value):
                if field not in fields:
                    fields.append(field)
        elif isinstance(value, dict):
            for v in value.values():
                visit(v)
        elif isinstance(value, list):
            for v in value:
                visit(v)

    visit(obj)
    return fields


def evaluate_expression(spec: Any, df: pd.DataFrame) -> pd.Series:
    """Evaluate a restricted expression spec against a daily panel.

    Supported shapes:

    * ``{"field": "$close"}``
    * ``{"expression": "Sub(Div($high,$low),1)"}``
    * direct string expressions, including ``"$close"``
    """
    expr = _resolve_expression_text(spec)
    tokens = _tokenize(expr)
    parser = _Parser(tokens, df)
    out = parser.parse()
    if parser.pos != len(tokens):
        raise ExpressionError(f"unexpected trailing tokens in expression: {expr}")
    if isinstance(out, pd.Series):
        return out.astype(float)
    return pd.Series(float(out), index=df.index, dtype=float)


def _resolve_expression_text(spec: Any) -> str:
    if isinstance(spec, dict):
        if spec.get("field"):
            return str(spec["field"])
        if spec.get("expression"):
            return str(spec["expression"])
    if isinstance(spec, str):
        return spec
    if isinstance(spec, (int, float)):
        return str(spec)
    raise ExpressionError(f"unsupported expression spec: {spec!r}")


def _tokenize(expr: str) -> list[str]:
    tokens: list[str] = []
    pos = 0
    while pos < len(expr):
        match = _TOKEN_RE.match(expr, pos)
        if match is None:
            raise ExpressionError(f"unsupported token near: {expr[pos:pos + 20]!r}")
        tokens.append(match.group(1))
        pos = match.end()
    return tokens


class _Parser:
    def __init__(self, tokens: list[str], df: pd.DataFrame) -> None:
        self.tokens = tokens
        self.df = df
        self.pos = 0

    def parse(self) -> pd.Series | float:
        if self.pos >= len(self.tokens):
            raise ExpressionError("empty expression")
        tok = self.tokens[self.pos]
        self.pos += 1
        if tok.startswith("$"):
            if tok not in self.df.columns:
                raise ExpressionError(f"missing field: {tok}")
            return self.df[tok]
        if _is_number(tok):
            return float(tok)
        if self.pos < len(self.tokens) and self.tokens[self.pos] == "(":
            self.pos += 1
            args: list[pd.Series | float] = []
            if self.pos < len(self.tokens) and self.tokens[self.pos] != ")":
                args.append(self.parse())
                while self.pos < len(self.tokens) and self.tokens[self.pos] == ",":
                    self.pos += 1
                    args.append(self.parse())
            if self.pos >= len(self.tokens) or self.tokens[self.pos] != ")":
                raise ExpressionError(f"unbalanced call for operator: {tok}")
            self.pos += 1
            return _apply_operator(tok, args)
        raise ExpressionError(f"unexpected token: {tok}")


def _apply_operator(op: str, args: list[pd.Series | float]) -> pd.Series | float:
    if op == "Add":
        _arity(op, args, 2)
        return args[0] + args[1]
    if op == "Sub":
        _arity(op, args, 2)
        return args[0] - args[1]
    if op == "Mul":
        _arity(op, args, 2)
        return args[0] * args[1]
    if op == "Div":
        _arity(op, args, 2)
        return args[0] / args[1]
    if op == "Abs":
        _arity(op, args, 1)
        return abs(args[0])
    if op == "Sign":
        _arity(op, args, 1)
        return np.sign(args[0])
    if op == "Log":
        _arity(op, args, 1)
        return np.log(args[0])
    if op == "Power":
        _arity(op, args, 2)
        return args[0] ** args[1]
    if op in {"Gt", "Greater"}:
        _arity(op, args, 2)
        return args[0] > args[1]
    if op == "Ge":
        _arity(op, args, 2)
        return args[0] >= args[1]
    if op in {"Lt", "Less"}:
        _arity(op, args, 2)
        return args[0] < args[1]
    if op == "Le":
        _arity(op, args, 2)
        return args[0] <= args[1]
    if op == "Eq":
        _arity(op, args, 2)
        return args[0] == args[1]
    if op == "Ne":
        _arity(op, args, 2)
        return args[0] != args[1]
    if op == "And":
        _arity(op, args, 2)
        return args[0].astype(bool) & args[1].astype(bool)
    if op == "Or":
        _arity(op, args, 2)
        return args[0].astype(bool) | args[1].astype(bool)
    if op == "Ref":
        _arity(op, args, 2)
        series = _series_arg(op, args[0])
        return series.groupby(level=-1).shift(int(args[1]))
    if op == "Mean":
        _arity(op, args, 2)
        series = _series_arg(op, args[0])
        return _rolling_by_instrument(series, int(args[1]), "mean")
    if op == "Std":
        _arity(op, args, 2)
        series = _series_arg(op, args[0])
        return _rolling_by_instrument(series, int(args[1]), "std")
    raise ExpressionError(f"unsupported operator: {op}")


def _rolling_by_instrument(series: pd.Series, window: int, fn: str) -> pd.Series:
    grouped = series.groupby(level=-1, group_keys=False)
    if fn == "mean":
        return grouped.rolling(window, min_periods=1).mean().droplevel(0)
    if fn == "std":
        return grouped.rolling(window, min_periods=2).std().droplevel(0)
    raise ExpressionError(f"unsupported rolling fn: {fn}")


def _series_arg(op: str, value: pd.Series | float) -> pd.Series:
    if not isinstance(value, pd.Series):
        raise ExpressionError(f"{op} first argument must be a Series")
    return value


def _arity(op: str, args: list[Any], n: int) -> None:
    if len(args) != n:
        raise ExpressionError(f"{op} expects {n} args, got {len(args)}")


def _is_number(tok: str) -> bool:
    try:
        value = float(tok)
    except ValueError:
        return False
    return math.isfinite(value)
