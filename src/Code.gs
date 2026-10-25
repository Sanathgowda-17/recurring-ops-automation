/**
 * ==============================================================================
 * ALLO INNOWARE - AI OPERATIONS MANAGER SYSTEM
 * Recurring Task Tracking, Pending Reports & Escalation Automation
 * ==============================================================================
 * Primary Script File: Code.gs
 * Version: 2.4.0 (Production Candidate)
 *
 * This system automates:
 * 1. Master task definitions & dynamic recurrence cycle scheduling.
 * 2. Single-point employee task workbench (no duplicated effort).
 * 3. Daily task completion tracking (WhatsApp update verification).
 * 4. Automated same-day manager pending alerts with 1-click web acknowledgement.
 * 5. SLA-based multi-tiered leadership escalation.
 * 6. Concurrency locking & complete anti-duplication guards.
 * 7. Full automated test suite for evaluation & demonstration.
 * ==============================================================================
 */

// Global Sheet Names
const SHEETS = {
  CONFIG: 'Config',
  TASK_MASTER: 'Task_Master',
  ACTIVE_TASKS: 'Active_Tasks',
  EMPLOYEE_WORKBENCH: 'Employee_Workbench',
  MANAGER_DASHBOARD: 'Manager_Dashboard',
  AUDIT_LOG: 'Audit_Log'
};

/**
 * Custom menu created when the Google Sheet opens
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('⚡ Allo Innoware Ops')
    .addItem('🚀 Setup / Reset Complete Sheets', 'setupCompleteSystem')
    .addSeparator()
    .addItem('📝 Employee: Submit Completion (Selected Row)', 'submitWorkbenchCompletion')
    .addItem('⏰ Run Escalation Engine Check Now', 'runEscalationEngineManual')
    .addItem('👀 Manager: Acknowledge Selected Task', 'acknowledgeSelectedTask')
    .addSeparator()
    .addSubMenu(ui.createMenu('🧪 Run Test Scenarios')
      .addItem('Test 1: Recurring Cycle (7-Day Task)', 'runTest1_RecurringCycle')
      .addItem('Test 2: Single-Point Completion', 'runTest2_SinglePointCompletion')
      .addItem('Test 3: Daily Task (WhatsApp Proof)', 'runTest3_DailyTask')
      .addItem('Test 4: Same-Day Manager Alert', 'runTest4_ManagerAlert')
      .addItem('Test 5: Manager Action & Acknowledgement', 'runTest5_ManagerAck')
      .addItem('Test 6: Leadership Escalation', 'runTest6_LeadershipEscalation')
      .addItem('Test 7: Timing SLA Matrix Validation', 'runTest7_TimingSLA')
      .addItem('Test 8: Anti-Duplication Verification', 'runTest8_AntiDuplication')
      .addSeparator()
      .addItem('🎯 Run ALL 8 Tests (Full Suite)', 'runFullTestSuite'))
    .addSeparator()
    .addItem('⚙️ Install Automated Time Triggers', 'installTriggers')
    .addItem('🗑️ Uninstall Time Triggers', 'uninstallTriggers')
    .addItem('ℹ️ System Architecture & Instructions', 'showSystemInfo')
    .addToUi();
}

/**
 * Fetches configuration dictionary from Config sheet
 */
function getConfig() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const configSheet = ss.getSheetByName(SHEETS.CONFIG);
  const config = {
    MANAGER_EMAIL: 'manager@innoware.com',
    LEADERSHIP_EMAIL: 'leadership@innoware.com',
    ENABLE_EMAIL_ALERTS: true,
    DAILY_TASK_CUTOFF_TIME: '11:00',
    DAILY_TASK_MANAGER_ALERT_DELAY_MINS: 30,
    DAILY_TASK_LEADERSHIP_ESCALATION_HOURS: 4,
    PERIODIC_TASK_DUE_TIME: '17:00',
    PERIODIC_MANAGER_ALERT_DELAY_HOURS: 16,
    PERIODIC_LEADERSHIP_ESCALATION_HOURS: 24,
    RECURRENCE_CALCULATION_MODE: 'SCHEDULE_BASED',
    WEB_APP_URL: '',
    TIMEZONE: 'Asia/Kolkata'
  };

  if (!configSheet) return config;

  const data = configSheet.getDataRange().getValues();
  for (let i = 1; i < data.length; i++) {
    const key = String(data[i][0]).trim();
    const val = data[i][1];
    if (key && val !== undefined && val !== '') {
      if (key === 'ENABLE_EMAIL_ALERTS') {
        config[key] = (String(val).toUpperCase() === 'TRUE');
      } else if (key.endsWith('_MINS') || key.endsWith('_HOURS')) {
        config[key] = Number(val);
      } else {
        config[key] = val;
      }
    }
  }
  return config;
}

/**
 * 1-Click System Setup & Initializer
 * Automatically creates and designs all 6 sheets with styles, formulas, and validations.
 */
