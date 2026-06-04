"""PS 组件自组装/附着规则（莲池 tick 可选阶段）。

排错: 见 `builtin/README.md`。
"""

from typing import List, Dict, Optional, Any, TYPE_CHECKING
import random

# 使用TYPE_CHECKING避免循环导入
if TYPE_CHECKING:
    from builtin.components.components_base import ComponentBase
from builtin.components.connection import Connection


class AssemblySystem:
    """自组装系统 - 管理组件的自组装机制
    
    负责：
    1. 组件碰撞检测
    2. 组件自动连线
    3. 组件系统形成
    4. 自组装规则管理
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
        self.assembly_enabled = True  # 是否启用自组装
        self.collision_radius = 10.0  # 组件碰撞半径
        self.assembly_probability = 0.1  # 组件自组装概率
        self.assembly_rules = self._load_assembly_rules()  # 自组装规则
    
    def _load_assembly_rules(self) -> Dict[str, Dict[str, Any]]:
        """加载自组装规则
        
        返回:
            Dict[str, Dict[str, Any]] - 自组装规则字典
        """
        # 预设的自组装规则
        return {
            "sensor-actuator": {
                "conditions": [
                    {"type": "sensor"},  # 传感器
                    {"type": "actuator"}  # 执行器
                ],
                "result": "reflex_arc",  # 形成反射弧
                "probability": 0.8  # 组装概率
            },
            "sensor-sensor": {
                "conditions": [
                    {"type": "sensor"},
                    {"type": "sensor"}
                ],
                "result": "composite_sensor",  # 形成复合传感器
                "probability": 0.6
            },
            "actuator-actuator": {
                "conditions": [
                    {"type": "actuator"},
                    {"type": "actuator"}
                ],
                "result": "coordinated_actuators",  # 形成协同执行器
                "probability": 0.6
            },
            "sensor-hybrid": {
                "conditions": [
                    {"type": "sensor"},
                    {"type": "hybrid"}
                ],
                "result": "enhanced_sensing",  # 增强感知
                "probability": 0.7
            },
            "actuator-hybrid": {
                "conditions": [
                    {"type": "actuator"},
                    {"type": "hybrid"}
                ],
                "result": "enhanced_actuation",  # 增强执行
                "probability": 0.7
            },
            "hybrid-hybrid": {
                "conditions": [
                    {"type": "hybrid"},
                    {"type": "hybrid"}
                ],
                "result": "complex_system",  # 形成复杂系统
                "probability": 0.5
            }
        }
    
    def check_collision(self, component1: 'ComponentBase', component2: 'ComponentBase') -> bool:
        """检查两个组件是否发生碰撞。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if not hasattr(component1, 'position') or not hasattr(component2, 'position'):
            return False
        
        # 计算两个组件之间的距离
        dx = component1.position[0] - component2.position[0]
        dy = component1.position[1] - component2.position[1]
        distance = (dx ** 2 + dy ** 2) ** 0.5
        
        return distance <= self.collision_radius
    
    def check_assembly_possible(self, component1: 'ComponentBase', component2: 'ComponentBase') -> Optional[Dict[str, Any]]:
        """检查两个组件是否可以自组装。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 确定组件类型
        type1 = self._get_component_type(component1)
        type2 = self._get_component_type(component2)
        
        # 检查所有可能的规则
        for rule in self.assembly_rules.values():
            # 规则条件
            conditions = rule["conditions"]
            
            # 检查组件是否符合规则条件
            if len(conditions) != 2:
                continue
            
            # 检查条件1
            condition1 = conditions[0]
            condition2 = conditions[1]
            
            # 检查组件1是否符合条件1，组件2是否符合条件2
            if (self._component_matches_condition(component1, type1, condition1) and
                self._component_matches_condition(component2, type2, condition2)):
                return rule
            
            # 检查组件1是否符合条件2，组件2是否符合条件1（顺序无关）
            if (self._component_matches_condition(component1, type1, condition2) and
                self._component_matches_condition(component2, type2, condition1)):
                return rule
        
        return None
    
    def _get_component_type(self, component: 'ComponentBase') -> str:
        """获取组件类型
        
        参数:
            component: ComponentBase - 组件
        
        返回:
            str - 组件类型（sensor, actuator, hybrid）
        """
        if hasattr(component, 'is_sensor') and hasattr(component, 'is_actuator'):
            if component.is_sensor and component.is_actuator:
                return "hybrid"
            elif component.is_sensor:
                return "sensor"
            elif component.is_actuator:
                return "actuator"
        elif hasattr(component, 'is_sensor') and component.is_sensor:
            return "sensor"
        elif hasattr(component, 'is_actuator') and component.is_actuator:
            return "actuator"
        
        return "unknown"
    
    def _component_matches_condition(self, component: 'ComponentBase', component_type: str, condition: Dict[str, Any]) -> bool:
        """检查组件是否符合条件
        
        参数:
            component: ComponentBase - 组件
            component_type: str - 组件类型
            condition: Dict[str, Any] - 条件
        
        返回:
            bool - 是否符合条件
        """
        if "type" in condition:
            return component_type == condition["type"]
        
        return False
    
    def assemble_components(self, component1: 'ComponentBase', component2: 'ComponentBase', rule: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """组装两个组件。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 检查组装概率
        if random.random() > rule.get("probability", self.assembly_probability):
            return None
        
        # 创建连接
        connection = self._create_connection(component1, component2, rule)
        
        # 设置连接
        component1.add_connection(connection)
        component2.add_connection(connection)
        
        # 返回组装结果
        return {
            "result": rule["result"],
            "component1": component1.id,
            "component2": component2.id,
            "connection": connection.id
        }
    
    def _create_connection(self, component1: 'ComponentBase', component2: 'ComponentBase', rule: Dict[str, Any]) -> Connection:
        """创建组件之间的连接
        
        参数:
            component1: ComponentBase - 第一个组件
            component2: ComponentBase - 第二个组件
            rule: Dict[str, Any] - 组装规则
        
        返回:
            Connection - 创建的连接
        """
        # 确定连接方向
        # 传感器 -> 执行器
        if self._get_component_type(component1) == "sensor" and self._get_component_type(component2) == "actuator":
            source = component1
            target = component2
        # 执行器 -> 传感器（反向）
        elif self._get_component_type(component1) == "actuator" and self._get_component_type(component2) == "sensor":
            source = component2
            target = component1
        # 传感器 -> 传感器
        elif self._get_component_type(component1) == "sensor" and self._get_component_type(component2) == "sensor":
            # 随机选择源和目标
            source = component1 if random.random() < 0.5 else component2
            target = component2 if source == component1 else component1
        # 执行器 -> 执行器
        elif self._get_component_type(component1) == "actuator" and self._get_component_type(component2) == "actuator":
            # 随机选择源和目标
            source = component1 if random.random() < 0.5 else component2
            target = component2 if source == component1 else component1
        # 其他情况
        else:
            source = component1
            target = component2
        
        # 创建连接
        connection = Connection(
            source=source,
            target=target,
            id=f"connection_{random.randint(1000, 9999)}",
            connection_type=rule["result"]
        )
        
        return connection
    
    def update(self, floating_components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """更新自组装系统。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if not self.assembly_enabled:
            return []
        
        assembly_events: List[Dict[str, Any]] = []
        
        # 检查所有组件对之间的碰撞和自组装
        for i in range(len(floating_components)):
            for j in range(i + 1, len(floating_components)):
                comp1_data = floating_components[i]
                comp2_data = floating_components[j]
                
                component1 = comp1_data["component"]
                component2 = comp2_data["component"]
                
                # 检查碰撞
                if self.check_collision(component1, component2):
                    # 检查是否可以自组装
                    rule = self.check_assembly_possible(component1, component2)
                    if rule:
                        # 尝试自组装
                        result = self.assemble_components(component1, component2, rule)
                        if result:
                            assembly_events.append(result)
        
        return assembly_events
    
    def enable_assembly(self):
        """启用自组装。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self.assembly_enabled = True
    
    def disable_assembly(self):
        """禁用自组装。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self.assembly_enabled = False
    
    def set_assembly_probability(self, probability: float):
        """设置自组装概率。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self.assembly_probability = max(0.0, min(1.0, probability))
    
    def get_assembly_rules(self) -> Dict[str, Dict[str, Any]]:
        """获取自组装规则。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        return self.assembly_rules.copy()
