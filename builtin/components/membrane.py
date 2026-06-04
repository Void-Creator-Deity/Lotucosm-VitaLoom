"""PS 细胞膜：物理边界与半径内自动吞噬（非 SR 趋食路径）。

架构数据流（PS 莲池 tick）::

    Organism.update → Membrane.auto_ingest → Environment.get_nearby_food

SR 边界::

    主世界趋食经 `nutrient_gradient_at` + chemo 信号边 + PvaecScript，**不**经本模块 GPS/直连食物。
    SR 膜拓扑见 `core/Lotucosm/sr_membrane_topology.py`。

排错: 见 `builtin/README.md`（膜不吞噬 / SR 与 PS 混谈）。
"""
from typing import Optional, Tuple, Any, List, Dict
import numpy as np
from builtin.components.components_base import ComponentBase
from core.VitaLoom.core.logger import get_logger

logger = get_logger("Membrane")


class Membrane(ComponentBase):
    """PS 细胞膜：附着于 Organism，负责边界判定与局部吞噬。"""

    def __init__(self, component_id: Optional[str] = None, **kwargs):
        """Membrane.__init__。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 确保不会向父类传递两次 component_type
        kwargs.setdefault('component_type', 'membrane')
        super().__init__(component_id=component_id, **kwargs)
        
        self.register_property('radius', kwargs.get('radius', 50.0), float, min=10.0, max=200.0)
        self.register_property('ingest_threshold', kwargs.get('ingest_threshold', 0.4), float, min=0.1, max=1.0)
        self.register_property('efficiency', kwargs.get('efficiency', 1.0), float, min=0.1, max=2.0)

    def is_inside(self, point: np.ndarray) -> bool:
        """检查点是否在细胞膜内。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 计算相对于细胞膜中心的距离
        dist = np.linalg.norm(point - self.position)
        return dist <= self.radius

    def auto_ingest(self, environment: Any) -> float:
        """半径内查询食物并吞噬（PS 专用，非 SR chemo 导航）。

        职责: 以 `world_position` 与 `radius` 调用 `environment.get_nearby_food`，
            对足够小的食物调用 `consume()`，按 `efficiency` 累加能量。
        时机: PS 莲池/生物体 update 链中由宿主调用；SR 运行时不用本方法趋食。
        不变量: 环境须实现 `get_nearby_food`；吞噬阈值与 `ingest_threshold`、`radius` 绑定。
        排错: 始终为 0 → 查 Environment 实现与食物尺寸；勿与 SR 梯度趋化混淆（见 README）。
        """
        if not hasattr(environment, 'get_nearby_food'):
            return 0.0

        # 获取生物体的位置（使用 world_position 处理相对于宿主的偏移）
        pos = self.world_position
        r = self.radius
        logger.debug("Membrane %s auto_ingest get_nearby_food at %s radius %s", self.id, pos, r)
        nearby_food = environment.get_nearby_food(pos, r)

        total_energy = 0.0

        
        for food in nearby_food:
            # 只有比细胞膜小很多的物体才能被吞噬
            if food.energy < self.radius * self.ingest_threshold * 10:
                energy_gain = food.consume()
                total_energy += energy_gain * self.efficiency
                
        return total_energy

    def update(self, delta_time: float = 1.0):
        """更新细胞膜状态。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        super().update(delta_time)

    def get_status(self) -> Dict[str, Any]:
        """获取状态。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        status = super().get_status()
        status.update({
            'radius': self.radius,
            'ingest_threshold': self.ingest_threshold,
            'efficiency': self.efficiency
        })
        return status
