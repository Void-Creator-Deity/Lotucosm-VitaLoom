# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from core.VitaLoom.viewports.viewport_pixel_capture import ViewportPixelCapture
from core.VitaLoom.viewports.viewport_snapshot import (
    ViewportCameraSnapshot,
    ViewportEdgeSnapshot,
    ViewportEntitySnapshot,
    ViewportFrameSnapshot,
)


def _frame() -> ViewportFrameSnapshot:
    return ViewportFrameSnapshot(
        width=96,
        height=64,
        scene_time=1.25,
        camera=ViewportCameraSnapshot(position=(4.0, -3.0), zoom=1.5, rotation=0.25),
        entities=(
            ViewportEntitySnapshot(
                id="organism-a",
                entity_type="organism",
                position=(20.0, 24.0),
                velocity=(1.0, 2.0),
                radius=7.0,
                selected=True,
                visual_state={"label": "A", "color": (10, 20, 30, 255)},
            ),
        ),
        edges=(ViewportEdgeSnapshot(source_id="organism-a", target_id="organism-a"),),
        metadata={"probe": True, "layers": ("edges", "entities", "text")},
    )


def test_opengl_probe_protocol_round_trips_plain_frame_and_capture() -> None:
    from core.VitaLoom.viewports.opengl_probe_worker import (
        capture_from_payload,
        capture_to_payload,
        frame_snapshot_from_payload,
        frame_snapshot_to_payload,
    )

    frame = _frame()
    restored_frame = frame_snapshot_from_payload(frame_snapshot_to_payload(frame))

    assert restored_frame == frame

    capture = ViewportPixelCapture.from_rgba(
        bytes((10, 20, 30, 255)) * 4,
        width=2,
        height=2,
        background_rgba=(1, 2, 3, 255),
        current_context=True,
        fallback_used=False,
        draw_mode="qt_opengl_texture",
        gpu_draw_calls=3,
    )
    restored_capture = capture_from_payload(capture_to_payload(capture))

    assert restored_capture == capture


def test_offscreen_environment_routes_public_probe_to_isolated_worker(monkeypatch) -> None:
    import core.VitaLoom.viewports.opengl_canvas as module

    sentinel = module._base_smoke_result()
    sentinel.update({"rendered": True, "isolated_process": True})
    calls: list[dict[str, object]] = []

    def fake_isolated(**kwargs):
        calls.append(kwargs)
        return sentinel

    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.delenv("VITALOOM_OPENGL_PROBE_WORKER", raising=False)
    monkeypatch.setattr(module, "_run_isolated_qt_opengl_probe", fake_isolated)

    result = module.probe_qt_opengl_canvas_smoke(frame=_frame(), include_logical_capture=True)

    assert result is sentinel
    assert calls and calls[0]["frame"] == _frame()
    assert calls[0]["include_logical_capture"] is True


def test_worker_recursion_guard_keeps_probe_local(monkeypatch) -> None:
    import core.VitaLoom.viewports.opengl_canvas as module

    sentinel = module._base_smoke_result()
    sentinel["worker_local"] = True

    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("VITALOOM_OPENGL_PROBE_WORKER", "1")
    monkeypatch.setattr(module, "_probe_qt_opengl_canvas_smoke_local", lambda **kwargs: sentinel)
    monkeypatch.setattr(
        module,
        "_run_isolated_qt_opengl_probe",
        lambda **kwargs: pytest.fail("worker recursion guard must prevent another subprocess"),
    )

    assert module.probe_qt_opengl_canvas_smoke() is sentinel