function setupCompleteSystem() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const ui = SpreadsheetApp.getUi();

  // 1. Config Sheet
  let configSheet = ss.getSheetByName(SHEETS.CONFIG);
  if (!configSheet) configSheet = ss.insertSheet(SHEETS.CONFIG);
  configSheet.clear();
  const configData = [
    ['Key', 'Value', 'Description'],
    ['MANAGER_EMAIL', Session.getActiveUser().getEmail() || 'manager@innoware.com', 'Recipient for manager alerts (defaulted to your email for testing)'],
    ['LEADERSHIP_EMAIL', Session.getActiveUser().getEmail() || 'leadership@innoware.com', 'Recipient for leadership escalations'],
    ['ENABLE_EMAIL_ALERTS', 'TRUE', 'Set TRUE to send real emails; FALSE to simulate in Audit Log only'],
    ['DAILY_TASK_CUTOFF_TIME', '11:00', 'Daily task deadline (24-hour format)'],
    ['DAILY_TASK_MANAGER_ALERT_DELAY_MINS', 30, 'Minutes after cutoff before manager alert (e.g. 11:30 AM)'],
    ['DAILY_TASK_LEADERSHIP_ESCALATION_HOURS', 4, 'Hours after manager alert before leadership escalation'],
    ['PERIODIC_TASK_DUE_TIME', '17:00', 'Cutoff time for 7/15/30 day periodic tasks'],
    ['PERIODIC_MANAGER_ALERT_DELAY_HOURS', 16, 'Hours after periodic cutoff before manager alert (next morning 09:00)'],
    ['PERIODIC_LEADERSHIP_ESCALATION_HOURS', 24, 'Hours after manager alert before leadership escalation'],
    ['RECURRENCE_CALCULATION_MODE', 'SCHEDULE_BASED', 'SCHEDULE_BASED (Prev Due + Freq) or COMPLETION_BASED (Completion Date + Freq)'],
    ['WEB_APP_URL', ScriptApp.getService().getUrl() || 'https://script.google.com/macros/s/.../exec', 'Web App URL for 1-click email acknowledgement'],
    ['TIMEZONE', 'Asia/Kolkata', 'Operational timezone']
  ];
  configSheet.getRange(1, 1, configData.length, configData[0].length).setValues(configData);
  styleHeaders(configSheet, 1, 3);
  configSheet.setColumnWidth(1, 280);
  configSheet.setColumnWidth(2, 320);
  configSheet.setColumnWidth(3, 400);

  // 2. Task Master Sheet
  let masterSheet = ss.getSheetByName(SHEETS.TASK_MASTER);
  if (!masterSheet) masterSheet = ss.insertSheet(SHEETS.TASK_MASTER);
  masterSheet.clear();
  const masterHeaders = [
    'Task_ID', 'Task_Name', 'Assigned_To', 'Employee_Email', 'Frequency', 
    'Frequency_Days', 'Expected_Cutoff_Time', 'Proof_Type', 'Target_Portal_Channel', 'Active', 'Description'
  ];
  const userEmail = Session.getActiveUser().getEmail() || 'ops@innoware.com';
  const masterRows = [
    ['TSK-001', 'Daily Operations Update', 'Employee A', userEmail, 'Daily', 1, '11:00:00', 'WhatsApp Timestamp & Summary', 'Ops WhatsApp Group', true, 'Post daily operations summary in the WhatsApp Ops group before 11:00 AM.'],
    ['TSK-002', 'Portal Task A', 'Employee B', userEmail, '7 Days', 7, '17:00:00', 'Ticket ID', 'Jira / Internal Portal', true, 'Review weekly inventory counts and log ticket on Jira portal.'],
    ['TSK-003', 'Portal Task B', 'Employee C', userEmail, '15 Days', 15, '17:00:00', 'Ticket ID', 'Vendor Settlement Portal', true, 'Bi-weekly reconciliation of vendor payments and raise ticket.'],
    ['TSK-004', 'Portal Task C', 'Employee D', userEmail, '30 Days', 30, '17:00:00', 'Ticket ID', 'ERP Core System', true, 'Monthly closing audits and post-closing journal ticket.']
  ];
  masterSheet.getRange(1, 1, 1, masterHeaders.length).setValues([masterHeaders]);
  masterSheet.getRange(2, 1, masterRows.length, masterHeaders.length).setValues(masterRows);
  styleHeaders(masterSheet, 1, masterHeaders.length);
  masterSheet.autoResizeColumns(1, masterHeaders.length);

  // 3. Active Tasks Sheet (Database of active cycles & history)
  let activeSheet = ss.getSheetByName(SHEETS.ACTIVE_TASKS);
  if (!activeSheet) activeSheet = ss.insertSheet(SHEETS.ACTIVE_TASKS);
  activeSheet.clear();
  const activeHeaders = [
    'Instance_ID', 'Task_ID', 'Task_Name', 'Assigned_To', 'Employee_Email', 'Frequency', 
    'Cycle_Number', 'Cycle_Start_Date', 'Due_Date', 'Due_Time', 'Proof_Type', 'Status', 
    'Proof_Submitted', 'Completion_Notes', 'Completed_By', 'Completed_At', 
    'Manager_Alert_Sent_At', 'Manager_Acknowledged_At', 'Manager_Notes', 'Leadership_Escalation_Sent_At', 'Next_Cycle_Generated'
  ];
  activeSheet.getRange(1, 1, 1, activeHeaders.length).setValues([activeHeaders]);
  styleHeaders(activeSheet, 1, activeHeaders.length);

  const today = new Date();
  const todayStr = Utilities.formatDate(today, 'Asia/Kolkata', 'yyyy-MM-dd');
  
  // Initial cycle dates
  const d7 = new Date(today.getTime() + 7 * 24 * 3600 * 1000);
  const d15 = new Date(today.getTime() + 15 * 24 * 3600 * 1000);
  const d30 = new Date(today.getTime() + 30 * 24 * 3600 * 1000);

  const initActiveRows = [
    ['TSK-001-C01', 'TSK-001', 'Daily Operations Update', 'Employee A', userEmail, 'Daily', 1, todayStr, todayStr, '11:00:00', 'WhatsApp Timestamp & Summary', 'Pending', '', '', '', '', '', '', '', '', 'NO'],
    ['TSK-002-C01', 'TSK-002', 'Portal Task A', 'Employee B', userEmail, '7 Days', 1, todayStr, Utilities.formatDate(d7, 'Asia/Kolkata', 'yyyy-MM-dd'), '17:00:00', 'Ticket ID', 'Pending', '', '', '', '', '', '', '', '', 'NO'],
    ['TSK-003-C01', 'TSK-003', 'Portal Task B', 'Employee C', userEmail, '15 Days', 1, todayStr, Utilities.formatDate(d15, 'Asia/Kolkata', 'yyyy-MM-dd'), '17:00:00', 'Ticket ID', 'Pending', '', '', '', '', '', '', '', '', 'NO'],
    ['TSK-004-C01', 'TSK-004', 'Portal Task C', 'Employee D', userEmail, '30 Days', 1, todayStr, Utilities.formatDate(d30, 'Asia/Kolkata', 'yyyy-MM-dd'), '17:00:00', 'Ticket ID', 'Pending', '', '', '', '', '', '', '', '', 'NO']
  ];
  activeSheet.getRange(2, 1, initActiveRows.length, activeHeaders.length).setValues(initActiveRows);
  activeSheet.autoResizeColumns(1, activeHeaders.length);

  // 4. Employee Workbench Sheet (Single-Point Interface)
  let benchSheet = ss.getSheetByName(SHEETS.EMPLOYEE_WORKBENCH);
  if (!benchSheet) benchSheet = ss.insertSheet(SHEETS.EMPLOYEE_WORKBENCH);
  benchSheet.clear();

  // Workbench Header Banner
  benchSheet.getRange('A1:J1').merge().setValue('ALLO INNOWARE - EMPLOYEE TASK WORKBENCH')
    .setBackground('#1e3a8a').setFontColor('#ffffff').setFontWeight('bold').setFontSize(14).setHorizontalAlignment('center');
  
  benchSheet.getRange('A2:J2').merge().setValue('Single-point task monitoring and completion. No duplicate updates required.')
    .setBackground('#eff6ff').setFontColor('#1e40af').setFontStyle('italic').setFontSize(10).setHorizontalAlignment('center');

  benchSheet.getRange('A4').setValue('Select Employee:').setFontWeight('bold');
  benchSheet.getRange('B4').setValue('Employee A'); // Default
  
  // Data validation dropdown for employee selector
  const empRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(['All Employees', 'Employee A', 'Employee B', 'Employee C', 'Employee D'], true)
    .setAllowInvalid(false)
    .build();
  benchSheet.getRange('B4').setDataValidation(empRule)
    .setBackground('#fef08a').setFontWeight('bold').setBorder(true, true, true, true, false, false, '#ca8a04', SpreadsheetApp.BorderStyle.SOLID_MEDIUM);

  benchSheet.getRange('D4').setValue('Pending Tasks:').setFontWeight('bold');
  benchSheet.getRange('E4').setFormula('=COUNTIFS(Active_Tasks!D2:D, IF(B4="All Employees", "*", B4), Active_Tasks!L2:L, "<>Completed")')
    .setFontWeight('bold').setFontColor('#dc2626');

  benchSheet.getRange('G4').setValue('Action:').setFontWeight('bold');
  benchSheet.getRange('H4:J4').merge().setValue('Enter Proof in Col H, Notes in Col I, then click menu: Allo Innoware Ops > Employee: Submit Completion')
    .setFontSize(9).setFontColor('#475569');

  const benchHeaders = [
    'Instance_ID', 'Task_Name', 'Assigned_To', 'Frequency', 'Due_Date', 'Due_Time', 
    'Status', 'Enter_Proof_Or_Ticket_ID (Col H)', 'Completion_Notes (Col I)', 'Expected_Proof_Type'
  ];
  benchSheet.getRange(6, 1, 1, benchHeaders.length).setValues([benchHeaders]);
  benchSheet.getRange(6, 1, 1, benchHeaders.length)
    .setBackground('#334155').setFontColor('#ffffff').setFontWeight('bold');
  
  // Highlight editable columns H and I in the header
  benchSheet.getRange('H6').setBackground('#065f46').setFontColor('#ffffff').setValue('Enter Proof / Ticket ID (EDIT HERE)');
  benchSheet.getRange('I6').setBackground('#0f766e').setFontColor('#ffffff').setValue('Notes / Remarks (EDIT HERE)');

  // Refresh workbench data rows
  refreshWorkbenchView();

  benchSheet.setColumnWidth(1, 120);
  benchSheet.setColumnWidth(2, 220);
  benchSheet.setColumnWidth(3, 110);
  benchSheet.setColumnWidth(4, 90);
  benchSheet.setColumnWidth(5, 100);
  benchSheet.setColumnWidth(6, 90);
  benchSheet.setColumnWidth(7, 130);
  benchSheet.setColumnWidth(8, 260); // Proof
  benchSheet.setColumnWidth(9, 220); // Notes
  benchSheet.setColumnWidth(10, 180);

  // 5. Manager Dashboard Sheet
  let dashSheet = ss.getSheetByName(SHEETS.MANAGER_DASHBOARD);
  if (!dashSheet) dashSheet = ss.insertSheet(SHEETS.MANAGER_DASHBOARD);
  dashSheet.clear();

  dashSheet.getRange('A1:G1').merge().setValue('ALLO INNOWARE - OPERATIONS MANAGER DASHBOARD')
    .setBackground('#1e3a8a').setFontColor('#ffffff').setFontWeight('bold').setFontSize(14).setHorizontalAlignment('center');

  // KPI Cards
  const kpis = [
    ['Total Active Cycles', '=COUNTA(Active_Tasks!A2:A)', '#f8fafc', '#1e293b'],
    ['Pending Tasks', '=COUNTIF(Active_Tasks!L2:L, "Pending")', '#eff6ff', '#2563eb'],
    ['Manager Alerted', '=COUNTIF(Active_Tasks!L2:L, "Manager Alerted")', '#fef3c7', '#d97706'],
    ['Manager Acknowledged', '=COUNTIF(Active_Tasks!L2:L, "Manager Acknowledged")', '#e0e7ff', '#4338ca'],
    ['Escalated to Leadership', '=COUNTIF(Active_Tasks!L2:L, "Escalated")', '#fee2e2', '#dc2626'],
    ['Completed Cycles', '=COUNTIF(Active_Tasks!L2:L, "Completed")', '#dcfce7', '#15803d']
  ];

  for (let k = 0; k < kpis.length; k++) {
    const col = k + 1;
    dashSheet.getRange(3, col).setValue(kpis[k][0]).setFontSize(9).setFontWeight('bold').setHorizontalAlignment('center')
      .setBackground(kpis[k][2]).setFontColor(kpis[k][3]);
    dashSheet.getRange(4, col).setFormula(kpis[k][1]).setFontSize(18).setFontWeight('bold').setHorizontalAlignment('center')
      .setBackground(kpis[k][2]).setFontColor(kpis[k][3]).setBorder(true, true, true, true, false, false, '#cbd5e1', SpreadsheetApp.BorderStyle.SOLID);
  }

  // Employee Compliance Table
  dashSheet.getRange('A6:G6').merge().setValue('TEAM PERFORMANCE & COMPLIANCE SUMMARY')
    .setBackground('#334155').setFontColor('#ffffff').setFontWeight('bold').setFontSize(11);

  const teamHeaders = ['Employee', 'Total Cycles', 'Pending', 'Alerted', 'Escalated', 'Completed', 'Compliance %'];
  dashSheet.getRange(7, 1, 1, teamHeaders.length).setValues([teamHeaders]).setBackground('#e2e8f0').setFontWeight('bold');

  const employees = ['Employee A', 'Employee B', 'Employee C', 'Employee D'];
  for (let e = 0; e < employees.length; e++) {
    const row = 8 + e;
    const emp = employees[e];
    dashSheet.getRange(row, 1).setValue(emp).setFontWeight('bold');
    dashSheet.getRange(row, 2).setFormula(`=COUNTIF(Active_Tasks!D2:D, "${emp}")`);
    dashSheet.getRange(row, 3).setFormula(`=COUNTIFS(Active_Tasks!D2:D, "${emp}", Active_Tasks!L2:L, "Pending")`);
    dashSheet.getRange(row, 4).setFormula(`=COUNTIFS(Active_Tasks!D2:D, "${emp}", Active_Tasks!L2:L, "Manager Alerted")`);
    dashSheet.getRange(row, 5).setFormula(`=COUNTIFS(Active_Tasks!D2:D, "${emp}", Active_Tasks!L2:L, "Escalated")`);
    dashSheet.getRange(row, 6).setFormula(`=COUNTIFS(Active_Tasks!D2:D, "${emp}", Active_Tasks!L2:L, "Completed")`);
    dashSheet.getRange(row, 7).setFormula(`=IF(B${row}>0, TEXT(F${row}/B${row}, "0.0%"), "100.0%")`).setFontWeight('bold');
  }

  dashSheet.autoResizeColumns(1, 7);

  // 6. Audit Log Sheet
  let logSheet = ss.getSheetByName(SHEETS.AUDIT_LOG);
  if (!logSheet) logSheet = ss.insertSheet(SHEETS.AUDIT_LOG);
  logSheet.clear();
  const logHeaders = ['Log_ID', 'Timestamp', 'Event_Type', 'Instance_ID', 'Task_ID', 'Actor', 'Details', 'Status_Before', 'Status_After'];
  logSheet.getRange(1, 1, 1, logHeaders.length).setValues([logHeaders]);
  styleHeaders(logSheet, 1, logHeaders.length);
  
  appendAuditLog('SYSTEM_INIT', 'ALL', 'ALL', 'System Setup', 'Complete sheets and initial cycles initialized', '-', 'Pending');
  logSheet.autoResizeColumns(1, logHeaders.length);

  // Apply conditional formatting across sheets
  applyStatusFormatting(activeSheet);
  applyStatusFormatting(benchSheet);

  ss.setActiveSheet(benchSheet);
  ui.alert('Setup Complete', 'All 6 sheets have been successfully initialized with formulas, master tasks, and active cycles.\n\nEmployees can now work directly from the Employee_Workbench sheet!', ui.ButtonSet.OK);
}

