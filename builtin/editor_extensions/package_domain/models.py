"""
包 manifest 与操作记录 dataclass（package_manager 序列化用）。
排错: 见 docs/comment_standard.md、docs/lotucosm_core_troubleshooting.md 或子树 README。

"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class PackageArtifact:
    type: str = "file"
    path: str = ""
    url: str = ""
    sha256: str = ""


@dataclass
class PackageManifest:
    id: str
    display_name: str
    version: str
    category: str
    description: str
    source: str
    dependencies: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    plugins: List[str] = field(default_factory=list)
    artifact: PackageArtifact = field(default_factory=PackageArtifact)


@dataclass
class OperationRecord:
    action: str
    at: str
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class PackageState:
    overrides: Dict[str, str] = field(default_factory=dict)
    installed: Dict[str, Dict[str, str]] = field(default_factory=dict)
    history: List[Dict[str, str]] = field(default_factory=list)
    rollback_points: List[Dict[str, object]] = field(default_factory=list)

