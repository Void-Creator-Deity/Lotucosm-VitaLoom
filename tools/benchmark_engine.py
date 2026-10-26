#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lightweight engine benchmarks for portfolio and regression evidence."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools._runtime_bootstrap import install_runtime_paths

install_runtime_paths(ROOT)


def _configure_stdout() -> None:
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8")


def _sample_project(kind: str) -> Path:
    samples = ROOT / "workspace" / "projects" / "samples"
    candidates = sorted(
        path for path in samples.iterdir() if path.is_dir() and (path / "project.json").is_file()
    )
    if kind == "pvaec":
        for path in candidates:
            data = json.loads((path / "project.json").read_text(encoding="utf-8"))
            required = data.get("required_capabilities")
            if isinstance(required, dict) and "vitalloom.pvaec.simulation" in required:
                return path
    if kind == "roguelike":
        for path in candidates:
            if "Roguelike" in path.name:
                return path
    if candidates:
        return candidates[0]
    raise FileNotFoundError("No sample project found")


def _time_case(name: str, fn: Callable[[], Any], repeats: int) -> dict[str, Any]:
    samples: list[float] = []
    last: Any = None
    for _ in range(max(1, repeats)):
        start = time.perf_counter()
        with contextlib.redirect_stdout(sys.stderr):
            last = fn()
        samples.append((time.perf_counter() - start) * 1000.0)
    return {
        "name": name,
        "repeats": len(samples),
        "mean_ms": statistics.fmean(samples),
        "min_ms": min(samples),
        "max_ms": max(samples),
        "last_result": last,
    }


def _bench_command_list() -> dict[str, Any]:
    from core.VitaLoom.commands.registry import get_command_registry

    return {"commands": len(get_command_registry().list())}


def _bench_command_dispatch() -> dict[str, Any]:
    from core.VitaLoom.commands.registry import get_command_registry

    registry = get_command_registry()
    project = _sample_project("pvaec")
    result = registry.run("project.state", {"project_path": str(project)})
    return {
        "ok": bool(result.get("ok")),
        "command_id": "project.state",
        "project": project.name,
    }


def _bench_resource_scan() -> dict[str, Any]:
    from builtin.editor_extensions.asset_dependency_scan import (
        dependency_summary,
        scan_project_dependencies,
    )

    project = _sample_project("pvaec")
    edges = scan_project_dependencies(str(project))
    data = dependency_summary(edges)
    return {
        "project": project.name,
        "summary": data,
    }


def _bench_export_closure() -> dict[str, Any]:
    from core.VitaLoom.commands.registry import get_command_registry

    project = _sample_project("pvaec")
    result = get_command_registry().run("asset.export_closure", {"project_path": str(project)})
    data = result.get("result", {}) if result.get("ok") else {}
    return {
        "ok": bool(result.get("ok")),
        "project": project.name,
        "file_count": data.get("file_count", 0),
        "missing_total": data.get("missing_total", 0),
        "enabled_plugins": len(data.get("enabled_plugins", []) or []),
    }


def _bench_asset_index_scale() -> dict[str, Any]:
    from core.VitaLoom.project.asset_index import build_project_asset_index
    from core.VitaLoom.project.asset_registry import refresh_project_asset_registry

    with tempfile.TemporaryDirectory(prefix="vitalloom_asset_index_scale_") as tmp:
        project = Path(tmp) / "project"
        (project / "assets").mkdir(parents=True)
        (project / "scenes").mkdir()
        (project / "scripts").mkdir()
        (project / "project.json").write_text(json.dumps({"name": "scale"}), encoding="utf-8")
        for index in range(1000):
            (project / "assets" / f"asset_{index:04d}.dat").write_bytes(f"asset-{index}".encode())
        for scene_index in range(20):
            refs = [
                {"asset_path": f"assets/asset_{scene_index * 20 + offset:04d}.dat"}
                for offset in range(20)
            ]
            (project / "scenes" / f"scene_{scene_index:02d}.pond").write_text(
                json.dumps({"entities": refs}), encoding="utf-8"
            )

        started = time.perf_counter()
        first = build_project_asset_index(project)
        cold_ms = (time.perf_counter() - started) * 1000.0
        started = time.perf_counter()
        second = build_project_asset_index(project)
        full_rebuild_ms = (time.perf_counter() - started) * 1000.0
        started = time.perf_counter()
        registry_cold = refresh_project_asset_registry(project)
        registry_cold_ms = (time.perf_counter() - started) * 1000.0
        started = time.perf_counter()
        unchanged = refresh_project_asset_registry(project)
        unchanged_refresh_ms = (time.perf_counter() - started) * 1000.0
        changed_path = project / "assets" / "asset_0500.dat"
        changed_path.write_bytes(b"asset-500-mutated")
        started = time.perf_counter()
        one_file = refresh_project_asset_registry(project)
        one_file_refresh_ms = (time.perf_counter() - started) * 1000.0
        full_after_mutation = build_project_asset_index(project)
        started = time.perf_counter()
        projection = [{"path": row["path"], "sha256": row["sha256"]} for row in first["assets"]]
        projection_ms = (time.perf_counter() - started) * 1000.0
        return {
            "asset_count": first["asset_count"],
            "file_count": first["file_count"],
            "dependency_edges": first["dependencies"]["total_edges"],
            "cold_build_ms": cold_ms,
            "full_rebuild_ms": full_rebuild_ms,
            "registry_cold_refresh_ms": registry_cold_ms,
            "unchanged_refresh_ms": unchanged_refresh_ms,
            "one_file_refresh_ms": one_file_refresh_ms,
            "projection_ms": projection_ms,
            "deterministic_revision": first["index_revision"] == second["index_revision"],
            "projection_count": len(projection),
            "unchanged_cache_hits": unchanged["refresh"]["cache_hits"],
            "unchanged_cache_misses": unchanged["refresh"]["cache_misses"],
            "one_file_cache_hits": one_file["refresh"]["cache_hits"],
            "one_file_cache_misses": one_file["refresh"]["cache_misses"],
            "one_file_changed_files": one_file["refresh"]["changed_files"],
            "registry_projection_parity": (
                one_file["asset_index"]["index_revision"] == full_after_mutation["index_revision"]
                and one_file["refresh"]["parity"]
            ),
            "metadata_digest_cache_claimed": True,
            "metadata_digest_cache_scope": "path_bytes_mtime_ns_reuse_only",
            "watcher_or_hot_reload_claimed": False,
        }


