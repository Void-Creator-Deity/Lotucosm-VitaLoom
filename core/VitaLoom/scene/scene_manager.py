# -*- coding: utf-8 -*-
"""场景管理器：`.pond` 文件 CRUD 与 EditorContext 同步。

架构数据流::

    load_scene → editor_context.current_scene → event_bus scene_loaded → SceneViewport

排错: 见 core/VitaLoom/README.md「场景重载」
"""

import os
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal

from core.VitaLoom.core.editor_context import get_editor_context
from core.VitaLoom.core.signal_bus import get_signal_bus
from core.VitaLoom.core.logger import get_logger


logger = get_logger("SceneManager")


class SceneManager(QObject):
    """职责: 单例管理当前 `.pond` 路径、JSON 数据与脏标记。
    时机: 项目打开后由插件/向导调用 load/save；退出时 `EditorKernel.closeEvent` 查询脏状态。
    不变量: `load_scene` 成功须设置 `editor_context.current_scene` 并 publish `scene_loaded`。
    排错: 视口不刷新 → 事件总线与 SignalBus 双通道是否都触发。
    """
    
    # 信号
    scene_created = pyqtSignal(str)  # 场景路径
    scene_loaded = pyqtSignal(str)  # 场景路径
    scene_saved = pyqtSignal(str)  # 场景路径
    scene_changed = pyqtSignal(str)  # 场景路径
    scene_modified = pyqtSignal(bool)  # 是否已修改
    
    _instance: Optional['SceneManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """SceneManager.__init__。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if self._initialized:
            return
        
        super().__init__()
        self._initialized = True
        
        self.editor_context = get_editor_context()
        self.signal_bus = get_signal_bus()
        
        # 当前场景
        self._current_scene_path: Optional[str] = None
        self._current_scene_data: Optional[Dict[str, Any]] = None
        self._scene_modified: bool = False

    def _publish_bus(self, event_name: str, payload: Any = "") -> None:
        """安全发布 event_bus（无 kernel 时跳过，避免单测/脚本崩溃）。"""
        bus = getattr(self.editor_context, "event_bus", None)
        if bus is None or not hasattr(bus, "publish"):
            return
        try:
            bus.publish(event_name, payload)
        except Exception as exc:
            logger.warning("发布事件失败 %s: %s", event_name, exc)
    
    def create_scene(self, scene_name: str, project_path: str, template: Optional[str] = None) -> Optional[str]:
        """创建新场景。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        try:
            scenes_dir = os.path.join(project_path, "scenes")
            os.makedirs(scenes_dir, exist_ok=True)
            
            scene_filename = f"{scene_name}.pond"
            scene_path = os.path.join(scenes_dir, scene_filename)
            
            # 检查场景是否已存在
            if os.path.exists(scene_path):
                return None
            
            # 创建场景数据
            scene_data = {
                "name": scene_name,
                "version": "1.0",
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "modified_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "pond_config": {
                    "name": "默认莲池",
                    "size": [1200, 800],
                    "initial_components": 50,
                    "initial_organisms": 10
                },
                "entities": [],
                "components": [],
                "nodes": [],
                "connections": [],
                "resources": []
            }
            
            # 如果指定了模板，加载模板
            if template:
                template_path = os.path.join(project_path, "templates", template)
                if os.path.exists(template_path):
                    with open(template_path, 'r', encoding='utf-8') as f:
                        template_data = json.load(f)
                        scene_data.update(template_data)
            
            # 保存场景文件
            with open(scene_path, 'w', encoding='utf-8') as f:
                json.dump(scene_data, f, indent=2, ensure_ascii=False)
            
            # 发送信号
            self.scene_created.emit(scene_path)
            self.signal_bus.emit_scene_loaded(scene_path)
            
            return scene_path
        
        except Exception as e:
            logger.exception("创建场景失败: %s", e)
            return None
    
    def clear_scene(self, *, notify: bool = True) -> None:
        """清空内存中的当前场景（切换项目前热刷新 UI）。

        职责:
            重置路径/数据/脏标记，并通知订阅方清空画布。

        时机:
            ProjectManager.open_project 在加载新场景之前。

        排错:
            换项目后仍见旧节点 → 是否未调用本方法或未订阅 scene_loaded('')。
        """
        self._current_scene_path = None
        self._current_scene_data = None
        self._scene_modified = False
        self.editor_context.current_scene = None
        if not notify:
            return
        self.scene_changed.emit("")
        self.scene_modified.emit(False)
        self.signal_bus.emit_scene_modified(False)
        self._publish_bus("scene_cleared", "")
        self._publish_bus("scene_loaded", "")

    def load_scene(self, scene_path: str) -> bool:
        """职责: 读取 `.pond` 并更新当前场景与 project.json 的 active_scene。
        时机: 项目浏览器或场景切换器选中场景时。
        不变量: 文件不存在返回 False；成功时 `_scene_modified` 清零。
        排错: 加载成功但视图为空 → SceneViewport 是否订阅 scene_loaded。
        """
        try:
            if not os.path.exists(scene_path):
                return False
            
            # 读取场景文件
            with open(scene_path, 'r', encoding='utf-8') as f:
                scene_data = json.load(f)
            
            # 更新当前场景
            self._current_scene_path = scene_path
            self._current_scene_data = scene_data
            self._scene_modified = False
            
            # 更新编辑器上下文
            self.editor_context.current_scene = scene_data
            
            # 更新项目的激活场景记录
            if self.editor_context.current_project_path:
                project_json_path = os.path.join(self.editor_context.current_project_path, "project.json")
                if os.path.exists(project_json_path):
                    try:
                        with open(project_json_path, 'r', encoding='utf-8') as f:
                            project_data = json.load(f)
                        
                        relative_path = os.path.relpath(scene_path, os.path.join(self.editor_context.current_project_path, "scenes"))
                        project_data["active_scene"] = relative_path
                        
                        with open(project_json_path, 'w', encoding='utf-8') as f:
                            json.dump(project_data, f, indent=2, ensure_ascii=False)
                    except Exception as e:
                        logger.exception("更新项目激活场景失败: %s", e)

            # 发送信号
            self.scene_loaded.emit(scene_path)
            self.scene_changed.emit(scene_path)
            self.scene_modified.emit(False)
            self.signal_bus.emit_scene_loaded(scene_path)
            
            self._publish_bus("scene_loaded", scene_path)
            
            return True
        
        except Exception as e:
            logger.exception("加载场景失败: %s", e)
            return False
    
    def save_scene(self, scene_path: Optional[str] = None, data: Optional[Dict[str, Any]] = None) -> bool:
        """职责: 将内存场景 JSON 写盘并清除脏标记。
        时机: 用户保存或退出确认 Yes 时。
        不变量: 无当前路径且无 scene_path 时返回 False；可注入 data 覆盖内存。
        排错: 磁盘未更新 → 是否传入视口 `get_scene_data` 合并后的 data。
        """
        try:
            if scene_path is None:
                scene_path = self._current_scene_path
            
            if data:
                self._current_scene_data = data
                self.editor_context.current_scene = data

            if not scene_path or not self._current_scene_data:
                return False
            
            # 更新修改时间
            self._current_scene_data["modified_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 保存场景文件
            with open(scene_path, 'w', encoding='utf-8') as f:
                json.dump(self._current_scene_data, f, indent=2, ensure_ascii=False)
            
            self._scene_modified = False
            
            # 发送信号
            self.scene_saved.emit(scene_path)
            self.scene_modified.emit(False)
            self.signal_bus.emit_scene_saved(scene_path)
            
            return True
        
        except Exception as e:
            logger.exception("保存场景失败: %s", e)
            return False
    
    def save_scene_as(self, scene_path: str) -> bool:
        """另存场景为。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if not self._current_scene_data:
            return False
        
        # 更新场景名称
        scene_name = os.path.splitext(os.path.basename(scene_path))[0]
        self._current_scene_data["name"] = scene_name
        
        # 保存到新路径
        if self.save_scene(scene_path):
            self._current_scene_path = scene_path
            return True
        return False
    
    def get_scene_data(self) -> Optional[Dict[str, Any]]:
        """获取当前场景数据。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        return self._current_scene_data.copy() if self._current_scene_data else None
    
    def update_scene_data(self, data: Dict[str, Any]):
        """更新场景数据。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if self._current_scene_data:
            self._current_scene_data.update(data)
            self._scene_modified = True
            self.scene_modified.emit(True)
            self.signal_bus.emit_scene_modified(True)
    
    def set_scene_modified(self, modified: bool):
        """设置场景修改状态。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if self._scene_modified != modified:
            self._scene_modified = modified
            self.scene_modified.emit(modified)
            self.signal_bus.emit_scene_modified(modified)
    
    def is_scene_modified(self) -> bool:
        """检查场景是否已修改。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        return self._scene_modified
    
    def get_current_scene_path(self) -> Optional[str]:
        """获取当前场景路径。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        return self._current_scene_path
    
    def get_scenes_in_project(self, project_path: str) -> List[str]:
        """获取项目中的所有场景。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        scenes_dir = os.path.join(project_path, "scenes")
        if not os.path.exists(scenes_dir):
            return []
        
        scenes = []
        for filename in os.listdir(scenes_dir):
            if filename.endswith('.pond'):
                scenes.append(os.path.join(scenes_dir, filename))
        
        return sorted(scenes)
    
    def get_scene_info(self, scene_path: str) -> Optional[Dict[str, Any]]:
        """获取场景信息。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        try:
            if not os.path.exists(scene_path):
                return None
            
            with open(scene_path, 'r', encoding='utf-8') as f:
                scene_data = json.load(f)
            
            scene_data['path'] = scene_path
            scene_data['filename'] = os.path.basename(scene_path)
            
            return scene_data
        
        except Exception as e:
            logger.warning("读取场景信息失败: %s (path=%s)", e, scene_path)
            return None


def get_scene_manager() -> SceneManager:
    """获取场景管理器单例"""
    return SceneManager()
