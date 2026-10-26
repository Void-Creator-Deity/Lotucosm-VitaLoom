"""组件基类 Component：继承 EntityBase，管理信号、连接与 Inspector 可检视属性。

架构数据流::

    Organism 挂载 Component → process_signal / act → Connection.update
    register_property → Inspector get_inspectable_properties

具体传感器/执行器在 builtin/components；本模块为统一契约。
"""
from typing import Optional, Dict, Any, List, TYPE_CHECKING, Mapping
import numpy as np
from core.Lotucosm.entity import EntityBase

# 使用TYPE_CHECKING避免循环导入
if TYPE_CHECKING:
    from core.Lotucosm.entity import EntityBase


class Component(EntityBase):
    """生物体组件父类：信号、连接、遗传元数据与 Inspector 属性注册。

    生命周期:
        构造 → on_attach → update（含 connections）→ mutate 繁殖
    """

    def __init__(self, component_id: Optional[str] = None, **kwargs: Any):
        """初始化组件 ID、organism_id、信号状态与遗传字段。

        职责:
            调用 EntityBase.__init__ 并设置 component_type、connections、activation 等。

        时机:
            ComponentFactory 或序列化重建时。

        不变量:
            state 为 idle|active|processing 之一（约定）；location 默认 internal。

        排错:
            Inspector 无属性 → 须 register_property 而非仅 setattr。
        """
        # 初始化父类
        super().__init__(entity_id=component_id, **kwargs)

        # 组件特有属性
        self.organism_id: Optional[str] = kwargs.get('organism_id', None)
        # Optional explicit SR structural identity.  Never infer this from
        # component type, list order, or display name.
        self.sr_component_id: Optional[str] = kwargs.get('sr_component_id', None)
        if self.sr_component_id is not None:
            if not isinstance(self.sr_component_id, str) or not self.sr_component_id.strip():
                raise ValueError("sr_component_id must be a non-empty string when provided")
            self.sr_component_id = self.sr_component_id.strip()
        self.component_type: str = kwargs.get('component_type', 'base')

        # 连接管理
        self.connections: List[Any] = []

        # 信号处理
        self.activation: float = 0.0
        self.state: str = 'idle'  # idle, active, processing
        self.input_signals: Dict[str, float] = {}
        self.output_signal: float = 0.0

        # 遗传特性
        self.genetic_strength: float = kwargs.get('genetic_strength', 1.0)
        self.mutation_rate: float = kwargs.get('mutation_rate', 0.01)

        # 位置属性
        self.location: str = kwargs.get('location', 'internal')  # internal, external, both
        self.acquired: bool = kwargs.get('acquired', False)
        self.congenital: bool = kwargs.get('congenital', True)
        self.attach_point: Optional[str] = kwargs.get('attach_point', None)
        self.energy_consumption: float = float(kwargs.get('energy_consumption', 0.0))

        # 属性定义 (用于 Inspector 显示)
        self._inspectable_properties: Dict[str, Dict[str, Any]] = {}

    def restore_persistent_state(self, state: Mapping[str, Any]) -> None:
        """原子恢复序列化字段；由 serializer hydration 调用。

        这是组件状态的唯一持久化恢复入口。先完整校验输入，再一次性写入，
        避免 legacy/pond serializer 在字段中途失败时留下半恢复实例。
        未知字段不会被写入，以保持 schema 向后兼容且避免污染组件对象。
        """
        if not isinstance(state, Mapping):
            raise TypeError("component state must be a mapping")

        required = ("location", "congenital", "acquired", "attach_point", "energy_consumption")
        missing = [name for name in required if name not in state]
        if missing:
            raise ValueError(f"component state missing fields: {', '.join(missing)}")
        location = state["location"]
        if not isinstance(location, str):
            raise TypeError("component location must be a string")
        try:
            energy_consumption = float(state["energy_consumption"])
        except (TypeError, ValueError) as exc:
            raise TypeError("component energy_consumption must be numeric") from exc
        if not np.isfinite(energy_consumption) or energy_consumption < 0:
            raise ValueError("component energy_consumption must be finite and non-negative")

        updates: Dict[str, Any] = {
            "location": location,
            "congenital": state["congenital"],
            "acquired": state["acquired"],
            "attach_point": state["attach_point"],
            "energy_consumption": energy_consumption,
        }
        if "sr_component_id" in state:
            sr_component_id = state["sr_component_id"]
            if sr_component_id is not None and (
                not isinstance(sr_component_id, str) or not sr_component_id.strip()
            ):
                raise ValueError("component sr_component_id must be a non-empty string or null")
            updates["sr_component_id"] = (
                None if sr_component_id is None else sr_component_id.strip()
            )
        for name in (
            "is_sensor", "sensor_sensitivity", "sense_range",
            "is_actuator", "actuator_strength", "actuation_speed",
            "is_hybrid", "mode",
            "is_membrane", "permeability", "thickness", "surface_area",
            "is_pvaec_engine", "learning_rate", "exploration_rate",
            "success_threshold", "associations",
        ):
            if name in state:
                updates[name] = state[name]
        if "success_threshold" in updates:
            updates["success_threshold"] = float(updates["success_threshold"])
            if not np.isfinite(updates["success_threshold"]):
                raise ValueError("component success_threshold must be finite")
        if "associations" in updates and not isinstance(updates["associations"], dict):
            raise TypeError("component associations must be a dict")

        self.__dict__.update(updates)

    def register_property(self, name: str, value: Any, prop_type: type, **kwargs):
        """注册 Inspector 可编辑属性。

        职责:
            setattr + 记录 type 与 min/max/step/readonly 元数据。

        时机:
            组件 __init__ 或工厂创建后。

        不变量:
            name 唯一；后续修改值直接 setattr(self, name)。

        排错:
            Inspector 不显示 → 未调用 register_property 或 name 与属性不同步。
        """
        setattr(self, name, value)
        self._inspectable_properties[name] = {
            'type': prop_type,
            'attributes': kwargs
        }

    def get_inspectable_properties(self) -> Dict[str, Any]:
        """返回已注册属性当前值与元数据。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        properties = {}
        for name, info in self._inspectable_properties.items():
            properties[name] = {
                'value': getattr(self, name),
                'type': info['type'],
                'attributes': info['attributes']
            }
        return properties

    def on_attach(self, entity: 'EntityBase'):
        """脚本式附着钩子；组件默认空实现。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        pass

    def on_detach(self, entity: 'EntityBase'):
        """脱离钩子；组件默认空实现。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        pass

    def process_signal(self, signal: float) -> float:
        """基础信号处理：写入 input_signals['last'] 并透传 output_signal。

        职责:
            子类覆写实现滤波/激活函数。

        时机:
            Connection 或 PVAEC 管线传递信号时。

        不变量:
            返回 float 与 output_signal 一致。

        排错:
            信号恒等 → 确认未覆写本方法且上游 signal 有变化。
        """
        # 基础信号处理：直接传递
        self.input_signals['last'] = signal
        self.output_signal = signal
        return self.output_signal

    def activate(self) -> None:
        """state='active'，activation=1。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self.state = 'active'
        self.activation = 1.0

    def deactivate(self) -> None:
        """state='idle'，activation=0。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self.state = 'idle'
        self.activation = 0.0

    def update(self, delta_time: float = 1.0) -> None:
        """先 EntityBase.update，再更新各 connection。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        super().update(delta_time)

        # 更新连接
        for connection in self.connections:
            if hasattr(connection, 'update'):
                connection.update(delta_time)

    def add_connection(self, connection: Any) -> None:
        """添加连接对象（去重）。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if connection not in self.connections:
            self.connections.append(connection)

    def remove_connection(self, connection: Any) -> None:
        """移除连接。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if connection in self.connections:
            self.connections.remove(connection)

    def mutate(self, *, randomness_rng=None) -> Any:
        """生成同类型新组件，尺寸与 genetic_strength 微扰。

        职责:
            供演化/繁殖复制组件拓扑时使用。

        时机:
            builtin 变异流水线。

        不变量:
            新 id 后缀 _mutated；organism_id 保留。

        排错:
            子类行为丢失 → 须覆写 mutate 调用 super 或完全自定义。
        """
        from core.Lotucosm.randomness import random_uniform
        if randomness_rng is None:
            raise RuntimeError("Component mutation requires an explicit randomness owner")

        # 基础变异：创建一个相同类型的新组件
        new_component = self.__class__(
            component_id=f"{self.id}_mutated",
            organism_id=self.organism_id,
            position=self.position.copy(),
            size=self.size * (1 + random_uniform(randomness_rng, -0.1, 0.1)),
            component_type=self.component_type
        )

        # 随机调整遗传强度
        new_component.genetic_strength = self.genetic_strength * (
            1 + random_uniform(randomness_rng, -0.05, 0.05)
        )

        return new_component

    def get_status(self) -> Dict[str, Any]:
        """合并 EntityBase 状态与组件专有字段。

        
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
            'component_type': self.component_type,
            'activation': self.activation,
            'state': self.state,
            'connection_count': len(self.connections),
            'genetic_strength': self.genetic_strength,
            'location': self.location,
            'acquired': self.acquired,
            'congenital': self.congenital
        })
        return status

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, type={self.component_type}, state={self.state})"
