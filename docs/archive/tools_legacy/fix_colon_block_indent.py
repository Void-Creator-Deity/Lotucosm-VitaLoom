#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复 enrich/repair 后 if/for/return{{ 块体未缩进的问题。"""
from __future__ import annotations

import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_BLOCK_TAIL = (":",)
_SAME_LEVEL = ("elif ", "else:", "except ", "finally:", "elif:")


def _strip_blanks(lines: list[str]) -> list[str]:
    return [ln.rstrip() for ln in lines if ln.strip()]


def fix_colon_bodies(lines: list[str]) -> list[str]:
    result = list(lines)
    i = 0
    while i < len(result):
        line = result[i]
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#") or not line.rstrip().endswith(_BLOCK_TAIL):
            i += 1
            continue
        base = len(line) - len(line.lstrip())
        j = i + 1
        while j < len(result):
            ln = result[j]
            st = ln.lstrip()
            ind = len(ln) - len(ln.lstrip())
            if ind < base:
                break
            if ind == base:
                if st.startswith(_SAME_LEVEL):
                    break
                if st.startswith(("def ", "class ", "@")):
                    break
                result[j] = " " * (base + 4) + st
            j += 1
        i += 1
    return result


def repair_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8-sig")
    lines = _strip_blanks(text.splitlines())
    for _ in range(8):
        lines = fix_colon_bodies(lines)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        py_compile.compile(str(path), doraise=True)
        return True
    except py_compile.PyCompileError:
        return False


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        paths = [ROOT / p for p in argv[1:]]
    else:
        paths = sorted(ROOT.rglob("core/VitaLoom/**/*.py"))
    ok = 0
    for path in paths:
        if not path.is_file():
            continue
        try:
            py_compile.compile(str(path), doraise=True)
            continue
        except py_compile.PyCompileError:
            pass
        if repair_file(path):
            print("fixed", path.relative_to(ROOT).as_posix())
            ok += 1
        else:
            print("fail", path.relative_to(ROOT).as_posix())
    print("ok", ok)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