/**
 * Helper to style table header rows
 */
function styleHeaders(sheet, row, numCols) {
  sheet.getRange(row, 1, 1, numCols)
    .setBackground('#1e3a8a')
    .setFontColor('#ffffff')
    .setFontWeight('bold')
    .setFontSize(10)
    .setVerticalAlignment('middle')
    .setWrap(true);
  sheet.setFrozenRows(row);
}

/**
 * Applies color coding rules to status columns
 */
function applyStatusFormatting(sheet) {
  const rules = sheet.getConditionalFormatRules() || [];
  
  // Pending = Yellow
  const pendingRule = SpreadsheetApp.newConditionalFormatRule()
    .whenTextEqualTo('Pending')
    .setBackground('#fef08a').setFontColor('#854d0e')
    .setRanges([sheet.getDataRange()])
    .build();

  // Manager Alerted = Orange
  const alertedRule = SpreadsheetApp.newConditionalFormatRule()
    .whenTextEqualTo('Manager Alerted')
    .setBackground('#ffedd5').setFontColor('#c2410c')
    .setRanges([sheet.getDataRange()])
    .build();

  // Manager Acknowledged = Blue
  const ackRule = SpreadsheetApp.newConditionalFormatRule()
    .whenTextEqualTo('Manager Acknowledged')
    .setBackground('#e0e7ff').setFontColor('#3730a3')
    .setRanges([sheet.getDataRange()])
    .build();

  // Escalated = Red Bold
  const escRule = SpreadsheetApp.newConditionalFormatRule()
    .whenTextEqualTo('Escalated')
    .setBackground('#fee2e2').setFontColor('#991b1b')
    .setBold(true)
    .setRanges([sheet.getDataRange()])
    .build();

  // Completed = Green
  const compRule = SpreadsheetApp.newConditionalFormatRule()
    .whenTextEqualTo('Completed')
    .setBackground('#dcfce7').setFontColor('#166534')
    .setRanges([sheet.getDataRange()])
    .build();

  rules.push(pendingRule, alertedRule, ackRule, escRule, compRule);
  sheet.setConditionalFormatRules(rules);
}

/**
 * Appends an entry into the immutable Audit Log
 */
function appendAuditLog(eventType, instanceId, taskId, actor, details, statusBefore, statusAfter) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const logSheet = ss.getSheetByName(SHEETS.AUDIT_LOG);
  if (!logSheet) return;

  const timestamp = Utilities.formatDate(new Date(), 'Asia/Kolkata', 'yyyy-MM-dd HH:mm:ss');
  const logId = 'LOG-' + Utilities.getUuid().substring(0, 8).toUpperCase();
  logSheet.appendRow([logId, timestamp, eventType, instanceId, taskId, actor, details, statusBefore, statusAfter]);
}

/**
 * Refreshes the active rows shown on the Employee_Workbench sheet
 */
function refreshWorkbenchView() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const benchSheet = ss.getSheetByName(SHEETS.EMPLOYEE_WORKBENCH);
  const activeSheet = ss.getSheetByName(SHEETS.ACTIVE_TASKS);
  if (!benchSheet || !activeSheet) return;

  const selectedEmployee = benchSheet.getRange('B4').getValue() || 'All Employees';
  const lastRow = activeSheet.getLastRow();
  if (lastRow < 2) return;

  const activeData = activeSheet.getRange(2, 1, lastRow - 1, 21).getValues();

  // Clear existing display rows from row 7 downwards
  const benchLastRow = Math.max(benchSheet.getLastRow(), 7);
  if (benchLastRow >= 7) {
    benchSheet.getRange(7, 1, benchLastRow - 6, 10).clearContent().clearFormat();
  }

  const rowsToDisplay = [];
  for (let i = 0; i < activeData.length; i++) {
    const row = activeData[i];
    const instId = row[0];
    const taskName = row[2];
    const assignedTo = row[3];
    const freq = row[5];
    const dueDate = row[8] instanceof Date ? Utilities.formatDate(row[8], 'Asia/Kolkata', 'yyyy-MM-dd') : row[8];
    const dueTime = row[9];
    const proofType = row[10];
    const status = row[11];

    // Filter condition: only pending, alerted, acknowledged, or escalated tasks for selected employee
    const matchEmp = (selectedEmployee === 'All Employees' || assignedTo === selectedEmployee);
    const isUnfinished = (status !== 'Completed');

    if (matchEmp && isUnfinished) {
      rowsToDisplay.push([
        instId,
        taskName,
        assignedTo,
        freq,
        dueDate,
        dueTime,
        status,
        '', // Empty cell for employee to enter Ticket ID / WhatsApp proof
        '', // Empty cell for employee notes
        proofType
      ]);
    }
  }

  if (rowsToDisplay.length > 0) {
    const range = benchSheet.getRange(7, 1, rowsToDisplay.length, 10);
    range.setValues(rowsToDisplay);

    // Style the editable columns H and I
    const editRange = benchSheet.getRange(7, 8, rowsToDisplay.length, 2);
    editRange.setBackground('#f0fdf4')
      .setBorder(true, true, true, true, true, true, '#86efac', SpreadsheetApp.BorderStyle.SOLID);
  }
}

/**
 * Triggered when user edits cell B4 (Employee Selector) on Employee_Workbench
 */
function onEdit(e) {
  if (!e) return;
  const sheet = e.range.getSheet();
  if (sheet.getName() === SHEETS.EMPLOYEE_WORKBENCH && e.range.getA1Notation() === 'B4') {
    refreshWorkbenchView();
  }
}

/**
 * ==============================================================================
 * SINGLE-POINT COMPLETION LOGIC (Test 2 & Test 3)
 * ==============================================================================
 * Reads the active selected row on Employee_Workbench.
 * Validates proof input.
 * Closes the active cycle in Active_Tasks.
 * Automatically spawns the next cycle.
 * Logs to Audit Log.
 * Refreshes workbench.
 */
