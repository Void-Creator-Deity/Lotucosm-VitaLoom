#!/usr/bin/env python3
"""Explicitly add a SHA-256 trust grant for one project-local script."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"
sys.path.insert(0, str(RUNTIME))

from core.Lotucosm.script_trust_policy import evaluate_project_script_trust  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("script", type=Path, help="Path relative to the project, e.g. scripts/behavior.py")
    parser.add_argument("--approve", action="store_true", help="Explicitly trust this exact source digest")
    args = parser.parse_args(argv)
    if not args.approve:
        print("approval failed: --approve is required; trust grants execute project code", file=sys.stderr)
        return 2

    project = args.project.resolve()
    manifest_path = project / "project.json"
    script_path = (project / args.script).resolve()
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise ValueError("project.json root must be an object")
        digest = hashlib.sha256(script_path.read_bytes()).hexdigest()
        candidate = evaluate_project_script_trust(
            script_path,
            project,
            source_sha256=digest,
        )
        if candidate["reason"] not in {"script_trust_not_configured", "script_not_trusted", "script_trust_digest_mismatch"}:
            raise ValueError(f"script cannot be approved: {candidate['reason']}")
        relative = script_path.relative_to(project).as_posix()
        trust = manifest.setdefault("script_trust", {})
        if not isinstance(trust, dict):
            raise ValueError("project.json script_trust must be an object")
        grants = trust.setdefault("sha256_allowlist", [])
        if not isinstance(grants, list):
            raise ValueError("script_trust.sha256_allowlist must be a list")
        grants[:] = [grant for grant in grants if not (isinstance(grant, dict) and grant.get("path") == relative)]
        grants.append({"path": relative, "sha256": digest})
        manifest_before = manifest_path.read_bytes()
        lock_path = project / "project.lock.json"
        lock_before = lock_path.read_bytes() if lock_path.is_file() else None
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        try:
            from core.VitaLoom.suite.project_lock import ensure_project_lock

            ensure_project_lock(project, repo_root=ROOT, overwrite=True)
        except Exception:
            manifest_path.write_bytes(manifest_before)
            if lock_before is None:
                lock_path.unlink(missing_ok=True)
            else:
                lock_path.write_bytes(lock_before)
            raise
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"approval failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"approved": True, "path": relative, "sha256": digest}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
