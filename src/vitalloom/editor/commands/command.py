"""可视化命令模式实现 - 用于撤销/重做功能，包含可视化日志和调试"""


from abc import ABC, abstractmethod


from typing import List, Any, Optional, Dict, Callable, TYPE_CHECKING


import time


if TYPE_CHECKING:
    from vitalloom.components.components_base import ComponentBase
    from vitalloom.core.memory import MemoryGene


class Command(ABC):

    """命令基类 - 可视化版本"""

    def __init__(self):

        self.timestamp: float = 0.0

        self.execution_time: float = 0.0

        self.visual_effects: Dict[str, Any] = {}

        self.command_type: str = self.__class__.__name__

        self.description: str = ""

        self.log_callback: Optional[Callable[[str], None]] = None

    @abstractmethod

    def execute(self) -> None:

        """执行命令"""

        pass

    @abstractmethod

    def undo(self) -> None:

        """撤销命令"""

        pass

    def set_log_callback(self, callback: Callable[[str], None]) -> None:

        """设置日志回调函数"""

        self.log_callback = callback

    def log(self, message: str) -> None:

        """记录日志"""

        if self.log_callback:

            self.log_callback(message)

        print(f"[COMMAND] {self.command_type}: {message}")

    def get_visual_info(self) -> Dict[str, Any]:

        """获取可视化信息"""

        return {

            "type": self.command_type,

            "description": self.description,

            "timestamp": self.timestamp,

            "execution_time": self.execution_time,

            "effects": self.visual_effects

        }


class CommandStack:

    """命令栈，用于实现撤销/重做功能 - 可视化版本"""

    def __init__(self, max_size: int = 100):

        self.undo_stack: List[Command] = []

        self.redo_stack: List[Command] = []

        self.max_size = max_size

        self.log_callback: Optional[Callable[[str], None]] = None

        self.command_history: List[Dict[str, Any]] = []

        self.visualization_enabled: bool = True

    def set_log_callback(self, callback: Callable[[str], None]) -> None:

        """设置日志回调函数"""

        self.log_callback = callback

    def enable_visualization(self, enabled: bool = True) -> None:

        """启用/禁用可视化"""

        self.visualization_enabled = enabled

    def log(self, message: str) -> None:

        """记录日志"""

        if self.log_callback:

            self.log_callback(message)

        print(f"[COMMAND_STACK] {message}")

    def execute(self, command: Command) -> None:

        """执行命令"""

        if self.log_callback:

            command.set_log_callback(self.log_callback)

        # 记录开始时间

        start_time = time.time()

        # 执行命令

        command.execute()

        # 记录执行时间

        command.execution_time = time.time() - start_time

        command.timestamp = start_time

        # 添加到撤销栈

        self.undo_stack.append(command)

        # 限制栈大小

        if len(self.undo_stack) > self.max_size:

            self.undo_stack.pop(0)

        # 清空重做栈

        self.redo_stack.clear()

        # 记录命令历史

        if self.visualization_enabled:

            self.command_history.append(command.get_visual_info())

        self.log(f"执行命令: {command.command_type}")

    def undo(self) -> None:

        """撤销命令"""

        if self.undo_stack:

            command = self.undo_stack.pop()

            # 记录开始时间

            start_time = time.time()

            # 执行撤销

            command.undo()

            # 记录执行时间

            command.execution_time = time.time() - start_time

            # 添加到重做栈

            self.redo_stack.append(command)

            # 记录命令历史

            if self.visualization_enabled:

                undo_info = command.get_visual_info()

                undo_info["action"] = "undo"

                self.command_history.append(undo_info)

            self.log(f"撤销命令: {command.command_type}")

    def redo(self) -> None:

        """重做命令"""

        if self.redo_stack:

            command = self.redo_stack.pop()

            # 记录开始时间

            start_time = time.time()

            # 执行重做

            command.execute()

            # 记录执行时间

            command.execution_time = time.time() - start_time

            # 添加到撤销栈

            self.undo_stack.append(command)

            # 记录命令历史

            if self.visualization_enabled:

                redo_info = command.get_visual_info()

                redo_info["action"] = "redo"

                self.command_history.append(redo_info)

            self.log(f"重做命令: {command.command_type}")

    def clear(self) -> None:

        """清除所有命令"""

        self.undo_stack.clear()

        self.redo_stack.clear()

        self.command_history.clear()

        self.log("清除所有命令")

    def can_undo(self) -> bool:

        """检查是否可以撤销"""

        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:

        """检查是否可以重做"""

        return len(self.redo_stack) > 0

    def get_visual_history(self) -> List[Dict[str, Any]]:

        """获取可视化历史记录"""

        return self.command_history

    def get_stack_info(self) -> Dict[str, Any]:

        """获取栈信息"""

        return {

            "undo_stack_size": len(self.undo_stack),

            "redo_stack_size": len(self.redo_stack),

            "history_size": len(self.command_history),

            "visualization_enabled": self.visualization_enabled

        }

    def visualize_stack(self) -> None:

        """可视化命令栈"""

        print("\n=== 命令栈可视化 ===")

        print(f"撤销栈 ({len(self.undo_stack)}):")

        for i, cmd in enumerate(reversed(self.undo_stack)):

            print(f"  {i+1}. {cmd.command_type}: {cmd.description}")

        print(f"\n重做栈 ({len(self.redo_stack)}):")

        for i, cmd in enumerate(reversed(self.redo_stack)):

            print(f"  {i+1}. {cmd.command_type}: {cmd.description}")

        print(f"\n历史记录 ({len(self.command_history)} 条命令)")

        print("=== 结束 ===\n")