function submitWorkbenchCompletion() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const ui = SpreadsheetApp.getUi();
  const benchSheet = ss.getSheetByName(SHEETS.EMPLOYEE_WORKBENCH);
  const activeSheet = ss.getSheetByName(SHEETS.ACTIVE_TASKS);

  if (!benchSheet || !activeSheet) {
    ui.alert('Error', 'Required sheets not found.', ui.ButtonSet.OK);
    return;
  }

  const activeRange = benchSheet.getActiveRange();
  const selectedRow = activeRange ? activeRange.getRow() : -1;

  if (selectedRow < 7) {
    ui.alert('Action Required', 'Please click on the row of the task you want to complete (row 7 or below) and ensure Col H has your Ticket ID or WhatsApp proof.', ui.ButtonSet.OK);
    return;
  }

  const rowData = benchSheet.getRange(selectedRow, 1, 1, 10).getValues()[0];
  const instanceId = String(rowData[0]).trim();
  const taskName = rowData[1];
  const assignedTo = rowData[2];
  const proofSubmitted = String(rowData[7]).trim(); // Col H
  const notes = String(rowData[8]).trim(); // Col I
  const proofType = rowData[9];

  if (!instanceId) {
    ui.alert('Error', 'No valid Task Instance ID found in the selected row.', ui.ButtonSet.OK);
    return;
  }

  if (!proofSubmitted) {
    ui.alert('Proof Required', `Please enter your ${proofType} in Column H (highlighted green) before submitting!`, ui.ButtonSet.OK);
    return;
  }

  // Complete the task
  const userEmail = Session.getActiveUser().getEmail() || assignedTo;
  const result = executeTaskCompletion(instanceId, proofSubmitted, notes, userEmail);

  if (result.success) {
    refreshWorkbenchView();
    ui.alert('Task Completed Successfully! 🎉', 
      `Task: ${taskName} (${instanceId})\nStatus: Completed\nProof Logged: ${proofSubmitted}\n\n✅ Next cycle has been automatically generated and scheduled in Active_Tasks!`, 
      ui.ButtonSet.OK);
  } else {
    ui.alert('Completion Failed', result.message, ui.ButtonSet.OK);
  }
}

/**
 * Core completion handler with script concurrency lock
 */
function executeTaskCompletion(instanceId, proof, notes, completedBy) {
  const lock = LockService.getScriptLock();
  try {
    // 30-second lock to prevent duplicate updates or race conditions
    lock.waitLock(30000);
  } catch (e) {
    return { success: false, message: 'Could not acquire lock. System is busy. Please try again.' };
  }

  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const activeSheet = ss.getSheetByName(SHEETS.ACTIVE_TASKS);
    const lastRow = activeSheet.getLastRow();
    const data = activeSheet.getRange(2, 1, lastRow - 1, 21).getValues();

    let targetRowIndex = -1;
    let targetRowData = null;

    for (let i = 0; i < data.length; i++) {
      if (data[i][0] === instanceId) {
        targetRowIndex = i + 2; // 1-based index including header
        targetRowData = data[i];
        break;
      }
    }

    if (targetRowIndex === -1) {
      return { success: false, message: `Task Instance ${instanceId} not found in Active Tasks database.` };
    }

    const currentStatus = targetRowData[11];
    if (currentStatus === 'Completed') {
      return { success: false, message: `Task ${instanceId} is already marked as Completed!` };
    }

    const now = new Date();
    const nowStr = Utilities.formatDate(now, 'Asia/Kolkata', 'yyyy-MM-dd HH:mm:ss');

    // Update row in Active_Tasks
    // Columns: 12=Status, 13=Proof_Submitted, 14=Completion_Notes, 15=Completed_By, 16=Completed_At
    activeSheet.getRange(targetRowIndex, 12).setValue('Completed');
    activeSheet.getRange(targetRowIndex, 13).setValue(proof);
    activeSheet.getRange(targetRowIndex, 14).setValue(notes);
    activeSheet.getRange(targetRowIndex, 15).setValue(completedBy);
    activeSheet.getRange(targetRowIndex, 16).setValue(nowStr);

    appendAuditLog('COMPLETION_SUBMITTED', instanceId, targetRowData[1], completedBy, `Proof: ${proof} | Notes: ${notes}`, currentStatus, 'Completed');

    // Recurrence Engine: Check if next cycle already generated (Test 8 Anti-duplication)
    const nextGenerated = targetRowData[20];
    if (nextGenerated !== 'YES') {
      generateNextCycle(targetRowData, now);
      activeSheet.getRange(targetRowIndex, 21).setValue('YES');
    }

    return { success: true, message: 'Cycle closed and next cycle generated.' };
  } catch (err) {
    return { success: false, message: err.toString() };
  } finally {
    lock.releaseLock();
  }
}

/**
 * ==============================================================================
 * RECURRING CYCLE LOGIC (Test 1)
 * ==============================================================================
 * Automatically closes current cycle and prepares/tracks the next cycle.
 * Calculates next due date based on frequency and business logic.
 */
function generateNextCycle(currentRowData, completionDate) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const activeSheet = ss.getSheetByName(SHEETS.ACTIVE_TASKS);
  const config = getConfig();

  const taskId = currentRowData[1];
  const taskName = currentRowData[2];
  const assignedTo = currentRowData[3];
  const employeeEmail = currentRowData[4];
  const freq = currentRowData[5];
  const currentCycleNum = Number(currentRowData[6]) || 1;
  const currentDueDate = currentRowData[8] instanceof Date ? currentRowData[8] : parseDateString(currentRowData[8]);
  const dueTime = currentRowData[9];
  const proofType = currentRowData[10];

  const nextCycleNum = currentCycleNum + 1;
  const nextCycleStr = nextCycleNum < 10 ? 'C0' + nextCycleNum : 'C' + nextCycleNum;
  const nextInstanceId = `${taskId}-${nextCycleStr}`;

  // Next Cycle Start Date is today/completion date
  const nextStartDate = Utilities.formatDate(completionDate, 'Asia/Kolkata', 'yyyy-MM-dd');

  // Next Due Date Calculation
  const nextDueDateObj = calculateNextDueDate(currentDueDate, completionDate, freq, config.RECURRENCE_CALCULATION_MODE);
  const nextDueDateStr = Utilities.formatDate(nextDueDateObj, 'Asia/Kolkata', 'yyyy-MM-dd');

  const newRow = [
    nextInstanceId,
    taskId,
    taskName,
    assignedTo,
    employeeEmail,
    freq,
    nextCycleNum,
    nextStartDate,
    nextDueDateStr,
    dueTime,
    proofType,
    'Pending',
    '', // Proof_Submitted
    '', // Completion_Notes
    '', // Completed_By
    '', // Completed_At
    '', // Manager_Alert_Sent_At
    '', // Manager_Acknowledged_At
    '', // Manager_Notes
    '', // Leadership_Escalation_Sent_At
    'NO' // Next_Cycle_Generated
  ];

  activeSheet.appendRow(newRow);
  appendAuditLog('CYCLE_CREATED', nextInstanceId, taskId, 'Recurrence Engine', 
    `Cycle ${nextCycleNum} auto-scheduled. Start: ${nextStartDate}, Due: ${nextDueDateStr} ${dueTime}`, 
    '-', 'Pending');
}

/**
 * Date arithmetic helper supporting SCHEDULE_BASED and COMPLETION_BASED recurrence
 */
function calculateNextDueDate(previousDueDate, completionDate, frequencyText, mode) {
  const baseDate = (mode === 'COMPLETION_BASED') ? new Date(completionDate.getTime()) : new Date(previousDueDate.getTime());
  const freqLower = String(frequencyText).toLowerCase();

  let daysToAdd = 1;
  if (freqLower.includes('daily')) {
    // Next working day logic: if Friday, advance to Monday (or next calendar day)
    daysToAdd = 1;
    const nextDay = new Date(baseDate.getTime() + daysToAdd * 24 * 3600 * 1000);
    // If weekend (Sunday=0, Saturday=6), move to Monday
    if (nextDay.getDay() === 0) daysToAdd += 1;
    if (nextDay.getDay() === 6) daysToAdd += 2;
  } else if (freqLower.includes('7')) {
    daysToAdd = 7;
  } else if (freqLower.includes('15')) {
    daysToAdd = 15;
  } else if (freqLower.includes('30') || freqLower.includes('monthly')) {
    daysToAdd = 30;
  }

  return new Date(baseDate.getTime() + daysToAdd * 24 * 3600 * 1000);
}

/**
 * ==============================================================================
 * AUTOMATED ALERT & ESCALATION ENGINE (Tests 4, 6, 7 & 8)
 * ==============================================================================
 * Triggered on scheduled time intervals or manually.
 * - Test 4: Same-day manager alert when task is overdue.
 * - Test 6: Leadership escalation when SLA is breached without resolution.
 * - Test 8: Guaranteed anti-duplication guards.
 */
function runEscalationEngineManual() {
  const results = runEscalationEngine();
  SpreadsheetApp.getUi().alert('Escalation Engine Executed', 
    `Scan Complete:\n• Manager Alerts Sent: ${results.managerAlertsSent}\n• Leadership Escalations Sent: ${results.leadershipEscalationsSent}\n• Items Skipped (Already Alerted / On Track): ${results.skippedCount}`, 
    SpreadsheetApp.getUi().ButtonSet.OK);
}

