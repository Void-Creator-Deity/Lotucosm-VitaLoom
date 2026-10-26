"""
包管理领域模型：manifest、依赖解析与约束策略；入口 models/resolver/policy。 排错: 见同目录 README 或 docs/lotucosm_core_troubleshooting.md。
"""

from .models import PackageManifest, PackageArtifact, PackageState, OperationRecord
from .resolver import resolve_dependency_graph
from .policy import ConstraintPolicy, should_block
from .catalog import (
    apply_version_overrides,
    collect_update_candidates,
    matches_status_filter,
    merge_package_lists,
    normalize_package,
    parse_dependency_expr,
    parse_version,
    select_target_updates,
    should_block_enable,
    version_gte,
)
from .project_operations import PackageProjectOperations

__all__ = [
    "PackageManifest",
    "PackageArtifact",
    "PackageState",
    "OperationRecord",
    "resolve_dependency_graph",
    "ConstraintPolicy",
    "should_block",
    "normalize_package",
    "merge_package_lists",
    "parse_version",
    "version_gte",
    "parse_dependency_expr",
    "should_block_enable",
    "collect_update_candidates",
    "select_target_updates",
    "matches_status_filter",
    "apply_version_overrides",
    "PackageProjectOperations",
]
