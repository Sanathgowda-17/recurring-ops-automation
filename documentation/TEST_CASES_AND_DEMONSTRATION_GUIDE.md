# Allo Innoware: Working Test Cases & Demonstration Guide
## Step-by-Step Proof of Tests 1 Through 8

This guide provides exact instructions for evaluating and verifying the **Allo Innoware Operations Automation Prototype**.

You can run each test case using the **Automated Menu Items** under `⚡ Allo Innoware Ops > 🧪 Run Test Scenarios`, or execute them manually in the sheets as described below.

---

## Pre-Test Setup (1 Minute)

1. Open the Google Sheet.
2. Click menu: **`⚡ Allo Innoware Ops > 🚀 Setup / Reset Complete Sheets`**.
3. Accept authorization permissions if prompted by Google.
4. The system will build and format all 6 sheets, populate the 4 default recurring tasks, and initialize Cycle 1 in `Active_Tasks`.

---

## Test 1 — Recurring Cycle Logic

### Objective:
Demonstrate that completing a 7-day, 15-day, or 30-day task closes the current cycle and automatically prepares and tracks the next cycle without manual employee calculations.

### Execution Options:
- **Automated Verification:** Click **`⚡ Allo Innoware Ops > 🧪 Run Test Scenarios > Test 1: Recurring Cycle (7-Day Task)`**.
- **Manual Verification:**
  1. Go to `Active_Tasks`.
  2. Locate row for `TSK-002-C01` (Portal Task A, 7 Days, Employee B).
  3. Enter `JIRA-10492` in `Proof_Submitted` (Col M) and set `Status` (Col L) to `Completed`.
  4. Run `⚡ Allo Innoware Ops > 📝 Employee: Submit Completion (Selected Row)`.

### Expected Results:
1. `TSK-002-C01`:
   - `Status` transitions to `Completed`.
   - `Completed_At` records current timestamp.
   - `Next_Cycle_Generated` flips to `YES`.
2. A new row **`TSK-002-C02`** is instantly appended to `Active_Tasks`:
   - `Cycle_Number`: `2`
   - `Status`: `Pending`
   - `Due_Date`: Exactly **7 days** ahead of Cycle 1 due date.
   - All alert timestamps (`Manager_Alert_Sent_At`, `Leadership_Escalation_Sent_At`) are blank.
3. An entry is recorded in `Audit_Log` with event `CYCLE_CREATED`.

---

## Test 2 — Single-Point Completion (No Duplicated Work)

### Objective:
Demonstrate that an employee can view their pending tasks and update their Ticket ID / completion proof from a single operating location without touching raw databases or editing multiple sheets.

### Execution Options:
- **Automated Verification:** Click **`⚡ Allo Innoware Ops > 🧪 Run Test Scenarios > Test 2: Single-Point Completion`**.
- **Manual Verification:**
  1. Open sheet: **`Employee_Workbench`**.
  2. In cell `B4`, choose **`Employee C`** from the dropdown.
  3. The table automatically filters to show only Employee C's pending task: `TSK-003-C01` (Portal Task B, 15 Days).
  4. Click on row 7. In **Column H** (light green cell `Enter Proof / Ticket ID`), type: `VEND-RECON-5510`.
  5. In **Column I** (`Completion Notes`), type: `Vendor ledger reconciled with ERP`.
  6. Click menu: **`⚡ Allo Innoware Ops > 📝 Employee: Submit Completion (Selected Row)`**.

### Expected Results:
1. A confirmation dialog appears: *"Task Completed Successfully!"*
2. Row 7 vanishes from `Employee_Workbench` because pending count is now 0.
3. In `Active_Tasks`, `TSK-003-C01` is marked `Completed` with ticket `VEND-RECON-5510`, and `TSK-003-C02` is automatically created with due date advanced by 15 days.
4. The employee never had to touch `Active_Tasks`, `Task_Master`, or `Audit_Log`.

---

## Test 3 — Daily Task Completion (WhatsApp Proof Protocol)

### Objective:
Demonstrate a practical, verifiable method for capturing completion of a daily task (such as posting in an Ops WhatsApp group) that does not naturally generate a Ticket ID.

### Proposed Practical Method:
- **Protocol**: The employee copies the **Send Timestamp + 1-Line Message Summary** from WhatsApp into the Workbench.
- **Example Proof**: `10:45 AM - "Daily Ops Standup: 18 dispatches on schedule, zero delays."`
- **Optional Artifact**: Link to screenshot saved on Google Drive.

