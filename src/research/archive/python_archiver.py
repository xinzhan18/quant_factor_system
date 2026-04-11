"""Copy admitted Python candidates into ``storage/python_factors/``.

When a Python candidate (R8 escape hatch) is admitted, its source must
move out of the per-batch ``python_candidates/`` directory and into
``storage/python_factors/{factor_id}_{name}.py`` as the long-term
canonical copy. The batch dir stays immutable as an audit trail.

Operation is a copy (not a move) so the batch archive remains complete
for provenance. The python_factors target is atomic — we write to a
temp file and rename.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path


class PythonArchiveError(RuntimeError):
    """Raised when the archive source is missing or target already exists."""


def archive_python_factor(
    source_path: str | Path,
    python_factors_dir: str | Path,
    factor_id: str,
    name: str,
) -> Path:
    """Copy *source_path* to ``python_factors_dir/{factor_id}_{name}.py``.

    Parameters
    ----------
    source_path
        Path to the candidate file under ``batches/.../python_candidates/``.
    python_factors_dir
        Where admitted Python factors live long-term (e.g.
        ``storage/python_factors/``).
    factor_id
        The allocated ``F{id}`` string.
    name
        Sanitized factor name (letters / digits / underscores — caller
        is responsible for cleaning).

    Returns
    -------
    Path
        The destination path.

    Raises
    ------
    PythonArchiveError
        If the source is missing or the destination already exists.
    """
    src = Path(source_path)
    if not src.exists():
        raise PythonArchiveError(f"source missing: {src}")

    out_dir = Path(python_factors_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    dst = out_dir / f"{factor_id}_{name}.py"
    if dst.exists():
        raise PythonArchiveError(
            f"destination already exists: {dst} — factor_id collision"
        )

    # Atomic copy: shutil.copy2 into a temp, then rename
    tmp = dst.with_suffix(".py.tmp")
    try:
        shutil.copy2(src, tmp)
        os.replace(tmp, dst)
    except BaseException:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
        raise

    return dst
