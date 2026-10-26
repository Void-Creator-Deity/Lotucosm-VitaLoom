# -*- coding: utf-8 -*-
from __future__ import annotations

from core.VitaLoom.viewports.opengl_batching import compile_opengl_batches
from core.VitaLoom.viewports.viewport_draw_commands import CircleCommand, LineCommand


def test_compile_opengl_batches_groups_by_primitive_and_style() -> None:
    commands = (
        CircleCommand(
            kind="circle",
            entity_id="a",
            center=(1.0, 2.0),
            radius=3.0,
            fill=(10, 20, 30, 255),
            stroke=(0, 0, 0, 255),
            stroke_width=1.0,
        ),
        CircleCommand(
            kind="circle",
            entity_id="b",
            center=(5.0, 6.0),
            radius=4.0,
            fill=(10, 20, 30, 255),
            stroke=(0, 0, 0, 255),
            stroke_width=1.0,
        ),
        LineCommand(
            kind="line",
            edge_id="a:b",
            start=(1.0, 2.0),
            end=(5.0, 6.0),
            color=(80, 90, 100, 255),
            width=2.0,
        ),
    )

    batches = compile_opengl_batches(commands)

    assert [batch.primitive for batch in batches] == ["line", "circle"]
    assert batches[0].style_key == ("line", (80, 90, 100, 255), 2.0)
    assert batches[0].instance_count == 1
    assert batches[1].style_key == ("circle", (10, 20, 30, 255), (0, 0, 0, 255), 1.0)
    assert batches[1].instance_count == 2


def test_compile_opengl_batches_keeps_deterministic_payloads() -> None:
    commands = (
        LineCommand(
            kind="line",
            edge_id="b:c",
            start=(3.0, 4.0),
            end=(5.0, 6.0),
            color=(1, 2, 3, 4),
            width=1.5,
        ),
        CircleCommand(
            kind="circle",
            entity_id="a",
            center=(1.0, 2.0),
            radius=3.0,
            fill=(9, 8, 7, 6),
            stroke=(5, 4, 3, 2),
            stroke_width=1.0,
        ),
    )

    batches = compile_opengl_batches(commands)

    assert batches[0].ids == ("b:c",)
    assert batches[0].instances == ((3.0, 4.0, 5.0, 6.0),)
    assert batches[1].ids == ("a",)
    assert batches[1].instances == ((1.0, 2.0, 3.0),)


def test_compile_opengl_batches_preserves_semantic_draw_order() -> None:
    commands = (
        LineCommand(
            kind="line",
            edge_id="behind",
            start=(0.0, 0.0),
            end=(10.0, 10.0),
            color=(255, 255, 255, 255),
            width=2.0,
        ),
        CircleCommand(
            kind="circle",
            entity_id="base",
            center=(5.0, 5.0),
            radius=4.0,
            fill=(10, 20, 30, 255),
            stroke=(0, 0, 0, 255),
            stroke_width=1.0,
        ),
        CircleCommand(
            kind="circle",
            entity_id="base:selected",
            center=(5.0, 5.0),
            radius=7.0,
            fill=(0, 0, 0, 0),
            stroke=(255, 230, 110, 255),
            stroke_width=2.0,
        ),
    )

    batches = compile_opengl_batches(commands)

    assert [batch.ids for batch in batches] == [("behind",), ("base",), ("base:selected",)]
