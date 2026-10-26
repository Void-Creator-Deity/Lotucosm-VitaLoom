# -*- coding: utf-8
"""Opt-in transaction boundary for one live WorldBridge handoff.

The object wraps the existing ordered handoff instead of creating another
tick loop. It captures all live checkpoint owners before the first input or
field mutation, and delegates recovery to the existing checkpoint coordinator
plus its identity-preserving Pond owner hook.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import Any, Callable

from .world_bridge_live_checkpoint import (
    WorldBridgeLiveCheckpointCoordinator,
    WorldBridgeLiveTransactionCheckpoint,
)


STATUS = "worldbridge_opt_in_live_handoff_transaction"


class WorldBridgeLiveHandoffTransaction:
    """One-shot pre-mutation capture and compensating rollback."""

    def __init__(
        self,
        coordinator: WorldBridgeLiveCheckpointCoordinator,
        *,
        checkpoint_id: str,
        sequence: int,
    ) -> None:
        if not isinstance(coordinator, WorldBridgeLiveCheckpointCoordinator):
            raise TypeError("coordinator must be a live checkpoint coordinator")
        if not isinstance(checkpoint_id, str) or not checkpoint_id:
            raise ValueError("checkpoint_id must be non-empty")
        if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
            raise ValueError("sequence must be a non-negative integer")
        self._coordinator = coordinator
        self._checkpoint_id = checkpoint_id
        self._sequence = sequence
        self._snapshot: WorldBridgeLiveTransactionCheckpoint | None = None
        self._rollback_report: dict[str, Any] | None = None

    @property
    def started(self) -> bool:
        return self._snapshot is not None

    @property
    def rollback_report(self) -> Mapping[str, Any] | None:
        return copy.deepcopy(self._rollback_report)

    def begin(self) -> Mapping[str, Any]:
        if self._snapshot is not None:
            raise RuntimeError("WorldBridge live handoff transaction already started")
        self._snapshot = self._coordinator.capture_transaction(
            checkpoint_id=self._checkpoint_id,
            sequence=self._sequence,
            handoff_scope=True,
        )
        return copy.deepcopy(dict(self._snapshot.checkpoint))

    def rollback(self) -> dict[str, Any]:
        if self._snapshot is None:
            report = self._build_report(
                attempted=False,
                complete=False,
                error="transaction was not started",
            )
            self._rollback_report = report
            return copy.deepcopy(report)
        if self._rollback_report is not None:
            return copy.deepcopy(self._rollback_report)
        try:
            restore = self._coordinator.restore(
                self._snapshot.checkpoint,
                live_ps_state=self._snapshot.live_ps_state,
                transactional_ps=True,
                tick_binding=self._snapshot.tick_binding,
                tick_scope=self._snapshot.tick_scope,
                allow_active_tick=self._snapshot.tick_scope is not None,
            )
        except Exception as exc:
            report = self._build_report(
                attempted=True,
                complete=False,
                error=f"{type(exc).__name__}: {exc}",
            )
            report["restore_report"] = getattr(exc, "report", None)
        else:
            report = self._build_report(
                attempted=True,
                complete=restore.get("transaction_verified") is True,
                error=None,
            )
            report["restore_report"] = restore
        self._rollback_report = report
        return copy.deepcopy(report)

    def _build_report(
        self,
        *,
        attempted: bool,
        complete: bool,
        error: str | None,
    ) -> dict[str, Any]:
        report: dict[str, Any] = {
            "schema_version": 1,
            "status": STATUS,
            "transactional_ps": True,
            "capture_completed": self._snapshot is not None,
            "rollback_attempted": attempted,
            "rollback_complete": complete,
            "rollback_performed": attempted,
            "cross_lane_transaction": complete,
            "atomic_checkpoint": False,
            "replay_admitted": False,
            "lossless_mapping": False,
            "default_ready": False,
        }
        if self._snapshot is not None:
            report["checkpoint_id"] = self._snapshot.checkpoint.get("checkpoint_id")
            report["checkpoint_digest"] = self._snapshot.checkpoint.get("digest")
            report["captured_live_ps_state_digest"] = self._snapshot.live_ps_state_digest
        if error is not None:
            report["rollback_error"] = error
        return report


def create_worldbridge_live_handoff_transaction(
    coordinator: WorldBridgeLiveCheckpointCoordinator,
    *,
    checkpoint_id: str,
    sequence: int,
) -> WorldBridgeLiveHandoffTransaction:
    return WorldBridgeLiveHandoffTransaction(
        coordinator,
        checkpoint_id=checkpoint_id,
        sequence=sequence,
    )


def execute_worldbridge_handoff_with_transaction(
    transaction: WorldBridgeLiveHandoffTransaction,
    handoff: Callable[[], Any],
) -> Any:
    """Execute one handoff and compensate every failure after begin()."""
    try:
        return handoff()
    except BaseException as failure:
        try:
            rollback_report = transaction.rollback()
        except BaseException as rollback_failure:
            rollback_report = {
                "schema_version": 1,
                "status": STATUS,
                "rollback_attempted": True,
                "rollback_complete": False,
                "rollback_performed": True,
                "atomic_checkpoint": False,
                "rollback_error": (
                    f"{type(rollback_failure).__name__}: {rollback_failure}"
                ),
            }
        from .world_bridge_transaction_authority import WorldBridgeHandoffFailure

        if isinstance(failure, WorldBridgeHandoffFailure):
            failure.attach_transaction_rollback(rollback_report)
        else:
            setattr(failure, "worldbridge_transaction_rollback", rollback_report)
        raise


__all__ = [
    "STATUS",
    "WorldBridgeLiveHandoffTransaction",
    "create_worldbridge_live_handoff_transaction",
    "execute_worldbridge_handoff_with_transaction",
]
