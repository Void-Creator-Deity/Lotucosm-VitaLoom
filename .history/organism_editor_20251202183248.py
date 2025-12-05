"""AI生命体生物编辑器"""

import pygame
import sys
import random
from ai_organism.core import Organism, MemoryGene
from ai_organism.tools import (
    TouchSensor, LightSensor, MuscleActuator, CiliaActuator,
    Connection
)

class OrganismEditor:
    """生物编辑器类"""
    
    def __init__(self):
        # 初始化Pygame
        pygame.init()
        
        # 编辑器配置
        self.WIDTH, self.HEIGHT = 1200, 800
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("AI生命体生物编辑器")
        self.clock = pygame.time.Clock()
        
        # 颜色定义
        self.BACKGROUND_COLOR = (20, 20, 30)
        self.PANEL_COLOR = (30, 30, 40)
        self.BUTTON_COLOR = (60, 60, 80)
        self.BUTTON_HOVER_COLOR = (80, 80, 100)
        self.TEXT_COLOR = (255, 255, 255)
        self.HIGHLIGHT_COLOR = (0, 200, 255)
        self.BORDER_COLOR = (100, 100, 100)
        
        # 字体
        self.font = pygame.font.Font("C:/Windows/Fonts/msyh.ttc", 20)
        self.small_font = pygame.font.Font("C:/Windows/Fonts/msyh.ttc", 16)
        
        # 创建一个新生物或加载现有生物
        self.organism = Organism("editor_org", (self.WIDTH // 2, self.HEIGHT // 2))
        
        # 编辑器状态
        self.selected_tool = None
        self.selected_organism = self.organism
        self.editor_mode = "view"  # view, add_sensor, add_actuator, connect
        self.dragging_tool = None
        self.drag_offset = (0, 0)
        
        # 面板配置
        self.SIDE_PANEL_WIDTH = 300
        self.TOP_PANEL_HEIGHT = 50
        
        # 工具列表
        self.tool_types = {
            "sensor": ["TouchSensor", "LightSensor"],
            "actuator": ["MuscleActuator", "CiliaActuator"]
        }
        
        # 记忆编辑
        self.selected_memory = None
        
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
        elif event.key == pygame.K_s:
            self.save_organism()
        elif event.key == pygame.K_l:
            self.load_organism()
    
    def handle_mouse_down(self, event):
        """处理鼠标按下事件"""
        mouse_pos = event.pos
        
        # 检查是否点击了侧边面板按钮
        if self.is_in_side_panel(mouse_pos):
            self.handle_side_panel_click(mouse_pos)
        elif self.is_in_top_panel(mouse_pos):
            self.handle_top_panel_click(mouse_pos)
        else:
            # 主编辑区域
            self.handle_editor_area_click(mouse_pos)
    
    def handle_mouse_up(self, event):
        """处理鼠标释放事件"""
        if self.dragging_tool:
            self.dragging_tool = None
    
    def handle_mouse_motion(self, event):
        """处理鼠标移动事件"""
        if self.dragging_tool:
            # 更新工具位置
            rel_pos = (event.pos[0] - self.WIDTH // 2, event.pos[1] - self.HEIGHT // 2)
            self.dragging_tool.position = rel_pos
    
    def is_in_side_panel(self, pos):
        """检查是否在侧边面板内"""
        return pos[0] > self.WIDTH - self.SIDE_PANEL_WIDTH
    
    def is_in_top_panel(self, pos):
        """检查是否在顶部面板内"""
        return pos[1] < self.TOP_PANEL_HEIGHT
    
    def handle_side_panel_click(self, pos):
        """处理侧边面板点击"""
        x, y = pos
        panel_x = self.WIDTH - self.SIDE_PANEL_WIDTH
        
        # 传感器按钮
        sensor_y = 60
        for sensor_type in self.tool_types["sensor"]:
            if y >= sensor_y and y <= sensor_y + 30:
                self.editor_mode = "add_sensor"
                self.selected_tool = sensor_type
                return
            sensor_y += 40
        
        # 效应器按钮
        actuator_y = sensor_y + 20
        for actuator_type in self.tool_types["actuator"]:
            if y >= actuator_y and y <= actuator_y + 30:
                self.editor_mode = "add_actuator"
                self.selected_tool = actuator_type
                return
            actuator_y += 40
        
        # 连接按钮
        connect_y = actuator_y + 20
        if y >= connect_y and y <= connect_y + 30:
            self.editor_mode = "connect"
            self.selected_tool = "connect"
            return
        
        # 记忆编辑区域
        memory_y = connect_y + 60
        if y >= memory_y:
            self.handle_memory_panel_click(pos, memory_y)
    
    def handle_top_panel_click(self, pos):
        """处理顶部面板点击"""
        x, y = pos
        
        # 保存按钮
        save_rect = pygame.Rect(10, 10, 100, 30)
        if save_rect.collidepoint(pos):
            self.save_organism()
        
        # 加载按钮
        load_rect = pygame.Rect(120, 10, 100, 30)
        if load_rect.collidepoint(pos):
            self.load_organism()
        
        # 新建按钮
        new_rect = pygame.Rect(230, 10, 100, 30)
        if new_rect.collidepoint(pos):
            self.organism = Organism("editor_org", (self.WIDTH // 2, self.HEIGHT // 2))
            self.selected_organism = self.organism
    
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
        rel_pos = (pos[0] - self.WIDTH // 2, pos[1] - self.HEIGHT // 2)
        
        if self.selected_tool == "TouchSensor":
            sensor = TouchSensor(f"touch_{len(self.organism.sensors) + 1}", rel_pos)
        elif self.selected_tool == "LightSensor":
            sensor = LightSensor(f"light_{len(self.organism.sensors) + 1}", rel_pos)
        else:
            return
        
        self.organism.add_sensor(sensor)
        self.editor_mode = "view"
        self.selected_tool = None
    
    def add_actuator_at_pos(self, pos):
        """在指定位置添加效应器"""
        rel_pos = (pos[0] - self.WIDTH // 2, pos[1] - self.HEIGHT // 2)
        
        if self.selected_tool == "MuscleActuator":
            actuator = MuscleActuator(f"muscle_{len(self.organism.actuators) + 1}", rel_pos)
        elif self.selected_tool == "CiliaActuator":
            actuator = CiliaActuator(f"cilia_{len(self.organism.actuators) + 1}", rel_pos)
        else:
            return
        
        self.organism.add_actuator(actuator)
        self.editor_mode = "view"
        self.selected_tool = None
    
    def handle_connection_click(self, pos):
        """处理连接模式下的点击"""
        # 简化实现：先选择源工具，再选择目标工具
        clicked_tool = self.get_tool_at_pos(pos)
        if clicked_tool:
            if not hasattr(self, "connection_source"):
                self.connection_source = clicked_tool
            else:
                # 创建连接
                self.organism.connect_tools(self.connection_source.tool_id, clicked_tool.tool_id)
                delattr(self, "connection_source")
                self.editor_mode = "view"
                self.selected_tool = None
    
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
        self.selected_tool = self.get_tool_at_pos(pos)
        if self.selected_tool:
            self.dragging_tool = self.selected_tool
            org_pos = (self.WIDTH // 2, self.HEIGHT // 2)
            tool_pos = (org_pos[0] + self.selected_tool.position[0], org_pos[1] + self.selected_tool.position[1])
            self.drag_offset = (pos[0] - tool_pos[0], pos[1] - tool_pos[1])
    
    def handle_memory_panel_click(self, pos, start_y):
        """处理记忆面板点击"""
        x, y = pos
        panel_x = self.WIDTH - self.SIDE_PANEL_WIDTH
        
        # 显示所有记忆基因
        for i, memory in enumerate(self.organism.memory_bank + self.organism.learned_memories):
            memory_y = start_y + i * 40
            if y >= memory_y and y <= memory_y + 30:
                self.selected_memory = memory
                return
        
        # 添加记忆按钮
        add_y = start_y + len(self.organism.memory_bank + self.organism.learned_memories) * 40 + 20
        if y >= add_y and y <= add_y + 30:
            self.add_new_memory()
    
    def add_new_memory(self):
        """添加新记忆"""
        # 创建一个新的记忆基因
        new_memory = MemoryGene(
            "new_situation",
            {actuator_id: 0.0 for actuator_id in self.organism.actuators},
            0.5
        )
        self.organism.memory_bank.append(new_memory)
        self.selected_memory = new_memory
    
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
            print("生物配置已从 organism_config.pkl 加载")
        except FileNotFoundError:
            print("未找到 organism_config.pkl 文件")
    
    def draw(self):
        """绘制编辑器界面"""
        # 清空屏幕
        self.screen.fill(self.BACKGROUND_COLOR)
        
        # 绘制顶部面板
        self.draw_top_panel()
        
        # 绘制主编辑区域
        self.draw_editor_area()
        
        # 绘制侧边面板
        self.draw_side_panel()
    
    def draw_top_panel(self):
        """绘制顶部面板"""
        # 背景
        pygame.draw.rect(self.screen, self.PANEL_COLOR, 
                        (0, 0, self.WIDTH, self.TOP_PANEL_HEIGHT))
        pygame.draw.line(self.screen, self.BORDER_COLOR, 
                        (0, self.TOP_PANEL_HEIGHT), (self.WIDTH, self.TOP_PANEL_HEIGHT), 2)
        
        # 标题
        title = self.font.render("AI生命体生物编辑器", True, self.TEXT_COLOR)
        self.screen.blit(title, (self.WIDTH // 2 - title.get_width() // 2, 10))
        
        # 按钮
        self.draw_button(10, 10, 100, 30, "保存生物")
        self.draw_button(120, 10, 100, 30, "加载生物")
        self.draw_button(230, 10, 100, 30, "新建生物")
    
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
            if self.selected_tool == sensor:
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
            if self.selected_tool == actuator:
                pygame.draw.rect(self.screen, self.HIGHLIGHT_COLOR, 
                                (tool_pos[0] - 20, tool_pos[1] - 20, 40, 40), 3)
    
    def draw_side_panel(self):
        """绘制侧边面板"""
        # 背景
        pygame.draw.rect(self.screen, self.PANEL_COLOR, 
                        (self.WIDTH - self.SIDE_PANEL_WIDTH, 0, self.SIDE_PANEL_WIDTH, self.HEIGHT))
        pygame.draw.line(self.screen, self.BORDER_COLOR, 
                        (self.WIDTH - self.SIDE_PANEL_WIDTH, 0), 
                        (self.WIDTH - self.SIDE_PANEL_WIDTH, self.HEIGHT), 2)
        
        # 标题
        title = self.font.render("编辑器", True, self.TEXT_COLOR)
        self.screen.blit(title, (self.WIDTH - self.SIDE_PANEL_WIDTH + 10, 10))
        
        # 传感器标题
        sensor_title = self.small_font.render("传感器", True, self.TEXT_COLOR)
        self.screen.blit(sensor_title, (self.WIDTH - self.SIDE_PANEL_WIDTH + 10, 50))
        
        # 传感器按钮
        sensor_y = 60
        for sensor_type in self.tool_types["sensor"]:
            self.draw_button(self.WIDTH - self.SIDE_PANEL_WIDTH + 10, sensor_y, 
                            self.SIDE_PANEL_WIDTH - 20, 30, f"添加 {sensor_type}")
            sensor_y += 40
        
        # 效应器标题
        actuator_title = self.small_font.render("效应器", True, self.TEXT_COLOR)
        self.screen.blit(actuator_title, (self.WIDTH - self.SIDE_PANEL_WIDTH + 10, sensor_y + 10))
        
        # 效应器按钮
        actuator_y = sensor_y + 20
        for actuator_type in self.tool_types["actuator"]:
            self.draw_button(self.WIDTH - self.SIDE_PANEL_WIDTH + 10, actuator_y, 
                            self.SIDE_PANEL_WIDTH - 20, 30, f"添加 {actuator_type}")
            actuator_y += 40
        
        # 连接按钮
        connect_y = actuator_y + 20
        self.draw_button(self.WIDTH - self.SIDE_PANEL_WIDTH + 10, connect_y, 
                        self.SIDE_PANEL_WIDTH - 20, 30, "连接工具")
        
        # 记忆编辑标题
        memory_title = self.small_font.render("记忆基因", True, self.TEXT_COLOR)
        self.screen.blit(memory_title, (self.WIDTH - self.SIDE_PANEL_WIDTH + 10, connect_y + 50))
        
        # 绘制记忆基因列表
        self.draw_memory_list(connect_y + 60)
    
    def draw_memory_list(self, start_y):
        """绘制记忆基因列表"""
        all_memories = self.organism.memory_bank + self.organism.learned_memories
        
        for i, memory in enumerate(all_memories):
            memory_y = start_y + i * 40
            
            # 记忆背景
            memory_rect = pygame.Rect(self.WIDTH - self.SIDE_PANEL_WIDTH + 10, memory_y, 
                                    self.SIDE_PANEL_WIDTH - 20, 30)
            
            if self.selected_memory == memory:
                pygame.draw.rect(self.screen, self.HIGHLIGHT_COLOR, memory_rect, 2)
            else:
                pygame.draw.rect(self.screen, self.BORDER_COLOR, memory_rect, 1)
            
            # 记忆信息
            memory_text = f"{memory.situation[:15]}... (强度: {memory.strength:.2f})"
            text_surface = self.small_font.render(memory_text, True, self.TEXT_COLOR)
            self.screen.blit(text_surface, (self.WIDTH - self.SIDE_PANEL_WIDTH + 20, memory_y + 5))
        
        # 添加记忆按钮
        add_y = start_y + len(all_memories) * 40 + 20
        self.draw_button(self.WIDTH - self.SIDE_PANEL_WIDTH + 10, add_y, 
                        self.SIDE_PANEL_WIDTH - 20, 30, "添加记忆")
    
    def draw_button(self, x, y, width, height, text):
        """绘制按钮"""
        # 按钮背景
        pygame.draw.rect(self.screen, self.BUTTON_COLOR, (x, y, width, height))
        pygame.draw.rect(self.screen, self.BORDER_COLOR, (x, y, width, height), 2)
        
        # 按钮文本
        text_surface = self.small_font.render(text, True, self.TEXT_COLOR)
        text_x = x + (width - text_surface.get_width()) // 2
        text_y = y + (height - text_surface.get_height()) // 2
        self.screen.blit(text_surface, (text_x, text_y))

def main():
    """主函数"""
    editor = OrganismEditor()
    editor.run()

if __name__ == "__main__":
    main()
