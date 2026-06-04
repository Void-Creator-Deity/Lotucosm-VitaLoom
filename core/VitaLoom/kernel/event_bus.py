"""VitaLoom 字符串事件总线（PyQt 信号 + 订阅表），与 `core/api/events` 枚举总线分离。

排错: 订阅无回调 → 事件名是否与发布方一致；勿与 `EventSystem.emit` 混用。
"""

from PyQt6.QtCore import QObject, pyqtSignal
from typing import Callable, Dict, List
from core.VitaLoom.core.logger import get_logger


logger = get_logger("EventBus")


class EventBus(QObject):
    """职责: 插件间 publish/subscribe 与 `event_fired` Qt 信号桥接。
    时机: `EditorKernel.__init__` 创建；插件 `on_load` 后订阅。
    不变量: 回调异常仅打日志，不阻断其余订阅者。
    排错: 无回调 → `subscribe` 事件名；对比 `core/api/event_system.EventBus`。
    """
    
    # 动态信号（使用字符串事件名）
    event_fired = pyqtSignal(str, object)
    
    def __init__(self):
        """EventBus.__init__。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        super().__init__()
        self.subscribers: Dict[str, List[Callable]] = {}
    
    def subscribe(self, event_name: str, callback: Callable):
        """职责: 注册字符串事件名的 Python 回调。
        时机: 插件加载或面板初始化时。
        不变量: 同一 callback 可重复 append，需配对 unsubscribe。
        排错: 回调未触发 → 发布方是否调用 `publish` 而非 API 层 `emit`。
        """
        if event_name not in self.subscribers:
            self.subscribers[event_name] = []
        self.subscribers[event_name].append(callback)
    
    def unsubscribe(self, event_name: str, callback: Callable):
        """取消订阅。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if event_name in self.subscribers:
            if callback in self.subscribers[event_name]:
                self.subscribers[event_name].remove(callback)
    
    def publish(self, event_name: str, data=None):
        """职责: 依次调用订阅回调并发射 `event_fired`。
        时机: 插件或内核在状态变更时同步广播。
        不变量: 无订阅者时仍发射 Qt 信号。
        排错: 部分监听器失败 → 日志 `事件回调失败` 含 event_name。
        """
        if event_name in self.subscribers:
            for callback in self.subscribers[event_name]:
                try:
                    callback(data)
                except Exception as e:
                    logger.warning("事件回调失败: %s, error=%s", event_name, e)
        
        self.event_fired.emit(event_name, data)
