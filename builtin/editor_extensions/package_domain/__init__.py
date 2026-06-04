"""
包管理领域模型：manifest、依赖解析与约束策略；入口 models/resolver/policy。 排错: 见同目录 README 或 docs/lotucosm_core_troubleshooting.md。
"""

from .models import PackageManifest, PackageArtifact, PackageState, OperationRecord
from .resolver import resolve_dependency_graph
from .policy import ConstraintPolicy, should_block

__all__ = [
    "PackageManifest",
    "PackageArtifact",
    "PackageState",
    "OperationRecord",
    "resolve_dependency_graph",
    "ConstraintPolicy",
    "should_block",
]
