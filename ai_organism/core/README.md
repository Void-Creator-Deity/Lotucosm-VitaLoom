# Core模块 - AI生命体核心实现

## 1. 模块概述

Core模块是AI生命体模拟系统的核心组件，实现了AI生命体的基本属性和行为，包括：

- 生命体的核心结构和功能
- 记忆基因和遗传机制
- 事件系统

## 2. 核心类说明

### 2.1 Organism类

**功能**：AI生命体的核心类，包含Tool系统和记忆继承机制

**主要属性**：
- `id`: 生命体唯一标识符
- `position`: 位置坐标
- `velocity`: 速度向量
- `energy`: 能量值
- `age`: 年龄
- `generation`: 代数
- `membrane`: 细胞膜
- `sensors`: 传感器集合
- `actuators`: 执行器集合
- `central_managers`: 中枢管理器集合
- `connections`: 连接列表
- `inherited_memories`: 遗传记忆库
- `learned_memories`: 学习记忆库

**主要方法**：
- `add_sensor()`: 添加传感器到AI生命体
- `add_actuator()`: 添加执行器到AI生命体
- `add_central_brain()`: 添加中枢管理器到AI生命体
- `connect_tools()`: 连接两个工具组件
- `perceive_environment()`: 感知环境，生成情境描述
- `decide_action()`: 基于记忆决定控制信号
- `apply_controls()`: 应用控制信号到执行器
- `learn_from_experience()`: 从经验中学习
- `reproduce()`: 繁殖后代
- `update()`: 每帧更新

### 2.2 MemoryGene类

**功能**：记忆基因类，实现了记忆的遗传和进化

**主要属性**：
- `situation`: 情境描述
- `action_pattern`: 动作模式
- `success_rate`: 成功率
- `strength`: 记忆强度
- `age`: 记忆年龄

**主要方法**：
- `mutate()`: 记忆变异
- `decay()`: 记忆衰减
- `reinforce()`: 记忆强化

### 2.3 EventSystem类

**功能**：事件系统类，用于组件间通信

**主要方法**：
- `register_listener()`: 注册事件监听器
- `unregister_listener()`: 注销事件监听器
- `emit_event()`: 触发事件

## 3. 模块依赖关系

```
core/
├── organism.py      # 依赖: tools, memory
├── memory.py        # 无外部依赖
└── event_system.py  # 无外部依赖
```

## 4. 使用示例

### 创建AI生命体

```python
from ai_organism.core import Organism
from ai_organism.tools import TouchSensor, LightSensor, MuscleActuator, CiliaActuator, CentralBrain, Connection

# 创建AI生命体
organism = Organism("organism_1", (400, 300))

# 添加传感器
touch_sensor = TouchSensor("touch_1", (10, 10), 50)
light_sensor = LightSensor("light_1", (-10, 10), 100)
organism.add_sensor(touch_sensor)
organism.add_sensor(light_sensor)

# 添加执行器
muscle_actuator = MuscleActuator("muscle_1", (10, -10), 5.0)
cilia_actuator = CiliaActuator("cilia_1", (-10, -10), 2.0)
organism.add_actuator(muscle_actuator)
organism.add_actuator(cilia_actuator)

# 添加中枢管理器
central_brain = CentralBrain("brain_1", (0, 0))
organism.add_central_brain(central_brain)

# 连接工具组件
organism.connect_tools("touch_1", "muscle_1", 1.0)
organism.connect_tools("light_1", "cilia_1", 1.0)
organism.connect_tools("brain_1", "muscle_1", 0.5)
organism.connect_tools("brain_1", "cilia_1", 0.5)
```

### 模拟AI生命体

```python
# 在模拟主循环中更新生命体状态
while running:
    # 感知环境
situation = organism.perceive_environment(environment)
    
    # 决策动作
controls = organism.decide_action(situation)
    
    # 执行动作
organism.apply_controls(controls)
    
    # 学习
organism.learn_from_experience(situation, controls, success)
    
    # 繁殖
if organism.energy > 100 and random.random() < 0.01:
        child = organism.reproduce()
        organisms.append(child)
    
    # 更新状态
organism.update(environment)
```

## 5. 开发指南

### 添加新的生命体属性

1. 在`Organism`类中添加新的属性
2. 在`__init__`方法中初始化该属性
3. 在`update`方法中更新该属性
4. 在相关方法中使用该属性

### 扩展记忆系统

1. 在`MemoryGene`类中添加新的属性
2. 在`__init__`方法中初始化该属性
3. 在相关方法中使用该属性
4. 更新`mutate`、`decay`和`reinforce`方法以处理新属性

## 6. 性能优化建议

- 使用字典存储工具组件和记忆，提高查找效率
- 只在必要时更新和计算属性
- 限制记忆的数量和大小，避免内存溢出
- 使用高效的算法进行记忆匹配和选择

## 7. 测试

运行测试用例：

```bash
pytest tests/test_organism.py -v
pytest tests/test_memory.py -v
```