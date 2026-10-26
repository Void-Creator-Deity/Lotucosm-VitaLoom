"""Install the product runtime selected by this sample Project World's lock."""
from __future__ import annotations

import sys
from pathlib import Path


def install_locked_runtime() -> tuple[Path, Path]:
    project_root = Path(__file__).resolve().parents[1]
    repo_root = next(
        (
            parent
            for parent in project_root.parents
            if (parent / "FrameCore").is_dir() and (parent / "main.py").is_file()
        ),
        None,
    )
    if repo_root is None:
        raise RuntimeError("cannot locate VitaLoom repository root")

    repo_text = str(repo_root)
    if repo_text not in sys.path:
        sys.path.insert(0, repo_text)

    from FrameCore.lifecycle import FrameApi
    from FrameCore.product_registry import load_product_registry
    from FrameCore.project_lock import resolve_project_runtime
    from FrameCore.suite_registry import load_default_suite_manifest

    resolution = resolve_project_runtime(project_root, repo_root=repo_root)
    if resolution.has_blocking_issues:
        raise RuntimeError(resolution.blocking_issue_summary)

    suite = load_default_suite_manifest(repo_root)
    if suite.suite_root is None:
        raise RuntimeError("default product plugin manifest has no suite_root")
    version = load_product_registry(suite.suite_root).get_version(
        resolution.product_id,
        resolution.product_version,
    )
    if version is None:
        raise RuntimeError(
            f"missing locked product version: {resolution.product_id} "
            f"{resolution.product_version}"
        )

    FrameApi(app_root=repo_root, resource_root=repo_root, suite=suite).install_runtime_env(
        version
    )
    return repo_root, project_root
