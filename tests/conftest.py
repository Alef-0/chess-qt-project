"""Pytest configuration and shared fixtures."""

import gc
import os
import sys
from pathlib import Path
import pytest

SRC_DIR = Path(__file__).parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """Ensure a single QApplication instance exists for the entire test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture(autouse=True)
def cleanup_qt(qapp):
    """Clean up Qt event loop and garbage collect after each test."""
    yield
    qapp.processEvents()
    gc.collect()
