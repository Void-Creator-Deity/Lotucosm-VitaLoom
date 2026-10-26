"""宇宙单例 Cosmos：多莲池（世界）注册、活跃世界指针与全局系统。

架构数据流::

    get_cosmos() → create_world / set_active_world → Pond.update
    ScriptBase.instantiate 回退 get_active_world()

历史坑::

    - create_world 传入 Pond(id=world_id) 与 Pond(name=...)  kwargs 并存，调用方须与 Pond.__init__ 对齐
"""
import sys

# 修复 Windows 控制台编码问题 (解决 Emoji 导致的 UnicodeEncodeError)
if sys.platform == 'win32':
    import io
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from typing import Dict, List, Any, Optional
import threading
from core.VitaLoom.core.logger import get_logger

logger = get_logger("Cosmos")


class Cosmos:
    """线程安全单例：管理 worlds、active_world_id、全局 systems 与简易 event_bus。

    生命周期:
        首次 get_cosmos/Cosmos() 初始化 → 运行时 register/update → cleanup 销毁世界
    """

    _instance: Optional['Cosmos'] = None
    _lock = threading.Lock()

    def __new__(cls):
        """双重检查锁定单例构造。"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
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
        if self._initialized:
            return

        self._initialized = True

        # 管理所有莲池
        self.worlds: Dict[str, Any] = {}  # {世界ID: 莲池实例}
        self.active_world_id: Optional[str] = None  # 当前激活的世界ID

        # 全局系统
        self.systems: Dict[str, Any] = {}  # {系统名称: 系统实例}

        # 全局事件总线
        self.event_bus: List[Any] = []

        # 宇宙配置
        self.config: Dict[str, Any] = {
            'max_worlds': 10,
            'auto_save': True,
            'auto_save_interval': 1000
        }

        logger.info("宇宙单例已初始化")

    def create_world(self, world_id: str, **kwargs) -> Any:
        """创建并注册新莲池世界。

        职责:
            构造 Pond 实例写入 worlds[world_id]。

        时机:
            启动器/编辑器新建场景或切换多世界实验时。

        不变量:
            world_id 不可重复，否则 ValueError。

        排错:
            Pond 构造参数错误 → 查 kwargs 是否与 pond.Pond.__init__ 一致；见 lotucosm_core_troubleshooting.md。
        """
        if world_id in self.worlds:
            raise ValueError(f"世界ID {world_id} 已存在")

        from core.Lotucosm.pond import Pond
        world = Pond(id=world_id, **kwargs)
        self.worlds[world_id] = world

        logger.info("创建新世界: %s", world_id)
        return world

    def get_world(self, world_id: str) -> Optional[Any]:
        """按 ID 获取莲池引用。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        return self.worlds.get(world_id)

    def set_active_world(self, world_id: str) -> bool:
        """设置当前活跃世界 ID。

        职责:
            更新 active_world_id 供 get_active_world 使用。

        时机:
            编辑器切换场景、脚本 instantiate 回退前应由宿主设置。

        不变量:
            world_id 必须已存在于 worlds。

        排错:
            返回 False → ID 未注册；脚本 instantiate 将得到 None。
        """
        if world_id not in self.worlds:
            return False

        self.active_world_id = world_id
        logger.info("激活世界: %s", world_id)
        return True

    def get_active_world(self) -> Optional[Any]:
        """返回当前活跃莲池；无活跃 ID 时 None。

        职责:
            按 active_world_id 从 worlds 字典取当前活跃世界实例。

        排错:
            脚本无法生成实体 → 先 set_active_world 或给 entity.pond 赋值。
        """
        if self.active_world_id:
            return self.worlds.get(self.active_world_id)
        return None

    def remove_world(self, world_id: str) -> bool:
        """移除世界；若其为活跃世界则清空 active_world_id。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if world_id not in self.worlds:
            return False

        if self.active_world_id == world_id:
            self.active_world_id = None

        del self.worlds[world_id]
        logger.info("移除世界: %s", world_id)
        return True

    def register_system(self, system_name: str, system: Any) -> None:
        """注册全局命名系统（如物理、演化调度）。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self.systems[system_name] = system
        logger.info("注册全局系统: %s", system_name)

    def get_system(self, system_name: str) -> Optional[Any]:
        """按名称获取全局系统。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        return self.systems.get(system_name)

    def update(self) -> None:
        """遍历所有世界的 update 及带 update 方法的全局 systems。

        职责:
            驱动全部 world 与全局 system 的一帧 tick。

        时机:
            主循环或编辑器模拟 tick 顶层驱动。

        不变量:
            各 world.update 无顺序保证（dict 迭代顺序）。

        排错:
            某世界不 tick → 该世界是否仍在 worlds 且 update 未被外层跳过。
        """
        for world in self.worlds.values():
            world.update()

        for system in self.systems.values():
            if hasattr(system, 'update'):
                system.update()

    def get_status(self) -> Dict[str, Any]:
        """返回世界/系统数量及 ID 列表快照。

        
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
            'world_count': len(self.worlds),
            'active_world': self.active_world_id,
            'system_count': len(self.systems),
            'worlds': list(self.worlds.keys()),
            'systems': list(self.systems.keys())
        }

    def broadcast_event(self, event: Dict[str, Any]) -> None:
        """追加 event_bus 并对各世界调用 handle_event（若存在）。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self.event_bus.append(event)
        for world in self.worlds.values():
            if hasattr(world, 'handle_event'):
                world.handle_event(event)

    def cleanup(self) -> None:
        """移除所有世界并清空 systems 与 event_bus。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        logger.info("清理宇宙资源...")
        for world_id in list(self.worlds.keys()):
            self.remove_world(world_id)
        self.systems.clear()
        self.event_bus.clear()
        logger.info("宇宙资源清理完成")


def get_cosmos() -> Cosmos:
    """获取 Cosmos 单例（与直接 Cosmos() 等价）。

    排错:
        多线程下仍安全；勿在测试中假设每次为新实例。
    """
    return Cosmos()
