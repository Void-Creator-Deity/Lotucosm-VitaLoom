"""改进版AI生命体生物编辑器 - 支持撤销/重做功能"""

import pygame
import sys
import random
from ai_organism.core import Organism, MemoryGene
from ai_organism.tools import (
    TouchSensor, LightSensor, MuscleActuator, CiliaActuator,
    Connection
)

# =========================================
# 命令模式实现
# =========================================

class Command:
    """命令基类"""
    def execute(self):
        """执行命令"""
        pass
    
    def undo(self):
        """撤销命令"""
        pass

class CommandStack:
    """命令栈，用于实现撤销/重做功能"""
    def __init__(self, max_size=100):
        self.undo_stack = []
        self.redo_stack = []
        self.max_size = max_size
    
    def execute(self, command):
        """执行命令"""
        command.execute()
        self.undo_stack.append(command)
        # 限制栈大小
        if len(self.undo_stack) > self.max_size:
            self.undo_stack.pop(0)
        # 清空重做栈
        self.redo_stack.clear()
    
    def undo(self):
        """撤销命令"""
        if self.undo_stack:
            command = self.undo_stack.pop()
            command.undo()
            self.redo_stack.append(command)
            return True
        return False
    
    def redo(self):
        """重做命令"""
        if self.redo_stack:
            command = self.redo_stack.pop()
            command.execute()
            self.undo_stack.append(command)
            return True
        return False

# 具体命令实现

class AddSensorCommand(Command):
    """添加传感器命令"""
    def __init__(self, organism, sensor):
        self.organism = organism
        self.sensor = sensor
    
    def execute(self):
        self.organism.add_sensor(self.sensor)
    
    def undo(self):
        if self.sensor.tool_id in self.organism.sensors:
            del self.organism.sensors[self.sensor.tool_id]

class AddActuatorCommand(Command):
    """添加效应器命令"""
    def __init__(self, organism, actuator):
        self.organism = organism
        self.actuator = actuator
    
    def execute(self):
        self.organism.add_actuator(self.actuator)
    
    def undo(self):
        if self.actuator.tool_id in self.organism.actuators:
            del self.organism.actuators[self.actuator.tool_id]
            if self.actuator.tool_id in self.organism.control_signals:
                del self.organism.control_signals[self.actuator.tool_id]

class ConnectToolsCommand(Command):
    """连接工具命令"""
    def __init__(self, organism, source_id, target_id, weight=1.0):
        self.organism = organism
        self.source_id = source_id
        self.target_id = target_id
        self.weight = weight
        self.connection = None
    
    def execute(self):
        # 保存原始连接状态
        self.original_connections = [conn for conn in self.organism.connections]
        # 执行连接
        self.organism.connect_tools(self.source_id, self.target_id, self.weight)
        # 找到新创建的连接
        new_connections = [conn for conn in self.organism.connections if conn not in self.original_connections]
        if new_connections:
            self.connection = new_connections[0]
    
    def undo(self):
        # 恢复原始连接状态
        self.organism.connections = self.original_connections
        # 恢复源工具的连接列表
        for tool in list(self.organism.sensors.values()) + list(self.organism.actuators.values()):
            tool.connections = []
        # 重新构建连接关系
        for conn in self.original_connections:
            if conn.source.tool_id in self.organism.sensors:
                self.organism.sensors[conn.source.tool_id].connections.append(conn)
            elif conn.source.tool_id in self.organism.actuators:
                self.organism.actuators[conn.source.tool_id].connections.append(conn)

class MoveToolCommand(Command):
    """移动工具命令"""
    def __init__(self, tool, old_position, new_position):
        self.tool = tool
        # 处理位置数据，确保可以正确复制
        if hasattr(old_position, 'copy'):
            self.old_position = old_position.copy()
        else:
            # 对于元组，使用 tuple() 创建副本
            self.old_position = tuple(old_position)
        
        if hasattr(new_position, 'copy'):
            self.new_position = new_position.copy()
        else:
            self.new_position = tuple(new_position)
    
    def execute(self):
        self.tool.position = self.new_position
    
    def undo(self):
        self.tool.position = self.old_position

class AddMemoryCommand(Command):
    """添加记忆命令"""
    def __init__(self, organism, memory):
        self.organism = organism
        self.memory = memory
        self.is_learned = False  # 默认添加到遗传记忆
    
    def execute(self):
        self.organism.memory_bank.append(self.memory)
    
    def undo(self):
        if self.memory in self.organism.memory_bank:
            self.organism.memory_bank.remove(self.memory)