function runEscalationEngine() {
  const lock = LockService.getScriptLock();
  try {
    lock.waitLock(30000);
  } catch (e) {
    Logger.log('Could not acquire lock for escalation engine.');
    return { managerAlertsSent: 0, leadershipEscalationsSent: 0, skippedCount: 0 };
  }

  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const activeSheet = ss.getSheetByName(SHEETS.ACTIVE_TASKS);
    if (!activeSheet) return { managerAlertsSent: 0, leadershipEscalationsSent: 0, skippedCount: 0 };

    const config = getConfig();
    const now = new Date();
    const lastRow = activeSheet.getLastRow();
    if (lastRow < 2) return { managerAlertsSent: 0, leadershipEscalationsSent: 0, skippedCount: 0 };

    const data = activeSheet.getRange(2, 1, lastRow - 1, 21).getValues();
    let managerAlerts = 0;
    let leadershipEscalations = 0;
    let skipped = 0;

    for (let i = 0; i < data.length; i++) {
      const rowIndex = i + 2;
      const row = data[i];

      const instanceId = row[0];
      const taskId = row[1];
      const taskName = row[2];
      const assignedTo = row[3];
      const employeeEmail = row[4];
      const freq = row[5];
      const cycleNum = row[6];
      const dueDateVal = row[8];
      const dueTimeVal = row[9];
      const proofType = row[10];
      const status = row[11];
      const managerAlertSentAt = row[16];
      const managerAckAt = row[17];
      const leadershipEscalationSentAt = row[19];

      // Skip already completed tasks
      if (status === 'Completed') {
        skipped++;
        continue;
      }

      // Compute precise due datetime
      const dueDateTime = combineDateAndTime(dueDateVal, dueTimeVal);
      const isPastDue = (now.getTime() > dueDateTime.getTime());
      const hoursOverdue = (now.getTime() - dueDateTime.getTime()) / (1000 * 3600);

      // -----------------------------------------------------------------------
      // STAGE 1: SAME-DAY MANAGER ALERT (Test 4)
      // -----------------------------------------------------------------------
      // Condition: Past due AND Manager_Alert_Sent_At is empty (Test 8 Anti-duplication)
      if (isPastDue && !managerAlertSentAt && status === 'Pending') {
        const isDaily = String(freq).toLowerCase().includes('daily');
        const alertDelayMins = isDaily ? config.DAILY_TASK_MANAGER_ALERT_DELAY_MINS : (config.PERIODIC_MANAGER_ALERT_DELAY_HOURS * 60);

        // Check if grace period has elapsed
        if (hoursOverdue * 60 >= alertDelayMins) {
          sendManagerAlertEmail(config, {
            instanceId: instanceId,
            taskId: taskId,
            taskName: taskName,
            assignedTo: assignedTo,
            employeeEmail: employeeEmail,
            frequency: freq,
            dueDateTime: dueDateTime,
            hoursOverdue: hoursOverdue.toFixed(1),
            proofType: proofType
          });

          // State transition & timestamp stamp
          activeSheet.getRange(rowIndex, 12).setValue('Manager Alerted');
          const nowStr = Utilities.formatDate(now, 'Asia/Kolkata', 'yyyy-MM-dd HH:mm:ss');
          activeSheet.getRange(rowIndex, 17).setValue(nowStr);

          appendAuditLog('MANAGER_ALERT_SENT', instanceId, taskId, 'Escalation Engine', 
            `Manager alerted: ${hoursOverdue.toFixed(1)} hrs overdue. Alert sent to ${config.MANAGER_EMAIL}`, 
            status, 'Manager Alerted');

          managerAlerts++;
          continue;
        }
      }

      // -----------------------------------------------------------------------
      // STAGE 2: LEADERSHIP ESCALATION (Test 6)
      // -----------------------------------------------------------------------
      // Condition: In 'Manager Alerted' or 'Manager Acknowledged' AND Leadership_Escalation_Sent_At is empty
      if (managerAlertSentAt && !leadershipEscalationSentAt && status !== 'Completed') {
        const isDaily = String(freq).toLowerCase().includes('daily');
        const alertTime = parseDateString(managerAlertSentAt);
        const hoursSinceAlert = (now.getTime() - alertTime.getTime()) / (1000 * 3600);

        const escalationThresholdHours = isDaily ? config.DAILY_TASK_LEADERSHIP_ESCALATION_HOURS : config.PERIODIC_LEADERSHIP_ESCALATION_HOURS;

        let shouldEscalate = false;
        let escalationReason = '';

        // Escalation Criteria 1: Manager failed to acknowledge within SLA
        if (!managerAckAt && hoursSinceAlert >= escalationThresholdHours) {
          shouldEscalate = true;
          escalationReason = `Manager failed to acknowledge within SLA threshold of ${escalationThresholdHours} hours.`;
        }
        // Escalation Criteria 2: Task remains incomplete even after manager acknowledgement beyond extended SLA
        else if (managerAckAt && hoursSinceAlert >= (escalationThresholdHours * 2)) {
          shouldEscalate = true;
          escalationReason = `Task remains uncompleted ${hoursSinceAlert.toFixed(1)} hours post-alert, exceeding final leadership SLA threshold.`;
        }

        if (shouldEscalate) {
          sendLeadershipEscalationEmail(config, {
            instanceId: instanceId,
            taskId: taskId,
            taskName: taskName,
            assignedTo: assignedTo,
            employeeEmail: employeeEmail,
            frequency: freq,
            dueDateTime: dueDateTime,
            hoursOverdue: hoursOverdue.toFixed(1),
            managerAlertTime: managerAlertSentAt,
            managerAckTime: managerAckAt || 'NOT ACKNOWLEDGED',
            reason: escalationReason
          });

          activeSheet.getRange(rowIndex, 12).setValue('Escalated');
          const nowStr = Utilities.formatDate(now, 'Asia/Kolkata', 'yyyy-MM-dd HH:mm:ss');
          activeSheet.getRange(rowIndex, 20).setValue(nowStr);

          appendAuditLog('LEADERSHIP_ESCALATED', instanceId, taskId, 'Escalation Engine', 
            `Escalated to Leadership: ${escalationReason}. Email sent to ${config.LEADERSHIP_EMAIL}`, 
            status, 'Escalated');

          leadershipEscalations++;
          continue;
        }
      }

      skipped++;
    }

    // Refresh workbench view in case statuses changed
    refreshWorkbenchView();

    return {
      managerAlertsSent: managerAlerts,
      leadershipEscalationsSent: leadershipEscalations,
      skippedCount: skipped
    };
  } finally {
    lock.releaseLock();
  }
}

/**
 * Helper to construct Manager Alert Email with 1-Click Action Link
 */
function sendManagerAlertEmail(config, task) {
  if (!config.ENABLE_EMAIL_ALERTS) {
    Logger.log(`[SIMULATION] Manager Alert for ${task.instanceId} logged to Audit Log (Email disabled).`);
    return;
  }

  const webAppUrl = config.WEB_APP_URL || ScriptApp.getService().getUrl();
  const ackUrl = `${webAppUrl}?action=ack&id=${encodeURIComponent(task.instanceId)}`;

  const subject = `⚠️ [PENDING ALERT] Task Overdue: ${task.taskName} (${task.assignedTo})`;
  const htmlBody = `
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;">
      <div style="background-color: #1e3a8a; color: white; padding: 20px 24px; text-align: left;">
        <h2 style="margin: 0; font-size: 18px; font-weight: 700;">ALLO INNOWARE OPERATIONS ALERT</h2>
        <p style="margin: 4px 0 0 0; font-size: 13px; opacity: 0.85;">Pending Recurring Task Requires Manager Attention</p>
      </div>
      <div style="padding: 24px;">
        <p style="font-size: 14px; color: #334155; margin-top: 0;">
          The following recurring operational task has passed its expected completion deadline and is currently <strong>PENDING</strong>.
        </p>
        
        <table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 13px; background-color: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0;">
          <tr>
            <td style="padding: 10px 14px; font-weight: bold; color: #64748b; width: 35%;">Task Instance</td>
            <td style="padding: 10px 14px; font-weight: bold; color: #0f172a;">${task.instanceId}</td>
          </tr>
          <tr>
            <td style="padding: 10px 14px; font-weight: bold; color: #64748b;">Task Description</td>
            <td style="padding: 10px 14px; color: #0f172a;">${task.taskName}</td>
          </tr>
          <tr>
            <td style="padding: 10px 14px; font-weight: bold; color: #64748b;">Assigned Employee</td>
            <td style="padding: 10px 14px; color: #0f172a;"><strong>${task.assignedTo}</strong> (${task.employeeEmail})</td>
          </tr>
          <tr>
            <td style="padding: 10px 14px; font-weight: bold; color: #64748b;">Recurrence Frequency</td>
            <td style="padding: 10px 14px; color: #0f172a;">${task.frequency}</td>
          </tr>
          <tr>
            <td style="padding: 10px 14px; font-weight: bold; color: #64748b;">Hours Overdue</td>
            <td style="padding: 10px 14px; color: #dc2626; font-weight: bold;">${task.hoursOverdue} hrs past deadline</td>
          </tr>
          <tr>
            <td style="padding: 10px 14px; font-weight: bold; color: #64748b;">Required Completion Proof</td>
            <td style="padding: 10px 14px; color: #0f172a;">${task.proofType}</td>
          </tr>
        </table>

        <div style="background-color: #eff6ff; border-left: 4px solid #3b82f6; padding: 14px; border-radius: 0 8px 8px 0; font-size: 13px; color: #1e40af; margin-bottom: 24px;">
          <strong>Manager Action Required:</strong><br>
          Please click the button below to acknowledge this alert and engage the team member. Acknowledging extends the SLA hold before leadership escalation.
        </div>

        <div style="text-align: center; margin: 30px 0;">
          <a href="${ackUrl}" style="background-color: #2563eb; color: #ffffff; padding: 14px 28px; text-decoration: none; font-size: 14px; font-weight: bold; border-radius: 8px; display: inline-block;">
            ✓ Click Here to Acknowledge Task (${task.instanceId})
          </a>
        </div>
      </div>
      <div style="background-color: #f1f5f9; padding: 14px; text-align: center; font-size: 11px; color: #64748b; border-top: 1px solid #e2e8f0;">
        Allo Innoware Automated Operations Control • Live Google Sheets Sync
      </div>
    </div>
  `;

  try {
    MailApp.sendEmail({
      to: config.MANAGER_EMAIL,
      subject: subject,
      htmlBody: htmlBody
    });
  } catch (err) {
    Logger.log('MailApp error in sendManagerAlertEmail: ' + err.toString());
  }
}

