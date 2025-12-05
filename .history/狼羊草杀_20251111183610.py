import numpy as np
import random
from enum import Enum
from typing import List, Dict, Tuple
from collections import defaultdict

class Action(Enum):
    MOVE_RANDOM = "随机移动"
    MOVE_TOWARD_PREY = "追踪猎物" 
    MOVE_TOWARD_FOOD = "寻找食物"
    MOVE_AWAY_THREAT = "逃离威胁"
    STAY_STILL = "保持静止"
    REPRODUCE = "繁殖"

class Species(Enum):
    WOLF = "狼"
    SHEEP = "羊" 
    GRASS = "草"

class MemoryGene:
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
        if random.random() < 0.05:
            self.success = not self.success  # 偶尔会"记错"结果
            
    def decay(self):
        """记忆衰减"""
        self.age += 1
        self.strength *= 0.95  # 每年衰减5%

class Animal:
    """动物基类，拥有记忆继承能力"""
    
    def __init__(self, x: int, y: int, energy: int, inherited_memories: List[MemoryGene] = None):
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
        new_memory = MemoryGene(situation, action, success, strength=0.3)
        self.personal_memories.append(new_memory)
        
    def reproduce(self) -> 'Animal':
        """繁殖后代，传递记忆"""
        # 能量消耗
        self.energy -= 20
        
        # 选择强记忆遗传
        strong_memories = [m for m in self.memory_bank + self.personal_memories 
                          if m.strength > 0.5]
        inherited_memories = []
        
        for memory in strong_memories:
            if random.random() < memory.strength:  # 强度决定遗传概率
                new_memory = MemoryGene(
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
    def __init__(self, x: int, y: int, energy: int = 100, inherited_memories=None):
        super().__init__(x, y, energy, inherited_memories)
        self.species = Species.WOLF
        
    def _instinct_behavior(self, situation: str) -> Action:
        if "饥饿" in situation or "看到羊群" in situation:
            return Action.MOVE_TOWARD_PREY
        return Action.MOVE_RANDOM

class Sheep(Animal):
    def __init__(self, x: int, y: int, energy: int = 80, inherited_memories=None):
        super().__init__(x, y, energy, inherited_memories)
        self.species = Species.SHEEP
        
    def _instinct_behavior(self, situation: str) -> Action:
        if "狼接近" in situation:
            return Action.MOVE_AWAY_THREAT
        if "饥饿" in situation:
            return Action.MOVE_TOWARD_FOOD
        return Action.MOVE_RANDOM

class Grass:
    """草类，简单的资源"""
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.growth_level = 1.0  # 生长等级
        
    def grow(self):
        """草生长"""
        self.growth_level = min(1.0, self.growth_level + 0.2)
        
    def eaten(self):
        """被吃后重置"""
        self.growth_level = 0.0

class Ecosystem:
    """生态系统"""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.wolves: List[Wolf] = []
        self.sheep: List[Sheep] = []
        self.grass: List[Grass] = []
        self.time_step = 0
        
        # 初始化基础记忆库
        self.base_wolf_memories = [
            MemoryGene("饥饿", Action.MOVE_TOWARD_PREY, True, 0.9),
            MemoryGene("受伤", Action.MOVE_AWAY_THREAT, True, 0.7),
        ]
        
        self.base_sheep_memories = [
            MemoryGene("狼接近", Action.MOVE_AWAY_THREAT, True, 0.9),
            MemoryGene("饥饿", Action.MOVE_TOWARD_FOOD, True, 0.8),
        ]
        
        self.initialize_ecosystem()
        
    def initialize_ecosystem(self):
        """初始化生态系统"""
        # 创建草
        for _ in range(100):
            x, y = random.randint(0, self.width-1), random.randint(0, self.height-1)
            self.grass.append(Grass(x, y))
            
        # 创建狼
        for _ in range(5):
            x, y = random.randint(0, self.width-1), random.randint(0, self.height-1)
            self.wolves.append(Wolf(x, y, inherited_memories=self.base_wolf_memories.copy()))
            
        # 创建羊
        for _ in range(20):
            x, y = random.randint(0, self.width-1), random.randint(0, self.height-1)
            self.sheep.append(Sheep(x, y, inherited_memories=self.base_sheep_memories.copy()))
    
    def get_nearby_animals(self, x: int, y: int, radius: int) -> List[Animal]:
        """获取附近的动物"""
        nearby = []
        for wolf in self.wolves:
            if abs(wolf.x - x) <= radius and abs(wolf.y - y) <= radius:
                nearby.append(wolf)
        for sheep in self.sheep:
            if abs(sheep.x - x) <= radius and abs(sheep.y - y) <= radius:
                nearby.append(sheep)
        return nearby
        
    def get_nearby_grass(self, x: int, y: int, radius: int) -> List[Grass]:
        """获取附近的草"""
        return [g for g in self.grass 
                if abs(g.x - x) <= radius and abs(g.y - y) <= radius and g.growth_level > 0.5]
    
    def simulate_step(self):
        """模拟一个时间步"""
        self.time_step += 1
        
        # 动物行动阶段
        for wolf in self.wolves[:]:  # 使用切片避免修改列表问题
            self.animal_action(wolf)
            
        for sheep in self.sheep[:]:
            self.animal_action(sheep)
            
        # 草生长
        for grass in self.grass:
            grass.grow()
            
        # 能量消耗和死亡
        self.handle_energy_and_death()
        
        # 繁殖检查
        self.handle_reproduction()
        
    def animal_action(self, animal: Animal):
        """处理单个动物的行动"""
        # 感知环境
        situation = animal.perceive_situation(self)
        
        # 决策行动
        action = animal.decide_action(situation, self)
        
        # 执行行动并学习
        success = self.execute_action(animal, action, situation)
        animal.learn_from_experience(situation, action, success)
        
        # 记忆衰减
        for memory in animal.memory_bank:
            memory.decay()
            
        # 年龄增长
        animal.age += 1
        
    def execute_action(self, animal: Animal, action: Action, situation: str) -> bool:
        """执行动物行动并返回是否成功"""
        old_x, old_y = animal.x, animal.y
        
        # 移动行动
        if action == Action.MOVE_RANDOM:
            animal.x += random.choice([-1, 0, 1])
            animal.y += random.choice([-1, 0, 1])
            
        elif action == Action.MOVE_TOWARD_PREY:
            # 寻找最近的猎物/食物并移动
            target = self.find_nearest_target(animal)
            if target:
                if target.x > animal.x: animal.x += 1
                elif target.x < animal.x: animal.x -= 1
                if target.y > animal.y: animal.y += 1  
                elif target.y < animal.y: animal.y -= 1
                
        elif action == Action.MOVE_AWAY_THREAT:
            # 远离威胁
            threat = self.find_nearest_threat(animal)
            if threat:
                if threat.x > animal.x: animal.x -= 1
                elif threat.x < animal.x: animal.x += 1
                if threat.y > animal.y: animal.y -= 1
                elif threat.y < animal.y: animal.y += 1
                
        elif action == Action.REPRODUCE:
            if animal.energy > 50:
                return True  # 繁殖总是"成功"的，但需要能量条件
            return False
            
        # 边界检查
        animal.x = max(0, min(self.width-1, animal.x))
        animal.y = max(0, min(self.height-1, animal.y))
        
        # 处理交互
        return self.handle_interactions(animal, old_x, old_y)
        
    def find_nearest_target(self, animal: Animal):
        """寻找最近的目标（狼找羊，羊找草）"""
        if animal.species == Species.WOLF:
            targets = self.sheep
        else:  # SHEEP
            targets = self.grass
            targets = [g for g in targets if g.growth_level > 0.5]
            
        if not targets:
            return None
            
        return min(targets, key=lambda t: abs(t.x - animal.x) + abs(t.y - animal.y))
        
    def find_nearest_threat(self, animal: Animal):
        """寻找最近的威胁"""
        if animal.species == Species.SHEEP:
            threats = self.wolves
            if not threats:
                return None
            return min(threats, key=lambda t: abs(t.x - animal.x) + abs(t.y - animal.y))
        return None
        
    def handle_interactions(self, animal: Animal, old_x: int, old_y: int) -> bool:
        """处理动物与环境的交互"""
        success = False
        
        if animal.species == Species.WOLF:
            # 狼吃羊
            for sheep in self.sheep[:]:
                if sheep.x == animal.x and sheep.y == animal.y:
                    animal.energy += 30
                    self.sheep.remove(sheep)
                    success = True
                    break
                    
        elif animal.species == Species.SHEEP:
            # 羊吃草
            for grass in self.grass:
                if grass.x == animal.x and grass.y == animal.y and grass.growth_level > 0.5:
                    animal.energy += 20
                    grass.eaten()
                    success = True
                    break
                    
        # 移动消耗能量
        if (animal.x, animal.y) != (old_x, old_y):
            animal.energy -= 1
            
        return success
        
    def handle_energy_and_death(self):
        """处理能量消耗和死亡"""
        # 狼死亡检查
        for wolf in self.wolves[:]:
            wolf.energy -= 2  # 基础代谢
            if wolf.energy <= 0 or wolf.age > 50:
                self.wolves.remove(wolf)
                
        # 羊死亡检查  
        for sheep in self.sheep[:]:
            sheep.energy -= 1  # 基础代谢
            if sheep.energy <= 0 or sheep.age > 30:
                self.sheep.remove(sheep)
                
    def handle_reproduction(self):
        """处理繁殖"""
        new_wolves = []
        new_sheep = []
        
        # 狼繁殖
        for wolf in self.wolves:
            if wolf.energy > 60 and random.random() < 0.1:  # 10%几率繁殖
                child = wolf.reproduce()
                new_wolves.append(child)
                
        # 羊繁殖
        for sheep in self.sheep:
            if sheep.energy > 40 and random.random() < 0.2:  # 20%几率繁殖
                child = sheep.reproduce()
                new_sheep.append(child)
                
        self.wolves.extend(new_wolves)
        self.sheep.extend(new_sheep)
        
    def get_statistics(self) -> Dict:
        """获取生态系统统计信息"""
        wolf_memories = [len(wolf.memory_bank) for wolf in self.wolves]
        sheep_memories = [len(sheep.memory_bank) for sheep in self.sheep]
        
        return {
            'time_step': self.time_step,
            'wolf_count': len(self.wolves),
            'sheep_count': len(self.sheep),
            'grass_count': len([g for g in self.grass if g.growth_level > 0.5]),
            'avg_wolf_memories': np.mean(wolf_memories) if wolf_memories else 0,
            'avg_sheep_memories': np.mean(sheep_memories) if sheep_memories else 0,
            'total_memories': sum(wolf_memories) + sum(sheep_memories)
        }

# 模拟运行
def run_simulation():
    ecosystem = Ecosystem(50, 50)
    
    print("开始生态模拟...")
    print("时间步 | 狼数量 | 羊数量 | 草数量 | 平均记忆数")
    print("-" * 50)
    
    for step in range(1000):
        ecosystem.simulate_step()
        
        if step % 50 == 0:
            stats = ecosystem.get_statistics()
            print(f"{stats['time_step']:6} | {stats['wolf_count']:6} | "
                  f"{stats['sheep_count']:6} | {stats['grass_count']:6} | "
                  f"{stats['avg_wolf_memories']:.1f}/{stats['avg_sheep_memories']:.1f}")
                  
        # 如果种群灭绝，重新初始化
        if len(ecosystem.wolves) == 0 or len(ecosystem.sheep) == 0:
            print("种群失衡，重新初始化...")
            ecosystem.initialize_ecosystem()
            
    return ecosystem

if __name__ == "__main__":
    final_ecosystem = run_simulation()
    
    # 分析记忆进化
    if final_ecosystem.wolves:
        wolf = final_ecosystem.wolves[0]
        print(f"\n最终一代狼的记忆库({len(wolf.memory_bank)}个记忆):")
        for i, memory in enumerate(wolf.memory_bank[:5]):
            print(f"  {memory.situation} -> {memory.action.value} (成功:{memory.success}, 强度:{memory.strength:.2f})")