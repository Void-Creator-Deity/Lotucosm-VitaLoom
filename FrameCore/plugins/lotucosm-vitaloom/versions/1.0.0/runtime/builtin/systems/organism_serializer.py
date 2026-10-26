"""PS 生物体专用序列化辅助（人口条目结构与 PondSerializer 协同）。

排错: 见 `builtin/README.md`。
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from builtin.entity_types.organism import Organism
from builtin.components.components_base import ComponentBase
from builtin.components.component_library import canonical_component_type
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
    
    @staticmethod
    def _serialize_component_connections(organism: Any) -> list[Dict[str, Any]]:
        edges: list[Dict[str, Any]] = []
        for component in organism.components.values():
            for order, connection in enumerate(getattr(component, "connections", ())):
                target = getattr(connection, "target", connection)
                target_id = getattr(target, "id", None)
                if isinstance(target_id, str) and target_id in organism.components:
                    edges.append({
                        "source_id": component.id,
                        "target_id": target_id,
                        "order": order,
                    })
        return edges

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
            "size": organism.size,
            "radius": organism.radius,
            "energy": organism.energy,
            "max_energy": organism.max_energy,
            "health": organism.health,
            "max_health": organism.max_health,
            "age": organism.age,
            "generation": getattr(organism, "generation", 1),
            "dead": getattr(organism, "dead", False),
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

        # 组件图持久化：只写稳定 id/顺序，不泄漏 live object 引用。
        organism_data["component_connections"] = self._serialize_component_connections(organism)
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
            "type": canonical_component_type(component),
            "name": getattr(component, "name", component.id),
            "location": getattr(component, "location", "internal"),
            "congenital": getattr(component, "congenital", True),
            "acquired": getattr(component, "acquired", False),
            "attach_point": getattr(component, "attach_point", None),
            "energy_consumption": getattr(component, "energy_consumption", 0.0)
        }
        if getattr(component, "sr_component_id", None) is not None:
            component_data["sr_component_id"] = component.sr_component_id
        
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
            
            # Hydration 是 runtime owner API 边界：兼容旧 payload 缺少的新字段，
            # 但新格式的 motion/size/state 必须经过完整校验后再写入。
            organism.restore_motion_state(
                position=position,
                velocity=organism_data.get("velocity", organism.velocity),
                acceleration=organism_data.get("acceleration", organism.acceleration),
            )
            if "size" in organism_data:
                organism.set_size(organism_data["size"])
            if "radius" in organism_data:
                organism.set_radius(organism_data["radius"])
            organism.set_age(organism_data["age"])
            if "generation" in organism_data:
                organism.set_generation(organism_data["generation"])
            if "dead" in organism_data:
                organism.set_dead(organism_data["dead"])
            et = organism_data.get("evolvable_traits")
            if isinstance(et, dict):
                organism.evolvable_traits = dict(et)
            if "enable_pvaec_cycle_per_tick" in organism_data:
                organism.enable_pvaec_cycle_per_tick = bool(
                    organism_data["enable_pvaec_cycle_per_tick"]
                )
            
            # 反序列化组件
            restored_components = []
            for component_data in organism_data["components"]:
                component = self._deserialize_component(component_data)
                if component:
                    restored_components.append(component)
            organism.replace_components(restored_components)
            
            # 反序列化细胞膜
            if "membrane" in organism_data and organism_data["membrane"]:
                membrane = self._deserialize_component(organism_data["membrane"])
                if membrane:
                    organism.set_membrane(membrane)
            
            # 组件图恢复必须在全部组件 owner hydration 完成后进行。
            organism.replace_component_connections(
                organism_data.get("component_connections", [])
            )

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
                    organism.memory_system.adopt_memory(memory, enforce_capacity=False)
            
            return organism
        except Exception as e:
            self._log_error("反序列化生物体", e)
            return None
    
    def _deserialize_component(self, component_data: Dict[str, Any]) -> Optional[ComponentBase]:
        """通过统一组件工厂恢复组件，未知类型兼容回退为 ComponentBase。"""
        try:
            self._require_fields(
                component_data,
                ["type", "id", "name", "location", "congenital", "acquired", "attach_point", "energy_consumption"],
                "component_data",
            )
            from builtin.components.component_factory import ComponentFactory

            component = ComponentFactory().create_component(
                str(component_data["type"]),
                str(component_data["id"]),
                organism_id="temp_organism",
                name=component_data["name"],
                **({"sr_component_id": component_data["sr_component_id"]}
                   if "sr_component_id" in component_data else {}),
            )
            component.restore_persistent_state(component_data)
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


