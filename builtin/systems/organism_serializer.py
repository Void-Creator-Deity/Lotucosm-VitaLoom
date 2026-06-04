"""PS 生物体专用序列化辅助（人口条目结构与 PondSerializer 协同）。

排错: 见 `builtin/README.md`。
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from builtin.entity_types.organism import Organism
from builtin.components.components_base import ComponentBase
from core.VitaLoom.core.logger import get_logger

logger = get_logger("OrganismSerializer")


class OrganismSerializer:
    """生物体序列化器 - 负责生物体的序列化和反序列化
    
    负责：
    1. 生物体完整序列化
    2. 生物体反序列化
    3. 生物体模板管理
    """
    
    def __init__(self, save_format: str = "json"):
        """构造并初始化实例。

        职责:
            建立本对象运行所需字段与子系统引用。

        时机:
            宿主创建对象时单次调用。

        不变量:
            子类须完整 super().__init__ 链。

        排错:
            属性缺失 → 查 super 与模块顶 docstring。
        """
        self.save_format = save_format
        self.version = "1.0"  # 序列化版本

    def _log_error(self, action: str, error: Exception):
        logger.warning("[System:OrganismSerializer] %s失败: %s", action, error)

    def _require_fields(self, data: Dict[str, Any], fields: list[str], context: str):
        missing = [field for field in fields if field not in data]
        if missing:
            raise ValueError(f"{context}缺少字段: {', '.join(missing)}")
    
    def serialize_organism(self, organism: Organism) -> Dict[str, Any]:
        """序列化生物体。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 基本信息
        organism_data: Dict[str, Any] = {
            "version": self.version,
            "type": type(organism).__name__,
            "id": organism.id,
            "name": organism.id,  # 使用id作为名称
            "timestamp": datetime.now().isoformat(),
            "position": organism.position.tolist() if hasattr(organism.position, "tolist") else organism.position,
            "velocity": organism.velocity.tolist() if hasattr(organism.velocity, "tolist") else organism.velocity,
            "acceleration": organism.acceleration.tolist() if hasattr(organism.acceleration, "tolist") else organism.acceleration,
            "energy": organism.energy,
            "max_energy": organism.max_energy,
            "health": organism.health,
            "max_health": organism.max_health,
            "age": organism.age,
            "mutation_rate": organism.mutation_rate,
            "inheritance_rate": organism.inheritance_rate,
            "energy_consumption_rate": organism.energy_consumption_rate,
            "evolvable_traits": dict(getattr(organism, "evolvable_traits", {}) or {}),
            "enable_pvaec_cycle_per_tick": bool(
                getattr(organism, "enable_pvaec_cycle_per_tick", False)
            ),
        }
        
        # 序列化组件
        organism_data["components"] = []
        components_list: list[Dict[str, Any]] = organism_data["components"]
        for _, comp in organism.components.items():
            component_data = self._serialize_component(comp)
            components_list.append(component_data)
        
        # 序列化细胞膜
        if organism.membrane:
            organism_data["membrane"] = self._serialize_component(organism.membrane)
        
        # 序列化记忆系统
        if getattr(organism, "memory_system", None):
            memories = organism.memory_system.get_memories()
            organism_data["memories"] = [
                {
                    "situation": memory.situation,
                    "action_pattern": memory.action_pattern,
                    "success_rate": memory.success_rate,
                    "strength": memory.strength,
                    "age": memory.age
                }
                for memory in memories
            ]
        
        return organism_data
    
    def _serialize_component(self, component: ComponentBase) -> Dict[str, Any]:
        """序列化组件
        
        参数:
            component: ComponentBase - 组件实例
        
        返回:
            Dict[str, Any] - 序列化后的组件数据
        """
        component_data: Dict[str, Any] = {
            "id": component.id,
            "type": type(component).__name__,
            "name": component.name,
            "location": component.location,
            "congenital": component.congenital,
            "acquired": component.acquired,
            "attach_point": component.attach_point,
            "energy_consumption": component.energy_consumption
        }
        
        # 添加组件特定属性
        if hasattr(component, "is_sensor") and component.is_sensor:
            component_data["is_sensor"] = True
            if hasattr(component, "sensor_sensitivity"):
                component_data["sensor_sensitivity"] = component.sensor_sensitivity
            if hasattr(component, "sense_range"):
                component_data["sense_range"] = component.sense_range
        
        if hasattr(component, "is_actuator") and component.is_actuator:
            component_data["is_actuator"] = True
            if hasattr(component, "actuator_strength"):
                component_data["actuator_strength"] = component.actuator_strength
            if hasattr(component, "actuation_speed"):
                component_data["actuation_speed"] = component.actuation_speed
        
        if hasattr(component, "is_hybrid") and component.is_hybrid:
            component_data["is_hybrid"] = True
            if hasattr(component, "mode"):
                component_data["mode"] = component.mode
        
        if hasattr(component, "is_membrane") and component.is_membrane:
            component_data["is_membrane"] = True
            if hasattr(component, "permeability"):
                component_data["permeability"] = component.permeability
            if hasattr(component, "thickness"):
                component_data["thickness"] = component.thickness
        
        if hasattr(component, "is_pvaec_engine") and component.is_pvaec_engine:
            component_data["is_pvaec_engine"] = True
            if hasattr(component, "learning_rate"):
                component_data["learning_rate"] = component.learning_rate
            if hasattr(component, "exploration_rate"):
                component_data["exploration_rate"] = component.exploration_rate
            if hasattr(component, "success_threshold"):
                component_data["success_threshold"] = component.success_threshold
            if hasattr(component, "associations") and isinstance(getattr(component, "associations"), dict):
                component_data["associations"] = {
                    str(k): {str(ak): float(av) for ak, av in (v or {}).items()}
                    for k, v in component.associations.items()
                }
        
        return component_data
    
    def deserialize_organism(self, organism_data: Dict[str, Any]) -> Optional[Organism]:
        """反序列化生物体。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        try:
            self._require_fields(
                organism_data,
                [
                    "type",
                    "id",
                    "position",
                    "energy",
                    "max_energy",
                    "health",
                    "max_health",
                    "mutation_rate",
                    "inheritance_rate",
                    "energy_consumption_rate",
                    "age",
                    "components",
                ],
                "organism_data",
            )
            # 导入需要的类
            from builtin.entity_types.simple_organism import SimpleOrganism
            from builtin.entity_types.intelligent_organism import IntelligentOrganism
            from core.Lotucosm.memory import MemorySystem, MemoryGene
            
            # 创建生物体实例
            organism_type = organism_data["type"]
            position = organism_data["position"]
            
            # 根据类型创建不同的生物体实例
            if organism_type == "IntelligentOrganism":
                organism = IntelligentOrganism(
                    organism_id=organism_data["id"],
                    position=position,
                    energy=organism_data["energy"],
                    max_energy=organism_data["max_energy"],
                    health=organism_data["health"],
                    max_health=organism_data["max_health"],
                    mutation_rate=organism_data["mutation_rate"],
                    inheritance_rate=organism_data["inheritance_rate"],
                    energy_consumption_rate=organism_data["energy_consumption_rate"]
                )
            else:
                organism = SimpleOrganism(
                    organism_id=organism_data["id"],
                    position=position,
                    energy=organism_data["energy"],
                    max_energy=organism_data["max_energy"],
                    health=organism_data["health"],
                    max_health=organism_data["max_health"],
                    mutation_rate=organism_data["mutation_rate"],
                    inheritance_rate=organism_data["inheritance_rate"],
                    energy_consumption_rate=organism_data["energy_consumption_rate"]
                )
            
            # 恢复基本属性
            organism.age = organism_data["age"]
            et = organism_data.get("evolvable_traits")
            if isinstance(et, dict):
                organism.evolvable_traits = dict(et)
            if "enable_pvaec_cycle_per_tick" in organism_data:
                organism.enable_pvaec_cycle_per_tick = bool(
                    organism_data["enable_pvaec_cycle_per_tick"]
                )
            
            # 反序列化组件
            organism.components = {}
            for component_data in organism_data["components"]:
                component = self._deserialize_component(component_data)
                if component:
                    organism.components[component.id] = component
            
            # 反序列化细胞膜
            if "membrane" in organism_data and organism_data["membrane"]:
                membrane = self._deserialize_component(organism_data["membrane"])
                if membrane:
                    organism.membrane = membrane
            
            # 反序列化记忆系统
            if "memories" in organism_data and organism_data["memories"]:
                organism.memory_system = MemorySystem()
                for memory_data in organism_data["memories"]:
                    memory = MemoryGene(
                        situation=memory_data["situation"],
                        action_pattern=memory_data["action_pattern"],
                        success_rate=memory_data["success_rate"]
                    )
                    memory.strength = memory_data["strength"]
                    memory.age = memory_data["age"]
                    organism.memory_system.memories.append(memory)
            
            return organism
        except Exception as e:
            self._log_error("反序列化生物体", e)
            return None
    
    def _deserialize_component(self, component_data: Dict[str, Any]) -> Optional[ComponentBase]:
        """反序列化组件
        
        参数:
            component_data: Dict[str, Any] - 序列化后的组件数据
        
        返回:
            Optional[ComponentBase] - 反序列化后的组件实例，如果失败返回None
        """
        try:
            self._require_fields(
                component_data,
                ["type", "id", "name", "location", "congenital", "acquired", "attach_point", "energy_consumption"],
                "component_data",
            )
            # 导入需要的类
            from builtin.components.components_base import ComponentBase
            from builtin.components.sensors import Sensor
            from builtin.components.actuators import Actuator
            from builtin.components.hybrid import HybridComponent
            from builtin.components.membrane import Membrane
            
            # 根据类型创建组件实例
            component_type = component_data["type"]
            
            if component_type == "Sensor":
                component = Sensor(
                    component_id=component_data["id"],
                    organism_id="",
                    name=component_data["name"]
                )
            elif component_type == "Actuator":
                component = Actuator(
                    component_id=component_data["id"],
                    organism_id="",
                    name=component_data["name"]
                )
            elif component_type == "HybridComponent":
                component = HybridComponent(
                    component_id=component_data["id"],
                    organism_id="",
                    name=component_data["name"]
                )
            elif component_type == "Membrane":
                component = Membrane(
                    component_id=component_data["id"],
                    organism_id="",
                    name=component_data["name"]
                )
            elif component_type == "PVAECEngine":
                from builtin.components.PVAECEngine import PVAECEngine
                component = PVAECEngine(
                    component_id=component_data["id"],
                    organism_id="",
                    name=component_data["name"]
                )
            else:
                # 默认创建基础组件
                component = ComponentBase(
                    component_id=component_data["id"],
                    organism_id="",
                    name=component_data["name"]
                )
            
            # 恢复基本属性
            component.location = component_data["location"]
            component.congenital = component_data["congenital"]
            component.acquired = component_data["acquired"]
            component.attach_point = component_data["attach_point"]
            component.energy_consumption = component_data["energy_consumption"]
            
            # 恢复特定属性
            if component_data.get("is_sensor", False):
                component.is_sensor = True
                if "sensor_sensitivity" in component_data:
                    component.sensor_sensitivity = component_data["sensor_sensitivity"]
                if "sense_range" in component_data:
                    component.sense_range = component_data["sense_range"]
            
            if component_data.get("is_actuator", False):
                component.is_actuator = True
                if "actuator_strength" in component_data:
                    component.actuator_strength = component_data["actuator_strength"]
                if "actuation_speed" in component_data:
                    component.actuation_speed = component_data["actuation_speed"]
            
            if component_data.get("is_hybrid", False):
                component.is_hybrid = True
                if "mode" in component_data:
                    component.mode = component_data["mode"]
            
            if component_data.get("is_membrane", False):
                component.is_membrane = True
                if "permeability" in component_data:
                    component.permeability = component_data["permeability"]
                if "thickness" in component_data:
                    component.thickness = component_data["thickness"]
            
            if component_data.get("is_pvaec_engine", False):
                component.is_pvaec_engine = True
                if "learning_rate" in component_data:
                    component.learning_rate = component_data["learning_rate"]
                if "exploration_rate" in component_data:
                    component.exploration_rate = component_data["exploration_rate"]
                if "success_threshold" in component_data:
                    component.success_threshold = float(component_data["success_threshold"])
                if "associations" in component_data and isinstance(component_data.get("associations"), dict):
                    component.associations = {
                        str(k): {str(ak): float(av) for ak, av in (v or {}).items()}
                        for k, v in component_data["associations"].items()
                    }
            
            return component
        except Exception as e:
            self._log_error("反序列化组件", e)
            return None
    
    def save_organism(self, organism: Organism, file_path: str) -> bool:
        """保存生物体到文件。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        try:
            # 确保保存目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 序列化生物体
            organism_data = self.serialize_organism(organism)
            
            # 保存到文件
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(organism_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            self._log_error("保存生物体", e)
            return False
    
    def load_organism(self, file_path: str) -> Optional[Organism]:
        """从文件加载生物体。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        try:
            # 读取文件
            with open(file_path, "r", encoding="utf-8") as f:
                organism_data = json.load(f)
            
            # 反序列化生物体
            organism = self.deserialize_organism(organism_data)
            
            return organism
        except Exception as e:
            self._log_error("加载生物体", e)
            return None
    
    def save_organism_template(self, organism: Organism, save_path: str, template_name: str) -> Optional[str]:
        """保存生物体为模板。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        try:
            # 确保保存目录存在
            os.makedirs(save_path, exist_ok=True)
            
            # 生成文件名
            file_name = f"{template_name}.json"
            file_path = os.path.join(save_path, file_name)
            
            # 保存生物体
            success = self.save_organism(organism, file_path)
            
            if success:
                return file_path
            else:
                return None
        except Exception as e:
            self._log_error("保存生物体模板", e)
            return None
    
    def load_organism_template(self, template_path: str) -> Optional[Organism]:
        """加载生物体模板。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        return self.load_organism(template_path)