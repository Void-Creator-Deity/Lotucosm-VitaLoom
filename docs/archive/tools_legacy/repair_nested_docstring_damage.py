#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复 enrich + fix 连锁导致的整文件多缩进一层（如 command.py）。"""
from __future__ import annotations

import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def collapse_blank(lines: list[str]) -> list[str]:
    out: list[str] = []
    for ln in lines:
        if not ln.strip():
            if out and not out[-1].strip():
                continue
        out.append(ln.rstrip())
    return out


def repair_text(text: str) -> str:
    lines = collapse_blank(text.splitlines())
    changed = True
    while changed:
        changed = False
        new_lines: list[str] = []
        for ln in lines:
            orig = ln
            if ln.startswith("        class ") and not ln.startswith("            class "):
                ln = ln[8:]
                changed = True
            elif ln.startswith("        @abstractmethod"):
                ln = "    @abstractmethod"
                changed = True
            elif ln.startswith("        def ") and not ln.startswith("            def "):
                ln = "    " + ln.lstrip()
                changed = True
            elif ln.startswith("            ") and not ln.startswith("                "):
                # one dedent pass for 12-space blocks (method bodies after fix)
                stripped = ln.lstrip()
                if stripped.startswith(("def ", "class ", "@")):
                    ln = "        " + stripped
                else:
                    ln = "        " + stripped
                if ln != orig:
                    changed = True
            new_lines.append(ln)
        lines = new_lines
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    targets = [ROOT / p for p in argv[1:]] if len(argv) > 1 else [
        ROOT / "core/VitaLoom/commands/command.py",
        ROOT / "core/VitaLoom/tools/selection_tool.py",
        ROOT / "core/VitaLoom/ui/console.py",
        ROOT / "core/VitaLoom/viewports/world_viewport.py",
    ]
    for path in targets:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8-sig")
        fixed = repair_text(text)
        path.write_text(fixed, encoding="utf-8")
        try:
            py_compile.compile(str(path), doraise=True)
            print("ok", path.relative_to(ROOT).as_posix())
        except py_compile.PyCompileError as e:
            print("fail", path.relative_to(ROOT).as_posix(), e)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
