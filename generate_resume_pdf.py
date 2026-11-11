#!/usr/bin/env python3
"""
generate_resume_pdf.py
Generates an ATS-compliant, pixel-perfect 1-page PDF resume for Sanath S Gowda
matching the exact design and structure of Rakshan R Rao's resume:
- Centered bold header with web link
- Rounded grey pill/banner section headers (SUMMARY, EXPERIENCE, PROJECTS, TECHNICAL SKILLS, EDUCATION)
- Clean typography, high-impact bullets, and clickable hyperlinks.
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
    Renders a soft-grey rounded rectangle banner with centered bold text,
    matching Rakshan's section header style.
    """
    def __init__(self, text, width=540, height=17, bg_color=colors.HexColor("#E5E7EB"), text_color=colors.HexColor("#1F2937")):
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
        # Rounded rectangle: radius 4pt
        self.canv.roundRect(0, 0, self.width, self.height, radius=4, stroke=0, fill=1)
        self.canv.setFillColor(self.text_color)
        self.canv.setFont("Helvetica-Bold", 9.5)
        self.canv.drawCentredString(self.width / 2.0, 4.5, self.text)
        self.canv.restoreState()

def build_pdf(filename="Sanath_S_Gowda_Resume.pdf"):
    # Target 1-page Letter (8.5 x 11 in = 612 x 792 pt)
    # Margins: 32 pt left/right, 24 pt top/bottom
    content_width = 612 - (2 * 32) # 548 pt
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=32,
        rightMargin=32,
        topMargin=22,
        bottomMargin=20
    )

    styles = getSampleStyleSheet()

    # Color definitions
    DARK_TEXT = colors.HexColor("#111827")   # Gray 900
    MUTED_TEXT = colors.HexColor("#4B5563")  # Gray 600
    LINK_COLOR = colors.HexColor("#1D4ED8")  # Blue 700

    name_style = ParagraphStyle(
        'NameStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=22,
        alignment=TA_CENTER,
        textColor=DARK_TEXT
    )

    contact_style = ParagraphStyle(
        'ContactStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.3,
        leading=11,
        alignment=TA_CENTER,
        textColor=MUTED_TEXT
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.3,
        leading=10.8,
        textColor=DARK_TEXT,
        alignment=TA_LEFT
    )

    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.2,
        leading=10.5,
        textColor=DARK_TEXT,
        alignment=TA_LEFT,
        leftIndent=8
    )

    item_title_style = ParagraphStyle(
        'ItemTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.6,
        leading=11.2,
        textColor=DARK_TEXT
    )

    item_sub_style = ParagraphStyle(
        'ItemSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.2,
        leading=10.5,
        textColor=MUTED_TEXT
    )

    edu_left_bold = ParagraphStyle(
        'EduLeftBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.4,
        leading=11,
        textColor=DARK_TEXT
    )

    edu_right = ParagraphStyle(
        'EduRight',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.4,
        leading=11,
        alignment=TA_RIGHT,
        textColor=MUTED_TEXT
    )

    edu_left_sub = ParagraphStyle(
        'EduLeftSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.2,
        leading=10.5,
        textColor=DARK_TEXT
    )

    elements = []

    # 1. Header
    elements.append(Paragraph("SANATH S GOWDA", name_style))
    elements.append(Spacer(1, 3))
    contact_line = (
        '+91 9945816437 &nbsp;|&nbsp; '
        '<font color="#1D4ED8"><a href="mailto:1mp22cs046@gmail.com"><u>1mp22cs046@gmail.com</u></a></font> &nbsp;|&nbsp; '
        '<font color="#1D4ED8"><a href="https://linkedin.com/in/sanath-s-gowda-4265222aa"><u>linkedin.com/in/sanath-s-gowda-4265222aa</u></a></font> &nbsp;|&nbsp; '
        '<font color="#1D4ED8"><a href="https://sanathgowda.vercel.app"><u>https://sanathgowda.vercel.app</u></a></font>'
    )
    elements.append(Paragraph(contact_line, contact_style))
    elements.append(Spacer(1, 6))

    # 2. SUMMARY
    elements.append(SectionBanner("SUMMARY", width=content_width))
    elements.append(Spacer(1, 4))
    summary_text = (
        "Software Developer and Computer Science graduate with hands-on experience in full-stack application development, "
        "scalable backend architectures, and high-performance distributed systems. Proficient in Python, Java, JavaScript, and SQL, "
        "with demonstrated experience engineering high-throughput REST and WebSocket APIs (FastAPI), interactive frontends "
        "(React Native), and cloud databases (Firestore, MySQL). State-level KSCST engineering grant recipient and 2x hackathon winner "
        "committed to developing clean, robust, and impactful production software."
    )
    elements.append(Paragraph(summary_text, body_style))
    elements.append(Spacer(1, 6))

    # 3. EXPERIENCE
    elements.append(SectionBanner("EXPERIENCE", width=content_width))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("<b>Android and Generative AI Intern – MindMatrix / CL Infotech Pvt. Ltd.</b>", item_title_style))
    elements.append(Paragraph("Bengaluru | Feb 2026 – May 2026", item_sub_style))
    elements.append(Spacer(1, 1.5))
    exp_desc = (
        "Engineered production mobile application modules using Kotlin and Jetpack Compose under MVVM architecture, ensuring smooth "
        "60 FPS UI performance. Architected backend API integrations with Google Cloud and AI services, implementing asynchronous "
        "request pipelines and resilient error recovery. Designed scalable Cloud Firestore NoSQL schemas and Firebase Authentication workflows, "
        "authoring unit and integration test suites that reduced sprint bug rates by 35% in a live production environment."
    )
    elements.append(Paragraph(exp_desc, body_style))
    elements.append(Spacer(1, 6))

    # 4. PROJECTS
    elements.append(SectionBanner("PROJECTS", width=content_width))
    elements.append(Spacer(1, 4))

    # Project 1: Fitness Assistant
    p1_title = (
        "<b>Intelligent Fitness Assistant</b> | Python, FastAPI, WebSockets, MediaPipe, OpenCV, React Native | "
        '<font color="#1D4ED8"><a href="https://github.com/Sanathgowda-17"><u>Github Link</u></a></font>'
    )
    elements.append(Paragraph(p1_title, item_title_style))
    elements.append(Paragraph("<i>Recipient – KSCST State Engineering Research Grant, 49th Series Student Project Programme</i>", item_sub_style))
    elements.append(Spacer(1, 1))
    elements.append(Paragraph("• Built an end-to-end computer vision and pose tracking system using MediaPipe Pose to evaluate 33 skeletal landmarks with 94%+ accuracy.", bullet_style))
    elements.append(Paragraph("• Developed full-stack mobile client and FastAPI backend enabling sub-100ms bi-directional WebSocket telemetry with asynchronous LLM form correction.", bullet_style))
    elements.append(Spacer(1, 4))

    # Project 2: Operations Automation Engine
    p2_title = (
        "<b>Automated Recurring Operations &amp; Escalation Engine</b> | Google Apps Script, Webhooks, HTML/CSS, REST | "
        '<font color="#1D4ED8"><a href="https://github.com/Sanathgowda-17"><u>Github Link</u></a></font>'
    )
    elements.append(Paragraph(p2_title, item_title_style))
    elements.append(Spacer(1, 1))
    elements.append(Paragraph("• Engineered an enterprise scheduling engine managing recurring task lifecycles (Daily, 7d, 15d, 30d) with business-day calculation algorithms and automated rollover.", bullet_style))
    elements.append(Paragraph("• Built centralized Employee Workbench interface and multi-tiered SLA escalation engine with LockService concurrency, eliminating 100% of reporting redundancy.", bullet_style))
    elements.append(Spacer(1, 4))

    # Project 3: Conversational Customer Service AI Agent
    p3_title = (
        "<b>Conversational Customer Service AI Agent</b> | Python, FastAPI, NLP, Vector Embeddings, Pydantic | "
        '<font color="#1D4ED8"><a href="https://github.com/Sanathgowda-17"><u>Github Link</u></a></font>'
    )
    elements.append(Paragraph(p3_title, item_title_style))
    elements.append(Spacer(1, 1))
    elements.append(Paragraph("• Developed high-throughput RESTful backend services using FastAPI and Python to process multi-intent customer queries with sub-second response latency.", bullet_style))
    elements.append(Paragraph("• Implemented semantic search and vector retrieval pipelines with schema validation and in-memory caching, accelerating resolution speed by 60%.", bullet_style))
    elements.append(Spacer(1, 6))

    # 5. TECHNICAL SKILLS
    elements.append(SectionBanner("TECHNICAL SKILLS", width=content_width))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("<b>Languages:</b> Python, Java, JavaScript (ES6+), C, C++, SQL, HTML5/CSS3", body_style))
    elements.append(Spacer(1, 1.5))
    elements.append(Paragraph("<b>Libraries &amp; Frameworks:</b> FastAPI, React Native, Expo, Jetpack Compose, MediaPipe, OpenCV, Pydantic, Scikit-learn, AsyncIO", body_style))
    elements.append(Spacer(1, 1.5))
    elements.append(Paragraph("<b>Tools &amp; Platforms:</b> MySQL, PostgreSQL, Cloud Firestore, Firebase, Microsoft Azure, Google Apps Script, Git, Postman, Linux", body_style))
    elements.append(Spacer(1, 6))

    # 6. ACHIEVEMENTS & CERTIFICATIONS
    elements.append(SectionBanner("ACHIEVEMENTS & CERTIFICATIONS", width=content_width))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("• <b>KSCST State Research Grant:</b> Awarded competitive research grant for Intelligent Fitness Assistant under 49th Series SPP.", bullet_style))
    elements.append(Paragraph("• <b>Runner-up, Cyber Security Hackathon:</b> SIT (competed among 45+ collegiate engineering teams on secure system architecture).", bullet_style))
    elements.append(Paragraph("• <b>Top Finalist, Ideathon:</b> BIT (recognized for assistive computer vision architecture and interactive product usability).", bullet_style))
    elements.append(Paragraph("• <b>Software Testing (Elite Certification):</b> NPTEL — Verification, Validation, Unit Testing, TDD &amp; Test Coverage.", bullet_style))
    elements.append(Spacer(1, 6))

    # 7. EDUCATION
    elements.append(SectionBanner("EDUCATION", width=content_width))
    elements.append(Spacer(1, 4))

    edu_coursework_style = ParagraphStyle(
        'EduCoursework',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.2,
        leading=10.5,
        textColor=DARK_TEXT,
        alignment=TA_LEFT,
        leftIndent=0
    )

    edu1_data = [
        [Paragraph("<b>BGS College Of Engineering And Technology</b>", edu_left_bold), Paragraph("Bengaluru", edu_right)],
        [Paragraph("B.E (Computer Science And Engineering) | 8.00 CGPA", edu_left_sub), Paragraph("2022–2026", edu_right)],
        [Paragraph("<b>Relevant Coursework:</b> Data Structures &amp; Algorithms, OOP, DBMS, Operating Systems, Computer Networks, Software Engineering", edu_coursework_style), Paragraph("", edu_right)],
    ]
    t_edu1 = Table(edu1_data, colWidths=[content_width - 80, 80])
    t_edu1.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('SPAN', (0,2), (1,2)), # Span across full width
    ]))
    elements.append(t_edu1)

    # Build PDF
    doc.build(elements)
    print(f"Generated PDF: {filename}")

if __name__ == '__main__':
    build_pdf()
