"""记忆系统：MemoryGene 可遗传单元与 MemorySystem 运行时存储/检索。

架构数据流::

    PVAECCycle.update_memory → MemorySystem.store
    PVAECCycle.retrieve_memories → MemorySystem.retrieve → generate_action

与 Organism.memory_genes（代际）分工：本模块侧重单体内 PVAEC 回合记忆；遗传走 builtin InheritanceSystem。
"""
from typing import Dict, List, Any
import random
import numpy as np

class MemoryGene:
    """记忆基因：情境 + 动作模式 + 成功率/强度，支持 copy/mutate/decay。

    生命周期:
        创建 → store 入 MemorySystem → retrieve 匹配 → decay 衰减 → 代际 copy/mutate（builtin）
    """

    def __init__(self, situation: str, action_pattern: Dict[str, float], success_rate: float):
        """初始化记忆基因。

        职责:
            绑定情境字符串、动作模式 dict 与初始成功率。

        时机:
            MemorySystem.store 从 memory_entry 构造。

        不变量:
            success_rate、strength 语义在 [0,1] 附近；age 从 0 起。

        排错:
            检索不到 → situation 与 perception 字符串化后须能子串匹配。
        """
        self.situation = situation  # 触发情境，由感知信号和内部状态组成
        self.action_pattern = action_pattern  # 动作模式，键为工具ID，值为控制信号
        self.success_rate = success_rate  # 成功率，0-1之间
        self.strength = 1.0  # 记忆强度，初始为1.0，0-1之间
        self.age = 0  # 记忆年龄，用于计算衰减

    def copy(self) -> "MemoryGene":
        """浅拷贝供 InheritanceSystem 代际遗传（独立 action_pattern 字典）。

        职责:
            复制 situation/success_rate/strength/age，动作模式为新 dict。

        时机:
            builtin 遗传流水线复制父代 memory_genes 时。

        不变量:
            不共享 action_pattern 引用。

        排错:
            子代与父代共用一个 dict → 勿绕过 copy 直接 append 引用。
        """
        clone = MemoryGene(
            situation=self.situation,
            action_pattern=dict(self.action_pattern),
            success_rate=float(self.success_rate),
        )
        clone.strength = float(self.strength)
        clone.age = int(self.age)
        return clone

    def mutate(self):
        """遗传时随机微调动作模式（10% 触发，30%  per 键高斯扰动）。

        职责:
            在 [-1,1] 内 clip 各 tool_id 控制量。

        时机:
            代际变异阶段（非每帧）。

        不变量:
            不改变 situation 字符串。

        排错:
            行为无变异 → 随机未命中 10% 门限，属预期。
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
        """记忆强度每调用 ×0.99，age += 1。

        职责:
            模拟遗忘，供 MemorySystem.decay_all_memories 批量调用。

        时机:
            宿主定期维护或世代边界（若接入）。

        不变量:
            strength 可趋近 0 但不强制删除（删除由 MemorySystem.store 容量策略负责）。

        排错:
            有效记忆被挤出 → max_memories 满后按 strength 删最弱项。
        """
        self.age += 1  # 记忆年龄增加1
        self.strength *= 0.99  # 记忆强度衰减1%


class MemorySystem:
    """运行时记忆表：store / retrieve / 强度更新与容量上限。

    与 Organism.memory_genes 及 IntelligentOrganism.memory 表分工不同；
    本类服务 PVAECCycle 回合内学习与检索。
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
        self.memories: List[MemoryGene] = []  # 记忆列表
        self.max_memories = 1000  # 最大记忆数量
        self.decay_rate = 0.99  # 记忆衰减率

    def store(self, memory_entry: Dict[str, Any]) -> None:
        """存储一条 PVAEC 记忆条目。

        职责:
            从 entry 提取 situation/action_pattern/success_rate 构造 MemoryGene 并 append。

        时机:
            PVAECCycle.update_memory 成功验证后。

        不变量:
            超 max_memories 时删除 strength 最低的一条。

        排错:
            记忆爆炸 → 调低 max_memories 或提高 decay 调用频率。
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
        """按情境字符串子串匹配检索，按 strength 取前 10。

        职责:
            将 perception 转为 str 与 MemoryGene.situation 互含匹配。

        时机:
            PVAECCycle.retrieve_memories → generate_action。

        不变量:
            返回新列表引用，最多 10 条。

        排错:
            恒为空 → 情境字符串不一致；可改用更相似度算法（当前为简化实现）。
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
        """调整单条记忆强度，钳制在 [0.1, 1.0]。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        memory.strength = max(0.1, min(1.0, memory.strength + delta))

    def decay_all_memories(self):
        """对所有 MemoryGene 调用 decay()。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        for memory in self.memories:
            memory.decay()

    def get_memories(self) -> List[MemoryGene]:
        """返回记忆列表浅拷贝。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        return self.memories.copy()

    def clear_memories(self):
        """清空记忆表（重置模拟时用）。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self.memories.clear()
