# -*- coding: utf-8 -*-
"""
script_property_edit：检视器键解析、嵌套写回、场景单一写回通道（无 Qt）。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""

from __future__ import annotations

import pathlib
from typing import Any, Dict

from core.VitaLoom.scene import script_property_edit as spe


def test_parse_script_inspector_key_longest_script_name_first() -> None:
    names = ["evo_central_brain_pvaec", "evo"]
    key = "script_evo_central_brain_pvaec_mind.wander_amp"
    got = spe.parse_script_inspector_key(key, names)
    assert got == ("evo_central_brain_pvaec", "mind.wander_amp")


def test_parse_script_inspector_key_rejects_empty_path() -> None:
    assert spe.parse_script_inspector_key("script_foo_", ["foo"]) is None


def test_nested_get_set() -> None:
    root: Dict[str, Any] = {"a": {"b": {"c": 1}}}
    assert spe.nested_get(root, "a.b.c") == 1
    spe.nested_set(root, "a.b.d", 99)
    assert root["a"]["b"]["d"] == 99
    spe.nested_set(root, "x.y.z", "ok")
    assert root["x"]["y"]["z"] == "ok"


def test_normalize_script_properties_dict_value_wrapper() -> None:
    raw = {"k": {"value": 7}, "plain": 3}
    assert spe.normalize_script_properties_dict(raw) == {"k": 7, "plain": 3}


def test_coerce_script_property_update_list_json_string() -> None:
    old = [1, 2]
    assert spe.coerce_script_property_update(old, "[3, 4]") == [3, 4]


def test_coerce_script_property_update_scalar_float() -> None:
    assert spe.coerce_script_property_update(1.5, "2.25") == 2.25


def test_scripts_holder_entity_wrapper() -> None:
    wrapped = {"type": "entity", "data": {"id": "e1", "scripts": []}}
    h = spe.scripts_holder(wrapped)
    assert h == wrapped["data"]
    assert spe.entity_id_from_inspector_obj(wrapped) == "e1"


def test_merge_script_property_into_entity_by_prop_key() -> None:
    entity = {
        "id": "e1",
        "scripts": [
            {"name": "my_script", "properties": {"mind": {"wander_amp": 1.0}}},
        ],
    }
    ok = spe.merge_script_property_into_entity_by_prop_key(
        entity, "script_my_script_mind.wander_amp", "7.5"
    )
    assert ok
    assert entity["scripts"][0]["properties"]["mind"]["wander_amp"] == 7.5


def test_apply_entity_script_property_to_scene_injected_manager() -> None:
    entities = [
        {"id": "x", "scripts": [{"name": "s", "properties": {"a": 1}}]},
    ]
    store: Dict[str, Any] = {"entities": entities}
    calls: list[Dict[str, Any]] = []

    class _SM:
        def get_scene_data(self) -> Dict[str, Any]:
            return store

        def update_scene_data(self, patch: Dict[str, Any]) -> None:
            calls.append(patch)
            if "entities" in patch:
                store["entities"] = patch["entities"]

    def _gsm() -> _SM:
        return _SM()

    ok = spe.apply_entity_script_property_to_scene(
        "x", "script_s_a", 42, get_scene_manager=_gsm
    )
    assert ok
    assert entities[0]["scripts"][0]["properties"]["a"] == 42
    assert calls == [{"entities": entities}]


def test_inspector_rows_schema_groups_for_evo_central_brain() -> None:
    repo = pathlib.Path(__file__).resolve().parents[1]
    script_path = repo / "projects" / "pvaec-细胞演化" / "scripts" / "evo_central_brain_pvaec.py"
    if not script_path.is_file():
        return
    scripts_dir = str(script_path.parent)
    norm = {"mind": {"wander_amp": 6.5}, "evo": {"reproduce_energy": 100.0}}
    rows = spe.inspector_rows_for_script("evo_central_brain_pvaec", norm, scripts_dir)
    groups = {r["group"] for r in rows}
    assert "心智" in groups
    assert "演化" in groups
    mind_rows = [r for r in rows if r["path"] == "mind.wander_amp"]
    assert mind_rows and mind_rows[0]["label"] == "漫游幅度"


def test_inspector_rows_schema_sensor_patrol_pvaec() -> None:
    repo = pathlib.Path(__file__).resolve().parents[1]
    script_path = repo / "projects" / "pvaec-细胞演化" / "scripts" / "sensor_patrol_pvaec.py"
    if not script_path.is_file():
        return
    scripts_dir = str(script_path.parent)
    norm = {"patrol": {"patrol_amp": 4.0, "org_pull": 8.0}}
    rows = spe.inspector_rows_for_script("sensor_patrol_pvaec", norm, scripts_dir)
    pr = [r for r in rows if r["path"] == "patrol.patrol_amp"]
    assert pr and pr[0]["label"] == "巡逻幅度"


def test_inspector_rows_schema_actuator_pulse_pvaec() -> None:
    repo = pathlib.Path(__file__).resolve().parents[1]
    script_path = repo / "projects" / "pvaec-细胞演化" / "scripts" / "actuator_pulse_pvaec.py"
    if not script_path.is_file():
        return
    scripts_dir = str(script_path.parent)
    norm = {"pulse": {"radial_amp": 18.0, "omega": 2.15}}
    rows = spe.inspector_rows_for_script("actuator_pulse_pvaec", norm, scripts_dir)
    om = [r for r in rows if r["path"] == "pulse.omega"]
    assert om and "ω" in om[0]["label"]


def test_apply_entity_script_property_no_entity_returns_false() -> None:
    store = {"entities": [{"id": "other", "scripts": []}]}

    class _SM:
        def get_scene_data(self) -> Dict[str, Any]:
            return store

        def update_scene_data(self, patch: Dict[str, Any]) -> None:
            raise AssertionError("should not update")

    assert not spe.apply_entity_script_property_to_scene(
        "missing", "script_s_a", 1, get_scene_manager=lambda: _SM()
    )
