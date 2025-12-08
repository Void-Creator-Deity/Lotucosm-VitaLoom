"""记忆系统实现"""

from typing import Dict, List, Any
import random
import numpy as np

class MemoryGene:
    """记忆基因 - AI生命体的结构化记忆单元

    用于实现记忆的遗传和进化，每个记忆基因包含一个特定情境下的动作模式
    以及该模式的成功率和强度信息。记忆基因可以在代际间遗传，并在遗传过程中发生变异。

    属性:
        situation: str - 触发记忆的情境描述，由感知信号和内部状态组成
        action_pattern: Dict[str, float] - 动作模式，键为工具ID，值为对应的控制信号
        success_rate: float - 该记忆对应的动作模式的成功率（0-1之间）
        strength: float - 记忆的强度（0-1之间），影响记忆的遗传概率
        age: int - 记忆的年龄，影响记忆的衰减
    """

    def __init__(self, situation: str, action_pattern: Dict[str, float], success_rate: float):
        """初始化记忆基因

        参数:
            situation: str - 触发记忆的情境描述
            action_pattern: Dict[str, float] - 动作模式，{工具ID: 控制信号}
            success_rate: float - 该动作模式的成功率（0-1之间）
        """
        self.situation = situation  # 触发情境，由感知信号和内部状态组成
        self.action_pattern = action_pattern  # 动作模式，键为工具ID，值为控制信号
        self.success_rate = success_rate  # 成功率，0-1之间
        self.strength = 1.0  # 记忆强度，初始为1.0，0-1之间
        self.age = 0  # 记忆年龄，用于计算衰减

    def mutate(self):
        """记忆变异 - 在遗传过程中随机调整动作模式

        实现了记忆的变异机制，有10%的概率触发变异，
        变异时会有30%的概率调整每个动作的控制信号，
        调整幅度服从高斯分布（均值0，标准差0.1），
        最终结果会被限制在[-1, 1]范围内。
        """
        if random.random() < 0.1:  # 10%的概率触发变异
            # 动作模式微调
            for tool_id in self.action_pattern:
                if random.random() < 0.3:  # 30%的概率调整该动作
                    # 高斯分布调整，均值0，标准差0.1
                    self.action_pattern[tool_id] = np.clip(
                        self.action_pattern[tool_id] + random.gauss(0, 0.1), -1, 1
                    )

    def decay(self):
        """记忆衰减 - 随时间降低记忆强度

        实现了记忆的自然衰减机制，
        每次调用时，记忆年龄加1，
        记忆强度乘以0.99，模拟记忆随时间逐渐遗忘的过程。
        """
        self.age += 1  # 记忆年龄增加1
        self.strength *= 0.99  # 记忆强度衰减1%

class MemorySystem:
    """记忆系统 - 管理生物体的记忆存储、检索和更新

    实现了记忆的完整生命周期管理，包括：
    1. 记忆的存储和组织
    2. 基于情境的记忆检索
    3. 记忆的更新和强化
    4. 记忆的遗传和变异
    """

    def __init__(self):
        """初始化记忆系统"""
        self.memories: List[MemoryGene] = []  # 记忆列表
        self.max_memories = 1000  # 最大记忆数量
        self.decay_rate = 0.99  # 记忆衰减率

    def store(self, memory_entry: Dict[str, Any]) -> None:
        """存储新记忆

        参数:
            memory_entry: Dict[str, Any] - 记忆条目，包含情境、动作模式、结果和成功率
        """
        # 构建记忆情境描述
        situation = str(memory_entry.get('situation', {}))
        action_pattern = memory_entry.get('action_pattern', {})
        success_rate = memory_entry.get('success_rate', 0.5)

        # 创建新的记忆基因
        new_memory = MemoryGene(situation, action_pattern, success_rate)

        # 存储记忆
        self.memories.append(new_memory)

        # 限制记忆数量
        if len(self.memories) > self.max_memories:
            # 移除强度最低的记忆
            self.memories.sort(key=lambda m: float(m.strength))
            self.memories.pop(0)

    def retrieve(self, perception: Dict[str, Any]) -> List[MemoryGene]:
        """基于感知情境检索相关记忆

        参数:
            perception: Dict[str, Any] - 当前感知情境

        返回:
            List[MemoryGene] - 相关记忆列表
        """
        # 简化的记忆检索：基于情境相似度
        # 这里使用简单的字符串匹配，实际应用中可以使用更复杂的相似度算法
        situation = str(perception)
        relevant_memories: List[MemoryGene] = []

        for memory in self.memories:
            # 计算情境相似度（简单的字符串匹配）
            if situation in memory.situation or memory.situation in situation:
                relevant_memories.append(memory)

        # 按强度排序，返回前10个最相关的记忆
        relevant_memories.sort(key=lambda m: float(m.strength), reverse=True)
        return relevant_memories[:10]

    def update_memory_strength(self, memory: MemoryGene, delta: float):
        """更新记忆强度

        参数:
            memory: MemoryGene - 要更新的记忆
            delta: float - 强度变化量（正数表示增强，负数表示减弱）
        """
        memory.strength = max(0.1, min(1.0, memory.strength + delta))

    def decay_all_memories(self):
        """衰减所有记忆的强度

        定期调用，让所有记忆自然衰减
        """
        for memory in self.memories:
            memory.decay()

    def get_memories(self) -> List[MemoryGene]:
        """获取所有记忆

        返回:
            List[MemoryGene] - 所有记忆列表
        """
        return self.memories.copy()

    def clear_memories(self):
        """清除所有记忆

        用于重置记忆系统
        """
        self.memories.clear()
