"""莲池环境 Pond：生物体、漂浮组件、资源与子系统每帧 tick。

架构数据流（单帧）::

    update: time++ → physics_engine → floating/assembly/resource
        → organisms.update → root_entities.update → floating_components
        → generate_resources →（可选）EvolutionRunner.apply_generation

    time：物理帧计数；iteration：世代计数（EvolutionRunner 递增）

历史坑::

    - organisms 与 root_entities 双轨并存，add_organism 会同步 root_entities
    - evolution_generation_interval <= 0 视为未配置，避免取模除零
"""
from typing import Dict, List, Any, TYPE_CHECKING
import math
import numpy as np
import copy
from core.VitaLoom.core.logger import get_logger

# 使用TYPE_CHECKING避免循环导入
if TYPE_CHECKING:
    from builtin.components.components_base import ComponentBase
    from builtin.entity_types.organism import Organism


logger = get_logger("Pond")


class Pond:
    """数字生命演化莲池：实体注册、资源、物理/漂浮/组装子系统与可选世代演化。

    生命周期:
        __init__ → initialize_pond → 每帧 update → save_pond/load_pond 持久化
    """

    def _bind_subsystem_owner(self, subsystem: Any) -> Any:
        """Bind a newly attached subsystem to this Pond's randomness owner."""
        if subsystem is None:
            return None
        setter = getattr(subsystem, "set_randomness_owner", None)
        if callable(setter):
            setter(self.randomness_rng)
        elif hasattr(subsystem, "randomness_rng"):
            subsystem.randomness_rng = self.randomness_rng
        if hasattr(subsystem, "randomness_owner_mode"):
            subsystem.randomness_owner_mode = "runtime"
        return subsystem

    @property
    def floating_system(self) -> Any:
        return self._floating_system

    @floating_system.setter
    def floating_system(self, value: Any) -> None:
        self._floating_system = self._bind_subsystem_owner(value)

    @property
    def assembly_system(self) -> Any:
        return self._assembly_system

    @assembly_system.setter
    def assembly_system(self, value: Any) -> None:
        self._assembly_system = self._bind_subsystem_owner(value)

    @property
    def resource_manager(self) -> Any:
        return self._resource_manager

    @resource_manager.setter
    def resource_manager(self, value: Any) -> None:
        self._resource_manager = self._bind_subsystem_owner(value)

    @property
    def pvaec_orchestrator(self) -> Any:
        return self._pvaec_orchestrator

    @pvaec_orchestrator.setter
    def pvaec_orchestrator(self, value: Any) -> None:
        self._pvaec_orchestrator = self._bind_subsystem_owner(value)

    def __init__(self, **kwargs: Any):
        """构造莲池，默认调用 initialize_pond。

        职责:
            解析 name/size/initial_*、evolution_generation_interval、pvaec_orchestrator 等。
            `initialize=False` 供持久化恢复先建立空容器，再由存档 hydration。

        时机:
            Cosmos.create_world、模拟器启动或 PondSerializer 反序列化后替换状态。

        不变量:
            time 从 0 起；iteration 为世代计数；interval<=0 时 evolution_generation_interval 为 None。

        排错:
            世代从不触发 → interval 须 >0 且 pvaec_orchestrator 非空；见 lotucosm_core_troubleshooting.md。
        """
        self.name: str = kwargs.get('name', '演化实验场')  # 莲池名称
        self.size: tuple[float, float] = kwargs.get('size', (1200, 800))  # 莲池大小
        self.randomness_rng: Any = kwargs.get(
            "randomness_rng", np.random.default_rng(12345)
        )
        self.randomness_owner_mode = "runtime"
        self._worldbridge_random_draw_count = 0
        self._worldbridge_input_events_last_tick: list[dict[str, Any]] = []
        if self.randomness_rng is None:
            self.randomness_rng = np.random.default_rng(12345)
        if not hasattr(self.randomness_rng, "random"):
            raise TypeError("randomness_rng must expose random()")

        # time：每帧 tick（update 开头自增）；iteration：仅世代边界由 EvolutionRunner 递增
        self.time: int = 0
        self.simulation_time: float = 0.0

        # 生物体管理 (保留旧的字典以防兼容，但主推层级系统)
        self.organisms: Dict[str, Any] = {}  # 生物体字典，{生物体ID: 生物体实例}
        
        # 层次结构实体管理 (Unity-like)
        self.root_entities: List[Any] = []

        # 组件管理
        self.floating_components: List[Any] = []  # 漂浮组件列表
        self.initial_components: int = kwargs.get('initial_components', 50)  # 初始漂浮组件数量
        self.initial_organisms: int = kwargs.get('initial_organisms', 10)  # 初始生物体数量
        self.component_variety: str = kwargs.get('component_variety', 'all')  # 组件多样性类型

        # 资源管理
        self.resources: Dict[str, List[Dict[str, Any]]] = {
            'food': [],  # 食物粒子
            'energy': []  # 能量粒子
        }

        # 物理引擎
        self.physics_engine: Any = None  # 物理引擎实例

        # 漂浮系统
        self._floating_system: Any = None  # 漂浮系统实例

        # 自组装系统
        self._assembly_system: Any = None  # 自组装系统实例

        # 资源管理器
        self._resource_manager: Any = None  # 资源管理器实例

        # 序列化相关属性（世代计数，非物理帧）
        self.iteration: int = 0
        self.max_population: int = kwargs.get('max_population', 100)
        self.environmental_factors: Dict[str, Any] = kwargs.get('environmental_factors', {})
        self.statistics: Dict[str, Any] = kwargs.get('statistics', {})

        _interval = kwargs.get("evolution_generation_interval")
        if _interval is not None:
            try:
                iv = int(_interval)
            except (TypeError, ValueError):
                iv = 0
            # <=0 视为未配置，避免 update 中 time % interval 除零或语义无效
            self.evolution_generation_interval: int | None = iv if iv > 0 else None
        else:
            self.evolution_generation_interval = None
        self._pvaec_orchestrator: Any = None
        self.pvaec_orchestrator = kwargs.get('pvaec_orchestrator')

        # 恢复路径需要保留配置元数据，但不能先生成会被丢弃的默认状态。
        if kwargs.get("initialize", True):
            self.initialize_pond()

    def apply_worldbridge_input_events(self, events: Any) -> None:
        """Consume the canonical SR input batch at the PS handoff boundary."""
        from core.Lotucosm.runtime.world_bridge_input_sequence import (
            validate_worldbridge_input_events,
        )

        if events is None:
            normalized: list[dict[str, Any]] = []
        elif isinstance(events, list):
            normalized = copy.deepcopy(events)
        else:
            raise TypeError("WorldBridge input events must be a list")
        validation = validate_worldbridge_input_events(
            normalized,
            last_sequence=(int(normalized[0]["sequence"]) - 1 if normalized else 0),
            pause_reset_epoch=(
                int(normalized[0]["pause_reset_epoch"]) if normalized else 0
            ),
        )
        if normalized and not validation["valid"]:
            raise ValueError("invalid WorldBridge input batch: " + ",".join(validation["errors"]))
        self._worldbridge_input_events_last_tick = normalized

    @property
    def worldbridge_input_events_last_tick(self) -> list[dict[str, Any]]:
        """Return a copy-isolated canonical input batch for PS consumers."""
        return copy.deepcopy(self._worldbridge_input_events_last_tick)

    def capture_worldbridge_live_transaction_state(self) -> Any:
        """Capture every mutable owner reachable from this Pond in-process."""
        from core.Lotucosm.runtime.pond_live_transaction_state import (
            capture_pond_live_transaction_state,
        )

        return capture_pond_live_transaction_state(self)

    def restore_worldbridge_live_transaction_state(self, snapshot: Any) -> str:
        """Restore an identity-bound Pond snapshot and verify its fresh digest."""
        from core.Lotucosm.runtime.pond_live_transaction_state import (
            restore_pond_live_transaction_state,
        )

        return restore_pond_live_transaction_state(self, snapshot)

    def _refresh_physics_targets(self) -> None:
        """Bind the physics adapter to the Pond's current organism owners."""
        physics_engine = self.physics_engine
        register_body = getattr(physics_engine, "register_body", None)
        targets = getattr(physics_engine, "_targets", None)
        if not callable(register_body) or targets is None:
            return
        targets.clear()
        for organism in list(self.organisms.values()):
            register_body(organism)

    def initialize_pond(self):
        """创建初始漂浮组件、资源与生物体（构造末尾自动调用）。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        logger.info("初始化莲池: %s, 大小: %s", self.name, self.size)

        # 创建初始漂浮组件
        self.create_initial_components()

        # 创建初始资源
        self.create_initial_resources()

        # 创建初始生物体
        self.create_initial_organisms()

    def create_initial_organisms(self):
        """创建初始生物体。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        from builtin.entity_types.intelligent_organism import IntelligentOrganism

        for i in range(self.initial_organisms):
            # 随机位置
            position = self._random_array(2) * self.size

            # 创建智能生物体
            organism_id = f"organism_{i + 1}"
            organism = IntelligentOrganism(
                organism_id = organism_id,
                position = tuple(position),
                name = f"初始生物体_{i + 1}"
            )

            # 添加到莲池
            self.add_organism(organism)

    def create_initial_components(self):
        """创建初始漂浮组件。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        import numpy as np
        from builtin.components.component_factory import ComponentFactory

        factory = ComponentFactory()
        n = max(0, int(self.initial_components))
        for i in range(n):
            pos = self._random_array(2) * np.array(self.size, dtype=float)
            comp = factory.create_component(
                "ComponentBase",
                f"float_comp_{i}",
                organism_id="",
                name=f"漂浮组件_{i}",
                position=tuple(pos.tolist()),
            )
            try:
                comp.acquired = True
                comp.congenital = False
            except Exception as e:
                logger.debug("漂浮组件属性初始化跳过: %s", e)
            self.add_floating_component(comp)

    def create_initial_resources(self):
        """创建初始资源。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 创建初始食物粒子
        for _ in range(200):
            food_position = self._random_array(2) * self.size
            self.resources['food'].append({
                'position': food_position,
                'amount': self._random_uniform(1, 5),
                'type': 'food'
            })

        # 创建初始能量粒子
        for _ in range(100):
            energy_position = self._random_array(2) * self.size
            self.resources['energy'].append({
                'position': energy_position,
                'amount': self._random_uniform(1, 3),
                'type': 'energy'
            })

    def update(self, delta_time: float = 1.0) -> None:
        """每帧推进：子系统、生物体、根实体、资源生成与可选世代演化。

        职责:
            time 自增；驱动 physics/floating/assembly/resource；移除 dead 生物体。

        时机:
            Cosmos.update 或模拟主循环每帧。

        不变量:
            evolution 仅在 time % interval == 0 且 organisms 非空时触发。

        排错:
            人口不更新 → EvolutionRunner 条件未满足；物理未动 → physics_engine 未注入。
        """
        # The bridge supplies the shared simulation delta; legacy callers retain
        # the historical one-unit default.
        if isinstance(delta_time, bool) or not isinstance(delta_time, (int, float)):
            raise TypeError("delta_time must be a finite positive number")
        delta = float(delta_time)
        if not math.isfinite(delta) or delta <= 0.0:
            raise ValueError("delta_time must be a finite positive number")
        self.time += 1
        self.simulation_time += delta

        # 更新物理引擎
        if self.physics_engine:
            self._refresh_physics_targets()
            self.physics_engine.update()

        # 更新漂浮系统
        if self.floating_system:
            if self.randomness_rng is not None and hasattr(self.floating_system, "randomness_rng"):
                self.floating_system.randomness_rng = self.randomness_rng
            self.floating_system.update()

        # 更新自组装系统
        if self.assembly_system:
            if self.randomness_rng is not None and hasattr(self.assembly_system, "randomness_rng"):
                self.assembly_system.randomness_rng = self.randomness_rng
            self.assembly_system.update(self.floating_components)

        # 更新资源管理器
        if self.resource_manager:
            if self.randomness_rng is not None and hasattr(self.resource_manager, "randomness_rng"):
                self.resource_manager.randomness_rng = self.randomness_rng
            self.resource_manager.update()
        if self.pvaec_orchestrator is not None and self.randomness_rng is not None:
            setter = getattr(self.pvaec_orchestrator, "set_randomness_owner", None)
            if callable(setter):
                setter(self.randomness_rng)
            else:
                self.pvaec_orchestrator.randomness_rng = self.randomness_rng

        # 更新所有生物体 (传统的)
        for organism in list(self.organisms.values()):
            organism.update(environment=self)

            # 检查生物体是否死亡
            if getattr(organism, 'dead', False):
                self.remove_organism(organism.id)

        # 更新所有根实体及其子实体 (Unity-like)
        for entity in list(self.root_entities):
            entity.update(delta)

        # 更新所有漂浮组件
        for component in self.floating_components:
            component.update()

        # 生成新资源
        self.generate_resources()

        if (
            self.evolution_generation_interval
            and self.pvaec_orchestrator
            and self.organisms
            and self.time % int(self.evolution_generation_interval) == 0
            and not getattr(self, "_evolution_in_progress", False)
        ):
            from builtin.systems.evolution_runner import EvolutionRunner

            self._evolution_in_progress = True
            try:
                EvolutionRunner.apply_generation(self, self.pvaec_orchestrator)
            finally:
                self._evolution_in_progress = False

    def add_organism(self, organism: 'Organism') -> bool:
        """注册生物体到 organisms 并 add_entity（ID 重复返回 False）。

        职责:
            将 Organism 写入 organisms 映射并同步注册为莲池根实体。

        排错:
            返回 False → organism.id 已存在。
        """
        if organism.id in self.organisms:
            return False  # 生物体ID已存在

        organism.pond = self
        if self.randomness_rng is not None:
            setter = getattr(organism, "set_randomness_owner", None)
            if callable(setter):
                setter(self.randomness_rng)
            elif hasattr(organism, "randomness_rng"):
                organism.randomness_rng = self.randomness_rng
        self.organisms[organism.id] = organism
        self.add_entity(organism) # 同时注册为根实体
        logger.info("添加生物体到莲池: %s", organism.id)
        return True

    def remove_organism(self, organism_id: str) -> bool:
        """从莲池中移除生物体。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if organism_id in self.organisms:
            organism = self.organisms[organism_id]
            if organism in self.root_entities:
                self.root_entities.remove(organism)
            del self.organisms[organism_id]
            logger.info("从莲池中移除生物体: %s", organism_id)
            return True
        return False

    def add_entity(self, entity: 'EntityBase') -> None:
        """添加根实体到莲池。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if entity not in self.root_entities:
            self.root_entities.append(entity)
            logger.info("添加根实体到莲池: %s", entity.id)

    def remove_entity(self, entity: 'EntityBase') -> None:
        """从莲池中移除根实体。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if entity in self.root_entities:
            self.root_entities.remove(entity)
            logger.info("从莲池中移除根实体: %s", entity.id)

    def get_nearby_components(self, position: np.ndarray, radius: float) -> List['ComponentBase']:
        """获取附近漂浮组件。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        nearby: List['ComponentBase'] = []
        for component in self.floating_components:
            distance = np.linalg.norm(component.position - position)
            if distance <= radius:
                nearby.append(component)

        return nearby

    def replace_floating_components(self, components: List[Any]) -> None:
        """替换兼容层漂浮组件并保持公开 list identity。"""
        if components is None:
            components = []
        if not isinstance(components, list):
            components = list(components)
        self.floating_components[:] = components
        if self.randomness_rng is not None:
            for component in self.floating_components:
                if hasattr(component, "randomness_rng"):
                    component.randomness_rng = self.randomness_rng

    def add_floating_component(self, component: 'ComponentBase'):
        """添加漂浮组件到莲池。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if self.randomness_rng is not None and hasattr(component, "randomness_rng"):
            component.randomness_rng = self.randomness_rng
        self.floating_components.append(component)

    def remove_floating_component(self, component: 'ComponentBase'):
        """从莲池中移除漂浮组件。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if component in self.floating_components:
            self.floating_components.remove(component)

    def generate_resources(self):
        """生成新资源。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 每100次迭代生成新资源
        if self.time % 100 == 0:
            # 生成食物粒子
            food_position = self._random_array(2) * self.size
            self.resources['food'].append({
                'position': food_position,
                'amount': self._random_uniform(1, 5),
                'type': 'food'
            })

            # 生成能量粒子
            energy_position = self._random_array(2) * self.size
            self.resources['energy'].append({
                'position': energy_position,
                'amount': self._random_uniform(1, 3),
                'type': 'energy'
            })

    def _random_array(self, size: int) -> np.ndarray:
        """Draw from the explicit PS owner; a cleared owner is a hard error."""
        if self.randomness_rng is None:
            raise RuntimeError("Pond randomness owner is unavailable")
        value = np.asarray(self.randomness_rng.random(size), dtype=float)
        self._worldbridge_random_draw_count += int(np.asarray(value).size)
        return value

    def _random_uniform(self, low: float, high: float) -> float:
        if self.randomness_rng is None:
            raise RuntimeError("Pond randomness owner is unavailable")
        value = float(self.randomness_rng.uniform(low, high))
        self._worldbridge_random_draw_count += 1
        return value

    def get_nearby_resources(self, position: np.ndarray, radius: float, resource_type: str = 'all') -> List[Dict[str, Any]]:
        """获取附近资源。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        nearby_resources: List[Dict[str, Any]] = []

        if resource_type in ['all', 'food']:
            for food in self.resources['food']:
                distance = np.linalg.norm(food['position'] - position)
                if distance <= radius:
                    nearby_resources.append(food)

        if resource_type in ['all', 'energy']:
            for energy in self.resources['energy']:
                distance = np.linalg.norm(energy['position'] - position)
                if distance <= radius:
                    nearby_resources.append(energy)

        return nearby_resources

    def get_nearby_entities(self, position: np.ndarray, radius: float) -> List[Any]:
        """返回感知半径内的生物体与漂浮组件（供 Sensor.sense 使用）。

        职责:
            聚合 organisms 与 floating_components 中在 radius 内的实体。

        时机:
            Organism.update / PVAEC 感知阶段传入 self（莲池）作 environment。

        不变量:
            返回项须具 `.position` ndarray；不含已死亡生物体。

        排错:
            Sensor 报错无此方法 → 确认 environment 为 Pond 而非裸 dict。
        """
        pos = np.asarray(position, dtype=float).reshape(-1)[:2]
        nearby: List[Any] = []
        for organism in list(self.organisms.values()):
            if getattr(organism, "dead", False):
                continue
            op = np.asarray(organism.position, dtype=float).reshape(-1)[:2]
            if float(np.linalg.norm(op - pos)) <= float(radius):
                nearby.append(organism)
        for comp in self.floating_components:
            cp = getattr(comp, "position", None)
            if cp is None:
                continue
            cp_arr = np.asarray(cp, dtype=float).reshape(-1)[:2]
            if float(np.linalg.norm(cp_arr - pos)) <= float(radius):
                nearby.append(comp)
        return nearby

    def check_contact(self, position: np.ndarray, radius: float) -> Dict[str, Any]:
        """检查接触。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        contact_info: Dict[str, Any] = {
            'contact': False,
            'pressure': 0.0,
            'objects': []
        }

        # 检查与其他生物体的接触
        for organism in list(self.organisms.values()):
            if organism.id != getattr(self, 'current_organism_id', ''):
                distance = np.linalg.norm(organism.position - position)
                if distance < radius + getattr(organism.membrane, 'radius', 30):
                    contact_info['contact'] = True
                    contact_info['pressure'] += 0.5
                    contact_info['objects'].append({'type': 'organism', 'id': organism.id})

        # 检查与资源的接触
        for resource in self.resources['food'] + self.resources['energy']:
            distance = np.linalg.norm(resource['position'] - position)
            if distance < radius + 5:  # 资源半径简化处理
                contact_info['contact'] = True
                contact_info['pressure'] += 0.2
                contact_info['objects'].append({'type': resource['type']})

        return contact_info

    def get_light_intensity(self, position: np.ndarray) -> float:
        """获取光照强度。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 简单的光照模型，实际项目中可能需要更复杂的光照系统
        return 0.8  # 默认光照强度

    def get_temperature(self, position: np.ndarray) -> float:
        """获取温度。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 简单的温度模型
        return 25.0  # 默认温度

    def get_pond_status(self) -> Dict[str, Any]:
        """获取莲池状态。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        return {
            'name': self.name,
            'size': self.size,
            'time': self.time,
            'organism_count': len(self.organisms),
            'floating_component_count': len(self.floating_components),
            'food_count': len(self.resources['food']),
            'energy_count': len(self.resources['energy'])
        }

    def save_pond(self, save_path: str) -> str:
        """保存莲池到 JSON（委托 PondSerializer）。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        from builtin.systems.pond_serializer import PondSerializer

        ok = PondSerializer(save_format="json").save_pond(self, save_path)
        if ok:
            logger.info("保存莲池到: %s", save_path)
            return f"pond_{self.time}"
        logger.warning("保存莲池失败: %s", save_path)
        return ""

    def load_pond(self, load_path: str) -> bool:
        """从 JSON 加载到当前实例并 _apply_loaded_pond_state。

        职责:
            经 PondSerializer 反序列化并覆盖当前莲池运行时状态。

        排错:
            False → PondSerializer 失败；加载后实体无 pond → 查 _apply_loaded_pond_state。
        """
        from builtin.systems.pond_serializer import PondSerializer

        loaded = PondSerializer(save_format="json").load_pond(
            load_path,
            type(self),
            randomness_rng=self.randomness_rng,
        )
        if loaded is None:
            logger.warning("加载莲池失败: %s", load_path)
            return False
        self._apply_loaded_pond_state(loaded)
        logger.info("从 %s 加载莲池", load_path)
        return True




    def _apply_loaded_pond_state(self, loaded: "Pond") -> None:
        """合并反序列化莲池状态；回填 org.pond 与 root_entities。

        排错:
            模拟中实体找不到环境 → 确认本方法已执行且 organisms 已赋值。
        """
        self.name = loaded.name
        randomness_rng = self.randomness_rng
        self.size = loaded.size
        self.time = getattr(loaded, "time", 0)
        self.simulation_time = float(getattr(loaded, "simulation_time", 0.0))
        self.iteration = loaded.iteration
        self.max_population = loaded.max_population
        self.initial_organisms = loaded.initial_organisms
        self.initial_components = loaded.initial_components
        self.component_variety = loaded.component_variety
        self.evolution_generation_interval = loaded.evolution_generation_interval
        self.environmental_factors = loaded.environmental_factors
        self.statistics = loaded.statistics
        self.organisms = loaded.organisms
        self.set_randomness_owner(randomness_rng)
        self.root_entities = list(self.organisms.values())
        self._refresh_physics_targets()
        for org in self.organisms.values():
            if hasattr(org, "pond"):
                org.pond = self
        sources = getattr(loaded, "_loaded_pond_sources", None)
        if sources is not None and self.resource_manager:
            self.resources = sources["basic_resources"]
            self.resource_manager.resources = sources["managed_resources"]
            self.resource_manager.world_size = self.size
        elif hasattr(loaded, "resources"):
            self.resources = loaded.resources

        if sources is not None and self.floating_system:
            self.replace_floating_components(list(sources["simple_floating_components"]))
            self.floating_system.replace_floating_components(list(sources["managed_floating_components"]))
            restore_sequence = getattr(self.floating_system, "restore_assembly_sequence", None)
            if callable(restore_sequence):
                restore_sequence(sources.get("floating_assembly_sequence"))
            self.floating_system.world_size = self.size
        else:
            self.replace_floating_components(list(getattr(loaded, "floating_components", []) or []))

    def restore_serialized_state_in_place(self, pond_data: Dict[str, Any]) -> None:
        """Atomically replace this Pond's lane-local serialized state.

        The serializer reconstructs a detached candidate first.  This method
        commits only after reconstruction succeeds, so malformed payloads do
        not partially mutate the live Pond.  It does not restore scheduler,
        RNG, plugin/native state, or SR/PS bridge identity.
        """
        from builtin.systems.pond_serializer import PondSerializer

        serializer = PondSerializer(save_format="json")
        required = (
            "name",
            "size",
            "max_population",
            "initial_organisms",
            "iteration",
            "environmental_factors",
            "statistics",
        )
        serializer._require_fields(pond_data, list(required), "pond_data")
        for index, item in enumerate(pond_data.get("organisms", [])):
            if not isinstance(item, dict):
                raise TypeError(f"organisms[{index}] must be an object")
            serializer._require_fields(
                item,
                [
                    "id", "type", "position", "energy", "max_energy", "health",
                    "max_health", "mutation_rate", "inheritance_rate",
                    "energy_consumption_rate", "age", "dead", "velocity",
                    "acceleration", "components",
                ],
                f"organisms[{index}]",
            )
        candidate = serializer.deserialize_pond(
            pond_data,
            type(self),
            randomness_rng=self.randomness_rng,
        )
        if candidate is None:
            raise ValueError("pond serialized state could not be reconstructed")
        previous = self._capture_lane_local_restore_state()
        try:
            self._apply_loaded_pond_state(candidate)
        except Exception:
            self._restore_lane_local_restore_state(previous)
            raise

    def set_randomness_owner(self, randomness_rng: Any = None) -> None:
        """Bind one caller-owned PS RNG to the Pond and reachable PS owners."""
        if randomness_rng is None:
            raise ValueError("Pond randomness owner cannot be cleared")
        if not hasattr(randomness_rng, "random"):
            raise TypeError("randomness_rng must expose random()")
        self.randomness_rng = randomness_rng
        for subsystem in (
            self.floating_system,
            self.assembly_system,
            self.resource_manager,
            self.pvaec_orchestrator,
        ):
            if subsystem is None:
                continue
            self._bind_subsystem_owner(subsystem)
        for component in self.floating_components:
            if hasattr(component, "randomness_rng"):
                component.randomness_rng = randomness_rng
        for organism in self.organisms.values():
            setter = getattr(organism, "set_randomness_owner", None)
            if callable(setter):
                setter(randomness_rng)
            elif hasattr(organism, "randomness_rng"):
                organism.randomness_rng = randomness_rng

    def _capture_lane_local_restore_state(self) -> dict[str, Any]:
        """Capture live references needed to compensate a commit failure."""
        return {
            "name": self.name,
            "size": self.size,
            "time": self.time,
            "iteration": self.iteration,
            "max_population": self.max_population,
            "initial_organisms": self.initial_organisms,
            "initial_components": self.initial_components,
            "component_variety": self.component_variety,
            "evolution_generation_interval": self.evolution_generation_interval,
            "environmental_factors": self.environmental_factors,
            "statistics": self.statistics,
            "organisms": self.organisms,
            "root_entities": self.root_entities,
            "resources": self.resources,
            "floating_components": self.floating_components,
            "floating_components_items": list(self.floating_components),
            "floating_system_components": (
                getattr(self.floating_system, "floating_components", None)
                if self.floating_system is not None else None
            ),
            "floating_system_components_items": (
                list(self.floating_system.floating_components)
                if self.floating_system is not None
                and hasattr(self.floating_system, "floating_components") else None
            ),
            "floating_system_world_size": (
                getattr(self.floating_system, "world_size", None)
                if self.floating_system is not None else None
            ),
            "floating_assembly_sequence": (
                getattr(self.floating_system, "_assembly_sequence", None)
                if self.floating_system is not None else None
            ),
            "resource_manager_resources": (
                getattr(self.resource_manager, "resources", None)
                if self.resource_manager is not None else None
            ),
            "resource_manager_world_size": (
                getattr(self.resource_manager, "world_size", None)
                if self.resource_manager is not None else None
            ),
        }

    def _restore_lane_local_restore_state(self, state: dict[str, Any]) -> None:
        """Restore references captured before a failed in-place commit."""
        for field in (
            "name", "size", "time", "iteration", "max_population",
            "initial_organisms", "initial_components", "component_variety",
            "evolution_generation_interval", "environmental_factors", "statistics",
            "organisms", "root_entities", "resources", "floating_components",
        ):
            setattr(self, field, state[field])
        self.floating_components[:] = state["floating_components_items"]
        if self.floating_system is not None and state["floating_system_components"] is not None:
            self.floating_system.floating_components = state["floating_system_components"]
            if state["floating_system_components_items"] is not None:
                self.floating_system.floating_components[:] = state["floating_system_components_items"]
            if state["floating_system_world_size"] is not None:
                self.floating_system.world_size = state["floating_system_world_size"]
            if state["floating_assembly_sequence"] is not None:
                self.floating_system._assembly_sequence = state["floating_assembly_sequence"]
        if self.resource_manager is not None and state["resource_manager_resources"] is not None:
            self.resource_manager.resources = state["resource_manager_resources"]
            if state["resource_manager_world_size"] is not None:
                self.resource_manager.world_size = state["resource_manager_world_size"]
        for organism in self.organisms.values():
            if hasattr(organism, "pond"):
                organism.pond = self

class LotusPond(Pond):
    """向后兼容别名类，旧序列化/导入路径可继续引用 LotusPond。"""
