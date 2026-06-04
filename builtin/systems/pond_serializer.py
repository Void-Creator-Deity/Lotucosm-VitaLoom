"""PS 莲池 JSON/pickle 序列化：人口、组件、漂浮物与资源快照。

架构数据流::

    Pond → serialize_pond → 文件 → load_pond → deserialize_pond → Pond

不变量: `version` 字段当前为 1.0；organism 反序列化后须回填 `organism_id` 与 `org.pond`。

排错: 见 `builtin/README.md`（缺字段、temp organism_id、资源为空）。
"""

import json
import os
import pickle
from datetime import datetime
from typing import Dict, Any, Optional, List, TYPE_CHECKING

from core.Lotucosm.pond import Pond
from core.VitaLoom.core.logger import get_logger

logger = get_logger("PondSerializer")


def _to_json_value(value: Any) -> Any:
    """将 ndarray 等类型转为 JSON 可序列化结构。"""
    if hasattr(value, "tolist"):
        return value.tolist()
    return value


# 使用TYPE_CHECKING避免循环导入
if TYPE_CHECKING:
    from builtin.entity_types.organism import Organism
    from builtin.components.components_base import ComponentBase


class PondSerializer:
    """莲池与生物体、组件的往返序列化；生命周期为无状态工具类实例。"""
    
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
        logger.warning("[System:PondSerializer] %s失败: %s", action, error)

    def _require_fields(self, data: Dict[str, Any], fields: list[str], context: str):
        missing = [field for field in fields if field not in data]
        if missing:
            raise ValueError(f"{context}缺少字段: {', '.join(missing)}")
    
    def serialize_pond(self, pond: Pond) -> Dict[str, Any]:
        """将莲池人口、漂浮物、资源写入可 JSON 化的 dict。

        职责: 快照 `pond.organisms`、floating_system/resource_manager 或回退字段。
        时机: `save_pond`、编辑器导出、存档前调用。
        不变量: 输出含 `version`；生物体经 `serialize_organism` 逐项序列化。
        排错: 缺漂浮物/资源 → 查是否有 `floating_system`/`resource_manager`（见 README）。
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
                        "position": _to_json_value(resource["position"]),
                        "amount": resource["amount"],
                        "id": resource["id"]
                    })
        pond_data["resources"] = resources_data

        # 基础资源（无 resource_manager 时来自 Pond.resources）
        basic_res = []
        res_dict = getattr(pond, "resources", None)
        if isinstance(res_dict, dict):
            for key in ("food", "energy"):
                for item in res_dict.get(key, []) or []:
                    if isinstance(item, dict):
                        basic_res.append({
                            "kind": key,
                            "position": _to_json_value(item.get("position")),
                            "amount": item.get("amount"),
                            "type": item.get("type", key),
                        })
        pond_data["basic_resources"] = basic_res

        # 简单漂浮组件（无 floating_system 时）
        simple_fc = []
        for comp in getattr(pond, "floating_components", []) or []:
            if comp is None:
                continue
            try:
                simple_fc.append({
                    "component": self.serialize_component(comp),
                    "position": comp.position.tolist() if hasattr(comp.position, "tolist") else list(comp.position),
                })
            except Exception:
                continue
        pond_data["simple_floating_components"] = simple_fc

        return pond_data
    
    def serialize_organism(self, organism: Any) -> Dict[str, Any]:
        """快照单只生物体的运动学、组件 dict、膜与记忆列表。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
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
        if getattr(organism, "memory_system", None):
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

        # 代际 memory_genes（与 InheritanceSystem / mutation 对齐，独立于 memory_system）
        mg_data: List[Dict[str, Any]] = []
        for mg in getattr(organism, "memory_genes", []) or []:
            mg_data.append({
                "situation": mg.situation,
                "action_pattern": dict(getattr(mg, "action_pattern", {}) or {}),
                "success_rate": float(getattr(mg, "success_rate", 0.0)),
                "strength": float(getattr(mg, "strength", 1.0)),
                "age": int(getattr(mg, "age", 0)),
            })
        organism_data["memory_genes"] = mg_data
        
        return organism_data
    
    def serialize_component(self, component: Any) -> Dict[str, Any]:
        """序列化组件。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        component_data: Dict[str, Any] = {
            "id": component.id,
            "type": type(component).__name__,
            "name": getattr(component, "name", component.id),
            "location": getattr(component, "location", "internal"),
            "congenital": getattr(component, "congenital", True),
            "acquired": getattr(component, "acquired", False),
            "attach_point": getattr(component, "attach_point", None),
            "energy_consumption": getattr(component, "energy_consumption", 0.0),
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
            if hasattr(component, "success_threshold"):
                component_data["success_threshold"] = component.success_threshold
            if hasattr(component, "associations") and isinstance(getattr(component, "associations"), dict):
                component_data["associations"] = {
                    str(k): {str(ak): float(av) for ak, av in (v or {}).items()}
                    for k, v in component.associations.items()
                }
        
        return component_data

    def _restore_component_payload(self, component: Any, component_data: Dict[str, Any]) -> None:
        """将序列化字段写回已由工厂构造的组件实例。"""
        component.location = component_data["location"]
        component.congenital = component_data["congenital"]
        component.acquired = component_data["acquired"]
        component.attach_point = component_data["attach_point"]
        component.energy_consumption = component_data["energy_consumption"]

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
            if "success_threshold" in component_data:
                component.success_threshold = float(component_data["success_threshold"])
            if "associations" in component_data and isinstance(component_data.get("associations"), dict):
                component.associations = {
                    str(k): {str(ak): float(av) for ak, av in (v or {}).items()}
                    for k, v in component_data["associations"].items()
                }
    
    def deserialize_pond(self, pond_data: Dict[str, Any], pond_class: type = Pond) -> Optional[Pond]:
        """从 dict 重建 Pond 并回填各 organism 的 `pond` 引用。

        职责: 校验必填字段，反序列化人口与资源/漂浮物分支。
        时机: `load_pond`、编辑器导入 `.pond`（PS 人口路径）时调用。
        不变量: 成功时每个 `org.pond = pond`；失败返回 None 并打日志。
        排错: ValueError 缺字段 → 对照 `serialize_pond` 键名；人口空 → 查 organisms 列表。
        """
        try:
            self._require_fields(
                pond_data,
                ["name", "size", "max_population", "initial_organisms", "iteration", "environmental_factors", "statistics"],
                "pond_data",
            )
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
            organisms_dict: Dict[str, Any] = {}
            organisms_list: List[Dict[str, Any]] = pond_data.get("organisms", [])
            for organism_data in organisms_list:
                organism = self.deserialize_organism(organism_data)
                if organism is not None:
                    organisms_dict[organism.id] = organism
            pond.organisms = organisms_dict

            # 恢复基础资源
            br = pond_data.get("basic_resources", [])
            if isinstance(br, list) and hasattr(pond, "resources"):
                food = []
                energy = []
                for item in br:
                    if not isinstance(item, dict):
                        continue
                    kind = item.get("kind", "food")
                    entry = {
                        "position": item.get("position"),
                        "amount": item.get("amount", 1.0),
                        "type": item.get("type", kind),
                    }
                    if kind == "energy":
                        energy.append(entry)
                    else:
                        food.append(entry)
                pond.resources["food"] = food
                pond.resources["energy"] = energy

            # 简单漂浮组件
            import numpy as np
            pond.floating_components.clear()
            sf = pond_data.get("simple_floating_components", [])
            if isinstance(sf, list):
                for entry in sf:
                    if not isinstance(entry, dict):
                        continue
                    payload = entry.get("component")
                    if not isinstance(payload, dict):
                        continue
                    comp = self.deserialize_component(payload)
                    if comp is None:
                        continue
                    pos = entry.get("position")
                    if pos is not None and hasattr(comp, "position"):
                        comp.position = np.array(pos, dtype=float)
                    pond.floating_components.append(comp)

            # 反序列化漂浮组件
            if hasattr(pond, "floating_system") and pond.floating_system:
                floating_components_list: List[Dict[str, Any]] = []
                floating_components_data = pond_data.get("floating_components", [])
                for floating_component_data in floating_components_data:
                    if not isinstance(floating_component_data, dict):
                        continue
                    component_payload = floating_component_data.get("component")
                    if not isinstance(component_payload, dict):
                        continue
                    component = self.deserialize_component(component_payload)
                    if component is None:
                        continue
                    floating_components_list.append({
                        "component": component,
                        "position": floating_component_data.get("position"),
                        "velocity": floating_component_data.get("velocity"),
                        "lifespan": floating_component_data.get("lifespan"),
                        "decay_rate": floating_component_data.get("decay_rate"),
                    })
                pond.floating_system.floating_components = floating_components_list
        
            # 反序列化资源
            if hasattr(pond, "resource_manager") and pond.resource_manager:
                resources: Dict[str, List[Dict[str, Any]]] = {}
                resources_data = pond_data.get("resources", [])
                for resource_data in resources_data:
                    if not isinstance(resource_data, dict):
                        continue
                    resource_type = resource_data.get("type")
                    if not resource_type:
                        continue
                    if resource_type not in resources:
                        resources[resource_type] = []
                    resources[resource_type].append({
                        "type": resource_type,
                        "position": resource_data.get("position"),
                        "amount": resource_data.get("amount"),
                        "id": resource_data.get("id"),
                    })
                pond.resource_manager.resources = resources
            
            for org in pond.organisms.values():
                if hasattr(org, "pond"):
                    org.pond = pond
            
            return pond
        except Exception as e:
            self._log_error("反序列化莲池", e)
            return None
    
    def deserialize_organism(self, organism_data: Dict[str, Any]) -> Any:
        """重建 Simple/IntelligentOrganism 并将组件 `organism_id` 设为真实 ID。

        职责: 按 `type` 选类，遍历 components 调用 `deserialize_component`。
        时机: `deserialize_pond` 内对每个 organism 条目调用。
        不变量: 组件反序列化后 `component.organism_id = organism.id`。
        排错: None → 缺必填字段或组件 type 无法映射（见 README temp id）。
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
                    "dead",
                    "velocity",
                    "acceleration",
                    "components",
                ],
                "organism_data",
            )
            # 导入需要的类
            from builtin.entity_types.simple_organism import SimpleOrganism
            from builtin.entity_types.intelligent_organism import IntelligentOrganism
            from core.Lotucosm.memory import MemorySystem
        
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
                if component is None:
                    continue
                # 更新组件的organism_id为实际的生物体ID
                component.organism_id = organism.id
                organism.components[component.id] = component
        
            # 反序列化细胞膜
            if "membrane" in organism_data and organism_data["membrane"]:
                membrane = self.deserialize_component(organism_data["membrane"])
                if membrane is not None:
                    # 更新细胞膜的organism_id为实际的生物体ID
                    membrane.organism_id = organism.id
                    organism.membrane = membrane
        
            # 反序列化记忆系统
            if "memories" in organism_data and organism_data["memories"]:
                organism.memory_system = MemorySystem()
                for memory_data in organism_data["memories"]:
                    if not isinstance(memory_data, dict):
                        continue
                    self._require_fields(
                        memory_data,
                        ["situation", "action_pattern", "success_rate"],
                        "memory_data",
                    )
                    from core.Lotucosm.memory import MemoryGene
                    memory = MemoryGene(
                        situation=memory_data["situation"],
                        action_pattern=memory_data["action_pattern"],
                        success_rate=memory_data["success_rate"]
                    )
                    memory.strength = memory_data.get("strength", memory.strength)
                    memory.age = memory_data.get("age", memory.age)
                    organism.memory_system.memories.append(memory)

            # 代际 memory_genes
            organism.memory_genes = []
            for mg_data in organism_data.get("memory_genes", []) or []:
                if not isinstance(mg_data, dict):
                    continue
                self._require_fields(
                    mg_data,
                    ["situation", "action_pattern", "success_rate"],
                    "memory_gene_data",
                )
                from core.Lotucosm.memory import MemoryGene

                mg = MemoryGene(
                    situation=mg_data["situation"],
                    action_pattern=dict(mg_data.get("action_pattern") or {}),
                    success_rate=float(mg_data["success_rate"]),
                )
                mg.strength = float(mg_data.get("strength", mg.strength))
                mg.age = int(mg_data.get("age", mg.age))
                organism.memory_genes.append(mg)
            
            return organism
        except Exception as e:
            self._log_error("反序列化生物体", e)
            return None
    
    def deserialize_component(self, component_data: Dict[str, Any]) -> Any:
        """按 `type` 字段构造组件（临时 organism_id，须由宿主回填）。

        职责: 映射 Sensor/Actuator/Membrane/PVAECEngine 等并恢复序列化属性。
        时机: `deserialize_organism` 内逐项调用；成功后 `organism_id` 被覆盖为真实 ID。
        不变量: 初值 `temp_organism` 仅中间态；未知 type 回退 ComponentBase。
        排错: None → type 拼写或必填键缺失；加载后 ID 仍为 temp → 查 deserialize_organism 回填（README）。
        """
        try:
            self._require_fields(
                component_data,
                ["type", "id", "name", "location", "congenital", "acquired", "attach_point", "energy_consumption"],
                "component_data",
            )
            from builtin.components.component_factory import ComponentFactory

            temp_organism_id = "temp_organism"
            factory = ComponentFactory()
            component = factory.create_component(
                component_data["type"],
                component_data["id"],
                organism_id=temp_organism_id,
                name=component_data["name"],
            )
            self._restore_component_payload(component, component_data)
            return component
        except Exception as e:
            self._log_error("反序列化组件", e)
            return None
    
    def save_pond(self, pond: Pond, file_path: str) -> bool:
        """序列化并写入 json/pickle 文件。

        职责: `serialize_pond` + 按 `save_format` 写盘，自动 `makedirs`。
        时机: 用户存档、工作流导出。
        不变量: `save_format` 为 json 或 pickle；路径父目录可创建。
        排错: 返回 False → 查日志 `[System:PondSerializer] 保存莲池失败` 与磁盘权限。
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
            self._log_error("保存莲池", e)
            return False
    
    def load_pond(self, file_path: str, pond_class: type = Pond) -> Optional[Pond]:
        """读文件并 `deserialize_pond`。

        职责: 解析 JSON/pickle 为 dict 后反序列化。
        时机: 打开工程场景、恢复存档。
        不变量: 格式须与 `save_format` 一致；失败返回 None。
        排错: None → 文件损坏、版本字段不兼容或必填键缺失（见 README）。
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
            self._log_error("加载莲池", e)
            return None