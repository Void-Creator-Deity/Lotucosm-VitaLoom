# -*- coding: utf-8 -*-
"""SR 膜拓扑：附着偏移、信号边、繁殖模板与 chemo 通道聚合。

架构数据流（阅读顺序：场景加载 → 每 tick → 繁殖）::

    nutrient_gradient_at
        → sensor 脚本写入 sr_channel_out[chemo, chemo_dir_*]
        → signal_edges（start=sensor, end=actuator, weight）
        → aggregate_channel_signals → actuator 的 inbound_signals
        → actuator 脚本 + 宿主 _apply_actuator_coupling 推动 organism(hub)

膜组件位置由 build_membrane_attachments + 宿主 _sync_membrane_positions 维护，
与 pinned 解耦（膜子实体 membrane_locked，随 hub 刚体平移）。

边权与繁殖流水线（宿主 _process_organism_with_membrane_spawn 须遵守）::

    expand_signal_edges
        → inherit_chemo_edge_weights（或按序 signal_edge_weights 回退）
        → mutate_signal_edges
        → dedupe_signal_edges

历史坑（改代码前先看对应函数的「排错」段）::

    - 同一 (sensor, actuator) 两条 chemo 边会导致 aggregate 双倍趋化（已用 expand 补缺 + dedupe）
    - 对全部 chemo 边写「权重均值」会使 edge_mutation_sigma 失效（已改为 inherit + 最后 mutate）
    - inherit 按排序后的 sensor/actuator 下标映射，勿按实体 ID 字符串硬匹配
"""
from __future__ import annotations

import random
from typing import Any, Dict, List, Mapping, Optional, Tuple

# 与 main_scene.pond 默认拓扑一致：繁殖时宿主 _sr_membrane_template 可覆盖本常量
DEFAULT_MEMBRANE_TEMPLATE: Dict[str, Any] = {
    "sensors": [
        {"suffix": "s1", "dx": 60.0, "dy": -30.0, "radius": 14.0, "script": "sensor_patrol_pvaec"},
        {"suffix": "s2", "dx": -60.0, "dy": -50.0, "radius": 14.0, "script": "sensor_patrol_pvaec"},
        {"suffix": "s3", "dx": -30.0, "dy": 60.0, "radius": 14.0, "script": "sensor_patrol_pvaec"},
    ],
    "actuators": [
        {"suffix": "a1", "dx": 40.0, "dy": 40.0, "radius": 12.0, "script": "actuator_pulse_pvaec"},
        {"suffix": "a2", "dx": -50.0, "dy": 20.0, "radius": 12.0, "script": "actuator_pulse_pvaec"},
    ],
    "default_edge_weight": 1.0,
    "organelle_birth_cost": 20.0,
}


def resolve_membrane_template(scene_data: Any) -> Dict[str, Any]:
    """解析场景级繁殖膜模板。

    职责:
        深拷贝 DEFAULT_MEMBRANE_TEMPLATE，并用 scene_data['sr_membrane_template'] 覆盖字段。

    时机:
        GameViewport._load_scene_runtime_entities 加载 .pond 时写入 _sr_membrane_template；
        繁殖 spawn 未带 template 时宿主用该结果。

    不变量:
        返回 dict 含 sensors/actuators 列表及 organelle_birth_cost、default_edge_weight。

    排错:
        子代膜组件与主场景不一致 → 检查 .pond 是否缺 sr_membrane_template；
        勿在 evo 脚本内写死 DEFAULT_MEMBRANE_TEMPLATE 覆盖场景配置。
    """
    import copy

    tpl = copy.deepcopy(DEFAULT_MEMBRANE_TEMPLATE)
    if not isinstance(scene_data, dict):
        return tpl
    raw = scene_data.get("sr_membrane_template")
    if not isinstance(raw, dict):
        return tpl
    for key in ("organelle_birth_cost", "default_edge_weight"):
        if key in raw:
            try:
                tpl[key] = float(raw[key])
            except (TypeError, ValueError):
                tpl[key] = raw[key]
    for key in ("sensors", "actuators"):
        if isinstance(raw.get(key), list):
            tpl[key] = raw[key]
    return tpl


