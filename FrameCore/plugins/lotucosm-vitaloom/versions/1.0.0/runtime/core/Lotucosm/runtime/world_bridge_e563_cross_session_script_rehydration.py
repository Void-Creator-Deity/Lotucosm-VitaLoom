# -*- coding: utf-8 -*-
"""Cross-session script source-bundle rehydration with explicit quarantine."""
from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from .world_bridge_e562_script_checkpoint_authority import (
    validate_worldbridge_e562_script_checkpoint_authority,
)
from .world_bridge_script_checkpoint import (
    retarget_sr_script_checkpoint,
    restore_sr_script_checkpoint,
    validate_sr_script_checkpoint,
)


SCHEMA_VERSION = 1
BUNDLE_STATUS = "worldbridge_sr_script_source_bundle"
RESTORE_STATUS = "worldbridge_e563_cross_session_script_restore"
WITNESS_STATUS = "worldbridge_e563_cross_session_script_rehydration_authority"
POLICY = "checkpoint_bound_source_bundle_or_quarantine_v1"
SCOPE = "cross_session_source_bundle_script_rehydration"
QUARANTINE_REASONS = (
    "source_missing",
    "version_mismatch",
    "bundle_tamper",
)
PROOF_FIELDS = (
    "base_checkpoint_valid",
    "source_bundle_valid",
    "fresh_rehydrated",
    "fresh_recaptured_graph_valid",
    "descriptors_equal",
    "restore_counts_equal",
    "source_bundle_bound_to_checkpoint",
    "all_quarantine_cases_fail_closed",
    "live_owner_preserved_on_reject",
)
CLOSED_ADMISSION_FIELDS = (
    "portable_sr_executable_script_checkpoint",
    "arbitrary_external_script_state_admitted",
    "atomic_sr_ps_checkpoint",
    "cross_process_atomicity",
)
REMAINING_SCRIPT_BLOCKERS = (
    "portable_sr_executable_script_checkpoint_not_proven",
    "arbitrary_external_script_state_not_admitted",
    "cross_process_atomicity_not_proven",
)
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_BUNDLE_KEYS = {
    "schema_version",
    "status",
    "policy",
    "runtime_contract_version",
    "checkpoint_graph_digest",
    "checkpoint_runtime_epoch",
    "project_identity",
    "sources",
    "bundle_digest",
}
_PROJECT_IDENTITY_KEYS = {
    "name",
    "version",
    "loom_editor_version",
    "required_packages",
    "capabilities",
}
_SOURCE_KEYS = {"path", "sha256"}
_RESTORE_KEYS = {
    "schema_version",
    "status",
    "read_only",
    "policy",
    "decision",
    "admitted",
    "runtime_contract_version",
    "target_runtime_epoch",
    "source_checkpoint_digest",
    "source_bundle_digest",
    "errors",
    "quarantine_reason",
    "live_owner_preserved",
    "restore_result",
}
_WITNESS_KEYS = {
    "schema_version",
    "status",
    "read_only",
    "scope",
    "policy",
    "runtime_contract_version",
    "base_script_checkpoint_witness",
    "source_bundle",
    "fresh_restore_result",
    "fresh_recaptured_script_graph",
    "quarantine_results",
    "source_graph_digest",
    "fresh_graph_digest",
    "source_bundle_digest",
    *PROOF_FIELDS,
    "remaining_script_blockers",
    "grants_admission",
    "cross_session_script_rehydration_admitted",
    *CLOSED_ADMISSION_FIELDS,
    "witness_digest",
}


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _json_copy(value: object, field: str) -> Any:
    try:
        return json.loads(_canonical(value).decode("utf-8"))
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{field} must be finite canonical JSON") from exc


def _mapping_copy(value: object, field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field} must be a mapping")
    copied = _json_copy(dict(value), field)
    if not isinstance(copied, dict):
        raise TypeError(f"{field} must remain a mapping")
    return copied


def _bundle_digest(value: Mapping[str, Any]) -> str:
    payload = dict(value)
    payload["bundle_digest"] = ""
    return _digest(payload)


def _witness_digest(value: Mapping[str, Any]) -> str:
    payload = dict(value)
    payload["witness_digest"] = ""
    return _digest(payload)


