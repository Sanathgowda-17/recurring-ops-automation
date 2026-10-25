# Allo Innoware - AI Operations Manager Assignment Prototype
### Recurring Task Tracking, Pending Reports & Escalation Automation

Welcome to the production prototype built for the **Allo Innoware AI Operations Manager Assignment Test**.

This solution automates the complete lifecycle of recurring operational tasks:
$$\text{Task Due} \longrightarrow \text{Employee Single-Point Action} \longrightarrow \text{Cycle Closed & Next Cycle Auto-Scheduled} \longrightarrow \text{Same-Day Manager Alert} \longrightarrow \text{1-Click Manager Ack} \longrightarrow \text{Leadership Escalation}$$

---

## ⚡ 3-Minute Quickstart: Setup Instructions

Follow these steps to deploy this prototype into your own Google Account:

### Step 1: Create a New Google Sheet
1. Open [Google Sheets](https://sheets.new) in your browser.
2. Name the spreadsheet: **`Allo Innoware - Operations Automation System`**.

### Step 2: Open Apps Script & Paste the Code
1. In the Google Sheet top menu, click **Extensions > Apps Script**.
2. Rename the project to: **`AlloInnowareOps`**.
3. In the left sidebar under **Files**:
   - Open `Code.gs` (delete any default code) and paste the complete content of [`src/Code.gs`](src/Code.gs).
   - Click the **+** (Add a file) button next to Files > select **HTML** > name it **`ManagerWebApp`** (do not add `.html`, Apps Script adds it automatically).
   - Paste the complete content of [`src/ManagerWebApp.html`](src/ManagerWebApp.html) into `ManagerWebApp.html`.
4. Click **Save** (💾 icon) or press `Cmd+S` / `Ctrl+S`.

### Step 3: Run the 1-Click System Setup
1. In the Apps Script code editor, select the function **`setupCompleteSystem`** from the function dropdown at the top.
2. Click **Run**.
3. Google will show an **Authorization Required** popup:
   - Click *Review Permissions* > Choose your Google account > Click *Advanced* (small text at bottom) > Click *Go to AlloInnowareOps (unsafe)* > Click *Allow*.
4. Switch back to your Google Sheet!
   - You will see all 6 sheets automatically generated, styled with dark navy headers, formulas, KPI cards, conditional formatting badges, and default tasks!
   - A new custom menu **`⚡ Allo Innoware Ops`** will now appear in your Google Sheet menu bar.

### Step 4 (Optional for Full 1-Click Email Action): Deploy Web App
1. In the Apps Script editor, click the blue **Deploy** button (top right) > **New deployment**.
2. Click the gear icon (⚙️) next to *Select type* > select **Web app**.
3. Configure:
   - **Description**: `Allo Innoware Operations Webhook`
   - **Execute as**: `Me (your email)`
   - **Who has access**: `Anyone` *(required so clicking the link from your email inbox can record acknowledgement without OAuth errors)*.
4. Click **Deploy**.
5. Copy the generated **Web App URL**.
6. Switch to the **`Config`** sheet in Google Sheets, locate the row `WEB_APP_URL`, and paste your URL into cell `B12`.

---

## 📂 Repository Structure

```
.
├── README.md                                          # This quickstart guide
├── setup_helper.py                                    # Local Python test runner & SLA validator
├── src/
│   ├── Code.gs                                        # Complete Google Apps Script automation engine
│   ├── ManagerWebApp.html                             # Responsive 1-click acknowledgement web app page
│   └── appsscript.json                                # Manifest with scopes and timezone (Asia/Kolkata)
├── sheets_csv/                                        # Raw data structure templates
│   ├── 01_Config.csv                                  # SLA thresholds, emails, and system configs
│   ├── 02_Task_Master.csv                             # Master recurring task catalog (Daily, 7d, 15d, 30d)
│   ├── 03_Active_Tasks.csv                            # Live operational cycle queue & audit timestamps
│   ├── 04_Employee_Workbench.csv                      # Single-point employee task interface
│   ├── 05_Manager_Dashboard.csv                       # Executive KPI summary & compliance tracking
│   └── 06_Audit_Log.csv                               # Immutable event ledger
└── documentation/
    ├── INNOWARE_Operations_System_Architecture.md     # Full architectural and operational blueprint
    ├── TEST_CASES_AND_DEMONSTRATION_GUIDE.md          # Step-by-step verification manual for Tests 1-8
    └── SUBMISSION_COVER_LETTER_AND_PORTFOLIO.md       # Submission email template for hr.ops.allo@gmail.com
```

---

## 🎯 Verification: Testing Scenarios 1 Through 8

You can test all scenarios directly from the custom menu in Google Sheets:

| Menu Path: `⚡ Allo Innoware Ops > 🧪 Run Test Scenarios > ...` | Verified Feature |
| :--- | :--- |
| **`Test 1: Recurring Cycle (7-Day Task)`** | Closes 7-day task, records ticket ID, and auto-generates Cycle 2 with due date + 7 days. |
| **`Test 2: Single-Point Completion`** | Employee C views filtered pending task and submits completion from `Employee_Workbench` without touching raw databases. |
| **`Test 3: Daily Task (WhatsApp Proof)`** | Tests practical WhatsApp update proof capture (`Timestamp + Standup Summary`) with immediate next-working-day cycle creation. |
| **`Test 4: Same-Day Manager Alert`** | Simulates 3-hour overdue task and dispatches an HTML email to the manager with a 1-click acknowledge button. |
| **`Test 5: Manager Action & Acknowledgement`** | Simulates 1-click email acknowledgement, updating status to `Manager Acknowledged` and pausing escalation. |
| **`Test 6: Leadership Escalation`** | Simulates manager SLA breach (4 hours unacknowledged) and triggers high-priority escalation email to Leadership. |
| **`Test 7: Timing SLA Matrix Validation`** | Outputs detailed SLA timing rationale and rules for Daily, 7-Day, 15-Day, and 30-Day tasks. |
| **`Test 8: Anti-Duplication Verification`** | Runs escalation engine 3 consecutive times, proving **0 duplicate emails** and **0 duplicate cycles** created. |
| **`🎯 Run ALL 8 Tests (Full Suite)`** | Runs the entire end-to-end assignment test suite in sequence. |

---

## 📧 Submission Instructions for Candidates

To submit your assignment to Allo Innoware:
1. In your Google Sheet, click the green **Share** button (top right).
2. Add **`hr.ops.allo@gmail.com`** with **Editor** access.
3. Use the formal cover letter in [`documentation/SUBMISSION_COVER_LETTER_AND_PORTFOLIO.md`](documentation/SUBMISSION_COVER_LETTER_AND_PORTFOLIO.md) to email your submission link, portfolio, and contact details.
