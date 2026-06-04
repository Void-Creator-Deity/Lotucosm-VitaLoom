"""包目录与安装/卸载操作服务（供 package_manager_plugin 调用）。

排错: 见 `builtin/README.md`。
"""

from __future__ import annotations

import json
import os
import shutil
import hashlib
import tempfile
import zipfile
import urllib.request
import base64
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from builtin.editor_extensions.package_domain.resolver import resolve_dependency_graph
from builtin.editor_extensions.package_domain.policy import should_block


def parse_version(version: str) -> tuple[int, int, int]:
    parts = (version or "0.0.0").split(".")
    nums = []
    for i in range(3):
        try:
            nums.append(int(parts[i]) if i < len(parts) else 0)
        except Exception:
            nums.append(0)
    return nums[0], nums[1], nums[2]


def version_gte(actual: str, expected_min: str) -> bool:
    return parse_version(actual) >= parse_version(expected_min)


def parse_dependency_expr(expr: str) -> tuple[str, str, str]:
    text = (expr or "").strip()
    if ">=" in text:
        pkg_id, ver = text.split(">=", 1)
        return pkg_id.strip(), ">=", ver.strip()
    return text, "", ""


class PackageCatalogService:
    def __init__(self, repo_root: str):
        self.repo_root = repo_root

    def registry_config_path(self) -> str:
        return os.path.join(self.repo_root, "data", "system", "package_registries.json")

    def load_registry_config(self) -> List[Dict[str, Any]]:
        try:
            path = self.registry_config_path()
            if not os.path.exists(path):
                return [{"name": "builtin", "type": "file", "path": "builtin/package_index.json"}]
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            registries = data.get("registries", [])
            return registries if isinstance(registries, list) else []
        except Exception:
            return [{"name": "builtin", "type": "file", "path": "builtin/package_index.json"}]

    def load_index_from_file(self, path: str) -> List[Dict[str, Any]]:
        abs_path = path if os.path.isabs(path) else os.path.join(self.repo_root, path)
        with open(abs_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        packages = data.get("packages", [])
        return packages if isinstance(packages, list) else []

    def load_index_from_url(self, url: str, downloader: Any = None) -> List[Dict[str, Any]]:
        if downloader and hasattr(downloader, "fetch_json"):
            data, err = downloader.fetch_json(url, timeout_s=8)
            if err:
                raise RuntimeError(err)
        else:
            import urllib.request

            with urllib.request.urlopen(url, timeout=8) as resp:  # nosec - from user registry config
                raw = resp.read().decode("utf-8", errors="replace")
            data = json.loads(raw)
        packages = data.get("packages", [])
        return packages if isinstance(packages, list) else []

    @staticmethod
    def normalize_package(pkg: Dict[str, Any], source: str) -> Dict[str, Any]:
        if not isinstance(pkg, dict):
            return {}
        normalized = dict(pkg)
        normalized.setdefault("id", "")
        normalized.setdefault("display_name", normalized.get("id", ""))
        normalized.setdefault("version", "")
        normalized.setdefault("category", "")
        normalized.setdefault("description", "")
        normalized.setdefault("dependencies", [])
        normalized.setdefault("conflicts", [])
        normalized.setdefault("plugins", [])
        normalized.setdefault("source", source)
        return normalized

    @staticmethod
    def merge_package_lists(package_lists: List[List[Dict[str, Any]]], priority_sources: List[str]) -> List[Dict[str, Any]]:
        priority = {name: idx for idx, name in enumerate(priority_sources)}
        merged: Dict[str, Dict[str, Any]] = {}
        for pkg_list in package_lists:
            for pkg in pkg_list:
                if not isinstance(pkg, dict):
                    continue
                pkg_id = str(pkg.get("id", "") or "")
                if not pkg_id:
                    continue
                src = str(pkg.get("source", "unknown"))
                if pkg_id not in merged:
                    merged[pkg_id] = pkg
                    continue
                old = merged[pkg_id]
                old_src = str(old.get("source", "unknown"))
                if priority.get(src, 10_000) < priority.get(old_src, 10_000):
                    merged[pkg_id] = pkg
        return sorted(merged.values(), key=lambda p: (str(p.get("display_name", "")), str(p.get("id", ""))))

    @classmethod
    def collect_update_candidates(
        cls, loaded_lists: List[List[Dict[str, Any]]], merged: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        highest: Dict[str, str] = {}
        for pkg_list in loaded_lists:
            for pkg in pkg_list:
                pkg_id = str(pkg.get("id", "") or "")
                if not pkg_id:
                    continue
                ver = str(pkg.get("version", "") or "0.0.0")
                old = highest.get(pkg_id)
                if old is None or version_gte(ver, old):
                    highest[pkg_id] = ver
        updates: Dict[str, str] = {}
        for pkg in merged:
            pkg_id = str(pkg.get("id", "") or "")
            if not pkg_id:
                continue
            current = str(pkg.get("version", "") or "0.0.0")
            latest = highest.get(pkg_id, current)
            if version_gte(latest, current) and parse_version(latest) != parse_version(current):
                updates[pkg_id] = latest
        return updates

    @staticmethod
    def apply_version_overrides(packages: List[Dict[str, Any]], overrides: Dict[str, str]) -> List[Dict[str, Any]]:
        if not overrides:
            return packages
        out: List[Dict[str, Any]] = []
        for pkg in packages:
            pkg_id = str(pkg.get("id", "") or "")
            if pkg_id and pkg_id in overrides:
                p = dict(pkg)
                p["version"] = overrides[pkg_id]
                out.append(p)
            else:
                out.append(pkg)
        return out

    def load_all_packages(
        self, version_overrides: Dict[str, str], downloader: Any = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, str], List[str]]:
        registries = self.load_registry_config()
        priority_sources = ["builtin", "file", "url", "unknown"]
        loaded_lists: List[List[Dict[str, Any]]] = []
        errors: List[str] = []
        for reg in registries:
            try:
                name = str(reg.get("name", "registry"))
                reg_type = str(reg.get("type", "file"))
                if reg_type == "file":
                    path = str(reg.get("path", ""))
                    pkgs = self.load_index_from_file(path)
                    loaded_lists.append([self.normalize_package(p, "builtin" if name == "builtin" else "file") for p in pkgs])
                elif reg_type == "url":
                    url = str(reg.get("url", ""))
                    pkgs = self.load_index_from_url(url, downloader=downloader)
                    loaded_lists.append([self.normalize_package(p, "url") for p in pkgs])
                else:
                    errors.append(f"{name}: unsupported registry type={reg_type}")
            except Exception as e:
                errors.append(f"{reg.get('name', 'registry')}: {e}")
        merged = self.merge_package_lists(loaded_lists, priority_sources)
        merged = self.apply_version_overrides(merged, version_overrides)
        updates = self.collect_update_candidates(loaded_lists, merged)
        return merged, updates, errors


class PackageOperationService:
    def __init__(self, project_manager: Any):
        self.project_manager = project_manager

    def get_disabled_plugins(self) -> List[str]:
        cfg = self.project_manager.get_current_project_config()
        if not cfg:
            return []
        disabled = cfg.get("disabled_plugins", [])
        if not isinstance(disabled, list):
            return []
        return [str(x) for x in disabled if x is not None]

    def write_disabled_plugins(self, disabled_plugins: List[str]) -> bool:
        return self.project_manager.update_project_config_fields({"disabled_plugins": disabled_plugins})

    def _read_package_state(self) -> Dict[str, Any]:
        cfg = self.project_manager.get_current_project_config() or {}
        state = cfg.get("package_state", {})
        if not isinstance(state, dict):
            state = {}
        legacy = cfg.get("package_version_overrides", {})
        legacy_overrides = legacy if isinstance(legacy, dict) else {}
        state.setdefault("version_overrides", dict(legacy_overrides))
        state.setdefault("operation_log", [])
        state.setdefault("installed", {})
        state.setdefault("history", [])
        state.setdefault("rollback_points", [])
        return state

    def migrate_legacy_state(self) -> bool:
        state = self._read_package_state()
        return self.project_manager.update_project_config_fields(
            {
                "package_version_overrides": dict(state.get("version_overrides", {})),
                "package_state": state,
            }
        )

    def get_version_overrides(self) -> Dict[str, str]:
        state = self._read_package_state()
        raw = state.get("version_overrides", {})
        if not isinstance(raw, dict):
            return {}
        cleaned: Dict[str, str] = {}
        for k, v in raw.items():
            key = str(k or "").strip()
            val = str(v or "").strip()
            if key and val:
                cleaned[key] = val
        return cleaned

    def write_version_overrides(self, overrides: Dict[str, str], action: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        state = self._read_package_state()
        state["version_overrides"] = dict(overrides)
        op_log = state.get("operation_log", [])
        if not isinstance(op_log, list):
            op_log = []
        op_log.append(
            {
                "action": action,
                "at": datetime.now().isoformat(timespec="seconds"),
                "metadata": metadata or {},
                "version_overrides": dict(overrides),
            }
        )
        state["operation_log"] = op_log[-200:]
        history = state.get("history", [])
        if not isinstance(history, list):
            history = []
        history.append(
            {
                "action": action,
                "at": datetime.now().isoformat(timespec="seconds"),
                "metadata": metadata or {},
            }
        )
        state["history"] = history[-200:]
        return self.project_manager.update_project_config_fields(
            {"package_version_overrides": dict(overrides), "package_state": state}
        )

    def _project_packages_dir(self) -> Optional[str]:
        project_path = self.project_manager.get_current_project_path()
        if not project_path:
            return None
        out = os.path.join(project_path, "packages")
        os.makedirs(out, exist_ok=True)
        return out

    def _project_cache_dir(self) -> Optional[str]:
        project_path = self.project_manager.get_current_project_path()
        if not project_path:
            return None
        out = os.path.join(project_path, ".pkgcache")
        os.makedirs(out, exist_ok=True)
        return out

    def create_rollback_point(self, reason: str) -> Optional[str]:
        state = self._read_package_state()
        points = state.get("rollback_points", [])
        if not isinstance(points, list):
            points = []
        point_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        points.append(
            {
                "id": point_id,
                "reason": reason,
                "at": datetime.now().isoformat(timespec="seconds"),
                "version_overrides": dict(state.get("version_overrides", {})),
                "installed": dict(state.get("installed", {})),
            }
        )
        state["rollback_points"] = points[-100:]
        ok = self.project_manager.update_project_config_fields({"package_state": state})
        return point_id if ok else None

    def rollback_to_point(self, point_id: str) -> bool:
        state = self._read_package_state()
        points = state.get("rollback_points", [])
        if not isinstance(points, list):
            return False
        target = None
        for p in points:
            if isinstance(p, dict) and str(p.get("id")) == str(point_id):
                target = p
                break
        if target is None:
            return False
        state["version_overrides"] = dict(target.get("version_overrides", {}))
        state["installed"] = dict(target.get("installed", {}))
        return self.project_manager.update_project_config_fields(
            {
                "package_state": state,
                "package_version_overrides": dict(state.get("version_overrides", {})),
            }
        )

    def create_update_plan(self, target_updates: Dict[str, str], package_lookup: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        items: List[Dict[str, str]] = []
        source_summary: Dict[str, int] = {}
        for pkg_id in sorted(target_updates.keys()):
            pkg = package_lookup.get(pkg_id, {})
            current = str(pkg.get("version", "0.0.0"))
            target = str(target_updates[pkg_id])
            source = str(pkg.get("source", "unknown"))
            source_summary[source] = source_summary.get(source, 0) + 1
            items.append(
                {
                    "id": pkg_id,
                    "current_version": current,
                    "target_version": target,
                    "source": source,
                }
            )
        return {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "count": len(items),
            "source_summary": source_summary,
            "items": items,
        }

    def apply_update_plan(self, plan: Dict[str, Any], action: str = "update") -> tuple[bool, int]:
        self.create_rollback_point(f"before_{action}")
        overrides = self.get_version_overrides()
        items = plan.get("items", [])
        if not isinstance(items, list):
            return False, 0
        for item in items:
            if not isinstance(item, dict):
                continue
            pkg_id = str(item.get("id", "")).strip()
            target = str(item.get("target_version", "")).strip()
            if pkg_id and target:
                overrides[pkg_id] = target
        ok = self.write_version_overrides(overrides, action=action, metadata={"plan_count": len(items)})
        return ok, len(items)

    def export_plan_to_logs(self, plan: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
        project_path = self.project_manager.get_current_project_path()
        if not project_path:
            return None, "no_project"
        logs_dir = os.path.join(project_path, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = os.path.join(logs_dir, f"package_update_plan_{ts}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)
        return out_path, None

    def list_exported_plans(self) -> List[str]:
        project_path = self.project_manager.get_current_project_path()
        if not project_path:
            return []
        logs_dir = os.path.join(project_path, "logs")
        if not os.path.isdir(logs_dir):
            return []
        files = [os.path.join(logs_dir, n) for n in os.listdir(logs_dir) if n.startswith("package_update_plan_") and n.endswith(".json")]
        files.sort(reverse=True)
        return files

    def rollback_from_latest_export(self) -> tuple[bool, str]:
        files = self.list_exported_plans()
        if not files:
            return False, "no_plan"
        latest = files[0]
        with open(latest, "r", encoding="utf-8") as f:
            data = json.load(f)
        items = data.get("items", [])
        overrides = self.get_version_overrides()
        if not isinstance(items, list):
            return False, "invalid_plan"
        for item in items:
            if not isinstance(item, dict):
                continue
            pkg_id = str(item.get("id", "")).strip()
            current = str(item.get("current_version", "")).strip()
            if pkg_id and current:
                overrides[pkg_id] = current
        ok = self.write_version_overrides(overrides, action="rollback", metadata={"from_plan": os.path.basename(latest)})
        return ok, latest

    def resolve_transaction(
        self,
        package_id: str,
        packages: List[Dict[str, Any]],
        enabled_ids: set[str],
        mode: str = "warn",
    ) -> Dict[str, Any]:
        lookup = {str(p.get("id", "")): p for p in packages}
        order, issues = resolve_dependency_graph(package_id, lookup, enabled_ids)
        block = should_block(mode, len(issues))
        return {"order": order, "issues": issues, "should_block": block}

    def _hash_file(self, path: str) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while True:
                chunk = f.read(1024 * 1024)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()

    def _fetch_artifact(self, artifact: Dict[str, Any], downloader: Any = None) -> tuple[Optional[str], Optional[str]]:
        cache_dir = self._project_cache_dir()
        if not cache_dir:
            return None, "no_project"
        source_type = str(artifact.get("type", "file"))
        source = str(artifact.get("path", "") or artifact.get("url", ""))
        if not source:
            return None, "no_source"
        file_name = os.path.basename(source) or "package.zip"
        out_path = os.path.join(cache_dir, file_name)
        if source_type == "file":
            abs_src = source if os.path.isabs(source) else os.path.join(os.getcwd(), source)
            if not os.path.exists(abs_src):
                return None, "file_not_found"
            shutil.copy2(abs_src, out_path)
        else:
            if downloader and hasattr(downloader, "fetch_bytes"):
                raw, err = downloader.fetch_bytes(source, timeout_s=15)
                if err:
                    return None, err
                with open(out_path, "wb") as f:
                    f.write(raw)
            else:
                with urllib.request.urlopen(source, timeout=15) as resp:
                    with open(out_path, "wb") as f:
                        f.write(resp.read())
        return out_path, None

    def _verify_artifact(self, path: str, artifact: Dict[str, Any]) -> Optional[str]:
        expected = str(artifact.get("sha256", "")).strip().lower()
        if not expected:
            return None
        actual = self._hash_file(path).lower()
        if actual != expected:
            return "sha256_mismatch"
        return None

    def _verify_artifact_signature(self, zip_path: str, artifact: Dict[str, Any]) -> Optional[str]:
        """
        签名验证：warn-only（不阻断）。
        返回 issue_code（字符串）表示签名问题，否则返回 None。
        """
        signature_b64 = artifact.get("signature", None)
        if not signature_b64:
            return None

        signature_b64_text = str(signature_b64).strip()
        if not signature_b64_text:
            return None

        try:
            sig_bytes = base64.b64decode(signature_b64_text)
        except Exception:
            return "signature_invalid"

        # 消息：zip 文件内容 sha256 digest 的原始字节（32 bytes）
        # install 流程在这里已先完成 sha256_mismatch 校验，因此直接从 expected sha256 推导更高效。
        expected_sha = str(artifact.get("sha256", "")).strip().lower()
        try:
            digest_bytes = bytes.fromhex(expected_sha)
        except Exception:
            return "signature_unverifiable"

        pem = artifact.get("public_key_pem", None)
        public_key_pem: Optional[str] = str(pem).strip() if pem else None

        if not public_key_pem:
            try:
                repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
                key_path = os.path.join(repo_root, "builtin", "package_public_key.pem")
                if not os.path.exists(key_path):
                    return "signature_unverifiable"
                with open(key_path, "r", encoding="utf-8") as f:
                    public_key_pem = f.read()
            except Exception:
                return "signature_unverifiable"

        try:
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
            from cryptography.exceptions import InvalidSignature

            public_key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
            if not isinstance(public_key, Ed25519PublicKey):
                return "signature_invalid"
            public_key.verify(sig_bytes, digest_bytes)
            return None
        except InvalidSignature:
            return "signature_invalid"
        except Exception:
            return "signature_unverifiable"

    def _install_zip_atomic(self, pkg_id: str, version: str, zip_path: str) -> tuple[bool, Optional[str], Optional[str]]:
        packages_dir = self._project_packages_dir()
        if not packages_dir:
            return False, None, "no_project"
        target_dir = os.path.join(packages_dir, pkg_id, version)
        stage_root = tempfile.mkdtemp(prefix="pkg_stage_")
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(stage_root)
            os.makedirs(os.path.dirname(target_dir), exist_ok=True)
            if os.path.isdir(target_dir):
                shutil.rmtree(target_dir)
            shutil.move(stage_root, target_dir)
            return True, target_dir, None
        except Exception as e:
            return False, None, str(e)

    def install_package(
        self,
        package_id: str,
        packages: List[Dict[str, Any]],
        enabled_ids: set[str],
        downloader: Any = None,
        mode: str = "warn",
    ) -> Dict[str, Any]:
        resolve = self.resolve_transaction(package_id, packages, enabled_ids, mode=mode)
        if resolve["should_block"]:
            return {"ok": False, "stage": "resolve", "error": "; ".join(resolve["issues"]), "issues": resolve["issues"]}
        lookup = {str(p.get("id", "")): p for p in packages}
        pkg = lookup.get(package_id)
        if not pkg:
            return {"ok": False, "stage": "resolve", "error": "package_not_found", "issues": resolve["issues"]}
        self.create_rollback_point(f"before_install_{package_id}")
        artifact = pkg.get("artifact", {})
        if isinstance(artifact, dict) and artifact:
            zip_path, err = self._fetch_artifact(artifact, downloader=downloader)
            if err or not zip_path:
                return {"ok": False, "stage": "fetch", "error": err or "fetch_failed", "issues": resolve["issues"]}
            verify_err = self._verify_artifact(zip_path, artifact)
            if verify_err:
                return {"ok": False, "stage": "verify", "error": verify_err, "issues": resolve["issues"]}

            signature_issue = self._verify_artifact_signature(zip_path, artifact)
            signature_issues: List[str] = []
            if signature_issue:
                signature_issues.append(signature_issue)

            ok, install_path, install_err = self._install_zip_atomic(package_id, str(pkg.get("version", "0.0.0")), zip_path)
            if not ok:
                return {"ok": False, "stage": "install", "error": install_err or "install_failed", "issues": resolve["issues"]}
        else:
            install_path = None
            signature_issues = []
        state = self._read_package_state()
        installed = state.get("installed", {})
        if not isinstance(installed, dict):
            installed = {}
        installed[package_id] = {
            "version": str(pkg.get("version", "0.0.0")),
            "source": str(pkg.get("source", "unknown")),
            "path": install_path or "",
            "installed_at": datetime.now().isoformat(timespec="seconds"),
        }
        state["installed"] = installed
        self.project_manager.update_project_config_fields({"package_state": state})
        self.write_version_overrides(self.get_version_overrides(), action="install", metadata={"package_id": package_id})
        final_issues = list(resolve.get("issues", []))
        final_issues.extend(signature_issues)
        return {"ok": True, "stage": "activate", "issues": final_issues}

    def uninstall_package(self, package_id: str) -> Dict[str, Any]:
        self.create_rollback_point(f"before_uninstall_{package_id}")
        state = self._read_package_state()
        installed = state.get("installed", {})
        if not isinstance(installed, dict):
            installed = {}
        info = installed.get(package_id)
        if not isinstance(info, dict):
            return {"ok": False, "error": "not_installed"}
        target_path = str(info.get("path", "")).strip()
        if target_path and os.path.isdir(target_path):
            try:
                shutil.rmtree(target_path)
            except Exception as e:
                return {"ok": False, "error": str(e)}
        installed.pop(package_id, None)
        overrides = self.get_version_overrides()
        if package_id in overrides:
            overrides.pop(package_id, None)
        state["installed"] = installed
        ok = self.project_manager.update_project_config_fields(
            {"package_state": state, "package_version_overrides": overrides}
        )
        if ok:
            self.write_version_overrides(overrides, action="uninstall", metadata={"package_id": package_id})
        return {"ok": ok}

