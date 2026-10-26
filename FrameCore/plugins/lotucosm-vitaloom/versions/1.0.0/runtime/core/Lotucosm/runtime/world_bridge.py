# -*- coding: utf-8
"""Phase C.4 统一 Pond 接缝（ADR-0005 桩 + 最小映射试点）。

职责: SR 显示实体 ↔ PS Organism 的 position/energy 同步；完整组件映射未实现。
时机: project.json runtime_mode == unified_pond 时试点。
排错: 见 docs/adr/0005-unified-pond-bridge.md。
"""
from __future__ import annotations

import inspect
import copy
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence

from .world_bridge_field_mapper import (
    DEFAULT_WORLD_BRIDGE_FIELD_MAPPER,
    InvalidOrganismCreationSeed,
    build_organism_creation_seed,
    sync_organism_to_sr_display,
    sync_sr_entity_to_organism,
    developmental_profile_from_spawn_request as _extract_developmental_profile,
)

RUNTIME_MODE_DUAL = "dual"
RUNTIME_MODE_UNIFIED = "unified_pond"

BRIDGE_ORGANISM_ATTR = "_world_bridge_organism_id"


class WorldBridgeNotReadyError(NotImplementedError):
    """Bridge 完整映射未评审通过。"""


def resolve_runtime_mode(project_config: Optional[dict[str, Any]]) -> str:
    if not project_config:
        return RUNTIME_MODE_DUAL
    mode = str(project_config.get("runtime_mode", RUNTIME_MODE_DUAL) or RUNTIME_MODE_DUAL)
    return mode if mode in (RUNTIME_MODE_DUAL, RUNTIME_MODE_UNIFIED) else RUNTIME_MODE_DUAL


def unified_pond_enabled(project_config: Optional[dict[str, Any]]) -> bool:
    return resolve_runtime_mode(project_config) == RUNTIME_MODE_UNIFIED


def sr_entity_to_organism(
    entity: Any,
    pond: Any,
    *,
    profile: Any = None,
    equip_pvaec: bool = False,
) -> Any:
    """SR 实体 → PS Organism（试点：仅 position/energy/developmental 字段）。"""
    from builtin.entity_types.organism import Organism

    try:
        seed = build_organism_creation_seed(entity)
    except InvalidOrganismCreationSeed as exc:
        raise WorldBridgeNotReadyError("实体缺少 position，无法桥接。") from exc
    eid = str(getattr(entity, "id", "unknown"))
    oid = f"bridge_{eid}"
    organisms = getattr(pond, "organisms", None)
    add = getattr(pond, "add_organism", None)
    if not callable(add) or not hasattr(organisms, "get"):
        raise WorldBridgeNotReadyError("Pond 缺少可验证的 organism 注册接口。")
    if organisms.get(oid) is not None:
        raise WorldBridgeNotReadyError(f"Pond 已存在 organism id: {oid}")
    org = Organism(
        oid,
        seed.position,
        energy=seed.energy,
        max_energy=seed.max_energy,
        health=seed.health,
        max_health=seed.max_health,
        size=seed.size,
        active=seed.active,
        **seed.kinematic_kwargs(),
    )
    set_radius = getattr(org, "set_radius", None)
    if callable(set_radius):
        set_radius(seed.radius)
    else:
        org.radius = seed.radius
    dev_profile = None
    if isinstance(profile, dict):
        dev_profile = profile.get("developmental")
    elif profile is not None:
        dev_profile = profile
    if isinstance(dev_profile, dict):
        from core.Lotucosm.ps_developmental import apply_developmental_profile_to_organism

        apply_developmental_profile_to_organism(org, dev_profile)
    DEFAULT_WORLD_BRIDGE_FIELD_MAPPER.copy_creation_memory_genes(entity, org)
    if equip_pvaec:
        try:
            from builtin.systems.organism_builder import equip_ps_organism

            equip_ps_organism(org, enable_pvaec_cycle=True)
        except Exception:
            pass
    from .world_bridge_component_identity import bind_worldbridge_component_identity_links
    bind_worldbridge_component_identity_links(entity, org)
    registered = add(org)
    if registered is False or organisms.get(oid) is not org:
        raise WorldBridgeNotReadyError(f"Pond 未注册桥接 organism: {oid}")
    setattr(entity, BRIDGE_ORGANISM_ATTR, oid)
    return org


