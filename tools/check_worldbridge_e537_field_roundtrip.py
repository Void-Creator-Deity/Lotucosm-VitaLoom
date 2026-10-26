# -*- coding: utf-8 -*-
"""E537 SR/PS field round-trip measurement gate (measurement only).

For every field declared in the worldbridge mutation owner contract this
instrument seeds a distinctive baseline on the live lane owner, captures an
opt-in live checkpoint, perturbs the same live owner, restores the checkpoint
and re-reads the owner.  Each field/lane record states whether the live owner
exposes the field, whether the field was actually mutated, and whether the
captured checkpoint restored it.

The instrument is read-only with respect to production policy: it never opens
an admission and never claims replay or lossless authority.  Declared fields
without a safe reversible live mutation API are reported as ``no_mutation_api``
together with their observed live value.

Every matrix cell is cross-classified against the mutation owner contract.  A
cell whose field is declared ``covered`` with ``checkpoint_scope ==
"sr_state_and_ps_state"`` is a *capture contract* cell: the live checkpoint is
required to restore it, so ``lost_on_restore`` there is a real defect, is
reported in ``capture_contract_violations`` and fails the gate.  A cell whose
field is declared partial / creation_only / not_mapped / lane_local is not
required to survive a checkpoint, so a loss there is the declared phase-3 gap
rather than a defect.  Capture contract cells whose lane owner does not expose
the field at all are reported separately in ``owner_contract_findings`` and do
not fail the gate on their own.
"""
from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Mapping
from typing import Any, Callable

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from _runtime_bootstrap import install_runtime_paths
except ModuleNotFoundError:
    from tools._runtime_bootstrap import install_runtime_paths

ROOT = Path(__file__).resolve().parents[1]
install_runtime_paths(ROOT)

from PyQt6.QtWidgets import QApplication

from core.Lotucosm.memory import MemoryGene
from core.Lotucosm.runtime.world_bridge import iter_bridged_entities
from core.Lotucosm.runtime.world_bridge_mutation_authority import (
    build_worldbridge_mutation_owner_contract,
)
from core.Lotucosm.sr_memory_gene_bridge import (
    memory_genes_from_dicts,
    memory_genes_to_dicts,
    replace_entity_memory_genes,
)

try:
    from tools.check_worldbridge_e505_fresh_host_reconstruction import _new_viewport
except ModuleNotFoundError:
    from check_worldbridge_e505_fresh_host_reconstruction import _new_viewport


ADMISSION_KEYS = ("atomic_checkpoint", "lossless", "replay_admitted", "default_ready")
TOLERANCE = 1e-6


class OwnerAbsent(Exception):
    """The live lane owner does not expose the probed field."""


def _closed_admissions(node: object, path: str = "") -> list[str]:
    """Return every location where a closed admission is not actually closed."""
    open_paths: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            here = f"{path}.{key}" if path else str(key)
            if key in ADMISSION_KEYS and value is not False:
                open_paths.append(here)
            open_paths.extend(_closed_admissions(value, here))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            open_paths.extend(_closed_admissions(value, f"{path}[{index}]"))
    return open_paths


CAPTURE_SCOPE = "sr_state_and_ps_state"
OWNER_ABSENT_VERDICTS = ("lane_owner_absent", "owner_absent")


def _contract_requirement(entry: dict[str, Any]) -> tuple[str, str, bool]:
    """Return (declared state, declared checkpoint scope, capture required)."""
    state = str(entry.get("state", ""))
    scope = str(entry.get("checkpoint_scope", ""))
    return state, scope, state == "covered" and scope == CAPTURE_SCOPE