def _bench_asset_reference_transaction_scale() -> dict[str, Any]:
    """Time one-file reference migration separately from Index/Registry refresh."""

    from core.VitaLoom.project.asset_index import build_project_asset_index
    from core.VitaLoom.project.asset_reference_transaction import (
        apply_asset_reference_mutation,
        plan_asset_reference_mutation,
        redo_asset_reference_mutation,
        undo_asset_reference_mutation,
    )

    with tempfile.TemporaryDirectory(prefix="vitalloom_asset_transaction_scale_") as tmp:
        project = Path(tmp) / "project"
        (project / "assets").mkdir(parents=True)
        (project / "scenes").mkdir()
        (project / "project.json").write_text(
            json.dumps({"name": "transaction-scale", "active_scene": "scene_00.pond"}),
            encoding="utf-8",
        )
        (project / "project.lock.json").write_text("{}", encoding="utf-8")
        for index in range(1000):
            (project / "assets" / f"asset_{index:04d}.dat").write_bytes(f"asset-{index}".encode())
        for scene_index in range(20):
            refs = [
                {"asset_path": f"assets/asset_{scene_index * 20 + offset:04d}.dat"}
                for offset in range(20)
            ]
            (project / "scenes" / f"scene_{scene_index:02d}.pond").write_text(
                json.dumps({"entities": refs}), encoding="utf-8"
            )

        started = time.perf_counter()
        rename_plan = plan_asset_reference_mutation(
            project,
            operation="rename",
            source_path="assets/asset_0000.dat",
            target_path="assets/asset_0000_renamed.dat",
        )
        rename_plan_ms = (time.perf_counter() - started) * 1000.0
        started = time.perf_counter()
        rename_receipt = apply_asset_reference_mutation(project, rename_plan)
        rename_apply_ms = (time.perf_counter() - started) * 1000.0
        started = time.perf_counter()
        undo_asset_reference_mutation(project, rename_receipt["transaction_id"])
        rename_undo_ms = (time.perf_counter() - started) * 1000.0
        started = time.perf_counter()
        redo_asset_reference_mutation(project, rename_receipt["transaction_id"])
        rename_redo_ms = (time.perf_counter() - started) * 1000.0

        replacement_target = project / "assets" / "asset_0002.dat"
        replacement_digest_before = hashlib.sha256(replacement_target.read_bytes()).hexdigest()
        started = time.perf_counter()
        replacement_plan = plan_asset_reference_mutation(
            project,
            operation="replace_referenced",
            source_path="assets/asset_0001.dat",
            target_path="assets/asset_0002.dat",
        )
        replacement_plan_ms = (time.perf_counter() - started) * 1000.0
        started = time.perf_counter()
        replacement_receipt = apply_asset_reference_mutation(project, replacement_plan)
        replacement_apply_ms = (time.perf_counter() - started) * 1000.0
        started = time.perf_counter()
        undo_asset_reference_mutation(project, replacement_receipt["transaction_id"])
        replacement_undo_ms = (time.perf_counter() - started) * 1000.0
        started = time.perf_counter()
        redo_asset_reference_mutation(project, replacement_receipt["transaction_id"])
        replacement_redo_ms = (time.perf_counter() - started) * 1000.0
        replacement_bytes_unchanged = (
            hashlib.sha256(replacement_target.read_bytes()).hexdigest() == replacement_digest_before
        )
        replacement_source_retired_after_redo = not (project / "assets" / "asset_0001.dat").exists()

        started = time.perf_counter()
        delete_plan = plan_asset_reference_mutation(
            project,
            operation="delete",
            source_path="assets/asset_0999.dat",
        )
        delete_plan_ms = (time.perf_counter() - started) * 1000.0
        started = time.perf_counter()
        delete_receipt = apply_asset_reference_mutation(project, delete_plan)
        delete_apply_ms = (time.perf_counter() - started) * 1000.0
        started = time.perf_counter()
        undo_asset_reference_mutation(project, delete_receipt["transaction_id"])
        delete_undo_ms = (time.perf_counter() - started) * 1000.0
        started = time.perf_counter()
        redo_asset_reference_mutation(project, delete_receipt["transaction_id"])
        delete_redo_ms = (time.perf_counter() - started) * 1000.0
        index = build_project_asset_index(project)
        return {
            "asset_count": 1000,
            "scene_count": 20,
            "dependency_edges": 400,
            "rename_reference_edits": len(rename_plan["reference_edits"]),
            "delete_reference_edits": len(delete_plan["reference_edits"]),
            "rename_plan_ms": rename_plan_ms,
            "rename_apply_ms": rename_apply_ms,
            "rename_undo_ms": rename_undo_ms,
            "rename_redo_ms": rename_redo_ms,
            "replace_referenced_reference_edits": len(replacement_plan["reference_edits"]),
            "replace_referenced_plan_ms": replacement_plan_ms,
            "replace_referenced_apply_ms": replacement_apply_ms,
            "replace_referenced_undo_ms": replacement_undo_ms,
            "replace_referenced_redo_ms": replacement_redo_ms,
            "replacement_bytes_unchanged": replacement_bytes_unchanged,
            "replacement_source_retired_after_redo": replacement_source_retired_after_redo,
            "delete_plan_ms": delete_plan_ms,
            "delete_apply_ms": delete_apply_ms,
            "delete_undo_ms": delete_undo_ms,
            "delete_redo_ms": delete_redo_ms,
            "export_ready_after_redo": index["export"]["ready"],
            "transaction_metadata_in_export": any(
                path.startswith(".vitaloom/asset_transactions/") for path in index["export"]["files"]
            ),
        }


