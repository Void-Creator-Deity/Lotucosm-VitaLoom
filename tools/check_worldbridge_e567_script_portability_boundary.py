#!/usr/bin/env python3
"""Verify digest-only script transport and executable-source quarantine."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from _runtime_bootstrap import install_runtime_paths
except ModuleNotFoundError:
    from tools._runtime_bootstrap import install_runtime_paths

ROOT = Path(__file__).resolve().parents[1]
install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_e564_checkpoint_transaction import (
    export_checkpoint_artifact,
)
from core.Lotucosm.runtime.world_bridge_e567_script_portability_boundary import (
    PROOF_FIELDS,
    build_worldbridge_e567_script_portability_boundary,
    validate_digest_only_artifact,
    validate_worldbridge_e567_script_portability_boundary,
)
from tools.check_worldbridge_e548_rng_draw_order_authority import (
    _trusted_sample_project,
)
from tools.check_worldbridge_e563_cross_session_script_rehydration import (
    _quarantine,
    verify as verify_e563,
)


RUNTIME_CONTRACT_VERSION = "1.0.0"


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _reseal_graph(graph: dict[str, Any]) -> dict[str, Any]:
    sealed = copy.deepcopy(graph)
    sealed["graph_digest"] = ""
    sealed["graph_digest"] = _digest(sealed)
    return sealed


def _reseal_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    sealed = copy.deepcopy(bundle)
    sealed["bundle_digest"] = ""
    sealed["bundle_digest"] = _digest(sealed)
    return sealed


def _first_source(graph: dict[str, Any]) -> tuple[str, str]:
    for entity in graph.get("entities", []):
        for script in entity.get("scripts", []):
            return str(script["source_path"]), str(script["source_sha256"])
    raise AssertionError("E567 checkpoint has no script source")


def _propagate_source_digest(
    graph: dict[str, Any],
    bundle: dict[str, Any],
    *,
    source_path: str,
    source_digest: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    updated_graph = copy.deepcopy(graph)
    for entity in updated_graph.get("entities", []):
        for script in entity.get("scripts", []):
            if script.get("source_path") == source_path:
                script["source_sha256"] = source_digest
    updated_graph = _reseal_graph(updated_graph)
    updated_bundle = copy.deepcopy(bundle)
    updated_bundle["checkpoint_graph_digest"] = updated_graph["graph_digest"]
    for source in updated_bundle.get("sources", []):
        if source.get("path") == source_path:
            source["sha256"] = source_digest
    updated_bundle = _reseal_bundle(updated_bundle)
    return updated_graph, updated_bundle


def verify() -> dict[str, Any]:
    e563 = verify_e563()
    witness563 = e563["witness"]
    graph = witness563["base_script_checkpoint_witness"][
        "source_script_graph"
    ]
    bundle = witness563["source_bundle"]
    source_available = witness563["fresh_restore_result"]
    source_missing = witness563["quarantine_results"][0]
    source_path, _source_digest = _first_source(graph)

    with _trusted_sample_project(ROOT) as project:
        with tempfile.TemporaryDirectory(prefix="vitaloom-e567-") as temp:
            temp_path = Path(temp)
            artifact_path = temp_path / "checkpoint.e564.json"
            export_checkpoint_artifact(
                project_path=project,
                scene_path=project / "scenes" / "challenge_scene.pond",
                checkpoint_graph=graph,
                source_bundle=bundle,
                runtime_contract_version=RUNTIME_CONTRACT_VERSION,
                artifact_path=artifact_path,
            )
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
            artifact_validation = validate_digest_only_artifact(artifact)
            if artifact_validation["valid"] is not True:
                raise AssertionError(
                    "E567 artifact embeds executable source: "
                    + ",".join(artifact_validation["errors"])
                )

            digest_project = temp_path / "digest-drift" / project.name
            shutil.copytree(project, digest_project)
            digest_source = digest_project / source_path
            digest_source.write_bytes(
                digest_source.read_bytes() + b"\n# source drift\n"
            )
            digest_drift = _quarantine(
                graph=graph,
                bundle=bundle,
                project=digest_project,
            )

            trust_project = temp_path / "trust-drift" / project.name
            shutil.copytree(project, trust_project)
            trust_source = trust_project / source_path
            trust_source.write_bytes(
                trust_source.read_bytes() + b"\n# trust drift\n"
            )
            new_digest = hashlib.sha256(trust_source.read_bytes()).hexdigest()
            trust_graph, trust_bundle = _propagate_source_digest(
                graph,
                bundle,
                source_path=source_path,
                source_digest=new_digest,
            )
            trust_drift = _quarantine(
                graph=trust_graph,
                bundle=trust_bundle,
                project=trust_project,
            )

            external_graph = copy.deepcopy(graph)
            for entity in external_graph.get("entities", []):
                for script in entity.get("scripts", []):
                    if script.get("source_path") == source_path:
                        script["source_path"] = "../external.py"
                        break
            external_graph = _reseal_graph(external_graph)
            external = _quarantine(
                graph=external_graph,
                bundle=bundle,
                project=project,
            )

            result = build_worldbridge_e567_script_portability_boundary(
                artifact=artifact,
                source_available_result=source_available,
                source_missing_result=source_missing,
                source_digest_drift_result=digest_drift,
                manifest_trust_drift_result=trust_drift,
                arbitrary_external_source_result=external,
            )
            validation = (
                validate_worldbridge_e567_script_portability_boundary(result)
            )
            if validation != {"valid": True, "errors": []}:
                raise AssertionError(
                    "E567 witness invalid: " + ",".join(validation["errors"])
                )
            return {
                "schema_version": 1,
                "status": "worldbridge_e567_script_portability_boundary",
                "artifact_digest": artifact["artifact_digest"],
                "artifact_bytes": artifact_path.stat().st_size,
                "proof": {field: result[field] for field in PROOF_FIELDS},
                "quarantine_reasons": {
                    name: item.get("quarantine_reason")
                    for name, item in {
                        "source_missing": source_missing,
                        "source_digest_drift": digest_drift,
                        "manifest_trust_drift": trust_drift,
                        "arbitrary_external": external,
                    }.items()
                },
                "portable_sr_executable_script_checkpoint": False,
                "executable_source_portability_closed": True,
                "witness_digest": result["witness_digest"],
                "witness": result,
                "errors": [],
                "ok": True,
            }


def main() -> int:
    result = verify()
    print(json.dumps(result, ensure_ascii=False, allow_nan=False, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
