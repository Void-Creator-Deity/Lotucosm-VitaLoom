# -*- coding: utf-8 -*-
"""记忆编辑业务逻辑（非 Dock）：查看/编辑/导入导出 MemoryGene。

排错: UI 见 docks/memory_editor.py；字段契约见 Lotucosm memory 模块。
"""

from typing import List, Dict, Any, Optional
import json

from core.VitaLoom.core.logger import get_logger
from core.VitaLoom.core.editor_context import get_editor_context
from core.VitaLoom.commands.registry import get_command_registry


logger = get_logger("MemoryEditor")

class MemoryEditor:
    """职责: 记忆 CRUD 与模板导入导出（供 MemoryEditorWidget 调用）。
    时机: 选中带 memory 组件的实体后由 Dock 触发。
    不变量: 修改须经 Qt-free CommandRegistry 的 memory.edit 命令以保持撤销。
    排错: 检索为空 → situation 字符串与 perception 对齐（Lotucosm 子串匹配）。
    """

    def __init__(self, organism: object):

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

        self.organism = organism

        self.memory_system = getattr(organism, 'memory_system', None)
        # Registry history stores a token rather than the Python memory object.
        # Keep bindings alive until the owning editor surface is closed so undo/redo
        # remains available after the edit call returns.
        self._memory_tokens: Dict[int, str] = {}
        self._memory_system_token: Optional[str] = None

    def list_memories(self) -> List[Any]:

        """

        查看生物体的记忆结构

        返回:

        - List[Any]: 记忆列表

        """

        if not self.memory_system or not hasattr(self.memory_system, 'memories'):

            return []

        return self.memory_system.memories

    def _memory_snapshot(self, memory: Any) -> Optional[Dict[str, Any]]:
        """Return the JSON-safe editable fields without mutating ``memory``."""
        try:
            situation = getattr(memory, "situation")
            action_pattern = getattr(memory, "action_pattern")
            success_rate = getattr(memory, "success_rate")
            if not isinstance(action_pattern, dict):
                return None
            return {
                "situation": str(situation),
                "action_pattern": json.loads(json.dumps(action_pattern, ensure_ascii=False, default=str)),
                "success_rate": json.loads(json.dumps(success_rate, ensure_ascii=False, default=str)),
            }
        except (AttributeError, TypeError, ValueError):
            return None

    def _memory_system_binding(self) -> Optional[str]:
        if self.memory_system is None:
            return None
        if self._memory_system_token is None:
            self._memory_system_token = get_command_registry().bind_transient_target(self.memory_system)
        return self._memory_system_token

    def _memory_collection_snapshot(self) -> Optional[List[Dict[str, Any]]]:
        if not self.memory_system or not hasattr(self.memory_system, "memories"):
            return None
        records: List[Dict[str, Any]] = []
        try:
            for memory in self.memory_system.memories:
                action_pattern = getattr(memory, "action_pattern")
                if not isinstance(action_pattern, dict):
                    return None
                records.append(
                    {
                        "situation": str(getattr(memory, "situation")),
                        "action_pattern": json.loads(json.dumps(action_pattern, ensure_ascii=False, default=str)),
                        "success_rate": json.loads(json.dumps(getattr(memory, "success_rate"), ensure_ascii=False, default=str)),
                        "strength": json.loads(json.dumps(getattr(memory, "strength", 1.0), ensure_ascii=False, default=str)),
                        "age": json.loads(json.dumps(getattr(memory, "age", 0), ensure_ascii=False, default=str)),
                    }
                )
        except (AttributeError, TypeError, ValueError):
            return None
        return records


    def _memory_token(self, memory: Any) -> str:
        key = id(memory)
        token = self._memory_tokens.get(key)
        if token is None:
            token = get_command_registry().bind_transient_target(memory)
            self._memory_tokens[key] = token
        return token

    def edit_memory(self, memory_id: str, situation: Optional[str] = None,
                    action_pattern: Optional[Dict[str, float]] = None,
                    success_rate: Optional[float] = None) -> bool:
        """Edit one memory through the shared guarded Registry command.

        ``memory_id`` remains the historical situation-based compatibility
        identifier; the command itself targets the selected object by a transient
        Registry token and stores only JSON-safe snapshots in undo history.
        """
        if not self.memory_system or not hasattr(self.memory_system, "memories"):
            return False
        for memory in self.memory_system.memories:
            if getattr(memory, "situation", None) != memory_id:
                continue
            old_snapshot = self._memory_snapshot(memory)
            if old_snapshot is None:
                return False
            new_snapshot = dict(old_snapshot)
            if situation is not None:
                new_snapshot["situation"] = situation
            if action_pattern is not None:
                new_snapshot["action_pattern"] = action_pattern
            if success_rate is not None:
                new_snapshot["success_rate"] = success_rate
            result = get_command_registry().run(
                "memory.edit",
                {
                    "target_token": self._memory_token(memory),
                    "expected_snapshot": old_snapshot,
                    "snapshot": new_snapshot,
                },
            )
            if not result.get("ok"):
                logger.warning("Memory edit rejected: %s", result.get("error"))
            return bool(result.get("ok"))
        return False

    def close(self) -> None:
        """Release transient bindings owned by this editor surface."""
        registry = get_command_registry()
        for token in self._memory_tokens.values():
            registry.unbind_transient_target(token)
        self._memory_tokens.clear()
        if self._memory_system_token is not None:
            registry.unbind_transient_target(self._memory_system_token)
            self._memory_system_token = None

    def export_memory(self, memory_id: str, file_path: str) -> bool:

        """

        导出记忆为模板

        参数:

        - memory_id: 记忆ID

        - file_path: 导出文件路径

        返回:

        - bool: 导出是否成功

        """

        import json

        for memory in self.list_memories():

            # 使用情境作为记忆标识，因为 MemoryGene 类没有 id 属性

            if memory.situation == memory_id:

                # 转换记忆为可序列化格式

                memory_data: Dict[str, Any] = {

                    'id': memory.situation,  # 使用情境作为唯一标识

                    'situation': memory.situation,

                    'action_pattern': memory.action_pattern,

                    'success_rate': getattr(memory, 'success_rate', 0.5),

                    'timestamp': getattr(memory, 'timestamp', 0)

                }

                try:

                    with open(file_path, 'w', encoding='utf-8') as f:

                        json.dump(memory_data, f, indent=2, ensure_ascii=False)

                    return True

                except Exception as e:
                    logger.warning(
                        self._t("memory_core.export_failed", "导出记忆失败: {error}").format(error=e)
                    )

                    return False

        return False

    def import_memory(self, file_path: str) -> bool:

        """

        导入记忆到生物体

        参数:

        - file_path: 导入文件路径

        返回:

        - bool: 导入是否成功

        """

        import json

        if not self.memory_system or not hasattr(self.memory_system, 'memories'):

            return False

        try:
            with open(file_path, 'r', encoding='utf-8') as f:

                memory_data = json.load(f)
            if not isinstance(memory_data, dict):
                return False
            expected_memories = self._memory_collection_snapshot()
            token = self._memory_system_binding()
            if expected_memories is None or not token:
                return False
            result = get_command_registry().run(
                "memory.store",
                {
                    "target_token": token,
                    "expected_memories": expected_memories,
                    "memory_entry": memory_data,
                },
            )
            if not result.get("ok"):
                logger.warning("Memory import rejected: %s", result.get("error"))
            return bool(result.get("ok"))

        except Exception as e:
            logger.warning(
                self._t("memory_core.import_failed", "导入记忆失败: {error}").format(error=e)
            )
            return False

    def export_organism_template(self, file_path: str) -> bool:

        """

        导出生物体为模板，包括其记忆系统

        参数:

        - file_path: 导出文件路径

        返回:

        - bool: 导出是否成功

        """

        import json

        # 构建生物体模板数据

        organism_data: Dict[str, Any] = {

            'type': self.organism.__class__.__name__,

            'id': getattr(self.organism, 'id', 'unknown'),

            'components': [],

            'memories': []

        }

        # 添加组件数据，确保 organism 有 components 属性

        if hasattr(self.organism, 'components'):

            components = getattr(self.organism, 'components', {})

            organism_data['components'] = [{    'type': component.__class__.__name__,

                'id': component.id,

                'location': getattr(component, 'location', 'internal'),

                'congenital': getattr(component, 'congenital', True)

            } for component in components.values()] if hasattr(components, 'values') else []

        # 添加记忆数据

        for memory in self.list_memories():

            memory_data: Dict[str, Any] = {

                'id': memory.situation,  # 使用情境作为唯一标识

                'situation': memory.situation,

                'action_pattern': memory.action_pattern,

                'success_rate': getattr(memory, 'success_rate', 0.5),

                'timestamp': getattr(memory, 'timestamp', 0)

            }

            organism_data['memories'].append(memory_data)

        try:

            with open(file_path, 'w', encoding='utf-8') as f:

                json.dump(organism_data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            logger.warning(
                self._t("memory_core.export_organism_failed", "导出生物体模板失败: {error}").format(error=e)
            )

            return False

    def visualize_memory_network(self, output_path: Optional[str] = None) -> bool:

        """

        可视化记忆关联网络

        参数:

        - output_path: 输出文件路径（可选，若提供则保存可视化结果）

        返回:

        - bool: 可视化是否成功

        """

        # 简单的记忆网络可视化实现

        # 实际项目中可以使用更复杂的可视化库

        memories = self.list_memories()

        if not memories:
            logger.info(self._t("memory_core.visualize.empty", "没有记忆可以可视化"))

            return False

        logger.info(self._t("memory_core.visualize.header", "=== 记忆关联网络 ==="))

        for i, memory in enumerate(memories):

            logger.info(
                self._t("memory_core.visualize.item", "记忆 {index}: {situation}")
                .format(index=i + 1, situation=memory.situation)
            )
            logger.info(
                self._t("memory_core.visualize.situation", "  情境: {situation}")
                .format(situation=memory.situation)
            )
            logger.info(
                self._t("memory_core.visualize.action_pattern", "  行动模式: {pattern}")
                .format(pattern=memory.action_pattern)
            )
            logger.info(
                self._t("memory_core.visualize.success_rate", "  成功率: {rate}")
                .format(rate=getattr(memory, "success_rate", 0.5))
            )

        if output_path:

            # 保存简单的文本可视化

            try:

                with open(output_path, 'w', encoding='utf-8') as f:

                    f.write(self._t("memory_core.visualize.header_file", "=== 记忆关联网络 ===\n\n"))

                    for i, memory in enumerate(memories):

                        f.write(
                            self._t("memory_core.visualize.item_file", "记忆 {index}: {situation}\n")
                            .format(index=i + 1, situation=memory.situation)
                        )
                        f.write(
                            self._t("memory_core.visualize.situation_file", "  情境: {situation}\n")
                            .format(situation=memory.situation)
                        )
                        f.write(
                            self._t("memory_core.visualize.action_pattern_file", "  行动模式: {pattern}\n")
                            .format(pattern=memory.action_pattern)
                        )
                        f.write(
                            self._t("memory_core.visualize.success_rate_file", "  成功率: {rate}\n\n")
                            .format(rate=getattr(memory, "success_rate", 0.5))
                        )

                return True

            except Exception as e:
                logger.warning(
                    self._t("memory_core.visualize.save_failed", "保存可视化结果失败: {error}").format(error=e)
                )

                return False

        return True

    def _t(self, key: str, default: str = "") -> str:
        try:
            ctx = get_editor_context()
            tr_fn = getattr(ctx, "i18n_tr", None)
            if callable(tr_fn):
                return tr_fn(key, default)
        except Exception:
            __import__("logging").getLogger(__name__).debug("Ignored recoverable exception.", exc_info=True)
        return default or key