class AddNodeCommand(Command):

    """添加节点命令 - 可视化版本"""

    def __init__(self, canvas: Any, node: Any, pos: Any):

        super().__init__()

        self.canvas = canvas

        self.node = node

        self.pos = pos

        self.node_id = getattr(node, "id", str(id(node))[:8])

        self.description = f"添加节点 {self.node_id} 到位置 {pos}"

        self.visual_effects = {

            "node_id": self.node_id,

            "position": pos,

            "effect": "add"

        }

    def execute(self) -> None:

        """执行添加节点"""

        self.log(f"添加节点 {self.node_id} 到位置 {self.pos}")

        self.canvas.nodes.append(self.node)

        # 触发可视化更新

        if hasattr(self.canvas, "update"):

            self.canvas.update()

    def undo(self) -> None:

        """撤销添加节点"""

        self.log(f"撤销添加节点 {self.node_id}")

        # 删除相关连接

        self.canvas.connections = [c for c in self.canvas.connections \

                                 if c.start_node != self.node \

                                 and c.end_node != self.node]

        # 删除节点

        if self.node in self.canvas.nodes:

            self.canvas.nodes.remove(self.node)

        # 触发可视化更新

        if hasattr(self.canvas, "update"):

            self.canvas.update()

class DeleteNodeCommand(Command):

    """删除节点命令 - 可视化版本"""

    def __init__(self, canvas: Any, node: Any):

        super().__init__()

        self.canvas = canvas

        self.node = node

        self.node_id = getattr(node, "id", str(id(node))[:8])

        # 保存相关连接

        self.connections = [c for c in self.canvas.connections \

                          if c.start_node == self.node or c.end_node == self.node]

        self.description = f"删除节点 {self.node_id}"

        self.visual_effects = {

            "node_id": self.node_id,

            "connected_nodes": len(self.connections),

            "effect": "delete"

        }

    def execute(self) -> None:

        """执行删除节点"""

        self.log(f"删除节点 {self.node_id} 及 {len(self.connections)} 个连接")

        # 删除相关连接

        self.canvas.connections = [c for c in self.canvas.connections \

                                 if c.start_node != self.node \

                                 and c.end_node != self.node]

        # 删除节点

        if self.node in self.canvas.nodes:

            self.canvas.nodes.remove(self.node)

        # 触发可视化更新

        if hasattr(self.canvas, "update"):

            self.canvas.update()

    def undo(self) -> None:

        """撤销删除节点"""

        self.log(f"撤销删除节点 {self.node_id}")

        # 恢复节点

        self.canvas.nodes.append(self.node)

        # 恢复连接

        for connection in self.connections:

            self.canvas.connections.append(connection)

        # 触发可视化更新

        if hasattr(self.canvas, "update_visualization"):

            self.canvas.update_visualization()

