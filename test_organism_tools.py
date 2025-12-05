#!/usr/bin/env python3
"""
测试脚本：验证生物体传感器和效应器的添加
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_organism.core import Organism
from ai_organism.tools import LightSensor, MuscleActuator, Connection
from ai_organism.tools import Membrane

# 测试1：基本的传感器和效应器添加
print("=== 测试1：基本的传感器和效应器添加 ===")

# 创建生物体
organism = Organism("test_organism", (400, 300))
print(f"初始传感器数量: {len(organism.sensors)}")
print(f"初始效应器数量: {len(organism.actuators)}")

# 调整细胞膜半径，允许更多传感器和效应器
organism.membrane.radius = 100

# 添加传感器
print("\n添加传感器...")
sensor1 = LightSensor("sensor_1", (10, 0))
organism.add_sensor(sensor1)
sensor2 = LightSensor("sensor_2", (0, 10))
organism.add_sensor(sensor2)

# 添加效应器
print("\n添加效应器...")
actuator1 = MuscleActuator("actuator_1", (-10, 0))
organism.add_actuator(actuator1)
actuator2 = MuscleActuator("actuator_2", (0, -10))
organism.add_actuator(actuator2)

print(f"\n最终传感器数量: {len(organism.sensors)}")
print(f"最终效应器数量: {len(organism.actuators)}")
print(f"传感器列表: {[sensor.tool_id for sensor in organism.sensors.values()]}")
print(f"效应器列表: {[actuator.tool_id for actuator in organism.actuators.values()]}")

# 测试2：验证细胞膜is_inside方法
print("\n=== 测试2：验证细胞膜is_inside方法 ===")


# 测试不同位置
positions = [
    (400, 300),  # 中心
    (450, 300),  # 右侧边界
    (490, 300),  # 右侧边界内
    (501, 300),  # 右侧边界外
    (400, 350),  # 下侧边界
    (400, 390),  # 下侧边界内
    (400, 401),  # 下侧边界外
]

for pos in positions:
    is_inside = organism.membrane.is_inside(pos)
    print(f"位置 {pos}: {'内部' if is_inside else '外部'}")

# 测试3：验证连接创建
print("\n=== 测试3：验证连接创建 ===")

print(f"初始连接数量: {len(organism.connections)}")

# 创建连接
if len(organism.sensors) > 0 and len(organism.actuators) > 0:
    sensor = list(organism.sensors.values())[0]
    actuator = list(organism.actuators.values())[0]
    
    connection = Connection(sensor, actuator, 0.8, False)
    organism.connections.append(connection)
    sensor.connections.append(connection)
    
    print(f"\n连接创建成功: {sensor.tool_id} -> {actuator.tool_id}")
    print(f"最终连接数量: {len(organism.connections)}")
    print(f"传感器连接数量: {len(sensor.connections)}")
    print(f"效应器连接数量: {len(actuator.connections)}")

print("\n=== 测试完成 ===")

# 测试4：模拟编辑器中的场景
print("\n=== 测试4：模拟编辑器中的场景 ===")

# 模拟编辑器中的节点
class MockNode:
    def __init__(self, id, x, y, type):
        self.id = id
        self.x = x
        self.y = y
        self.type = type

# 创建模拟节点
organism_node = MockNode("organism_1", 300, 200, "organism")
sensor_node1 = MockNode("sensor_1", 320, 200, "sensor")
sensor_node2 = MockNode("sensor_2", 280, 200, "sensor")
actuator_node1 = MockNode("actuator_1", 300, 220, "actuator")
actuator_node2 = MockNode("actuator_2", 300, 180, "actuator")

nodes = [organism_node, sensor_node1, sensor_node2, actuator_node1, actuator_node2]

# 创建新生物体
organism = Organism(organism_node.id, (400, 300))
organism.membrane.radius = 100

# 模拟apply_to_simulation中的传感器和效应器添加逻辑
for node in nodes:
    if node == organism_node:
        continue  # 跳过生物节点
    
    # 计算相对于生物体中心的位置
    rel_x = node.x - organism_node.x
    rel_y = node.y - organism_node.y
    
    if node.type == "sensor":
        sensor_id = f"sensor_{node.id[-1]}"
        sensor = LightSensor(sensor_id, (rel_x, rel_y))
        organism.add_sensor(sensor)
        print(f"添加传感器: {sensor_id} at ({rel_x}, {rel_y})")
    elif node.type == "actuator":
        actuator_id = f"actuator_{node.id[-1]}"
        actuator = MuscleActuator(actuator_id, (rel_x, rel_y))
        organism.add_actuator(actuator)
        print(f"添加效应器: {actuator_id} at ({rel_x}, {rel_y})")

print(f"\n模拟场景传感器数量: {len(organism.sensors)}")
print(f"模拟场景效应器数量: {len(organism.actuators)}")

print("\n=== 所有测试完成 ===")
