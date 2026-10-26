from __future__ import annotations

import math
from typing import Any

import pytest

from core.Lotucosm.runtime.world_bridge_descriptor_contract import (
    DescriptorContractError,
    build_worldbridge_graph_descriptor,
    canonicalize_descriptor,
    descriptor_round_trip,
)


def test_descriptor_preserves_unknown_fields_and_list_order() -> None:
    descriptor = build_worldbridge_graph_descriptor(
        membrane_nodes=[{"id": "m-2", "unknown": {"z": 2, "a": 1}}, {"id": "m-1"}],
        component_nodes=[{"id": "c-1", "custom": ["x", {"keep": True}]}],
        edges=[{"source": "m-2", "target": "c-1", "weight": 0.5}],
        scripts=[{"id": "script-1", "properties": {"future": "kept"}}],
    )

    assert [item["id"] for item in descriptor["membrane_nodes"]] == ["m-2", "m-1"]
    assert descriptor["membrane_nodes"][0]["unknown"] == {"a": 1, "z": 2}
    assert descriptor["component_nodes"][0]["custom"] == ["x", {"keep": True}]
    assert descriptor["scripts"][0]["properties"]["future"] == "kept"


def test_descriptor_json_round_trip_is_lossless_for_descriptor_input() -> None:
    descriptor = build_worldbridge_graph_descriptor(
        membrane_nodes=[{"id": "膜-1", "properties": {"threshold": 1.25}}],
        edges=[{"source": "膜-1", "target": "c-1", "route": ["a", "b"]}],
    )
    assert descriptor_round_trip(descriptor) == descriptor


def test_canonicalization_rejects_non_finite_and_unsupported_values() -> None:
    with pytest.raises(DescriptorContractError, match="non-finite"):
        canonicalize_descriptor({"value": math.nan})
    with pytest.raises(DescriptorContractError, match="unsupported"):
        canonicalize_descriptor({"value": object()})


def test_canonicalization_rejects_non_string_keys() -> None:
    with pytest.raises(DescriptorContractError, match="non-string"):
        canonicalize_descriptor({"nested": {1: "invalid"}})  # type: ignore[dict-item]


def test_descriptor_is_data_only_and_does_not_claim_live_mapping() -> None:
    descriptor = build_worldbridge_graph_descriptor()
    assert descriptor["descriptor_state"] == "data_only"
    assert descriptor["read_only"] is True
    assert descriptor["maps_live_objects"] is False
    assert descriptor["lossless_for_descriptor_input"] is True
    assert descriptor["preservation"]["live_mutation"] == "forbidden"
