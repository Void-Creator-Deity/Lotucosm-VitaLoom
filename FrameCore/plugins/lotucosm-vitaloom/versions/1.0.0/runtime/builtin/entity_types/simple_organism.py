"""PS 简单生命体：无额外学习分支的 Organism 子类。

排错: 见 `builtin/README.md`。
"""

from typing import Any, Dict, List, Tuple

from builtin.entity_types.organism import Organism


class SimpleOrganism(Organism):
    """简单生命体 - 仅包含基础生存逻辑"""

    def __init__(self, organism_id: str, position: Tuple[float, float], **kwargs):
        """SimpleOrganism.__init__。

        
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
        self.entity_type = "simple_organism"
        self.behavior_mode = kwargs.get("behavior_mode", "wander")
        self.traits: List[str] = list(kwargs.get("traits", []))

    def decide(self, environment: Any = None) -> Dict[str, Any]:
        """生成一个轻量决策结果，供外层系统按需消费。

        
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
            "mode": self.behavior_mode,
            "energy": self.energy,
            "position": tuple(self.position) if hasattr(self, "position") else (0.0, 0.0),
            "has_environment": environment is not None,
        }

    def to_dict(self) -> Dict[str, Any]:
        """SimpleOrganism.to_dict。

        
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
        data.update(
            {
                "behavior_mode": self.behavior_mode,
                "traits": list(self.traits),
            }
        )
        return data
