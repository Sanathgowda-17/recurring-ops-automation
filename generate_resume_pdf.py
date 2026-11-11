#!/usr/bin/env python3
"""
generate_resume_pdf.py
Generates an ATS-compliant, pixel-perfect, beautifully aligned 1-page PDF resume
for Sanath S Gowda:
- Perfectly aligned 2-column item headers (Title/Stack on left, Date/Links on right)
- Hanging bullet indentations so wrapped lines never sit under the bullet dot
- Vertically aligned Technical Skills table
- Perfectly centered, balanced contact information and section banners
- Exactly 1 page on Letter size
"""

import os
import sys

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Flowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

class SectionBanner(Flowable):
    """
    Renders a clean, rounded grey pill banner with vertically and horizontally
    centered section text matching the executive ATS standard.
    """
    def __init__(self, text, width=548, height=15.5, bg_color=colors.HexColor("#E5E7EB"), text_color=colors.HexColor("#1F2937")):
        super().__init__()
        self.text = text
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.text_color = text_color

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        return self.width, self.height

    def draw(self):
        self.canv.saveState()
        self.canv.setFillColor(self.bg_color)
        self.canv.setStrokeColor(self.bg_color)
        self.canv.roundRect(0, 0, self.width, self.height, radius=3.5, stroke=0, fill=1)
        self.canv.setFillColor(self.text_color)
        self.canv.setFont("Helvetica-Bold", 9)
        # Vertically centered: baseline at 4.5 pt for 15.5 pt height
        self.canv.drawCentredString(self.width / 2.0, 4.5, self.text)
        self.canv.restoreState()

