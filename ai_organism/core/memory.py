"""记忆基因实现"""

from typing import Dict
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
