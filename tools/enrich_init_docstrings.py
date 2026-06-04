# -*- coding: utf-8 -*-
"""将仅含「初始化」的 __init__ docstring 补为四段式（仅注释，跳过 tests）。"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {".cursor", ".git", "__pycache__", ".history", ".venv", "venv", "tests"}

INIT_DOC = '''"""构造并初始化实例。

        职责:
            建立本对象运行所需字段与子系统引用。

        时机:
            宿主创建对象时单次调用。

        不变量:
            子类须完整 super().__init__ 链。

        排错:
            属性缺失 → 查 super 与模块顶 docstring。
        """'''

PAT = re.compile(
    r"(def __init__\([^)]*\)\s*(?:->\s*[^:]+)?:\s*)"
    r'"""([^"]{0,200})"""',
    re.MULTILINE,
)


def main() -> None:
    n = 0
    for root_name in ("core", "builtin", "plugins", "projects", "tools"):
        root = ROOT / root_name
        if not root.is_dir():
            continue
        for path in root.rglob("*.py"):
            if any(s in path.parts for s in SKIP_PARTS) or ".bak_" in path.name:
                continue
            text = path.read_text(encoding="utf-8-sig")

            def repl(m: re.Match) -> str:
                body = m.group(2).strip()
                if "职责:" in body or "排错:" in body:
                    return m.group(0)
                if "初始化" not in body and len(body) > 60:
                    return m.group(0)
                return m.group(1) + INIT_DOC

            new, count = PAT.subn(repl, text)
            if count:
                path.write_text(new, encoding="utf-8")
                print(f"{path.as_posix()} ({count})")
                n += 1
    print("updated files:", n)


if __name__ == "__main__":
    main()
