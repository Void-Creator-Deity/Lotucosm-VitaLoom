# -*- coding: utf-8 -*-
"""
场景脚本 properties 的检视器编辑：解析 inspector 键名、嵌套读写、与 SceneManager 单一写回通道。

对齐 Unity SerializedProperty / Godot 属性路径的思路：用稳定的「点分路径」映射 JSON 子树，而非在 UI 散落的重复逻辑。

排错: Inspector 脚本字段不保存 → apply_script_property_to_holder 与 nested_set 路径。
"""

from __future__ import annotations

import copy
import importlib.util
import json
import os
from typing import Any, Callable, Dict, List, Optional, Tuple

__all__ = [
    "nested_get",
    "nested_set",
    "scripts_holder",
    "script_names_from_holder",
    "parse_script_inspector_key",
    "inspector_key_for_script_field",
    "infer_scalar_prop_type",
    "coerce_for_script_value",
    "coerce_script_property_update",
    "flatten_script_properties",
    "normalize_script_properties_dict",
    "snapshot_scripts",
    "restore_scripts",
    "apply_script_property_to_holder",
    "merge_script_property_into_entity_by_prop_key",
    "apply_entity_script_property_to_scene",
    "entity_id_from_inspector_obj",
    "load_sr_inspector_schema",
    "inspector_rows_for_script",
]


def nested_get(root: Dict[str, Any], dotted: str) -> Any:
    cur: Any = root
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def nested_set(root: Dict[str, Any], dotted: str, value: Any) -> None:
    parts = dotted.split(".")
    cur = root
    for part in parts[:-1]:
        nxt = cur.get(part)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[part] = nxt
        cur = nxt
    cur[parts[-1]] = value


def scripts_holder(obj: Any) -> Any:
    if isinstance(obj, dict):
        if obj.get("type") == "entity":
            inner = obj.get("data")
            if isinstance(inner, dict):
                return inner
        if isinstance(obj.get("scripts"), list):
            return obj
    return obj


def script_names_from_holder(holder: Any) -> List[str]:
    scripts = getattr(holder, "scripts", None)
    if scripts is None and isinstance(holder, dict):
        scripts = holder.get("scripts")
    if not isinstance(scripts, list):
        return []
    out: List[str] = []
    for sd in scripts:
        if isinstance(sd, dict):
            n = sd.get("name")
            if isinstance(n, str) and n:
                out.append(n)
    return out


def parse_script_inspector_key(prop_name: str, script_names: List[str]) -> Optional[Tuple[str, str]]:
    prefix = "script_"
    if not prop_name.startswith(prefix):
        return None
    rest = prop_name[len(prefix) :]
    for sn in sorted(script_names, key=len, reverse=True):
        sep = sn + "_"
        if rest.startswith(sep):
            path = rest[len(sep) :]
            return (sn, path) if path else None
    return None


def inspector_key_for_script_field(script_name: str, dotted_path: str) -> str:
    return f"script_{script_name}_{dotted_path}"


def infer_scalar_prop_type(val: Any) -> type:
    if isinstance(val, bool):
        return bool
    if isinstance(val, int) and not isinstance(val, bool):
        return int
    if isinstance(val, float):
        return float
    return str


def coerce_for_script_value(new_value: Any, hint: type) -> Any:
    if hint == bool:
        return bool(new_value)
    if hint == int:
        try:
            return int(round(float(new_value)))
        except (TypeError, ValueError):
            return int(new_value)
    if hint == float:
        try:
            return float(new_value)
        except (TypeError, ValueError):
            return float(str(new_value))
    if hint == str:
        return str(new_value)
    try:
        return float(new_value)
    except (TypeError, ValueError):
        return new_value


def coerce_script_property_update(old_value: Any, raw_new: Any) -> Any:
    """根据旧值类型决定如何把检视器 raw 输入写成 JSON 兼容值。"""
    try:
        if isinstance(old_value, list):
            return json.loads(str(raw_new))
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    hint = infer_scalar_prop_type(old_value) if old_value is not None else float
    try:
        return coerce_for_script_value(raw_new, hint)
    except Exception:
        return raw_new


