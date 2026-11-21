"""
DevCore BugTracker - Database and Metrics Engine
Team: DevCore
Members: M. Sanjhay Baargav (623147) & G. Dheeraj (623192)
Department: B.Tech ECE 4th Year

This file handles:
1. SQLite Database creation (Zero-configuration, stored in a single file)
2. Realistic Seed Data (So your demo always looks full and realistic)
3. Calculation of Software Engineering Process Improvement Metrics:
   - Defect Density (Defects / KLOC)
   - Defect Severity Index (DSI)
   - Mean Time to Resolution (MTTR)
   - Defect Reopen Rate (%)
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta

DB_FILE = os.path.join(os.path.dirname(__file__), "devcore_bugs.db")

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Table 1: Modules (Used to calculate Defect Density per KLOC)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS modules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        kloc REAL NOT NULL, -- Size in Thousands of Lines of Code
        description TEXT
    )
    """)

    # Table 2: Bugs (Issue Tracking)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bugs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bug_code TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        module_name TEXT NOT NULL,
        maintenance_type TEXT NOT NULL, -- Corrective, Adaptive, Perfective, Preventive
        severity TEXT NOT NULL,         -- Critical, High, Medium, Low
        priority TEXT NOT NULL,         -- P1 (Immediate), P2 (High), P3 (Medium), P4 (Low)
        status TEXT NOT NULL,           -- New, Assigned, In_Progress, Resolved, Under_Retest, Closed, Reopened
        environment TEXT NOT NULL,
        reporter TEXT NOT NULL,
        assignee TEXT NOT NULL,
        description TEXT NOT NULL,
        steps_to_reproduce TEXT NOT NULL,
        expected_behavior TEXT NOT NULL,
        actual_behavior TEXT NOT NULL,
        created_at TEXT NOT NULL,
        resolved_at TEXT,
        closed_at TEXT,
        reopen_count INTEGER DEFAULT 0
    )
    """)

    # Table 3: Bug History / Audit Trail (Life Cycle State Transitions)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bug_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bug_id INTEGER NOT NULL,
        changed_by TEXT NOT NULL,
        old_status TEXT NOT NULL,
        new_status TEXT NOT NULL,
        comment TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (bug_id) REFERENCES bugs(id)
    )
    """)

    conn.commit()
    conn.close()

