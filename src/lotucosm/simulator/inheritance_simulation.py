"""Tool继承算法模拟器入口"""

import pygame
import random
from .simulation import Simulation


def main():
    """主函数 - 统一的编辑和模拟界面"""
    # 初始化Pygame
    pygame.init()
    WIDTH, HEIGHT = 1200, 800
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("AI生命体编辑器与模拟器")
    clock = pygame.time.Clock()
    
    # 加载适合中文显示的字体
    def load_chinese_font(size: int) -> pygame.font.Font:
        """加载适合中文显示的字体"""
        # 尝试使用常见的中文字体
        chinese_fonts = [
            "SimHei",  # 黑体
            "Microsoft YaHei",  # 微软雅黑
            "SimSun",  # 宋体
            "WenQuanYi Micro Hei",  # 文泉驿微米黑
        ]
        
        for font_name in chinese_fonts:
            try:
                font = pygame.font.SysFont(font_name, size)
                # 测试是否能渲染中文
                test_surface = font.render("测试", True, (255, 255, 255))
                if test_surface.get_width() > 0:
                    return font
            except:
                continue
        
        # 尝试获取系统默认字体
        try:
            return pygame.font.SysFont(None, size)
        except:
            # 最后回退到默认字体
            return pygame.font.Font(None, size)
    
    font = load_chinese_font(24)
    small_font = load_chinese_font(16)
    
    # 模式定义
    MODE_EDIT = "edit"  # 编辑模式
    MODE_SIMULATE = "simulate"  # 模拟模式
    current_mode = MODE_EDIT
    
    # 界面尺寸设置
    CONTROL_PANEL_WIDTH = 250
    SIMULATION_WIDTH = WIDTH - CONTROL_PANEL_WIDTH
    
    # 控制面板按钮尺寸
    BUTTON_WIDTH = 200
    BUTTON_HEIGHT = 40
    BUTTON_MARGIN = 10
    
    simulation = Simulation(WIDTH, HEIGHT)
    running = True
    
    # 性能优化参数
    target_fps = 60
    simulation_speed = 1  # 模拟速度倍率
    show_performance = False  # 是否显示性能信息
    
    print("AI生命体编辑器与模拟器启动!")
    print("功能说明:")
    print("- 左侧控制面板: 模式切换和参数调整")
    print("- 中央编辑区: 生物编辑和模拟运行")
    print("- 编辑模式: 添加传感器、效应器和连接")
    print("- 模拟模式: 观察生物行为和进化")
    
    # 性能监控变量
    frame_count = 0
    last_time = pygame.time.get_ticks()
    fps = 0
    
    try:
        while running:
            # 处理事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # 左键
                        # 检查是否点击了控制面板
                        if event.pos[0] > SIMULATION_WIDTH:
                            # 计算按钮区域
                            button_y = 50
                            # 模式切换按钮
                            if button_y <= event.pos[1] <= button_y + BUTTON_HEIGHT:
                                current_mode = MODE_SIMULATE if current_mode == MODE_EDIT else MODE_EDIT
                                print(f"切换到{current_mode}模式")
                            # 重置按钮
                            button_y += BUTTON_HEIGHT + BUTTON_MARGIN
                            if button_y <= event.pos[1] <= button_y + BUTTON_HEIGHT:
                                simulation = Simulation(WIDTH, HEIGHT)
                                print("重置模拟")
                            # 添加食物按钮
                            button_y += BUTTON_HEIGHT + BUTTON_MARGIN
                            if button_y <= event.pos[1] <= button_y + BUTTON_HEIGHT:
                                x = random.randint(50, SIMULATION_WIDTH - 50)
                                y = random.randint(50, HEIGHT - 50)
                                simulation.environment.add_food((x, y))
                                print("添加食物")
                            # 创建新生物按钮
                            button_y += BUTTON_HEIGHT + BUTTON_MARGIN
                            if button_y <= event.pos[1] <= button_y + BUTTON_HEIGHT:
                                x = random.randint(100, SIMULATION_WIDTH - 100)
                                y = random.randint(100, HEIGHT - 100)
                                simulation.create_test_organism()
                                simulation.organisms[-1].position = simulation.organisms[-1].position.copy()
                                simulation.organisms[-1].position[0] = x
                                simulation.organisms[-1].position[1] = y
                                print("创建新生物")
                        else:
                            # 点击编辑区域
                            simulation.handle_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:  # 按R重置
                        simulation = Simulation(WIDTH, HEIGHT)
                        print("重置模拟")
                    elif event.key == pygame.K_f:  # 按F添加食物到随机位置
                        x = random.randint(50, SIMULATION_WIDTH - 50)
                        y = random.randint(50, HEIGHT - 50)
                        simulation.environment.add_food((x, y))
                        print("添加食物")
                    elif event.key == pygame.K_n:  # 按N创建新生物
                        x = random.randint(100, SIMULATION_WIDTH - 100)
                        y = random.randint(100, HEIGHT - 100)
                        simulation.create_test_organism()
                        simulation.organisms[-1].position = simulation.organisms[-1].position.copy()
                        simulation.organisms[-1].position[0] = x
                        simulation.organisms[-1].position[1] = y
                        print("创建新生物")
                    elif event.key == pygame.K_PLUS or event.key == pygame.K_KP_PLUS or event.key == pygame.K_EQUALS:  # 按+提高模拟速度
                        simulation_speed = min(5, simulation_speed + 0.5)
                        print(f"模拟速度: {simulation_speed:.1f}x")
                    elif event.key == pygame.K_MINUS or event.key == pygame.K_UNDERSCORE:  # 按-降低模拟速度
                        simulation_speed = max(0.5, simulation_speed - 0.5)
                        print(f"模拟速度: {simulation_speed:.1f}x")
                    elif event.key == pygame.K_p:  # 按P显示/隐藏性能信息
                        show_performance = not show_performance
                        print(f"性能信息: {'显示' if show_performance else '隐藏'}")
                    elif event.key == pygame.K_v:  # 按V切换到查看模式
                        simulation.editor_mode = "view"
                        simulation.selected_objects = []
                        print("切换到查看模式")
                    elif event.key == pygame.K_s:  # 按S切换到添加传感器模式
                        simulation.editor_mode = "add_sensor"
                        simulation.selected_objects = []
                        print("切换到添加传感器模式")
                    elif event.key == pygame.K_a:  # 按A切换到添加效应器模式
                        simulation.editor_mode = "add_actuator"
                        simulation.selected_objects = []
                        print("切换到添加效应器模式")
                    elif event.key == pygame.K_c:  # 按C切换到连接工具模式
                        simulation.editor_mode = "connect"
                        simulation.selected_objects = []
                        simulation.connection_source = None
                        print("切换到连接工具模式")
                    elif event.key == pygame.K_DELETE:  # 按Delete删除选中工具
                        if simulation.selected_organism and simulation.selected_objects:
                            for obj in simulation.selected_objects:
                                if obj in list(simulation.selected_organism.sensors.values()):
                                    del simulation.selected_organism.sensors[obj.id]
                                elif obj in list(simulation.selected_organism.actuators.values()):
                                    del simulation.selected_organism.actuators[obj.id]
                                    if obj.id in simulation.selected_organism.control_signals:
                                        del simulation.selected_organism.control_signals[obj.id]
                            # 删除相关连接
                            from typing import Dict, List
                            connections_to_remove: List[Dict[str, str]] = []
                            for conn in simulation.selected_organism.connections:
                                for obj in simulation.selected_objects:
                                    if conn['source'] == obj.id or conn['target'] == obj.id:
                                        connections_to_remove.append(conn)
                            for conn in connections_to_remove:
                                simulation.selected_organism.connections.remove(conn)
                            # 更新源工具的连接列表
                            from vitalloom.components.components_base import ComponentBase
                            all_components: List[ComponentBase] = list(simulation.selected_organism.sensors.values()) + list(simulation.selected_organism.actuators.values())
                            for _ in all_components:
                                # 这里不需要更新组件的connections列表，因为organism.connections是连接的主要存储位置
                                pass
                            simulation.selected_objects = []
                            print("已删除选中工具")
            
            # 更新模拟（仅在模拟模式下）
            if current_mode == MODE_SIMULATE:
                if simulation_speed >= 1:
                    for _ in range(int(simulation_speed)):
                        simulation.update()
                else:
                    # 慢速模式，随机更新
                    if random.random() < simulation_speed:
                        simulation.update()
            
            # 绘制
            simulation.draw(screen)
            
            # 绘制控制面板
            # 1. 绘制面板背景
            panel_rect = pygame.Rect(SIMULATION_WIDTH, 0, CONTROL_PANEL_WIDTH, HEIGHT)
            pygame.draw.rect(screen, (30, 30, 40), panel_rect)
            pygame.draw.line(screen, (60, 60, 60), (SIMULATION_WIDTH, 0), (SIMULATION_WIDTH, HEIGHT), 2)
            
            # 2. 绘制标题
            title_text = font.render("控制面板", True, (255, 255, 255))
            screen.blit(title_text, (SIMULATION_WIDTH + 20, 10))
            
            # 3. 绘制按钮
            button_y = 50
            
            # 模式切换按钮
            button_rect = pygame.Rect(SIMULATION_WIDTH + 25, button_y, BUTTON_WIDTH, BUTTON_HEIGHT)
            pygame.draw.rect(screen, (60, 60, 80), button_rect)
            pygame.draw.rect(screen, (80, 80, 100), button_rect, 2)
            button_text = small_font.render("切换到模拟模式" if current_mode == MODE_EDIT else "切换到编辑模式", True, (255, 255, 255))
            text_rect = button_text.get_rect(center=button_rect.center)
            screen.blit(button_text, text_rect)
            
            # 重置按钮
            button_y += BUTTON_HEIGHT + BUTTON_MARGIN
            button_rect = pygame.Rect(SIMULATION_WIDTH + 25, button_y, BUTTON_WIDTH, BUTTON_HEIGHT)
            pygame.draw.rect(screen, (60, 60, 80), button_rect)
            pygame.draw.rect(screen, (80, 80, 100), button_rect, 2)
            button_text = small_font.render("重置模拟", True, (255, 255, 255))
            text_rect = button_text.get_rect(center=button_rect.center)
            screen.blit(button_text, text_rect)
            
            # 添加食物按钮
            button_y += BUTTON_HEIGHT + BUTTON_MARGIN
            button_rect = pygame.Rect(SIMULATION_WIDTH + 25, button_y, BUTTON_WIDTH, BUTTON_HEIGHT)
            pygame.draw.rect(screen, (60, 60, 80), button_rect)
            pygame.draw.rect(screen, (80, 80, 100), button_rect, 2)
            button_text = small_font.render("添加食物", True, (255, 255, 255))
            text_rect = button_text.get_rect(center=button_rect.center)
            screen.blit(button_text, text_rect)
            
            # 创建新生物按钮
            button_y += BUTTON_HEIGHT + BUTTON_MARGIN
            button_rect = pygame.Rect(SIMULATION_WIDTH + 25, button_y, BUTTON_WIDTH, BUTTON_HEIGHT)
            pygame.draw.rect(screen, (60, 60, 80), button_rect)
            pygame.draw.rect(screen, (80, 80, 100), button_rect, 2)
            button_text = small_font.render("创建新生物", True, (255, 255, 255))
            text_rect = button_text.get_rect(center=button_rect.center)
            screen.blit(button_text, text_rect)
            
            # 绘制当前模式
            mode_text = font.render(f"当前模式: {'编辑' if current_mode == MODE_EDIT else '模拟'}", True, (255, 255, 255))
            screen.blit(mode_text, (10, HEIGHT - 60))
            
            # 显示按键提示
            keys_text = small_font.render(f"按键: R-重置 F-加食物 N-新生物 +/--速度 {simulation_speed:.1f}x", True, (255, 255, 255))
            screen.blit(keys_text, (WIDTH // 2 - 200, HEIGHT - 30))
            
            # 显示性能信息
            if show_performance:
                frame_count += 1
                current_time = pygame.time.get_ticks()
                if current_time - last_time >= 1000:
                    fps = frame_count
                    frame_count = 0
                    last_time = current_time
                
                performance_text = small_font.render(f"FPS: {fps} | 生物数: {len(simulation.organisms)} | 食物数: {len(simulation.environment.foods)}", True, (255, 255, 255))
                screen.blit(performance_text, (10, HEIGHT - 30))
            
            pygame.display.flip()
            clock.tick(target_fps)
    except Exception as e:
        print(f"\n错误: 模拟器运行失败 - {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 确保Pygame资源被正确释放
        pygame.quit()
        print("Tool继承算法模拟器已关闭")


if __name__ == "__main__":
    main()