def parse_weighted_edges(connections: List[Any]) -> List[Dict[str, Any]]:
    """从场景 connections / sr_signal_connections 解析带权边列表。

    职责:
        将 JSON 连接转为统一边 dict：start, end, channel, weight。

    时机:
        加载场景结构边与 sr_signal_connections 显式 chemo 边时。

    不变量:
        缺省 channel='chemo'，weight=1.0；无效项跳过。

    排错:
        边未生效 → 核对 start/end 与实体 id 一致；channel 非 chemo 时聚合通道不同。
    """
    out: List[Dict[str, Any]] = []
    for conn in connections:
        if not isinstance(conn, dict):
            continue
        start_id = conn.get("start", conn.get("start_id", conn.get("from", "")))
        end_id = conn.get("end", conn.get("end_id", conn.get("to", "")))
        if not start_id or not end_id:
            continue
        try:
            weight = float(conn.get("weight", 1.0))
        except (TypeError, ValueError):
            weight = 1.0
        channel = str(conn.get("channel", "chemo"))
        row: Dict[str, Any] = {
            "start": str(start_id),
            "end": str(end_id),
            "channel": channel,
            "weight": weight,
        }
        lk = conn.get("link_kind", conn.get("coupling"))
        if lk is not None:
            row["link_kind"] = str(lk)
        for key in ("stiffness", "damping", "rest_length", "transmission", "mechanical"):
            if key in conn:
                row[key] = conn[key]
        out.append(row)
    return out


def apply_explicit_signal_edges(
    signal_edges: List[Dict[str, Any]],
    explicit: List[Dict[str, Any]],
    entity_ids: Optional[set[str]] = None,
) -> List[Dict[str, Any]]:
    """合并场景 sr_signal_connections 到信号边表。

    职责:
        同键 (start, end, channel) 则覆盖 weight；否则追加新边。

    时机:
        场景加载 expand 之后、dedupe_signal_edges 之前。

    不变量:
        entity_ids 非空时两端 id 均须在集合内。

    排错:
        显式权重被默认值覆盖 → 须在 expand 之后调用本函数，并最终 dedupe；
        历史：expand 隐式边若后写会盖掉显式边，已在 expand 内改为「仅补缺」。
    """
    if not explicit:
        return list(signal_edges)
    out = [dict(e) for e in signal_edges]
    index: Dict[Tuple[str, str, str], int] = {}
    for i, edge in enumerate(out):
        index[_signal_edge_key(edge)] = i
    for ex in explicit:
        if not isinstance(ex, dict):
            continue
        sa = str(ex.get("start", ""))
        sb = str(ex.get("end", ""))
        if not sa or not sb:
            continue
        if entity_ids is not None and (sa not in entity_ids or sb not in entity_ids):
            continue
        ch = str(ex.get("channel", "chemo"))
        try:
            weight = float(ex.get("weight", 1.0))
        except (TypeError, ValueError):
            weight = 1.0
        key = (sa, sb, ch)
        if key in index:
            out[index[key]]["weight"] = weight
        else:
            out.append({"start": sa, "end": sb, "channel": ch, "weight": weight})
            index[key] = len(out) - 1
    return out


def build_membrane_attachments(
    entities: List[Any],
    structural_edges: List[Dict[str, Any]],
) -> Dict[str, Tuple[str, float, float]]:
    """建立膜子实体相对 hub 的附着偏移表。

    职责:
        仅处理 organism—sensor / organism—actuator 结构边，计算 child 相对 parent 的 (dx, dy)。

    时机:
        场景加载与繁殖生成结构边之后；宿主每 tick 用该表同步膜位置。

    不变量:
        返回 child_id -> (parent_organism_id, dx, dy)；子实体 membrane_locked=True, pinned=False。

    排错:
        膜不跟细胞走 → 查宿主 _sync_membrane_positions 与 attach 表是否含该 child；
        子代缺膜组件 → 查繁殖是否走 organism_with_membrane 而非单 organism。
    """
    id_to_type = {str(getattr(e, "id", "")): str(getattr(e, "entity_type", "")) for e in entities}
    id_to_ent = {str(getattr(e, "id", "")): e for e in entities}
    attach: Dict[str, Tuple[str, float, float]] = {}
    for edge in structural_edges:
        lk = str(edge.get("link_kind", "hard")).lower()
        if lk in ("soft", "independent", "none", "free", "signal", "diffusion"):
            continue
        a, b = edge["start"], edge["end"]
        ta, tb = id_to_type.get(a, ""), id_to_type.get(b, "")
        parent_id = child_id = None
        if ta == "organism" and tb in ("sensor", "actuator"):
            parent_id, child_id = a, b
        elif tb == "organism" and ta in ("sensor", "actuator"):
            parent_id, child_id = b, a
        if not parent_id or not child_id:
            continue
        pe = id_to_ent.get(parent_id)
        ce = id_to_ent.get(child_id)
        if pe is None or ce is None:
            continue
        dx = float(ce.position[0]) - float(pe.position[0])
        dy = float(ce.position[1]) - float(pe.position[1])
        attach[child_id] = (parent_id, dx, dy)
        ce.membrane_locked = True
        ce.pinned = False
    return attach


