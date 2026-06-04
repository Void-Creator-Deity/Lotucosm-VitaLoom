"""PS 生物体基类：组件图、膜、记忆与 update 链（非 SR `_SceneRuntimeEntity`）。

架构数据流::

    Organism.update → components.sense/act → Membrane.auto_ingest（PS）

排错: 见 `builtin/README.md`。
"""
from typing import Dict, List, Any, Optional, Tuple, TYPE_CHECKING
import numpy as np
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
        self.energy: float = kwargs.get('energy', 100.0)
        self.max_energy: float = kwargs.get('max_energy', 200.0)
        _mh = float(kwargs.get("max_health", 100.0) or 100.0)
        self.max_health: float = max(1.0, _mh)
        self.health: float = float(kwargs.get("health", self.max_health) or self.max_health)
        self.health = max(0.0, min(self.health, self.max_health))
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
        self.generation: int = kwargs.get('generation', 1)
        self.dead: bool = False

        # 组件管理
        self.components: Dict[str, ComponentBase] = {}
        self.membrane: Optional[ComponentBase] = None

        # 记忆系统：结构化代际记忆（MemoryGene），由 InheritanceSystem 在繁殖时复制； 与 IntelligentOrganism.memory / MemorySystem 的运行时缓存长期并存，迁移方向为统一经 memory_genes + 编排器闭环。
        self.memory_genes: List[Any] = []

        # 统计信息
        self.offspring_count: int = 0
        self.successful_actions: int = 0

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
        self.add_child(component) # 确保组件在实体树中，从而正确计算 world_position
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

        component = self.components.pop(component_id)
        self.remove_child(component)
        return True


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

        if self.dead:
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
        self.age += 1
        self.energy -= 0.05 * delta_time
        if self.energy <= 0:
            self.dead = True
            self.energy = 0

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

        # 繁殖消耗能量并产生变异后代
        repro_cost = 100.0
        if self.energy < repro_cost + 20.0:
            return None
            
        self.energy -= repro_cost
        self.offspring_count += 1
        
        child_id = f"Org_{self.id}_{self.offspring_count}"
        # 产生偏移位置
        offset = np.random.uniform(-30, 30, 2)
        child = self.__class__(
            organism_id=child_id,
            position=tuple(self.position + offset),
            energy=65.0,
            generation=self.generation + 1
        )
        
        # 复制并变异组件
        for comp in self.components.values():
            if hasattr(comp, 'mutate'):
                mutated_comp = comp.mutate()
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
            self.energy -= amount
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

        self.energy = min(self.energy + amount, self.max_energy)

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
