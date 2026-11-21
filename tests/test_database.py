"""Unit tests for the SQLite database and metrics engine."""

import sqlite3

import database


def test_init_db_creates_expected_tables(isolated_database):
    with sqlite3.connect(isolated_database) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }

    assert {"modules", "bugs", "bug_history"} <= tables


def test_seed_sample_data_populates_expected_records(isolated_database):
    with sqlite3.connect(isolated_database) as conn:
        module_count = conn.execute("SELECT COUNT(*) FROM modules").fetchone()[0]
        bug_count = conn.execute("SELECT COUNT(*) FROM bugs").fetchone()[0]
        history_count = conn.execute("SELECT COUNT(*) FROM bug_history").fetchone()[0]

    assert module_count == 5
    assert bug_count == 6
    assert history_count >= 6


def test_seed_sample_data_is_idempotent():
    database.seed_sample_data()

    with database.get_connection() as conn:
        bug_count = conn.execute("SELECT COUNT(*) FROM bugs").fetchone()[0]

    assert bug_count == 6


def test_calculate_metrics_returns_expected_values():
    metrics = database.calculate_metrics()

    assert metrics["total_bugs"] == 6
    assert metrics["open_bugs"] == 4
    assert metrics["resolved_bugs"] == 1
    assert metrics["closed_bugs"] == 1
    assert metrics["dsi"] == 2.5
    assert metrics["reopen_rate"] == 33.3
    assert round(metrics["total_kloc"], 2) == 22.0
    assert len(metrics["module_density"]) == 5
