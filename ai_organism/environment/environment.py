"""环境实现 - AI生命体的生存环境系统"""

from typing import Dict, List, Tuple
import numpy as np


class Environment:
    """环境类 - 管理AI生命体的生存环境
    
    负责管理环境中的食物、光源和障碍物，提供环境信息查询接口，
    支持AI生命体与环境的交互。
    
    属性:
        foods: List[Dict] - 食物列表，每个食物包含位置和能量信息
        light_sources: List[Dict] - 光源列表，每个光源包含位置和强度信息
        obstacles: List[Dict] - 障碍物列表，每个障碍物包含位置和半径信息
    """
    
    def __init__(self):
        """初始化环境"""
        self.foods = []  # 食物列表，存储环境中的食物
        self.light_sources = []  # 光源列表，存储环境中的光源
        self.obstacles = []  # 障碍物列表，存储环境中的障碍物
        
    def add_food(self, position: Tuple[float, float]):
        """添加食物到环境中
        
        在指定位置添加一个食物，食物具有固定能量值20。
        
        参数:
            position: Tuple[float, float] - 食物的位置坐标
        """
        self.foods.append({"position": np.array(position), "energy": 20})
        
    def add_light_source(self, position: Tuple[float, float], intensity: float = 1.0):
        """添加光源到环境中
        
        在指定位置添加一个光源，光源具有指定的强度。
        
        参数:
            position: Tuple[float, float] - 光源的位置坐标
            intensity: float - 光源的强度，默认为1.0
        """
        self.light_sources.append({"position": np.array(position), "intensity": intensity})
        
    def add_obstacle(self, position: Tuple[float, float], radius: float):
        """添加障碍物到环境中
        
        在指定位置添加一个具有指定半径的障碍物。
        
        参数:
            position: Tuple[float, float] - 障碍物的位置坐标
            radius: float - 障碍物的半径
        """
        self.obstacles.append({"position": np.array(position), "radius": radius})
        
    def check_contact(self, position: np.ndarray, radius: float) -> Dict[str, any]:
        """检查指定位置是否与障碍物接触
        
        计算指定位置和半径的物体是否与环境中的障碍物发生碰撞，
        返回碰撞信息，包括是否碰撞、碰撞压力和碰撞方向。
        
        参数:
            position: np.ndarray - 物体的位置坐标
            radius: float - 物体的半径
        
        返回:
            Dict[str, any] - 碰撞信息字典，包含以下键:
                - contacting: bool - 是否发生碰撞
                - pressure: float - 碰撞压力，范围0-1
                - direction: np.ndarray - 碰撞方向向量
        """
        for obstacle in self.obstacles:
            # 计算物体与障碍物之间的距离
            distance = np.linalg.norm(position - obstacle["position"])
            
            # 检查是否发生碰撞
            if distance < obstacle["radius"] + radius:
                # 计算碰撞方向
                direction = position - obstacle["position"]
                if np.linalg.norm(direction) > 0:
                    direction = direction / np.linalg.norm(direction)  # 归一化方向向量
                
                # 计算碰撞压力，距离越小压力越大
                pressure = 1.0 - (distance / (obstacle["radius"] + radius))
                
                return {
                    "contacting": True,
                    "pressure": pressure,
                    "direction": direction
                }
        
        # 没有发生碰撞
        return {
            "contacting": False,
            "pressure": 0.0,
            "direction": np.array([0.0, 0.0])
        }
    
    def get_light_intensity(self, position: np.ndarray) -> float:
        """获取指定位置的光线强度
        
        计算环境中所有光源在指定位置产生的总光线强度，
        光线强度随距离衰减，总强度限制在0-1之间。
        
        参数:
            position: np.ndarray - 要查询的位置坐标
        
        返回:
            float - 光线强度，范围0-1
        """
        if not self.light_sources:
            return 0.0  # 没有光源时返回0.0
            
        total_intensity = 0.0  # 总光线强度
        
        for light in self.light_sources:
            # 计算光源到指定位置的距离
            distance = np.linalg.norm(position - light["position"])
            # 光线强度随距离衰减，使用1/(1 + 0.1*distance)作为衰减函数
            intensity = light["intensity"] / (1 + distance * 0.1)
            total_intensity += intensity
            
        return min(1.0, total_intensity)  # 限制总强度在0-1之间
    
    def consume_food(self, position: np.ndarray, radius: float) -> bool:
        """消耗指定位置附近的食物
        
        检查指定位置和半径的物体是否与食物接触，
        如果接触则消耗该食物并返回True，否则返回False。
        
        参数:
            position: np.ndarray - 物体的位置坐标
            radius: float - 物体的半径
        
        返回:
            bool - 是否成功消耗食物
        """
        for i, food in enumerate(self.foods):
            # 计算物体与食物之间的距离
            distance = np.linalg.norm(position - food["position"])
            
            # 检查是否接触食物
            if distance < radius:
                self.foods.pop(i)  # 消耗食物，从列表中移除
                return True
        return False
    
    def get_nearby_food(self, position: np.ndarray, radius: float) -> List:
        """获取指定位置附近的食物
        
        查找并返回指定位置和半径范围内的所有食物。
        
        参数:
            position: np.ndarray - 中心位置坐标
            radius: float - 搜索半径
        
        返回:
            List - 附近食物的列表
        """
        nearby = []  # 附近食物列表
        
        for food in self.foods:
            # 计算食物与指定位置的距离
            distance = np.linalg.norm(position - food["position"])
            
            # 检查食物是否在搜索范围内
            if distance < radius:
                nearby.append(food)
        
        return nearby
    
    def draw(self, surface):
        """在指定表面上绘制环境
        
        绘制环境中的食物、光源和障碍物。
        
        参数:
            surface - 绘制表面，通常是Pygame的Surface对象
        """
        import pygame  # 延迟导入Pygame，避免不必要的依赖
        
        # 绘制食物
        for food in self.foods:
            pos = food["position"].astype(int)  # 转换为整数坐标
            pygame.draw.circle(surface, (100, 200, 100), pos, 8)  # 绘制食物主体
            pygame.draw.circle(surface, (50, 150, 50), pos, 8, 2)  # 绘制食物边框
            
        # 绘制光源
        for light in self.light_sources:
            pos = light["position"].astype(int)  # 转换为整数坐标
            # 绘制光晕效果，使用多层半透明圆圈
            for radius in range(20, 5, -5):
                alpha = int(100 * (1 - radius / 20))  # 透明度随半径增大而减小
                s = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)  # 创建半透明表面
                pygame.draw.circle(s, (255, 255, 200, alpha), (radius, radius), radius)  # 绘制光晕
                surface.blit(s, (pos[0]-radius, pos[1]-radius))  # 绘制到主表面
            pygame.draw.circle(surface, (255, 255, 100), pos, 5)  # 绘制光源中心
            
        # 绘制障碍物
        for obstacle in self.obstacles:
            pos = obstacle["position"].astype(int)  # 转换为整数坐标
            pygame.draw.circle(surface, (100, 100, 100), pos, int(obstacle["radius"]))  # 绘制障碍物主体
            pygame.draw.circle(surface, (50, 50, 50), pos, int(obstacle["radius"]), 2)  # 绘制障碍物边框
