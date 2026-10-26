# -*- coding: utf-8 -*-
from __future__ import annotations

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


def test_compile_entities_and_edges_into_stable_draw_commands() -> None:
    frame = ViewportFrameSnapshot(
        width=320,
        height=240,
        entities=(
            ViewportEntitySnapshot(
                id="b",
                entity_type="nutrient",
                position=(20.0, 30.0),
                radius=5.0,
            ),
            ViewportEntitySnapshot(
                id="a",
                entity_type="organism",
                position=(10.0, 15.0),
                radius=8.0,
                selected=True,
            ),
        ),
        edges=(ViewportEdgeSnapshot(source_id="a", target_id="b", kind="hard"),),
    )

    commands = compile_viewport_draw_commands(frame)

    assert [command.kind for command in commands] == ["line", "circle", "circle", "circle"]
    assert isinstance(commands[0], LineCommand)
    assert isinstance(commands[1], CircleCommand)
    assert commands[0].edge_id == "a:b"
    assert commands[1].entity_id == "a"
    assert commands[2].entity_id == "a:selected"
    assert commands[3].entity_id == "b"


def test_compile_skips_hidden_entities_and_unresolved_edges() -> None:
    frame = ViewportFrameSnapshot(
        width=320,
        height=240,
        entities=(
            ViewportEntitySnapshot(
                id="visible",
                entity_type="sensor",
                position=(1.0, 2.0),
                radius=3.0,
            ),
            ViewportEntitySnapshot(
                id="hidden",
                entity_type="actuator",
                position=(3.0, 4.0),
                radius=5.0,
                visible=False,
            ),
        ),
        edges=(
            ViewportEdgeSnapshot(source_id="visible", target_id="hidden", kind="hard"),
            ViewportEdgeSnapshot(source_id="visible", target_id="missing", kind="signal"),
        ),
    )

    commands = compile_viewport_draw_commands(frame)

    assert len(commands) == 1
    assert isinstance(commands[0], CircleCommand)
    assert commands[0].entity_id == "visible"


def test_compile_uses_visual_state_color_and_freezes_plain_tuples() -> None:
    frame = ViewportFrameSnapshot(
        width=320,
        height=240,
        entities=(
            ViewportEntitySnapshot(
                id="custom",
                entity_type="organism",
                position=(1.0, 2.0),
                radius=3.0,
                visual_state={"fill": [1, 2, 3, 4], "stroke": (5, 6, 7, 8)},
            ),
        ),
    )

    commands = compile_viewport_draw_commands(frame)

    assert commands[0].fill == (1, 2, 3, 4)
    assert commands[0].stroke == (5, 6, 7, 8)
