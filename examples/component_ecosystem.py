"""组件生态系统演示

展示莲池宇宙中的组件漂浮、捕获和自组装机制
"""

import sys
import os

# 将src目录添加到Python路径
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src')
sys.path.insert(0, src_path)

from lotucosm.environment.lotus_pond import LotusPond
from vitalloom.components.sensors import Sensor
from vitalloom.components.actuators import Actuator
from vitalloom.components.hybrid import HybridComponent
import numpy as np


def main():
    """主函数"""
    print("=" * 60)
    print("🔧 组件生态系统演示")
    print("=" * 60)
    
    # 创建莲池环境
    pond = LotusPond(
        name="组件生态系统演示",
        size=(1200, 800),
        initial_organisms=2,
        max_population=10
    )
    
    print(f"✅ 莲池创建成功: {getattr(pond, 'name', '未命名')}")
    print(f"📊 初始生物体数量: {len(pond.organisms)}")
    
    # 手动添加一些漂浮组件
    add_floating_components(pond)
    
    print(f"🔄 组件漂浮系统中当前有 {len(pond.floating_components)} 个组件")
    
    # 运行模拟
    print("\n🔄 开始组件生态系统模拟...")
    print("💡 提示: 模拟将运行100步，每10步显示一次状态")
    
    for i in range(100):
        pond.update()
        
        if i % 10 == 0:
            print(f"\n⏱️  迭代 {i}:")
            print(f"   🧬 生物体数量: {len(pond.organisms)}")
            print(f"   🔧 漂浮组件数量: {len(pond.floating_components)}")
            print(f"   📊 统计信息: {getattr(pond, 'statistics', {})}")
    
    print(f"\n✅ 组件生态系统演示完成！")
    print(f"📊 最终生物体数量: {len(pond.organisms)}")
    print(f"🔧 最终漂浮组件数量: {len(pond.floating_components)}")
    print(f"📈 统计信息: {getattr(pond, 'statistics', {})}")
    
    return True


def add_floating_components(pond: LotusPond):
    """添加漂浮组件到莲池
    
    参数:
        pond: LotusPond - 莲池实例
    """
    import random
    
    # 组件类型列表
    component_types = ["sensor", "actuator", "hybrid"]
    
    # 添加10个随机漂浮组件
    for i in range(10):
        # 随机选择组件类型
        component_type = random.choice(component_types)
        
        # 随机位置
        position = (random.randint(100, 1100), random.randint(100, 700))
        
        # 创建组件
        if component_type == "sensor":
            component = Sensor(
                component_id=f"sensor_{i}",
                organism_id="floating"
            )
        elif component_type == "actuator":
            component = Actuator(
                component_id=f"actuator_{i}",
                organism_id="floating"
            )
        else:  # hybrid
            component = HybridComponent(
                component_id=f"hybrid_{i}",
                organism_id="floating"
            )
        
        # 添加到漂浮系统
        component.position = np.array(position)
        pond.add_floating_component(component)


if __name__ == "__main__":
    main()