def flatten_script_properties(
    props: Dict[str, Any], prefix: str = ""
) -> List[Tuple[str, str, Any, type]]:
    rows: List[Tuple[str, str, Any, type]] = []
    for key in sorted(props.keys()):
        path = f"{prefix}.{key}" if prefix else key
        label = path.replace(".", " › ")
        val = props[key]
        if isinstance(val, dict):
            rows.extend(flatten_script_properties(val, path))
        elif isinstance(val, list):
            try:
                txt = json.dumps(val, ensure_ascii=False)
            except (TypeError, ValueError):
                txt = str(val)
            rows.append((label, path, txt, str))
        else:
            rows.append((label, path, val, infer_scalar_prop_type(val)))
    return rows


def snapshot_scripts(holder: Any) -> Any:
    scripts = getattr(holder, "scripts", None)
    if scripts is None and isinstance(holder, dict):
        scripts = holder.get("scripts")
    return copy.deepcopy(scripts) if scripts is not None else []


def restore_scripts(holder: Any, snapshot: Any) -> None:
    if isinstance(holder, dict):
        holder["scripts"] = copy.deepcopy(snapshot)
    else:
        setattr(holder, "scripts", copy.deepcopy(snapshot))


def apply_script_property_to_holder(holder: Any, script_name: str, dotted_path: str, coerced: Any) -> None:
    scripts = getattr(holder, "scripts", None)
    if scripts is None and isinstance(holder, dict):
        scripts = holder.get("scripts")
    if not isinstance(scripts, list):
        return
    for sd in scripts:
        if isinstance(sd, dict) and sd.get("name") == script_name:
            p = sd.setdefault("properties", {})
            if not isinstance(p, dict):
                p = {}
                sd["properties"] = p
            nested_set(p, dotted_path, coerced)
            break


def normalize_script_properties_dict(script_props: Dict[str, Any]) -> Dict[str, Any]:
    norm: Dict[str, Any] = {}
    for k, v in script_props.items():
        if isinstance(v, dict) and "value" in v:
            norm[k] = v.get("value")
        else:
            norm[k] = v
    return norm


def merge_script_property_into_entity_by_prop_key(
    entity: Dict[str, Any], inspector_prop_key: str, raw_new: Any
) -> bool:
    """
    在单个 entity 字典上合并脚本字段（就地修改）。
    inspector_prop_key 形如 script_<脚本名>_<点分路径>。
    """
    names: List[str] = []
    for sd in entity.get("scripts", []) or []:
        if isinstance(sd, dict):
            n = sd.get("name")
            if isinstance(n, str) and n:
                names.append(n)
    parsed = parse_script_inspector_key(inspector_prop_key, names)
    if not parsed:
        return False
    script_name, dotted_path = parsed
    for sd in entity.get("scripts", []) or []:
        if not isinstance(sd, dict) or sd.get("name") != script_name:
            continue
        props = sd.setdefault("properties", {})
        if not isinstance(props, dict):
            props = {}
            sd["properties"] = props
        old_v = nested_get(props, dotted_path)
        coerced = coerce_script_property_update(old_v, raw_new)
        nested_set(props, dotted_path, coerced)
        return True
    return False


def apply_entity_script_property_to_scene(
    entity_id: str,
    inspector_prop_key: str,
    raw_new: Any,
    *,
    get_scene_manager: Optional[Callable[[], Any]] = None,
) -> bool:
    """
    单一写回通道：更新 SceneManager 中当前场景的 entities，并标记脏。
    get_scene_manager 可注入便于测试；默认使用 VitaLoom SceneManager。
    """
    if get_scene_manager is None:
        from core.VitaLoom.scene.scene_manager import get_scene_manager as _gsm

        get_scene_manager = _gsm

    sm = get_scene_manager()
    scene_data = sm.get_scene_data()
    if not scene_data:
        return False
    entities = scene_data.get("entities", [])
    if not isinstance(entities, list):
        return False

    changed = False
    for entity in entities:
        if not isinstance(entity, dict) or entity.get("id") != entity_id:
            continue
        if merge_script_property_into_entity_by_prop_key(entity, inspector_prop_key, raw_new):
            changed = True
        break

    if changed:
        sm.update_scene_data({"entities": entities})
    return changed


