"""资源管理器实现"""

from typing import Dict, List, Any, Tuple
import numpy as np

class ResourceManager:
    """资源管理器 - 负责管理环境中的资源
    
    资源管理器实现了环境中的资源管理，包括：
    1. 资源生成
    2. 资源分布
    3. 资源消耗
    4. 资源再生
    """
    
    def __init__(self, **kwargs: Any):
        """初始化资源管理器
        
        参数:
            kwargs: 其他参数
        """
        self.resource_spawn_rate = kwargs.get('resource_spawn_rate', 0.1)  # 资源生成率
        self.food_spawn_interval = kwargs.get('food_spawn_interval', 100)  # 食物生成间隔
        self.energy_spawn_interval = kwargs.get('energy_spawn_interval', 200)  # 能量生成间隔
        self.world_size = kwargs.get('world_size', (1200, 800))  # 世界大小
        
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
        """更新资源管理器状态"""
        # 生成新资源
        self.generate_resources()
        
        # 管理资源数量
        self.manage_resource_counts()
    
    def generate_resources(self):
        """生成新资源"""
        # 随机生成食物
        if len(self.resources['food']) < self.max_food and np.random.random() < self.resource_spawn_rate:
            self.create_resource('food')
        
        # 随机生成能量
        if len(self.resources['energy']) < self.max_energy and np.random.random() < self.resource_spawn_rate * 0.5:
            self.create_resource('energy')
    
    def create_resource(self, resource_type: str):
        """创建资源
        
        参数:
            resource_type: str - 资源类型 ('food', 'energy')
        """
        position = np.random.rand(2) * self.world_size
        
        if resource_type == 'food':
            resource: Dict[str, Any] = {
                'position': position,
                'amount': np.random.uniform(1, 5),
                'type': 'food',
                'id': f"food_{len(self.resources['food'])}"
            }
            self.resources['food'].append(resource)
        elif resource_type == 'energy':
            resource: Dict[str, Any] = {
                'position': position,
                'amount': np.random.uniform(1, 3),
                'type': 'energy',
                'id': f"energy_{len(self.resources['energy'])}"
            }
            self.resources['energy'].append(resource)
    
    def manage_resource_counts(self):
        """管理资源数量，确保不超过最大值"""
        # 限制食物数量
        if len(self.resources['food']) > self.max_food:
            # 随机移除多余的食物，直接使用列表处理
            import random
            self.resources['food'] = random.sample(self.resources['food'], self.max_food)
        
        # 限制能量数量
        if len(self.resources['energy']) > self.max_energy:
            # 随机移除多余的能量，直接使用列表处理
            import random
            self.resources['energy'] = random.sample(self.resources['energy'], self.max_energy)
    
    def get_nearby_resources(self, position: np.ndarray, radius: float, resource_type: str = 'all') -> List[Dict[str, Any]]:
        """获取附近资源
        
        参数:
            position: np.ndarray - 位置坐标
            radius: float - 搜索半径
            resource_type: str - 资源类型 ('all', 'food', 'energy')
        
        返回:
            List[Dict[str, Any]] - 附近资源列表
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
        """消耗资源
        
        参数:
            resource: Dict[str, Any] - 资源实例
        
        返回:
            bool - 消耗是否成功
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
        """获取资源数量
        
        参数:
            resource_type: str - 资源类型 ('all', 'food', 'energy')
        
        返回:
            int - 资源数量
        """
        if resource_type == 'all':
            return len(self.resources['food']) + len(self.resources['energy'])
        elif resource_type in self.resources:
            return len(self.resources[resource_type])
        return 0
    
    def get_resource_density(self, area: Tuple[float, float, float, float], resource_type: str = 'all') -> float:
        """获取资源密度
        
        参数:
            area: Tuple[float, float, float, float] - 区域 (x, y, width, height)
            resource_type: str - 资源类型 ('all', 'food', 'energy')
        
        返回:
            float - 资源密度
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
        """获取资源状态
        
        返回:
            Dict[str, Any] - 资源状态信息
        """
        return {
            'food_count': len(self.resources['food']),
            'energy_count': len(self.resources['energy']),
            'max_food': self.max_food,
            'max_energy': self.max_energy,
            'resource_spawn_rate': self.resource_spawn_rate
        }
