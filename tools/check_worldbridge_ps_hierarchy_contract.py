#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from _runtime_bootstrap import install_runtime_paths
install_runtime_paths(ROOT)

from builtin.components.component_factory import ComponentFactory
from builtin.entity_types.organism import Organism
from core.Lotucosm.runtime.world_bridge_ps_hierarchy_contract import (
    build_ps_hierarchy_authority_contract,
    validate_ps_hierarchy_authority_contract,
)


def main() -> int:
    organism = Organism("e312-hierarchy-owner", (0.0, 0.0))
    factory = ComponentFactory()
    for component_id, component_type in (("sensor", "Sensor"), ("actuator", "Actuator")):
        organism.add_component(factory.create_component(component_type, component_id, organism_id=organism.id))
    organism.set_membrane(factory.create_component("Membrane", "membrane", organism_id=organism.id))
    result = build_ps_hierarchy_authority_contract(organism)
    result["validation"] = validate_ps_hierarchy_authority_contract(result)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["validation"]["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
