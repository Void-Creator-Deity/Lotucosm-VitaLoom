# Launcher模块 - AI生命体启动器

## 1. 模块概述

Launcher模块是AI生命体模拟系统的启动器组件，提供了一个统一的入口点，用于管理环境存档、运行模拟器和编辑器。该模块包含：

- 现代化GUI启动器
- 环境存档管理
- 模拟器和编辑器的启动控制

## 2. 核心设计理念

### 2.1 启动器架构

启动器采用了现代化的GUI设计，提供了直观的用户界面：

- **左侧面板**：环境存档管理，用于选择、创建、编辑和删除环境存档
- **右侧面板**：功能选择，用于启动模拟器和编辑器
- **底部面板**：功能说明和帮助信息

### 2.2 启动流程

1. **初始化启动器**：加载环境存档列表
2. **选择环境**：用户从列表中选择一个环境存档
3. **选择功能**：用户选择要运行的功能（模拟器或编辑器）
4. **启动功能**：启动器启动相应的功能模块
5. **监控运行**：监控功能模块的运行状态

## 3. 核心类说明

### 3.1 ModernLauncher类

**功能**：现代化GUI启动器，提供环境存档管理和功能启动

**主要属性**：
- `archive_manager`: 环境存档管理器
- `archive_list`: 环境存档列表组件
- `run_simulation_btn`: 运行模拟器按钮
- `run_editor_btn`: 运行编辑器按钮
- `exit_btn`: 退出按钮

**主要方法**：
- `__init__()`: 初始化启动器
- `init_ui()`: 初始化用户界面
- `load_archives()`: 加载环境存档列表
- `create_new_environment()`: 创建新环境
- `edit_environment()`: 编辑环境
- `delete_environment()`: 删除环境
- `run_tool_simulation()`: 运行继承算法模拟器
- `run_organism_editor()`: 运行AI生命体编辑器

## 4. 模块依赖关系

```
launcher/
├── __init__.py              # 模块初始化
├── modern_launcher.py       # 现代化GUI启动器，依赖: PyQt6, environment
└── __pycache__/             # 编译缓存
```

## 5. 使用示例

### 5.1 运行启动器

```python
# 直接运行启动器
from ai_organism.launcher import modern_launcher
modern_launcher.main()

# 或通过模块导入运行
python -m ai_organism.launcher.modern_launcher
```

### 5.2 使用启动器

1. **启动启动器**：运行上述命令启动现代化GUI启动器
2. **创建环境**：点击"新建环境"按钮创建新的环境存档
3. **选择环境**：从列表中选择一个环境存档
4. **运行模拟器**：点击"运行继承算法模拟器"按钮启动模拟器
5. **运行编辑器**：点击"运行AI生命体编辑器"按钮启动编辑器
6. **退出系统**：点击"退出系统"按钮退出启动器

## 6. 启动器功能

### 6.1 环境存档管理

- **新建环境**：创建新的环境存档
- **编辑环境**：编辑选中的环境存档
- **删除环境**：删除选中的环境存档
- **查看环境信息**：查看选中环境的详细信息

### 6.2 模拟器控制

- **运行模拟器**：在选中的环境中运行继承算法模拟器
- **模拟器参数配置**：配置模拟器的运行参数

### 6.3 编辑器控制

- **运行编辑器**：启动AI生命体编辑器
- **编辑器参数配置**：配置编辑器的运行参数

### 6.4 系统控制

- **退出系统**：退出整个系统
- **显示帮助**：显示系统帮助信息
- **显示关于**：显示系统版本信息

## 7. 环境存档管理

### 7.1 环境存档结构

环境存档包含以下信息：

- **名称**：环境的名称
- **描述**：环境的详细描述
- **创建时间**：环境的创建时间
- **修改时间**：环境的最后修改时间
- **环境数据**：环境的实际数据（食物、光源、障碍物等）

### 7.2 环境存档操作

| 操作 | 功能 |
|------|------|
| 新建环境 | 创建新的环境存档 |
| 编辑环境 | 修改环境存档的信息和数据 |
| 删除环境 | 从系统中删除环境存档 |
| 加载环境 | 将环境数据加载到内存中 |

## 8. 配置参数

### 8.1 启动器参数

| 参数 | 描述 | 默认值 |
|------|------|--------|
| `window_width` | 启动器窗口宽度 | 900 |
| `window_height` | 启动器窗口高度 | 600 |
| `min_window_width` | 启动器窗口最小宽度 | 800 |
| `min_window_height` | 启动器窗口最小高度 | 500 |
| `archive_dir` | 环境存档目录 | ./environments |

## 9. 开发指南

### 9.1 扩展启动器功能

1. **添加新功能按钮**：
   ```python
   new_feature_btn = QPushButton("新功能")
   new_feature_btn.clicked.connect(self.run_new_feature)
   function_buttons_layout.addWidget(new_feature_btn)
   ```

2. **添加新环境类型**：
   - 在`environment`模块中创建新的环境类
   - 在启动器中添加对应的环境创建和管理逻辑

3. **自定义样式**：
   ```python
   self.setStyleSheet("""
       QMainWindow {
           background-color: #f0f0f0;
       }
       /* 其他样式 */
   """)
   ```

### 9.2 集成新模块

1. **导入新模块**：
   ```python
   from ai_organism.new_module import NewModule
   ```

2. **添加启动方法**：
   ```python
   def run_new_module(self):
       """运行新模块"""
       try:
           import subprocess
           import sys
           cmd = [sys.executable, '-c', 'from ai_organism.new_module import new_module; new_module.main()']
           subprocess.Popen(cmd, shell=False)
       except Exception as e:
           QMessageBox.critical(self, "错误", f"启动新模块失败: {str(e)}")
   ```

## 10. 测试

运行测试用例：

```bash
pytest tests/test_launcher.py -v
```

## 11. 常见问题

### 11.1 启动器无法启动

**解决方法**：
- 检查PyQt6是否正确安装
- 确保所有依赖项都已安装
- 检查Python版本是否符合要求（>=3.12）

### 11.2 无法加载环境存档

**解决方法**：
- 检查环境存档目录是否存在
- 检查环境存档文件是否损坏
- 检查文件权限

### 11.3 模拟器或编辑器无法启动

**解决方法**：
- 检查对应模块是否正确安装
- 检查模块依赖项是否满足
- 查看日志文件获取详细错误信息

## 12. 未来计划

- [ ] 支持更多的环境类型
- [ ] 添加环境预览功能
- [ ] 支持环境模板
- [ ] 添加更多的模拟器和编辑器选项
- [ ] 支持多语言
- [ ] 支持主题切换