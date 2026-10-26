# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import random
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import (
    create_worldbridge_deterministic_randomness_context,
    register_worldbridge_deterministic_random_stream,
)
from core.Lotucosm.runtime.world_bridge_named_stream_adapter import (
    build_worldbridge_named_stream_adapter_contract,
    build_worldbridge_respawn_two_stream_handoff_contract,
    mutate_sr_mind_with_worldbridge_named_stream,
    run_worldbridge_named_stream_sr_respawn_handoff,
    validate_worldbridge_named_stream_sr_mind_adapter,
    validate_worldbridge_named_stream_sr_respawn_handoff,
)
from core.Lotucosm.sr_mind_gene import mind_dict_mutate
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status
from core.VitaLoom.viewports.game_viewport import GameViewport


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"
VIEWPORT = RUNTIME / "core/VitaLoom/viewports/game_viewport.py"


def _context(seed: str = "e224-seed"):
    context = create_worldbridge_deterministic_randomness_context("e224-context", seed)
    register_worldbridge_deterministic_random_stream(
        context,
        "sr.war.respawn.mind",
        "python_random",
    )
    return context


def test_adapter_contract_is_explicit_and_not_default_ready() -> None:
    contract = build_worldbridge_named_stream_adapter_contract()
    assert contract == {
        "schema_version": 1,
        "adapter_kind": "worldbridge_named_stream_sr_mind_mutation_adapter",
        "supported_consumer": "sr_mind_gene.mind_dict_mutate",
        "supported_stream_family": "python_random",
        "caller_owned": True,
        "default_tick_attached": False,
        "global_rng_reseeded": False,
        "restore_api_exposed": False,
        "replay_admitted": False,
        "default_ready": False,
    }


def test_adapter_consumes_one_named_local_stream_and_records_snapshot_pair() -> None:
    parent = {"wander_amp": 20.0, "gain_high_stress": 40.0, "mem_alpha": 0.3}
    first = mutate_sr_mind_with_worldbridge_named_stream(
        _context(), "sr.war.respawn.mind", parent, 0.25
    )
    second = mutate_sr_mind_with_worldbridge_named_stream(
        _context(), "sr.war.respawn.mind", parent, 0.25
    )
    assert first["child"] == second["child"]
    assert first["deltas"] == second["deltas"]
    assert first["before_snapshot_digest"] == second["before_snapshot_digest"]
    assert first["after_snapshot_digest"] == second["after_snapshot_digest"]
    assert first["stream_state_changed"] is True
    assert first["caller_owned"] is True
    assert first["default_tick_attached"] is False
    assert first["replay_admitted"] is False
    assert first["lossless"] is False


def test_adapter_rejects_missing_or_wrong_family_without_consuming_selected_stream() -> None:
    context = _context()
    before = context.snapshot()
    with pytest.raises(KeyError):
        validate_worldbridge_named_stream_sr_mind_adapter(context, "missing")
    register_worldbridge_deterministic_random_stream(context, "numpy-only", "numpy_pcg64_generator")
    with pytest.raises(ValueError, match="requires 'python_random'"):
        validate_worldbridge_named_stream_sr_mind_adapter(context, "numpy-only")
    after = context.snapshot()
    assert after["streams"][0]["state"] == before["streams"][0]["state"]


def test_adapter_does_not_touch_module_global_rngs() -> None:
    parent = {"wander_amp": 20.0, "gain_high_stress": 40.0, "mem_alpha": 0.3}
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    mutate_sr_mind_with_worldbridge_named_stream(_context(), "sr.war.respawn.mind", parent, 0.25)
    assert random.getstate() == python_before
    numpy_after = np.random.get_state()
    assert numpy_after[0] == numpy_before[0]
    assert np.array_equal(numpy_after[1], numpy_before[1])
    assert numpy_after[2:] == numpy_before[2:]


def test_viewport_real_respawn_handoff_is_opt_in_and_legacy_fallback_is_preserved() -> None:
    parent = {"wander_amp": 20.0, "gain_high_stress": 40.0, "mem_alpha": 0.3}
    viewport = SimpleNamespace()
    legacy = GameViewport._apply_sr_respawn_mind_mutation(viewport, parent, 0.25, "lineage", 2, 1.5)
    global_before = random.getstate()
    legacy_again = GameViewport._apply_sr_respawn_mind_mutation(
        SimpleNamespace(), parent, 0.25, "lineage", 2, 1.5
    )
    assert legacy == legacy_again
    assert random.getstate() == global_before

    context = _context()
    GameViewport.set_worldbridge_opt_in_named_stream(viewport, context, stream_name="sr.war.respawn.mind")
    adapted = GameViewport._apply_sr_respawn_mind_mutation(
        viewport, parent, 0.25, "lineage", 2, 1.5
    )
    direct = mutate_sr_mind_with_worldbridge_named_stream(
        _context(), "sr.war.respawn.mind", parent, 0.25
    )
    assert adapted == direct["child"]
    GameViewport.set_worldbridge_opt_in_named_stream(
        viewport, None, stream_name="sr.war.respawn.mind"
    )
    assert not hasattr(viewport, "_worldbridge_opt_in_named_stream")


