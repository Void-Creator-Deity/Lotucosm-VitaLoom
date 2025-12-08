"""记忆存储系统实现"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from vitalloom.core.memory import MemoryGene


class MemoryStorage:
    """记忆存储系统 - 负责记忆的持久化存储
    
    负责：
    1. 记忆完整存储
    2. 记忆检索
    3. 记忆模板管理
    """
    
    def __init__(self, save_format: str = "json"):
        """初始化记忆存储系统
        
        参数:
            save_format: str - 保存格式（目前仅支持json）
        """
        self.save_format = save_format
        self.version = "1.0"  # 序列化版本
    
    def serialize_memory(self, memory: MemoryGene) -> Dict[str, Any]:
        """序列化记忆
        
        参数:
            memory: MemoryGene - 记忆实例
        
        返回:
            Dict[str, Any] - 序列化后的记忆数据
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
        """反序列化记忆
        
        参数:
            memory_data: Dict[str, Any] - 序列化后的记忆数据
        
        返回:
            MemoryGene - 反序列化后的记忆实例
        """
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
        """保存单个记忆到文件
        
        参数:
            memory: MemoryGene - 记忆实例
            file_path: str - 文件路径
        
        返回:
            bool - 是否保存成功
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
            print(f"保存记忆失败: {e}")
            return False
    
    def load_memory(self, file_path: str) -> Optional[MemoryGene]:
        """从文件加载单个记忆
        
        参数:
            file_path: str - 文件路径
        
        返回:
            Optional[MemoryGene] - 加载的记忆实例，如果失败返回None
        """
        try:
            # 读取文件
            with open(file_path, "r", encoding="utf-8") as f:
                memory_data = json.load(f)
            
            # 反序列化记忆
            memory = self.deserialize_memory(memory_data)
            
            return memory
        except Exception as e:
            print(f"加载记忆失败: {e}")
            return None
    
    def save_memories(self, memories: List[MemoryGene], file_path: str) -> bool:
        """保存记忆列表到文件
        
        参数:
            memories: List[MemoryGene] - 记忆列表
            file_path: str - 文件路径
        
        返回:
            bool - 是否保存成功
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
            print(f"保存记忆列表失败: {e}")
            return False
    
    def load_memories(self, file_path: str) -> Optional[List[MemoryGene]]:
        """从文件加载记忆列表
        
        参数:
            file_path: str - 文件路径
        
        返回:
            Optional[List[MemoryGene]] - 加载的记忆列表，如果失败返回None
        """
        try:
            # 读取文件
            with open(file_path, "r", encoding="utf-8") as f:
                memories_data = json.load(f)
            
            # 反序列化所有记忆
            memories = [self.deserialize_memory(memory_data) for memory_data in memories_data["memories"]]
            
            return memories
        except Exception as e:
            print(f"加载记忆列表失败: {e}")
            return None
    
    def save_memory_template(self, memories: List[MemoryGene], save_path: str, template_name: str) -> Optional[str]:
        """保存记忆列表为模板
        
        参数:
            memories: List[MemoryGene] - 记忆列表
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
            
            # 保存记忆列表
            success = self.save_memories(memories, file_path)
            
            if success:
                return file_path
            else:
                return None
        except Exception as e:
            print(f"保存记忆模板失败: {e}")
            return None
    
    def load_memory_template(self, template_path: str) -> Optional[List[MemoryGene]]:
        """加载记忆模板
        
        参数:
            template_path: str - 模板文件路径
        
        返回:
            Optional[List[MemoryGene]] - 加载的记忆列表，如果失败返回None
        """
        return self.load_memories(template_path)
    
    def export_memories(self, memories: List[MemoryGene]) -> str:
        """导出记忆列表为JSON字符串
        
        参数:
            memories: List[MemoryGene] - 记忆列表
        
        返回:
            str - JSON格式的记忆数据
        """
        memories_data: Dict[str, Any] = {
            "version": self.version,
            "timestamp": datetime.now().isoformat(),
            "memories": [self.serialize_memory(memory) for memory in memories]
        }
        
        return json.dumps(memories_data, indent=2, ensure_ascii=False)
    
    def import_memories(self, json_str: str) -> Optional[List[MemoryGene]]:
        """从JSON字符串导入记忆列表
        
        参数:
            json_str: str - JSON格式的记忆数据
        
        返回:
            Optional[List[MemoryGene]] - 导入的记忆列表，如果失败返回None
        """
        try:
            memories_data = json.loads(json_str)
            memories = [self.deserialize_memory(memory_data) for memory_data in memories_data["memories"]]
            return memories
        except Exception as e:
            print(f"导入记忆列表失败: {e}")
            return None
    
    def filter_memories_by_strength(self, memories: List[MemoryGene], min_strength: float = 0.5) -> List[MemoryGene]:
        """根据强度过滤记忆
        
        参数:
            memories: List[MemoryGene] - 记忆列表
            min_strength: float - 最小强度阈值
        
        返回:
            List[MemoryGene] - 过滤后的记忆列表
        """
        return [memory for memory in memories if memory.strength >= min_strength]
    
    def sort_memories_by_success_rate(self, memories: List[MemoryGene], reverse: bool = True) -> List[MemoryGene]:
        """根据成功率排序记忆
        
        参数:
            memories: List[MemoryGene] - 记忆列表
            reverse: bool - 是否降序排序
        
        返回:
            List[MemoryGene] - 排序后的记忆列表
        """
        return sorted(memories, key=lambda x: x.success_rate, reverse=reverse)
    
    def get_memory_stats(self, memories: List[MemoryGene]) -> Dict[str, float]:
        """获取记忆统计信息
        
        参数:
            memories: List[MemoryGene] - 记忆列表
        
        返回:
            Dict[str, float] - 统计信息字典
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