"""PS 莲池漂浮组件：位置、速度、寿命与衰减（序列化见 PondSerializer）。

排错: 见 `builtin/README.md`。
"""

from typing import Dict, List, Any, TYPE_CHECKING
import numpy as np

from core.VitaLoom.core.logger import get_logger

logger = get_logger("FloatingSystem")


def _component_motion_vector(component: Any, attribute: str) -> np.ndarray | None:
    """Return a validated detached component motion vector."""
    try:
        vector = np.asarray(getattr(component, attribute), dtype=float)
    except (AttributeError, TypeError, ValueError):
        return None
    if vector.shape != (2,) or not np.all(np.isfinite(vector)):
        return None
    return vector.copy()


def _set_component_motion_vector(component: Any, attribute: str, vector: np.ndarray) -> None:
    """Use ComponentBase/EntityBase owner APIs with a legacy-double fallback."""
    setter = getattr(component, f"set_{attribute}", None)
    if callable(setter):
        setter(tuple(float(value) for value in vector))
        return
    setattr(component, attribute, vector)


# 使用TYPE_CHECKING避免循环导入
if TYPE_CHECKING:
    from builtin.components.components_base import ComponentBase

class FloatingSystem:
    """漂浮系统 - 管理莲池中漂浮的组件和食物
    
    漂浮系统实现了莲池中漂浮组件和食物的管理，包括：
    1. 组件漂浮：死亡细胞释放的组件在环境中漂浮
    2. 组件碰撞：不同类型组件碰撞可能自动连线
    3. 组件分解：组件随时间分解为食物粒子
    4. 食物重组：食物粒子碰撞可能重组为新组件
    5. 捕获机制：生物体可捕获漂浮的组件
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
        self.floating_components: List[Any] = []  # 漂浮组件列表
        self.food_particles: List[Dict[str, Any]] = []  # 食物粒子列表
        self.energy_particles: List[Dict[str, Any]] = []  # 能量粒子列表
        self._assembly_sequence = 0
        self.world_size: tuple[float, float] = kwargs.get('world_size', (1200, 800))  # 世界大小
        supplied_rng = kwargs.get("randomness_rng")
        self.randomness_owner_mode = "runtime" if supplied_rng is not None else "detached"
        self.randomness_rng = supplied_rng if supplied_rng is not None else np.random.default_rng(12345)
        if self.randomness_rng is None:
            self.randomness_rng = np.random.default_rng(12345)
        if not hasattr(self.randomness_rng, "random"):
            raise TypeError("randomness_rng must expose random()")
        
        # 组件分解参数
        self.component_decay_rate: float = kwargs.get('component_decay_rate', 0.001)  # 组件衰减率
        self.decay_threshold: float = kwargs.get('decay_threshold', 0.1)  # 分解阈值
        
        # 组件自组装参数
        self.assembly_probability: float = kwargs.get('assembly_probability', 0.01)  # 自组装概率
        self.assembly_distance: float = kwargs.get('assembly_distance', 10.0)  # 自组装距离
        
        # 物理参数
        self.gravity: np.ndarray = kwargs.get('gravity', np.array([0.0, 0.0]))  # 重力向量
        self.drag: float = kwargs.get('drag', 0.99)  # 阻力系数
    
    def update(self):
        """更新漂浮系统状态。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 更新漂浮组件
        self.update_floating_components()
        
        # 更新食物粒子
        self.update_food_particles()
        
        # 更新能量粒子
        self.update_energy_particles()
        
        # 检查组件碰撞和自组装
        self.check_component_collisions()
        
        # 检查食物重组
        self.check_food_reassembly()
    
    def update_floating_components(self):
        """更新漂浮组件。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        for component in self.floating_components:
            # 应用漂浮物理
            self.apply_floating_physics(component)
            
            # 组件衰减
            self.decay_component(component)
    
    def update_food_particles(self):
        """更新食物粒子。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        for food in self.food_particles:
            # 应用漂浮物理
            self.apply_floating_physics_to_particle(food)
    
    def update_energy_particles(self):
        """更新能量粒子。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        for energy in self.energy_particles:
            # 应用漂浮物理
            self.apply_floating_physics_to_particle(energy)
    
    def apply_floating_physics(self, component: 'ComponentBase'):
        """应用漂浮物理到组件。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        position = _component_motion_vector(component, "position")
        velocity = _component_motion_vector(component, "velocity")
        try:
            gravity = np.asarray(self.gravity, dtype=float)
        except (TypeError, ValueError):
            return
        if (
            position is None
            or velocity is None
            or gravity.shape != (2,)
            or not np.all(np.isfinite(gravity))
        ):
            return

        velocity += self._normal(2) * 0.1
        velocity += gravity
        velocity *= float(self.drag)
        speed = float(np.linalg.norm(velocity))
        if speed > 2.0:
            velocity = (velocity / speed) * 2.0
        position += velocity

        _set_component_motion_vector(component, "position", position)
        _set_component_motion_vector(component, "velocity", velocity)
        self.handle_boundary(component)
    
    def handle_boundary(self, component: 'ComponentBase'):
        """处理边界。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        position = _component_motion_vector(component, "position")
        velocity = _component_motion_vector(component, "velocity")
        if position is None:
            return
        try:
            width, height = float(self.world_size[0]), float(self.world_size[1])
        except (TypeError, ValueError, IndexError):
            return

        if position[0] < 0:
            position[0] = 0
            if velocity is not None:
                velocity[0] *= -0.5
        elif position[0] > width:
            position[0] = width
            if velocity is not None:
                velocity[0] *= -0.5
        if position[1] < 0:
            position[1] = 0
            if velocity is not None:
                velocity[1] *= -0.5
        elif position[1] > height:
            position[1] = height
            if velocity is not None:
                velocity[1] *= -0.5

        _set_component_motion_vector(component, "position", position)
        if velocity is not None:
            _set_component_motion_vector(component, "velocity", velocity)
    
    def decay_component(self, component: 'ComponentBase'):
        """组件衰减和分解。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 检查组件是否已经有衰减属性
        if not hasattr(component, 'decay_level'):
            component.decay_level = 1.0  # 初始衰减等级
        
        # 组件衰减
        component.decay_level -= self.component_decay_rate
        
        # 检查是否需要分解
        if component.decay_level <= self.decay_threshold:
            self.decompose_component(component)
    
    def decompose_component(self, component: 'ComponentBase'):
        """分解组件为食物粒子。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 创建食物粒子
        food_count = max(1, int(component.decay_level * 10))  # 分解为多个食物粒子
        
        for _ in range(food_count):
            food: Dict[str, Any] = {
                'position': component.position + self._normal(2) * 5,
                'amount': self._uniform(1, 3),
                'type': 'food',
                'id': f"food_{len(self.food_particles)}"
            }
            self.food_particles.append(food)
        
        # 从漂浮组件列表中移除
        if component in self.floating_components:
            self.floating_components.remove(component)
        
        logger.info("组件 %s 分解为 %s 个食物粒子", component.id, food_count)
    
    def replace_floating_components(self, entries: List[Any]) -> None:
        """替换漂浮条目并保持公开 list identity。"""
        if entries is None:
            entries = []
        if not isinstance(entries, list):
            entries = list(entries)
        for entry in entries:
            if not isinstance(entry, dict) or entry.get("component") is None:
                raise TypeError("floating entry must be a dict containing component")
        self.floating_components[:] = entries

    def restore_assembly_sequence(self, sequence: Any = None) -> None:
        """Restore the persisted identity counter without reusing old IDs."""
        try:
            requested = int(sequence) if sequence is not None else 0
        except (TypeError, ValueError):
            requested = 0
        observed = 0
        for entry in self.floating_components:
            component = entry.get("component") if isinstance(entry, dict) else None
            identifier = str(getattr(component, "id", ""))
            if identifier.startswith("assembled_"):
                try:
                    observed = max(observed, int(identifier.rsplit("_", 1)[1]))
                except (TypeError, ValueError):
                    continue
        self._assembly_sequence = max(0, requested, observed)

    def add_floating_component(self, component: 'ComponentBase'):
        """添加漂浮组件。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 初始化组件的漂浮属性；ComponentBase 已有 owner API，旧 double 保留回退。
        if not hasattr(component, 'velocity'):
            _set_component_motion_vector(component, "velocity", self._normal(2) * 2)
        if not hasattr(component, 'acceleration'):
            _set_component_motion_vector(component, "acceleration", np.zeros(2, dtype=float))
        
        # 设置组件为漂浮状态
        component.floating = True
        
        # 添加到漂浮组件列表
        self.floating_components.append(component)
        
        logger.info("添加漂浮组件: %s, 类型: %s", component.id, component.type)
    
    def remove_floating_component(self, component: 'ComponentBase'):
        """移除漂浮组件。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if component in self.floating_components:
            self.floating_components.remove(component)
            component.floating = False
    
    def check_component_collisions(self):
        """检查组件碰撞和自组装。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        for i in range(len(self.floating_components)):
            for j in range(i + 1, len(self.floating_components)):
                component1 = self.floating_components[i]
                component2 = self.floating_components[j]
                
                # 计算距离
                distance = np.linalg.norm(component1.position - component2.position)
                
                if distance < self.assembly_distance:
                    # 检查是否可以自组装
                    if self.can_assemble(component1, component2):
                        # 尝试自组装
                        if self._random() < self.assembly_probability:
                            self.assemble_components(component1, component2)
    
    def can_assemble(self, component1: 'ComponentBase', component2: 'ComponentBase') -> bool:
        """检查组件是否可以自组装。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 简单的自组装规则：传感器和执行器可以组装
        component1_type = component1.type
        component2_type = component2.type
        
        # 传感器 + 执行器 → 简单反射弧
        if (('sensor' in component1_type and 'actuator' in component2_type) or 
           ('actuator' in component1_type and 'sensor' in component2_type)):
            return True
        
        # 传感器 + 传感器 → 复合感知系统
        if 'sensor' in component1_type and 'sensor' in component2_type:
            return True
        
        # 执行器 + 执行器 → 协同运动系统
        if 'actuator' in component1_type and 'actuator' in component2_type:
            return True
        
        return False
    
    def assemble_components(self, component1: 'ComponentBase', component2: 'ComponentBase'):
        """自组装组件。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        logger.info("组件自组装: %s + %s", component1.type, component2.type)
        
        # 实际项目中需要实现组件连接逻辑
        # 这里简化处理，只是移除两个组件，创建一个新组件
        
        # 从漂浮列表中移除
        self.remove_floating_component(component1)
        self.remove_floating_component(component2)
        
        # 创建新的复合组件（默认 Hybrid）
        try:
            from builtin.components.hybrid import HybridComponent

            p1 = np.asarray(component1.position, dtype=float)
            p2 = np.asarray(component2.position, dtype=float)
            mid = (p1 + p2) / 2.0
            self._assembly_sequence += 1
            new_id = f"assembled_{self._assembly_sequence}"
            hybrid = HybridComponent(
                component_id=new_id,
                position=mid,
                component_type="hybrid_assembled",
                mode="sensor",
            )
            self.add_floating_component(hybrid)
        except Exception as exc:
            logger.warning("自组装创建 HybridComponent 失败: %s", exc)
    
    def check_food_reassembly(self):
        """检查食物重组：近距离粒子概率合并。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if len(self.food_particles) < 2:
            return
        merge_dist = max(float(self.assembly_distance) * 1.5, 8.0)
        prob = min(float(self.assembly_probability) * 3.0, 0.15)
        i = 0
        while i < len(self.food_particles):
            fi = self.food_particles[i]
            j = i + 1
            while j < len(self.food_particles):
                fj = self.food_particles[j]
                pi = fi.get("position")
                pj = fj.get("position")
                if pi is None or pj is None:
                    j += 1
                    continue
                pi = np.asarray(pi, dtype=float)
                pj = np.asarray(pj, dtype=float)
                if np.linalg.norm(pi - pj) < merge_dist and self._random() < prob:
                    fi["amount"] = float(fi.get("amount", 1.0)) + float(fj.get("amount", 1.0))
                    fi["position"] = (pi + pj) / 2.0
                    self.food_particles.pop(j)
                    continue
                j += 1
            i += 1
    
    def apply_floating_physics_to_particle(self, particle: Dict[str, Any]):
        """应用漂浮物理到粒子。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 确保位置是numpy数组
        if not isinstance(particle['position'], np.ndarray):
            particle['position'] = np.array(particle['position'], dtype=float)
        
        # 添加随机扰动
        particle['position'] += self._normal(2) * 0.1

    def _random(self) -> float:
        if self.randomness_rng is None:
            raise RuntimeError("FloatingSystem randomness owner is unavailable")
        return float(self.randomness_rng.random())

    def _normal(self, size: int) -> np.ndarray:
        if self.randomness_rng is None:
            raise RuntimeError("FloatingSystem randomness owner is unavailable")
        return np.asarray(self.randomness_rng.normal(size=size), dtype=float)

    def _uniform(self, low: float, high: float) -> float:
        if self.randomness_rng is None:
            raise RuntimeError("FloatingSystem randomness owner is unavailable")
        return float(self.randomness_rng.uniform(low, high))
        
        # 边界处理
        if particle['position'][0] < 0:
            particle['position'][0] = 0
        elif particle['position'][0] > self.world_size[0]:
            particle['position'][0] = self.world_size[0]
        
        if particle['position'][1] < 0:
            particle['position'][1] = 0
        elif particle['position'][1] > self.world_size[1]:
            particle['position'][1] = self.world_size[1]
    
    def get_nearby_components(self, position: np.ndarray, radius: float) -> List['ComponentBase']:
        """获取附近漂浮组件。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        nearby: List['ComponentBase'] = []
        for component in self.floating_components:
            distance = np.linalg.norm(component.position - position)
            if distance <= radius:
                nearby.append(component)
        
        return nearby
    
    def get_nearby_food(self, position: np.ndarray, radius: float) -> List[Dict[str, Any]]:
        """获取附近食物粒子。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        nearby: List[Dict[str, Any]] = []
        for food in self.food_particles:
            distance = np.linalg.norm(food['position'] - position)
            if distance <= radius:
                nearby.append(food)
        
        return nearby
    
    def get_nearby_energy(self, position: np.ndarray, radius: float) -> List[Dict[str, Any]]:
        """获取附近能量粒子。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        nearby: List[Dict[str, Any]] = []
        for energy in self.energy_particles:
            distance = np.linalg.norm(energy['position'] - position)
            if distance <= radius:
                nearby.append(energy)
        
        return nearby
    
    def get_floating_system_status(self) -> Dict[str, Any]:
        """获取漂浮系统状态。

        
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
            'floating_components': len(self.floating_components),
            'food_particles': len(self.food_particles),
            'energy_particles': len(self.energy_particles),
            'component_decay_rate': self.component_decay_rate,
            'assembly_probability': self.assembly_probability
        }