class MoveNodeCommand(Command):

    """移动节点命令 - 可视化版本"""

    def __init__(self, node: Any, old_x: int, old_y: int, new_x: int, new_y: int):

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

            "effect": "move"

        }

    def execute(self) -> None:

        """执行移动节点"""

        self.log(f"移动节点 {self.node_id} 到 ({self.new_x}, {self.new_y})")

        self.node.update_position(self.new_x, self.new_y)

        # 触发可视化更新

        if hasattr(self.node, "canvas") and hasattr(self.node.canvas, "update"):

            self.node.canvas.update()

    def undo(self) -> None:

        """撤销移动节点"""

        self.log(f"撤销移动节点 {self.node_id} 回到 ({self.old_x}, {self.old_y})")

        self.node.update_position(self.old_x, self.old_y)

        # 触发可视化更新

        if hasattr(self.node, "canvas") and hasattr(self.node.canvas, "update_visualization"):

            self.node.canvas.update_visualization()

class CreateConnectionCommand(Command):

    """创建连接命令 - 可视化版本"""

    def __init__(self, canvas: Any, connection: Any):

        super().__init__()

        self.canvas = canvas

        self.connection = connection

        self.start_node_id = getattr(connection.start_node, "id", str(id(connection.start_node))[:8])

        self.end_node_id = getattr(connection.end_node, "id", str(id(connection.end_node))[:8])

        self.description = f"创建连接 {self.start_node_id} → {self.end_node_id}"

        self.visual_effects = {

            "start_node": self.start_node_id,

            "end_node": self.end_node_id,

            "effect": "connect"

        }

    def execute(self) -> None:

        """执行创建连接"""

        self.log(f"创建连接 {self.start_node_id} → {self.end_node_id}")

        self.canvas.connections.append(self.connection)

        # 触发可视化更新

        if hasattr(self.canvas, "update_visualization"):

            self.canvas.update_visualization()

    def undo(self) -> None:

        """撤销创建连接"""

        self.log(f"撤销连接 {self.start_node_id} → {self.end_node_id}")

        if self.connection in self.canvas.connections:

            self.canvas.connections.remove(self.connection)

        # 触发可视化更新

        if hasattr(self.canvas, "update_visualization"):

            self.canvas.update_visualization()

class DeleteConnectionCommand(Command):

    """删除连接命令 - 可视化版本"""

    def __init__(self, canvas: Any, connection: Any):

        super().__init__()

        self.canvas = canvas

        self.connection = connection

        self.start_node_id = getattr(connection.start_node, "id", str(id(connection.start_node))[:8])

        self.end_node_id = getattr(connection.end_node, "id", str(id(connection.end_node))[:8])

        self.description = f"删除连接 {self.start_node_id} → {self.end_node_id}"

        self.visual_effects = {

            "start_node": self.start_node_id,

            "end_node": self.end_node_id,

            "effect": "disconnect"

        }

    def execute(self) -> None:

        """执行删除连接"""

        self.log(f"删除连接 {self.start_node_id} → {self.end_node_id}")

        if self.connection in self.canvas.connections:

            self.canvas.connections.remove(self.connection)

        # 触发可视化更新

        if hasattr(self.canvas, "update_visualization"):

            self.canvas.update_visualization()

    def undo(self) -> None:

        """撤销删除连接"""

        self.log(f"恢复连接 {self.start_node_id} → {self.end_node_id}")

        self.canvas.connections.append(self.connection)

        # 触发可视化更新

        if hasattr(self.canvas, "update_visualization"):

            self.canvas.update_visualization()

