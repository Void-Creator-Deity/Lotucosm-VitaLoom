"""Tool继承算法模拟器入口"""

import pygame
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
                    import random
                    x = random.randint(50, WIDTH - 50)
                    y = random.randint(50, HEIGHT - 50)
                    simulation.environment.add_food((x, y))
                elif event.key == pygame.K_n:  # 按N创建新生物
                    import random
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