def developmental_profile_from_spawn_request(req: Mapping[str, Any]) -> dict[str, Any]:
    """Compatibility facade for field mapper spawn-profile extraction."""
    return _extract_developmental_profile(req)


def apply_bridge_profile_to_organism(organism: Any, profile: Mapping[str, Any]) -> None:
    DEFAULT_WORLD_BRIDGE_FIELD_MAPPER.apply_spawn_profile(profile, organism)


def ensure_bridged_organisms(
    sr_organism_entities: Iterable[Any],
    pond: Any,
    *,
    profile: Optional[Mapping[str, Any]] = None,
    equip_pvaec: bool = False,
) -> int:
    """为尚未桥接的 SR organism hub 创建 PS Organism。"""
    created = 0
    orgs = getattr(pond, "organisms", None) or {}
    for ent in sr_organism_entities:
        if str(getattr(ent, "entity_type", "")) != "organism":
            continue
        oid = getattr(ent, BRIDGE_ORGANISM_ATTR, None)
        if oid and hasattr(orgs, "get") and orgs.get(oid) is not None:
            continue
        sr_entity_to_organism(
            ent,
            pond,
            profile=profile,
            equip_pvaec=equip_pvaec,
        )
        created += 1
    return created


def bridge_spawned_organism(
    entity: Any,
    pond: Any,
    spawn_request: Mapping[str, Any],
    *,
    equip_pvaec: bool = True,
) -> Any:
    """繁殖 spawn 后绑定 PS Organism（子代 developmental 从 props 读取）。"""
    if "component_identity_links" in spawn_request:
        links = spawn_request["component_identity_links"]
        if not isinstance(links, list):
            raise ValueError("spawn component_identity_links must be a list")
        # The declaration is an explicit runtime receipt source.  It is kept
        # on the SR entity so later live capture can revalidate the same data.
        setattr(entity, "_world_bridge_component_identity_links", copy.deepcopy(links))
    profile = developmental_profile_from_spawn_request(spawn_request)
    org = sr_entity_to_organism(entity, pond, profile=profile, equip_pvaec=equip_pvaec)
    apply_bridge_profile_to_organism(org, profile)
    return org


def iter_bridged_entities(entities: Iterable[Any]) -> list[tuple[Any, str]]:
    out: list[tuple[Any, str]] = []
    for ent in entities:
        oid = getattr(ent, BRIDGE_ORGANISM_ATTR, None)
        if oid:
            out.append((ent, str(oid)))
    return out


def capture_bridge_identity_links(entities: Iterable[Any]) -> list[dict[str, str]]:
    """Capture detached SR-to-PS identity links without live object references."""
    links: list[dict[str, str]] = []
    seen_sr: set[str] = set()
    seen_ps: set[str] = set()
    for entity in entities:
        sr_id = str(getattr(entity, "id", "")).strip()
        ps_id = getattr(entity, BRIDGE_ORGANISM_ATTR, None)
        if not sr_id or not isinstance(ps_id, str) or not ps_id.strip():
            continue
        ps_id = ps_id.strip()
        if sr_id in seen_sr or ps_id in seen_ps:
            raise ValueError("duplicate bridge identity link")
        seen_sr.add(sr_id)
        seen_ps.add(ps_id)
        links.append({"sr_entity_id": sr_id, "ps_organism_id": ps_id})
    return sorted(links, key=lambda item: (item["sr_entity_id"], item["ps_organism_id"]))


