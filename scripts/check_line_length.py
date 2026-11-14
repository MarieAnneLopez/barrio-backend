"""Regla del proyecto: ningún archivo de código supera 100 líneas.

Uso: python scripts/check_line_length.py [directorio ...]
Sin argumentos revisa la raíz del repo. Sale con 1 si hay infractores.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Iterator
from pathlib import Path

MAX_LINES = 100
CODE_EXTENSIONS = {".ts", ".tsx", ".js", ".mjs", ".py", ".css"}
EXCLUDED_DIRS = {
    "node_modules", "dist", ".venv", "venv", ".git", "__pycache__", "coverage",
}
REPO_ROOT = Path(__file__).resolve().parent.parent


def count_lines(text: str) -> int:
    """Cuenta líneas como un editor: el salto final no abre una línea nueva."""
    if not text:
        return 0
    breaks = text.count("\n")
    return breaks if text.endswith("\n") else breaks + 1


def is_excluded(path: Path) -> bool:
    parts = path.parts
    if any(part in EXCLUDED_DIRS for part in parts):
        return True
    return any(
        part == "alembic" and parts[i + 1 : i + 2] == ("versions",)
        for i, part in enumerate(parts)
    )


def walk(root: Path) -> Iterator[Path]:
    for current, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if not is_excluded(Path(current, d))]
        for name in files:
            path = Path(current, name)
            if path.suffix.lower() in CODE_EXTENSIONS and not is_excluded(path):
                yield path


def main(args: list[str]) -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    roots = [Path(a).resolve() for a in args] or [REPO_ROOT]
    checked = 0
    offenders: list[tuple[Path, int]] = []
    for root in roots:
        for path in walk(root):
            checked += 1
            text = path.read_text(encoding="utf-8")
            lines = count_lines(text)
            if lines > MAX_LINES:
                offenders.append((path, lines))
    for path, lines in offenders:
        shown = path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path
        print(f"  {shown}: {lines} líneas (máximo {MAX_LINES})", file=sys.stderr)
    if offenders:
        print(
            f"check_line_length: {len(offenders)} de {checked} archivos "
            f"superan {MAX_LINES} líneas.",
            file=sys.stderr,
        )
        return 1
    print(
        f"check_line_length: OK, {checked} archivos de código, "
        f"todos <= {MAX_LINES} líneas."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