def _project_identity(project_path: str | Path) -> dict[str, Any]:
    project = Path(project_path).resolve()
    manifest_path = project / "project.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("project_manifest_unavailable") from exc
    if not isinstance(manifest, dict):
        raise ValueError("project_manifest_invalid")
    identity: dict[str, Any] = {}
    for key in ("name", "version", "loom_editor_version"):
        value = manifest.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"project_identity_{key}_invalid")
        identity[key] = value.strip()
    for key in ("required_packages", "capabilities"):
        values = manifest.get(key)
        if (
            not isinstance(values, list)
            or any(not isinstance(item, str) or not item for item in values)
            or len(set(values)) != len(values)
        ):
            raise ValueError(f"project_identity_{key}_invalid")
        identity[key] = sorted(values)
    return identity


def _checkpoint_sources(graph: Mapping[str, Any]) -> list[dict[str, str]]:
    sources: dict[str, str] = {}
    entities = graph.get("entities")
    if not isinstance(entities, list):
        raise ValueError("checkpoint_entities_invalid")
    for entity in entities:
        if not isinstance(entity, Mapping):
            raise ValueError("checkpoint_entity_invalid")
        scripts = entity.get("scripts")
        if not isinstance(scripts, list):
            raise ValueError("checkpoint_scripts_invalid")
        for script in scripts:
            if not isinstance(script, Mapping):
                raise ValueError("checkpoint_script_invalid")
            path = script.get("source_path")
            source_digest = script.get("source_sha256")
            if not isinstance(path, str) or not isinstance(source_digest, str):
                raise ValueError("checkpoint_source_invalid")
            previous = sources.get(path)
            if previous is not None and previous != source_digest:
                raise ValueError("checkpoint_source_digest_conflict")
            sources[path] = source_digest
    return [
        {"path": path, "sha256": sources[path]}
        for path in sorted(sources)
    ]


def build_cross_session_source_bundle(
    *,
    checkpoint_graph: Mapping[str, Any],
    project_path: str | Path,
    runtime_contract_version: str,
) -> dict[str, Any]:
    """Bind a checkpoint to portable project identity and source digests."""
    if (
        not isinstance(runtime_contract_version, str)
        or not runtime_contract_version.strip()
    ):
        raise ValueError("runtime_contract_version must be non-empty")
    graph = _mapping_copy(checkpoint_graph, "checkpoint_graph")
    graph_epoch = graph.get("runtime_epoch")
    if not isinstance(graph_epoch, str) or not graph_epoch:
        raise ValueError("checkpoint runtime_epoch invalid")
    validation = validate_sr_script_checkpoint(
        graph,
        runtime_epoch=graph_epoch,
    )
    if validation["valid"] is not True:
        raise ValueError(
            "checkpoint graph invalid: " + ",".join(validation["errors"])
        )
    bundle: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": BUNDLE_STATUS,
        "policy": POLICY,
        "runtime_contract_version": runtime_contract_version.strip(),
        "checkpoint_graph_digest": graph["graph_digest"],
        "checkpoint_runtime_epoch": graph_epoch,
        "project_identity": _project_identity(project_path),
        "sources": _checkpoint_sources(graph),
        "bundle_digest": "",
    }
    bundle["bundle_digest"] = _bundle_digest(bundle)
    return bundle


def _validate_sources_list(value: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, list):
        return ["source_bundle_sources_invalid"]
    seen: set[str] = set()
    previous = ""
    for index, source in enumerate(value):
        if not isinstance(source, Mapping) or set(source) != _SOURCE_KEYS:
            errors.append(f"source_bundle_source_{index}_invalid")
            continue
        path = source.get("path")
        source_digest = source.get("sha256")
        if (
            not isinstance(path, str)
            or not path
            or Path(path).is_absolute()
            or ".." in Path(path).parts
            or not path.casefold().startswith("scripts/")
            or not path.casefold().endswith(".py")
        ):
            errors.append(f"source_bundle_source_{index}_path_invalid")
        elif path in seen:
            errors.append(f"source_bundle_source_{index}_duplicate")
        else:
            seen.add(path)
            if previous and path < previous:
                errors.append("source_bundle_sources_not_sorted")
            previous = path
        if (
            not isinstance(source_digest, str)
            or _DIGEST_RE.fullmatch(source_digest) is None
        ):
            errors.append(f"source_bundle_source_{index}_digest_invalid")
    return errors