def _classify_cells(
    matrix: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    """Split capture-contract cells into required, violated and owner findings."""
    required = [
        item for item in matrix if item.get("contract_requirement") == "capture_required"
    ]
    violations = [
        f"{item['field']}:{item['lane']}"
        for item in required
        if str(item["verdict"]) == "lost_on_restore"
    ]
    findings = [
        f"{item['field']}:{item['lane']}"
        for item in required
        if str(item["verdict"]).startswith(OWNER_ABSENT_VERDICTS)
    ]
    return required, violations, findings


def _close(left: Any, right: Any) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return left is right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=TOLERANCE)
    if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
        return len(left) == len(right) and all(_close(a, b) for a, b in zip(left, right))
    if isinstance(left, dict) and isinstance(right, dict):
        return set(left) == set(right) and all(_close(left[k], right[k]) for k in left)
    return left == right


def _portable(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, (list, tuple)):
        return [_portable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _portable(item) for key, item in value.items()}
    return value


def _attr(target: Any, name: str) -> Any:
    if not hasattr(target, name):
        raise OwnerAbsent(name)
    return getattr(target, name)


def _scalar(value: Any) -> float:
    if value is None:
        raise OwnerAbsent("scalar_missing")
    return float(value)


def _vec2(value: Any) -> list[float]:
    if value is None:
        raise OwnerAbsent("vector_missing")
    return [float(value[0]), float(value[1])]


class _E537ScriptA:
    """Minimal executable probe carrying a caller-owned RNG binding."""

    def __init__(self, owner: Any = None) -> None:
        self.randomness_rng = owner
        self.randomness_owner_mode = "runtime"


class _E537ScriptB(_E537ScriptA):
    """A distinct script identity so the owner graph digest changes."""


def _write_sr_scripts(target: Any, viewport: Any, value: Any) -> None:
    owner = getattr(viewport, "_sr_runtime_rng", None)
    target.replace_scripts([script_type(owner) for script_type in value])


def _write_ps_scripts(target: Any, viewport: Any, value: Any) -> None:
    pond = getattr(viewport, "_unified_pond", None)
    owner = getattr(pond, "randomness_rng", None)
    target.replace_scripts([script_type(owner) for script_type in value])


def _script_kinds(target: Any) -> dict[str, Any]:
    scripts = _attr(target, "scripts")
    if not isinstance(scripts, list):
        raise OwnerAbsent("scripts_not_a_list")
    return {
        "count": len(scripts),
        "kinds": sorted(type(item).__name__ for item in scripts),
    }


def _entity_genes(target: Any, attribute: str) -> list[dict[str, Any]]:
    genes = getattr(target, attribute, None)
    if genes is None:
        raise OwnerAbsent(attribute)
    return memory_genes_to_dicts(list(genes))


def _probe_genes(situation: str, rate: float) -> list[dict[str, Any]]:
    return memory_genes_to_dicts([MemoryGene(situation, {"move": 1.0}, rate)])


def _membrane_graph_probe(label: str, spawn_seq: int, channel: int) -> dict[str, Any]:
    """Return a partial override for the live SR topology owner graph."""
    return {
        "spawn_seq": int(spawn_seq),
        "membrane_template": {f"e537-{label}": [{"channel": int(channel)}]},
    }


def _sr_render_identity(entity: Any, viewport: Any) -> dict[str, Any]:
    visual = getattr(entity, "sr_visual", None)
    if visual is None:
        raise OwnerAbsent("sr_visual")
    return {
        "flip_x": bool(getattr(visual, "flip_x", False)),
        "alpha": float(getattr(visual, "alpha", 1.0)),
    }


def _write_sr_render_identity(entity: Any, viewport: Any, value: Any) -> None:
    visual = getattr(entity, "sr_visual", None)
    if visual is None:
        raise OwnerAbsent("sr_visual")
    visual.flip_x = bool(value["flip_x"])
    visual.alpha = float(value["alpha"])


def _sr_membrane_graph(entity: Any, viewport: Any) -> dict[str, Any]:
    capture = getattr(viewport, "capture_sr_topology_owner_state", None)
    if not callable(capture):
        raise OwnerAbsent("sr_membrane_topology")
    state = capture()
    if not isinstance(state, dict):
        raise OwnerAbsent("sr_membrane_topology")
    attach = state.get("membrane_attach")
    template = state.get("membrane_template")
    entry = attach.get(str(getattr(entity, "id", ""))) if isinstance(attach, dict) else None
    return {
        "attached": entry is not None,
        "template_count": len(template) if isinstance(template, dict) else 0,
        "structural_edge_count": len(state.get("structural_edges") or []),
        "signal_edge_count": len(state.get("signal_edges") or []),
        "spawn_seq": int(state.get("spawn_seq", 0)),
    }


