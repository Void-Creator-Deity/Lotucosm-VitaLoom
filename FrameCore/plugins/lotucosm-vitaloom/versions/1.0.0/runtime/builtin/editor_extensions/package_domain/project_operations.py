"""Qt-free package operation orchestration for project command authority."""
from __future__ import annotations

from functools import wraps
from typing import Any, Callable, Dict, List, Mapping, Optional, Set, Tuple

from builtin.editor_extensions.package_domain.package_transactions import (
    PackageTransactionError,
    PackageTransactionStore,
    create_store_from_operation_service,
)

ProjectCommand = Callable[[str, str, Optional[Dict[str, Any]]], Dict[str, Any]]
CommandSucceeded = Callable[[Dict[str, Any]], bool]


def _command_succeeded(result: Dict[str, Any]) -> bool:
    return bool(isinstance(result, dict) and result.get("ok"))


def _unique_package_ids(package_ids: List[str]) -> List[str]:
    seen: Set[str] = set()
    normalized: List[str] = []
    for raw_id in package_ids:
        package_id = str(raw_id).strip()
        if package_id and package_id not in seen:
            seen.add(package_id)
            normalized.append(package_id)
    return normalized


def _install_payload(operation: Dict[str, Any], package: Dict[str, Any]) -> Dict[str, str]:
    return {
        "source": str(operation.get("source") or package.get("source") or "official"),
        "path": str(operation.get("install_path") or ""),
        "version": str(operation.get("version") or package.get("version") or "0.0.0"),
    }