def validate_cross_session_source_bundle(
    value: object,
    *,
    checkpoint_graph: Mapping[str, Any] | None = None,
    project_path: str | Path | None = None,
    expected_runtime_contract_version: str | None = None,
) -> dict[str, Any]:
    """Validate bundle identity, checkpoint binding, sources and trust."""
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["source_bundle_not_mapping"]}
    if set(value) != _BUNDLE_KEYS:
        errors.append("source_bundle_keys_invalid")
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("source_bundle_schema_mismatch")
    if value.get("status") != BUNDLE_STATUS:
        errors.append("source_bundle_status_mismatch")
    if value.get("policy") != POLICY:
        errors.append("source_bundle_policy_mismatch")
    contract = value.get("runtime_contract_version")
    if not isinstance(contract, str) or not contract:
        errors.append("source_bundle_runtime_contract_invalid")
    elif (
        expected_runtime_contract_version is not None
        and contract != expected_runtime_contract_version
    ):
        errors.append("source_bundle_runtime_contract_mismatch")
    checkpoint_digest = value.get("checkpoint_graph_digest")
    if (
        not isinstance(checkpoint_digest, str)
        or _DIGEST_RE.fullmatch(checkpoint_digest) is None
    ):
        errors.append("source_bundle_checkpoint_digest_invalid")
    checkpoint_epoch = value.get("checkpoint_runtime_epoch")
    if not isinstance(checkpoint_epoch, str) or not checkpoint_epoch:
        errors.append("source_bundle_checkpoint_epoch_invalid")
    identity = value.get("project_identity")
    if not isinstance(identity, Mapping) or set(identity) != _PROJECT_IDENTITY_KEYS:
        errors.append("source_bundle_project_identity_invalid")
    sources = value.get("sources")
    errors.extend(_validate_sources_list(sources))
    digest = value.get("bundle_digest")
    if (
        not isinstance(digest, str)
        or _DIGEST_RE.fullmatch(digest) is None
        or digest != _bundle_digest(value)
    ):
        errors.append("source_bundle_digest_mismatch")

    if checkpoint_graph is not None:
        graph = _mapping_copy(checkpoint_graph, "checkpoint_graph")
        graph_epoch = graph.get("runtime_epoch")
        if isinstance(graph_epoch, str) and graph_epoch:
            graph_validation = validate_sr_script_checkpoint(
                graph,
                runtime_epoch=graph_epoch,
            )
            if graph_validation["valid"] is not True:
                errors.extend(
                    f"source_bundle_checkpoint_{item}"
                    for item in graph_validation["errors"]
                )
        else:
            errors.append("source_bundle_checkpoint_epoch_invalid")
        if value.get("checkpoint_graph_digest") != graph.get("graph_digest"):
            errors.append("source_bundle_checkpoint_mismatch")
        if value.get("checkpoint_runtime_epoch") != graph.get("runtime_epoch"):
            errors.append("source_bundle_checkpoint_epoch_mismatch")
        try:
            expected_sources = _checkpoint_sources(graph)
        except ValueError:
            expected_sources = []
            errors.append("source_bundle_checkpoint_sources_invalid")
        if sources != expected_sources:
            errors.append("source_bundle_source_set_mismatch")

    if project_path is not None:
        project = Path(project_path).resolve()
        try:
            identity_matches = _project_identity(project) == identity
        except ValueError:
            identity_matches = False
        if not identity_matches:
            errors.append("source_bundle_project_identity_mismatch")
        if isinstance(sources, list):
            from core.Lotucosm.script_trust_policy import (
                evaluate_project_script_trust,
            )

            for source in sources:
                if not isinstance(source, Mapping):
                    continue
                relative = source.get("path")
                source_digest = source.get("sha256")
                if not isinstance(relative, str) or not isinstance(
                    source_digest,
                    str,
                ):
                    continue
                source_path = project / relative
                if not source_path.is_file():
                    errors.append(
                        f"source_bundle_source_missing:{relative}"
                    )
                    continue
                actual_digest = hashlib.sha256(
                    source_path.read_bytes()
                ).hexdigest()
                if actual_digest != source_digest:
                    errors.append(
                        f"source_bundle_source_digest_mismatch:{relative}"
                    )
                    continue
                trust = evaluate_project_script_trust(
                    source_path,
                    project,
                    source_sha256=actual_digest,
                )
                if trust.get("trusted") is not True:
                    errors.append(
                        "source_bundle_source_untrusted:"
                        + str(trust.get("reason"))
                        + ":"
                        + relative
                    )
    return {"valid": not errors, "errors": list(dict.fromkeys(errors))}


