import pytest

from builtin.components.components_base import ComponentBase
from builtin.systems.floating_system import FloatingSystem
from core.Lotucosm.pond import Pond


def _state(**overrides):
    state = {
        "location": "external",
        "congenital": False,
        "acquired": True,
        "attach_point": "north",
        "energy_consumption": 1.25,
        "is_sensor": True,
        "sensor_sensitivity": 0.7,
    }
    state.update(overrides)
    return state


def test_component_persistent_restore_is_atomic_and_updates_specialized_fields():
    component = ComponentBase("c1", location="internal", energy_consumption=0.25)
    component.restore_persistent_state(_state())

    assert component.location == "external"
    assert component.energy_consumption == 1.25
    assert component.sensor_sensitivity == 0.7

    with pytest.raises(ValueError):
        component.restore_persistent_state(_state(energy_consumption=-1.0))
    assert component.location == "external"
    assert component.energy_consumption == 1.25


def test_floating_owner_replacements_preserve_public_list_identity():
    system = FloatingSystem()
    original = system.floating_components
    entry = {"component": ComponentBase("c1")}
    system.replace_floating_components([entry])
    assert system.floating_components is original
    assert system.floating_components == [entry]

    pond = Pond(initial_components=0, initial_organisms=0)
    original_pond = pond.floating_components
    component = ComponentBase("c2")
    pond.replace_floating_components([component])
    assert pond.floating_components is original_pond
    assert pond.floating_components == [component]
