"""
包安装约束策略：warn / block / fail-fast 与 should_block 判定。
排错: 见 docs/comment_standard.md、docs/lotucosm_core_troubleshooting.md 或子树 README。

"""
from __future__ import annotations


ConstraintPolicy = str


def should_block(mode: ConstraintPolicy, issues_count: int) -> bool:
    text = str(mode or "warn").strip().lower()
    if text == "fail-fast":
        return issues_count > 0
    if text == "block":
        return issues_count > 0
    return False

