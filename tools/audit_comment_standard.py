# -*- coding: utf-8 -*-
"""注释规范审计：统计缺模块 docstring 的 .py（报告用，不阻断 CI）。

职责: 扫描 FrameCore/、workspace/、tools/、tests/（可传根目录）。
用法: python tools/audit_comment_standard.py [path]

排错: 见 docs/comment_standard.md；金样 sr_membrane_topology.py。
"""
from __future__ import annotations

import ast
import sys
from collections import defaultdict
from pathlib import Path

SKIP_PARTS = {
    ".cursor",
    ".git",
    "__pycache__",
    "node_modules",
    ".history",
    ".venv",
    "venv",
    "dist",
    "build",
    "tools_legacy",
}
SKIP_SUFFIX = (".bak_",)


def module_docstring(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8-sig")
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return None
    doc = ast.get_docstring(tree)
    if doc:
        return doc.strip()
    lines = text.splitlines()
    if len(lines) >= 2 and "coding" in lines[0] and lines[1].strip().startswith('"""'):
        block = []
        for line in lines[1:]:
            block.append(line)
            if line.strip().endswith('"""') and line.strip().count('"""') >= 2:
                break
            if line.strip() == '"""':
                break
        raw = "\n".join(block).strip()
        if raw.startswith('"""') and raw.endswith('"""'):
            return raw[3:-3].strip()
    return None


def iter_py_files(root: Path):
    for p in root.rglob("*.py"):
        if any(part in SKIP_PARTS for part in p.parts):
            continue
        if any(s in p.name for s in SKIP_SUFFIX):
            continue
        yield p


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


def l3_public_method_stats(path: Path) -> tuple[int, int] | None:
    """返回 (公开方法总数, 缺四段式职责/排错数)。"""
    text = path.read_text(encoding="utf-8-sig")
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return None
    pmap = _parent_map(tree)
    total = 0
    missing = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for item in node.body:
            if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if _nested_in_function(item, pmap):
                continue
            if item.name.startswith("_") and item.name != "__init__":
                continue
            total += 1
            doc = ast.get_docstring(item) or ""
            if "职责:" not in doc or "排错:" not in doc:
                missing += 1
    return total, missing


def _bucket(rel: str) -> str:
    parts = rel.split("/")
    if len(parts) >= 2:
        return "/".join(parts[:2])
    return parts[0] if parts else rel


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parents[1]
    missing: list[str] = []
    short: list[str] = []
    l3_total = 0
    l3_missing = 0
    l3_syntax_errors: list[str] = []
    by_bucket: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for p in sorted(iter_py_files(root)):
        rel = p.relative_to(root).as_posix()
        doc = module_docstring(p)
        if not doc:
            missing.append(rel)
        elif len(doc) < 12 and "职责" not in doc:
            short.append(rel)
        if "tests" in p.parts:
            continue
        stats = l3_public_method_stats(p)
        if stats is None:
            l3_syntax_errors.append(rel)
            continue
        total, miss = stats
        l3_total += total
        l3_missing += miss
        if total:
            b = _bucket(rel)
            by_bucket[b][0] += total
            by_bucket[b][1] += miss
    print(f"# Comment audit: {root}\n")
    print(f"Missing module docstring: {len(missing)}")
    for r in missing[:80]:
        print(f"  - {r}")
    if len(missing) > 80:
        print(f"  ... and {len(missing) - 80} more")
    print(f"\nVery short / no 职责 keyword: {len(short)}")
    for r in short[:40]:
        print(f"  - {r}")
    print(f"\nL3 public methods (excl. tests): {l3_total}")
    print(f"L3 missing 职责/排错: {l3_missing}")
    if l3_total:
        pct = 100.0 * (l3_total - l3_missing) / l3_total
        print(f"L3 complete: {l3_total - l3_missing}/{l3_total} ({pct:.1f}%)")
    if l3_syntax_errors:
        print(f"\nL3 skipped (syntax error): {len(l3_syntax_errors)}")
        for r in l3_syntax_errors[:20]:
            print(f"  - {r}")
    if by_bucket:
        print("\nL3 by area (total / missing):")
        for b in sorted(by_bucket, key=lambda k: -by_bucket[k][1]):
            t, m = by_bucket[b]
            print(f"  {b}: {t - m}/{t} complete, {m} missing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
