from typing import Dict, Any, List

class PVAECCycle:
    """
    感知-验证自主演化循环 (PVAEC) 实现
    定义了数字生命"编织"智能的根本法则：
    感知 → 记忆 → 尝试 → 验证（利用新感知） → 再记忆 → ...
    """

    def __init__(self):
        """初始化PVAEC循环"""
        self.current_step = 0

    def run_cycle(self, organism: Any, environment: Any) -> bool:
        """
        运行完整的PVAEC循环

        参数:
        - organism: 生物体实例
        - environment: 环境实例

        返回:
        - bool: 循环是否成功完成
        """
        try:
            # 1. 感知阶段 - 生物体感知环境
            perception = self.perceive(organism, environment)

            # 2. 记忆检索阶段 - 检索相关经验记忆
            memories = self.retrieve_memories(organism, perception)

            # 3. 行动生成阶段 - 基于记忆生成探索性行动
            action = self.generate_action(organism, memories, perception)

            # 4. 执行阶段 - 执行行动
            result = self.execute_action(organism, environment, action)

            # 5. 验证阶段 - 利用新感知验证行动效果
            new_perception = self.perceive(organism, environment)
            success = self.validate_action(organism, perception, new_perception, action, result)

            # 6. 记忆更新阶段 - 更新记忆结构
            self.update_memory(organism, perception, action, result, success, new_perception)

            self.current_step += 1
            return True
        except Exception as e:
            print(f"PVAEC循环执行失败: {e}")
            return False

    def perceive(self, organism: Any, environment: Any) -> Dict[str, Any]:
        """
        感知阶段 - 生物体感知环境

        参数:
        - organism: 生物体实例
        - environment: 环境实例

        返回:
        - Dict[str, Any]: 感知结果
        """
        perception: Dict[str, Any] = {}
        # 收集所有传感器的感知结果
        if hasattr(organism, 'components'):
            components = getattr(organism, 'components', {})
            if hasattr(components, 'values'):
                for component in components.values():
                    if hasattr(component, 'sense'):
                        sense_result = component.sense(environment, organism)
                        perception[component.id] = sense_result

        return perception

    def retrieve_memories(self, organism: Any, perception: Dict[str, Any]) -> List[Any]:
        """
        记忆检索阶段 - 检索相关经验记忆

        参数:
        - organism: 生物体实例
        - perception: 感知结果

        返回:
        - List[Any]: 相关记忆列表
        """
        if hasattr(organism, 'memory_system') and hasattr(organism.memory_system, 'retrieve'):
            return organism.memory_system.retrieve(perception)
        return []

    def generate_action(self, organism: Any, memories: List[Any], perception: Dict[str, Any]) -> Dict[str, Any]:
        """
        行动生成阶段 - 基于记忆生成探索性行动

        参数:
        - organism: 生物体实例
        - memories: 相关记忆列表
        - perception: 感知结果

        返回:
        - Dict[str, Any]: 行动计划
        """
        action: Dict[str, Any] = {}

        # 1. 如果有记忆，优先基于记忆生成行动
        if memories:
            # 选择成功率最高的记忆
            best_memory = max(memories, key=lambda m: m.success_rate if hasattr(m, 'success_rate') else 0)
            action = best_memory.action_pattern if hasattr(best_memory, 'action_pattern') else {}

        # 2. 否则生成探索性行动
        if not action:
            # 随机激活一些执行器
            if hasattr(organism, 'components'):
                components = getattr(organism, 'components', {})
                if hasattr(components, 'values'):
                    for component in components.values():
                        if hasattr(component, 'act'):
                            action[component.id] = {
                                'command': 'explore',
                                'params': {}
                            }

        return action

    def execute_action(self, organism: Any, environment: Any, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行阶段 - 执行行动

        参数:
        - organism: 生物体实例
        - environment: 环境实例
        - action: 行动计划

        返回:
        - Dict[str, Any]: 执行结果
        """
        result: Dict[str, Any] = {}

        if hasattr(organism, 'components'):
            components = getattr(organism, 'components', {})
            if hasattr(components, 'get'):
                for component_id, action_details in action.items():
                    component = components.get(component_id)
                    if component and hasattr(component, 'act'):
                        act_result = component.act(environment, organism, action_details)
                        result[component_id] = act_result

        return result

    def validate_action(self, organism: Any, old_perception: Dict[str, Any], new_perception: Dict[str, Any], action: Dict[str, Any], result: Dict[str, Any]) -> float:
        """
        验证阶段 - 利用新感知验证行动效果

        参数:
        - organism: 生物体实例
        - old_perception: 行动前的感知
        - new_perception: 行动后的感知
        - action: 执行的行动
        - result: 行动结果

        返回:
        - float: 行动成功率 (0-1)
        """
        # 简单的验证逻辑：比较前后感知差异
        # 如果环境对生物体更有利，成功率更高

        # 计算感知差异
        success: float = 0.5  # 默认成功率

        # 检查能量变化
        if hasattr(organism, 'energy'):
            # 如果能量增加，成功率提高
            if organism.energy > getattr(organism, '_previous_energy', organism.energy):
                success += 0.3
            elif organism.energy < getattr(organism, '_previous_energy', organism.energy):
                success -= 0.3
            organism._previous_energy = organism.energy

        # 限制成功率在0-1之间
        return max(0, min(1, success))

    def update_memory(self, organism: Any, perception: Dict[str, Any], action: Dict[str, Any], result: Dict[str, Any], success: float, new_perception: Dict[str, Any]) -> None:
        """
        记忆更新阶段 - 更新记忆结构

        参数:
        - organism: 生物体实例
        - perception: 行动前的感知
        - action: 执行的行动
        - result: 行动结果
        - success: 行动成功率
        - new_perception: 行动后的感知
        """
        if hasattr(organism, 'memory_system') and hasattr(organism.memory_system, 'store'):
            # 构建记忆条目
            memory_entry: Dict[str, Any] = {
                'situation': perception,
                'action_pattern': action,
                'result': result,
                'success_rate': success,
                'timestamp': self.current_step,
                'previous_situation': new_perception
            }

            # 存储记忆
            organism.memory_system.store(memory_entry)