def _write_sr_membrane_graph(entity: Any, viewport: Any, value: Any) -> None:
    """Apply a partial override onto the live SR topology owner graph.

    The probe never fabricates a synthetic graph: it reads the real owner
    state and writes back a modified copy, so entity ids, membrane
    attachments and edges stay consistent with the running scene.
    """
    capture = getattr(viewport, "capture_sr_topology_owner_state", None)
    restore = getattr(viewport, "restore_sr_topology_owner_state", None)
    if not callable(capture) or not callable(restore):
        raise OwnerAbsent("sr_membrane_topology")
    if not isinstance(value, Mapping):
        raise OwnerAbsent("sr_membrane_topology_probe")
    merged = capture()
    merged.update(value)
    restore(merged)


def _ps_hierarchy(target: Any, viewport: Any) -> dict[str, Any]:
    children = getattr(target, "children", None)
    if children is None:
        raise OwnerAbsent("children")
    parent = getattr(target, "parent", None)
    return {
        "parent": None if parent is None else str(getattr(parent, "id", parent)),
        "children": [str(getattr(child, "id", child)) for child in list(children)],
    }


def _write_ps_hierarchy(target: Any, viewport: Any, value: Any) -> None:
    """Replay a PS entity-child order directive with rollback.

    Two layouts are used so the checkpoint must reproduce the exact captured
    child order: ``rotate`` moves the last child to the front, while
    ``component_order`` re-derives the layout from the serialized component
    mapping (which is what a hierarchical-restore-free payload would produce).
    """
    if not isinstance(value, Mapping):
        raise TypeError("hierarchy probe must be a mapping")
    mode = str(value.get("mode", ""))
    add_child = getattr(target, "add_child", None)
    remove_child = getattr(target, "remove_child", None)
    if not callable(add_child) or not callable(remove_child):
        raise OwnerAbsent("hierarchy_mutation_api")
    before = list(getattr(target, "children", []) or [])
    before_parents = {id(child): getattr(child, "parent", None) for child in before}
    try:
        children = list(getattr(target, "children", []) or [])
        components = getattr(target, "components", None)
        component_order: list[Any] = []
        if isinstance(components, Mapping):
            for component_id in components:
                for child in children:
                    if str(getattr(child, "id", child)) == str(component_id):
                        component_order.append(child)
                        break
        if mode == "rotate":
            desired = children[-1:] + children[:-1]
        elif mode == "component_order":
            desired = component_order + [child for child in children if child not in component_order]
        else:
            raise ValueError(f"unknown hierarchy probe mode {mode!r}")
        for child in children:
            remove_child(child)
        for child in desired:
            add_child(child)
    except Exception:
        for child in list(getattr(target, "children", []) or []):
            if child not in before:
                remove_child(child)
        for child in before:
            if child not in getattr(target, "children", []):
                add_child(child)
        for child in before:
            child.parent = before_parents[id(child)]
        raise
    return None


def _ps_component_graph(target: Any, viewport: Any) -> dict[str, Any]:
    components = getattr(target, "components", None)
    if components is None:
        raise OwnerAbsent("components")
    component_ids = [str(component_id) for component_id in components]
    membrane = getattr(target, "membrane", None)
    membrane_id = None if membrane is None else str(getattr(membrane, "id", ""))
    return {
        "component_count": len(component_ids),
        "component_ids": component_ids,
        "component_parent_ids": [
            None
            if getattr(component, "parent", None) is None
            else str(getattr(component.parent, "id", component.parent))
            for component in components.values()
        ],
        "membrane_attached": membrane is not None,
        "membrane_id": membrane_id,
    }


