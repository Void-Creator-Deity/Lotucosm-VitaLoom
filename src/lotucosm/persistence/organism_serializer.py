"""生物体序列化器实现"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from vitalloom.organisms.organism import Organism
from vitalloom.components.components_base import ComponentBase


class OrganismSerializer:
    """生物体序列化器 - 负责生物体的序列化和反序列化
    
    负责：
    1. 生物体完整序列化
    2. 生物体反序列化
    3. 生物体模板管理
    """
    
    def __init__(self, save_format: str = "json"):
        """初始化生物体序列化器
        
        参数:
            save_format: str - 保存格式（目前仅支持json）
        """
        self.save_format = save_format
        self.version = "1.0"  # 序列化版本
    
    def serialize_organism(self, organism: Organism) -> Dict[str, Any]:
        """序列化生物体
        
        参数:
            organism: Organism - 生物体实例
        
        返回:
            Dict[str, Any] - 序列化后的生物体数据
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
            "energy_consumption_rate": organism.energy_consumption_rate
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
        if organism.memory_system:
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
        
        return component_data
    
    def deserialize_organism(self, organism_data: Dict[str, Any]) -> Optional[Organism]:
        """反序列化生物体
        
        参数:
            organism_data: Dict[str, Any] - 序列化后的生物体数据
        
        返回:
            Optional[Organism] - 反序列化后的生物体实例，如果失败返回None
        """
        try:
            # 导入需要的类
            from vitalloom.organisms.simple_organism import SimpleOrganism
            from vitalloom.organisms.intelligent_organism import IntelligentOrganism
            from vitalloom.core.memory import MemorySystem, MemoryGene
            
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
            print(f"反序列化生物体失败: {e}")
            return None
    
    def _deserialize_component(self, component_data: Dict[str, Any]) -> Optional[ComponentBase]:
        """反序列化组件
        
        参数:
            component_data: Dict[str, Any] - 序列化后的组件数据
        
        返回:
            Optional[ComponentBase] - 反序列化后的组件实例，如果失败返回None
        """
        try:
            # 导入需要的类
            from vitalloom.components.components_base import ComponentBase
            from vitalloom.components.sensors import Sensor
            from vitalloom.components.actuators import Actuator
            from vitalloom.components.hybrid import HybridComponent
            from vitalloom.components.membrane import Membrane
            from vitalloom.components.PVAECEngine import PVAECEngine
            
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
            
            return component
        except Exception as e:
            print(f"反序列化组件失败: {e}")
            return None
    
    def save_organism(self, organism: Organism, file_path: str) -> bool:
        """保存生物体到文件
        
        参数:
            organism: Organism - 生物体实例
            file_path: str - 文件路径
        
        返回:
            bool - 是否保存成功
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
            print(f"保存生物体失败: {e}")
            return False
    
    def load_organism(self, file_path: str) -> Optional[Organism]:
        """从文件加载生物体
        
        参数:
            file_path: str - 文件路径
        
        返回:
            Optional[Organism] - 加载的生物体实例，如果失败返回None
        """
        try:
            # 读取文件
            with open(file_path, "r", encoding="utf-8") as f:
                organism_data = json.load(f)
            
            # 反序列化生物体
            organism = self.deserialize_organism(organism_data)
            
            return organism
        except Exception as e:
            print(f"加载生物体失败: {e}")
            return None
    
    def save_organism_template(self, organism: Organism, save_path: str, template_name: str) -> Optional[str]:
        """保存生物体为模板
        
        参数:
            organism: Organism - 生物体实例
            save_path: str - 保存路径
            template_name: str - 模板名称
        
        返回:
            Optional[str] - 保存的文件路径，如果失败返回None
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
            print(f"保存生物体模板失败: {e}")
            return None
    
    def load_organism_template(self, template_path: str) -> Optional[Organism]:
        """加载生物体模板
        
        参数:
            template_path: str - 模板文件路径
        
        返回:
            Optional[Organism] - 加载的生物体实例，如果失败返回None
        """
        return self.load_organism(template_path)