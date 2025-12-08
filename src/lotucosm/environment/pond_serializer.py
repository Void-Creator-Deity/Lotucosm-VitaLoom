"""莲池序列化器实现"""

import json
import os
import pickle
from datetime import datetime
from typing import Dict, Any, Optional, List
from lotucosm.environment.lotus_pond import LotusPond
from vitalloom.organisms.organism import Organism
from vitalloom.components.components_base import ComponentBase


class PondSerializer:
    """莲池序列化器 - 负责莲池环境的序列化和反序列化
    
    负责：
    1. 莲池状态的保存
    2. 莲池状态的加载
    3. 生物体的序列化
    4. 组件的序列化
    """
    
    def __init__(self, save_format: str = "json"):
        """初始化莲池序列化器
        
        参数:
            save_format: str - 保存格式（json或pickle）
        """
        self.save_format = save_format
        self.version = "1.0"  # 序列化版本
    
    def serialize_pond(self, pond: LotusPond) -> Dict[str, Any]:
        """序列化莲池
        
        参数:
            pond: LotusPond - 莲池实例
        
        返回:
            Dict[str, Any] - 序列化后的莲池数据
        """
        # 基本信息
        pond_data: Dict[str, Any] = {
            "version": self.version,
            "name": pond.name,
            "size": pond.size,
            "timestamp": datetime.now().isoformat(),
            "iteration": pond.iteration,
            "max_population": pond.max_population,
            "initial_organisms": pond.initial_organisms,
            "environmental_factors": pond.environmental_factors,
            "statistics": pond.statistics
        }
        
        # 序列化生物体
        organisms_data: List[Dict[str, Any]] = []
        for organism in pond.organisms.values():
            organism_data = self.serialize_organism(organism)
            organisms_data.append(organism_data)
        pond_data["organisms"] = organisms_data
        
        # 序列化漂浮组件
        floating_components_data: List[Dict[str, Any]] = []
        if hasattr(pond, "floating_system") and pond.floating_system:
            for component_data in pond.floating_system.floating_components:
                component = component_data["component"]
                floating_component_data: Dict[str, Any] = {
                    "component": self.serialize_component(component),
                    "position": component_data["position"],
                    "velocity": component_data["velocity"],
                    "lifespan": component_data["lifespan"],
                    "decay_rate": component_data["decay_rate"]
                }
                floating_components_data.append(floating_component_data)
        pond_data["floating_components"] = floating_components_data
        
        # 序列化资源
        resources_data: List[Dict[str, Any]] = []
        if hasattr(pond, "resource_manager") and pond.resource_manager:
            # resources是一个字典，包含不同类型的资源列表
            for _, res_list in pond.resource_manager.resources.items():
                for resource in res_list:
                    resources_data.append({
                        "type": resource["type"],
                        "position": resource["position"],
                        "amount": resource["amount"],
                        "id": resource["id"]
                    })
        pond_data["resources"] = resources_data
        
        return pond_data
    
    def serialize_organism(self, organism: Organism) -> Dict[str, Any]:
        """序列化生物体
        
        参数:
            organism: Organism - 生物体实例
        
        返回:
            Dict[str, Any] - 序列化后的生物体数据
        """
        organism_data: Dict[str, Any] = {
            "id": organism.id,
            "type": type(organism).__name__,
            "position": organism.position.tolist() if hasattr(organism.position, "tolist") else organism.position,
            "velocity": organism.velocity.tolist() if hasattr(organism.velocity, "tolist") else organism.velocity,
            "acceleration": organism.acceleration.tolist() if hasattr(organism.acceleration, "tolist") else organism.acceleration,
            "energy": organism.energy,
            "max_energy": organism.max_energy,
            "health": organism.health,
            "max_health": organism.max_health,
            "age": organism.age,
            "dead": organism.dead,
            "mutation_rate": organism.mutation_rate,
            "inheritance_rate": organism.inheritance_rate,
            "energy_consumption_rate": organism.energy_consumption_rate
        }
        
        # 序列化组件
        components_data: List[Dict[str, Any]] = []
        for _, comp in organism.components.items():
            component_data = self.serialize_component(comp)
            components_data.append(component_data)
        organism_data["components"] = components_data
        
        # 序列化细胞膜
        if organism.membrane:
            organism_data["membrane"] = self.serialize_component(organism.membrane)
        
        # 序列化记忆系统
        if organism.memory_system:
            memories = organism.memory_system.get_memories()
            memories_data: List[Dict[str, Any]] = []
            for memory in memories:
                memories_data.append({
                    "situation": memory.situation,
                    "action_pattern": memory.action_pattern,
                    "success_rate": memory.success_rate,
                    "strength": memory.strength,
                    "age": memory.age
                })
            organism_data["memories"] = memories_data
        
        return organism_data
    
    def serialize_component(self, component: ComponentBase) -> Dict[str, Any]:
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
        # 传感器属性
        if hasattr(component, "is_sensor") and component.is_sensor:
            component_data["is_sensor"] = True
            if hasattr(component, "sensor_sensitivity"):
                component_data["sensor_sensitivity"] = component.sensor_sensitivity
            if hasattr(component, "sense_range"):
                component_data["sense_range"] = component.sense_range
        
        # 执行器属性
        if hasattr(component, "is_actuator") and component.is_actuator:
            component_data["is_actuator"] = True
            if hasattr(component, "actuator_strength"):
                component_data["actuator_strength"] = component.actuator_strength
            if hasattr(component, "actuation_speed"):
                component_data["actuation_speed"] = component.actuation_speed
        
        # 复合器属性
        if hasattr(component, "is_hybrid") and component.is_hybrid:
            component_data["is_hybrid"] = True
            if hasattr(component, "mode"):
                component_data["mode"] = component.mode
        
        # 细胞膜属性
        if hasattr(component, "is_membrane") and component.is_membrane:
            component_data["is_membrane"] = True
            if hasattr(component, "permeability"):
                component_data["permeability"] = component.permeability
            if hasattr(component, "thickness"):
                component_data["thickness"] = component.thickness
            if hasattr(component, "surface_area"):
                component_data["surface_area"] = component.surface_area
        
        # PVAEC引擎属性
        if hasattr(component, "is_pvaec_engine") and component.is_pvaec_engine:
            component_data["is_pvaec_engine"] = True
            if hasattr(component, "learning_rate"):
                component_data["learning_rate"] = component.learning_rate
            if hasattr(component, "exploration_rate"):
                component_data["exploration_rate"] = component.exploration_rate
        
        return component_data
    
    def deserialize_pond(self, pond_data: Dict[str, Any], pond_class: type = LotusPond) -> LotusPond:
        """反序列化莲池
        
        参数:
            pond_data: Dict[str, Any] - 序列化后的莲池数据
            pond_class: type - 莲池类（默认为LotusPond）
        
        返回:
            LotusPond - 反序列化后的莲池实例
        """
        # 创建莲池实例
        pond = pond_class(
            name=pond_data["name"],
            size=pond_data["size"],
            max_population=pond_data["max_population"],
            initial_organisms=pond_data["initial_organisms"]
        )
        
        # 恢复基本属性
        pond.iteration = pond_data["iteration"]
        pond.environmental_factors = pond_data["environmental_factors"]
        pond.statistics = pond_data["statistics"]
        
        # 反序列化生物体
        organisms_dict: Dict[str, Organism] = {}
        organisms_list: List[Dict[str, Any]] = pond_data.get("organisms", [])
        for organism_data in organisms_list:
            organism = self.deserialize_organism(organism_data)
            organisms_dict[organism.id] = organism
        pond.organisms = organisms_dict
        
        # 反序列化漂浮组件
        if hasattr(pond, "floating_system") and pond.floating_system:
            floating_components_list: List[Dict[str, Any]] = []
            floating_components_data = pond_data.get("floating_components", [])
            for floating_component_data in floating_components_data:
                component = self.deserialize_component(floating_component_data["component"])
                floating_components_list.append({
                    "component": component,
                    "position": floating_component_data["position"],
                    "velocity": floating_component_data["velocity"],
                    "lifespan": floating_component_data["lifespan"],
                    "decay_rate": floating_component_data["decay_rate"]
                })
            pond.floating_system.floating_components = floating_components_list
        
        # 反序列化资源
        if hasattr(pond, "resource_manager") and pond.resource_manager:
            resources: Dict[str, List[Dict[str, Any]]] = {}
            resources_data = pond_data.get("resources", [])
            for resource_data in resources_data:
                resource_type = resource_data["type"]
                if resource_type not in resources:
                    resources[resource_type] = []
                resources[resource_type].append({
                    "type": resource_data["type"],
                    "position": resource_data["position"],
                    "amount": resource_data["amount"],
                    "id": resource_data["id"]
                })
            pond.resource_manager.resources = resources
        
        return pond
    
    def deserialize_organism(self, organism_data: Dict[str, Any]) -> Organism:
        """反序列化生物体
        
        参数:
            organism_data: Dict[str, Any] - 序列化后的生物体数据
        
        返回:
            Organism - 反序列化后的生物体实例
        """
        # 导入需要的类
        from vitalloom.organisms.simple_organism import SimpleOrganism
        from vitalloom.organisms.intelligent_organism import IntelligentOrganism
        from vitalloom.core.memory import MemorySystem
        
        # 创建生物体实例
        organism_type = organism_data["type"]
        position = organism_data["position"]
        
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
        organism.dead = organism_data["dead"]
        organism.velocity = organism_data["velocity"]
        organism.acceleration = organism_data["acceleration"]
        
        # 反序列化组件
        organism.components = {}
        for component_data in organism_data["components"]:
            component = self.deserialize_component(component_data)
            # 更新组件的organism_id为实际的生物体ID
            component.organism_id = organism.id
            organism.components[component.id] = component
        
        # 反序列化细胞膜
        if "membrane" in organism_data and organism_data["membrane"]:
            membrane = self.deserialize_component(organism_data["membrane"])
            # 更新细胞膜的organism_id为实际的生物体ID
            membrane.organism_id = organism.id
            organism.membrane = membrane
        
        # 反序列化记忆系统
        if "memories" in organism_data and organism_data["memories"]:
            organism.memory_system = MemorySystem()
            for memory_data in organism_data["memories"]:
                from vitalloom.core.memory import MemoryGene
                memory = MemoryGene(
                    situation=memory_data["situation"],
                    action_pattern=memory_data["action_pattern"],
                    success_rate=memory_data["success_rate"]
                )
                memory.strength = memory_data["strength"]
                memory.age = memory_data["age"]
                organism.memory_system.memories.append(memory)
        
        return organism
    
    def deserialize_component(self, component_data: Dict[str, Any]) -> ComponentBase:
        """反序列化组件
        
        参数:
            component_data: Dict[str, Any] - 序列化后的组件数据
        
        返回:
            ComponentBase - 反序列化后的组件实例
        """
        # 导入需要的类
        from vitalloom.components.sensors import Sensor
        from vitalloom.components.actuators import Actuator
        from vitalloom.components.hybrid import HybridComponent
        from vitalloom.components.membrane import Membrane
        from vitalloom.components.PVAECEngine import PVAECEngine
        
        # 根据类型创建组件
        component_type = component_data["type"]
        
        # 对于组件反序列化，我们需要从上下文获取organism_id
        # 由于组件是生物体的一部分，我们需要从生物体数据中获取organism_id
        # 这里暂时使用临时organism_id，后续会在organism反序列化时更新
        temp_organism_id = "temp_organism"
        
        if component_type == "Sensor":
            component = Sensor(
                component_id=component_data["id"],
                organism_id=temp_organism_id,
                name=component_data["name"]
            )
        elif component_type == "Actuator":
            component = Actuator(
                component_id=component_data["id"],
                organism_id=temp_organism_id,
                name=component_data["name"]
            )
        elif component_type == "HybridComponent":
            component = HybridComponent(
                component_id=component_data["id"],
                organism_id=temp_organism_id,
                name=component_data["name"]
            )
        elif component_type == "Membrane":
            component = Membrane(
                component_id=component_data["id"],
                organism_id=temp_organism_id,
                name=component_data["name"]
            )
        elif component_type == "PVAECEngine":
            component = PVAECEngine(
                component_id=component_data["id"],
                organism_id=temp_organism_id,
                name=component_data["name"]
            )
        else:
            # 默认创建基础组件
            from vitalloom.components.components_base import ComponentBase
            component = ComponentBase(
                component_id=component_data["id"],
                organism_id=temp_organism_id,
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
            if "surface_area" in component_data:
                component.surface_area = component_data["surface_area"]
        
        if component_data.get("is_pvaec_engine", False):
            component.is_pvaec_engine = True
            if "learning_rate" in component_data:
                component.learning_rate = component_data["learning_rate"]
            if "exploration_rate" in component_data:
                component.exploration_rate = component_data["exploration_rate"]
        
        return component
    
    def save_pond(self, pond: LotusPond, file_path: str) -> bool:
        """保存莲池到文件
        
        参数:
            pond: LotusPond - 莲池实例
            file_path: str - 文件路径
        
        返回:
            bool - 是否保存成功
        """
        try:
            # 序列化莲池
            pond_data = self.serialize_pond(pond)
            
            # 创建目录（如果不存在）
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 保存文件
            if self.save_format == "json":
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(pond_data, f, indent=2, ensure_ascii=False)
            elif self.save_format == "pickle":
                with open(file_path, "wb") as f:
                    pickle.dump(pond_data, f)
            else:
                raise ValueError(f"不支持的保存格式: {self.save_format}")
            
            return True
        except Exception as e:
            print(f"保存莲池失败: {e}")
            return False
    
    def load_pond(self, file_path: str, pond_class: type = LotusPond) -> Optional[LotusPond]:
        """从文件加载莲池
        
        参数:
            file_path: str - 文件路径
            pond_class: type - 莲池类（默认为LotusPond）
        
        返回:
            Optional[LotusPond] - 加载的莲池实例，如果加载失败返回None
        """
        try:
            # 读取文件
            if self.save_format == "json":
                with open(file_path, "r", encoding="utf-8") as f:
                    pond_data = json.load(f)
            elif self.save_format == "pickle":
                with open(file_path, "rb") as f:
                    pond_data = pickle.load(f)
            else:
                raise ValueError(f"不支持的保存格式: {self.save_format}")
            
            # 反序列化莲池
            pond = self.deserialize_pond(pond_data, pond_class)
            return pond
        except Exception as e:
            print(f"加载莲池失败: {e}")
            return None