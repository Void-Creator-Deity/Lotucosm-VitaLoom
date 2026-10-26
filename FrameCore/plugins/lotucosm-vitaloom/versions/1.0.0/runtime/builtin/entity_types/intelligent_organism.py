# -*- coding: utf-8 -*-
"""PS 智能生命体：带扩展学习/记忆行为的 Organism 子类。

排错: 见 `builtin/README.md`。
"""

from builtin.entity_types.organism import Organism
from typing import Dict, Any


class IntelligentOrganism(Organism):
    """智能生命体 - 可以学习和进化"""
    
    def __init__(self, organism_id: str, position: list, **kwargs):
        """IntelligentOrganism.__init__。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        super().__init__(organism_id, position, **kwargs)
        self.entity_type = "intelligent_organism"
        self.learning_rate = kwargs.get("learning_rate", 0.01)
        # 运行时学习缓冲（键值经验）；代际遗传请使用基类 memory_genes + InheritanceSystem / 莲池编排器，勿与此 dict 混为一谈。
        self.memory: Dict[str, Any] = {}
    
    def learn(self, experience: Dict[str, Any]):
        """学习经验。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if not isinstance(experience, dict):
            return

        key = experience.get("key")
        if not key:
            # 回退：用经验内容生成可重复键
            key = str(sorted(experience.items()))

        value = experience.get("value", experience)
        current = self.memory.get(key)

        if isinstance(current, (int, float)) and isinstance(value, (int, float)):
            # 数值型经验做指数滑动平均，避免剧烈抖动
            alpha = max(0.0, min(1.0, self.learning_rate))
            self.memory[key] = current * (1.0 - alpha) + value * alpha
        else:
            # 非数值型直接覆盖
            self.memory[key] = value
    
    def to_dict(self) -> dict:
        """序列化为字典。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        data = super().to_dict()
        data.update({
            "learning_rate": self.learning_rate,
            "memory": self.memory
        })
        return data