def restore_bridge_identity_links(
    entities: Iterable[Any],
    pond: Any,
    links: Iterable[Mapping[str, Any]],
    *,
    replace_existing: bool = False,
) -> None:
    """Validate and apply identity links atomically to an existing SR set.

    This restores only the SR attribute and verifies PS registration. It does
    not create organisms, restore their state, or claim cross-lane replay.
    ``replace_existing`` removes links absent from the supplied baseline while
    retaining the historical strict-subset behavior for existing callers.
    """
    entities = list(entities)
    entity_by_id: dict[str, Any] = {}
    for entity in entities:
        entity_id = str(getattr(entity, "id", "")).strip()
        if not entity_id or entity_id in entity_by_id:
            raise ValueError("duplicate or missing SR entity id")
        entity_by_id[entity_id] = entity
    organisms = getattr(pond, "organisms", None)
    if not hasattr(organisms, "get"):
        raise ValueError("pond.organisms registration map is unavailable")

    normalized: list[tuple[str, str]] = []
    seen_sr: set[str] = set()
    seen_ps: set[str] = set()
    for index, raw in enumerate(links):
        if not isinstance(raw, Mapping):
            raise TypeError(f"links[{index}] must be an object")
        sr_id = raw.get("sr_entity_id")
        ps_id = raw.get("ps_organism_id")
        if not isinstance(sr_id, str) or not sr_id.strip() or not isinstance(ps_id, str) or not ps_id.strip():
            raise ValueError(f"links[{index}] has invalid identity")
        sr_id, ps_id = sr_id.strip(), ps_id.strip()
        if sr_id in seen_sr or ps_id in seen_ps:
            raise ValueError("duplicate bridge identity link")
        if sr_id not in entity_by_id:
            raise ValueError(f"unknown SR entity id: {sr_id}")
        if organisms.get(ps_id) is None:
            raise ValueError(f"unknown PS organism id: {ps_id}")
        seen_sr.add(sr_id)
        seen_ps.add(ps_id)
        normalized.append((sr_id, ps_id))

    if replace_existing:
        affected_ids = set(entity_by_id)
    else:
        affected_ids = {sr_id for sr_id, _ in normalized}
    previous = {
        sr_id: getattr(entity_by_id[sr_id], BRIDGE_ORGANISM_ATTR, None)
        for sr_id in affected_ids
    }
    try:
        for sr_id in affected_ids:
            try:
                delattr(entity_by_id[sr_id], BRIDGE_ORGANISM_ATTR)
            except AttributeError:
                pass
        for sr_id, ps_id in normalized:
            setattr(entity_by_id[sr_id], BRIDGE_ORGANISM_ATTR, ps_id)
        captured = capture_bridge_identity_links(entity_by_id.values())
        expected = sorted(
            ({"sr_entity_id": sr_id, "ps_organism_id": ps_id} for sr_id, ps_id in normalized),
            key=lambda item: (item["sr_entity_id"], item["ps_organism_id"]),
        )
        if captured != expected:
            raise ValueError("bridge identity links changed during restore")
    except Exception:
        for sr_id, old_value in previous.items():
            if old_value is None:
                try:
                    delattr(entity_by_id[sr_id], BRIDGE_ORGANISM_ATTR)
                except AttributeError:
                    pass
            else:
                setattr(entity_by_id[sr_id], BRIDGE_ORGANISM_ATTR, old_value)
        raise


def _prepare_unified_pond_handoff(
    pond: Any,
    sr_entities: Iterable[Any],
    *,
    trace_requested: bool,
    require_callable_update: bool,
) -> tuple[list[Any], Any, Any, list[tuple[Any, str]]]:
    """Materialize existing public inputs before the first live synchronization.

    This is only a preflight boundary, not a transaction: current SR and PS
    public seams do not provide one complete shared checkpoint/restore API.
    Plain hand-offs retain their historical missing-update no-op behavior;
    trace production stays stricter because it needs a real fixed update.
    """
    from core.Lotucosm.runtime.world_bridge_transaction_authority import (
        PHASE_PREFLIGHT,
        WorldBridgeHandoffFailure,
    )

    try:
        entities = list(sr_entities)
        organisms = getattr(pond, "organisms", None) or {}
        update = getattr(pond, "update", None)
        if require_callable_update and not callable(update):
            raise TypeError("pond.update must be callable for live trace production")
        pairs = iter_bridged_entities(entities)
        if not trace_requested:
            seen_sr_ids: set[str] = set()
            seen_ps_ids: set[str] = set()
            for entity, organism_id in pairs:
                sr_id = getattr(entity, "id", None)
                if sr_id is not None:
                    sr_id = str(sr_id)
                    if sr_id in seen_sr_ids:
                        raise ValueError(f"duplicate sr_entity_id: {sr_id}")
                    seen_sr_ids.add(sr_id)
                if organism_id in seen_ps_ids:
                    raise ValueError(f"duplicate ps_organism_id: {organism_id}")
                seen_ps_ids.add(organism_id)
        return entities, organisms, update, pairs
    except WorldBridgeHandoffFailure:
        raise
    except Exception as exc:
        raise WorldBridgeHandoffFailure(
            PHASE_PREFLIGHT,
            exc,
            trace_requested=trace_requested,
            preflight_completed=False,
            sr_to_ps_sync_started=False,
            pond_update_started=False,
            ps_to_sr_reflection_started=False,
        ) from exc


