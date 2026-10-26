"""PS 演示环境：食物、光照、障碍物与邻近查询（供 Simulation / Organism.sense）。

排错: 见 `builtin/README.md`；SR 场域见 `scene_runtime_ambient`。
"""

from typing import List, Dict, Any, Tuple
import numpy as np
from core.Lotucosm.entity import EntityBase
from .food import Food
from .obstacle import Obstacle


class Environment:
    """PS 环境容器：食物/光/障碍列表及 get_nearby_* 查询接口。

    属性:
        foods: List[Food] - 食物列表
        light_sources: List[Dict] - 光源列表，每个光源包含位置和强度信息
        obstacles: List[Obstacle] - 障碍物列表
    """

    def __init__(self):
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
        self.foods: List[Food] = []  # 食物列表，存储环境中的食物
        self.light_sources: List[Dict[str, Any]] = []  # 光源列表，存储环境中的光源
        self.obstacles: List[Obstacle] = []  # 障碍物列表，存储环境中的障碍物

    def add_food(self, position: Tuple[float, float], energy: float = 20.0):
        """添加食物到环境中。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        food = Food(position=position, energy=energy)
        self.foods.append(food)

    def add_light_source(self, position: Tuple[float, float], intensity: float = 1.0):
        """添加光源到环境中。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self.light_sources.append({"position": np.array(position), "intensity": intensity})

    def add_obstacle(self, position: Tuple[float, float], radius: float = 20.0, **kwargs: Any):
        """添加障碍物到环境中。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        obstacle = Obstacle(position=position, size=radius, **kwargs)
        self.obstacles.append(obstacle)

    def check_contact(self, position: np.ndarray, radius: float) -> Dict[str, Any]:
        """检查指定位置是否与障碍物接触。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        for obstacle in self.obstacles:
            # 使用Obstacle类的碰撞检测方法
            collision_info = obstacle.get_collision_info(position, radius)
            if collision_info['colliding']:
                return {
                    "contacting": True,
                    "pressure": collision_info['pressure'],
                    "direction": collision_info['direction'],
                    "damage": collision_info['damage']
                }

        # 没有发生碰撞
        return {
            "contacting": False,
            "pressure": 0.0,
            "direction": np.array([0.0, 0.0]),
            "damage": 0.0
        }

    def get_light_intensity(self, position: np.ndarray) -> float:
        """获取指定位置的光线强度。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
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
        """消耗指定位置附近的食物。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        for i, food in enumerate(self.foods):
            # 使用EntityBase的碰撞检测方法
            if food.check_collision_with_point(tuple(position)):
                # 消耗食物
                energy = food.consume()
                self.foods.pop(i)  # 从列表中移除
                return True
        return False

    def get_nearby_food(self, position: np.ndarray, radius: float) -> List[Food]:
        """获取指定位置附近的食物。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        nearby: List[Food] = []  # 附近食物列表

        for food in self.foods:
            # 使用EntityBase的距离计算方法
            dist = food.get_distance_to_point(tuple(position))
            if dist < radius:
                nearby.append(food)
        
        return nearby


    def get_nearby_entities(self, position: np.ndarray, radius: float) -> List[EntityBase]:
        """获取指定位置附近的所有实体（障碍物和食物）。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        nearby: List[EntityBase] = []
        
        # 检查障碍物
        for obs in self.obstacles:
            if obs.get_distance_to_point(tuple(position)) < radius + obs.radius:
                nearby.append(obs)
                
        # 检查食物
        for food in self.foods:
            if food.get_distance_to_point(tuple(position)) < radius:
                nearby.append(food)
                
        return nearby

    def update(self, delta_time: float = 1.0):
        """更新环境状态。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 更新所有食物
        for food in self.foods:
            food.update(delta_time)

        # 更新所有障碍物
        for obstacle in self.obstacles:
            obstacle.update(delta_time)

        # 移除不活跃的实体
        self.foods = [food for food in self.foods if food.active]
        self.obstacles = [obstacle for obstacle in self.obstacles if obstacle.active]

    def draw(self, surface: Any):
        """在指定表面上绘制环境。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 绘制食物
        for food in self.foods:
            food.draw(surface)

        # 绘制光源
        self._draw_light_sources(surface)

        # 绘制障碍物
        for obstacle in self.obstacles:
            obstacle.draw(surface)

    def _draw_light_sources(self, surface: Any):
        """绘制光源

        在指定的表面上绘制所有光源。

        参数:
            surface - 绘制表面
        """
        import pygame  # 延迟导入Pygame，避免不必要的依赖

        for light in self.light_sources:
            pos = light["position"].astype(int)  # 转换为整数坐标
            # 绘制光晕效果，使用多层半透明圆圈
            for radius in range(20, 5, -5):
                alpha = int(100 * (1 - radius / 20))  # 透明度随半径增大而减小
                s = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)  # 创建半透明表面
                pygame.draw.circle(s, (255,255,200, alpha), (radius, radius), radius)  # 绘制光晕
                surface.blit(s, (pos[0]-radius, pos[1]-radius))  # 绘制到主表面
            pygame.draw.circle(surface, (255,255,100), pos, 5)  # 绘制光源中心

    def get_environment_status(self) -> Dict[str, Any]:
        """获取环境状态信息。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        return {
            'food_count': len(self.foods),
            'light_source_count': len(self.light_sources),
            'obstacle_count': len(self.obstacles),
            'total_food_energy': sum(food.energy for food in self.foods)
        }
