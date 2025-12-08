# Lotucosm: VitaLoom 🌌✨

## 🌸 莲池宇宙 · 生命织机

### 项目介绍

Lotucosm: VitaLoom 是一个基于 **感知-验证自主演化循环 (PVAEC)** 的数字生命模拟框架，构建了名为"莲池宇宙"的虚拟演化环境，让智能通过生命自身的经验"编织"而成。

### 灵感来源

我们摒弃了传统AI从静态数据中学习的范式，转向模拟生命在其生命周期内通过自身经验建构智能的过程。在"莲池宇宙"中，智能不是被编程的，而是通过：

```text
感知 → 记忆 → 尝试 → 验证（利用新感知） → 再记忆 → ...
```

这一递归循环自主涌现的。这个感知-验证自主演化循环 (PVAEC) 定义了数字生命"编织"智能的根本法则。

### 核心特点

- **组件生态系统**：所有组件（传感器、执行器、复合器）均为独立文件存储，支持组件漂浮、自组装和生命周期管理
- **遗传与演化机制**：支持记忆遗传、组件遗传和体外获取机制
- **莲池存档系统**：完整环境存档、增量保存和存档版本管理
- **记忆编辑系统**：演化产生的生物可保存为新模板，其记忆系统可编辑
- **组件位置系统**：支持体内组件、体外组件和通用组件的动态管理

### 当前实现状态

- ✅ 感知-验证自主演化循环 (PVAEC) 核心机制
- ✅ 莲池存档系统（完整环境存档、增量保存、存档版本管理）
- ✅ 组件生态系统（组件模板、漂浮机制、自组装、生命周期）
- ✅ 遗传与演化新机制（记忆遗传、组件遗传、体外获取）
- ✅ 组件位置系统（体内组件、体外组件、通用组件、动态迁移）
- ✅ 记忆编辑系统
- ✅ 复合器组件

### 未来发展方向

- ⏳ 跨莲池组件交换
- ⏳ 记忆迁移工具
- ⏳ 支持分布式模拟
- ⏳ 在线组件共享平台
- ⏳ 可视化编辑界面优化

### 技术栈

- Python 3.9+
- PyQt6 (图形界面)
- JSON (数据存储)
- 模块化设计

### 许可证

MIT License

---

