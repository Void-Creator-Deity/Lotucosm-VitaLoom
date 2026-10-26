# -*- coding: utf-8 -*-
"""Plain-data protocol and subprocess runner for the Qt OpenGL probe.

This Module belongs to the existing Qt/OpenGL viewport Host Adapter seam.  It
isolates current-context evidence from a pytest/editor process that already owns
an incompatible offscreen QApplication; it is not a renderer, Plugin Host, or
composition root.
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from core.VitaLoom.viewports.viewport_pixel_capture import ViewportPixelCapture
from core.VitaLoom.viewports.viewport_snapshot import (
    ViewportFrameSnapshot,
    build_viewport_frame_snapshot,
)

_WORKER_ENV = "VITALOOM_OPENGL_PROBE_WORKER"
_DEFAULT_TIMEOUT_SECONDS = 45.0


def frame_snapshot_to_payload(frame: ViewportFrameSnapshot | None) -> dict[str, Any] | None:
    """Serialize one immutable viewport snapshot into JSON-safe facts."""

    if frame is None:
        return None
    if not isinstance(frame, ViewportFrameSnapshot):
        raise TypeError("frame must be an immutable ViewportFrameSnapshot or None")
    return {
        "width": int(frame.width),
        "height": int(frame.height),
        "scene_time": float(frame.scene_time),
        "camera": {
            "position": list(frame.camera.position),
            "zoom": float(frame.camera.zoom),
            "rotation": float(frame.camera.rotation),
        },
        "entities": [
            {
                "id": entity.id,
                "entity_type": entity.entity_type,
                "position": list(entity.position),
                "velocity": list(entity.velocity),
                "radius": float(entity.radius),
                "selected": bool(entity.selected),
                "visible": bool(entity.visible),
                "pinned": bool(entity.pinned),
                "membrane_locked": bool(entity.membrane_locked),
                "visual_state": _json_safe(entity.visual_state),
            }
            for entity in frame.entities
        ],
        "edges": [
            {
                "source_id": edge.source_id,
                "target_id": edge.target_id,
                "kind": edge.kind,
                "weight": float(edge.weight),
                "metadata": _json_safe(edge.metadata),
            }
            for edge in frame.edges
        ],
        "metadata": _json_safe(frame.metadata),
    }


def frame_snapshot_from_payload(payload: Mapping[str, Any] | None) -> ViewportFrameSnapshot | None:
    """Reconstruct the Qt-free immutable snapshot accepted by the renderer seam."""

    if payload is None:
        return None
    if not isinstance(payload, Mapping):
        raise TypeError("frame payload must be a mapping or None")
    return build_viewport_frame_snapshot(
        payload.get("entities", ()),
        width=payload.get("width", 0),
        height=payload.get("height", 0),
        scene_time=payload.get("scene_time", 0.0),
        camera=payload.get("camera", {}),
        edges=payload.get("edges", ()),
        metadata=payload.get("metadata", {}),
    )


def capture_to_payload(capture: ViewportPixelCapture | None) -> dict[str, Any] | None:
    """Serialize a Qt-free RGBA capture without exposing Qt/GL objects."""

    if capture is None:
        return None
    if not isinstance(capture, ViewportPixelCapture):
        raise TypeError("logical capture must be ViewportPixelCapture or None")
    return {
        "width": int(capture.width),
        "height": int(capture.height),
        "format": capture.format,
        "pixels_base64": base64.b64encode(capture.pixels).decode("ascii"),
        "evidence": capture.evidence.to_dict(),
    }


def capture_from_payload(payload: Mapping[str, Any] | None) -> ViewportPixelCapture | None:
    """Reconstruct the logical RGBA capture and independently re-analyse evidence."""

    if payload is None:
        return None
    if not isinstance(payload, Mapping):
        raise TypeError("logical capture payload must be a mapping or None")
    evidence = payload.get("evidence", {})
    if not isinstance(evidence, Mapping):
        raise TypeError("logical capture evidence must be a mapping")
    background = evidence.get("background_rgba", (0, 0, 0, 255))
    if not isinstance(background, Sequence) or isinstance(background, (str, bytes)):
        raise TypeError("logical capture background_rgba must be a sequence")
    raw = base64.b64decode(str(payload.get("pixels_base64", "")), validate=True)
    return ViewportPixelCapture.from_rgba(
        raw,
        width=int(payload.get("width", 0) or 0),
        height=int(payload.get("height", 0) or 0),
        background_rgba=tuple(int(channel) for channel in background),  # type: ignore[arg-type]
        pixel_format=str(payload.get("format", "RGBA8888")),
        current_context=bool(evidence.get("current_context", False)),
        fallback_used=bool(evidence.get("fallback_used", False)),
        draw_mode=str(evidence.get("draw_mode", "")),
        gpu_draw_calls=int(evidence.get("gpu_draw_calls", 0) or 0),
        errors=tuple(str(item) for item in evidence.get("errors", ()) if item),
    )


def run_isolated_qt_opengl_probe(
    *,
    frame: ViewportFrameSnapshot | None = None,
    width: int = 64,
    height: int = 64,
    process_events: int = 8,
    include_logical_capture: bool = False,
    timeout: float = _DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Run the existing probe in a clean Windows QApplication process."""

    request = {
        "frame": frame_snapshot_to_payload(frame),
        "width": int(width),
        "height": int(height),
        "process_events": int(process_events),
        "include_logical_capture": bool(include_logical_capture),
    }
    command = [sys.executable, "-B", "-m", "core.VitaLoom.viewports.opengl_probe_worker"]
    env = dict(os.environ)
    env["QT_QPA_PLATFORM"] = "windows"
    env[_WORKER_ENV] = "1"
    env["PYTHONPATH"] = _worker_pythonpath(env.get("PYTHONPATH", ""))
    try:
        completed = subprocess.run(
            command,
            input=json.dumps(request, ensure_ascii=False),
            cwd=str(_runtime_root()),
            env=env,
            capture_output=True,
            text=True,
            timeout=max(0.01, float(timeout)),
            check=False,
        )
    except subprocess.TimeoutExpired:
        return _failure_result(f"isolated OpenGL probe timed out after {float(timeout):.2f}s")
    except Exception as exc:
        return _failure_result(
            f"isolated OpenGL probe launch failed: {exc.__class__.__name__}: {exc}"
        )

    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "worker exited without diagnostics").strip()
        return _failure_result(
            f"isolated OpenGL probe exited with code {completed.returncode}: {detail}"
        )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        return _failure_result("isolated OpenGL probe returned no JSON result")
    try:
        payload = json.loads(lines[-1])
        if not isinstance(payload, dict):
            raise TypeError("worker result must be a JSON object")
        logical_payload = payload.get("logical_capture")
        payload["logical_capture"] = capture_from_payload(logical_payload)
    except Exception as exc:
        return _failure_result(
            f"isolated OpenGL probe returned invalid JSON: {exc.__class__.__name__}: {exc}"
        )
    payload["isolated_process"] = True
    return payload


