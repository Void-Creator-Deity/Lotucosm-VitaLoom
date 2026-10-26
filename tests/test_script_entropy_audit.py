from __future__ import annotations

import hashlib
import random

import pytest
import json

from core.Lotucosm.script_entropy_audit import (
    build_dynamic_script_boundary_receipt,
    audit_script_entropy,
    audit_script_file,
    build_script_entropy_receipt,
    diagnose_script_entropy_admission,
    validate_dynamic_script_boundary_receipt,
    validate_script_evidence_corpus,
    validate_script_descriptor_coverage,
    build_project_script_inventory,
    validate_project_script_inventory,
)
from core.Lotucosm.script_trust_policy import (
    evaluate_project_script_trust,
    validate_project_script_trust_sources,
)


def _bare_viewport() -> object:
    from core.VitaLoom.viewports.game_viewport import GameViewport

    viewport = GameViewport.__new__(GameViewport)
    viewport._sr_script_entropy_audits = []
    viewport._sr_script_entropy_receipts = []
    viewport._sr_runtime_rng = random.Random(7)
    viewport._sr_runtime_epoch = "epoch-test"
    return viewport


def test_script_entropy_audit_accepts_owner_seam() -> None:
    report = audit_script_entropy(
        "from core.Lotucosm.scripts import ScriptBase\n"
        "class Behavior(ScriptBase):\n"
        "    def update(self, dt):\n"
        "        self.random_uniform(-1, 1)\n"
    )
    assert report["parseable"] is True
    assert report["deterministic_ready"] is True
    assert report["findings"] == []


def test_script_evidence_corpus_requires_success_and_trust_failure_coverage() -> None:
    audit = {"path": "scripts/a.py", "deterministic_ready": True, "findings": []}
    receipt = {"path": "scripts/a.py", "source_sha256": "a" * 64}
    denial = {"path": "scripts/b.py", "reason": "script_not_trusted"}
    failure = {
        "path": "scripts/b.py",
        "phase": "trust",
        "status": "script_runtime_failure",
    }
    assert validate_script_evidence_corpus(
        [audit], [receipt], [denial], [failure]
    ) == {"valid": True, "errors": []}
    incomplete = validate_script_evidence_corpus([audit], [], [], [])
    assert incomplete["valid"] is False
    assert "receipt_missing_for_audit" in incomplete["errors"]


def test_script_evidence_corpus_accepts_identical_reused_script_evidence() -> None:
    audit = {"path": "scripts/shared.py", "deterministic_ready": True, "findings": []}
    receipt = {"path": "scripts/shared.py", "source_sha256": "a" * 64}

    result = validate_script_evidence_corpus(
        [audit, dict(audit)], [receipt, dict(receipt)], [], []
    )

    assert result == {"valid": True, "errors": []}


def test_script_evidence_corpus_rejects_conflicting_reused_script_evidence() -> None:
    audit = {"path": "scripts/shared.py", "deterministic_ready": True, "findings": []}
    changed_audit = {**audit, "findings": [{"kind": "global_entropy_call"}]}
    receipt = {"path": "scripts/shared.py", "source_sha256": "a" * 64}
    changed_receipt = {**receipt, "source_sha256": "b" * 64}

    result = validate_script_evidence_corpus(
        [audit, changed_audit], [receipt, changed_receipt], [], []
    )

    assert result["valid"] is False
    assert "conflicting_audit_path" in result["errors"]
    assert "conflicting_receipt_path" in result["errors"]


def test_script_owner_registry_digest_ignores_pond_lifetime() -> None:
    from types import SimpleNamespace

    viewport = _bare_viewport()
    before = viewport._script_owner_registry_digest()
    viewport._unified_pond = SimpleNamespace(randomness_rng=random.Random(9))

    assert viewport._script_owner_registry_digest() == before


def test_script_descriptor_coverage_rejects_unobserved_declared_script() -> None:
    result = validate_script_descriptor_coverage(
        ["scripts/declared.py"], [], [], [], []
    )
    assert result["valid"] is False
    assert "declared_script_outcome_missing" in result["errors"]


