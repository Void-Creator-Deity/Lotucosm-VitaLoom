# -*- coding: utf-8
"""Concrete opt-in checkpoint adapters for the existing GameViewport owners.

The module is Qt-free at import time and uses duck-typed viewport access so
the engine contract remains independent from the UI host.  It restores only
an existing active runtime; it never creates a scene, Pond, entity, or bridge
organism.
"""

from __future__ import annotations

import copy
import hashlib
import json
import random
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np

from .world_bridge_live_checkpoint import (
    LiveCheckpointAdapters,
    WorldBridgeTransactionCapture,
    WorldBridgeTransactionCaptureError,
)


def create_game_viewport_live_checkpoint_adapters(viewport: Any) -> LiveCheckpointAdapters:
    """Build explicit adapters around one already-running GameViewport.

    The caller still chooses when to pass these adapters to the checkpoint
    coordinator.  Default GameViewport ticks do not call this function.
    """
    if viewport is None:
        raise TypeError("viewport is required")
    from .world_bridge_mutation_authority import validate_process_owner_binding

    def validate_owner_binding(expected: Mapping[str, Any]) -> dict[str, Any]:
        current = _capture_process_owner_binding(viewport)
        return validate_process_owner_binding(expected, current)

    return LiveCheckpointAdapters(
        capture_sr=lambda: _capture_sr(viewport),
        restore_sr=lambda state: _restore_sr(viewport, state),
        capture_ps=lambda: _capture_ps(viewport),
        restore_ps=lambda state: _restore_ps(viewport, state),
        capture_live_ps=lambda: _capture_live_ps(viewport),
        capture_transaction_state=lambda: _capture_transaction_state(viewport),
        capture_transaction_snapshot=lambda: _capture_transaction_snapshot(viewport),
        capture_handoff_transaction_snapshot=lambda: _capture_handoff_transaction_snapshot(viewport),
        capture_legacy_transaction_snapshot=lambda: _capture_legacy_transaction_snapshot(viewport),
        capture_tick_evidence=lambda: _capture_restore_tick_evidence(viewport),
        restore_live_ps=lambda state: _restore_live_ps(viewport, state),
        capture_bridge=lambda: _capture_bridge(viewport),
        restore_bridge=lambda links: _restore_bridge(viewport, links),
        capture_input=lambda: _capture_input(viewport),
        restore_input=lambda state: _restore_input(viewport, state),
        capture_randomness=lambda: _capture_randomness(viewport),
        restore_randomness=lambda state: _restore_randomness(viewport, state),
        capture_lifecycle=lambda: _capture_lifecycle(viewport),
        restore_lifecycle=lambda state: _restore_lifecycle(viewport, state),
        capture_topology=lambda: _capture_topology_owner_state(viewport),
        restore_topology=lambda state: _restore_topology_owner_state(viewport, state),
        compensate_topology=lambda state: _restore_topology_owner_state(viewport, state),
        compensate_sr=lambda state: _restore_sr(viewport, state),
        compensate_ps=lambda state: _compensate_ps(viewport, state),
        compensate_bridge=lambda links: _restore_bridge(viewport, links),
        compensate_input=lambda state: _restore_input(viewport, state),
        compensate_randomness=lambda state: _restore_randomness(viewport, state),
        compensate_lifecycle=lambda state: _restore_lifecycle(viewport, state),
        capture_tick_authority=lambda: _capture_tick_authority_snapshot(viewport),
        restore_tick_authority=lambda state: _restore_tick_authority_snapshot(
            viewport, state
        ),
        compensate_tick_authority=lambda state: _restore_tick_authority_snapshot(
            viewport, state
        ),
        validate_tick_authority=lambda state: _validate_tick_authority_snapshot(
            viewport, state
        ),
        capture_owner_binding=lambda: _capture_process_owner_binding(viewport),
        validate_owner_binding=validate_owner_binding,
    )


def build_game_viewport_live_checkpoint_adapter_contract() -> dict[str, Any]:
    """Describe the concrete owner boundary without claiming admission."""
    return {
        "schema_version": 1,
        "status": "worldbridge_live_checkpoint_adapter",
        "qt_free_import": True,
        "owner_scope": [
            "active_sr_runtime_epoch",
            "existing_unified_pond",
            "existing_bridge_identity_links",
            "caller_owned_sr_rng",
            "sr_local_input_buffer",
            "viewport_lifecycle_flags_and_scene_time",
            "sr_topology_and_membrane_component_owner",
            "python_process_global_random_state",
            "numpy_legacy_global_randomstate",
            "opt_in_named_python_and_numpy_stream_context",
        "process_local_owner_binding",
        ],
        "global_rng_restore_is_opt_in": True,
        "global_rng_restore_thread_atomic": False,
        "creates_live_objects": False,
        "default_tick_attached": False,
        "fresh_instance_restore": False,
        "owner_binding_validated": True,
        "owner_drift_fail_closed": True,
        "transaction_owner_evidence_fenced": True,
        "transaction_owner_snapshot_count": 1,
        "transaction_owner_evidence_probe_rounds": 2,
        "transaction_capture_uses_combined_owner_callback": True,
        "transaction_ps_capture_digest_fenced": True,
        "completed_tick_binding_required": True,
        "tick_binding_stable_across_capture": True,
        "tick_authority_capture_restore": True,
        "tick_authority_stable_across_capture": True,
        "tick_authority_fail_closed": True,
        "active_tick_capture_rejected": True,
        "active_tick_handoff_scope_supported": True,
        "legacy_checkpoint_without_completed_tick_supported": True,
        "atomic_checkpoint": False,
        "replay_admitted": False,
        "default_ready": False,
        "contract_valid": True,
    }


def _capture_process_owner_binding(viewport: Any) -> dict[str, Any]:
    """Capture the roots that a single live checkpoint operation may address."""
    from .world_bridge_mutation_authority import (
        OWNER_ROOTS,
        capture_process_owner_binding,
    )

    pond = getattr(viewport, "_unified_pond", None)
    roots = {
        "viewport_host": viewport,
        # The entity list is replaceable simulation state (for example, the
        # tick removes dead entities). Its stable owner is the viewport that
        # hosts the SR registry, while per-entity identities are bound below.
        "sr_runtime_entities": viewport,
        "ps_pond": pond,
        "sr_runtime_rng": getattr(viewport, "_sr_runtime_rng", None),
        "ps_pond_rng": getattr(pond, "randomness_rng", None) if pond is not None else None,
        "input_sequence": getattr(viewport, "_worldbridge_input_sequence", None),
        "sr_identity_source": getattr(viewport, "_sr_identity_source", None),
        "ps_identity_source": getattr(pond, "identity_source", None) if pond is not None else None,
        "sr_physics_world": getattr(viewport, "_sr_physics_world", None),
    }
    if set(roots) != set(OWNER_ROOTS):
        raise RuntimeError("live checkpoint owner root inventory is incomplete")
    return capture_process_owner_binding(
        runtime_epoch=getattr(viewport, "_sr_runtime_epoch", None),
        roots=roots,
        sr_entities=tuple(getattr(viewport, "scene_runtime_entities", ()) or ()),
    )


def _require_active(viewport: Any) -> None:
    if not bool(getattr(viewport, "_using_scene_runtime", False)):
        raise RuntimeError("live checkpoint requires active SR scene runtime")
    if getattr(viewport, "_sr_runtime_epoch", None) is None:
        raise RuntimeError("live checkpoint requires active SR runtime epoch")
    if not bool(getattr(viewport, "_unified_pond_mode", False)):
        raise RuntimeError("live checkpoint requires unified Pond mode")
    if getattr(viewport, "_unified_pond", None) is None:
        raise RuntimeError("live checkpoint requires an existing unified Pond")


def _capture_sr(viewport: Any) -> dict[str, Any]:
    _require_active(viewport)
    from core.VitaLoom.simulation.sr_runtime_structure_parity import (
        build_sr_runtime_structure_fingerprint,
    )

    envelope = copy.deepcopy(viewport.capture_sr_runtime_restore_envelope())
    structure = build_sr_runtime_structure_fingerprint(
        entities=viewport.scene_runtime_entities,
        scene_path=viewport._sr_runtime_scene_path,
        structural_edges=getattr(viewport, "_sr_structural_edges", ()),
        signal_edges=getattr(viewport, "_sr_signal_edges", ()),
        membrane_attach=getattr(viewport, "_sr_membrane_attach", {}),
        membrane_template=getattr(viewport, "_sr_membrane_template", {}),
    )
    physics_backend = _capture_physics_backend(viewport)
    from .world_bridge_native_entropy_audit import build_native_backend_selection_evidence

    backend_selection = build_native_backend_selection_evidence(
        physics_backend,
        requested_backend=str(getattr(viewport, "_sr2d_backend_request", "auto")),
    )
    return {
        "runtime_restore_envelope": envelope,
        "structure_fingerprint": structure,
        "topology_receipt": _capture_dynamic_topology_receipt(viewport, structure),
        "physics_backend": physics_backend,
        "native_backend_selection": backend_selection,
        "script_entropy_audits": copy.deepcopy(
            list(getattr(viewport, "_sr_script_entropy_audits", ()))
        ),
        "script_entropy_receipts": copy.deepcopy(
            list(getattr(viewport, "_sr_script_entropy_receipts", ()))
        ),
    }


def _capture_dynamic_topology_receipt(
    viewport: Any, structure: Mapping[str, Any]
) -> dict[str, Any]:
    """Bind the live structure snapshot to the existing component evidence.

    The component artifact records dynamic spawn generations when available;
    it is diagnostic evidence only and does not grant live topology authority.
    """
    from .world_bridge_dynamic_topology_receipt import (
        build_worldbridge_dynamic_topology_receipt,
    )

    artifact = getattr(viewport, "_worldbridge_component_identity_artifact", None)
    if artifact is not None:
        from .world_bridge_component_identity_artifact import (
            validate_worldbridge_component_identity_artifact,
        )

        validation = validate_worldbridge_component_identity_artifact(artifact)
        if not validation["valid"]:
            raise RuntimeError(
                "component identity artifact is invalid: "
                + ",".join(validation["errors"])
            )
        records = artifact["receipts"]
        generations = [
            record["generation"]
            for record in records
            if isinstance(record, Mapping)
            and isinstance(record.get("generation"), int)
            and not isinstance(record.get("generation"), bool)
            and record["generation"] >= 0
        ]
        generation = max(generations, default=0)
    else:
        generation = 0

    if not isinstance(structure, Mapping):
        raise TypeError("structure fingerprint must be a mapping")
    return build_worldbridge_dynamic_topology_receipt(
        runtime_epoch=str(viewport._sr_runtime_epoch),
        generation=generation,
        structure_fingerprint=structure,
        component_identity_artifact=artifact,
    )


