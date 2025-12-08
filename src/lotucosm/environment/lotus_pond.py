"""莲池环境实现"""

from typing import Dict, List, Any
import numpy as np
from vitalloom.components.components_base import ComponentBase
from vitalloom.organisms.organism import Organism

class LotusPond:
    """莲池环境 - 数字生命的演化环境
    
    莲池环境是数字生命的演化场所，负责管理：
    1. 生物体管理
    2. 组件管理（漂浮组件）
    3. 资源分布
    4. 物理规则
    5. 环境事件
    """
    
    def __init__(self, **kwargs: Any):
        """初始化莲池环境
        
        参数:
            kwargs: 其他参数
                - name: str - 莲池名称
                - size: tuple[float, float] - 莲池大小
                - initial_components: int - 初始漂浮组件数量
                - component_variety: str - 组件多样性类型
        """
        self.name: str = kwargs.get('name', '演化实验场')  # 莲池名称
        self.size: tuple[float, float] = kwargs.get('size', (1200, 800))  # 莲池大小
        self.time: int = 0  # 时间（迭代次数）
        
        # 生物体管理
        self.organisms: Dict[str, Organism] = {}  # 生物体字典，{生物体ID: 生物体实例}
        
        # 组件管理
        self.floating_components: List[ComponentBase] = []  # 漂浮组件列表
        self.initial_components: int = kwargs.get('initial_components', 50)  # 初始漂浮组件数量
        self.initial_organisms: int = kwargs.get('initial_organisms', 10)  # 初始生物体数量
        self.component_variety: str = kwargs.get('component_variety', 'all')  # 组件多样性类型
        
        # 资源管理
        self.resources: Dict[str, List[Dict[str, Any]]] = {
            'food': [],  # 食物粒子
            'energy': []  # 能量粒子
        }
        
        # 物理引擎
        self.physics_engine: Any = None  # 物理引擎实例
        
        # 漂浮系统
        self.floating_system: Any = None  # 漂浮系统实例
        
        # 自组装系统
        self.assembly_system: Any = None  # 自组装系统实例
        
        # 资源管理器
        self.resource_manager: Any = None  # 资源管理器实例
        
        # 序列化相关属性
        self.iteration: int = 0
        self.max_population: int = kwargs.get('max_population', 100)
        self.environmental_factors: Dict[str, Any] = kwargs.get('environmental_factors', {})
        self.statistics: Dict[str, Any] = kwargs.get('statistics', {})
        
        # 初始化莲池
        self.initialize_pond()
    
    def initialize_pond(self):
        """初始化莲池
        
        创建初始漂浮组件、资源和生物体
        """
        print(f"初始化莲池: {self.name}, 大小: {self.size}")
        
        # 创建初始漂浮组件
        self.create_initial_components()
        
        # 创建初始资源
        self.create_initial_resources()
        
        # 创建初始生物体
        self.create_initial_organisms()
        
    def create_initial_organisms(self):
        """创建初始生物体
        
        根据initial_organisms参数创建指定数量的初始生物体
        """
        from vitalloom.organisms.intelligent_organism import IntelligentOrganism
        
        for i in range(self.initial_organisms):
            # 随机位置
            position = np.random.rand(2) * self.size
            
            # 创建智能生物体
            organism_id = f"organism_{i + 1}"
            organism = IntelligentOrganism(
                organism_id = organism_id,
                position = tuple(position),
                name = f"初始生物体_{i + 1}"
            )
            
            # 添加到莲池
            self.add_organism(organism)
    
    def create_initial_components(self):
        """创建初始漂浮组件"""
        # 实际项目中需要从组件库创建组件
        # 这里简化处理，只创建空列表
        pass
    
    def create_initial_resources(self):
        """创建初始资源"""
        # 创建初始食物粒子
        for _ in range(200):
            food_position = np.random.rand(2) * self.size
            self.resources['food'].append({
                'position': food_position,
                'amount': np.random.uniform(1, 5),
                'type': 'food'
            })
        
        # 创建初始能量粒子
        for _ in range(100):
            energy_position = np.random.rand(2) * self.size
            self.resources['energy'].append({
                'position': energy_position,
                'amount': np.random.uniform(1, 3),
                'type': 'energy'
            })
    
    def update(self) -> None:
        """每帧更新莲池状态"""
        # 更新时间
        self.time += 1
        
        # 更新物理引擎
        if self.physics_engine:
            self.physics_engine.update()
        
        # 更新漂浮系统
        if self.floating_system:
            self.floating_system.update()
        
        # 更新自组装系统
        if self.assembly_system:
            self.assembly_system.update()
        
        # 更新资源管理器
        if self.resource_manager:
            self.resource_manager.update()
        
        # 更新所有生物体
        for organism in list(self.organisms.values()):
            organism.update(environment=self)
            
            # 检查生物体是否死亡
            if organism.dead:
                self.remove_organism(organism.id)
        
        # 更新所有漂浮组件
        for component in self.floating_components:
            component.update()
        
        # 生成新资源
        self.generate_resources()
    
    def add_organism(self, organism: Organism) -> bool:
        """添加生物体到莲池
        
        参数:
            organism: Organism - 生物体实例
        
        返回:
            bool - 添加是否成功
        """
        if organism.id in self.organisms:
            return False  # 生物体ID已存在
        
        self.organisms[organism.id] = organism
        print(f"添加生物体到莲池: {organism.id}")
        return True
    
    def remove_organism(self, organism_id: str) -> bool:
        """从莲池中移除生物体
        
        参数:
            organism_id: str - 生物体ID
        
        返回:
            bool - 移除是否成功
        """
        if organism_id in self.organisms:
            del self.organisms[organism_id]
            print(f"从莲池中移除生物体: {organism_id}")
            return True
        return False
    
    def get_nearby_components(self, position: np.ndarray, radius: float) -> List[ComponentBase]:
        """获取附近漂浮组件
        
        参数:
            position: np.ndarray - 位置坐标
            radius: float - 搜索半径
        
        返回:
            List[ComponentBase] - 附近漂浮组件列表
        """
        nearby: List[ComponentBase] = []
        for component in self.floating_components:
            distance = np.linalg.norm(component.position - position)
            if distance <= radius:
                nearby.append(component)
        
        return nearby
    
    def add_floating_component(self, component: ComponentBase):
        """添加漂浮组件到莲池
        
        参数:
            component: ComponentBase - 组件实例
        """
        self.floating_components.append(component)
    
    def remove_floating_component(self, component: ComponentBase):
        """从莲池中移除漂浮组件
        
        参数:
            component: ComponentBase - 组件实例
        """
        if component in self.floating_components:
            self.floating_components.remove(component)
    
    def generate_resources(self):
        """生成新资源"""
        # 每100次迭代生成新资源
        if self.time % 100 == 0:
            # 生成食物粒子
            food_position = np.random.rand(2) * self.size
            self.resources['food'].append({
                'position': food_position,
                'amount': np.random.uniform(1, 5),
                'type': 'food'
            })
            
            # 生成能量粒子
            energy_position = np.random.rand(2) * self.size
            self.resources['energy'].append({
                'position': energy_position,
                'amount': np.random.uniform(1, 3),
                'type': 'energy'
            })
    
    def get_nearby_resources(self, position: np.ndarray, radius: float, resource_type: str = 'all') -> List[Dict[str, Any]]:
        """获取附近资源
        
        参数:
            position: np.ndarray - 位置坐标
            radius: float - 搜索半径
            resource_type: str - 资源类型 ('all', 'food', 'energy')
        
        返回:
            List[Dict[str, Any]] - 附近资源列表
        """
        nearby_resources: List[Dict[str, Any]] = []
        
        if resource_type in ['all', 'food']:
            for food in self.resources['food']:
                distance = np.linalg.norm(food['position'] - position)
                if distance <= radius:
                    nearby_resources.append(food)
        
        if resource_type in ['all', 'energy']:
            for energy in self.resources['energy']:
                distance = np.linalg.norm(energy['position'] - position)
                if distance <= radius:
                    nearby_resources.append(energy)
        
        return nearby_resources
    
    def check_contact(self, position: np.ndarray, radius: float) -> Dict[str, Any]:
        """检查接触
        
        参数:
            position: np.ndarray - 位置坐标
            radius: float - 检查半径
        
        返回:
            Dict[str, Any] - 接触信息
        """
        contact_info: Dict[str, Any] = {
            'contact': False,
            'pressure': 0.0,
            'objects': []
        }
        
        # 检查与其他生物体的接触
        for organism in self.organisms.values():
            if organism.id != getattr(self, 'current_organism_id', ''):
                distance = np.linalg.norm(organism.position - position)
                if distance < radius + getattr(organism.membrane, 'radius', 30):
                    contact_info['contact'] = True
                    contact_info['pressure'] += 0.5
                    contact_info['objects'].append({'type': 'organism', 'id': organism.id})
        
        # 检查与资源的接触
        for resource in self.resources['food'] + self.resources['energy']:
            distance = np.linalg.norm(resource['position'] - position)
            if distance < radius + 5:  # 资源半径简化处理
                contact_info['contact'] = True
                contact_info['pressure'] += 0.2
                contact_info['objects'].append({'type': resource['type']})
        
        return contact_info
    
    def get_light_intensity(self, position: np.ndarray) -> float:
        """获取光照强度
        
        参数:
            position: np.ndarray - 位置坐标
        
        返回:
            float - 光照强度 (0-1)
        """
        # 简单的光照模型，实际项目中可能需要更复杂的光照系统
        return 0.8  # 默认光照强度
    
    def get_temperature(self, position: np.ndarray) -> float:
        """获取温度
        
        参数:
            position: np.ndarray - 位置坐标
        
        返回:
            float - 温度
        """
        # 简单的温度模型
        return 25.0  # 默认温度
    
    def get_pond_status(self) -> Dict[str, Any]:
        """获取莲池状态
        
        返回:
            Dict[str, Any] - 莲池状态信息
        """
        return {
            'name': self.name,
            'size': self.size,
            'time': self.time,
            'organism_count': len(self.organisms),
            'floating_component_count': len(self.floating_components),
            'food_count': len(self.resources['food']),
            'energy_count': len(self.resources['energy'])
        }
    
    def save_pond(self, save_path: str) -> str:
        """保存莲池
        
        参数:
            save_path: str - 保存路径
        
        返回:
            str - 保存的莲池ID
        """
        # 实际项目中需要实现莲池序列化
        print(f"保存莲池到: {save_path}")
        return f"pond_{self.time}"
    
    def load_pond(self, load_path: str) -> bool:
        """加载莲池
        
        参数:
            load_path: str - 加载路径
        
        返回:
            bool - 加载是否成功
        """
        # 实际项目中需要实现莲池反序列化
        print(f"从: {load_path} 加载莲池")
        return True
