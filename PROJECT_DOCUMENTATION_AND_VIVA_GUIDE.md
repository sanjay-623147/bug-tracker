# DEVCORE BUG TRACKER & PROCESS METRICS SYSTEM
### Software Engineering Lab (CSM402) — Project Title #12
**Department:** Electronics and Communication Engineering (ECE)  
**Academic Year:** B.Tech 4th Year  
**Team Name:** DevCore  

---

### Team Members & Allocation of Responsibilities

| Student Name | Roll Number | Primary Project Role | Core Lab Focus |
| :--- | :--- | :--- | :--- |
| **M. Sanjhay Baargav** | **623147** | Systems Analyst & Backend Architecture | Outcome 1 (Maintenance Requirements) & Outcome 3 (System Architecture / DB) |
| **G. Dheeraj** | **623192** | Quality Assurance Lead & Metrics Specialist | Outcome 2 (Bug Life Cycle Workflow) & Outcome 4 (Process Improvement Metrics) |

---

## 1. Executive Summary & Objective

In modern software engineering, maintenance represents over **60% to 70% of the total software lifecycle cost**. Defects that escape testing and enter production cause financial damage, security vulnerabilities, and system downtime.

The **DevCore Bug Tracking System** is a full-lifecycle software defect management and metrics evaluation engine. It addresses the four mandatory outcomes prescribed in the lab syllabus:
1. **Analyze Software Maintenance Requirements:** Classifies issues into Corrective, Adaptive, Perfective, and Preventive maintenance under standard IEEE software maintenance frameworks.
2. **Design Bug Life Cycle Workflows:** Implements a finite state machine governing defect state transitions (New ➔ Assigned ➔ In Progress ➔ Resolved ➔ Closed / Reopened).
3. **Implement Issue Reporting and Tracking:** Provides structured defect logging with reproduction steps, environment details, severity/priority matrices, and audit history logs.
4. **Evaluate Process Improvement Metrics:** Dynamically computes Defect Severity Index (DSI), Mean Time to Resolution (MTTR), Defect Density per KLOC, and Defect Reopen Rate.

---

## 2. Outcome 1: Software Maintenance Requirements Analysis

### 2.1 The Four Types of Software Maintenance
Software maintenance begins after delivery. Our system supports all four IEEE standard maintenance categories:

```
                          ┌─────────────────────────────────────┐
                          │    Software Maintenance Types       │
                          └──────────────────┬──────────────────┘
                                             │
         ┌──────────────────┬────────────────┴────────────────┬──────────────────┐
         ▼                  ▼                                 ▼                  ▼
  ┌──────────────┐   ┌──────────────┐                  ┌──────────────┐   ┌──────────────┐
  │  Corrective  │   │   Adaptive   │                  │  Perfective  │   │  Preventive  │
  │ (Bug Fixing) │   │ (Env Change) │                  │(Enhancement) │   │(Code Health) │
  └──────────────┘   └──────────────┘                  └──────────────┘   └──────────────┘
```

1. **Corrective Maintenance (Reactive):**
   * *Purpose:* Correcting faults and failures discovered during user operations or QA testing.
   * *Examples in DevCore:* Fixing 504 Gateway Timeouts in payment processing, resolving unhandled null pointers.
2. **Adaptive Maintenance (Environmental):**
   * *Purpose:* Modifying software to maintain compatibility with shifting operational environments (new OS, new browser versions, updated hardware).
   * *Examples in DevCore:* Adjusting dashboard canvas scaling on Windows 11 high-DPI displays.
3. **Perfective Maintenance (Proactive):**
   * *Purpose:* Enhancing performance, user experience, and adding requested functional improvements.
   * *Examples in DevCore:* Adding CSV export capabilities alongside existing PDF reports.
4. **Preventive Maintenance (Refactoring):**
   * *Purpose:* Detecting and fixing latent faults before they manifest into system failures.
   * *Examples in DevCore:* Refactoring unclosed database connections to prevent pool exhaustion.

### 2.2 Stakeholder Role-Based Access Control (RBAC)

| Stakeholder Role | Key Responsibilities | System Privileges |
| :--- | :--- | :--- |
| **QA / Test Engineer** | Detects bugs, isolates reproduction steps, verifies fixes | Create Bug, Move to Under Retest, Close, or Reopen |
| **Developer / Engineer** | Identifies root cause, writes code patch, unit tests | Move status to In Progress, Resolved |
| **Project Manager** | Triages incoming bugs, sets Priority/Severity, monitors DSI | Assign developers, view process improvement dashboards |

---

## 3. Outcome 2: Bug Life Cycle Workflows

### 3.1 State Machine Workflow Diagram