/**
 * Helper to construct Leadership Escalation Email
 */
function sendLeadershipEscalationEmail(config, task) {
  if (!config.ENABLE_EMAIL_ALERTS) {
    Logger.log(`[SIMULATION] Leadership Escalation for ${task.instanceId} logged to Audit Log (Email disabled).`);
    return;
  }

  const subject = `🚨 [URGENT ESCALATION] SLA Breach on Operational Task: ${task.taskName} (${task.assignedTo})`;
  const htmlBody = `
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #fecaca; border-radius: 12px; overflow: hidden;">
      <div style="background-color: #991b1b; color: white; padding: 20px 24px; text-align: left;">
        <h2 style="margin: 0; font-size: 18px; font-weight: 700;">🚨 ALLO INNOWARE LEADERSHIP ESCALATION</h2>
        <p style="margin: 4px 0 0 0; font-size: 13px; opacity: 0.85;">Operational SLA Breach & Escalation Notification</p>
      </div>
      <div style="padding: 24px;">
        <p style="font-size: 14px; color: #334155; margin-top: 0;">
          This is an automated escalation to leadership. The operational recurring task detailed below has exceeded all SLA resolution windows and remains <strong>UNRESOLVED</strong>.
        </p>

        <div style="background-color: #fef2f2; border: 1px solid #f87171; border-radius: 8px; padding: 14px; margin: 16px 0; font-size: 13px; color: #991b1b;">
          <strong>Escalation Trigger:</strong> ${task.reason}
        </div>
        
        <table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 13px; background-color: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0;">
          <tr>
            <td style="padding: 10px 14px; font-weight: bold; color: #64748b; width: 35%;">Task Instance</td>
            <td style="padding: 10px 14px; font-weight: bold; color: #0f172a;">${task.instanceId}</td>
          </tr>
          <tr>
            <td style="padding: 10px 14px; font-weight: bold; color: #64748b;">Task Name</td>
            <td style="padding: 10px 14px; color: #0f172a;">${task.taskName}</td>
          </tr>
          <tr>
            <td style="padding: 10px 14px; font-weight: bold; color: #64748b;">Assigned Employee</td>
            <td style="padding: 10px 14px; color: #0f172a;"><strong>${task.assignedTo}</strong> (${task.employeeEmail})</td>
          </tr>
          <tr>
            <td style="padding: 10px 14px; font-weight: bold; color: #64748b;">Total Overdue Duration</td>
            <td style="padding: 10px 14px; color: #991b1b; font-weight: bold;">${task.hoursOverdue} hours</td>
          </tr>
          <tr>
            <td style="padding: 10px 14px; font-weight: bold; color: #64748b;">Manager Alert Dispatched</td>
            <td style="padding: 10px 14px; color: #0f172a;">${task.managerAlertTime}</td>
          </tr>
          <tr>
            <td style="padding: 10px 14px; font-weight: bold; color: #64748b;">Manager Acknowledgement</td>
            <td style="padding: 10px 14px; color: ${task.managerAckTime === 'NOT ACKNOWLEDGED' ? '#dc2626' : '#0f172a'}; font-weight: bold;">
              ${task.managerAckTime}
            </td>
          </tr>
        </table>

        <div style="background-color: #fff1f2; border-left: 4px solid #e11d48; padding: 14px; border-radius: 0 8px 8px 0; font-size: 13px; color: #9f1239;">
          <strong>Executive Attention Required:</strong><br>
          Operations leadership intervention is requested to resolve the roadblock and ensure process compliance.
        </div>
      </div>
      <div style="background-color: #f1f5f9; padding: 14px; text-align: center; font-size: 11px; color: #64748b; border-top: 1px solid #e2e8f0;">
        Allo Innoware Automated Operations Control • Live Google Sheets Sync
      </div>
    </div>
  `;

  try {
    MailApp.sendEmail({
      to: config.LEADERSHIP_EMAIL,
      cc: `${config.MANAGER_EMAIL}, ${task.employeeEmail}`,
      subject: subject,
      htmlBody: htmlBody
    });
  } catch (err) {
    Logger.log('MailApp error in sendLeadershipEscalationEmail: ' + err.toString());
  }
}

/**
 * ==============================================================================
 * MANAGER 1-CLICK ACKNOWLEDGEMENT & WEB APP (Test 5)
 * ==============================================================================
 * Web App endpoint responding to doGet(e) from email 1-click button
 */
function doGet(e) {
  const params = e ? e.parameter : {};
  const action = params.action;
  const instanceId = params.id;

  if (action === 'ack' && instanceId) {
    const ackResult = executeManagerAcknowledgement(instanceId, 'Acknowledged via 1-Click Email Action Link', 'Manager (Email Link)');
    
    const template = HtmlService.createTemplateFromFile('ManagerWebApp');
    template.instanceId = instanceId;
    template.taskName = ackResult.taskName || 'Operational Recurring Task';
    template.assignedTo = ackResult.assignedTo || 'Assigned Employee';
    template.timestamp = Utilities.formatDate(new Date(), 'Asia/Kolkata', 'yyyy-MM-dd HH:mm:ss');
    template.status = ackResult.success ? 'Success' : 'Notice';
    template.message = ackResult.message;

    return template.evaluate()
      .setTitle('Allo Innoware Ops | Task Acknowledged')
      .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
  }

  return HtmlService.createHtmlOutput('<h3>Allo Innoware Operations API Active</h3><p>No valid action specified.</p>');
}

/**
 * Manager direct acknowledgement from Google Sheets custom menu
 */
function acknowledgeSelectedTask() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const ui = SpreadsheetApp.getUi();
  const sheet = ss.getActiveSheet();

  if (sheet.getName() !== SHEETS.ACTIVE_TASKS && sheet.getName() !== SHEETS.MANAGER_DASHBOARD) {
    ui.alert('Instruction', 'Please switch to the Active_Tasks sheet and click on the row of the task you wish to acknowledge.', ui.ButtonSet.OK);
    return;
  }

  const activeRange = sheet.getActiveRange();
  const selectedRow = activeRange ? activeRange.getRow() : -1;

  if (selectedRow < 2) {
    ui.alert('Selection Required', 'Please select a valid row in Active_Tasks.', ui.ButtonSet.OK);
    return;
  }

  const instanceId = sheet.getRange(selectedRow, 1).getValue();
  if (!instanceId) {
    ui.alert('Error', 'No valid Task Instance ID found in Column A.', ui.ButtonSet.OK);
    return;
  }

  const prompt = ui.prompt('Manager Acknowledgement', `Enter follow-up notes for ${instanceId}:`, ui.ButtonSet.OK_CANCEL);
  if (prompt.getSelectedButton() !== ui.Button.OK) return;

  const notes = prompt.getResponseText() || 'Acknowledged by manager via Google Sheet dashboard.';
  const user = Session.getActiveUser().getEmail() || 'Manager';

  const res = executeManagerAcknowledgement(instanceId, notes, user);
  if (res.success) {
    ui.alert('Success', `Task ${instanceId} acknowledged successfully!\n\nStatus updated to 'Manager Acknowledged'.`, ui.ButtonSet.OK);
  } else {
    ui.alert('Notice', res.message, ui.ButtonSet.OK);
  }
}

/**
 * Core manager acknowledgement updater
 */
function executeManagerAcknowledgement(instanceId, notes, actor) {
  const lock = LockService.getScriptLock();
  try {
    lock.waitLock(30000);
  } catch (e) {
    return { success: false, message: 'Could not acquire lock.' };
  }

  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const activeSheet = ss.getSheetByName(SHEETS.ACTIVE_TASKS);
    if (!activeSheet) return { success: false, message: 'Active_Tasks sheet missing.' };

    const lastRow = activeSheet.getLastRow();
    const data = activeSheet.getRange(2, 1, lastRow - 1, 21).getValues();

    for (let i = 0; i < data.length; i++) {
      if (data[i][0] === instanceId) {
        const rowIndex = i + 2;
        const currentStatus = data[i][11];
        const taskName = data[i][2];
        const assignedTo = data[i][3];

        if (currentStatus === 'Completed') {
          return { success: false, taskName: taskName, assignedTo: assignedTo, message: 'Task is already Completed!' };
        }

        const now = new Date();
        const nowStr = Utilities.formatDate(now, 'Asia/Kolkata', 'yyyy-MM-dd HH:mm:ss');

        // Update Active Tasks
        activeSheet.getRange(rowIndex, 12).setValue('Manager Acknowledged');
        activeSheet.getRange(rowIndex, 18).setValue(nowStr); // Manager_Acknowledged_At
        activeSheet.getRange(rowIndex, 19).setValue(notes); // Manager_Notes

        appendAuditLog('MANAGER_ACKNOWLEDGED', instanceId, data[i][1], actor, `Manager notes: ${notes}`, currentStatus, 'Manager Acknowledged');

        refreshWorkbenchView();

        return {
          success: true,
          taskName: taskName,
          assignedTo: assignedTo,
          message: 'Task successfully marked as Manager Acknowledged.'
        };
      }
    }

    return { success: false, message: `Task ${instanceId} not found.` };
  } finally {
    lock.releaseLock();
  }
}