def _raise_unified_pond_handoff_failure(
    phase: str,
    exc: BaseException,
    *,
    trace_requested: bool,
    sr_to_ps_sync_started: bool,
    pond_update_started: bool,
    ps_to_sr_reflection_started: bool,
) -> None:
    from core.Lotucosm.runtime.world_bridge_transaction_authority import WorldBridgeHandoffFailure

    if isinstance(exc, WorldBridgeHandoffFailure):
        raise exc
    raise WorldBridgeHandoffFailure(
        phase,
        exc,
        trace_requested=trace_requested,
        preflight_completed=True,
        sr_to_ps_sync_started=sr_to_ps_sync_started,
        pond_update_started=pond_update_started,
        ps_to_sr_reflection_started=ps_to_sr_reflection_started,
    ) from exc


def _require_stable_handoff_links(pairs: list[tuple[Any, str]]) -> None:
    for entity, organism_id in pairs:
        current = getattr(entity, BRIDGE_ORGANISM_ATTR, None)
        if current is None or str(current) != organism_id:
            raise ValueError(f"bridge binding changed during pond update: {organism_id}")


def _require_stable_pond_targets(
    pond: Any,
    pairs: list[tuple[Any, str]],
    targets: dict[str, Any],
    *,
    allow_removed: bool = False,
) -> None:
    if not pairs:
        return
    current = getattr(pond, "organisms", None)
    if not callable(getattr(current, "get", None)):
        raise ValueError("pond.organisms changed during handoff")
    for _, organism_id in pairs:
        actual = current.get(organism_id)
        if allow_removed and actual is None and targets[organism_id] is not None:
            continue
        if actual is not targets[organism_id]:
            raise ValueError(f"PS organism identity changed during pond update: {organism_id}")


def _invoke_clocked_pond_update(update: Callable[..., Any], delta_time: float) -> None:
    """Pass the shared delta to clock-aware ponds while preserving old adapters."""
    try:
        signature = inspect.signature(update)
        signature.bind(delta_time)
    except (TypeError, ValueError):
        update()
    else:
        update(delta_time)


