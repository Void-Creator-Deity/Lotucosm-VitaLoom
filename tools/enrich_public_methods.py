# -*- coding: utf-8 -*-
"""为缺四段式的公开 def 补 docstring（跳过嵌套函数、tests、@abstractmethod、def 后空行）。

用法: python tools/enrich_public_methods.py [subdir] [--dry-run]
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {".cursor", ".git", "__pycache__", ".history", ".venv", "venv", "tests"}


def _parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    m: dict[ast.AST, ast.AST] = {}
    for p in ast.walk(tree):
        for ch in ast.iter_child_nodes(p):
            m[ch] = p
    return m


def _nested_in_function(node: ast.AST, pmap: dict[ast.AST, ast.AST]) -> bool:
    cur: ast.AST | None = pmap.get(node)
    while cur is not None:
        if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return True
        cur = pmap.get(cur)
    return False


def _summary(existing: str | None, name: str, cls: str | None) -> str:
    if existing:
        first = existing.strip().split("\n")[0].strip().strip('"').strip("'")
        if first and "职责:" not in first and len(first) < 120:
            return first.rstrip("。") + "。"
    return f"{cls + '.' if cls else ''}{name}。"


def _body_indent(node: ast.FunctionDef | ast.AsyncFunctionDef, lines: list[str]) -> str:
    start = node.lineno  # 1-based
    if start < len(lines):
        def_ln = lines[start - 1]
        return def_ln[: len(def_ln) - len(def_ln.lstrip())] + "    "
    return "    "


def _has_decorator(node: ast.FunctionDef | ast.AsyncFunctionDef, name: str) -> bool:
    for dec in node.decorator_list:
        if isinstance(dec, ast.Name) and dec.id == name:
            return True
        if isinstance(dec, ast.Attribute) and dec.attr == name:
            return True
    return False


def _def_body_gap_before_docstring(
    node: ast.FunctionDef | ast.AsyncFunctionDef, lines: list[str]
) -> bool:
    """def 与 docstring/首条语句之间有空行时跳过（易破坏缩进）。"""
    start = node.lineno - 1
    end = (node.end_lineno or node.lineno) - 1
    i = start + 1
    while i <= end and lines[i].strip().startswith("@"):
        i += 1
    if i > end:
        return False
    if not lines[i].strip():
        return True
    if node.body and isinstance(node.body[0], ast.Expr) and isinstance(
        getattr(node.body[0], "value", None), ast.Constant
    ):
        ds_line = node.body[0].lineno - 1
        for j in range(i, ds_line):
            if j < len(lines) and not lines[j].strip():
                return True
    return False


def _doc_text(summary: str, indent: str) -> str:
    inner = indent + "    "
    return (
        f'"""{summary}\n\n'
        f"{inner}职责:\n"
        f"{inner}    执行本函数声明的对外行为（见实现）。\n\n"
        f"{inner}时机:\n"
        f"{inner}    由调用方在对应生命周期内调用。\n\n"
        f"{inner}不变量:\n"
        f"{inner}    不破坏模块顶 docstring 与同级契约。\n\n"
        f"{inner}排错:\n"
        f"{inner}    异常时见本文件模块说明与子树 README 排错表。\n"
        f'{indent}"""'
    )


def _iter_public_methods(tree: ast.Module) -> Iterable[tuple[ast.FunctionDef | ast.AsyncFunctionDef, str | None]]:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if item.name.startswith("_") and item.name != "__init__":
                        continue
                    yield item, node.name


def _line_range(lines: list[str], node: ast.AST) -> tuple[int, int]:
    start = node.lineno - 1
    end = (node.end_lineno or node.lineno) - 1
    return start, end


def _would_enrich(node: ast.FunctionDef | ast.AsyncFunctionDef, pmap, lines: list[str]) -> bool:
    if _nested_in_function(node, pmap):
        return False
    if _has_decorator(node, "abstractmethod") or _has_decorator(node, "property"):
        return False
    if _def_body_gap_before_docstring(node, lines):
        return False
    old = ast.get_docstring(node) or ""
    return "职责:" not in old and "排错:" not in old


def count_candidates(path: Path) -> int:
    text = path.read_text(encoding="utf-8-sig")
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return 0
    pmap = _parent_map(tree)
    lines = text.splitlines(keepends=True)
    return sum(1 for node, _cls in _iter_public_methods(tree) if _would_enrich(node, pmap, lines))


def process_file(path: Path) -> int:
    text = path.read_text(encoding="utf-8-sig")
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return 0
    pmap = _parent_map(tree)
    lines = text.splitlines(keepends=True)
    edits: list[tuple[int, int, list[str]]] = []

    for node, cls in _iter_public_methods(tree):
        if not _would_enrich(node, pmap, lines):
            continue
        old = ast.get_docstring(node) or ""
        indent = _body_indent(node, lines)
        new_block = _doc_text(_summary(old, node.name, cls), indent) + "\n"
        new_lines = [ln + "\n" for ln in new_block.split("\n")]
        if new_lines and new_lines[-1] == "\n":
            new_lines.pop()

        start, end = _line_range(lines, node)
        insert_at = start + 1
        # skip decorators
        while insert_at <= end and lines[insert_at].strip().startswith("@"):
            insert_at += 1

        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(
            getattr(node.body[0], "value", None), ast.Constant
        ) and isinstance(node.body[0].value.value, str):
            ds = node.body[0]
            d0 = ds.lineno - 1
            d1 = (ds.end_lineno or ds.lineno) - 1
            edits.append((d0, d1 + 1, new_lines))
        else:
            edits.append((insert_at, insert_at, new_lines))
        count_placeholder = 1

    if not edits:
        return 0
    edits.sort(key=lambda x: x[0], reverse=True)
    for a, b, rep in edits:
        lines[a:b] = rep
    path.write_text("".join(lines), encoding="utf-8")
    return len(edits)


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if a != "--dry-run"]
    dry_run = "--dry-run" in argv[1:]
    if args:
        roots = [ROOT / args[0]]
    else:
        roots = [
            ROOT / "core" / "Lotucosm",
            ROOT / "core" / "api",
            ROOT / "core" / "plugin",
            ROOT / "core" / "VitaLoom" / "kernel",
            ROOT / "core" / "VitaLoom" / "scene",
            ROOT / "core" / "VitaLoom" / "simulation",
            ROOT / "core" / "VitaLoom" / "project",
            ROOT / "builtin" / "systems",
            ROOT / "builtin" / "components",
            ROOT / "builtin" / "entity_types",
            ROOT / "projects" / "pvaec-细胞演化" / "scripts",
        ]
    total = 0
    for root in roots:
        if not root.exists():
            continue
        for p in sorted(root.rglob("*.py")):
            if any(s in p.parts for s in SKIP_PARTS) or ".bak_" in p.name:
                continue
            if dry_run:
                n = count_candidates(p)
            else:
                n = process_file(p)
            if n:
                print(f"{p.relative_to(ROOT).as_posix()} +{n}")
                total += n
    print("total", total)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
