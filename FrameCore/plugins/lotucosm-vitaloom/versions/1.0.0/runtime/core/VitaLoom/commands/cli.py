# -*- coding: utf-8 -*-
"""CLI adapter for the AI-native command registry."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from core.VitaLoom.commands.registry import command_error, get_command_registry


def main(
    argv: list[str] | None = None,
    *,
    capability_registry: object | None = None,
) -> int:
    parser = argparse.ArgumentParser(description="Run VitaLoom commands as JSON.")
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("list", help="List available commands.")
    describe = sub.add_parser("describe", help="Describe one command.")
    describe.add_argument("command_id")
    run = sub.add_parser("run", help="Run one command.")
    run.add_argument("command_id")
    run.add_argument("--json", default="{}", help="JSON payload string.")
    run.add_argument("--json-file", help="Read payload from a JSON file.")
    args = parser.parse_args(argv)

    from core.VitaLoom.core.runtime_capability_registry import (
        InMemoryRuntimeCapabilityRegistry,
        RUNTIME_CAPABILITY_REGISTRY_CONTEXT_KEY,
        require_runtime_capability_registry,
    )

    runtime_registry = (
        InMemoryRuntimeCapabilityRegistry()
        if capability_registry is None
        else require_runtime_capability_registry(capability_registry)
    )
    command_context = {
        RUNTIME_CAPABILITY_REGISTRY_CONTEXT_KEY: runtime_registry
    }
    registry = get_command_registry()
    if args.action == "list":
        _emit({"commands": registry.list()})
        return 0
    if args.action == "describe":
        try:
            _emit(registry.describe(args.command_id))
            return 0
        except KeyError:
            _emit(command_error("unknown_command", f"Unknown command: {args.command_id}"))
            return 1
    if args.action == "run":
        payload = _load_payload(args.json, args.json_file)
        if isinstance(payload, dict) and payload.get("ok") is False and payload.get("error"):
            _emit(payload)
            return 1
        result = registry.run(
            args.command_id, payload, context=command_context
        )
        _emit(result)
        return 0 if result.get("ok") else 1
    return 1


def _load_payload(raw_json: str, json_file: str | None) -> dict[str, Any]:
    try:
        if json_file:
            data = json.loads(Path(json_file).read_text(encoding="utf-8-sig"))
        else:
            data = json.loads(raw_json or "{}")
        if not isinstance(data, dict):
            return command_error("invalid_json_payload", "Payload must be a JSON object")
        return data
    except (OSError, json.JSONDecodeError) as exc:
        return command_error("invalid_json_payload", str(exc))


def _emit(data: dict[str, Any]) -> None:
    text = json.dumps(data, ensure_ascii=False, indent=2)
    print(text)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
