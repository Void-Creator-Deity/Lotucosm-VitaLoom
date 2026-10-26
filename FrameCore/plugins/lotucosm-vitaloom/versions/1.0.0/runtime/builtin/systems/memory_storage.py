"""PS 生物体记忆持久化辅助（与 core MemorySystem 协同）。

排错: 见 `builtin/README.md`、`lotucosm_core_troubleshooting.md`。
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from core.Lotucosm.memory import MemoryGene
from core.VitaLoom.core.logger import get_logger

logger = get_logger("MemoryStorage")


class MemoryStorage:
    """记忆存储系统 - 负责记忆的持久化存储
    
    负责：
    1. 记忆完整存储
    2. 记忆检索
    3. 记忆模板管理
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
        """统一日志前缀，方便批量排查系统问题。"""
        logger.warning("[System:MemoryStorage] %s失败: %s", action, error)

    def _require_fields(self, data: Dict[str, Any], fields: list[str], context: str):
        missing = [field for field in fields if field not in data]
        if missing:
            raise ValueError(f"{context}缺少字段: {', '.join(missing)}")
    
    def serialize_memory(self, memory: MemoryGene) -> Dict[str, Any]:
        """序列化记忆。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        return {
            "version": self.version,
            "situation": memory.situation,
            "action_pattern": memory.action_pattern,
            "success_rate": memory.success_rate,
            "strength": memory.strength,
            "age": memory.age,
            "timestamp": datetime.now().isoformat()
        }
    
    def deserialize_memory(self, memory_data: Dict[str, Any]) -> MemoryGene:
        """反序列化记忆。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self._require_fields(memory_data, ["situation", "action_pattern", "success_rate"], "memory_data")
        memory = MemoryGene(
            situation=memory_data["situation"],
            action_pattern=memory_data["action_pattern"],
            success_rate=memory_data["success_rate"]
        )
        
        # 恢复其他属性
        if "strength" in memory_data:
            memory.strength = memory_data["strength"]
        if "age" in memory_data:
            memory.age = memory_data["age"]
        
        return memory
    
    def save_memory(self, memory: MemoryGene, file_path: str) -> bool:
        """保存单个记忆到文件。

        
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
            
            # 序列化记忆
            memory_data = self.serialize_memory(memory)
            
            # 保存到文件
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(memory_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            self._log_error("保存记忆", e)
            return False
    
    def load_memory(self, file_path: str) -> Optional[MemoryGene]:
        """从文件加载单个记忆。

        
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
                memory_data = json.load(f)
            
            # 反序列化记忆
            memory = self.deserialize_memory(memory_data)
            
            return memory
        except Exception as e:
            self._log_error("加载记忆", e)
            return None
    
    def save_memories(self, memories: List[MemoryGene], file_path: str) -> bool:
        """保存记忆列表到文件。

        
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
            
            # 序列化所有记忆
            memories_data: Dict[str, Any] = {
                "version": self.version,
                "timestamp": datetime.now().isoformat(),
                "memories": [self.serialize_memory(memory) for memory in memories]
            }
            
            # 保存到文件
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(memories_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            self._log_error("保存记忆列表", e)
            return False
    
    def load_memories(self, file_path: str) -> Optional[List[MemoryGene]]:
        """从文件加载记忆列表。

        
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
                memories_data = json.load(f)
            
            self._require_fields(memories_data, ["memories"], "memories_data")
            # 反序列化所有记忆
            memories = [self.deserialize_memory(memory_data) for memory_data in memories_data["memories"]]
            
            return memories
        except Exception as e:
            self._log_error("加载记忆列表", e)
            return None
    
    def save_memory_template(self, memories: List[MemoryGene], save_path: str, template_name: str) -> Optional[str]:
        """保存记忆列表为模板。

        
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
            
            # 保存记忆列表
            success = self.save_memories(memories, file_path)
            
            if success:
                return file_path
            else:
                return None
        except Exception as e:
            self._log_error("保存记忆模板", e)
            return None
    
    def load_memory_template(self, template_path: str) -> Optional[List[MemoryGene]]:
        """加载记忆模板。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        return self.load_memories(template_path)
    
    def export_memories(self, memories: List[MemoryGene]) -> str:
        """导出记忆列表为JSON字符串。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        memories_data: Dict[str, Any] = {
            "version": self.version,
            "timestamp": datetime.now().isoformat(),
            "memories": [self.serialize_memory(memory) for memory in memories]
        }
        
        return json.dumps(memories_data, indent=2, ensure_ascii=False)
    
    def import_memories(self, json_str: str) -> Optional[List[MemoryGene]]:
        """从JSON字符串导入记忆列表。

        
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
            memories_data = json.loads(json_str)
            self._require_fields(memories_data, ["memories"], "memories_data")
            memories = [self.deserialize_memory(memory_data) for memory_data in memories_data["memories"]]
            return memories
        except Exception as e:
            self._log_error("导入记忆列表", e)
            return None
    
    def filter_memories_by_strength(self, memories: List[MemoryGene], min_strength: float = 0.5) -> List[MemoryGene]:
        """根据强度过滤记忆。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        return [memory for memory in memories if memory.strength >= min_strength]
    
    def sort_memories_by_success_rate(self, memories: List[MemoryGene], reverse: bool = True) -> List[MemoryGene]:
        """根据成功率排序记忆。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        return sorted(memories, key=lambda x: x.success_rate, reverse=reverse)
    
    def get_memory_stats(self, memories: List[MemoryGene]) -> Dict[str, float]:
        """获取记忆统计信息。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if not memories:
            return {
                "count": 0,
                "avg_strength": 0.0,
                "avg_success_rate": 0.0,
                "avg_age": 0.0,
                "max_strength": 0.0,
                "max_success_rate": 0.0
            }
        
        return {
            "count": len(memories),
            "avg_strength": sum(m.strength for m in memories) / len(memories),
            "avg_success_rate": sum(m.success_rate for m in memories) / len(memories),
            "avg_age": sum(m.age for m in memories) / len(memories),
            "max_strength": max(m.strength for m in memories),
            "max_success_rate": max(m.success_rate for m in memories)
        }