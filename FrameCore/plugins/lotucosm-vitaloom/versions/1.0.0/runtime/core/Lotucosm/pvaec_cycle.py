"""通用 PVAEC 六步循环：感知 → 记忆 → 行动 → 执行 → 验证 → 再记忆。

架构数据流::

    organism.update / 模拟器
        → PVAECCycle.run_cycle
        → perceive → retrieve_memories → generate_action → execute_action
        → validate_action → update_memory

与 SR 脚本管线（PvaecScript + SceneRuntimeTickContext）并行存在；legacy 感知走 PerceptionSystem。
"""
from typing import Dict, Any, List
from core.VitaLoom.core.logger import get_logger


logger = get_logger("PVAECCycle")

class PVAECCycle:
    """感知-验证自主演化循环实现（非场景 SR 中枢专用）。"""

    def __init__(self):
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
        self.current_step = 0

    def run_cycle(self, organism: Any, environment: Any) -> bool:
        """运行完整 PVAEC 六步；异常时记录日志并返回 False。

        职责:
            串联 perceive → … → update_memory，并递增 current_step。

        时机:
            智能生物体 update 或专用模拟驱动每逻辑步。

        不变量:
            成功返回 True；任一步异常不部分回滚已写入记忆。

        排错:
            日志「PVAEC循环执行失败」→ 查 organism.components 与 sense/act 签名；见 lotucosm_core_troubleshooting.md。
        """
        try:
            raw_perception = self.perceive(organism, environment)
            from core.Lotucosm.ps_developmental import (
                enrich_ps_perception,
                filter_ps_perception_for_stage,
                gate_ps_generate_action,
                gate_ps_retrieve,
                ps_ladder_enabled,
                track_ps_developmental_after_cycle,
                component_ids,
            )

            perception = enrich_ps_perception(organism, raw_perception, self.current_step)
            if ps_ladder_enabled(organism):
                perception = filter_ps_perception_for_stage(
                    perception,
                    int(getattr(organism, "developmental_stage", 0)),
                    component_ids(organism),
                )

            memories = self.retrieve_memories(organism, perception)
            memories = gate_ps_retrieve(organism, memories)

            action = self.generate_action(organism, memories, perception)
            from core.Lotucosm.social_memory import apply_ps_social_action_bias

            action = apply_ps_social_action_bias(organism, action)
            action = gate_ps_generate_action(organism, action)

            from core.Lotucosm.ps_verify import ps_use_verify_triple, snapshot_pre_act_motion

            if ps_use_verify_triple(organism):
                snapshot_pre_act_motion(organism)

            result = self.execute_action(organism, environment, action)

            raw_after = self.perceive(organism, environment)
            new_perception = enrich_ps_perception(organism, raw_after, self.current_step)
            if ps_ladder_enabled(organism):
                new_perception = filter_ps_perception_for_stage(
                    new_perception,
                    int(getattr(organism, "developmental_stage", 0)),
                    component_ids(organism),
                )
            success = self.validate_action(organism, perception, new_perception, action, result)

            self.update_memory(organism, perception, action, result, success, new_perception)

            from core.Lotucosm.social_memory import maybe_record_peer_from_environment

            maybe_record_peer_from_environment(organism, environment, action, success)

            track_ps_developmental_after_cycle(
                organism,
                success=success,
                action=action,
                remember_written=True,
                environment=environment,
            )

            self.current_step += 1
            return True
        except Exception as e:
            logger.error("PVAEC循环执行失败: %s", e)
            return False

    def perceive(self, organism: Any, environment: Any) -> Dict[str, Any]:
        """聚合各组件 sense 结果；可选 legacy 噪声融合。

        职责:
            收集 component.sense 输出为 {component_id: data} flat dict。

        时机:
            run_cycle 首尾各一次（验证用第二次感知）。

        不变量:
            use_legacy_perception_pipeline 为 True 时走 PerceptionSystem 缓存实例。

        排错:
            空 dict → 无 sense 方法或 components 非 dict-like；TypeError 时已尝试单参 sense。
        """
        perception: Dict[str, Any] = {}
        # 收集所有传感器的感知结果
        if hasattr(organism, 'components'):
            components = getattr(organism, 'components', {})
            if hasattr(components, 'values'):
                for component in components.values():
                    if hasattr(component, 'sense'):
                        try:
                            sense_result = component.sense(environment, organism)
                        except TypeError:
                            sense_result = component.sense(environment)
                        perception[component.id] = sense_result

        if getattr(organism, "use_legacy_perception_pipeline", False):
            from core.Lotucosm.perception import PerceptionSystem

            noise = float(getattr(organism, "perception_noise_level", 0.05))
            cache_key = "_perception_system_cache"
            ps: Any = getattr(organism, cache_key, None)
            if not isinstance(ps, PerceptionSystem) or abs(ps.noise_level - noise) > 1e-9:
                ps = PerceptionSystem(
                    noise_level=noise,
                    randomness_rng=getattr(environment, "randomness_rng", None),
                )
                setattr(organism, cache_key, ps)
            elif getattr(environment, "randomness_rng", None) is not None:
                ps.randomness_rng = environment.randomness_rng
            return ps.fuse_flat_sensor_dict(perception)

        return perception

    def retrieve_memories(self, organism: Any, perception: Dict[str, Any]) -> List[Any]:
        """委托 organism.memory_system.retrieve（若存在）。

        职责:
            返回与当前 perception 相关的记忆列表。

        时机:
            run_cycle 感知之后、generate_action 之前。

        不变量:
            无 memory_system 时返回 []。

        排错:
            恒为空 → 检查是否挂载 MemorySystem 及 retrieve 实现。
        """
        if hasattr(organism, 'memory_system') and hasattr(organism.memory_system, 'retrieve'):
            return organism.memory_system.retrieve(perception)
        return []

    def generate_action(self, organism: Any, memories: List[Any], perception: Dict[str, Any]) -> Dict[str, Any]:
        """基于记忆或探索性默认生成 {component_id: action_details}。

        职责:
            有记忆时取 success_rate 最高条的 action_pattern；否则为带 act 的组件生成 explore。

        时机:
            retrieve_memories 之后、execute_action 之前。

        不变量:
            返回 dict，键为组件 id。

        排错:
            空 action → 无记忆且无 act 组件；检查 components 注册。
        """
        action: Dict[str, Any] = {}

        # 1. 如果有记忆，优先基于记忆生成行动
        if memories:
            # 选择成功率最高的记忆
            best_memory = max(memories, key=lambda m: m.success_rate if hasattr(m, 'success_rate') else 0)
            action = best_memory.action_pattern if hasattr(best_memory, 'action_pattern') else {}

        # 2. 否则生成探索性行动
        if not action:
            if hasattr(organism, 'components'):
                components = getattr(organism, 'components', {})
                if hasattr(components, 'values'):
                    for component in components.values():
                        if hasattr(component, 'act'):
                            action[component.id] = {'command': 'explore', 'params': {}}
                        elif hasattr(component, 'process_signal'):
                            action[component.id] = {'signal': 0.35, 'command': 'explore'}

        return action

    def execute_action(self, organism: Any, environment: Any, action: Dict[str, Any]) -> Dict[str, Any]:
        """对 action 中每个 component_id 调用 component.act。

        职责:
            收集 act 返回值为 result dict。

        时机:
            generate_action 之后、validate_action 之前。

        不变量:
            components 须支持 .get(component_id)。

        排错:
            result 为空 → action 键与 components 键不一致或缺少 act。
        """
        result: Dict[str, Any] = {}

        if hasattr(organism, 'components'):
            components = getattr(organism, 'components', {})
            if hasattr(components, 'get'):
                for component_id, action_details in action.items():
                    component = components.get(component_id)
                    if not component:
                        continue
                    if hasattr(component, 'act'):
                        act_result = component.act(environment, organism, action_details)
                        result[component_id] = act_result
                    elif hasattr(component, 'process_signal'):
                        sig = 0.5
                        if isinstance(action_details, dict):
                            sig = float(action_details.get('signal', 0.5))
                        result[component_id] = component.process_signal(sig)

        return result

    def validate_action(self, organism: Any, old_perception: Dict[str, Any], new_perception: Dict[str, Any], action: Dict[str, Any], result: Dict[str, Any]) -> float:
        """验证行动效果：默认 energy/health 启发式；`use_ps_verify_triple` 时走三分 verify。

        职责:
            返回 [0,1] 成功率估计。

        时机:
            第二次 perceive 之后、update_memory 之前。

        不变量:
            三分路径写入 `_ps_verify_components` 与 `_ps_last_verify_success`。

        排错:
            成功率恒 0.5 → 检查 intero_* 是否经 enrich_ps_perception 注入。
        """
        from core.Lotucosm.ps_verify import ps_use_verify_triple, validate_action_legacy, validate_action_triple

        if ps_use_verify_triple(organism):
            return validate_action_triple(
                organism,
                old_perception,
                new_perception,
                action,
                delta_time=float(getattr(organism, "_ps_verify_delta_time", 1.0) or 1.0),
            )
        return validate_action_legacy(organism)

    def update_memory(self, organism: Any, perception: Dict[str, Any], action: Dict[str, Any], result: Dict[str, Any], success: float, new_perception: Dict[str, Any]) -> None:
        """构建 memory_entry 并调用 memory_system.store。

        职责:
            打包 situation/action_pattern/result/success_rate/timestamp。

        时机:
            validate_action 之后、run_cycle 结束前。

        不变量:
            无 memory_system.store 时静默跳过。

        排错:
            记忆不增长 → organism 未绑定 MemorySystem 或 store 未实现。
        """
        if hasattr(organism, 'memory_system') and hasattr(organism.memory_system, 'store'):
            # 构建记忆条目
            memory_entry: Dict[str, Any] = {
                'situation': perception,
                'action_pattern': action,
                'result': result,
                'success_rate': success,
                'timestamp': self.current_step,
                'previous_situation': new_perception
            }

            # 存储记忆
            organism.memory_system.store(memory_entry)