class ModifyNodePropertyCommand(Command):

    """修改节点属性命令 - 可视化版本"""

    def __init__(self, node: Any, property_name: str, old_value: Any, new_value: Any):

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

            "effect": "modify"

        }

    def execute(self) -> None:

        """执行修改属性"""

        self.log(f"修改节点 {self.node_id} 的 {self.property_name} 属性")

        setattr(self.node, self.property_name, self.new_value)

        # 触发可视化更新

        if hasattr(self.node, "canvas") and hasattr(self.node.canvas, "update_visualization"):

            self.node.canvas.update_visualization()

    def undo(self) -> None:

        """撤销修改属性"""

        self.log(f"撤销修改节点 {self.node_id} 的 {self.property_name} 属性")

        setattr(self.node, self.property_name, self.old_value)

        # 触发可视化更新

        if hasattr(self.node, "canvas") and hasattr(self.node.canvas, "update_visualization"):

            self.node.canvas.update_visualization()

class ModifyConnectionPropertyCommand(Command):

    """修改连接属性命令 - 可视化版本"""

    def __init__(self, connection: Any, property_name: str, old_value: Any, new_value: Any):

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

            "effect": "modify"

        }

    def execute(self) -> None:

        """执行修改属性"""

        self.log(f"修改连接 {self.start_node_id} → {self.end_node_id} 的 {self.property_name} 属性")

        setattr(self.connection, self.property_name, self.new_value)

        # 触发可视化更新

        if hasattr(self.connection, "canvas") and hasattr(self.connection.canvas, "update"):

            self.connection.canvas.update()

    def undo(self) -> None:

        """撤销修改属性"""

        self.log(f"撤销修改连接 {self.start_node_id} → {self.end_node_id} 的 {self.property_name} 属性")

        setattr(self.connection, self.property_name, self.old_value)

        # 触发可视化更新

        if hasattr(self.connection, "canvas") and hasattr(self.connection.canvas, "update_visualization"):

            self.connection.canvas.update_visualization()

class AddComponentCommand(Command):

    """添加组件命令 - 可视化版本"""

    def __init__(self, organism: Any, component: 'ComponentBase'):

        super().__init__()

        self.organism = organism

        self.component = component

        self.component_id = getattr(component, "id", str(id(component))[:8])

        self.description = f"向生物 {organism.id} 添加组件 {self.component_id}"

        self.visual_effects = {

            "organism_id": organism.id,

            "component_id": self.component_id,

            "component_type": getattr(component, "type", "unknown"),

            "effect": "add"

        }

    def execute(self) -> None:

        """执行添加组件"""

        self.log(f"向生物 {self.organism.id} 添加组件 {self.component_id}")

        if not hasattr(self.organism, "components"):

            self.organism.components = {}  # type: ignore

        elif not isinstance(self.organism.components, dict):

            self.organism.components = {}

        self.organism.components[self.component_id] = self.component  # type: ignore[union-attr, type-var, unknown-member]  # type: ignore[union-attr, type-var, unknown-member]

        # 触发可视化更新

        if hasattr(self.organism, "canvas") and hasattr(self.organism.canvas, "update"):

            self.organism.canvas.update()

    def undo(self) -> None:

        """撤销添加组件"""

        self.log(f"撤销向生物 {self.organism.id} 添加组件 {self.component_id}")

        if hasattr(self.organism, "components") and isinstance(self.organism.components, dict):

            if self.component_id in self.organism.components:  # type: ignore

                del self.organism.components[self.component_id]  # type: ignore

        # 触发可视化更新

        if hasattr(self.organism, "canvas") and hasattr(self.organism.canvas, "update_visualization"):

            self.organism.canvas.update_visualization()