[![python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![核心](https://img.shields.io/badge/%E6%A0%B8%E5%BF%83-PVAEC_%E5%BE%AA%E7%8E%AF-important)](README.md)

## 🌟 核心哲学

我们摒弃了传统AI从静态数据中学习的范式，转向模拟生命在其生命周期内通过自身经验建构智能的过程。在"莲池宇宙"中，智能不是被编程的，而是通过：

```text
感知 → 记忆 → 尝试 → 验证（利用新感知） → 再记忆 → ...
```

这一递归循环自主涌现的。这个感知-验证自主演化循环 (PVAEC) 定义了数字生命"编织"智能的根本法则。

## 🆕 新增核心机制

### 1. 莲池存档系统

- 完整环境存档：莲池可以完整保存为本地文件，包含环境状态、生物体、组件、资源分布等
- 增量保存：支持快照和增量保存，便于长期实验记录
- 存档版本管理：莲池演化历史可追溯和对比

### 2. 组件生态系统

- 组件模板系统：所有组件（传感器、执行器、复合器）均为独立文件存储
- 组件漂浮机制：死亡细胞释放的组件在莲池中漂浮，可被其他生物捕获
- 组件自组装：不同类属组件碰撞时可自动连线形成简单系统
- 组件生命周期：组件随时间分解为食物，食物可重组为新组件

### 3. 遗传与演化新机制

- 记忆遗传：细胞分裂时继承绝大部分记忆，但后天获得的记忆有概率继承
- 组件遗传：分裂时继承所有先天组件，后天获得的组件通过变异概率继承
- 体外获取机制：生物体可通过捕获漂浮组件获得新能力
- 记忆编辑系统：演化产生的生物可保存为新模板，其记忆系统可编辑

### 4. 组件位置系统

- 体内组件：只能在细胞膜内部，参与生物体内部信号传递
- 体外组件：附着在细胞膜表面，直接与环境交互
- 通用组件：既可位于体内也可在体外，捕获时随机确定位置
- 动态迁移：部分组件可根据需要在体内外迁移

## 🚀 快速开始

### 安装

```bash
# 克隆项目
git clone https://github.com/Void-Creator-Deity/Lotucosm-VitaLoom.git
cd Lotucosm-VitaLoom

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 快速体验

```bash
# 启动主程序
python src/main.py

# 加载预设莲池
python examples/load_saved_pond.py

# 组件生态系统演示
python examples/component_ecosystem.py
```

### 基本使用示例

```python
from src.vitalloom.core.pvaec_cycle import PVAECCycle
from src.vitalloom.components.PVAECEngine import PVAECEngine

# 创建一个PVAEC循环实例
pvaec = PVAECCycle()

# 创建PVAEC引擎组件（原中枢大脑）
brain = PVAECEngine(organism_id="test_organism")

# 运行完整的PVAEC循环
print("启动感知-验证自主演化循环...")
print("1. 生物体感知环境状态")
print("2. 检索相关经验记忆")
print("3. 基于记忆生成探索性行动")
print("4. 利用新感知验证行动效果")
print("5. 更新记忆结构，完成智能建构")
```

## 📁 项目架构（更新版）

```text
Lotucosm-VitaLoom/
├── src/                          # 源代码
│   ├── lotucosm/                # 莲池核心
│   │   ├── environment/        # 环境系统（增强）
│   │   │   ├── lotus_pond.py   # 莲池环境（增强存档功能）
│   │   │   ├── physics_engine.py # 物理引擎（增强碰撞检测）
│   │   │   ├── resource_manager.py # 资源管理
│   │   │   ├── floating_system.py # 新增：漂浮系统（组件、食物）
│   │   │   ├── assembly_system.py # 新增：自组装系统
│   │   │   └── pond_serializer.py # 新增：莲池序列化器
│   │   ├── evolution/          # 演化机制（增强）
│   │   │   ├── inheritance.py  # 遗传机制（增强记忆遗传）
│   │   │   ├── mutation.py     # 变异机制
│   │   │   ├── selection.py    # 新增：选择机制
│   │   │   └── component_inheritance.py # 新增：组件遗传系统
│   │   ├── persistence/        # 新增：持久化系统
│   │   │   ├── __init__.py
│   │   │   ├── pond_saver.py   # 莲池保存
│   │   │   ├── organism_serializer.py # 生物体序列化
│   │   │   ├── component_serializer.py # 组件序列化
│   │   │   └── memory_storage.py # 记忆存储系统
│   │   └── simulator/          # 模拟器（增强）
│   ├── vitalloom/              # 生命织机编辑器（核心生物系统）
│   │   ├── core/               # 核心算法
│   │   │   ├── pvaec_cycle.py  # PVAEC循环实现
│   │   │   ├── perception.py   # 感知系统
│   │   │   ├── memory.py       # 记忆系统
│   │   │   └── memory_editor.py # 新增：记忆编辑器
│   │   ├── components/         # 组件系统（增强）
│   │   │   ├── __init__.py     # 组件导出
│   │   │   ├── components_base.py  # 组件基类（新增位置属性）
│   │   │   ├── sensors.py      # 传感器实现
│   │   │   ├── actuators.py    # 执行器实现
│   │   │   ├── hybrid.py       # 新增：复合器（兼具传感和执行功能）
│   │   │   ├── membrane.py     # 细胞膜实现（一个细胞容器）
│   │   │   ├── PVAECEngine.py  # PVAEC引擎（也有复合器功能但不继承复合器，留好扩展后面有可能对接ai智能体，现在不考虑）
│   │   │   ├── connection.py   # 连接系统
│   │   │   ├── component_library.py # 新增：组件库管理器
│   │   │   └── component_factory.py # 新增：组件工厂
│   │   ├── organisms/          # 生物体系（增强）
│   │   │   ├── __init__.py     # 生物体导出
│   │   │   ├── organism.py     # 生物体基类（增强遗传机制）
│   │   │   ├── simple_organism.py  # 简单生物（无PVAEC引擎）
│   │   │   ├── intelligent_organism.py  # 智能生物（有PVAEC引擎）
│   │   │   ├── reproduction.py # 新增：繁殖与分裂系统
│   │   │   └── component_acquisition.py # 新增：组件获取系统
│   │   └── editor/             # 编辑器核心（增强）
│   └── main.py                 # 主入口（调用启动器）
├── data/                       # 项目数据（重构）
│   ├── components/             # 组件模板库
│   │   ├── sensors/           # 传感器模板
│   │   │   ├── cilia_sensor.json  # 纤毛传感器
│   │   │   ├── light_sensor.json  # 光传感器
│   │   │   └── chemical_sensor.json # 化学传感器
│   │   ├── actuators/         # 执行器模板
│   │   │   ├── cilia_actuator.json # 纤毛执行器
│   │   │   ├── muscle.json    # 肌肉执行器
│   │   │   └── secretor.json  # 分泌器
│   │   ├── hybrids/           # 复合器模板
│   │   │   ├── cilia_hybrid.json # 纤毛复合器
│   │   │   └── flagellum.json # 鞭毛复合器
│   │   └── special/           # 特殊组件
│   │       ├── PVAEC_engine.json # PVAEC引擎模板
│   │       └── membrane.json  # 细胞膜模板
│   ├── organisms/             # 生物体模板库
│   │   ├── predefined/        # 预设生物
│   │   │   ├── basic_cell.json # 基础细胞
│   │   │   ├── predator.json  # 捕食者
│   │   │   └── photosynthesizer.json # 光合作用者
│   │   ├── evolved/           # 演化产生生物
│   │   │   └── pond_{id}/     # 按莲池分类
│   │   └── user_created/      # 用户创建生物
│   ├── ponds/                 # 莲池存档
│   │   ├── experimental/      # 实验莲池
│   │   │   ├── pond_001/
│   │   │   │   ├── config.json # 莲池配置
│   │   │   │   ├── snapshot.json # 当前快照
│   │   │   │   ├── history/    # 历史版本
│   │   │   │   ├── statistics/ # 统计数据
│   │   │   │   └── components/ # 莲池内组件存档
│   │   │   └── pond_002/
│   │   └── templates/         # 莲池模板
│   ├── memories/              # （可选，记忆和那个PVAEC引擎有关系，没有这个的没有记忆，没于这个组件连接的组件也不会记录，细胞变异后原有记忆不适应会慢慢淡忘）新增：记忆库
│   │   ├── inherited/         # 遗传记忆模板
│   │   ├── learned/           # 学习记忆存档
│   │   └── edited/            # 编辑后的记忆
│   └── system/                # 系统数据
│       ├── config.json        # 系统配置
│       └── component_registry.json # 组件注册表
├── examples/                   # 示例代码
├── docs/                       # 项目文档
├── tests/                      # 测试代码
├── scripts/                    # 辅助脚本
├── assets/                     # 静态资源
├── requirements.txt            # 依赖清单
└── README.md                   # 本文件
```

## 🔧 新增核心模块详解

### 1. 记忆编辑器 (src/vitalloom/core/memory_editor.py)

```python
class MemoryEditor:
    """
    记忆编辑系统，允许用户：
    1. 查看生物体的记忆结构
    2. 编辑记忆内容（情境、行动模式、成功率）
    3. 导出记忆为模板
    4. 导入记忆到生物体
    5. 可视化记忆关联网络
    """
```

### 2. 复合器组件 (src/vitalloom/components/hybrid.py)

```python
class HybridComponent(ComponentBase):
    """
    复合器组件，兼具传感和执行功能
    例如：纤毛复合器 - 既能感知水流，又能产生推进力
    属性：
    - is_sensor: bool = True
    - is_actuator: bool = True
    - sensor_sensitivity: float  # 传感灵敏度
    - actuator_strength: float   # 执行强度
    - mode: str = 'auto'  # 'sensor', 'actuator', 'auto'
    """
```

### 3. 组件位置系统 (src/vitalloom/components/components_base.py)

```python
class ComponentBase:
    """
    组件基类增强：
    - location: str = 'internal'  # 'internal', 'external', 'both'
    - acquired: bool = False  # 是否是后天获得的
    - congenital: bool = True  # 是否是先天组件
    - attach_point: Optional[str]  # 附着点（对于体外组件）
    """
```

### 4. 莲池漂浮系统 (src/lotucosm/environment/floating_system.py)

```python
class FloatingSystem:
    """
    管理莲池中漂浮的组件和食物：
    1. 组件漂浮：死亡细胞释放的组件在环境中漂浮
    2. 组件碰撞：不同类型组件碰撞可能自动连线
    3. 组件分解：组件随时间分解为食物粒子
    4. 食物重组：食物粒子碰撞可能重组为新组件
    5. 捕获机制：生物体可捕获漂浮的组件
    """
```

### 5. 遗传增强系统 (src/lotucosm/evolution/component_inheritance.py)

```python
class ComponentInheritance:
    """
    组件遗传规则：
    1. 先天组件：100%遗传给子代
    2. 后天组件：根据变异率概率遗传
    3. 组件位置：遗传时保持相同位置属性
    4. 组件状态：遗传时重置为初始状态
    5. 记忆关联：组件相关的记忆有更高遗传概率
    """
```

## 🎯 新机制使用示例

### 1. 创建和保存莲池

```python
from src.lotucosm.environment.lotus_pond import LotusPond
from src.lotucosm.persistence.pond_saver import PondSaver

# 创建新莲池
pond = LotusPond(
    name="演化实验场",
    size=(1200, 800),
    initial_components=50,  # 初始漂浮组件数量
    component_variety="all"  # 导入所有组件类型
)

# 运行一段时间
for _ in range(1000):
    pond.update()
    
# 保存莲池
saver = PondSaver()
pond_id = saver.save_pond(pond, "data/ponds/experimental/pond_001")

print(f"莲池已保存，ID: {pond_id}")
```

### 2. 组件捕获和整合

```python
from src.vitalloom.organisms.intelligent_organism import IntelligentOrganism

# 生物体捕获漂浮组件
organism = IntelligentOrganism("cell_001", (400, 300))

# 扫描周围漂浮组件
nearby_components = pond.get_nearby_components(organism.position, radius=50)

for component in nearby_components:
    if organism.can_capture(component):
        captured = organism.capture_component(component)
        if captured:
            print(f"捕获组件: {component.type}")
            # 组件自动整合到生物体
            # 体外组件附着在细胞膜
            # 体内组件整合到内部系统
```

### 3. 细胞分裂和遗传

```python
# 细胞达到分裂条件时
if organism.ready_to_reproduce():
    # 创建子代
    offspring = organism.reproduce()
    
    # 遗传机制：
    # 1. 继承所有先天组件
    # 2. 后天组件按变异率继承
    # 3. 继承大部分记忆（后天记忆概率继承）
    # 4. 记忆强度可能衰减
    
    print(f"子代创建成功，继承组件: {len(offspring.components)}")
    print(f"继承记忆: {len(offspring.memory_system.memories)}")
```

### 4. 组件自组装

```python
# 莲池中漂浮组件的自组装
# 不同类型组件碰撞时可能自动连线

# 传感器 + 执行器 → 简单反射弧
# 传感器 + 传感器 → 复合感知系统
# 执行器 + 执行器 → 协同运动系统

# 这些自组装的系统可被生物体整体捕获
# 加速复杂功能的获得
```

### 5. 记忆编辑和导出

```python
from src.vitalloom.core.memory_editor import MemoryEditor
from src.vitalloom.persistence.organism_serializer import load_organism

# 加载演化产生的生物体
organism = load_organism("data/organisms/evolved/smart_cell_042.json")

# 创建记忆编辑器
editor = MemoryEditor(organism)

# 查看记忆结构
memories = editor.list_memories()
for memory in memories:
    print(f"情境: {memory.situation}")
    print(f"行动模式: {memory.action_pattern}")
    print(f"成功率: {memory.success_rate}")

# 编辑特定记忆
editor.edit_memory(
    memory_id="memory_001",
    situation="light_high_food_near",
    action_pattern={"move_towards": 0.8, "extend_cilia": 0.3},
    success_rate=0.85
)

# 导出生物体为模板
editor.export_organism_template("data/organisms/user_created/my_design.json")
```

## 📊 实验与数据分析

### 新数据收集维度

- 组件获取轨迹：记录生物体如何获得新组件
- 记忆演化路径：追踪记忆的创建、强化、衰减过程
- 遗传成功率：统计不同组件的遗传成功率
- 自组装效率：漂浮组件形成功能系统的比率
- 环境适应性：不同组件配置对环境的适应度

### 实验配置示例

```python
experiment_config = {
    "pond": {
        "size": (1600, 1200),
        "initial_component_count": 100,
        "component_variety": ["sensor", "actuator", "hybrid"],
        "floating_system": {
            "assembly_enabled": True,
            "decay_rate": 0.001,
            "reassembly_probability": 0.01
        }
    },
    "organisms": {
        "initial_count": 20,
        "reproduction_energy": 80,
        "inheritance": {
            "congenital_inheritance_rate": 1.0,
            "acquired_inheritance_rate": 0.3,
            "memory_inheritance_rate": 0.8
        }
    },
    "data_collection": {
        "save_interval": 1000,  # 每1000步保存一次
        "track_component_acquisition": True,
        "record_memory_changes": True
    }
}
```

## 🧪 研究应用扩展

新增机制支持以下研究方向：

### 1. 模块化演化

- 研究组件如何通过获取、整合、遗传实现功能模块化
- 分析模块化对演化速度和适应度的影响

### 2. 记忆-组件共演化

- 探索记忆系统如何与组件系统协同演化
- 研究后天获得的组件如何影响记忆结构

### 3. 生态系统动力学

- 分析组件漂浮、捕获、重组形成的生态系统
- 研究资源（组件、食物）循环对演化的影响

### 4. 人工设计辅助

- 使用记忆编辑器分析演化产生的智能
- 将自然演化与人工设计相结合

## 🔬 新增示例演示

| 示例文件 | 功能描述 | 运行命令 |
|---------|---------|---------|
| component_ecosystem.py | 组件生态系统演示 | python examples/component_ecosystem.py |
| memory_inheritance.py | 记忆遗传实验 | python examples/memory_inheritance.py |
| pond_save_load.py | 莲池存档演示 | python examples/pond_save_load.py |
| hybrid_component_demo.py | 复合器功能演示 | python examples/hybrid_component_demo.py |
| capture_and_integrate.py | 组件捕获演示 | python examples/capture_and_integrate.py |

## 🚧 开发路线图

### 近期目标

- 实现基础组件漂浮和捕获系统
- 完成记忆编辑器的基本功能
- 实现莲池完整序列化
- 添加组件遗传规则

### 中期目标

- 实现组件自组装系统
- 完善记忆-组件关联系统
- 添加可视化编辑界面
- 优化性能以支持大规模模拟

### 长期目标

- 实现跨莲池组件交换
- 开发记忆迁移工具
- 支持分布式模拟
- 构建在线组件共享平台

## 🤝 贡献指南

欢迎对新增机制的贡献！特别需要以下方向的帮助：

- 组件设计：创建新的传感器、执行器、复合器模板
- 遗传算法：改进组件遗传和变异规则
- 记忆系统：增强记忆编辑和可视化工具
- 性能优化：提升大规模组件漂浮系统的性能
- 文档完善：编写新机制的使用教程和API文档

## 📄 许可证

本项目采用MIT许可证 - 查看 LICENSE 文件了解详情。

## 📞 联系方式

- 项目主页: [https://github.com/Void-Creator-Deity/Lotucosm-VitaLoom](https://github.com/Void-Creator-Deity/Lotucosm-VitaLoom)
- 问题反馈: GitHub Issues
- 讨论交流: 欢迎在GitHub Discussions中参与讨论

🌌 在莲池宇宙中，每一个组件都是可重用的智慧碎片。
🧬 每一段记忆都是可编辑的经验传承。
🔬 加入我们，探索模块化智能的涌现与演化！
