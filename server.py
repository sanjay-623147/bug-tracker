"""
DevCore BugTracker - Web Application Server
Team: DevCore
Members: M. Sanjhay Baargav (623147) & G. Dheeraj (623192)
Department: B.Tech ECE 4th Year

This server uses ONLY Python's built-in standard library (http.server).
ZERO EXTERNAL INSTALLATION REQUIRED:
Runs out-of-the-box on any Windows/Linux/Mac PC with Python 3.
"""

import http.server
import socketserver
import json
import os
import urllib.parse
from datetime import datetime
import webbrowser
import database

PORT = 8000
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

class DevCoreAPIHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def _send_json(self, data, status_code=200):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # 1. API Endpoint: Metrics & Analytics (Outcome 4)
        if path == "/api/metrics":
            try:
                metrics = database.calculate_metrics()
                self._send_json(metrics)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
            return

        # 2. API Endpoint: Modules List
        if path == "/api/modules":
            conn = database.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM modules ORDER BY name")
            modules = [dict(row) for row in cursor.fetchall()]
            conn.close()
            self._send_json(modules)
            return

        # 3. API Endpoint: List All Bugs with optional filters (Outcome 3)
        if path == "/api/bugs":
            conn = database.get_connection()
            cursor = conn.cursor()

            sql = "SELECT * FROM bugs WHERE 1=1"
            params = []

            if "status" in query and query["status"][0] and query["status"][0] != "ALL":
                sql += " AND status = ?"
                params.append(query["status"][0])

            if "severity" in query and query["severity"][0] and query["severity"][0] != "ALL":
                sql += " AND severity = ?"
                params.append(query["severity"][0])

            if "maintenance" in query and query["maintenance"][0] and query["maintenance"][0] != "ALL":
                sql += " AND maintenance_type = ?"
                params.append(query["maintenance"][0])

            if "search" in query and query["search"][0]:
                search_term = f"%{query['search'][0]}%"
                sql += " AND (title LIKE ? OR bug_code LIKE ? OR module_name LIKE ?)"
                params.extend([search_term, search_term, search_term])

            sql += " ORDER BY id DESC"
            cursor.execute(sql, params)
            bugs = [dict(row) for row in cursor.fetchall()]
            conn.close()
            self._send_json(bugs)
            return

        # 4. API Endpoint: Single Bug Details + Audit History
        if path.startswith("/api/bugs/"):
            try:
                bug_id = int(path.split("/api/bugs/")[1])
                conn = database.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM bugs WHERE id = ?", (bug_id,))
                bug_row = cursor.fetchone()
                if not bug_row:
                    conn.close()
                    self._send_json({"error": "Bug not found"}, 404)
                    return

                bug = dict(bug_row)
                cursor.execute("SELECT * FROM bug_history WHERE bug_id = ? ORDER BY id ASC", (bug_id,))
                bug["history"] = [dict(r) for r in cursor.fetchall()]
                conn.close()
                self._send_json(bug)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
            return

        # 5. Fallback: Serve static UI files (index.html, styles, scripts)
        if path == "/" or path == "":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Read JSON body
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode("utf-8")
        payload = json.loads(post_data) if post_data else {}

        # 1. API Endpoint: Create a New Bug (Outcome 3: Issue Reporting)
        if path == "/api/bugs":
            try:
                conn = database.get_connection()
                cursor = conn.cursor()

                # Generate next bug code e.g. BUG-107
                cursor.execute("SELECT MAX(id) FROM bugs")
                max_id = cursor.fetchone()[0] or 100
                bug_code = f"BUG-{max_id + 1}"

                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                cursor.execute("""
                INSERT INTO bugs (
                    bug_code, title, module_name, maintenance_type, severity, priority,
                    status, environment, reporter, assignee, description,
                    steps_to_reproduce, expected_behavior, actual_behavior,
                    created_at, reopen_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
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
                    0
                ))
                new_id = cursor.lastrowid

                # Create initial audit log entry
                cursor.execute("""
                INSERT INTO bug_history (bug_id, changed_by, old_status, new_status, comment, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    new_id,
                    payload.get("reporter", "QA Tester"),
                    "None",
                    "New",
                    "Bug reported and entered into lifecycle",
                    now_str
                ))

                conn.commit()
                conn.close()
                self._send_json({"success": True, "id": new_id, "bug_code": bug_code})
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
            return

        # 2. API Endpoint: Change Bug Life Cycle Status (Outcome 2: Workflow transitions)
        if path.endswith("/status"):
            try:
                parts = path.split("/")
                bug_id = int(parts[2])
                new_status = payload.get("new_status")
                changed_by = payload.get("changed_by", "DevCore Team")
                comment = payload.get("comment", f"Status changed to {new_status}")

                conn = database.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT status, reopen_count FROM bugs WHERE id = ?", (bug_id,))
                row = cursor.fetchone()
                if not row:
                    conn.close()
                    self._send_json({"error": "Bug not found"}, 404)
                    return

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

                sql = f"UPDATE bugs SET status = ?, reopen_count = ? {resolved_at_sql} {closed_at_sql} WHERE id = ?"
                cursor.execute(sql, [new_status, reopen_count] + extra_params + [bug_id])

                cursor.execute("""
                INSERT INTO bug_history (bug_id, changed_by, old_status, new_status, comment, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (bug_id, changed_by, old_status, new_status, comment, now_str))

                conn.commit()
                conn.close()
                self._send_json({"success": True, "old_status": old_status, "new_status": new_status})
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
            return

        # 3. API Endpoint: Reset Database to Default Sample Data
        if path == "/api/reset":
            try:
                conn = database.get_connection()
                cursor = conn.cursor()
                cursor.execute("DROP TABLE IF EXISTS bug_history")
                cursor.execute("DROP TABLE IF EXISTS bugs")
                cursor.execute("DROP TABLE IF EXISTS modules")
                conn.commit()
                conn.close()

                database.init_db()
                database.seed_sample_data()
                self._send_json({"success": True, "message": "Database reset to sample state successfully"})
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
            return

        self._send_json({"error": "Unknown API endpoint"}, 404)

def run():
    database.init_db()
    database.seed_sample_data()

    handler = DevCoreAPIHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        url = f"http://localhost:{PORT}"
        print("=" * 70)
        print(" DEVCORE BUG TRACKING & METRICS SYSTEM")
        print(" Software Engineering Lab Project 12")
        print(" Department: B.Tech ECE 4th Year")
        print(" Team Members: M. Sanjhay Baargav (623147) & G. Dheeraj (623192)")
        print("=" * 70)
        print(f" [+] Server is running at: {url}")
        print(" [+] Opening your web browser automatically...")
        print(" [+] Press Ctrl+C in this terminal window to stop the server.")
        print("=" * 70)
        try:
            webbrowser.open(url)
        except Exception:
            pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server cleanly...")

if __name__ == "__main__":
    run()

