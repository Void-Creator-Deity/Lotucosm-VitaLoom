# -*- coding: utf-8 -*-
"""SR 2D adapter boundary.

The Python adapter is the behavioral reference. Native adapters must preserve
this public contract before they are allowed behind SrPhysics2DWorld.
"""

from __future__ import annotations

import importlib
import hashlib
import os
import platform
import struct
import sys
import sysconfig
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Iterable, Protocol, Sequence


SR2D_ABI_VERSION = 1
SR2D_INPUT_CONTRACT = {
    "kernel": "step_pvaec_circles",
    "arguments": [
        "positions: sequence[tuple[float, float]]",
        "velocities: sequence[tuple[float, float]]",
        "radii: sequence[float]",
        "entity_types: sequence[str]",
        "pinned: sequence[bool]",
        "membrane_locked: sequence[bool]",
        "dt: float",
        "width: float",
        "height: float",
        "config: mapping[str, float|int|str]",
    ],
    "result": {
        "positions": "sequence[tuple[float, float]]",
        "velocities": "sequence[tuple[float, float]]",
    },
    "cardinality": "all entity-aligned sequences equal len(positions)",
    "mutation": "returns new mapping; adapter mutates entities only after full validation",
}


def build_sr2d_runtime_provenance() -> dict[str, Any]:
    """Describe the host ABI/numeric surface without claiming portability."""
    implementation_version = getattr(sys.implementation, "version", None)
    return {
        "schema_version": 1,
        "python_implementation": str(getattr(sys.implementation, "name", "unknown")),
        "python_version": platform.python_version(),
        "python_abi": sysconfig.get_config_var("SOABI") or sysconfig.get_config_var("PYTHON_ABI") or None,
        "platform": sysconfig.get_platform(),
        "os": platform.system(),
        "machine": platform.machine(),
        "pointer_bits": struct.calcsize("P") * 8,
        "float_radix": sys.float_info.radix,
        "float_mant_dig": sys.float_info.mant_dig,
        "float_rounds": sys.float_info.rounds,
        "python_compiler": platform.python_compiler(),
        "implementation_release": str(implementation_version) if implementation_version else None,
        "cross_platform_parity_proven": False,
    }

from core.Lotucosm.sr_physics2d.config import SrPhysics2DConfig
from core.Lotucosm.sr_physics2d.integrator import integrate_all
from core.Lotucosm.sr_physics2d.mode import Physics2DMode
from core.Lotucosm.sr_physics2d.pvaec_contacts import (
    normalize_pvaec_broadphase,
    resolve_pvaec_contacts,
)


class SrPhysics2DAdapter(Protocol):
    def step(
        self,
        entities: Sequence[Any],
        *,
        dt: float,
        width: float,
        height: float,
        mode: Physics2DMode,
        springs: Iterable[Any] | None,
        config: SrPhysics2DConfig,
    ) -> None:
        """Advance entities in place for one SR 2D frame."""


class PythonSrPhysics2DAdapter:
    """Reference implementation used as fallback and parity oracle."""

    backend_id = "python"

    def step(
        self,
        entities: Sequence[Any],
        *,
        dt: float,
        width: float,
        height: float,
        mode: Physics2DMode,
        springs: Iterable[Any] | None,
        config: SrPhysics2DConfig,
    ) -> None:
        if dt <= 0.0 or not entities:
            return

        ent_list = list(entities)

        if mode == Physics2DMode.PVAEC and springs:
            from core.Lotucosm.sr_link_physics import step_spring_network

            step_spring_network(ent_list, springs, dt)

        integrate_all(ent_list, dt, width, height, config)

        if mode == Physics2DMode.PVAEC:
            resolve_pvaec_contacts(
                ent_list,
                width=width,
                height=height,
                config=config,
            )
        else:
            from core.Lotucosm.sr_physics2d.game_contacts import resolve_game_contacts

            resolve_game_contacts(ent_list, config=config)


def _load_module(*names: str) -> Any | None:
    for name in names:
        try:
            return importlib.import_module(name)
        except ImportError:
            continue
    return None


def _load_rust_module() -> Any | None:
    return _load_module("_vitalloom_sr2d_rust", "_vitalloom_sr2d")


def _load_cpp_module() -> Any | None:
    return _load_module("_vitalloom_sr2d_cpp")


