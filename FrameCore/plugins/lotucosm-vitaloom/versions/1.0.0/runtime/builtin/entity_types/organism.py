"""PS 生物体基类：组件图、膜、记忆与 update 链（非 SR `_SceneRuntimeEntity`）。

架构数据流::

    Organism.update → components.sense/act → Membrane.auto_ingest（PS）

排错: 见 `builtin/README.md`。
"""
from typing import Dict, List, Any, Optional, Tuple, TYPE_CHECKING
import numpy as np
import math
from core.Lotucosm.entity import EntityBase
from builtin.components.components_base import ComponentBase
from core.VitaLoom.core.logger import get_logger

logger = get_logger("Organism")

if TYPE_CHECKING:
    from core.Lotucosm.memory import MemoryGene


class Organism(EntityBase):
    """PS 生物体统一父类：传感器/执行器 dict、连接与能量生命周期。"""

    def __init__(self, organism_id: str, position: Tuple[float, float], **kwargs):
        """初始化生物体。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 初始化父类
        super().__init__(entity_id=organism_id, position=position, **kwargs)

        # 生物体特有属性
        self.organism_id: str = organism_id
        self.name: str = kwargs.get('name', f"Organism_{organism_id}")
        self.energy: float = 0.0
        self.max_energy: float = 200.0
        self.set_max_energy(kwargs.get("max_energy", 200.0))
        self.set_energy(kwargs.get("energy", 100.0))
        self.max_health: float = 1.0
        self.set_max_health(kwargs.get("max_health", 100.0))
        self.health: float = 0.0
        self.set_health(kwargs.get("health", self.max_health))
        self.mutation_rate: float = float(kwargs.get("mutation_rate", 0.01) or 0.01)
        self.inheritance_rate: float = float(kwargs.get("inheritance_rate", 0.8) or 0.8)
        self.energy_consumption_rate: float = float(kwargs.get("energy_consumption_rate", 0.05) or 0.05)
        _et = kwargs.get("evolvable_traits")
        self.evolvable_traits: dict[str, object] = dict(_et) if isinstance(_et, dict) else {}
        # 旧版运行时记忆（MemorySystem）；PVAECCycle 读写此对象
        self.memory_system: Any = kwargs.get("memory_system")
        self.enable_pvaec_cycle_per_tick: bool = bool(kwargs.get("enable_pvaec_cycle_per_tick", False))
        self._pvaec_cycle: Any = None
        self.age: int = 0
        self.set_age(kwargs.get("age", 0))
        self.generation: int = 1
        self.set_generation(kwargs.get("generation", 1))
        self.dead: bool = False

        # 组件管理
        self.components: Dict[str, ComponentBase] = {}
        self.membrane: Optional[ComponentBase] = None

        # 记忆系统：结构化代际记忆（MemoryGene），由 InheritanceSystem 在繁殖时复制； 与 IntelligentOrganism.memory / MemorySystem 的运行时缓存长期并存，迁移方向为统一经 memory_genes + 编排器闭环。
        self.memory_genes: List[Any] = []

        # 统计信息
        self.offspring_count: int = 0
        self.successful_actions: int = 0

        # 个体发育阶梯（ADR-0004 PS 轨；默认关以保持向后兼容）
        self.developmental_ladder_enabled: bool = bool(
            kwargs.get("developmental_ladder_enabled", False)
        )
        self.developmental_stage: int = int(kwargs.get("developmental_initial_stage", 0) or 0)
        from core.Lotucosm.ps_developmental import ensure_ps_developmental_state
        from core.Lotucosm.sr_developmental_ladder import clamp_stage

        ensure_ps_developmental_state(self)
        self.developmental_stage = clamp_stage(self.developmental_stage)

        # 社会学习（S3+；默认关）
        self.social_learning_enabled: bool = bool(kwargs.get("social_learning_enabled", False))
        self.developmental_plasticity_window: int = max(
            0, int(kwargs.get("developmental_plasticity_window", 0) or 0)
        )
        self.developmental_plasticity_penalty: bool = bool(
            kwargs.get("developmental_plasticity_penalty", False)
        )

    def adopt_memory_gene(self, memory_gene: "MemoryGene") -> None:
        """接纳一个已构造的 PS 代际记忆基因。

        `memory_genes` 仍保留为公开列表以兼容旧调用方，但 runtime 生产写入
        应通过此 organism-owned 边界完成。该方法不隐式复制；需要所有权隔离时，
        调用方必须先调用 `MemoryGene.copy()`。
        """
        from core.Lotucosm.memory import MemoryGene

        if not isinstance(memory_gene, MemoryGene):
            raise TypeError("memory_gene must be a MemoryGene")
        self.memory_genes.append(memory_gene)

    def replace_memory_genes(self, memory_genes: Any) -> None:
        """原子替换 PS 代际记忆基因集合，供受控 hydration 使用。

        先 materialize 并验证整个输入，再修改实体状态，避免 malformed 输入造成
        半更新。输入对象会被复制为新列表，但其中的 MemoryGene 不会被隐式复制。
        """
        from core.Lotucosm.memory import MemoryGene

        replacement = list(memory_genes)
        if any(not isinstance(gene, MemoryGene) for gene in replacement):
            raise TypeError("memory_genes must contain only MemoryGene instances")
        self.memory_genes = replacement

    def set_generation(self, generation: int) -> None:
        """设置非负整数代际编号。"""
        if isinstance(generation, bool):
            raise TypeError("generation must be an integer")
        try:
            normalized = int(generation)
        except (TypeError, ValueError) as exc:
            raise ValueError("generation must be an integer") from exc
        if normalized < 0:
            raise ValueError("generation must be non-negative")
        self.generation = normalized

    def increment_offspring_count(self) -> None:
        """记录一次成功的后代创建。"""
        self.offspring_count = int(getattr(self, "offspring_count", 0) or 0) + 1

    def set_randomness_owner(self, randomness_rng: Any = None) -> None:
        """Bind one simulation RNG to this organism and its current PS graph."""
        if randomness_rng is None:
            raise ValueError("Organism randomness owner cannot be cleared")
        if not hasattr(randomness_rng, "random"):
            raise TypeError("randomness_rng must expose random()")
        self.randomness_rng = randomness_rng
        for script in getattr(self, "scripts", ()):
            if hasattr(script, "randomness_rng"):
                script.randomness_rng = randomness_rng
        for component in self.components.values():
            if hasattr(component, "randomness_rng"):
                component.randomness_rng = randomness_rng
        if self.membrane is not None and hasattr(self.membrane, "randomness_rng"):
            self.membrane.randomness_rng = randomness_rng

    def set_max_energy(self, max_energy: float) -> None:
        """设置正的最大能量容量。"""
        try:
            normalized = float(max_energy)
        except (TypeError, ValueError) as exc:
            raise ValueError("max_energy must be a positive finite number") from exc
        if not math.isfinite(normalized) or normalized <= 0.0:
            raise ValueError("max_energy must be a positive finite number")
        self.max_energy = normalized

    def set_max_health(self, max_health: float) -> None:
        """设置正的最大生命容量，并重新约束当前 health。"""
        try:
            normalized = float(max_health)
        except (TypeError, ValueError) as exc:
            raise ValueError("max_health must be a positive finite number") from exc
        if not math.isfinite(normalized) or normalized <= 0.0:
            raise ValueError("max_health must be a positive finite number")
        self.max_health = normalized
        if hasattr(self, "health"):
            self.health = max(0.0, min(float(self.health), normalized))

    def set_health(self, health: float) -> None:
        """设置有限且不超过 max_health 的生命值。"""
        try:
            normalized = float(health)
        except (TypeError, ValueError) as exc:
            raise ValueError("health must be a finite number") from exc
        if not math.isfinite(normalized):
            raise ValueError("health must be a finite number")
        self.health = max(0.0, min(normalized, self.max_health))

    def set_dead(self, dead: bool) -> None:
        """设置死亡标志；死亡状态由 Organism 生命周期持有。"""
        if not isinstance(dead, bool):
            raise TypeError("dead must be a bool")
        self.dead = dead

    def set_energy(self, energy: float) -> None:
        """设置有限的能量值，作为 PS runtime energy 写入边界。"""
        try:
            normalized = float(energy)
        except (TypeError, ValueError) as exc:
            raise ValueError("energy must be a finite number") from exc
        if not math.isfinite(normalized):
            raise ValueError("energy must be a finite number")
        self.energy = normalized

    def replace_components(self, components: Any) -> None:
        """原子替换组件集合，保留公开 components dict seam。

        这是组件集合的 owner 写入边界，只负责 components mapping 与对应
        EntityBase 子节点关系；``membrane`` 是特殊引用，不经由本入口改写。
        校验全部在首次变更前完成，因此单次调用的失败不会留下半替换状态。
        """
        replacement = list(components)
        if any(not isinstance(component, ComponentBase) for component in replacement):
            raise TypeError("components must contain only ComponentBase instances")
        ids = [component.id for component in replacement]
        if len(ids) != len(set(ids)):
            raise ValueError("components must contain unique component ids")

        previous = list(self.components.values())
        previous_children = [
            child for child in list(self.children) if child in previous
        ]
        previous_parents = {id(component): component.parent for component in previous}
        replacement_preimages = {
            id(component): (
                component,
                getattr(component, "parent", None),
                getattr(component, "organism_id", None),
                getattr(component, "randomness_rng", None),
            )
            for component in replacement
        }

        for component in previous:
            self.remove_child(component)
        self.components.clear()
        try:
            for component in replacement:
                self.components[component.id] = component
                component.organism_id = self.id
                if hasattr(component, "randomness_rng"):
                    component.randomness_rng = self.randomness_rng
                self.add_child(component)
                on_attach = getattr(component, "on_attach", None)
                if callable(on_attach):
                    on_attach(self)
        except Exception:
            self.components.clear()
            replacement_set = {id(component) for component in replacement}
            for component in list(self.children):
                if id(component) in replacement_set and component not in previous_children:
                    self.remove_child(component)
            for component in previous:
                self.components[component.id] = component
                component.organism_id = self.id
                parent = previous_parents[id(component)]
                if parent is not None and component not in parent.children:
                    parent.children.append(component)
                component.parent = parent
            for component, parent, organism_id, randomness_rng in replacement_preimages.values():
                if component in self.children:
                    self.remove_child(component)
                component.parent = parent
                component.organism_id = organism_id
                if hasattr(component, "randomness_rng"):
                    component.randomness_rng = randomness_rng
            for child in previous_children:
                if child not in self.children:
                    self.children.append(child)
                child.parent = self
            raise

    def replace_component_graph(
        self,
        components: Any,
        membrane: Optional[ComponentBase] = None,
    ) -> None:
        """原子替换 components 映射与 membrane 特殊引用。

        与 :meth:`replace_components` 不同，本入口覆盖 PS 组件图的两个
        owner 字段：组件集合以及不进入 ``children`` 的 membrane 引用。
        用于 WorldBridge/检查点回放时，调用方可以在一次事务中获得完整
        pre-image 与补偿；注入失败不会留下部分组件、半绑定 membrane 或
        detached 子节点。
        """
        replacement = list(components)
        if any(not isinstance(component, ComponentBase) for component in replacement):
            raise TypeError("components must contain only ComponentBase instances")
        if membrane is not None and not isinstance(membrane, ComponentBase):
            raise TypeError("membrane must be a ComponentBase or None")
        ids = [component.id for component in replacement]
        if len(ids) != len(set(ids)):
            raise ValueError("components must contain unique component ids")

        previous_components = list(self.components.values())
        previous_children = list(self.children)
        previous_parents = {id(component): component.parent for component in previous_components}
        previous_membrane = self.membrane
        previous_membrane_owner = getattr(previous_membrane, "organism_id", None)
        previous_membrane_rng = getattr(previous_membrane, "randomness_rng", None)

        def restore_preimage() -> None:
            self.components.clear()
            for component in previous_components:
                self.components[component.id] = component
                component.organism_id = self.id
                parent = previous_parents[id(component)]
                if parent is not None and component not in parent.children:
                    parent.children.append(component)
                component.parent = parent
            self.children[:] = previous_children
            for child in self.children:
                if child in previous_components:
                    child.parent = self
                else:
                    child.parent = previous_parents.get(id(child), getattr(child, "parent", None))
            self.membrane = previous_membrane
            if previous_membrane is not None:
                previous_membrane.organism_id = previous_membrane_owner
                if hasattr(previous_membrane, "randomness_rng"):
                    previous_membrane.randomness_rng = previous_membrane_rng

        try:
            self.replace_components(replacement)
            self.set_membrane(membrane)
        except Exception:
            restore_preimage()
            if list(self.components.values()) != previous_components:
                raise RuntimeError("component graph compensation failed: components") from None
            if list(self.children) != previous_children:
                raise RuntimeError("component graph compensation failed: children") from None
            if self.membrane is not previous_membrane:
                raise RuntimeError("component graph compensation failed: membrane") from None
            raise

    def describe_component_hierarchy(self) -> Dict[str, Any]:
        """返回 PS 组件/膜层级的稳定、只读描述。

        `components` 是 organism 的实体子节点集合；`membrane` 是 organism
        持有的特殊组件引用，故意不加入 `children`，避免在 Organism.update
        的组件阶段与 EntityBase 递归阶段被重复更新。这个策略是 PS 本地
        hierarchy contract，不等同于 SR/PS 共享层级或 WorldBridge authority。
        """
        return {
            "owner_id": self.id,
            "component_ids": list(self.components.keys()),
            "component_parent_ids": {
                component_id: getattr(component, "parent", None).id
                if getattr(component, "parent", None) is not None
                else None
                for component_id, component in self.components.items()
            },
            "membrane_id": getattr(self.membrane, "id", None),
            "membrane_owner_id": getattr(self.membrane, "organism_id", None),
            "membrane_relation": "special_owned_reference",
            "membrane_is_entity_child": bool(self.membrane is not None and self.membrane in self.children),
        }
    def set_membrane(self, membrane: Optional[ComponentBase]) -> None:
        """设置细胞膜引用并绑定其 organism_id。"""
        if membrane is not None and not isinstance(membrane, ComponentBase):
            raise TypeError("membrane must be a ComponentBase or None")
        if membrane is not None:
            membrane.organism_id = self.id
            if hasattr(membrane, "randomness_rng"):
                membrane.randomness_rng = self.randomness_rng
        self.membrane = membrane

    def add_component(self, component: ComponentBase) -> bool:
        """添加组件到生物体。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if component.id in self.components:
            return False

        self.components[component.id] = component
        component.organism_id = self.id
        if hasattr(component, "randomness_rng"):
            component.randomness_rng = self.randomness_rng
        try:
            self.add_child(component) # 确保组件在实体树中，从而正确计算 world_position
            on_attach = getattr(component, "on_attach", None)
            if callable(on_attach):
                on_attach(self)
        except Exception:
            # attach 失败时回滚 owner 和实体树，避免半附着组件泄漏。
            self.components.pop(component.id, None)
            self.remove_child(component)
            raise
        return True


    def remove_component(self, component_id: str) -> bool:
        """从生物体中移除组件。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if component_id not in self.components:
            return False

        component = self.components[component_id]
        on_detach = getattr(component, "on_detach", None)
        if callable(on_detach):
            on_detach(self)
        self.components.pop(component_id, None)
        self.remove_child(component)
        return True


    def replace_component_connections(self, edges: Any) -> None:
        """原子恢复有序组件边；连接目标必须属于当前 organism。

        持久化格式只保存 source/target id 与边顺序，不保存 live component
        引用。恢复完成后仍通过 Component.add_connection owner seam 建边。
        缺少 `component_connections` 的旧场景保持空图兼容。
        """
        if edges is None:
            return
        if not isinstance(edges, (list, tuple)):
            raise TypeError("component_connections must be a list")
        parsed: list[tuple[str, str]] = []
        for index, edge in enumerate(edges):
            if not isinstance(edge, dict):
                raise TypeError(f"component connection {index} must be an object")
            source_id = edge.get("source_id")
            target_id = edge.get("target_id")
            if not isinstance(source_id, str) or not isinstance(target_id, str):
                raise ValueError(f"component connection {index} requires source_id/target_id")
            if source_id not in self.components or target_id not in self.components:
                raise ValueError(
                    f"component connection {index} references an unknown component"
                )
            parsed.append((source_id, target_id))

        for component in self.components.values():
            component.connections.clear()
        for source_id, target_id in parsed:
            self.components[source_id].add_connection(self.components[target_id])

    def get_component(self, component_id: str) -> Optional[ComponentBase]:
        """获取组件。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        return self.components.get(component_id)

    def add_sensor(self, sensor: ComponentBase) -> bool:
        """添加传感器为子实体。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        success = self.add_component(sensor)
        if success:
            # 在新架构中，传感器也是一个子实体
            self.add_child(sensor)
            logger.info("Organism: 已将传感器 %s 添加为子实体", sensor.id)
        return success

    def add_actuator(self, actuator: ComponentBase) -> bool:
        """添加执行器为子实体。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        success = self.add_component(actuator)
        if success:
            # 同理，执行器也是子实体
            self.add_child(actuator)
            logger.info("Organism: 已将执行器 %s 添加为子实体", actuator.id)
        return success

    def connect_tools(self, tool1_id: str, tool2_id: str) -> bool:
        """连接两个工具（传感器和执行器）。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if tool1_id not in self.components or tool2_id not in self.components:
            return False

        c1 = self.components[tool1_id]
        c2 = self.components[tool2_id]
        
        # 建立连接
        if hasattr(c1, 'add_connection'):
            c1.add_connection(c2)
            return True
        return False

    def update(self, delta_time: float = 1.0, environment: Any = None) -> None:
        """更新生物体状态。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if self.dead or not self.active:
            return

        # 0. 可选：旧版单体 PVAEC 闭环（默认关）
        if environment and self.enable_pvaec_cycle_per_tick and self.memory_system is not None:
            from core.Lotucosm.pvaec_cycle import PVAECCycle

            if self._pvaec_cycle is None:
                self._pvaec_cycle = PVAECCycle()
            self._pvaec_cycle.run_cycle(self, environment)

        # 1. 感知环境
        if environment:
            for component in self.components.values():
                if hasattr(component, 'sense'):
                    component.sense(environment)

        # 2. 信号传递与组件更新
        for component in self.components.values():
            environment_rng = getattr(environment, "randomness_rng", None) if environment else None
            if environment_rng is not None and hasattr(component, "randomness_rng"):
                component.randomness_rng = environment_rng
            component.update(delta_time)
            
            # 如果是传感器且有输出信号，传递给连接的组件
            if hasattr(component, 'output_signal') and hasattr(component, 'connections'):
                for conn in component.connections:
                    if hasattr(conn, 'process_signal'):
                        conn.process_signal(component.output_signal)

        # 3. 物质交换 (细胞膜吞噬)
        if environment:
            for component in self.components.values():
                if hasattr(component, 'auto_ingest'):
                    energy_gain = component.auto_ingest(environment)
                    if energy_gain > 0:
                        self.gain_energy(energy_gain)
                        self.successful_actions += 1

        # 4. 执行行为 (应用执行器的力)

        for component in self.components.values():
            # 肌肉执行器影响位移
            if hasattr(component, 'get_force_vector'):
                angle = getattr(self, 'rotation', 0.0)
                force = component.get_force_vector(angle)
                self.apply_force(force)
                # 消耗额外能量
                self.consume_energy(getattr(component, 'energy_cost', 0.01) * abs(getattr(component, 'current_force', 0)))
            
            # 纤毛执行器影响旋转
            if hasattr(component, 'current_torque'):
                self.rotation = getattr(self, 'rotation', 0.0) + component.current_torque * delta_time
                self.consume_energy(getattr(component, 'energy_cost', 0.01) * abs(component.current_torque))

        # 4. 更新物理（位置、速度等）
        super().update(delta_time)

        # 5. 基础能量代谢
        self.advance_age()
        self.set_energy(self.energy - 0.05 * delta_time)
        if self.energy <= 0:
            self.set_dead(True)
            self.set_energy(0.0)

    def reproduce(self) -> Optional['Organism']:
        """繁殖产生后代。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        from core.Lotucosm.randomness import random_uniform_array

        # 繁殖消耗能量并产生变异后代
        repro_cost = 100.0
        if self.energy < repro_cost + 20.0:
            return None
            
        self.set_energy(self.energy - repro_cost)
        self.offspring_count += 1
        
        child_id = f"Org_{self.id}_{self.offspring_count}"
        # 产生偏移位置
        randomness_rng = getattr(self, "randomness_rng", None)
        if randomness_rng is None:
            randomness_rng = getattr(getattr(self, "pond", None), "randomness_rng", None)
        offset = random_uniform_array(randomness_rng, -30, 30, 2)
        child = self.__class__(
            organism_id=child_id,
            position=tuple(self.position + offset),
            energy=65.0,
            generation=self.generation + 1
        )
        
        # 复制并变异组件
        for comp in self.components.values():
            if hasattr(comp, 'mutate'):
                mutated_comp = comp.mutate(randomness_rng=randomness_rng)
                child.add_component(mutated_comp)
                
        return child


    def consume_energy(self, amount: float) -> bool:
        """消耗能量。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if self.energy >= amount:
            self.set_energy(self.energy - amount)
            return True
        return False

    def gain_energy(self, amount: float) -> None:
        """获得能量。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self.set_energy(min(self.energy + amount, self.max_energy))

    def get_status(self) -> Dict[str, Any]:
        """获取生物体状态。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        status = super().get_status()
        status.update({
            'organism_id': self.organism_id,
            'name': self.name,
            'energy': self.energy,
            'max_energy': self.max_energy,
            'age': self.age,
            'generation': self.generation,
            'dead': self.dead,
            'component_count': len(self.components),
            'offspring_count': self.offspring_count,
            'successful_actions': self.successful_actions
        })
        return status

    def __repr__(self) -> str:
        """返回生物体的字符串表示"""
        return f"{self.__class__.__name__}(id={self.id}, name={self.name}, energy={self.energy:.1f})"

