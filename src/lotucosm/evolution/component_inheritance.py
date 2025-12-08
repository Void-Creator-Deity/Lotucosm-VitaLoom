"""组件遗传系统实现"""

from typing import Dict, List
import random
from vitalloom.components.components_base import ComponentBase
from vitalloom.organisms.organism import Organism
from lotucosm.environment.environment import Environment


class ComponentInheritance:
    """组件遗传系统 - 管理组件的遗传规则
    
    实现了组件的遗传机制：
    1. 先天组件：100%遗传给子代
    2. 后天组件：根据变异率概率遗传
    3. 组件位置：遗传时保持相同位置属性
    4. 组件状态：遗传时重置为初始状态
    5. 记忆关联：组件相关的记忆有更高遗传概率
    """
    
    def __init__(self):
        """初始化组件遗传系统"""
        self.congenital_inheritance_rate = 1.0  # 先天组件遗传率（100%）
        self.acquired_inheritance_rate = 0.3  # 后天获得组件遗传率（30%）
    
    def inherit_components(self, parent_components: Dict[str, ComponentBase], mutation_rate: float = 0.1) -> List[ComponentBase]:
        """继承组件
        
        参数:
            parent_components: Dict[str, ComponentBase] - 父代组件字典
            mutation_rate: float - 变异率
        
        返回:
            List[ComponentBase] - 子代组件列表
        """
        inherited_components: List[ComponentBase] = []
        
        for component in parent_components.values():
            if self._should_inherit_component(component):
                # 克隆组件
                inherited_component = component.clone()
                
                # 应用变异
                if random.random() < mutation_rate:
                    inherited_component.mutate()
                
                # 重置组件状态
                inherited_component.reset_state()
                
                inherited_components.append(inherited_component)
        
        return inherited_components
    
    def _should_inherit_component(self, component: ComponentBase) -> bool:
        """判断组件是否应该被继承
        
        参数:
            component: ComponentBase - 要判断的组件
        
        返回:
            bool - 是否应该继承
        """
        if component.congenital:
            # 先天组件100%遗传
            return random.random() < self.congenital_inheritance_rate
        else:
            # 后天获得的组件按概率遗传
            return random.random() < self.acquired_inheritance_rate
    
    def get_inheritance_probability(self, component: ComponentBase) -> float:
        """获取组件的遗传概率
        
        参数:
            component: ComponentBase - 组件
        
        返回:
            float - 遗传概率
        """
        if component.congenital:
            return self.congenital_inheritance_rate
        else:
            return self.acquired_inheritance_rate
    
    def set_congenital_inheritance_rate(self, rate: float) -> None:
        """设置先天组件遗传率
        
        参数:
            rate: float - 遗传率（0-1之间）
        """
        self.congenital_inheritance_rate = max(0.0, min(1.0, rate))
    
    def set_acquired_inheritance_rate(self, rate: float) -> None:
        """设置后天获得组件遗传率
        
        参数:
            rate: float - 遗传率（0-1之间）
        """
        self.acquired_inheritance_rate = max(0.0, min(1.0, rate))
    
    def calculate_component_fitness(self, component: ComponentBase, organism: Organism, environment: Environment) -> float:
        """计算组件的适应度
        
        参数:
            component: ComponentBase - 组件
            organism: Organism - 生物体实例
            environment: Environment - 环境实例
        
        返回:
            float - 组件适应度（0-1之间）
        """
        fitness = 0.0
        
        # 1. 组件类型适应度
        # 传感器、执行器、复合器各有不同的适应度权重
        if hasattr(component, 'is_sensor') and component.is_sensor:
            fitness += 0.3
        if hasattr(component, 'is_actuator') and component.is_actuator:
            fitness += 0.3
        if hasattr(component, 'is_hybrid') and component.is_hybrid:
            fitness += 0.4  # 复合器适应度更高
        
        # 2. 组件位置适应度
        # 不同位置的组件适应度不同
        if component.location == 'internal':
            fitness += 0.3
        elif component.location == 'external':
            fitness += 0.3
        elif component.location == 'both':
            fitness += 0.4  # 通用组件适应度更高
        
        # 3. 组件使用频率适应度
        # 基于组件的使用次数
        if hasattr(component, 'usage_count'):
            usage_fitness = min(component.usage_count / 100.0, 1.0)
            fitness += usage_fitness * 0.4
        
        return min(fitness, 1.0)
    
    def select_components_for_inheritance(self, components: Dict[str, ComponentBase], organism: Organism, environment: Environment, max_components: int = 20) -> List[ComponentBase]:
        """选择要继承的组件（基于适应度）
        
        参数:
            components: Dict[str, ComponentBase] - 父代组件字典
            organism: Organism - 生物体实例
            environment: Environment - 环境实例
            max_components: int - 最大继承组件数量
        
        返回:
            List[ComponentBase] - 选中的组件列表
        """
        # 计算每个组件的适应度
        component_fitness: List[tuple[ComponentBase, float]] = []
        for component in components.values():
            fitness = self.calculate_component_fitness(component, organism, environment)
            component_fitness.append((component, fitness))
        
        # 按适应度排序
        component_fitness.sort(key=lambda x: x[1], reverse=True)
        
        # 选择适应度最高的组件
        selected_components: List[ComponentBase] = [component for component, _ in component_fitness[:max_components]]
        
        return selected_components
    
    def create_component_combinations(self, components: List[ComponentBase]) -> List[List[ComponentBase]]:
        """创建组件组合（用于繁殖时的组件重组）
        
        参数:
            components: List[ComponentBase] - 组件列表
        
        返回:
            List[List[ComponentBase]] - 组件组合列表
        """
        # 简单的组件重组：随机选择不同类型的组件组合
        combinations: List[List[ComponentBase]] = []
        
        # 按组件类型分组
        sensor_components = [c for c in components if hasattr(c, 'is_sensor') and c.is_sensor]
        actuator_components = [c for c in components if hasattr(c, 'is_actuator') and c.is_actuator]
        hybrid_components = [c for c in components if hasattr(c, 'is_hybrid') and c.is_hybrid]
        
        # 创建不同类型的组合
        # 1. 传感器 + 执行器组合
        if sensor_components and actuator_components:
            for sensor in sensor_components:
                for actuator in actuator_components:
                    combinations.append([sensor, actuator])
        
        # 2. 复合器 + 传感器组合
        if hybrid_components and sensor_components:
            for hybrid in hybrid_components:
                for sensor in sensor_components:
                    combinations.append([hybrid, sensor])
        
        # 3. 复合器 + 执行器组合
        if hybrid_components and actuator_components:
            for hybrid in hybrid_components:
                for actuator in actuator_components:
                    combinations.append([hybrid, actuator])
        
        # 4. 纯复合器组合
        if len(hybrid_components) > 1:
            for i in range(len(hybrid_components)):
                for j in range(i+1, len(hybrid_components)):
                    combinations.append([hybrid_components[i], hybrid_components[j]])
        
        return combinations