class DeleteComponentCommand(Command):

    """删除组件命令 - 可视化版本"""

    def __init__(self, organism: Any, component: 'ComponentBase'):

        super().__init__()

        self.organism = organism

        self.component = component

        self.component_id = getattr(component, "id", str(id(component))[:8])

        self.description = f"从生物 {organism.id} 删除组件 {self.component_id}"

        self.visual_effects = {

            "organism_id": organism.id,

            "component_id": self.component_id,

            "component_type": getattr(component, "type", "unknown"),

            "effect": "delete"

        }

    def execute(self) -> None:

        """执行删除组件"""

        self.log(f"从生物 {self.organism.id} 删除组件 {self.component_id}")

        if hasattr(self.organism, "components") and isinstance(self.organism.components, dict):  # type: ignore
            if self.component_id in self.organism.components:  # type: ignore
                del self.organism.components[self.component_id]  # type: ignore

        # 触发可视化更新

        if hasattr(self.organism, "canvas") and hasattr(self.organism.canvas, "update_visualization"):

            self.organism.canvas.update_visualization()

    def undo(self) -> None:

        """撤销删除组件"""

        self.log(f"撤销从生物 {self.organism.id} 删除组件 {self.component_id}")

        if not hasattr(self.organism, "components"):

            self.organism.components = {}

        elif not isinstance(self.organism.components, dict):

            self.organism.components = {}

        self.organism.components[self.component_id] = self.component  # type: ignore[union-attr, type-var, unknown-member]

        # 触发可视化更新

        if hasattr(self.organism, "canvas") and hasattr(self.organism.canvas, "update_visualization"):

            self.organism.canvas.update_visualization()

class ModifyComponentPropertyCommand(Command):

    """修改组件属性命令 - 可视化版本"""

    def __init__(self, component: 'ComponentBase', property_name: str, old_value: Any, new_value: Any):

        super().__init__()

        self.component = component

        self.property_name = property_name

        self.old_value = old_value

        self.new_value = new_value

        self.component_id = getattr(component, "id", str(id(component))[:8])

        self.organism_id = getattr(component, "organism_id", "unknown")

        self.description = f"修改组件 {self.component_id} 的 {property_name} 属性从 {old_value} 到 {new_value}"

        self.visual_effects = {

            "component_id": self.component_id,

            "organism_id": self.organism_id,

            "property": property_name,

            "old_value": str(old_value),

            "new_value": str(new_value),

            "effect": "modify"

        }

    def execute(self) -> None:

        """执行修改属性"""

        self.log(f"修改组件 {self.component_id} 的 {self.property_name} 属性")

        setattr(self.component, self.property_name, self.new_value)

        # 触发可视化更新

        organism = getattr(self.component, "organism", None)
        if organism:
            canvas = getattr(organism, "canvas", None)
            if canvas:
                update_method = getattr(canvas, "update", None)
                if update_method:
                    update_method()

    def undo(self) -> None:

        """撤销修改属性"""

        self.log(f"撤销修改组件 {self.component_id} 的 {self.property_name} 属性")

        setattr(self.component, self.property_name, self.old_value)

        # 触发可视化更新

        organism = getattr(self.component, "organism", None)
        if organism:
            canvas = getattr(organism, "canvas", None)
            if canvas:
                update_visualization = getattr(canvas, "update_visualization", None)
                if update_visualization:
                    update_visualization()

class AddMemoryCommand(Command):

    """添加记忆命令 - 可视化版本"""

    def __init__(self, organism: Any, memory: 'MemoryGene'):

        super().__init__()

        self.organism = organism

        self.memory = memory

        self.memory_id = getattr(memory, "id", str(id(memory))[:8])

        self.description = f"向生物 {organism.id} 添加记忆 {self.memory_id}"

        self.visual_effects = {

            "organism_id": organism.id,

            "memory_id": self.memory_id,

            "memory_type": getattr(memory, "type", "unknown"),

            "effect": "add"

        }

    def execute(self) -> None:

        """执行添加记忆"""

        self.log(f"向生物 {self.organism.id} 添加记忆 {self.memory_id}")

        # 使用 learned_memories 列表来存储学习记忆
        if not hasattr(self.organism, "learned_memories"):

            self.organism.learned_memories = []  # type: ignore

        elif not isinstance(self.organism.learned_memories, list):

            self.organism.learned_memories = []

        self.organism.learned_memories.append(self.memory)  # type: ignore[union-attr, type-var, unknown-member]

        # 触发可视化更新

        if hasattr(self.organism, "canvas") and hasattr(self.organism.canvas, "update_visualization"):

            self.organism.canvas.update_visualization()

    def undo(self) -> None:

        """撤销添加记忆"""

        self.log(f"撤销向生物 {self.organism.id} 添加记忆 {self.memory_id}")

        if hasattr(self.organism, "learned_memories") and isinstance(self.organism.learned_memories, list):

            if self.memory in self.organism.learned_memories:  # type: ignore

                self.organism.learned_memories.remove(self.memory)  # type: ignore

        # 触发可视化更新

        if hasattr(self.organism, "canvas") and hasattr(self.organism.canvas, "update_visualization"):

            self.organism.canvas.update_visualization()

