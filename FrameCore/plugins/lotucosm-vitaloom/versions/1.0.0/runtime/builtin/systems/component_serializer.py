"""PS 单组件 JSON 快照（与 PondSerializer 字段对齐的辅助模块）。

排错: 见 `builtin/README.md`、`pond_serializer.py`。
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from builtin.components.components_base import ComponentBase
from core.VitaLoom.core.logger import get_logger
from builtin.components.component_library import canonical_component_type

logger = get_logger("ComponentSerializer")


class ComponentSerializer:
    """组件序列化器 - 负责组件的序列化和反序列化
    
    负责：
    1. 组件完整序列化
    2. 组件反序列化
    3. 组件模板管理
    """
    
    def __init__(self, save_format: str = "json"):
        """构造并初始化实例。

        职责:
            建立本对象运行所需字段与子系统引用。

        时机:
            宿主创建对象时单次调用。

        不变量:
            子类须完整 super().__init__ 链。

        排错:
            属性缺失 → 查 super 与模块顶 docstring。
        """
        self.save_format = save_format
        self.version = "1.0"  # 序列化版本

    def _log_error(self, action: str, error: Exception):
        logger.warning("[System:ComponentSerializer] %s失败: %s", action, error)

    def _require_fields(self, data: Dict[str, Any], fields: list[str], context: str):
        missing = [field for field in fields if field not in data]
        if missing:
            raise ValueError(f"{context}缺少字段: {', '.join(missing)}")
    
    def serialize_component(self, component: ComponentBase) -> Dict[str, Any]:
        """序列化组件。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 基本信息
        component_data: Dict[str, Any] = {
            "version": self.version,
            "type": canonical_component_type(component),
            "id": component.id,
            "name": getattr(component, "name", component.id),
            "timestamp": datetime.now().isoformat(),
            "location": getattr(component, "location", "internal"),
            "congenital": getattr(component, "congenital", True),
            "acquired": getattr(component, "acquired", False),
            "attach_point": getattr(component, "attach_point", None),
            "energy_consumption": getattr(component, "energy_consumption", 0.0)
        }
        if getattr(component, "sr_component_id", None) is not None:
            component_data["sr_component_id"] = component.sr_component_id
        
        # 添加组件特定属性
        if hasattr(component, "is_sensor") and component.is_sensor:
            component_data["is_sensor"] = True
            if hasattr(component, "sensor_sensitivity"):
                component_data["sensor_sensitivity"] = component.sensor_sensitivity
            if hasattr(component, "sense_range"):
                component_data["sense_range"] = component.sense_range
            # 检查并添加传感器类型，只有当属性存在时才添加
        
        if hasattr(component, "is_actuator") and component.is_actuator:
            component_data["is_actuator"] = True
            if hasattr(component, "actuator_strength"):
                component_data["actuator_strength"] = component.actuator_strength
            if hasattr(component, "actuation_speed"):
                component_data["actuation_speed"] = component.actuation_speed
            # 检查并添加执行器类型，只有当属性存在时才添加
        
        if hasattr(component, "is_hybrid") and component.is_hybrid:
            component_data["is_hybrid"] = True
            if hasattr(component, "mode"):
                component_data["mode"] = component.mode
            if hasattr(component, "sensor_sensitivity"):
                component_data["sensor_sensitivity"] = component.sensor_sensitivity
            if hasattr(component, "actuator_strength"):
                component_data["actuator_strength"] = component.actuator_strength
        
        if hasattr(component, "is_membrane") and component.is_membrane:
            component_data["is_membrane"] = True
            if hasattr(component, "permeability"):
                component_data["permeability"] = component.permeability
            if hasattr(component, "thickness"):
                component_data["thickness"] = component.thickness
            if hasattr(component, "surface_area"):
                component_data["surface_area"] = component.surface_area
        
        if hasattr(component, "is_pvaec_engine") and component.is_pvaec_engine:
            component_data["is_pvaec_engine"] = True
            if hasattr(component, "learning_rate"):
                component_data["learning_rate"] = component.learning_rate
            if hasattr(component, "exploration_rate"):
                component_data["exploration_rate"] = component.exploration_rate
            if hasattr(component, "success_threshold"):
                component_data["success_threshold"] = component.success_threshold
            if hasattr(component, "associations") and isinstance(getattr(component, "associations"), dict):
                component_data["associations"] = {
                    str(k): {str(ak): float(av) for ak, av in (v or {}).items()}
                    for k, v in component.associations.items()
                }
            # 检查并添加记忆容量，只有当属性存在时才添加
        
        return component_data
    
    def deserialize_component(self, component_data: Dict[str, Any]) -> Optional[ComponentBase]:
        """通过统一组件工厂恢复组件，未知类型兼容回退为 ComponentBase。"""
        try:
            self._require_fields(
                component_data,
                ["type", "id", "name", "location", "congenital", "acquired", "attach_point", "energy_consumption"],
                "component_data",
            )
            from builtin.components.component_factory import ComponentFactory

            component = ComponentFactory().create_component(
                str(component_data["type"]),
                str(component_data["id"]),
                organism_id="",
                name=component_data["name"],
                **({"sr_component_id": component_data["sr_component_id"]}
                   if "sr_component_id" in component_data else {}),
            )
            component.restore_persistent_state(component_data)
            return component
        except Exception as e:
            self._log_error("反序列化组件", e)
            return None
    def save_component(self, component: ComponentBase, file_path: str) -> bool:
        """保存组件到文件。

        
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
            # 确保保存目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 序列化组件
            component_data = self.serialize_component(component)
            
            # 保存到文件
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(component_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            self._log_error("保存组件", e)
            return False
    
    def load_component(self, file_path: str) -> Optional[ComponentBase]:
        """从文件加载组件。

        
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
            # 读取文件
            with open(file_path, "r", encoding="utf-8") as f:
                component_data = json.load(f)
            
            # 反序列化组件
            component = self.deserialize_component(component_data)
            
            return component
        except Exception as e:
            self._log_error("加载组件", e)
            return None
    
    def save_component_template(self, component: ComponentBase, save_path: str, template_name: str) -> Optional[str]:
        """保存组件为模板。

        
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
            # 确保保存目录存在
            os.makedirs(save_path, exist_ok=True)
            
            # 生成文件名
            file_name = f"{template_name}.json"
            file_path = os.path.join(save_path, file_name)
            
            # 保存组件
            success = self.save_component(component, file_path)
            
            if success:
                return file_path
            else:
                return None
        except Exception as e:
            self._log_error("保存组件模板", e)
            return None
    
    def load_component_template(self, template_path: str) -> Optional[ComponentBase]:
        """加载组件模板。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        return self.load_component(template_path)
    
    def export_component(self, component: ComponentBase) -> str:
        """导出组件为JSON字符串。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        component_data = self.serialize_component(component)
        return json.dumps(component_data, indent=2, ensure_ascii=False)
    
    def import_component(self, json_str: str) -> Optional[ComponentBase]:
        """从JSON字符串导入组件。

        
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
            component_data = json.loads(json_str)
            return self.deserialize_component(component_data)
        except Exception as e:
            self._log_error("导入组件", e)
            return None

