"""记忆基因实现"""

from typing import Dict
import random
import numpy as np


class MemoryGene:
    """记忆基因 - 用于继承算法"""
    def __init__(self, situation: str, action_pattern: Dict[str, float], success_rate: float):
        self.situation = situation  # 触发情境
        self.action_pattern = action_pattern  # 动作模式 {tool_id: 控制信号}
        self.success_rate = success_rate  # 成功率
        self.strength = 1.0  # 记忆强度
        self.age = 0
        
    def mutate(self):
        """记忆变异"""
        if random.random() < 0.1:
            # 动作模式微调
            for tool_id in self.action_pattern:
                if random.random() < 0.3:
                    self.action_pattern[tool_id] = np.clip(
                        self.action_pattern[tool_id] + random.gauss(0, 0.1), -1, 1
                    )
                    
    def decay(self):
        """记忆衰减"""
        self.age += 1
        self.strength *= 0.99
