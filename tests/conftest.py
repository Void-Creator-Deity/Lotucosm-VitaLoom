"""Keep legacy top-level test-module imports valid inside the test package."""

from __future__ import annotations

import os
import gc
import sys
from pathlib import Path

import pytest


TEST_ROOT = Path(__file__).resolve().parent
REPO_ROOT = TEST_ROOT.parent
RUNTIME_ROOT = (
    REPO_ROOT
    / "FrameCore"
    / "plugins"
    / "lotucosm-vitaloom"
    / "versions"
    / "1.0.0"
    / "runtime"
)
SUITE_ROOT = RUNTIME_ROOT.parent.parent.parent
for path in (TEST_ROOT, REPO_ROOT, RUNTIME_ROOT, SUITE_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


@pytest.fixture(scope="session", autouse=True)
def shared_qapplication():
    """Keep one QApplication alive for the full GUI test process.

    Creating and destroying QApplication repeatedly across test modules causes
    order-dependent Qt6Core BEX64 exits on Windows. The fixture does not move
    application ownership into production code; it only stabilizes test-host
    lifetime.
    """
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PyQt6.QtWidgets import QApplication
    except ImportError:
        yield None
        return

    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    yield app
    app.processEvents()


@pytest.fixture(autouse=True)
def cleanup_qt_objects(shared_qapplication):
    """Release test-created QObjects before the next test mutates Qt state."""
    yield
    if shared_qapplication is None:
        gc.collect()
        return
    from PyQt6.QtCore import QCoreApplication, QEvent

    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    shared_qapplication.processEvents()
    gc.collect()
