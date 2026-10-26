# -*- coding: utf-8 -*-
from __future__ import annotations

import math
import hashlib

import pytest
from types import SimpleNamespace

from core.Lotucosm.sr_physics2d import (
    CppSrPhysics2DAdapter,
    Physics2DMode,
    PythonSrPhysics2DAdapter,
    RustSrPhysics2DAdapter,
    SrPhysics2DConfig,
    is_cpp_sr2d_available,
    is_native_sr2d_available,
    is_rust_sr2d_available,
    make_default_adapter,
    describe_sr2d_adapter,
    build_sr2d_runtime_provenance,
)
from core.Lotucosm.sr_link_physics import SrSpringLink


def _org(x: float, y: float, *, r: float = 22.0) -> SimpleNamespace:
    return SimpleNamespace(
        entity_type="organism",
        position=[x, y],
        velocity=[0.0, 0.0],
        radius=r,
        pinned=False,
        membrane_locked=False,
    )


def _nut(x: float, y: float, *, r: float = 14.0) -> SimpleNamespace:
    return SimpleNamespace(
        entity_type="nutrient",
        position=[x, y],
        velocity=[0.0, 0.0],
        radius=r,
        pinned=True,
        membrane_locked=False,
    )


def test_python_adapter_matches_pvaec_overlap_resolution() -> None:
    org = _org(50.0, 50.0)
    nut = _nut(50.0, 50.0)
    adapter = PythonSrPhysics2DAdapter()

    adapter.step(
        [org, nut],
        dt=0.016,
        width=400.0,
        height=400.0,
        mode=Physics2DMode.PVAEC,
        springs=(),
        config=SrPhysics2DConfig(contact_iterations=4),
    )

    dist = math.hypot(org.position[0] - nut.position[0], org.position[1] - nut.position[1])
    assert dist >= org.radius + nut.radius - 1.0


def test_adapter_capability_is_stable_and_identifies_backend() -> None:
    capability = describe_sr2d_adapter(PythonSrPhysics2DAdapter())
    assert capability == {
        "schema_version": 1,
        "backend_id": "python",
        "adapter_class": "PythonSrPhysics2DAdapter",
        "module_name": None,
        "artifact_sha256": None,
        "artifact_provenance": "not_applicable",
        "kernel_symbol": None,
        "abi_contract": "python_reference_v1",
        "abi_version_required": None,
        "abi_version_exported": None,
        "input_contract": None,
        "runtime_provenance": build_sr2d_runtime_provenance(),
        "native_pvaec_enabled": False,
        "python_fallback_for_game_or_springs": True,
    }


def test_native_capability_hashes_loaded_artifact_and_does_not_invent_abi() -> None:
    artifact = __import__("pathlib").Path(__file__).resolve()
    module = SimpleNamespace(
        __name__="_vitalloom_sr2d_cpp",
        __file__=str(artifact),
        VITALLOOM_SR2D_ABI_VERSION=1,
        VITALLOOM_SR2D_ENTROPY_CONTRACT="none",
        step_pvaec_circles=lambda *args: {},
    )
    capability = describe_sr2d_adapter(CppSrPhysics2DAdapter(module=module))
    assert capability["artifact_sha256"] == hashlib.sha256(artifact.read_bytes()).hexdigest()
    assert capability["artifact_provenance"] == "hashed"
    assert capability["abi_contract"] == "sr2d_pvaec_circles_v1"
    assert capability["abi_version_exported"] == 1
    assert capability["input_contract"]["kernel"] == "step_pvaec_circles"
    assert capability["input_contract"]["result"]["positions"] == "sequence[tuple[float, float]]"
    assert capability["runtime_provenance"]["pointer_bits"] in (32, 64)
    assert capability["runtime_provenance"]["cross_platform_parity_proven"] is False


def test_binary_native_adapter_rejects_missing_or_wrong_abi() -> None:
    artifact = __import__("pathlib").Path(__file__).resolve()
    module = SimpleNamespace(
        __name__="_vitalloom_sr2d_cpp",
        __file__=str(artifact),
        step_pvaec_circles=lambda *args: {},
    )
    with pytest.raises(RuntimeError, match=r"C\+\+ SR2D adapter requested"):
        CppSrPhysics2DAdapter(module=module)


def test_binary_native_adapter_accepts_declared_abi() -> None:
    artifact = __import__("pathlib").Path(__file__).resolve()
    module = SimpleNamespace(
        __name__="_vitalloom_sr2d_cpp",
        __file__=str(artifact),
        VITALLOOM_SR2D_ABI_VERSION=1,
        VITALLOOM_SR2D_ENTROPY_CONTRACT="none",
        step_pvaec_circles=lambda *args: {},
    )
    adapter = CppSrPhysics2DAdapter(module=module)
    assert describe_sr2d_adapter(adapter)["abi_version_exported"] == 1