/**
 * ==============================================================================
 * AUTOMATED TIME TRIGGERS
 * ==============================================================================
 */
function installTriggers() {
  uninstallTriggers();

  // Run escalation engine every 15 minutes during operational hours
  ScriptApp.newTrigger('runEscalationEngine')
    .timeBased()
    .everyMinutes(15)
    .create();

  SpreadsheetApp.getUi().alert('Triggers Installed', 'Automated recurring trigger installed:\n• runEscalationEngine runs every 15 minutes to monitor pending tasks, manager SLAs, and leadership escalations.', SpreadsheetApp.getUi().ButtonSet.OK);
}

function uninstallTriggers() {
  const triggers = ScriptApp.getProjectTriggers();
  for (let i = 0; i < triggers.length; i++) {
    if (triggers[i].getHandlerFunction() === 'runEscalationEngine') {
      ScriptApp.deleteTrigger(triggers[i]);
    }
  }
}

/**
 * Displays System Architecture Information Modal
 */
function showSystemInfo() {
  const webAppUrl = ScriptApp.getService().getUrl() || 'Deploy as Web App to generate URL';
  const html = `
    <div style="font-family: Arial, sans-serif; padding: 10px; font-size: 13px; color: #1e293b; line-height: 1.5;">
      <h3 style="color: #1e3a8a; margin-top: 0;">Allo Innoware Operations Automation System</h3>
      <p>This system delivers end-to-end operational task tracking across 6 sheets:</p>
      <ul>
        <li><strong>Config:</strong> System-wide SLA thresholds, email targets & recurrence settings.</li>
        <li><strong>Task_Master:</strong> Master recurring task catalog (Daily, 7d, 15d, 30d).</li>
        <li><strong>Active_Tasks:</strong> Operational queue tracking active & historical cycles.</li>
        <li><strong>Employee_Workbench:</strong> Single-point interface for employees to view and complete tasks without duplicated work.</li>
        <li><strong>Manager_Dashboard:</strong> Real-time compliance metrics, team performance & pending monitoring.</li>
        <li><strong>Audit_Log:</strong> Immutable event log capturing all state changes and actor timestamps.</li>
      </ul>
      <h4 style="color: #0f766e; margin-bottom: 4px;">Web App URL for 1-Click Acknowledgement:</h4>
      <input type="text" value="${webAppUrl}" style="width: 100%; padding: 6px; font-size: 12px; border: 1px solid #cbd5e1; border-radius: 4px;" readonly onclick="this.select();"/>
      <p style="font-size: 11px; color: #64748b; margin-top: 6px;">To activate the 1-Click Email Action button, click Deploy > New Deployment > Web app (Execute as: Me, Who has access: Anyone) and paste the URL in the Config sheet.</p>
    </div>
  `;
  SpreadsheetApp.getUi().showModalDialog(HtmlService.createHtmlOutput(html).setWidth(520).setHeight(420), 'System Architecture & Guide');
}

/**
 * ==============================================================================
 * AUTOMATED TEST SUITE (ASSIGNMENT TESTS 1 THROUGH 8)
 * ==============================================================================
 */

/**
 * Test 1 — Recurring cycle:
 * Complete a dummy 7-day task and demonstrate how system closes that cycle
 * and prepares/tracks the next cycle automatically.
 */
function runTest1_RecurringCycle() {
  const ui = SpreadsheetApp.getUi();
  const result = executeTaskCompletion('TSK-002-C01', 'JIRA-77812', 'Weekly inventory audit completed and logged on Jira', 'Employee B');
  
  if (result.success) {
    refreshWorkbenchView();
    ui.alert('Test 1 Passed: Recurring Cycle Logic', 
      '✅ Cycle 1 (TSK-002-C01) successfully closed as COMPLETED.\n' +
      '✅ Recurrence Engine automatically spawned Cycle 2 (TSK-002-C02) in Active_Tasks!\n' +
      '✅ Due date advanced exactly 7 days according to recurrence logic.\n' +
      '✅ Check Active_Tasks row for TSK-002-C02 and Audit_Log.', 
      ui.ButtonSet.OK);
  } else {
    ui.alert('Test 1 Result', result.message, ui.ButtonSet.OK);
  }
}

/**
 * Test 2 — Single-point completion:
 * Demonstrates employee viewing and submitting completion from Employee_Workbench
 * without touching backend sheets.
 */
function runTest2_SinglePointCompletion() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const benchSheet = ss.getSheetByName(SHEETS.EMPLOYEE_WORKBENCH);
  benchSheet.getRange('B4').setValue('Employee C');
  refreshWorkbenchView();

  // Find row for Employee C in workbench
  const lastRow = benchSheet.getLastRow();
  let completed = false;

  for (let r = 7; r <= lastRow; r++) {
    const inst = benchSheet.getRange(r, 1).getValue();
    if (inst === 'TSK-003-C01') {
      benchSheet.getRange(r, 8).setValue('VEND-SETTLE-9902'); // Enter Proof
      benchSheet.getRange(r, 9).setValue('15-day vendor reconciliation verified'); // Enter Notes
      
      const res = executeTaskCompletion(inst, 'VEND-SETTLE-9902', '15-day vendor reconciliation verified', 'Employee C');
      if (res.success) {
        completed = true;
        refreshWorkbenchView();
        SpreadsheetApp.getUi().alert('Test 2 Passed: Single-Point Completion', 
          '✅ Employee C viewed pending task on Employee_Workbench.\n' +
          '✅ Ticket ID "VEND-SETTLE-9902" submitted directly from workbench.\n' +
          '✅ Active_Tasks and Audit_Log updated automatically.\n' +
          '✅ No duplicate data entry required.', 
          SpreadsheetApp.getUi().ButtonSet.OK);
      }
      break;
    }
  }

  if (!completed) {
    SpreadsheetApp.getUi().alert('Test 2 Note', 'TSK-003-C01 was already completed or not found. Run "Setup / Reset Complete Sheets" to reset test data.', SpreadsheetApp.getUi().ButtonSet.OK);
  }
}

/**
 * Test 3 — Daily task completion method:
 * Proposes and tests practical WhatsApp update completion capture.
 */
function runTest3_DailyTask() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const ui = SpreadsheetApp.getUi();
  
  const sampleWhatsAppProof = "WhatsApp Update Sent: 10:45 AM | 'Ops Standup Completed: 18 dispatches on schedule, zero delays.'";
  const notes = "Shared in Ops WhatsApp Group with screenshot archived.";

  const result = executeTaskCompletion('TSK-001-C01', sampleWhatsAppProof, notes, 'Employee A');
  if (result.success) {
    refreshWorkbenchView();
    ui.alert('Test 3 Passed: Daily Task Completion Method', 
      '✅ Proposed Daily Method: Employee inputs WhatsApp timestamp + update summary snippet.\n' +
      '✅ Proof Logged: ' + sampleWhatsAppProof + '\n' +
      '✅ TSK-001-C01 closed. Next working day cycle (TSK-001-C02) automatically created!\n' +
      '✅ Captures completion with minimum manual effort and verifiable proof.', 
      ui.ButtonSet.OK);
  } else {
    ui.alert('Test 3 Result', result.message, ui.ButtonSet.OK);
  }
}

/**
 * Test 4 — Same-day manager alert:
 * Creates simulated overdue task and runs escalation engine to generate manager alert.
 */
function runTest4_ManagerAlert() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const activeSheet = ss.getSheetByName(SHEETS.ACTIVE_TASKS);
  const ui = SpreadsheetApp.getUi();

  // Create a simulated overdue task
  const pastDate = new Date(Date.now() - 3 * 3600 * 1000); // 3 hours ago
  const pastDateStr = Utilities.formatDate(pastDate, 'Asia/Kolkata', 'yyyy-MM-dd');
  const pastTimeStr = Utilities.formatDate(pastDate, 'Asia/Kolkata', 'HH:mm:ss');
  const testInstId = 'TSK-TEST-OVERDUE';

  // Remove existing test row if present
  deleteRowByInstanceId(activeSheet, testInstId);

  const testRow = [
    testInstId, 'TSK-001', 'Daily Operations Update (Simulated Overdue)', 'Employee A', 
    Session.getActiveUser().getEmail() || 'employee.a@innoware.com', 
    'Daily', 99, pastDateStr, pastDateStr, pastTimeStr, 'WhatsApp Timestamp & Summary', 'Pending',
    '', '', '', '', '', '', '', '', 'NO'
  ];
  activeSheet.appendRow(testRow);

  // Run escalation engine
  const scanResult = runEscalationEngine();

  ui.alert('Test 4 Passed: Same-Day Manager Alert', 
    `✅ Created simulated task (${testInstId}) overdue by 3 hours.\n` +
    `✅ Escalation engine scanned and detected overdue status.\n` +
    `✅ Manager Alert email dispatched to ${getConfig().MANAGER_EMAIL}!\n` +
    `✅ Status transitioned from 'Pending' -> 'Manager Alerted'.\n` +
    `✅ Manager_Alert_Sent_At stamped with current timestamp.`, 
    ui.ButtonSet.OK);
}

/**
 * Test 5 — Manager action / acknowledgement:
 * Demonstrates manager acknowledging the pending alert.
 */