### Execution Options:
- **Automated Verification:** Click **`⚡ Allo Innoware Ops > 🧪 Run Test Scenarios > Test 3: Daily Task (WhatsApp Proof)`**.
- **Manual Verification:**
  1. Open `Employee_Workbench`.
  2. Select `Employee A` in cell `B4`.
  3. Locate `TSK-001-C01` (Daily Operations Update).
  4. In Column H, enter: `WhatsApp Update 10:45 AM - Operations standup posted in Ops group`.
  5. Click menu: **`⚡ Allo Innoware Ops > 📝 Employee: Submit Completion (Selected Row)`**.

### Expected Results:
1. System validates that proof is present.
2. `TSK-001-C01` is marked `Completed`.
3. The recurrence engine calculates the next working day (e.g. tomorrow or Monday if on Friday) and schedules `TSK-001-C02`.
4. Establishes clear auditability for the manager with minimum employee friction (< 15 seconds).

---

## Test 4 — Same-Day Manager Alert

### Objective:
Demonstrate that when an employee fails to complete a task by the required cutoff, the manager automatically receives an email on the same day informing them which employee/task is still pending.

### Execution Options:
- **Automated Verification:** Click **`⚡ Allo Innoware Ops > 🧪 Run Test Scenarios > Test 4: Same-Day Manager Alert`**.
- **Manual Verification:**
  1. Open `Active_Tasks`.
  2. Add or modify a row with `Due_Date` set to today, `Due_Time` set to 3 hours ago (e.g. `09:00:00`), and `Status` set to `Pending`.
  3. Ensure `Manager_Alert_Sent_At` is blank.
  4. Click menu: **`⚡ Allo Innoware Ops > ⏰ Run Escalation Engine Check Now`**.

### Expected Results:
1. Escalation engine detects that cutoff + 30-minute grace period has passed.
2. An executive HTML email is delivered to `MANAGER_EMAIL` (defaulted to your login email for verification):
   - **Subject**: `⚠️ [PENDING ALERT] Task Overdue: Daily Operations Update (Employee A)`
   - **Body**: Shows Task ID, Employee Name, Hours Overdue, and a prominent blue button: **`[Click Here to Acknowledge Task]`**.
3. In `Active_Tasks`:
   - `Status` transitions to **`Manager Alerted`**.
   - `Manager_Alert_Sent_At` is stamped with the exact dispatch timestamp.
4. Event `MANAGER_ALERT_SENT` is recorded in `Audit_Log`.

---

## Test 5 — Manager Action & Acknowledgement

### Objective:
Demonstrate what the manager is expected to do after receiving the alert email, how the system captures manager review/acknowledgement, and how it updates the task status.

### Manager Action Options:
1. **Option A (Recommended 1-Click Email Action):**
   - In the alert email received in Test 4, the manager clicks the button: **`[Click Here to Acknowledge Task]`**.
   - A browser tab opens displaying the responsive **Allo Innoware Acknowledgement Confirmation** page.
   - The web app automatically records the acknowledgement in the Google Sheet.
2. **Option B (Directly on Google Sheet):**
   - Click menu: **`⚡ Allo Innoware Ops > 🧪 Run Test Scenarios > Test 5: Manager Action & Acknowledgement`** OR select row in `Active_Tasks` and click **`⚡ Allo Innoware Ops > 👀 Manager: Acknowledge Selected Task`**.

### Expected Results:
1. In `Active_Tasks`:
   - `Status` transitions to **`Manager Acknowledged`**.
   - `Manager_Acknowledged_At` records the timestamp.
   - `Manager_Notes` records: *"Reviewed by Manager / Acknowledged via 1-Click Email Action Link"*.
2. On `Manager_Dashboard`, the task moves from "Manager Alerted" to "Manager Acknowledged".
3. An audit record `MANAGER_ACKNOWLEDGED` is logged.
4. **SLA Impact**: The escalation timer is placed on hold to give the employee the agreed window to finalize completion.

---

## Test 6 — Leadership Escalation

### Objective:
Demonstrate that when a pending task remains unresolved beyond the defined SLA window, or when the manager fails to acknowledge the alert within the manager SLA, the system automatically escalates to the leadership team.

### Execution Options:
- **Automated Verification:** Click **`⚡ Allo Innoware Ops > 🧪 Run Test Scenarios > Test 6: Leadership Escalation`**.
- **Manual Verification:**
  1. In `Active_Tasks`, create a row where `Status` is `Manager Alerted`, `Manager_Alert_Sent_At` was 5 hours ago, and `Manager_Acknowledged_At` is blank.
  2. Click menu: **`⚡ Allo Innoware Ops > ⏰ Run Escalation Engine Check Now`**.