def _restore_sr(viewport: Any, state: Mapping[str, Any]) -> None:
    _require_active(viewport)
    if not isinstance(state, Mapping):
        raise TypeError("SR checkpoint state must be a mapping")
    envelope = state.get("runtime_restore_envelope")
    expected = state.get("structure_fingerprint")
    topology_receipt = state.get("topology_receipt")
    expected_audits = state.get("script_entropy_audits", [])
    expected_receipts = state.get("script_entropy_receipts")
    expected_backend = state.get("physics_backend")
    expected_backend_selection = state.get("native_backend_selection")
    if (
        not isinstance(envelope, Mapping)
        or not isinstance(expected, Mapping)
        or not isinstance(expected_audits, list)
        or not isinstance(expected_backend, Mapping)
        or not isinstance(expected_backend_selection, Mapping)
    ):
        raise ValueError("SR checkpoint structure metadata is missing")
    if topology_receipt is not None:
        from .world_bridge_dynamic_topology_receipt import validate_worldbridge_dynamic_topology_receipt
        receipt_validation = validate_worldbridge_dynamic_topology_receipt(
            topology_receipt, runtime_epoch=str(viewport._sr_runtime_epoch)
        )
        if receipt_validation != {"valid": True, "errors": []}:
            raise RuntimeError("dynamic topology receipt rejected: " + ",".join(receipt_validation["errors"]))
        if topology_receipt.get("structure_fingerprint") != expected.get("fingerprint"):
            raise RuntimeError("dynamic topology receipt structure mismatch")
        receipt_artifact = topology_receipt.get("component_identity_artifact")
        current_artifact = getattr(
            viewport, "_worldbridge_component_identity_artifact", None
        )
        if receipt_artifact != current_artifact:
            raise RuntimeError("dynamic topology receipt component artifact mismatch")
    from core.VitaLoom.simulation.sr_runtime_structure_parity import (
        build_sr_runtime_structure_fingerprint,
        compare_sr_runtime_structure_fingerprints,
    )

    topology = envelope.get("topology")
    if topology is not None and not isinstance(topology, Mapping):
        raise ValueError("SR checkpoint topology owner state is invalid")
    topology = topology if isinstance(topology, Mapping) else {}
    current = build_sr_runtime_structure_fingerprint(
        entities=viewport.scene_runtime_entities,
        scene_path=viewport._sr_runtime_scene_path,
        structural_edges=topology.get("structural_edges", getattr(viewport, "_sr_structural_edges", ())),
        signal_edges=topology.get("signal_edges", getattr(viewport, "_sr_signal_edges", ())),
        membrane_attach=topology.get("membrane_attach", getattr(viewport, "_sr_membrane_attach", {})),
        membrane_template=topology.get("membrane_template", getattr(viewport, "_sr_membrane_template", {})),
    )
    comparison = compare_sr_runtime_structure_fingerprints(expected, current)
    if comparison.get("equal") is not True:
        raise RuntimeError("SR runtime structure fingerprint mismatch")
    current_audits = list(getattr(viewport, "_sr_script_entropy_audits", ()))
    if current_audits != expected_audits:
        raise RuntimeError("SR script entropy audit mismatch")
    if expected_receipts is not None:
        if not isinstance(expected_receipts, list):
            raise ValueError("SR script entropy receipts must be a list")
        current_receipts = list(getattr(viewport, "_sr_script_entropy_receipts", ()))
        from core.Lotucosm.script_entropy_audit import diagnose_script_entropy_admission

        owner_digest_builder = getattr(viewport, "_script_owner_registry_digest", None)
        admission = diagnose_script_entropy_admission(
            current_audits,
            current_receipts,
            owner_family=type(getattr(viewport, "_sr_runtime_rng", None)).__name__,
            runtime_epoch=str(viewport._sr_runtime_epoch),
            owner_stream_name="sr.runtime" if callable(owner_digest_builder) else None,
            owner_registry_digest=(owner_digest_builder() if callable(owner_digest_builder) else None),
        )
        viewport._sr_script_entropy_admission_diagnostic = copy.deepcopy(admission)
        if not admission["admitted"] or current_receipts != expected_receipts:
            reasons = ",".join(admission["reasons"]) or "checkpoint_receipt_mismatch"
            raise RuntimeError(f"SR script entropy receipt admission failed: {reasons}")
    current_backend = _capture_physics_backend(viewport)
    if dict(current_backend) != dict(expected_backend):
        raise RuntimeError("SR2D backend capability mismatch")
    from .world_bridge_native_entropy_audit import (
        build_native_backend_selection_evidence,
        validate_native_backend_selection_evidence,
    )

    current_backend_selection = build_native_backend_selection_evidence(
        current_backend,
        requested_backend=str(getattr(viewport, "_sr2d_backend_request", "auto")),
    )
    if dict(current_backend_selection) != dict(expected_backend_selection):
        raise RuntimeError("SR2D backend selection evidence mismatch")
    selection_validation = validate_native_backend_selection_evidence(
        expected_backend_selection,
        current_backend,
        requested_backend=str(getattr(viewport, "_sr2d_backend_request", "auto")),
    )
    if selection_validation != {"valid": True, "errors": []}:
        raise RuntimeError(
            "SR2D backend selection is not admissible: "
            + ", ".join(selection_validation["errors"])
        )
    viewport.restore_sr_runtime_restore_envelope(copy.deepcopy(dict(envelope)))
    restored = build_sr_runtime_structure_fingerprint(
        entities=viewport.scene_runtime_entities,
        scene_path=viewport._sr_runtime_scene_path,
        structural_edges=getattr(viewport, "_sr_structural_edges", ()),
        signal_edges=getattr(viewport, "_sr_signal_edges", ()),
        membrane_attach=getattr(viewport, "_sr_membrane_attach", {}),
        membrane_template=getattr(viewport, "_sr_membrane_template", {}),
    )
    restored_comparison = compare_sr_runtime_structure_fingerprints(expected, restored)
    if restored_comparison.get("equal") is not True:
        raise RuntimeError("restored SR runtime structure fingerprint mismatch")


def _capture_topology_owner_state(viewport: Any) -> dict[str, Any]:
    """Capture the dedicated SR topology/membrane owner surface.

    The viewport owns edges, membrane attachments/templates and spawn sequence
    as one graph.  This adapter deliberately fails closed when the host does
    not expose the contract instead of silently substituting a read-only
    projection or an empty graph.
    """
    capture = getattr(viewport, "capture_sr_topology_owner_state", None)
    if not callable(capture):
        raise RuntimeError("sr_topology_owner_capture_contract_unavailable")
    state = capture()
    if not isinstance(state, Mapping):
        raise TypeError("sr_topology_owner_state must be a mapping")
    return copy.deepcopy(dict(state))


def _restore_topology_owner_state(viewport: Any, state: Mapping[str, Any]) -> None:
    """Restore the dedicated SR topology/membrane owner surface."""
    restore = getattr(viewport, "restore_sr_topology_owner_state", None)
    if not callable(restore):
        raise RuntimeError("sr_topology_owner_restore_contract_unavailable")
    if not isinstance(state, Mapping):
        raise TypeError("sr_topology_owner_state must be a mapping")
    restore(copy.deepcopy(dict(state)))


def _capture_physics_backend(viewport: Any) -> dict[str, Any]:
    physics_world = getattr(viewport, "_sr_physics_world", None)
    if physics_world is None or not callable(getattr(physics_world, "backend_capability", None)):
        return {
            "schema_version": 1,
            "backend_id": "unavailable",
            "adapter_class": None,
            "module_name": None,
            "artifact_sha256": None,
            "artifact_provenance": "unavailable",
            "kernel_symbol": None,
            "abi_contract": "unknown",
            "abi_version_required": None,
            "abi_version_exported": None,
            "input_contract": None,
            "native_pvaec_enabled": False,
            "python_fallback_for_game_or_springs": None,
        }
    capability = physics_world.backend_capability()
    if not isinstance(capability, Mapping):
        raise RuntimeError("SR2D backend capability must be a mapping")
    return copy.deepcopy(dict(capability))


# Side overlays carry owner-graph metadata that the portable Pond JSON
# serializer cannot represent (executable script refs, lifecycle owners).
# They are intentionally excluded from any comparison against a freshly
# serialized canonical PS payload, which never contains them.
PS_SIDE_OVERLAY_KEYS = (
    "worldbridge_organism_lifecycle",
    "worldbridge_organism_scripts",
    "worldbridge_organism_hierarchy",
)


def canonical_ps_serializer_projection(state: Any) -> dict[str, Any]:
    """Project a checkpoint ``ps_state`` onto portable serializer-owned keys.

    A checkpoint ``ps_state`` is the portable Pond JSON plus side overlays
    for owners the serializer drops.  Fresh-restore parity compares against
    a freshly serialized Pond, so the overlays must be removed before an
    equality check or every checkpoint would report a false parity break.
    """
    if not isinstance(state, Mapping):
        raise TypeError("ps_state must be a mapping")
    return {
        key: copy.deepcopy(value)
        for key, value in state.items()
        if key not in PS_SIDE_OVERLAY_KEYS
    }


_PS_SCRIPTS_OVERLAY_KEY = "worldbridge_organism_scripts"
_PS_SCRIPTS_SCHEMA_VERSION = 1


def _capture_ps_organism_scripts(pond: Any) -> dict[str, Any]:
    """Record the PS executable-script owner graph as a fail-closed digest.

    ``PondSerializer`` never carries live script objects, and
    ``restore_serialized_state_in_place`` rebuilds organism objects, so any
    script set attached before capture would be silently dropped on restore.
    Scripts are executable objects bound to a caller-owned ``randomness_rng``;
    they cannot be round-tripped through canonical JSON.  The overlay therefore
    records identity + owner family only, and restore rejects a changed live
    script graph instead of silently discarding it.
    """
    organisms = getattr(pond, "organisms", None)
    if not isinstance(organisms, Mapping):
        raise RuntimeError("PS pond organism registry unavailable")
    entries: dict[str, Any] = {}
    for organism_id, organism in organisms.items():
        scripts = getattr(organism, "scripts", None)
        if not scripts:
            continue
        rows: list[dict[str, Any]] = []
        for script in scripts:
            owner = getattr(script, "randomness_rng", None)
            if isinstance(owner, random.Random):
                family = "python_random"
            elif isinstance(owner, np.random.Generator):
                family = "numpy_pcg64_generator"
            elif owner is None:
                family = "missing"
            else:
                family = type(owner).__name__
            rows.append(
                {
                    "script_type": f"{type(script).__module__}.{type(script).__qualname__}",
                    "owner_family": family,
                    "owner_mode": str(getattr(script, "randomness_owner_mode", "unknown")),
                }
            )
        entries[str(organism_id)] = rows
    return {
        "schema_version": _PS_SCRIPTS_SCHEMA_VERSION,
        "organisms": entries,
    }


def _validate_ps_organism_scripts(overlay: Any) -> dict[str, list[dict[str, Any]]]:
    """Validate the scripts overlay without touching any live owner."""
    if not isinstance(overlay, Mapping):
        raise ValueError("PS scripts overlay must be a mapping")
    if set(overlay) != {"schema_version", "organisms"}:
        raise ValueError("PS scripts overlay has unexpected keys")
    if overlay.get("schema_version") != _PS_SCRIPTS_SCHEMA_VERSION:
        raise ValueError("PS scripts overlay schema_version mismatch")
    organisms = overlay.get("organisms")
    if not isinstance(organisms, Mapping):
        raise ValueError("PS scripts overlay organisms must be a mapping")
    prepared: dict[str, list[dict[str, Any]]] = {}
    for organism_id, rows in organisms.items():
        if not isinstance(rows, list):
            raise ValueError(f"PS scripts overlay entry {organism_id!r} must be a list")
        prepared_rows: list[dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, Mapping):
                raise ValueError(f"PS scripts overlay entry {organism_id!r} row malformed")
            if set(row) != {"script_type", "owner_family", "owner_mode"}:
                raise ValueError(f"PS scripts overlay entry {organism_id!r} row keys invalid")
            for field in ("script_type", "owner_family", "owner_mode"):
                if not isinstance(row[field], str):
                    raise ValueError(
                        f"PS scripts overlay entry {organism_id!r} {field} must be str"
                    )
            prepared_rows.append(dict(row))
        prepared[str(organism_id)] = prepared_rows
    return prepared


def _apply_ps_organism_scripts(
    pond: Any,
    prepared: Mapping[str, list[dict[str, Any]]],
) -> None:
    """Reject a changed live PS script graph before any state is applied.

    The portable payload cannot recreate script instances, so the only sound
    outcome is fail-closed: if the captured and live owner graphs differ, the
    restore must raise rather than silently drop executable scripts.
    """
    organisms = getattr(pond, "organisms", None)
    if not isinstance(organisms, Mapping):
        raise RuntimeError("PS pond organism registry unavailable")
    live = _capture_ps_organism_scripts(pond)["organisms"]
    if set(live) != set(prepared):
        raise RuntimeError("PS organism script owner graph is not checkpointable")
    for organism_id, expected_rows in prepared.items():
        actual_rows = list(live.get(organism_id, []))
        if len(actual_rows) != len(expected_rows):
            raise RuntimeError("PS organism script owner graph is not checkpointable")
        for index, (actual, expected) in enumerate(zip(actual_rows, expected_rows)):
            if actual != expected:
                raise RuntimeError(
                    "PS organism script owner graph is not checkpointable: "
                    f"{organism_id}[{index}]"
                )


_PS_LIFECYCLE_OVERLAY_KEY = "worldbridge_organism_lifecycle"
_PS_LIFECYCLE_SCHEMA_VERSION = 1
_PS_LIFECYCLE_FIELDS = ("active", "visible", "developmental_stage")


