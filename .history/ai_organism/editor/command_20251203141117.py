"""命令模式实现 - 用于撤销/重做功能"""

from abc import ABC, abstractmethod
from typing import List, Any


class Command(ABC):
    """命令基类"""
    @abstractmethod
    def execute(self) -> None:
        """执行命令"""
        pass
    
    @abstractmethod
    def undo(self) -> None:
        """撤销命令"""
        pass


class CommandStack:
    """命令栈，用于实现撤销/重做功能"""
    def __init__(self, max_size: int = 100):
        self.undo_stack: List[Command] = []
        self.redo_stack: List[Command] = []
        self.max_size = max_size
    
    def execute(self, command: Command) -> None:
        """执行命令"""
        command.execute()
        self.undo_stack.append(command)
        # 限制栈大小
        if len(self.undo_stack) > self.max_size:
            self.undo_stack.pop(0)
        # 清空重做栈
        self.redo_stack.clear()
    
    def undo(self) -> None:
        """撤销命令"""
        if self.undo_stack:
            command = self.undo_stack.pop()
            command.undo()
            self.redo_stack.append(command)
    
    def redo(self) -> None:
        """重做命令"""
        if self.redo_stack:
            command = self.redo_stack.pop()
            command.execute()
            self.undo_stack.append(command)
    
    def clear(self) -> None:
        """清除所有命令"""
        self.undo_stack.clear()
        self.redo_stack.clear()
    
    def can_undo(self) -> bool:
        """检查是否可以撤销"""
        return len(self.undo_stack) > 0
    
    def can_redo(self) -> bool:
        """检查是否可以重做"""
        return len(self.redo_stack) > 0


class AddNodeCommand(Command):
    """添加节点命令"""
    def __init__(self, canvas: Any, node: Any, pos: Any):
        self.canvas = canvas
        self.node = node
        self.pos = pos
    
    def execute(self) -> None:
        """执行添加节点"""
        self.canvas.nodes.append(self.node)
    
    def undo(self) -> None:
        """撤销添加节点"""
        # 删除相关连接
        self.canvas.connections = [c for c in self.canvas.connections \
                                 if c.start_node != self.node \
                                 and c.end_node != self.node]
        # 删除节点
        if self.node in self.canvas.nodes:
            self.canvas.nodes.remove(self.node)


class DeleteNodeCommand(Command):
    """删除节点命令"""
    def __init__(self, canvas: Any, node: Any):
        self.canvas = canvas
        self.node = node
        # 保存相关连接
        self.connections = [c for c in self.canvas.connections \
                          if c.start_node == self.node or c.end_node == self.node]
    
    def execute(self) -> None:
        """执行删除节点"""
        # 删除相关连接
        self.canvas.connections = [c for c in self.canvas.connections \
                                 if c.start_node != self.node \
                                 and c.end_node != self.node]
        # 删除节点
        if self.node in self.canvas.nodes:
            self.canvas.nodes.remove(self.node)
    
    def undo(self) -> None:
        """撤销删除节点"""
        # 恢复节点
        self.canvas.nodes.append(self.node)
        # 恢复连接
        for connection in self.connections:
            self.canvas.connections.append(connection)


class MoveNodeCommand(Command):
    """移动节点命令"""
    def __init__(self, node: Any, old_x: int, old_y: int, new_x: int, new_y: int):
        self.node = node
        self.old_x = old_x
        self.old_y = old_y
        self.new_x = new_x
        self.new_y = new_y
    
    def execute(self) -> None:
        """执行移动节点"""
        self.node.update_position(self.new_x, self.new_y)
    
    def undo(self) -> None:
        """撤销移动节点"""
        self.node.update_position(self.old_x, self.old_y)


class CreateConnectionCommand(Command):
    """创建连接命令"""
    def __init__(self, canvas: Any, connection: Any):
        self.canvas = canvas
        self.connection = connection
    
    def execute(self) -> None:
        """执行创建连接"""
        self.canvas.connections.append(self.connection)
    
    def undo(self) -> None:
        """撤销创建连接"""
        if self.connection in self.canvas.connections:
            self.canvas.connections.remove(self.connection)


class DeleteConnectionCommand(Command):
    """删除连接命令"""
    def __init__(self, canvas: Any, connection: Any):
        self.canvas = canvas
        self.connection = connection
    
    def execute(self) -> None:
        """执行删除连接"""
        if self.connection in self.canvas.connections:
            self.canvas.connections.remove(self.connection)
    
    def undo(self) -> None:
        """撤销删除连接"""
        self.canvas.connections.append(self.connection)


class ModifyNodePropertyCommand(Command):
    """修改节点属性命令"""
    def __init__(self, node: Any, property_name: str, old_value: Any, new_value: Any):
        self.node = node
        self.property_name = property_name
        self.old_value = old_value
        self.new_value = new_value
    
    def execute(self) -> None:
        """执行修改属性"""
        setattr(self.node, self.property_name, self.new_value)
    
    def undo(self) -> None:
        """撤销修改属性"""
        setattr(self.node, self.property_name, self.old_value)


class ModifyConnectionPropertyCommand(Command):
    """修改连接属性命令"""
    def __init__(self, connection: Any, property_name: str, old_value: Any, new_value: Any):
        self.connection = connection
        self.property_name = property_name
        self.old_value = old_value
        self.new_value = new_value
    
    def execute(self) -> None:
        """执行修改属性"""
        setattr(self.connection, self.property_name, self.new_value)
    
    def undo(self) -> None:
        """撤销修改属性"""
        setattr(self.connection, self.property_name, self.old_value)
