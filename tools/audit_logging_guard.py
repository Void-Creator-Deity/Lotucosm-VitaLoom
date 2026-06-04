#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""轻量审计：扫描 traceback.print_exc 等日志/异常反模式。

职责: 按 PATTERNS 正则扫 .py，输出违规路径（CI 可选）。
时机: 本地或 CI 手动运行；与 audit_comment_standard.py 互补。
排错: 见 docs/logging_convention.md。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable, List, Tuple


Pattern = Tuple[str, re.Pattern[str], str]


PATTERNS: List[Pattern] = [
    (
        "traceback_print_exc",
        re.compile(r"traceback\.print_exc\s*\("),
        "检测到 traceback.print_exc()，建议改为 logger.exception(...)",
    ),
    (
        "bare_except_pass",
        re.compile(r"except\s*:\s*\n\s*pass\b", re.MULTILINE),
        "检测到 except: pass，禁止静默吞异常",
    ),
    (
        "except_exception_pass",
        re.compile(r"except\s+Exception\s*:\s*\n\s*pass\b", re.MULTILINE),
        "检测到 except Exception: pass，建议至少记录 warning",
    ),
    (
        "logger_fstring",
        re.compile(
            r"(?:^|[^A-Za-z0-9_])(?:logger|self\.logger)\."
            r"(?:debug|info|warning|error|exception|critical)\s*\(\s*f[\"']"
        ),
        "检测到 logger f-string，建议使用参数化日志占位符",
    ),
]

DEFAULT_EXCLUDES = {
    ".git",
    ".history",
    "__pycache__",
    ".cursor",
    ".trae",
    "mcps",
}


def iter_py_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.py"):
        if any(part in DEFAULT_EXCLUDES for part in path.parts):
            continue
        yield path


def line_no_from_offset(content: str, offset: int) -> int:
    return content.count("\n", 0, offset) + 1


def _is_i18n_t_fallback(content: str, offset: int) -> bool:
    """允许 _t() 翻译回退中的静默容错。"""
    window_start = max(0, offset - 400)
    context = content[window_start:offset]
    return (
        "def _t(" in context
        and "tr_fn = getattr" in context
        and "return tr_fn(" in context
    )


def scan_file(path: Path) -> List[Tuple[str, int, str]]:
    issues: List[Tuple[str, int, str]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="ignore")

    for name, pattern, message in PATTERNS:
        for match in pattern.finditer(text):
            if name in {"bare_except_pass", "except_exception_pass"} and _is_i18n_t_fallback(
                text, match.start()
            ):
                continue
            line_no = line_no_from_offset(text, match.start())
            issues.append((message, line_no, match.group(0).strip()))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="审计日志与异常处理回退模式")
    parser.add_argument(
        "--root",
        default="core",
        help="扫描根目录（默认: core）",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"[audit] root 不存在: {root}")
        return 2

    all_issues: List[Tuple[Path, str, int, str]] = []
    for py_file in iter_py_files(root):
        for msg, line_no, snippet in scan_file(py_file):
            all_issues.append((py_file, msg, line_no, snippet))

    if not all_issues:
        print("[audit] 通过：未发现日志/异常处理回退模式")
        return 0

    print(f"[audit] 发现 {len(all_issues)} 个问题:")
    for file_path, msg, line_no, snippet in all_issues:
        rel = file_path.relative_to(Path.cwd()) if file_path.is_relative_to(Path.cwd()) else file_path
        print(f"- {rel}:{line_no} | {msg}")
        print(f"  -> {snippet}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