class DeleteToolCommand(Command):
    """删除工具命令"""
    def __init__(self, organism, tool_id):
        self.organism = organism
        self.tool_id = tool_id
        self.tool = None
        self.is_sensor = False
    
    def execute(self):
        # 保存工具信息
        if self.tool_id in self.organism.sensors:
            self.tool = self.organism.sensors[self.tool_id]
            self.is_sensor = True
            del self.organism.sensors[self.tool_id]
        elif self.tool_id in self.organism.actuators:
            self.tool = self.organism.actuators[self.tool_id]
            self.is_sensor = False
            del self.organism.actuators[self.tool_id]
            if self.tool_id in self.organism.control_signals:
                del self.organism.control_signals[self.tool_id]
        # 删除相关连接
        self.removed_connections = []
        for conn in list(self.organism.connections):
            if conn.source.tool_id == self.tool_id or conn.target.tool_id == self.tool_id:
                self.removed_connections.append(conn)
                self.organism.connections.remove(conn)
        # 更新源工具的连接列表
        for tool in list(self.organism.sensors.values()) + list(self.organism.actuators.values()):
            tool.connections = [conn for conn in tool.connections if conn not in self.removed_connections]
    
    def undo(self):
        # 恢复工具
        if self.is_sensor:
            self.organism.add_sensor(self.tool)
        else:
            self.organism.add_actuator(self.tool)
        # 恢复连接
        for conn in self.removed_connections:
            self.organism.connections.append(conn)
            if conn.source.tool_id in self.organism.sensors:
                self.organism.sensors[conn.source.tool_id].connections.append(conn)
            elif conn.source.tool_id in self.organism.actuators:
                self.organism.actuators[conn.source.tool_id].connections.append(conn)

# =========================================
# 属性编辑面板类
# =========================================

