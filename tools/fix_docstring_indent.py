# -*- coding: utf-8 -*-
"""修复 enrich_public_methods 误插入的无缩进 docstring。

职责: 扫描无法 py_compile 的 .py，修正 def/class 与 docstring 之间的缩进。
时机: enrich_public_methods 之后必须运行。
不变量: 不修改已有正确缩进的 docstring。
排错: 仍失败 → 检查 docstring 是否插在参数列表中间（需手工修）。
"""
from __future__ import annotations

import py_compile
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_DEF_RE = re.compile(r"^\s*(async\s+def|def|class)\s+")


def _docstring_end(stripped: str) -> bool:
    if stripped == '"""':
        return True
    if stripped.startswith('"""') and stripped.count('"""') >= 2:
        return stripped.rstrip().endswith('"""')
    return False


def fix_lines(lines: list[str]) -> bool:
    changed = False
    i = 0
    while i < len(lines):
        line = lines[i]
        if not (line.rstrip().endswith(":") and _DEF_RE.match(line)):
            i += 1
            continue
        base = len(line) - len(line.lstrip())
        body_ind = " " * (base + 4)
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j >= len(lines):
            i += 1
            continue
        nxt = lines[j]
        stripped_nxt = nxt.lstrip()
        if not stripped_nxt.startswith('"""'):
            i += 1
            continue
        if nxt.startswith(body_ind):
            i += 1
            continue
        k = j
        while k < len(lines):
            raw = lines[k]
            stripped = raw.lstrip()
            if k == j and not stripped.startswith('"""'):
                break
            if not raw.startswith(body_ind):
                lines[k] = body_ind + stripped + ("\n" if raw.endswith("\n") else "")
                changed = True
            if _docstring_end(stripped):
                k += 1
                break
            k += 1
        i = k
    return changed


def main() -> None:
    n = 0
    for p in sorted(ROOT.rglob("*.py")):
        if any(x in p.parts for x in (".git", "__pycache__", ".history", ".venv", "tests")):
            continue
        try:
            py_compile.compile(str(p), doraise=True)
            continue
        except py_compile.PyCompileError:
            pass
        text = p.read_text(encoding="utf-8-sig")
        lines = text.splitlines(keepends=True)
        if fix_lines(lines):
            p.write_text("".join(lines), encoding="utf-8")
            try:
                py_compile.compile(str(p), doraise=True)
                print("fixed", p.relative_to(ROOT).as_posix())
                n += 1
            except py_compile.PyCompileError as e:
                print("still bad", p.relative_to(ROOT).as_posix(), e)
    print("ok", n)


if __name__ == "__main__":
    main()
