#!/usr/bin/env python3
"""
AI生命体环境存档管理器
"""

import os
import json
import numpy as np
from typing import Dict, List, Optional, Any
from .environment import Environment


class EnvironmentArchiveManager:
    """环境存档管理器 - 负责环境的保存和加载
    
    提供环境存档的创建、加载、删除和列表查询功能。
    """
    
    def __init__(self, archive_dir: str = "env_archives"):
        """初始化环境存档管理器
        
        参数:
            archive_dir: str - 存档目录路径，默认为"env_archives"
        """
        self.archive_dir = archive_dir
        # 确保存档目录存在
        if not os.path.exists(self.archive_dir):
            os.makedirs(self.archive_dir)
    
    def save_environment(self, env: Environment, name: str, description: str = "") -> str:
        """保存环境到存档
        
        参数:
            env: Environment - 要保存的环境对象
            name: str - 存档名称
            description: str - 存档描述
        
        返回:
            str - 存档文件路径
        """
        
        def process_position(pos: Any) -> List[float]:
            """处理位置数据，转换为统一的列表格式"""
            position_data: List[float] = [0.0, 0.0]
            
            if isinstance(pos, np.ndarray):
                # 处理numpy数组格式
                try:
                    np_list: List[Any] = pos.tolist()
                    if len(np_list) >= 2:
                        # 确保np_list[0]和np_list[1]是数值类型
                        if isinstance(np_list[0], (int, float)) and isinstance(np_list[1], (int, float)):
                            position_data = [float(np_list[0]), float(np_list[1])]
                except (AttributeError, ValueError, IndexError):
                    pass  # 跳过无效数据
            elif isinstance(pos, (list, tuple)):
                # 处理列表和元组格式
                try:
                    # 确保pos至少有2个元素
                    if len(pos) >= 2:  # type: ignore
                        # 类型转换时添加显式类型检查
                        if isinstance(pos[0], (int, float, str)) and isinstance(pos[1], (int, float, str)):  # type: ignore
                            x = float(pos[0])  # type: ignore
                            y = float(pos[1])  # type: ignore
                            position_data = [x, y]
                except (TypeError, ValueError, IndexError):
                    pass  # 跳过无效数据
            elif isinstance(pos, dict):
                # 处理字典格式
                try:
                    # 确保'x'和'y'键存在且值为数值类型
                    x = pos.get('x')  # type: ignore
                    y = pos.get('y')  # type: ignore
                    if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                        position_data = [float(x), float(y)]
                except (TypeError, ValueError):
                    pass  # 跳过无效数据
            
            return position_data
        
        # 构建存档数据
        archive_data: Dict[str, Any] = {
            "name": name,
            "description": description,
            "foods": [],
            "light_sources": [],
            "obstacles": []
        }
        
        # 处理食物数据
        if hasattr(env, 'foods'):
            foods = getattr(env, 'foods', [])
            for food in foods:
                if isinstance(food, dict) and 'position' in food and 'energy' in food:
                    # 明确类型转换
                    energy_value = food['energy']  # type: ignore
                    food_energy = float(energy_value) if isinstance(energy_value, (int, float)) else 10.0
                    position_data = process_position(food['position'])
                    
                    archive_data['foods'].append({
                        "position": position_data,
                        "energy": food_energy
                    })
        
        # 处理光源数据
        if hasattr(env, 'light_sources'):
            light_sources = getattr(env, 'light_sources', [])
            for light in light_sources:
                if isinstance(light, dict) and 'position' in light and 'intensity' in light:
                    # 明确类型转换
                    intensity_value = light['intensity']  # type: ignore
                    light_intensity = float(intensity_value) if isinstance(intensity_value, (int, float)) else 100.0
                    position_data = process_position(light['position'])
                    
                    archive_data['light_sources'].append({
                        "position": position_data,
                        "intensity": light_intensity
                    })
        
        # 处理障碍物数据
        if hasattr(env, 'obstacles'):
            obstacles = getattr(env, 'obstacles', [])
            for obstacle in obstacles:
                if isinstance(obstacle, dict) and 'position' in obstacle and 'radius' in obstacle:
                    # 明确类型转换
                    radius_value = obstacle['radius']  # type: ignore
                    obstacle_radius = float(radius_value) if isinstance(radius_value, (int, float)) else 15.0
                    position_data = process_position(obstacle['position'])
                    
                    archive_data['obstacles'].append({
                        "position": position_data,
                        "radius": obstacle_radius
                    })
        
        # 构建存档文件名
        filename = f"{name.replace(' ', '_').lower()}.json"
        filepath = os.path.join(self.archive_dir, filename)
        
        # 保存到文件
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(archive_data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def load_environment(self, filename: str) -> Optional[Environment]:
        """从存档加载环境
        
        参数:
            filename: str - 存档文件名
        
        返回:
            Optional[Environment] - 加载的环境对象，加载失败返回None
        """
        filepath = os.path.join(self.archive_dir, filename)
        
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                archive_data = json.load(f)
            
            # 创建环境对象
            env = Environment()
            
            # 加载食物
            for food_data in archive_data["foods"]:
                env.add_food(tuple(food_data["position"]))
            
            # 加载光源
            for light_data in archive_data["light_sources"]:
                env.add_light_source(
                    tuple(light_data["position"]),
                    light_data["intensity"]
                )
            
            # 加载障碍物
            for obstacle_data in archive_data["obstacles"]:
                env.add_obstacle(
                    tuple(obstacle_data["position"]),
                    obstacle_data["radius"]
                )
            
            return env
        except Exception as e:
            print(f"加载环境存档失败: {e}")
            return None
    
    def list_archives(self) -> List[Dict[str, str]]:
        """列出所有环境存档
        
        返回:
            List[Dict[str, str]] - 存档列表，每个元素包含name和file字段
        """
        archives: List[Dict[str, str]] = []
        
        if not os.path.exists(self.archive_dir):
            return archives
        
        # 遍历存档目录
        for filename in os.listdir(self.archive_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.archive_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        archive_data: Dict[str, Any] = json.load(f)
                    archives.append({
                        "name": archive_data["name"],
                        "file": filename,
                        "description": archive_data.get("description", "")
                    })
                except Exception as e:
                    print(f"读取存档文件 {filename} 失败: {e}")
        
        return archives
    
    def delete_archive(self, filename: str) -> bool:
        """删除环境存档
        
        参数:
            filename: str - 存档文件名
        
        返回:
            bool - 删除成功返回True，否则返回False
        """
        filepath = os.path.join(self.archive_dir, filename)
        
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                return True
            except Exception as e:
                print(f"删除存档文件 {filename} 失败: {e}")
                return False
        
        return False
    
    def create_new_environment(self) -> Environment:
        """创建新环境
        
        返回:
            Environment - 新创建的环境对象
        """
        return Environment()