def _owner_signature(entities: Iterable[object]) -> str:
    rows: list[list[object]] = []
    for entity in entities:
        entity_id = str(getattr(entity, "id", "") or "")
        scripts = getattr(entity, "scripts", ())
        if not isinstance(scripts, (list, tuple)):
            scripts = ()
        rows.append(
            [
                entity_id,
                [id(script) for script in scripts],
            ]
        )
    return _digest(rows)


def _restore_projection(
    *,
    runtime_contract_version: str,
    target_runtime_epoch: str,
    source_checkpoint_digest: object,
    source_bundle_digest: object,
    decision: str,
    errors: Sequence[str],
    live_owner_preserved: bool | None,
    restore_result: Mapping[str, Any] | None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": RESTORE_STATUS,
        "read_only": False,
        "policy": POLICY,
        "decision": decision,
        "admitted": decision == "rehydrated",
        "runtime_contract_version": runtime_contract_version,
        "target_runtime_epoch": target_runtime_epoch,
        "source_checkpoint_digest": (
            source_checkpoint_digest
            if isinstance(source_checkpoint_digest, str)
            else None
        ),
        "source_bundle_digest": (
            source_bundle_digest
            if isinstance(source_bundle_digest, str)
            else None
        ),
        "errors": list(dict.fromkeys(errors)),
        "quarantine_reason": errors[0] if errors else None,
        "live_owner_preserved": live_owner_preserved,
        "restore_result": (
            copy.deepcopy(dict(restore_result))
            if restore_result is not None
            else None
        ),
    }


def restore_cross_session_script_checkpoint(
    *,
    checkpoint_graph: object,
    source_bundle: object,
    runtime_contract_version: str,
    target_runtime_epoch: str,
    project_path: str | Path,
    entities: Iterable[object],
    instantiate_script: Callable[[dict[str, Any]], object | None],
) -> dict[str, Any]:
    """Rehydrate a trusted source bundle or quarantine without live mutation."""
    entity_list = list(entities)
    before = _owner_signature(entity_list)
    graph = (
        checkpoint_graph if isinstance(checkpoint_graph, Mapping) else {}
    )
    bundle = source_bundle if isinstance(source_bundle, Mapping) else {}
    checkpoint_digest = graph.get("graph_digest")
    bundle_digest = bundle.get("bundle_digest")
    validation = validate_cross_session_source_bundle(
        source_bundle,
        checkpoint_graph=graph if graph else None,
        project_path=project_path,
        expected_runtime_contract_version=runtime_contract_version,
    )
    if validation["valid"] is not True:
        return _restore_projection(
            runtime_contract_version=runtime_contract_version,
            target_runtime_epoch=target_runtime_epoch,
            source_checkpoint_digest=checkpoint_digest,
            source_bundle_digest=bundle_digest,
            decision="quarantined",
            errors=list(validation["errors"]),
            live_owner_preserved=_owner_signature(entity_list) == before,
            restore_result=None,
        )
    try:
        retargeted = retarget_sr_script_checkpoint(
            graph,
            target_runtime_epoch=target_runtime_epoch,
        )
        restore_result = restore_sr_script_checkpoint(
            retargeted,
            runtime_epoch=target_runtime_epoch,
            project_path=project_path,
            entities=entity_list,
            instantiate_script=instantiate_script,
        )
    except Exception as exc:
        return _restore_projection(
            runtime_contract_version=runtime_contract_version,
            target_runtime_epoch=target_runtime_epoch,
            source_checkpoint_digest=checkpoint_digest,
            source_bundle_digest=bundle_digest,
            decision="quarantined",
            errors=[f"script_restore_failed:{type(exc).__name__}:{exc}"],
            live_owner_preserved=_owner_signature(entity_list) == before,
            restore_result=None,
        )
    return _restore_projection(
        runtime_contract_version=runtime_contract_version,
        target_runtime_epoch=target_runtime_epoch,
        source_checkpoint_digest=checkpoint_digest,
        source_bundle_digest=bundle_digest,
        decision="rehydrated",
        errors=[],
        live_owner_preserved=None,
        restore_result=restore_result,
    )


