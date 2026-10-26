"""PS 莲池资源分区管理：按类型存储可采集资源条目。

排错: 见 `builtin/README.md`。
"""

from typing import Dict, List, Any, Tuple
import numpy as np
from core.Lotucosm.randomness import random_sample

class ResourceManager:
    """资源管理器 - 负责管理环境中的资源
    
    资源管理器实现了环境中的资源管理，包括：
    1. 资源生成
    2. 资源分布
    3. 资源消耗
    4. 资源再生
    """
    
    def __init__(self, **kwargs: Any):
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
        self.resource_spawn_rate = kwargs.get('resource_spawn_rate', 0.1)  # 资源生成率
        self.food_spawn_interval = kwargs.get('food_spawn_interval', 100)  # 食物生成间隔
        self.energy_spawn_interval = kwargs.get('energy_spawn_interval', 200)  # 能量生成间隔
        self.world_size = kwargs.get('world_size', (1200, 800))  # 世界大小
        supplied_rng = kwargs.get("randomness_rng")
        self.randomness_owner_mode = "runtime" if supplied_rng is not None else "detached"
        self.randomness_rng = supplied_rng if supplied_rng is not None else np.random.default_rng(12345)
        if self.randomness_rng is None:
            self.randomness_rng = np.random.default_rng(12345)
        if not hasattr(self.randomness_rng, "random"):
            raise TypeError("randomness_rng must expose random()")
        
        # 资源限制
        self.max_food = kwargs.get('max_food', 300)  # 最大食物数量
        self.max_energy = kwargs.get('max_energy', 150)  # 最大能量数量
        
        # 资源消耗率
        self.food_consumption_rate = kwargs.get('food_consumption_rate', 0.5)  # 食物消耗率
        self.energy_consumption_rate = kwargs.get('energy_consumption_rate', 0.3)  # 能量消耗率
        
        # 资源列表
        self.resources: Dict[str, List[Dict[str, Any]]] = {
            'food': [],
            'energy': []
        }
    
    def update(self):
        """更新资源管理器状态。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 生成新资源
        self.generate_resources()
        
        # 管理资源数量
        self.manage_resource_counts()
    
    def generate_resources(self):
        """生成新资源。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 随机生成食物
        if len(self.resources['food']) < self.max_food and self._random() < self.resource_spawn_rate:
            self.create_resource('food')
        
        # 随机生成能量
        if len(self.resources['energy']) < self.max_energy and self._random() < self.resource_spawn_rate * 0.5:
            self.create_resource('energy')
    
    def create_resource(self, resource_type: str):
        """创建资源。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        position = self._random_array(2) * self.world_size
        
        if resource_type == 'food':
            resource: Dict[str, Any] = {
                'position': position,
                'amount': self._uniform(1, 5),
                'type': 'food',
                'id': f"food_{len(self.resources['food'])}"
            }
            self.resources['food'].append(resource)
        elif resource_type == 'energy':
            resource: Dict[str, Any] = {
                'position': position,
                'amount': self._uniform(1, 3),
                'type': 'energy',
                'id': f"energy_{len(self.resources['energy'])}"
            }
            self.resources['energy'].append(resource)
    
    def _random(self) -> float:
        if self.randomness_rng is None:
            raise RuntimeError("ResourceManager randomness owner is unavailable")
        return float(self.randomness_rng.random())

    def _random_array(self, size: int) -> np.ndarray:
        if self.randomness_rng is None:
            raise RuntimeError("ResourceManager randomness owner is unavailable")
        return np.asarray(self.randomness_rng.random(size), dtype=float)

    def _uniform(self, low: float, high: float) -> float:
        if self.randomness_rng is None:
            raise RuntimeError("ResourceManager randomness owner is unavailable")
        return float(self.randomness_rng.uniform(low, high))

    def manage_resource_counts(self):
        """管理资源数量，确保不超过最大值。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 限制食物数量
        if len(self.resources['food']) > self.max_food:
            # 随机移除多余的食物，直接使用列表处理
            self.resources['food'] = random_sample(
                self.randomness_rng,
                self.resources['food'],
                self.max_food,
            )
        
        # 限制能量数量
        if len(self.resources['energy']) > self.max_energy:
            # 随机移除多余的能量，直接使用列表处理
            self.resources['energy'] = random_sample(
                self.randomness_rng,
                self.resources['energy'],
                self.max_energy,
            )
    
    def get_nearby_resources(self, position: np.ndarray, radius: float, resource_type: str = 'all') -> List[Dict[str, Any]]:
        """获取附近资源。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        nearby: List[Dict[str, Any]] = []
        
        if resource_type in ['all', 'food']:
            for resource in self.resources['food']:
                distance = np.linalg.norm(resource['position'] - position)
                if distance <= radius:
                    nearby.append(resource)
        
        if resource_type in ['all', 'energy']:
            for resource in self.resources['energy']:
                distance = np.linalg.norm(resource['position'] - position)
                if distance <= radius:
                    nearby.append(resource)
        
        return nearby
    
    def consume_resource(self, resource: Dict[str, Any]) -> bool:
        """消耗资源。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        resource_type = resource['type']
        resource_id = resource['id']
        
        # 查找并移除资源
        if resource_type in self.resources:
            for i, res in enumerate(self.resources[resource_type]):
                if res['id'] == resource_id:
                    del self.resources[resource_type][i]
                    return True
        
        return False
    
    def get_resource_count(self, resource_type: str = 'all') -> int:
        """获取资源数量。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if resource_type == 'all':
            return len(self.resources['food']) + len(self.resources['energy'])
        elif resource_type in self.resources:
            return len(self.resources[resource_type])
        return 0
    
    def get_resource_density(self, area: Tuple[float, float, float, float], resource_type: str = 'all') -> float:
        """获取资源密度。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        x, y, width, height = area
        count = 0
        
        # 计算区域内资源数量
        if resource_type in ['all', 'food']:
            for resource in self.resources['food']:
                if x <= resource['position'][0] <= x + width and y <= resource['position'][1] <= y + height:
                    count += 1
        
        if resource_type in ['all', 'energy']:
            for resource in self.resources['energy']:
                if x <= resource['position'][0] <= x + width and y <= resource['position'][1] <= y + height:
                    count += 1
        
        # 计算密度
        area_size = width * height
        if area_size > 0:
            return count / area_size
        return 0
    
    def get_resource_status(self) -> Dict[str, Any]:
        """获取资源状态。

        
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
            'food_count': len(self.resources['food']),
            'energy_count': len(self.resources['energy']),
            'max_food': self.max_food,
            'max_energy': self.max_energy,
            'resource_spawn_rate': self.resource_spawn_rate
        }
