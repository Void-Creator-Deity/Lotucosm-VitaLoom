"""
幂等：补齐 simulation_goals 第 6–8 节、legacy_gap_b_triage 的 SR 说明块（若缺失），并尝试升级 legacy_gap_inventory 的 matrix md 输出格式。最后总是调用 legacy_gap_inventory 刷新 CSV/md。

从仓库根运行：`python tools/refine_gap_docs.py`
排错: 见 docs/comment_standard.md、docs/lotucosm_core_troubleshooting.md 或子树 README。

"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""幂等：补齐 simulation_goals 第 6–8 节、legacy_gap_b_triage 的 SR 说明块（若缺失），并尝试升级 legacy_gap_inventory 的 matrix md 输出格式。最后总是调用 legacy_gap_inventory 刷新 CSV/md。

从仓库根运行：`python tools/refine_gap_docs.py`
"""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
docs = ROOT / "docs"

ADD = """

## 6. 计划外大改（本评估轨道不默认做）

以下属于产品接线或大范围重构，**不**作为「模拟目标驱动评估」的默认交付：

- 将场景 `.pond` 中的 `pond_config`（如 `initial_organisms`）**自动同步**为真 `Pond` 人口并与 `GameViewport` 场景运行时二选一或合并驱动（需单独立项与验收设计）。
- 旧版 **PyQt 单应用编辑器 / command 全集** 行为对等（矩阵 **C**，见 [legacy_gap_d_class.md](legacy_gap_d_class.md)）。

## 7. 日常内化工作流（简）

1. 跑清单：`python tools/legacy_gap_inventory.py`，看 `legacy_gap_matrix.md` 中 A/B/C/D 计数是否变化。
2. 若有新 **B** 行：在 [legacy_gap_b_triage.md](legacy_gap_b_triage.md) **追加一行**（勿改历史结论除非矩阵行被删除或改类）。
3. 若要内化：先写 **触发场景**，选定 **PS** 或 **SR**，再写测/脚本，最后改代码并保持默认行为不变。
4. **D** 类候选：先写在 [legacy_gap_d_class.md](legacy_gap_d_class.md)，满足准入条后再实现。

## 8. 代码锚点（便于评审时打开）

- SR：`core/Lotucosm/pvaec_script.py`、`core/Lotucosm/scene_runtime_context.py`、`core/VitaLoom/viewports/game_viewport.py`
- PS：`core/Lotucosm/pond.py`、`builtin/entity_types/organism.py`、`builtin/systems/*.py`、`core/Lotucosm/pvaec_cycle.py`
"""

NEEDLE = "- **acceptance**：验收方式（测试文件关键字或 `manual`）。\n\n## environment"
INSERT = """- **acceptance**：验收方式（测试文件关键字或 `manual`）。

**与矩阵同步**：刷新 CSV 后，用 `gap_class=B` 过滤应与本表行数一致（当前矩阵统计见 [legacy_gap_matrix.md](legacy_gap_matrix.md)）；多出新 B 行必须在本表追加。

## SR（主世界 / 场景运行时）说明

当前 CSV 中的 B 类旧模块**几乎全部落在 PS**（莲池、演化、持久化、组件工厂）：旧版没有与现版 `PvaecScript` 一一对应的「场景脚本文件」。若某行为**仅**用于主世界演示（邻域、环境场、拓扑边），内化时应：

- 将逻辑放在 `projects/*/scripts/*.py` 或扩展 `SceneRuntimeTickContext` / 视口 tick；
- 验收用 `tests/test_main_world_pvaec_scripts_smoke.py`、`tests/test_central_brain_pvaec.py` 等扩展用例，**不要**误挂到 `Organism` 组件图除非同时满足 PS 目标。

## environment"""

INV_OLD = """    ct = {}
    for r in rows:
        ct[r["gap_class"]] = ct.get(r["gap_class"], 0) + 1
    (docs / "legacy_gap_matrix.md").write_text(
        "# Legacy gap matrix\\n\\nCounts: %s\\nRows: %s\\nSee legacy_gap_matrix.csv\\n" % (ct, len(rows)),
        encoding="utf-8",
    )
    print("ok", len(rows))"""


def patch_simulation_goals() -> None:
    p = docs / "simulation_goals.md"
    t = p.read_text(encoding="utf-8")
    if "## 6. 计划外大改" in t:
        return
    p.write_text(t.rstrip() + ADD, encoding="utf-8")
    print("simulation_goals: appended sections 6-8")


def patch_b_triage() -> None:
    p = docs / "legacy_gap_b_triage.md"
    u = p.read_text(encoding="utf-8")
    if "**与矩阵同步**" in u:
        return
    if NEEDLE not in u:
        raise SystemExit("legacy_gap_b_triage.md: expected needle missing")
    p.write_text(u.replace(NEEDLE, INSERT, 1), encoding="utf-8")
    print("legacy_gap_b_triage: inserted SR block")


def patch_inventory() -> None:
    inv = ROOT / "tools" / "legacy_gap_inventory.py"
    s = inv.read_text(encoding="utf-8")
    if "b_count = ct.get" in s:
        return
    if INV_OLD not in s:
        raise SystemExit("legacy_gap_inventory.py: expected block missing")
    new = """    ct: dict[str, int] = {}
    for r in rows:
        ct[r["gap_class"]] = ct.get(r["gap_class"], 0) + 1
    b_count = ct.get("B", 0)
    md_lines = [
        "# Legacy gap matrix",
        "",
        "Counts: %s" % (ct,),
        "Rows: %s" % len(rows),
        "See legacy_gap_matrix.csv",
        "",
        "See also [simulation_goals.md](simulation_goals.md) and [legacy_gap_b_triage.md](legacy_gap_b_triage.md).",
        "",
        "If gap_class=B count changed (now **%s**), update [legacy_gap_b_triage.md](legacy_gap_b_triage.md) with any new rows."
        % b_count,
        "",
    ]
    (docs / "legacy_gap_matrix.md").write_text("\\n".join(md_lines), encoding="utf-8")
    print("ok", len(rows), "B=", b_count, "| sync legacy_gap_b_triage.md if B rows changed")"""
    inv.write_text(s.replace(INV_OLD, new, 1), encoding="utf-8")
    print("legacy_gap_inventory: patched markdown output")


def main() -> int:
    patch_simulation_goals()
    patch_b_triage()
    patch_inventory()
    subprocess.check_call([sys.executable, str(ROOT / "tools" / "legacy_gap_inventory.py")], cwd=str(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
