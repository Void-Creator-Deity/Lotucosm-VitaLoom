# -*- coding: utf-8
"""SR 贴图目录：manifest.json 按 sprite 键 / 动画 clip 绘制，失败回退程序化绘制。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPixmap

from core.Lotucosm.sr_entity_visual import SrEntityVisual
from core.Lotucosm.sr_game_effects import entity_hit_flash, paint_hit_flash_overlay
from core.VitaLoom.viewports.sr_visual_renderer import paint_game_entity, paint_scene_entity


class SrSpriteCatalog:
    """缓存 QPixmap；支持 per-entity sr_visual.sprite / anim / flip_x / alpha。"""

    _instance: Optional["SrSpriteCatalog"] = None
    _loaded_root: Optional[str] = None

    def __init__(self, assets_dir: Path):
        self.assets_dir = assets_dir
        self._sprites: dict[str, QPixmap] = {}
        self._animations: dict[str, list[str]] = {}
        self._load_manifest()

    @classmethod
    def for_project(cls, project_path: Optional[str]) -> Optional["SrSpriteCatalog"]:
        if not project_path:
            return None
        root = Path(project_path)
        assets = root / "assets"
        if not assets.is_dir():
            return None
        key = str(assets.resolve())
        if cls._instance is not None and cls._loaded_root == key:
            return cls._instance
        manifest = assets / "manifest.json"
        if not manifest.is_file():
            return None
        cls._instance = cls(assets)
        cls._loaded_root = key
        return cls._instance

    @classmethod
    def invalidate_cache(cls) -> None:
        cls._instance = None
        cls._loaded_root = None

    def _load_pix(self, rel: str) -> Optional[QPixmap]:
        path = (self.assets_dir / rel.replace("\\", "/")).resolve()
        if not path.is_file():
            return None
        pix = QPixmap(str(path))
        return pix if not pix.isNull() else None

    def _load_manifest(self) -> None:
        manifest_path = self.assets_dir / "manifest.json"
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        sprites = data.get("sprites", {})
        if isinstance(sprites, dict):
            for key, rel in sprites.items():
                if not isinstance(rel, str):
                    continue
                pix = self._load_pix(rel)
                if pix is not None:
                    self._sprites[str(key)] = pix
        anims = data.get("animations", {})
        if isinstance(anims, dict):
            for key, frames in anims.items():
                if isinstance(frames, list):
                    rels = [str(f) for f in frames if f]
                    self._animations[str(key)] = rels
                    for rel in rels:
                        pix = self._load_pix(rel)
                        if pix is not None:
                            self._sprites[rel] = pix
                            base = Path(rel.replace("\\", "/")).stem
                            if base and base not in self._sprites:
                                self._sprites[base] = pix

    def has_sprite(self, entity_type: str) -> bool:
        return str(entity_type) in self._sprites

    def _visual(self, entity: Any) -> SrEntityVisual:
        vis = getattr(entity, "sr_visual", None)
        if isinstance(vis, SrEntityVisual):
            return vis
        return SrEntityVisual()

    def resolve_sprite_key(self, entity: Any) -> Optional[str]:
        vis = self._visual(entity)
        if vis.sprite and vis.sprite in self._sprites:
            return vis.sprite
        if vis.anim and vis.anim in self._animations:
            return vis.anim
        et = str(getattr(entity, "entity_type", ""))
        if et in self._sprites:
            return et
        return None

    def can_paint(self, entity: Any) -> bool:
        vis = self._visual(entity)
        if vis.sprite:
            if vis.sprite in self._sprites:
                return True
            if self._load_pix(vis.sprite) is not None:
                return True
            if (self.assets_dir / vis.sprite.replace("\\", "/")).is_file():
                return True
        if vis.anim and vis.anim in self._animations:
            return True
        et = str(getattr(entity, "entity_type", ""))
        return et in self._sprites

    def _resolve_pixmap(self, entity: Any, scene_time: float) -> Optional[QPixmap]:
        vis = self._visual(entity)
        if vis.anim and vis.anim in self._animations:
            frames = self._animations[vis.anim]
            if not frames:
                return None
            idx = vis.frame if vis.frame >= 0 else int(scene_time * 6.0) % len(frames)
            idx = max(0, min(len(frames) - 1, idx))
            rel = frames[idx]
            if rel in self._sprites:
                return self._sprites[rel]
            return self._load_pix(rel)
        key = vis.sprite or str(getattr(entity, "entity_type", ""))
        if key in self._sprites:
            return self._sprites[key]
        if key.startswith("sprites/") or "/" in key:
            cached = self._load_pix(key)
            if cached is not None:
                self._sprites[key] = cached
                return cached
        return None

    @staticmethod
    def _uses_rect_sprite(entity: Any, vis: SrEntityVisual) -> bool:
        eid = str(getattr(entity, "id", ""))
        if vis.sprite == "wall" or eid.startswith("wall"):
            return True
        et = str(getattr(entity, "entity_type", ""))
        return et == "game_prop" and vis.sprite == "wall"

    def paint_entity(self, painter: QPainter, entity: Any, scene_time: float) -> None:
        pix = self._resolve_pixmap(entity, scene_time)
        if pix is None or pix.isNull():
            et = str(getattr(entity, "entity_type", ""))
            if et in ("game_actor", "game_prop", "organism", "nutrient"):
                paint_game_entity(painter, entity, scene_time)
            else:
                paint_scene_entity(painter, entity, scene_time)
            return
        vis = self._visual(entity)
        cx = float(entity.position[0])
        cy = float(entity.position[1])
        r = max(4.0, float(getattr(entity, "radius", 18.0)))
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, not self._uses_rect_sprite(entity, vis))
        if vis.alpha < 0.999:
            painter.setOpacity(max(0.0, min(1.0, float(vis.alpha))))
        if self._uses_rect_sprite(entity, vis):
            tw = max(12, int(r * 2.0))
            th = max(8, int(r * 0.75))
            scaled = pix.scaled(
                tw,
                th,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.FastTransformation,
            )
            ox = int(cx - scaled.width() * 0.5)
            oy = int(cy - scaled.height() * 0.5)
            painter.drawPixmap(ox, oy, scaled)
        else:
            d = int(r * 2.2)
            x = int(cx - d * 0.5)
            y = int(cy - d * 0.5)
            scaled = pix.scaled(
                d,
                d,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            ox = x + (d - scaled.width()) // 2
            oy = y + (d - scaled.height()) // 2
            if vis.flip_x:
                painter.translate(ox + scaled.width(), oy)
                painter.scale(-1.0, 1.0)
                painter.drawPixmap(0, 0, scaled)
            else:
                painter.drawPixmap(ox, oy, scaled)
        flash = entity_hit_flash(entity)
        if flash > 0.0:
            paint_hit_flash_overlay(painter, cx, cy, r, flash)
        painter.restore()