def test_interaction_sequence_counts_each_isolated_worker_as_target_recreation(monkeypatch) -> None:
    import core.VitaLoom.viewports.opengl_canvas as module

    frames = (_frame(), _frame())
    call_index = 0

    def fake_probe(**kwargs):
        nonlocal call_index
        call_index += 1
        capture = ViewportPixelCapture.from_rgba(
            bytes((10 * call_index, 20, 30, 255)) * (96 * 64),
            width=96,
            height=64,
            background_rgba=(26, 140, 217, 255),
            current_context=True,
            fallback_used=False,
            draw_mode="qt_opengl_texture",
            gpu_draw_calls=1,
        )
        result = module._base_smoke_result()
        result.update(
            {
                "isolated_process": True,
                "rendered": True,
                "context_current": True,
                "context_released": True,
                "logical_capture": capture,
                "frame": {"commands": 1, "batches": 1, "instances": 1, "first_command": "entity"},
                "target_snapshot": {
                    "context_current": True,
                    "fallback_required": False,
                    "pending_instances": 0,
                    "generation": 1,
                    "details": {},
                },
                "pixel_probe": capture.evidence.to_dict(),
            }
        )
        return result

    monkeypatch.setattr(module, "probe_qt_opengl_canvas_smoke", fake_probe)

    result = module.probe_qt_opengl_interaction_sequence(frames)

    assert result["completed"] is True
    assert result["target_recreations"] == 2
    assert [record["target_generation"] for record in result["records"]] == [1, 2]
    assert [record["target_native_generation"] for record in result["records"]] == [1, 1]
    assert all(record["isolated_process"] for record in result["records"])

def test_isolated_worker_timeout_fails_closed(monkeypatch) -> None:
    import core.VitaLoom.viewports.opengl_probe_worker as module

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs["timeout"])

    monkeypatch.setattr(module.subprocess, "run", timeout)

    result = module.run_isolated_qt_opengl_probe(frame=_frame(), timeout=0.01)

    assert result["rendered"] is False
    assert result["isolated_process"] is True
    assert result["pixel_probe"]["ready"] is False
    assert "timed out" in result["skip_reason"]
    assert result["pixel_probe"]["errors"]


@pytest.mark.skipif(sys.platform != "win32", reason="controlled Windows worker gate")
def test_offscreen_parent_process_gets_real_windows_worker_pixels() -> None:
    runtime_root = (
        Path(__file__).resolve().parents[1]
        / "FrameCore"
        / "plugins"
        / "lotucosm-vitaloom"
        / "versions"
        / "1.0.0"
        / "runtime"
    )
    script = r'''
import json
from core.VitaLoom.viewports.opengl_canvas import probe_qt_opengl_canvas_smoke
from core.VitaLoom.viewports.viewport_snapshot import ViewportEntitySnapshot, ViewportFrameSnapshot
frame = ViewportFrameSnapshot(
    width=96,
    height=64,
    entities=(ViewportEntitySnapshot(id="a", entity_type="organism", position=(32.0, 24.0), radius=8.0),),
)
result = probe_qt_opengl_canvas_smoke(
    frame=frame,
    width=frame.width,
    height=frame.height,
    include_logical_capture=True,
)
print(json.dumps({
    "isolated_process": result.get("isolated_process", False),
    "rendered": result["rendered"],
    "context_current": result["context_current"],
    "context_released": result["context_released"],
    "fallback_used": result["pixel_probe"]["fallback_used"],
    "errors": result["pixel_probe"]["errors"],
    "logical_capture": result["logical_capture"] is not None,
    "skip_reason": result["skip_reason"],
}))
'''
    env = dict(os.environ)
    env["QT_QPA_PLATFORM"] = "offscreen"
    env.pop("VITALOOM_OPENGL_PROBE_WORKER", None)
    pythonpath = [str(runtime_root)]
    if env.get("PYTHONPATH"):
        pythonpath.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(pythonpath)

    completed = subprocess.run(
        [sys.executable, "-B", "-c", script],
        cwd=runtime_root,
        env=env,
        capture_output=True,
        text=True,
        timeout=45.0,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout.strip().splitlines()[-1])
    assert payload == {
        "isolated_process": True,
        "rendered": True,
        "context_current": True,
        "context_released": True,
        "fallback_used": False,
        "errors": [],
        "logical_capture": True,
        "skip_reason": "",
    }