def _capture_ps_organism_lifecycle(pond: Any) -> dict[str, Any]:
    """Snapshot per-organism lifecycle owners the portable PS payload drops.

    ``PondSerializer`` omits ``active`` / ``visible`` /
    ``developmental_stage`` from the portable organism payload, and
    ``restore_serialized_state_in_place`` rebuilds organism objects, so those
    owners would otherwise be lost on restore.  The overlay rides inside
    ``ps_state`` as one extra top-level key: the serializer ignores unknown
    keys, so the portable ``.pond`` schema is unchanged.

    Only owners the organism actually exposes are recorded, so entity types
    that never carried a lifecycle owner are neither captured nor asserted.
    """
    organisms = getattr(pond, "organisms", None)
    if not isinstance(organisms, Mapping):
        raise RuntimeError("PS pond organism registry unavailable")
    entries: dict[str, dict[str, Any]] = {}
    for organism_id, organism in organisms.items():
        entry: dict[str, Any] = {}
        if hasattr(organism, "active"):
            entry["active"] = bool(organism.active)
        if hasattr(organism, "visible"):
            entry["visible"] = bool(organism.visible)
        if hasattr(organism, "developmental_stage"):
            entry["developmental_stage"] = int(organism.developmental_stage)
        if entry:
            entries[str(organism_id)] = entry
    return {
        "schema_version": _PS_LIFECYCLE_SCHEMA_VERSION,
        "organisms": entries,
    }


def _validate_ps_organism_lifecycle(overlay: Any) -> dict[str, dict[str, Any]]:
    """Validate the lifecycle overlay without touching any live owner."""
    if not isinstance(overlay, Mapping):
        raise ValueError("PS lifecycle overlay must be a mapping")
    if set(overlay) != {"schema_version", "organisms"}:
        raise ValueError("PS lifecycle overlay has unexpected keys")
    if overlay.get("schema_version") != _PS_LIFECYCLE_SCHEMA_VERSION:
        raise ValueError("PS lifecycle overlay schema_version mismatch")
    organisms = overlay.get("organisms")
    if not isinstance(organisms, Mapping):
        raise ValueError("PS lifecycle overlay organisms must be a mapping")
    prepared: dict[str, dict[str, Any]] = {}
    for organism_id, entry in organisms.items():
        if not isinstance(entry, Mapping) or not entry:
            raise ValueError(f"PS lifecycle overlay entry {organism_id!r} is malformed")
        if not set(entry) <= set(_PS_LIFECYCLE_FIELDS):
            raise ValueError(
                f"PS lifecycle overlay entry {organism_id!r} has unknown fields"
            )
        for flag in ("active", "visible"):
            if flag in entry and not isinstance(entry[flag], bool):
                raise ValueError(
                    f"PS lifecycle overlay entry {organism_id!r} flags must be bool"
                )
        if "developmental_stage" in entry:
            stage = entry["developmental_stage"]
            if isinstance(stage, bool) or not isinstance(stage, int):
                raise ValueError(
                    f"PS lifecycle overlay entry {organism_id!r} stage must be int"
                )
        prepared[str(organism_id)] = dict(entry)
    return prepared


def _ps_payload_organism_ids(payload: Mapping[str, Any]) -> set[str] | None:
    """Return the serialized organism ids, or ``None`` when not determinable."""
    organisms = payload.get("organisms")
    if isinstance(organisms, Mapping):
        return {str(key) for key in organisms}
    if isinstance(organisms, list):
        identifiers: set[str] = set()
        for item in organisms:
            if not isinstance(item, Mapping) or item.get("id") is None:
                return None
            identifiers.add(str(item["id"]))
        return identifiers
    return None


def _apply_ps_organism_lifecycle(
    pond: Any,
    prepared: Mapping[str, Mapping[str, Any]],
) -> None:
    """Write captured lifecycle owners back onto the rebuilt organisms.

    Every target is resolved before the first write so a stale overlay cannot
    leave the Pond half-restored.
    """
    from core.Lotucosm.sr_developmental_ladder import clamp_stage

    organisms = getattr(pond, "organisms", None)
    if not isinstance(organisms, Mapping):
        raise RuntimeError("PS pond organism registry unavailable")
    targets: dict[str, Any] = {}
    for organism_id in prepared:
        organism = organisms.get(organism_id)
        if organism is None:
            raise RuntimeError(
                f"PS lifecycle overlay references missing organism {organism_id!r}"
            )
        targets[organism_id] = organism
    for organism_id, entry in prepared.items():
        organism = targets[organism_id]
        if "active" in entry:
            organism.active = entry["active"]
        if "visible" in entry:
            organism.visible = entry["visible"]
        if "developmental_stage" in entry:
            organism.developmental_stage = clamp_stage(entry["developmental_stage"])


_PS_HIERARCHY_OVERLAY_KEY = "worldbridge_organism_hierarchy"
_PS_HIERARCHY_SCHEMA_VERSION = 1


def _entity_owner_id(value: Any) -> str:
    """Return a stable entity id, or fail when the owner cannot be named."""
    if isinstance(value, str):
        return value
    identifier = getattr(value, "id", None)
    if identifier is None:
        raise RuntimeError("PS hierarchy overlay entity is missing an id")
    return str(identifier)


def _capture_ps_organism_hierarchy(pond: Any) -> dict[str, Any]:
    """Snapshot the PS entity-child graph the portable payload drops.

    ``PondSerializer`` records an organism's ``components`` mapping and
    rebuilds component children from it, but it carries no ``parent`` /
    ``children`` owner graph: child order, non-component children and nested
    organism parents would otherwise be lost on restore.  The overlay records
    the id graph only.  Entity children the portable payload cannot recreate
    stay in the graph so restore fails closed instead of dropping them.
    """
    organisms = getattr(pond, "organisms", None)
    if not isinstance(organisms, Mapping):
        raise RuntimeError("PS pond organism registry unavailable")
    entries: dict[str, dict[str, Any]] = {}
    for organism_id, organism in organisms.items():
        children = getattr(organism, "children", None)
        if children is None:
            continue
        parent = getattr(organism, "parent", None)
        entries[str(organism_id)] = {
            "parent": None if parent is None else _entity_owner_id(parent),
            "children": [_entity_owner_id(child) for child in list(children)],
        }
    return {
        "schema_version": _PS_HIERARCHY_SCHEMA_VERSION,
        "organisms": entries,
    }


def _validate_ps_organism_hierarchy(overlay: Any) -> dict[str, dict[str, Any]]:
    """Validate the hierarchy overlay without touching any live owner."""
    if not isinstance(overlay, Mapping):
        raise ValueError("PS hierarchy overlay must be a mapping")
    if set(overlay) != {"schema_version", "organisms"}:
        raise ValueError("PS hierarchy overlay has unexpected keys")
    if overlay.get("schema_version") != _PS_HIERARCHY_SCHEMA_VERSION:
        raise ValueError("PS hierarchy overlay schema_version mismatch")
    organisms = overlay.get("organisms")
    if not isinstance(organisms, Mapping):
        raise ValueError("PS hierarchy overlay organisms must be a mapping")
    prepared: dict[str, dict[str, Any]] = {}
    for organism_id, entry in organisms.items():
        if not isinstance(entry, Mapping) or set(entry) != {"parent", "children"}:
            raise ValueError(f"PS hierarchy overlay entry {organism_id!r} is malformed")
        parent = entry["parent"]
        if parent is not None and not isinstance(parent, str):
            raise ValueError(
                f"PS hierarchy overlay entry {organism_id!r} parent must be str or None"
            )
        children = entry["children"]
        if not isinstance(children, list):
            raise ValueError(
                f"PS hierarchy overlay entry {organism_id!r} children must be a list"
            )
        for child_id in children:
            if not isinstance(child_id, str):
                raise ValueError(
                    f"PS hierarchy overlay entry {organism_id!r} child ids must be str"
                )
        if len(children) != len(set(children)):
            raise ValueError(
                f"PS hierarchy overlay entry {organism_id!r} has duplicate children"
            )
        prepared[str(organism_id)] = {
            "parent": parent,
            "children": list(children),
        }
    return prepared


def _ps_payload_component_owners(payload: Mapping[str, Any]) -> dict[str, str]:
    """Map serialized component ids to the organism that declares them."""
    organisms = payload.get("organisms")
    if isinstance(organisms, Mapping):
        items = [(str(key), value) for key, value in organisms.items()]
    elif isinstance(organisms, list):
        items = []
        for item in organisms:
            if not isinstance(item, Mapping) or item.get("id") is None:
                continue
            items.append((str(item["id"]), item))
    else:
        return {}
    owners: dict[str, str] = {}
    for organism_id, entry in items:
        if not isinstance(entry, Mapping):
            continue
        components = entry.get("components")
        if not isinstance(components, list):
            continue
        for component in components:
            if not isinstance(component, Mapping) or component.get("id") is None:
                continue
            component_id = str(component["id"])
            previous = owners.get(component_id)
            if previous is not None and previous != organism_id:
                raise ValueError(
                    f"PS hierarchy overlay component {component_id!r} has multiple owners"
                )
            owners[component_id] = organism_id
    return owners


def _validate_ps_organism_hierarchy_targets(
    payload: Mapping[str, Any],
    prepared: Mapping[str, Mapping[str, Any]],
) -> None:
    """Cross-check a captured hierarchy against the portable payload.

    Runs before ``restore_serialized_state_in_place`` so a hierarchy that
    references owners the payload cannot recreate fails closed without
    touching the live Pond.
    """
    declared = _ps_payload_organism_ids(payload)
    if declared is None:
        raise ValueError("PS hierarchy overlay requires determinable organism ids")
    if not set(prepared) <= declared:
        raise ValueError("PS hierarchy overlay references missing organisms")
    component_owners = _ps_payload_component_owners(payload)
    namespace = set(declared) | set(component_owners)
    seen_children: set[str] = set()
    for organism_id, entry in prepared.items():
        parent = entry["parent"]
        if parent is not None:
            if parent not in declared:
                raise ValueError(
                    f"PS hierarchy overlay parent {parent!r} is not a serialized organism"
                )
            parent_children = prepared.get(parent, {}).get("children")
            if parent_children is None or organism_id not in parent_children:
                raise ValueError(
                    "PS hierarchy overlay parent/child links are inconsistent"
                )
        for child_id in entry["children"]:
            if child_id in seen_children:
                raise ValueError(
                    f"PS hierarchy overlay child {child_id!r} has multiple parents"
                )
            seen_children.add(child_id)
            if child_id == organism_id:
                raise ValueError("PS hierarchy overlay contains a self child")
            if child_id not in namespace:
                raise ValueError(
                    "PS hierarchy overlay references an entity the portable payload "
                    f"cannot restore: {child_id!r}"
                )
            owner = component_owners.get(child_id)
            if owner is not None and owner != organism_id:
                raise ValueError(
                    f"PS hierarchy overlay child {child_id!r} does not belong to "
                    f"{organism_id!r}"
                )
            if child_id in prepared and prepared[child_id]["parent"] != organism_id:
                raise ValueError(
                    "PS hierarchy overlay parent/child links are inconsistent"
                )
    missing = set(component_owners) - seen_children
    if missing:
        raise ValueError(
            "PS hierarchy overlay omits serialized components: "
            + ", ".join(sorted(missing))
        )
    for organism_id in prepared:
        visited: set[str] = set()
        current: str | None = organism_id
        while current is not None:
            if current in visited:
                raise ValueError("PS hierarchy overlay contains a parent cycle")
            visited.add(current)
            current = prepared.get(current, {}).get("parent")


