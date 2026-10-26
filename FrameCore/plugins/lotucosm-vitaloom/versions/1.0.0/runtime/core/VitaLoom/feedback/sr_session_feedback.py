# -*- coding: utf-8 -*-
"""SR 会话反馈音：Victory / 灭绝短音效（可选，默认开）。"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from core.VitaLoom.core.logger import get_logger
from core.VitaLoom.project.project_world_capabilities import get_project_world_read_model

logger = get_logger("SrSessionFeedback")

_player = None
_enabled: Optional[bool] = None


def _is_enabled() -> bool:
    global _enabled
    if _enabled is None:
        _enabled = os.environ.get("VITALOOM_SR_AUDIO", "1").strip().lower() not in (
            "0",
            "false",
            "no",
        )
    return bool(_enabled)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _project_audio_dir() -> Optional[Path]:
    try:
        path = get_project_world_read_model().current_project_world_path()
        if path:
            audio = Path(path) / "assets" / "audio"
            if audio.is_dir():
                return audio
    except Exception:
        __import__("logging").getLogger(__name__).debug("Ignored recoverable exception.", exc_info=True)
    return None


def _audio_candidates(kind: str) -> list[Path]:
    root = _repo_root()
    names = {
        "victory": ("victory.wav", "win.wav"),
        "extinction": ("extinction.wav", "fail.wav"),
    }
    rel_dirs: list[Path] = []
    proj_audio = _project_audio_dir()
    if proj_audio is not None:
        rel_dirs.append(proj_audio)
    rel_dirs.append(root / "assets" / "audio")
    out: list[Path] = []
    for d in rel_dirs:
        for name in names.get(kind, ()):
            p = d / name
            if p.is_file():
                out.append(p)
    return out


def play_session_feedback(kind: str) -> None:
    """播放 victory / extinction 音效；找不到文件或禁用时静默跳过。"""
    if not _is_enabled() or kind not in ("victory", "extinction"):
        return
    paths = _audio_candidates(kind)
    if not paths:
        logger.debug("未找到 SR 音效: kind=%s", kind)
        return
    path = paths[0]
    try:
        from PyQt6.QtCore import QUrl
        from PyQt6.QtMultimedia import QSoundEffect

        global _player
        if _player is None:
            _player = QSoundEffect()
        _player.setSource(QUrl.fromLocalFile(str(path.resolve())))
        _player.setVolume(0.55)
        _player.play()
    except Exception as e:
        logger.debug("播放 SR 音效跳过: %s", e)