class DeleteMemoryCommand(Command):

    """删除记忆命令 - 可视化版本"""

    def __init__(self, organism: Any, memory: 'MemoryGene'):

        super().__init__()

        self.organism = organism

        self.memory = memory

        self.memory_id = getattr(memory, "id", str(id(memory))[:8])

        self.description = f"从生物 {organism.id} 删除记忆 {self.memory_id}"

        self.visual_effects = {

            "organism_id": organism.id,

            "memory_id": self.memory_id,

            "memory_type": getattr(memory, "type", "unknown"),

            "effect": "delete"

        }

    def execute(self) -> None:

        """执行删除记忆"""

        self.log(f"从生物 {self.organism.id} 删除记忆 {self.memory_id}")

        if hasattr(self.organism, "learned_memories") and isinstance(self.organism.learned_memories, list):  # type: ignore
            if self.memory in self.organism.learned_memories:  # type: ignore
                self.organism.learned_memories.remove(self.memory)  # type: ignore

        # 触发可视化更新

        if hasattr(self.organism, "canvas") and hasattr(self.organism.canvas, "update_visualization"):

            self.organism.canvas.update_visualization()

    def undo(self) -> None:

        """撤销删除记忆"""

        self.log(f"撤销从生物 {self.organism.id} 删除记忆 {self.memory_id}")

        if not hasattr(self.organism, "learned_memories"):

            self.organism.learned_memories = []
        elif not isinstance(self.organism.learned_memories, list):
            self.organism.learned_memories = []
        self.organism.learned_memories.append(self.memory)  # type: ignore[union-attr, type-var, unknown-member]

        # 触发可视化更新

        if hasattr(self.organism, "canvas") and hasattr(self.organism.canvas, "update_visualization"):

            self.organism.canvas.update_visualization()

class ModifyMemoryCommand(Command):

    """修改记忆内容命令 - 可视化版本"""

    def __init__(self, organism: Any, memory: 'MemoryGene', old_content: Any, new_content: Any):

        super().__init__()

        self.organism = organism

        self.memory = memory

        self.old_content = old_content

        self.new_content = new_content

        self.memory_id = getattr(memory, "id", str(id(memory))[:8])

        self.description = f"修改生物 {organism.id} 的记忆 {self.memory_id} 内容"

        self.visual_effects = {

            "organism_id": organism.id,

            "memory_id": self.memory_id,

            "memory_type": getattr(memory, "type", "unknown"),

            "old_content": str(old_content)[:50] + "..." if len(str(old_content)) > 50 else str(old_content),

            "new_content": str(new_content)[:50] + "..." if len(str(new_content)) > 50 else str(new_content),

            "effect": "modify"

        }

    def execute(self) -> None:

        """执行修改记忆内容"""

        self.log(f"修改生物 {self.organism.id} 的记忆 {self.memory_id} 内容")

        # MemoryGene uses 'situation' as its content
        if hasattr(self.memory, "situation"):

            self.memory.situation = self.new_content

        # 触发可视化更新

        if hasattr(self.organism, "canvas") and hasattr(self.organism.canvas, "update_visualization"):

            self.organism.canvas.update_visualization()

    def undo(self) -> None:

        """撤销修改记忆内容"""

        self.log(f"撤销修改生物 {self.organism.id} 的记忆 {self.memory_id} 内容")

        # MemoryGene uses 'situation' as its content
        if hasattr(self.memory, "situation"):

            self.memory.situation = self.old_content

        # 触发可视化更新

        if hasattr(self.organism, "canvas") and hasattr(self.organism.canvas, "update_visualization"):

            self.organism.canvas.update_visualization()
