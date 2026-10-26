from __future__ import annotations

import pytest


def test_identity_source_is_repeatable_and_domain_scoped():
    from core.Lotucosm.runtime.deterministic_identity import DeterministicIdentitySource

    first = DeterministicIdentitySource("e416")
    second = DeterministicIdentitySource("e416")
    assert [first.next("ps"), first.next("sr"), first.next("ps")] == [
        second.next("ps"), second.next("sr"), second.next("ps")
    ]


def test_identity_source_snapshot_restore_is_atomic_and_seed_bound():
    from core.Lotucosm.runtime.deterministic_identity import DeterministicIdentitySource

    source = DeterministicIdentitySource("e416")
    source.next("ps")
    snapshot = source.snapshot()
    expected = source.next("ps")
    restored = DeterministicIdentitySource("e416")
    restored.restore(snapshot)
    assert restored.next("ps") == expected
    with pytest.raises(ValueError, match="seed mismatch"):
        DeterministicIdentitySource("other").restore(snapshot)


def test_snapshot_authorities_accept_caller_owned_identity_source():
    from core.Lotucosm.runtime.deterministic_identity import DeterministicIdentitySource
    from core.Lotucosm.runtime.ps_runtime_snapshot_authority import PsRuntimeSnapshotAuthority
    from core.VitaLoom.simulation.sr_runtime_snapshot_authority import SrRuntimeSnapshotAuthority

    ps_source = DeterministicIdentitySource("shared")
    sr_source = DeterministicIdentitySource("shared")
    ps = PsRuntimeSnapshotAuthority(identity_source=ps_source)
    sr = SrRuntimeSnapshotAuthority(identity_source=sr_source)
    assert ps.begin() == PsRuntimeSnapshotAuthority(identity_source=DeterministicIdentitySource("shared")).begin()
    assert sr.begin("scene.pond") == SrRuntimeSnapshotAuthority(identity_source=DeterministicIdentitySource("shared")).begin("scene.pond")


def test_entity_and_runtime_factory_accept_caller_owned_identity_source():
    from core.Lotucosm.runtime.deterministic_identity import DeterministicIdentitySource
    from core.Lotucosm.entity import EntityBase
    from core.Lotucosm.runtime_entities import instantiate_entity
    from core.Lotucosm.pond import Pond

    source = DeterministicIdentitySource("entities")
    first = EntityBase(identity_source=source)
    second = EntityBase(identity_source=source)
    assert first.id != second.id
    assert first.id.startswith("entity_")

    pond = Pond(initialize=False, initial_organisms=0, initial_components=0)
    created = instantiate_entity("other", pond, identity_source=source)
    assert created.id.startswith("entity_")
    assert source.snapshot()["counters"]["entity"] == 3


def test_runtime_factory_identity_is_repeatable_for_same_source_seed():
    from core.Lotucosm.runtime.deterministic_identity import DeterministicIdentitySource
    from core.Lotucosm.runtime_entities import instantiate_entity
    from core.Lotucosm.pond import Pond

    def create(seed):
        source = DeterministicIdentitySource(seed)
        pond = Pond(initialize=False, initial_organisms=0, initial_components=0)
        return instantiate_entity("organism", pond, identity_source=source).id

    assert create("repeatable") == create("repeatable")


def test_script_instantiation_inherits_pond_identity_source():
    from core.Lotucosm.pond import Pond
    from core.Lotucosm.runtime.deterministic_identity import DeterministicIdentitySource
    from core.Lotucosm.scripts import ScriptBase

    pond = Pond(initialize=False, initial_organisms=0, initial_components=0)
    pond.identity_source = DeterministicIdentitySource("script-entities")

    class Host:
        def __init__(self):
            self.position = (4.0, 5.0)
            self.pond = pond

    created = ScriptBase()
    created.entity = Host()
    entity = created.instantiate("other")
    assert entity is not None
    assert entity.id == DeterministicIdentitySource("script-entities").next("entity")


def test_runtime_factory_compensates_identity_and_registration_failure():
    from core.Lotucosm.runtime.deterministic_identity import DeterministicIdentitySource
    from core.Lotucosm.runtime_entities import instantiate_entity

    class FailingPond:
        def __init__(self):
            self.root_entities = []

        def add_entity(self, entity):
            self.root_entities.append(entity)
            raise RuntimeError("injected registration failure")

        def remove_entity(self, entity):
            if entity in self.root_entities:
                self.root_entities.remove(entity)

    source = DeterministicIdentitySource("compensate")
    pond = FailingPond()
    assert instantiate_entity("other", pond, identity_source=source) is None
    assert source.snapshot()["counters"] == {}
    assert pond.root_entities == []
