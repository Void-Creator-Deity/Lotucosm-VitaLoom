"""环境实现"""

from typing import Dict, List, Tuple
import numpy as np


class Environment:
    """简化环境"""
    def __init__(self):
        self.foods = []
        self.light_sources = []
        self.obstacles = []
        
    def add_food(self, position: Tuple[float, float]):
        """添加食物"""
        self.foods.append({"position": np.array(position), "energy": 20})
        
    def add_light_source(self, position: Tuple[float, float], intensity: float = 1.0):
        """添加光源"""
        self.light_sources.append({"position": np.array(position), "intensity": intensity})
        
    def add_obstacle(self, position: Tuple[float, float], radius: float):
        """添加障碍物"""
        self.obstacles.append({"position": np.array(position), "radius": radius})
        
    def check_contact(self, position: np.ndarray, radius: float) -> Dict[str, any]:
        """检查接触"""
        for obstacle in self.obstacles:
            distance = np.linalg.norm(position - obstacle["position"])
            if distance < obstacle["radius"] + radius:
                direction = position - obstacle["position"]
                if np.linalg.norm(direction) > 0:
                    direction = direction / np.linalg.norm(direction)
                return {
                    "contacting": True,
                    "pressure": 1.0 - (distance / (obstacle["radius"] + radius)),
                    "direction": direction
                }
        return {"contacting": False, "pressure": 0.0, "direction": np.array([0.0, 0.0])}
    
    def get_light_intensity(self, position: np.ndarray) -> float:
        """获取光线强度"""
        if not self.light_sources:
            return 0.0
            
        total_intensity = 0.0
        for light in self.light_sources:
            distance = np.linalg.norm(position - light["position"])
            intensity = light["intensity"] / (1 + distance * 0.1)  # 距离衰减
            total_intensity += intensity
            
        return min(1.0, total_intensity)
    
    def consume_food(self, position: np.ndarray, radius: float) -> bool:
        """消耗食物"""
        for i, food in enumerate(self.foods):
            distance = np.linalg.norm(position - food["position"])
            if distance < radius:
                self.foods.pop(i)
                return True
        return False
    
    def get_nearby_food(self, position: np.ndarray, radius: float) -> List:
        """获取附近食物"""
        nearby = []
        for food in self.foods:
            distance = np.linalg.norm(position - food["position"])
            if distance < radius:
                nearby.append(food)
        return nearby
    
    def draw(self, surface):
        """绘制环境"""
        import pygame
        # 绘制食物
        for food in self.foods:
            pos = food["position"].astype(int)
            pygame.draw.circle(surface, (100, 200, 100), pos, 8)
            pygame.draw.circle(surface, (50, 150, 50), pos, 8, 2)
            
        # 绘制光源
        for light in self.light_sources:
            pos = light["position"].astype(int)
            # 光晕效果
            for radius in range(20, 5, -5):
                alpha = int(100 * (1 - radius / 20))
                s = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
                pygame.draw.circle(s, (255, 255, 200, alpha), (radius, radius), radius)
                surface.blit(s, (pos[0]-radius, pos[1]-radius))
            pygame.draw.circle(surface, (255, 255, 100), pos, 5)
            
        # 绘制障碍物
        for obstacle in self.obstacles:
            pos = obstacle["position"].astype(int)
            pygame.draw.circle(surface, (100, 100, 100), pos, int(obstacle["radius"]))
            pygame.draw.circle(surface, (50, 50, 50), pos, int(obstacle["radius"]), 2)
