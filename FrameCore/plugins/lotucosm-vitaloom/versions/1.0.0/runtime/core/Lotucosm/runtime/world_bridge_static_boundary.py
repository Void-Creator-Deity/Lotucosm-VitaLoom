from __future__ import annotations

"""Static guard for the WorldBridge live-mapping boundary.

The current bridge is intentionally a read-only projection plus narrowly
admitted hand-off code.  This guard scans that integration surface so a future
change cannot silently construct or mutate PS components, membrane graphs, or
connection objects without first changing the admission contract.
"""

import ast
from pathlib import Path
from typing import Iterable


# These are mutation/creation seams owned by the PS component and membrane
# systems.  They are not legal in the WorldBridge integration surface while
# the admission verifier reports no admitted fields.
_FORBIDDEN_CALLS = frozenset(
    {
        "add_connection",
        "attach_component",
        "connect",
        "create_component",
        "disconnect",
        "ingest",
        "mutate",
        "mutate_signal_edges",
        "process_signal",
        "remove_component",
        "set_component",
    }
)
_FORBIDDEN_IMPORT_TOKENS = (
    "ComponentFactory",
    "core.Lotucosm.component",
    "builtin.components",
)
_FORBIDDEN_ATTRIBUTE_WRITES = frozenset(
    {
        "components",
        "connections",
        "live_components",
        "live_connection",
        "live_connections",
        "membrane_graph",
        "connection_graph",
    }
)


def _surface_files(runtime_root: Path) -> tuple[Path, ...]:
    runtime = runtime_root / "core" / "Lotucosm" / "runtime"
    if not runtime.is_dir():
        return ()
    files = [runtime / "world_bridge.py", runtime / "runtime_snapshot_component_projection.py"]
    files.extend(sorted(runtime.glob("world_bridge_*.py")))
    # Fact corpus construction is a separate read-only probe, not bridge integration.
    files = [path for path in files if path.name not in {"world_bridge_ps_component_corpus.py", "world_bridge_ps_graph_corpus.py"}]
    return tuple(dict.fromkeys(path for path in files if path.is_file()))


def _call_name(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _line(source: str, lineno: int) -> str:
    lines = source.splitlines()
    return lines[lineno - 1].strip() if 0 < lineno <= len(lines) else ""


def scan_worldbridge_live_mapping_boundary(runtime_root: Path) -> dict[str, object]:
    """Return deterministic violations found in the bridge integration files."""
    violations: list[dict[str, object]] = []
    files = _surface_files(runtime_root)
    for path in files:
        try:
            source = path.read_text(encoding="utf-8-sig")
            tree = ast.parse(source, filename=str(path))
        except (OSError, SyntaxError) as exc:
            violations.append({"file": str(path), "line": 1, "kind": "parse_error", "detail": str(exc)})
            continue
        rel = path.relative_to(runtime_root).as_posix()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = node.names
                imported = ",".join(alias.name for alias in names)
                module = node.module if isinstance(node, ast.ImportFrom) else ""
                text = f"{module} {imported}"
                for token in _FORBIDDEN_IMPORT_TOKENS:
                    if token in text:
                        violations.append({"file": rel, "line": node.lineno, "kind": "forbidden_import", "detail": token})
            elif isinstance(node, ast.Call):
                name = _call_name(node)
                if name in _FORBIDDEN_CALLS:
                    violations.append({"file": rel, "line": node.lineno, "kind": "forbidden_call", "detail": name})
            elif isinstance(node, ast.Assign):
                targets: Iterable[ast.expr] = node.targets
                for target in targets:
                    if isinstance(target, ast.Attribute) and target.attr in _FORBIDDEN_ATTRIBUTE_WRITES:
                        violations.append({"file": rel, "line": node.lineno, "kind": "forbidden_attribute_write", "detail": target.attr})
            elif isinstance(node, ast.AnnAssign):
                target = node.target
                if isinstance(target, ast.Attribute) and target.attr in _FORBIDDEN_ATTRIBUTE_WRITES:
                    violations.append({"file": rel, "line": node.lineno, "kind": "forbidden_attribute_write", "detail": target.attr})
        # Keep source text in the result only for human diagnosis, never as a
        # second source of matching rules.
        for violation in violations:
            if violation["file"] == rel:
                violation["source"] = _line(source, int(violation["line"]))
    violations.sort(key=lambda item: (str(item["file"]), int(item["line"]), str(item["kind"]), str(item["detail"])))
    return {
        "schema_version": 1,
        "status": "worldbridge_static_live_mapping_boundary",
        "read_only": True,
        "scanned_files": [path.relative_to(runtime_root).as_posix() for path in files],
        "violations": violations,
        "valid": not violations,
        "live_adapter_admitted": False,
        "admission_verifier_required": True,
    }


__all__ = ["scan_worldbridge_live_mapping_boundary"]



