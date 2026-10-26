"""PS component connection value object.

``Organism.connect_tools`` remains the owner API for registering an edge on a
component.  This object is only the edge payload used by optional systems such
as ``AssemblySystem``; it does not own an organism or introduce another tick
loop.  The serializer already understands edges exposing ``target``.
"""

from __future__ import annotations

from typing import Any


class Connection:
    """A directed PS component edge with explicit source and target owners."""

    __slots__ = ("source", "target", "id", "connection_type")

    def __init__(
        self,
        *,
        source: Any,
        target: Any,
        id: str,
        connection_type: str = "generic",
    ) -> None:
        if not isinstance(id, str) or not id:
            raise ValueError("connection id must be a non-empty string")
        self.source = source
        self.target = target
        self.id = id
        self.connection_type = str(connection_type)

    def update(self, delta_time: float = 1.0) -> None:
        """Forward the current source signal to the target when supported."""

        del delta_time
        process_signal = getattr(self.target, "process_signal", None)
        if not callable(process_signal):
            return
        signal = getattr(self.source, "output_signal", None)
        if signal is not None:
            process_signal(signal)

    def to_dict(self) -> dict[str, str]:
        """Return a stable diagnostic representation without object references."""

        return {
            "id": self.id,
            "connection_type": self.connection_type,
            "source_id": str(getattr(self.source, "id", "")),
            "target_id": str(getattr(self.target, "id", "")),
        }


__all__ = ["Connection"]
