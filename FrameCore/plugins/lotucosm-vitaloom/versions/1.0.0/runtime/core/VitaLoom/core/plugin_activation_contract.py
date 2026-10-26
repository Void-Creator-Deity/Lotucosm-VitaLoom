"""Qt-free contract authority for plugin activation context metadata.

The L1 engine plugin owns this contract for official, user, and Project World
extension metadata.  It deliberately contains no Host, Qt, or lifecycle code.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

DEFAULT_ACTIVATION_CONTEXT = "legacy_ui"
LEGACY_UI_ACTIVATION_CONTEXT = "legacy_ui"
RUNTIME_ACTIVATION_CONTEXT = "runtime"
SUPPORTED_ACTIVATION_CONTEXTS = frozenset(
    {LEGACY_UI_ACTIVATION_CONTEXT, RUNTIME_ACTIVATION_CONTEXT}
)


class PluginActivationContractError(ValueError):
    """Stable, JSON-safe contract failure before import or activation."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = str(code)
        self.message = str(message)
        self.details = {
            str(key): value
            for key, value in (details or {}).items()
        }


@dataclass(frozen=True, slots=True)
class PluginActivationMetadata:
    """The normalized activation kind and its provenance."""

    kind: str
    explicit: bool
    source: str = "default"

    def to_dict(self) -> dict[str, Any]:
        return {
            "activation_context": self.kind,
            "activation_context_explicit": self.explicit,
            "activation_context_source": self.source,
        }


def _details(*, plugin_id: str, source: str) -> dict[str, str]:
    return {
        "plugin_id": str(plugin_id or ""),
        "source": str(source or ""),
    }


def parse_plugin_activation_metadata(
    metadata: Mapping[str, Any],
    *,
    plugin_id: str = "",
    source: str = "",
) -> PluginActivationMetadata:
    """Normalize one plugin metadata mapping without inferring its context.

    Missing ``activation_context`` is the intentional compatibility path and
    resolves to ``legacy_ui``.  A present value must be a string and one of the
    two contract kinds; booleans and numeric values are rejected explicitly.
    """

    if not isinstance(metadata, Mapping):
        raise PluginActivationContractError(
            "activation_context_metadata_invalid",
            "plugin metadata must be an object",
            details=_details(plugin_id=plugin_id, source=source),
        )
    if "activation_context" not in metadata:
        return PluginActivationMetadata(
            kind=DEFAULT_ACTIVATION_CONTEXT,
            explicit=False,
            source="default",
        )

    value = metadata.get("activation_context")
    if not isinstance(value, str) or isinstance(value, bool):
        raise PluginActivationContractError(
            "activation_context_invalid_type",
            "activation_context must be a string",
            details={
                **_details(plugin_id=plugin_id, source=source),
                "value_type": type(value).__name__,
            },
        )
    kind = value.strip()
    if kind not in SUPPORTED_ACTIVATION_CONTEXTS:
        raise PluginActivationContractError(
            "activation_context_unknown",
            f"unsupported activation_context {value!r}",
            details={
                **_details(plugin_id=plugin_id, source=source),
                "value": value,
                "supported": sorted(SUPPORTED_ACTIVATION_CONTEXTS),
            },
        )
    return PluginActivationMetadata(kind=kind, explicit=True, source="declared")


def validate_plugin_activation_context_pair(
    manifest: PluginActivationMetadata,
    code: PluginActivationMetadata,
) -> PluginActivationMetadata:
    """Require manifest and imported code to resolve to the same context kind."""

    if manifest.kind != code.kind:
        raise PluginActivationContractError(
            "activation_context_manifest_code_mismatch",
            "manifest/code activation_context values do not match",
            details={
                "manifest_activation_context": manifest.kind,
                "code_activation_context": code.kind,
            },
        )
    return code


def contract_diagnostic(
    error: PluginActivationContractError,
    *,
    plugin_id: str = "",
    source: str = "",
) -> dict[str, Any]:
    """Return a deterministic diagnostic payload for lifecycle/report Modules."""

    return {
        "level": "error",
        "code": error.code,
        "message": error.message,
        "plugin_id": str(plugin_id or error.details.get("plugin_id", "")),
        "source": str(source or error.details.get("source", "")),
        "details": dict(error.details),
    }