def _write_ps_component_graph(target: Any, viewport: Any, value: Any) -> None:
    """Apply a relative component-graph override through the PS owner API.

    The probe never fabricates component ids: it derives the replacement set
    from the live owner and the directive, then delegates the whole graph write
    (component set plus membrane reference) to
    ``Organism.replace_component_graph`` so a failed attach cannot leak a
    partially replaced graph.
    """
    if not isinstance(value, Mapping):
        raise OwnerAbsent("ps_component_graph_probe")
    components = getattr(target, "components", None)
    if not isinstance(components, Mapping):
        raise OwnerAbsent("components")
    writer = getattr(target, "replace_component_graph", None)
    if not callable(writer):
        raise OwnerAbsent("ps_component_graph_mutation_api")
    mode = str(value.get("mode", ""))
    live = list(components.values())
    if mode == "single":
        replacement = live[:1]
    elif mode == "all":
        replacement = list(live)
    elif mode == "all_reversed":
        replacement = list(reversed(live))
    elif mode == "rotate":
        replacement = live[-1:] + live[:-1]
    elif mode == "detached":
        replacement = list(live[1:]) + list(live[:1])
    elif mode == "empty":
        replacement = []
    else:
        raise ValueError(f"unknown PS component graph probe mode {mode!r}")
    membrane = getattr(target, "membrane", None)
    if mode == "detached":
        membrane = None
    elif mode == "empty":
        membrane = None if membrane is None else live[0] if live else None
    writer(replacement, membrane)


@dataclass(frozen=True)
class LaneSpec:
    """One field on one lane: live read plus an optional reversible write."""

    read: Callable[[Any, Any], Any]
    write: Callable[[Any, Any, Any], None] | None
    seed: Any = None
    perturb: Any = None
    fail_closed_on_restore: bool = False