def build_pdf(filename="Sanath_S_Gowda_Resume.pdf"):
    # Target 1-page Letter (8.5 x 11 in = 612 x 792 pt)
    # Margins: 32 pt left/right -> 548 pt printable width
    content_width = 612 - (2 * 32)
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=32,
        rightMargin=32,
        topMargin=20,
        bottomMargin=18
    )

    styles = getSampleStyleSheet()

    # Color definitions
    DARK_TEXT = colors.HexColor("#111827")   # Gray 900
    MUTED_TEXT = colors.HexColor("#4B5563")  # Gray 600
    BLUE_LINK = colors.HexColor("#1D4ED8")   # Blue 700

    name_style = ParagraphStyle(
        'NameStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=19,
        leading=21,
        alignment=TA_CENTER,
        textColor=DARK_TEXT
    )

    contact_style = ParagraphStyle(
        'ContactStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.2,
        leading=10.5,
        alignment=TA_CENTER,
        textColor=DARK_TEXT
    )

    summary_style = ParagraphStyle(
        'SummaryStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.2,
        leading=10.8,
        textColor=DARK_TEXT,
        alignment=TA_JUSTIFY
    )

    # Bullet with hanging indent: leftIndent=12, firstLineIndent=-12
    bullet_style = ParagraphStyle(
        'BulletHanging',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.1,
        leading=10.4,
        textColor=DARK_TEXT,
        alignment=TA_LEFT,
        leftIndent=11,
        firstLineIndent=-11,
        spaceAfter=1.5
    )

    item_left_bold = ParagraphStyle(
        'ItemLeftBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=10.8,
        textColor=DARK_TEXT
    )

    item_left_sub = ParagraphStyle(
        'ItemLeftSub',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.0,
        leading=10.2,
        textColor=MUTED_TEXT
    )

    item_right_bold = ParagraphStyle(
        'ItemRightBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.2,
        leading=10.8,
        alignment=TA_RIGHT,
        textColor=DARK_TEXT
    )

    item_right_sub = ParagraphStyle(
        'ItemRightSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.0,
        leading=10.2,
        alignment=TA_RIGHT,
        textColor=MUTED_TEXT
    )

    skill_label_style = ParagraphStyle(
        'SkillLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.2,
        leading=10.6,
        textColor=DARK_TEXT
    )

    skill_val_style = ParagraphStyle(
        'SkillVal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.2,
        leading=10.6,
        textColor=DARK_TEXT
    )

    elements = []

    # =========================================================================
    # 1. Header
    # =========================================================================
    elements.append(Paragraph("SANATH S GOWDA", name_style))
    elements.append(Spacer(1, 2.5))
    contact_line = (
        '+91 9945816437 &nbsp;&bull;&nbsp; '
        '<font color="#1D4ED8"><a href="mailto:1mp22cs046@gmail.com"><u>1mp22cs046@gmail.com</u></a></font> &nbsp;&bull;&nbsp; '
        '<font color="#1D4ED8"><a href="https://linkedin.com/in/sanath-s-gowda-4265222aa"><u>linkedin.com/in/sanath-s-gowda</u></a></font> &nbsp;&bull;&nbsp; '
        '<font color="#1D4ED8"><a href="https://sanathgowda.vercel.app"><u>sanathgowda.vercel.app</u></a></font> &nbsp;&bull;&nbsp; '
        '<font color="#1D4ED8"><a href="https://github.com/Sanathgowda-17"><u>github.com/Sanathgowda-17</u></a></font>'
    )
    elements.append(Paragraph(contact_line, contact_style))
    elements.append(Spacer(1, 5))

    # =========================================================================
    # 2. Summary
    # =========================================================================
    elements.append(SectionBanner("SUMMARY", width=content_width))
    elements.append(Spacer(1, 3.5))
    summary_text = (
        "Software Developer and Computer Science graduate with hands-on experience in full-stack application development, "
        "scalable backend architectures, and high-performance distributed systems. Proficient in Python, Java, JavaScript, and SQL, "
        "with demonstrated experience engineering high-throughput REST and WebSocket APIs (FastAPI), interactive frontends "
        "(React Native), and cloud databases (Firestore, MySQL). State-level KSCST engineering grant recipient and 2x hackathon winner "
        "committed to developing clean, robust, and impactful production software."
    )
    elements.append(Paragraph(summary_text, summary_style))
    elements.append(Spacer(1, 4.5))

    # =========================================================================
    # 3. Experience
    # =========================================================================
    elements.append(SectionBanner("EXPERIENCE", width=content_width))
    elements.append(Spacer(1, 3))

    exp_data = [
        [
            Paragraph("<b>Android and Generative AI Intern</b> &nbsp;|&nbsp; MindMatrix / CL Infotech Pvt. Ltd.", item_left_bold),
            Paragraph("Feb 2026 – May 2026", item_right_bold)
        ],
        [
            Paragraph("<i>Mobile Architecture &amp; Cloud Integration</i>", item_left_sub),
            Paragraph("Bengaluru, India", item_right_sub)
        ]
    ]
    t_exp = Table(exp_data, colWidths=[content_width - 130, 130])
    t_exp.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(t_exp)
    elements.append(Spacer(1, 2))

    elements.append(Paragraph("&bull;&nbsp;&nbsp;Engineered production mobile application modules using Kotlin and Jetpack Compose under MVVM architecture, ensuring smooth 60 FPS UI performance.", bullet_style))
    elements.append(Paragraph("&bull;&nbsp;&nbsp;Architected backend API integrations with Google Cloud and AI services, implementing asynchronous request pipelines and resilient error recovery.", bullet_style))
    elements.append(Paragraph("&bull;&nbsp;&nbsp;Designed scalable Cloud Firestore NoSQL schemas and Firebase Authentication workflows, authoring unit and integration test suites that reduced sprint bug rates by 35%.", bullet_style))
    elements.append(Spacer(1, 4.5))

    # =========================================================================
    # 4. Projects
    # =========================================================================
    elements.append(SectionBanner("PROJECTS", width=content_width))
    elements.append(Spacer(1, 3))

    # Helper for project headers
    def make_project_header(title, tech_stack, links_html, date_text):
        data = [
            [
                Paragraph(f"<b>{title}</b>", item_left_bold),
                Paragraph(f"{date_text} &nbsp;|&nbsp; {links_html}", item_right_bold)
            ],
            [
                Paragraph(f"<i>{tech_stack}</i>", item_left_sub),
                Paragraph("", item_right_sub)
            ]
        ]
        t = Table(data, colWidths=[content_width - 150, 150])
        t.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        return t

    # Project 1: Upadha AI
    p1_links = '<font color="#1D4ED8"><a href="https://upadha-ai.onrender.com"><u>Live App</u></a></font> &bull; <font color="#1D4ED8"><a href="https://github.com/Sanathgowda-17/upadha-ai"><u>GitHub</u></a></font>'
    elements.append(make_project_header("Upadha AI — Kautilya's Test of Statecraft", "Node.js, Gemini Vision OCR, Turso Cloud (libSQL), Capacitor SDK, SSE, PWA", p1_links, "2026"))
    elements.append(Spacer(1, 1.5))
    elements.append(Paragraph("&bull;&nbsp;&nbsp;Architected a production full-stack edtech platform evaluating UPSC CSE mains answers with real-time SSE streaming, multi-page handwriting OCR, Topper visual diff, and Dholpur House DAF interview simulation (275-mark rubric).", bullet_style))
    elements.append(Paragraph("&bull;&nbsp;&nbsp;Engineered a resilient dual-mode database pairing Turso Cloud SQLite (libSQL) in AWS Mumbai with local SQLite fallback for 100% uptime; packaged standalone Android APK with Capacitor and deployed live on Render.", bullet_style))
    elements.append(Spacer(1, 3.5))

    # Project 2: Fitness Assistant
    p2_links = '<font color="#1D4ED8"><a href="https://github.com/Sanathgowda-17"><u>GitHub</u></a></font>'
    elements.append(make_project_header("Intelligent Fitness Assistant", "Python, FastAPI, WebSockets, MediaPipe, OpenCV, React Native, Cloud Firestore", p2_links, "2025–2026"))
    elements.append(Paragraph("<i>Recipient – KSCST State Engineering Research Grant, 49th Series Student Project Programme</i>", item_left_sub))
    elements.append(Spacer(1, 1.5))
    elements.append(Paragraph("&bull;&nbsp;&nbsp;Built an end-to-end computer vision and pose tracking system using MediaPipe Pose to evaluate 33 skeletal landmarks with 94%+ accuracy.", bullet_style))
    elements.append(Paragraph("&bull;&nbsp;&nbsp;Developed full-stack mobile client and FastAPI backend enabling sub-100ms bi-directional WebSocket telemetry with asynchronous LLM form correction.", bullet_style))
    elements.append(Spacer(1, 3.5))

    # Project 3: Operations Automation Engine
    p3_links = '<font color="#1D4ED8"><a href="https://github.com/Sanathgowda-17"><u>GitHub</u></a></font>'
    elements.append(make_project_header("Automated Recurring Operations &amp; Escalation Engine", "Google Apps Script, Webhooks, HTML/CSS, REST APIs, LockService Concurrency", p3_links, "2026"))
    elements.append(Spacer(1, 1.5))
    elements.append(Paragraph("&bull;&nbsp;&nbsp;Engineered an enterprise scheduling engine managing recurring task lifecycles (Daily, 7d, 15d, 30d) with business-day calculation algorithms and automated rollover.", bullet_style))
    elements.append(Paragraph("&bull;&nbsp;&nbsp;Built centralized Employee Workbench interface and multi-tiered SLA escalation engine with LockService concurrency, eliminating 100% of reporting redundancy.", bullet_style))
    elements.append(Spacer(1, 4.5))

    # =========================================================================
    # 5. Technical Skills
    # =========================================================================
    elements.append(SectionBanner("TECHNICAL SKILLS", width=content_width))
    elements.append(Spacer(1, 3))

    skills_data = [
        [
            Paragraph("<b>Languages:</b>", skill_label_style),
            Paragraph("Python, Java, JavaScript (ES6+), C, C++, SQL, HTML5/CSS3", skill_val_style)
        ],
        [
            Paragraph("<b>Libraries &amp; Frameworks:</b>", skill_label_style),
            Paragraph("Node.js, FastAPI, React Native, Expo, Jetpack Compose, MediaPipe, OpenCV, Pydantic, Capacitor, AsyncIO", skill_val_style)
        ],
        [
            Paragraph("<b>Tools &amp; Platforms:</b>", skill_label_style),
            Paragraph("Turso Cloud (libSQL), MySQL, PostgreSQL, Cloud Firestore, Firebase, Android Studio, Git, Postman, Linux, Render", skill_val_style)
        ]
    ]
    t_skills = Table(skills_data, colWidths=[125, content_width - 125])
    t_skills.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(t_skills)
    elements.append(Spacer(1, 4.5))

    # =========================================================================
    # 6. Achievements & Certifications
    # =========================================================================
    elements.append(SectionBanner("ACHIEVEMENTS & CERTIFICATIONS", width=content_width))
    elements.append(Spacer(1, 3))
    elements.append(Paragraph("&bull;&nbsp;&nbsp;<b>KSCST State Research Grant:</b> Awarded competitive research grant for Intelligent Fitness Assistant under 49th Series SPP.", bullet_style))
    elements.append(Paragraph("&bull;&nbsp;&nbsp;<b>Runner-up, Cyber Security Hackathon:</b> SIT (competed among 45+ collegiate engineering teams on secure system architecture).", bullet_style))
    elements.append(Paragraph("&bull;&nbsp;&nbsp;<b>Top Finalist, Ideathon:</b> BIT (recognized for assistive computer vision architecture and interactive product usability).", bullet_style))
    elements.append(Paragraph("&bull;&nbsp;&nbsp;<b>Software Testing (Elite Certification):</b> NPTEL — Verification, Validation, Unit Testing, TDD &amp; Test Coverage.", bullet_style))
    elements.append(Spacer(1, 4.5))

    # =========================================================================
    # 7. Education
    # =========================================================================
    elements.append(SectionBanner("EDUCATION", width=content_width))
    elements.append(Spacer(1, 3))

    edu_left_bold = ParagraphStyle(
        'EduLeftBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=10.8,
        textColor=DARK_TEXT
    )

    edu_right = ParagraphStyle(
        'EduRight',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.2,
        leading=10.8,
        alignment=TA_RIGHT,
        textColor=DARK_TEXT
    )

    edu_left_sub = ParagraphStyle(
        'EduLeftSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.1,
        leading=10.4,
        textColor=DARK_TEXT
    )

    edu_coursework_style = ParagraphStyle(
        'EduCoursework',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.0,
        leading=10.2,
        textColor=MUTED_TEXT,
        alignment=TA_LEFT
    )

    edu1_data = [
        [
            Paragraph("<b>BGS College Of Engineering And Technology</b>", edu_left_bold),
            Paragraph("Bengaluru, India", edu_right)
        ],
        [
            Paragraph("B.E. in Computer Science &amp; Engineering &nbsp;|&nbsp; <b>8.00 CGPA</b>", edu_left_sub),
            Paragraph("<b>2022–2026</b>", edu_right)
        ],
        [
            Paragraph("<b>Relevant Coursework:</b> Data Structures &amp; Algorithms, OOP, DBMS, Operating Systems, Computer Networks, Software Engineering", edu_coursework_style),
            Paragraph("", edu_right)
        ],
    ]
    t_edu1 = Table(edu1_data, colWidths=[content_width - 110, 110])
    t_edu1.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('SPAN', (0,2), (1,2)),
    ]))
    elements.append(t_edu1)

    # Build PDF
    doc.build(elements)
    print(f"Generated PDF: {filename}")

if __name__ == '__main__':
    build_pdf()
