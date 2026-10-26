# -*- coding: utf-8 -*-
"""Runtime 兼容 Adapter：project lock 的权威 Implementation 位于 FrameCore。

职责:
    保留历史 ``core.VitaLoom.suite.project_lock`` 导入 seam，避免产品 runtime、
    工具和第三方扩展一次性改名；所有解析与写入行为统一委托给 FrameCore。

排错:
    若导入失败，检查应用入口是否已将仓库根或导出包 ``runtime`` 加入
    ``PYTHONPATH``，并确认随包复制了 ``FrameCore/project_lock.py``。
"""
from FrameCore.project_lock import (
    CAPABILITY_PACKAGES,
    SUPPORTED_SR2D_BACKENDS,
    DEFAULT_PRODUCT_ID,
    DEFAULT_SUITE_ID,
    IMPLICIT_PACKAGES,
    ProjectRuntimeResolution,
    build_project_lock,
    build_project_lock_for_path,
    collect_required_capability_constraints,
    collect_required_package_ids,
    collect_runtime_backend_selection,
    ensure_project_lock,
    load_package_catalog,
    load_project_lock,
    parse_version_tuple,
    normalize_sr2d_backend_request,
    project_lock_schema_error,
    project_lock_path,
    resolve_project_runtime,
    select_product_version,
    version_matches_constraint,
    write_project_lock,
)

__all__ = [
    "CAPABILITY_PACKAGES",
    "SUPPORTED_SR2D_BACKENDS",
    "DEFAULT_PRODUCT_ID",
    "DEFAULT_SUITE_ID",
    "IMPLICIT_PACKAGES",
    "ProjectRuntimeResolution",
    "build_project_lock",
    "build_project_lock_for_path",
    "collect_required_capability_constraints",
    "collect_required_package_ids",
    "collect_runtime_backend_selection",
    "ensure_project_lock",
    "load_package_catalog",
    "load_project_lock",
    "parse_version_tuple",
    "normalize_sr2d_backend_request",
    "project_lock_schema_error",
    "project_lock_path",
    "resolve_project_runtime",
    "select_product_version",
    "version_matches_constraint",
    "write_project_lock",
]
