#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only guard against new production dependencies on legacy CommandStack."""
from __future__ import annotations

import argparse
import ast
import json
from dataclasses import asdict, dataclass
from pathlib import Path

DEFAULT_RUNTIME = Path(__file__).resolve().parents[1] / "FrameCore" / "plugins" / "lotucosm-vitaloom" / "versions" / "1.0.0" / "runtime"
DEFAULT_DEFINITION = Path("core/VitaLoom/commands/command.py")


@dataclass(frozen=True)
class Usage:
    path: str
    line: int
    column: int
    kind: str
    text: str


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _is_definition_file(path: Path, runtime_root: Path, definition_path: Path) -> bool:
    return path.resolve() == (runtime_root / definition_path).resolve()


def _is_test_path(path: Path) -> bool:
    return any(part.lower() in {"tests", "test"} for part in path.parts) or path.name.startswith("test_")


def _source_line(source: str, line: int) -> str:
    lines = source.splitlines()
    return lines[line - 1].strip() if 0 < line <= len(lines) else ""


def scan_file(path: Path, runtime_root: Path, definition_path: Path = DEFAULT_DEFINITION) -> list[Usage]:
    """Return semantic CommandStack references in one production Python file."""
    if _is_definition_file(path, runtime_root, definition_path) or _is_test_path(path):
        return []
    source = path.read_text(encoding="utf-8-sig")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as error:
        return [Usage(_relative(path, runtime_root), error.lineno or 0, error.offset or 0, "syntax_error", str(error))]

    usages: list[Usage] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == "CommandStack":
            kind = "instantiation" if isinstance(node.ctx, ast.Load) and any(
                isinstance(parent, ast.Call) and parent.func is node for parent in ast.walk(tree)
            ) else "reference"
            usages.append(Usage(_relative(path, runtime_root), node.lineno, node.col_offset, kind, _source_line(source, node.lineno)))
        elif isinstance(node, ast.Attribute) and node.attr == "CommandStack":
            usages.append(Usage(_relative(path, runtime_root), node.lineno, node.col_offset, "qualified_reference", _source_line(source, node.lineno)))
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == "CommandStack":
                    usages.append(Usage(_relative(path, runtime_root), node.lineno, node.col_offset, "import", _source_line(source, node.lineno)))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.rsplit(".", 1)[-1] == "CommandStack":
                    usages.append(Usage(_relative(path, runtime_root), node.lineno, node.col_offset, "import", _source_line(source, node.lineno)))
    return sorted(set(usages), key=lambda item: (item.path, item.line, item.column, item.kind))


def scan_runtime(runtime_root: Path, definition_path: Path = DEFAULT_DEFINITION) -> list[Usage]:
    """Scan production Python files under *runtime*, excluding tests and definition."""
    runtime_root = runtime_root.resolve()
    usages: list[Usage] = []
    for path in sorted(runtime_root.rglob("*.py")):
        usages.extend(scan_file(path, runtime_root, definition_path))
    return usages


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-root", type=Path, default=DEFAULT_RUNTIME)
    args = parser.parse_args()
    root = args.runtime_root.resolve()
    usages = scan_runtime(root)
    report = {"runtime_root": str(root), "legacy_definition_excluded": str((root / DEFAULT_DEFINITION).resolve()), "production_usages": [asdict(item) for item in usages], "status": "ok" if not usages else "violation"}
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not usages else 1


if __name__ == "__main__":
    raise SystemExit(main())

