from __future__ import annotations

from pathlib import Path

from tools.check_legacy_command_stack_usage import scan_file, scan_runtime


def test_scan_excludes_legacy_definition_file(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    definition = runtime / "core/VitaLoom/commands/command.py"
    definition.parent.mkdir(parents=True)
    definition.write_text("class CommandStack: pass\n", encoding="utf-8")
    assert scan_file(definition, runtime) == []


def test_scan_detects_import_and_instantiation(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    source = runtime / "adapter.py"
    source.parent.mkdir(parents=True)
    source.write_text("from x import CommandStack\nstack = CommandStack()\n", encoding="utf-8")
    usages = scan_file(source, runtime)
    assert [usage.kind for usage in usages] == ["import", "instantiation"]


def test_scan_detects_qualified_reference(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    source = runtime / "adapter.py"
    source.parent.mkdir(parents=True)
    source.write_text("legacy.CommandStack\n", encoding="utf-8")
    assert scan_file(source, runtime)[0].kind == "qualified_reference"


def test_scan_runtime_ignores_test_paths(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    test_file = runtime / "tests/test_legacy.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("CommandStack()\n", encoding="utf-8")
    assert scan_runtime(runtime) == []
