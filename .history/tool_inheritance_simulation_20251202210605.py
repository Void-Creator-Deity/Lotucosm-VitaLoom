"""Tool继承算法模拟器入口"""

import pygame
import random
from ai_organism.simulation import Simulation


def main():
    """主函数"""
    # 初始化Pygame
    pygame.init()
    WIDTH, HEIGHT = 1200, 800
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tool继承算法模拟器")
    clock = pygame.time.Clock()
    font = pygame.font.Font("C:/Windows/Fonts/msyh.ttc", 24)
    
    simulation = Simulation(WIDTH, HEIGHT)
    running = True
    
    # 性能优化参数
    target_fps = 60
    simulation_speed = 1  # 模拟速度倍率
    show_performance = False  # 是否显示性能信息
    
    print("Tool继承算法模拟器启动!")
    print("功能说明:")
    print("- 绿色圆圈: 触觉传感器")
    print("- 黄色太阳: 光感传感器") 
    print("- 红色条状: 肌肉效应器")
    print("- 青色波浪: 纤毛效应器")
    print("- 蓝色线条: Tool连接")
    print("- 点击生物查看详细信息")
    print("- 点击空地添加食物")
    print("- 按+/-调整模拟速度")
    print("- 按P显示/隐藏性能信息")
    print("- 按S降低画质/按Q提高画质")
    
    # 性能监控变量
    frame_count = 0
    last_time = pygame.time.get_ticks()
    fps = 0
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键
                    simulation.handle_click(event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # 按R重置
                    simulation = Simulation(WIDTH, HEIGHT)
                elif event.key == pygame.K_f:  # 按F添加食物到随机位置
                    x = random.randint(50, WIDTH - 50)
                    y = random.randint(50, HEIGHT - 50)
                    simulation.environment.add_food((x, y))
                elif event.key == pygame.K_n:  # 按N创建新生物
                    x = random.randint(100, WIDTH - 100)
                    y = random.randint(100, HEIGHT - 100)
                    simulation.create_test_organism()
                    simulation.organisms[-1].position = simulation.organisms[-1].position.copy()
                    simulation.organisms[-1].position[0] = x
                    simulation.organisms[-1].position[1] = y
                elif event.key == pygame.K_PLUS or event.key == pygame.K_KP_PLUS:  # 按+提高模拟速度
                    simulation_speed = min(5, simulation_speed + 0.5)
                    print(f"模拟速度: {simulation_speed}x")
                elif event.key == pygame.K_MINUS or event.key == pygame.K_KP_MINUS:  # 按-降低模拟速度
                    simulation_speed = max(0.5, simulation_speed - 0.5)
                    print(f"模拟速度: {simulation_speed}x")
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
                elif event.key == pygame.K_q:  # 按Q提高画质
                    print("提高画质功能尚未实现")
                elif event.key == pygame.K_EQUALS:  # 按=键（主键盘）提高模拟速度
                    simulation_speed = min(5, simulation_speed + 0.5)
                    print(f"模拟速度: {simulation_speed}x")
                elif event.key == pygame.K_MINUS:  # 按-键（主键盘）降低模拟速度
                    simulation_speed = max(0.5, simulation_speed - 0.5)
                    print(f"模拟速度: {simulation_speed}x")
                elif event.key == pygame.K_DELETE:  # 按Delete删除选中工具
                    if simulation.selected_organism and simulation.selected_objects:
                        for obj in simulation.selected_objects:
                            if obj in list(simulation.selected_organism.sensors.values()):
                                del simulation.selected_organism.sensors[obj.tool_id]
                            elif obj in list(simulation.selected_organism.actuators.values()):
                                del simulation.selected_organism.actuators[obj.tool_id]
                                if obj.tool_id in simulation.selected_organism.control_signals:
                                    del simulation.selected_organism.control_signals[obj.tool_id]
                        # 删除相关连接
                        connections_to_remove = []
                        for conn in simulation.selected_organism.connections:
                            for obj in simulation.selected_objects:
                                if conn.source.tool_id == obj.tool_id or conn.target.tool_id == obj.tool_id:
                                    connections_to_remove.append(conn)
                        for conn in connections_to_remove:
                            simulation.selected_organism.connections.remove(conn)
                        # 更新源工具的连接列表
                        for tool in list(simulation.selected_organism.sensors.values()) + list(simulation.selected_organism.actuators.values()):
                            tool.connections = [conn for conn in tool.connections if conn not in connections_to_remove]
                        simulation.selected_objects = []
                        print("已删除选中工具")
        
        # 更新模拟（根据模拟速度调整更新次数）
        if simulation_speed >= 1:
            for _ in range(int(simulation_speed)):
                simulation.update()
        else:
            # 慢速模式，随机更新
            if random.random() < simulation_speed:
                simulation.update()
        
        # 绘制
        simulation.draw(screen)
        
        # 显示按键提示
        keys_text = font.render(f"按键: R-重置 F-加食物 N-新生物 +/--速度 {simulation_speed:.1f}x", True, (255, 255, 255))
        screen.blit(keys_text, (WIDTH // 2 - 200, HEIGHT - 30))
        
        # 显示性能信息
        if show_performance:
            frame_count += 1
            current_time = pygame.time.get_ticks()
            if current_time - last_time >= 1000:
                fps = frame_count
                frame_count = 0
                last_time = current_time
            
            performance_text = font.render(f"FPS: {fps} | 生物数: {len(simulation.organisms)} | 食物数: {len(simulation.environment.foods)}", True, (255, 255, 255))
            screen.blit(performance_text, (10, HEIGHT - 30))
        
        pygame.display.flip()
        clock.tick(target_fps)
    
    pygame.quit()


if __name__ == "__main__":
    main()
