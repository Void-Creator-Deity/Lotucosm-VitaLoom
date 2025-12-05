"""模拟器实现"""

import random
import pygame
from ..core import Organism
from ..environment import Environment
from ..tools import TouchSensor, LightSensor, MuscleActuator, CiliaActuator


class Simulation:
    """模拟器主类"""
    
    def __init__(self, width: int = 1200, height: int = 800):
        self.width = width
        self.height = height
        self.organisms = []
        self.environment = Environment()
        self.selected_organism = None
        self.time = 0
        # 缓存字体对象，避免频繁加载
        try:
            # 尝试使用系统字体
            self.font = pygame.font.SysFont(None, 24)
        except:
            # 回退到默认字体
            self.font = pygame.font.Font(None, 24)
        
        # 编辑模式支持
        self.editor_mode = "view"  # view, add_sensor, add_actuator, connect
        self.selected_tool = None
        self.selected_objects = []
        self.dragging_tool = None
        self.connection_source = None
        
        # 编辑器颜色
        self.BACKGROUND_COLOR = (20, 20, 30)
        self.PANEL_COLOR = (30, 30, 40)
        self.TEXT_COLOR = (255, 255, 255)
        self.HIGHLIGHT_COLOR = (0, 200, 255)
        self.BORDER_COLOR = (100, 100, 100)
        self.setup_test_environment()
        
    def setup_test_environment(self):
        """设置测试环境"""
        # 添加食物
        for _ in range(15):
            x = random.randint(50, self.width - 50)
            y = random.randint(50, self.height - 50)
            self.environment.add_food((x, y))
            
        # 添加光源
        self.environment.add_light_source((self.width // 2, self.height // 2), 2.0)
        self.environment.add_light_source((self.width // 4, self.height // 4), 1.5)
        
        # 添加障碍物
        for _ in range(5):
            x = random.randint(100, self.width - 100)
            y = random.randint(100, self.height - 100)
            self.environment.add_obstacle((x, y), random.randint(20, 40))
            
        # 创建初始生物
        self.create_test_organism()
        
    def create_test_organism(self):
        """创建测试生物"""
        org = Organism("org_1", (self.width // 2, self.height // 2))
        
        # 添加传感器
        touch1 = TouchSensor("touch_1", (-20, 0))
        touch2 = TouchSensor("touch_2", (0, -20))
        light_sensor = LightSensor("light_1", (20, 0))
        
        org.add_sensor(touch1)
        org.add_sensor(touch2)
        org.add_sensor(light_sensor)
        
        # 添加效应器
        muscle1 = MuscleActuator("muscle_1", (-15, 15))
        muscle2 = MuscleActuator("muscle_2", (15, 15))
        muscle3 = MuscleActuator("muscle_3", (0, -15))
        cilia = CiliaActuator("cilia_1", (0, 20))
        
        org.add_actuator(muscle1)
        org.add_actuator(muscle2)
        org.add_actuator(muscle3)
        org.add_actuator(cilia)
        
        # 添加一些基础连接（非条件反射）
        org.connect_tools("touch_1", "muscle_1", 1.0)  # 左边碰到东西 -> 左边肌肉收缩
        org.connect_tools("touch_2", "muscle_3", 1.0)  # 上边碰到东西 -> 上边肌肉收缩
        org.connect_tools("light_1", "cilia_1", 0.8)   # 看到光 -> 纤毛运动
        
        # 添加基础记忆
        from ..core import MemoryGene
        base_memory = MemoryGene(
            "LIGHT_high",
            {"cilia_1": 0.7*random.uniform(0.8, 1.2), "muscle_1": 0.3*random.uniform(0.8, 1.2), "muscle_2": 0.3*random.uniform(0.8, 1.2)},
            0.8*random.uniform(0.8, 1.2)
        )
        org.memory_bank.append(base_memory)
        
        self.organisms.append(org)
        self.selected_organism = org
        
    def update(self):
        """更新模拟"""
        self.time += 1
        
        # 更新所有生物
        for org in self.organisms[:]:  # 使用切片避免修改问题
            org.update(self.environment)
            
            # 检查繁殖条件
            if org.energy > 100 and random.random() < 0.01:
                child = org.reproduce()
                self.organisms.append(child)
                
            # 检查死亡
            if org.energy <= 0 or org.age > 1000:
                self.organisms.remove(org)
                if self.selected_organism == org:
                    self.selected_organism = None
                    
        # 偶尔添加新食物
        if random.random() < 0.01 and len(self.environment.foods) < 20:
            x = random.randint(50, self.width - 50)
            y = random.randint(50, self.height - 50)
            self.environment.add_food((x, y))
            
    def handle_click(self, pos):
        """处理鼠标点击"""
        if self.selected_organism:
            if self.editor_mode == "view":
                # 查看模式下，先检查是否点击了工具
                clicked_tool = self.get_tool_at_pos(pos, self.selected_organism)
                if clicked_tool:
                    self.select_tool(clicked_tool)
                else:
                    # 检查是否点击了其他生物
                    for org in self.organisms:
                        distance = ((org.position[0] - pos[0]) ** 2 + (org.position[1] - pos[1]) ** 2) ** 0.5
                        if distance < org.radius:
                            self.selected_organism = org
                            self.selected_objects = []
                            return
                    # 点击空白处添加食物
                    self.environment.add_food(pos)
            elif self.editor_mode == "add_sensor":
                self.add_sensor_at_pos(pos)
            elif self.editor_mode == "add_actuator":
                self.add_actuator_at_pos(pos)
            elif self.editor_mode == "connect":
                self.handle_connection_click(pos)
        else:
            # 没有选中生物，先选择生物
            for org in self.organisms:
                distance = ((org.position[0] - pos[0]) ** 2 + (org.position[1] - pos[1]) ** 2) ** 0.5
                if distance < org.radius:
                    self.selected_organism = org
                    self.selected_objects = []
                    return
            # 点击空白处添加食物
            self.environment.add_food(pos)
    
    def get_tool_at_pos(self, pos, org):
        """获取指定位置的工具"""
        # 检查传感器
        for sensor in org.sensors.values():
            tool_pos = (org.position[0] + sensor.position[0], org.position[1] + sensor.position[1])
            distance = ((tool_pos[0] - pos[0]) ** 2 + (tool_pos[1] - pos[1]) ** 2) ** 0.5
            if distance < 15:
                return sensor
        
        # 检查效应器
        for actuator in org.actuators.values():
            tool_pos = (org.position[0] + actuator.position[0], org.position[1] + actuator.position[1])
            distance = ((tool_pos[0] - pos[0]) ** 2 + (tool_pos[1] - pos[1]) ** 2) ** 0.5
            if distance < 15:
                return actuator
        
        return None
    
    def select_tool(self, tool):
        """选择工具"""
        self.selected_objects = [tool]
    
    def add_sensor_at_pos(self, pos):
        """在指定位置添加传感器"""
        if not self.selected_organism:
            return
        
        org_pos = self.selected_organism.position.astype(int)
        rel_pos = (pos[0] - org_pos[0], pos[1] - org_pos[1])
        
        # 添加光感传感器
        sensor_id = f"light_{len(self.selected_organism.sensors) + 1}"
        sensor = LightSensor(sensor_id, rel_pos)
        self.selected_organism.add_sensor(sensor)
        self.selected_objects = [sensor]
    
    def add_actuator_at_pos(self, pos):
        """在指定位置添加效应器"""
        if not self.selected_organism:
            return
        
        org_pos = self.selected_organism.position.astype(int)
        rel_pos = (pos[0] - org_pos[0], pos[1] - org_pos[1])
        
        # 添加肌肉效应器
        actuator_id = f"muscle_{len(self.selected_organism.actuators) + 1}"
        actuator = MuscleActuator(actuator_id, rel_pos)
        self.selected_organism.add_actuator(actuator)
        self.selected_objects = [actuator]
    
    def handle_connection_click(self, pos):
        """处理连接模式下的点击"""
        if not self.selected_organism:
            return
        
        clicked_tool = self.get_tool_at_pos(pos, self.selected_organism)
        if clicked_tool:
            if not self.connection_source:
                self.connection_source = clicked_tool
            else:
                # 创建连接
                source_id = self.connection_source.tool_id
                target_id = clicked_tool.tool_id
                self.selected_organism.connect_tools(source_id, target_id)
                self.connection_source = None
                self.editor_mode = "view"
        
    def draw(self, surface):
        """绘制整个模拟"""
        # 清屏
        surface.fill(self.BACKGROUND_COLOR)
        
        # 绘制环境
        self.environment.draw(surface)
        
        # 绘制所有生物
        for org in self.organisms:
            org.draw(surface)
            
            # 高亮选中的生物
            if org == self.selected_organism:
                pos = org.position.astype(int)
                pygame.draw.circle(surface, (255, 255, 255), pos, 
                                 org.radius + 5, 2)
                
                # 高亮选中的工具
                for obj in self.selected_objects:
                    if obj in list(org.sensors.values()) + list(org.actuators.values()):
                        tool_pos = (int(pos[0] + obj.position[0]), int(pos[1] + obj.position[1]))
                        if hasattr(obj, 'radius'):
                            pygame.draw.circle(surface, self.HIGHLIGHT_COLOR, tool_pos, 
                                             obj.radius + 5, 3)
                        else:
                            # 效应器通常是矩形
                            pygame.draw.rect(surface, self.HIGHLIGHT_COLOR, 
                                           (tool_pos[0] - 20, tool_pos[1] - 20, 40, 40), 3)
        
        # 绘制编辑模式提示
        self.draw_editor_mode(surface)
            
        # 绘制选中生物的信息
        if self.selected_organism:
            self.draw_organism_info(surface, self.selected_organism)
            
        # 绘制模拟信息
        self.draw_simulation_info(surface)
        
    def draw_editor_mode(self, surface):
        """绘制编辑模式提示"""
        # 绘制编辑模式按钮
        editor_buttons = [
            ("查看模式 (V)", "view", 10, 10),
            ("添加传感器 (S)", "add_sensor", 150, 10),
            ("添加效应器 (A)", "add_actuator", 300, 10),
            ("连接工具 (C)", "connect", 450, 10)
        ]
        
        for text, mode, x, y in editor_buttons:
            # 按钮背景
            color = self.PANEL_COLOR
            if self.editor_mode == mode:
                color = (80, 80, 100)
            
            button_rect = pygame.Rect(x, y, 140, 30)
            pygame.draw.rect(surface, color, button_rect)
            pygame.draw.rect(surface, self.BORDER_COLOR, button_rect, 2)
            
            # 按钮文字
            try:
                font = pygame.font.SysFont(None, 16)
            except:
                font = pygame.font.Font(None, 16)
            text_surface = font.render(text, True, self.TEXT_COLOR)
            text_rect = text_surface.get_rect(center=button_rect.center)
            surface.blit(text_surface, text_rect)
        
        # 绘制编辑模式提示
        mode_text = f"当前模式: {self.editor_mode}"
        if self.editor_mode == "connect":
            if hasattr(self, 'connection_source') and self.connection_source:
                mode_text += f" - 选择目标工具 (已选择: {self.connection_source.tool_id})"
            else:
                mode_text += " - 选择源工具"
        
        font = pygame.font.Font("C:/Windows/Fonts/msyh.ttc", 18)
        text_surface = font.render(mode_text, True, self.TEXT_COLOR)
        surface.blit(text_surface, (10, 50))
        
    def draw_organism_info(self, surface, org):
        """绘制选中生物的信息"""
        font = self.font
        info_lines = [
            f"生物: {org.id}",
            f"世代: {org.generation}",
            f"能量: {org.energy:.1f}",
            f"年龄: {org.age}",
            f"行动: {org.current_action}",
            f"记忆数: {len(org.memory_bank)}遗传 + {len(org.learned_memories)}学习",
            f"传感器: {len(org.sensors)} 效应器: {len(org.actuators)}"
        ]
        
        # 绘制背景
        info_rect = pygame.Rect(10, 10, 250, len(info_lines) * 25 + 10)
        pygame.draw.rect(surface, (0, 0, 0, 180), info_rect)
        pygame.draw.rect(surface, (255, 255, 255), info_rect, 2)
        
        # 绘制文本
        for i, line in enumerate(info_lines):
            text = font.render(line, True, (255, 255, 255))
            surface.blit(text, (20, 15 + i * 25))
            
        # 绘制控制信号
        control_y = info_rect.bottom + 10
        if org.control_signals:
            control_text = font.render("控制信号:", True, (255, 255, 255))
            surface.blit(control_text, (20, control_y))
            
            for j, (tool_id, signal) in enumerate(org.control_signals.items()):
                signal_color = (100, 255, 100) if signal > 0 else (255, 100, 100)
                signal_text = font.render(f"  {tool_id}: {signal:.2f}", True, signal_color)
                surface.blit(signal_text, (20, control_y + 25 + j * 20))
                
    def draw_simulation_info(self, surface):
        """绘制模拟信息"""
        font = self.font
        info_lines = [
            f"时间: {self.time}",
            f"生物数量: {len(self.organisms)}",
            f"食物数量: {len(self.environment.foods)}",
            "点击生物选择，点击空地添加食物"
        ]
        
        # 绘制在右上角
        for i, line in enumerate(info_lines):
            text = font.render(line, True, (255, 255, 255))
            surface.blit(text, (self.width - 250, 10 + i * 25))
