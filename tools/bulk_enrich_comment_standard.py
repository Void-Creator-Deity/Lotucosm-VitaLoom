# -*- coding: utf-8 -*-
"""批量为缺「职责/排错」的模块补 L0/L5 注释块（仅改 docstring，不改逻辑）。"""
from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIST = ROOT / "tools" / "_no_standard.txt"
SKIP_PARTS = {".cursor", ".git", "__pycache__", ".history", ".venv", "venv"}

TEST_SUFFIX = """
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。
"""

INIT_SUFFIX = " 排错: 见同目录 README 或 docs/lotucosm_core_troubleshooting.md。"

CODE_SUFFIX = """
排错: 见 docs/comment_standard.md、docs/lotucosm_core_troubleshooting.md 或子树 README。
"""


def read_doc(path: Path) -> tuple[str, int, int] | None:
    text = path.read_text(encoding="utf-8-sig")
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return None
    doc = ast.get_docstring(tree)
    if doc:
        return doc.strip(), 0, 0
    lines = text.splitlines()
    if len(lines) >= 2 and "coding" in lines[0] and lines[1].strip().startswith('"""'):
        start = 1
        end = start
        for i in range(start, len(lines)):
            if lines[i].strip().endswith('"""') and '"""' in lines[i].strip()[3:]:
                end = i
                break
            if lines[i].strip() == '"""':
                end = i
                break
        block = "\n".join(lines[start : end + 1])
        if block.startswith('"""') and block.endswith('"""'):
            return block[3:-3].strip(), start, end
    if lines and lines[0].strip().startswith('"""'):
        end = 0
        for i, line in enumerate(lines):
            if i > 0 and line.strip().endswith('"""'):
                end = i
                break
        block = "\n".join(lines[: end + 1])
        if block.count('"""') >= 2:
            return block[3 : block.rindex('"""')].strip(), 0, end
    return None


def replace_module_doc(path: Path, new_doc: str) -> bool:
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines(keepends=True)
    if lines and "coding" in lines[0] and len(lines) > 1 and '"""' in lines[1]:
        # coding + docstring block
        end = 1
        for i in range(1, len(lines)):
            stripped = lines[i].strip()
            if stripped.endswith('"""') and stripped.count('"""') >= 2:
                end = i
                break
            if stripped == '"""':
                end = i
                break
        new_block = '"""\n' + new_doc + '\n"""\n'
        new_lines = [lines[0]] + [new_block] + lines[end + 1 :]
        path.write_text("".join(new_lines), encoding="utf-8")
        return True
    if lines and lines[0].lstrip().startswith('"""'):
        end = 0
        for i, line in enumerate(lines):
            if i > 0 and '"""' in line:
                end = i
                if line.strip().endswith('"""'):
                    break
        new_block = '"""\n' + new_doc + '\n"""\n'
        path.write_text(new_block + "".join(lines[end + 1 :]), encoding="utf-8")
        return True
    # insert at top
    new_block = '"""\n' + new_doc + '\n"""\n\n'
    path.write_text(new_block + text, encoding="utf-8")
    return True


def enrich_doc(doc: str, suffix: str) -> str:
    if "职责:" in doc or "排错:" in doc:
        return doc
    doc = doc.rstrip()
    if suffix.strip() in doc:
        return doc
    return doc + suffix


def main() -> None:
    if not LIST.is_file():
        print("missing", LIST)
        return
    paths = [
        ROOT / line.strip()
        for line in LIST.read_text(encoding="utf-8").splitlines()
        if line.strip() and "tests/" not in line.replace("\\", "/")
    ]
    updated = 0
    for path in paths:
        if not path.is_file():
            continue
        info = read_doc(path)
        if info is None:
            base = path.stem.replace("test_", "")
            doc = f"{path.parent.name}/{path.name} 模块。"
            suffix = TEST_SUFFIX if "tests" in path.parts else CODE_SUFFIX
            new_doc = enrich_doc(doc, suffix)
            replace_module_doc(path, new_doc)
            updated += 1
            print("insert", path.as_posix())
            continue
        doc, _, _ = info
        if "tests" in path.parts or path.name.startswith("test_"):
            suffix = TEST_SUFFIX
        elif path.name == "__init__.py":
            suffix = INIT_SUFFIX
        else:
            suffix = CODE_SUFFIX
        new_doc = enrich_doc(doc, suffix)
        if new_doc == doc:
            continue
        replace_module_doc(path, new_doc)
        updated += 1
        print("update", path.as_posix())
    print("updated", updated)


if __name__ == "__main__":
    main()
