"""组件获取系统实现"""

from typing import Dict, List, Any, Optional
import numpy as np
from .organism import Organism
from vitalloom.components.components_base import ComponentBase
from vitalloom.components.PVAECEngine import PVAECEngine

class ComponentAcquisitionSystem:
    """组件获取系统 - 负责生物体捕获和整合外部组件

    组件获取系统实现了生物体捕获和整合外部组件的逻辑，包括：
    1. 扫描周围漂浮组件
    2. 评估组件价值
    3. 捕获组件
    4. 整合组件到生物体
    5. 组件位置管理
    """

    def __init__(self, **kwargs: Any):
        """初始化组件获取系统

        参数:
            kwargs: 其他参数
        """
        self.scan_radius = float(kwargs.get('scan_radius', 50.0))  # 扫描半径
        self.capture_cost = float(kwargs.get('capture_cost', 5.0))  # 捕获组件的能量消耗
        self.integration_efficiency = float(kwargs.get('integration_efficiency', 0.8))  # 组件整合效率

    def scan_nearby_components(self, organism: Organism, environment: Any) -> List[ComponentBase]:
        """扫描周围漂浮组件

        参数:
            organism: Organism - 生物体实例
            environment: Any - 环境实例

        返回:
            List[ComponentBase] - 附近漂浮组件列表
        """
        # 从环境中获取附近组件
        return environment.get_nearby_components(organism.position, self.scan_radius)

    def evaluate_component(self, organism: Organism, component: ComponentBase) -> float:
        """评估组件价值

        参数:
            organism: Organism - 生物体实例
            component: ComponentBase - 组件实例

        返回:
            float - 组件价值评估 (0-1)
        """
        value = 0.0

        # 检查组件类型是否对生物体有用
        component_type = component.type

        # 检查生物体是否已经有类似组件
        similar_components = [comp for comp in organism.components.values() if comp.type == component_type]

        if not similar_components:
            # 生物体没有类似组件，价值较高
            value += 0.5
        else:
            # 生物体已有类似组件，价值降低
            value += 0.1

        # 检查组件是否是先天组件
        if component.congenital:
            value += 0.2

        # 检查组件位置是否适合生物体
        if component.location == 'both' or (organism.membrane and component.location == 'external'):
            value += 0.2

        # 检查组件健康状态
        # 简单的健康状态检查，实际项目中可能需要更复杂的逻辑
        value += 0.1

        return value

    def select_best_component(self, organism: Organism, components: List[ComponentBase]) -> Optional[ComponentBase]:
        """选择最佳组件进行捕获

        参数:
            organism: Organism - 生物体实例
            components: List[ComponentBase] - 组件列表

        返回:
            Optional[ComponentBase] - 最佳组件，没有合适组件返回None
        """
        if not components:
            return None

        # 评估所有组件
        component_values = [(comp, self.evaluate_component(organism, comp)) for comp in components]

        # 选择价值最高的组件
        best_component, best_value = max(component_values, key=lambda x: x[1])

        # 只有价值超过阈值的组件才值得捕获
        if best_value < 0.5:
            return None

        return best_component

    def can_capture(self, organism: Organism, component: ComponentBase) -> bool:
        """检查生物体是否可以捕获组件

        参数:
            organism: Organism - 生物体实例
            component: ComponentBase - 组件实例

        返回:
            bool - 是否可以捕获
        """
        # 检查能量是否充足
        if organism.energy < self.capture_cost:
            return False

        # 检查组件是否在捕获范围内
        distance = np.linalg.norm(component.position - organism.position)
        if distance > self.scan_radius:
            return False

        # 检查生物体是否已经有太多组件
        if len(organism.components) >= 10:  # 简单的组件数量限制
            return False

        return True

    def capture_component(self, organism: Organism, component: ComponentBase) -> bool:
        """捕获组件

        参数:
            organism: Organism - 生物体实例
            component: ComponentBase - 组件实例

        返回:
            bool - 捕获是否成功
        """
        if not self.can_capture(organism, component):
            return False

        # 消耗能量
        organism.energy -= self.capture_cost

        # 设置组件为后天获得
        component.acquired = True
        component.congenital = False

        # 调整组件位置
        self.adjust_component_position(organism, component)

        # 添加组件到生物体
        success = organism.add_component(component)

        if success:
            print(f"生物体 {organism.id} 成功捕获组件: {component.type}")

        return success

    def adjust_component_position(self, organism: Organism, component: ComponentBase):
        """调整组件位置

        参数:
            organism: Organism - 生物体实例
            component: ComponentBase - 组件实例
        """
        # 根据组件类型调整位置
        if component.location == 'external':
            # 外部组件附着在细胞膜表面
            if organism.membrane:
                # 随机附着在细胞膜表面
                angle = np.random.uniform(0, 2 * np.pi)
                radius = organism.membrane.radius
                component.position = np.array([
                    radius * np.cos(angle),
                    radius * np.sin(angle)
                ])
        else:
            # 内部组件位于细胞内部
            component.position = np.random.randn(2) * 10  # 内部随机位置

    def integrate_component(self, organism: Organism, component: ComponentBase) -> bool:
        """整合组件到生物体

        参数:
            organism: Organism - 生物体实例
            component: ComponentBase - 组件实例

        返回:
            bool - 整合是否成功
        """
        # 简单的整合逻辑
        # 实际项目中可能需要更复杂的整合过程，如连接组件到PVAEC引擎

        # 检查组件是否已经在生物体中
        if component.id not in organism.components:
            return False

        # 从组件字典中查找PVAEC引擎
        for comp in organism.components.values():
            if isinstance(comp, PVAECEngine):
                # 自动连接传感器和执行器到PVAEC引擎
                if hasattr(component, 'sense') or hasattr(component, 'act'):
                    # 简单的连接逻辑，实际项目中可能需要更复杂的逻辑
                    pass
                break

        return True

    def perform_component_acquisition(self, organism: Organism, environment: Any) -> bool:
        """执行组件获取流程

        参数:
            organism: Organism - 生物体实例
            environment - 环境实例

        返回:
            bool - 是否成功获取组件
        """
        # 扫描附近组件
        nearby_components = self.scan_nearby_components(organism, environment)

        if not nearby_components:
            return False

        # 选择最佳组件
        best_component = self.select_best_component(organism, nearby_components)

        if not best_component:
            return False

        # 捕获组件
        if self.capture_component(organism, best_component):
            # 整合组件
            return self.integrate_component(organism, best_component)

        return False

    def release_component(self, organism: Organism, component_id: str) -> bool:
        """释放组件到环境

        参数:
            organism: Organism - 生物体实例
            component_id: str - 组件ID

        返回:
            bool - 释放是否成功
        """
        # 检查组件是否存在
        component = organism.get_component(component_id)
        if not component:
            return False

        # 从生物体中移除组件
        success = organism.remove_component(component_id)

        if success:
            # 设置组件为漂浮状态
            component.position = organism.position + np.random.randn(2) * 5
            # 实际项目中需要将组件添加到环境的漂浮系统
            # environment.add_floating_component(component)
            print(f"生物体 {organism.id} 释放组件: {component.type}")

        return success

    def get_acquisition_status(self, organism: Organism) -> Dict[str, Any]:
        """获取组件获取状态

        参数:
            organism: Organism - 生物体实例

        返回:
            Dict[str, Any] - 状态信息
        """
        # 计算已获取组件数量
        acquired_components = [comp for comp in organism.components.values() if comp.acquired]

        return {
            'total_components': len(organism.components),
            'acquired_components': len(acquired_components),
            'congenital_components': len(organism.components) - len(acquired_components),
            'scan_radius': self.scan_radius,
            'capture_cost': self.capture_cost,
            'energy_available': organism.energy >= self.capture_cost
        }