def test_binary_native_adapter_rejects_boolean_abi_version() -> None:
    artifact = __import__("pathlib").Path(__file__).resolve()
    module = SimpleNamespace(
        __name__="_vitalloom_sr2d_cpp",
        __file__=str(artifact),
        VITALLOOM_SR2D_ABI_VERSION=True,
        step_pvaec_circles=lambda *args: {},
    )
    with pytest.raises(RuntimeError, match=r"C\+\+ SR2D adapter requested"):
        CppSrPhysics2DAdapter(module=module)


class RecordingAdapter:
    def __init__(self) -> None:
        self.calls = []

    def step(self, entities, *, dt, width, height, mode, springs, config) -> None:
        self.calls.append(
            {
                "entities": entities,
                "dt": dt,
                "width": width,
                "height": height,
                "mode": mode,
                "springs": springs,
                "config": config,
            }
        )


def test_world_delegates_step_to_configured_adapter() -> None:
    from core.Lotucosm.sr_physics2d import SrPhysics2DWorld

    adapter = RecordingAdapter()
    cfg = SrPhysics2DConfig(linear_damping=0.9)
    entities = [_org(10.0, 10.0)]

    world = SrPhysics2DWorld(cfg, adapter=adapter)
    world.step(entities, 0.02, 320.0, 240.0, mode=Physics2DMode.PVAEC, springs=())

    assert len(adapter.calls) == 1
    assert adapter.calls[0]["entities"] is entities
    assert adapter.calls[0]["dt"] == 0.02
    assert adapter.calls[0]["mode"] == Physics2DMode.PVAEC
    assert adapter.calls[0]["config"] is cfg


def test_auto_adapter_falls_back_to_python_when_native_is_missing(monkeypatch) -> None:
    monkeypatch.setenv("VITALOOM_SR2D_ADAPTER", "auto")

    adapter = make_default_adapter()

    if is_cpp_sr2d_available():
        assert isinstance(adapter, CppSrPhysics2DAdapter)
    elif is_rust_sr2d_available():
        assert isinstance(adapter, RustSrPhysics2DAdapter)
    else:
        assert isinstance(adapter, PythonSrPhysics2DAdapter)


def test_python_adapter_can_be_forced_with_env(monkeypatch) -> None:
    monkeypatch.setenv("VITALOOM_SR2D_ADAPTER", "python")

    assert isinstance(make_default_adapter(), PythonSrPhysics2DAdapter)


def test_project_backend_request_is_explicit_and_does_not_use_process_env(monkeypatch) -> None:
    monkeypatch.setenv("VITALOOM_SR2D_ADAPTER", "cpp")
    assert isinstance(make_default_adapter("python"), PythonSrPhysics2DAdapter)


def test_unknown_project_backend_request_fails_closed() -> None:
    try:
        make_default_adapter("made-up")
    except ValueError as exc:
        assert "unsupported SR2D backend request" in str(exc)
    else:
        raise AssertionError("unknown project backend request must fail closed")


def test_rust_adapter_force_fails_loudly_when_native_is_missing(monkeypatch) -> None:
    monkeypatch.setenv("VITALOOM_SR2D_ADAPTER", "rust")

    if is_rust_sr2d_available():
        assert isinstance(make_default_adapter(), RustSrPhysics2DAdapter)
    else:
        try:
            make_default_adapter()
        except RuntimeError as exc:
            assert "native SR2D adapter requested" in str(exc)
        else:
            raise AssertionError("rust adapter request must fail when native module is unavailable")


def test_cpp_adapter_force_fails_loudly_when_native_is_missing(monkeypatch) -> None:
    monkeypatch.setenv("VITALOOM_SR2D_ADAPTER", "cpp")

    if is_cpp_sr2d_available():
        assert isinstance(make_default_adapter(), CppSrPhysics2DAdapter)
    else:
        try:
            make_default_adapter()
        except RuntimeError as exc:
            assert "C++ SR2D adapter requested" in str(exc)
        else:
            raise AssertionError("cpp adapter request must fail when native module is unavailable")


def test_native_availability_is_any_backend() -> None:
    assert is_native_sr2d_available() == (
        is_cpp_sr2d_available() or is_rust_sr2d_available()
    )


class ExplodingNativeModule:
    def step_pvaec_circles(self, *args, **kwargs):
        raise AssertionError("native kernel should not be called for fallback cases")


