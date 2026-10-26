"""PS 简易物理积分：实体速度/位置更新（演示级，非完整刚体）。

排错: 见 `builtin/README.md`。
"""

from typing import Dict, Any
import numpy as np


def _motion_vector(subject: Any, attribute: str) -> np.ndarray | None:
    """Return a validated detached motion vector without exposing owner state."""
    try:
        vector = np.asarray(getattr(subject, attribute), dtype=float)
    except (AttributeError, TypeError, ValueError):
        return None
    if vector.shape != (2,) or not np.all(np.isfinite(vector)):
        return None
    return vector.copy()


def _set_motion_vector(subject: Any, attribute: str, vector: np.ndarray) -> None:
    """Write simulation output through owner APIs, retaining legacy-double fallback."""
    setter = getattr(subject, f"set_{attribute}", None)
    if callable(setter):
        setter(tuple(float(value) for value in vector))
        return
    setattr(subject, attribute, vector)


class PhysicsEngine:
    """物理引擎 - 负责管理环境中的物理规则
    
    物理引擎实现了环境中的物理规则，包括：
    1. 碰撞检测
    2. 力的计算和应用
    3. 运动模拟
    4. 物理约束
    """
    
    def __init__(self, **kwargs: Any):
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
        self.gravity = kwargs.get('gravity', np.array([0.0, 0.0]))  # 重力向量
        self.drag = kwargs.get('drag', 0.99)  # 阻力系数
        self.collision_damping = kwargs.get('collision_damping', 0.8)  # 碰撞阻尼
        self.world_size = kwargs.get('world_size', (1200, 800))  # 世界大小
        
        # 碰撞检测精度
        self.collision_precision = kwargs.get('collision_precision', 1.0)
        self._targets: list = []
    
    def update(self):
        """更新物理引擎状态：对已注册物体调用 update_motion。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        for obj in list(getattr(self, "_targets", []) or []):
            try:
                self.update_motion(obj)
            except Exception:
                continue
    
    def apply_force(self, obj: Any, force: np.ndarray):
        """应用力到物体。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        acceleration = _motion_vector(obj, "acceleration")
        if acceleration is None:
            return
        try:
            normalized_force = np.asarray(force, dtype=float)
        except (TypeError, ValueError):
            return
        if normalized_force.shape != (2,) or not np.all(np.isfinite(normalized_force)):
            return
        _set_motion_vector(obj, "acceleration", acceleration + normalized_force)
    
    def update_motion(self, obj: Any):
        """更新物体运动。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        position = _motion_vector(obj, "position")
        velocity = _motion_vector(obj, "velocity")
        acceleration = _motion_vector(obj, "acceleration")
        try:
            gravity = np.asarray(self.gravity, dtype=float)
        except (TypeError, ValueError):
            return
        if (
            position is None
            or velocity is None
            or acceleration is None
            or gravity.shape != (2,)
            or not np.all(np.isfinite(gravity))
        ):
            return

        acceleration += gravity
        velocity += acceleration
        velocity *= float(self.drag)
        speed = float(np.linalg.norm(velocity))
        if speed > 10.0:
            velocity = (velocity / speed) * 10.0
        position += velocity

        _set_motion_vector(obj, "position", position)
        _set_motion_vector(obj, "velocity", velocity)
        _set_motion_vector(obj, "acceleration", np.zeros(2, dtype=float))
        self.handle_boundary_collision(obj)

    def register_body(self, obj) -> None:
        """注册参与积分的物体。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if obj not in self._targets:
            self._targets.append(obj)

    def unregister_body(self, obj) -> None:
        """PhysicsEngine.unregister_body。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if obj in self._targets:
            self._targets.remove(obj)

    def handle_boundary_collision(self, obj: Any):
        """处理边界碰撞。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        position = _motion_vector(obj, "position")
        velocity = _motion_vector(obj, "velocity")
        if position is None or velocity is None:
            return
        try:
            width, height = float(self.world_size[0]), float(self.world_size[1])
        except (TypeError, ValueError, IndexError):
            return

        if position[0] < 0:
            position[0] = 0
            velocity[0] *= -self.collision_damping
        elif position[0] > width:
            position[0] = width
            velocity[0] *= -self.collision_damping
        if position[1] < 0:
            position[1] = 0
            velocity[1] *= -self.collision_damping
        elif position[1] > height:
            position[1] = height
            velocity[1] *= -self.collision_damping

        _set_motion_vector(obj, "position", position)
        _set_motion_vector(obj, "velocity", velocity)
    
    def check_collision(self, obj1: Any, obj2: Any) -> bool:
        """检查两个物体是否碰撞。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 简化的碰撞检测：圆形碰撞。读取 detached snapshot，避免依赖可变 owner state。
        position1 = _motion_vector(obj1, "position")
        position2 = _motion_vector(obj2, "position")
        if position1 is None or position2 is None:
            return False
        distance = float(np.linalg.norm(position1 - position2))
        radius1 = getattr(obj1.membrane, 'radius', 30) if hasattr(obj1, 'membrane') else 30
        radius2 = getattr(obj2.membrane, 'radius', 30) if hasattr(obj2, 'membrane') else 30
        return bool(distance < radius1 + radius2)
    
    def resolve_collision(self, obj1: Any, obj2: Any):
        """解决碰撞。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if not self.check_collision(obj1, obj2):
            return
        
        # 先在 detached snapshots 上计算，确认完整输入后再通过 owner API 写回。
        position1 = _motion_vector(obj1, "position")
        position2 = _motion_vector(obj2, "position")
        if position1 is None or position2 is None:
            return
        collision_vector = position2 - position1
        distance = float(np.linalg.norm(collision_vector))
        if distance == 0:
            collision_normal = np.array([1.0, 0.0])
        else:
            collision_normal = collision_vector / distance

        radius1 = getattr(obj1.membrane, 'radius', 30) if hasattr(obj1, 'membrane') else 30
        radius2 = getattr(obj2.membrane, 'radius', 30) if hasattr(obj2, 'membrane') else 30
        overlap = radius1 + radius2 - distance
        separation = collision_normal * (overlap * 0.5)
        _set_motion_vector(obj1, "position", position1 - separation)
        _set_motion_vector(obj2, "position", position2 + separation)

        velocity1 = _motion_vector(obj1, "velocity")
        velocity2 = _motion_vector(obj2, "velocity")
        if velocity1 is None or velocity2 is None:
            return
        relative_velocity = velocity2 - velocity1
        velocity_along_normal = float(np.dot(relative_velocity, collision_normal))

        # 如果物体正在分离，不处理冲量。
        if velocity_along_normal > 0:
            return

        restitution = self.collision_damping
        impulse_scalar = -(1 + restitution) * velocity_along_normal
        impulse = impulse_scalar * collision_normal
        _set_motion_vector(obj1, "velocity", velocity1 - impulse * 0.5)
        _set_motion_vector(obj2, "velocity", velocity2 + impulse * 0.5)
    
    def check_point_collision(self, point: np.ndarray, obj: Any) -> bool:
        """检查点与物体是否碰撞。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if hasattr(obj, 'position'):
            distance = float(np.linalg.norm(point - obj.position))
            radius = getattr(obj.membrane, 'radius', 30) if hasattr(obj, 'membrane') else 30
            return bool(distance < radius)
        
        return False
    
    def get_distance(self, obj1: Any, obj2: Any) -> float:
        """获取两个物体之间的距离。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if hasattr(obj1, 'position') and hasattr(obj2, 'position'):
            return float(np.linalg.norm(obj1.position - obj2.position))
        return float('inf')
    
    def get_physics_status(self) -> Dict[str, Any]:
        """获取物理引擎状态。

        
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
            'gravity': self.gravity.tolist(),
            'drag': self.drag,
            'collision_damping': self.collision_damping,
            'world_size': self.world_size,
            'collision_precision': self.collision_precision
        }
