# -*- coding: utf-8 -*-
"""演化版中枢 PVAEC：代谢、摄食、繁殖与膜通道增益（SR 专用）。

趋食路径:
    中枢 think **不**读 nutrient 梯度（无 GPS 直指食物）；
    膜 sensor → chemo 边 → actuator → 宿主耦合推 hub；
    本脚本仅通过 ent.sr_chemo_gain_scale 放大膜受体输出强度。

繁殖:
    登记 organism_with_membrane；**勿**在 req 内塞 DEFAULT_MEMBRANE_TEMPLATE，
    由宿主 _sr_membrane_template 解析场景；边权传 parent_signal_edges + parent_hub_id。
    宿主流水线见 GameViewport._process_organism_with_membrane_spawn 注释。
"""
from __future__ import annotations

import math
from typing import Any, Dict, Mapping, Optional

from core.Lotucosm.runtime.world_bridge_sr_runtime_randomness import (
    create_detached_sr_entity_randomness_rng,
)
from core.Lotucosm.scene_runtime_context import SceneRuntimeTickContext
import sys
from pathlib import Path

_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from central_brain_pvaec import CentralBrainPvaec
from core.Lotucosm.sr_mind_gene import format_gene_deltas, mind_dict_mutate, resolve_gene_keys
from core.VitaLoom.core.logger import get_logger

logger = get_logger("MainWorld.EvoCentralBrainPvaec")

# Editor-only：VitaLoom Inspector 可选读取，分组展示心智 / 演化等嵌套参数。
SR_INSPECTOR_SCHEMA = [
    {"group": "心智", "label": "漫游幅度", "path": "mind.wander_amp", "type": "float", "min": 0.0, "max": 50.0, "step": 0.1},
    {"group": "心智", "label": "低应激增益", "path": "mind.gain_low_stress", "type": "float", "min": 0.0, "max": 80.0, "step": 0.5},
    {"group": "心智", "label": "高应激增益", "path": "mind.gain_high_stress", "type": "float", "min": 0.0, "max": 80.0, "step": 0.5},
    {"group": "心智", "label": "记忆平滑 α", "path": "mind.mem_alpha", "type": "float", "min": 0.0, "max": 1.0, "step": 0.01},
    {"group": "心智", "label": "最大速度", "path": "mind.max_speed", "type": "float", "min": 10.0, "max": 600.0, "step": 1.0},
    {"group": "初始", "label": "初始能量", "path": "initial_energy", "type": "float", "min": 1.0, "max": 500.0, "step": 1.0},
    {"group": "初始", "label": "初始速度阻尼", "path": "initial_velocity_damp", "type": "float", "min": 0.0, "max": 1.0, "step": 0.05},
    {"group": "调试", "label": "日志间隔帧", "path": "log_every", "type": "int", "min": 0, "max": 600, "step": 1},
    {"group": "演化", "label": "繁殖能量阈值", "path": "evo.reproduce_energy", "type": "float", "min": 10.0, "max": 400.0, "step": 1.0},
    {"group": "演化", "label": "繁殖冷却(秒)", "path": "evo.reproduce_cooldown", "type": "float", "min": 0.5, "max": 60.0, "step": 0.1},
    {"group": "演化", "label": "突变 σ", "path": "evo.mutation_sigma", "type": "float", "min": 0.0, "max": 2.0, "step": 0.01},
    {"group": "演化", "label": "记忆衰减", "path": "evo.mem_decay", "type": "float", "min": 0.0, "max": 2.0, "step": 0.05},
    {"group": "演化", "label": "基础代谢", "path": "evo.base_metabolism", "type": "float", "min": 0.1, "max": 50.0, "step": 0.1},
    {"group": "演化", "label": "速度代价系数", "path": "evo.speed_cost", "type": "float", "min": 0.0, "max": 1.0, "step": 0.001},
    {"group": "演化", "label": "生态位代价", "path": "evo.niche_cost", "type": "float", "min": 0.0, "max": 100.0, "step": 0.5},
    {"group": "演化", "label": "场摄取系数", "path": "evo.feed_from_field", "type": "float", "min": 0.0, "max": 0.001, "step": 1e-6},
    {"group": "演化", "label": "井旁增益", "path": "evo.well_proximity_feed", "type": "float", "min": 0.0, "max": 50.0, "step": 0.5},
    {"group": "演化", "label": "趋化增益", "path": "evo.chemo_gain", "type": "float", "min": 0.0, "max": 200.0, "step": 1.0},
    {"group": "演化", "label": "趋化最大距离", "path": "evo.chemo_max_dist", "type": "float", "min": 50.0, "max": 2000.0, "step": 10.0},
    {"group": "演化", "label": "单次噬咬能量", "path": "evo.eat_energy_per_bite", "type": "float", "min": 1.0, "max": 200.0, "step": 1.0},
]


