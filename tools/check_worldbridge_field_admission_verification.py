#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify WorldBridge live-mapping blockers without mutating runtime state."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))
from _runtime_bootstrap import install_runtime_paths  # noqa: E402
install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_field_admission import (  # noqa: E402
    build_worldbridge_field_admission_verification,
)
from core.Lotucosm.runtime.world_bridge_ps_component_corpus import (  # noqa: E402
    build_worldbridge_ps_component_corpus,
    build_worldbridge_ps_component_persistence_audit,
)
from core.Lotucosm.runtime.world_bridge_ps_graph_corpus import (  # noqa: E402
    build_worldbridge_ps_graph_corpus,
)


def main() -> int:
    result = build_worldbridge_field_admission_verification()
    corpus = build_worldbridge_ps_component_corpus()
    persistence = build_worldbridge_ps_component_persistence_audit()
    graph = build_worldbridge_ps_graph_corpus()
    result["local_ps_component_evidence"] = {
        "component_type_count": corpus["component_type_count"],
        "lifecycle_ownership": corpus["evidence"]["lifecycle_ownership"],
        "all_round_trip_ok": persistence["all_round_trip_ok"],
        "lossy_or_failed_types": persistence["lossy_or_failed_types"],
        "cross_lane_replay": False,
        "promoted_to_live_adapter": False,
        "graph_owner_and_connection_facts": {
            "organism_component_owner": graph["evidence"]["organism_component_owner"],
            "membrane_reference_owner": graph["evidence"]["membrane_reference_owner"],
            "ordered_directed_edges": graph["evidence"]["ordered_directed_edges"],
            "graph_persistence_round_trip": graph["evidence"]["graph_persistence_round_trip"],
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    valid = result["read_only"] and result["all_fields_blocked"]
    valid = valid and result["live_adapter_admitted"] is False
    valid = valid and result["local_ps_component_evidence"]["lifecycle_ownership"]
    valid = valid and result["local_ps_component_evidence"]["all_round_trip_ok"]
    valid = valid and not result["local_ps_component_evidence"]["lossy_or_failed_types"]
    graph_facts = result["local_ps_component_evidence"]["graph_owner_and_connection_facts"]
    valid = valid and graph_facts["organism_component_owner"] and graph_facts["membrane_reference_owner"]
    valid = valid and graph_facts["ordered_directed_edges"]
    valid = valid and graph_facts["graph_persistence_round_trip"] is True
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())