def _field_probes() -> dict[str, dict[str, LaneSpec]]:
    sr: dict[str, LaneSpec] = {
        "position": LaneSpec(
            read=lambda t, v: _vec2(_attr(t, "position")),
            write=lambda t, v, value: t.set_position(value),
            seed=[101.0, 97.0],
            perturb=[151.0, 173.0],
        ),
        "energy": LaneSpec(
            read=lambda t, v: _scalar(_attr(t, "energy")),
            write=lambda t, v, value: t.set_energy(value),
            seed=41.5,
            perturb=78.25,
        ),
        "health": LaneSpec(
            read=lambda t, v: _scalar(_attr(t, "health")),
            write=lambda t, v, value: t.set_health(value),
            seed=31.0,
            perturb=63.0,
        ),
        "max_energy": LaneSpec(
            read=lambda t, v: _scalar(_attr(t, "max_energy")),
            write=lambda t, v, value: t.set_max_energy(value),
            seed=150.0,
            perturb=175.0,
        ),
        "max_health": LaneSpec(
            read=lambda t, v: _scalar(_attr(t, "max_health")),
            write=lambda t, v, value: t.set_max_health(value),
            seed=120.0,
            perturb=140.0,
        ),
        "size_radius": LaneSpec(
            read=lambda t, v: _scalar(_attr(t, "radius")),
            write=lambda t, v, value: t.set_radius(value),
            seed=25.0,
            perturb=33.5,
        ),
        "velocity_acceleration": LaneSpec(
            read=lambda t, v: [
                _vec2(_attr(t, "velocity")),
                _vec2(_attr(t, "acceleration")),
            ],
            write=lambda t, v, value: (
                t.set_velocity(value[0]),
                t.set_acceleration(value[1]),
            ),
            seed=[[3.0, 4.0], [0.5, -0.5]],
            perturb=[[9.0, 11.0], [1.5, -1.5]],
        ),
        "render_identity": LaneSpec(
            read=_sr_render_identity,
            write=_write_sr_render_identity,
            seed={"flip_x": True, "alpha": 0.5},
            perturb={"flip_x": False, "alpha": 0.25},
        ),
        "active_visible_state": LaneSpec(
            read=lambda t, v: [bool(_attr(t, "active")), bool(_attr(t, "visible"))],
            write=lambda t, v, value: (
                setattr(t, "active", bool(value[0])),
                setattr(t, "visible", bool(value[1])),
            ),
            seed=[False, False],
            perturb=[True, True],
        ),
        "developmental_profile": LaneSpec(
            read=lambda t, v: int(_attr(t, "developmental_stage")),
            write=lambda t, v, value: t.set_developmental_stage(value),
            seed=2,
            perturb=4,
        ),
        "social_enabled": LaneSpec(
            read=lambda t, v: bool(_attr(t, "social_learning_enabled")),
            write=lambda t, v, value: t.set_social_learning_enabled(value),
            seed=True,
            perturb=False,
        ),
        "scripts": LaneSpec(
            read=lambda t, v: _script_kinds(t),
            write=_write_sr_scripts,
            seed=[_E537ScriptA],
            perturb=[_E537ScriptA, _E537ScriptB],
            fail_closed_on_restore=True,
        ),
        "memory_genes": LaneSpec(
            read=lambda t, v: _entity_genes(t, "sr_memory_genes"),
            write=lambda t, v, value: replace_entity_memory_genes(
                t, memory_genes_from_dicts(value)
            ),
            seed=_probe_genes("e537-probe", 0.25),
            perturb=_probe_genes("e537-perturb", 0.75),
        ),
        "membrane_component_graph": LaneSpec(
            read=_sr_membrane_graph,
            write=_write_sr_membrane_graph,
            seed=_membrane_graph_probe("e537-probe", 3, 11),
            perturb=_membrane_graph_probe("e537-perturb", 5, 23),
        ),
    }
    ps: dict[str, LaneSpec] = {
        "position": LaneSpec(
            read=lambda t, v: _vec2(_attr(t, "position")),
            write=lambda t, v, value: t.set_position(value),
            seed=[101.0, 97.0],
            perturb=[151.0, 173.0],
        ),
        "energy": LaneSpec(
            read=lambda t, v: _scalar(_attr(t, "energy")),
            write=lambda t, v, value: t.set_energy(value),
            seed=41.5,
            perturb=78.25,
        ),
        "health": LaneSpec(
            read=lambda t, v: _scalar(_attr(t, "health")),
            write=lambda t, v, value: t.set_health(value),
            seed=31.0,
            perturb=63.0,
        ),
        "max_energy": LaneSpec(
            read=lambda t, v: _scalar(_attr(t, "max_energy")),
            write=lambda t, v, value: t.set_max_energy(value),
            seed=150.0,
            perturb=175.0,
        ),
        "max_health": LaneSpec(
            read=lambda t, v: _scalar(_attr(t, "max_health")),
            write=lambda t, v, value: t.set_max_health(value),
            seed=120.0,
            perturb=140.0,
        ),
        "size_radius": LaneSpec(
            read=lambda t, v: [_scalar(_attr(t, "size")), _scalar(_attr(t, "radius"))],
            write=lambda t, v, value: (t.set_size(value[0]), t.set_radius(value[1])),
            seed=[25.0, 25.0],
            perturb=[33.5, 33.5],
        ),
        "velocity_acceleration": LaneSpec(
            read=lambda t, v: [
                _vec2(_attr(t, "velocity")),
                _vec2(_attr(t, "acceleration")),
            ],
            write=lambda t, v, value: (
                t.set_velocity(value[0]),
                t.set_acceleration(value[1]),
            ),
            seed=[[3.0, 4.0], [0.5, -0.5]],
            perturb=[[9.0, 11.0], [1.5, -1.5]],
        ),
        "developmental_profile": LaneSpec(
            read=lambda t, v: int(_attr(t, "developmental_stage")),
            write=lambda t, v, value: setattr(t, "developmental_stage", int(value)),
            seed=2,
            perturb=4,
        ),
        "social_enabled": LaneSpec(
            read=lambda t, v: bool(_attr(t, "social_learning_enabled")),
            write=lambda t, v, value: setattr(
                t, "social_learning_enabled", bool(value)
            ),
            seed=True,
            perturb=False,
        ),
        "active_visible_state": LaneSpec(
            read=lambda t, v: [bool(_attr(t, "active")), bool(_attr(t, "visible"))],
            write=lambda t, v, value: (
                setattr(t, "active", bool(value[0])),
                setattr(t, "visible", bool(value[1])),
            ),
            seed=[False, False],
            perturb=[True, True],
        ),
        "scripts": LaneSpec(
            read=lambda t, v: _script_kinds(t),
            write=_write_ps_scripts,
            seed=[_E537ScriptA],
            perturb=[_E537ScriptA, _E537ScriptB],
        ),
        "memory_genes": LaneSpec(
            read=lambda t, v: _entity_genes(t, "memory_genes"),
            write=lambda t, v, value: t.replace_memory_genes(
                memory_genes_from_dicts(value)
            ),
            seed=_probe_genes("e537-probe", 0.25),
            perturb=_probe_genes("e537-perturb", 0.75),
        ),
        "hierarchy": LaneSpec(
            read=_ps_hierarchy,
            write=_write_ps_hierarchy,
            seed={"mode": "rotate"},
            perturb={"mode": "component_order"},
        ),
        "membrane_component_graph": LaneSpec(
            read=_ps_component_graph,
            write=_write_ps_component_graph,
            seed={"mode": "all"},
            perturb={"mode": "single"},
        ),
    }
    return {"sr": sr, "ps": ps}


