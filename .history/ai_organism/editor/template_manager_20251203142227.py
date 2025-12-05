"""模板管理器 - 用于保存、加载和管理生物模板"""

import json
import os
from typing import Dict, Any, List


class TemplateManager:
    """生物模板管理器"""
    def __init__(self, template_dir: str = "templates"):
        self.template_dir = template_dir
        self.templates: Dict[str, Dict[str, Any]] = {}
        self.preset_templates: Dict[str, Dict[str, Any]] = {}
        
        # 确保模板目录存在
        os.makedirs(self.template_dir, exist_ok=True)
        
        # 加载现有模板
        self.load_templates()
        
        # 初始化预设模板
        self.initialize_preset_templates()
    
    def initialize_preset_templates(self):
        """初始化预设模板"""
        # 基础生物模板
        self.preset_templates["basic_organism"] = {
            "name": "基础生物",
            "description": "具有基本感知和行动能力的简单生物",
            "type": "preset",
            "data": {
                "nodes": [
                    {"id": "organism_1", "type": "organism", "x": 300, "y": 200},
                    {"id": "sensor_1", "type": "sensor", "x": 200, "y": 150},
                    {"id": "sensor_2", "type": "sensor", "x": 400, "y": 150},
                    {"id": "actuator_1", "type": "actuator", "x": 200, "y": 250},
                    {"id": "actuator_2", "type": "actuator", "x": 400, "y": 250}
                ],
                "connections": [
                    {"start_node": "sensor_1", "end_node": "organism_1"},
                    {"start_node": "sensor_2", "end_node": "organism_1"},
                    {"start_node": "organism_1", "end_node": "actuator_1"},
                    {"start_node": "organism_1", "end_node": "actuator_2"}
                ]
            }
        }
        
        # 传感器丰富的生物模板
        self.preset_templates["sensor_rich_organism"] = {
            "name": "传感器丰富生物",
            "description": "具有多种传感器的复杂生物",
            "type": "preset",
            "data": {
                "nodes": [
                    {"id": "organism_1", "type": "organism", "x": 300, "y": 200},
                    {"id": "sensor_1", "type": "sensor", "x": 200, "y": 150},
                    {"id": "sensor_2", "type": "sensor", "x": 400, "y": 150},
                    {"id": "sensor_3", "type": "sensor", "x": 200, "y": 250},
                    {"id": "sensor_4", "type": "sensor", "x": 400, "y": 250},
                    {"id": "actuator_1", "type": "actuator", "x": 250, "y": 300},
                    {"id": "actuator_2", "type": "actuator", "x": 350, "y": 300}
                ],
                "connections": [
                    {"start_node": "sensor_1", "end_node": "organism_1"},
                    {"start_node": "sensor_2", "end_node": "organism_1"},
                    {"start_node": "sensor_3", "end_node": "organism_1"},
                    {"start_node": "sensor_4", "end_node": "organism_1"},
                    {"start_node": "organism_1", "end_node": "actuator_1"},
                    {"start_node": "organism_1", "end_node": "actuator_2"}
                ]
            }
        }
        
        # 效应器丰富的生物模板
        self.preset_templates["actuator_rich_organism"] = {
            "name": "效应器丰富生物",
            "description": "具有多种行动能力的复杂生物",
            "type": "preset",
            "data": {
                "nodes": [
                    {"id": "organism_1", "type": "organism", "x": 300, "y": 200},
                    {"id": "sensor_1", "type": "sensor", "x": 200, "y": 150},
                    {"id": "sensor_2", "type": "sensor", "x": 400, "y": 150},
                    {"id": "actuator_1", "type": "actuator", "x": 200, "y": 250},
                    {"id": "actuator_2", "type": "actuator", "x": 400, "y": 250},
                    {"id": "actuator_3", "type": "actuator", "x": 250, "y": 300},
                    {"id": "actuator_4", "type": "actuator", "x": 350, "y": 300}
                ],
                "connections": [
                    {"start_node": "sensor_1", "end_node": "organism_1"},
                    {"start_node": "sensor_2", "end_node": "organism_1"},
                    {"start_node": "organism_1", "end_node": "actuator_1"},
                    {"start_node": "organism_1", "end_node": "actuator_2"},
                    {"start_node": "organism_1", "end_node": "actuator_3"},
                    {"start_node": "organism_1", "end_node": "actuator_4"}
                ]
            }
        }
    
    def load_templates(self):
        """加载所有模板"""
        self.templates.clear()
        
        # 遍历模板目录
        for filename in os.listdir(self.template_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.template_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        template_data = json.load(f)
                        template_id = os.path.splitext(filename)[0]
                        self.templates[template_id] = template_data
                except Exception as e:
                    print(f"加载模板失败 {filename}: {e}")
    
    def save_template(self, template_id: str, name: str, description: str, data: Dict[str, Any]) -> bool:
        """保存模板"""
        try:
            template = {
                "name": name,
                "description": description,
                "type": "custom",
                "created_at": os.path.getmtime(__file__),
                "data": data
            }
            
            # 保存到字典
            self.templates[template_id] = template
            
            # 保存到文件
            filepath = os.path.join(self.template_dir, f"{template_id}.json")
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(template, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"保存模板失败 {template_id}: {e}")
            return False
    
    def load_template(self, template_id: str) -> Dict[str, Any]:
        """加载模板"""
        # 首先检查自定义模板
        if template_id in self.templates:
            return self.templates[template_id]
        
        # 检查预设模板
        if template_id in self.preset_templates:
            return self.preset_templates[template_id]
        
        raise ValueError(f"模板不存在: {template_id}")
    
    def delete_template(self, template_id: str) -> bool:
        """删除模板"""
        if template_id in self.templates:
            try:
                filepath = os.path.join(self.template_dir, f"{template_id}.json")
                if os.path.exists(filepath):
                    os.remove(filepath)
                
                del self.templates[template_id]
                return True
            except Exception as e:
                print(f"删除模板失败 {template_id}: {e}")
        
        return False
    
    def get_all_templates(self) -> List[Dict[str, Any]]:
        """获取所有模板（包括预设和自定义）"""
        all_templates = []
        
        # 添加预设模板
        for template_id, template in self.preset_templates.items():
            template_copy = template.copy()
            template_copy["id"] = template_id
            all_templates.append(template_copy)
        
        # 添加自定义模板
        for template_id, template in self.templates.items():
            template_copy = template.copy()
            template_copy["id"] = template_id
            all_templates.append(template_copy)
        
        return all_templates
    
    def export_template(self, template_id: str, export_path: str) -> bool:
        """导出模板到指定路径"""
        try:
            template = self.load_template(template_id)
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(template, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"导出模板失败 {template_id}: {e}")
            return False
    
    def import_template(self, import_path: str) -> str:
        """从指定路径导入模板"""
        try:
            with open(import_path, "r", encoding="utf-8") as f:
                template_data = json.load(f)
            
            # 生成模板ID
            import_name = os.path.splitext(os.path.basename(import_path))[0]
            template_id = f"imported_{import_name}"
            
            # 确保模板ID唯一
            counter = 1
            original_id = template_id
            while template_id in self.templates:
                template_id = f"{original_id}_{counter}"
                counter += 1
            
            # 保存模板
            self.templates[template_id] = template_data
            
            # 保存到文件
            filepath = os.path.join(self.template_dir, f"{template_id}.json")
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(template_data, f, ensure_ascii=False, indent=2)
            
            return template_id
        except Exception as e:
            print(f"导入模板失败 {import_path}: {e}")
            raise
    
    def create_template_from_organism(self, organism_data: Dict[str, Any], name: str, description: str) -> str:
        """从生物数据创建模板"""
        # 生成模板ID
        template_id = name.lower().replace(" ", "_")
        
        # 确保模板ID唯一
        counter = 1
        original_id = template_id
        while template_id in self.templates:
            template_id = f"{original_id}_{counter}"
            counter += 1
        
        # 保存模板
        self.save_template(template_id, name, description, organism_data)
        
        return template_id