def test_default_viewport_has_only_lazy_adapter_seam() -> None:
    tree = ast.parse(VIEWPORT.read_text(encoding="utf-8"))
    top_level_imports = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
    assert not any(
        isinstance(node, ast.ImportFrom)
        and node.module
        and "world_bridge_named_stream_adapter" in node.module
        for node in top_level_imports
    )
    source = VIEWPORT.read_text(encoding="utf-8")
    assert "create_worldbridge_deterministic_randomness_context" not in source
    assert "_worldbridge_opt_in_named_stream" in source


def test_status_nests_adapter_contract_without_default_adoption() -> None:
    status = build_runtime_worldbridge_status()
    assert status["opt_in_named_stream_sr_mind_adapter_contract"]["default_ready"] is False
    assert "named_stream_sr_mind_adapter_module" in status["pilot_modules"]
    assert status["runtime_mode"] == "dual"
    assert status["unified_pond_enabled"] is False
    assert status["default_ready"] is False



def _two_stream_context(seed: str = "e225-seed"):
    context = create_worldbridge_deterministic_randomness_context("e225-context", seed)
    register_worldbridge_deterministic_random_stream(
        context, "sr.war.respawn.decision", "python_random"
    )
    register_worldbridge_deterministic_random_stream(
        context, "sr.war.respawn.mind", "python_random"
    )
    return context


def test_two_stream_handoff_requires_distinct_python_streams() -> None:
    context = _two_stream_context()
    contract = validate_worldbridge_named_stream_sr_respawn_handoff(
        context, "sr.war.respawn.decision", "sr.war.respawn.mind"
    )
    assert contract["ordered_roles"] == ["decision", "mutation_if_admitted"]
    with pytest.raises(ValueError, match="must be distinct"):
        validate_worldbridge_named_stream_sr_respawn_handoff(
            context, "sr.war.respawn.mind", "sr.war.respawn.mind"
        )


def test_two_stream_handoff_rejection_consumes_only_decision_stream() -> None:
    context = _two_stream_context()
    before = context.snapshot()
    result = run_worldbridge_named_stream_sr_respawn_handoff(
        context,
        "sr.war.respawn.decision",
        "sr.war.respawn.mind",
        {"wander_amp": 20.0},
        0.25,
        0.0,
    )
    after = context.snapshot()
    assert result["admitted"] is False
    assert result["ordered_steps"] == ["decision"]
    assert result["mutation_stream_consumed"] is False
    assert after["streams"][0]["state"] != before["streams"][0]["state"]
    assert after["streams"][1]["state"] == before["streams"][1]["state"]


def test_two_stream_handoff_admission_is_deterministic_and_ordered() -> None:
    parent = {"wander_amp": 20.0, "gain_high_stress": 40.0, "mem_alpha": 0.3}
    first = run_worldbridge_named_stream_sr_respawn_handoff(
        _two_stream_context(),
        "sr.war.respawn.decision",
        "sr.war.respawn.mind",
        parent,
        0.25,
        1.0,
    )
    second = run_worldbridge_named_stream_sr_respawn_handoff(
        _two_stream_context(),
        "sr.war.respawn.decision",
        "sr.war.respawn.mind",
        parent,
        0.25,
        1.0,
    )
    assert first == second
    assert first["admitted"] is True
    assert first["ordered_steps"] == ["decision", "mutation"]
    assert first["mutation_stream_consumed"] is True


def test_viewport_two_stream_handoff_avoids_global_rng_and_status_stays_opt_in() -> None:
    viewport = SimpleNamespace()
    context = _two_stream_context()
    GameViewport.set_worldbridge_opt_in_respawn_random_streams(
        viewport,
        context,
        decision_stream_name="sr.war.respawn.decision",
        mutation_stream_name="sr.war.respawn.mind",
    )
    global_before = random.getstate()
    child, mutated = GameViewport._apply_sr_respawn_mind_mutation_if_admitted(
        viewport,
        {"wander_amp": 20.0, "gain_high_stress": 40.0, "mem_alpha": 0.3},
        0.25,
        1.0,
        "lineage",
        2,
        1.5,
    )
    assert random.getstate() == global_before
    assert mutated is True
    assert child["wander_amp"] != 20.0
    status = build_runtime_worldbridge_status()
    assert status["opt_in_respawn_two_stream_handoff_contract"] == (
        build_worldbridge_respawn_two_stream_handoff_contract()
    )
    assert status["default_ready"] is False
