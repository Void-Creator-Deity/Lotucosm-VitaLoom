"""PS Pygame 演示模拟器：Environment + Organism 编辑器壳（非 SR 主路径）。

架构数据流::

    Simulation.update → Organism.update(environment) → 本地 pygame 绘制

SR 边界: 编辑器「播放」走 `GameViewport` + 场景运行时；**不**实例化本 `Simulation` 类。

排错: 见 `builtin/README.md`（与 SR 混谈、Pygame 窗无生物）。
"""
import random
try:
    import pygame
except ImportError:  # pragma: no cover - 运行环境可能不带 pygame
    pygame = None
from typing import List, Optional, Tuple, Any
from builtin.entity_types.organism import Organism
from core.Lotucosm.pond import Pond
from builtin.components.sensors import TouchSensor, LightSensor
from builtin.components.actuators import MuscleActuator, CiliaActuator
from builtin.systems.environment import Environment


class Simulation:
    """PS 独立 Pygame 窗口演示；生命周期为构造→`update` 循环→可选 `main()` 入口。"""
    
    def __init__(self, width: int = 1200, height: int = 800):
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
        import pygame
        if not pygame.get_init():
            pygame.init()
            
        self.width = width  # 模拟窗口宽度
        self.height = height  # 模拟窗口高度
        self.organisms: List[Organism] = []  # 生物列表
        self.environment = Environment()  # 环境对象
        self.selected_organism: Optional[Organism] = None  # 选中的生物
        self.time = 0  # 模拟时间
        
        # 编辑器颜色 - 先初始化，确保draw方法可以访问
        self.BACKGROUND_COLOR = (20, 20, 30)  # 背景颜色
        self.PANEL_COLOR = (30, 30, 40)  # 面板颜色
        self.TEXT_COLOR = (255, 255, 255)  # 文本颜色
        self.HIGHLIGHT_COLOR = (0, 200, 255)  # 高亮颜色
        self.BORDER_COLOR = (100, 100, 100)  # 边框颜色
        
        # 缓存字体对象，避免频繁加载
        self.font = self._load_font(24)  # 字体对象
        
        # 编辑模式支持
        self.editor_mode = "view"  # 编辑器模式: view, add_sensor, add_actuator, connect
        self.selected_tool = None  # 选中的工具
        self.selected_objects: List[Any] = []  # 选中的对象列表
        self.dragging_tool: Optional[Any] = None  # 正在拖动的工具
        self.connection_source: Optional[Any] = None  # 连接源工具
        
        self.setup_test_environment()  # 设置测试环境
    
    def _load_font(self, size: int):
        """加载适合中文显示的字体"""
        if pygame is None:
            return None
        if not pygame.font.get_init():
            return None
        
        # 尝试使用常见的中文字体
        chinese_fonts = [
            "SimHei",  # 黑体
            "Microsoft YaHei",  # 微软雅黑
            "SimSun",  # 宋体
            "WenQuanYi Micro Hei",  # 文泉驿微米黑
            "Heiti TC",  # 黑体（繁体）
            "Apple LiGothic Medium",  # Apple丽黑
        ]
        
        for font_name in chinese_fonts:
            try:
                font = pygame.font.SysFont(font_name, size)
                # 测试是否能渲染中文
                test_surface = font.render("测试", True, (255, 255, 255))
                if test_surface.get_width() > 0:
                    return font
            except Exception:
                continue
        
        # 尝试获取系统默认字体
        try:
            font = pygame.font.SysFont(None, size)
            return font
        except Exception:
            try:
                # 最后回退到默认字体
                return pygame.font.Font(None, size)
            except Exception:
                # 所有尝试都失败，返回None
                return None
        
    def setup_test_environment(self):
        """初始化演示用食物、光源、障碍物与一只测试生物。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

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
        """构造带 Touch/Light 传感器与 Muscle/Cilia 的演示 Organism 及连接。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        org = Organism("org_1", (self.width // 2, self.height // 2))
        
        # 添加传感器
        touch1 = TouchSensor("touch_1", organism_id=org.id, position=(-20, 0))
        touch2 = TouchSensor("touch_2", organism_id=org.id, position=(0, -20))
        light_sensor = LightSensor("light_1", organism_id=org.id, position=(20, 0))
        
        org.add_sensor(touch1)
        org.add_sensor(touch2)
        org.add_sensor(light_sensor)
        
        # 添加效应器
        muscle1 = MuscleActuator("muscle_1", organism_id=org.id, position=(-15, 15))
        muscle2 = MuscleActuator("muscle_2", organism_id=org.id, position=(15, 15))
        muscle3 = MuscleActuator("muscle_3", organism_id=org.id, position=(0, -15))
        cilia = CiliaActuator("cilia_1", organism_id=org.id, position=(0, 20))
        
        org.add_actuator(muscle1)
        org.add_actuator(muscle2)
        org.add_actuator(muscle3)
        org.add_actuator(cilia)
        
        # 添加一些基础连接（非条件反射）
        org.connect_tools("touch_1", "muscle_1")  # 左边碰到东西 -> 左边肌肉收缩
        org.connect_tools("touch_2", "muscle_3")  # 上边碰到东西 -> 上边肌肉收缩
        org.connect_tools("light_1", "cilia_1")   # 看到光 -> 纤毛运动
        
        # 添加基础记忆
        from core.Lotucosm.memory import MemoryGene
        base_memory = MemoryGene(
            "LIGHT_high",
            {"cilia_1": 0.7*random.uniform(0.8, 1.2), "muscle_1": 0.3*random.uniform(0.8, 1.2), "muscle_2": 0.3*random.uniform(0.8, 1.2)},
            0.8*random.uniform(0.8, 1.2)
        )
        org.memory_genes.append(base_memory)
        
        self.organisms.append(org)
        self.selected_organism = org
        
    def update(self) -> None:
        """推进一帧：生物 update、繁殖/死亡、环境补食物与清理。

        职责: `time` 自增；遍历 `organisms` 调用 `org.update(1.0, environment)`。
        时机: Pygame 主循环每帧；**非** VitaLoom SR tick。
        不变量: 迭代时用切片 `organisms[:]` 避免删除时修改列表。
        排错: 列表为空 → 须先 `create_test_organism`；与 SR 人口无关（见 README）。
        """
        self.time += 1  # 增加模拟时间

        # 更新所有生物，使用切片避免修改列表时的迭代问题
        for org in self.organisms[:]:
            org.update(1.0, self.environment)  # 更新生物状态
            
            # 检查繁殖条件：能量充足且随机概率
            if org.energy > 100 and random.random() < 0.01:
                child = org.reproduce()  # 繁殖后代
                if child is not None:
                    self.organisms.append(child)  # 将后代添加到生物列表
                
            # 检查死亡条件：能量耗尽或年龄过大
            if org.energy <= 0 or org.age > 1000:
                self.organisms.remove(org)  # 从列表中移除死亡的生物
                if self.selected_organism == org:
                    self.selected_organism = None  # 取消选中
                    
        # 偶尔添加新食物，保持食物数量在合理范围
        if random.random() < 0.01 and len(self.environment.foods) < 20:
            x = random.randint(50, self.width - 50)
            y = random.randint(50, self.height - 50)
            self.environment.add_food((x, y))

        # 更新环境内容（清理已被吃掉的食物等）
        self.environment.update(1.0)

            
    def handle_click(self, pos: Tuple[int, int]) -> None:
        """处理鼠标点击。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

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
    
    def get_tool_at_pos(self, pos: Tuple[int, int], org: Organism) -> Optional[Any]:
        """获取指定位置的工具。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

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
    
    def select_tool(self, tool: Any) -> None:
        """选择工具。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self.selected_objects = [tool]
    
    def add_sensor_at_pos(self, pos: Tuple[int, int]) -> None:
        """在指定位置添加传感器。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if not self.selected_organism:
            return
        
        org_pos = self.selected_organism.position.astype(int)
        rel_pos = (pos[0] - org_pos[0], pos[1] - org_pos[1])
        
        # 添加光感传感器
        sensor_id = f"light_{len(self.selected_organism.sensors) + 1}"
        sensor = LightSensor(sensor_id, organism_id=self.selected_organism.id, attach_point=rel_pos)
        self.selected_organism.add_sensor(sensor)
        self.selected_objects = [sensor]
    
    def add_actuator_at_pos(self, pos: Tuple[int, int]) -> None:
        """在指定位置添加效应器。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if not self.selected_organism:
            return
        
        org_pos = self.selected_organism.position.astype(int)
        rel_pos = (pos[0] - org_pos[0], pos[1] - org_pos[1])
        
        # 添加肌肉效应器
        actuator_id = f"muscle_{len(self.selected_organism.actuators) + 1}"
        actuator = MuscleActuator(actuator_id, organism_id=self.selected_organism.id, attach_point=rel_pos)
        self.selected_organism.add_actuator(actuator)
        self.selected_objects = [actuator]
    
    def handle_connection_click(self, pos: Tuple[int, int]) -> None:
        """处理连接模式下的点击。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if not self.selected_organism:
            return
        
        clicked_tool = self.get_tool_at_pos(pos, self.selected_organism)
        if clicked_tool:
            if not self.connection_source:
                self.connection_source = clicked_tool
            else:
                # 创建连接
                source_id = self.connection_source.id
                target_id = clicked_tool.id
                self.selected_organism.connect_tools(source_id, target_id)
                self.connection_source = None
                self.editor_mode = "view"
        
    def draw(self, surface: Any):
        """绘制整个模拟。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 清屏（只清理模拟区域）
        simulation_rect = pygame.Rect(0, 0, surface.get_width() - 250, surface.get_height())
        surface.fill(self.BACKGROUND_COLOR, simulation_rect)
        
        # 绘制环境
        self.environment.draw(surface)
        
        # 绘制所有生物
        for org in self.organisms:
            org.draw(surface)
            
            # 高亮选中的生物
            if org == self.selected_organism:
                pos = tuple(org.position.astype(int))
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
        
    def draw_editor_mode(self, surface: Any):
        """绘制编辑模式提示。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

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
            
            # 按钮文字 - 安全处理
            font = self._load_font(16)
            if font:
                text_surface = font.render(text, True, self.TEXT_COLOR)
                text_rect = text_surface.get_rect(center=button_rect.center)
                surface.blit(text_surface, text_rect)
        
        # 绘制编辑模式提示
        mode_text = f"当前模式: {self.editor_mode}"
        if self.editor_mode == "connect":
            if hasattr(self, 'connection_source') and self.connection_source:
                mode_text += f" - 选择目标工具 (已选择: {self.connection_source.id})"
            else:
                mode_text += " - 选择源工具"
        
        # 安全处理字体
        font = self._load_font(18)
        if font:
            text_surface = font.render(mode_text, True, self.TEXT_COLOR)
            surface.blit(text_surface, (10, 50))
        
    def draw_organism_info(self, surface: Any, org: Organism):
        """绘制选中生物的信息。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 安全获取字体
        font = self.font
        if not font:
            # 字体不可用，跳过绘制信息
            return
            
        info_lines = [
            f"生物: {org.id}",
            f"世代: {org.generation}",
            f"能量: {org.energy:.1f}",
            f"年龄: {org.age}",
            f"行动: {org.current_action}",
            f"记忆数: {len(org.inherited_memories)}遗传 + {len(org.learned_memories)}学习",
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
                
    def draw_simulation_info(self, surface: Any):
        """绘制模拟信息。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 安全获取字体
        font = self.font
        if not font:
            # 字体不可用，跳过绘制信息
            return
            
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


def main():
    """命令行交互主函数"""
    print("🌌 莲池宇宙 · 生命织机 - 命令行交互模式")
    print("=" * 50)
    print("这是命令行交互模式，用于简单测试和调试。")
    print("如需完整功能，请使用图形化启动器或Pygame模拟器。")
    print("=" * 50)
    
    # 示例：创建一个简单的模拟
    from builtin.systems.simulation import Simulation
    
    print("\n1. 初始化模拟环境...")
    simulation = Simulation(800, 600)
    
    print("\n2. 创建测试生物...")
    simulation.create_test_organism()
    
    print(f"\n3. 初始生物数量: {len(simulation.organisms)}")
    
    # 运行简单模拟
    print("\n4. 运行100次模拟迭代...")
    for i in range(100):
        simulation.update()
        if i % 10 == 0:
            print(f"   迭代 {i}: 生物={len(simulation.organisms)}, 食物={len(simulation.environment.foods)}")
    
    print("\n5. 最终状态:")
    print(f"   生物数量: {len(simulation.organisms)}")
    print(f"   食物数量: {len(simulation.environment.foods)}")
    print(f"   模拟时间: {simulation.time}")
    
    print("\n6. 命令行模式测试完成！")
    print("如需完整功能，请使用图形化启动器。")


if __name__ == "__main__":
    # 运行命令行交互模式
    main()
