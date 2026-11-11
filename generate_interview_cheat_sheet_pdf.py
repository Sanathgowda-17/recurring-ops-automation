#!/usr/bin/env python3
"""
Generates Allo_Innoware_Interview_Call_Cheat_Sheet.pdf
A high-impact, professional interview & call preparation guide for Sanath S Gowda.
Built using standard library Python (no external dependencies required).
"""

import os
import sys
import zlib
import textwrap
from datetime import datetime

class PDFBuilder:
    def __init__(self, filename="Allo_Innoware_Interview_Call_Cheat_Sheet.pdf"):
        self.filename = filename
        self.page_width = 612.0   # Letter width in points (8.5 in)
        self.page_height = 792.0  # Letter height in points (11 in)
        self.margin_left = 40.0
        self.margin_right = 40.0
        self.margin_top = 42.0
        self.margin_bottom = 44.0
        self.content_width = self.page_width - self.margin_left - self.margin_right
        
        self.pages = []  # list of bytearray streams for each page
        self.current_page_stream = bytearray()
        self.current_y = self.page_height - self.margin_top
        self.page_num = 0
        
        # Colors
        self.c_primary = (0.106, 0.212, 0.365)     # Navy #1B365D
        self.c_secondary = (0.169, 0.424, 0.690)   # Slate Blue #2B6CB0
        self.c_accent = (0.753, 0.337, 0.129)      # Warm Amber/Rust #C05621
        self.c_green = (0.184, 0.522, 0.353)       # Forest Green #2F855A
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
        
        # If page 2+, draw running header
        if self.page_num > 1:
            self.draw_running_header()

    def draw_running_header(self):
        s = self.current_page_stream
        # Thin divider line
        s.extend(f"{self.c_border[0]:.3f} {self.c_border[1]:.3f} {self.c_border[2]:.3f} RG\n".encode('latin1'))
        s.extend(b"0.75 w\n")
        y = self.page_height - 30
        s.extend(f"{self.margin_left} {y} m {self.page_width - self.margin_right} {y} l S\n".encode('latin1'))
        
        # Header text
        txt = "ALLO INNOWARE — AI OPERATIONS MANAGER | CALL & INTERVIEW CHEAT SHEET"
        esc = self.escape_text(txt)
        s.extend(b"BT\n")
        s.extend(b"/F2 7.5 Tf\n")
        s.extend(f"{self.c_gray[0]:.3f} {self.c_gray[1]:.3f} {self.c_gray[2]:.3f} rg\n".encode('latin1'))
        s.extend(f"{self.margin_left} {y + 4} Td ({esc}) Tj\n".encode('latin1'))
        s.extend(b"ET\n")
        self.current_y = self.page_height - 48

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

    def draw_wrapped_paragraph(self, x, text, font="/F1", size=9.0, leading=12.5, color=(0.176, 0.216, 0.282), width=None):
        if width is None:
            width = self.content_width - (x - self.margin_left)
        
        approx_chars = int(width / (size * 0.52))
        lines = []
        for paragraph in text.split('\n'):
            if not paragraph.strip():
                lines.append('')
                continue
            wrapped = textwrap.wrap(paragraph, width=approx_chars)
            lines.extend(wrapped)
            
        total_height = len(lines) * leading
        self.ensure_space(total_height + 4)
        
        y = self.current_y
        for line in lines:
            if line:
                self.draw_text_line(x, y, line, font=font, size=size, color=color)
            y -= leading
            
        self.current_y = y
        return total_height

    def draw_section_header(self, title, subtitle=None):
        needed = 34 if subtitle else 26
        self.ensure_space(needed)
        
        y = self.current_y
        # Colored accent pill / banner
        h = 20.0
        self.draw_rect(self.margin_left, y - h, self.content_width, h, fill_color=self.c_primary)
        self.draw_text_line(self.margin_left + 8, y - 14.5, title.upper(), font="/F2", size=9.5, color=self.c_white)
        self.current_y = y - h - 6
        
        if subtitle:
            self.draw_text_line(self.margin_left, self.current_y - 2, subtitle, font="/F3", size=8.5, color=self.c_secondary)
            self.current_y -= 12

    def draw_callout_box(self, title, text, icon="⚡"):
        approx_chars = int((self.content_width - 24) / (8.8 * 0.52))
        lines = []
        for p in text.split('\n'):
            if not p.strip():
                lines.append('')
                continue
            lines.extend(textwrap.wrap(p, width=approx_chars))
            
        box_height = 20 + len(lines) * 12.0 + 8
        self.ensure_space(box_height + 6)
        
        y = self.current_y
        # Background box
        self.draw_rect(self.margin_left, y - box_height, self.content_width, box_height, 
                       fill_color=self.c_card_bg, stroke_color=self.c_secondary, stroke_width=0.75)
        
        # Left highlight bar
        self.draw_rect(self.margin_left, y - box_height, 3.5, box_height, fill_color=self.c_secondary)
        
        # Title
        full_title = f"{icon}  {title}"
        self.draw_text_line(self.margin_left + 10, y - 14, full_title, font="/F2", size=9.0, color=self.c_primary)
        
        # Body lines
        line_y = y - 28
        for line in lines:
            if line:
                self.draw_text_line(self.margin_left + 12, line_y, line, font="/F1", size=8.5, color=self.c_dark)
            line_y -= 12.0
            
        self.current_y = y - box_height - 10

    def draw_qa_item(self, q_num, question, answer, key_takeaway=None):
        approx_chars = int((self.content_width - 16) / (8.5 * 0.52))
        q_lines = textwrap.wrap(f"Q{q_num}: {question}", width=approx_chars)
        
        a_lines = []
        for p in answer.split('\n'):
            if not p.strip():
                a_lines.append('')
                continue
            a_lines.extend(textwrap.wrap(p, width=approx_chars - 2))
            
        t_lines = textwrap.wrap(f"★ KEY POINT TO SAY: {key_takeaway}", width=approx_chars - 4) if key_takeaway else []
        
        total_h = len(q_lines) * 12 + 4 + len(a_lines) * 11.5 + (len(t_lines) * 11 + 6 if t_lines else 0) + 12
        self.ensure_space(total_h)
        
        y = self.current_y
        
        # Draw Question
        for ql in q_lines:
            self.draw_text_line(self.margin_left, y, ql, font="/F2", size=9.0, color=self.c_primary)
            y -= 12
            
        y -= 2
        # Draw Answer
        for al in a_lines:
            if al:
                self.draw_text_line(self.margin_left + 10, y, al, font="/F1", size=8.5, color=self.c_dark)
            y -= 11.5
            
        # Draw Key Point tag if exists
        if t_lines:
            y -= 2
            for tl in t_lines:
                self.draw_text_line(self.margin_left + 12, y, tl, font="/F2", size=8.0, color=self.c_accent)
                y -= 11
                
        y -= 6
        # subtle divider
        self.draw_rect(self.margin_left, y, self.content_width, 0.4, fill_color=self.c_border)
        self.current_y = y - 8

    def draw_table(self, headers, rows, col_widths, font_size=8.0):
        row_height = 16.0
        total_height = (len(rows) + 1) * row_height + 4
        self.ensure_space(total_height)
        
        y = self.current_y
        
        # Header row
        x = self.margin_left
        for i, h in enumerate(headers):
            w = col_widths[i]
            self.draw_rect(x, y - row_height, w, row_height, fill_color=self.c_primary, stroke_color=self.c_border, stroke_width=0.5)
            self.draw_text_line(x + 5, y - row_height + 4.5, h, font="/F2", size=font_size, color=self.c_white)
            x += w
            
        y -= row_height
        
        # Data rows
        for r_idx, row in enumerate(rows):
            bg = self.c_white if r_idx % 2 == 0 else self.c_light_bg
            x = self.margin_left
            for i, val in enumerate(row):
                w = col_widths[i]
                self.draw_rect(x, y - row_height, w, row_height, fill_color=bg, stroke_color=self.c_border, stroke_width=0.5)
                fnt = "/F2" if i == 0 else "/F1"
                clr = self.c_primary if i == 0 else self.c_dark
                self.draw_text_line(x + 5, y - row_height + 4.5, str(val), font=fnt, size=font_size, color=clr)
                x += w
            y -= row_height
            
        self.current_y = y - 8

    def finish_pages_and_footers(self):
        # Finalize the last page
        if self.page_num > 0 and (len(self.pages) < self.page_num):
            self.pages.append(bytes(self.current_page_stream))
            
        total_pages = len(self.pages)
        
        # Append footers onto each page stream
        completed_pages = []
        for idx, page_bytes in enumerate(self.pages):
            p_stream = bytearray(page_bytes)
            p_num = idx + 1
            
            # Bottom divider line
            y = 32.0
            p_stream.extend(f"{self.c_border[0]:.3f} {self.c_border[1]:.3f} {self.c_border[2]:.3f} RG\n".encode('latin1'))
            p_stream.extend(b"0.5 w\n")
            p_stream.extend(f"{self.margin_left} {y} m {self.page_width - self.margin_right} {y} l S\n".encode('latin1'))
            
            # Left footer: Candidate & Confidentiality
            left_txt = "Candidate: Sanath S Gowda | Allo Innoware Operations Assignment | Phone & Interview Defense"
            esc_left = self.escape_text(left_txt)
            p_stream.extend(b"BT\n")
            p_stream.extend(b"/F1 7.0 Tf\n")
            p_stream.extend(f"{self.c_gray[0]:.3f} {self.c_gray[1]:.3f} {self.c_gray[2]:.3f} rg\n".encode('latin1'))
            p_stream.extend(f"{self.margin_left} {y - 10} Td ({esc_left}) Tj\n".encode('latin1'))
            p_stream.extend(b"ET\n")
            
            # Right footer: Page count
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

        # 1: Catalog
        # 2: Pages
        # 3.. 3+N-1: Page objects
        # 3+N.. 3+2N-1: Content stream objects
        # Font objects
        
        pages_kids_refs = []
        for i in range(total_pages):
            page_obj_idx = 3 + i
            pages_kids_refs.append(f"{page_obj_idx} 0 R")
            
        kids_str = " ".join(pages_kids_refs)
        catalog_obj = b"<< /Type /Catalog /Pages 2 0 R >>"
        pages_obj = f"<< /Type /Pages /Kids [{kids_str}] /Count {total_pages} >>".encode('latin1')
        
        add_obj(catalog_obj)  # 1
        add_obj(pages_obj)    # 2
        
        # Create page objects & compress stream objects
        font_ref_idx = 3 + 2 * total_pages
        
        for i in range(total_pages):
            stream_ref_idx = 3 + total_pages + i
            page_dict = (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {self.page_width} {self.page_height}] "
                f"/Resources << /Font << "
                f"/F1 {font_ref_idx} 0 R "
                f"/F2 {font_ref_idx+1} 0 R "
                f"/F3 {font_ref_idx+2} 0 R "
                f">> >> /Contents {stream_ref_idx} 0 R >>"
            ).encode('latin1')
            add_obj(page_dict)
            
        for i in range(total_pages):
            c_raw = pages_content[i]
            c_comp = zlib.compress(c_raw)
            stream_dict = (
                f"<< /Length {len(c_comp)} /Filter /FlateDecode >>\nstream\n"
            ).encode('latin1') + c_comp + b"\nendstream"
            add_obj(stream_dict)
            
        # Font objects
        add_obj(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
        add_obj(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
        add_obj(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique /Encoding /WinAnsiEncoding >>")
        
        # XRef table
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


def generate_cheat_sheet():
    builder = PDFBuilder("Allo_Innoware_Interview_Call_Cheat_Sheet.pdf")
    
    # PAGE 1: TITLE BANNER & 60-SEC ELEVATOR PITCH & ARCHITECTURE
    builder.draw_rect(builder.margin_left, builder.current_y - 48, builder.content_width, 48, 
                      fill_color=builder.c_primary)
    builder.draw_text_line(builder.margin_left + 12, builder.current_y - 20, 
                           "ALLO INNOWARE — AI OPERATIONS MANAGER", 
                           font="/F2", size=15.0, color=builder.c_white)
    builder.draw_text_line(builder.margin_left + 12, builder.current_y - 36, 
                           "Official Interview & Phone Call Cheat Sheet | Project Defense Guide", 
                           font="/F1", size=9.5, color=builder.c_card_bg)
    builder.current_y -= 58
    
    # Meta Info Card
    meta_text = (
        "Candidate: Sanath S Gowda  |  Target Domain: E-Commerce & Marketplace Operations Automation\n"
        "Tech Stack: Google Sheets, Apps Script, Webhook/Web App (doGet), Concurrency Locks, HTML Email Automation\n"
        "GitHub: github.com/Sanathgowda-17/recurring-ops-automation  |  Sheet: docs.google.com/spreadsheets/d/1pt30OdGGjmo8_U7oqjAg3V4QRMNh3V6hm0Cz7OxmSdI"
    )
    builder.draw_callout_box("CANDIDATE & REPOSITORY OVERVIEW", meta_text, icon="📌")
    
    # Section 1: The 60-Second Elevator Pitch
    builder.draw_section_header("1. THE 60-SECOND PHONE CALL SCRIPT (MEMORIZE OR READ DIRECTLY)", 
                                "Use this as soon as they ask: 'Can you tell us about what you have built?'")
    
    pitch_text = (
        "\"At Allo Innoware, as a growing e-commerce brand, operations rely heavily on recurring cadences—from daily "
        "WhatsApp standup dispatches to weekly portal reconciliations and monthly closes. In most scaling teams, "
        "employees suffer from reporting friction and manual cycle drift—forgetting due dates or overwriting master sheets. "
        "Meanwhile, delays either get overlooked or dragged directly to the founders, causing micromanagement.\n\n"
        "To solve this, I built a production automation prototype in Google Sheets and Google Apps Script:\n"
        "1. Employees get an isolated Single-Point Workbench: they filter by name, paste their ticket ID or proof, and submit with zero friction.\n"
        "2. Recurrence is 100% automated: the engine closes the cycle and auto-schedules the next cycle (skipping weekends for daily tasks).\n"
        "3. Smart 2-Tier Escalation: managers get a same-day alert with an embedded 1-Click Ack button powered by an Apps Script Web App.\n"
        "4. Leadership Shield: founders are only alerted if the manager breaches their 4-hour SLA.\n\n"
        "I also built an automated test suite right into the sheet menu covering all 8 test scenarios with zero duplicate alerts.\""
    )
    builder.draw_callout_box("WORD-FOR-WORD SPEAKING SCRIPT (NATURAL, CONFIDENT, PROFESSIONAL)", pitch_text, icon="🎙️")
    
    # Section 2: Architecture & Sheet Summary
    builder.draw_section_header("2. THE 6-SHEET ARCHITECTURE (SEPARATION OF CONCERNS)",
                                "Why the system separates storage from employee interaction")
    
    headers = ["Sheet Name", "Role / Layer", "Operational Purpose & Safeguards"]
    rows = [
        ["Config", "Control Center", "Central parameters: Cutoff times (11 AM), Manager/Leadership emails, SLAs, Web App URL."],
        ["Task_Master", "Catalog", "Master definitions: Task IDs, cadences (Daily, 7d, 15d, 30d), assignees, proof requirements."],
        ["Active_Tasks", "Live Queue", "Heartbeat engine: Tracks cycle instances (TSK-001-C01), due dates, status, & alert timestamps."],
        ["Employee_Workbench", "Single-Point UI", "Filtered employee front-end. Enter proof in Col H, click Submit. Zero master database editing."],
        ["Manager_Dashboard", "Executive KPI", "Overhead summary: Pending, Alerted, Escalated counters, and team compliance percentages."],
        ["Audit_Log", "Immutable Ledger", "Permanent audit trail: actor, timestamp, event type, and before/after statuses."]
    ]
    col_w = [110.0, 95.0, 327.0]
    builder.draw_table(headers, rows, col_w, font_size=7.5)
    
    # PAGE 2: TOP INTERVIEW QUESTIONS & ANSWERS (PART 1)
    builder.new_page()
    builder.draw_section_header("3. TOP TECHNICAL & STRATEGIC INTERVIEW QUESTIONS (Q1 - Q5)",
                                "Exact answers to expected founder & hiring manager questions")
    
    # Q1
    builder.draw_qa_item(
        1,
        "Why did you build an Employee Workbench instead of letting team members edit Active_Tasks directly?",
        "Directly editing master sheets is the primary cause of formula corruption and duplicate data in operations teams. "
        "When multiple employees work on a 20-column database simultaneously, they accidentally overwrite rows, filter other "
        "people's views, or miscalculate recurring dates. The Workbench serves as a clean front-end interface: employees see "
        "only what's assigned to them, type their proof in one designated green cell, and click Submit. The Apps Script backend "
        "handles database updates and cycle advances in the background with zero duplicate work.",
        key_takeaway="Separation of concerns prevents human error and eliminates master sheet corruption."
    )
    
    # Q2
    builder.draw_qa_item(
        2,
        "How did you solve the daily WhatsApp task (Test 3) since WhatsApp updates don't produce a Ticket ID?",
        "This is a common real-world operational challenge. A simple Yes/No checkbox invites careless ticking, while full "
        "enterprise WhatsApp bots require heavy setup and monthly API fees. I implemented the 'Timestamp + Summary Snippet Protocol': "
        "the employee pastes the dispatch time and 1-line summary (e.g., 10:45 AM - 'Daily Ops: 18 dispatches on schedule, 0 delays') "
        "into the Workbench. It takes under 15 seconds, creates a searchable audit record, allows managers to spot-check against "
        "the WhatsApp group instantly, and automatically schedules the next business day.",
        key_takeaway="Zero employee friction (<15s) with 100% auditability without expensive third-party tools."
    )
    
    # Q3
    builder.draw_qa_item(
        3,
        "What prevents the automation from spamming duplicate emails or creating duplicate cycles? (Test 8)",
        "I implemented two enterprise-grade safeguards: First, Concurrency Locking via Apps Script's LockService.getScriptLock().waitLock(30000). "
        "If an employee clicks Submit multiple times rapidly, the second thread detects the task is already completed and safely exits. "
        "Second, Atomic Timestamp Guards: before dispatching alerts or generating cycles, the engine checks Manager_Alert_Sent_At and "
        "Next_Cycle_Generated. Once stamped, subsequent automated cron scans immediately bypass that record. Test 8 verifies this by "
        "running the engine 3 times back-to-back—producing exactly 0 duplicate alerts and 0 duplicate cycles.",
        key_takeaway="LockService concurrency locks + atomic timestamp flags guarantee 100% idempotency."
    )
    
    # Q4
    builder.draw_qa_item(
        4,
        "How does the 1-Click Manager Acknowledgement work technically? (Test 5)",
        "The automated alert email sent to the manager includes an HTML button: [Click Here to Acknowledge Task]. "
        "This button calls a deployed Google Apps Script Web App (ManagerWebApp.html) via its doGet() webhook endpoint with "
        "the task ID as a parameter. When clicked from email, the Web App validates the task, timestamps Manager_Acknowledged_At, "
        "updates status to 'Manager Acknowledged', records an audit event, and serves a clean confirmation page in the browser. "
        "This immediately pauses leadership escalation without requiring the manager to open Google Sheets on a desktop.",
        key_takeaway="Zero friction for busy managers—can be acknowledged from a phone inbox in 2 seconds."
    )
    
    # Q5
    builder.draw_qa_item(
        5,
        "How does your architecture specifically reduce founder dependency?",
        "In unmanaged setups, whenever an operational task is delayed, either the founder spends time chasing employees, or "
        "issues go unnoticed until customer deliveries fail. My architecture creates an automated 2-tier SLA shield: the direct manager "
        "is alerted first and given a 4-hour resolution window. Founders/leadership are only alerted if the manager neglects their SLA. "
        "Routine operational delays stay at the operational manager tier, protecting executive leadership focus.",
        key_takeaway="Automated 2-tier SLA shield stops executive micromanagement."
    )
    
    # PAGE 3: QUESTIONS (Q6-Q8), TEST MATRIX & PRO TIPS
    builder.new_page()
    builder.draw_section_header("4. DEEP-DIVE TECHNICAL QUESTIONS (Q6 - Q8)",
                                "Edge cases, business logic, and enterprise scaling")
    
    # Q6
    builder.draw_qa_item(
        6,
        "What happens if a daily task falls on a Friday or weekend?",
        "The recurrence engine includes working-day intelligence in the calculateNextDueDate() function. When a daily task is "
        "completed on a Friday, the system checks the calendar day and advances by 3 days (skipping Saturday and Sunday), "
        "setting the next due date for Monday morning at 11:00 AM. This ensures realistic, business-accurate operational cadences.",
        key_takeaway="Recurrence calculation automatically accounts for weekends and working days."
    )
    
    # Q7
    builder.draw_qa_item(
        7,
        "How did you test all this? Can you prove it works?",
        "I engineered an automated test runner directly into the Google Sheet under the custom menu: ⚡ Allo Innoware Ops > "
        "🧪 Run Test Scenarios. Evaluators can run individual tests from Test 1 to Test 8—such as 7-day cycle generation, "
        "single-point completion, same-day alert dispatch, 1-click acknowledgement, leadership escalation, and anti-duplication—or "
        "run the full test suite in one click. Every test verifies state changes and outputs an instant summary dialog.",
        key_takeaway="Built-in automated test suite allows any evaluator to verify all 8 scenarios in 60 seconds."
    )
    
    # Q8
    builder.draw_qa_item(
        8,
        "How does this system scale as Allo Innoware grows from 4 tasks to 100+ tasks?",
        "The architecture is designed to scale across three operational phases: Phase 1 (Current Sheets Prototype): Uses batch "
        "array reading (getValues/setValues) to handle hundreds of tasks well within Apps Script execution limits. Phase 2 (Webhook "
        "Evolution): Integrate WhatsApp Cloud API / Twilio webhooks to intercept hashtags like #OPS_DONE directly into Apps Script. "
        "Phase 3 (Enterprise Modernization): The exact same relational schema and SLA state machine maps directly to PostgreSQL/Supabase "
        "and a lightweight React/Next.js dashboard as company volume scales.",
        key_takeaway="Clear 3-phase roadmap from Google Workspace prototype to enterprise microservice."
    )
    
    # Section 5: The 8 Tests Summary Matrix
    builder.draw_section_header("5. QUICK-REFERENCE: THE 8 TEST SCENARIOS MATRIX",
                                "What each test proves in the assignment")
    
    test_headers = ["Test #", "Name / Scenario", "Key Behavior Verified", "Sheet Proof"]
    test_rows = [
        ["Test 1", "7-Day Cycle Logic", "Closes cycle 1, auto-generates cycle 2 (+7 days).", "Active_Tasks: C01 -> C02"],
        ["Test 2", "Single-Point UI", "Employee C submits Ticket ID from Workbench without master editing.", "Employee_Workbench -> Active_Tasks"],
        ["Test 3", "Daily WhatsApp Proof", "Captures timestamp + standup summary, schedules next business day.", "Active_Tasks proof col & audit"],
        ["Test 4", "Same-Day Alert", "Fires HTML email with 1-click ack button when cutoff passes.", "Manager_Alert_Sent_At stamped"],
        ["Test 5", "Manager Ack", "Web app records 1-click ack from inbox, pauses leadership escalation.", "Manager_Acknowledged_At & status"],
        ["Test 6", "Leadership Escalation", "Fires high-priority escalation to founders if manager breaches SLA.", "Leadership_Escalation_Sent_At"],
        ["Test 7", "SLA Timing Matrix", "Validates distinct SLA tiers: daily (4h SLA) vs periodic (24h SLA).", "Config sheet parameter rules"],
        ["Test 8", "Anti-Duplication", "Runs engine 3x consecutively: verifies 0 duplicate alerts/cycles.", "LockService & idempotency logs"]
    ]
    col_w2 = [48.0, 108.0, 246.0, 130.0]
    builder.draw_table(test_headers, test_rows, col_w2, font_size=7.2)
    
    # Section 6: Pro-Tips for Phone Call
    builder.draw_section_header("6. WINNING THE CALL: 4 PRACTICAL TIPS FOR SANATH",
                                "Deliver with confidence and executive poise")
    
    tips = (
        "• Offer a Live Demo Immediately: \"I have the Google Sheet open right in front of me with the ⚡ Allo Innoware Ops menu. "
        "If you'd like, I can run any of the 8 test scenarios live or share my screen.\"\n"
        "• Speak in Terms of Business Impact: Emphasize 'reducing founder micromanagement', 'eliminating manual cycle drift', and 'zero duplicate work'.\n"
        "• Frame Sheets as the Pragmatic Starting Point: Explain that starting in Google Sheets enabled immediate zero-cost deployment "
        "while maintaining enterprise-grade safeguards like LockService and immutable audit logging.\n"
        "• Stay Calm and Structured: Use the formula: Problem -> Architecture Solution -> Measurable Business Outcome."
    )
    builder.draw_callout_box("EXECUTIVE DELIVERY GUIDELINES", tips, icon="💡")
    
    return builder.build_pdf()

if __name__ == "__main__":
    generate_cheat_sheet()
