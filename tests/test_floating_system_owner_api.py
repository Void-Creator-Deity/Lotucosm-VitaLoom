import numpy as np

from builtin.components.components_base import ComponentBase
from builtin.systems.floating_system import FloatingSystem


def test_floating_component_motion_and_boundary_use_owner_apis(monkeypatch):
    component = ComponentBase("c_motion", position=(9.0, 5.0), velocity=(5.0, 0.0))
    class ZeroOwner:
        def random(self, *args, **kwargs):
            return 0.0

        def normal(self, *args, size=None, **kwargs):
            return np.zeros(size, dtype=float)

        def uniform(self, low, high, *args, **kwargs):
            return (low + high) / 2.0

    system = FloatingSystem(
        gravity=np.array([0.0, 0.0]),
        drag=1.0,
        world_size=(10.0, 10.0),
        randomness_rng=ZeroOwner(),
    )
    calls: list[str] = []

    for name in ("set_position", "set_velocity"):
        original = getattr(component, name)

        def tracked(value, *, _original=original, _name=name):
            calls.append(_name)
            _original(value)

        setattr(component, name, tracked)
    system.apply_floating_physics(component)

    assert calls == ["set_position", "set_velocity", "set_position", "set_velocity"]
    assert component.position.tolist() == [10.0, 5.0]
    assert np.allclose(component.velocity, [-1.0, 0.0])


def test_floating_component_rejects_malformed_motion_without_partial_update():
    component = ComponentBase("c_bad", position=(1.0, 2.0), velocity=(3.0, 4.0))
    system = FloatingSystem()
    component.velocity = np.array([np.nan, 4.0])
    before_position = component.position.copy()

    system.apply_floating_physics(component)

    assert np.array_equal(component.position, before_position)
