"""实体基类 EntityBase：位置/运动学、层级、脚本列表与碰撞查询。

架构数据流::

    Pond/场景加载 → EntityBase 构造 → add_script → update 递归子节点
    draw 使用局部 position（world_position 供未来层级叠加）

历史坑::

    - draw 未使用 world_position，子实体绘制与父级偏移可能不一致
"""
from typing import Optional, Dict, Any, Tuple, List
import numpy as np
import uuid
from core.VitaLoom.core.logger import get_logger


logger = get_logger("EntityBase")


class EntityBase:
    """所有场景实体的统一父类：运动学、层级、脚本与 2D 圆形碰撞。

    生命周期:
        __init__ →（可选）add_child/add_script → update 每帧 → draw
    """

    def __init__(self, entity_id: Optional[str] = None, **kwargs: Any):
        """初始化 id、运动状态、层级与脚本列表。

        职责:
            生成或使用 entity_id；解析 position/velocity/size/color 等 kwargs。

        时机:
            直接构造或由 runtime_entities / 序列化加载创建。

        不变量:
            position/velocity/acceleration 为 float ndarray；active 默认 True。

        排错:
            id 重复 → 上层注册表（pond.organisms）须保证唯一，非本类职责。
        """
        # 唯一标识符
        self.id = entity_id if entity_id else f"{self.__class__.__name__}_{uuid.uuid4().hex[:8]}"

        # 位置和运动属性
        position = kwargs.get('position', (0.0, 0.0))
        self.position = np.array(position, dtype=float) if isinstance(position, (list, tuple)) else position
        self.velocity = np.array(kwargs.get('velocity', (0.0, 0.0)), dtype=float)
        self.acceleration = np.array(kwargs.get('acceleration', (0.0, 0.0)), dtype=float)

        # 尺寸属性
        self.size = float(kwargs.get('size', 10.0))
        self.radius = self.size  # 默认半径等于尺寸

        # 状态属性
        self.active = kwargs.get('active', True)
        self.age = 0
        self.entity_type = kwargs.get('entity_type', self.__class__.__name__)

        # 渲染属性
        self.color = kwargs.get('color', (255, 255, 255))
        self.visible = kwargs.get('visible', True)

        # 层次结构 (Unity-like)
        self.parent: Optional['EntityBase'] = kwargs.get('parent', None)
        self.children: List['EntityBase'] = []
        self.pond: Optional[Any] = kwargs.get('pond', None)
        
        # 脚本/组件列表 (Unity-like)
        self.scripts: List[Any] = []

    def add_child(self, child: 'EntityBase') -> None:
        """添加子实体并设置 child.parent。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if child not in self.children:
            child.parent = self
            self.children.append(child)

    def remove_child(self, child: 'EntityBase') -> None:
        """移除子实体并清空其 parent。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if child in self.children:
            child.parent = None
            self.children.remove(child)

    def add_script(self, script: Any) -> None:
        """附加脚本；若存在 on_attach 则调用。

        职责:
            将脚本注册到 entity.scripts 并触发 on_attach 生命周期。

        排错:
            脚本 start 未跑 → 应通过 on_attach 而非直接 append。
        """
        if script not in self.scripts:
            self.scripts.append(script)
            if hasattr(script, 'on_attach'):
                script.on_attach(self)

    def remove_script(self, script: Any) -> None:
        """移除脚本并调用 on_detach（若存在）。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if script in self.scripts:
            if hasattr(script, 'on_detach'):
                script.on_detach(self)
            self.scripts.remove(script)

    @property
    def world_position(self) -> np.ndarray:
        """世界坐标：有 parent 时 parent.world_position + 局部 position。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if self.parent:
            return self.parent.world_position + self.position
        return self.position

    def update(self, delta_time: float = 1.0) -> None:
        """积分运动学、阻尼、脚本与子节点 update。

        职责:
            v += a*dt；p += v*dt；velocity *= 0.95；acceleration 清零；递归子节点。

        时机:
            Pond.update 对 root_entities 或 organism 内部调用。

        不变量:
            inactive 时早退；age 每帧 +1。

        排错:
            速度发散 → 检查外力是否每帧累加加速度未清零；PacMan 调试日志见 id 含 PacMan。
        """
        if not self.active:
            return

        # 更新速度（速度 = 速度 + 加速度 * 时间）
        self.velocity += self.acceleration * delta_time

        # 更新位置（位置 = 位置 + 速度 * 时间）
        self.position += self.velocity * delta_time

        # 调试打印 (仅针对 PacMan)
        if "PacMan" in self.id and self.age % 20 == 0:
            logger.debug(
                "DEBUG: %s pos=%s vel=%s acc=%s",
                self.id,
                self.position,
                self.velocity,
                self.acceleration,
            )

        # 阻尼（摩擦力），防止速度无休止增加
        self.velocity *= 0.95

        # 重置加速度
        self.acceleration *= 0


        # 更新所有脚本
        for script in self.scripts:
            if hasattr(script, 'update'):
                script.update(delta_time)

        # 递归更新所有子实体
        for child in self.children:
            child.update(delta_time)

        # 增加年龄
        self.age += 1

    def draw(self, surface: Any) -> None:
        """Pygame 画圆并递归子节点 draw（局部坐标）。

        职责:
            在 surface 上绘制本实体圆点并递归绘制可见子实体。

        排错:
            无显示 → ImportError 被吞；visible/active 为 False。
        """
        if not self.visible or not self.active:
            return

        try:
            import pygame
            # 计算绝对位置 (此处简化，假设所有位置都是相对于 Pond 的，但未来可改为相对于父实体)
            pos = self.position.astype(int)
            pygame.draw.circle(surface, self.color, tuple(pos), int(self.radius))
            
            # 递归绘制子实体
            for child in self.children:
                child.draw(surface)
        except ImportError:
            pass

    def check_collision(self, other: 'EntityBase') -> bool:
        """圆形碰撞：距离 < r1+r2。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if not self.active or not other.active:
            return False

        distance = np.linalg.norm(self.position - other.position)
        return distance < (self.radius + other.radius)

    def check_collision_with_point(self, point: Tuple[float, float]) -> bool:
        """点是否在圆内。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if not self.active:
            return False

        point_array = np.array(point, dtype=float)
        distance = np.linalg.norm(self.position - point_array)
        return distance < self.radius

    def get_distance_to(self, other: 'EntityBase') -> float:
        """欧氏距离到另一实体。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        return np.linalg.norm(self.position - other.position)

    def get_distance_to_point(self, point: Tuple[float, float]) -> float:
        """欧氏距离到点。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        point_array = np.array(point, dtype=float)
        return np.linalg.norm(self.position - point_array)

    def apply_force(self, force: np.ndarray) -> None:
        """力累加到 acceleration。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self.acceleration += force

    def set_position(self, position: Tuple[float, float]) -> None:
        """直接设置 position ndarray。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self.position = np.array(position, dtype=float)

    def set_velocity(self, velocity: Tuple[float, float]) -> None:
        """直接设置 velocity ndarray。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self.velocity = np.array(velocity, dtype=float)

    def set_size(self, size: float) -> None:
        """设置 size 并同步 radius。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self.size = float(size)
        self.radius = self.size

    def activate(self) -> None:
        """active = True。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self.active = True

    def deactivate(self) -> None:
        """active = False。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self.active = False

    def get_status(self) -> Dict[str, Any]:
        """返回 id/type/position/velocity/size/active/age 快照。

        
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
            'id': self.id,
            'type': self.entity_type,
            'position': self.position.tolist(),
            'velocity': self.velocity.tolist(),
            'size': self.size,
            'active': self.active,
            'age': self.age
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, pos={self.position}, size={self.size})"