class EvoCentralBrainPvaec(CentralBrainPvaec):
    """在 CentralBrainPvaec 之上增加代谢、趋食、繁殖与 HUD 世代信息。"""

    homeostatic_pvaec_enabled = True

    def __init__(self) -> None:
        """EvoCentralBrainPvaec.__init__。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        super().__init__()
        self._evo_rng = None
        self._evo_rng_mode = "unbound"
        self._repro_acc = 0.0
        self._spawn_capability_warned = False
        self._spawn_list_warned = False
        self._chemo_max_dist = 420.0

    def start(self) -> None:
        """EvoCentralBrainPvaec.start。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        super().start()
        props = getattr(self, "_scene_script_properties", None) or {}
        ent = self.entity
        if ent is not None:
            owner = getattr(self, "randomness_rng", None)
            if owner is not None and callable(getattr(owner, "random", None)):
                self._evo_rng = owner
                self._evo_rng_mode = "runtime"
            else:
                # Manual/headless construction remains deterministic and is
                # explicitly detached from the runtime owner graph.
                position = getattr(ent, "position", (0.0, 0.0))
                self._evo_rng = create_detached_sr_entity_randomness_rng(
                    getattr(ent, "id", "detached_evo_entity"),
                    getattr(ent, "entity_type", "organism"),
                    (float(position[0]), float(position[1])),
                    float(getattr(ent, "radius", 22.0)),
                )
                self._evo_rng_mode = "detached"
            if getattr(ent, "energy", None) is None:
                try:
                    ent.energy = float(props.get("initial_energy", 110.0))
                except (TypeError, ValueError):
                    ent.energy = 110.0
            if not hasattr(ent, "generation"):
                ent.generation = 0
            vel = getattr(ent, "velocity", None)
            if isinstance(vel, (list, tuple)) and len(vel) >= 2:
                damp = float(props.get("initial_velocity_damp", 0.0) or 0.0)
                if damp >= 1.0:
                    ent.velocity[0] = 0.0
                    ent.velocity[1] = 0.0
                elif damp > 0:
                    ent.velocity[0] *= 1.0 - damp
                    ent.velocity[1] *= 1.0 - damp
        evo = props.get("evo") if isinstance(props.get("evo"), dict) else {}
        self._repro_energy = float(evo.get("reproduce_energy", 128.0))
        self._repro_cooldown = float(evo.get("reproduce_cooldown", 4.5))
        self._mutation_sigma = float(evo.get("mutation_sigma", 0.38))
        self._mem_decay = float(evo.get("mem_decay", 0.35))
        self._base_metabolism = float(evo.get("base_metabolism", 5.2))
        self._speed_cost = float(evo.get("speed_cost", 0.014))
        self._niche_cost = float(evo.get("niche_cost", 24.0))
        self._feed_from_field = float(evo.get("feed_from_field", 0.000022))
        self._well_feed = float(evo.get("well_proximity_feed", 9.0))
        self._well_reach = float(evo.get("well_reach_scale", 1.35))
        self._chemo_gain = float(evo.get("chemo_gain", 42.0))
        self._chemo_max_dist = float(evo.get("chemo_max_dist", 420.0))
        self._eat_energy = float(evo.get("eat_energy_per_bite", 38.0))

        im = props.get("initial_memory")
        if isinstance(im, dict):
            for k in ("stress_ema", "field_ema", "speed_ema"):
                if k in im:
                    try:
                        self._memory[k] = float(im[k])
                    except (TypeError, ValueError):
                        pass
        from core.Lotucosm.sr_memory_gene_bridge import load_sr_memory_genes_from_props

        load_sr_memory_genes_from_props(ent, props)

    def perceive(self, ctx: SceneRuntimeTickContext) -> Dict[str, Any]:
        """EvoCentralBrainPvaec.perceive。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        return super().perceive(ctx)

    def think(self, observation: Dict[str, Any], delta_time: float) -> Dict[str, Any]:
        return super().think(observation, delta_time)

    def remember(
        self,
        ctx: SceneRuntimeTickContext,
        observation: Dict[str, Any],
        decision: Dict[str, Any],
        success: float,
    ) -> None:
        super().remember(ctx, observation, decision, success)
        ent = self.entity
        if ent is not None:
            try:
                e_now = float(getattr(ent, "energy", 0.0))
                e_was = float(getattr(self, "_evo_energy_before_act", e_now))
                if e_now > e_was:
                    boost = min(1.0, success + (e_now - e_was) / 40.0)
                    ent._sr_last_verify_success = boost
            except (TypeError, ValueError):
                pass

    def act(self, decision: Dict[str, Any], delta_time: float) -> None:
        """EvoCentralBrainPvaec.act。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        ent = self.entity
        if ent is not None and getattr(ent, "energy", None) is not None:
            try:
                self._evo_energy_before_act = float(ent.energy)
            except (TypeError, ValueError):
                self._evo_energy_before_act = 0.0
        super().act(decision, delta_time)
        ent = self.entity
        ctx = getattr(self, "_pvaec_tick_ctx", None)
        obs = getattr(self, "_pvaec_last_observation", None)
        if ent is None or delta_time <= 0 or not isinstance(obs, dict):
            return
        if getattr(ent, "energy", None) is None:
            return

        caps: Mapping[str, Any] = getattr(ctx, "capabilities", {}) if ctx is not None else {}
        if not bool(caps.get("dynamic_spawn", False)) and not self._spawn_capability_warned:
            logger.error(
                "【SR 演化】当前运行环境未声明 dynamic_spawn 能力，动态繁殖将被跳过。"
                "请使用支持 spawn_requests 的游戏视口宿主。"
            )
            self._spawn_capability_warned = True

        niche = float(obs.get("niche_pressure", 0.0))
        field = float(obs.get("ambient_field", 0.0))
        vel = getattr(ent, "velocity", None)
        if isinstance(vel, (list, tuple)) and len(vel) >= 2:
            speed = math.hypot(float(vel[0]), float(vel[1]))
        else:
            speed = float(obs.get("intrinsic_speed", 0.0))

        well_bonus = 0.0
        if ctx is not None:
            px, py = float(ent.position[0]), float(ent.position[1])
            r0 = float(getattr(ent, "radius", 18.0))
            for p in ctx.peers:
                if p.entity_type != "environment_well":
                    continue
                wx, wy = p.position
                d = math.hypot(px - wx, py - wy) + 1e-6
                rr = (p.radius + r0) * self._well_reach
                if d < rr * 3.5:
                    well_bonus += self._well_feed * max(0.0, 1.0 - d / (rr * 3.5)) * delta_time

        # 代谢须乘 delta_time；starter_scale 仅作用于 drain，不减弱场摄取（前 18s 易积能）
        sim_t = float(obs.get("simulation_time", 0.0))
        starter_scale = 0.55 if sim_t < 18.0 else 1.0
        drain = (
            self._base_metabolism * (1.0 + niche * self._niche_cost / 100.0)
            + self._speed_cost * speed * (1.0 + 0.55 * niche)
        ) * delta_time * starter_scale
        gain = self._feed_from_field * max(0.0, field) * delta_time + well_bonus
        ent.energy = float(ent.energy) - drain + gain

        self._try_eat_nutrients(ctx, ent)

        self._repro_acc += delta_time
        if (
            ent.energy >= self._repro_energy
            and self._repro_acc >= self._repro_cooldown
            and ctx is not None
        ):
            self._try_reproduce(ctx, ent)

        hud = getattr(ent, "sr_debug_hud", None)
        try:
            stress_norm = abs(float(decision.get("stress_norm", 0.0)))
        except (TypeError, ValueError):
            stress_norm = 0.0
        scale = 0.85 + 0.35 * (1.0 - min(1.0, stress_norm))
        scale *= 0.75 + 0.25 * min(1.0, float(self._chemo_gain) / 42.0)
        ent.sr_chemo_gain_scale = max(0.35, min(2.2, scale))

        if isinstance(hud, dict):
            hud["energy"] = float(ent.energy)
            hud["generation"] = int(getattr(ent, "generation", 0))
            hud["niche_pressure"] = niche
            hud["chemo_gain_scale"] = float(ent.sr_chemo_gain_scale)

    def _try_eat_nutrients(self, ctx: Optional[SceneRuntimeTickContext], ent: Any) -> None:
        if ctx is None:
            return
        removal = getattr(ctx, "removal_requests", None)
        if removal is None:
            return
        if not hasattr(removal, "append"):
            if not self._spawn_list_warned:
                logger.error("【SR 演化】removal_requests 不可用（非列表），无法吞噬营养颗粒。")
                self._spawn_list_warned = True
            return
        r0 = float(getattr(ent, "radius", 18.0))
        px, py = float(ent.position[0]), float(ent.position[1])
        for p in ctx.peers:
            if p.entity_type != "nutrient":
                continue
            touch = float(p.distance) <= r0 + float(p.radius) + 4.0
            if not touch:
                continue
            if p.id in removal:
                continue
            removal.append(str(p.id))
            ent.energy = float(ent.energy) + self._eat_energy
            logger.info(
                "[摄食] 已吞噬营养颗粒 id=%s，能量 +%.1f（当前 %.1f）",
                p.id,
                self._eat_energy,
                float(ent.energy),
            )

    def _try_reproduce(self, ctx: SceneRuntimeTickContext, ent: Any) -> None:
        """登记带膜子代 spawn 请求。

        职责: membrane_spawn_spec + parent_signal_edges；template 交由宿主。
        不变量: 须 dynamic_spawn；亲本能量须 >= reproduce_energy + organelle_birth_cost。
        排错: 子代边权全同 → 查宿主是否仍对 chemo 边做均值覆盖；
        子代膜与场景不符 → 勿恢复脚本内 DEFAULT_MEMBRANE_TEMPLATE。
        """
        spawn_requests = getattr(ctx, "spawn_requests", None)
        if spawn_requests is None:
            if not self._spawn_list_warned:
                logger.error("【SR 演化】spawn_requests 不可用，无法繁殖。")
                self._spawn_list_warned = True
            return
        if not hasattr(spawn_requests, "append"):
            if not self._spawn_list_warned:
                logger.error("【SR 演化】spawn_requests 非列表，无法 append，繁殖已跳过。")
                self._spawn_list_warned = True
            return
        _caps = getattr(ctx, "capabilities", None) or {}
        if not bool(_caps.get("dynamic_spawn", False)):
            return

        props = getattr(self, "_scene_script_properties", None) or {}
        base = self._mind.to_dict()
        from core.Lotucosm.evolution_profile import resolve_sr_reproduction_rates
        from core.Lotucosm.sr_memory_gene_bridge import (
            inherit_sr_memory_genes,
            memory_genes_to_dicts,
        )
        from core.Lotucosm.social_memory import inherit_social_sr_memory_genes, is_social_memory_gene
        from core.Lotucosm.sr_navigation_body import navigation_state_to_props

        evo_cfg = props.get("evo") if isinstance(props.get("evo"), dict) else {}
        evo_profile = resolve_sr_reproduction_rates(evo_cfg)
        gene_keys = resolve_gene_keys(evo_profile.gene_keys)
        parent_genes = {k: float(base[k]) for k in gene_keys if k in base}
        child_genes, deltas = mind_dict_mutate(
            parent_genes,
            evo_profile.mutation_sigma,
            self._evo_rng,
            gene_keys=gene_keys,
        )
        child_mind = {**base, **child_genes}
        decay = max(0.0, min(1.0, self._mem_decay))
        child_initial_memory = {k: float(self._memory[k]) * (1.0 - decay) for k in self._memory}

        mem_inherit_rate = evo_profile.memory_gene_inheritance_rate
        mem_mut_rate = evo_profile.memory_gene_mutation_rate
        self._mutation_sigma = evo_profile.mutation_sigma
        parent_sr_genes = getattr(ent, "sr_memory_genes", None) or []
        if not isinstance(parent_sr_genes, list):
            parent_sr_genes = []
        non_social_genes = [g for g in parent_sr_genes if not is_social_memory_gene(g)]
        social_genes = [g for g in parent_sr_genes if is_social_memory_gene(g)]
        child_memory_genes = inherit_sr_memory_genes(
            non_social_genes,
            inheritance_rate=mem_inherit_rate,
            mutation_rate=mem_mut_rate,
            rng=self._evo_rng,
        )
        child_memory_genes.extend(
            inherit_social_sr_memory_genes(social_genes, rng=self._evo_rng)
        )
        child_memory_genes = child_memory_genes[:32]
        child_navigation = navigation_state_to_props(ent)

        from core.Lotucosm.sr_membrane_topology import membrane_spawn_spec
        try:
            birth_cost = float(evo_cfg.get("organelle_birth_cost", 20.0))
        except (TypeError, ValueError):
            birth_cost = 20.0

        energy_before = float(ent.energy)
        if energy_before < self._repro_energy + birth_cost:
            return
        ent.energy = energy_before * 0.52 - birth_cost
        self._repro_acc = 0.0

        ang = self.random_uniform(0.0, math.tau)
        dist = float(getattr(ent, "radius", 22.0)) * 2.15
        cx = float(ent.position[0]) + math.cos(ang) * dist
        cy = float(ent.position[1]) + math.sin(ang) * dist
        w, h = int(ctx.bounds[0]), int(ctx.bounds[1])
        r = max(14.0, float(getattr(ent, "radius", 22.0)) * 0.9)
        cx = max(r, min(w - r, cx))
        cy = max(r, min(h - r, cy))

        evo_cfg = props.get("evo") if isinstance(props.get("evo"), dict) else {}
        child_props: Dict[str, Any] = {
            "mind": {k: float(child_mind[k]) for k in child_mind},
            "initial_energy": max(35.0, energy_before * 0.28),
            "evo": evo_cfg,
            "log_every": props.get("log_every", 60),
            "initial_memory": child_initial_memory,
            "initial_memory_genes": memory_genes_to_dicts(child_memory_genes),
            "initial_navigation": child_navigation,
            "initial_velocity_damp": 1.0,
            "developmental": {"enabled": True, "initial_stage": 0},
        }
        parent_edges = getattr(ent, "_sr_inherited_signal_edges", None)
        parent_chemo_edges: list[dict] = []
        parent_weights: list[float] = []
        if isinstance(parent_edges, list):
            for edge in parent_edges:
                if isinstance(edge, dict) and str(edge.get("channel", "chemo")) == "chemo":
                    parent_chemo_edges.append(dict(edge))
                    try:
                        parent_weights.append(float(edge.get("weight", 1.0)))
                    except (TypeError, ValueError):
                        pass

        self._sr_spawn_seq_local = int(getattr(self, "_sr_spawn_seq_local", 0)) + 1
        hub_id = f"evo_organism_{getattr(ent, 'id', 'x')}_{self._sr_spawn_seq_local:05d}"

        spawn_req = membrane_spawn_spec(
            hub_id,
            (cx, cy),
            r,
            template=None,
            signal_edges=None,
        )
        # 宿主用场景 sr_membrane_template，禁止携带脚本侧 DEFAULT 模板
        spawn_req.pop("template", None)
        spawn_requests.append(spawn_req)
        spawn_requests[-1]["energy"] = float(child_props["initial_energy"])
        spawn_requests[-1]["generation"] = int(getattr(ent, "generation", 0)) + 1
        spawn_requests[-1]["edge_mutation_sigma"] = float(self._mutation_sigma)
        spawn_requests[-1]["parent_hub_id"] = str(getattr(ent, "id", ""))
        if parent_chemo_edges:
            spawn_requests[-1]["parent_signal_edges"] = parent_chemo_edges
        elif parent_weights:
            spawn_requests[-1]["signal_edge_weights"] = parent_weights
        spawn_requests[-1]["scripts"] = [
            {
                "name": "evo_central_brain_pvaec",
                "type": "EvoCentralBrainPvaec",
                "properties": child_props,
            }
        ]

        gen = int(getattr(ent, "generation", 0)) + 1
        delta_txt = format_gene_deltas(deltas, gene_keys=gene_keys)
        mem_txt = (
            f"stress_ema={child_initial_memory.get('stress_ema', 0.0):.3f} "
            f"field_ema={child_initial_memory.get('field_ema', 0.0):.3f} "
            f"speed_ema={child_initial_memory.get('speed_ema', 0.0):.3f} | "
            f"memory_genes={len(child_memory_genes)}"
        )
        logger.info(
            "[世代 %d] 新个体诞生 | 继承基因: wander_amp=%.2f gain_high_stress=%.2f mem_alpha=%.3f | 突变(%s)",
            gen,
            child_genes.get("wander_amp", 0.0),
            child_genes.get("gain_high_stress", 0.0),
            child_genes.get("mem_alpha", 0.0),
            delta_txt,
        )
        logger.info("[世代 %d] | 继承记忆: %s", gen, mem_txt)
        self.notify_developmental_reproduction()
