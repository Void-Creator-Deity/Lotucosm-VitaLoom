"""命令模式：Scene/Inspector 撤销重做栈与可视化日志。

架构数据流::

    UI 变更 → Command.execute → CommandStack.undo_stack

排错: 见 core/VitaLoom/README.md「撤销」
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

from core.VitaLoom.core.logger import get_logger

logger = get_logger("Command")

if TYPE_CHECKING:
    from builtin.components.components_base import ComponentBase
    from core.Lotucosm.memory import MemoryGene


class Command(ABC):
    """定义 execute/undo 契约与可视化元数据。"""

    def __init__(self) -> None:
        self.timestamp: float = 0.0
        self.execution_time: float = 0.0
        self.visual_effects: Dict[str, Any] = {}
        self.command_type: str = self.__class__.__name__
        self.description: str = ""
        self.log_callback: Optional[Callable[[str], None]] = None

    @abstractmethod
    def execute(self) -> None:
        pass

    @abstractmethod
    def undo(self) -> None:
        pass

    def set_log_callback(self, callback: Callable[[str], None]) -> None:
        self.log_callback = callback

    def log(self, message: str) -> None:
        if self.log_callback:
            self.log_callback(message)
        logger.info("[COMMAND] %s: %s", self.command_type, message)

    def get_visual_info(self) -> Dict[str, Any]:
        return {
            "type": self.command_type,
            "description": self.description,
            "timestamp": self.timestamp,
            "execution_time": self.execution_time,
            "effects": self.visual_effects,
        }


class CommandStack:
    """维护 undo/redo 双栈与可选可视化历史。"""

    def __init__(self, max_size: int = 100) -> None:
        self.undo_stack: List[Command] = []
        self.redo_stack: List[Command] = []
        self.max_size = max_size
        self.log_callback: Optional[Callable[[str], None]] = None
        self.command_history: List[Dict[str, Any]] = []
        self.visualization_enabled: bool = True

    def set_log_callback(self, callback: Callable[[str], None]) -> None:
        self.log_callback = callback

    def enable_visualization(self, enabled: bool = True) -> None:
        self.visualization_enabled = enabled

    def log(self, message: str) -> None:
        if self.log_callback:
            self.log_callback(message)
        logger.info("[COMMAND_STACK] %s", message)

    def execute(self, command: Command) -> None:
        if self.log_callback:
            command.set_log_callback(self.log_callback)
        start_time = time.time()
        command.execute()
        command.execution_time = time.time() - start_time
        command.timestamp = start_time
        self.undo_stack.append(command)
        if len(self.undo_stack) > self.max_size:
            self.undo_stack.pop(0)
        self.redo_stack.clear()
        if self.visualization_enabled:
            self.command_history.append(command.get_visual_info())
        self.log(f"执行命令: {command.command_type}")

    def undo(self) -> None:
        if not self.undo_stack:
            return
        command = self.undo_stack.pop()
        start_time = time.time()
        command.undo()
        command.execution_time = time.time() - start_time
        self.redo_stack.append(command)
        if self.visualization_enabled:
            undo_info = command.get_visual_info()
            undo_info["action"] = "undo"
            self.command_history.append(undo_info)
        self.log(f"撤销命令: {command.command_type}")

    def redo(self) -> None:
        if not self.redo_stack:
            return
        command = self.redo_stack.pop()
        start_time = time.time()
        command.execute()
        command.execution_time = time.time() - start_time
        self.undo_stack.append(command)
        if self.visualization_enabled:
            redo_info = command.get_visual_info()
            redo_info["action"] = "redo"
            self.command_history.append(redo_info)
        self.log(f"重做命令: {command.command_type}")

    def can_undo(self) -> bool:
        return bool(self.undo_stack)

    def can_redo(self) -> bool:
        return bool(self.redo_stack)

    def clear(self) -> None:
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.command_history.clear()


class AddNodeCommand(Command):
    def __init__(self, canvas: Any, node: Any, pos: Any) -> None:
        super().__init__()
        self.canvas = canvas
        self.node = node
        self.pos = pos
        self.node_id = getattr(node, "id", str(id(node))[:8])
        self.description = f"添加节点 {self.node_id} 到位置 {pos}"
        self.visual_effects = {"node_id": self.node_id, "position": pos, "effect": "add"}

    def execute(self) -> None:
        self.log(f"添加节点 {self.node_id} 到位置 {self.pos}")
        self.canvas.nodes.append(self.node)
        if hasattr(self.canvas, "update"):
            self.canvas.update()

    def undo(self) -> None:
        self.log(f"撤销添加节点 {self.node_id}")
        self.canvas.connections = [
            c for c in self.canvas.connections if c.start_node != self.node and c.end_node != self.node
        ]
        if self.node in self.canvas.nodes:
            self.canvas.nodes.remove(self.node)
        if hasattr(self.canvas, "update"):
            self.canvas.update()


class DeleteNodeCommand(Command):
    def __init__(self, canvas: Any, node: Any) -> None:
        super().__init__()
        self.canvas = canvas
        self.node = node
        self.node_id = getattr(node, "id", str(id(node))[:8])
        self.connections = [
            c for c in self.canvas.connections if c.start_node == self.node or c.end_node == self.node
        ]
        self.node_index = self.canvas.nodes.index(node) if node in self.canvas.nodes else -1
        self.description = f"删除节点 {self.node_id}"
        self.visual_effects = {
            "node_id": self.node_id,
            "connected_nodes": len(self.connections),
            "effect": "delete",
        }

    def execute(self) -> None:
        self.log(f"删除节点 {self.node_id} 及 {len(self.connections)} 个连接")
        self.canvas.connections = [
            c for c in self.canvas.connections if c.start_node != self.node and c.end_node != self.node
        ]
        if self.node in self.canvas.nodes:
            self.canvas.nodes.remove(self.node)
        if hasattr(self.canvas, "update"):
            self.canvas.update()

    def undo(self) -> None:
        self.log(f"撤销删除节点 {self.node_id}")
        if self.node not in self.canvas.nodes:
            if 0 <= self.node_index <= len(self.canvas.nodes):
                self.canvas.nodes.insert(self.node_index, self.node)
            else:
                self.canvas.nodes.append(self.node)
        for conn in self.connections:
            if conn not in self.canvas.connections:
                self.canvas.connections.append(conn)
        if hasattr(self.canvas, "update"):
            self.canvas.update()


class MoveNodeCommand(Command):
    def __init__(self, node: Any, old_x: int, old_y: int, new_x: int, new_y: int) -> None:
        super().__init__()
        self.node = node
        self.old_x = old_x
        self.old_y = old_y
        self.new_x = new_x
        self.new_y = new_y
        self.node_id = getattr(node, "id", str(id(node))[:8])
        self.description = f"移动节点 {self.node_id} 从 ({old_x}, {old_y}) 到 ({new_x}, {new_y})"
        self.visual_effects = {
            "node_id": self.node_id,
            "old_position": (old_x, old_y),
            "new_position": (new_x, new_y),
            "effect": "move",
        }

    def execute(self) -> None:
        self.log(f"移动节点 {self.node_id} 到 ({self.new_x}, {self.new_y})")
        if hasattr(self.node, "update_position"):
            self.node.update_position(self.new_x, self.new_y)
        else:
            self.node.x = self.new_x
            self.node.y = self.new_y
        if hasattr(self.node, "canvas") and hasattr(self.node.canvas, "update"):
            self.node.canvas.update()

    def undo(self) -> None:
        self.log(f"撤销移动节点 {self.node_id} 到 ({self.old_x}, {self.old_y})")
        if hasattr(self.node, "update_position"):
            self.node.update_position(self.old_x, self.old_y)
        else:
            self.node.x = self.old_x
            self.node.y = self.old_y
        if hasattr(self.node, "canvas") and hasattr(self.node.canvas, "update"):
            self.node.canvas.update()


class CreateConnectionCommand(Command):
    def __init__(self, canvas: Any, connection: Any) -> None:
        super().__init__()
        self.canvas = canvas
        self.connection = connection
        self.start_node_id = getattr(connection.start_node, "id", str(id(connection.start_node))[:8])
        self.end_node_id = getattr(connection.end_node, "id", str(id(connection.end_node))[:8])
        self.description = f"创建连接 {self.start_node_id} → {self.end_node_id}"
        self.visual_effects = {
            "start_node": self.start_node_id,
            "end_node": self.end_node_id,
            "effect": "connect",
        }

    def execute(self) -> None:
        self.log(f"创建连接 {self.start_node_id} → {self.end_node_id}")
        self.canvas.connections.append(self.connection)
        if hasattr(self.canvas, "update_visualization"):
            self.canvas.update_visualization()
        elif hasattr(self.canvas, "update"):
            self.canvas.update()

    def undo(self) -> None:
        self.log(f"撤销创建连接 {self.start_node_id} → {self.end_node_id}")
        if self.connection in self.canvas.connections:
            self.canvas.connections.remove(self.connection)
        if hasattr(self.canvas, "update_visualization"):
            self.canvas.update_visualization()
        elif hasattr(self.canvas, "update"):
            self.canvas.update()


class DeleteConnectionCommand(Command):
    def __init__(self, canvas: Any, connection: Any) -> None:
        super().__init__()
        self.canvas = canvas
        self.connection = connection
        self.start_node_id = getattr(connection.start_node, "id", str(id(connection.start_node))[:8])
        self.end_node_id = getattr(connection.end_node, "id", str(id(connection.end_node))[:8])
        self.description = f"删除连接 {self.start_node_id} → {self.end_node_id}"
        self.visual_effects = {
            "start_node": self.start_node_id,
            "end_node": self.end_node_id,
            "effect": "disconnect",
        }

    def execute(self) -> None:
        self.log(f"删除连接 {self.start_node_id} → {self.end_node_id}")
        if self.connection in self.canvas.connections:
            self.canvas.connections.remove(self.connection)
        if hasattr(self.canvas, "update_visualization"):
            self.canvas.update_visualization()
        elif hasattr(self.canvas, "update"):
            self.canvas.update()

    def undo(self) -> None:
        self.log(f"撤销删除连接 {self.start_node_id} → {self.end_node_id}")
        if self.connection not in self.canvas.connections:
            self.canvas.connections.append(self.connection)
        if hasattr(self.canvas, "update_visualization"):
            self.canvas.update_visualization()
        elif hasattr(self.canvas, "update"):
            self.canvas.update()


class ModifyNodePropertyCommand(Command):
    def __init__(self, node: Any, property_name: str, old_value: Any, new_value: Any) -> None:
        super().__init__()
        self.node = node
        self.property_name = property_name
        self.old_value = old_value
        self.new_value = new_value
        self.node_id = getattr(node, "id", str(id(node))[:8])
        self.description = f"修改节点 {self.node_id} 的 {property_name} 属性从 {old_value} 到 {new_value}"
        self.visual_effects = {
            "node_id": self.node_id,
            "property": property_name,
            "old_value": str(old_value),
            "new_value": str(new_value),
            "effect": "modify",
        }

    def execute(self) -> None:
        self.log(f"修改节点 {self.node_id} 的 {self.property_name} 属性")
        setattr(self.node, self.property_name, self.new_value)
        if hasattr(self.node, "canvas") and hasattr(self.node.canvas, "update_visualization"):
            self.node.canvas.update_visualization()

    def undo(self) -> None:
        self.log(f"撤销修改节点 {self.node_id} 的 {self.property_name} 属性")
        setattr(self.node, self.property_name, self.old_value)
        if hasattr(self.node, "canvas") and hasattr(self.node.canvas, "update_visualization"):
            self.node.canvas.update_visualization()


class ModifyConnectionPropertyCommand(Command):
    def __init__(self, connection: Any, property_name: str, old_value: Any, new_value: Any) -> None:
        super().__init__()
        self.connection = connection
        self.property_name = property_name
        self.old_value = old_value
        self.new_value = new_value
        self.start_node_id = getattr(connection.start_node, "id", str(id(connection.start_node))[:8])
        self.end_node_id = getattr(connection.end_node, "id", str(id(connection.end_node))[:8])
        self.description = f"修改连接 {self.start_node_id} → {self.end_node_id} 的 {property_name} 属性"
        self.visual_effects = {
            "start_node": self.start_node_id,
            "end_node": self.end_node_id,
            "property": property_name,
            "old_value": str(old_value),
            "new_value": str(new_value),
            "effect": "modify",
        }

    def execute(self) -> None:
        self.log(f"修改连接 {self.start_node_id} → {self.end_node_id} 的 {self.property_name} 属性")
        setattr(self.connection, self.property_name, self.new_value)
        if hasattr(self.connection, "canvas") and hasattr(self.connection.canvas, "update"):
            self.connection.canvas.update()

    def undo(self) -> None:
        self.log(f"撤销修改连接 {self.start_node_id} → {self.end_node_id} 的 {self.property_name} 属性")
        setattr(self.connection, self.property_name, self.old_value)
        if hasattr(self.connection, "canvas") and hasattr(self.connection.canvas, "update"):
            self.connection.canvas.update()
