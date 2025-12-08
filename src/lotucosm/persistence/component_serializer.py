"""组件序列化器实现"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from vitalloom.components.components_base import ComponentBase


class ComponentSerializer:
    """组件序列化器 - 负责组件的序列化和反序列化
    
    负责：
    1. 组件完整序列化
    2. 组件反序列化
    3. 组件模板管理
    """
    
    def __init__(self, save_format: str = "json"):
        """初始化组件序列化器
        
        参数:
            save_format: str - 保存格式（目前仅支持json）
        """
        self.save_format = save_format
        self.version = "1.0"  # 序列化版本
    
    def serialize_component(self, component: ComponentBase) -> Dict[str, Any]:
        """序列化组件
        
        参数:
            component: ComponentBase - 组件实例
        
        返回:
            Dict[str, Any] - 序列化后的组件数据
        """
        # 基本信息
        component_data: Dict[str, Any] = {
            "version": self.version,
            "type": type(component).__name__,
            "id": component.id,
            "name": component.name,
            "timestamp": datetime.now().isoformat(),
            "location": component.location,
            "congenital": component.congenital,
            "acquired": component.acquired,
            "attach_point": component.attach_point,
            "energy_consumption": component.energy_consumption
        }
        
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
            # 检查并添加记忆容量，只有当属性存在时才添加
        
        return component_data
    
    def deserialize_component(self, component_data: Dict[str, Any]) -> Optional[ComponentBase]:
        """反序列化组件
        
        参数:
            component_data: Dict[str, Any] - 序列化后的组件数据
        
        返回:
            Optional[ComponentBase] - 反序列化后的组件实例，如果失败返回None
        """
        try:
            # 导入需要的类
            from vitalloom.components.components_base import ComponentBase
            from vitalloom.components.sensors import Sensor
            from vitalloom.components.actuators import Actuator
            from vitalloom.components.hybrid import HybridComponent
            from vitalloom.components.membrane import Membrane
            from vitalloom.components.PVAECEngine import PVAECEngine
            
            # 根据类型创建组件实例
            component_type = component_data["type"]
            
            if component_type == "Sensor":
                component = Sensor(
                    component_id=component_data["id"],
                    organism_id="",
                    name=component_data["name"]
                )
            elif component_type == "Actuator":
                component = Actuator(
                    component_id=component_data["id"],
                    organism_id="",
                    name=component_data["name"]
                )
            elif component_type == "HybridComponent":
                component = HybridComponent(
                    component_id=component_data["id"],
                    organism_id="",
                    name=component_data["name"]
                )
            elif component_type == "Membrane":
                component = Membrane(
                    component_id=component_data["id"],
                    organism_id="",
                    name=component_data["name"]
                )
            elif component_type == "PVAECEngine":
                component = PVAECEngine(
                    component_id=component_data["id"],
                    organism_id="",
                    name=component_data["name"]
                )
            else:
                # 默认创建基础组件
                component = ComponentBase(
                    component_id=component_data["id"],
                    organism_id="",
                    name=component_data["name"]
                )
            
            # 恢复基本属性
            component.location = component_data["location"]
            component.congenital = component_data["congenital"]
            component.acquired = component_data["acquired"]
            component.attach_point = component_data["attach_point"]
            component.energy_consumption = component_data["energy_consumption"]
            
            # 恢复特定属性
            if component_data.get("is_sensor", False):
                component.is_sensor = True
                if "sensor_sensitivity" in component_data:
                    component.sensor_sensitivity = component_data["sensor_sensitivity"]
                if "sense_range" in component_data:
                    component.sense_range = component_data["sense_range"]
                # 检查并恢复传感器类型，只有当属性存在时才恢复
            
            if component_data.get("is_actuator", False):
                component.is_actuator = True
                if "actuator_strength" in component_data:
                    component.actuator_strength = component_data["actuator_strength"]
                if "actuation_speed" in component_data:
                    component.actuation_speed = component_data["actuation_speed"]
                # 检查并恢复执行器类型，只有当属性存在时才恢复
            
            if component_data.get("is_hybrid", False):
                component.is_hybrid = True
                if "mode" in component_data:
                    component.mode = component_data["mode"]
                if "sensor_sensitivity" in component_data:
                    component.sensor_sensitivity = component_data["sensor_sensitivity"]
                if "actuator_strength" in component_data:
                    component.actuator_strength = component_data["actuator_strength"]
            
            if component_data.get("is_membrane", False):
                component.is_membrane = True
                if "permeability" in component_data:
                    component.permeability = component_data["permeability"]
                if "thickness" in component_data:
                    component.thickness = component_data["thickness"]
                if "surface_area" in component_data:
                    component.surface_area = component_data["surface_area"]
            
            if component_data.get("is_pvaec_engine", False):
                component.is_pvaec_engine = True
                if "learning_rate" in component_data:
                    component.learning_rate = component_data["learning_rate"]
                if "exploration_rate" in component_data:
                    component.exploration_rate = component_data["exploration_rate"]
                # 检查并恢复记忆容量，只有当属性存在时才恢复
            
            return component
        except Exception as e:
            print(f"反序列化组件失败: {e}")
            return None
    
    def save_component(self, component: ComponentBase, file_path: str) -> bool:
        """保存组件到文件
        
        参数:
            component: ComponentBase - 组件实例
            file_path: str - 文件路径
        
        返回:
            bool - 是否保存成功
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
            print(f"保存组件失败: {e}")
            return False
    
    def load_component(self, file_path: str) -> Optional[ComponentBase]:
        """从文件加载组件
        
        参数:
            file_path: str - 文件路径
        
        返回:
            Optional[ComponentBase] - 加载的组件实例，如果失败返回None
        """
        try:
            # 读取文件
            with open(file_path, "r", encoding="utf-8") as f:
                component_data = json.load(f)
            
            # 反序列化组件
            component = self.deserialize_component(component_data)
            
            return component
        except Exception as e:
            print(f"加载组件失败: {e}")
            return None
    
    def save_component_template(self, component: ComponentBase, save_path: str, template_name: str) -> Optional[str]:
        """保存组件为模板
        
        参数:
            component: ComponentBase - 组件实例
            save_path: str - 保存路径
            template_name: str - 模板名称
        
        返回:
            Optional[str] - 保存的文件路径，如果失败返回None
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
            print(f"保存组件模板失败: {e}")
            return None
    
    def load_component_template(self, template_path: str) -> Optional[ComponentBase]:
        """加载组件模板
        
        参数:
            template_path: str - 模板文件路径
        
        返回:
            Optional[ComponentBase] - 加载的组件实例，如果失败返回None
        """
        return self.load_component(template_path)
    
    def export_component(self, component: ComponentBase) -> str:
        """导出组件为JSON字符串
        
        参数:
            component: ComponentBase - 组件实例
        
        返回:
            str - JSON格式的组件数据
        """
        component_data = self.serialize_component(component)
        return json.dumps(component_data, indent=2, ensure_ascii=False)
    
    def import_component(self, json_str: str) -> Optional[ComponentBase]:
        """从JSON字符串导入组件
        
        参数:
            json_str: str - JSON格式的组件数据
        
        返回:
            Optional[ComponentBase] - 导入的组件实例，如果失败返回None
        """
        try:
            component_data = json.loads(json_str)
            return self.deserialize_component(component_data)
        except Exception as e:
            print(f"导入组件失败: {e}")
            return None