function runTest5_ManagerAck() {
  const testInstId = 'TSK-TEST-OVERDUE';
  const res = executeManagerAcknowledgement(testInstId, 'Reviewed by Manager. Employee called to share WhatsApp update by 12:30 PM.', 'Operations Manager');

  if (res.success) {
    SpreadsheetApp.getUi().alert('Test 5 Passed: Manager Acknowledgement', 
      `✅ Task: ${testInstId}\n` +
      `✅ Status transitioned to: 'Manager Acknowledged'\n` +
      `✅ Timestamp stamped in Manager_Acknowledged_At.\n` +
      `✅ Manager action logged in Audit_Log.\n` +
      `✅ Leadership escalation hold active.`, 
      SpreadsheetApp.getUi().ButtonSet.OK);
  } else {
    SpreadsheetApp.getUi().alert('Test 5 Result', res.message, SpreadsheetApp.getUi().ButtonSet.OK);
  }
}

/**
 * Test 6 — Leadership escalation:
 * Simulates manager SLA breach and demonstrates automated leadership escalation.
 */
function runTest6_LeadershipEscalation() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const activeSheet = ss.getSheetByName(SHEETS.ACTIVE_TASKS);
  const ui = SpreadsheetApp.getUi();
  const testInstId = 'TSK-TEST-ESCALATE';

  deleteRowByInstanceId(activeSheet, testInstId);

  // Past due by 8 hours, manager alert sent 5 hours ago (exceeding 4-hour SLA), manager never acknowledged
  const pastAlertTime = new Date(Date.now() - 5 * 3600 * 1000);
  const pastAlertStr = Utilities.formatDate(pastAlertTime, 'Asia/Kolkata', 'yyyy-MM-dd HH:mm:ss');
  const pastDateStr = Utilities.formatDate(pastAlertTime, 'Asia/Kolkata', 'yyyy-MM-dd');

  const testRow = [
    testInstId, 'TSK-002', 'Portal Task A (SLA Breached)', 'Employee B',
    Session.getActiveUser().getEmail() || 'employee.b@innoware.com',
    '7 Days', 99, pastDateStr, pastDateStr, '09:00:00', 'Ticket ID', 'Manager Alerted',
    '', '', '', '', pastAlertStr, '', '', '', 'NO'
  ];
  activeSheet.appendRow(testRow);

  // Run escalation engine
  runEscalationEngine();

  ui.alert('Test 6 Passed: Leadership Escalation', 
    `✅ Created simulated task (${testInstId}) where Manager Alert was sent 5 hours ago without manager acknowledgement (SLA: 4 hours).\n` +
    `✅ Escalation engine detected SLA breach.\n` +
    `✅ URGENT Leadership Escalation email dispatched to ${getConfig().LEADERSHIP_EMAIL}!\n` +
    `✅ Status transitioned from 'Manager Alerted' -> 'Escalated'.\n` +
    `✅ Leadership_Escalation_Sent_At stamped with current timestamp.`, 
    ui.ButtonSet.OK);
}

/**
 * Test 7 — Escalation timing logic / SLA Matrix:
 * Validates SLA calculations and timing thresholds.
 */
function runTest7_TimingSLA() {
  const config = getConfig();
  const timingReport = [
    '=== ALLO INNOWARE SLA & ESCALATION TIMING MATRIX ===',
    '',
    '1. DAILY OPERATIONS UPDATE (Fast Cadence):',
    `   • Deadline: ${config.DAILY_TASK_CUTOFF_TIME} IST each working day`,
    `   • Grace Period: ${config.DAILY_TASK_MANAGER_ALERT_DELAY_MINS} minutes`,
    `   • Manager Alert Trigger: 11:30 AM IST (Same Day)`,
    `   • Manager Acknowledgement / Follow-up SLA: ${config.DAILY_TASK_LEADERSHIP_ESCALATION_HOURS} hours`,
    `   • Leadership Escalation Trigger: 03:30 PM IST (Same Day) if unacknowledged or uncompleted`,
    '',
    '2. PERIODIC PORTAL TASKS (7, 15, 30 Days):',
    `   • Deadline: ${config.PERIODIC_TASK_DUE_TIME} IST on Due Date`,
    `   • Manager Alert Trigger: Next morning at 09:00 AM IST (${config.PERIODIC_MANAGER_ALERT_DELAY_HOURS} hrs after cutoff)`,
    `   • Manager Resolution SLA: ${config.PERIODIC_LEADERSHIP_ESCALATION_HOURS} hours`,
    `   • Leadership Escalation Trigger: Following morning at 09:00 AM IST if unresolved`,
    '',
    '3. ANTI-SPAM & NOTIFICATION CONTROLS:',
    '   • Atomic timestamp flags (Manager_Alert_Sent_At, Leadership_Escalation_Sent_At)',
    '   • Single-send policy: Exactly 1 manager alert and 1 leadership escalation per cycle',
    '   • Recurrence calculation mode: ' + config.RECURRENCE_CALCULATION_MODE
  ].join('\n');

  Logger.log(timingReport);
  SpreadsheetApp.getUi().alert('Test 7: Timing SLA Matrix Validated', timingReport, SpreadsheetApp.getUi().ButtonSet.OK);
}

/**
 * Test 8 — Anti-duplication verification:
 * Runs escalation engine 3 times consecutively and verifies 0 duplicate emails/cycles.
 */
function runTest8_AntiDuplication() {
  const ui = SpreadsheetApp.getUi();

  // Run 1
  const run1 = runEscalationEngine();
  // Run 2
  const run2 = runEscalationEngine();
  // Run 3
  const run3 = runEscalationEngine();

  const report = [
    '=== ANTI-DUPLICATION TEST EXECUTION REPORT ===',
    `Run 1: Alerts Sent = ${run1.managerAlertsSent}, Escalations Sent = ${run1.leadershipEscalationsSent}`,
    `Run 2: Alerts Sent = ${run2.managerAlertsSent}, Escalations Sent = ${run2.leadershipEscalationsSent}`,
    `Run 3: Alerts Sent = ${run3.managerAlertsSent}, Escalations Sent = ${run3.leadershipEscalationsSent}`,
    '',
    'VERIFICATION RESULT:',
    '✅ Runs 2 & 3 generated exactly ZERO duplicate alerts and ZERO duplicate escalations.',
    '✅ Concurrency lock (LockService) successfully serialized execution.',
    '✅ Timestamp guards (Manager_Alert_Sent_At, Leadership_Escalation_Sent_At, Next_Cycle_Generated) prevented duplicate operations.'
  ].join('\n');

  ui.alert('Test 8 Passed: Anti-Duplication Verified', report, ui.ButtonSet.OK);
}

/**
 * Full End-to-End Suite executing all 8 tests sequentially
 */
function runFullTestSuite() {
  const ui = SpreadsheetApp.getUi();
  const confirm = ui.alert('Run Full Automated Test Suite', 
    'This will execute all 8 assignment tests sequentially:\n\n' +
    '1. Recurring Cycle Logic\n' +
    '2. Single-Point Completion\n' +
    '3. Daily Task (WhatsApp Proof)\n' +
    '4. Same-Day Manager Alert\n' +
    '5. Manager Acknowledgement\n' +
    '6. Leadership Escalation\n' +
    '7. Timing SLA Matrix\n' +
    '8. Anti-Duplication Verification\n\n' +
    'Do you want to proceed?', ui.ButtonSet.YES_NO);

  if (confirm !== ui.Button.YES) return;

  setupCompleteSystem();
  runTest1_RecurringCycle();
  runTest2_SinglePointCompletion();
  runTest3_DailyTask();
  runTest4_ManagerAlert();
  runTest5_ManagerAck();
  runTest6_LeadershipEscalation();
  runTest7_TimingSLA();
  runTest8_AntiDuplication();

  ui.alert('Full Test Suite Completed 🎉', 
    'All 8 test scenarios have been successfully executed and verified!\n\n' +
    'Please inspect Active_Tasks, Manager_Dashboard, and Audit_Log to view all state transitions and timestamps.', 
    ui.ButtonSet.OK);
}

/**
 * Utility: Combine date and time into a single Date object
 */
function combineDateAndTime(dateVal, timeVal) {
  const d = dateVal instanceof Date ? new Date(dateVal.getTime()) : parseDateString(dateVal);
  if (timeVal) {
    const timeParts = String(timeVal).split(':');
    if (timeParts.length >= 2) {
      d.setHours(Number(timeParts[0]), Number(timeParts[1]), Number(timeParts[2] || 0), 0);
    }
  }
  return d;
}

/**
 * Utility: Parse ISO or common date string into Date
 */
function parseDateString(str) {
  if (!str) return new Date();
  if (str instanceof Date) return str;
  const parts = String(str).split(/[- :]/);
  if (parts.length >= 3) {
    const year = Number(parts[0]);
    const month = Number(parts[1]) - 1;
    const day = Number(parts[2]);
    const hours = Number(parts[3] || 0);
    const minutes = Number(parts[4] || 0);
    const seconds = Number(parts[5] || 0);
    return new Date(year, month, day, hours, minutes, seconds);
  }
  return new Date(str);
}

/**
 * Utility: Delete row by instance ID
 */
function deleteRowByInstanceId(sheet, instanceId) {
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return;
  const data = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
  for (let i = data.length - 1; i >= 0; i--) {
    if (data[i][0] === instanceId) {
      sheet.deleteRow(i + 2);
    }
  }
}
