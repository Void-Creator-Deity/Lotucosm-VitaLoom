#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate product, plugin, workspace, CI, and release metadata consistency."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITE_ROOT = ROOT / "FrameCore" / "plugins" / "lotucosm-vitaloom"
VERSION_ROOT = (
    SUITE_ROOT / "versions" / "1.0.0"
)
RUNTIME_ROOT = VERSION_ROOT / "runtime"
CATALOG_PATH = RUNTIME_ROOT / "builtin" / "package_index.json"
for _path in (ROOT, RUNTIME_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
TEXT_SUFFIXES = {
    "",
    ".bat",
    ".cfg",
    ".ini",
    ".json",
    ".md",
    ".py",
    ".spec",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
SKIP_DIRS = {
    ".git",
    ".history",
    ".mypy_cache",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "ai_organism_based_on_inheritance_algorithm.egg-info",
    "build",
    "dist",
    "logs",
}
SKIP_REL_PREFIXES = {
    ("docs", "archive"),
}
FORBIDDEN_REPOSITORY_REFERENCES = (
    "lotucosm-vitaloom-suite",
    "products/lotucosm-vitaloom/versions",
    "products\\lotucosm-vitaloom\\versions",
    "projects/pvaec-",
    "projects\\pvaec-",
    "projects/织机教程",
    "projects\\织机教程",
    "python -m compileall -q FrameCore plugins projects tools main.py player.py",
    "`core/Lotucosm`, `core/VitaLoom`, or `builtin` still exists at repository root",
    "only the first-round manifest compatibility layer remains",
    "第一轮不搬迁",
    "未来迁移",
    "Iteration 7",
    "VitaLoom.exe",
    "data/system",
    "data\\system",
    "data/experiments",
    "data\\experiments",
    "data/experiment_runs",
    "data\\experiment_runs",
    "ARCHITECTURE_DIAGRAM",
    "package_operation_lifecycle",
    "builtin/packages/README",
    "D:\\文件仓库",
    "C:\\Users\\",
)


def _canonical_json(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _read_pyproject_version() -> str:
    path = ROOT / "pyproject.toml"
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
    return m.group(1).strip() if m else ""


def _read_pyproject_requires_python() -> str:
    path = ROOT / "pyproject.toml"
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8")
    m = re.search(r'^requires-python\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
    return m.group(1).strip() if m else ""


def _entry_file_exists(root: Path, command: str) -> bool:
    entry = str(command or "").strip()
    if not entry:
        return False
    script = entry.split(" ", 1)[0]
    return (root / script).exists() or (VERSION_ROOT / script).exists()


def _check_no_tracked_local_history(errors: list[str]) -> None:
    """Reject local IDE/AI history snapshots from the release repository."""
    try:
        proc = subprocess.run(
            ["git", "ls-files", ".history"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return
    if proc.returncode != 0:
        return
    tracked_existing = [
        line.strip()
        for line in proc.stdout.splitlines()
        if line.strip() and (ROOT / line.strip()).exists()
    ]
    if tracked_existing:
        preview = ", ".join(tracked_existing[:5])
        extra = (
            ""
            if len(tracked_existing) <= 5
            else f" ... (+{len(tracked_existing) - 5})"
        )
        errors.append(f"tracked local history snapshots found: {preview}{extra}")


def _discover_plugin_class_names() -> set[str]:
    names: set[str] = set()
    plugin_roots = (
        RUNTIME_ROOT / "builtin" / "editor_extensions",
        ROOT / "workspace" / "extensions" / "user",
        ROOT / "workspace" / "extensions" / "community",
    )
    class_re = re.compile(r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*Plugin)\b")
    for root in plugin_roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*_plugin.py"):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for line in text.splitlines():
                m = class_re.match(line)
                if m:
                    names.add(m.group(1))
    return names


def _check_sample_project_locks(errors: list[str]) -> None:
    from tools.update_project_lock import build_expected_lock

    samples_root = ROOT / "workspace" / "projects" / "samples"
    if not samples_root.is_dir():
        errors.append("missing workspace/projects/samples")
        return
    found_project = False
    for project in sorted(samples_root.iterdir()):
        if not project.is_dir() or not (project / "project.json").is_file():
            continue
        found_project = True
        lock_path = project / "project.lock.json"
        if not lock_path.is_file():
            errors.append(f"sample project missing lock: {project.name}")
            continue
        try:
            expected = build_expected_lock(project, ROOT)
            current = json.loads(lock_path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"sample project lock invalid: {project.name}: {exc}")
            continue
        if _canonical_json(current) != _canonical_json(expected):
            errors.append(
                f"sample project lock stale: {project.name} "
                f"(run python tools/update_project_lock.py {project} --write)"
            )
    if not found_project:
        errors.append("workspace/projects/samples contains no project.json")


def _check_forbidden_repository_references(errors: list[str]) -> None:
    self_path = Path(__file__).resolve()
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        try:
            parts = path.relative_to(ROOT).parts
        except ValueError:
            continue
        if any(
            part in SKIP_DIRS
            or part.startswith(".venv-")
            or part.startswith(".pytest-")
            for part in parts
        ):
            continue
        if any(tuple(parts[: len(prefix)]) == prefix for prefix in SKIP_REL_PREFIXES):
            continue
        if path.resolve() == self_path:
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pattern in FORBIDDEN_REPOSITORY_REFERENCES:
            if pattern in text:
                rel = path.relative_to(ROOT).as_posix()
                errors.append(f"forbidden repository reference {pattern!r} in {rel}")
                break


def _check_plugin_layout(errors: list[str]) -> None:
    """Allow application extensions only in user/community extension roots."""
    legacy_plugins_root = ROOT / "plugins"
    if legacy_plugins_root.exists():
        errors.append("legacy root plugins/ directory found; use workspace/extensions/")
    legacy_app_extensions_root = ROOT / "app_extensions"
    if legacy_app_extensions_root.exists():
        errors.append("legacy root app_extensions/ directory found; use workspace/extensions/")
    plugins_root = ROOT / "workspace" / "extensions"
    if not plugins_root.is_dir():
        return
    allowed_dirs = {"user", "community", "__pycache__"}
    for child in sorted(plugins_root.iterdir()):
        if child.is_dir() and child.name not in allowed_dirs:
            errors.append(
                "legacy flat app extension directory found: "
                f"{child.relative_to(ROOT).as_posix()} "
                "(move it under workspace/extensions/user or workspace/extensions/community)"
            )


def _check_project_layout(errors: list[str]) -> None:
    """Allow project worlds only in sample/user project roots."""
    legacy_projects_root = ROOT / "projects"
    if legacy_projects_root.exists():
        errors.append("legacy root projects/ directory found; use workspace/projects/")
    projects_root = ROOT / "workspace" / "projects"
    if not projects_root.is_dir():
        errors.append("missing workspace/projects")
        return
    allowed_dirs = {"samples", "user", "__pycache__"}
    allowed_files = {"README.md"}
    for child in sorted(projects_root.iterdir()):
        if child.is_dir() and child.name not in allowed_dirs:
            errors.append(
                "legacy flat project directory found: "
                f"{child.relative_to(ROOT).as_posix()} "
                "(move samples under workspace/projects/samples or user worlds under workspace/projects/user)"
            )
        elif child.is_file() and child.name not in allowed_files:
            errors.append(
                "unexpected file in projects root: "
                f"{child.relative_to(ROOT).as_posix()}"
            )
    samples_root = projects_root / "samples"
    if samples_root.is_dir():
        for dist_dir in samples_root.glob("*/dist"):
            if dist_dir.is_dir():
                errors.append(
                    "generated sample export directory found: "
                    f"{dist_dir.relative_to(ROOT).as_posix()} "
                    "(remove generated Player exports before committing)"
                )


def _check_workspace_state_layout(errors: list[str]) -> None:
    legacy_data_root = ROOT / "data"
    if legacy_data_root.exists():
        errors.append("legacy root data/ directory found; use workspace/state/ and workspace/experiments/")
    system_root = ROOT / "workspace" / "state" / "system"
    experiments_root = ROOT / "workspace" / "experiments"
    runs_root = ROOT / "workspace" / "state" / "experiment_runs"
    for path, label in (
        (system_root, "workspace/state/system"),
        (experiments_root, "workspace/experiments"),
        (runs_root, "workspace/state/experiment_runs"),
    ):
        if not path.is_dir():
            errors.append(f"missing {label}")
    if runs_root.is_dir():
        for child in runs_root.iterdir():
            if child.name != ".gitkeep":
                errors.append(
                    "generated experiment run output found: "
                    f"{child.relative_to(ROOT).as_posix()} "
                    "(keep only workspace/state/experiment_runs/.gitkeep)"
                )


def _check_ci_python_matrix(errors: list[str]) -> None:
    workflow = ROOT / ".github" / "workflows" / "ci.yml"
    if not workflow.is_file():
        errors.append("missing .github/workflows/ci.yml")
        return
    text = workflow.read_text(encoding="utf-8", errors="replace")
    if 'python-version: ["3.11", "3.12"]' not in text:
        errors.append("CI must cover python-version matrix [3.11, 3.12]")


def _check_worldbridge_admission_ci_contract(errors: list[str]) -> None:
    """Keep the WorldBridge no-overclaim gates in the general CI path."""
    workflow = ROOT / ".github" / "workflows" / "ci.yml"
    if not workflow.is_file():
        return
    text = workflow.read_text(encoding="utf-8-sig", errors="replace")
    required = (
        "tools/check_worldbridge_field_admission_verification.py",
        "tools/check_worldbridge_static_live_mapping_boundary.py",
        "tools/check_worldbridge_ps_graph_corpus.py",
        "tools/check_worldbridge_ps_hierarchy_contract.py",
        "tools/check_worldbridge_e313_bounded_replay_corpus.py",
        "tools/check_worldbridge_e313_live_capture_binding.py",
        "tools/check_worldbridge_shared_state_transport.py",
        "tools/check_worldbridge_e315_shared_state_transport_binding.py",
        "tools/check_worldbridge_e316_checkpoint_restore_witness.py",
        "tools/check_worldbridge_e317_live_checkpoint_gap_audit.py",
        "tools/check_worldbridge_e366_live_checkpoint_admission.py",
        "tools/check_worldbridge_e367_live_viewport_witness.py",
        "tools/check_worldbridge_e369_cross_process_receipt.py",
        "tools/check_worldbridge_e370_receipt_tamper_matrix.py",
        "tools/check_worldbridge_e371_deterministic_receipt.py",
        "tools/check_worldbridge_e372_receipt_artifact.py",
        "tools/check_worldbridge_e373_receipt_integrity.py",
        "tools/check_worldbridge_e374_compatibility_corpus.py",
        "tools/check_worldbridge_e375_compatibility_provenance.py",
        "tools/check_worldbridge_e376_provenance_canonical.py",
        "tools/check_worldbridge_fresh_sr_restore.py",
        "tools/check_worldbridge_e378_real_game_viewport_fresh_sr.py",
        "tools/check_worldbridge_e379_tick_envelope.py",
        "tools/check_worldbridge_e380_tick_execution.py",
        "tools/check_worldbridge_e381_tick_sequence.py",
        "tools/check_worldbridge_e382_restore_receipt.py",
        "tools/check_worldbridge_e384_receipt_ledger.py",
        "tools/check_worldbridge_e385_ledger_recovery.py",
        "tools/check_worldbridge_e386_project_identity.py",
        "tools/check_worldbridge_e387_project_world_identity.py",
        "tools/check_worldbridge_e388_real_project_receipt.py",
        "tools/check_worldbridge_e389_checkpoint_digest.py",
        "tools/check_worldbridge_e390_component_digest_matrix.py",
        "tools/check_worldbridge_e391_durable_component_matrix.py",
        "tools/check_worldbridge_e392_ledger_provenance.py",
        "tools/check_worldbridge_e393_project_identity_provenance.py",
        "tools/check_worldbridge_e394_identity_change_matrix.py",
        "tools/check_worldbridge_e395_identity_cross_process.py",
        "tools/check_worldbridge_e396_ledger_schema_boundary.py",
        "tools/check_worldbridge_e397_receipt_encoding_boundary.py",
        "tools/check_worldbridge_e398_atomic_write_failure.py",
        "tools/check_worldbridge_e399_concurrent_consumption.py",
        "tools/check_worldbridge_e400_end_to_end_chain.py",
        "tools/check_worldbridge_e401_shared_delta_contract.py",
        "tools/check_worldbridge_e402_delta_lifecycle.py",
        "tools/check_worldbridge_e403_input_sequence.py",
    )
    for fragment in required:
        if fragment not in text:
            errors.append(f"CI missing WorldBridge admission boundary check: {fragment}")


def _check_sr2d_native_release_contract(errors: list[str]) -> None:
    native_pyproject = ROOT / "native" / "sr2d_cpp" / "pyproject.toml"
    if not native_pyproject.is_file():
        errors.append("missing native/sr2d_cpp/pyproject.toml")
        return

    data = tomllib.loads(native_pyproject.read_text(encoding="utf-8"))
    project = data.get("project", {})
    if project.get("name") != "lotucosm-vitaloom-sr2d-cpp":
        errors.append("SR2D native distribution name must align with the L1 product")
    if project.get("version") != _read_pyproject_version():
        errors.append("SR2D native distribution version must match the L1 product version")
    if project.get("requires-python") != _read_pyproject_requires_python():
        errors.append("SR2D native Python floor must match the L1 product")

    scikit_build = data.get("tool", {}).get("scikit-build", {})
    cmake = scikit_build.get("cmake", {})
    ninja = scikit_build.get("ninja", {})
    if cmake.get("version") != ">=3.18,<4":
        errors.append("SR2D native build must constrain CMake to the supported pre-4 line")
    if ninja.get("version") != ">=1.11":
        errors.append("SR2D native build must provision Ninja through scikit-build-core")
    if ninja.get("make-fallback") is not False:
        errors.append("SR2D native build must fail closed instead of changing generators")

    package_tool = ROOT / "tools" / "package_sr2d_cpp.py"
    if not package_tool.is_file():
        errors.append("missing tools/package_sr2d_cpp.py")
    else:
        tool_text = package_tool.read_text(encoding="utf-8", errors="replace")
        tool_fragments = {
            "Ninja generator": 'environment["CMAKE_GENERATOR"] = "Ninja"',
            "Visual Studio 17-18 discovery range": 'VISUAL_STUDIO_VERSION_RANGE = "[17.0,19.0)"',
            "ephemeral backend build directory": 'f"build-dir={build_dir.resolve()}"',
            "MSVC discovery": '"Microsoft.VisualStudio.Component.VC.Tools.x86.x64"',
        }
        for label, fragment in tool_fragments.items():
            if fragment not in tool_text:
                errors.append(f"SR2D package verifier missing {label}: {fragment}")
        for forbidden in (r"D:\app", r"Microsoft Visual Studio\2022\Community"):
            if forbidden in tool_text:
                errors.append(
                    f"SR2D package verifier must not hardcode a local tool path: {forbidden}"
                )

    native_workflow = ROOT / ".github" / "workflows" / "sr2d-native.yml"
    if not native_workflow.is_file():
        errors.append("missing independent .github/workflows/sr2d-native.yml")
        return
    text = native_workflow.read_text(encoding="utf-8", errors="replace")
    required_fragments = {
        "Windows native runner": "runs-on: windows-latest",
        "supported Python matrix": 'python-version: ["3.11", "3.12"]',
        "exact package verifier": (
            "python tools/package_sr2d_cpp.py --wheel-dir dist/sr2d-cpp"
        ),
        "wheel artifact upload": "actions/upload-artifact@v4",
        "wheel artifact path": "dist/sr2d-cpp/*.whl",
    }
    for label, fragment in required_fragments.items():
        if fragment not in text:
            errors.append(f"SR2D native workflow missing {label}: {fragment}")

    general_ci = ROOT / ".github" / "workflows" / "ci.yml"
    if general_ci.is_file():
        general_text = general_ci.read_text(encoding="utf-8", errors="replace")
        if "tools/package_sr2d_cpp.py" in general_text:
            errors.append(
                "pure-Python CI must remain independent from the optional SR2D native wheel"
            )
def main() -> int:
    errors: list[str] = []

    for legacy in (
        ROOT / "core" / "Lotucosm",
        ROOT / "core" / "VitaLoom",
        ROOT / "core" / "api",
        ROOT / "builtin",
        ROOT / "products",
        ROOT / "suite_manifest.json",
    ):
        if legacy.exists():
            errors.append(f"legacy root runtime path still exists: {legacy.relative_to(ROOT)}")

    requires_python = _read_pyproject_requires_python()
    if requires_python != ">=3.11":
        errors.append(
            f"pyproject.toml requires-python={requires_python!r} "
            "应为 '>=3.11'"
        )
    version_file = ROOT / ".python-version"
    if version_file.is_file():
        declared_python = version_file.read_text(encoding="utf-8").strip()
        if not declared_python.startswith("3.11"):
            errors.append(
                f".python-version={declared_python!r} must declare local minimum 3.11"
            )
    if sys.version_info < (3, 11):
        errors.append(
            f"当前 Python {sys.version_info.major}.{sys.version_info.minor} "
            "低于项目最低版本 3.11"
        )

    pyproject_ver = _read_pyproject_version()
    if not pyproject_ver:
        errors.append("pyproject.toml 缺少 version 字段")
    else:
        from core.VitaLoom.project.project_manifest import (
            LOOM_EDITOR_VERSION,
            get_loom_editor_version_from_pyproject,
        )

        resolved = get_loom_editor_version_from_pyproject(ROOT)
        if resolved != pyproject_ver:
            errors.append(
                f"get_loom_editor_version_from_pyproject={resolved!r} "
                f"does not match pyproject version={pyproject_ver!r}"
            )
        if LOOM_EDITOR_VERSION != pyproject_ver:
            errors.append(
                f"LOOM_EDITOR_VERSION={LOOM_EDITOR_VERSION!r} "
                f"does not match pyproject version={pyproject_ver!r}"
            )
        try:
            from FrameCore.product_registry import load_product_registry
            from FrameCore.suite_registry import load_suite_manifest

            suite = load_suite_manifest(SUITE_ROOT)
            if suite.version != pyproject_ver:
                errors.append(
                    f"suite_manifest version={suite.version!r} "
                    f"does not match pyproject version={pyproject_ver!r}"
                )
            registry = load_product_registry(SUITE_ROOT)
            if suite.capability_catalog and not (SUITE_ROOT / suite.capability_catalog).is_file():
                errors.append(
                    f"suite_manifest capability_catalog missing: {suite.capability_catalog}"
                )
            for product_id in suite.products:
                if product_id not in registry.products:
                    errors.append(f"suite_manifest products missing product: {product_id}")
            for product_id, product_manifest in registry.products.items():
                if product_manifest.default_version not in product_manifest.versions:
                    errors.append(
                        f"{product_id}: default_version not listed: "
                        f"{product_manifest.default_version}"
                    )
                for version in product_manifest.versions:
                    pv = registry.get_version(product_id, version)
                    if pv is None:
                        errors.append(f"{product_id}: missing version manifest {version}")
                        continue
                    for name, command in sorted(pv.entrypoints.items()):
                        if not _entry_file_exists(ROOT, command):
                            errors.append(
                                f"{product_id}@{version}: entrypoint {name} missing: {command}"
                            )
                    if pv.builtin_capability_index and not (
                        pv.version_root / pv.builtin_capability_index
                    ).is_file():
                        errors.append(
                            f"{product_id}@{version}: builtin_capability_index missing: "
                            f"{pv.builtin_capability_index}"
                        )
                    suite_catalog = (
                        (SUITE_ROOT / suite.capability_catalog).resolve()
                        if suite.capability_catalog
                        else None
                    )
                    product_catalog = (
                        (pv.version_root / pv.builtin_capability_index).resolve()
                        if pv.builtin_capability_index
                        else None
                    )
                    if suite_catalog and product_catalog and product_catalog != suite_catalog:
                        errors.append(
                            f"{product_id}@{version}: capability catalog "
                            f"{pv.builtin_capability_index!r} != suite "
                            f"{suite.capability_catalog!r}"
                        )
            product = registry.products.get("lotucosm-vitaloom")
            if product is None:
                errors.append("products: 缺少 lotucosm-vitaloom product_manifest")
            else:
                default = registry.get_default_version(product.product_id)
                if default is None:
                    errors.append("products: 缺少 lotucosm-vitaloom 默认版本 manifest")
                elif default.version != pyproject_ver:
                    errors.append(
                        f"lotucosm-vitaloom default version={default.version!r} "
                        f"does not match pyproject version={pyproject_ver!r}"
                    )
        except Exception as exc:
            errors.append(f"Suite/Product manifest 校验失败: {exc}")

    index_path = CATALOG_PATH
    if not index_path.is_file():
        errors.append("缺少 builtin/package_index.json")
    else:
        try:
            from core.VitaLoom.core.bundle_paths import physical_root_exists

            data = json.loads(index_path.read_text(encoding="utf-8"))
            packages = data.get("packages", [])
            if not isinstance(packages, list):
                errors.append("package_index.json: packages 不是数组")
            else:
                ids: set[str] = set()
                plugin_classes = _discover_plugin_class_names()
                for pkg in packages:
                    if not isinstance(pkg, dict):
                        continue
                    pkg_id = str(pkg.get("id", "") or "").strip()
                    if not pkg_id:
                        errors.append("package_index: 存在空 id 的包条目")
                        continue
                    if pkg_id in ids:
                        errors.append(f"package_index: 重复 id {pkg_id}")
                    ids.add(pkg_id)
                    ver = str(pkg.get("version", "") or "").strip()
                    status = str(pkg.get("status", "")).lower()
                    if status != "planned" and ver and not SEMVER_RE.match(ver):
                        errors.append(f"package_index: {pkg_id} version 非 semver: {ver!r}")
                    origin = str(pkg.get("origin", "") or "").strip().lower()
                    role = str(pkg.get("role", "") or "").strip().lower()
                    if origin and origin not in {
                        "core",
                        "official",
                        "community",
                        "embedded",
                    }:
                        errors.append(f"package_index: {pkg_id} origin 无效: {origin!r}")
                    if role and role not in {
                        "editor",
                        "runtime",
                        "hybrid",
                        "resource",
                    }:
                        errors.append(f"package_index: {pkg_id} role 无效: {role!r}")
                    physical_roots = pkg.get("physical_roots", [])
                    if not isinstance(physical_roots, list):
                        errors.append(
                            f"package_index: {pkg_id} physical_roots 不是数组"
                        )
                        physical_roots = []
                    if status != "planned":
                        for rel in physical_roots:
                            rel_s = str(rel or "").strip()
                            if rel_s and not physical_root_exists(rel_s, repo_root=ROOT):
                                errors.append(
                                    f"package_index: {pkg_id} physical_root 不存在: {rel_s}"
                                )
                    plugins = pkg.get("plugins", [])
                    if not isinstance(plugins, list):
                        errors.append(f"package_index: {pkg_id} plugins 不是数组")
                        plugins = []
                    if status != "planned":
                        for plugin_id in plugins:
                            plugin_s = str(plugin_id or "").strip()
                            if plugin_s and plugin_s not in plugin_classes:
                                errors.append(
                                    f"package_index: {pkg_id} plugin 未发现: {plugin_s}"
                                )
        except json.JSONDecodeError as exc:
            errors.append(f"package_index.json 解析失败: {exc}")

    try:
        _check_sample_project_locks(errors)
    except Exception as exc:
        errors.append(f"sample project lock check failed: {exc}")

    try:
        _check_forbidden_repository_references(errors)
    except Exception as exc:
        errors.append(f"forbidden repository reference check failed: {exc}")

    try:
        _check_no_tracked_local_history(errors)
    except Exception as exc:
        errors.append(f"tracked local history check failed: {exc}")

    try:
        _check_plugin_layout(errors)
    except Exception as exc:
        errors.append(f"plugin layout check failed: {exc}")

    try:
        _check_project_layout(errors)
    except Exception as exc:
        errors.append(f"project layout check failed: {exc}")

    try:
        _check_workspace_state_layout(errors)
    except Exception as exc:
        errors.append(f"workspace state layout check failed: {exc}")

    try:
        _check_ci_python_matrix(errors)
    except Exception as exc:
        errors.append(f"CI python matrix check failed: {exc}")
    try:
        _check_worldbridge_admission_ci_contract(errors)
    except Exception as exc:
        errors.append(f"WorldBridge admission CI contract check failed: {exc}")
    try:
        _check_sr2d_native_release_contract(errors)
    except Exception as exc:
        errors.append(f"SR2D native release contract check failed: {exc}")

    if errors:
        print("release consistency FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("release consistency OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


