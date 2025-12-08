"""物理引擎实现"""

from typing import Dict, Any
import numpy as np

class PhysicsEngine:
    """物理引擎 - 负责管理环境中的物理规则
    
    物理引擎实现了环境中的物理规则，包括：
    1. 碰撞检测
    2. 力的计算和应用
    3. 运动模拟
    4. 物理约束
    """
    
    def __init__(self, **kwargs: Any):
        """初始化物理引擎
        
        参数:
            kwargs: 其他参数
        """
        self.gravity = kwargs.get('gravity', np.array([0.0, 0.0]))  # 重力向量
        self.drag = kwargs.get('drag', 0.99)  # 阻力系数
        self.collision_damping = kwargs.get('collision_damping', 0.8)  # 碰撞阻尼
        self.world_size = kwargs.get('world_size', (1200, 800))  # 世界大小
        
        # 碰撞检测精度
        self.collision_precision = kwargs.get('collision_precision', 1.0)
    
    def update(self):
        """更新物理引擎状态"""
        # 物理引擎更新逻辑
        pass
    
    def apply_force(self, obj: Any, force: np.ndarray):
        """应用力到物体
        
        参数:
            obj - 物体实例
            force: np.ndarray - 力向量
        """
        if hasattr(obj, 'acceleration'):
            obj.acceleration += force
    
    def update_motion(self, obj: Any):
        """更新物体运动
        
        参数:
            obj - 物体实例
        """
        if hasattr(obj, 'position') and hasattr(obj, 'velocity') and hasattr(obj, 'acceleration'):
            # 应用重力
            obj.acceleration += self.gravity
            
            # 更新速度
            obj.velocity += obj.acceleration
            
            # 应用阻力
            obj.velocity *= self.drag
            
            # 限制最大速度
            max_speed = 10.0
            speed = float(np.linalg.norm(obj.velocity))
            if speed > max_speed:
                obj.velocity = (obj.velocity / speed) * max_speed
            
            # 更新位置
            obj.position += obj.velocity
            
            # 边界碰撞检测和处理
            self.handle_boundary_collision(obj)
            
            # 重置加速度
            obj.acceleration *= 0
    
    def handle_boundary_collision(self, obj: Any):
        """处理边界碰撞
        
        参数:
            obj - 物体实例
        """
        # 检查x边界
        if obj.position[0] < 0:
            obj.position[0] = 0
            obj.velocity[0] *= -self.collision_damping
        elif obj.position[0] > self.world_size[0]:
            obj.position[0] = self.world_size[0]
            obj.velocity[0] *= -self.collision_damping
        
        # 检查y边界
        if obj.position[1] < 0:
            obj.position[1] = 0
            obj.velocity[1] *= -self.collision_damping
        elif obj.position[1] > self.world_size[1]:
            obj.position[1] = self.world_size[1]
            obj.velocity[1] *= -self.collision_damping
    
    def check_collision(self, obj1: Any, obj2: Any) -> bool:
        """检查两个物体是否碰撞
        
        参数:
            obj1 - 物体1
            obj2 - 物体2
        
        返回:
            bool - 是否碰撞
        """
        # 简化的碰撞检测：圆形碰撞
        if hasattr(obj1, 'position') and hasattr(obj2, 'position'):
            distance = float(np.linalg.norm(obj1.position - obj2.position))
            radius1 = getattr(obj1.membrane, 'radius', 30) if hasattr(obj1, 'membrane') else 30
            radius2 = getattr(obj2.membrane, 'radius', 30) if hasattr(obj2, 'membrane') else 30
            
            return bool(distance < radius1 + radius2)
        
        return False
    
    def resolve_collision(self, obj1: Any, obj2: Any):
        """解决碰撞
        
        参数:
            obj1 - 物体1
            obj2 - 物体2
        """
        if not self.check_collision(obj1, obj2):
            return
        
        # 计算碰撞法线
        if hasattr(obj1, 'position') and hasattr(obj2, 'position'):
            collision_vector = obj2.position - obj1.position
            distance = float(np.linalg.norm(collision_vector))
            if distance == 0:
                collision_normal = np.array([1.0, 0.0])
            else:
                collision_normal = collision_vector / distance
            
            # 分离物体
            radius1 = getattr(obj1.membrane, 'radius', 30) if hasattr(obj1, 'membrane') else 30
            radius2 = getattr(obj2.membrane, 'radius', 30) if hasattr(obj2, 'membrane') else 30
            overlap = radius1 + radius2 - distance
            separation = collision_normal * (overlap * 0.5)
            
            if hasattr(obj1, 'position'):
                obj1.position -= separation
            if hasattr(obj2, 'position'):
                obj2.position += separation
            
            # 计算碰撞后的速度变化
            if hasattr(obj1, 'velocity') and hasattr(obj2, 'velocity'):
                relative_velocity = obj2.velocity - obj1.velocity
                velocity_along_normal = float(np.dot(relative_velocity, collision_normal))
                
                # 如果物体正在分离，不处理
                if velocity_along_normal > 0:
                    return
                
                # 计算冲量标量
                restitution = self.collision_damping
                impulse_scalar = -(1 + restitution) * velocity_along_normal
                impulse = impulse_scalar * collision_normal
                
                # 应用冲量
                obj1.velocity -= impulse * 0.5
                obj2.velocity += impulse * 0.5
    
    def check_point_collision(self, point: np.ndarray, obj: Any) -> bool:
        """检查点与物体是否碰撞
        
        参数:
            point: np.ndarray - 点坐标
            obj - 物体实例
        
        返回:
            bool - 是否碰撞
        """
        if hasattr(obj, 'position'):
            distance = float(np.linalg.norm(point - obj.position))
            radius = getattr(obj.membrane, 'radius', 30) if hasattr(obj, 'membrane') else 30
            return bool(distance < radius)
        
        return False
    
    def get_distance(self, obj1: Any, obj2: Any) -> float:
        """获取两个物体之间的距离
        
        参数:
            obj1 - 物体1
            obj2 - 物体2
        
        返回:
            float - 距离
        """
        if hasattr(obj1, 'position') and hasattr(obj2, 'position'):
            return float(np.linalg.norm(obj1.position - obj2.position))
        return float('inf')
    
    def get_physics_status(self) -> Dict[str, Any]:
        """获取物理引擎状态
        
        返回:
            Dict[str, Any] - 状态信息
        """
        return {
            'gravity': self.gravity.tolist(),
            'drag': self.drag,
            'collision_damping': self.collision_damping,
            'world_size': self.world_size,
            'collision_precision': self.collision_precision
        }
