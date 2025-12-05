"""动物实现"""

import random
from typing import List, Dict
from collections import defaultdict
from .base import Action, Species
from .memory import EcosystemMemoryGene


class Animal:
    """动物基类，拥有记忆继承能力"""
    
    def __init__(self, x: int, y: int, energy: int, inherited_memories: List[EcosystemMemoryGene] = None):
        self.x = x
        self.y = y 
        self.energy = energy
        self.age = 0
        self.memory_bank = inherited_memories if inherited_memories else []
        self.personal_memories = []  # 个体学习的新记忆
        self.species = None
        
    def perceive_situation(self, world: 'Ecosystem') -> str:
        """感知当前环境状况"""
        perceptions = []
        
        # 检查周围环境
        nearby_animals = world.get_nearby_animals(self.x, self.y, radius=3)
        
        # 狼的感知
        if self.species == Species.WOLF:
            nearby_sheep = [a for a in nearby_animals if a.species == Species.SHEEP]
            if nearby_sheep:
                perceptions.append("看到羊群")
            if self.energy < 30:
                perceptions.append("饥饿")
            if len(nearby_sheep) > 2:
                perceptions.append("羊群众多")
                
        # 羊的感知  
        elif self.species == Species.SHEEP:
            nearby_wolves = [a for a in nearby_animals if a.species == Species.WOLF]
            nearby_grass = world.get_nearby_grass(self.x, self.y, radius=2)
            
            if nearby_wolves:
                perceptions.append("狼接近")
            if self.energy < 20:
                perceptions.append("饥饿")
            if nearby_grass:
                perceptions.append("有草可吃")
                
        return "&".join(perceptions) if perceptions else "平静"
    
    def decide_action(self, situation: str, world: 'Ecosystem') -> Action:
        """基于遗传记忆和个体经验决策"""
        relevant_memories = []
        
        # 检索相关记忆
        for memory in self.memory_bank + self.personal_memories:
            if any(s in memory.situation for s in situation.split("&")):
                relevant_memories.append(memory)
                
        if not relevant_memories:
            # 没有相关记忆，使用本能行为
            return self._instinct_behavior(situation)
            
        # 基于记忆权重选择行动
        action_weights = defaultdict(float)
        for memory in relevant_memories:
            action_weights[memory.action] += memory.get_weight()
            
        # 加入探索机制
        if random.random() < 0.2:  # 20%探索新行为
            return random.choice(list(Action))
            
        # 选择权重最高的行为
        if action_weights:
            best_action = max(action_weights.items(), key=lambda x: x[1])[0]
            return best_action
        else:
            return self._instinct_behavior(situation)
            
    def _instinct_behavior(self, situation: str) -> Action:
        """物种本能行为"""
        if self.species == Species.WOLF:
            if "饥饿" in situation:
                return Action.MOVE_TOWARD_PREY
            return Action.MOVE_RANDOM
        elif self.species == Species.SHEEP:
            if "饥饿" in situation:
                return Action.MOVE_TOWARD_FOOD
            if "狼接近" in situation:
                return Action.MOVE_AWAY_THREAT
            return Action.MOVE_RANDOM
            
    def learn_from_experience(self, situation: str, action: Action, success: bool):
        """从本次行动结果中学习"""
        # 寻找类似记忆
        for memory in self.personal_memories:
            if memory.situation == situation and memory.action == action:
                # 强化或削弱现有记忆
                if memory.success == success:
                    memory.strength = min(1.0, memory.strength + 0.1)
                else:
                    memory.strength = max(0.1, memory.strength - 0.2)
                return
                
        # 创建新记忆
        new_memory = EcosystemMemoryGene(situation, action, success, strength=0.3)
        self.personal_memories.append(new_memory)
        
    def reproduce(self) -> 'Animal':
        """繁殖后代，传递记忆"""
        # 能量消耗
        self.energy -= 20
        
        # 选择强记忆遗传
        strong_memories = [m for m in self.memory_bank + self.personal_memories \
                          if m.strength > 0.5]
        inherited_memories = []
        
        for memory in strong_memories:
            if random.random() < memory.strength:  # 强度决定遗传概率
                new_memory = EcosystemMemoryGene(
                    memory.situation, 
                    memory.action, 
                    memory.success,
                    memory.strength * 0.8  # 遗传后强度减弱
                )
                new_memory.mutate()
                inherited_memories.append(new_memory)
                
        # 创建后代
        child = Animal(self.x, self.y, energy=50, inherited_memories=inherited_memories)
        child.species = self.species
        
        return child


class Wolf(Animal):
    """狼类，捕食者"""
    def __init__(self, x: int, y: int, energy: int = 100, inherited_memories=None):
        super().__init__(x, y, energy, inherited_memories)
        self.species = Species.WOLF
        
    def _instinct_behavior(self, situation: str) -> Action:
        """狼的本能行为"""
        if "饥饿" in situation or "看到羊群" in situation:
            return Action.MOVE_TOWARD_PREY
        return Action.MOVE_RANDOM


class Sheep(Animal):
    """羊类，食草动物"""
    def __init__(self, x: int, y: int, energy: int = 80, inherited_memories=None):
        super().__init__(x, y, energy, inherited_memories)
        self.species = Species.SHEEP
        
    def _instinct_behavior(self, situation: str) -> Action:
        """羊的本能行为"""
        if "狼接近" in situation:
            return Action.MOVE_AWAY_THREAT
        if "饥饿" in situation:
            return Action.MOVE_TOWARD_FOOD
        return Action.MOVE_RANDOM
