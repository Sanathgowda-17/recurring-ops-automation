#!/usr/bin/env python3
"""
generate_assignment_guide_pdf.py
Builds a beautifully styled, comprehensive reference PDF guide for:
"Allo Innoware: AI Operations Manager Assignment - System Architecture, 8 Tests & Interview Master Guide"
"""

import os
import sys

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header (Pages > 1)
        if self._pageNumber > 1:
            self.drawString(36, 11 * inch - 28, "ALLO INNOWARE | AI Operations Manager — System Architecture & Interview Guide")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(36, 11 * inch - 32, 8.5 * inch - 36, 11 * inch - 32)
        
        # Footer
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * inch - 36, 25, page_str)
        self.drawString(36, 25, "Confidential — Candidate Reference & Operational Blueprint")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(36, 35, 8.5 * inch - 36, 35)
        self.restoreState()

def build_guide_pdf(filename="Allo_Innoware_Assignment_Complete_Guide.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=42,
        bottomMargin=46
    )

    styles = getSampleStyleSheet()

    # Color Palette
    PRIMARY = colors.HexColor("#1e3a8a")    # Deep Navy
    SECONDARY = colors.HexColor("#0f766e")  # Teal Accent
    ACCENT_RED = colors.HexColor("#b91c1c") # Crimson
    TEXT_DARK = colors.HexColor("#0f172a")  # Slate 900
    TEXT_MUTED = colors.HexColor("#475569") # Slate 600
    BG_LIGHT = colors.HexColor("#f8fafc")   # Slate 50
    BORDER_CLR = colors.HexColor("#e2e8f0")

    # Typography
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=PRIMARY,
        alignment=TA_LEFT
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=TEXT_MUTED,
        alignment=TA_LEFT
    )

    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=PRIMARY,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=SECONDARY,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=TEXT_DARK,
        alignment=TA_LEFT,
        spaceAfter=5
    )

    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=TEXT_DARK,
        leftIndent=14,
        spaceAfter=3
    )

    qa_q = ParagraphStyle(
        'QA_Q',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13.5,
        textColor=PRIMARY,
        spaceBefore=8,
        spaceAfter=2,
        keepWithNext=True
    )

    qa_a = ParagraphStyle(
        'QA_A',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.8,
        leading=12.8,
        textColor=TEXT_DARK,
        leftIndent=12,
        spaceAfter=8
    )

    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.2,
        leading=11.2,
        textColor=TEXT_DARK
    )

    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.white
    )

    story = []

    # Title Banner
    story.append(Paragraph("ALLO INNOWARE — AI OPERATIONS MANAGER", title_style))
    story.append(Paragraph("Recurring Task Tracking, Pending Reports & Escalation Automation | Master Guide & Blueprint", subtitle_style))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=12))

    # Executive Overview
    meta_data = [
        [
            Paragraph("<b>Candidate:</b> Sanath S Gowda<br/><b>Role:</b> AI Operations Manager<br/><b>Prototype Link:</b> <u>docs.google.com/spreadsheets/d/1pt30OdGGjmo8_U7oqjAg3V4QRMNh3V6hm0Cz7OxmSdI</u>", table_cell),
            Paragraph("<b>Target Domain:</b> E-commerce & Operations Automation<br/><b>Technology:</b> Google Sheets, Apps Script, Webhooks, HTML Web App<br/><b>Repository:</b> <u>github.com/Sanathgowda-17/recurring-ops-automation</u>", table_cell)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[270, 270])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 0.75, BORDER_CLR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_CLR),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # Section 1: Business Problem
    story.append(Paragraph("1. THE REAL BUSINESS PROBLEM (THE 'WHY')", h1_style))
    story.append(Paragraph(
        "Allo Innoware is a rapidly scaling e-commerce brand operating across major marketplaces (Amazon, Flipkart) and D2C channels. "
        "As order volumes and operational touchpoints expand, recurring processes across inventory, vendor reconciliation, accounting closing, "
        "and daily team standups must execute flawlessly on fixed cadences without constant executive supervision.",
        body_style
    ))
    story.append(Paragraph("<b>The Core Failure Modes Before This Prototype:</b>", body_style))
    story.append(Paragraph("• <b>Manual Cycle Drift:</b> If a 7-day task due on Tuesday was completed on Thursday, employees would manually recalculate dates incorrectly or forget the next due date entirely.", bullet_style))
    story.append(Paragraph("• <b>Duplicated Reporting Friction:</b> Team members had to check one sheet for pending items, perform work in an external portal, update a master tracker, and then log completion notes elsewhere.", bullet_style))
    story.append(Paragraph("• <b>The Daily Task Proof Vacuum:</b> Daily standup updates in WhatsApp groups produce no natural Ticket IDs. Without a structured proof protocol, managers had no lightweight way to verify completion.", bullet_style))
    story.append(Paragraph("• <b>Founder Chokehold:</b> Lacking automated multi-tiered escalation, operational delays were either completely overlooked or dragged straight to executive leadership, creating constant founder micro-management.", bullet_style))

    # Section 2: Architecture
    story.append(Paragraph("2. SYSTEM ARCHITECTURE & 6 CORE OPERATIONAL SHEETS", h1_style))
    story.append(Paragraph(
        "The system organizes operational state into 6 purpose-built sheets, separating data storage from employee interaction to prevent formula corruption and duplication:",
        body_style
    ))

    sheet_table_data = [
        [Paragraph("Sheet Name", table_header), Paragraph("Primary Role", table_header), Paragraph("Operational Function", table_header)],
        [Paragraph("<b>Config</b>", table_cell), Paragraph("System Control", table_cell), Paragraph("Centralized parameters: Manager/Leadership emails, cutoffs (11:00 AM daily), SLA timers, Web App URL.", table_cell)],
        [Paragraph("<b>Task_Master</b>", table_cell), Paragraph("Catalog", table_cell), Paragraph("Master definitions: Task IDs, names, assigned employees, cadences (Daily, 7d, 15d, 30d), and proof types.", table_cell)],
        [Paragraph("<b>Active_Tasks</b>", table_cell), Paragraph("Live Queue", table_cell), Paragraph("The heartbeat engine tracking cycle instances (e.g. TSK-001-C01), due dates, status transitions, and audit timestamps.", table_cell)],
        [Paragraph("<b>Employee_Workbench</b>", table_cell), Paragraph("Single-Point UI", table_cell), Paragraph("Filtered interface for employees. Enter Ticket ID/WhatsApp proof in Col H and submit with 1 click. Zero duplicate work.", table_cell)],
        [Paragraph("<b>Manager_Dashboard</b>", table_cell), Paragraph("Executive KPI", table_cell), Paragraph("Overhead summary cards (Pending, Alerted, Escalated, Completed) and real-time employee compliance percentages.", table_cell)],
        [Paragraph("<b>Audit_Log</b>", table_cell), Paragraph("Immutable Ledger", table_cell), Paragraph("Permanent event trail recording actor, timestamp, event type, and before/after status for all transactions.", table_cell)],
    ]
    st = Table(sheet_table_data, colWidths=[110, 100, 330])
    st.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT]),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_CLR),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(st)
    story.append(Spacer(1, 10))

    # Section 3: 8 Tests
    story.append(Paragraph("3. BREAKDOWN OF THE 8 ASSIGNMENT TEST SCENARIOS", h1_style))
    story.append(Paragraph("Each required test was engineered into the prototype and can be triggered via the custom Google Sheets menu:", body_style))

    tests = [
        ("Test 1 — Recurring Cycle Logic", "Completing a 7-day, 15-day, or 30-day task closes the active cycle and automatically spawns Cycle N+1 in Active_Tasks with the due date advanced exactly by the frequency offset. Daily tasks skip weekends to maintain working-day cadences."),
        ("Test 2 — Single-Point Completion", "Demonstrates that Employee C selects their name in Employee_Workbench, views only their pending tasks, types their Ticket ID (e.g. VEND-RECON-5510) directly into Column H, and clicks Submit. The master database updates without secondary manual entries."),
        ("Test 3 — Daily Task (WhatsApp Proof)", "Deploys the practical 'Timestamp + Summary Snippet Protocol' (e.g., 10:45 AM - 'Ops Standup: 18 dispatches on schedule, zero delays'). Requires <15s of employee effort, provides verifiable proof against group chats, and auto-schedules the next business day."),
        ("Test 4 — Same-Day Manager Alert", "When a task passes cutoff + 30-min grace period, the escalation engine dispatches an HTML email to the manager on the same day containing task details, delay duration, and an embedded 1-Click Acknowledge button. Stamps Manager_Alert_Sent_At."),
        ("Test 5 — Manager Action & Acknowledgement", "Clicking the 1-Click button calls the deployed Apps Script Web App (doGet). The system marks status as 'Manager Acknowledged', records the manager timestamp, and places a hold on leadership escalation while follow-up occurs."),
        ("Test 6 — Leadership Escalation", "If 4 hours elapse post-alert without manager acknowledgement or resolution, the engine detects an SLA breach and fires an urgent high-priority HTML escalation email to Leadership (CCing Manager and Employee)."),
        ("Test 7 — Timing SLA Matrix Logic", "Enforces distinct SLA tiers: Daily tasks trigger alert at 11:30 AM with a 4-hour manager window (escalating at 3:30 PM same day before COB). Periodic tasks alert next morning at 9:00 AM with a 24-hour resolution SLA."),
        ("Test 8 — Anti-Duplication & Idempotency", "Enforces LockService concurrency locks and atomic timestamp guards (Manager_Alert_Sent_At, Next_Cycle_Generated). Running the engine 3 times back-to-back verifies exactly 0 duplicate alerts and 0 duplicate cycles.")
    ]

    for title, desc in tests:
        story.append(Paragraph(f"• <b>{title}:</b> {desc}", bullet_style))
        story.append(Spacer(1, 2))

    story.append(Spacer(1, 8))

    # Section 4: Daily Task Strategy
    story.append(Paragraph("4. DAILY TASK TRACKING METHODOLOGY (TEST 3 IN-DEPTH)", h1_style))
    story.append(Paragraph(
        "<b>The Challenge:</b> Daily operational actions (such as posting morning dispatches in a WhatsApp group) do not natively produce portal ticket IDs. "
        "A simple yes/no checkbox invites dishonest ticking, while full API bots cost significant monthly tooling spend.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Our 2-Phase Operational Strategy:</b><br/>"
        "1. <b>Immediate Protocol (Implemented):</b> The employee pastes `[Timestamp] - [Message Summary Snippet]` into Column H of the Workbench. "
        "This takes under 15 seconds, creates an audit log entry, and enables the manager to spot-check against the WhatsApp group in seconds.<br/>"
        "2. <b>Enterprise Evolution Path:</b> As volume grows, a webhook listener (Twilio/WhatsApp Cloud API) can intercept `#OPS_STANDUP_DONE` hashtags in the group and post directly to the Apps Script doGet/doPost endpoint, achieving zero-touch automation.",
        body_style
    ))
    story.append(Spacer(1, 8))

    # Section 5: Golden Interview Q&A
    story.append(Paragraph("5. GOLDEN INTERVIEW PREPARATION (EXACT FOUNDER QUESTIONS & ANSWERS)", h1_style))
    
    qa_list = [
        ("Q1: Why did you build an Employee Workbench instead of letting team members edit Active_Tasks directly?",
         "Answer: Direct master editing creates human error and duplication. When 4 employees edit a 20-column table simultaneously, formulas get broken and rows overwritten. The Workbench acts like a clean front-end filter—employees see only their tasks, enter proof in a dedicated green cell, click Submit, and the system handles the database and cycle generation in the background with zero duplicate work."),
        
        ("Q2: How does the system guarantee zero duplicate alert emails or cycle generations?",
         "Answer: Through two enterprise-grade safeguards: First, script concurrency locking using Google Apps Script's LockService.getScriptLock(), which queues requests and prevents race conditions. Second, atomic timestamp guards (Manager_Alert_Sent_At, Leadership_Escalation_Sent_At, Next_Cycle_Generated). Once a flag is stamped, subsequent scans immediately ignore the record."),
         
        ("Q3: How does your architecture specifically reduce founder dependency?",
         "Answer: Before this system, any delay caused the employee to go to the founder or the founder to hunt for updates. Our architecture introduces an automated 2-tier SLA shield: the system alerts the manager first with a 1-click email action button. The founder is only notified if the manager neglects their 4-hour SLA or if the task remains unresolved beyond critical thresholds. Routine issues stay at the operational tier."),

        ("Q4: What happens if a daily task falls on a Friday or weekend?",
         "Answer: The recurrence engine incorporates working-day intelligence. When a daily task is completed on Friday, the calculateNextDueDate function automatically skips Saturday and Sunday, setting the next cycle due date for Monday morning at 11:00 AM, maintaining realistic operational cadences.")
    ]

    for q, a in qa_list:
        story.append(Paragraph(q, qa_q))
        story.append(Paragraph(a, qa_a))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"✅ Generated Master Guide PDF: {filename}")

if __name__ == '__main__':
    build_guide_pdf()
