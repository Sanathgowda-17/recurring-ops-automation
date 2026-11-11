#!/usr/bin/env python3
"""
Generates Allo_Innoware_Google_Sheets_Architecture_Guide.pdf
A comprehensive, beautifully styled PDF guide explaining all 6 Google Sheets
in the Allo Innoware Operations Automation System.
Built using standard library Python (pure Python PDF generator).
"""

import os
import sys
import zlib
import textwrap

class PDFBuilder:
    def __init__(self, filename="Allo_Innoware_Google_Sheets_Architecture_Guide.pdf"):
        self.filename = filename
        self.page_width = 612.0   # Letter width in points (8.5 in)
        self.page_height = 792.0  # Letter height in points (11 in)
        self.margin_left = 40.0
        self.margin_right = 40.0
        self.margin_top = 40.0
        self.margin_bottom = 42.0
        self.content_width = self.page_width - self.margin_left - self.margin_right
        
        self.pages = []
        self.current_page_stream = bytearray()
        self.current_y = self.page_height - self.margin_top
        self.page_num = 0
        
        # Colors
        self.c_primary = (0.106, 0.212, 0.365)     # Deep Navy #1B365D
        self.c_secondary = (0.169, 0.424, 0.690)   # Slate Blue #2B6CB0
        self.c_accent = (0.753, 0.337, 0.129)      # Warm Amber #C05621
        self.c_green = (0.184, 0.522, 0.353)       # Forest Green #2F855A
        self.c_purple = (0.424, 0.235, 0.612)      # Deep Purple #6C3C9C
        self.c_dark = (0.176, 0.216, 0.282)        # Charcoal #2D3748
        self.c_gray = (0.443, 0.498, 0.549)        # Medium Gray #718096
        self.c_light_bg = (0.969, 0.980, 0.988)    # Light Slate Gray #F7FAFC
        self.c_card_bg = (0.941, 0.961, 0.984)     # Soft Ice Blue #F0F4FA
        self.c_border = (0.796, 0.835, 0.878)      # Light Border #CBD5E0
        self.c_white = (1.0, 1.0, 1.0)
        
        self.new_page()

    def escape_text(self, text):
        replacements = {
            '—': '--',
            '–': '-',
            '’': "'",
            '‘': "'",
            '“': '"',
            '”': '"',
            '•': '*',
            '★': '*',
            '⚡': '[!]',
            '📌': '[*]',
            '🎙️': '[MIC]',
            '🎙': '[MIC]',
            '💡': '[TIP]',
            '→': '->',
            '←': '<-',
            '…': '...',
            '×': 'x',
            '™': 'TM',
            '©': '(c)',
            '®': '(R)',
            '✔': '[OK]',
            '✅': '[OK]',
            '⚠️': '[WARN]',
            '🚨': '[ALERT]',
            '1️⃣': '1.',
            '2️⃣': '2.',
            '3️⃣': '3.',
            '4️⃣': '4.',
            '5️⃣': '5.',
            '6️⃣': '6.',
            '🔄': '<->'
        }
        for k, v in replacements.items():
            text = text.replace(k, v)
        clean = []
        for ch in text:
            if ord(ch) < 256:
                clean.append(ch)
            else:
                clean.append(' ')
        text = ''.join(clean)
        return text.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')

    def new_page(self):
        if self.page_num > 0:
            self.pages.append(bytes(self.current_page_stream))
        self.page_num += 1
        self.current_page_stream = bytearray()
        self.current_y = self.page_height - self.margin_top
        
        if self.page_num > 1:
            self.draw_running_header()

    def draw_running_header(self):
        s = self.current_page_stream
        y = self.page_height - 28
        s.extend(f"{self.c_border[0]:.3f} {self.c_border[1]:.3f} {self.c_border[2]:.3f} RG\n".encode('latin1'))
        s.extend(b"0.75 w\n")
        s.extend(f"{self.margin_left} {y} m {self.page_width - self.margin_right} {y} l S\n".encode('latin1'))
        
        txt = "ALLO INNOWARE -- 6-SHEET ARCHITECTURE & DATA FLOW BLUEPRINT"
        esc = self.escape_text(txt)
        s.extend(b"BT\n")
        s.extend(b"/F2 7.5 Tf\n")
        s.extend(f"{self.c_gray[0]:.3f} {self.c_gray[1]:.3f} {self.c_gray[2]:.3f} rg\n".encode('latin1'))
        s.extend(f"{self.margin_left} {y + 4} Td ({esc}) Tj\n".encode('latin1'))
        s.extend(b"ET\n")
        self.current_y = self.page_height - 46

    def ensure_space(self, height_needed):
        if self.current_y - height_needed < self.margin_bottom:
            self.new_page()

    def draw_rect(self, x, y, w, h, fill_color=None, stroke_color=None, stroke_width=0.75):
        s = self.current_page_stream
        if fill_color:
            s.extend(f"{fill_color[0]:.3f} {fill_color[1]:.3f} {fill_color[2]:.3f} rg\n".encode('latin1'))
        if stroke_color:
            s.extend(f"{stroke_color[0]:.3f} {stroke_color[1]:.3f} {stroke_color[2]:.3f} RG\n".encode('latin1'))
            s.extend(f"{stroke_width:.2f} w\n".encode('latin1'))
        
        s.extend(f"{x:.2f} {y:.2f} {w:.2f} {h:.2f} re\n".encode('latin1'))
        if fill_color and stroke_color:
            s.extend(b"B\n")
        elif fill_color:
            s.extend(b"f\n")
        elif stroke_color:
            s.extend(b"S\n")

    def draw_text_line(self, x, y, text, font="/F1", size=9.0, color=(0, 0, 0)):
        s = self.current_page_stream
        esc = self.escape_text(text)
        s.extend(b"BT\n")
        s.extend(f"{font} {size:.2f} Tf\n".encode('latin1'))
        s.extend(f"{color[0]:.3f} {color[1]:.3f} {color[2]:.3f} rg\n".encode('latin1'))
        s.extend(f"{x:.2f} {y:.2f} Td ({esc}) Tj\n".encode('latin1'))
        s.extend(b"ET\n")

    def draw_section_header(self, title, subtitle=None):
        needed = 34 if subtitle else 26
        self.ensure_space(needed)
        y = self.current_y
        h = 19.0
        self.draw_rect(self.margin_left, y - h, self.content_width, h, fill_color=self.c_primary)
        self.draw_text_line(self.margin_left + 8, y - 13.5, title.upper(), font="/F2", size=9.0, color=self.c_white)
        self.current_y = y - h - 5
        
        if subtitle:
            self.draw_text_line(self.margin_left, self.current_y - 2, subtitle, font="/F3", size=8.0, color=self.c_secondary)
            self.current_y -= 11

    def draw_sheet_card(self, num_str, name, role, audience, summary, columns, why_it_matters, accent_color=None):
        if accent_color is None:
            accent_color = self.c_secondary
            
        approx_chars = int((self.content_width - 24) / (8.2 * 0.52))
        sum_lines = textwrap.wrap(f"Summary: {summary}", width=approx_chars)
        col_lines = textwrap.wrap(f"Key Columns / Data: {columns}", width=approx_chars)
        why_lines = textwrap.wrap(f"Operational Value: {why_it_matters}", width=approx_chars)
        
        card_h = 24 + (len(sum_lines) + len(col_lines) + len(why_lines)) * 11.5 + 16
        self.ensure_space(card_h + 8)
        
        y = self.current_y
        
        # Background box
        self.draw_rect(self.margin_left, y - card_h, self.content_width, card_h,
                       fill_color=self.c_card_bg, stroke_color=self.c_border, stroke_width=0.6)
        # Left colored accent bar
        self.draw_rect(self.margin_left, y - card_h, 4.0, card_h, fill_color=accent_color)
        
        # Top banner inside card
        header_title = f"{num_str}  Tab Name: '{name}'   |   Role: {role}"
        self.draw_text_line(self.margin_left + 10, y - 14, header_title, font="/F2", size=9.2, color=self.c_primary)
        
        aud_text = f"Audience / Primary Actor: {audience}"
        self.draw_text_line(self.margin_left + 10, y - 25, aud_text, font="/F2", size=8.0, color=accent_color)
        
        curr_y = y - 38
        # Summary
        for sl in sum_lines:
            self.draw_text_line(self.margin_left + 12, curr_y, sl, font="/F1", size=8.2, color=self.c_dark)
            curr_y -= 11.5
            
        # Columns
        for cl in col_lines:
            self.draw_text_line(self.margin_left + 12, curr_y, cl, font="/F2" if "Key Columns" in cl else "/F1", 
                                size=8.0, color=self.c_dark)
            curr_y -= 11.5
            
        # Why it matters
        for wl in why_lines:
            self.draw_text_line(self.margin_left + 12, curr_y, wl, font="/F3", size=8.0, color=self.c_secondary)
            curr_y -= 11.5
            
        self.current_y = y - card_h - 8

    def draw_table(self, headers, rows, col_widths, font_size=7.5):
        row_height = 15.0
        total_height = (len(rows) + 1) * row_height + 4
        self.ensure_space(total_height)
        y = self.current_y
        
        # Header
        x = self.margin_left
        for i, h in enumerate(headers):
            w = col_widths[i]
            self.draw_rect(x, y - row_height, w, row_height, fill_color=self.c_primary, stroke_color=self.c_border, stroke_width=0.5)
            self.draw_text_line(x + 5, y - row_height + 4.0, h, font="/F2", size=font_size, color=self.c_white)
            x += w
        y -= row_height
        
        # Rows
        for r_idx, row in enumerate(rows):
            bg = self.c_white if r_idx % 2 == 0 else self.c_light_bg
            x = self.margin_left
            for i, val in enumerate(row):
                w = col_widths[i]
                self.draw_rect(x, y - row_height, w, row_height, fill_color=bg, stroke_color=self.c_border, stroke_width=0.5)
                fnt = "/F2" if i == 0 else "/F1"
                clr = self.c_primary if i == 0 else self.c_dark
                self.draw_text_line(x + 5, y - row_height + 4.0, str(val), font=fnt, size=font_size, color=clr)
                x += w
            y -= row_height
        self.current_y = y - 8

    def finish_pages_and_footers(self):
        if self.page_num > 0 and (len(self.pages) < self.page_num):
            self.pages.append(bytes(self.current_page_stream))
            
        total_pages = len(self.pages)
        completed_pages = []
        for idx, page_bytes in enumerate(self.pages):
            p_stream = bytearray(page_bytes)
            p_num = idx + 1
            
            y = 30.0
            p_stream.extend(f"{self.c_border[0]:.3f} {self.c_border[1]:.3f} {self.c_border[2]:.3f} RG\n".encode('latin1'))
            p_stream.extend(b"0.5 w\n")
            p_stream.extend(f"{self.margin_left} {y} m {self.page_width - self.margin_right} {y} l S\n".encode('latin1'))
            
            left_txt = "Candidate: Sanath S Gowda | Allo Innoware Operations Automation | 6 Google Sheets Blueprint"
            esc_left = self.escape_text(left_txt)
            p_stream.extend(b"BT\n")
            p_stream.extend(b"/F1 7.0 Tf\n")
            p_stream.extend(f"{self.c_gray[0]:.3f} {self.c_gray[1]:.3f} {self.c_gray[2]:.3f} rg\n".encode('latin1'))
            p_stream.extend(f"{self.margin_left} {y - 10} Td ({esc_left}) Tj\n".encode('latin1'))
            p_stream.extend(b"ET\n")
            
            right_txt = f"Page {p_num} of {total_pages}"
            esc_right = self.escape_text(right_txt)
            p_stream.extend(b"BT\n")
            p_stream.extend(b"/F2 7.0 Tf\n")
            p_stream.extend(f"{self.c_gray[0]:.3f} {self.c_gray[1]:.3f} {self.c_gray[2]:.3f} rg\n".encode('latin1'))
            p_stream.extend(f"{self.page_width - self.margin_right - 55} {y - 10} Td ({esc_right}) Tj\n".encode('latin1'))
            p_stream.extend(b"ET\n")
            
            completed_pages.append(bytes(p_stream))
        return completed_pages

    def build_pdf(self):
        pages_content = self.finish_pages_and_footers()
        total_pages = len(pages_content)
        pdf = bytearray()
        pdf.extend(b"%PDF-1.4\n")
        
        offsets = []
        def add_obj(data):
            offsets.append(len(pdf))
            pdf.extend(f"{len(offsets)} 0 obj\n".encode('latin1'))
            pdf.extend(data)
            pdf.extend(b"\nendobj\n")
            return len(offsets)

        pages_kids_refs = [f"{3 + i} 0 R" for i in range(total_pages)]
        kids_str = " ".join(pages_kids_refs)
        add_obj(b"<< /Type /Catalog /Pages 2 0 R >>")
        add_obj(f"<< /Type /Pages /Kids [{kids_str}] /Count {total_pages} >>".encode('latin1'))
        
        font_ref_idx = 3 + 2 * total_pages
        for i in range(total_pages):
            stream_ref_idx = 3 + total_pages + i
            page_dict = (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {self.page_width} {self.page_height}] "
                f"/Resources << /Font << "
                f"/F1 {font_ref_idx} 0 R /F2 {font_ref_idx+1} 0 R /F3 {font_ref_idx+2} 0 R "
                f">> >> /Contents {stream_ref_idx} 0 R >>"
            ).encode('latin1')
            add_obj(page_dict)
            
        for i in range(total_pages):
            c_raw = pages_content[i]
            c_comp = zlib.compress(c_raw)
            stream_dict = f"<< /Length {len(c_comp)} /Filter /FlateDecode >>\nstream\n".encode('latin1') + c_comp + b"\nendstream"
            add_obj(stream_dict)
            
        add_obj(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
        add_obj(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
        add_obj(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique /Encoding /WinAnsiEncoding >>")
        
        xref_start = len(pdf)
        pdf.extend(b"xref\n")
        pdf.extend(f"0 {len(offsets) + 1}\n".encode('latin1'))
        pdf.extend(b"0000000000 65535 f \n")
        for off in offsets:
            pdf.extend(f"{off:010d} 00000 n \n".encode('latin1'))
            
        pdf.extend(b"trailer\n")
        pdf.extend(f"<< /Size {len(offsets) + 1} /Root 1 0 R >>\n".encode('latin1'))
        pdf.extend(f"startxref\n{xref_start}\n%%EOF".encode('latin1'))
        
        with open(self.filename, 'wb') as f:
            f.write(pdf)
        print(f"Generated PDF: {self.filename} ({len(pdf)} bytes, {total_pages} pages)")
        return self.filename


def generate_sheets_guide():
    builder = PDFBuilder("Allo_Innoware_Google_Sheets_Architecture_Guide.pdf")
    
    # PAGE 1: TITLE BANNER & CORE DESIGN PHILOSOPHY & SHEETS 1-3
    builder.draw_rect(builder.margin_left, builder.current_y - 46, builder.content_width, 46, fill_color=builder.c_primary)
    builder.draw_text_line(builder.margin_left + 12, builder.current_y - 19, 
                           "ALLO INNOWARE -- GOOGLE SHEETS SYSTEM BLUEPRINT", 
                           font="/F2", size=14.0, color=builder.c_white)
    builder.draw_text_line(builder.margin_left + 12, builder.current_y - 34, 
                           "Detailed Explanation of the 6 Operational Sheets, Data Flow & Separation of Concerns", 
                           font="/F1", size=8.8, color=builder.c_card_bg)
    builder.current_y -= 54
    
    # Executive Overview Box
    overview_text = (
        "CORE DESIGN PRINCIPLE: SEPARATION OF CONCERNS\n"
        "In growing operations teams, spreadsheets fail because companies cram data storage, employee data entry, "
        "and management reporting into a single sheet. This causes accidental formula deletion, multi-user concurrency locks, "
        "and dirty data. Our prototype strictly organizes operations into 6 purpose-built sheets: Configuration, Catalog, "
        "Live Queue, Single-Point UI, Executive KPI Dashboard, and Immutable Audit Log."
    )
    builder.draw_sheet_card("[*]", "ARCHITECTURAL PHILOSOPHY", "System Foundation", "Engineering & Management",
                            overview_text, "Config, Task_Master, Active_Tasks, Employee_Workbench, Manager_Dashboard, Audit_Log",
                            "Eliminates spreadsheet chaos by ensuring employees never touch the master database.",
                            accent_color=builder.c_primary)
    
    builder.draw_section_header("1. TAB-BY-TAB DETAILED BREAKDOWN (SHEETS 1 TO 3)", 
                                "The engine, configuration, and catalog layers")
    
    # Sheet 1: Config
    builder.draw_sheet_card(
        "1.", "Config", "System Control Center & Dynamic Parameters",
        "Operations Admin / Manager (Set once during onboarding)",
        "Acts as the master settings page for the entire automation. Centralizes email recipients, daily/periodic cutoff times, "
        "grace periods, SLA escalation hours, and the deployed Web App URL.",
        "Key (Col A): MANAGER_EMAIL, LEADERSHIP_EMAIL, DAILY_TASK_CUTOFF_TIME (11:00), DAILY_TASK_MANAGER_ALERT_DELAY_MINS (30), "
        "DAILY_TASK_LEADERSHIP_ESCALATION_HOURS (4), WEB_APP_URL, TIMEZONE (Asia/Kolkata). Value (Col B), Description (Col C).",
        "Zero-code maintainability: If management emails or SLA hours change, update cell B4 without modifying script code.",
        accent_color=builder.c_purple
    )
    
    # Sheet 2: Task_Master
    builder.draw_sheet_card(
        "2.", "Task_Master", "Master Recurring Task Catalog & Rules Library",
        "Operations Manager / Admin (Updated when new recurring routines are added)",
        "The permanent blueprint catalog defining all recurring processes across Allo Innoware. Stores frequency rules, assigned owners, "
        "working channels, cutoff times, and proof type criteria.",
        "Task_ID (TSK-001..004), Task_Name (Daily Ops Update, Portal Tasks A/B/C), Assigned_To (Employee A..D), Employee_Email, "
        "Frequency (Daily, 7 Days, 15 Days, 30 Days), Frequency_Days, Expected_Cutoff_Time, Proof_Type, Target_Portal_Channel, Active.",
        "Whenever a task is completed, the engine consults this catalog to calculate the next cycle date and frequency offset.",
        accent_color=builder.c_secondary
    )
    
    # Sheet 3: Active_Tasks
    builder.draw_sheet_card(
        "3.", "Active_Tasks", "The Live Operational Queue & Timestamp Ledger",
        "The Automation Engine (Apps Script) -- Employees NEVER edit directly",
        "The running heartbeat of the operations system. Tracks every individual cycle instance (e.g. TSK-001-C01, TSK-001-C02) with "
        "exact due dates, real-time statuses, and atomic timestamp tracking for audits and anti-duplication.",
        "Instance_ID, Task_ID, Task_Name, Assigned_To, Frequency, Cycle_Number, Due_Date, Due_Time, Proof_Type, Status (Pending, "
        "Manager Alerted, Manager Acknowledged, Escalated, Completed), Proof_Submitted, Completed_At, Manager_Alert_Sent_At, "
        "Manager_Acknowledged_At, Leadership_Escalation_Sent_At, Next_Cycle_Generated.",
        "Single source of truth. Contains all state flags preventing duplicate alert emails and duplicate cycle creations.",
        accent_color=builder.c_accent
    )
    
    # PAGE 2: SHEETS 4-6 & DATA FLOW DIAGRAM
    builder.new_page()
    builder.draw_section_header("2. TAB-BY-TAB DETAILED BREAKDOWN (SHEETS 4 TO 6)",
                                "The user interface, reporting, and compliance layers")
    
    # Sheet 4: Employee_Workbench
    builder.draw_sheet_card(
        "4.", "Employee_Workbench", "Single-Point Action UI for Team Members",
        "Operations Employees (Employee A, B, C, D) -- Daily operating home",
        "A clean, filtered user interface designed specifically for low friction. The employee chooses their name from a dropdown "
        "in cell B4, and the table dynamically displays ONLY their pending tasks. They enter proof into Column H and click Submit.",
        "Dropdown Filter (B4), Real-Time Pending Count (B5: =COUNTIF), Filtered Table: Instance_ID (Col A), Task_Name (Col B), "
        "Frequency (Col C), Due_Date (Col D), Status (Col F), Proof_Type_Required (Col G), Enter Proof / Ticket ID (Col H), Notes (Col I).",
        "Frictionless execution (<15 seconds). Employees never see raw databases or other departments' tasks.",
        accent_color=builder.c_green
    )
    
    # Sheet 5: Manager_Dashboard
    builder.draw_sheet_card(
        "5.", "Manager_Dashboard", "Executive KPI Summary & Compliance Monitor",
        "Operations Managers & Executive Leadership (Real-time monitoring)",
        "High-level operational cockpit displaying live KPI counter cards and employee-by-employee compliance metrics. Automatically "
        "computes metrics using dynamic COUNTIFS formulas linked to Active_Tasks.",
        "Top KPI Cards: Total Active Cycles (=COUNTA), Pending Tasks (=COUNTIF 'Pending'), Manager Alerted (=COUNTIF 'Manager Alerted'), "
        "Manager Acknowledged, Escalated to Leadership, Completed Cycles. Employee Compliance Matrix: Total Assigned, Pending, Alerted, "
        "Escalated, Completed, and Compliance_Rate % (=Completed / Total).",
        "Provides 5-second situational awareness: managers immediately spot bottlenecks without asking for manual status reports.",
        accent_color=builder.c_primary
    )
    
    # Sheet 6: Audit_Log
    builder.draw_sheet_card(
        "6.", "Audit_Log", "Immutable Transaction Ledger (The Black Box)",
        "System Auditor, Manager, Leadership (Strictly append-only)",
        "Permanent, un-editable event history recording every single operational state change across the company. Every completion, "
        "cycle advance, alert dispatch, manager acknowledgement, and escalation is timestamped here.",
        "Log_ID (LOG-001..), Timestamp (YYYY-MM-DD HH:MM:SS), Event_Type (SYSTEM_INIT, TASK_COMPLETED, CYCLE_CREATED, "
        "MANAGER_ALERT_SENT, MANAGER_ACKNOWLEDGED, LEADERSHIP_ESCALATED), Instance_ID, Task_ID, Actor, Details, Status_Before, Status_After.",
        "Complete enterprise auditability: resolves vendor disputes, proves SLA adherence, and leaves zero room for finger-pointing.",
        accent_color=builder.c_gray
    )
    
    # Section 3: Data Flow Architecture Diagram
    builder.draw_section_header("3. SYSTEM INTERACTION & DATA FLOW ARCHITECTURE",
                                "How data moves across the 6 sheets during the task lifecycle")
    
    flow_headers = ["Lifecycle Step", "Trigger / Action", "Source Sheet", "Target Sheet", "System State Transition"]
    flow_rows = [
        ["1. Task Initiation", "System setup / cycle advance", "Task_Master", "Active_Tasks", "Spawns new Instance (e.g. TSK-002-C02) in 'Pending'."],
        ["2. Single-Point View", "Employee selects name (B4)", "Active_Tasks", "Employee_Workbench", "Filters and displays only assigned pending tasks."],
        ["3. Proof Submission", "Enters Ticket ID & clicks Submit", "Employee_Workbench", "Active_Tasks & Audit_Log", "Transitions status from 'Pending' -> 'Completed'."],
        ["4. Recurrence Spawn", "Triggered by completion", "Task_Master", "Active_Tasks", "Calculates Due Date + Frequency, sets Next_Cycle = YES."],
        ["5. Overdue Alert", "Cron engine scans past cutoff", "Config", "Active_Tasks & Email", "Sends HTML alert to Manager; marks 'Manager Alerted'."],
        ["6. 1-Click Acknowledge", "Manager clicks button in email", "Web App Webhook", "Active_Tasks & Dashboard", "Stamps 'Manager Acknowledged'; pauses escalation timer."],
        ["7. SLA Escalation", "4 hours elapse unacknowledged", "Config & Active_Tasks", "Leadership Email", "Escalates to Founders; marks status 'Escalated'."],
        ["8. Live KPI Update", "Formula recalculation", "Active_Tasks", "Manager_Dashboard", "Real-time KPI cards & Compliance % update instantly."]
    ]
    col_w = [85.0, 115.0, 95.0, 105.0, 132.0]
    builder.draw_table(flow_headers, flow_rows, col_w, font_size=6.8)
    
    # PAGE 3: TECHNICAL SAFEGUARDS & COMPARISON MATRIX
    builder.new_page()
    builder.draw_section_header("4. WHY THIS ARCHITECTURE PREVENTS SPREADSHEET COLLAPSE",
                                "Comparison of traditional manual sheets vs. Allo Innoware automated prototype")
    
    comp_headers = ["Operational Dimension", "Traditional Manual Sheets (Failure Mode)", "Allo Innoware 6-Sheet Architecture"]
    comp_rows = [
        ["Data Entry", "Everyone edits the same 20-col master sheet; accidental overwrites.", "Employee Workbench: isolated front-end; zero master sheet editing."],
        ["Recurrence Tracking", "Employees manually calculate next due dates; cycle drift occurs.", "Automated Engine: closes cycle, adds frequency, skips weekends."],
        ["Daily Task Proof", "Unchecked boxes or verbal claims with zero proof verification.", "WhatsApp Protocol: Timestamp + Summary snippet stored in audit trail."],
        ["Overdue Notification", "Silent failures until an order is late or vendor complains.", "Same-day Manager Alert fired automatically at cutoff + grace period."],
        ["Manager Response", "Requires logging into sheet, finding row, and changing cell.", "1-Click Email Action: acknowledge directly from mobile inbox in 2 sec."],
        ["Leadership Visibility", "Founders micromanage daily tasks or are blindsided by crises.", "2-Tier SLA Shield: leadership only notified on manager SLA breach."],
        ["Concurrency / Races", "Double submits create duplicate rows and repeated alert emails.", "LockService concurrency lock + atomic timestamp guards (0 duplicates)."],
        ["Historical Audit", "No change tracking; impossible to know who modified what.", "Immutable Audit_Log: records every actor, before/after status & time."]
    ]
    col_w_comp = [95.0, 215.0, 222.0]
    builder.draw_table(comp_headers, comp_rows, col_w_comp, font_size=7.0)
    
    # Section 5: Formulas & Backend Tech Deep-Dive
    builder.draw_section_header("5. KEY FORMULAS & SCRIPTLOCK LOGIC REFERENCE",
                                "Technical implementation details behind the formulas and code")
    
    tech_box = (
        "1. DYNAMIC DASHBOARD AGGREGATIONS:\n"
        "   - Pending Count: =COUNTIF(Active_Tasks!L2:L, \"Pending\")\n"
        "   - Escalation Count: =COUNTIF(Active_Tasks!L2:L, \"Escalated\")\n"
        "   - Employee Compliance Rate: =IF(Total>0, TEXT(Completed/Total, \"0.0%\"), \"100%\")\n\n"
        "2. WORKBENCH CONDITIONAL FILTERING:\n"
        "   - Dynamic pending task counter: =COUNTIF(F9:F, \"<>Completed\") - COUNTBLANK(F9:F)\n"
        "   - Google Sheets FILTER/QUERY formula maps Active_Tasks where Assigned_To = Employee_Workbench!B4 and Status <> 'Completed'.\n\n"
        "3. GOOGLE APPS SCRIPT CONCURRENCY & IDEMPOTENCY:\n"
        "   - LockService.getScriptLock().waitLock(30000): Queues concurrent requests up to 30 seconds to prevent race conditions.\n"
        "   - Atomic Flags: Manager_Alert_Sent_At, Leadership_Escalation_Sent_At, and Next_Cycle_Generated are checked before "
        "every write. If already stamped, subsequent cron passes immediately abort, ensuring 100% mathematical idempotency."
    )
    builder.draw_sheet_card("[*]", "TECHNICAL SPECIFICATIONS", "Formulas & Code Logic", "Engineering Evaluators",
                            tech_box, "COUNTIF, COUNTIFS, FILTER, Apps Script LockService, doGet Webhook Web App",
                            "High performance: batch array reading (getValues/setValues) prevents hitting Google API quotas.",
                            accent_color=builder.c_primary)
    
    return builder.build_pdf()

if __name__ == "__main__":
    generate_sheets_guide()