### Expected Results:
1. The escalation engine detects that manager SLA (4 hours for daily tasks) has been breached without acknowledgement.
2. A high-priority HTML escalation email is delivered to `LEADERSHIP_EMAIL` (CC'ing Manager and Employee):
   - **Subject**: `🚨 [URGENT ESCALATION] SLA Breach on Operational Task: Portal Task A (Employee B)`
   - **Body**: Red alert banner, details of the SLA breach, hours overdue, and intervention guidance.
3. In `Active_Tasks`:
   - `Status` transitions to **`Escalated`**.
   - `Leadership_Escalation_Sent_At` is stamped with the dispatch timestamp.
4. On `Manager_Dashboard`, the "Escalated to Leadership" KPI card increments.
5. Event `LEADERSHIP_ESCALATED` is logged in `Audit_Log`.

---

## Test 7 — Escalation Timing Logic & SLA Matrix

### Objective:
Demonstrate and justify the complete SLA timing architecture across all task cadences.

### Execution:
- Click menu: **`⚡ Allo Innoware Ops > 🧪 Run Test Scenarios > Test 7: Timing SLA Matrix Validation`**.

### Design Rationale:
1. **Daily Operational Updates (11:00 AM Cutoff)**:
   - *Why 30-minute grace period (11:30 AM alert)?* Accommodates unexpected last-minute customer calls while alerting the manager before mid-day.
   - *Why 4-hour manager SLA (03:30 PM escalation)?* Provides the manager time to call the employee during the business day. If still unresolved by 3:30 PM, leadership has 2.5 hours before close-of-business to intervene.
2. **Periodic Portal Tasks (7, 15, 30 Days - 05:00 PM Cutoff)**:
   - *Why morning alert (09:00 AM next day)?* Avoids sending after-hours emails at night. Alerts the manager at the start of the next business day.
   - *Why 24-hour leadership SLA?* Complex portal reconciliations may take half a day to troubleshoot with vendors; 24 hours strikes the optimal balance between operational urgency and practical resolution time.

---

## Test 8 — Anti-Duplication & Idempotency Verification

### Objective:
Demonstrate that running the automation repeatedly does NOT generate duplicate task cycles, duplicate completion entries, or duplicate alert/escalation emails.

### Execution Options:
- **Automated Verification:** Click **`⚡ Allo Innoware Ops > 🧪 Run Test Scenarios > Test 8: Anti-Duplication Verification`**.

### Mechanism Verified:
The test executes `runEscalationEngine()` **three consecutive times** in rapid succession:
- **Run 1**: Processes overdue tasks, dispatches alerts, and stamps timestamps.
- **Run 2**: Re-evaluates identical database state. Verifies:
  - `Manager Alerts Sent = 0`
  - `Leadership Escalations Sent = 0`
- **Run 3**: Re-evaluates again. Verifies:
  - `Manager Alerts Sent = 0`
  - `Leadership Escalations Sent = 0`

### Concurrency Lock Verification:
- Both `executeTaskCompletion()` and `runEscalationEngine()` utilize `LockService.getScriptLock().waitLock(30000)`.
- If an employee clicks "Submit Completion" multiple times rapidly, the second execution detects `Status == 'Completed'` and safely aborts.
- If `Next_Cycle_Generated == 'YES'`, cycle duplication is strictly prevented.

---

## Summary Checklist for Evaluators

| Test # | Test Description | Verification Status | Primary Proof Location |
| :---: | :--- | :---: | :--- |
| **Test 1** | Recurring cycle closing & next cycle generation | ✅ PASS | `Active_Tasks` rows `TSK-002-C01` & `TSK-002-C02` |
| **Test 2** | Single-point employee completion | ✅ PASS | `Employee_Workbench` filtered view & submission |
| **Test 3** | Daily task WhatsApp proof capture | ✅ PASS | `Active_Tasks` proof column & timestamp verification |
| **Test 4** | Same-day manager alert dispatch | ✅ PASS | `Manager_Alert_Sent_At` stamp & Manager HTML Email |
| **Test 5** | Manager 1-click action & acknowledgement | ✅ PASS | `ManagerWebApp.html` & `Manager_Acknowledged_At` |
| **Test 6** | Leadership escalation on SLA breach | ✅ PASS | `Leadership_Escalation_Sent_At` & Leadership Email |
| **Test 7** | Escalation timing & SLA matrix | ✅ PASS | `Config` sheet parameters & Test 7 dialog report |
| **Test 8** | Anti-duplication & concurrency protection | ✅ PASS | 3-run idempotency test & LockService verification |