TOOL_FAILURE_MARKERS = ("_failed:", "restore_failed", "read_failed")


def _probe_field(
    field_name: str,
    lane: str,
    spec: LaneSpec,
    resolve: Callable[[], Any],
    viewport: Any,
    counter: list[int],
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "field": field_name,
        "lane": lane,
        "available": False,
        "mutated": False,
        "restored": False,
        "verdict": "unavailable",
    }
    try:
        target = resolve()
    except Exception as exc:
        record["verdict"] = f"owner_absent:{type(exc).__name__}"
        return record
    if target is None:
        record["verdict"] = "owner_absent"
        return record
    try:
        observed = spec.read(target, viewport)
    except OwnerAbsent as exc:
        record["verdict"] = f"owner_absent:{exc}"
        return record
    except Exception as exc:
        record["verdict"] = f"read_failed:{type(exc).__name__}"
        return record
    record["available"] = True
    record["observed"] = _portable(observed)
    if spec.write is None:
        record["verdict"] = "no_mutation_api"
        return record
    try:
        spec.write(target, viewport, spec.seed)
        baseline = spec.read(target, viewport)
    except OwnerAbsent as exc:
        record["verdict"] = f"owner_absent:{exc}"
        return record
    except Exception as exc:
        record["verdict"] = f"seed_failed:{type(exc).__name__}"
        return record
    try:
        transaction = viewport.capture_worldbridge_live_checkpoint_transaction(
            f"e537-{field_name}-{lane}-{counter[0]}"
        )
    except Exception as exc:
        record["verdict"] = f"capture_failed:{type(exc).__name__}:{exc}"
        return record
    checkpoint = transaction.checkpoint
    counter[0] += 1
    try:
        spec.write(target, viewport, spec.perturb)
        perturbed = spec.read(target, viewport)
    except Exception as exc:
        record["verdict"] = f"perturb_failed:{type(exc).__name__}"
        return record
    if _close(perturbed, baseline):
        record["verdict"] = "not_writable"
        return record
    record["mutated"] = True
    if spec.fail_closed_on_restore:
        # The portable checkpoint cannot carry executable script objects; the
        # only sound contract is that a drifted live script graph is rejected
        # and the live owner survives the rejected restore unchanged.
        try:
            viewport.restore_worldbridge_live_checkpoint_transaction(
                transaction
            )
        except Exception as exc:
            after_reject = spec.read(target, viewport)
            record["live_preserved_on_reject"] = _close(after_reject, perturbed)
            record["after_reject"] = _portable(after_reject)
            record["rejection"] = f"{type(exc).__name__}"
            record["restored"] = False
            record["verdict"] = "fail_closed_restore"
            return record
        record["verdict"] = "fail_closed_not_enforced"
        return record
    try:
        viewport.restore_worldbridge_live_checkpoint_transaction(transaction)
    except Exception as exc:
        record["verdict"] = f"restore_failed:{type(exc).__name__}:{exc}"
        return record
    try:
        after_target = resolve()
        after = spec.read(after_target, viewport)
    except Exception as exc:
        record["verdict"] = f"read_after_restore_failed:{type(exc).__name__}"
        return record
    record["object_reidentified"] = after_target is not target
    record["restored"] = _close(after, baseline)
    record["after_restore"] = _portable(after)
    record["verdict"] = "restored" if record["restored"] else "lost_on_restore"
    return record