def _bench_asset_retirement_policy_scale() -> dict[str, Any]:
    """Time the Phase 7E read-only retirement analysis at the transaction-scale fixture."""

    from core.VitaLoom.project.asset_index import build_project_asset_index
    from core.VitaLoom.project.asset_reference_transaction import analyze_asset_retirement_policy
    from core.VitaLoom.project.asset_registry import load_project_asset_registry

    with tempfile.TemporaryDirectory(prefix="vitalloom_asset_retirement_policy_scale_") as tmp:
        project = Path(tmp) / "project"
        (project / "assets").mkdir(parents=True)
        (project / "scenes").mkdir()
        (project / "project.json").write_text(
            json.dumps({"name": "retirement-policy-scale", "active_scene": "scene_00.pond"}),
            encoding="utf-8",
        )
        (project / "project.lock.json").write_text("{}", encoding="utf-8")
        for index in range(1000):
            (project / "assets" / f"asset_{index:04d}.dat").write_bytes(f"asset-{index}".encode())
        for scene_index in range(20):
            refs = [
                {"asset_path": f"assets/asset_{scene_index * 20 + offset:04d}.dat"}
                for offset in range(20)
            ]
            (project / "scenes" / f"scene_{scene_index:02d}.pond").write_text(
                json.dumps({"entities": refs}), encoding="utf-8"
            )

        def tree_bytes() -> dict[str, bytes]:
            return {
                file.relative_to(project).as_posix(): file.read_bytes()
                for file in sorted(project.rglob("*"))
                if file.is_file()
            }

        before_bytes = tree_bytes()
        before_index = build_project_asset_index(project)
        before_registry = load_project_asset_registry(project)
        started = time.perf_counter()
        result = analyze_asset_retirement_policy(
            project,
            source_path="assets/asset_0000.dat",
            replacement_path="assets/asset_0999.dat",
        )
        analysis_ms = (time.perf_counter() - started) * 1000.0
        repeated = analyze_asset_retirement_policy(
            project,
            source_path="assets/asset_0000.dat",
            replacement_path="assets/asset_0999.dat",
        )
        after_index = build_project_asset_index(project)
        after_registry = load_project_asset_registry(project)
        after_bytes = tree_bytes()
        if result != repeated:
            raise RuntimeError("retirement policy analysis was not deterministic")
        if before_bytes != after_bytes:
            raise RuntimeError("retirement policy analysis changed project bytes")
        if before_index != after_index or before_registry != after_registry:
            raise RuntimeError("retirement policy analysis changed Index or Registry facts")
        return {
            "asset_count": 1000,
            "scene_count": 20,
            "dependency_edges": 400,
            "analysis_ms": analysis_ms,
            "decision": result["decision"],
            "ready_for_future_transaction": result["ready_for_future_transaction"],
            "proposed_reference_edits": len(result["proposed_reference_edits"]),
            "deterministic": True,
            "export_ready_before": before_index["export"]["ready"],
            "export_ready_after": after_index["export"]["ready"],
            "registry_status_after": after_registry["status"],
            "transaction_metadata_created": (project / ".vitaloom" / "asset_transactions").exists(),
        }


