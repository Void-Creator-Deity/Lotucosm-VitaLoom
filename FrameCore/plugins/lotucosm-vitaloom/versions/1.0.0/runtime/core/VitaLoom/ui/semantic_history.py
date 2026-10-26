# -*- coding: utf-8 -*-
"""Small UI-host adapters for semantic command history results."""
from __future__ import annotations

import json
from typing import Any, Mapping


def mirror_scene_save_history_snapshot(result: Mapping[str, Any]) -> bool:
    """Mirror a successful canonical scene-save history snapshot into the host.

    The Registry has already persisted and audited the exact snapshot.  This
    adapter deliberately performs no file write and never calls ``scene.open``:
    loading through SceneManager would reintroduce active-scene manifest
    authority that semantic scene-save history explicitly excludes.
    """

    result_data = result.get("result") if isinstance(result, Mapping) else None
    if not isinstance(result_data, Mapping):
        return False
    if result_data.get("history_sync_host_scene") is not True:
        return False
    if result_data.get("history_rehydrate_scene") is not False:
        return False
    scene_path = str(result_data.get("scene_path") or "").strip()
    scene_data = result_data.get("scene_data")
    if not scene_path or not isinstance(scene_data, Mapping):
        return False
    try:
        # Preserve the command boundary's detached JSON snapshot if a legacy
        # host later mutates its own in-memory copy.
        snapshot = json.loads(json.dumps(dict(scene_data), ensure_ascii=False))
        from core.VitaLoom.scene.scene_manager import get_scene_manager

        get_scene_manager().commit_persisted_scene(scene_path, snapshot)
    except Exception:
        # Host mirroring is an adapter concern after the canonical Registry
        # transition. Never turn a successful semantic history mutation into a
        # scene.open fallback or an uncaught GUI action failure.
        return False
    return True