def test_project_script_inventory_distinguishes_declared_not_loaded_and_loaded(tmp_path) -> None:
    project = tmp_path / "project"
    addon = project / "addons" / "demo"
    addon.mkdir(parents=True)
    entry = addon / "demo_plugin.py"
    entry.write_text("class DemoPlugin: pass\n", encoding="utf-8")
    (addon / "plugin.json").write_text(json.dumps({
        "schema_version": 1,
        "id": "demo_plugin",
        "version": "1.0.0",
        "entry": "demo_plugin.py",
    }), encoding="utf-8")
    manifest = {
        "script_trust": {
            "sha256_allowlist": [{"path": "scripts/scene.py", "sha256": "a" * 64}]
        }
    }
    inventory = build_project_script_inventory(
        manifest,
        project_path=project,
        scene_script_paths=["scripts/scene.py"],
        loaded_receipts=[{"path": "scripts/scene.py"}],
    )
    assert {item["outcome"] for item in inventory} == {"loaded", "declared_not_loaded"}
    assert {item["kind"] for item in inventory} == {"project_script", "project_addon"}
    assert validate_project_script_inventory(
        inventory,
        loaded_receipts=[{"path": "scripts/scene.py"}],
    )["valid"] is False


def test_project_script_inventory_rejects_runtime_source_not_declared() -> None:
    inventory = build_project_script_inventory({"script_trust": {"sha256_allowlist": []}})
    result = validate_project_script_inventory(
        inventory,
        loaded_receipts=[{"path": "scripts/ghost.py"}],
    )
    assert result["valid"] is False
    assert "runtime_executable_not_declared" in result["errors"]


def test_project_addon_inventory_rejects_runtime_digest_mismatch(tmp_path) -> None:
    addon = tmp_path / "addons" / "demo"
    addon.mkdir(parents=True)
    entry = addon / "demo_plugin.py"
    entry.write_text("class DemoPlugin: pass\n", encoding="utf-8")
    (addon / "plugin.json").write_text(json.dumps({
        "schema_version": 1,
        "id": "demo_plugin",
        "version": "1.0.0",
        "entry": "demo_plugin.py",
    }), encoding="utf-8")
    inventory = build_project_script_inventory(
        {},
        project_path=tmp_path,
        loaded_receipts=[{
            "path": str(entry),
            "kind": "project_addon",
            "entry_sha256": "0" * 64,
            "manifest_sha256": "0" * 64,
        }],
    )
    result = validate_project_script_inventory(
        inventory,
        loaded_receipts=[{
            "path": str(entry),
            "kind": "project_addon",
            "entry_sha256": "0" * 64,
            "manifest_sha256": "0" * 64,
        }],
    )
    assert result["valid"] is False
    assert "project_addon_source_digest_mismatch" in result["errors"]


def test_script_attach_inherits_pond_owner_when_entity_slot_is_empty() -> None:
    from core.Lotucosm.scripts import ScriptBase

    class Pond:
        randomness_rng = random.Random(19)

    class Entity:
        randomness_rng = None
        pond = Pond()

    script = ScriptBase()
    script.on_attach(Entity())
    assert script.randomness_rng is Entity.pond.randomness_rng


def test_script_entropy_audit_rejects_process_global_random() -> None:
    report = audit_script_entropy("import random\nrandom.uniform(0, 1)\n", path="demo.py")
    assert report["deterministic_ready"] is False
    assert {finding["authority"] for finding in report["findings"]} == {
        "python_process_global_random"
    }


@pytest.mark.parametrize(
    ("source", "symbol"),
    (
        ("import random\nlocal = random.Random(7)\n", "random.Random"),
        ("import numpy as np\nlocal = np.random.default_rng(7)\n", "numpy.random.default_rng"),
        ("from numpy.random import Generator\nlocal = Generator()\n", "numpy.random.Generator"),
    ),
)
def test_script_entropy_audit_rejects_unregistered_local_rngs(
    source: str, symbol: str
) -> None:
    report = audit_script_entropy(source, path="local_rng.py")
    assert report["deterministic_ready"] is False
    assert {
        "kind": "unregistered_local_rng_constructor",
        "authority": "dynamic_script_plugin_entropy",
        "line": 2,
        "symbol": symbol,
    } in report["findings"]