```
       [Start]
          │
          ▼
       ┌─────┐
       │ NEW │ ◄────────────────────────────────────────┐
       └──┬──┘                                          │
          │ (Manager assigns to dev)                     │
          ▼                                             │
     ┌──────────┐                                       │
     │ ASSIGNED │                                       │
     └────┬─────┘                                       │
          │ (Dev starts debugging)                      │
          ▼                                             │
   ┌─────────────┐                                      │ (QA finds bug
   │ IN PROGRESS │ ◄──────────────┐                     │  still persists)
   └──────┬──────┘                │                     │
          │ (Dev commits patch)   │                     │
          ▼                       │                     │
     ┌──────────┐                 │                     │
     │ RESOLVED │                 │                     │
     └────┬─────┘                 │ (Re-assigned        │
          │ (QA initiates retest) │  for rework)        │
          ▼                       │                     │
   ┌──────────────┐               │                     │
   │ UNDER RETEST ├───────────────┼─────────────────────┘
   └──────┬───────┘               │
          │                       │
     ┌────┴───────────────────────┴──┐
     │                               │
(Fix Verified)                (Bug Persists)
     │                               │
     ▼                               ▼
 ┌────────┐                    ┌──────────┐
 │ CLOSED │                    │ REOPENED │
 └────────┘                    └──────────┘
```

### 3.2 State Definitions
* **NEW:** Defect freshly logged by QA with steps to reproduce and environment specifications.
* **ASSIGNED:** Project Manager reviews defect validity and allocates it to the appropriate developer.
* **IN PROGRESS:** Developer is actively analyzing code, reproducing the fault, and creating a patch.
* **RESOLVED:** Developer has committed the patch and deployed it to the test environment.
* **UNDER RETEST:** QA executes regression test cases to verify the fix without breaking existing modules.
* **CLOSED:** Defect is verified as resolved. The ticket is sealed with timestamp.
* **REOPENED:** Defect persists during retest; routes back to the developer with an incremented reopen counter.

---

## 4. Outcome 3: Issue Reporting, Tracking & System Architecture

### 4.1 System Architecture
The application runs on a clean, zero-dependency architecture:
* **Frontend:** Responsive HTML5, CSS3, and JavaScript Single-Page Application (SPA).
* **Backend:** Python Standard Library (`http.server` & `socketserver`) serving RESTful JSON endpoints.
* **Database:** SQLite (`devcore_bugs.db`) ensuring relational integrity with zero external server dependencies.

```
┌────────────────────────────────────────────────────────┐
│               Frontend (Client Browser)                │
│  - Metrics Dashboard  - Issue Tracker  - Workflow Tab  │
└───────────────────────────┬────────────────────────────┘
                            │ HTTP GET / POST (JSON)
                            ▼
┌────────────────────────────────────────────────────────┐
│           Backend Server (Python server.py)            │
│  - REST API Router  - State Validator  - Metrics Calc  │
└───────────────────────────┬────────────────────────────┘
                            │ SQL Queries
                            ▼
┌────────────────────────────────────────────────────────┐
│          Database Layer (SQLite devcore_bugs.db)       │
│  - modules (KLOC)   - bugs (Tickets)   - bug_history   │
└────────────────────────────────────────────────────────┘
```

### 4.2 Database Relational Schema

1. **`modules` Table:**
   * `id` (INTEGER, PK)
   * `name` (TEXT, UNIQUE)
   * `kloc` (REAL) — Thousands of Lines of Code (used for Defect Density).
   * `description` (TEXT)

2. **`bugs` Table:**
   * `id` (INTEGER, PK)
   * `bug_code` (TEXT, UNIQUE, e.g., "BUG-101")
   * `title` (TEXT)
   * `module_name` (TEXT, FK)
   * `maintenance_type` (TEXT: Corrective, Adaptive, Perfective, Preventive)
   * `severity` (TEXT: Critical, High, Medium, Low)
   * `priority` (TEXT: P1, P2, P3, P4)
   * `status` (TEXT: New, Assigned, In_Progress, Resolved, Closed, Reopened)
   * `environment` (TEXT)
   * `reporter` (TEXT)
   * `assignee` (TEXT)
   * `steps_to_reproduce`, `expected_behavior`, `actual_behavior` (TEXT)
   * `created_at`, `resolved_at`, `closed_at` (DATETIME strings)
   * `reopen_count` (INTEGER)

3. **`bug_history` Table (Audit Trail / Traceability):**
   * `id` (INTEGER, PK)
   * `bug_id` (INTEGER, FK)
   * `changed_by` (TEXT)
   * `old_status` (TEXT)
   * `new_status` (TEXT)
   * `comment` (TEXT)
   * `timestamp` (DATETIME string)

---

## 5. Outcome 4: Process Improvement Metrics & Mathematical Formulations

To satisfy Outcome 4, our system continuously monitors four quantitative metrics:

### 5.1 Defect Severity Index (DSI)
Measures the overall severity profile and risk level of defects in the system.
$$\text{DSI} = \frac{\sum_{i} (\text{Weight}_i \times N_i)}{\text{Total Defects}}$$
Where standard weights are:
* **Critical:** 4
* **High:** 3
* **Medium:** 2
* **Low:** 1

*Sample Calculation:*
If a release has 2 Critical ($2 \times 4 = 8$), 1 High ($1 \times 3 = 3$), 1 Medium ($1 \times 2 = 2$), and 2 Low ($2 \times 1 = 2$):
$$\text{DSI} = \frac{8 + 3 + 2 + 2}{6} = \frac{15}{6} = 2.50$$
*Target Interpretation:* A DSI below 2.0 indicates a stable, low-risk build; a DSI above 3.0 indicates severe release instability.