def _has_kernel(module: Any | None) -> bool:
    if module is None or not callable(getattr(module, "step_pvaec_circles", None)):
        return False
    # Test doubles and caller-owned adapters have no binary path and remain
    # usable; an actual extension must explicitly advertise the ABI version.
    module_path = getattr(module, "__file__", None)
    if not isinstance(module_path, str):
        return True
    declared_abi = getattr(module, "VITALLOOM_SR2D_ABI_VERSION", None)
    entropy_contract = getattr(module, "VITALLOOM_SR2D_ENTROPY_CONTRACT", None)
    return (
        not isinstance(declared_abi, bool)
        and declared_abi == SR2D_ABI_VERSION
        and entropy_contract == "none"
    )


def _coerce_kernel_vectors(
    result: Any,
    *,
    entity_count: int,
) -> tuple[list[tuple[float, float]], list[tuple[float, float]]]:
    """Validate the complete native ABI result before mutating any entity."""
    if not isinstance(result, Mapping):
        raise RuntimeError("native SR2D kernel result must be a mapping")

    converted: dict[str, list[tuple[float, float]]] = {}
    for field in ("positions", "velocities"):
        if field not in result:
            raise RuntimeError(f"native SR2D kernel result missing {field}")
        values = result[field]
        try:
            actual_length = len(values)
        except (TypeError, AttributeError) as exc:
            raise RuntimeError(
                f"native SR2D kernel {field} must be a sized sequence"
            ) from exc
        if actual_length != entity_count:
            raise RuntimeError(
                f"native SR2D kernel {field} length {actual_length} "
                f"does not match entity count {entity_count}"
            )

        rows: list[tuple[float, float]] = []
        for index, row in enumerate(values):
            try:
                row_length = len(row)
            except (TypeError, AttributeError) as exc:
                raise RuntimeError(
                    f"native SR2D kernel {field}[{index}] must be a 2D pair"
                ) from exc
            if row_length != 2:
                raise RuntimeError(
                    f"native SR2D kernel {field}[{index}] must be a 2D pair"
                )
            try:
                rows.append((float(row[0]), float(row[1])))
            except (TypeError, ValueError, IndexError, KeyError) as exc:
                raise RuntimeError(
                    f"native SR2D kernel {field}[{index}] must contain numbers"
                ) from exc
        converted[field] = rows

    return converted["positions"], converted["velocities"]


def _load_native_module() -> Any | None:
    return _load_cpp_module() or _load_rust_module()


def is_cpp_sr2d_available() -> bool:
    return _has_kernel(_load_cpp_module())


def is_rust_sr2d_available() -> bool:
    return _has_kernel(_load_rust_module())


def is_native_sr2d_available() -> bool:
    return is_cpp_sr2d_available() or is_rust_sr2d_available()


class NativeSrPhysics2DAdapter:
    """Base class for native adapters backed by a Python extension module."""

    module_names: tuple[str, ...] = ()
    missing_message = "native SR2D adapter requested, but no native module is available"
    backend_id = "native"

    def __init__(self, module: Any | None = None) -> None:
        self._module = module if module is not None else _load_module(*self.module_names)
        if not _has_kernel(self._module):
            raise RuntimeError(self.missing_message)

    def step(
        self,
        entities: Sequence[Any],
        *,
        dt: float,
        width: float,
        height: float,
        mode: Physics2DMode,
        springs: Iterable[Any] | None,
        config: SrPhysics2DConfig,
    ) -> None:
        if dt <= 0.0 or not entities:
            return
        if mode != Physics2DMode.PVAEC or springs:
            PythonSrPhysics2DAdapter().step(
                entities,
                dt=dt,
                width=width,
                height=height,
                mode=mode,
                springs=springs,
                config=config,
            )
            return

        ent_list = list(entities)
        result = self._module.step_pvaec_circles(
            [(float(e.position[0]), float(e.position[1])) for e in ent_list],
            [(float(e.velocity[0]), float(e.velocity[1])) for e in ent_list],
            [float(getattr(e, "radius", 18.0)) for e in ent_list],
            [str(getattr(e, "entity_type", "")) for e in ent_list],
            [bool(getattr(e, "pinned", False)) for e in ent_list],
            [bool(getattr(e, "membrane_locked", False)) for e in ent_list],
            float(dt),
            float(width),
            float(height),
            {
                "linear_damping": config.linear_damping,
                "boundary_bounce": config.boundary_bounce,
                "restitution": config.restitution,
                "friction": config.friction,
                "contact_slop": config.contact_slop,
                "contact_correction": config.contact_correction,
                "contact_iterations": config.contact_iterations,
                "pvaec_broadphase": normalize_pvaec_broadphase(
                    config.pvaec_broadphase
                ),
                "max_speed": config.max_speed,
            },
        )
        positions, velocities = _coerce_kernel_vectors(
            result,
            entity_count=len(ent_list),
        )
        for entity, pos, vel in zip(ent_list, positions, velocities):
            entity.position[0] = float(pos[0])
            entity.position[1] = float(pos[1])
            entity.velocity[0] = float(vel[0])
            entity.velocity[1] = float(vel[1])


