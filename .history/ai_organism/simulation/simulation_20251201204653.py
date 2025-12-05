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
        self.font = pygame.font.Font("C:/Windows/Fonts/msyh.ttc", 24)
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
            {"cilia_1": 0.7, "muscle_1": 0.3, "muscle_2": 0.3},
            0.8
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
            if org.energy > 80 and random.random() < 0.01:
                child = org.reproduce()
                self.organisms.append(child)
                
            # 检查死亡
            if org.energy <= 0 or org.age > 1000:
                self.organisms.remove(org)
                if self.selected_organism == org:
                    self.selected_organism = None
                    
        # 偶尔添加新食物
        if random.random() < 0.02 and len(self.environment.foods) < 20:
            x = random.randint(50, self.width - 50)
            y = random.randint(50, self.height - 50)
            self.environment.add_food((x, y))
            
    def handle_click(self, pos):
        """处理鼠标点击"""
        for org in self.organisms:
            distance = ((org.position[0] - pos[0]) ** 2 + (org.position[1] - pos[1]) ** 2) ** 0.5
            if distance < org.radius:
                self.selected_organism = org
                return
                
        # 点击空白处添加食物
        self.environment.add_food(pos)
        
    def draw(self, surface):
        """绘制整个模拟"""
        # 清屏
        surface.fill((20, 20, 30))
        
        # 绘制环境
        self.environment.draw(surface)
        
        # 绘制所有生物
        for org in self.organisms:
            org.draw(surface)
            
        # 高亮选中的生物
        if self.selected_organism:
            pos = self.selected_organism.position.astype(int)
            pygame.draw.circle(surface, (255, 255, 255), pos, 
                             self.selected_organism.radius + 5, 2)
            
            # 绘制选中生物的信息
            self.draw_organism_info(surface, self.selected_organism)
            
        # 绘制模拟信息
        self.draw_simulation_info(surface)
        
    def draw_organism_info(self, surface, org):
        """绘制选中生物的信息"""
        font = pygame.font.Font("C:/Windows/Fonts/msyh.ttc", 24)
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
        font = pygame.font.Font("C:/Windows/Fonts/msyh.ttc", 24)
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