def test_native_adapter_uses_python_for_game_mode_fallback() -> None:
    actor = SimpleNamespace(
        id="actor",
        entity_type="game_actor",
        position=[50.0, 50.0],
        velocity=[10.0, 0.0],
        radius=12.0,
        pinned=False,
        membrane_locked=False,
    )
    adapter = CppSrPhysics2DAdapter(module=ExplodingNativeModule())

    adapter.step(
        [actor],
        dt=0.1,
        width=200.0,
        height=160.0,
        mode=Physics2DMode.GAME,
        springs=None,
        config=SrPhysics2DConfig(),
    )

    assert actor.position[0] > 50.0


def test_native_adapter_uses_python_for_pvaec_springs_fallback() -> None:
    a = _org(50.0, 50.0)
    a.id = "a"
    b = _org(90.0, 50.0)
    b.id = "b"
    spring = SrSpringLink(
        start_id="a",
        end_id="b",
        rest_length=10.0,
        stiffness=20.0,
        damping=0.0,
    )
    adapter = CppSrPhysics2DAdapter(module=ExplodingNativeModule())

    adapter.step(
        [a, b],
        dt=0.1,
        width=200.0,
        height=160.0,
        mode=Physics2DMode.PVAEC,
        springs=(spring,),
        config=SrPhysics2DConfig(),
    )

    assert abs(a.velocity[0]) > 0.0 or abs(b.velocity[0]) > 0.0


class NonCallableNativeModule:
    step_pvaec_circles = "not-callable"


class RecordingNativeModule:
    def __init__(self, result=None) -> None:
        self.calls = []
        self.result = result

    def step_pvaec_circles(self, *args):
        self.calls.append(args)
        if self.result is not None:
            return self.result
        positions, velocities = args[0], args[1]
        return {"positions": positions, "velocities": velocities}


def test_native_kernel_attribute_must_be_callable() -> None:
    with pytest.raises(RuntimeError, match="step_pvaec_circles"):
        CppSrPhysics2DAdapter(module=NonCallableNativeModule())


def test_native_adapter_preserves_python_zero_dt_noop() -> None:
    entity = _org(50.0, 60.0)
    entity.velocity[:] = [30.0, -10.0]
    before = (tuple(entity.position), tuple(entity.velocity))
    adapter = CppSrPhysics2DAdapter(module=ExplodingNativeModule())

    adapter.step(
        [entity],
        dt=0.0,
        width=200.0,
        height=160.0,
        mode=Physics2DMode.PVAEC,
        springs=(),
        config=SrPhysics2DConfig(),
    )

    assert (tuple(entity.position), tuple(entity.velocity)) == before


def test_native_adapter_forwards_actual_pvaec_broadphase() -> None:
    module = RecordingNativeModule()
    entity = _org(50.0, 60.0)
    adapter = CppSrPhysics2DAdapter(module=module)

    adapter.step(
        [entity],
        dt=0.016,
        width=200.0,
        height=160.0,
        mode=Physics2DMode.PVAEC,
        springs=(),
        config=SrPhysics2DConfig(pvaec_broadphase="spatial_hash"),
    )

    assert len(module.calls) == 1
    assert module.calls[0][-1]["pvaec_broadphase"] == "spatial_hash"


@pytest.mark.parametrize(
    ("configured", "expected"),
    [
        (" SPATIAL_HASH ", "spatial_hash"),
        ("", "spatial_hash"),
        (None, "spatial_hash"),
        (" BRUTEFORCE ", "bruteforce"),
    ],
)
def test_native_adapter_canonicalizes_pvaec_broadphase_like_python_oracle(
    configured, expected
) -> None:
    module = RecordingNativeModule()
    entity = _org(50.0, 60.0)
    adapter = CppSrPhysics2DAdapter(module=module)

    adapter.step(
        [entity],
        dt=0.016,
        width=200.0,
        height=160.0,
        mode=Physics2DMode.PVAEC,
        springs=(),
        config=SrPhysics2DConfig(pvaec_broadphase=configured),
    )

    assert module.calls[0][-1]["pvaec_broadphase"] == expected


@pytest.mark.parametrize(
    "result, message",
    [
        ({"velocities": [(0.0, 0.0)]}, "positions"),
        ({"positions": [(90.0, 80.0)], "velocities": []}, "velocities length"),
        ({"positions": [(90.0,)], "velocities": [(0.0, 0.0)]}, r"positions\[0\]"),
    ],
)
def test_native_adapter_rejects_malformed_result_before_entity_mutation(
    result, message
) -> None:
    entity = _org(50.0, 60.0)
    before = (tuple(entity.position), tuple(entity.velocity))
    adapter = CppSrPhysics2DAdapter(module=RecordingNativeModule(result))

    with pytest.raises(RuntimeError, match=message):
        adapter.step(
            [entity],
            dt=0.016,
            width=200.0,
            height=160.0,
            mode=Physics2DMode.PVAEC,
            springs=(),
            config=SrPhysics2DConfig(),
        )

    assert (tuple(entity.position), tuple(entity.velocity)) == before
