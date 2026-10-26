# -*- coding: utf-8 -*-
from __future__ import annotations

import pytest

from core.VitaLoom.viewports.opengl_batching import compile_opengl_batches
from core.VitaLoom.viewports.viewport_draw_commands import (
    CircleCommand,
    LineCommand,
    compile_viewport_draw_commands,
)
from core.VitaLoom.viewports.viewport_snapshot import (
    ViewportEdgeSnapshot,
    ViewportEntitySnapshot,
    ViewportFrameSnapshot,
)


def _scene(name: str) -> ViewportFrameSnapshot:
    if name == "empty":
        return ViewportFrameSnapshot(width=320, height=240)
    if name == "single":
        return ViewportFrameSnapshot(
            width=320,
            height=240,
            entities=(ViewportEntitySnapshot(id="a", entity_type="organism", position=(10.0, 20.0), radius=5.0),),
        )
    if name == "selected":
        return ViewportFrameSnapshot(
            width=320,
            height=240,
            entities=(
                ViewportEntitySnapshot(
                    id="a",
                    entity_type="organism",
                    position=(10.0, 20.0),
                    radius=5.0,
                    selected=True,
                ),
            ),
        )
    if name == "edge":
        return ViewportFrameSnapshot(
            width=320,
            height=240,
            entities=(
                ViewportEntitySnapshot(id="a", entity_type="organism", position=(10.0, 20.0), radius=5.0),
                ViewportEntitySnapshot(id="b", entity_type="nutrient", position=(30.0, 40.0), radius=6.0),
            ),
            edges=(ViewportEdgeSnapshot(source_id="a", target_id="b", kind="hard"),),
        )
    if name == "dense":
        return ViewportFrameSnapshot(
            width=640,
            height=480,
            entities=tuple(
                ViewportEntitySnapshot(
                    id=f"e{i:03d}",
                    entity_type="organism" if i % 2 == 0 else "nutrient",
                    position=(float(i % 20) * 12.0, float(i // 20) * 12.0),
                    radius=4.0 + float(i % 3),
                )
                for i in range(100)
            ),
        )
    if name == "hidden":
        return ViewportFrameSnapshot(
            width=320,
            height=240,
            entities=(
                ViewportEntitySnapshot(id="a", entity_type="organism", position=(10.0, 20.0), radius=5.0),
                ViewportEntitySnapshot(id="b", entity_type="nutrient", position=(30.0, 40.0), radius=6.0, visible=False),
            ),
            edges=(ViewportEdgeSnapshot(source_id="a", target_id="b", kind="hard"),),
        )
    raise AssertionError(name)


@pytest.mark.parametrize("scene_name", ["empty", "single", "selected", "edge", "dense", "hidden"])
def test_opengl_batches_preserve_qpainter_command_semantics(scene_name: str) -> None:
    commands = compile_viewport_draw_commands(_scene(scene_name))
    batches = compile_opengl_batches(commands)

    command_circle_ids = tuple(command.entity_id for command in commands if isinstance(command, CircleCommand))
    batch_circle_ids = tuple(
        item_id
        for batch in batches
        if batch.primitive == "circle"
        for item_id in batch.ids
    )
    command_line_ids = tuple(command.edge_id for command in commands if isinstance(command, LineCommand))
    batch_line_ids = tuple(
        item_id
        for batch in batches
        if batch.primitive == "line"
        for item_id in batch.ids
    )

    assert sorted(batch_circle_ids) == sorted(command_circle_ids)
    assert sorted(batch_line_ids) == sorted(command_line_ids)
    assert sum(batch.instance_count for batch in batches) == len(commands)


def test_selected_outline_semantics_survive_batching() -> None:
    commands = compile_viewport_draw_commands(_scene("selected"))
    batches = compile_opengl_batches(commands)

    assert any(
        batch.primitive == "circle" and "a:selected" in batch.ids
        for batch in batches
    )