def _capture_scope(viewport: Any, entity_id: str, organism_id: str) -> dict[str, Any]:
    checkpoint = viewport.capture_worldbridge_live_checkpoint("e537-scope")
    sr_keys: list[str] = []
    sr_state = checkpoint.get("sr_state")
    if isinstance(sr_state, dict):
        envelope = sr_state.get("runtime_restore_envelope")
        if isinstance(envelope, dict):
            for snapshot in envelope.get("snapshots", []):
                if str(snapshot.get("entity_id")) == entity_id:
                    sr_keys = sorted(str(key) for key in snapshot)
                    break
    ps_keys: list[str] = []
    ps_state = checkpoint.get("ps_state")
    if isinstance(ps_state, dict):
        organisms = ps_state.get("organisms")
        if isinstance(organisms, dict) and isinstance(organisms.get(organism_id), dict):
            ps_keys = sorted(str(key) for key in organisms[organism_id])
        elif isinstance(organisms, list):
            for item in organisms:
                if not isinstance(item, dict):
                    continue
                identifier = item.get("id", item.get("organism_id"))
                if str(identifier) == organism_id:
                    ps_keys = sorted(str(key) for key in item)
                    break
    return {"sr_snapshot_keys": sr_keys, "ps_organism_keys": ps_keys}