def _plain_mapping(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _transaction_store(
    transaction_store: Optional[PackageTransactionStore], operation_service: Any
) -> Tuple[Optional[PackageTransactionStore], Optional[Dict[str, Any]]]:
    if transaction_store is not None:
        return transaction_store, None
    try:
        return create_store_from_operation_service(operation_service), None
    except PackageTransactionError as exc:
        return None, {"error": exc.code, "details": dict(exc.details)}


def _begin_receipt(
    store: Optional[PackageTransactionStore],
    action: str,
    package_id: str,
    *,
    payload: Optional[Mapping[str, Any]] = None,
    local_snapshot: Optional[Mapping[str, Any]] = None,
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    if store is None:
        return None, None
    try:
        return store.begin(action, package_id, payload=payload, local_snapshot=local_snapshot), None
    except PackageTransactionError as exc:
        return None, {"error": exc.code, "details": dict(exc.details)}


def _advance_receipt(
    store: Optional[PackageTransactionStore],
    receipt: Optional[Mapping[str, Any]],
    state: str,
    **kwargs: Any,
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    if store is None or receipt is None:
        return dict(receipt) if isinstance(receipt, Mapping) else None, None
    try:
        return store.advance(str(receipt["transaction_id"]), state, **kwargs), None
    except PackageTransactionError as exc:
        return None, {"error": exc.code, "details": dict(exc.details)}


def _receipt_fields(receipt: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    if not isinstance(receipt, Mapping):
        return {"transaction_id": "", "transaction_state": "", "recovery": {}}
    return {
        "transaction_id": str(receipt.get("transaction_id", "")),
        "transaction_state": str(receipt.get("state", "")),
        "recovery": _plain_mapping(receipt.get("recovery")),
    }


def _capture_local_snapshot(operation_service: Any, package_id: str) -> Dict[str, Any]:
    capture = getattr(operation_service, "capture_local_artifact", None)
    if callable(capture):
        result = capture(package_id)
        return _plain_mapping(result)
    return {
        "ok": True,
        "package_id": str(package_id),
        "path": "",
        "recorded": False,
        "exists": False,
        "artifact_present": False,
    }


def _remove_local_artifact(operation_service: Any, package_id: str, snapshot: Mapping[str, Any]) -> Dict[str, Any]:
    remove = getattr(operation_service, "remove_local_artifact", None)
    if callable(remove):
        return _plain_mapping(remove(dict(snapshot)))
    uninstall = getattr(operation_service, "uninstall_package")
    try:
        return _plain_mapping(
            uninstall(package_id, record_project_state=False, artifact_snapshot=dict(snapshot))
        )
    except TypeError:
        return _plain_mapping(uninstall(package_id, record_project_state=False))


def _artifact_is_available(operation_service: Any, package_id: str, artifact_path: str) -> bool:
    inspect = getattr(operation_service, "inspect_local_artifact_path", None)
    if not callable(inspect):
        return bool(artifact_path)
    result = _plain_mapping(inspect(package_id, artifact_path))
    return bool(result.get("ok") and result.get("exists"))


def _package_transaction_mutation(authority_action: str):
    """Guard a public package write sequence with its own project-local interlock.

    The wrapper resolves the durable store before any receipt/local/project mutation.
    Legacy contract-only callers without an active durable project store remain
    non-mutating test adapters; every real receipt-backed operation must prove an
    owned package interlock before entering the wrapped authority seam.
    """

    def decorate(operation):
        @wraps(operation)
        def guarded(*args: Any, **kwargs: Any) -> Dict[str, Any]:
            store, store_error = _transaction_store(kwargs.get("transaction_store"), kwargs.get("operation_service"))
            if store_error:
                return {
                    "ok": False,
                    "error": "transaction_store_unavailable",
                    "transaction_error": store_error,
                    "operation": {},
                }
            if store is None:
                return operation(*args, **kwargs)
            project_path = str(getattr(store, "project_path", "") or "")
            if not project_path:
                return {
                    "ok": False,
                    "error": "package_transaction_interlock_project_unavailable",
                    "interlock": {"authority_action": authority_action},
                    "operation": {},
                }
            try:
                from builtin.editor_extensions.package_domain.package_transaction_interlock import (
                    PackageTransactionInterlockError,
                    package_transaction_mutation_interlock,
                )

                with package_transaction_mutation_interlock(project_path, authority_action=authority_action):
                    forwarded = dict(kwargs)
                    forwarded["transaction_store"] = store
                    return operation(*args, **forwarded)
            except PackageTransactionInterlockError as exc:
                return {
                    "ok": False,
                    "error": exc.code,
                    "interlock": dict(exc.details),
                    "operation": {},
                }

        return guarded

    return decorate


class PackageProjectOperations:
    """Coordinates package storage with project commands without UI dependencies.

    Project command registry calls remain the only authority for project-state writes.
    Receipt persistence records cross-boundary progress so a crash or command failure does
    not get misreported as completion and has an explicit, safe recovery action.
    """

    @staticmethod
    def enable_packages(
        package_ids: List[str],
        run_project_command: ProjectCommand,
        *,
        command_succeeded: Optional[CommandSucceeded] = None,
    ) -> Dict[str, Any]:
        targets = _unique_package_ids(package_ids)
        if not targets:
            return {
                "ok": False,
                "all_ok": False,
                "changed": False,
                "results": [],
                "succeeded_ids": [],
                "failed_ids": [],
            }
        is_success = command_succeeded or _command_succeeded
        results: List[Dict[str, Any]] = []
        succeeded_ids: List[str] = []
        failed_ids: List[str] = []
        for package_id in targets:
            result = run_project_command("plugin.enable", package_id, None)
            success = is_success(result)
            results.append({"package_id": package_id, "result": result, "ok": success})
            if success:
                succeeded_ids.append(package_id)
            else:
                failed_ids.append(package_id)
        all_ok = not failed_ids
        return {
            "ok": all_ok,
            "all_ok": all_ok,
            "changed": bool(succeeded_ids),
            "results": results,
            "succeeded_ids": succeeded_ids,
            "failed_ids": failed_ids,
        }

    @staticmethod
    @_package_transaction_mutation("package.install")
    def install_package(
        package: Dict[str, Any],
        packages: List[Dict[str, Any]],
        enabled_ids: Set[str],
        *,
        operation_service: Any,
        run_project_command: ProjectCommand,
        downloader: Any,
        mode: str,
        command_succeeded: Optional[CommandSucceeded] = None,
        transaction_store: Optional[PackageTransactionStore] = None,
    ) -> Dict[str, Any]:
        package_id = str(package.get("id", "")).strip()
        if not package_id:
            return {"ok": False, "error": "missing_package_id", "operation": {"ok": False}}
        store, store_error = _transaction_store(transaction_store, operation_service)
        if store_error:
            return {"ok": False, "error": "transaction_store_unavailable", "transaction_error": store_error, "operation": {}}
        receipt, receipt_error = _begin_receipt(
            store,
            "install",
            package_id,
            payload={
                "source": str(package.get("source") or "official"),
                "path": "",
                "version": str(package.get("version") or "0.0.0"),
            },
        )
        if receipt_error:
            return {"ok": False, "error": "transaction_begin_failed", "transaction_error": receipt_error, "operation": {}}
        operation = _plain_mapping(
            operation_service.install_package(
                package_id,
                packages,
                enabled_ids,
                downloader=downloader,
                mode=mode,
                record_project_state=False,
            )
        )
        if not operation.get("ok"):
            failed, advance_error = _advance_receipt(
                store, receipt, "failed", details={"reason": "local_install_failed"}, local_result=operation
            )
            return {
                "ok": False,
                "error": str(operation.get("error", "local_install_failed")),
                "operation": operation,
                "command": None,
                "command_ok": False,
                **_receipt_fields(failed or receipt),
                "transaction_error": advance_error,
            }
        payload = _install_payload(operation, package)
        local, advance_error = _advance_receipt(
            store,
            receipt,
            "local_applied",
            details={"install_path": payload["path"]},
            payload=payload,
            local_snapshot={"package_id": package_id, "path": payload["path"], "recorded": True, "exists": bool(payload["path"])},
            local_result=operation,
        )
        if advance_error:
            return {
                "ok": False,
                "error": "transaction_local_record_failed",
                "operation": operation,
                "command": None,
                "command_ok": False,
                **_receipt_fields(receipt),
                "transaction_error": advance_error,
            }
        command = _plain_mapping(run_project_command("plugin.install", package_id, payload))
        command_ok = (command_succeeded or _command_succeeded)(command)
        if not command_ok:
            failed, advance_error = _advance_receipt(
                store,
                local,
                "failed_recoverable",
                details={"reason": "project_install_failed"},
                project_command=command,
                recovery={"action": "retry_project_install", "artifact_path": payload["path"]},
            )
            return {
                "ok": False,
                "error": "project_command_failed",
                "operation": operation,
                "command": command,
                "command_ok": False,
                "payload": payload,
                **_receipt_fields(failed or local),
                "transaction_error": advance_error,
            }
        project_applied, advance_error = _advance_receipt(
            store,
            local,
            "project_applied",
            details={"command": "plugin.install"},
            project_command=command,
        )
        if advance_error:
            return {
                "ok": False,
                "error": "transaction_project_record_failed",
                "operation": operation,
                "command": command,
                "command_ok": True,
                "payload": payload,
                **_receipt_fields(local),
                "transaction_error": advance_error,
            }
        completed, advance_error = _advance_receipt(store, project_applied, "completed", details={})
        return {
            "ok": not advance_error,
            "error": "transaction_complete_failed" if advance_error else "",
            "operation": operation,
            "command": command,
            "command_ok": True,
            "payload": payload,
            **_receipt_fields(completed or project_applied),
            "transaction_error": advance_error,
        }

    @staticmethod
    @_package_transaction_mutation("package.uninstall")
    def uninstall_package(
        package_id: str,
        *,
        operation_service: Any,
        run_project_command: ProjectCommand,
        command_succeeded: Optional[CommandSucceeded] = None,
        transaction_store: Optional[PackageTransactionStore] = None,
    ) -> Dict[str, Any]:
        normalized_id = str(package_id).strip()
        if not normalized_id:
            return {"ok": False, "error": "missing_package_id", "operation": {"ok": False}}
        store, store_error = _transaction_store(transaction_store, operation_service)
        if store_error:
            return {"ok": False, "error": "transaction_store_unavailable", "transaction_error": store_error, "operation": {}}
        snapshot = _capture_local_snapshot(operation_service, normalized_id)
        if not snapshot.get("ok"):
            return {"ok": False, "error": str(snapshot.get("error", "artifact_snapshot_failed")), "operation": {}}
        receipt, receipt_error = _begin_receipt(
            store, "uninstall", normalized_id, local_snapshot=snapshot
        )
        if receipt_error:
            return {"ok": False, "error": "transaction_begin_failed", "transaction_error": receipt_error, "operation": {}}
        command = _plain_mapping(run_project_command("plugin.uninstall", normalized_id, None))
        command_ok = (command_succeeded or _command_succeeded)(command)
        if not command_ok:
            failed, advance_error = _advance_receipt(
                store,
                receipt,
                "failed",
                details={"reason": "project_uninstall_failed"},
                project_command=command,
            )
            return {
                "ok": False,
                "operation": {},
                "command": command,
                "command_ok": False,
                "operation_ok": False,
                "operation_skipped": True,
                "error": "project_command_failed",
                **_receipt_fields(failed or receipt),
                "transaction_error": advance_error,
            }
        project_applied, advance_error = _advance_receipt(
            store,
            receipt,
            "project_applied",
            details={"command": "plugin.uninstall"},
            project_command=command,
        )
        if advance_error:
            return {
                "ok": False,
                "operation": {},
                "command": command,
                "command_ok": True,
                "operation_ok": False,
                "operation_skipped": True,
                "error": "transaction_project_record_failed",
                **_receipt_fields(receipt),
                "transaction_error": advance_error,
            }
        operation = _remove_local_artifact(operation_service, normalized_id, snapshot)
        operation_ok = bool(operation.get("ok") or operation.get("error") == "not_installed")
        if not operation_ok:
            failed, record_error = _advance_receipt(
                store,
                project_applied,
                "failed_recoverable",
                details={"reason": "local_uninstall_failed"},
                local_result=operation,
                recovery={"action": "retry_local_uninstall"},
            )
            return {
                "ok": False,
                "operation": operation,
                "command": command,
                "command_ok": True,
                "operation_ok": False,
                "operation_skipped": False,
                "error": "local_operation_failed",
                **_receipt_fields(failed or project_applied),
                "transaction_error": record_error,
            }
        local_applied, advance_error = _advance_receipt(
            store, project_applied, "local_applied", details={}, local_result=operation
        )
        if advance_error:
            return {
                "ok": False,
                "operation": operation,
                "command": command,
                "command_ok": True,
                "operation_ok": True,
                "operation_skipped": False,
                "error": "transaction_local_record_failed",
                **_receipt_fields(project_applied),
                "transaction_error": advance_error,
            }
        completed, advance_error = _advance_receipt(store, local_applied, "completed", details={})
        return {
            "ok": not advance_error,
            "operation": operation,
            "command": command,
            "command_ok": True,
            "operation_ok": True,
            "operation_skipped": False,
            "error": "transaction_complete_failed" if advance_error else "",
            **_receipt_fields(completed or local_applied),
            "transaction_error": advance_error,
        }

    @staticmethod
    def list_recoverable_transactions(transaction_store: PackageTransactionStore) -> Dict[str, Any]:
        try:
            return transaction_store.list_recoverable()
        except PackageTransactionError as exc:
            return {"ok": False, "records": [], "malformed": [], "error": exc.code, "details": dict(exc.details)}

    @staticmethod
    @_package_transaction_mutation("package.transaction.recovery.resolve")
    def recover_transaction(
        transaction_id: str,
        *,
        transaction_store: PackageTransactionStore,
        operation_service: Any,
        run_project_command: ProjectCommand,
        command_succeeded: Optional[CommandSucceeded] = None,
    ) -> Dict[str, Any]:
        try:
            receipt = transaction_store.read(transaction_id)
        except PackageTransactionError as exc:
            return {"ok": False, "error": exc.code, "transaction_id": str(transaction_id)}
        action = str(receipt.get("action", ""))
        state = str(receipt.get("state", ""))
        package_id = str(receipt.get("package_id", ""))
        if state == "prepared":
            return {
                "ok": False,
                "error": "transaction_state_ambiguous",
                **_receipt_fields(receipt),
                "recovery": {"action": "manual_review", "reason": "prepared_receipt_has_no_committed_side_effect_record"},
            }
        if state not in {"local_applied", "project_applied", "failed_recoverable"}:
            return {"ok": False, "error": "transaction_not_recoverable", **_receipt_fields(receipt)}
        is_success = command_succeeded or _command_succeeded
        if action == "install":
            if state == "project_applied":
                completed, error = _advance_receipt(transaction_store, receipt, "completed", details={"recovery": "finalize"})
                return {"ok": not error, **_receipt_fields(completed or receipt), "transaction_error": error}
            payload = _plain_mapping(receipt.get("payload"))
            artifact_path = str(payload.get("path", ""))
            if artifact_path and not _artifact_is_available(operation_service, package_id, artifact_path):
                failed, error = _advance_receipt(
                    transaction_store,
                    receipt,
                    "failed_recoverable",
                    details={"reason": "artifact_missing_before_project_retry"},
                    recovery={"action": "manual_review", "artifact_path": artifact_path},
                )
                return {"ok": False, "error": "artifact_missing", **_receipt_fields(failed or receipt), "transaction_error": error}
            command = _plain_mapping(run_project_command("plugin.install", package_id, payload))
            if not is_success(command):
                failed, error = _advance_receipt(
                    transaction_store,
                    receipt,
                    "failed_recoverable",
                    details={"reason": "project_install_retry_failed"},
                    project_command=command,
                    recovery={"action": "retry_project_install", "artifact_path": artifact_path},
                )
                return {"ok": False, "error": "project_command_failed", "command": command, **_receipt_fields(failed or receipt), "transaction_error": error}
            project_applied, error = _advance_receipt(
                transaction_store, receipt, "project_applied", details={"recovery": "retry_project_install"}, project_command=command
            )
            if error:
                return {"ok": False, "error": "transaction_project_record_failed", **_receipt_fields(receipt), "transaction_error": error}
            completed, error = _advance_receipt(transaction_store, project_applied, "completed", details={"recovery": "complete"})
            return {"ok": not error, "command": command, **_receipt_fields(completed or project_applied), "transaction_error": error}
        if action == "uninstall":
            if state not in {"project_applied", "failed_recoverable"}:
                return {"ok": False, "error": "transaction_not_recoverable", **_receipt_fields(receipt)}
            snapshot = _plain_mapping(receipt.get("local_snapshot"))
            operation = _remove_local_artifact(operation_service, package_id, snapshot)
            if not operation.get("ok"):
                failed, error = _advance_receipt(
                    transaction_store,
                    receipt,
                    "failed_recoverable",
                    details={"reason": "local_uninstall_retry_failed"},
                    local_result=operation,
                    recovery={"action": "retry_local_uninstall"},
                )
                return {"ok": False, "error": "local_operation_failed", "operation": operation, **_receipt_fields(failed or receipt), "transaction_error": error}
            local_applied, error = _advance_receipt(
                transaction_store, receipt, "local_applied", details={"recovery": "retry_local_uninstall"}, local_result=operation
            )
            if error:
                return {"ok": False, "error": "transaction_local_record_failed", "operation": operation, **_receipt_fields(receipt), "transaction_error": error}
            completed, error = _advance_receipt(transaction_store, local_applied, "completed", details={"recovery": "complete"})
            return {"ok": not error, "operation": operation, **_receipt_fields(completed or local_applied), "transaction_error": error}
        return {"ok": False, "error": "transaction_invalid_action", **_receipt_fields(receipt)}

    @classmethod
    def align_manifest_packages(
        cls,
        missing_ids: List[str],
        packages: List[Dict[str, Any]],
        *,
        get_enabled_ids: Callable[[], Set[str]],
        operation_service: Any,
        run_project_command: ProjectCommand,
        downloader: Any,
        mode: str,
        command_succeeded: Optional[CommandSucceeded] = None,
        transaction_store: Optional[PackageTransactionStore] = None,
    ) -> Dict[str, Any]:
        targets = _unique_package_ids(missing_ids)
        if not targets:
            return {
                "ok": False,
                "changed": False,
                "install_results": [],
                "enable": {"ok": False, "results": []},
                "resolved_ids": [],
                "unresolved": [],
            }
        lookup = {str(package.get("id", "")): package for package in packages}
        enabled_ids = set(get_enabled_ids())
        install_results: List[Dict[str, Any]] = []
        ready_to_enable: List[str] = []
        unresolved: List[Dict[str, str]] = []
        changed = False
        for package_id in targets:
            package = lookup.get(package_id)
            if not isinstance(package, dict):
                unresolved.append({"package_id": package_id, "reason": "package_not_in_catalog"})
                continue
            needs_artifact_install = str(package.get("status", "")).lower() != "builtin" and bool(package.get("artifact"))
            if needs_artifact_install:
                result = cls.install_package(
                    package,
                    packages,
                    enabled_ids,
                    operation_service=operation_service,
                    run_project_command=run_project_command,
                    downloader=downloader,
                    mode=mode,
                    command_succeeded=command_succeeded,
                    transaction_store=transaction_store,
                )
                install_results.append({"package_id": package_id, **result})
                if not result.get("ok"):
                    reason = "project_install_failed" if result.get("command_ok") is False and result.get("operation", {}).get("ok") else "artifact_install_failed"
                    unresolved.append({"package_id": package_id, "reason": reason})
                    continue
                changed = True
                enabled_ids = set(get_enabled_ids())
            ready_to_enable.append(package_id)
        enable = cls.enable_packages(ready_to_enable, run_project_command, command_succeeded=command_succeeded)
        for package_id in enable["failed_ids"]:
            unresolved.append({"package_id": package_id, "reason": "project_enable_failed"})
        changed = changed or bool(enable["changed"])
        resolved_ids = [
            package_id for package_id in targets
            if not any(item["package_id"] == package_id for item in unresolved)
        ]
        return {
            "ok": not unresolved and len(resolved_ids) == len(targets),
            "changed": changed,
            "install_results": install_results,
            "enable": enable,
            "resolved_ids": resolved_ids,
            "unresolved": unresolved,
        }
