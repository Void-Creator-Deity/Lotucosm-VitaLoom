# PVAEC · 战争后进化

仿 **自研 AI 生命演化模拟**选题，基于官方包 `vitalloom.pvaec.simulation`。配置真源为场景根字段 **`sr_war_recovery`**（脚本 `properties.war_recovery` 仅作缺省，通常留空）。

## 三幕时间轴

| 阶段 | 默认时间 | 机制 |
|------|----------|------|
| 和平 | 0 – `peace_until`（50s） | 8 颗营养、正常代谢、繁殖 |
| 战争 | `peace_until` – `war_until`（85s） | **纯互攻**：膜刺近战、击杀积分、死亡变异复活（禁觅食） |
| 恢复 | `war_until` 之后 | 营养 +3、`well_proximity_feed`×1.35、繁殖重建 |

HUD 显示 **`阶段·和平/战争/恢复`** 与阶段倒计时；战争期显示积分、战亡次数与下次变异概率；进入战争/恢复时顶部横幅提示。画布有战争微红 / 恢复淡绿色调叠层；膜簇上可见**红色刺状执行器**。

## 战争互攻（`sr_war_recovery.combat`）

| 字段 | 说明 |
|------|------|
| `combat_enabled_in_war` | 战争期启用 HP 与近战伤害 |
| `disable_feeding_in_war` | 战争期禁用场摄取与噬咬营养 |
| `base_hp` / `melee_damage` / `melee_reach` | 战斗数值 |
| `kill_score` | 击杀对方获得积分 |
| `respawn_delay` / `max_respawns_per_lineage` | 死亡后延迟复活上限 |
| `death_mutation_*` | 死亡次数越多，复活前 mind 变异概率越高 |
| `online_train_on_kill` | 存活时击杀后在线微调战斗相关基因 |

引擎：`sr_war_combat.py`、`sr_organism_combat.py`；脚本：`actuator_spike_combat_pvaec`、`evo_war_recovery_brain_pvaec`。

## 手动灾难

`sr_war_recovery.manual_trigger: true` 时，运行中按 **`W`** 强制进入战争窗 `manual_war_duration` 秒。

## 快速开始

1. `python main.py` → 打开本工程 → `war_recovery_scene.pond` → **▶ 运行**
2. PS 批实验：`workspace/experiments/post_war_recovery.json`
3. 可选 unified：`project.unified_pond.example.json` 合并进 `project.json`

## 与细胞演化示范的关系

共用膜趋化脚本来自 [`pvaec-细胞演化`](../pvaec-细胞演化/)；本工程新增战争互攻脚本与 `war_recovery_director_pvaec`。

详见 [`docs/pvaec_war_recovery.md`](../../docs/pvaec_war_recovery.md)。
