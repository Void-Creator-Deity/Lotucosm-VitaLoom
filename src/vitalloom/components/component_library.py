import json
import os
from typing import Dict, List, Type, Any
from .components_base import ComponentBase

class ComponentLibrary:
    """
    组件库管理器，负责：
    1. 加载和管理组件模板
    2. 注册和查找组件类
    3. 提供组件实例化服务
    """

    def __init__(self):
        """初始化组件库"""
        self.component_templates: Dict[str, Dict[str, Any]] = {}  # {组件类型: 模板数据}
        self.component_classes: Dict[str, Type[ComponentBase]] = {}  # {组件类型: 组件类}
        self.template_dir = "data/components/"  # 组件模板目录

        # 加载组件模板
        self.load_component_templates()

    def load_component_templates(self):
        """
        加载组件模板
        """
        # 遍历组件模板目录
        try:
            for root, _, files in os.walk(self.template_dir):
                for file in files:
                    if file.endswith('.json'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                template = json.load(f)
                                component_type = template.get('type', '').lower()
                                if component_type:
                                    self.component_templates[component_type] = template
                        except Exception as e:
                            print(f"加载组件模板失败 {file_path}: {e}")
        except FileNotFoundError:
            # 如果目录不存在，跳过加载模板
            print(f"组件模板目录 {self.template_dir} 不存在，跳过加载模板")

    def register_component_class(self, component_class: Type[ComponentBase]):
        """
        注册组件类

        参数:
        - component_class: 组件类
        """
        component_type = component_class.__name__.lower()
        self.component_classes[component_type] = component_class

    def get_component_template(self, component_type: str) -> Dict[str, Any]:
        """
        获取组件模板

        参数:
        - component_type: 组件类型

        返回:
        - Dict[str, Any]: 组件模板数据
        """
        return self.component_templates.get(component_type, {})

    def create_component(self, component_type: str, component_id: str, organism_id: str, **kwargs: Any) -> ComponentBase:
        """
        创建组件实例

        参数:
        - component_type: 组件类型
        - component_id: 组件ID
        - organism_id: 所属生物体ID
        - kwargs: 其他参数

        返回:
        - ComponentBase: 组件实例
        """
        # 获取组件类
        component_class = self.component_classes.get(component_type)
        if not component_class:
            raise ValueError(f"未知组件类型: {component_type}")

        # 获取组件模板
        template = self.get_component_template(component_type)

        # 合并模板参数和传入参数
        params = template.copy()
        params.update(kwargs)

        # 创建组件实例
        return component_class(component_id, organism_id, **params)

    def list_available_components(self) -> List[str]:
        """
        列出可用组件类型

        返回:
        - List[str]: 可用组件类型列表
        """
        return list(self.component_classes.keys())

    def save_component_template(self, component_type: str, template: Dict[str, Any]):
        """
        保存组件模板

        参数:
        - component_type: 组件类型
        - template: 模板数据

        返回:
        - bool: 保存是否成功
        """
        # 确定模板文件路径
        if component_type.startswith('sensor'):
            subdir = 'sensors'
        elif component_type.startswith('actuator'):
            subdir = 'actuators'
        elif component_type.startswith('hybrid'):
            subdir = 'hybrids'
        else:
            subdir = 'special'

        file_path = os.path.join(self.template_dir, subdir, f"{component_type}.json")

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=2, ensure_ascii=False)

            # 更新内存中的模板
            self.component_templates[component_type] = template
            return True
        except Exception as e:
            print(f"保存组件模板失败 {file_path}: {e}")
            return False
