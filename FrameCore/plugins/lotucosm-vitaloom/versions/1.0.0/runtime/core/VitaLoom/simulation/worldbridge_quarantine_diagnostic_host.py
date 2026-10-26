# -*- coding: utf-8 -*-
"""Query-only host seam for WorldBridge quarantine diagnostic visibility."""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from core.VitaLoom.core.service_keys import WORLDBRIDGE_QUARANTINE_DIAGNOSTIC_HOST


HOST_AUTHORITY = "worldbridge_quarantine_diagnostic_host"
UNAVAILABLE_REASON = "worldbridge_quarantine_diagnostic_host_unavailable"


@runtime_checkable
class IWorldBridgeQuarantineDiagnosticHost(Protocol):
    """Command-facing diagnostic query; never exposes the UI adapter itself."""

    def query_worldbridge_quarantine_diagnostic(self) -> dict[str, Any]: ...


@runtime_checkable
class IWorldBridgeQuarantineLifecycleCorrelationHost(Protocol):
    """Optional E241 extension; it must not invalidate the E240 host seam."""

    def query_worldbridge_quarantine_lifecycle_correlation(self) -> dict[str, Any]: ...


class _NullWorldBridgeQuarantineDiagnosticHost:
    def query_worldbridge_quarantine_diagnostic(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "status": "unavailable",
            "scope": "current_runtime_worldbridge_failure_quarantine",
            "authority": HOST_AUTHORITY,
            "read_only": True,
            "availability": "unavailable",
            "current_runtime_quarantined": None,
            "reason": UNAVAILABLE_REASON,
            "negative_capabilities": {
                "may_clear_quarantine": False,
                "may_retry_same_runtime_handoff": False,
                "may_construct_or_reuse_pond": False,
                "may_call_sr_ps_bridge_mutator": False,
                "rollback_performed": False,
                "compensation_performed": False,
                "in_place_restore": False,
                "replay_admitted": False,
                "default_ready": False,
            },
        }


    def query_worldbridge_quarantine_lifecycle_correlation(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "status": "unavailable",
            "scope": "same_adapter_worldbridge_quarantine_lifecycle_evidence",
            "authority": HOST_AUTHORITY,
            "read_only": True,
            "availability": "unavailable",
            "current_runtime_quarantined": None,
            "reason": UNAVAILABLE_REASON,
            "negative_capabilities": {
                "may_clear_quarantine": False,
                "may_retry_same_runtime_handoff": False,
                "may_construct_or_reuse_pond": False,
                "may_call_sr_ps_bridge_mutator": False,
                "fresh_boundary_is_state_recovery": False,
                "rollback_performed": False,
                "compensation_performed": False,
                "in_place_restore": False,
                "replay_admitted": False,
                "cross_adapter_lifecycle_correlation": False,
                "default_ready": False,
            },
        }


def get_worldbridge_quarantine_diagnostic_host(
    source: Any = None,
) -> IWorldBridgeQuarantineDiagnosticHost:
    """Resolve only a composed capability; never create or inspect a runtime."""
    from core.VitaLoom.core.runtime_capability_registry import (
        resolve_runtime_capability_registry,
    )

    registry = resolve_runtime_capability_registry(source)
    if registry is None and source is None:
        try:
            from core.VitaLoom.core.editor_context import get_existing_editor_context

            registry = resolve_runtime_capability_registry(get_existing_editor_context())
        except Exception:
            registry = None
    host = registry.get(WORLDBRIDGE_QUARANTINE_DIAGNOSTIC_HOST) if registry is not None else None
    if isinstance(host, IWorldBridgeQuarantineDiagnosticHost):
        return host
    return _NullWorldBridgeQuarantineDiagnosticHost()


def get_worldbridge_quarantine_lifecycle_host(
    source: Any = None,
) -> IWorldBridgeQuarantineLifecycleCorrelationHost:
    """Resolve the optional E241 lifecycle extension without breaking E240 hosts."""
    from core.VitaLoom.core.runtime_capability_registry import (
        resolve_runtime_capability_registry,
    )

    registry = resolve_runtime_capability_registry(source)
    if registry is None and source is None:
        try:
            from core.VitaLoom.core.editor_context import get_existing_editor_context

            registry = resolve_runtime_capability_registry(get_existing_editor_context())
        except Exception:
            registry = None
    host = registry.get(WORLDBRIDGE_QUARANTINE_DIAGNOSTIC_HOST) if registry is not None else None
    if isinstance(host, IWorldBridgeQuarantineLifecycleCorrelationHost):
        return host
    return _NullWorldBridgeQuarantineDiagnosticHost()


__all__ = [
    "HOST_AUTHORITY",
    "IWorldBridgeQuarantineDiagnosticHost",
    "IWorldBridgeQuarantineLifecycleCorrelationHost",
    "UNAVAILABLE_REASON",
    "get_worldbridge_quarantine_diagnostic_host",
    "get_worldbridge_quarantine_lifecycle_host",
]
