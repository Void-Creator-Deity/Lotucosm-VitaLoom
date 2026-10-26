from __future__ import annotations

import ast
from pathlib import Path

from core.Lotucosm.runtime.world_bridge_static_boundary import (
    scan_worldbridge_live_mapping_boundary,
)

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore" / "plugins" / "lotucosm-vitaloom" / "versions" / "1.0.0" / "runtime"


def test_current_worldbridge_surface_has_no_unadmitted_live_component_or_graph_writes() -> None:
    result = scan_worldbridge_live_mapping_boundary(RUNTIME)
    assert result["valid"] is True
    assert result["violations"] == []
    assert result["read_only"] is True
    assert result["admission_verifier_required"] is True
    assert result["live_adapter_admitted"] is False


def test_guard_detects_forbidden_component_and_graph_seams(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    surface = runtime / "core" / "Lotucosm" / "runtime"
    surface.mkdir(parents=True)
    (surface / "world_bridge.py").write_text(
        "from builtin.components.component_factory import ComponentFactory\n"
        "def bad(entity, graph):\n"
        "    entity.components = {}\n"
        "    graph.add_connection(entity)\n",
        encoding="utf-8",
    )
    result = scan_worldbridge_live_mapping_boundary(runtime)
    kinds = {(item["kind"], item["detail"]) for item in result["violations"]}
    assert ("forbidden_import", "ComponentFactory") in kinds
    assert ("forbidden_attribute_write", "components") in kinds
    assert ("forbidden_call", "add_connection") in kinds


def test_guard_surface_is_ast_based_and_does_not_flag_comments_or_strings(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    surface = runtime / "core" / "Lotucosm" / "runtime"
    surface.mkdir(parents=True)
    (surface / "world_bridge.py").write_text(
        "# add_connection(create_component()) is forbidden in a future adapter\n"
        "MESSAGE = 'ComponentFactory and membrane_graph are policy vocabulary'\n",
        encoding="utf-8",
    )
    result = scan_worldbridge_live_mapping_boundary(runtime)
    assert result["valid"] is True
