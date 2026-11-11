#!/usr/bin/env python3
"""
Generates Allo_Innoware_Simple_Explanation_Guide.pdf
Contains the EXACT simple English explanation provided to Sanath:
1. In Plain English: What is this project & what did I build?
2. The 4-Step Operational Flow Diagram
3. The 5 Key Things Built
4. The 6 Google Sheets Explained Simply
5. How They Work Together
6. The 2-Sentence & 60-Second Phone Speaking Scripts
"""

import os
import sys
import zlib
import textwrap

class SimplePDFBuilder:
    def __init__(self, filename="Allo_Innoware_Simple_Explanation_Guide.pdf"):
        self.filename = filename
        self.page_width = 612.0   # Letter width in points (8.5 in)
        self.page_height = 792.0  # Letter height in points (11 in)
        self.margin_left = 38.0
        self.margin_right = 38.0
        self.margin_top = 38.0
        self.margin_bottom = 40.0
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
        self.c_red = (0.784, 0.188, 0.188)         # Alert Red #C83030
        self.c_purple = (0.424, 0.235, 0.612)      # Deep Purple #6C3C9C
        self.c_dark = (0.150, 0.180, 0.220)        # Soft Dark Text #262E38
        self.c_gray = (0.420, 0.460, 0.520)        # Medium Gray
        self.c_light_bg = (0.965, 0.975, 0.985)    # Card Background
        self.c_highlight_bg = (0.930, 0.955, 0.985)# Soft Accent Box
        self.c_border = (0.780, 0.820, 0.870)      # Border
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
            '🔄': '<->',
            '🤖': '[AI]',
            '🌟': '[*]',
            '🔍': '[>]'
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
        y = self.page_height - 26
        s.extend(f"{self.c_border[0]:.3f} {self.c_border[1]:.3f} {self.c_border[2]:.3f} RG\n".encode('latin1'))
        s.extend(b"0.75 w\n")
        s.extend(f"{self.margin_left} {y} m {self.page_width - self.margin_right} {y} l S\n".encode('latin1'))
        
        txt = "ALLO INNOWARE -- PROJECT & GOOGLE SHEETS EXPLAINED IN SIMPLE ENGLISH"
        esc = self.escape_text(txt)
        s.extend(b"BT\n")
        s.extend(b"/F2 7.5 Tf\n")
        s.extend(f"{self.c_gray[0]:.3f} {self.c_gray[1]:.3f} {self.c_gray[2]:.3f} rg\n".encode('latin1'))
        s.extend(f"{self.margin_left} {y + 4} Td ({esc}) Tj\n".encode('latin1'))
        s.extend(b"ET\n")
        self.current_y = self.page_height - 44

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

    def draw_section_banner(self, title, subtitle=None, color=None):
        if color is None:
            color = self.c_primary
        needed = 32 if subtitle else 24
        self.ensure_space(needed)
        y = self.current_y
        h = 18.0
        self.draw_rect(self.margin_left, y - h, self.content_width, h, fill_color=color)
        self.draw_text_line(self.margin_left + 8, y - 13.0, title.upper(), font="/F2", size=9.0, color=self.c_white)
        self.current_y = y - h - 5
        
        if subtitle:
            self.draw_text_line(self.margin_left, self.current_y - 2, subtitle, font="/F3", size=8.0, color=self.c_secondary)
            self.current_y -= 11

    def draw_card(self, title, lines_list, accent_bar_color=None, bg_color=None, border_color=None):
        if accent_bar_color is None:
            accent_bar_color = self.c_secondary
        if bg_color is None:
            bg_color = self.c_light_bg
        if border_color is None:
            border_color = self.c_border
            
        approx_chars = int((self.content_width - 24) / (8.2 * 0.52))
        formatted_lines = []
        for item in lines_list:
            if isinstance(item, tuple):
                # (is_bold, text)
                prefix = item[0]
                text = item[1]
                wrapped = textwrap.wrap(text, width=approx_chars)
                for i, w in enumerate(wrapped):
                    formatted_lines.append((prefix if i == 0 else False, w))
            else:
                wrapped = textwrap.wrap(item, width=approx_chars)
                for w in wrapped:
                    formatted_lines.append((False, w))
                    
        card_h = 22 + len(formatted_lines) * 11.5 + 8
        self.ensure_space(card_h + 6)
        
        y = self.current_y
        self.draw_rect(self.margin_left, y - card_h, self.content_width, card_h, 
                       fill_color=bg_color, stroke_color=border_color, stroke_width=0.6)
        self.draw_rect(self.margin_left, y - card_h, 4.0, card_h, fill_color=accent_bar_color)
        
        # Title
        self.draw_text_line(self.margin_left + 10, y - 14, title, font="/F2", size=9.2, color=self.c_primary)
        
        curr_y = y - 27
        for is_bold, line_text in formatted_lines:
            fnt = "/F2" if is_bold else "/F1"
            clr = self.c_primary if is_bold else self.c_dark
            self.draw_text_line(self.margin_left + 12, curr_y, line_text, font=fnt, size=8.2, color=clr)
            curr_y -= 11.5
            
        self.current_y = y - card_h - 7

    def draw_flow_box(self, steps):
        # steps: list of (step_title, step_desc)
        step_h = 24.0
        arrow_h = 10.0
        total_h = len(steps) * step_h + (len(steps) - 1) * arrow_h + 10
        self.ensure_space(total_h)
        
        y = self.current_y
        for i, (title, desc) in enumerate(steps):
            box_y = y - step_h
            # Draw step box
            self.draw_rect(self.margin_left + 20, box_y, self.content_width - 40, step_h,
                           fill_color=self.c_highlight_bg, stroke_color=self.c_secondary, stroke_width=0.75)
            self.draw_text_line(self.margin_left + 30, box_y + 13.5, title, font="/F2", size=8.5, color=self.c_primary)
            self.draw_text_line(self.margin_left + 30, box_y + 4.5, desc, font="/F1", size=7.8, color=self.c_dark)
            
            y -= step_h
            if i < len(steps) - 1:
                # Draw connecting down arrow
                mid_x = self.margin_left + self.content_width / 2.0
                self.draw_text_line(mid_x - 3, y - 8, "|", font="/F2", size=9.0, color=self.c_secondary)
                self.draw_text_line(mid_x - 5, y - 10, "v", font="/F2", size=8.5, color=self.c_secondary)
                y -= arrow_h
                
        self.current_y = y - 8

    def finish_pages_and_footers(self):
        if self.page_num > 0 and (len(self.pages) < self.page_num):
            self.pages.append(bytes(self.current_page_stream))
            
        total_pages = len(self.pages)
        completed_pages = []
        for idx, page_bytes in enumerate(self.pages):
            p_stream = bytearray(page_bytes)
            p_num = idx + 1
            
            y = 28.0
            p_stream.extend(f"{self.c_border[0]:.3f} {self.c_border[1]:.3f} {self.c_border[2]:.3f} RG\n".encode('latin1'))
            p_stream.extend(b"0.5 w\n")
            p_stream.extend(f"{self.margin_left} {y} m {self.page_width - self.margin_right} {y} l S\n".encode('latin1'))
            
            left_txt = "Sanath S Gowda | Allo Innoware Operations Project | Plain English Walkthrough"
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


