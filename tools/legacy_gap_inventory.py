#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""遍历旧版 Lotucosm-VitaLoom/src，生成 docs/legacy_gap_matrix.csv 与 .md。

职责: 对比 LEGACY_SRC 与当前树，输出 gap 矩阵 CSV/Markdown。
时机: 旧 src 有变更时在项目根手动运行。
不变量: LEGACY_SRC_ROOT 可覆盖默认旧版路径。
排错: 见 docs/simulation_goals.md、docs/legacy_gap_b_triage.md。
"""
from __future__ import annotations
import csv, os, sys
from pathlib import Path

THIS = Path(__file__).resolve()
NEW_ROOT = THIS.parents[1]
DEFAULT_LEGACY = NEW_ROOT.parent / "Lotucosm-VitaLoom" / "src"
LEGACY_SRC = Path(os.environ.get("LEGACY_SRC_ROOT", str(DEFAULT_LEGACY))).resolve()

OVERRIDES = {
    "lotucosm/environment/lotus_pond.py": ("core/Lotucosm/pond.py", "environment", "A", ""),
    "lotucosm/environment/floating_system.py": ("builtin/systems/floating_system.py", "environment", "A", ""),
    "lotucosm/environment/entity_base.py": ("core/Lotucosm/entity.py", "environment", "A", ""),
    "lotucosm/environment/food.py": ("core/Lotucosm/pond.py", "environment", "A", ""),
    "lotucosm/environment/obstacle.py": ("builtin/systems/obstacle.py", "environment", "A", ""),
    "lotucosm/environment/environment.py": ("builtin/systems/environment.py", "environment", "A", ""),
    "lotucosm/environment/pond_serializer.py": ("builtin/systems/pond_serializer.py", "serialization", "A", ""),
    "lotucosm/environment/assembly_system.py": ("core/Lotucosm/pond.py", "environment", "B", ""),
    "lotucosm/evolution/inheritance.py": ("builtin/systems/inheritance.py", "evolution", "B", "evolvable_traits"),
    "lotucosm/simulator/simulation.py": ("projects/main_world", "shell", "C", "Pygame"),
    "lotucosm/simulator/inheritance_simulation.py": ("projects/main_world", "shell", "C", ""),
    "lotucosm/persistence/memory_storage.py": ("builtin/systems/memory_storage.py", "persistence", "A", ""),
    "vitalloom/core/memory.py": ("core/Lotucosm/memory.py", "memory", "A", ""),
    "vitalloom/core/pvaec_cycle.py": ("core/Lotucosm/pvaec_cycle.py", "pvaec", "A", ""),
    "vitalloom/core/perception.py": ("core/Lotucosm/perception.py", "perception", "D", "optional"),
    "vitalloom/core/event_system.py": ("core/api/event_system.py", "events", "C", ""),
    "vitalloom/components/PVAECEngine.py": ("builtin/components/PVAECEngine.py", "components", "A", ""),
    "vitalloom/components/components_base.py": ("builtin/components/components_base.py", "components", "A", ""),
    "vitalloom/components/sensors.py": ("builtin/components/sensors.py", "components", "A", ""),
    "vitalloom/components/actuators.py": ("builtin/components/actuators.py", "components", "A", ""),
    "vitalloom/components/connection.py": ("builtin/components/connection.py", "components", "A", ""),
    "vitalloom/components/hybrid.py": ("builtin/components/hybrid.py", "components", "A", ""),
    "vitalloom/components/membrane.py": ("builtin/components/membrane.py", "components", "A", ""),
    "vitalloom/components/component_library.py": ("builtin/components/component_library.py", "components", "A", ""),
    "vitalloom/organisms/organism.py": ("builtin/entity_types/organism.py", "organism", "A", ""),
    "vitalloom/organisms/intelligent_organism.py": ("builtin/entity_types/intelligent_organism.py", "organism", "A", ""),
    "vitalloom/organisms/simple_organism.py": ("builtin/entity_types/simple_organism.py", "organism", "A", ""),
    "vitalloom/organisms/reproduction.py": ("builtin/entity_types/reproduction.py", "organism", "B", ""),
    "vitalloom/organisms/component_acquisition.py": ("builtin/entity_types/component_acquisition.py", "acquisition", "D", ""),
    "vitalloom/editor/ui/pyqt_organism_editor.py": ("core/VitaLoom/kernel", "editor", "C", ""),
    "vitalloom/editor/commands/command.py": ("core/VitaLoom", "editor", "C", "out of scope"),
    "vitalloom/editor/template_manager.py": ("core/VitaLoom/project", "editor", "C", ""),
    "launcher/launcher.py": ("main.py", "launcher", "C", ""),
    "main.py": ("main.py", "entry", "C", ""),
}

def rel_posix(p, root):
    try:
        return p.relative_to(root).as_posix()
    except ValueError:
        return str(p)

def classify(rel):
    if rel in OVERRIDES:
        return OVERRIDES[rel]
    if rel.startswith("vitalloom/editor/"):
        return ("builtin/editor_extensions/*", "editor", "C", "editor default")
    return ("(TBD)", "unknown", "B", "manual")

def main():
    if not LEGACY_SRC.is_dir():
        print("LEGACY_SRC missing:", LEGACY_SRC, file=sys.stderr)
        return 1
    py_files = sorted(p for p in LEGACY_SRC.rglob("*.py") if ".history" not in p.parts)
    docs = NEW_ROOT / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    rows = []
    for p in py_files:
        rel = rel_posix(p, LEGACY_SRC)
        nc, dom, g, n = classify(rel)
        rows.append({"legacy_module": rel, "domain": dom, "new_counterpart": nc, "gap_class": g, "notes": n})
    csv_path = docs / "legacy_gap_matrix.csv"
    import csv as _csv
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = _csv.DictWriter(f, fieldnames=["legacy_module", "domain", "new_counterpart", "gap_class", "notes"])
        w.writeheader()
        w.writerows(rows)
    ct: dict[str, int] = {}
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
    (docs / "legacy_gap_matrix.md").write_text("\n".join(md_lines), encoding="utf-8")
    print("ok", len(rows), "B=", b_count, "| sync legacy_gap_b_triage.md if B rows changed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
