# Editor模块 - AI生命体编辑器

## 1. 模块概述

Editor模块是AI生命体模拟系统的可视化编辑组件，提供了创建和编辑AI生命体的工具。该模块包含：

- 基于PyQt6的现代化GUI编辑器
- 生物可视化编辑画布
- 属性面板和项目树
- 命令模式支持

## 2. 核心设计理念

### 2.1 编辑器架构

编辑器采用了典型的MVC架构：

- **模型(Model)**：生物数据和工具组件
- **视图(View)**：可视化界面，包括画布、属性面板和项目树
- **控制器(Controller)**：处理用户输入和命令执行

### 2.2 编辑流程

1. **创建生物**：从模板或从头开始创建新生物
2. **添加工具组件**：添加传感器、执行器和中枢管理器
3. **连接组件**：建立组件之间的信号连接
4. **配置属性**：调整组件的属性参数
5. **保存生物**：将生物保存到项目中
6. **运行模拟**：在模拟器中运行生物

## 3. 核心类说明

### 3.1 PyQtOrganismEditor类

**功能**：AI生命体编辑器主窗口

**主要属性**：
- `project_tree`: 项目树组件
- `canvas`: 生物可视化编辑画布
- `property_panel`: 属性面板
- `console_panel`: 控制台面板

**主要方法**：
- `__init__()`: 初始化编辑器
- `_init_ui()`: 初始化用户界面
- `create_menu_bar()`: 创建菜单栏
- `create_tool_bar()`: 创建工具栏
- `run_simulation()`: 运行模拟
- `export_organism()`: 导出生物
- `import_organism()`: 导入生物

### 3.2 OrganismCanvas类

**功能**：生物可视化编辑画布

**主要属性**：
- `nodes`: 节点列表
- `connections`: 连接列表
- `selected_node`: 当前选中的节点
- `selected_nodes`: 当前选中的节点列表
- `command_stack`: 命令栈，用于undo/redo

**主要方法**：
- `add_node()`: 添加节点
- `delete_node()`: 删除节点
- `connect_nodes()`: 连接节点
- `disconnect_nodes()`: 断开节点连接
- `move_node()`: 移动节点

### 3.3 ProjectTree类

**功能**：项目树组件，用于管理生物和环境存档

**主要信号**：
- `organism_created`: 生物创建信号
- `organism_deleted`: 生物删除信号

### 3.4 PropertyPanel类

**功能**：属性面板，用于编辑选中组件的属性

**主要方法**：
- `update_properties()`: 更新属性面板
- `_clear_properties()`: 清除属性面板

### 3.5 ConsolePanel类

**功能**：控制台面板，用于显示日志信息

**主要方法**：
- `append_log()`: 添加日志信息
- `clear_log()`: 清除日志信息

## 4. 模块依赖关系

```
editor/
├── __init__.py              # 模块初始化
├── command.py               # 命令模式实现
├── ui/
│   ├── __init__.py          # UI模块初始化
│   ├── pyqt_organism_editor.py  # 主编辑器窗口
│   ├── canvas.py            # 编辑画布
│   ├── panels.py            # 面板组件
│   ├── tree.py              # 项目树
│   ├── console.py           # 控制台
│   ├── nodes.py             # 节点和连接线
│   └── __pycache__/         # 编译缓存
└── __pycache__/             # 编译缓存
```

## 5. 使用示例

### 5.1 运行编辑器

```python
# 直接运行编辑器
from ai_organism.editor.ui import pyqt_organism_editor
pyqt_organism_editor.main()

# 或通过launcher运行
from ai_organism.launcher import modern_launcher
modern_launcher.main()
```

### 5.2 从启动器启动

1. 运行现代化启动器：
   ```bash
   python -m ai_organism.launcher.modern_launcher
   ```

2. 在启动器中点击"运行AI生命体编辑器"按钮

3. 开始创建和编辑AI生命体

## 6. 编辑器功能

### 6.1 生物编辑

- **添加节点**：从工具栏或上下文菜单添加传感器、执行器和中枢管理器
- **连接节点**：拖拽节点之间的连接点创建连接
- **删除节点**：选中节点后按Delete键或使用上下文菜单删除
- **移动节点**：拖拽节点到新位置
- **选择节点**：点击节点进行选择，按住Ctrl键多选

### 6.2 属性编辑

- **节点属性**：调整节点的位置、名称、类型等属性
- **连接属性**：调整连接的权重、方向等属性
- **生物属性**：调整生物的基本属性

### 6.3 项目管理

- **创建生物**：创建新的AI生命体
- **保存生物**：将生物保存到项目中
- **加载生物**：从项目中加载生物
- **删除生物**：从项目中删除生物

### 6.4 模拟控制

- **运行模拟**：在模拟器中运行当前编辑的生物
- **调试模式**：开启调试模式，显示详细信息

## 7. 命令模式支持

编辑器支持命令模式，允许用户进行undo/redo操作：

| 命令类型 | 功能 |
|---------|------|
| AddNodeCommand | 添加节点 |
| DeleteNodeCommand | 删除节点 |
| MoveNodeCommand | 移动节点 |
| CreateConnectionCommand | 创建连接 |
| DeleteConnectionCommand | 删除连接 |

## 8. 开发指南

### 8.1 扩展编辑器功能

1. **添加新工具类型**：
   - 在`tools`模块中创建新的工具类
   - 在编辑器中添加对应的节点类型
   - 实现节点的绘制和编辑功能

2. **添加新命令**：
   - 继承`Command`基类
   - 实现`execute()`和`undo()`方法
   - 在编辑器中注册命令

3. **扩展属性面板**：
   - 添加新的属性编辑器组件
   - 实现属性的读取和写入
   - 连接到属性面板的更新机制

### 8.2 自定义主题

1. 修改工具栏样式：
   ```python
tool_bar.setStyleSheet("""
    QToolBar {
        background-color: #252526;
        color: #ffffff;
        border: none;
        padding: 4px 8px;
        spacing: 8px;
    }
    /* 其他样式 */
""")
   ```

2. 修改画布样式：
   ```python
self.setStyleSheet("background-color: #1e1e1e;")
   ```

## 9. 配置参数

### 9.1 编辑器参数

| 参数 | 描述 | 默认值 |
|------|------|--------|
| `window_width` | 编辑器窗口宽度 | 1200 |
| `window_height` | 编辑器窗口高度 | 800 |
| `canvas_background` | 画布背景颜色 | #1e1e1e |
| `node_size` | 默认节点大小 | 60x40 |
| `connection_width` | 默认连接线宽度 | 2 |

### 9.2 命令参数

| 参数 | 描述 | 默认值 |
|------|------|--------|
| `command_stack_size` | 命令栈大小 | 50 |

## 10. 测试

运行测试用例：

```bash
pytest tests/test_editor.py -v
pytest tests/test_canvas.py -v
```

## 11. 常见问题

### 11.1 编辑器无法启动

**解决方法**：
- 检查PyQt6是否正确安装
- 确保所有依赖项都已安装
- 检查Python版本是否符合要求（>=3.12）

### 11.2 画布无法添加节点

**解决方法**：
- 检查节点类型是否正确
- 确保画布已正确初始化
- 检查事件处理是否正常

### 11.3 属性面板不更新

**解决方法**：
- 检查节点是否正确选中
- 确保信号连接正常
- 检查属性更新逻辑是否正确

## 12. 未来计划

- [ ] 实现3D编辑模式
- [ ] 添加更多工具类型
- [ ] 支持生物模板
- [ ] 添加更多可视化效果
- [ ] 支持协作编辑