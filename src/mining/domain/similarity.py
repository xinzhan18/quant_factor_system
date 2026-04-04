"""Structural similarity and lookahead-bias detection for factor code."""

from __future__ import annotations


def compute_structural_similarity(code1: str, code2: str) -> float:
    """Jaccard similarity of ops call signatures between two Python factors."""
    from mining.expression import ExpressionValidator
    validator = ExpressionValidator()
    ops1 = set(validator.extract_ops_calls(code1))
    ops2 = set(validator.extract_ops_calls(code2))
    if not ops1 and not ops2:
        return 0.0
    if not ops1 or not ops2:
        return 0.0
    return len(ops1 & ops2) / len(ops1 | ops2)


def check_lookahead_bias(code: str) -> bool:
    """Static analysis for common lookahead patterns in Python factor code.

    Checks for the most frequent lookahead anti-pattern: calling .shift() with
    a negative argument, which would pull future data into the current row.

    Args:
        code: Python source code string to analyse.

    Returns:
        True if a potential lookahead pattern is detected, False otherwise.
        Also returns False when ``code`` cannot be parsed (syntax error).
    """
    import ast
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False

    for node in ast.walk(tree):
        # shift with negative values: df['close'].shift(-5)
        if (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "shift"):
            for arg in node.args:
                if isinstance(arg, ast.UnaryOp) and isinstance(arg.op, ast.USub):
                    return True
                if (isinstance(arg, ast.Constant)
                        and isinstance(arg.value, (int, float))
                        and arg.value < 0):
                    return True
    return False