def test_script_entropy_audit_rejects_numpy_and_os_entropy() -> None:
    report = audit_script_entropy(
        "import numpy as np\nimport secrets\nnp.random.random()\nsecrets.token_bytes(2)\n"
    )
    assert report["deterministic_ready"] is False
    assert {finding["authority"] for finding in report["findings"]} == {
        "numpy_legacy_global_randomstate",
        "os_entropy",
    }


def test_script_entropy_audit_resolves_import_aliases_and_rebindings() -> None:
    report = audit_script_entropy(
        "import random as rng\n"
        "source = rng\n"
        "source.randrange(4)\n"
        "from uuid import uuid4 as make_id\n"
        "make_id()\n"
    )
    assert report["deterministic_ready"] is False
    assert {item["authority"] for item in report["findings"]} == {
        "python_process_global_random",
        "os_entropy",
    }


def test_script_entropy_audit_rejects_dynamic_import_and_execution() -> None:
    sources = (
        "__import__('random').random()\n",
        "import importlib as loader\nloader.import_module('secrets')\n",
        "from builtins import eval as run\nrun('random.random()')\n",
        "import builtins\nbuiltins.exec('import uuid')\n",
    )
    for source in sources:
        report = audit_script_entropy(source)
        assert report["deterministic_ready"] is False, source
        assert any(
            finding["kind"] in {"opaque_dynamic_import", "opaque_dynamic_execution"}
            for finding in report["findings"]
        ), source


def test_script_entropy_audit_rejects_reflective_entropy_lookup() -> None:
    report = audit_script_entropy(
        "import random as rng\ngetattr(rng, 'SystemRandom')()\n"
    )
    assert report["deterministic_ready"] is False
    assert any(
        finding["kind"] == "opaque_reflective_entropy_access"
        for finding in report["findings"]
    )


def test_script_entropy_audit_keeps_injected_owner_calls_admissible() -> None:
    report = audit_script_entropy("self.random_uniform(0, 1)\n")
    assert report["deterministic_ready"] is True
    assert report["findings"] == []


def test_script_entropy_audit_rejects_direct_owner_consumption() -> None:
    report = audit_script_entropy("self.randomness_rng.random()\n", path="owner.py")
    assert report["deterministic_ready"] is False
    assert report["findings"] == [{
        "kind": "untracked_owner_consumption",
        "authority": "dynamic_script_plugin_entropy",
        "line": 1,
        "symbol": "self.randomness_rng.random",
    }]


def test_dynamic_script_boundary_receipt_quarantines_opaque_corpus() -> None:
    receipt = build_dynamic_script_boundary_receipt(
        [{"path": "opaque.py", "deterministic_ready": False, "findings": [{"kind": "x"}]}],
        [],
        [],
        [],
    )
    assert receipt["status"] == "quarantined"
    assert receipt["opaque_findings"] is True
    assert validate_dynamic_script_boundary_receipt(receipt) == {
        "valid": True,
        "errors": [],
    }


def test_dynamic_script_boundary_receipt_rejects_admission_overclaim() -> None:
    receipt = build_dynamic_script_boundary_receipt([], [], [], [])
    receipt["status"] = "admitted"
    receipt["opaque_findings"] = True
    assert validate_dynamic_script_boundary_receipt(receipt)["valid"] is False


def test_script_entropy_audit_is_conservative_on_syntax_errors() -> None:
    report = audit_script_entropy("class Broken(:\n", path="broken.py")
    assert report["parseable"] is False
    assert report["deterministic_ready"] is False
    assert report["findings"][0]["kind"] == "syntax_error"


def test_script_entropy_receipt_seals_source_and_owner(tmp_path) -> None:
    path = tmp_path / "owned_script.py"
    path.write_text("from core.Lotucosm.scripts import ScriptBase\n", encoding="utf-8")
    audit = audit_script_entropy(path.read_text(encoding="utf-8"), path=str(path))
    receipt = build_script_entropy_receipt(
        audit,
        owner_family="Generator",
        runtime_epoch="epoch-1",
    )
    assert receipt["schema_version"] == 1
    assert len(receipt["source_sha256"]) == 64
    assert len(receipt["audit_sha256"]) == 64
    assert receipt["owner_family"] == "Generator"