def _apply_ps_organism_hierarchy(
    pond: Any,
    prepared: Mapping[str, Mapping[str, Any]],
) -> None:
    """Replay the captured PS entity-child graph onto rebuilt organisms.

    Every target is resolved before the first mutation so a stale overlay
    cannot leave the Pond half-restored.
    """
    if not prepared:
        return
    organisms = getattr(pond, "organisms", None)
    if not isinstance(organisms, Mapping):
        raise RuntimeError("PS pond organism registry unavailable")
    organism_targets: dict[str, Any] = {}
    for organism_id in prepared:
        organism = organisms.get(organism_id)
        if organism is None:
            raise RuntimeError(
                f"PS hierarchy overlay references missing organism {organism_id!r}"
            )
        organism_targets[organism_id] = organism
    object_lookup: dict[str, Any] = {
        str(key): value for key, value in organisms.items()
    }
    for organism in organisms.values():
        components = getattr(organism, "components", None)
        if isinstance(components, Mapping):
            for component_id, component in components.items():
                object_lookup.setdefault(str(component_id), component)
    child_targets: dict[str, Any] = {}
    for entry in prepared.values():
        for child_id in entry["children"]:
            child = object_lookup.get(child_id)
            if child is None:
                raise RuntimeError(
                    f"PS hierarchy overlay references missing entity {child_id!r}"
                )
            child_targets[child_id] = child
    for organism_id, organism in organism_targets.items():
        if not callable(getattr(organism, "remove_child", None)) or not callable(
            getattr(organism, "add_child", None)
        ):
            raise RuntimeError(
                f"PS hierarchy overlay organism {organism_id!r} has no entity-child API"
            )
    for organism in organism_targets.values():
        for child in list(getattr(organism, "children", ()) or ()):
            organism.remove_child(child)
    for organism_id, entry in prepared.items():
        organism = organism_targets[organism_id]
        for child_id in entry["children"]:
            organism.add_child(child_targets[child_id])


def _capture_ps(viewport: Any) -> dict[str, Any]:
    _require_active(viewport)
    from builtin.systems.pond_serializer import PondSerializer

    pond = viewport._unified_pond
    # JSON serialization is the portable checkpoint representation. Keep an
    # optional exact owner snapshot for compensation so normalization (for
    # example tuple -> list) cannot alter the pre-failure live object.
    raw_payload = getattr(pond, "payload", None)
    if isinstance(raw_payload, Mapping):
        viewport._worldbridge_raw_ps_compensation_state = copy.deepcopy(raw_payload)
    pond_data = PondSerializer(save_format="json").serialize_pond(pond)
    # Wall-clock timestamp is metadata, not simulation state and would make
    # two captures of an unchanged Pond differ.
    pond_data.pop("timestamp", None)
    # The portable organism payload intentionally omits lifecycle owners, and
    # restore rebuilds organism objects, so carry them in a side overlay.
    pond_data[_PS_LIFECYCLE_OVERLAY_KEY] = _capture_ps_organism_lifecycle(pond)
    # Executable scripts cannot round-trip through canonical JSON.  Record the
    # owner graph so a drifted live script set fails closed on restore instead
    # of being silently dropped by the rebuilt organism objects.
    pond_data[_PS_SCRIPTS_OVERLAY_KEY] = _capture_ps_organism_scripts(pond)
    # The portable organism payload rebuilds component children from the
    # components mapping but drops the entity-child graph, so carry the PS
    # hierarchy owner graph (parent, child order) in a side overlay too.
    pond_data[_PS_HIERARCHY_OVERLAY_KEY] = _capture_ps_organism_hierarchy(pond)
    return copy.deepcopy(pond_data)


def _compensate_ps(viewport: Any, state: Mapping[str, Any]) -> None:
    raw_payload = getattr(viewport, "_worldbridge_raw_ps_compensation_state", None)
    pond = getattr(viewport, "_unified_pond", None)
    if isinstance(raw_payload, Mapping) and hasattr(pond, "payload"):
        pond.payload = copy.deepcopy(raw_payload)
        return
    _restore_ps(viewport, state)


def _restore_ps(viewport: Any, state: Mapping[str, Any]) -> None:
    _require_active(viewport)
    payload = copy.deepcopy(dict(state))
    # Validate the overlay before touching live owners so a malformed payload
    # fails closed instead of half-restoring the Pond.
    overlay = payload.get(_PS_LIFECYCLE_OVERLAY_KEY)
    prepared = None if overlay is None else _validate_ps_organism_lifecycle(overlay)
    if prepared is not None:
        declared = _ps_payload_organism_ids(payload)
        if declared is not None and not set(prepared) <= declared:
            raise ValueError(
                "PS lifecycle overlay does not match serialized organisms"
            )
    hierarchy_overlay = payload.get(_PS_HIERARCHY_OVERLAY_KEY)
    prepared_hierarchy = (
        None
        if hierarchy_overlay is None
        else _validate_ps_organism_hierarchy(hierarchy_overlay)
    )
    if prepared_hierarchy is not None:
        _validate_ps_organism_hierarchy_targets(payload, prepared_hierarchy)
    scripts_overlay = payload.get(_PS_SCRIPTS_OVERLAY_KEY)
    prepared_scripts = (
        None
        if scripts_overlay is None
        else _validate_ps_organism_scripts(scripts_overlay)
    )
    if prepared_scripts is not None:
        # Validate the live owner graph before the payload is applied so a
        # drifted script set fails closed without touching the Pond.  An empty
        # captured set is still validated: a live script added after capture
        # must be rejected, not silently dropped.
        _apply_ps_organism_scripts(viewport._unified_pond, prepared_scripts)
    viewport._unified_pond.restore_serialized_state_in_place(payload)
    if prepared is not None:
        _apply_ps_organism_lifecycle(viewport._unified_pond, prepared)
    if prepared_hierarchy is not None:
        _apply_ps_organism_hierarchy(viewport._unified_pond, prepared_hierarchy)


def _capture_transaction_snapshot(viewport: Any) -> WorldBridgeTransactionCapture:
    """Capture one strict transaction bound to a completed authoritative tick."""

    return _capture_transaction_snapshot_for_mode(viewport, mode="strict")


def _capture_handoff_transaction_snapshot(
    viewport: Any,
) -> WorldBridgeTransactionCapture:
    """Capture one handoff transaction, allowing active-tick scope evidence."""

    return _capture_transaction_snapshot_for_mode(viewport, mode="handoff")


def _capture_legacy_transaction_snapshot(
    viewport: Any,
) -> WorldBridgeTransactionCapture:
    """Capture a checkpoint-only transaction without requiring a tick receipt."""

    return _capture_transaction_snapshot_for_mode(viewport, mode="legacy")


