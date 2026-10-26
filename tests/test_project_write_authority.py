from __future__ import annotations

import json
import os
import threading
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from core.VitaLoom.project.project_write_authority import (
    ProjectWriteInterlockError,
    build_project_write_authority_witness,
    inspect_project_write_interlock,
    project_write_interlock,
    recover_project_write_interlock,
    validate_project_write_authority_witness,
)
from core.VitaLoom.scene.scene_manager import SceneManager
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)
from tools.check_project_write_authority import verify as verify_project_write


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    (project / "project.json").write_text(
        json.dumps(
            {
                "name": "Project Write Probe",
                "version": "1.0.0",
                "loom_editor_version": "1.0.0",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return project


def _lock_path(project: Path) -> Path:
    return project / ".vitaloom" / "asset_transaction_interlock.json"


def _write_stale_lock(
    project: Path,
    *,
    nonce: str,
    pid: int,
) -> Path:
    path = _lock_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "project_path": str(project.resolve()),
                "owner_nonce": nonce,
                "pid": pid,
                "created_at_utc": datetime.now(UTC)
                .isoformat(timespec="microseconds")
                .replace("+00:00", "Z"),
                "authority_action": "stale_probe",
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def test_project_write_interlock_is_same_thread_reentrant(tmp_path: Path) -> None:
    project = _project(tmp_path)
    assert inspect_project_write_interlock(project)["held"] is False

    with project_write_interlock(
        project,
        authority_action="outer",
    ) as outer:
        assert outer["status"] == "held"
        nonce = outer["owner_nonce"]
        with project_write_interlock(
            project,
            authority_action="inner",
        ) as inner:
            assert inner["status"] == "held_reentrant"
            assert inner["depth"] == 2
            assert inner["owner_nonce"] == nonce
        held = inspect_project_write_interlock(project)
        assert held["held"] is True
        assert held["record"]["owner_nonce"] == nonce

    assert inspect_project_write_interlock(project)["held"] is False


def test_project_write_interlock_blocks_other_thread_and_process_owner(
    tmp_path: Path,
) -> None:
    project = _project(tmp_path)
    errors: list[ProjectWriteInterlockError] = []

    def contender() -> None:
        try:
            with project_write_interlock(
                project,
                authority_action="thread_contender",
            ):
                raise AssertionError("competing thread entered write lock")
        except ProjectWriteInterlockError as exc:
            errors.append(exc)

    with project_write_interlock(
        project,
        authority_action="thread_holder",
    ):
        thread = threading.Thread(target=contender)
        thread.start()
        thread.join(timeout=5)
        assert thread.is_alive() is False

    assert len(errors) == 1
    assert errors[0].code == "project_write_interlock_held"
    assert inspect_project_write_interlock(project)["held"] is False


def test_lock_owner_tamper_refuses_release_and_explicit_recovery_is_audited(
    tmp_path: Path,
) -> None:
    project = _project(tmp_path)
    with pytest.raises(ProjectWriteInterlockError) as release:
        with project_write_interlock(
            project,
            authority_action="owner_tamper",
        ):
            path = _lock_path(project)
            record = json.loads(path.read_text(encoding="utf-8"))
            record["owner_nonce"] = "f" * 64
            path.write_text(
                json.dumps(record, sort_keys=True, separators=(",", ":")),
                encoding="utf-8",
            )
    assert release.value.code == "project_write_interlock_release_failed"
    assert inspect_project_write_interlock(project)["held"] is True

    recovered = recover_project_write_interlock(
        project,
        expected_owner_nonce="f" * 64,
        reason="unit-test explicit owner tamper recovery",
        allow_live_owner=True,
    )
    assert recovered["status"] == "project_write_interlock_recovered"
    assert inspect_project_write_interlock(project)["held"] is False


def test_stale_lock_requires_exact_nonce_and_explicit_reason(
    tmp_path: Path,
) -> None:
    project = _project(tmp_path)
    dead_pid = 2_000_000_000
    nonce = "a" * 64
    _write_stale_lock(project, nonce=nonce, pid=dead_pid)
    assert inspect_project_write_interlock(project)["state"] == "valid"

    with pytest.raises(ProjectWriteInterlockError) as mismatch:
        recover_project_write_interlock(
            project,
            expected_owner_nonce="b" * 64,
            reason="wrong owner probe",
        )
    assert mismatch.value.code == "project_write_recovery_owner_mismatch"

    with pytest.raises(ProjectWriteInterlockError) as no_reason:
        recover_project_write_interlock(
            project,
            expected_owner_nonce=nonce,
            reason="",
        )
    assert no_reason.value.code == "project_write_recovery_reason_required"

    recovered = recover_project_write_interlock(
        project,
        expected_owner_nonce=nonce,
        reason="dead owner stale lock cleanup",
    )
    assert recovered["recovered_pid"] == dead_pid
    assert recovered["owner_was_alive"] is False
    assert inspect_project_write_interlock(project)["held"] is False


def test_absent_lock_migrates_without_precreated_metadata(tmp_path: Path) -> None:
    project = _project(tmp_path)
    assert not (project / ".vitaloom").exists()
    with project_write_interlock(
        project,
        authority_action="no_lock_migration",
    ) as ticket:
        assert ticket["owner_pid"] == os.getpid()
        assert _lock_path(project).is_file()
    assert inspect_project_write_interlock(project)["held"] is False


def test_scene_save_wraps_persistence_in_project_write_interlock(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project = _project(tmp_path)
    scene = project / "scenes" / "main.pond"
    scene.parent.mkdir()
    observed_held: list[bool] = []

    from core.VitaLoom.scene import scene_persistence

    def persist(path: str, data: dict[str, object]):
        observed_held.append(inspect_project_write_interlock(project)["held"])
        return {"scene_path": path, "scene_data": data}

    monkeypatch.setattr(scene_persistence, "persist_scene_snapshot", persist)
    manager = SimpleNamespace(
        _current_scene_path=str(scene),
        _current_scene_data={"entities": []},
        editor_context=SimpleNamespace(current_project_path=str(project)),
        commit_persisted_scene=lambda *_args: None,
    )

    assert SceneManager.save_scene(
        manager,
        scene_path=str(scene),
        data={"entities": []},
    )
    assert observed_held == [True]
    assert inspect_project_write_interlock(project)["held"] is False


def test_write_authority_witness_rejects_forged_process_or_seam() -> None:
    evidence = {
        "holder_pid": 101,
        "importer_pid": 202,
        "canonical_interlock_path": (
            ".vitaloom/asset_transaction_interlock.json"
        ),
        "checkpoint_import_blocked": True,
        "asset_transaction_blocked": True,
        "project_lock_refresh_blocked": True,
        "project_save_blocked": True,
        "post_release_import_succeeded": True,
        "interlock_released": True,
    }
    witness = build_project_write_authority_witness(evidence)
    assert validate_project_write_authority_witness(witness) == {
        "valid": True,
        "errors": [],
    }
    assert witness["global_cross_process_atomicity"] is True

    reused = dict(evidence)
    reused["importer_pid"] = reused["holder_pid"]
    with pytest.raises(ValueError):
        build_project_write_authority_witness(reused)

    forged = dict(witness)
    forged["project_save_blocked"] = False
    forged["witness_digest"] = "0" * 64
    validation = validate_project_write_authority_witness(forged)
    assert validation["valid"] is False
    assert "project_save_blocked_not_proven" in validation["errors"]


def test_real_cross_process_write_authority_and_status_projection() -> None:
    result = verify_project_write()
    assert result["ok"] is True
    witness = result["witness"]
    assert validate_project_write_authority_witness(witness) == {
        "valid": True,
        "errors": [],
    }
    assert witness["global_cross_process_atomicity"] is True
    status = build_runtime_worldbridge_status(
        project_write_authority_witness=witness,
    )
    assert status["global_cross_process_atomicity_admitted"] is True
    assert (
        status["project_write_authority_evidence"]["witness_digest"]
        == witness["witness_digest"]
    )
    assert status["default_ready"] is False