def test_script_entropy_receipt_requires_registry_binding_when_requested(tmp_path) -> None:
    path = tmp_path / "bound_owner.py"
    path.write_text("value = 1\n", encoding="utf-8")
    audit = audit_script_entropy(path.read_text(encoding="utf-8"), path=str(path))
    receipt = build_script_entropy_receipt(
        audit,
        owner_family="Random",
        runtime_epoch="epoch-1",
        owner_stream_name="sr.runtime",
        owner_registry_digest="a" * 64,
    )
    assert receipt["owner_stream_name"] == "sr.runtime"
    result = diagnose_script_entropy_admission(
        [audit],
        [receipt],
        owner_family="Random",
        runtime_epoch="epoch-1",
        owner_stream_name="sr.runtime",
        owner_registry_digest="b" * 64,
    )
    assert result == {"admitted": False, "reasons": ["opaque_owner"]}


def test_script_entropy_admission_classifies_missing_receipt(tmp_path) -> None:
    path = tmp_path / "missing.py"
    path.write_text("value = 1\n", encoding="utf-8")
    audit = audit_script_entropy(path.read_text(encoding="utf-8"), path=str(path))
    result = diagnose_script_entropy_admission([audit], [])
    assert result == {"admitted": False, "reasons": ["receipt_missing"]}


def test_script_entropy_admission_detects_source_digest_change(tmp_path) -> None:
    path = tmp_path / "changed.py"
    path.write_text("value = 1\n", encoding="utf-8")
    audit = audit_script_entropy(path.read_text(encoding="utf-8"), path=str(path))
    receipt = build_script_entropy_receipt(audit, owner_family="Random", runtime_epoch="epoch-1")
    path.write_text("value = 2\n", encoding="utf-8")
    result = diagnose_script_entropy_admission(
        [audit], [receipt], owner_family="Random", runtime_epoch="epoch-1"
    )
    assert result == {"admitted": False, "reasons": ["source_digest_changed"]}


def test_script_file_audit_binds_exact_source_bytes(tmp_path) -> None:
    path = tmp_path / "bound.py"
    source = b"value = 1\r\n"
    path.write_bytes(source)
    audit = audit_script_file(path)
    receipt = build_script_entropy_receipt(
        audit,
        owner_family="Random",
        runtime_epoch="epoch-1",
        source_sha256=audit["source_sha256"],
    )
    assert receipt["source_sha256"] == audit["source_sha256"]
    path.write_bytes(source.replace(b"1", b"2"))
    result = diagnose_script_entropy_admission([audit], [receipt])
    assert result == {"admitted": False, "reasons": ["source_digest_changed"]}


def test_script_entropy_admission_recomputes_findings_instead_of_trusting_ready_flag(tmp_path) -> None:
    path = tmp_path / "tampered_audit.py"
    path.write_text("value = 1\n", encoding="utf-8")
    audit = audit_script_file(path)
    receipt = build_script_entropy_receipt(
        audit,
        owner_family="Random",
        runtime_epoch="epoch-1",
        source_sha256=audit["source_sha256"],
    )
    audit["findings"] = [{
        "kind": "opaque_dynamic_import",
        "authority": "unknown_dynamic_module",
    }]
    result = diagnose_script_entropy_admission([audit], [receipt])
    assert result == {"admitted": False, "reasons": ["legacy_audit"]}


def test_script_entropy_admission_detects_owner_or_epoch_mismatch(tmp_path) -> None:
    path = tmp_path / "owner.py"
    path.write_text("value = 1\n", encoding="utf-8")
    audit = audit_script_entropy(path.read_text(encoding="utf-8"), path=str(path))
    receipt = build_script_entropy_receipt(audit, owner_family="Random", runtime_epoch="epoch-1")
    result = diagnose_script_entropy_admission(
        [audit], [receipt], owner_family="OtherRandom", runtime_epoch="epoch-2"
    )
    assert result == {"admitted": False, "reasons": ["opaque_owner"]}


