# -*- coding: utf-8 -*-
"""记忆编辑业务逻辑（非 Dock）：查看/编辑/导入导出 MemoryGene。

排错: UI 见 docks/memory_editor.py；字段契约见 Lotucosm memory 模块。
"""

from typing import List, Dict, Any, Optional

from core.VitaLoom.core.logger import get_logger
from core.VitaLoom.core.editor_context import get_editor_context


logger = get_logger("MemoryEditor")

class MemoryEditor:
    """职责: 记忆 CRUD 与模板导入导出（供 MemoryEditorWidget 调用）。
    时机: 选中带 memory 组件的实体后由 Dock 触发。
    不变量: 修改须经 CommandStack 的 Memory*Command 以保持撤销。
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

    def list_memories(self) -> List[Any]:

        """

        查看生物体的记忆结构

        返回:

        - List[Any]: 记忆列表

        """

        if not self.memory_system or not hasattr(self.memory_system, 'memories'):

            return []

        return self.memory_system.memories

    def edit_memory(self, memory_id: str, situation: Optional[str] = None, 

                   action_pattern: Optional[Dict[str, float]] = None, 

                   success_rate: Optional[float] = None) -> bool:

        """

        编辑记忆内容

        参数:

        - memory_id: 记忆ID

        - situation: 新的情境（可选）

        - action_pattern: 新的行动模式（可选）

        - success_rate: 新的成功率（可选）

        返回:

        - bool: 编辑是否成功

        """

        if not self.memory_system or not hasattr(self.memory_system, 'memories'):

            return False

        for memory in self.memory_system.memories:

            # MemoryGene 类没有 id 属性，这里应该使用其他方式标识记忆

            # 暂时使用情境作为标识，因为记忆基因的主要标识是情境

            if memory.situation == memory_id:

                # 更新记忆内容

                if situation is not None:

                    memory.situation = situation

                if action_pattern is not None:

                    memory.action_pattern = action_pattern

                if success_rate is not None:

                    memory.success_rate = success_rate

                return True

        return False

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

        if not self.memory_system or not hasattr(self.memory_system, 'store'):

            return False

        try:

            with open(file_path, 'r', encoding='utf-8') as f:

                memory_data = json.load(f)

            # 存储导入的记忆

            self.memory_system.store(memory_data)

            return True

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
            pass
        return default or key