def generate_simple_guide():
    builder = SimplePDFBuilder("Allo_Innoware_Simple_English_Project_Guide.pdf")
    
    # PAGE 1: TITLE BANNER, THE REAL PROBLEM, WHAT DID YOU BUILD, & 4-STEP FLOW
    builder.draw_rect(builder.margin_left, builder.current_y - 44, builder.content_width, 44, fill_color=builder.c_primary)
    builder.draw_text_line(builder.margin_left + 12, builder.current_y - 18, 
                           "ALLO INNOWARE -- PROJECT EXPLAINED IN SIMPLE ENGLISH", 
                           font="/F2", size=13.5, color=builder.c_white)
    builder.draw_text_line(builder.margin_left + 12, builder.current_y - 33, 
                           "Candidate: Sanath S Gowda | Clear, Relatable, Jargon-Free Guide to Read or Memorize", 
                           font="/F1", size=8.5, color=builder.c_highlight_bg)
    builder.current_y -= 52
    
    # Section: In Plain English
    builder.draw_section_banner("1. IN PLAIN ENGLISH: WHAT IS THIS PROJECT?", "The real-world company context")
    intro_lines = [
        (True, "Imagine a busy e-commerce company like Allo Innoware (selling on Amazon, Flipkart, D2C):"),
        (False, "Every single day and week, employees have routine operational tasks they MUST complete on time:"),
        (False, "* Post a morning dispatch update in the WhatsApp group (Daily by 11:00 AM)."),
        (False, "* Check marketplace portal metrics (Every 7 days)."),
        (False, "* Reconcile vendor payments (Every 15 days)."),
        (False, "* Close monthly accounts and post closing entries (Every 30 days).")
    ]
    builder.draw_card("THE E-COMMERCE CONTEXT", intro_lines, accent_bar_color=builder.c_secondary)
    
    # Section: The Real Problem
    builder.draw_section_banner("2. THE REAL PROBLEM (WHY COMPANIES MESS THIS UP)", "Why manual systems always break down", color=builder.c_red)
    problem_lines = [
        (True, "1. People Forget (Cycle Drift):"),
        (False, "An employee finishes a weekly task on Thursday instead of Tuesday, forgets when the next one is due, and the schedule drifts into chaos."),
        (True, "2. Spreadsheet Chaos:"),
        (False, "5 people edit the same big Excel/Google Sheet at the same time, accidentally deleting formulas, overwriting rows, or breaking data."),
        (True, "3. Founder Headache (Micromanagement):"),
        (False, "When someone delays work, nobody notices until customer orders are late. Or worse: the founder has to spend all day chasing employees: 'Did you send the WhatsApp update?'")
    ]
    builder.draw_card("THE 3 CORE FAILURE MODES", problem_lines, accent_bar_color=builder.c_red)
    
    # Section: What Did You Build?
    builder.draw_section_banner("3. WHAT DID YOU BUILD?", "The intelligent automated operations manager")
    build_lines = [
        (True, "You built an intelligent, automated operations manager inside Google Sheets & Google Apps Script."),
        (False, "Think of it as an automatic task tracker with an alert dog: it manages the tasks, schedules the next ones, watches deadlines, and alerts managers automatically.")
    ]
    builder.draw_card("THE ROBOT AT WORK", build_lines, accent_bar_color=builder.c_green)
    
    # 4-Step Diagram
    builder.draw_section_banner("4. HOW IT WORKS IN 4 SIMPLE STEPS", "The automated operational journey")
    steps = [
        ("[Step 1] Employee Submits Work", "Employee opens their clean screen, picks their name, enters proof, and clicks 'Submit' (under 15s)."),
        ("[Step 2] System Auto-Schedules Next Cycle", "System marks it completed and automatically sets the next due date (+7 days, or Friday moves to Monday)."),
        ("[Step 3] Manager Alert (If Missed / Overdue)", "If missed past cutoff (11:00 AM), Manager gets an email with a 1-Click 'Acknowledge' button."),
        ("[Step 4] Leadership Escalation (If Ignored)", "If Manager ignores the alert for 4 hours, top leadership/founders get an urgent escalation email.")
    ]
    builder.draw_flow_box(steps)
    
    # PAGE 2: THE 5 KEY FEATURES & 2-SENTENCE PITCH
    builder.new_page()
    builder.draw_section_banner("5. THE 5 KEY THINGS YOU BUILT (EXPLAINED SIMPLY)", "The core features of your solution")
    
    f1 = [
        (True, "1. A Clean 'Employee Workbench' (No messy sheets):"),
        (False, "Instead of letting employees touch the master database, they open a clean front screen. They pick their name from a dropdown, see only their pending work, type their proof (Ticket ID or WhatsApp summary), and click Submit. It takes under 15 seconds and prevents accidental deletions.")
    ]
    builder.draw_card("FEATURE 1: ZERO SPREADSHEET FRICTION", f1, accent_bar_color=builder.c_primary)
    
    f2 = [
        (True, "2. Automatic Recurrence Engine:"),
        (False, "As soon as a task is submitted, the system automatically creates the next cycle. If it's a 7-day task, it sets the date 7 days ahead. If it's a daily task completed on Friday, it's smart enough to skip Saturday and Sunday and set it for Monday morning!")
    ]
    builder.draw_card("FEATURE 2: SMART WORKING-DAY RECURRENCE", f2, accent_bar_color=builder.c_secondary)
    
    f3 = [
        (True, "3. 1-Click Manager Acknowledgement (Direct from Email):"),
        (False, "If an employee misses the deadline, the manager immediately receives an email alert. Inside the email is a big button: [Click Here to Acknowledge Task]. The manager taps that button on their phone, and the system records that the manager is handling it--pausing founder escalation. The manager never even has to open Google Sheets!")
    ]
    builder.draw_card("FEATURE 3: 1-CLICK MANAGER ACTION", f3, accent_bar_color=builder.c_accent)
    
    f4 = [
        (True, "4. The 'Leadership Shield':"),
        (False, "The founders are NOT bothered with minor daily hiccups. Leadership is ONLY alerted if the manager ignores the issue for more than 4 hours. This protects the founders from micromanaging and lets them focus on company growth.")
    ]
    builder.draw_card("FEATURE 4: PROTECTING FOUNDER FOCUS", f4, accent_bar_color=builder.c_green)
    
    f5 = [
        (True, "5. Anti-Duplication Safeguards & 8 Built-in Test Buttons:"),
        (False, "The engine uses LockService and timestamp flags: it NEVER sends duplicate spam emails or creates duplicate tasks, even if someone clicks Submit 10 times fast. You also built 8 automated test buttons under the custom menu 'Allo Innoware Ops' so anyone can click and watch the system work live.")
    ]
    builder.draw_card("FEATURE 5: BULLETPROOF RELIABILITY & LIVE TESTS", f5, accent_bar_color=builder.c_purple)
    
    # 2-Sentence Pitch Box
    builder.draw_section_banner("6. HOW TO EXPLAIN IT IN 2 SENTENCES OVER THE PHONE", "The ultimate phone call summary")
    pitch_box = [
        (True, "Read this directly if you need a quick 10-second summary:"),
        (False, "\"I built an automated operations tracking system in Google Sheets and Apps Script that completely automates recurring tasks. Employees submit their completion proof from a single clean screen, the system automatically schedules the next cycle, and if any task is missed, it alerts the manager via email with a 1-click acknowledgement button, only escalating to leadership if the delay is ignored.\"")
    ]
    builder.draw_card("THE 2-SENTENCE PHONE PITCH", pitch_box, accent_bar_color=builder.c_accent, bg_color=builder.c_highlight_bg)
    
    # PAGE 3: THE 6 GOOGLE SHEETS EXPLAINED IN SIMPLE ENGLISH
    builder.new_page()
    builder.draw_section_banner("7. THE 6 GOOGLE SHEETS EXPLAINED IN SIMPLE TERMS", "What each tab does and who uses it")
    
    s1 = [
        (True, "Sheet 1: 'Config' -- The Control Center (Settings):"),
        (False, "Think of this as the 'Settings menu' of your entire automation. Used once by the Admin. Holds manager emails, cutoff times (11:00 AM daily), and the Web App URL. If an email changes, you update 1 cell here without touching any code.")
    ]
    builder.draw_card("TAB 1: CONFIG (SETTINGS)", s1, accent_bar_color=builder.c_purple)
    
    s2 = [
        (True, "Sheet 2: 'Task_Master' -- The Blueprint / Catalog:"),
        (False, "The master list of all recurring duties in the company. Lists Task IDs (TSK-001..), names, frequencies (Daily, 7d, 15d, 30d), assignees, and required proof (WhatsApp summary or Ticket ID). The engine checks this to know when the next cycle is due.")
    ]
    builder.draw_card("TAB 2: TASK_MASTER (CATALOG)", s2, accent_bar_color=builder.c_secondary)
    
    s3 = [
        (True, "Sheet 3: 'Active_Tasks' -- The Engine Room (Live Database):"),
        (False, "The running queue of every single task instance happening right now (e.g. TSK-001-C01, TSK-001-C02). Employees never touch this sheet. Stores due dates, statuses (Pending, Alerted, Escalated, Completed), and exact timestamps of every email alert.")
    ]
    builder.draw_card("TAB 3: ACTIVE_TASKS (LIVE DATABASE)", s3, accent_bar_color=builder.c_accent)
    
    s4 = [
        (True, "Sheet 4: 'Employee_Workbench' -- The Front-End Screen for Workers:"),
        (False, "The clean interface for team members. An employee picks their name in cell B4, sees only THEIR pending tasks, types their proof in the green Column H, and clicks Submit on the top menu. Zero clutter, under 15 seconds, zero broken formulas.")
    ]
    builder.draw_card("TAB 4: EMPLOYEE_WORKBENCH (USER SCREEN)", s4, accent_bar_color=builder.c_green)
    
    s5 = [
        (True, "Sheet 5: 'Manager_Dashboard' -- The Executive KPI Screen:"),
        (False, "Real-time birds-eye view for the Manager. Shows 5 big counter cards (Pending, Alerted, Acknowledged, Escalated, Completed) plus an Employee Compliance Table with real-time percentages. In 5 seconds, a manager sees who is on track.")
    ]
    builder.draw_card("TAB 5: MANAGER_DASHBOARD (KPI DASHBOARD)", s5, accent_bar_color=builder.c_primary)
    
    s6 = [
        (True, "Sheet 6: 'Audit_Log' -- The Black Box (Permanent History Ledger):"),
        (False, "An un-editable historical ledger (like a bank statement or airplane black box). Records every action: who submitted it, exact timestamp, event type, and before/after statuses. Leaves zero room for finger-pointing.")
    ]
    builder.draw_card("TAB 6: AUDIT_LOG (THE BLACK BOX)", s6, accent_bar_color=builder.c_gray)
    
    # 10-Second Summary Diagram
    builder.draw_section_banner("8. HOW THEY WORK TOGETHER (THE 10-SECOND SUMMARY)", "How data moves across the sheets")
    summary_box = [
        (True, "The Complete System Loop:"),
        (False, "[Task_Master]       --> Defines what tasks exist and their frequencies."),
        (False, "[Active_Tasks]      --> Keeps live records, due dates & audit timestamps."),
        (False, "[Employee_Workbench]--> Filtered view for workers to submit proof in 1 click."),
        (False, "[Manager_Dashboard] --> Displays real-time KPI counters & team compliance %."),
        (False, "[Audit_Log]         --> Permanently logs every single action with zero tampering.")
    ]
    builder.draw_card("THE 10-SECOND SUMMARY MAP", summary_box, accent_bar_color=builder.c_secondary, bg_color=builder.c_highlight_bg)
    
    return builder.build_pdf()

if __name__ == "__main__":
    generate_simple_guide()