class CppSrPhysics2DAdapter(NativeSrPhysics2DAdapter):
    """Native SR 2D adapter backed by the optional C++/pybind11 extension."""

    module_names = ("_vitalloom_sr2d_cpp",)
    backend_id = "cpp"
    missing_message = (
        "C++ SR2D adapter requested, but _vitalloom_sr2d_cpp.step_pvaec_circles "
        "is not available"
    )


class RustSrPhysics2DAdapter(NativeSrPhysics2DAdapter):
    """Native SR 2D adapter backed by the optional Rust/PyO3 extension."""

    module_names = ("_vitalloom_sr2d_rust", "_vitalloom_sr2d")
    backend_id = "rust"
    missing_message = (
        "native SR2D adapter requested, but _vitalloom_sr2d_rust.step_pvaec_circles "
        "is not available"
    )


def _legacy_load_native_module() -> Any | None:
    try:
        return importlib.import_module("_vitalloom_sr2d")
    except ImportError:
        return None


def make_default_adapter(requested: str | None = None) -> SrPhysics2DAdapter:
    if requested is None:
        requested = os.environ.get("VITALOOM_SR2D_ADAPTER", "auto")
    requested = str(requested).strip().lower()
    if requested not in {"auto", "python", "cpp", "rust"}:
        raise ValueError("unsupported SR2D backend request: " + requested)
    if requested == "python":
        return PythonSrPhysics2DAdapter()
    if requested == "cpp":
        return CppSrPhysics2DAdapter()
    if requested == "rust":
        return RustSrPhysics2DAdapter()
    if requested == "auto" and is_cpp_sr2d_available():
        return CppSrPhysics2DAdapter()
    if requested == "auto" and is_rust_sr2d_available():
        return RustSrPhysics2DAdapter()
    return PythonSrPhysics2DAdapter()


def describe_sr2d_adapter(adapter: SrPhysics2DAdapter) -> dict[str, Any]:
    """Return stable backend/ABI evidence without exposing module addresses."""
    if isinstance(adapter, PythonSrPhysics2DAdapter):
        backend_id = "python"
        module = None
    elif isinstance(adapter, CppSrPhysics2DAdapter):
        backend_id = "cpp"
        module = getattr(adapter, "_module", None)
    elif isinstance(adapter, RustSrPhysics2DAdapter):
        backend_id = "rust"
        module = getattr(adapter, "_module", None)
    else:
        backend_id = str(getattr(adapter, "backend_id", "custom"))
        module = None
    module_name = getattr(module, "__name__", None)
    module_path = getattr(module, "__file__", None)
    artifact_sha256 = None
    artifact_status = "not_applicable" if backend_id == "python" else "unavailable"
    if isinstance(module_path, str):
        try:
            artifact_sha256 = hashlib.sha256(Path(module_path).read_bytes()).hexdigest()
            artifact_status = "hashed"
        except OSError:
            artifact_status = "unreadable"
    declared_abi = getattr(module, "VITALLOOM_SR2D_ABI_VERSION", None)
    if isinstance(declared_abi, bool) or not isinstance(declared_abi, int):
        declared_abi = None
    return {
        "schema_version": 1,
        "backend_id": backend_id,
        "adapter_class": type(adapter).__name__,
        "module_name": module_name if isinstance(module_name, str) else None,
        "artifact_sha256": artifact_sha256,
        "artifact_provenance": artifact_status,
        "kernel_symbol": "step_pvaec_circles" if backend_id in {"cpp", "rust"} else None,
        "abi_contract": "sr2d_pvaec_circles_v1" if backend_id in {"cpp", "rust"} else "python_reference_v1",
        "abi_version_required": SR2D_ABI_VERSION if backend_id in {"cpp", "rust"} else None,
        "abi_version_exported": declared_abi,
        "input_contract": dict(SR2D_INPUT_CONTRACT) if backend_id in {"cpp", "rust"} else None,
        "runtime_provenance": build_sr2d_runtime_provenance(),
        "native_pvaec_enabled": backend_id in {"cpp", "rust"},
        "python_fallback_for_game_or_springs": True,
    }