def _quarantine_kind(result: Mapping[str, Any]) -> str | None:
    errors = result.get("errors")
    if not isinstance(errors, list):
        return None
    rendered = "\n".join(str(item) for item in errors)
    if "source_bundle_source_missing:" in rendered:
        return "source_missing"
    if "source_bundle_runtime_contract_mismatch" in rendered:
        return "version_mismatch"
    if (
        "source_bundle_digest_mismatch" in rendered
        or "source_bundle_checkpoint_mismatch" in rendered
        or "source_bundle_source_set_mismatch" in rendered
        or "source_bundle_source_digest_mismatch:" in rendered
    ):
        return "bundle_tamper"
    return None


def _evaluate(
    *,
    runtime_contract_version: str,
    base_script_checkpoint_witness: Mapping[str, Any],
    source_bundle: Mapping[str, Any],
    fresh_restore_result: Mapping[str, Any],
    fresh_recaptured_script_graph: Mapping[str, Any],
    quarantine_results: Sequence[Mapping[str, Any]],
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    base_validation = validate_worldbridge_e562_script_checkpoint_authority(
        base_script_checkpoint_witness
    )
    base_valid = base_validation == {"valid": True, "errors": []}
    if not base_valid:
        errors.extend(f"base_{item}" for item in base_validation["errors"])
    source_graph = base_script_checkpoint_witness.get("source_script_graph")
    if not isinstance(source_graph, Mapping):
        source_graph = {}
        errors.append("base_source_graph_missing")
    source_graph_digest = source_graph.get("graph_digest")

    bundle_validation = validate_cross_session_source_bundle(
        source_bundle,
        checkpoint_graph=source_graph,
        expected_runtime_contract_version=runtime_contract_version,
    )
    source_bundle_valid = bundle_validation == {"valid": True, "errors": []}
    if not source_bundle_valid:
        errors.extend(bundle_validation["errors"])

    fresh_valid = (
        fresh_restore_result.get("status") == RESTORE_STATUS
        and fresh_restore_result.get("decision") == "rehydrated"
        and fresh_restore_result.get("admitted") is True
        and fresh_restore_result.get("runtime_contract_version")
        == runtime_contract_version
        and fresh_restore_result.get("source_checkpoint_digest")
        == source_graph_digest
        and fresh_restore_result.get("source_bundle_digest")
        == source_bundle.get("bundle_digest")
        and fresh_restore_result.get("errors") == []
    )
    if not fresh_valid:
        errors.append("fresh_restore_result_invalid")
    restore_result = fresh_restore_result.get("restore_result")
    if not isinstance(restore_result, Mapping):
        restore_result = {}
        errors.append("fresh_restore_result_missing")
    fresh_epoch = fresh_restore_result.get("target_runtime_epoch")
    recaptured_validation = validate_sr_script_checkpoint(
        fresh_recaptured_script_graph,
        runtime_epoch=str(fresh_epoch or ""),
    )
    fresh_recaptured_valid = recaptured_validation == {
        "valid": True,
        "errors": [],
    }
    if not fresh_recaptured_valid:
        errors.extend(
            f"fresh_recaptured_{item}"
            for item in recaptured_validation["errors"]
        )
    source_entities = source_graph.get("entities")
    fresh_entities = fresh_recaptured_script_graph.get("entities")
    descriptors_equal = (
        isinstance(source_entities, list)
        and isinstance(fresh_entities, list)
        and source_entities == fresh_entities
    )
    if not descriptors_equal:
        errors.append("fresh_script_descriptors_mismatch")
    source_script_count = _script_count(source_graph)
    fresh_script_count = _script_count(fresh_recaptured_script_graph)
    restore_counts_equal = (
        restore_result.get("restored_entities") == len(source_entities or ())
        and restore_result.get("restored_scripts") == source_script_count
        and source_script_count == fresh_script_count
        and restore_result.get("runtime_epoch") == fresh_epoch
    )
    if not restore_counts_equal:
        errors.append("fresh_restore_counts_mismatch")
    source_bundle_bound = (
        source_bundle.get("checkpoint_graph_digest") == source_graph_digest
        and source_bundle.get("sources") == _checkpoint_sources(source_graph)
    )
    if not source_bundle_bound:
        errors.append("source_bundle_checkpoint_binding_mismatch")

    observed_quarantine_kinds: list[str] = []
    quarantine_fail_closed = True
    live_owner_preserved = True
    for result in quarantine_results:
        if not isinstance(result, Mapping):
            quarantine_fail_closed = False
            continue
        kind = _quarantine_kind(result)
        if kind is not None:
            observed_quarantine_kinds.append(kind)
        if (
            result.get("status") != RESTORE_STATUS
            or result.get("decision") != "quarantined"
            or result.get("admitted") is not False
            or (
                kind != "version_mismatch"
                and result.get("runtime_contract_version")
                != runtime_contract_version
            )
            or result.get("source_checkpoint_digest")
            != source_graph_digest
            or (
                kind != "bundle_tamper"
                and result.get("source_bundle_digest")
                != source_bundle.get("bundle_digest")
            )
        ):
            quarantine_fail_closed = False
        if result.get("live_owner_preserved") is not True:
            live_owner_preserved = False
    all_quarantine_cases = (
        quarantine_fail_closed
        and sorted(observed_quarantine_kinds) == sorted(QUARANTINE_REASONS)
    )
    if not all_quarantine_cases:
        errors.append("quarantine_case_matrix_mismatch")
    if not live_owner_preserved:
        errors.append("quarantine_mutated_live_owner")

    proof = {
        "base_checkpoint_valid": base_valid,
        "source_bundle_valid": source_bundle_valid,
        "fresh_rehydrated": fresh_valid,
        "fresh_recaptured_graph_valid": fresh_recaptured_valid,
        "descriptors_equal": descriptors_equal,
        "restore_counts_equal": restore_counts_equal,
        "source_bundle_bound_to_checkpoint": source_bundle_bound,
        "all_quarantine_cases_fail_closed": all_quarantine_cases,
        "live_owner_preserved_on_reject": live_owner_preserved,
    }
    for field in PROOF_FIELDS:
        if proof[field] is not True:
            errors.append(f"{field}_not_proven")
    return list(dict.fromkeys(errors)), {
        **proof,
        "source_graph_digest": source_graph_digest,
        "fresh_graph_digest": fresh_recaptured_script_graph.get(
            "graph_digest"
        ),
        "source_bundle_digest": source_bundle.get("bundle_digest"),
    }


def _script_count(graph: Mapping[str, Any]) -> int:
    entities = graph.get("entities")
    if not isinstance(entities, list):
        return 0
    return sum(
        len(entity.get("scripts", ()))
        for entity in entities
        if isinstance(entity, Mapping)
        and isinstance(entity.get("scripts"), list)
    )


def build_worldbridge_e563_cross_session_script_rehydration_authority(
    *,
    runtime_contract_version: str,
    base_script_checkpoint_witness: Mapping[str, Any],
    source_bundle: Mapping[str, Any],
    fresh_restore_result: Mapping[str, Any],
    fresh_recaptured_script_graph: Mapping[str, Any],
    quarantine_results: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    if (
        not isinstance(runtime_contract_version, str)
        or not runtime_contract_version
    ):
        raise ValueError("runtime_contract_version must be non-empty")
    if not isinstance(quarantine_results, Sequence) or isinstance(
        quarantine_results,
        (str, bytes),
    ):
        raise TypeError("quarantine_results must be a sequence")
    base = _mapping_copy(
        base_script_checkpoint_witness,
        "base_script_checkpoint_witness",
    )
    bundle = _mapping_copy(source_bundle, "source_bundle")
    fresh = _mapping_copy(fresh_restore_result, "fresh_restore_result")
    recaptured = _mapping_copy(
        fresh_recaptured_script_graph,
        "fresh_recaptured_script_graph",
    )
    quarantines = [
        _mapping_copy(item, f"quarantine_results[{index}]")
        for index, item in enumerate(quarantine_results)
    ]
    errors, projection = _evaluate(
        runtime_contract_version=runtime_contract_version,
        base_script_checkpoint_witness=base,
        source_bundle=bundle,
        fresh_restore_result=fresh,
        fresh_recaptured_script_graph=recaptured,
        quarantine_results=quarantines,
    )
    if errors:
        raise ValueError(
            "E563 cross-session script witness rejected: "
            + ",".join(errors)
        )
    witness: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": WITNESS_STATUS,
        "read_only": True,
        "scope": SCOPE,
        "policy": POLICY,
        "runtime_contract_version": runtime_contract_version,
        "base_script_checkpoint_witness": base,
        "source_bundle": bundle,
        "fresh_restore_result": fresh,
        "fresh_recaptured_script_graph": recaptured,
        "quarantine_results": quarantines,
        **projection,
        "remaining_script_blockers": list(REMAINING_SCRIPT_BLOCKERS),
        "grants_admission": True,
        "cross_session_script_rehydration_admitted": True,
        **{field: False for field in CLOSED_ADMISSION_FIELDS},
        "witness_digest": "",
    }
    witness["witness_digest"] = _witness_digest(witness)
    return witness


def validate_worldbridge_e563_cross_session_script_rehydration_authority(
    value: object,
) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["witness_not_mapping"]}
    if set(value) != _WITNESS_KEYS:
        errors.append("witness_keys_invalid")
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if value.get("status") != WITNESS_STATUS:
        errors.append("status_mismatch")
    if value.get("read_only") is not True:
        errors.append("read_only_required")
    if value.get("scope") != SCOPE:
        errors.append("scope_mismatch")
    if value.get("policy") != POLICY:
        errors.append("policy_mismatch")
    runtime_contract_version = value.get("runtime_contract_version")
    base = value.get("base_script_checkpoint_witness")
    bundle = value.get("source_bundle")
    fresh = value.get("fresh_restore_result")
    recaptured = value.get("fresh_recaptured_script_graph")
    quarantines = value.get("quarantine_results")
    if (
        not isinstance(runtime_contract_version, str)
        or not isinstance(base, Mapping)
        or not isinstance(bundle, Mapping)
        or not isinstance(fresh, Mapping)
        or not isinstance(recaptured, Mapping)
        or not isinstance(quarantines, list)
    ):
        return {"valid": False, "errors": errors + ["witness_payload_invalid"]}
    revalidation, projection = _evaluate(
        runtime_contract_version=runtime_contract_version,
        base_script_checkpoint_witness=base,
        source_bundle=bundle,
        fresh_restore_result=fresh,
        fresh_recaptured_script_graph=recaptured,
        quarantine_results=quarantines,
    )
    errors.extend(revalidation)
    for field, expected in projection.items():
        if value.get(field) != expected:
            errors.append(f"{field}_mismatch")
    for field in PROOF_FIELDS:
        if value.get(field) is not True:
            errors.append(f"{field}_not_true")
    if value.get("remaining_script_blockers") != list(
        REMAINING_SCRIPT_BLOCKERS
    ):
        errors.append("remaining_script_blockers_mismatch")
    if value.get("grants_admission") is not True:
        errors.append("grants_admission_mismatch")
    if value.get("cross_session_script_rehydration_admitted") is not True:
        errors.append("cross_session_script_rehydration_not_admitted")
    for field in CLOSED_ADMISSION_FIELDS:
        if value.get(field) is not False:
            errors.append(f"{field}_overclaim")
    digest = value.get("witness_digest")
    if (
        not isinstance(digest, str)
        or _DIGEST_RE.fullmatch(digest) is None
        or digest != _witness_digest(value)
    ):
        errors.append("witness_digest_mismatch")
    return {"valid": not errors, "errors": list(dict.fromkeys(errors))}


__all__ = [
    "BUNDLE_STATUS",
    "CLOSED_ADMISSION_FIELDS",
    "POLICY",
    "PROOF_FIELDS",
    "QUARANTINE_REASONS",
    "REMAINING_SCRIPT_BLOCKERS",
    "RESTORE_STATUS",
    "SCHEMA_VERSION",
    "SCOPE",
    "WITNESS_STATUS",
    "build_cross_session_source_bundle",
    "build_worldbridge_e563_cross_session_script_rehydration_authority",
    "restore_cross_session_script_checkpoint",
    "validate_cross_session_source_bundle",
    "validate_worldbridge_e563_cross_session_script_rehydration_authority",
]
