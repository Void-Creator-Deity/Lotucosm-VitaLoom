"""选择机制实现"""

from typing import List, Any
import random
from vitalloom.organisms.organism import Organism
from lotucosm.environment.environment import Environment


class SelectionSystem:
    """选择系统 - 管理生物体的选择机制
    
    负责：
    1. 自然选择
    2. 繁殖选择
    3. 适应度评估
    """
    
    def __init__(self):
        """初始化选择系统"""
        self.selection_strategy = "roulette_wheel"  # 选择策略：轮盘赌、锦标赛等
        self.tournament_size = 3  # 锦标赛选择的规模
    
    def evaluate_fitness(self, organism: Organism, environment: Environment) -> float:
        """评估生物体的适应度
        
        参数:
            organism: Organism - 生物体实例
            environment: Environment - 环境实例
        
        返回:
            float - 适应度值（0-1之间，越高表示适应度越好）
        """
        # 综合考虑多个因素计算适应度
        fitness = 0.0
        
        # 1. 能量水平（0-1之间）
        energy_fitness = organism.energy / organism.max_energy if organism.max_energy > 0 else 0.0
        
        # 2. 健康状况（0-1之间）
        health_fitness = organism.health / organism.max_health if organism.max_health > 0 else 0.0
        
        # 3. 年龄（考虑生存时间）
        # 年龄适应度随年龄增长而增加，但增长速度逐渐减缓
        age_fitness = 1.0 - (1.0 / (1.0 + organism.age / 100.0))
        
        # 4. 组件多样性（组件数量）
        component_fitness = min(len(organism.components) / 20.0, 1.0)  # 最多20个组件
        
        # 5. 记忆系统复杂度（记忆数量）
        memory_fitness = 0.0
        if organism.memory_system:
            memories: List[Any] = organism.memory_system.get_memories()
            memory_count = len(memories)
            memory_fitness = min(memory_count / 100.0, 1.0)  # 最多100个记忆
        
        # 加权综合
        fitness = (
            energy_fitness * 0.3 +
            health_fitness * 0.3 +
            age_fitness * 0.2 +
            component_fitness * 0.1 +
            memory_fitness * 0.1
        )
        
        return max(0.0, min(1.0, fitness))
    
    def select_for_reproduction(self, organisms: List[Organism], environment: Environment, count: int = 2) -> List[Organism]:
        """选择用于繁殖的生物体
        
        参数:
            organisms: List[Organism] - 生物体列表
            environment: Environment - 环境实例
            count: int - 选择数量
        
        返回:
            List[Organism] - 选择用于繁殖的生物体列表
        """
        if len(organisms) < count:
            return organisms.copy()
        
        # 根据选择策略执行选择
        if self.selection_strategy == "roulette_wheel":
            return self.roulette_wheel_selection(organisms, environment, count)
        elif self.selection_strategy == "tournament":
            return self.tournament_selection(organisms, environment, count)
        elif self.selection_strategy == "rank":
            return self.rank_selection(organisms, environment, count)
        else:
            # 默认使用轮盘赌选择
            return self.roulette_wheel_selection(organisms, environment, count)
    
    def roulette_wheel_selection(self, organisms: List[Organism], environment: Environment, count: int) -> List[Organism]:
        """轮盘赌选择
        
        参数:
            organisms: List[Organism] - 生物体列表
            environment: Environment - 环境实例
            count: int - 选择数量
        
        返回:
            List[Organism] - 选择的生物体列表
        """
        # 计算所有生物体的适应度
        fitnesses = [self.evaluate_fitness(organism, environment) for organism in organisms]
        total_fitness = sum(fitnesses)
        
        if total_fitness == 0:
            # 如果所有适应度都为0，随机选择
            return random.sample(organisms, count)
        
        # 计算累积适应度
        cumulative_fitness: List[float] = []
        current_sum = 0.0
        for fitness in fitnesses:
            current_sum += fitness
            cumulative_fitness.append(current_sum / total_fitness)
        
        # 选择生物体
        selected: List[Organism] = []
        for _ in range(count):
            r = random.random()
            for i, organism in enumerate(organisms):
                if r <= cumulative_fitness[i]:
                    selected.append(organism)
                    break
        
        return selected
    
    def tournament_selection(self, organisms: List[Organism], environment: Environment, count: int) -> List[Organism]:
        """锦标赛选择
        
        参数:
            organisms: List[Organism] - 生物体列表
            environment: Environment - 环境实例
            count: int - 选择数量
        
        返回:
            List[Organism] - 选择的生物体列表
        """
        selected: List[Organism] = []
        
        for _ in range(count):
            # 随机选择锦标赛参与者
            participants = random.sample(organisms, min(self.tournament_size, len(organisms)))
            
            # 选择适应度最高的参与者
            best_organism = max(participants, key=lambda o: self.evaluate_fitness(o, environment))
            selected.append(best_organism)
        
        return selected
    
    def rank_selection(self, organisms: List[Organism], environment: Environment, count: int) -> List[Organism]:
        """排名选择
        
        参数:
            organisms: List[Organism] - 生物体列表
            environment: Environment - 环境实例
            count: int - 选择数量
        
        返回:
            List[Organism] - 选择的生物体列表
        """
        # 按适应度排序
        ranked_organisms = sorted(organisms, key=lambda o: self.evaluate_fitness(o, environment), reverse=True)
        
        # 计算排名权重（线性排名）
        n = len(ranked_organisms)
        weights: List[float] = [i / n for i in range(1, n + 1)]
        total_weight = sum(weights)
        cumulative_weights: List[float] = []
        current_sum = 0.0
        
        for weight in weights:
            current_sum += weight / total_weight
            cumulative_weights.append(current_sum)
        
        # 选择生物体
        selected: List[Organism] = []
        for _ in range(count):
            r = random.random()
            for i, organism in enumerate(ranked_organisms):
                if r <= cumulative_weights[i]:
                    selected.append(organism)
                    break
        
        return selected
    
    def select_survivors(self, organisms: List[Organism], environment: Environment, max_population: int) -> List[Organism]:
        """选择幸存者（自然选择）
        
        参数:
            organisms: List[Organism] - 生物体列表
            environment: Environment - 环境实例
            max_population: int - 最大种群数量
        
        返回:
            List[Organism] - 幸存的生物体列表
        """
        if len(organisms) <= max_population:
            return organisms.copy()
        
        # 按适应度排序，保留前max_population个
        sorted_organisms = sorted(organisms, key=lambda o: self.evaluate_fitness(o, environment), reverse=True)
        return sorted_organisms[:max_population]
    
    def set_selection_strategy(self, strategy: str) -> None:
        """设置选择策略
        
        参数:
            strategy: str - 选择策略（"roulette_wheel", "tournament", "rank"）
        """
        if strategy in ["roulette_wheel", "tournament", "rank"]:
            self.selection_strategy = strategy
    
    def set_tournament_size(self, size: int) -> None:
        """设置锦标赛规模
        
        参数:
            size: int - 锦标赛规模（大于0）
        """
        if size > 0:
            self.tournament_size = size
    
    def get_selection_strategy(self) -> str:
        """获取选择策略
        
        返回:
            str - 当前选择策略
        """
        return self.selection_strategy