def test_script_entropy_admission_keeps_empty_legacy_scene_compatible() -> None:
    assert diagnose_script_entropy_admission([], []) == {"admitted": True, "reasons": []}


def test_script_entropy_admission_classifies_legacy_audit(tmp_path) -> None:
    path = tmp_path / "legacy.py"
    path.write_text("import random\nrandom.random()\n", encoding="utf-8")
    audit = audit_script_entropy(path.read_text(encoding="utf-8"), path=str(path))
    receipt = {
        "path": str(path),
        "owner_family": "Random",
        "runtime_epoch": "epoch-1",
        "source_sha256": "0" * 64,
        "audit_sha256": "0" * 64,
    }
    result = diagnose_script_entropy_admission([audit], [receipt])
    assert result == {"admitted": False, "reasons": ["legacy_audit"]}


def test_viewport_executes_audited_source_and_reuses_identical_receipts(tmp_path) -> None:
    import json

    path = tmp_path / "behavior.py"
    project = tmp_path / "project"
    scripts = project / "scripts"
    scripts.mkdir(parents=True)
    path = scripts / "behavior.py"
    path.write_text("from core.Lotucosm.scripts import ScriptBase\nclass Behavior(ScriptBase):\n    pass\n", encoding="utf-8")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    (project / "project.json").write_text(json.dumps({
        "script_trust": {"sha256_allowlist": [{"path": "scripts/behavior.py", "sha256": digest}]}
    }), encoding="utf-8")
    viewport = _bare_viewport()
    first = viewport._instantiate_scene_script({"path": str(path)}, str(project))
    second = viewport._instantiate_scene_script({"path": str(path)}, str(project))
    assert first is not None and second is not None
    assert len(viewport._sr_script_entropy_audits) == 1
    assert len(viewport._sr_script_entropy_receipts) == 1
    assert all(item["source_sha256"] == digest for item in viewport._sr_script_entropy_audits)
    assert all(item["source_sha256"] == digest for item in viewport._sr_script_entropy_receipts)


def test_viewport_rejects_source_replacement_during_script_construction(tmp_path, monkeypatch) -> None:
    project = tmp_path / "project"
    scripts = project / "scripts"
    scripts.mkdir(parents=True)
    path = scripts / "racing.py"
    path.write_text(
        "from core.Lotucosm.scripts import ScriptBase\n"
        "class Behavior(ScriptBase):\n"
        "    def __init__(self):\n"
        "        open(__file__, 'w').write('value = 9\\n')\n",
        encoding="utf-8",
    )
    import json
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    (project / "project.json").write_text(json.dumps({
        "script_trust": {"sha256_allowlist": [{"path": "scripts/racing.py", "sha256": digest}]}
    }), encoding="utf-8")
    viewport = _bare_viewport()
    result = viewport._instantiate_scene_script({"path": str(path)}, str(project))
    assert result is None
    assert viewport._sr_script_entropy_audits == []
    assert viewport._sr_script_entropy_receipts == []
    assert viewport._sr_script_failure_receipts[-1]["reason"] == "source_changed"
    assert viewport._sr_script_failure_receipts[-1]["phase"] == "construct"


def test_viewport_failed_constructor_leaves_no_entropy_evidence(tmp_path) -> None:
    import json
    project = tmp_path / "project"
    scripts = project / "scripts"
    scripts.mkdir(parents=True)
    path = scripts / "failure.py"
    path.write_text(
        "from core.Lotucosm.scripts import ScriptBase\n"
        "class Behavior(ScriptBase):\n"
        "    def __init__(self):\n"
        "        raise RuntimeError('constructor failed')\n",
        encoding="utf-8",
    )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    (project / "project.json").write_text(json.dumps({
        "script_trust": {"sha256_allowlist": [{"path": "scripts/failure.py", "sha256": digest}]}
    }), encoding="utf-8")
    viewport = _bare_viewport()
    assert viewport._instantiate_scene_script({"path": str(path)}, str(project)) is None
    assert viewport._sr_script_entropy_audits == []
    assert viewport._sr_script_entropy_receipts == []
    assert viewport._sr_script_failure_receipts[-1]["reason"] == "construction_failed"


