#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check release image/audio assets have explicit provenance metadata."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ASSET_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".ico", ".svg", ".wav", ".mp3", ".ogg"}
SKIP_DIR_NAMES = {"__pycache__", ".git", ".venv", "dist", "build"}


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _asset_manifest(asset_root: Path) -> dict[str, Any]:
    path = asset_root / "manifest.json"
    if not path.is_file():
        return {}
    return _load_json(path)


def _declared_sources(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    sources = manifest.get("sources")
    if not isinstance(sources, dict):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for rel, meta in sources.items():
        if isinstance(meta, dict):
            result[str(rel).replace("\\", "/")] = meta
    return result


def _asset_roots() -> list[Path]:
    roots: list[Path] = []
    samples = ROOT / "workspace" / "projects" / "samples"
    if samples.is_dir():
        roots.extend(path / "assets" for path in samples.iterdir() if (path / "assets").is_dir())
    return sorted(roots)


def _iter_assets(asset_root: Path) -> list[Path]:
    result: list[Path] = []
    for path in asset_root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if path.name == "manifest.json":
            continue
        if path.suffix.lower() in ASSET_SUFFIXES:
            result.append(path)
    return sorted(result)


def _validate_source(rel: str, meta: dict[str, Any]) -> str | None:
    origin = str(meta.get("origin", "") or "").strip()
    license_name = str(meta.get("license", "") or "").strip()
    if not origin:
        return f"{rel}: missing sources.origin"
    if origin not in {"project_generated", "project_drawn", "self_drawn", "generated_script", "qt_standard_icon"}:
        return f"{rel}: unsupported sources.origin {origin!r}"
    if not license_name:
        return f"{rel}: missing sources.license"
    if license_name not in {"project-owned", "self-owned", "generated-project-owned", "qt-standard"}:
        return f"{rel}: unsupported sources.license {license_name!r}"
    if origin in {"project_generated", "generated_script"} and not str(meta.get("generator", "") or "").strip():
        return f"{rel}: generated assets must record sources.generator"
    return None


def check_asset_provenance() -> list[str]:
    errors: list[str] = []
    for asset_root in _asset_roots():
        manifest = _asset_manifest(asset_root)
        sources = _declared_sources(manifest)
        for asset in _iter_assets(asset_root):
            rel = asset.relative_to(asset_root).as_posix()
            meta = sources.get(rel)
            if meta is None:
                errors.append(
                    f"{asset.relative_to(ROOT).as_posix()}: missing assets/manifest.json sources entry"
                )
                continue
            error = _validate_source(rel, meta)
            if error:
                errors.append(f"{asset.relative_to(ROOT).as_posix()}: {error}")
    return errors


def main() -> int:
    errors = check_asset_provenance()
    if errors:
        print("asset provenance FAILED:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("asset provenance OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
