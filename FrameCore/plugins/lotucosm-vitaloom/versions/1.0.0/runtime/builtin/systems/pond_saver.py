"""PS 莲池存档门面：封装 PondSerializer 路径与触发时机。

排错: 见 `builtin/README.md`。
"""

import os
import shutil
from typing import Optional, Any

from core.Lotucosm.pond import Pond
from builtin.systems.pond_serializer import PondSerializer
from core.VitaLoom.core.logger import get_logger

logger = get_logger("PondSaver")


class PondSaver:
    """莲池保存系统 - 负责莲池的存档管理
    
    负责：
    1. 莲池完整保存
    2. 增量保存
    3. 存档版本管理
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
        self.serializer = PondSerializer(save_format=save_format)
        self.save_interval = 1000  # 默认每1000步保存一次

    def _log_error(self, action: str, error: Exception):
        logger.warning("[System:PondSaver] %s失败: %s", action, error)

    def _log_info(self, message: str):
        logger.info("[System:PondSaver] %s", message)
    
    def save_pond(self, pond: Any, save_path: str, increment: bool = False) -> Optional[str]:
        """保存莲池。

        
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
            self._log_error("保存莲池", e)
            return None
    
    def load_pond(self, load_path: str, pond_class: type = Pond) -> Optional[Any]:
        """加载莲池。

        
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
            # 检查路径是否存在
            if not os.path.exists(load_path):
                self._log_info(f"加载路径不存在: {load_path}")
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
                    try:
                        self.serializer.save_format = ext
                        return self.serializer.load_pond(config_file, pond_class)
                    finally:
                        # 确保格式在异常场景也能恢复
                        self.serializer.save_format = original_format
                else:
                    self._log_info(f"在目录中未找到配置文件: {load_path}")
                    return None
            else:
                self._log_info(f"无效的加载路径: {load_path}")
                return None
        except Exception as e:
            self._log_error("加载莲池", e)
            return None
    
    def create_backup(self, pond_path: str, backup_path: str) -> bool:
        """创建莲池存档备份。

        
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
            if not os.path.isdir(pond_path):
                self._log_info(f"源存档目录不存在或不是目录: {pond_path}")
                return False
            # 创建备份目录
            os.makedirs(backup_path, exist_ok=True)
            
            # 复制整个存档目录
            shutil.copytree(pond_path, backup_path, dirs_exist_ok=True)
            
            return True
        except Exception as e:
            self._log_error("创建备份", e)
            return False
    
    def list_snapshots(self, pond_path: str) -> list[str]:
        """列出莲池的所有快照。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        snapshots: list[tuple[int, str]] = []
        
        if not os.path.isdir(pond_path):
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
    
    def load_snapshot(self, pond_path: str, snapshot_name: str, pond_class: type = Pond) -> Optional[Any]:
        """加载特定快照。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if not snapshot_name.startswith("snapshot_"):
            self._log_info(f"非法快照名称: {snapshot_name}")
            return None
        snapshot_path = os.path.join(pond_path, snapshot_name)
        if not os.path.isfile(snapshot_path):
            self._log_info(f"快照文件不存在: {snapshot_path}")
            return None
        return self.serializer.load_pond(snapshot_path, pond_class)
    
    def delete_snapshot(self, pond_path: str, snapshot_name: str) -> bool:
        """删除快照。

        
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
            if not snapshot_name.startswith("snapshot_"):
                self._log_info(f"拒绝删除非法快照名称: {snapshot_name}")
                return False
            snapshot_path = os.path.join(pond_path, snapshot_name)
            if os.path.isfile(snapshot_path):
                os.remove(snapshot_path)
                return True
            else:
                return False
        except Exception as e:
            self._log_error("删除快照", e)
            return False
    
    def set_save_interval(self, interval: int):
        """设置自动保存间隔。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if interval > 0:
            self.save_interval = interval
    
    def should_save(self, iteration: int) -> bool:
        """判断是否应该保存。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        return iteration % self.save_interval == 0