def verify() -> dict[str, object]:
    app = QApplication.instance() or QApplication([])
    project = ROOT / "workspace" / "projects" / "samples" / "pvaec-细胞演化"
    scene = project / "scenes" / "challenge_scene.pond"
    viewport = _new_viewport(project, scene, "e537-field-roundtrip")
    for _ in range(2):
        viewport._update_simulation()

    pond = viewport._ensure_unified_pond()
    probe_pair = None
    for entity, organism_id in iter_bridged_entities(viewport.scene_runtime_entities):
        if organism_id in pond.organisms:
            probe_pair = (entity, organism_id)
            break
    if probe_pair is None:
        raise AssertionError("E537 field round-trip requires a bridged SR/PS pair")
    entity_id = str(getattr(probe_pair[0], "id", ""))
    organism_id = str(probe_pair[1])

    def resolve_sr() -> Any:
        for entity in viewport.scene_runtime_entities:
            if str(getattr(entity, "id", "")) == entity_id:
                return entity
        raise OwnerAbsent("sr_entity_missing")

    def resolve_ps() -> Any:
        current = viewport._ensure_unified_pond()
        organism = current.organisms.get(organism_id)
        if organism is None:
            raise OwnerAbsent("ps_organism_missing")
        return organism

    contract = build_worldbridge_mutation_owner_contract()
    declared = contract["fields"]
    probes = _field_probes()
    counter = [0]
    matrix: list[dict[str, Any]] = []
    failures: list[str] = []
    for name in sorted(declared):
        entry = declared[name]
        state, declared_scope, capture_required = _contract_requirement(entry)
        requirement = "capture_required" if capture_required else "not_required"
        for lane in ("sr", "ps"):
            spec = probes[lane].get(name)
            if spec is None:
                matrix.append(
                    {
                        "field": name,
                        "declared_state": state,
                        "declared_checkpoint_scope": declared_scope,
                        "contract_requirement": requirement,
                        "lane": lane,
                        "available": False,
                        "mutated": False,
                        "restored": False,
                        "verdict": "lane_owner_absent",
                        "contract_consistent": not capture_required,
                    }
                )
                continue
            record = _probe_field(
                name,
                lane,
                spec,
                resolve_sr if lane == "sr" else resolve_ps,
                viewport,
                counter,
            )
            record["declared_state"] = state
            record["declared_checkpoint_scope"] = declared_scope
            record["contract_requirement"] = requirement
            verdict = str(record["verdict"])
            record["contract_consistent"] = (not capture_required) or verdict == "restored"
            matrix.append(record)
            if any(marker in verdict for marker in TOOL_FAILURE_MARKERS):
                failures.append(f"{name}:{lane}:{verdict}")

    scope = _capture_scope(viewport, entity_id, organism_id)
    status = __import__(
        "core.VitaLoom.simulation.runtime_worldbridge_status",
        fromlist=["build_runtime_worldbridge_status"],
    ).build_runtime_worldbridge_status(project)
    open_admissions = _closed_admissions(status)

    restored = [item for item in matrix if item["verdict"] == "restored"]
    lost = [item for item in matrix if item["verdict"] == "lost_on_restore"]
    fail_closed = [
        item
        for item in matrix
        if item["verdict"] in ("fail_closed_restore", "fail_closed_not_enforced")
    ]
    fail_closed_enforced = [
        item for item in matrix if item["verdict"] == "fail_closed_restore"
    ]
    fail_closed_leaks = [
        item
        for item in matrix
        if item["verdict"] == "fail_closed_not_enforced"
        or item.get("live_preserved_on_reject") is False
    ]
    absent = [
        item
        for item in matrix
        if str(item["verdict"]).startswith(("lane_owner_absent", "owner_absent"))
    ]
    no_api = [item for item in matrix if item["verdict"] == "no_mutation_api"]
    not_writable = [item for item in matrix if item["verdict"] == "not_writable"]

    required_cells, capture_violations, owner_findings = _classify_cells(matrix)

    errors = list(failures)
    errors.extend(
        f"fail_closed_not_enforced:{item['field']}:{item['lane']}"
        for item in fail_closed_leaks
    )
    errors.extend(f"capture_contract_violation:{cell}" for cell in capture_violations)
    if open_admissions:
        errors.append("runtime_admission_opened")

    return {
        "schema_version": 2,
        "status": "worldbridge_e537_field_roundtrip",
        "real_game_viewport": True,
        "read_only": True,
        "probe_entity_id": entity_id,
        "probe_organism_id": organism_id,
        "declared_field_count": len(declared),
        "matrix_cell_count": len(matrix),
        "restored_cells": len(restored),
        "lost_cells": len(lost),
        "owner_absent_cells": len(absent),
        "no_mutation_api_cells": len(no_api),
        "not_writable_cells": len(not_writable),
        "fail_closed_cells": len(fail_closed),
        "fail_closed_enforced_cells": len(fail_closed_enforced),
        "fail_closed_leaks": [
            f"{item['field']}:{item['lane']}" for item in fail_closed_leaks
        ],
        "declared_checkpoint_scopes": {
            name: str(declared[name].get("checkpoint_scope", "")) for name in sorted(declared)
        },
        "capture_required_cells": len(required_cells),
        "capture_restored_cells": len(
            [item for item in required_cells if str(item["verdict"]) == "restored"]
        ),
        "capture_contract_violations": capture_violations,
        "owner_contract_findings": owner_findings,
        "checkpoint_scope": scope,
        "matrix": matrix,
        "runtime_admissions_closed": not open_admissions,
        "atomic_checkpoint": False,
        "lossless": False,
        "replay_admitted": False,
        "default_ready": False,
        "errors": errors,
        "ok": not errors,
    }


def main() -> int:
    result = verify()
    print(json.dumps(result, ensure_ascii=False, allow_nan=False, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
