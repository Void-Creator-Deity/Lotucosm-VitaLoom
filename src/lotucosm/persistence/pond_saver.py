"""莲池保存系统实现"""

import os
import shutil
from typing import Optional
from lotucosm.environment.lotus_pond import LotusPond
from lotucosm.environment.pond_serializer import PondSerializer


class PondSaver:
    """莲池保存系统 - 负责莲池的存档管理
    
    负责：
    1. 莲池完整保存
    2. 增量保存
    3. 存档版本管理
    """
    
    def __init__(self, save_format: str = "json"):
        """初始化莲池保存系统
        
        参数:
            save_format: str - 保存格式（json或pickle）
        """
        self.serializer = PondSerializer(save_format=save_format)
        self.save_interval = 1000  # 默认每1000步保存一次
    
    def save_pond(self, pond: LotusPond, save_path: str, increment: bool = False) -> Optional[str]:
        """保存莲池
        
        参数:
            pond: LotusPond - 莲池实例
            save_path: str - 保存路径
            increment: bool - 是否为增量保存
        
        返回:
            Optional[str] - 保存的文件路径，如果保存失败返回None
        """
        try:
            # 确保保存目录存在
            os.makedirs(save_path, exist_ok=True)
            
            # 生成文件名
            if increment:
                # 增量保存，使用迭代次数作为文件名
                file_name = f"snapshot_{pond.iteration:06d}.{self.serializer.save_format}"
            else:
                # 完整保存，使用"config"作为文件名
                file_name = f"config.{self.serializer.save_format}"
            
            file_path = os.path.join(save_path, file_name)
            
            # 序列化并保存莲池
            success = self.serializer.save_pond(pond, file_path)
            
            if success:
                return file_path
            else:
                return None
        except Exception as e:
            print(f"保存莲池失败: {e}")
            return None
    
    def load_pond(self, load_path: str, pond_class: type = LotusPond) -> Optional[LotusPond]:
        """加载莲池
        
        参数:
            load_path: str - 加载路径
            pond_class: type - 莲池类（默认为LotusPond）
        
        返回:
            Optional[LotusPond] - 加载的莲池实例，如果加载失败返回None
        """
        try:
            # 检查路径是否存在
            if not os.path.exists(load_path):
                print(f"加载路径不存在: {load_path}")
                return None
            
            # 检查是文件还是目录
            if os.path.isfile(load_path):
                # 直接加载文件
                return self.serializer.load_pond(load_path, pond_class)
            elif os.path.isdir(load_path):
                # 目录，查找配置文件
                config_files: list[tuple[str, str]] = []
                for ext in ["json", "pickle"]:
                    config_file = os.path.join(load_path, f"config.{ext}")
                    if os.path.exists(config_file):
                        config_files.append((config_file, ext))
                
                if config_files:
                    # 选择最新的配置文件
                    config_files.sort(key=lambda x: os.path.getmtime(x[0]), reverse=True)
                    config_file, ext = config_files[0]
                    # 临时更改序列化器的保存格式
                    original_format = self.serializer.save_format
                    self.serializer.save_format = ext
                    pond = self.serializer.load_pond(config_file, pond_class)
                    # 恢复原始格式
                    self.serializer.save_format = original_format
                    return pond
                else:
                    print(f"在目录中未找到配置文件: {load_path}")
                    return None
            else:
                print(f"无效的加载路径: {load_path}")
                return None
        except Exception as e:
            print(f"加载莲池失败: {e}")
            return None
    
    def create_backup(self, pond_path: str, backup_path: str) -> bool:
        """创建莲池存档备份
        
        参数:
            pond_path: str - 莲池存档路径
            backup_path: str - 备份路径
        
        返回:
            bool - 是否备份成功
        """
        try:
            # 创建备份目录
            os.makedirs(backup_path, exist_ok=True)
            
            # 复制整个存档目录
            shutil.copytree(pond_path, backup_path, dirs_exist_ok=True)
            
            return True
        except Exception as e:
            print(f"创建备份失败: {e}")
            return False
    
    def list_snapshots(self, pond_path: str) -> list[str]:
        """列出莲池的所有快照
        
        参数:
            pond_path: str - 莲池存档路径
        
        返回:
            list[str] - 快照文件列表，按迭代次数排序
        """
        snapshots: list[tuple[int, str]] = []
        
        if not os.path.exists(pond_path):
            return []
        
        # 遍历目录，查找快照文件
        for file_name in os.listdir(pond_path):
            if file_name.startswith("snapshot_"):
                # 提取迭代次数
                try:
                    iteration = int(file_name.split("_")[1].split(".")[0])
                    snapshots.append((iteration, file_name))
                except ValueError:
                    continue
        
        # 按迭代次数排序
        snapshots.sort(key=lambda x: x[0])
        
        return [file_name for _, file_name in snapshots]
    
    def load_snapshot(self, pond_path: str, snapshot_name: str, pond_class: type = LotusPond) -> Optional[LotusPond]:
        """加载特定快照
        
        参数:
            pond_path: str - 莲池存档路径
            snapshot_name: str - 快照文件名
            pond_class: type - 莲池类（默认为LotusPond）
        
        返回:
            Optional[LotusPond] - 加载的莲池实例，如果加载失败返回None
        """
        snapshot_path = os.path.join(pond_path, snapshot_name)
        return self.serializer.load_pond(snapshot_path, pond_class)
    
    def delete_snapshot(self, pond_path: str, snapshot_name: str) -> bool:
        """删除快照
        
        参数:
            pond_path: str - 莲池存档路径
            snapshot_name: str - 快照文件名
        
        返回:
            bool - 是否删除成功
        """
        try:
            snapshot_path = os.path.join(pond_path, snapshot_name)
            if os.path.exists(snapshot_path):
                os.remove(snapshot_path)
                return True
            else:
                return False
        except Exception as e:
            print(f"删除快照失败: {e}")
            return False
    
    def set_save_interval(self, interval: int):
        """设置自动保存间隔
        
        参数:
            interval: int - 保存间隔（迭代次数）
        """
        if interval > 0:
            self.save_interval = interval
    
    def should_save(self, iteration: int) -> bool:
        """判断是否应该保存
        
        参数:
            iteration: int - 当前迭代次数
        
        返回:
            bool - 是否应该保存
        """
        return iteration % self.save_interval == 0