class PropertyPanel:
    """属性编辑面板"""
    def __init__(self):
        self.width = 250
        self.height = 600
        self.x = 1200 - self.width
        self.y = 100
        self.color = (30, 30, 40)
        self.border_color = (100, 100, 100)
        self.text_color = (255, 255, 255)
        self.font = pygame.font.Font("C:/Windows/Fonts/msyh.ttc", 16)
        
    def draw(self, surface, selected_object):
        """绘制属性面板"""
        # 绘制面板背景
        pygame.draw.rect(surface, self.color, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(surface, self.border_color, (self.x, self.y, self.width, self.height), 2)
        
        # 绘制标题
        title = self.font.render("属性编辑", True, self.text_color)
        surface.blit(title, (self.x + 10, self.y + 10))
        
        if not selected_object:
            # 没有选中对象
            no_obj_text = self.font.render("未选中对象", True, self.text_color)
            surface.blit(no_obj_text, (self.x + 20, self.y + 40))
            return
        
        # 根据选中对象类型绘制不同的属性
        if isinstance(selected_object, (TouchSensor, LightSensor)):
            self.draw_sensor_properties(surface, selected_object)
        elif isinstance(selected_object, (MuscleActuator, CiliaActuator)):
            self.draw_actuator_properties(surface, selected_object)
        elif isinstance(selected_object, Connection):
            self.draw_connection_properties(surface, selected_object)
        elif isinstance(selected_object, MemoryGene):
            self.draw_memory_properties(surface, selected_object)
        elif isinstance(selected_object, Organism):
            self.draw_organism_properties(surface, selected_object)
    
    def draw_sensor_properties(self, surface, sensor):
        """绘制传感器属性"""
        properties = [
            ("类型", type(sensor).__name__),
            ("ID", sensor.tool_id),
            ("位置", f"({int(sensor.position[0])}, {int(sensor.position[1])})"),
            ("灵敏度", f"{sensor.sensitivity:.2f}" if hasattr(sensor, 'sensitivity') else "N/A")
        ]
        
        y_offset = 40
        for label, value in properties:
            text = self.font.render(f"{label}: {value}", True, self.text_color)
            surface.blit(text, (self.x + 20, self.y + y_offset))
            y_offset += 25
    
    def draw_actuator_properties(self, surface, actuator):
        """绘制效应器属性"""
        properties = [
            ("类型", type(actuator).__name__),
            ("ID", actuator.tool_id),
            ("位置", f"({int(actuator.position[0])}, {int(actuator.position[1])})"),
            ("强度", f"{actuator.strength:.2f}" if hasattr(actuator, 'strength') else "N/A")
        ]
        
        y_offset = 40
        for label, value in properties:
            text = self.font.render(f"{label}: {value}", True, self.text_color)
            surface.blit(text, (self.x + 20, self.y + y_offset))
            y_offset += 25
    
    def draw_connection_properties(self, surface, connection):
        """绘制连接属性"""
        properties = [
            ("类型", "连接"),
            ("源", connection.source.tool_id),
            ("目标", connection.target.tool_id),
            ("权重", f"{connection.weight:.2f}")
        ]
        
        y_offset = 40
        for label, value in properties:
            text = self.font.render(f"{label}: {value}", True, self.text_color)
            surface.blit(text, (self.x + 20, self.y + y_offset))
            y_offset += 25
    
    def draw_memory_properties(self, surface, memory):
        """绘制记忆属性"""
        properties = [
            ("类型", "记忆基因"),
            ("情境", memory.situation),
            ("强度", f"{memory.strength:.2f}"),
            ("成功率", f"{memory.success_rate:.2f}")
        ]
        
        y_offset = 40
        for label, value in properties:
            text = self.font.render(f"{label}: {value}", True, self.text_color)
            surface.blit(text, (self.x + 20, self.y + y_offset))
            y_offset += 25
        
        # 绘制行为模式
        behavior_text = self.font.render("行为模式:", True, self.text_color)
        surface.blit(behavior_text, (self.x + 20, self.y + y_offset))
        y_offset += 25
        
        for actuator_id, value in memory.action_pattern.items():
            behavior_line = self.font.render(f"  {actuator_id}: {value:.2f}", True, self.text_color)
            surface.blit(behavior_line, (self.x + 30, self.y + y_offset))
            y_offset += 20
    
    def draw_organism_properties(self, surface, organism):
        """绘制生物属性"""
        properties = [
            ("类型", "生物"),
            ("ID", organism.id),
            ("世代", organism.generation),
            ("能量", f"{organism.energy:.1f}"),
            ("年龄", organism.age),
            ("传感器数量", len(organism.sensors)),
            ("效应器数量", len(organism.actuators)),
            ("连接数量", len(organism.connections)),
            ("记忆数量", len(organism.memory_bank) + len(organism.learned_memories))
        ]
        
        y_offset = 40
        for label, value in properties:
            text = self.font.render(f"{label}: {value}", True, self.text_color)
            surface.blit(text, (self.x + 20, self.y + y_offset))
            y_offset += 25

# =========================================
# 改进版生物编辑器类
# =========================================

class ImprovedOrganismEditor:
    """改进后的生物编辑器"""
    
    def __init__(self):
        # 初始化Pygame
        pygame.init()
        
        # 编辑器配置
        self.WIDTH, self.HEIGHT = 1200, 800
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("AI生命体生物编辑器 - 改进版")
        self.clock = pygame.time.Clock()
        
        # 颜色定义
        self.BACKGROUND_COLOR = (20, 20, 30)
        self.PANEL_COLOR = (30, 30, 40)
        self.BUTTON_COLOR = (60, 60, 80)
        self.BUTTON_HOVER_COLOR = (80, 80, 100)
        self.TEXT_COLOR = (255, 255, 255)
        self.HIGHLIGHT_COLOR = (0, 200, 255)
        self.BORDER_COLOR = (100, 100, 100)
        self.TOP_PANEL_COLOR = (40, 40, 50)
        self.LEFT_PANEL_COLOR = (30, 30, 40)
        
        # 字体
        self.font = pygame.font.Font("C:/Windows/Fonts/msyh.ttc", 20)
        self.small_font = pygame.font.Font("C:/Windows/Fonts/msyh.ttc", 16)
        self.large_font = pygame.font.Font("C:/Windows/Fonts/msyh.ttc", 24)
        
        # 创建一个新生物或加载现有生物
        self.organism = Organism("editor_org", (self.WIDTH // 2, self.HEIGHT // 2))
        
        # 编辑器状态
        self.selected_tool = None
        self.selected_organism = self.organism
        self.editor_mode = "view"  # view, add_sensor, add_actuator, connect
        self.dragging_tool = None
        self.drag_offset = (0, 0)
        self.selected_objects = []  # 支持多选
        
        # 面板配置
        self.TOP_PANEL_HEIGHT = 60
        self.LEFT_PANEL_WIDTH = 180
        self.RIGHT_PANEL_WIDTH = 250
        
        # 工具列表
        self.tool_types = {
            "sensor": ["TouchSensor", "LightSensor"],
            "actuator": ["MuscleActuator", "CiliaActuator"]
        }
        
        # 记忆编辑
        self.selected_memory = None
        
        # 命令模式
        self.command_stack = CommandStack()
        
        # 属性面板
        self.property_panel = PropertyPanel()
        
        # 状态栏信息
        self.status_message = "就绪"
    
    def run(self):
        """运行编辑器"""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    self.handle_keyboard(event)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_mouse_down(event)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.handle_mouse_up(event)
                elif event.type == pygame.MOUSEMOTION:
                    self.handle_mouse_motion(event)
            
            # 绘制
            self.draw()
            
            # 更新显示
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()
    
    def handle_keyboard(self, event):
        """处理键盘事件"""
        if event.key == pygame.K_ESCAPE:
            self.editor_mode = "view"
            self.selected_tool = None
            self.selected_objects = []
        elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
            self.save_organism()
            self.status_message = "生物配置已保存"
        elif event.key == pygame.K_o and pygame.key.get_mods() & pygame.KMOD_CTRL:
            self.load_organism()
            self.status_message = "生物配置已加载"
        elif event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_CTRL:
            # 撤销操作
            if self.command_stack.undo():
                self.status_message = "撤销操作"
            else:
                self.status_message = "没有可撤销的操作"
        elif event.key == pygame.K_y and pygame.key.get_mods() & pygame.KMOD_CTRL:
            # 重做操作
            if self.command_stack.redo():
                self.status_message = "重做操作"
            else:
                self.status_message = "没有可重做的操作"
        elif event.key == pygame.K_DELETE:
            # 删除选中对象
            self.delete_selected_objects()
        elif event.key == pygame.K_SPACE:
            # 重置视图
            self.selected_tool = None
            self.selected_objects = []
            self.editor_mode = "view"
        elif event.key == pygame.K_s and not pygame.key.get_mods() & pygame.KMOD_CTRL:
            # 快速添加传感器
            self.editor_mode = "add_sensor"
            self.selected_tool = "TouchSensor"
            self.status_message = "添加传感器模式"
        elif event.key == pygame.K_a and not pygame.key.get_mods() & pygame.KMOD_CTRL:
            # 快速添加效应器
            self.editor_mode = "add_actuator"
            self.selected_tool = "MuscleActuator"
            self.status_message = "添加效应器模式"
        elif event.key == pygame.K_c and not pygame.key.get_mods() & pygame.KMOD_CTRL:
            # 快速连接工具
            self.editor_mode = "connect"
            self.selected_tool = "connect"
            self.status_message = "连接工具模式"
    
    def handle_mouse_down(self, event):
        """处理鼠标按下事件"""
        mouse_pos = event.pos
        
        # 检查是否点击了顶部面板按钮
        if self.is_in_top_panel(mouse_pos):
            self.handle_top_panel_click(mouse_pos)
            return
        
        # 检查是否点击了左侧面板按钮
        if self.is_in_left_panel(mouse_pos):
            self.handle_left_panel_click(mouse_pos)
            return
        
        # 检查是否点击了右侧属性面板
        if self.is_in_right_panel(mouse_pos):
            # 属性面板目前是只读的，后续可以添加交互
            return
        
        # 主编辑区域
        self.handle_editor_area_click(mouse_pos)
    
    def handle_mouse_up(self, event):
        """处理鼠标释放事件"""
        if self.dragging_tool:
            # 完成拖拽操作，记录命令
            old_position = self.dragging_tool._old_position
            new_position = self.dragging_tool.position
            if not (abs(old_position[0] - new_position[0]) < 1 and abs(old_position[1] - new_position[1]) < 1):
                command = MoveToolCommand(self.dragging_tool, old_position, new_position)
                self.command_stack.execute(command)
            self.dragging_tool = None
            self.status_message = "就绪"
    
    def handle_mouse_motion(self, event):
        """处理鼠标移动事件"""
        if self.dragging_tool:
            # 更新工具位置
            org_pos = (self.WIDTH // 2, self.HEIGHT // 2)
            rel_pos = (event.pos[0] - org_pos[0], event.pos[1] - org_pos[1])
            self.dragging_tool.position = rel_pos
            self.status_message = f"移动到: ({int(rel_pos[0])}, {int(rel_pos[1])})"
    
    def is_in_top_panel(self, pos):
        """检查是否在顶部面板内"""
        return pos[1] < self.TOP_PANEL_HEIGHT
    
    def is_in_left_panel(self, pos):
        """检查是否在左侧面板内"""
        return pos[0] < self.LEFT_PANEL_WIDTH
    
    def is_in_right_panel(self, pos):
        """检查是否在右侧面板内"""
        return pos[0] > self.WIDTH - self.RIGHT_PANEL_WIDTH
    
    def handle_top_panel_click(self, pos):
        """处理顶部面板点击"""
        x, y = pos
        
        # 按钮宽度和高度
        button_width = 120
        button_height = 40
        button_y = (self.TOP_PANEL_HEIGHT - button_height) // 2
        
        # 保存按钮
        save_rect = pygame.Rect(10, button_y, button_width, button_height)
        if save_rect.collidepoint(pos):
            self.save_organism()
            self.status_message = "生物配置已保存"
        
        # 加载按钮
        load_rect = pygame.Rect(140, button_y, button_width, button_height)
        if load_rect.collidepoint(pos):
            self.load_organism()
            self.status_message = "生物配置已加载"
        
        # 新建按钮
        new_rect = pygame.Rect(270, button_y, button_width, button_height)
        if new_rect.collidepoint(pos):
            self.organism = Organism("editor_org", (self.WIDTH // 2, self.HEIGHT // 2))
            self.selected_organism = self.organism
            self.selected_tool = None
            self.selected_objects = []
            self.status_message = "已创建新生物"
        
        # 撤销按钮
        undo_rect = pygame.Rect(400, button_y, button_width, button_height)
        if undo_rect.collidepoint(pos):
            if self.command_stack.undo():
                self.status_message = "撤销操作"
            else:
                self.status_message = "没有可撤销的操作"
        
        # 重做按钮
        redo_rect = pygame.Rect(530, button_y, button_width, button_height)
        if redo_rect.collidepoint(pos):
            if self.command_stack.redo():
                self.status_message = "重做操作"
            else:
                self.status_message = "没有可重做的操作"
        
        # 删除按钮
        delete_rect = pygame.Rect(660, button_y, button_width, button_height)
        if delete_rect.collidepoint(pos):
            self.delete_selected_objects()
            self.status_message = "已删除选中对象"
    
    def handle_left_panel_click(self, pos):
        """处理左侧面板点击"""
        x, y = pos
        
        # 传感器按钮
        sensor_y = 80
        for sensor_type in self.tool_types["sensor"]:
            button_rect = pygame.Rect(10, sensor_y, self.LEFT_PANEL_WIDTH - 20, 35)
            if button_rect.collidepoint(pos):
                self.editor_mode = "add_sensor"
                self.selected_tool = sensor_type
                self.status_message = f"添加 {sensor_type} 模式"
                return
            sensor_y += 45
        
        # 效应器按钮
        actuator_y = sensor_y + 20
        for actuator_type in self.tool_types["actuator"]:
            button_rect = pygame.Rect(10, actuator_y, self.LEFT_PANEL_WIDTH - 20, 35)
            if button_rect.collidepoint(pos):
                self.editor_mode = "add_actuator"
                self.selected_tool = actuator_type
                self.status_message = f"添加 {actuator_type} 模式"
                return
            actuator_y += 45
        
        # 连接按钮
        connect_y = actuator_y + 20
        connect_rect = pygame.Rect(10, connect_y, self.LEFT_PANEL_WIDTH - 20, 35)
        if connect_rect.collidepoint(pos):
            self.editor_mode = "connect"
            self.selected_tool = "connect"
            self.status_message = "连接工具模式"
            return
        
        # 查看模式按钮
        view_y = connect_y + 55
        view_rect = pygame.Rect(10, view_y, self.LEFT_PANEL_WIDTH - 20, 35)
        if view_rect.collidepoint(pos):
            self.editor_mode = "view"
            self.selected_tool = None
            self.selected_objects = []
            self.status_message = "查看模式"
            return
    
    def handle_editor_area_click(self, pos):
        """处理编辑区域点击"""
        if self.editor_mode == "add_sensor":
            self.add_sensor_at_pos(pos)
        elif self.editor_mode == "add_actuator":
            self.add_actuator_at_pos(pos)
        elif self.editor_mode == "connect":
            self.handle_connection_click(pos)
        else:
            # 检查是否点击了工具
            self.select_tool_at_pos(pos)
    
    def add_sensor_at_pos(self, pos):
        """在指定位置添加传感器"""
        org_pos = (self.WIDTH // 2, self.HEIGHT // 2)
        rel_pos = (pos[0] - org_pos[0], pos[1] - org_pos[1])
        
        if self.selected_tool == "TouchSensor":
            sensor = TouchSensor(f"touch_{len(self.organism.sensors) + 1}", rel_pos)
        elif self.selected_tool == "LightSensor":
            sensor = LightSensor(f"light_{len(self.organism.sensors) + 1}", rel_pos)
        else:
            return
        
        # 使用命令模式添加传感器
        command = AddSensorCommand(self.organism, sensor)
        self.command_stack.execute(command)
        
        # 更新状态
        self.editor_mode = "view"
        self.selected_tool = sensor
        self.selected_objects = [sensor]
        self.status_message = f"已添加 {self.selected_tool}"
    
    def add_actuator_at_pos(self, pos):
        """在指定位置添加效应器"""
        org_pos = (self.WIDTH // 2, self.HEIGHT // 2)
        rel_pos = (pos[0] - org_pos[0], pos[1] - org_pos[1])
        
        if self.selected_tool == "MuscleActuator":
            actuator = MuscleActuator(f"muscle_{len(self.organism.actuators) + 1}", rel_pos)
        elif self.selected_tool == "CiliaActuator":
            actuator = CiliaActuator(f"cilia_{len(self.organism.actuators) + 1}", rel_pos)
        else:
            return
        
        # 使用命令模式添加效应器
        command = AddActuatorCommand(self.organism, actuator)
        self.command_stack.execute(command)
        
        # 更新状态
        self.editor_mode = "view"
        self.selected_tool = actuator
        self.selected_objects = [actuator]
        self.status_message = f"已添加 {self.selected_tool}"
    
    def handle_connection_click(self, pos):
        """处理连接模式下的点击"""
        # 简化实现：先选择源工具，再选择目标工具
        clicked_tool = self.get_tool_at_pos(pos)
        if clicked_tool:
            if not hasattr(self, "connection_source"):
                self.connection_source = clicked_tool
                self.status_message = f"已选择源: {clicked_tool.tool_id}"
            else:
                # 保存源工具ID，因为我们要删除connection_source
                source_id = self.connection_source.tool_id
                target_id = clicked_tool.tool_id
                # 创建连接
                command = ConnectToolsCommand(self.organism, source_id, target_id)
                self.command_stack.execute(command)
                delattr(self, "connection_source")
                self.editor_mode = "view"
                self.selected_tool = None
                self.status_message = f"已连接 {source_id} 到 {target_id}"
    
    def get_tool_at_pos(self, pos):
        """获取指定位置的工具"""
        org_pos = (self.WIDTH // 2, self.HEIGHT // 2)
        
        # 检查传感器
        for sensor in self.organism.sensors.values():
            tool_pos = (org_pos[0] + sensor.position[0], org_pos[1] + sensor.position[1])
            distance = ((tool_pos[0] - pos[0]) ** 2 + (tool_pos[1] - pos[1]) ** 2) ** 0.5
            if distance < 15:
                return sensor
        
        # 检查效应器
        for actuator in self.organism.actuators.values():
            tool_pos = (org_pos[0] + actuator.position[0], org_pos[1] + actuator.position[1])
            distance = ((tool_pos[0] - pos[0]) ** 2 + (tool_pos[1] - pos[1]) ** 2) ** 0.5
            if distance < 15:
                return actuator
        
        return None
    
    def select_tool_at_pos(self, pos):
        """选择指定位置的工具"""
        clicked_tool = self.get_tool_at_pos(pos)
        if clicked_tool:
            self.selected_tool = clicked_tool
            self.selected_objects = [clicked_tool]
            # 准备拖拽
            self.dragging_tool = clicked_tool
            self.dragging_tool._old_position = clicked_tool.position.copy()
            self.status_message = f"已选择: {clicked_tool.tool_id}"
        else:
            # 点击空白处，取消选择
            self.selected_tool = None
            self.selected_objects = []
            self.status_message = "已取消选择"
    
    def delete_selected_objects(self):
        """删除选中的对象"""
        if not self.selected_objects:
            self.status_message = "没有选中对象可删除"
            return
        
        for obj in self.selected_objects:
            if isinstance(obj, (TouchSensor, LightSensor, MuscleActuator, CiliaActuator)):
                # 删除工具
                command = DeleteToolCommand(self.organism, obj.tool_id)
                self.command_stack.execute(command)
        
        # 清空选择
        self.selected_tool = None
        self.selected_objects = []
        self.status_message = "已删除选中对象"
    
    def save_organism(self):
        """保存生物配置"""
        import pickle
        with open("organism_config.pkl", "wb") as f:
            pickle.dump(self.organism, f)
        print("生物配置已保存到 organism_config.pkl")
    
    def load_organism(self):
        """加载生物配置"""
        import pickle
        try:
            with open("organism_config.pkl", "rb") as f:
                self.organism = pickle.load(f)
            self.selected_organism = self.organism
            self.selected_tool = None
            self.selected_objects = []
            print("生物配置已从 organism_config.pkl 加载")
        except FileNotFoundError:
            print("未找到 organism_config.pkl 文件")
            self.status_message = "未找到配置文件"
    
    def draw(self):
        """绘制编辑器界面"""
        # 清空屏幕
        self.screen.fill(self.BACKGROUND_COLOR)
        
        # 绘制顶部面板
        self.draw_top_panel()
        
        # 绘制左侧面板
        self.draw_left_panel()
        
        # 绘制右侧属性面板
        self.property_panel.draw(self.screen, self.selected_tool)
        
        # 绘制主编辑区域
        self.draw_editor_area()
        
        # 绘制状态栏
        self.draw_status_bar()
    
    def draw_top_panel(self):
        """绘制顶部面板"""
        # 背景
        pygame.draw.rect(self.screen, self.TOP_PANEL_COLOR, 
                        (0, 0, self.WIDTH, self.TOP_PANEL_HEIGHT))
        pygame.draw.line(self.screen, self.BORDER_COLOR, 
                        (0, self.TOP_PANEL_HEIGHT), (self.WIDTH, self.TOP_PANEL_HEIGHT), 2)
        
        # 标题
        title = self.large_font.render("AI生命体生物编辑器 - 改进版", True, self.TEXT_COLOR)
        self.screen.blit(title, (self.WIDTH // 2 - title.get_width() // 2, 10))
        
        # 按钮配置
        button_width = 120
        button_height = 40
        button_y = (self.TOP_PANEL_HEIGHT - button_height) // 2
        buttons = [
            ("保存生物", 10),
            ("加载生物", 140),
            ("新建生物", 270),
            ("撤销 (Ctrl+Z)", 400),
            ("重做 (Ctrl+Y)", 530),
            ("删除 (Del)", 660)
        ]
        
        # 绘制按钮
        for text, x in buttons:
            button_rect = pygame.Rect(x, button_y, button_width, button_height)
            pygame.draw.rect(self.screen, self.BUTTON_COLOR, button_rect)
            pygame.draw.rect(self.screen, self.BORDER_COLOR, button_rect, 2)
            button_text = self.small_font.render(text, True, self.TEXT_COLOR)
            self.screen.blit(button_text, 
                           (x + (button_width - button_text.get_width()) // 2, 
                            button_y + (button_height - button_text.get_height()) // 2))
    
    def draw_left_panel(self):
        """绘制左侧面板"""
        # 背景
        pygame.draw.rect(self.screen, self.LEFT_PANEL_COLOR, 
                        (0, self.TOP_PANEL_HEIGHT, self.LEFT_PANEL_WIDTH, self.HEIGHT - self.TOP_PANEL_HEIGHT))
        pygame.draw.line(self.screen, self.BORDER_COLOR, 
                        (self.LEFT_PANEL_WIDTH, self.TOP_PANEL_HEIGHT), 
                        (self.LEFT_PANEL_WIDTH, self.HEIGHT), 2)
        
        # 标题
        title = self.font.render("工具", True, self.TEXT_COLOR)
        self.screen.blit(title, (self.LEFT_PANEL_WIDTH // 2 - title.get_width() // 2, self.TOP_PANEL_HEIGHT + 10))
        
        # 传感器标题
        sensor_title = self.small_font.render("传感器", True, self.TEXT_COLOR)
        self.screen.blit(sensor_title, (10, self.TOP_PANEL_HEIGHT + 50))
        
        # 传感器按钮
        sensor_y = self.TOP_PANEL_HEIGHT + 80
        for sensor_type in self.tool_types["sensor"]:
            self.draw_panel_button(sensor_y, f"添加 {sensor_type}")
            sensor_y += 45
        
        # 效应器标题
        actuator_title = self.small_font.render("效应器", True, self.TEXT_COLOR)
        self.screen.blit(actuator_title, (10, sensor_y - 25))
        
        # 效应器按钮
        actuator_y = sensor_y
        for actuator_type in self.tool_types["actuator"]:
            self.draw_panel_button(actuator_y, f"添加 {actuator_type}")
            actuator_y += 45
        
        # 连接按钮
        connect_y = actuator_y
        self.draw_panel_button(connect_y, "连接工具")
        
        # 查看模式按钮
        view_y = connect_y + 55
        self.draw_panel_button(view_y, "查看模式")
        
        # 快捷键提示
        shortcut_y = view_y + 80
        shortcut_title = self.small_font.render("快捷键", True, self.TEXT_COLOR)
        self.screen.blit(shortcut_title, (10, shortcut_y))
        
        shortcuts = [
            "Ctrl+S: 保存",
            "Ctrl+O: 加载",
            "Ctrl+Z: 撤销",
            "Ctrl+Y: 重做",
            "Del: 删除",
            "S: 添加传感器",
            "A: 添加效应器",
            "C: 连接工具",
            "Space: 取消选择",
            "Esc: 退出模式"
        ]
        
        for i, shortcut in enumerate(shortcuts):
            shortcut_text = self.small_font.render(shortcut, True, self.TEXT_COLOR)
            self.screen.blit(shortcut_text, (10, shortcut_y + 30 + i * 20))
    
    def draw_panel_button(self, y, text):
        """绘制面板按钮"""
        button_rect = pygame.Rect(10, y, self.LEFT_PANEL_WIDTH - 20, 35)
        pygame.draw.rect(self.screen, self.BUTTON_COLOR, button_rect)
        pygame.draw.rect(self.screen, self.BORDER_COLOR, button_rect, 2)
        button_text = self.small_font.render(text, True, self.TEXT_COLOR)
        self.screen.blit(button_text, 
                       (button_rect.x + (button_rect.width - button_text.get_width()) // 2, 
                        button_rect.y + (button_rect.height - button_text.get_height()) // 2))
    
    def draw_editor_area(self):
        """绘制主编辑区域"""
        # 绘制生物
        org_pos = (self.WIDTH // 2, self.HEIGHT // 2)
        
        # 绘制生物主体
        pygame.draw.circle(self.screen, self.organism.color, org_pos, self.organism.radius)
        pygame.draw.circle(self.screen, (0, 0, 0), org_pos, self.organism.radius, 2)
        
        # 绘制连接
        for connection in self.organism.connections:
            source = self.organism.sensors.get(connection.source.tool_id) or self.organism.actuators.get(connection.source.tool_id)
            target = self.organism.sensors.get(connection.target.tool_id) or self.organism.actuators.get(connection.target.tool_id)
            
            if source and target:
                start_pos = (org_pos[0] + source.position[0], org_pos[1] + source.position[1])
                end_pos = (org_pos[0] + target.position[0], org_pos[1] + target.position[1])
                
                # 根据权重决定颜色
                color = (100, 100, 255) if connection.weight > 0 else (255, 100, 100)
                pygame.draw.line(self.screen, color, start_pos, end_pos, 2)
        
        # 绘制传感器
        for sensor in self.organism.sensors.values():
            tool_pos = (org_pos[0] + sensor.position[0], org_pos[1] + sensor.position[1])
            
            # 传感器颜色
            if sensor.tool_id.startswith("touch"):
                color = (0, 255, 0)  # 绿色
            elif sensor.tool_id.startswith("light"):
                color = (255, 255, 0)  # 黄色
            else:
                color = (255, 255, 255)
            
            pygame.draw.circle(self.screen, color, tool_pos, 15)
            pygame.draw.circle(self.screen, (0, 0, 0), tool_pos, 15, 2)
            
            # 选中效果
            if sensor in self.selected_objects:
                pygame.draw.circle(self.screen, self.HIGHLIGHT_COLOR, tool_pos, 20, 3)
        
        # 绘制效应器
        for actuator in self.organism.actuators.values():
            tool_pos = (org_pos[0] + actuator.position[0], org_pos[1] + actuator.position[1])
            
            # 效应器颜色
            if actuator.tool_id.startswith("muscle"):
                color = (255, 0, 0)  # 红色
            elif actuator.tool_id.startswith("cilia"):
                color = (0, 255, 255)  # 青色
            else:
                color = (255, 255, 255)
            
            pygame.draw.rect(self.screen, color, (tool_pos[0] - 15, tool_pos[1] - 15, 30, 30))
            pygame.draw.rect(self.screen, (0, 0, 0), (tool_pos[0] - 15, tool_pos[1] - 15, 30, 30), 2)
            
            # 选中效果
            if actuator in self.selected_objects:
                pygame.draw.rect(self.screen, self.HIGHLIGHT_COLOR, 
                                (tool_pos[0] - 20, tool_pos[1] - 20, 40, 40), 3)
        
        # 绘制模式提示
        mode_text = self.font.render(f"当前模式: {self.editor_mode}", True, self.TEXT_COLOR)
        mode_rect = mode_text.get_rect()
        mode_rect.bottomleft = (self.LEFT_PANEL_WIDTH + 10, self.HEIGHT - 10)
        self.screen.blit(mode_text, mode_rect)
    
    def draw_status_bar(self):
        """绘制状态栏"""
        # 状态栏背景
        status_height = 30
        pygame.draw.rect(self.screen, self.PANEL_COLOR, 
                        (0, self.HEIGHT - status_height, self.WIDTH, status_height))
        pygame.draw.line(self.screen, self.BORDER_COLOR, 
                        (0, self.HEIGHT - status_height), (self.WIDTH, self.HEIGHT - status_height), 2)
        
        # 状态信息
        status_text = self.small_font.render(self.status_message, True, self.TEXT_COLOR)
        self.screen.blit(status_text, (10, self.HEIGHT - status_height + 5))
        
        # 选中对象信息
        if self.selected_objects:
            selected_text = self.small_font.render(f"已选中 {len(self.selected_objects)} 个对象", True, self.TEXT_COLOR)
            selected_rect = selected_text.get_rect()
            selected_rect.bottomright = (self.WIDTH - 10, self.HEIGHT - 5)
            self.screen.blit(selected_text, selected_rect)

# =========================================
# 主函数
# =========================================

def main():
    """主函数"""
    editor = ImprovedOrganismEditor()
    editor.run()

if __name__ == "__main__":
    main()
