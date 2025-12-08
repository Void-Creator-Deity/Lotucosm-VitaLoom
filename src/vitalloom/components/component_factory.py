from typing import Dict, Any
from .components_base import ComponentBase
from .sensors import Sensor
from .actuators import Actuator
from .PVAECEngine import PVAECEngine
from .hybrid import HybridComponent
from .membrane import Membrane

class ComponentFactory:
    def __init__(self):
        self.component_types: Dict[str, type[ComponentBase]] = {
            'sensor': Sensor,
            'actuator': Actuator,
            'pvaecengine': PVAECEngine,
            'hybrid': HybridComponent,
            'membrane': Membrane
        }

    def create_component(self, component_type: str, component_id: str, organism_id: str, **kwargs: Any) -> ComponentBase:
        component_type_lower = component_type.lower()
        if component_type_lower not in self.component_types:
            raise ValueError(f"未知组件类型: {component_type}")
        component_class = self.component_types[component_type_lower]
        return component_class(component_id, organism_id, **kwargs)

    def register_component_type(self, component_type: str, component_class: type[ComponentBase]):
        self.component_types[component_type.lower()] = component_class

    def get_available_component_types(self):
        return list(self.component_types.keys())

    def create_component_from_template(self, template: Dict[str, Any], component_id: str, organism_id: str) -> ComponentBase:
        component_type = template.get('type', '').lower()
        if not component_type:
            raise ValueError("组件模板缺少type字段")
        params = template.copy()
        params.pop('type', None)
        return self.create_component(component_type, component_id, organism_id, **params)