def _signal_edge_key(edge: Dict[str, Any]) -> Tuple[str, str, str]:
    """信号边唯一键，供 dedupe / expand 索引使用。"""
    return (
        str(edge.get("start", "")),
        str(edge.get("end", "")),
        str(edge.get("channel", "chemo")),
    )


def dedupe_signal_edges(edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """按 (start, end, channel) 去重信号边。

    职责:
        保证 aggregate_channel_signals 不会对同一对节点累加两次。

    时机:
        场景加载末尾；繁殖 spawn 在 mutate 之后。

    不变量:
        后出现的边覆盖先出现的同键边。

    排错:
        趋化过强疑似双倍 → 对 _sr_signal_edges 按键计数，应各为 1；
        与 apply_explicit_signal_edges 共用键语义。
    """
    index: Dict[Tuple[str, str, str], int] = {}
    out: List[Dict[str, Any]] = []
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        key = _signal_edge_key(edge)
        if not key[0] or not key[1]:
            continue
        row = dict(edge)
        if key in index:
            out[index[key]] = row
        else:
            index[key] = len(out)
            out.append(row)
    return out


def expand_signal_edges(
    structural_edges: List[Dict[str, Any]],
    attachments: Mapping[str, Tuple[str, float, float]],
    id_to_type: Mapping[str, str],
    default_weight: float = 1.0,
) -> List[Dict[str, Any]]:
    """由结构边展开 chemo 信号边（显式优先，隐式仅补缺）。

    职责:
        1) 收录 structural 中 sensor→actuator 边（可带显式 weight/channel）；
        2) 对每个 hub 下 sensor×actuator 全连接，仅当键不存在时追加默认权。

    时机:
        场景加载、繁殖子代膜展开（无现成 signal_edges 列表时）。

    不变量:
        同键 (start, end, channel) 在表内唯一；sensor/actuator 迭代顺序为 sorted(id)。

    排错:
        趋化翻倍 → 检查是否重复 expand 且未 dedupe，或隐式边覆盖了 sr_signal_connections；
        历史：隐式循环曾覆盖显式 1.25 权重，已改为 if key in index: continue。
    """
    signal: List[Dict[str, Any]] = []
    index: Dict[Tuple[str, str, str], int] = {}

    def _add(edge: Dict[str, Any]) -> None:
        key = _signal_edge_key(edge)
        if not key[0] or not key[1]:
            return
        row = dict(edge)
        if key in index:
            signal[index[key]] = row
        else:
            index[key] = len(signal)
            signal.append(row)

    # 阶段 A：结构里已写的 sensor→actuator（含 main_scene.sr_signal_connections 解析结果）
    for edge in structural_edges:
        a, b = edge["start"], edge["end"]
        ta, tb = id_to_type.get(a, ""), id_to_type.get(b, "")
        if ta == "sensor" and tb == "actuator":
            _add(
                {
                    "start": a,
                    "end": b,
                    "channel": str(edge.get("channel", "chemo")),
                    "weight": float(edge.get("weight", default_weight)),
                }
            )
    by_parent: Dict[str, List[str]] = {}
    for child_id, (parent_id, _dx, _dy) in attachments.items():
        by_parent.setdefault(parent_id, []).append(child_id)
    # 阶段 B：隐式全连接，不覆盖阶段 A 已有键
    for _pid, children in by_parent.items():
        sensors = sorted(c for c in children if id_to_type.get(c) == "sensor")
        actuators = sorted(c for c in children if id_to_type.get(c) == "actuator")
        for sid in sensors:
            for aid in actuators:
                if (sid, aid, "chemo") in index:
                    continue
                _add(
                    {
                        "start": sid,
                        "end": aid,
                        "channel": "chemo",
                        "weight": float(default_weight),
                    }
                )
    return signal


def membrane_child_ids_for_hub(
    hub_id: str,
    attachments: Mapping[str, Tuple[str, float, float]],
    id_to_type: Mapping[str, str],
) -> Tuple[List[str], List[str]]:
    """列出某 hub 下膜 sensor / actuator 子 id（已排序）。

    职责:
        供 inherit_chemo_edge_weights 与 expand 使用同一排序约定。

    时机:
        繁殖 spawn 继承父代边权时。

    不变量:
        返回 (sorted_sensors, sorted_actuators)。

    排错:
        遗传边权错位 → 确认父/子 hub 的 sensor、actuator 数量一致或按序截断。
    """
    sensors: List[str] = []
    actuators: List[str] = []
    for child_id, (parent_id, _dx, _dy) in attachments.items():
        if parent_id != hub_id:
            continue
        if id_to_type.get(child_id) == "sensor":
            sensors.append(child_id)
        elif id_to_type.get(child_id) == "actuator":
            actuators.append(child_id)
    return sorted(sensors), sorted(actuators)


def inherit_chemo_edge_weights(
    child_edges: List[Dict[str, Any]],
    parent_edges: List[Dict[str, Any]],
    *,
    child_sensor_ids: List[str],
    child_actuator_ids: List[str],
    parent_sensor_ids: List[str],
    parent_actuator_ids: List[str],
) -> List[Dict[str, Any]]:
    """将父代 chemo 边权按拓扑下标映射到子代边。

    职责:
        用排序后 sensor 下标 i、actuator 下标 j 对应父 (ps[i], pa[j]) → 子 (cs[i], ca[j]) 的权重。

    时机:
        宿主繁殖流水线中，须在 expand 之后、mutate_signal_edges 之前。

    不变量:
        仅 channel=='chemo' 的边被改写 weight；未匹配键保持 expand 默认值。

    排错:
        子代边权全相同 → 历史曾用 signal_edge_weights 均值覆盖，已禁止；
        突变无效 → 检查 mutate 是否在 inherit 之后调用；
        勿按实体 ID 字符串匹配父/子（子代 id 不同，靠下标对齐）。
    """
    parent_map: Dict[Tuple[str, str], float] = {}
    for edge in parent_edges:
        if not isinstance(edge, dict) or str(edge.get("channel", "chemo")) != "chemo":
            continue
        try:
            parent_map[(str(edge["start"]), str(edge["end"]))] = float(edge.get("weight", 1.0))
        except (TypeError, ValueError, KeyError):
            continue
    ps = sorted(parent_sensor_ids)
    pa = sorted(parent_actuator_ids)
    cs = sorted(child_sensor_ids)
    ca = sorted(child_actuator_ids)
    child_map: Dict[Tuple[str, str], float] = {}
    for i, sid in enumerate(ps):
        for j, aid in enumerate(pa):
            if i >= len(cs) or j >= len(ca):
                continue
            w = parent_map.get((sid, aid), 1.0)
            child_map[(cs[i], ca[j])] = w
    out: List[Dict[str, Any]] = []
    for edge in child_edges:
        row = dict(edge)
        if str(row.get("channel", "chemo")) == "chemo":
            key = (str(row.get("start", "")), str(row.get("end", "")))
            if key in child_map:
                row["weight"] = child_map[key]
        out.append(row)
    return out


def mutate_signal_edges(
    edges: List[Dict[str, Any]],
    sigma: float,
    rng: random.Random,
) -> List[Dict[str, Any]]:
    """对边权施加高斯微扰（繁殖遗传最后一步）。

    职责:
        每条边 weight += N(0, sigma*0.15)，并夹紧到 [0.05, 3.0]。

    时机:
        inherit_chemo_edge_weights（或有序 signal_edge_weights）之后；
        dedupe_signal_edges 之前。

    不变量:
        sigma<=0 时不改动权重。

    排错:
        繁殖后代边权无差异 → 查是否仍在 mutate 之后做均值覆盖；
        权重爆炸 → 检查夹紧区间与 sigma 配置。
    """
    out: List[Dict[str, Any]] = []
    sig = max(0.0, float(sigma))
    for e in edges:
        w = float(e.get("weight", 1.0))
        if sig > 0:
            w = max(0.05, min(3.0, w + rng.gauss(0.0, sig * 0.15)))
        out.append({**e, "weight": w})
    return out


def learn_chemo_edge_weights(
    edges: list[dict[str, Any]],
    *,
    reward: float,
    stress: float = 0.0,
    learn_rate: float = 0.04,
) -> list[dict[str, Any]]:
    """Hebbian 式 chemo 边权调制：内稳态改善则增强，应激则衰减。"""
    r = max(0.0, min(1.0, float(reward)))
    s = max(0.0, min(1.0, float(stress)))
    lr = max(0.0, float(learn_rate))
    if lr <= 0.0:
        return edges
    delta = lr * (r - 0.45 - s * 0.35)
    out: list[dict[str, Any]] = []
    for edge in edges:
        row = dict(edge)
        if str(row.get("channel", "chemo")) != "chemo":
            out.append(row)
            continue
        try:
            w = float(row.get("weight", 1.0))
        except (TypeError, ValueError):
            w = 1.0
        w = max(0.05, min(3.0, w + delta))
        row["weight"] = w
        out.append(row)
    return out


def update_hub_chemo_edges_on_host(
    signal_edges: list[dict[str, Any]],
    hub_id: str,
    membrane_attach: Mapping[str, tuple[str, float, float]],
    *,
    reward: float,
    stress: float = 0.0,
) -> list[dict[str, Any]]:
    """更新宿主全局 signal_edges 中属于某 hub 膜子图的 chemo 边权。"""
    child_ids = {cid for cid, (pid, _dx, _dy) in membrane_attach.items() if pid == hub_id}
    if not child_ids:
        return signal_edges
    updated = learn_chemo_edge_weights(
        [e for e in signal_edges if e.get("start") in child_ids or e.get("end") in child_ids],
        reward=reward,
        stress=stress,
    )
    idx = {(str(e.get("start", "")), str(e.get("end", ""))): e for e in updated}
    out: list[dict[str, Any]] = []
    for edge in signal_edges:
        key = (str(edge.get("start", "")), str(edge.get("end", "")))
        if key in idx:
            out.append(dict(idx[key]))
        else:
            out.append(dict(edge))
    return out


def aggregate_channel_signals(
    signal_edges: List[Dict[str, Any]],
    entities: List[Any],
    *,
    use_prev: bool,
) -> Dict[str, Dict[str, float]]:
    """按信号边累加各 target 的 inbound 通道值。

    职责:
        对每条边：inbound[target][channel] += weight * source.sr_channel_out[channel]；
        chemo 方向分量 chemo_dir_* 同权累加。

    时机:
        宿主每 tick：organism/sensor 批 use_prev=True；actuator 批 False（读当帧 sensor 输出）。

    不变量:
        use_prev 时读 sr_channel_out_prev，否则读 sr_channel_out；
        chemo 通道兼容别名 chemo_signal。

    排错:
        纤毛无趋化 → 查 signal_edges 是否重复导致异常大/小、sensor 是否写出 chemo；
        晚一帧 → 查 tick 顺序是否 organism→sensor→actuator 与 use_prev 一致。
    """
    inbound: Dict[str, Dict[str, float]] = {}
    id_to_ent = {str(getattr(e, "id", "")): e for e in entities}

    def _src_field(ent: Any) -> Dict[str, float]:
        if use_prev:
            raw = getattr(ent, "sr_channel_out_prev", None)
        else:
            raw = getattr(ent, "sr_channel_out", None)
        return dict(raw) if isinstance(raw, dict) else {}

    for edge in signal_edges:
        src_id = str(edge["start"])
        tgt_id = str(edge["end"])
        ch = str(edge.get("channel", "chemo"))
        try:
            w = float(edge.get("weight", 1.0))
        except (TypeError, ValueError):
            w = 1.0
        se = id_to_ent.get(src_id)
        if se is None:
            continue
        src_map = _src_field(se)
        val = float(src_map.get(ch, 0.0))
        if val == 0.0 and ch == "chemo":
            val = float(src_map.get("chemo_signal", 0.0))
        if val == 0.0:
            continue
        bucket = inbound.setdefault(tgt_id, {})
        bucket[ch] = bucket.get(ch, 0.0) + w * val
        for dk in ("chemo_dir_x", "chemo_dir_y"):
            try:
                dv = float(src_map.get(dk, 0.0))
            except (TypeError, ValueError):
                dv = 0.0
            if dv != 0.0:
                bucket[dk] = bucket.get(dk, 0.0) + w * val * dv
    return inbound


def membrane_spawn_spec(
    hub_id: str,
    position: Tuple[float, float],
    radius: float,
    *,
    template: Optional[Dict[str, Any]] = None,
    signal_edges: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """构造 organism_with_membrane 动态生成请求字典。

    职责:
        返回宿主 _process_sr_spawn_requests 可识别的 req 骨架。

    时机:
        evo_central_brain_pvaec._try_reproduce 登记 spawn_requests。

    不变量:
        template=None 时宿主改用 _sr_membrane_template，勿在脚本内塞 DEFAULT；
        边权遗传优先 parent_signal_edges + parent_hub_id。

    排错:
        子代无膜 → type 须为 organism_with_membrane；
        模板与场景不符 → 繁殖 req 应 pop('template') 交由宿主解析场景模板。
    """
    tpl = template if isinstance(template, dict) else DEFAULT_MEMBRANE_TEMPLATE
    return {
        "type": "organism_with_membrane",
        "hub_id": hub_id,
        "position": position,
        "radius": radius,
        "template": tpl,
        "signal_edges": list(signal_edges or []),
    }
