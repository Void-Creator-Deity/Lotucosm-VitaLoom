# -*- coding: utf-8 -*-
"""Qt-free downstream extension operator inspection/recovery authority."""
from __future__ import annotations

import json
from pathlib import Path

import pytest


def _inspection(**overrides):
    from core.VitaLoom.project.plugin_host_operator import build_plugin_host_inspection

    facts = {
        "project_path": "C:/worlds/example",
        "embedded_catalog_project_path": "C:/worlds/example",
        "catalog_entries": [
            {
                "plugin_id": "ExamplePlugin",
                "scope": "embedded_mod",
                "source": "C:/worlds/example/addons/example/example_plugin.py",
                "version": "1.0.0",
                "dependencies": [],
                "protected": False,
            }
        ],
        "active_plugin_ids": ["ExamplePlugin"],
        "failed_plugins": {},
        "discovery_report": {"status": "ready", "project_path": "C:/worlds/example", "diagnostics": []},
        "lifecycle_report": {
            "status": "settled",
            "source": "project_open",
            "completed": {"deactivated": [], "activated": ["ExamplePlugin"]},
            "diagnostics": [],
            "failed_action": None,
        },
    }
    facts.update(overrides)
    return build_plugin_host_inspection(**facts)


def test_inspection_is_deterministic_json_safe_and_settled_has_no_recovery() -> None:
    first = _inspection()
    second = _inspection(active_plugin_ids={"ExamplePlugin"})

    assert first == second
    assert first["schema_version"] == 1
    assert first["status"] == "settled"
    assert first["active_plugin_ids"] == ["ExamplePlugin"]
    assert first["recoveries"] == []
    assert len(first["report_id"]) == 64
    json.dumps(first, ensure_ascii=False, sort_keys=True)


def test_inspection_normalises_non_finite_numbers_to_strict_json() -> None:
    inspection = _inspection(
        discovery_report={
            "status": "blocked",
            "diagnostics": [
                {"code": "non_finite_probe", "value": float("nan")},
                {"code": "positive_infinity_probe", "value": float("inf")},
                {"code": "negative_infinity_probe", "value": float("-inf")},
            ],
        }
    )

    encoded = json.dumps(inspection, ensure_ascii=False, sort_keys=True, allow_nan=False)
    assert "NaN" in encoded
    assert "Infinity" in encoded
    assert inspection["discovery"]["diagnostics"][0]["value"] == "NaN"
    assert inspection["discovery"]["diagnostics"][1]["value"] == "Infinity"
    assert inspection["discovery"]["diagnostics"][2]["value"] == "-Infinity"


def test_report_identity_changes_for_every_operator_relevant_fact() -> None:
    baseline = _inspection()["report_id"]
    variants = [
        _inspection(project_path="C:/worlds/other"),
        _inspection(embedded_catalog_project_path="C:/worlds/old"),
        _inspection(active_plugin_ids=[]),
        _inspection(failed_plugins={"ExamplePlugin": "boom"}),
        _inspection(discovery_report={"status": "blocked", "diagnostics": [{"code": "bad"}]}),
        _inspection(lifecycle_report={"status": "blocked", "diagnostics": [{"code": "cycle"}]}),
        _inspection(catalog_entries=[]),
    ]
    assert all(item["report_id"] != baseline for item in variants)


def test_blocked_and_partial_states_offer_confirmation_bound_normal_retry() -> None:
    from core.VitaLoom.project.plugin_host_operator import validate_plugin_host_recovery

    blocked = _inspection(
        embedded_catalog_project_path="C:/worlds/old",
        discovery_report={
            "status": "blocked",
            "project_path": "C:/worlds/example",
            "diagnostics": [{"code": "addon_manifest_malformed"}],
        },
    )
    assert blocked["status"] == "blocked"
    assert blocked["embedded_catalog_project_path"].endswith("worlds\\old")
    recovery = blocked["recoveries"][0]
    assert recovery["action"] == "retry_project_lifecycle"
    assert recovery["requires_manual_review"] is False
    validated = validate_plugin_host_recovery(
        blocked,
        project_path=blocked["project_path"],
        report_id=blocked["report_id"],
        action=recovery["action"],
        operator_confirmation=recovery["operator_confirmation_required"],
    )
    assert validated["action"] == "retry_project_lifecycle"

    partial = _inspection(
        lifecycle_report={
            "status": "failed",
            "completed": {"deactivated": [], "activated": ["IndependentPlugin"]},
            "skipped": {"activation": [{"plugin_id": "DependentPlugin", "blocked_by": ["BrokenPlugin"]}]},
            "failed_action": {"action": "activate", "plugin_id": "BrokenPlugin"},
            "diagnostics": [],
        }
    )
    assert partial["status"] == "partial"
    assert partial["recoveries"][0]["requires_manual_review"] is True
    assert "callback" in partial["recoveries"][0]["risk"]


def test_project_report_action_and_confirmation_mismatches_fail_closed() -> None:
    from core.VitaLoom.project.plugin_host_operator import (
        PluginHostOperatorError,
        validate_plugin_host_recovery,
    )

    inspection = _inspection(
        lifecycle_report={"status": "blocked", "diagnostics": [{"code": "plugin_dependency_cycle"}]}
    )
    recovery = inspection["recoveries"][0]
    cases = [
        {"project_path": "C:/worlds/other"},
        {"report_id": "0" * 64},
        {"action": "force_unload"},
        {"operator_confirmation": "yes"},
    ]
    base = {
        "project_path": inspection["project_path"],
        "report_id": inspection["report_id"],
        "action": recovery["action"],
        "operator_confirmation": recovery["operator_confirmation_required"],
    }
    for override in cases:
        payload = {**base, **override}
        with pytest.raises(PluginHostOperatorError):
            validate_plugin_host_recovery(inspection, **payload)


def test_operator_module_is_qt_free() -> None:
    module = Path(__file__).parents[1] / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/project/plugin_host_operator.py"
    source = module.read_text(encoding="utf-8-sig")
    assert "PyQt6" not in source
    assert "EditorContext" not in source
