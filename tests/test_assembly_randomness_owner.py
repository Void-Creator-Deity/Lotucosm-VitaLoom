import random

from builtin.components.components_base import ComponentBase
from builtin.systems.assembly_system import AssemblySystem


def _typed_component(component_id: str, component_type: str, **flags):
    component = ComponentBase(component_id, position=(0.0, 0.0), component_type=component_type)
    for name, value in flags.items():
        setattr(component, name, value)
    return component


def test_assembly_owner_path_imports_and_does_not_advance_global_random():
    sensor = _typed_component("sensor", "sensor", is_sensor=True, is_actuator=False)
    actuator = _typed_component("actuator", "actuator", is_sensor=False, is_actuator=True)
    system = AssemblySystem(randomness_rng=random.Random(51))
    system.assembly_probability = 1.0
    rule = system.check_assembly_possible(sensor, actuator)
    before = random.getstate()

    result = system.assemble_components(sensor, actuator, rule)

    assert result is not None
    assert result["connection"].startswith("connection_")
    assert sensor.connections and actuator.connections
    assert random.getstate() == before


def test_assembly_update_accepts_pond_component_list():
    sensor = _typed_component("sensor", "sensor", is_sensor=True, is_actuator=False)
    actuator = _typed_component("actuator", "actuator", is_sensor=False, is_actuator=True)
    system = AssemblySystem(randomness_rng=random.Random(52))
    system.assembly_probability = 1.0
    system.assembly_rules["sensor-actuator"]["probability"] = 1.0

    events = system.update([sensor, actuator])

    assert len(events) == 1
