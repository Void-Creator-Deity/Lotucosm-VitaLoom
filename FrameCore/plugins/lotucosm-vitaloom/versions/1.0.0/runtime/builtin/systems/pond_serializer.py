"""PS 莲池 JSON/pickle 序列化：人口、组件、漂浮物与资源快照。

架构数据流::

    Pond → serialize_pond → 文件 → load_pond → deserialize_pond → Pond

不变量: `version` 字段当前为 1.0；organism 反序列化后须回填 `organism_id` 与 `org.pond`。

排错: 见 `builtin/README.md`（缺字段、temp organism_id、资源为空）。
"""

import json
import math
import os
import pickle
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional, List, TYPE_CHECKING

from core.Lotucosm.pond import Pond
from core.VitaLoom.core.logger import get_logger
from builtin.components.component_library import canonical_component_type

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

    @staticmethod
    def _restore_pond_time(value: Any) -> int:
        """Validate the physical-frame counter before it enters a live Pond."""
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError("pond_data.time必须是非负整数")
        return value
    
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
            "time": pond.time,
            "simulation_time": float(getattr(pond, "simulation_time", 0.0)),
            "iteration": pond.iteration,
            "max_population": pond.max_population,
            "initial_organisms": pond.initial_organisms,
            "initial_components": pond.initial_components,
            "component_variety": pond.component_variety,
            "evolution_generation_interval": pond.evolution_generation_interval,
            "environmental_factors": pond.environmental_factors,
            "statistics": pond.statistics
        }
        floating_system = getattr(pond, "floating_system", None)
        if floating_system is not None:
            pond_data["floating_assembly_sequence"] = int(
                getattr(floating_system, "_assembly_sequence", 0) or 0
            )
        
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
                            **({"id": item["id"]} if "id" in item else {}),
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
            "size": organism.size,
            "radius": organism.radius,
            "energy": organism.energy,
            "max_energy": organism.max_energy,
            "health": organism.health,
            "max_health": organism.max_health,
            "age": organism.age,
            "generation": getattr(organism, "generation", 1),
            "dead": getattr(organism, "dead", False),
            "dead": organism.dead,
            "mutation_rate": organism.mutation_rate,
            "inheritance_rate": organism.inheritance_rate,
            "energy_consumption_rate": organism.energy_consumption_rate
        }
        organism_data["enable_pvaec_cycle_per_tick"] = bool(
            getattr(organism, "enable_pvaec_cycle_per_tick", False)
        )
        organism_data["social_learning_enabled"] = bool(
            getattr(organism, "social_learning_enabled", False)
        )
        
        # 序列化组件
        components_data: List[Dict[str, Any]] = []
        for _, comp in organism.components.items():
            component_data = self.serialize_component(comp)
            components_data.append(component_data)
        organism_data["components"] = components_data

        # 组件图持久化：只写稳定 id/顺序，不泄漏 live object 引用。
        organism_data["component_connections"] = self._serialize_component_connections(organism)
        
        # 序列化细胞膜
        if organism.membrane:
            organism_data["membrane"] = self.serialize_component(organism.membrane)
        
        # 序列化记忆系统
        organism_data["memory_system_enabled"] = getattr(organism, "memory_system", None) is not None
        pvaec_cycle = getattr(organism, "_pvaec_cycle", None)
        organism_data["pvaec_cycle_current_step"] = (
            int(getattr(pvaec_cycle, "current_step", 0)) if pvaec_cycle is not None else 0
        )
        organism_data["pvaec_runtime"] = {
            "use_ps_verify_triple": bool(getattr(organism, "use_ps_verify_triple", False)),
            "enable_pvaec_cycle_per_tick": bool(getattr(organism, "enable_pvaec_cycle_per_tick", False)),
            "previous_energy": float(getattr(organism, "_previous_energy", organism.energy)),
            "previous_health": float(getattr(organism, "_previous_health", organism.health)),
            "ps_verify_delta_time": float(getattr(organism, "_ps_verify_delta_time", 1.0)),
            "successful_actions": int(getattr(organism, "successful_actions", 0)),
        }
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
            "type": canonical_component_type(component),
            "name": getattr(component, "name", component.id),
            "location": getattr(component, "location", "internal"),
            "congenital": getattr(component, "congenital", True),
            "acquired": getattr(component, "acquired", False),
            "attach_point": getattr(component, "attach_point", None),
            "energy_consumption": getattr(component, "energy_consumption", 0.0),
        }
        if getattr(component, "sr_component_id", None) is not None:
            component_data["sr_component_id"] = component.sr_component_id
        
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
        """通过组件 owner API 原子恢复已构造组件。"""
        restore = getattr(component, "restore_persistent_state", None)
        if not callable(restore):
            raise TypeError("component does not provide restore_persistent_state")
        restore(component_data)

    def deserialize_pond(
        self,
        pond_data: Dict[str, Any],
        pond_class: type = Pond,
        *,
        randomness_rng: Any = None,
    ) -> Optional[Pond]:
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
            restored_time = self._restore_pond_time(pond_data.get("time", 0))
            # 创建莲池实例
            pond = pond_class(
                name=pond_data["name"],
                size=pond_data["size"],
                max_population=pond_data["max_population"],
                initial_organisms=pond_data["initial_organisms"],
                initial_components=pond_data.get("initial_components", 50),
                component_variety=pond_data.get("component_variety", "all"),
                evolution_generation_interval=pond_data.get("evolution_generation_interval"),
                randomness_rng=randomness_rng,
                initialize=False,
            )
            
            # 恢复基本属性
            pond.time = restored_time
            simulation_time = pond_data.get("simulation_time", 0.0)
            if isinstance(simulation_time, bool) or not isinstance(simulation_time, (int, float)):
                raise ValueError("pond_data.simulation_time必须是有限数值")
            if not math.isfinite(float(simulation_time)) or float(simulation_time) < 0.0:
                raise ValueError("pond_data.simulation_time必须是有限非负数")
            pond.simulation_time = float(simulation_time)
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
            if randomness_rng is not None:
                pond.set_randomness_owner(randomness_rng)
            # 构造器可能先创建默认实体；恢复后根注册必须只指向新对象。
            pond.root_entities.clear()
            for organism in pond.organisms.values():
                pond.add_entity(organism)

            # A plain Pond has no subsystem instances, so project both stored
            # resource sources into its compatibility collection.
            basic_resources = pond_data.get("basic_resources", [])
            managed_resources = pond_data.get("resources", [])
            def restore_resources(items: list) -> Dict[str, List[Dict[str, Any]]]:
                food = []
                energy = []
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    kind = item.get("type", item.get("kind", "food"))
                    entry = {
                        "position": item.get("position"),
                        "amount": item.get("amount", 1.0),
                        "type": item.get("type", kind),
                    }
                    if item.get("id") is not None:
                        entry["id"] = item["id"]
                    if kind == "energy":
                        energy.append(entry)
                    else:
                        food.append(entry)
                return {"food": food, "energy": energy}

            basic = restore_resources(basic_resources if isinstance(basic_resources, list) else [])
            managed = restore_resources(managed_resources if isinstance(managed_resources, list) else [])
            managed_by_type: Dict[str, List[Dict[str, Any]]] = {"food": [], "energy": []}
            if isinstance(managed_resources, list):
                for item in managed_resources:
                    if isinstance(item, dict) and item.get("type"):
                        resource_type = item["type"]
                        managed_by_type.setdefault(resource_type, []).append({
                            "type": resource_type,
                            "position": item.get("position"),
                            "amount": item.get("amount"),
                            "id": item.get("id"),
                        })
            if hasattr(pond, "resources"):
                pond.resources = {
                    kind: basic[kind] if pond.resource_manager else managed[kind] + basic[kind]
                    for kind in ("food", "energy")
                }

            # 简单漂浮组件
            import numpy as np
            simple_floating_components = []
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
                        comp.set_position(tuple(np.asarray(pos, dtype=float)))
                    simple_floating_components.append(comp)
            simple_source_components = list(simple_floating_components)

            # 反序列化漂浮组件。系统条目也投影到无 FloatingSystem 的 Pond。
            floating_components_list: List[Dict[str, Any]] = []
            floating_components_data = pond_data.get("floating_components", [])
            if isinstance(floating_components_data, list):
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
            if floating_components_list:
                compatible_components = []
                for entry in floating_components_list:
                    component = entry["component"]
                    position = entry.get("position")
                    velocity = entry.get("velocity")
                    if position is not None and hasattr(component, "set_position"):
                        component.set_position(tuple(np.asarray(position, dtype=float)))
                    if velocity is not None and hasattr(component, "set_velocity"):
                        component.set_velocity(tuple(np.asarray(velocity, dtype=float)))
                    compatible_components.append(component)
                if not pond.floating_system:
                    simple_floating_components.extend(compatible_components)
            pond.replace_floating_components(simple_floating_components)

            if hasattr(pond, "floating_system") and pond.floating_system:
                pond.floating_system.replace_floating_components(floating_components_list)
        
            # 反序列化资源
            if hasattr(pond, "resource_manager") and pond.resource_manager:
                pond.resource_manager.resources = managed_by_type

            pond._loaded_pond_sources = {
                "basic_resources": basic,
                "managed_resources": managed_by_type,
                "simple_floating_components": simple_source_components,
                "managed_floating_components": floating_components_list,
                "floating_assembly_sequence": pond_data.get("floating_assembly_sequence"),
            }
            
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
            from builtin.entity_types.organism import Organism
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
                    , enable_pvaec_cycle_per_tick=organism_data.get("enable_pvaec_cycle_per_tick", False)
                    , social_learning_enabled=organism_data.get("social_learning_enabled", False)
                )
            elif organism_type == "Organism":
                organism = Organism(
                    organism_id=organism_data["id"],
                    position=position,
                    energy=organism_data["energy"],
                    max_energy=organism_data["max_energy"],
                    health=organism_data["health"],
                    max_health=organism_data["max_health"],
                    mutation_rate=organism_data["mutation_rate"],
                    inheritance_rate=organism_data["inheritance_rate"],
                    energy_consumption_rate=organism_data["energy_consumption_rate"]
                    , enable_pvaec_cycle_per_tick=organism_data.get("enable_pvaec_cycle_per_tick", False)
                    , social_learning_enabled=organism_data.get("social_learning_enabled", False)
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
                    , enable_pvaec_cycle_per_tick=organism_data.get("enable_pvaec_cycle_per_tick", False)
                    , social_learning_enabled=organism_data.get("social_learning_enabled", False)
                )
        
            # Hydration 是 runtime owner API 边界：所有可持久化实体状态
            # 在完整输入校验后恢复；该顺序允许 size 与独立 collision radius 共存。
            organism.restore_motion_state(
                position=organism_data["position"],
                velocity=organism_data["velocity"],
                acceleration=organism_data["acceleration"],
            )
            if "size" in organism_data:
                organism.set_size(organism_data["size"])
            if "radius" in organism_data:
                organism.set_radius(organism_data["radius"])
            organism.set_age(organism_data["age"])
            if "generation" in organism_data:
                organism.set_generation(organism_data["generation"])
            organism.set_dead(organism_data["dead"])
            runtime_state = organism_data.get("pvaec_runtime")
            if isinstance(runtime_state, dict):
                organism.use_ps_verify_triple = bool(runtime_state.get("use_ps_verify_triple", False))
                organism.enable_pvaec_cycle_per_tick = bool(runtime_state.get("enable_pvaec_cycle_per_tick", False))
                organism._previous_energy = float(runtime_state.get("previous_energy", organism.energy))
                organism._previous_health = float(runtime_state.get("previous_health", organism.health))
                organism._ps_verify_delta_time = float(runtime_state.get("ps_verify_delta_time", 1.0))
                organism.successful_actions = int(runtime_state.get("successful_actions", 0))
        
            # 反序列化组件
            restored_components = []
            for component_data in organism_data["components"]:
                component = self.deserialize_component(component_data)
                if component is None:
                    continue
                restored_components.append(component)
            organism.replace_components(restored_components)
        
            # 反序列化细胞膜
            if "membrane" in organism_data and organism_data["membrane"]:
                membrane = self.deserialize_component(organism_data["membrane"])
                if membrane is not None:
                    # 更新细胞膜的organism_id为实际的生物体ID
                    organism.set_membrane(membrane)
        
            # 组件图恢复必须在全部组件 owner hydration 完成后进行。
            organism.replace_component_connections(
                organism_data.get("component_connections", [])
            )

            # 反序列化记忆系统
            if organism_data.get("memory_system_enabled") is True or (
                "memories" in organism_data and organism_data["memories"]
            ):
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
                    organism.memory_system.adopt_memory(memory, enforce_capacity=False)
            if organism_data.get("pvaec_cycle_current_step", 0):
                from core.Lotucosm.pvaec_cycle import PVAECCycle

                organism._pvaec_cycle = PVAECCycle()
                organism._pvaec_cycle.current_step = int(organism_data["pvaec_cycle_current_step"])

            # 代际 memory_genes
            organism.replace_memory_genes([])
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
                organism.adopt_memory_gene(mg)
            
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
                **({"sr_component_id": component_data["sr_component_id"]}
                   if "sr_component_id" in component_data else {}),
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
        temporary_path = None
        try:
            # 序列化莲池
            pond_data = self.serialize_pond(pond)
            directory = os.path.dirname(file_path) or "."
            os.makedirs(directory, exist_ok=True)

            if self.save_format == "json":
                mode = "w"
                encoding = "utf-8"
            elif self.save_format == "pickle":
                mode = "wb"
                encoding = None
            else:
                raise ValueError(f"不支持的保存格式: {self.save_format}")

            with tempfile.NamedTemporaryFile(
                mode=mode,
                encoding=encoding,
                dir=directory,
                prefix=f".{os.path.basename(file_path)}.",
                suffix=".tmp",
                delete=False,
            ) as stream:
                temporary_path = stream.name
                if self.save_format == "json":
                    json.dump(pond_data, stream, indent=2, ensure_ascii=False)
                else:
                    pickle.dump(pond_data, stream)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_path, file_path)
            return True
        except Exception as e:
            self._log_error("保存莲池", e)
            return False
        finally:
            if temporary_path is not None and os.path.exists(temporary_path):
                try:
                    os.unlink(temporary_path)
                except OSError as cleanup_error:
                    self._log_error("清理临时存档", cleanup_error)
    
    def load_pond(
        self,
        file_path: str,
        pond_class: type = Pond,
        *,
        randomness_rng: Any = None,
    ) -> Optional[Pond]:
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
            pond = self.deserialize_pond(
                pond_data,
                pond_class,
                randomness_rng=randomness_rng,
            )
            return pond
        except Exception as e:
            self._log_error("加载莲池", e)
            return None
