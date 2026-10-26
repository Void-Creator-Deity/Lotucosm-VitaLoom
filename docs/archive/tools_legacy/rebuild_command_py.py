#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从损坏的 command.py 按 class 切块并重排缩进。"""
from __future__ import annotations

import py_compile
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def normalize_chunk(chunk: str) -> str:
    lines = [ln.rstrip() for ln in chunk.splitlines() if ln.strip()]
    if not lines:
        return ""
    indents = [len(ln) - len(ln.lstrip()) for ln in lines]
    base = min(indents)
    out: list[str] = []
    for ln in lines:
        n = len(ln) - len(ln.lstrip())
        out.append(" " * (n - base) + ln.lstrip())
    return "\n".join(out)


def repair_command(text: str) -> str:
    # 保留模块头（第一个 class 之前）
    m = re.search(r"^(class \w+)", text, re.MULTILINE)
    if not m:
        return text
    head = text[: m.start()].strip()
    rest = text[m.start() :]
    parts = re.split(r"(?=^class \w+)", rest, flags=re.MULTILINE)
    blocks = [normalize_chunk(p) for p in parts if p.strip()]
    return head + "\n\n\n" + "\n\n\n".join(blocks) + "\n"


def main() -> int:
    path = ROOT / "core/VitaLoom/commands/command.py"
    fixed = repair_command(path.read_text(encoding="utf-8-sig"))
    # 多轮 colon body 修复
    from fix_colon_block_indent import _strip_blanks, fix_colon_bodies

    lines = _strip_blanks(fixed.splitlines())
    for _ in range(12):
        lines = fix_colon_bodies(lines)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    py_compile.compile(str(path), doraise=True)
    print("ok", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
