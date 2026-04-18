"""Rewrite legacy ``[[../...]]`` wikilinks to vault-root form.

Audit check c14 (and c11 for C{id}.md) require every wikilink in
direction.md / C{id}.md to be vault-root (``[[batches/...]]`` rather than
``[[../batches/...]]``). Existing ``storage/vault/directions/*.md`` files
were written before the rule and use the relative form in their
``## Narrative Log`` entries.

This one-shot script walks ``storage/vault/directions/*.md`` and rewrites
``[[../batches/`` → ``[[batches/`` (and the same for factors / lessons).
Run once after deploying the new audit rule; delete afterwards.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Match ``[[../<subdir>/`` where subdir is one of the known vault top-level
# folders. Kept intentionally narrow so we don't rewrite anything else.
_KNOWN_SUBDIRS = ("batches", "factors", "lessons", "directions")
_PATTERN = re.compile(
    r"\[\[\.\./(" + "|".join(_KNOWN_SUBDIRS) + r")/"
)


def rewrite_file(path: Path, dry_run: bool) -> int:
    original = path.read_text(encoding="utf-8")
    new = _PATTERN.sub(r"[[\1/", original)
    if new == original:
        return 0
    if not dry_run:
        path.write_text(new, encoding="utf-8")
    n_changes = len(_PATTERN.findall(original))
    return n_changes


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "directions_dir",
        nargs="?",
        default="storage/vault/directions",
        help="Path to the directions folder (default: storage/vault/directions)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report changes but don't write files",
    )
    args = parser.parse_args(argv)

    root = Path(args.directions_dir)
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2

    total = 0
    files_touched = 0
    for md in sorted(root.glob("*.md")):
        n = rewrite_file(md, args.dry_run)
        if n:
            files_touched += 1
            total += n
            prefix = "would rewrite" if args.dry_run else "rewrote"
            print(f"{prefix} {n:3d} wikilinks in {md.name}")

    verb = "would rewrite" if args.dry_run else "rewrote"
    print(f"\n{verb} {total} wikilinks across {files_touched} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