def _worker_main() -> int:
    """Read one request from stdin and emit one plain JSON report."""

    os.environ[_WORKER_ENV] = "1"
    try:
        raw = sys.stdin.read()
        request = json.loads(raw)
        if not isinstance(request, Mapping):
            raise TypeError("worker request must be a JSON object")
        frame = frame_snapshot_from_payload(request.get("frame"))
        from core.VitaLoom.viewports.opengl_canvas import _probe_qt_opengl_canvas_smoke_local

        result = _probe_qt_opengl_canvas_smoke_local(
            frame=frame,
            width=int(request.get("width", 64) or 64),
            height=int(request.get("height", 64) or 64),
            process_events=int(request.get("process_events", 8) or 8),
            include_logical_capture=bool(request.get("include_logical_capture", False)),
        )
        result = dict(result)
        result["logical_capture"] = capture_to_payload(result.get("logical_capture"))
        result["isolated_process"] = True
        sys.stdout.write(json.dumps(_json_safe(result), ensure_ascii=False) + "\n")
        return 0
    except Exception as exc:
        sys.stderr.write(f"{exc.__class__.__name__}: {exc}\n")
        return 1


def _failure_result(reason: str) -> dict[str, Any]:
    from core.VitaLoom.viewports.opengl_canvas import _base_smoke_result

    result = _base_smoke_result()
    result["isolated_process"] = True
    result["skip_reason"] = str(reason)
    result["pixel_probe"]["errors"] = [str(reason)]
    return result


def _runtime_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _worker_pythonpath(existing: str) -> str:
    candidates = [str(_runtime_root())]
    candidates.extend(str(Path(item).resolve()) for item in sys.path if item and Path(item).exists())
    candidates.extend(item for item in existing.split(os.pathsep) if item)
    return os.pathsep.join(dict.fromkeys(candidates))


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray, memoryview)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


if __name__ == "__main__":  # pragma: no cover - exercised through subprocess integration
    raise SystemExit(_worker_main())


__all__ = [
    "capture_from_payload",
    "capture_to_payload",
    "frame_snapshot_from_payload",
    "frame_snapshot_to_payload",
    "run_isolated_qt_opengl_probe",
]
