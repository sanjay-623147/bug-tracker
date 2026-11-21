"""
PythonAnywhere WSGI entry point for DevCore Bug Tracker.

The original `server.py` uses Python's built-in HTTP server, which cannot run
behind PythonAnywhere's WSGI web server. This file exposes the same routes as a
WSGI application so the project can be hosted on pythonanywhere.com without
adding any third-party dependencies.

Set the webapp's WSGI config file to import `application` from this module.
"""

import json
import mimetypes
import os
import urllib.parse
from datetime import datetime

import database

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Make sure the SQLite database exists and has the sample data before requests.
database.init_db()
database.seed_sample_data()


CORS_HEADERS = [
    ("Access-Control-Allow-Origin", "*"),
    ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
    ("Access-Control-Allow-Headers", "Content-Type"),
]


def _respond(start_response, status, body, content_type, extra_headers=None):
    """Send one WSGI response, always including Content-Length."""
    headers = [("Content-Type", content_type), ("Content-Length", str(len(body)))]
    headers.extend(CORS_HEADERS)
    if extra_headers:
        headers.extend(extra_headers)
    start_response(status, headers)
    return [body]


def _send_json(start_response, data, status="200 OK"):
    body = json.dumps(data, indent=2).encode("utf-8")
    return _respond(
        start_response,
        status,
        body,
        "application/json; charset=utf-8",
        [("Cache-Control", "no-store")],
    )


def _serve_static(start_response, path):
    """Serve files from static/, preventing traversal outside that directory."""
    relative = path.lstrip("/")
    if relative in ("", "index.html"):
        relative = "index.html"

    full_path = os.path.abspath(os.path.join(STATIC_DIR, relative))
    static_root = os.path.abspath(STATIC_DIR)
    if not (full_path == static_root or full_path.startswith(static_root + os.sep)):
        return _send_json(start_response, {"error": "Forbidden"}, "403 FORBIDDEN")
    if not os.path.isfile(full_path):
        return _send_json(start_response, {"error": "Not found"}, "404 NOT FOUND")

    with open(full_path, "rb") as handle:
        body = handle.read()

    content_type = mimetypes.guess_type(full_path)[0] or "application/octet-stream"
    if content_type.startswith("text/") or content_type in (
        "application/javascript",
        "application/json",
        "image/svg+xml",
    ):
        content_type += "; charset=utf-8"

    return _respond(start_response, "200 OK", body, content_type)


def _rows_to_dicts(cursor):
    return [dict(row) for row in cursor.fetchall()]


def _get_modules(start_response):
    conn = database.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM modules ORDER BY name")
        modules = _rows_to_dicts(cursor)
    finally:
        conn.close()
    return _send_json(start_response, modules)


def _get_bugs(start_response, query):
    conn = database.get_connection()
    try:
        cursor = conn.cursor()
        sql = "SELECT * FROM bugs WHERE 1=1"
        params = []

        filters = (
            ("status", "status"),
            ("severity", "severity"),
            ("maintenance", "maintenance_type"),
        )
        for key, column in filters:
            value = query.get(key, [None])[0]
            if value and value != "ALL":
                sql += f" AND {column} = ?"
                params.append(value)

        search = query.get("search", [None])[0]
        if search:
            term = f"%{search}%"
            sql += " AND (title LIKE ? OR bug_code LIKE ? OR module_name LIKE ?)"
            params.extend([term, term, term])

        sql += " ORDER BY id DESC"
        cursor.execute(sql, params)
        bugs = _rows_to_dicts(cursor)
    finally:
        conn.close()
    return _send_json(start_response, bugs)


def _get_bug(start_response, path):
    try:
        bug_id = int(path.split("/api/bugs/")[1])
    except (ValueError, IndexError):
        return _send_json(start_response, {"error": "Invalid bug id"}, "400 BAD REQUEST")

    conn = database.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bugs WHERE id = ?", (bug_id,))
        row = cursor.fetchone()
        if not row:
            return _send_json(start_response, {"error": "Bug not found"}, "404 NOT FOUND")

        bug = dict(row)
        cursor.execute(
            "SELECT * FROM bug_history WHERE bug_id = ? ORDER BY id ASC", (bug_id,)
        )
        bug["history"] = _rows_to_dicts(cursor)
    finally:
        conn.close()
    return _send_json(start_response, bug)


