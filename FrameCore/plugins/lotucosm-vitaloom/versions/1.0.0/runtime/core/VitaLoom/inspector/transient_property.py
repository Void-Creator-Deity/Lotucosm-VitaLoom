"""Qt-free property access for Inspector-owned transient objects.

The Inspector may display Python objects which do not belong to a persisted
``.pond`` scene.  This module keeps that small property contract independent
of Qt and makes every read/write explicit so Registry history can guard it.
"""

from __future__ import annotations

from typing import Any, Tuple

from core.VitaLoom.scene import script_property_edit as spe


_MISSING = object()


def _nested_state(root: Any, dotted_path: str) -> Tuple[bool, Any]:
    current = root
    parts = [part for part in str(dotted_path).split(".") if part]
    if not parts:
        return False, None
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]
    return True, current


def _nested_write(root: dict[str, Any], dotted_path: str, value: Any, present: bool) -> None:
    parts = [part for part in str(dotted_path).split(".") if part]
    if not parts:
        raise ValueError("property_path is required")
    current = root
    for part in parts[:-1]:
        child = current.get(part)
        if not isinstance(child, dict):
            if not present:
                raise KeyError(dotted_path)
            child = {}
            current[part] = child
        current = child
    leaf = parts[-1]
    if present:
        current[leaf] = value
    else:
        current.pop(leaf, None)


def _script_target(
    obj: Any, property_path: str
) -> tuple[Any, str, str, dict[str, Any] | None, dict[str, Any]] | None:
    """Resolve a script without mutating the holder during reads.

    The returned script mapping is kept separately from ``properties`` so a
    write can create the properties object only after the command's guards
    have passed.  This is important for stale and invalid commands: merely
    inspecting a target must not change it.
    """

    holder = spe.scripts_holder(obj)
    names = spe.script_names_from_holder(holder)
    parsed = spe.parse_script_inspector_key(property_path, names)
    if not parsed:
        return None
    script_name, dotted_path = parsed
    scripts = getattr(holder, "scripts", None)
    if scripts is None and isinstance(holder, dict):
        scripts = holder.get("scripts")
    if not isinstance(scripts, list):
        return None
    for script in scripts:
        if not isinstance(script, dict) or script.get("name") != script_name:
            continue
        props = script.get("properties")
        return holder, script_name, dotted_path, props if isinstance(props, dict) else None, script
    return None


def read_property(target: Any, property_path: str) -> tuple[bool, Any]:
    """Read one Inspector property and return ``(present, value)``."""

    prop = str(property_path or "").strip()
    if prop in {"position_x", "position_y"}:
        axis = 0 if prop == "position_x" else 1
        if hasattr(target, "position"):
            position = getattr(target, "position")
        elif isinstance(target, dict) and "position" in target:
            position = target["position"]
        elif hasattr(target, "x") and hasattr(target, "y"):
            axis_name = "x" if axis == 0 else "y"
            return True, getattr(target, axis_name)
        else:
            return False, None
        if not isinstance(position, (list, tuple)) or len(position) <= axis:
            return False, None
        return True, position[axis]

    script = _script_target(target, prop) if prop.startswith("script_") else None
    if script is not None:
        _holder, _script_name, dotted_path, props, _script = script
        if props is None:
            return False, None
        return _nested_state(props, dotted_path)
    if prop.startswith("script_"):
        return False, None

    if isinstance(target, dict):
        return (prop in target, target.get(prop))
    if hasattr(target, prop):
        return True, getattr(target, prop)
    return False, None


def write_property(target: Any, property_path: str, value: Any, present: bool = True) -> None:
    """Write or remove one Inspector property after the caller's guard passes."""

    prop = str(property_path or "").strip()
    if prop in {"position_x", "position_y"}:
        axis = 0 if prop == "position_x" else 1
        if hasattr(target, "position"):
            position = getattr(target, "position")
            if not isinstance(position, (list, tuple)):
                raise TypeError("position must be a list or tuple")
            updated = list(position)
            if len(updated) <= axis:
                raise IndexError("position axis is unavailable")
            if present:
                updated[axis] = value
            else:
                raise ValueError("position axis cannot be removed")
            normalized_position = tuple(updated) if isinstance(position, tuple) else updated
            setter = getattr(target, "set_position", None)
            if callable(setter):
                setter(normalized_position)
            else:
                setattr(target, "position", normalized_position)
            return
        if isinstance(target, dict) and isinstance(target.get("position"), (list, tuple)):
            updated = list(target["position"])
            if len(updated) <= axis:
                raise IndexError("position axis is unavailable")
            if not present:
                raise ValueError("position axis cannot be removed")
            updated[axis] = value
            target["position"] = updated
            return
        if hasattr(target, "x") and hasattr(target, "y"):
            if not present:
                raise ValueError("position axis cannot be removed")
            setattr(target, "x" if axis == 0 else "y", value)
            return
        raise AttributeError("position is unavailable")

    script = _script_target(target, prop) if prop.startswith("script_") else None
    if script is not None:
        _holder, _script_name, dotted_path, props, script_mapping = script
        if props is None:
            if not present:
                raise KeyError(dotted_path)
            props = {}
            script_mapping["properties"] = props
        _nested_write(props, dotted_path, value, present)
        return
    if prop.startswith("script_"):
        raise AttributeError("script property is unavailable")

    if isinstance(target, dict):
        if present:
            target[prop] = value
        else:
            target.pop(prop, None)
        return

    owner_state_setters = {
        "position": "set_position",
        "velocity": "set_velocity",
        "acceleration": "set_acceleration",
        "energy": "set_energy",
        "health": "set_health",
        "radius": "set_radius",
        "size": "set_size",
        "generation": "set_generation",
        "dead": "set_dead",
    }
    setter_name = owner_state_setters.get(prop)
    setter = getattr(target, setter_name, None) if setter_name else None
    if callable(setter):
        if not present:
            raise ValueError(f"{prop} cannot be removed from an owner-managed target")
        setter(value)
        return

    if present:
        setattr(target, prop, value)
    else:
        if not hasattr(target, prop):
            return
        delattr(target, prop)


def property_value_equal(left: Any, right: Any) -> bool:
    """Compare JSON-like values without allowing object identity to be a guard."""

    return left == right