def seed_sample_data():
    """Seeds realistic software defects so the demo looks full and impressive immediately."""
    conn = get_connection()
    cursor = conn.cursor()

    # Check if already seeded
    cursor.execute("SELECT COUNT(*) FROM modules")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    # 1. Insert Software Modules with realistic KLOC (Thousands of Lines of Code)
    modules = [
        ("Authentication & Security", 4.2, "User login, MFA, and JWT session handling"),
        ("Billing & Payment Gateway", 6.8, "Payment processing, invoice generation, refunds"),
        ("Analytics Dashboard", 3.5, "Charts, data visualization, reporting exports"),
        ("Notification Service", 2.1, "Email and SMS alerting system"),
        ("Database & Storage API", 5.4, "CRUD endpoints and caching layer")
    ]
    cursor.executemany("INSERT INTO modules (name, kloc, description) VALUES (?, ?, ?)", modules)

    # 2. Insert Sample Bugs reflecting various maintenance types and lifecycle stages
    now = datetime.now()
    sample_bugs = [
        (
            "BUG-101",
            "Payment Gateway times out on slow 3G mobile networks",
            "Billing & Payment Gateway",
            "Corrective",
            "Critical",
            "P1",
            "Closed",
            "Android 13 / Chrome Mobile v119",
            "G. Dheeraj (QA Lead)",
            "M. Sanjhay Baargav (Dev)",
            "Transactions fail with 504 Gateway Timeout when socket delay exceeds 10 seconds.",
            "1. Switch network to 3G throttling\n2. Add item to cart\n3. Click Pay via UPI/Card\n4. Observe timeout after 10s",
            "System should retry or gracefully show pending payment status.",
            "Screen freezes and displays raw JSON timeout error.",
            (now - timedelta(days=6, hours=4)).strftime("%Y-%m-%d %H:%M:%S"),
            (now - timedelta(days=4, hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
            (now - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"),
            0
        ),
        (
            "BUG-102",
            "Session token not invalidated after password change",
            "Authentication & Security",
            "Corrective",
            "Critical",
            "P1",
            "Resolved",
            "Ubuntu 22.04 / Firefox 120",
            "G. Dheeraj (QA Lead)",
            "M. Sanjhay Baargav (Dev)",
            "Security vulnerability: Existing active sessions remain valid even after user resets password.",
            "1. Login on Browser A and Browser B\n2. Change password on Browser A\n3. Refresh Browser B",
            "Browser B session must be terminated and redirect to login.",
            "Browser B continues to make authorized API calls.",
            (now - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S"),
            (now - timedelta(days=1, hours=3)).strftime("%Y-%m-%d %H:%M:%S"),
            None,
            0
        ),
        (
            "BUG-103",
            "Export to PDF layout misaligned on Windows 11 high DPI screens",
            "Analytics Dashboard",
            "Adaptive",
            "Medium",
            "P3",
            "In_Progress",
            "Windows 11 / 4K Display (150% Scale)",
            "G. Dheeraj (QA Lead)",
            "M. Sanjhay Baargav (Dev)",
            "Canvas charts overlap table headers when rendered under display scaling > 125%.",
            "1. Set display scaling to 150%\n2. Navigate to Dashboard Reports\n3. Click Export PDF",
            "PDF pages should respect margins with crisp vector charts.",
            "Chart images clip text and overflow onto page footer.",
            (now - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S"),
            None,
            None,
            0
        ),
        (
            "BUG-104",
            "Database connection pool exhaustion under 200 concurrent requests",
            "Database & Storage API",
            "Preventive",
            "High",
            "P2",
            "Reopened",
            "Production Staging / Linux Docker",
            "G. Dheeraj (QA Lead)",
            "M. Sanjhay Baargav (Dev)",
            "Unclosed DB cursor in audit logger leaks connections until pool limit (20) is hit.",
            "1. Run Apache Benchmark with 200 concurrent users\n2. Inspect active DB connections",
            "Connection pool should recycle idle connections smoothly.",
            "Service throws sqlite3.OperationalError: database is locked.",
            (now - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S"),
            (now - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"),
            None,
            1
        ),
        (
            "BUG-105",
            "SMS notification template exceeds 160 characters limit",
            "Notification Service",
            "Adaptive",
            "Low",
            "P4",
            "Assigned",
            "Global SMS Gateway",
            "G. Dheeraj (QA Lead)",
            "M. Sanjhay Baargav (Dev)",
            "OTP text contains long brand tagline causing telecom carrier to split into two billable SMS messages.",
            "1. Trigger OTP login\n2. Inspect raw SMS payload bytes",
            "SMS should fit within standard 160 GSM-7 character boundary.",
            "SMS is split into 2 segments (172 characters).",
            (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
            None,
            None,
            0
        ),
        (
            "BUG-106",
            "Add CSV export option to customer transaction history",
            "Billing & Payment Gateway",
            "Perfective",
            "Low",
            "P3",
            "New",
            "Web Portal / All Browsers",
            "G. Dheeraj (QA Lead)",
            "Unassigned",
            "Feature enhancement request from accounting team to export filtered monthly statements directly to CSV.",
            "1. Go to Billing history tab\n2. Check available export formats",
            "Both PDF and CSV export buttons should be available.",
            "Currently only PDF export is present.",
            (now - timedelta(hours=14)).strftime("%Y-%m-%d %H:%M:%S"),
            None,
            None,
            0
        )
    ]

    for bug in sample_bugs:
        cursor.execute("""
        INSERT INTO bugs (
            bug_code, title, module_name, maintenance_type, severity, priority,
            status, environment, reporter, assignee, description,
            steps_to_reproduce, expected_behavior, actual_behavior,
            created_at, resolved_at, closed_at, reopen_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, bug)
        bug_id = cursor.lastrowid

        # Insert audit history
        cursor.execute("""
        INSERT INTO bug_history (bug_id, changed_by, old_status, new_status, comment, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (bug_id, bug[8], "None", "New", "Bug logged during QA testing", bug[14]))

        if bug[6] in ["Assigned", "In_Progress", "Resolved", "Under_Retest", "Closed", "Reopened"]:
            cursor.execute("""
            INSERT INTO bug_history (bug_id, changed_by, old_status, new_status, comment, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (bug_id, "Project Manager", "New", "Assigned", "Assigned to developer for investigation", bug[14]))

        if bug[6] in ["In_Progress", "Resolved", "Under_Retest", "Closed", "Reopened"]:
            cursor.execute("""
            INSERT INTO bug_history (bug_id, changed_by, old_status, new_status, comment, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (bug_id, bug[9], "Assigned", "In_Progress", "Root cause identified; patch under development", bug[14]))

        if bug[15]: # resolved_at exists
            cursor.execute("""
            INSERT INTO bug_history (bug_id, changed_by, old_status, new_status, comment, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (bug_id, bug[9], "In_Progress", "Resolved", "Fix committed to main branch; ready for QA retest", bug[15]))

        if bug[6] == "Reopened":
            cursor.execute("""
            INSERT INTO bug_history (bug_id, changed_by, old_status, new_status, comment, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (bug_id, bug[8], "Resolved", "Reopened", "Regression identified during stress retest; re-assigning", bug[14]))

        if bug[16]: # closed_at exists
            cursor.execute("""
            INSERT INTO bug_history (bug_id, changed_by, old_status, new_status, comment, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (bug_id, bug[8], "Resolved", "Closed", "Fix verified in staging environment; closed successfully", bug[16]))

    conn.commit()
    conn.close()

def calculate_metrics():
    """
    Outcome 4: Evaluate Process Improvement Metrics.
    Calculates:
    1. Defect Severity Index (DSI)
    2. Mean Time to Resolution (MTTR) in Hours
    3. Defect Density (Defects per KLOC) per module & overall
    4. Defect Reopen Rate (%)
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Total counts
    cursor.execute("SELECT COUNT(*) FROM bugs")
    total_bugs = cursor.fetchone()[0]

    # Status distribution
    cursor.execute("SELECT status, COUNT(*) FROM bugs GROUP BY status")
    status_counts = dict(cursor.fetchall())

    # Severity distribution
    cursor.execute("SELECT severity, COUNT(*) FROM bugs GROUP BY severity")
    severity_counts = dict(cursor.fetchall())

    # Maintenance Type distribution (Outcome 1)
    cursor.execute("SELECT maintenance_type, COUNT(*) FROM bugs GROUP BY maintenance_type")
    maintenance_counts = dict(cursor.fetchall())

    # 1. Defect Severity Index (DSI)
    # Formula: DSI = Sum(Weight * Count) / Total Defects
    # Weights: Critical=4, High=3, Medium=2, Low=1
    weights = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
    dsi_sum = sum(severity_counts.get(sev, 0) * weight for sev, weight in weights.items())
    dsi = round(dsi_sum / total_bugs, 2) if total_bugs > 0 else 0.0

    # 2. Mean Time to Resolution (MTTR) in Hours
    # Formula: Average of (resolved_at - created_at) for all resolved/closed bugs
    cursor.execute("SELECT created_at, resolved_at FROM bugs WHERE resolved_at IS NOT NULL")
    resolved_pairs = cursor.fetchall()
    total_hours = 0.0
    for row in resolved_pairs:
        t_create = datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M:%S")
        t_resolve = datetime.strptime(row["resolved_at"], "%Y-%m-%d %H:%M:%S")
        total_hours += (t_resolve - t_create).total_seconds() / 3600.0

    mttr_hours = round(total_hours / len(resolved_pairs), 1) if resolved_pairs else 0.0

    # 3. Defect Density = Total Defects / KLOC
    cursor.execute("SELECT SUM(kloc) FROM modules")
    total_kloc = cursor.fetchone()[0] or 1.0
    overall_defect_density = round(total_bugs / total_kloc, 2)

    # Module-level Defect Density
    cursor.execute("""
    SELECT m.name, m.kloc, COUNT(b.id) as defect_count
    FROM modules m
    LEFT JOIN bugs b ON m.name = b.module_name
    GROUP BY m.id
    """)
    module_density = []
    for row in cursor.fetchall():
        count = row["defect_count"]
        kloc = row["kloc"]
        density = round(count / kloc, 2) if kloc > 0 else 0.0
        module_density.append({
            "module": row["name"],
            "kloc": kloc,
            "defects": count,
            "density": density
        })

    # 4. Defect Reopen Rate (%)
    # Formula: (Count of Reopened Bugs / Count of Resolved+Closed Bugs) * 100
    cursor.execute("SELECT SUM(reopen_count) FROM bugs")
    reopen_sum = cursor.fetchone()[0] or 0
    resolved_or_closed = status_counts.get("Resolved", 0) + status_counts.get("Closed", 0) + status_counts.get("Reopened", 0)
    reopen_rate = round((reopen_sum / resolved_or_closed) * 100, 1) if resolved_or_closed > 0 else 0.0

    conn.close()

    return {
        "total_bugs": total_bugs,
        "open_bugs": status_counts.get("New", 0) + status_counts.get("Assigned", 0) + status_counts.get("In_Progress", 0) + status_counts.get("Reopened", 0),
        "in_progress_bugs": status_counts.get("In_Progress", 0),
        "resolved_bugs": status_counts.get("Resolved", 0),
        "closed_bugs": status_counts.get("Closed", 0),
        "status_distribution": status_counts,
        "severity_distribution": severity_counts,
        "maintenance_distribution": maintenance_counts,
        "dsi": dsi,
        "mttr_hours": mttr_hours,
        "overall_defect_density": overall_defect_density,
        "total_kloc": total_kloc,
        "module_density": module_density,
        "reopen_rate": reopen_rate
    }

