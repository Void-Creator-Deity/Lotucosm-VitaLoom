"""生态系统实现"""

import random
import pickle
from typing import List, Dict
from .base import Action, Species
from .memory import EcosystemMemoryGene
from .animals import Animal, Wolf, Sheep
from .plants import Grass


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
            EcosystemMemoryGene("饥饿", Action.MOVE_TOWARD_PREY, True, 0.9),
            EcosystemMemoryGene("受伤", Action.MOVE_AWAY_THREAT, True, 0.7),
        ]
        
        self.base_sheep_memories = [
            EcosystemMemoryGene("狼接近", Action.MOVE_AWAY_THREAT, True, 0.9),
            EcosystemMemoryGene("饥饿", Action.MOVE_TOWARD_FOOD, True, 0.8),
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
        return [g for g in self.grass \
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
            'avg_wolf_memories': sum(wolf_memories) / len(wolf_memories) if wolf_memories else 0,
            'avg_sheep_memories': sum(sheep_memories) / len(sheep_memories) if sheep_memories else 0,
            'total_memories': sum(wolf_memories) + sum(sheep_memories)
        }
    
    def save_state(self, filename: str = "ecosystem_state.pkl"):
        """保存当前生态系统状态到文件"""
        with open(filename, 'wb') as f:
            pickle.dump({
                'width': self.width,
                'height': self.height,
                'wolves': self.wolves,
                'sheep': self.sheep,
                'grass': self.grass,
                'time_step': self.time_step,
                'base_wolf_memories': self.base_wolf_memories,
                'base_sheep_memories': self.base_sheep_memories
            }, f)
        print(f"状态已保存到 {filename}")
    
    @classmethod
    def load_state(cls, filename: str = "ecosystem_state.pkl") -> 'Ecosystem':
        """从文件加载生态系统状态"""
        with open(filename, 'rb') as f:
            data = pickle.load(f)
        
        eco = cls(data['width'], data['height'])
        eco.wolves = data['wolves']
        eco.sheep = data['sheep']
        eco.grass = data['grass']
        eco.time_step = data['time_step']
        eco.base_wolf_memories = data['base_wolf_memories']
        eco.base_sheep_memories = data['base_sheep_memories']
        print(f"已从 {filename} 加载状态，当前时间步: {eco.time_step}")
        return eco
