# -*- coding: utf-8 -*-
"""示例项目：吃豆豆莲池（PS Simulation 路径，非 SR scene runtime）。

职责: 组装 IntelligentOrganism + 传感器/效应器/膜，驱动 builtin Simulation。
时机: 独立脚本入口 `python examples/ps_pacman_demo.py`；与 `.pond` SR 播放无关。
排错: 与 SR 混淆 → 本文件不走 GameViewport scene_runtime_entities。
"""

import random
import numpy as np

from builtin.systems.simulation import Simulation
from builtin.entity_types.intelligent_organism import IntelligentOrganism
from builtin.components.sensors import TouchSensor
from builtin.components.actuators import MuscleActuator, CiliaActuator
from builtin.components.membrane import Membrane

class PacManPond(Simulation):
    """吃豆豆模拟场景"""
    
    def __init__(self, food_count=60):
        super().__init__()
        self.food_count = food_count
        self.name = "Pac-Man World"
        self.setup_pacman_environment()
        
    def setup_pacman_environment(self):
        """设置环境与生物体"""
        self.environment.foods = []
        self.organisms = []
        
        # 创建吃豆人 (Pac-Man)
        self.pacman = IntelligentOrganism(
            organism_id="PacMan_Alpha",
            position=np.array([600.0, 400.0]),
            name="Pac-Man",
            energy=150.0
        )
        
        # 安装器官 
        # 细胞膜 - 吃豆器官，半径大一点更容易吃到
        membrane = Membrane(
            component_id="membrane_01",
            organism_id="PacMan_Alpha",
            position=(0,0),
            radius=150.0, # 增大感知半径
            ingest_threshold=1.0
        )
        self.pacman.add_component(membrane)
        
        # 推进器 (大幅减小推力，让它慢下来吃)
        muscle = MuscleActuator(
            component_id="engine",
            organism_id="PacMan_Alpha",
            position=(0,0),
            max_force=2.0
        )
        self.pacman.add_component(muscle)
        
        # 转向器
        cilia = CiliaActuator(
            component_id="rudder",
            organism_id="PacMan_Alpha",
            position=(0,0),
            max_torque=1.0
        )
        self.pacman.add_component(cilia)
        
        self.organisms.append(self.pacman)
        
        # 散布大量豆豆，集中在中心区域
        for _ in range(self.food_count):
            pos = (random.randint(500, 700), random.randint(350, 450)) # 更密集的中心集群
            self.environment.add_food(pos, energy=50.0)
            
        # 在出发点前方放几个必经之豆
        for target_x in range(620, 800, 30):
            self.environment.add_food((target_x, 400), energy=100.0)

            
        print(f"✅ {self.name} 已准备就绪！")

    def run_demo(self, steps=300):
        """运行模拟并实时显示"""
        print(f"\n--- 正在运行: {self.name} ({steps}步) ---")
        for i in range(steps):
            # 获取执行器并给信号
            for org in self.organisms:
                engine = org.get_component("engine")
                rudder = org.get_component("rudder")
                
                if engine: engine.process_signal(0.4) # 持续前进
                if rudder: rudder.process_signal(random.uniform(-0.05, 0.05)) # 随机微调方向
                
                # 简易边界反弹逻辑
                if org.position[0] < 100: 
                    org.velocity[0] = abs(org.velocity[0]) + 1.0
                elif org.position[0] > 1100:
                    org.velocity[0] = -abs(org.velocity[0]) - 1.0
                    
                if org.position[1] < 100:
                    org.velocity[1] = abs(org.velocity[1]) + 1.0
                elif org.position[1] > 700:
                    org.velocity[1] = -abs(org.velocity[1]) - 1.0
            
            self.update()
            
            if i % 20 == 0:
                print(f"步数 {i:03}: 生物数={len(self.organisms)}, 剩余豆豆={len(self.environment.foods):2d}, "
                      f"能量={self.pacman.energy:5.1f}, 位置={self.pacman.position.astype(int)}")

                
        print(f"--- 模拟完成 ---")

if __name__ == "__main__":
    world = PacManPond(food_count=100)
    world.run_demo(300)
