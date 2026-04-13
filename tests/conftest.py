"""Shared pytest fixtures.

`QT_QPA_PLATFORM=offscreen` must be set before PyQt6 is imported anywhere.
pytest loads conftest.py before test modules, so setting the env here
guarantees any QApplication created by tests runs headlessly (WSL, CI).
"""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")  # `setdefault` lets local devs override, e.g. QT_QPA_PLATFORM=xcb

import pytest
from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """Session-scoped QApplication for all GUI tests."""
    app = QApplication.instance() or QApplication([])
    yield app
