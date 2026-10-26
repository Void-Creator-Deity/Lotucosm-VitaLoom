# -*- coding: utf-8 -*-
"""E203 guard: active cross-runtime code must not bypass scene command ownership."""
from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"
SEAMS = {"save_scene", "save_scene_as"}


def _active_non_test_sources() -> list[Path]:
    framecore_sources = [
        source
        for source in (ROOT / "FrameCore").rglob("*.py")
        if RUNTIME not in source.parents
    ]
    return sorted(
        [
            *framecore_sources,
            *(ROOT / "tools").rglob("*.py"),
            *(ROOT / name for name in ("main.py", "player.py") if (ROOT / name).is_file()),
        ]
    )


def _legacy_scene_manager_save_seam_references() -> set[tuple[str, str, str, str]]:
    references: set[tuple[str, str, str, str]] = set()
    for source in _active_non_test_sources():
        tree = ast.parse(source.read_text(encoding="utf-8-sig"), filename=str(source))
        relative = source.relative_to(ROOT).as_posix()

        class Visitor(ast.NodeVisitor):
            class_names: list[str] = []
            function_names: list[str] = []

            def _owner(self) -> str:
                return ".".join([*self.class_names, *self.function_names]) or "<module>"

            def visit_ClassDef(self, node: ast.ClassDef) -> None:
                self.class_names.append(node.name)
                self.generic_visit(node)
                self.class_names.pop()

            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                self.function_names.append(node.name)
                self.generic_visit(node)
                self.function_names.pop()

            visit_AsyncFunctionDef = visit_FunctionDef

            def visit_Attribute(self, node: ast.Attribute) -> None:
                if node.attr in SEAMS:
                    references.add((relative, self._owner(), "attribute", node.attr))
                self.generic_visit(node)

            def visit_Call(self, node: ast.Call) -> None:
                if (
                    isinstance(node.func, ast.Name)
                    and node.func.id == "getattr"
                    and len(node.args) >= 2
                    and isinstance(node.args[1], ast.Constant)
                    and node.args[1].value in SEAMS
                ):
                    references.add((relative, self._owner(), "getattr", str(node.args[1].value)))
                if (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "import_module"
                    and node.args
                    and isinstance(node.args[0], ast.Constant)
                    and str(node.args[0].value).endswith("scene_manager")
                ):
                    references.add((relative, self._owner(), "dynamic_import", "scene_manager"))
                self.generic_visit(node)

            def visit_Import(self, node: ast.Import) -> None:
                for alias in node.names:
                    if alias.name.endswith("scene_manager"):
                        references.add((relative, self._owner(), "import", alias.name))
                self.generic_visit(node)

            def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
                if (node.module or "").endswith("scene_manager"):
                    references.add((relative, self._owner(), "import_from", str(node.module)))
                self.generic_visit(node)

        Visitor().visit(tree)
    return references


def test_active_cross_runtime_sources_do_not_reference_legacy_scene_manager_save_seams() -> None:
    assert _legacy_scene_manager_save_seam_references() == set()


def test_e203_scope_is_limited_to_active_host_extension_tool_and_launcher_sources() -> None:
    sources = {source.relative_to(ROOT).as_posix() for source in _active_non_test_sources()}
    assert "main.py" in sources
    assert "player.py" in sources
    assert any(source.startswith("FrameCore/") for source in sources)
    assert any(source.startswith("tools/") for source in sources)
    assert not any("/versions/1.0.0/runtime/" in source for source in sources)
    assert not any(source.startswith("tests/") for source in sources)
