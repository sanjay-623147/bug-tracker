"""Shared pytest fixtures for the DevCore Bug Tracker test suite."""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import database  # noqa: E402
import pythonanywhere_wsgi  # noqa: E402


@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    """Give every test a fresh seeded SQLite database in a temp directory."""
    db_file = tmp_path / "devcore_bugs_test.db"
    monkeypatch.setattr(database, "DB_FILE", str(db_file))
    database.init_db()
    database.seed_sample_data()
    return db_file
