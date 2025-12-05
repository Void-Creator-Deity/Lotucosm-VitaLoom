"""生态记忆基因实现"""

import random
from .base import Action


class EcosystemMemoryGene:
    """生态记忆基因"""
    def __init__(self, situation: str, action: Action, success: bool, strength: float = 1.0):
        self.situation = situation  # 情境：如"看到羊群", "饥饿", "被狼追"
        self.action = action
        self.success = success      # 该行为是否成功
        self.strength = strength    # 记忆强度
        self.age = 0                # 记忆年龄
        
    def get_weight(self) -> float:
        """计算行为权重：成功记忆正权重，失败记忆负权重"""
        base_weight = 1.0 if self.success else -1.0
        return base_weight * self.strength
        
    def mutate(self):
        """记忆变异：可能改变对成功与否的判断"""
        if random.random() < 0.03:
            self.success = not self.success  # 偶尔会"记错"结果
            
    def decay(self):
        """记忆衰减"""
        self.age += 1
        self.strength *= 0.99  # 每年衰减5%