def _bench_ps_tick() -> dict[str, Any]:
    from builtin.systems.ps_experiment_runner import PsExperimentRunner
    from core.Lotucosm.experiment_config import PsExperimentConfig

    cfg = PsExperimentConfig(
        name="benchmark_ps",
        ticks=20,
        seed=42,
        initial_organisms=8,
        max_population=16,
        snapshot_interval=20,
    )
    final = (PsExperimentRunner(cfg).run().get("final") or {})
    return {"population": final.get("population"), "tick": final.get("tick")}


def _make_sr2d_entities(kind: str) -> list[Any]:
    from types import SimpleNamespace

    entities: list[Any] = []
    if kind == "dense":
        dynamic_count = 120
        static_count = 40
        dynamic_spacing = 12.0
        static_spacing = 28.0
    elif kind == "sparse":
        dynamic_count = 45
        static_count = 15
        dynamic_spacing = 44.0
        static_spacing = 72.0
    else:
        dynamic_count = 80
        static_count = 20
        dynamic_spacing = 18.0
        static_spacing = 40.0

    for i in range(dynamic_count):
        entities.append(
            SimpleNamespace(
                entity_type="organism",
                position=[
                    50.0 + (i % 12) * dynamic_spacing,
                    50.0 + (i // 12) * dynamic_spacing,
                ],
                velocity=[12.0, -8.0],
                radius=12.0,
                pinned=False,
                membrane_locked=False,
            )
        )
    for i in range(static_count):
        entities.append(
            SimpleNamespace(
                entity_type="nutrient",
                position=[
                    80.0 + (i % 8) * static_spacing,
                    80.0 + (i // 8) * static_spacing,
                ],
                velocity=[0.0, 0.0],
                radius=10.0,
                pinned=True,
                membrane_locked=False,
            )
        )
    return entities


def _select_sr2d_adapter(adapter_request: str) -> Any:
    from core.Lotucosm.sr_physics2d import (
        CppSrPhysics2DAdapter,
        PythonSrPhysics2DAdapter,
        RustSrPhysics2DAdapter,
        make_default_adapter,
    )

    requested = str(adapter_request or "auto").strip().lower()
    if requested == "auto":
        return make_default_adapter()
    if requested == "python":
        return PythonSrPhysics2DAdapter()
    if requested == "cpp":
        return CppSrPhysics2DAdapter()
    if requested == "rust":
        return RustSrPhysics2DAdapter()
    raise ValueError(f"unsupported SR2D adapter request: {adapter_request!r}")


def _bench_sr2d_step(
    kind: str = "default",
    broadphase: str | None = None,
    adapter_request: str = "auto",
) -> dict[str, Any]:
    from core.Lotucosm.sr_physics2d import (
        Physics2DMode,
        SrPhysics2DConfig,
        SrPhysics2DWorld,
        is_cpp_sr2d_available,
        is_native_sr2d_available,
        is_rust_sr2d_available,
    )
    from core.Lotucosm.sr_physics2d.pvaec_contacts import build_pvaec_contact_pairs

    adapter = _select_sr2d_adapter(adapter_request)
    entities = _make_sr2d_entities(kind)
    iterations = 120
    config_kwargs: dict[str, Any] = {"contact_iterations": 2}
    if broadphase is not None:
        config_kwargs["pvaec_broadphase"] = broadphase
    config = SrPhysics2DConfig(**config_kwargs)
    pvaec_pair_count = len(
        build_pvaec_contact_pairs(
            entities,
            broadphase=config.pvaec_broadphase,
            contact_iterations=config.contact_iterations,
        )
    )
    pvaec_spatial_pair_count = len(
        build_pvaec_contact_pairs(
            entities,
            broadphase="spatial_hash",
            contact_iterations=config.contact_iterations,
        )
    )
    pvaec_debug_pair_count = len(build_pvaec_contact_pairs(entities, broadphase="bruteforce"))
    world = SrPhysics2DWorld(config, adapter=adapter)
    for _ in range(iterations):
        world.step(entities, 1.0 / 60.0, 640.0, 480.0, mode=Physics2DMode.PVAEC)
    first = entities[0]
    return {
        "entities": len(entities),
        "iterations": iterations,
        "variant": kind,
        "requested_adapter": str(adapter_request or "auto").strip().lower(),
        "selected_adapter": world.adapter.__class__.__name__,
        "adapter": world.adapter.__class__.__name__,
        "native_available": is_native_sr2d_available(),
        "cpp_available": is_cpp_sr2d_available(),
        "rust_available": is_rust_sr2d_available(),
        "pvaec_broadphase": config.pvaec_broadphase,
        "pvaec_pair_count": pvaec_pair_count,
        "pvaec_spatial_pair_count": pvaec_spatial_pair_count,
        "pvaec_debug_pair_count": pvaec_debug_pair_count,
        "first_position": [round(first.position[0], 3), round(first.position[1], 3)],
    }


def _bench_sr2d_dense_step(adapter_request: str = "auto") -> dict[str, Any]:
    return _bench_sr2d_step("dense", adapter_request=adapter_request)


def _bench_sr2d_sparse_step(adapter_request: str = "auto") -> dict[str, Any]:
    return _bench_sr2d_step("sparse", adapter_request=adapter_request)


def _bench_sr2d_spatial_step(adapter_request: str = "auto") -> dict[str, Any]:
    return _bench_sr2d_step("default", "spatial_hash", adapter_request)


def _bench_sr2d_dense_spatial_step(adapter_request: str = "auto") -> dict[str, Any]:
    return _bench_sr2d_step("dense", "spatial_hash", adapter_request)


def _bench_sr2d_sparse_spatial_step(adapter_request: str = "auto") -> dict[str, Any]:
    return _bench_sr2d_step("sparse", "spatial_hash", adapter_request)


def _make_viewport_snapshot(kind: str) -> Any:
    from core.VitaLoom.viewports.viewport_snapshot import (
        ViewportEdgeSnapshot,
        ViewportEntitySnapshot,
        ViewportFrameSnapshot,
    )

    if kind == "dense":
        count = 360
        columns = 30
        spacing = 18.0
    else:
        count = 90
        columns = 15
        spacing = 34.0

    entity_types = (
        "organism",
        "sensor",
        "actuator",
        "central_brain",
        "nutrient",
        "environment_well",
    )
    entities = tuple(
        ViewportEntitySnapshot(
            id=f"entity_{index:04d}",
            entity_type=entity_types[index % len(entity_types)],
            position=(
                40.0 + float(index % columns) * spacing,
                40.0 + float(index // columns) * spacing,
            ),
            radius=8.0 + float(index % 5),
            selected=index == 0,
            visual_state=(
                {"fill": (110 + index % 90, 170, 220, 220)}
                if index % 11 == 0
                else {}
            ),
        )
        for index in range(count)
    )
    edges = tuple(
        ViewportEdgeSnapshot(
            source_id=f"entity_{index:04d}",
            target_id=f"entity_{index + 1:04d}",
            kind="signal" if index % 3 == 0 else "hard",
            weight=1.0 + float(index % 4),
        )
        for index in range(count - 1)
        if index % 4 != 0
    )
    return ViewportFrameSnapshot(
        width=1280,
        height=720,
        scene_time=1.0,
        entities=entities,
        edges=edges,
        metadata={"benchmark_variant": kind},
    )


def _command_label(command: Any) -> str:
    item_id = (
        getattr(command, "entity_id", None)
        or getattr(command, "edge_id", None)
        or getattr(command, "text_id", None)
        or ""
    )
    return f"{getattr(command, 'kind', type(command).__name__)}:{item_id}"


def _bench_viewport_draw(kind: str = "default") -> dict[str, Any]:
    from core.VitaLoom.viewports.viewport_draw_commands import compile_viewport_draw_commands
    from core.VitaLoom.viewports.opengl_batching import compile_opengl_batches

    frame = _make_viewport_snapshot(kind)
    commands = compile_viewport_draw_commands(frame)
    batches = compile_opengl_batches(commands)
    return {
        "backend": "draw_commands",
        "variant": kind,
        "entities": len(frame.entities),
        "commands": len(commands),
        "batches": len(batches),
        "instances": sum(batch.instance_count for batch in batches),
        "first_command": _command_label(commands[0]) if commands else "",
    }


def _bench_viewport_draw_dense() -> dict[str, Any]:
    return _bench_viewport_draw("dense")


def _bench_viewport_batch_compile() -> dict[str, Any]:
    from core.VitaLoom.viewports.viewport_draw_commands import compile_viewport_draw_commands
    from core.VitaLoom.viewports.opengl_batching import compile_opengl_batches

    frame = _make_viewport_snapshot("dense")
    commands = compile_viewport_draw_commands(frame)
    batches = compile_opengl_batches(commands)
    return {
        "backend": "opengl_batching",
        "variant": "dense",
        "entities": len(frame.entities),
        "commands": len(commands),
        "batches": len(batches),
        "instances": sum(batch.instance_count for batch in batches),
        "first_command": _command_label(commands[0]) if commands else "",
    }


class _BenchmarkPainter:
    def __init__(self) -> None:
        self.draw_calls = 0

    def setPen(self, value: object) -> None:
        return None

    def setBrush(self, value: object) -> None:
        return None

    def drawEllipse(self, x: int, y: int, width: int, height: int) -> None:
        self.draw_calls += 1

    def drawLine(self, x1: int, y1: int, x2: int, y2: int) -> None:
        self.draw_calls += 1

    def drawText(self, x: int, y: int, text: str) -> None:
        self.draw_calls += 1


def _bench_viewport_qpainter_render() -> dict[str, Any]:
    from core.VitaLoom.viewports.opengl_batching import compile_opengl_batches
    from core.VitaLoom.viewports.qpainter_backend import QPainterViewportBackend
    from core.VitaLoom.viewports.viewport_draw_commands import compile_viewport_draw_commands

    frame = _make_viewport_snapshot("dense")
    commands = compile_viewport_draw_commands(frame)
    batches = compile_opengl_batches(commands)
    painter = _BenchmarkPainter()
    backend = QPainterViewportBackend()
    backend.render(painter, frame)
    return {
        "backend": "qpainter_command_render",
        "variant": "dense",
        "entities": len(frame.entities),
        "commands": len(commands),
        "batches": len(batches),
        "instances": sum(batch.instance_count for batch in batches),
        "draw_calls": painter.draw_calls,
        "first_command": _command_label(commands[0]) if commands else "",
    }


def _bench_viewport_opengl_render() -> dict[str, Any]:
    from core.VitaLoom.viewports.opengl_backend import OpenGLViewportBackend
    from core.VitaLoom.viewports.opengl_render_target import (
        QtOpenGLInstancingTarget,
        QtOpenGLRenderTarget,
    )
    from core.VitaLoom.viewports.viewport_draw_commands import compile_viewport_draw_commands
    from core.VitaLoom.viewports.opengl_batching import compile_opengl_batches

    frame = _make_viewport_snapshot("dense")
    commands = compile_viewport_draw_commands(frame)
    batches = compile_opengl_batches(commands)
    painter = _BenchmarkPainter()
    target = QtOpenGLRenderTarget(painter)
    instancing = QtOpenGLInstancingTarget()
    backend = OpenGLViewportBackend()
    backend.render(target, frame)
    instancing.draw_opengl_batches(batches)
    stats = backend.stats()
    target_snapshot = target.snapshot()
    return {
        "backend": "opengl_qt_render_target",
        "variant": "dense",
        "entities": len(frame.entities),
        "commands": len(commands),
        "batches": len(batches),
        "instances": sum(batch.instance_count for batch in batches),
        "draw_calls": target_snapshot["draw_calls"],
        "painter_draw_calls": painter.draw_calls,
        "pixel_probe": target_snapshot["pixel_probe"],
        "text_policy": target_snapshot["text_policy"],
        "instancing": instancing.snapshot(),
        "default_switch_allowed": stats["default_switch_allowed"],
        "first_command": _command_label(commands[0]) if commands else "",
    }


def _bench_viewport_opengl_canvas() -> dict[str, Any]:
    from core.VitaLoom.viewports.opengl_canvas import probe_qt_opengl_canvas_smoke

    frame = _make_viewport_snapshot("dense")
    result = probe_qt_opengl_canvas_smoke(frame=frame)
    frame_stats = result["frame"]
    target_snapshot = result["target_snapshot"]
    return {
        "backend": "opengl_qt_canvas_smoke",
        "variant": "dense",
        "target": result["target"],
        "entities": len(frame.entities),
        "commands": frame_stats["commands"],
        "batches": frame_stats["batches"],
        "instances": frame_stats["instances"],
        "first_command": frame_stats["first_command"],
        "qopenglwidget_available": result["qopenglwidget_available"],
        "qapplication_available": result["qapplication_available"],
        "initialize_calls": result["initialize_calls"],
        "resize_calls": result["resize_calls"],
        "paint_calls": result["paint_calls"],
        "context_current": result["context_current"],
        "rendered": result["rendered"],
        "skip_reason": result["skip_reason"],
        "pixel_probe": result["pixel_probe"],
        "frame": frame_stats,
        "target_snapshot": target_snapshot,
        "gpu_draw_calls": target_snapshot.get("gpu_draw_calls", 0) if isinstance(target_snapshot, dict) else 0,
        "fallback_required": target_snapshot.get("fallback_required", True) if isinstance(target_snapshot, dict) else True,
    }


def _bench_viewport_interaction_smoke() -> dict[str, Any]:
    from core.VitaLoom.viewports.opengl_canvas import probe_opengl_canvas_interaction_smoke

    return probe_opengl_canvas_interaction_smoke()


def _bench_viewport_frame_loop_dense() -> dict[str, Any]:
    from core.VitaLoom.viewports.graphics_backend_strategy import select_viewport_backend
    from core.VitaLoom.viewports.opengl_canvas import probe_qt_opengl_canvas_smoke
    from core.VitaLoom.viewports.opengl_batching import compile_opengl_batches
    from core.VitaLoom.viewports.qpainter_backend import QPainterViewportBackend
    from core.VitaLoom.viewports.viewport_draw_commands import compile_viewport_draw_commands
    from core.VitaLoom.viewports.viewport_profiler import ViewportFrameProfiler

    frame = _make_viewport_snapshot("dense")
    frames = 30
    profiler = ViewportFrameProfiler(
        buckets=(
            "command_compile",
            "batch_compile",
            "qpainter_render",
            "opengl_canvas_smoke",
            "total",
        ),
        window=frames,
    )
    command_compile_ms = 0.0
    batch_compile_ms = 0.0
    qpainter_render_ms = 0.0
    last_commands: list[Any] = []
    last_batches: list[Any] = []

    for _ in range(frames):
        frame_start = time.perf_counter()
        start = time.perf_counter()
        commands = compile_viewport_draw_commands(frame)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        command_compile_ms += elapsed_ms
        profiler.record("command_compile", elapsed_ms)
        last_commands = list(commands)

        start = time.perf_counter()
        batches = compile_opengl_batches(commands)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        batch_compile_ms += elapsed_ms
        profiler.record("batch_compile", elapsed_ms)
        last_batches = list(batches)

        painter = _BenchmarkPainter()
        start = time.perf_counter()
        QPainterViewportBackend().render(painter, frame)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        qpainter_render_ms += elapsed_ms
        profiler.record("qpainter_render", elapsed_ms)
        profiler.record("total", (time.perf_counter() - frame_start) * 1000.0)

    start = time.perf_counter()
    opengl_canvas = probe_qt_opengl_canvas_smoke(frame=frame)
    opengl_canvas_smoke_ms = (time.perf_counter() - start) * 1000.0
    profiler.record("opengl_canvas_smoke", opengl_canvas_smoke_ms)
    target_snapshot = opengl_canvas.get("target_snapshot", {})

    return {
        "backend": "viewport_frame_loop",
        "variant": "dense",
        "frames": frames,
        "entities": len(frame.entities),
        "commands_per_frame": len(last_commands),
        "batches_per_frame": len(last_batches),
        "instances_per_frame": sum(batch.instance_count for batch in last_batches),
        "command_compile_ms": command_compile_ms,
        "command_compile_ms_per_frame": command_compile_ms / frames,
        "batch_compile_ms": batch_compile_ms,
        "batch_compile_ms_per_frame": batch_compile_ms / frames,
        "qpainter_render_ms": qpainter_render_ms,
        "qpainter_render_ms_per_frame": qpainter_render_ms / frames,
        "opengl_canvas_smoke_ms": opengl_canvas_smoke_ms,
        "opengl_canvas": {
            "context_current": bool(opengl_canvas.get("context_current")),
            "rendered": bool(opengl_canvas.get("rendered")),
            "gpu_draw_calls": int(target_snapshot.get("gpu_draw_calls", 0)) if isinstance(target_snapshot, dict) else 0,
            "fallback_required": bool(target_snapshot.get("fallback_required", True)) if isinstance(target_snapshot, dict) else True,
            "skip_reason": str(opengl_canvas.get("skip_reason", "")),
        },
        "profiler": profiler.structured_snapshot(),
        "auto_default_backend": select_viewport_backend("auto").info.name,
        "first_command": _command_label(last_commands[0]) if last_commands else "",
    }


def _bench_subprocess(name: str, *args: str) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, "-B", "main.py", *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    return {
        "name": name,
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout.strip().splitlines()[-3:],
        "stderr_tail": proc.stderr.strip().splitlines()[-3:],
    }


def _bench_viewport_adapter_end_to_end() -> dict[str, Any]:
    """Measure both concrete viewport Host Adapters under one lifecycle policy.

    This case is the default-backend policy evidence. The older dense frame-loop
    case remains useful for phase profiling, but it does not compare equivalent
    QPainter and OpenGL render/capture/teardown work.
    """

    from core.VitaLoom.viewports.graphics_backend_strategy import select_viewport_backend
    from core.VitaLoom.viewports.viewport_adapter_benchmark import benchmark_viewport_adapters

    report = benchmark_viewport_adapters(
        (_make_viewport_snapshot("dense"),),
        warmup=1,
        iterations=3,
        process_events=8,
    )
    report["current_auto_backend"] = select_viewport_backend("auto").info.name
    return report


def _bench_hub_startup() -> dict[str, Any]:
    return _bench_subprocess("hub_smoke", "--smoke-hub")


def _bench_editor_smoke_startup() -> dict[str, Any]:
    return _bench_subprocess("editor_smoke", "--smoke-editor")


def main(argv: list[str] | None = None) -> int:
    _configure_stdout()
    parser = argparse.ArgumentParser(description="Run lightweight VitaLoom engine benchmarks.")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument(
        "--sr2d-adapter",
        choices=["auto", "python", "cpp", "rust"],
        default="auto",
        help="Select the SR2D Adapter for SR2D benchmark cases without changing engine defaults.",
    )
    parser.add_argument(
        "--case",
        choices=[
            "all",
            "commands",
            "resources",
            "export_closure",
            "asset_index_scale",
            "asset_reference_transaction_scale",
            "asset_retirement_policy_scale",
            "ps",
            "sr2d",
            "sr2d_dense",
            "sr2d_sparse",
            "sr2d_spatial",
            "sr2d_dense_spatial",
            "sr2d_sparse_spatial",
            "viewport_draw",
            "viewport_draw_dense",
            "viewport_batch_compile",
            "viewport_qpainter_render",
            "viewport_opengl_render",
            "viewport_opengl_canvas",
            "viewport_interaction_smoke",
            "viewport_frame_loop_dense",
            "viewport_adapter_end_to_end",
            "hub_startup",
            "editor_smoke_startup",
        ],
        default="all",
    )
    args = parser.parse_args(argv)
    cases: list[tuple[str, Callable[[], Any]]] = []
    if args.case in ("all", "commands"):
        cases.append(("command_list", _bench_command_list))
        cases.append(("command_dispatch", _bench_command_dispatch))
    if args.case in ("all", "resources"):
        cases.append(("resource_scan", _bench_resource_scan))
    if args.case in ("all", "export_closure"):
        cases.append(("asset_export_closure", _bench_export_closure))
    if args.case in ("all", "asset_index_scale"):
        cases.append(("asset_index_scale_1000", _bench_asset_index_scale))
    if args.case in ("all", "asset_reference_transaction_scale"):
        cases.append(("asset_reference_transaction_scale_1000", _bench_asset_reference_transaction_scale))
    if args.case in ("all", "asset_retirement_policy_scale"):
        cases.append(("asset_retirement_policy_scale_1000", _bench_asset_retirement_policy_scale))
    if args.case in ("all", "ps"):
        cases.append(("ps_tick_20", _bench_ps_tick))
    if args.case in ("all", "sr2d"):
        cases.append(("sr2d_step_120", lambda: _bench_sr2d_step(adapter_request=args.sr2d_adapter)))
    if args.case in ("all", "sr2d_dense"):
        cases.append(("sr2d_dense_step_120", lambda: _bench_sr2d_dense_step(args.sr2d_adapter)))
    if args.case in ("all", "sr2d_sparse"):
        cases.append(("sr2d_sparse_step_120", lambda: _bench_sr2d_sparse_step(args.sr2d_adapter)))
    if args.case in ("all", "sr2d_spatial"):
        cases.append(("sr2d_spatial_step_120", lambda: _bench_sr2d_spatial_step(args.sr2d_adapter)))
    if args.case in ("all", "sr2d_dense_spatial"):
        cases.append(("sr2d_dense_spatial_step_120", lambda: _bench_sr2d_dense_spatial_step(args.sr2d_adapter)))
    if args.case in ("all", "sr2d_sparse_spatial"):
        cases.append(("sr2d_sparse_spatial_step_120", lambda: _bench_sr2d_sparse_spatial_step(args.sr2d_adapter)))
    if args.case in ("all", "viewport_draw"):
        cases.append(("viewport_draw_commands", _bench_viewport_draw))
    if args.case in ("all", "viewport_draw_dense"):
        cases.append(("viewport_draw_commands_dense", _bench_viewport_draw_dense))
    if args.case in ("all", "viewport_batch_compile"):
        cases.append(("viewport_batch_compile_dense", _bench_viewport_batch_compile))
    if args.case in ("all", "viewport_qpainter_render"):
        cases.append(("viewport_qpainter_command_render_dense", _bench_viewport_qpainter_render))
    if args.case in ("all", "viewport_opengl_render"):
        cases.append(("viewport_opengl_qt_render_target_dense", _bench_viewport_opengl_render))
    if args.case in ("all", "viewport_opengl_canvas"):
        cases.append(("viewport_opengl_qt_canvas_smoke_dense", _bench_viewport_opengl_canvas))
    if args.case in ("all", "viewport_interaction_smoke"):
        cases.append(("viewport_interaction_smoke", _bench_viewport_interaction_smoke))
    if args.case in ("all", "viewport_frame_loop_dense"):
        cases.append(("viewport_frame_loop_dense", _bench_viewport_frame_loop_dense))
    if args.case in ("all", "viewport_adapter_end_to_end"):
        cases.append(("viewport_adapter_end_to_end", _bench_viewport_adapter_end_to_end))
    if args.case in ("all", "hub_startup"):
        cases.append(("hub_smoke_startup", _bench_hub_startup))
    if args.case in ("all", "editor_smoke_startup"):
        cases.append(("editor_smoke_startup", _bench_editor_smoke_startup))
    result = {
        "schema_version": 1,
        "root": str(ROOT),
        "cases": [_time_case(name, fn, args.repeats) for name, fn in cases],
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

