"""PS 适应度选择与精英保留（PVAECOrchestrator 评估/繁殖阶段）。

排错: 见 `builtin/README.md`。
"""
from typing import List, Dict, Any, Optional
import random
from builtin.entity_types.organism import Organism
from core.Lotucosm.randomness import weighted_choices


class SelectionSystem:
    """选择系统 - 处理生物体的选择

    负责处理生物体的自然选择，包括：
    - 适应度评估
    - 选择策略
    - 淘汰机制
    """

    def __init__(self, *, randomness_rng=None):
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
        self.randomness_owner_mode = "runtime" if randomness_rng is not None else "detached"
        self.randomness_rng = randomness_rng if randomness_rng is not None else random.Random(12345)
        self.selection_pressure = 0.5  # 选择压力
        self.elitism_rate = 0.1  # 精英保留率

    def set_selection_pressure(self, pressure: float) -> None:
        """设置选择压力。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self.selection_pressure = max(0.0, min(1.0, pressure))

    def set_elitism_rate(self, rate: float) -> None:
        """设置精英保留率。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self.elitism_rate = max(0.0, min(1.0, rate))

    def select(self, organisms: List[Organism], count: int) -> List[Organism]:
        """选择生物体。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 计算适应度
        fitness_scores = [self._calculate_fitness(org) for org in organisms]

        # 按适应度排序
        sorted_organisms = sorted(zip(organisms, fitness_scores), key=lambda x: x[1], reverse=True)

        # 精英保留
        elite_count = int(len(organisms) * self.elitism_rate)
        selected = [org for org, _ in sorted_organisms[:elite_count]]

        # 轮盘赌选择
        remaining_count = count - elite_count
        if remaining_count > 0:
            total_fitness = sum(fitness_scores)
            if total_fitness > 0:
                probabilities = [f / total_fitness for f in fitness_scores]
                selected.extend(
                    weighted_choices(
                        self.randomness_rng,
                        organisms,
                        probabilities,
                        remaining_count,
                    )
                )

        return selected[:count]

    def _calculate_fitness(self, organism: Organism) -> float:
        """计算适应度

        参数:
            organism: Organism - 生物体

        返回:
            float - 适应度值
        """
        # 基础适应度：能量
        fitness = organism.energy

        # 加上成功动作数
        fitness += organism.successful_actions * 10

        # 加上后代数
        fitness += organism.offspring_count * 50

        # 减去年龄（年龄越大，适应度越低）
        fitness -= organism.age * 0.1

        return max(0.0, fitness)

    def get_status(self) -> Dict[str, Any]:
        """获取选择系统状态。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        return {
            'selection_pressure': self.selection_pressure,
            'elitism_rate': self.elitism_rate
        }
