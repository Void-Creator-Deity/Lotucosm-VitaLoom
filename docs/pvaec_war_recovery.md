# PVAEC · 战争后进化工程

工程路径：`workspace/projects/samples/pvaec-战争后进化`

## 定位

在 **PVAEC 细胞演化** 范式上增加 **三幕灾难叙事**（和平 → 战争互攻 → 恢复），对齐自研 AI 演化模拟选题。

## 架构

```
sr_war_recovery (场景 JSON 真源)
    ├── combat → sr_war_combat（战争期 HP / 禁觅食 / 复活变异）
    ├── GameViewport：战争期 damage 结算、膜 bootstrap、respawn 队列
    ├── EvoWarRecoveryBrainPvaec（和平 Evo / 战争 HUD+自训练）
    ├── ActuatorSpikeCombatPvaec（膜刺近战）
    └── WarRecoveryDirectorPvaec（场域脉冲，无营养清扫）
```

## 调参建议

- 战争过短看不清互攻：延长 `manual_war_duration` 或提前按 **W**
- 全灭太快：降低 `melee_damage`、提高 `base_hp`
- 变异太慢：提高 `death_mutation_per_death`
- 和平期种群不足：延长 `peace_until`、降低 `reproduce_energy`

## 测试

- `tests/test_sr_war_recovery.py` — 三幕配置
- `tests/test_sr_war_combat.py` — 互攻与变异概率
- `tests/test_pvaec_war_recovery_sample.py` — 刺脚本与场景契约

## 相关文档

- [pvaec_cell_evolution.md](pvaec_cell_evolution.md)
- [ADR-0005 unified pond](adr/0005-unified-pond-bridge.md)
