# -*- coding: utf-8 -*-
"""E201 guard: every direct legacy SceneManager save has explicit provenance."""
from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"


def _attribute_calls(attribute: str) -> set[tuple[str, str]]:
    calls: set[tuple[str, str]] = set()
    for source in RUNTIME.rglob("*.py"):
        tree = ast.parse(source.read_text(encoding="utf-8-sig"), filename=str(source))
        relative = source.relative_to(RUNTIME).as_posix()

        class Visitor(ast.NodeVisitor):
            class_names: list[str] = []
            function_names: list[str] = []

            def visit_ClassDef(self, node: ast.ClassDef) -> None:
                self.class_names.append(node.name)
                self.generic_visit(node)
                self.class_names.pop()

            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                self.function_names.append(node.name)
                self.generic_visit(node)
                self.function_names.pop()

            visit_AsyncFunctionDef = visit_FunctionDef

            def visit_Call(self, node: ast.Call) -> None:
                if isinstance(node.func, ast.Attribute) and node.func.attr == attribute:
                    owner = ".".join([*self.class_names, *self.function_names])
                    calls.add((relative, owner or "<module>"))
                self.generic_visit(node)

        Visitor().visit(tree)
    return calls


def _direct_save_scene_calls() -> set[tuple[str, str]]:
    return _attribute_calls("save_scene")


def test_direct_legacy_scene_manager_save_calls_match_e201_admitted_inventory() -> None:
    assert _direct_save_scene_calls() == {
        (
            "core/VitaLoom/project/project_manager.py",
            "ProjectManager._persist_viewport_scene",
        ),
        (
            "core/VitaLoom/project/project_manager.py",
            "ProjectManager.apply_project_world_flush",
        ),
        ("core/VitaLoom/scene/scene_manager.py", "SceneManager.save_scene_as"),
    }


def test_legacy_scene_save_as_has_no_runtime_callers_pending_a_typed_contract() -> None:
    assert _attribute_calls("save_scene_as") == set()


def test_e201_inventory_keeps_lifecycle_and_latent_save_as_out_of_semantic_history() -> None:
    project_manager = (
        RUNTIME / "core/VitaLoom/project/project_manager.py"
    ).read_text(encoding="utf-8")
    session = (
        RUNTIME / "core/VitaLoom/project/project_world_session.py"
    ).read_text(encoding="utf-8")
    scene_manager = (
        RUNTIME / "core/VitaLoom/scene/scene_manager.py"
    ).read_text(encoding="utf-8")
    standard_ui = (
        RUNTIME / "builtin/editor_extensions/standard_ui_plugin.py"
    ).read_text(encoding="utf-8")

    assert '"kind": "automatic_lifecycle_flush"' in session
    assert '"history_admission": "excluded"' in session
    assert '"audit_admission": "excluded"' in session
    assert "scene_manager.save_scene(data=viewport.get_scene_data())" in project_manager
    assert "scene_manager.save_scene()" in project_manager
    assert "candidate = json.loads(json.dumps(self._current_scene_data, ensure_ascii=False))" in scene_manager
    assert "if self.save_scene(scene_path, data=candidate):" in scene_manager
    save_scene_block = standard_ui.split("    def save_scene(self):", 1)[1].split(
        "    def ", 1
    )[0]
    assert '"scene.save"' in save_scene_block
    assert ".save_scene(" not in save_scene_block