def _unified_pond_step_impl(
    pond: Any,
    sr_entities: Iterable[Any],
    *,
    delta_time: float = 1.0,
    input_events: Sequence[Mapping[str, Any]] | None = None,
) -> None:
    """One ordered legacy SR/PS hand-off without compensating rollback.

    A preflight error happens before live synchronization. After a phase has
    begun, no shared rollback exists; the phase-labelled exception tells the
    caller what may already have mutated and later phases are not run.
    """
    from core.Lotucosm.runtime.world_bridge_transaction_authority import (
        PHASE_POND_UPDATE,
        PHASE_PS_TO_SR_REFLECTION,
        PHASE_SR_TO_PS_SYNC,
    )

    entities, organisms, update, pairs = _prepare_unified_pond_handoff(
        pond,
        sr_entities,
        trace_requested=False,
        require_callable_update=False,
    )
    targets = {organism_id: organisms.get(organism_id) for _, organism_id in pairs}
    sr_to_ps_sync_started = False
    pond_update_started = False
    ps_to_sr_reflection_started = False
    try:
        apply_inputs = getattr(pond, "apply_worldbridge_input_events", None)
        if input_events and not callable(apply_inputs):
            raise TypeError("pond must expose apply_worldbridge_input_events")
        if callable(apply_inputs):
            sr_to_ps_sync_started = True
            apply_inputs(list(input_events or []))
    except Exception as exc:
        _raise_unified_pond_handoff_failure(
            PHASE_SR_TO_PS_SYNC, exc, trace_requested=False,
            sr_to_ps_sync_started=sr_to_ps_sync_started, pond_update_started=False,
            ps_to_sr_reflection_started=False,
        )
    try:
        for entity, organism_id in pairs:
            organism = organisms.get(organism_id) if hasattr(organisms, "get") else None
            if organism is not None:
                sr_to_ps_sync_started = True
                sync_sr_entity_to_organism(entity, organism)
        _require_stable_handoff_links(pairs)
    except Exception as exc:
        _raise_unified_pond_handoff_failure(
            PHASE_SR_TO_PS_SYNC, exc, trace_requested=False,
            sr_to_ps_sync_started=sr_to_ps_sync_started,
            pond_update_started=pond_update_started,
            ps_to_sr_reflection_started=ps_to_sr_reflection_started,
        )

    if callable(update):
        pond_update_started = True
        try:
            _invoke_clocked_pond_update(update, delta_time)
        except Exception as exc:
            _raise_unified_pond_handoff_failure(
                PHASE_POND_UPDATE, exc, trace_requested=False,
                sr_to_ps_sync_started=sr_to_ps_sync_started,
                pond_update_started=pond_update_started,
                ps_to_sr_reflection_started=ps_to_sr_reflection_started,
            )

    try:
        _require_stable_handoff_links(pairs)
        _require_stable_pond_targets(pond, pairs, targets, allow_removed=True)
        for entity, organism_id in pairs:
            organism = organisms.get(organism_id) if hasattr(organisms, "get") else None
            if organism is not None:
                ps_to_sr_reflection_started = True
                sync_organism_to_sr_display(organism, entity)
    except Exception as exc:
        _raise_unified_pond_handoff_failure(
            PHASE_PS_TO_SR_REFLECTION, exc, trace_requested=False,
            sr_to_ps_sync_started=sr_to_ps_sync_started,
            pond_update_started=pond_update_started,
            ps_to_sr_reflection_started=ps_to_sr_reflection_started,
        )


def unified_pond_step(
    pond: Any,
    sr_entities: Iterable[Any],
    *,
    delta_time: float = 1.0,
    input_events: Sequence[Mapping[str, Any]] | None = None,
    transaction_coordinator: Any = None,
    mutation_preparation: Callable[[], Any] | None = None,
) -> None:
    """Run the existing handoff, optionally with verified compensation.

    Phase labels remain PHASE_SR_TO_PS_SYNC, PHASE_POND_UPDATE, and
    PHASE_PS_TO_SR_REFLECTION for the ordered handoff contract.

    The coordinator is opt-in; the default call remains the historical
    non-transactional path. A transactional call runs mutation preparation only
    after the pre-mutation checkpoint has been captured, so every preparation
    write is covered by the same rollback boundary.
    """
    if transaction_coordinator is None:
        if mutation_preparation is not None:
            mutation_preparation()
        return _unified_pond_step_impl(
            pond,
            sr_entities,
            delta_time=delta_time,
            input_events=input_events,
        )

    from core.Lotucosm.runtime.world_bridge_live_handoff_transaction import (
        create_worldbridge_live_handoff_transaction,
        execute_worldbridge_handoff_with_transaction,
    )
    entities = list(sr_entities)
    _prepare_unified_pond_handoff(
        pond,
        entities,
        trace_requested=False,
        require_callable_update=False,
    )
    sequence = getattr(pond, "time", 0)
    if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
        sequence = 0
    transaction = create_worldbridge_live_handoff_transaction(
        transaction_coordinator,
        checkpoint_id=f"worldbridge-handoff-{sequence}-{id(pond):x}",
        sequence=sequence,
    )
    _begin_worldbridge_transaction(transaction, trace_requested=False)

    def run_prepared_handoff() -> None:
        if mutation_preparation is not None:
            mutation_preparation()
        _unified_pond_step_impl(
            pond,
            entities,
            delta_time=delta_time,
            input_events=input_events,
        )

    return execute_worldbridge_handoff_with_transaction(
        transaction,
        run_prepared_handoff,
    )