def test_viewport_failure_projection_is_sanitized_and_observable(tmp_path) -> None:
    from core.VitaLoom.viewports.game_viewport import GameViewport

    viewport = GameViewport.__new__(GameViewport)
    viewport._sr_runtime_epoch = "epoch-failure"
    viewport._sr_script_failure_receipts = []
    viewport._record_script_failure(
        tmp_path / "blocked.py",
        "trust",
        "script_not_trusted",
        PermissionError("do not expose this"),
    )
    receipt = viewport._sr_script_failure_receipts[0]
    assert receipt["status"] == "script_runtime_failure"
    assert receipt["reason"] == "script_not_trusted"
    assert receipt["exception_type"] == "PermissionError"
    assert "do not expose this" not in str(receipt)


def test_project_script_trust_defaults_to_denied_and_binds_digest(tmp_path) -> None:
    project = tmp_path / "project"
    scripts = project / "scripts"
    scripts.mkdir(parents=True)
    path = scripts / "entry.py"
    path.write_text("value = 1\n", encoding="utf-8")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    (project / "project.json").write_text("{}", encoding="utf-8")
    assert evaluate_project_script_trust(path, project, source_sha256=digest)["reason"] == "script_trust_not_configured"
    (project / "project.json").write_text(json.dumps({
        "script_trust": {"sha256_allowlist": [{"path": "scripts/entry.py", "sha256": digest}]}
    }), encoding="utf-8")
    assert evaluate_project_script_trust(path, project, source_sha256=digest)["trusted"] is True
    changed = hashlib.sha256(b"value = 2\n").hexdigest()
    assert evaluate_project_script_trust(path, project, source_sha256=changed)["reason"] == "script_trust_digest_mismatch"
    assert evaluate_project_script_trust(tmp_path / "outside.py", project, source_sha256=digest)["reason"] == "script_outside_project"


def test_project_script_trust_source_validation_checks_all_grants(tmp_path) -> None:
    project = tmp_path / "project"
    scripts = project / "scripts"
    scripts.mkdir(parents=True)
    path = scripts / "entry.py"
    path.write_text("value = 1\n", encoding="utf-8")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    (project / "project.json").write_text(json.dumps({
        "script_trust": {"sha256_allowlist": [{"path": "scripts/entry.py", "sha256": digest}]}
    }), encoding="utf-8")

    result = validate_project_script_trust_sources(project)
    assert result["trusted"] is True
    assert result["checked_count"] == 1

    path.write_text("value = 2\n", encoding="utf-8")
    changed = validate_project_script_trust_sources(project)
    assert changed["reason"] == "script_source_digest_mismatch"


def test_project_script_trust_source_validation_rejects_path_escape(tmp_path) -> None:
    project = tmp_path / "project"
    (project / "scripts").mkdir(parents=True)
    outside = project / "outside.py"
    outside.write_text("value = 1\n", encoding="utf-8")
    digest = hashlib.sha256(outside.read_bytes()).hexdigest()
    (project / "project.json").write_text(json.dumps({
        "script_trust": {"sha256_allowlist": [{"path": "scripts/../outside.py", "sha256": digest}]}
    }), encoding="utf-8")
    assert validate_project_script_trust_sources(project)["reason"] == "script_path_not_project_script"


def test_approval_tool_requires_explicit_flag_and_updates_only_one_grant(tmp_path) -> None:
    import json
    from tools.approve_project_script import main

    project = tmp_path / "project"
    scripts = project / "scripts"
    scripts.mkdir(parents=True)
    (project / "project.json").write_text('{"name": "fixture"}', encoding="utf-8")
    script = scripts / "approved.py"
    script.write_text("value = 1\n", encoding="utf-8")
    assert main([str(project), "scripts/approved.py"]) == 2
    assert main([str(project), "scripts/approved.py", "--approve"]) == 0
    data = json.loads((project / "project.json").read_text(encoding="utf-8"))
    grants = data["script_trust"]["sha256_allowlist"]
    assert len(grants) == 1
    assert grants[0]["path"] == "scripts/approved.py"
    assert grants[0]["sha256"] == hashlib.sha256(script.read_bytes()).hexdigest()
