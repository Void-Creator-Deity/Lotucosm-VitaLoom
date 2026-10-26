"""系统基类 System：莲池/宇宙中按优先级运行的逻辑处理器父类。

架构数据流::

    Cosmos.register_system / 莲池子系统 → System.update(delta_time) → process_entity

子类在 builtin/systems 中实现具体模拟逻辑；本模块仅定义契约与实体列表管理。
"""
from typing import Dict, Any, List, Optional
from core.VitaLoom.core.logger import get_logger


logger = get_logger("System")


class System:
    """逻辑系统基类：启用开关、优先级、托管实体列表与事件钩子。

    生命周期:
        __init__ → initialize（可选）→ update 每帧 → cleanup 卸载
    """

    def __init__(self, name: str, **kwargs: Any):
        """初始化系统名、enabled、priority 与空 state/entities。

        职责:
            记录配置并打日志。

        时机:
            子类 super().__init__ 或 Cosmos.register_system 构造时。

        不变量:
            priority 数值越小越先执行（约定，由调度方保证）。

        排错:
            系统不运行 → 先查 enabled 与 update 是否被子类实现。
        """
        self.name: str = name
        self.enabled: bool = kwargs.get('enabled', True)
        self.priority: int = kwargs.get('priority', 100)

        # 系统状态
        self.state: Dict[str, Any] = {}
        self.entities: List[Any] = []

        logger.info("初始化系统: %s", self.name)

    def initialize(self) -> None:
        """首次运行前钩子；子类可加载资源或注册监听。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        logger.info("系统初始化: %s", self.name)

    def update(self, delta_time: float = 1.0) -> None:
        """每帧更新；enabled 为 False 时立即返回。

        职责:
            子类应覆写并实现核心逻辑。

        时机:
            Pond.update 或 Cosmos.update 遍历 systems 时。

        不变量:
            基类 update 为空操作。

        排错:
            无效果 → 确认子类覆写而非仅调用 super().update()。
        """
        if not self.enabled:
            return

        # 子类应该实现具体的更新逻辑
        pass

    def process_entity(self, entity: Any) -> None:
        """处理单个实体；子类实现具体规则。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 子类应该实现具体的实体处理逻辑
        pass

    def add_entity(self, entity: Any) -> None:
        """将实体加入本系统托管列表（去重）。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if entity not in self.entities:
            self.entities.append(entity)

    def remove_entity(self, entity: Any) -> None:
        """从托管列表移除实体。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if entity in self.entities:
            self.entities.remove(entity)

    def enable(self) -> None:
        """启用系统。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self.enabled = True
        logger.info("启用系统: %s", self.name)

    def disable(self) -> None:
        """禁用系统。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self.enabled = False
        logger.info("禁用系统: %s", self.name)

    def handle_event(self, event: Dict[str, Any]) -> None:
        """处理事件 dict；子类可覆写。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 子类可以重写此方法来处理特定事件
        pass

    def get_status(self) -> Dict[str, Any]:
        """返回 name/enabled/priority/entity_count 状态快照。

        
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
            'enabled': self.enabled,
            'priority': self.priority,
            'entity_count': len(self.entities)
        }

    def cleanup(self) -> None:
        """清理托管实体与 state。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        logger.info("清理系统: %s", self.name)
        self.entities.clear()
        self.state.clear()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, enabled={self.enabled})"