### 5.2 Mean Time to Resolution (MTTR)
Measures the operational efficiency of the maintenance team in diagnosing and resolving defects.
$$\text{MTTR} = \frac{\sum (\text{Timestamp}_{\text{Resolved}} - \text{Timestamp}_{\text{Created}})}{\text{Total Resolved Defects}}$$
*Unit:* Hours or Days. A lower MTTR signifies superior developer responsiveness and modular code design.

### 5.3 Defect Density (Normalized Software Quality)
Measures defect concentration normalized by the software's codebase size:
$$\text{Defect Density} = \frac{\text{Total Defect Count}}{\text{Size in KLOC (Thousands of Lines of Code)}}$$
*Example:* 6 defects identified across 22.0 KLOC:
$$\text{Defect Density} = \frac{6}{22.0} = 0.27 \text{ defects / KLOC}$$
*Engineering Value:* Allows objective quality comparisons between large subsystems (e.g., Billing at 6.8 KLOC) and smaller subsystems (Notification at 2.1 KLOC).

### 5.4 Defect Reopen Rate (%)
Evaluates patch quality and QA retest rigor:
$$\text{Defect Reopen Rate} = \left(\frac{\text{Count of Reopened Defects}}{\text{Total Closed or Resolved Defects}}\right) \times 100$$
*Engineering Value:* High reopen rates (> 15%) indicate that developers are delivering incomplete fixes or that test specifications are ambiguous.

---

## 6. Viva Voce & Presentation Guide

### 6.1 Team Speaking Order & Allocation

#### Part 1: M. Sanjhay Baargav (Roll No: 623147)
* **What you say:**
  > "Respected Madam and External Examiner, I am M. Sanjhay Baargav, Roll Number 623147. For our Software Engineering Lab Project 12, Team DevCore developed the Bug Tracking & Maintenance System.
  > 
  > I handled **Outcome 1 (Software Maintenance Requirements)** and **Outcome 3 (System Architecture & Traceability)**.
  > In software engineering, maintenance accounts for over 60% of total lifecycle cost. We analyzed and classified all defects into four standard IEEE categories: Corrective, Adaptive, Perfective, and Preventive.
  > In our system architecture, every defect is recorded in an SQLite relational database with full audit logging, so whenever a status changes, we record who changed it, the old status, the new status, and the reason. This fulfills the software traceability requirement."

#### Part 2: G. Dheeraj (Roll No: 623192)
* **What you say:**
  > "Respected Madam and External Examiner, I am G. Dheeraj, Roll Number 623192.
  > 
  > I focused on **Outcome 2 (Bug Life Cycle Workflows)** and **Outcome 4 (Process Improvement Metrics)**.
  > A bug does not simply jump from open to closed. It follows a formal state machine: from **New**, to **Assigned**, to **In Progress**, to **Resolved**, and finally through **Retesting** before it can be marked **Closed**. If the fault persists, it triggers a **Reopened** loop.
  > 
  > Under Outcome 4, we evaluate process health using four quantitative metrics: Defect Severity Index (DSI), Mean Time to Resolution (MTTR), Defect Density per KLOC, and Defect Reopen Rate. These metrics tell management whether the team's software quality is improving over successive releases."

---

### 6.2 Frequently Asked Examiner Questions & Direct Answers

**Q1: What is the fundamental difference between Bug Severity and Priority?**
* **Answer:** Severity reflects the *technical impact* on the system (e.g., system crash is Critical severity). Priority reflects the *business urgency* to resolve it (e.g., a spelling typo in the main corporate logo has Low severity but High priority for brand reputation).

**Q2: What is the difference between an Error, a Fault, and a Failure?**
* **Answer:** An **Error** is a human action/mistake by the programmer. A **Fault (or Bug)** is the resulting internal flaw in the source code. A **Failure** is the external observable malfunction when the system deviates from expected behavior during execution.

**Q3: Why calculate Defect Density per KLOC instead of just counting total bugs?**
* **Answer:** Raw defect counts are misleading because larger modules naturally have more code. Defect Density normalizes the defect count by code size ($Defects / KLOC$), allowing an objective comparison of code quality across different modules.

**Q4: How does this project support Software Configuration Management (SCM) and Traceability?**
* **Answer:** Every ticket maintains an automated `bug_history` audit trail capturing who transitioned the state, the exact timestamp, and the justification comment. This ensures complete verification traceability from initial bug report to final QA closure.

---

### 7. How to Run the Project (1-Click Instructions)
1. Navigate to the project directory:
   `c:\Users\sanjh\Downloads\4-1 files\Software engg. notes\DevCore-BugTracker`
2. **Double-click `run.bat`** (or open command prompt and run `python server.py`).
3. Your browser will automatically launch `http://localhost:8000`.
4. Click through the tabs on screen to demonstrate the 4 syllabus outcomes.