def _unified_pond_step_with_trace_impl(
    pond: Any,
    sr_entities: Iterable[Any],
    *,
    sr_checkpoint: Mapping[str, Any],
    delta_time: float = 1.0,
    input_events: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run one ordered non-atomic hand-off and return an opt-in live trace."""
    from core.Lotucosm.runtime.world_bridge_live_trace_producer import (
        build_worldbridge_live_dual_lane_trace,
        capture_worldbridge_ps_checkpoint,
        capture_worldbridge_sr_checkpoint,
        collect_worldbridge_live_entity_links,
    )
    from core.Lotucosm.runtime.world_bridge_transaction_authority import (
        PHASE_POND_UPDATE,
        PHASE_PS_TO_SR_REFLECTION,
        PHASE_SR_TO_PS_SYNC,
        PHASE_TRACE_PS_CAPTURE,
        PHASE_TRACE_SR_CAPTURE,
    )

    entities, organisms, update, pairs = _prepare_unified_pond_handoff(
        pond,
        sr_entities,
        trace_requested=True,
        require_callable_update=True,
    )
    sr_to_ps_sync_started = False
    pond_update_started = False
    ps_to_sr_reflection_started = False
    # Existing trace-pair validation is a no-mutation admission check. Keep its
    # public ValueError semantics so stale/duplicate links remain distinguishable
    # from a live bridge phase failure.
    links = collect_worldbridge_live_entity_links(entities, pond)
    targets = {organism_id: organisms.get(organism_id) for _, organism_id in pairs}
    try:
        apply_inputs = getattr(pond, "apply_worldbridge_input_events", None)
        if input_events and not callable(apply_inputs):
            raise TypeError("pond must expose apply_worldbridge_input_events")
        if callable(apply_inputs):
            sr_to_ps_sync_started = True
            apply_inputs(list(input_events or []))
    except Exception as exc:
        _raise_unified_pond_handoff_failure(
            PHASE_SR_TO_PS_SYNC, exc, trace_requested=True,
            sr_to_ps_sync_started=False, pond_update_started=False,
            ps_to_sr_reflection_started=False,
        )
    try:
        sr_capture = capture_worldbridge_sr_checkpoint(sr_checkpoint, entities, links)
    except Exception as exc:
        _raise_unified_pond_handoff_failure(
            PHASE_TRACE_SR_CAPTURE, exc, trace_requested=True,
            sr_to_ps_sync_started=sr_to_ps_sync_started,
            pond_update_started=pond_update_started,
            ps_to_sr_reflection_started=ps_to_sr_reflection_started,
        )

    try:
        for entity, organism_id in pairs:
            organism = organisms.get(organism_id) if hasattr(organisms, "get") else None
            if organism is not None:
                sr_to_ps_sync_started = True
                sync_sr_entity_to_organism(entity, organism)
        _require_stable_handoff_links(pairs)
    except Exception as exc:
        _raise_unified_pond_handoff_failure(
            PHASE_SR_TO_PS_SYNC, exc, trace_requested=True,
            sr_to_ps_sync_started=sr_to_ps_sync_started,
            pond_update_started=pond_update_started,
            ps_to_sr_reflection_started=ps_to_sr_reflection_started,
        )

    pond_update_started = True
    try:
        _invoke_clocked_pond_update(update, delta_time)
    except Exception as exc:
        _raise_unified_pond_handoff_failure(
            PHASE_POND_UPDATE, exc, trace_requested=True,
            sr_to_ps_sync_started=sr_to_ps_sync_started,
            pond_update_started=pond_update_started,
            ps_to_sr_reflection_started=ps_to_sr_reflection_started,
        )

    try:
        _require_stable_pond_targets(pond, pairs, targets, allow_removed=True)
        ps_capture = capture_worldbridge_ps_checkpoint(pond, links)
    except Exception as exc:
        _raise_unified_pond_handoff_failure(
            PHASE_TRACE_PS_CAPTURE, exc, trace_requested=True,
            sr_to_ps_sync_started=sr_to_ps_sync_started,
            pond_update_started=pond_update_started,
            ps_to_sr_reflection_started=ps_to_sr_reflection_started,
        )

    try:
        _require_stable_handoff_links(pairs)
        for entity, organism_id in pairs:
            organism = organisms.get(organism_id) if hasattr(organisms, "get") else None
            if organism is not None:
                ps_to_sr_reflection_started = True
                sync_organism_to_sr_display(organism, entity)
    except Exception as exc:
        _raise_unified_pond_handoff_failure(
            PHASE_PS_TO_SR_REFLECTION, exc, trace_requested=True,
            sr_to_ps_sync_started=sr_to_ps_sync_started,
            pond_update_started=pond_update_started,
            ps_to_sr_reflection_started=ps_to_sr_reflection_started,
        )
    return build_worldbridge_live_dual_lane_trace(
        sr_capture,
        ps_capture,
        entity_links=links,
        observed_sr_delta=delta_time,
    )


def unified_pond_step_with_trace(
    pond: Any,
    sr_entities: Iterable[Any],
    *,
    sr_checkpoint: Mapping[str, Any],
    delta_time: float = 1.0,
    input_events: Sequence[Mapping[str, Any]] | None = None,
    transaction_coordinator: Any = None,
    mutation_preparation: Callable[[], Any] | None = None,
) -> dict[str, Any]:
    """Run the trace handoff, optionally with verified compensation.

    Phase labels remain PHASE_TRACE_SR_CAPTURE, PHASE_SR_TO_PS_SYNC,
    PHASE_POND_UPDATE, PHASE_TRACE_PS_CAPTURE, and
    PHASE_PS_TO_SR_REFLECTION for the ordered handoff contract.
    """
    if transaction_coordinator is None:
        if mutation_preparation is not None:
            mutation_preparation()
        return _unified_pond_step_with_trace_impl(
            pond,
            sr_entities,
            sr_checkpoint=sr_checkpoint,
            delta_time=delta_time,
            input_events=input_events,
        )

    from core.Lotucosm.runtime.world_bridge_live_handoff_transaction import (
        create_worldbridge_live_handoff_transaction,
        execute_worldbridge_handoff_with_transaction,
    )
    entities = list(sr_entities)
    _prepare_unified_pond_handoff(
        pond,
        entities,
        trace_requested=True,
        require_callable_update=True,
    )
    sequence = getattr(pond, "time", 0)
    if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
        sequence = 0
    transaction = create_worldbridge_live_handoff_transaction(
        transaction_coordinator,
        checkpoint_id=f"worldbridge-trace-{sequence}-{id(pond):x}",
        sequence=sequence,
    )
    _begin_worldbridge_transaction(transaction, trace_requested=True)

    def run_prepared_handoff() -> dict[str, Any]:
        if mutation_preparation is not None:
            mutation_preparation()
        return _unified_pond_step_with_trace_impl(
            pond,
            entities,
            sr_checkpoint=sr_checkpoint,
            delta_time=delta_time,
            input_events=input_events,
        )

    return execute_worldbridge_handoff_with_transaction(
        transaction,
        run_prepared_handoff,
    )


def _begin_worldbridge_transaction(transaction: Any, *, trace_requested: bool) -> None:
    from core.Lotucosm.runtime.world_bridge_transaction_authority import (
        PHASE_PREFLIGHT,
        WorldBridgeHandoffFailure,
    )

    try:
        transaction.begin()
    except Exception as exc:
        raise WorldBridgeHandoffFailure(
            PHASE_PREFLIGHT,
            exc,
            trace_requested=trace_requested,
            preflight_completed=False,
            sr_to_ps_sync_started=False,
            pond_update_started=False,
            ps_to_sr_reflection_started=False,
        ) from exc
