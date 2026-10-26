"""Regression coverage for Qt-free portable editor-layout persistence facts."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from core.VitaLoom.kernel.editor_layout_state import EditorLayoutState


def _sample_layout() -> dict[str, object]:
    return {
        "window_state": "cGVyc2lzdGVkLXN0YXRl",
        "geometry": {"x": 12, "y": 34, "width": 1280, "height": 720},
        "dock_states": {
            "Inspector": {
                "visible": True,
                "floating": False,
                "area": 1,
                "geometry": {"x": 1, "y": 2, "width": 320, "height": 480},
            }
        },
        "viewport_state": {"current": "scene", "tabs_order": ["scene", "game"]},
    }


def test_layout_state_round_trip_preserves_known_persisted_contract_without_aliasing():
    source = _sample_layout()
    state = EditorLayoutState.from_mapping(source)
    persisted = state.to_mapping()

    assert persisted == source
    source["geometry"]["width"] = 1  # type: ignore[index]
    source["dock_states"]["Inspector"]["visible"] = False  # type: ignore[index]
    persisted["viewport_state"]["tabs_order"].append("preview")  # type: ignore[index]

    assert state.geometry["width"] == 1280
    assert state.dock_states["Inspector"]["visible"] is True
    assert state.viewport_state["tabs_order"] == ["scene", "game"]


def test_layout_state_drops_legacy_partial_or_invalid_sections_safely():
    state = EditorLayoutState.from_mapping(
        {
            "window_state": 42,
            "geometry": ["not", "a", "mapping"],
            "dock_states": {"good": {"visible": True}, "bad": ["not", "a", "mapping"]},
            "viewport_state": None,
            "ignored_future_key": {"safe": True},
        }
    )

    assert state.window_state == ""
    assert state.geometry == {}
    assert state.dock_states == {"good": {"visible": True}}
    assert state.viewport_state == {}
    assert state.to_mapping() == {
        "window_state": "",
        "geometry": {},
        "dock_states": {"good": {"visible": True}},
        "viewport_state": {},
    }


def test_layout_state_rejects_host_objects_in_persisted_facts():
    with pytest.raises(ValueError, match="JSON-safe"):
        EditorLayoutState.from_mapping({"geometry": {"widget": object()}})


def test_layout_state_requires_a_mapping_root():
    with pytest.raises(TypeError, match="must be a mapping"):
        EditorLayoutState.from_mapping([])  # type: ignore[arg-type]


def test_fresh_interpreter_import_does_not_load_pyqt():
    runtime_root = (
        Path(__file__).resolve().parents[1]
        / "FrameCore"
        / "plugins"
        / "lotucosm-vitaloom"
        / "versions"
        / "1.0.0"
        / "runtime"
    )
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(runtime_root)
    probe = subprocess.run(
        [
            sys.executable,
            "-B",
            "-S",
            "-c",
            "import sys; from core.VitaLoom.kernel.editor_layout_state import EditorLayoutState; "
            "assert EditorLayoutState.from_mapping({}).to_mapping(); "
            "assert not any(name == 'PyQt6' or name.startswith('PyQt6.') for name in sys.modules)",
        ],
        cwd=runtime_root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert probe.returncode == 0, probe.stderr
