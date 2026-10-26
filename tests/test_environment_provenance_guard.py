from __future__ import annotations

from pathlib import Path

from tools.check_environment_provenance import (
    calculate_lock_drift,
    classify_environment,
    read_lock_versions,
)


def test_classify_environment_prioritizes_conda_metadata() -> None:
    assert classify_environment(Path("C:/project/.venv"), Path("C:/Python"), True) == "conda_prefix"
    assert classify_environment(Path("C:/project/.venv"), Path("C:/project/.venv"), True) == "conda_prefix"


def test_classify_environment_recognizes_venv_without_conda_metadata() -> None:
    assert classify_environment(Path("C:/project/.venv"), Path("C:/Python"), False) == "stdlib_or_uv_venv"


def test_classify_environment_keeps_unknown_prefix_explicit() -> None:
    prefix = Path("C:/Python")
    assert classify_environment(prefix, prefix, False) == "standalone_or_unknown_prefix"


def test_read_lock_versions_extracts_package_table(tmp_path: Path) -> None:
    lock_path = tmp_path / "uv.lock"
    lock_path.write_text(
        'version = 1\n\n[[package]]\nname = "PyQt6"\nversion = "6.10.0"\n\n[[package]]\nname = "lotucosm-vitaloom"\nversion = "1.0.0"\n',
        encoding="utf-8",
    )

    assert read_lock_versions(lock_path) == {
        "pyqt6": "6.10.0",
        "lotucosm-vitaloom": "1.0.0",
    }


def test_calculate_lock_drift_only_reports_actual_differences() -> None:
    distributions = {
        "numpy": {"version": "2.4.6"},
        "PyQt6": {"version": "6.11.0"},
        "pytest": {"version": "9.1.1"},
        "missing": {"version": None},
    }
    lock_versions = {"numpy": "2.3.5", "pyqt6": "6.10.0", "pytest": "9.1.1"}

    assert calculate_lock_drift(distributions, lock_versions) == {
        "numpy": {"installed": "2.4.6", "locked": "2.3.5"},
        "PyQt6": {"installed": "6.11.0", "locked": "6.10.0"},
    }
