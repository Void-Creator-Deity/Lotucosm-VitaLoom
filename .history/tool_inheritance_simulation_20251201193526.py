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
    
    print("Tool继承算法模拟器启动!")
    print("功能说明:")
    print("- 绿色圆圈: 触觉传感器")
    print("- 黄色太阳: 光感传感器") 
    print("- 红色条状: 肌肉效应器")
    print("- 青色波浪: 纤毛效应器")
    print("- 蓝色线条: Tool连接")
    print("- 点击生物查看详细信息")
    print("- 点击空地添加食物")
    
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
        
        # 更新模拟
        simulation.update()
        
        # 绘制
        simulation.draw(screen)
        
        # 显示按键提示
        keys_text = font.render("按键: R-重置 F-加食物 N-新生物", True, (255, 255, 255))
        screen.blit(keys_text, (WIDTH // 2 - 150, HEIGHT - 30))
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()


if __name__ == "__main__":
    main()