def _create_bug(start_response, payload):
    conn = database.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(id) FROM bugs")
        max_id = cursor.fetchone()[0] or 100
        bug_code = f"BUG-{max_id + 1}"
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            """
            INSERT INTO bugs (
                bug_code, title, module_name, maintenance_type, severity, priority,
                status, environment, reporter, assignee, description,
                steps_to_reproduce, expected_behavior, actual_behavior,
                created_at, reopen_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                bug_code,
                payload.get("title", "Untitled Defect"),
                payload.get("module_name", "General"),
                payload.get("maintenance_type", "Corrective"),
                payload.get("severity", "Medium"),
                payload.get("priority", "P3"),
                "New",
                payload.get("environment", "Web Browser"),
                payload.get("reporter", "G. Dheeraj (QA Lead)"),
                payload.get("assignee", "M. Sanjhay Baargav (Dev)"),
                payload.get("description", ""),
                payload.get("steps_to_reproduce", ""),
                payload.get("expected_behavior", ""),
                payload.get("actual_behavior", ""),
                now_str,
                0,
            ),
        )
        new_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO bug_history (bug_id, changed_by, old_status, new_status, comment, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                new_id,
                payload.get("reporter", "QA Tester"),
                "None",
                "New",
                "Bug reported and entered into lifecycle",
                now_str,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return _send_json(
        start_response, {"success": True, "id": new_id, "bug_code": bug_code}
    )


def _change_status(start_response, path, payload):
    try:
        parts = path.strip("/").split("/")
        bug_id = int(parts[2])
    except (ValueError, IndexError):
        return _send_json(start_response, {"error": "Invalid bug id"}, "400 BAD REQUEST")

    new_status = payload.get("new_status")
    changed_by = payload.get("changed_by", "DevCore Team")
    comment = payload.get("comment", f"Status changed to {new_status}")

    conn = database.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT status, reopen_count FROM bugs WHERE id = ?", (bug_id,)
        )
        row = cursor.fetchone()
        if not row:
            return _send_json(start_response, {"error": "Bug not found"}, "404 NOT FOUND")

        old_status = row["status"]
        reopen_count = row["reopen_count"]
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        resolved_at_sql = ""
        closed_at_sql = ""
        extra_params = []
        if new_status == "Resolved":
            resolved_at_sql = ", resolved_at = ?"
            extra_params.append(now_str)
        elif new_status == "Closed":
            closed_at_sql = ", closed_at = ?"
            extra_params.append(now_str)
        elif new_status == "Reopened":
            reopen_count += 1

        sql = (
            f"UPDATE bugs SET status = ?, reopen_count = ? "
            f"{resolved_at_sql} {closed_at_sql} WHERE id = ?"
        )
        cursor.execute(sql, [new_status, reopen_count] + extra_params + [bug_id])
        cursor.execute(
            """
            INSERT INTO bug_history (bug_id, changed_by, old_status, new_status, comment, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (bug_id, changed_by, old_status, new_status, comment, now_str),
        )
        conn.commit()
    finally:
        conn.close()

    return _send_json(
        start_response,
        {"success": True, "old_status": old_status, "new_status": new_status},
    )


def _reset_database(start_response):
    conn = database.get_connection()
    try:
        cursor = conn.cursor()
        for table in ("bug_history", "bugs", "modules"):
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
        conn.commit()
    finally:
        conn.close()

    database.init_db()
    database.seed_sample_data()
    return _send_json(
        start_response,
        {"success": True, "message": "Database reset to sample state successfully"},
    )


def application(environ, start_response):
    """WSGI entry point used by PythonAnywhere."""
    path = environ.get("PATH_INFO", "/") or "/"
    method = environ.get("REQUEST_METHOD", "GET").upper()

    if method == "OPTIONS":
        return _respond(start_response, "200 OK", b"", "text/plain")

    if method == "GET":
        if path == "/api/metrics":
            try:
                return _send_json(start_response, database.calculate_metrics())
            except Exception as exc:
                return _send_json(
                    start_response, {"error": str(exc)}, "500 INTERNAL SERVER ERROR"
                )
        if path == "/api/modules":
            return _get_modules(start_response)
        if path == "/api/bugs":
            query = urllib.parse.parse_qs(environ.get("QUERY_STRING", ""))
            return _get_bugs(start_response, query)
        if path.startswith("/api/bugs/"):
            return _get_bug(start_response, path)
        return _serve_static(start_response, path)

    if method == "POST":
        try:
            length = int(environ.get("CONTENT_LENGTH") or 0)
        except ValueError:
            length = 0
        raw = environ.get("wsgi.input").read(length).decode("utf-8") if length else ""
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            return _send_json(start_response, {"error": "Invalid JSON"}, "400 BAD REQUEST")

        try:
            if path == "/api/bugs":
                return _create_bug(start_response, payload)
            if path.endswith("/status"):
                return _change_status(start_response, path, payload)
            if path == "/api/reset":
                return _reset_database(start_response)
        except Exception as exc:
            return _send_json(
                start_response, {"error": str(exc)}, "500 INTERNAL SERVER ERROR"
            )
        return _send_json(start_response, {"error": "Unknown API endpoint"}, "404 NOT FOUND")

    return _send_json(start_response, {"error": "Method not allowed"}, "405 METHOD NOT ALLOWED")
