#!/usr/bin/env python3
"""
测试连接权重功能的脚本

这个脚本创建一个简单的生物体，包含传感器和执行器，
并测试它们之间的信号传递是否能正确处理连接权重。
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, './src')

def test_organism_connect_tools():
    """测试生物体连接工具功能"""
    print("===== 测试生物体连接工具功能 =====")
    
    # 导入所需模块
    from vitalloom.organisms.organism import Organism
    
    # 创建测试生物体
    org = Organism("test_org", (150, 150))
    print(f"创建生物体: {org.id}")
    
    # 添加一些测试组件
    from vitalloom.components.sensors import Sensor
    from vitalloom.components.actuators import Actuator
    
    sensor = Sensor("sensor_1", organism_id=org.id, is_sensor=True)
    actuator = Actuator("actuator_1", organism_id=org.id, is_actuator=True)
    
    org.add_sensor(sensor)
    org.add_actuator(actuator)
    print(f"添加组件: 传感器-{sensor.id}, 执行器-{actuator.id}")
    
    # 测试连接功能
    weight = 0.5
    result = org.connect_tools(sensor.id, actuator.id, weight)
    print(f"\n连接传感器和执行器，权重: {weight}")
    print(f"连接结果: {result}")
    
    # 检查连接列表
    print(f"生物体连接列表: {org.connections}")
    
    # 检查组件连接
    print(f"传感器连接数: {len(sensor.connections)}")
    print(f"执行器连接数: {len(actuator.connections)}")
    
    # 检查连接权重
    if org.connections:
        connection = org.connections[0]
        print(f"连接权重: {connection.get('weight', '未设置')}")
    
    print("\n===== 测试完成 =====")

def test_signal_transmission():
    """测试信号传递功能"""
    print("\n===== 测试信号传递功能 =====")
    
    # 导入所需模块
    from vitalloom.organisms.organism import Organism
    from vitalloom.components.sensors import Sensor
    from vitalloom.components.actuators import Actuator
    
    # 创建测试生物体和组件
    org = Organism("test_org2", (150, 150))
    sensor = Sensor("sensor_2", organism_id=org.id, is_sensor=True)
    actuator = Actuator("actuator_2", organism_id=org.id, is_actuator=True)
    
    org.add_sensor(sensor)
    org.add_actuator(actuator)
    
    # 设置不同权重
    weights = [-1.0, 0.0, 0.5, 1.0, 2.0]
    
    for weight in weights:
        # 重置连接和信号
        org.connections.clear()
        sensor.connections.clear()
        actuator.connections.clear()
        
        # 创建新连接
        org.connect_tools(sensor.id, actuator.id, weight)
        
        # 模拟传感器输出信号
        sensor_output = 2.0
        sensor.output_signal = sensor_output
        
        # 重置执行器输入信号
        actuator.input_signals.clear()
        
        print(f"\n测试权重: {weight}")
        print(f"传感器输出信号: {sensor.output_signal}")
        
        # 手动调用信号传递
        try:
            for conn in sensor.connections:
                if hasattr(conn, 'transmit_signal'):
                    transmitted_value = conn.transmit_signal(sensor.output_signal)
                    if hasattr(conn.target, 'input_signals'):
                        conn.target.input_signals[sensor.id] = transmitted_value
            
            # 检查执行器输入信号
            print(f"执行器输入信号: {actuator.input_signals}")
            input_sum = sum(actuator.input_signals.values()) if actuator.input_signals else 0.0
            print(f"执行器输入信号总和: {input_sum}")
            expected = sensor_output * weight
            print(f"预期输入总和: {expected}")
            print(f"测试结果: {'通过' if abs(input_sum - expected) < 0.001 else '失败'}")
        except Exception as e:
            print(f"测试过程中发生错误: {e}")
    
    print("\n===== 信号传递测试完成 =====")

if __name__ == "__main__":
    test_organism_connect_tools()
    test_signal_transmission()
