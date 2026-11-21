"""Tests for the PythonAnywhere WSGI application and its JSON API."""

import io
import json

from pythonanywhere_wsgi import application


def call_app(path="/", method="GET", query="", payload=None):
    """Call the WSGI app and return status, headers, body, and parsed JSON."""
    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": query,
    }

    raw_body = b""
    if payload is not None:
        raw_body = json.dumps(payload).encode("utf-8")
        environ["CONTENT_LENGTH"] = str(len(raw_body))
    else:
        environ["CONTENT_LENGTH"] = "0"
    environ["wsgi.input"] = io.BytesIO(raw_body)

    response = {}
    def start_response(status, headers, exc_info=None):
        response["status"] = status
        response["headers"] = headers

    response["body"] = b"".join(application(environ, start_response))
    try:
        response["json"] = json.loads(response["body"]) if response["body"] else None
    except json.JSONDecodeError:
        response["json"] = None
    return response


def header_value(response, name):
    return dict(response["headers"]).get(name)


def test_home_page_is_served():
    response = call_app("/")

    assert response["status"] == "200 OK"
    assert "text/html" in header_value(response, "Content-Type")
    assert response["body"].startswith(b"<!DOCTYPE html>")


def test_unknown_static_file_returns_404():
    response = call_app("/does-not-exist.css")

    assert response["status"] == "404 NOT FOUND"
    assert response["json"] == {"error": "Not found"}


def test_static_path_traversal_is_blocked():
    response = call_app("/../database.py")

    assert response["status"] == "403 FORBIDDEN"
    assert response["json"] == {"error": "Forbidden"}


def test_modules_endpoint_returns_sorted_modules():
    response = call_app("/api/modules")

    assert response["status"] == "200 OK"
    assert len(response["json"]) == 5
    names = [module["name"] for module in response["json"]]
    assert names == sorted(names)


def test_metrics_endpoint_returns_expected_payload():
    response = call_app("/api/metrics")

    assert response["status"] == "200 OK"
    assert response["json"]["total_bugs"] == 6
    assert response["json"]["dsi"] == 2.5
    assert header_value(response, "Cache-Control") == "no-store"
    assert header_value(response, "Access-Control-Allow-Origin") == "*"


def test_bugs_endpoint_filters_by_status():
    response = call_app("/api/bugs", query="status=New")

    assert response["status"] == "200 OK"
    assert len(response["json"]) == 1
    assert response["json"][0]["bug_code"] == "BUG-106"


def test_bugs_endpoint_filters_by_search_term():
    response = call_app("/api/bugs", query="search=payment")

    assert response["status"] == "200 OK"
    assert all(
        "payment" in (
            bug["title"] + bug["bug_code"] + bug["module_name"]
        ).lower()
        for bug in response["json"]
    )


def test_single_bug_includes_audit_history():
    response = call_app("/api/bugs/1")

    assert response["status"] == "200 OK"
    assert response["json"]["bug_code"] == "BUG-101"
    assert isinstance(response["json"]["history"], list)
    assert len(response["json"]["history"]) >= 1


def test_unknown_bug_returns_404():
    response = call_app("/api/bugs/9999")

    assert response["status"] == "404 NOT FOUND"
    assert response["json"] == {"error": "Bug not found"}


def test_create_bug_and_change_status():
    created = call_app(
        "/api/bugs",
        method="POST",
        payload={
            "title": "pytest smoke test bug",
            "module_name": "Test Module",
            "reporter": "pytest",
        },
    )

    assert created["status"] == "200 OK"
    assert created["json"]["success"] is True
    bug_id = created["json"]["id"]
    assert created["json"]["bug_code"] == f"BUG-{bug_id}"

    updated = call_app(
        f"/api/bugs/{bug_id}/status",
        method="POST",
        payload={"new_status": "Resolved", "changed_by": "pytest"},
    )

    assert updated["status"] == "200 OK"
    assert updated["json"]["old_status"] == "New"
    assert updated["json"]["new_status"] == "Resolved"

    fetched = call_app(f"/api/bugs/{bug_id}")
    assert fetched["json"]["status"] == "Resolved"
    assert fetched["json"]["resolved_at"] is not None
    assert len(fetched["json"]["history"]) >= 2


def test_reset_restores_sample_data():
    call_app(
        "/api/bugs",
        method="POST",
        payload={"title": "temporary bug", "reporter": "pytest"},
    )

    reset = call_app("/api/reset", method="POST")
    assert reset["status"] == "200 OK"
    assert reset["json"]["success"] is True

    metrics = call_app("/api/metrics")
    assert metrics["json"]["total_bugs"] == 6


def test_options_request_includes_cors_headers():
    response = call_app("/api/bugs", method="OPTIONS")

    assert response["status"] == "200 OK"
    assert header_value(response, "Access-Control-Allow-Origin") == "*"
    assert "POST" in header_value(response, "Access-Control-Allow-Methods")


def test_unknown_api_endpoint_returns_json_404():
    response = call_app("/api/unknown", method="POST", payload={})

    assert response["status"] == "404 NOT FOUND"
    assert response["json"] == {"error": "Unknown API endpoint"}