def _capture_restore_tick_evidence(
    viewport: Any,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Probe either completed receipt evidence or one active handoff scope."""

    return _capture_tick_evidence(
        viewport,
        allow_active=True,
        require_completed=False,
    )


def _capture_transaction_snapshot_for_mode(
    viewport: Any,
    *,
    mode: str,
) -> WorldBridgeTransactionCapture:
    """Capture all owners once with one explicit tick-evidence policy.

    ``strict`` retains the E543 completed-receipt contract. ``handoff`` permits
    an active tick but records a separate process-local scope rather than
    fabricating a completed receipt. ``legacy`` permits the pre-first-tick case
    for checkpoint-only capture while still rejecting an active tick.
    """

    if mode not in {"strict", "handoff", "legacy"}:
        raise ValueError(f"unsupported transaction capture mode: {mode}")
    _require_active(viewport)
    pond = viewport._unified_pond
    capture_live = getattr(
        pond, "capture_worldbridge_live_transaction_state", None
    )
    if not callable(capture_live):
        raise RuntimeError("Pond live transaction capture owner unavailable")

    tick_binding_before, tick_scope_before = _capture_tick_evidence(
        viewport,
        allow_active=mode == "handoff",
        require_completed=mode == "strict",
    )
    tick_authority_before = _capture_tick_authority_snapshot(viewport)
    before_evidence = _capture_transaction_owner_evidence(
        viewport, capture_live
    )
    sr_state = _capture_sr(viewport)
    portable_ps_state = _capture_ps(viewport)
    live_ps_state = capture_live()
    bridge_identity_links = _capture_bridge(viewport)
    input_state = _capture_input(viewport)
    randomness_state = _capture_randomness(viewport)
    lifecycle = _capture_lifecycle(viewport)
    topology_owner_state = (
        _capture_topology_owner_state(viewport)
        if callable(getattr(viewport, "capture_sr_topology_owner_state", None))
        else None
    )
    after_evidence = _capture_transaction_owner_evidence(
        viewport, capture_live
    )
    tick_binding_after, tick_scope_after = _capture_tick_evidence(
        viewport,
        allow_active=mode == "handoff",
        require_completed=mode == "strict",
    )
    tick_authority_after = _capture_tick_authority_snapshot(viewport)
    if (
        tick_binding_before != tick_binding_after
        or tick_scope_before != tick_scope_after
    ):
        raise WorldBridgeTransactionCaptureError(
            "tick_binding_changed_during_capture",
            details={
                "before_binding": copy.deepcopy(tick_binding_before),
                "after_binding": copy.deepcopy(tick_binding_after),
                "before_scope": copy.deepcopy(tick_scope_before),
                "after_scope": copy.deepcopy(tick_scope_after),
            },
        )
    _require_tick_authority_matches_evidence(
        tick_authority_before,
        tick_binding_before,
        tick_scope_before,
    )
    if tick_authority_before != tick_authority_after:
        raise WorldBridgeTransactionCaptureError(
            "tick_authority_changed_during_capture",
            details={
                "before": copy.deepcopy(tick_authority_before),
                "after": copy.deepcopy(tick_authority_after),
            },
        )

    changed_owners = [
        owner
        for owner in before_evidence
        if before_evidence[owner] != after_evidence[owner]
    ]
    if changed_owners:
        raise WorldBridgeTransactionCaptureError(
            (
                "live_ps_changed_during_capture"
                if changed_owners == ["live_ps"]
                else "transaction_owner_changed_during_capture"
            ),
            details={
                "owners": changed_owners,
                "before": before_evidence,
                "after": after_evidence,
            },
        )
    return WorldBridgeTransactionCapture(
        sr_state=sr_state,
        ps_state=portable_ps_state,
        live_ps_state=live_ps_state,
        bridge_identity_links=bridge_identity_links,
        input_state=input_state,
        randomness_state=randomness_state,
        lifecycle=lifecycle,
        topology_owner_state=topology_owner_state,
        tick_binding=tick_binding_before,
        tick_scope=tick_scope_before,
        tick_authority_state=tick_authority_before,
    )


def _capture_tick_authority_snapshot(viewport: Any) -> dict[str, Any] | None:
    """Capture the process-local authority beside the portable checkpoint."""

    authority = getattr(viewport, "_worldbridge_tick_authority", None)
    if authority is None:
        return None
    snapshot_method = getattr(authority, "snapshot", None)
    if not callable(snapshot_method):
        raise RuntimeError("tick authority snapshot owner unavailable")
    try:
        snapshot = snapshot_method()
    except Exception as exc:
        raise RuntimeError("tick authority snapshot capture failed") from exc
    if not isinstance(snapshot, Mapping):
        raise RuntimeError("tick authority snapshot is not a mapping")
    detached = copy.deepcopy(dict(snapshot))
    from .world_bridge_tick_authority import (
        validate_worldbridge_tick_authority_snapshot,
    )

    validation = validate_worldbridge_tick_authority_snapshot(detached)
    if validation != {"valid": True, "errors": []}:
        raise RuntimeError(
            "tick authority snapshot invalid: "
            + ",".join(validation.get("errors", ()))
        )
    return detached


def _validate_tick_authority_snapshot(
    viewport: Any,
    snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate a detached authority snapshot against the current owner."""

    from .world_bridge_tick_authority import (
        validate_worldbridge_tick_authority_snapshot,
    )

    if not isinstance(snapshot, Mapping):
        return {"valid": False, "errors": ["tick_authority_snapshot_not_mapping"]}
    try:
        candidate = copy.deepcopy(dict(snapshot))
    except Exception:
        return {"valid": False, "errors": ["tick_authority_snapshot_invalid"]}
    errors = list(validate_worldbridge_tick_authority_snapshot(candidate)["errors"])
    authority = getattr(viewport, "_worldbridge_tick_authority", None)
    if authority is None:
        errors.append("tick_authority_owner_unavailable")
    elif getattr(authority, "rng_context_id", None) != candidate.get("rng_context_id"):
        errors.append("tick_authority_rng_context_mismatch")
    return {"valid": not errors, "errors": list(dict.fromkeys(errors))}


def _restore_tick_authority_snapshot(
    viewport: Any,
    snapshot: Mapping[str, Any],
) -> None:
    """Restore only after the whole detached snapshot passes validation."""

    validation = _validate_tick_authority_snapshot(viewport, snapshot)
    if not validation["valid"]:
        raise ValueError(
            "tick authority snapshot restore rejected: "
            + ",".join(validation["errors"])
        )
    authority = getattr(viewport, "_worldbridge_tick_authority", None)
    restore = getattr(authority, "restore_snapshot", None)
    if not callable(restore):
        raise RuntimeError("tick authority restore owner unavailable")
    restore(copy.deepcopy(dict(snapshot)))
    restored = _capture_tick_authority_snapshot(viewport)
    if restored != copy.deepcopy(dict(snapshot)):
        raise RuntimeError("tick authority restore did not reproduce the snapshot")


def _require_tick_authority_matches_evidence(
    authority_snapshot: Mapping[str, Any] | None,
    binding: Mapping[str, Any] | None,
    scope: Mapping[str, Any] | None,
) -> None:
    """Fail when authority and tick evidence name different activity."""

    if authority_snapshot is None:
        if binding is not None or scope is not None:
            raise WorldBridgeTransactionCaptureError(
                "tick_authority_snapshot_unavailable_for_tick_evidence"
            )
        return
    if binding is not None:
        receipt = authority_snapshot.get("last_receipt")
        if not isinstance(receipt, Mapping) or any(
            receipt.get(field) != binding.get(field)
            for field in (
                "tick_sequence",
                "pause_reset_epoch",
                "input_digest",
                "context_digest",
                "rng_context_id",
                "rng_start_digest",
                "rng_end_digest",
                "receipt_digest",
            )
        ):
            raise WorldBridgeTransactionCaptureError(
                "tick_authority_completed_binding_mismatch"
            )
        if authority_snapshot.get("current_tick") is not None:
            raise WorldBridgeTransactionCaptureError(
                "tick_authority_active_during_completed_capture"
            )
        return
    if scope is not None:
        current = authority_snapshot.get("current_tick")
        if not isinstance(current, Mapping) or any(
            current.get(field) != scope.get(field)
            for field in ("tick_sequence", "pause_reset_epoch", "context_digest")
        ):
            raise WorldBridgeTransactionCaptureError(
                "tick_authority_active_scope_mismatch"
            )
        return
    if authority_snapshot.get("current_tick") is not None:
        raise WorldBridgeTransactionCaptureError(
            "tick_authority_active_without_scope"
        )


def _capture_tick_evidence(
    viewport: Any,
    *,
    allow_active: bool,
    require_completed: bool,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Capture either a completed binding or a handoff-only active scope."""

    authority = getattr(viewport, "_worldbridge_tick_authority", None)
    if authority is None:
        return None, None
    current = getattr(authority, "current_tick", None)
    active = current() if callable(current) else None
    if active is not None:
        if not allow_active:
            raise WorldBridgeTransactionCaptureError(
                "active_tick_checkpoint_capture_rejected"
            )
        validation = authority.validate_tick_context(active)
        if validation != {"valid": True, "errors": []}:
            raise WorldBridgeTransactionCaptureError(
                "active_tick_context_invalid",
                details={"errors": validation["errors"]},
            )
        tick_sequence = getattr(authority, "tick_sequence", None)
        sequence = getattr(viewport, "_worldbridge_input_sequence", None)
        pause_epoch = getattr(sequence, "pause_reset_epoch", None)
        if (
            isinstance(tick_sequence, bool)
            or not isinstance(tick_sequence, int)
            or tick_sequence != active.get("tick_sequence")
        ):
            raise WorldBridgeTransactionCaptureError(
                "active_tick_sequence_mismatch"
            )
        if pause_epoch != active.get("pause_reset_epoch"):
            raise WorldBridgeTransactionCaptureError(
                "active_tick_pause_reset_epoch_mismatch"
            )
        return None, {
            "schema_version": 1,
            "status": "worldbridge_active_tick_scope",
            "authority_id": id(authority),
            "tick_sequence": tick_sequence,
            "pause_reset_epoch": pause_epoch,
            "context_digest": active["context_digest"],
        }

    receipt = getattr(authority, "last_receipt", None)
    if not isinstance(receipt, Mapping):
        if require_completed:
            raise WorldBridgeTransactionCaptureError(
                "completed_tick_receipt_unavailable"
            )
        return None, None
    return _build_completed_tick_binding(viewport, authority, receipt), None


def _capture_completed_tick_binding(
    viewport: Any,
) -> dict[str, Any] | None:
    """Return the last completed authoritative tick; legacy hosts may be unbound."""

    return _capture_tick_evidence(
        viewport,
        allow_active=False,
        require_completed=False,
    )[0]


def _build_completed_tick_binding(
    viewport: Any,
    authority: Any,
    receipt: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate and project one completed receipt into the eight-field binding."""

    from .world_bridge_tick_authority import validate_worldbridge_tick_receipt

    receipt_validation = validate_worldbridge_tick_receipt(receipt)
    if not receipt_validation["valid"]:
        raise WorldBridgeTransactionCaptureError(
            "completed_tick_receipt_invalid",
            details={"errors": receipt_validation["errors"]},
        )
    tick_sequence = getattr(authority, "tick_sequence", None)
    if (
        isinstance(tick_sequence, bool)
        or not isinstance(tick_sequence, int)
        or tick_sequence != receipt.get("tick_sequence")
    ):
        raise WorldBridgeTransactionCaptureError(
            "completed_tick_receipt_sequence_mismatch"
        )
    viewport_receipt = getattr(viewport, "_worldbridge_last_tick_receipt", None)
    if viewport_receipt != receipt:
        raise WorldBridgeTransactionCaptureError(
            "viewport_tick_receipt_mismatch"
        )
    sequence = getattr(viewport, "_worldbridge_input_sequence", None)
    snapshot = getattr(sequence, "snapshot", None)
    canonical = snapshot() if callable(snapshot) else None
    if (
        not isinstance(canonical, Mapping)
        or canonical.get("pause_reset_epoch") != receipt.get("pause_reset_epoch")
    ):
        raise WorldBridgeTransactionCaptureError(
            "completed_tick_pause_reset_epoch_mismatch"
        )
    return {
        "tick_sequence": receipt["tick_sequence"],
        "pause_reset_epoch": receipt["pause_reset_epoch"],
        "input_digest": receipt["input_digest"],
        "context_digest": receipt["context_digest"],
        "rng_context_id": receipt["rng_context_id"],
        "rng_start_digest": receipt["rng_start_digest"],
        "rng_end_digest": receipt["rng_end_digest"],
        "receipt_digest": receipt["receipt_digest"],
    }


def _capture_transaction_owner_evidence(
    viewport: Any, capture_live: Any
) -> dict[str, Any]:
    """Return canonical read-only evidence for every transaction owner.

    These probes deliberately do not replace the authoritative owner capture.
    They run before and after that capture to detect a moving owner window.
    """

    owners: dict[str, Any] = {
        "sr": _capture_sr(viewport),
        "live_ps": _live_ps_digest(capture_live()),
        "bridge": _capture_bridge(viewport),
        "input": _capture_input(viewport),
        "randomness": _capture_randomness(viewport),
        "lifecycle": _capture_lifecycle(viewport),
        "topology": (
            _capture_topology_owner_state(viewport)
            if callable(getattr(viewport, "capture_sr_topology_owner_state", None))
            else None
        ),
    }
    return {
        owner: hashlib.sha256(
            json.dumps(
                state,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
        ).hexdigest()
        for owner, state in owners.items()
    }

def _capture_transaction_state(viewport: Any) -> tuple[dict[str, Any], Any]:
    """Legacy tuple view of one coherent transaction capture."""

    snapshot = _capture_transaction_snapshot(viewport)
    return snapshot.ps_state, snapshot.live_ps_state


def _capture_live_ps(viewport: Any) -> Any:
    _require_active(viewport)
    capture = getattr(viewport._unified_pond, "capture_worldbridge_live_transaction_state", None)
    if not callable(capture):
        raise RuntimeError("Pond live transaction capture owner unavailable")
    return capture()


def _live_ps_digest(state: Any) -> str:
    digest = getattr(state, "digest", None)
    if not isinstance(digest, str) or not digest:
        raise ValueError("live PS transaction state must expose a digest")
    return digest


def _restore_live_ps(viewport: Any, state: Any) -> None:
    _require_active(viewport)
    restore = getattr(viewport._unified_pond, "restore_worldbridge_live_transaction_state", None)
    if not callable(restore):
        raise RuntimeError("Pond live transaction restore owner unavailable")
    restore(state)


def _capture_bridge(viewport: Any) -> list[dict[str, str]]:
    _require_active(viewport)
    from .world_bridge import capture_bridge_identity_links

    return capture_bridge_identity_links(viewport.scene_runtime_entities)


def _restore_bridge(viewport: Any, links: list[Mapping[str, Any]]) -> None:
    _require_active(viewport)
    from .world_bridge import restore_bridge_identity_links

    restore_bridge_identity_links(
        viewport.scene_runtime_entities,
        viewport._unified_pond,
        copy.deepcopy(links),
        replace_existing=True,
    )


def _capture_input(viewport: Any) -> dict[str, Any]:
    _require_active(viewport)
    state = copy.deepcopy(viewport.capture_sr_input_state())
    sequence = getattr(viewport, "_worldbridge_input_sequence", None)
    snapshot = getattr(sequence, "snapshot", None)
    if callable(snapshot):
        state["canonical_sequence"] = copy.deepcopy(snapshot())
    pond = getattr(viewport, "_unified_pond", None)
    pond_events = getattr(pond, "worldbridge_input_events_last_tick", None)
    if pond_events is not None:
        state["ps_handoff_input_events"] = copy.deepcopy(list(pond_events))
    state["shared_transport"] = _capture_shared_transport(viewport)
    return state


def _restore_input(viewport: Any, state: Mapping[str, Any]) -> None:
    _require_active(viewport)
    candidate = copy.deepcopy(dict(state))
    canonical = candidate.pop("canonical_sequence", None)
    ps_handoff_events = candidate.pop("ps_handoff_input_events", None)
    transport = candidate.pop("shared_transport", None)
    sequence = getattr(viewport, "_worldbridge_input_sequence", None)
    if canonical is not None:
        validate_snapshot = getattr(sequence, "validate_snapshot", None)
        if not callable(validate_snapshot):
            raise RuntimeError("canonical input sequence owner unavailable")
        validate_snapshot(canonical)
    if transport is not None:
        _validate_shared_transport(viewport, transport)
    if ps_handoff_events is not None:
        _validate_ps_handoff_input_events(ps_handoff_events)
    viewport.restore_sr_input_state(candidate)
    if canonical is not None:
        restore_snapshot = getattr(sequence, "restore_snapshot", None)
        if not callable(restore_snapshot):
            raise RuntimeError("canonical input sequence owner unavailable")
        restore_snapshot(canonical)
    if transport is not None:
        _restore_shared_transport(viewport, transport)
    if ps_handoff_events is not None:
        pond = getattr(viewport, "_unified_pond", None)
        apply_inputs = getattr(pond, "apply_worldbridge_input_events", None)
        if not callable(apply_inputs):
            raise RuntimeError("Pond input handoff owner unavailable")
        apply_inputs(ps_handoff_events)


def _validate_ps_handoff_input_events(events: object) -> list[dict[str, Any]]:
    """Validate a detached PS handoff batch without advancing its owner."""
    from .world_bridge_input_sequence import validate_worldbridge_input_events

    if not isinstance(events, list):
        raise ValueError("PS handoff input events must be a list")
    copied = copy.deepcopy(events)
    if not copied:
        return copied
    first_sequence = copied[0].get("sequence")
    epoch = copied[0].get("pause_reset_epoch")
    if isinstance(first_sequence, bool) or not isinstance(first_sequence, int):
        raise ValueError("PS handoff input sequence is invalid")
    if isinstance(epoch, bool) or not isinstance(epoch, int):
        raise ValueError("PS handoff input epoch is invalid")
    validation = validate_worldbridge_input_events(
        copied, last_sequence=first_sequence - 1, pause_reset_epoch=epoch
    )
    if not validation["valid"]:
        raise ValueError("invalid PS handoff input events: " + ",".join(validation["errors"]))
    return copied


def _capture_shared_transport(viewport: Any) -> dict[str, Any]:
    receiver = getattr(viewport, "_worldbridge_shared_state_receiver", None)
    continuity = None
    if receiver is not None:
        snapshot = getattr(receiver, "continuity_snapshot", None)
        if not callable(snapshot):
            raise RuntimeError("shared-state receiver continuity owner unavailable")
        continuity = snapshot()
    return {
        "schema_version": 1,
        "runtime_epoch": str(viewport._sr_runtime_epoch),
        "envelope_sequence": int(getattr(viewport, "_worldbridge_shared_state_sequence", 0)),
        "receiver": continuity,
    }


def _restore_shared_transport(viewport: Any, state: Mapping[str, Any]) -> None:
    _validate_shared_transport(viewport, state)
    sequence = state["envelope_sequence"]
    receiver_state = state.get("receiver")
    receiver = getattr(viewport, "_worldbridge_shared_state_receiver", None)
    if receiver_state is not None:
        from .world_bridge_shared_state_transport import WorldBridgeSharedStateReceiver

        if receiver is None:
            receiver = WorldBridgeSharedStateReceiver()
            viewport._worldbridge_shared_state_receiver = receiver
        receiver.restore_continuity(receiver_state)
    elif receiver is not None and receiver.last_sequence is not None:
        raise RuntimeError("shared transport checkpoint receiver state is stale")
    viewport._worldbridge_shared_state_sequence = sequence


def _validate_shared_transport(viewport: Any, state: Mapping[str, Any]) -> None:
    if not isinstance(state, Mapping):
        raise ValueError("shared transport checkpoint must be a mapping")
    required = {"schema_version", "runtime_epoch", "envelope_sequence", "receiver"}
    if set(state) != required or state.get("schema_version") != 1:
        raise ValueError("shared transport checkpoint schema mismatch")
    if state.get("runtime_epoch") != str(viewport._sr_runtime_epoch):
        raise RuntimeError("shared transport checkpoint epoch mismatch")
    sequence = state.get("envelope_sequence")
    if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
        raise ValueError("shared transport checkpoint sequence invalid")
    # A live checkpoint is an explicit time-travel operation within the same
    # runtime epoch. Transport receive monotonicity is enforced by the receiver
    # when envelopes arrive; it must not prevent restoring an older checkpoint.
    receiver_state = state.get("receiver")
    if receiver_state is not None:
        from .world_bridge_shared_state_transport import WorldBridgeSharedStateReceiver
        validator = WorldBridgeSharedStateReceiver()
        validator.restore_continuity(receiver_state)


def _capture_randomness(viewport: Any) -> dict[str, Any]:
    _require_active(viewport)
    rng = getattr(viewport, "_sr_runtime_rng", None)
    if not isinstance(rng, random.Random):
        raise RuntimeError("active SR runtime RNG is not a caller-owned random.Random")
    context = getattr(viewport, "_worldbridge_opt_in_deterministic_randomness_context", None)
    from .world_bridge_randomness_authority import (
        build_worldbridge_rng_checkpoint_state,
        validate_pond_randomness_owner_graph,
        validate_sr_script_randomness_owner_graph,
    )

    pond = getattr(viewport, "_unified_pond", None)
    if pond is not None:
        graph = validate_pond_randomness_owner_graph(
            pond, getattr(pond, "randomness_rng", None)
        )
        if graph != {"valid": True, "errors": []}:
            raise RuntimeError(
                "Pond randomness owner graph is not checkpointable: "
                + ", ".join(graph["errors"])
            )
    script_graph = validate_sr_script_randomness_owner_graph(
        getattr(viewport, "scene_runtime_entities", ()), rng
    )
    if script_graph != {"valid": True, "errors": []}:
        raise RuntimeError(
            "SR script randomness owner graph is not checkpointable: "
            + ", ".join(script_graph["errors"])
        )

    return build_worldbridge_rng_checkpoint_state(
        runtime_epoch=str(viewport._sr_runtime_epoch),
        sr_runtime_rng=rng,
        deterministic_context=context,
        pond_runtime_rng=(
            getattr(getattr(viewport, "_unified_pond", None), "randomness_rng", None)
        ),
        caller_owned_streams={
            "sr.runtime": rng,
            **(
                {
                    "ps.pond": getattr(viewport._unified_pond, "randomness_rng")
                }
                if isinstance(
                    getattr(getattr(viewport, "_unified_pond", None), "randomness_rng", None),
                    np.random.Generator,
                )
                else {}
            ),
        },
        caller_owned_stream_modes={
            "sr.runtime": str(getattr(viewport, "_sr_runtime_owner_mode", "runtime")),
            **(
                {
                    "ps.pond": str(
                        getattr(viewport._unified_pond, "randomness_owner_mode", "runtime")
                    )
                }
                if isinstance(
                    getattr(getattr(viewport, "_unified_pond", None), "randomness_rng", None),
                    np.random.Generator,
                )
                else {}
            ),
        },
    )


def _restore_randomness(viewport: Any, state: Mapping[str, Any] | None) -> None:
    _require_active(viewport)
    from .world_bridge_randomness_authority import (
        restore_worldbridge_global_random_states,
        restore_worldbridge_numpy_generator_state,
        restore_worldbridge_caller_owned_streams,
        validate_worldbridge_rng_checkpoint_state,
    )
    from .world_bridge_native_entropy_audit import build_native_entropy_boundary_receipt

    validation = validate_worldbridge_rng_checkpoint_state(state)
    if validation != {"valid": True, "errors": []}:
        raise ValueError(
            "invalid SR runtime randomness state: " + ", ".join(validation["errors"])
        )
    if state.get("runtime_epoch") != str(viewport._sr_runtime_epoch):
        raise RuntimeError("SR runtime randomness checkpoint epoch mismatch")
    if state.get("native_boundary_receipt") != build_native_entropy_boundary_receipt():
        raise RuntimeError("native entropy boundary receipt mismatch")
    sr_state = state.get("sr_runtime")
    global_state = state.get("process_global")
    if not isinstance(sr_state, Mapping) or sr_state.get("kind") != "sr_runtime_python_random":
        raise ValueError("invalid SR runtime randomness state")
    internal = sr_state.get("internal_state")
    if not isinstance(internal, list):
        raise ValueError("randomness internal_state must be a list")
    from .world_bridge_deterministic_randomness_context import (
        restore_worldbridge_deterministic_randomness_context,
    )

    rng = getattr(viewport, "_sr_runtime_rng")
    original_local = rng.getstate()
    pond = getattr(viewport, "_unified_pond", None)
    pond_rng = getattr(pond, "randomness_rng", None)
    pond_state = state.get("pond_runtime")
    original_pond = copy.deepcopy(pond_rng.bit_generator.state) if pond_state is not None and isinstance(pond_rng, np.random.Generator) else None
    caller_owned_state = state.get("caller_owned_streams")
    original_caller_owned = None
    if caller_owned_state is not None:
        original_caller_owned = {
            "sr.runtime": rng,
            **({"ps.pond": pond_rng} if isinstance(pond_rng, np.random.Generator) else {}),
        }
        from .world_bridge_randomness_authority import (
            build_caller_owned_stream_receipt,
            build_randomness_owner_inventory,
        )

        live_receipt = build_caller_owned_stream_receipt(
            original_caller_owned,
            {
                "sr.runtime": str(getattr(viewport, "_sr_runtime_owner_mode", "runtime")),
                **(
                    {
                        "ps.pond": str(
                            getattr(pond, "randomness_owner_mode", "runtime")
                        )
                    }
                    if isinstance(pond_rng, np.random.Generator)
                    else {}
                ),
            },
        )
        if state.get("caller_owned_stream_receipt") != live_receipt:
            raise RuntimeError("caller-owned stream owner receipt mismatch")
        live_inventory = build_randomness_owner_inventory(
            original_caller_owned,
            {
                "sr.runtime": str(getattr(viewport, "_sr_runtime_owner_mode", "runtime")),
                **(
                    {
                        "ps.pond": str(
                            getattr(pond, "randomness_owner_mode", "runtime")
                        )
                    }
                    if isinstance(pond_rng, np.random.Generator)
                    else {}
                ),
            },
        )
        if state.get("owner_inventory") != live_inventory:
            raise RuntimeError("randomness owner inventory mismatch")
    context = getattr(viewport, "_worldbridge_opt_in_deterministic_randomness_context", None)
    checkpoint_context = state.get("deterministic_context")
    if (context is None) != (checkpoint_context is None):
        raise RuntimeError("deterministic randomness context ownership mismatch")
    original_context = context.snapshot() if context is not None else None
    try:
        decoded = (int(sr_state["version"]), tuple(int(value) for value in internal), sr_state.get("gaussian_cache"))
        if context is not None:
            restore_worldbridge_deterministic_randomness_context(context, checkpoint_context)
        rng.setstate(decoded)
        if pond_state is not None:
            if not isinstance(pond_rng, np.random.Generator):
                raise RuntimeError("Pond randomness owner is unavailable during restore")
            restore_worldbridge_numpy_generator_state(pond_rng, pond_state)
        if caller_owned_state is not None:
            assert original_caller_owned is not None
            restore_worldbridge_caller_owned_streams(
                original_caller_owned, caller_owned_state
            )
        restore_worldbridge_global_random_states(global_state)
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        if context is not None and original_context is not None:
            restore_worldbridge_deterministic_randomness_context(context, original_context)
        rng.setstate(original_local)
        if original_pond is not None:
            pond_rng.bit_generator.state = original_pond
        raise ValueError("invalid SR runtime randomness state") from exc
    except Exception:
        if context is not None and original_context is not None:
            restore_worldbridge_deterministic_randomness_context(context, original_context)
        rng.setstate(original_local)
        if original_pond is not None:
            pond_rng.bit_generator.state = original_pond
        raise


def _capture_lifecycle(viewport: Any) -> dict[str, Any]:
    _require_active(viewport)
    identity_source = getattr(viewport, "_sr_identity_source", None)
    if identity_source is None:
        identity_snapshot = None
    else:
        snapshot = getattr(identity_source, "snapshot", None)
        if not callable(snapshot):
            raise RuntimeError("active identity source snapshot owner unavailable")
        identity_snapshot = copy.deepcopy(snapshot())
    audits = copy.deepcopy(list(getattr(viewport, "_sr_script_entropy_audits", ())))
    receipts = copy.deepcopy(list(getattr(viewport, "_sr_script_entropy_receipts", ())))
    trust_denials = copy.deepcopy(list(getattr(viewport, "_sr_script_trust_denials", ())))
    failure_receipts = copy.deepcopy(
        list(getattr(viewport, "_sr_script_failure_receipts", ()))
    )
    declared_paths = copy.deepcopy(
        list(getattr(viewport, "_sr_script_declared_paths", ()))
    )
    owner_digest_builder = getattr(viewport, "_script_owner_registry_digest", None)
    owner_digest = owner_digest_builder() if callable(owner_digest_builder) else None
    from .world_bridge_randomness_authority import (
        build_sr_script_owner_graph_digest,
        build_sr_script_execution_receipts,
        build_script_evidence_digest,
        validate_sr_script_randomness_owner_graph,
    )
    sr_owner = getattr(viewport, "_sr_runtime_rng", None)
    graph = validate_sr_script_randomness_owner_graph(
        getattr(viewport, "scene_runtime_entities", ()), sr_owner
    )
    if graph != {"valid": True, "errors": []}:
        raise RuntimeError(
            "SR script randomness owner graph is not checkpointable: "
            + ", ".join(graph["errors"])
        )
    script_owner_graph_digest = build_sr_script_owner_graph_digest(
        getattr(viewport, "scene_runtime_entities", ())
    )
    execution_receipts = build_sr_script_execution_receipts(
        getattr(viewport, "scene_runtime_entities", ())
    )
    project_path = getattr(viewport, "_sr_runtime_project_path", None)
    project_manifest = {}
    if project_path:
        try:
            project_manifest = json.loads(
                (Path(project_path) / "project.json").read_text(encoding="utf-8")
            )
        except (OSError, UnicodeError, json.JSONDecodeError):
            project_manifest = {}
    from core.Lotucosm.script_entropy_audit import (
        build_dynamic_script_boundary_receipt,
        build_project_script_inventory,
    )
    script_inventory = build_project_script_inventory(
        project_manifest,
        project_path=project_path,
        scene_script_paths=declared_paths,
        loaded_receipts=receipts,
        trust_denials=trust_denials,
        failure_receipts=failure_receipts,
    )
    boundary_receipt = build_dynamic_script_boundary_receipt(
        audits, receipts, trust_denials, failure_receipts
    )
    script_evidence = {
        "schema_version": 1,
        "runtime_epoch": str(viewport._sr_runtime_epoch),
        "audits": audits,
        "receipts": receipts,
        "trust_denials": trust_denials,
        "failure_receipts": failure_receipts,
        "declared_paths": declared_paths,
        "inventory": script_inventory,
        "owner_stream_name": "sr.runtime" if callable(owner_digest_builder) else None,
        "owner_registry_digest": owner_digest,
        "owner_graph_digest": script_owner_graph_digest,
        "execution_receipts": execution_receipts,
        "boundary_receipt": boundary_receipt,
        "evidence_digest": build_script_evidence_digest(
            audits, receipts, trust_denials, failure_receipts, declared_paths,
            script_inventory, execution_receipts, boundary_receipt
        ),
    }
    from core.Lotucosm.script_entropy_audit import (
        validate_project_script_inventory,
        validate_script_descriptor_coverage,
        validate_script_evidence_corpus,
    )
    corpus = validate_script_evidence_corpus(
        audits, receipts, trust_denials, failure_receipts
    )
    if corpus != {"valid": True, "errors": []}:
        raise RuntimeError(
            "script evidence corpus is incomplete: " + ", ".join(corpus["errors"])
        )
    descriptor_coverage = validate_script_descriptor_coverage(
        declared_paths, audits, receipts, trust_denials, failure_receipts
    )
    if descriptor_coverage != {"valid": True, "errors": []}:
        raise RuntimeError(
            "script descriptor coverage is incomplete: "
            + ", ".join(descriptor_coverage["errors"])
        )
    inventory_coverage = validate_project_script_inventory(
        script_inventory,
            project_path=project_path,
        loaded_receipts=receipts,
        trust_denials=trust_denials,
        failure_receipts=failure_receipts,
    )
    if inventory_coverage != {"valid": True, "errors": []}:
        raise RuntimeError(
            "project script inventory is incomplete: "
            + ", ".join(inventory_coverage["errors"])
        )
    lifecycle = {
        "runtime_epoch": str(viewport._sr_runtime_epoch),
        "scene_path": viewport._sr_runtime_scene_path,
        "scene_time": float(viewport._scene_runtime_time),
        "playing": bool(viewport.is_playing),
        "paused": bool(viewport.is_paused),
        "unified_pond_mode": bool(viewport._unified_pond_mode),
        "identity_source": identity_snapshot,
        "script_failure_receipts": failure_receipts,
        "script_evidence": script_evidence,
    }
    from .world_bridge_script_checkpoint import (
        ScriptCheckpointUnavailable,
        capture_sr_script_checkpoint,
    )

    entities = getattr(viewport, "scene_runtime_entities", ())
    has_scripts = any(
        bool(getattr(entity, "scripts", None)) for entity in entities
    )
    if isinstance(project_path, str) and project_path and has_scripts:
        try:
            lifecycle["script_graph"] = capture_sr_script_checkpoint(
                runtime_epoch=str(viewport._sr_runtime_epoch),
                project_path=project_path,
                entities=entities,
            )
        except ScriptCheckpointUnavailable:
            # Non-file scripts cannot be reconstructed by this overlay. Existing
            # script-evidence fail-closed behavior remains in force.
            pass
    sequence = getattr(viewport, "_worldbridge_input_sequence", None)
    pause_epoch = getattr(sequence, "pause_reset_epoch", None)
    if isinstance(pause_epoch, int) and not isinstance(pause_epoch, bool) and pause_epoch >= 0:
        lifecycle["input_pause_reset_epoch"] = pause_epoch
    runtime_binding = _capture_project_runtime_binding(viewport)
    if runtime_binding is not None:
        lifecycle["project_runtime_binding"] = runtime_binding
    provider = getattr(viewport, "_project_addon_lifecycle_evidence", None)
    if not callable(provider):
        context = getattr(viewport, "editor_context", None)
        loader = getattr(context, "plugin_loader", None)
        host = getattr(loader, "project_scoped_plugin_host", None)
        provider = getattr(host, "lifecycle_evidence", None)
    if callable(provider):
        addon_evidence = provider()
        if addon_evidence is not None:
            _validate_addon_lifecycle_evidence(addon_evidence)
            lifecycle["project_addon_lifecycle_evidence"] = copy.deepcopy(addon_evidence)
    from .world_bridge_component_identity import capture_worldbridge_component_identity_links
    lifecycle["component_identity_links"] = capture_worldbridge_component_identity_links(
        getattr(viewport, "scene_runtime_entities", ()), viewport._unified_pond
    )
    component_identity_artifact = getattr(
        viewport, "_worldbridge_component_identity_artifact", None
    )
    if component_identity_artifact is not None:
        from .world_bridge_component_identity_artifact import (
            validate_worldbridge_component_identity_artifact,
        )
        artifact_validation = validate_worldbridge_component_identity_artifact(
            component_identity_artifact
        )
        if not artifact_validation["valid"]:
            raise RuntimeError(
                "component identity artifact is invalid: "
                + ",".join(artifact_validation["errors"])
            )
        lifecycle["component_identity_artifact"] = copy.deepcopy(
            component_identity_artifact
        )
    gate_provider = getattr(viewport, "worldbridge_owner_gate_snapshot", None)
    if callable(gate_provider):
        from .world_bridge_owner_gate import (
            validate_worldbridge_owner_gate_snapshot,
        )

        gate_snapshot = gate_provider()
        validation = validate_worldbridge_owner_gate_snapshot(gate_snapshot)
        if validation != {"valid": True, "errors": []}:
            raise RuntimeError(
                "worldbridge owner gate snapshot is invalid: "
                + ",".join(validation["errors"])
            )
        lifecycle["owner_gate_snapshot"] = copy.deepcopy(gate_snapshot)
    return lifecycle


def _capture_project_runtime_binding(viewport: Any) -> dict[str, Any] | None:
    project_path = getattr(viewport, "_sr_runtime_project_path", None)
    runtime_epoch = getattr(viewport, "_sr_runtime_epoch", None)
    scene_path = getattr(viewport, "_sr_runtime_scene_path", None)
    if not all(isinstance(value, str) and value.strip() for value in (project_path, runtime_epoch, scene_path)):
        return None
    try:
        project_lock = json.loads(
            (Path(project_path) / "project.lock.json").read_text(encoding="utf-8")
        )
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise RuntimeError("worldbridge_project_runtime_binding_unavailable")
    from .world_bridge_component_identity_persistence import (
        build_worldbridge_project_runtime_binding,
    )
    return build_worldbridge_project_runtime_binding(
        project_path=str(project_path), project_lock=project_lock,
        runtime_epoch=str(runtime_epoch), scene_path=str(scene_path),
    )


def _validate_project_runtime_binding_for_restore(viewport: Any, state: Mapping[str, Any]) -> None:
    expected_project = getattr(viewport, "_sr_runtime_project_path", None)
    if not isinstance(expected_project, str) or not expected_project.strip():
        return
    binding = state.get("project_runtime_binding")
    if binding is None:
        diagnostic = _build_restore_diagnostic("project_runtime_binding_missing", ["runtime_binding_missing"])
        viewport._worldbridge_restore_diagnostic = diagnostic
        raise RuntimeError("worldbridge_project_runtime_binding_rejected: runtime_binding_missing")
    try:
        project_lock = json.loads(
            (Path(expected_project) / "project.lock.json").read_text(encoding="utf-8")
        )
    except (OSError, UnicodeError, json.JSONDecodeError):
        diagnostic = _build_restore_diagnostic("project_runtime_binding_unavailable", ["project_lock_unavailable"])
        viewport._worldbridge_restore_diagnostic = diagnostic
        raise RuntimeError("worldbridge_project_runtime_binding_rejected: project_lock_unavailable")
    from .world_bridge_component_identity_persistence import (
        validate_worldbridge_project_runtime_binding,
    )
    validation = validate_worldbridge_project_runtime_binding(
        binding, project_path=str(expected_project), project_lock=project_lock,
        runtime_epoch=str(viewport._sr_runtime_epoch),
        scene_path=str(viewport._sr_runtime_scene_path),
    )
    if not validation["valid"]:
        diagnostic = _build_restore_diagnostic(
            "project_runtime_binding_rejected", list(validation["errors"])
        )
        viewport._worldbridge_restore_diagnostic = diagnostic
        raise RuntimeError(
            "worldbridge_project_runtime_binding_rejected: "
            + ",".join(validation["errors"])
        )


def _build_restore_diagnostic(code: str, errors: list[str]) -> dict[str, Any]:
    payload = {"schema_version": 1, "code": code, "errors": list(errors)}
    digest = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()
    return {**payload, "diagnostic_digest": digest}


def _validate_addon_lifecycle_evidence(evidence: object) -> dict[str, Any]:
    if not isinstance(evidence, Mapping):
        raise ValueError("project addon lifecycle evidence must be a mapping")
    required = {
        "schema_version", "project_path", "discovery", "lifecycle",
        "addon_runtime_receipts", "digest",
    }
    if set(evidence) != required or evidence.get("schema_version") != 1:
        raise ValueError("project addon lifecycle evidence schema mismatch")
    if not isinstance(evidence.get("project_path"), str):
        raise ValueError("project addon lifecycle project path is invalid")
    if not isinstance(evidence.get("discovery"), Mapping) or not isinstance(
        evidence.get("lifecycle"), Mapping
    ) or not isinstance(evidence.get("addon_runtime_receipts"), list):
        raise ValueError("project addon lifecycle evidence payload is invalid")
    digest = evidence.get("digest")
    expected = hashlib.sha256(
        json.dumps(
            {**dict(evidence), "digest": ""},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    if not isinstance(digest, str) or digest != expected:
        raise ValueError("project addon lifecycle evidence digest mismatch")
    return copy.deepcopy(dict(evidence))


def _validate_current_addon_lifecycle_evidence(viewport: Any, evidence: object) -> None:
    expected = _validate_addon_lifecycle_evidence(evidence)
    provider = getattr(viewport, "_project_addon_lifecycle_evidence", None)
    if not callable(provider):
        context = getattr(viewport, "editor_context", None)
        loader = getattr(context, "plugin_loader", None)
        host = getattr(loader, "project_scoped_plugin_host", None)
        provider = getattr(host, "lifecycle_evidence", None)
    if not callable(provider):
        raise RuntimeError("project addon lifecycle evidence owner unavailable")
    current = _validate_addon_lifecycle_evidence(provider())
    if current.get("digest") != expected.get("digest"):
        raise RuntimeError("project addon lifecycle evidence digest mismatch")


def _validate_script_evidence(
    evidence: object,
    *,
    runtime_epoch: str,
    legacy_failure_receipts: object,
    viewport: Any,
) -> dict[str, Any] | None:
    if evidence is None:
        return None
    if not isinstance(evidence, Mapping):
        raise ValueError("script evidence envelope must be a mapping")
    required = {
        "schema_version",
        "runtime_epoch",
        "audits",
        "receipts",
        "trust_denials",
        "failure_receipts",
        "owner_stream_name",
        "owner_registry_digest",
        "owner_graph_digest",
        "execution_receipts",
        "boundary_receipt",
        "evidence_digest",
        "declared_paths",
        "inventory",
    }
    if set(evidence) != required or evidence.get("schema_version") != 1:
        raise ValueError("script evidence envelope schema mismatch")
    if evidence.get("runtime_epoch") != runtime_epoch:
        raise RuntimeError("script evidence envelope epoch mismatch")
    for field in (
        "audits", "receipts", "trust_denials", "failure_receipts", "declared_paths", "inventory", "execution_receipts"
    ):
        if not isinstance(evidence.get(field), list):
            raise ValueError(f"script evidence {field} must be a list")
    from core.Lotucosm.script_entropy_audit import (
        validate_project_script_inventory,
        validate_script_descriptor_coverage,
        validate_script_evidence_corpus,
    )
    corpus = validate_script_evidence_corpus(
        evidence["audits"],
        evidence["receipts"],
        evidence["trust_denials"],
        evidence["failure_receipts"],
    )
    if corpus != {"valid": True, "errors": []}:
        raise ValueError(
            "script evidence corpus is incomplete: " + ", ".join(corpus["errors"])
        )
    descriptor_coverage = validate_script_descriptor_coverage(
        evidence["declared_paths"],
        evidence["audits"],
        evidence["receipts"],
        evidence["trust_denials"],
        evidence["failure_receipts"],
    )
    if descriptor_coverage != {"valid": True, "errors": []}:
        raise ValueError(
            "script descriptor coverage is incomplete: "
            + ", ".join(descriptor_coverage["errors"])
        )
    inventory_coverage = validate_project_script_inventory(
        evidence["inventory"],
        project_path=getattr(viewport, "_sr_runtime_project_path", None),
        loaded_receipts=evidence["receipts"],
        trust_denials=evidence["trust_denials"],
        failure_receipts=evidence["failure_receipts"],
    )
    if inventory_coverage != {"valid": True, "errors": []}:
        raise ValueError(
            "project script inventory is incomplete: "
            + ", ".join(inventory_coverage["errors"])
        )
    from .world_bridge_randomness_authority import validate_sr_script_execution_receipts
    execution_validation = validate_sr_script_execution_receipts(
        evidence["execution_receipts"]
    )
    if execution_validation != {"valid": True, "errors": []}:
        raise ValueError(
            "script execution receipts are invalid: "
            + ", ".join(execution_validation["errors"])
        )
    from core.Lotucosm.script_entropy_audit import validate_dynamic_script_boundary_receipt
    boundary_validation = validate_dynamic_script_boundary_receipt(
        evidence["boundary_receipt"]
    )
    if boundary_validation != {"valid": True, "errors": []}:
        raise ValueError(
            "dynamic script boundary receipt is invalid: "
            + ", ".join(boundary_validation["errors"])
        )
    if evidence.get("failure_receipts") != legacy_failure_receipts:
        raise ValueError("script evidence failure receipt mismatch")
    from .world_bridge_randomness_authority import build_script_evidence_digest
    expected_evidence_digest = build_script_evidence_digest(
        evidence["audits"],
        evidence["receipts"],
        evidence["trust_denials"],
        evidence["failure_receipts"],
        evidence["declared_paths"],
        evidence["inventory"],
        evidence["execution_receipts"],
        evidence["boundary_receipt"],
    )
    if evidence.get("evidence_digest") != expected_evidence_digest:
        raise ValueError("script evidence digest mismatch")
    from .world_bridge_randomness_authority import build_sr_script_owner_graph_digest
    current_graph_digest = build_sr_script_owner_graph_digest(
        getattr(viewport, "scene_runtime_entities", ())
    )
    if evidence.get("owner_graph_digest") != current_graph_digest:
        raise RuntimeError("script owner graph digest mismatch")
    from .world_bridge_randomness_authority import build_sr_script_execution_receipts
    current_execution_receipts = build_sr_script_execution_receipts(
        getattr(viewport, "scene_runtime_entities", ())
    )
    structural_fields = (
        "execution_path", "owner_stream_name", "owner_family", "owner_mode", "lifecycle"
    )
    if [
        {field: item.get(field) for field in structural_fields}
        for item in evidence["execution_receipts"]
    ] != [
        {field: item.get(field) for field in structural_fields}
        for item in current_execution_receipts
    ]:
        raise RuntimeError("script execution receipt mismatch")
    stream_name = evidence.get("owner_stream_name")
    digest = evidence.get("owner_registry_digest")
    if (stream_name is None) != (digest is None):
        raise ValueError("script evidence owner binding is incomplete")
    if digest is not None:
        if not isinstance(stream_name, str) or stream_name != "sr.runtime":
            raise ValueError("script evidence owner stream mismatch")
        if not isinstance(digest, str) or len(digest) != 64 or any(
            char not in "0123456789abcdef" for char in digest
        ):
            raise ValueError("script evidence owner digest invalid")
        builder = getattr(viewport, "_script_owner_registry_digest", None)
        if not callable(builder) or builder() != digest:
            raise RuntimeError("script evidence owner registry mismatch")
    return copy.deepcopy(dict(evidence))


def _validate_script_failure_receipts(
    receipts: object,
    *,
    runtime_epoch: str,
) -> list[dict[str, Any]]:
    if not isinstance(receipts, list):
        raise ValueError("script failure receipts must be a list")
    required = {
        "schema_version",
        "status",
        "path",
        "phase",
        "reason",
        "exception_type",
        "runtime_epoch",
        "entropy_evidence_committed",
        "identity_or_pond_mutation",
    }
    prepared: list[dict[str, Any]] = []
    for index, receipt in enumerate(receipts):
        if not isinstance(receipt, Mapping) or set(receipt) != required:
            raise ValueError(f"script failure receipt {index} schema mismatch")
        if receipt.get("schema_version") != 1 or receipt.get("status") != "script_runtime_failure":
            raise ValueError(f"script failure receipt {index} status mismatch")
        if receipt.get("runtime_epoch") != runtime_epoch:
            raise RuntimeError(f"script failure receipt {index} epoch mismatch")
        for field in ("path", "phase", "reason"):
            if not isinstance(receipt.get(field), str):
                raise ValueError(f"script failure receipt {index}.{field} invalid")
        exception_type = receipt.get("exception_type")
        if exception_type is not None and not isinstance(exception_type, str):
            raise ValueError(f"script failure receipt {index}.exception_type invalid")
        if not isinstance(receipt.get("entropy_evidence_committed"), bool) or not isinstance(
            receipt.get("identity_or_pond_mutation"), bool
        ):
            raise ValueError(f"script failure receipt {index} mutation flags invalid")
        prepared.append(copy.deepcopy(dict(receipt)))
    return prepared


def _restore_lifecycle(viewport: Any, state: Mapping[str, Any]) -> None:
    _require_active(viewport)
    if not isinstance(state, Mapping):
        raise TypeError("lifecycle state must be a mapping")
    if state.get("runtime_epoch") != viewport._sr_runtime_epoch:
        viewport._worldbridge_restore_diagnostic = {
            **_build_restore_diagnostic(
                "project_runtime_binding_rejected",
                ["runtime_binding_runtime_epoch_mismatch"],
            )
        }
        raise RuntimeError("live checkpoint runtime epoch mismatch")
    if state.get("scene_path") != viewport._sr_runtime_scene_path:
        viewport._worldbridge_restore_diagnostic = {
            **_build_restore_diagnostic(
                "project_runtime_binding_rejected",
                ["runtime_binding_scene_path_mismatch"],
            )
        }
        raise RuntimeError("live checkpoint scene path mismatch")
    _validate_project_runtime_binding_for_restore(viewport, state)
    if state.get("unified_pond_mode") is not True:
        raise ValueError("live checkpoint unified Pond mode mismatch")
    scene_time = state.get("scene_time")
    if isinstance(scene_time, bool):
        raise ValueError("scene_time must be numeric")
    try:
        scene_time_value = float(scene_time)
    except (TypeError, ValueError) as exc:
        raise ValueError("scene_time must be numeric") from exc
    if scene_time_value < 0:
        raise ValueError("scene_time must be non-negative")
    if not isinstance(state.get("playing"), bool) or not isinstance(state.get("paused"), bool):
        raise ValueError("lifecycle flags must be boolean")
    script_graph = state.get("script_graph")
    if script_graph is not None:
        from .world_bridge_script_checkpoint import (
            restore_sr_script_checkpoint,
        )

        project_path = getattr(viewport, "_sr_runtime_project_path", None)
        if not isinstance(project_path, str) or not project_path.strip():
            raise ValueError("SR script graph restore requires project path")
        script_restore_result = restore_sr_script_checkpoint(
            script_graph,
            runtime_epoch=str(viewport._sr_runtime_epoch),
            project_path=project_path,
            entities=getattr(viewport, "scene_runtime_entities", ()),
            instantiate_script=lambda descriptor: viewport._instantiate_scene_script(
                descriptor,
                project_path,
            ),
        )
        viewport._worldbridge_script_checkpoint_restore_result = copy.deepcopy(
            script_restore_result
        )
    failure_receipts = _validate_script_failure_receipts(
        state.get("script_failure_receipts", []),
        runtime_epoch=str(viewport._sr_runtime_epoch),
    )
    script_evidence = _validate_script_evidence(
        state.get("script_evidence"),
        runtime_epoch=str(viewport._sr_runtime_epoch),
        legacy_failure_receipts=state.get("script_failure_receipts", []),
        viewport=viewport,
    )
    addon_evidence = state.get("project_addon_lifecycle_evidence")
    if addon_evidence is not None:
        _validate_current_addon_lifecycle_evidence(viewport, addon_evidence)
    component_identity_links = state.get("component_identity_links", [])
    if not isinstance(component_identity_links, list):
        raise ValueError("component identity links must be a list")
    component_identity_artifact = state.get("component_identity_artifact")
    if component_identity_artifact is not None:
        from .world_bridge_component_identity_artifact import (
            validate_worldbridge_component_identity_artifact,
        )
        artifact_validation = validate_worldbridge_component_identity_artifact(
            component_identity_artifact
        )
        if not artifact_validation["valid"]:
            viewport._worldbridge_restore_diagnostic = {
                **_build_restore_diagnostic(
                    "component_identity_artifact_rejected",
                    list(artifact_validation["errors"]),
                )
            }
            raise ValueError(
                "component identity artifact is invalid: "
                + ",".join(artifact_validation["errors"])
            )
    from .world_bridge_component_identity import validate_worldbridge_component_identity_against_live
    validate_worldbridge_component_identity_against_live(
        component_identity_links,
        getattr(viewport, "scene_runtime_entities", ()),
        viewport._unified_pond,
    )
    identity_source = getattr(viewport, "_sr_identity_source", None)
    has_identity_snapshot = "identity_source" in state
    identity_snapshot = state.get("identity_source")
    if identity_source is None:
        if has_identity_snapshot and identity_snapshot is not None:
            raise ValueError("legacy UUID lifecycle cannot restore deterministic identity state")
    else:
        if not has_identity_snapshot or identity_snapshot is None:
            raise RuntimeError("deterministic identity checkpoint state is missing")
        restore = getattr(identity_source, "restore", None)
        snapshot = getattr(identity_source, "snapshot", None)
        if not callable(restore) or not callable(snapshot):
            raise RuntimeError("active identity source restore owner unavailable")
        original_identity_snapshot = copy.deepcopy(snapshot())
        try:
            # DeterministicIdentitySource validates the complete snapshot before
            # replacing its counters, so invalid input cannot partially mutate it.
            restore(copy.deepcopy(identity_snapshot))
        except Exception:
            try:
                restore(original_identity_snapshot)
            except Exception as compensation_error:
                raise RuntimeError("identity source restore compensation failed") from compensation_error
            raise
    viewport._sr_script_failure_receipts = failure_receipts
    if script_evidence is not None:
        viewport._sr_script_entropy_audits = copy.deepcopy(script_evidence["audits"])
        viewport._sr_script_entropy_receipts = copy.deepcopy(script_evidence["receipts"])
        viewport._sr_script_trust_denials = copy.deepcopy(script_evidence["trust_denials"])
        viewport._sr_script_declared_paths = copy.deepcopy(
            script_evidence["declared_paths"]
        )
        entities = getattr(viewport, "scene_runtime_entities", ())
        for receipt in script_evidence["execution_receipts"]:
            match = re.fullmatch(
                r"scene_runtime_entities\[(\d+)\]\.scripts\[(\d+)\]",
                str(receipt["execution_path"]),
            )
            if match is None:
                raise ValueError("script execution receipt path is invalid")
            entity_index, script_index = (int(value) for value in match.groups())
            try:
                script = entities[entity_index].scripts[script_index]
            except (IndexError, AttributeError, TypeError) as exc:
                raise RuntimeError("script execution receipt target missing") from exc
            if hasattr(script, "_randomness_execution_ticks"):
                script._randomness_execution_ticks = int(receipt["execution_ticks"])
            if hasattr(script, "_randomness_consumption_count"):
                script._randomness_consumption_count = int(receipt["consumption_count"])
    viewport._scene_runtime_time = scene_time_value
    viewport.is_playing = state["playing"]
    viewport.is_paused = state["paused"]
    if "component_identity_artifact" in state:
        viewport._worldbridge_component_identity_artifact = copy.deepcopy(
            component_identity_artifact
        )


__all__ = [
    "PS_SIDE_OVERLAY_KEYS",
    "build_game_viewport_live_checkpoint_adapter_contract",
    "canonical_ps_serializer_projection",
    "create_game_viewport_live_checkpoint_adapters",
]