def load_sr_inspector_schema(script_py_path: Optional[str]) -> Optional[List[Dict[str, Any]]]:
    """从项目脚本文件顶层读取 SR_INSPECTOR_SCHEMA（可选）。"""
    if not script_py_path or not os.path.isfile(script_py_path):
        return None
    try:
        mod_name = f"_sr_inspect_{abs(hash(script_py_path))}"
        spec = importlib.util.spec_from_file_location(mod_name, script_py_path)
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        schema = getattr(mod, "SR_INSPECTOR_SCHEMA", None)
        return schema if isinstance(schema, list) else None
    except Exception:
        return None


def _python_type_from_schema_type(t: str) -> type:
    t = (t or "float").strip().lower()
    if t in ("int", "integer"):
        return int
    if t in ("float", "double", "number"):
        return float
    if t in ("bool", "boolean"):
        return bool
    return str


def inspector_rows_for_script(
    script_name: str,
    norm_properties: Dict[str, Any],
    scripts_project_dir: Optional[str],
) -> List[Dict[str, Any]]:
    """
    生成检视器行描述 dict：
    keys: group, label, path, value, prop_type, min_val, max_val, step
    """
    rows: List[Dict[str, Any]] = []
    schema_path = None
    if scripts_project_dir:
        schema_path = os.path.join(scripts_project_dir, f"{script_name}.py")
    schema = load_sr_inspector_schema(schema_path)
    covered: set[str] = set()

    if schema:
        for item in schema:
            if not isinstance(item, dict):
                continue
            path = str(item.get("path", "")).strip()
            if not path:
                continue
            covered.add(path)
            label = str(item.get("label", path.replace(".", " › ")))
            group = str(item.get("group", "")).strip() or script_name
            st = _python_type_from_schema_type(str(item.get("type", "float")))
            raw_val = nested_get(norm_properties, path)
            if raw_val is None:
                if st == float:
                    raw_val = 0.0
                elif st == int:
                    raw_val = 0
                elif st == bool:
                    raw_val = False
                else:
                    raw_val = ""
            row: Dict[str, Any] = {
                "group": group,
                "label": label,
                "path": path,
                "value": raw_val,
                "prop_type": st,
                "min_val": item.get("min"),
                "max_val": item.get("max"),
                "step": item.get("step"),
            }
            rows.append(row)

        for label, path, val, ptyp in flatten_script_properties(norm_properties):
            if path in covered:
                continue
            extra_min, extra_max, extra_step = -1e9, 1e9, 0.01
            erow: Dict[str, Any] = {
                "group": script_name,
                "label": label,
                "path": path,
                "value": val,
                "prop_type": ptyp,
                "min_val": extra_min if ptyp == float else None,
                "max_val": extra_max if ptyp == float else None,
                "step": extra_step if ptyp == float else None,
            }
            rows.append(erow)
        return rows

    for label, path, val, ptyp in flatten_script_properties(norm_properties):
        extra_min, extra_max, extra_step = -1e9, 1e9, 0.01
        rows.append(
            {
                "group": script_name,
                "label": label,
                "path": path,
                "value": val,
                "prop_type": ptyp,
                "min_val": extra_min if ptyp == float else None,
                "max_val": extra_max if ptyp == float else None,
                "step": extra_step if ptyp == float else None,
            }
        )
    return rows


def entity_id_from_inspector_obj(obj: Any) -> Optional[str]:
    if isinstance(obj, dict):
        return obj.get("id") or obj.get("data", {}).get("id")
    return getattr(obj, "id", None)
