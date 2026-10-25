#!/usr/bin/env python3
"""
generate_resume_pdf.py
Generates an ATS-compliant, pixel-perfect 1-page PDF resume for Sanath S Gowda.
Uses ReportLab with custom layout, tight margins, and modern typography.
"""

import os
import sys

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

def build_pdf(filename="Sanath_S_Gowda_Resume.pdf"):
    # Target 1-page Letter (8.5 x 11 in) with 0.38 in margins
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=26,
        rightMargin=26,
        topMargin=22,
        bottomMargin=22
    )

    styles = getSampleStyleSheet()
    
    # Custom palette
    PRIMARY = colors.HexColor("#0f172a")    # Slate 900
    ACCENT = colors.HexColor("#1e40af")     # Blue 800
    TEXT_DARK = colors.HexColor("#1e293b")  # Slate 800
    TEXT_MUTED = colors.HexColor("#475569") # Slate 600
    BORDER_CLR = colors.HexColor("#cbd5e1") # Slate 300

    # Typography styles
    name_style = ParagraphStyle(
        'NameStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=20,
        alignment=TA_CENTER,
        textColor=PRIMARY
    )

    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=11.5,
        alignment=TA_CENTER,
        textColor=ACCENT
    )

    contact_style = ParagraphStyle(
        'ContactStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.2,
        leading=10.5,
        alignment=TA_CENTER,
        textColor=TEXT_MUTED
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=11,
        textColor=ACCENT,
        spaceBefore=0,
        spaceAfter=0
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.2,
        leading=10.2,
        textColor=TEXT_DARK,
        alignment=TA_JUSTIFY
    )

    bold_label = ParagraphStyle(
        'BoldLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.2,
        leading=10.2,
        textColor=TEXT_DARK
    )

    job_title = ParagraphStyle(
        'JobTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=10.5,
        textColor=PRIMARY
    )

    job_date = ParagraphStyle(
        'JobDate',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.2,
        leading=10.5,
        alignment=TA_RIGHT,
        textColor=TEXT_MUTED
    )

    bullet_style = ParagraphStyle(
        'BulletText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.0,
        leading=9.8,
        textColor=TEXT_DARK,
        alignment=TA_JUSTIFY,
        leftIndent=11
    )

    elements = []

    # 1. Header
    elements.append(Paragraph("SANATH S GOWDA", name_style))
    elements.append(Spacer(1, 2))
    elements.append(Paragraph("Computer Science & Engineering Graduate | Software Development | AI & Computer Vision", subtitle_style))
    elements.append(Spacer(1, 2))
    contact_text = (
        'Bengaluru, Karnataka, India &nbsp;|&nbsp; +91 9945816437 &nbsp;|&nbsp; '
        '<font color="#1e40af"><u>1mp22cs046@gmail.com</u></font> &nbsp;|&nbsp; '
        '<font color="#1e40af"><u>linkedin.com/in/sanath-s-gowda-4265222aa</u></font> &nbsp;|&nbsp; '
        '<font color="#1e40af"><u>github.com/Sanathgowda-17</u></font>'
    )
    elements.append(Paragraph(contact_text, contact_style))
    elements.append(Spacer(1, 4))
    elements.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=0, spaceAfter=4))

    # Helper for Section Headers
    def add_section(title):
        t = Table(
            [[Paragraph(title, section_heading)]],
            colWidths=[560]
        )
        t.setStyle(TableStyle([
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
            ('TOPPADDING', (0,0), (-1,-1), 1),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('LINEBELOW', (0,0), (-1,-1), 0.75, ACCENT),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 3))

    # 2. Professional Summary
    add_section("PROFESSIONAL SUMMARY")
    summary_text = (
        "Computer Science & Engineering graduate specializing in applied AI, full-stack systems, and automated operations. "
        "Hands-on experience architecting real-time mobile/web applications (FastAPI, React Native, WebSockets) and integrating "
        "computer vision (MediaPipe, OpenCV) with Generative AI (Gemini/OpenAI APIs). Selected for state-level KSCST student sponsorship "
        "and winner/runner-up in 2 competitive hackathons. Proven ability to build low-latency, scalable solutions."
    )
    elements.append(Paragraph(summary_text, body_style))
    elements.append(Spacer(1, 4))

    # 3. Education
    add_section("EDUCATION")
    edu_row = [
        Paragraph("<b>B.E. in Computer Science & Engineering</b> — BGS College of Engineering and Technology, Bengaluru", bold_label),
        Paragraph("<b>2022 – 2026</b> | CGPA: <b>8.00 / 10</b>", job_date)
    ]
    edu_table = Table([edu_row], colWidths=[400, 160])
    edu_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(edu_table)
    elements.append(Spacer(1, 4))

    # 4. Technical Skills
    add_section("TECHNICAL SKILLS")
    skills = [
        ("• Languages:", "Python, JavaScript (ES6+), Kotlin, C, SQL"),
        ("• Frameworks & Libraries:", "FastAPI, React Native, Expo, Jetpack Compose, MediaPipe, OpenCV, NumPy"),
        ("• AI & Generative AI:", "LLM APIs (Google Gemini, OpenAI), Prompt Engineering, Pose Estimation, Real-time CV"),
        ("• Backend & Cloud:", "WebSockets, RESTful APIs, Webhooks, Cloud Firestore, Firebase Auth, Firebase Storage, MySQL"),
        ("• Tools & Automation:", "Git, GitHub, Postman, Google Apps Script, Google Workspace Automation, VS Code, Android Studio")
    ]
    skill_rows = []
    for lbl, val in skills:
        skill_rows.append([Paragraph(f"<b>{lbl}</b>", bold_label), Paragraph(val, body_style)])
    
    st = Table(skill_rows, colWidths=[130, 430])
    st.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 0.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0.5),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(st)
    elements.append(Spacer(1, 4))

    # 5. Internship Experience
    add_section("INTERNSHIP EXPERIENCE")
    exp_header = [
        Paragraph("<b>Android & Generative AI Software Intern</b> | MindMatrix / CL Infotech Pvt. Ltd.", job_title),
        Paragraph("<b>Feb 2026 – May 2026</b>", job_date)
    ]
    exp_table = Table([exp_header], colWidths=[420, 140])
    exp_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(exp_table)
    
    exp_bullets = [
        "• Engineered Android feature workflows using Kotlin and Jetpack Compose, achieving smooth 60 FPS UI rendering.",
        "• Explored and integrated Generative AI capabilities via Google AI Studio and Cloud APIs to deliver context-aware user experiences.",
        "• Structured Firebase Authentication and Cloud Firestore schemas; implemented structured tests reducing sprint bug rates by 35%."
    ]
    for b in exp_bullets:
        elements.append(Paragraph(b, bullet_style))
    elements.append(Spacer(1, 4))

    # 6. Projects
    add_section("PROJECTS")

    # Project 1: Fitness Assistant
    p1_head = [
        Paragraph("<b>An Intelligent Fitness Assistant</b> | <i>React Native, FastAPI, MediaPipe, OpenCV, Gemini API, Firestore</i>", job_title),
        Paragraph("<b>Major Project (2025–26)</b>", job_date)
    ]
    t1 = Table([p1_head], colWidths=[440, 120])
    t1.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(t1)
    elements.append(Paragraph("• Co-developed a cross-platform mobile system combining real-time pose estimation, rep tracking, and AI coaching via WebSockets.", bullet_style))
    elements.append(Paragraph("• Utilized MediaPipe Pose to track 33 landmarks and calculate joint angles across squats/push-ups, reaching 94%+ posture accuracy.", bullet_style))
    elements.append(Paragraph("• Integrated Google Gemini / OpenAI APIs with custom prompt engineering for adaptive real-time guidance; funded by KSCST (SPP).", bullet_style))
    elements.append(Spacer(1, 3))

    # Project 2: Operations Automation Engine
    p2_head = [
        Paragraph("<b>Automated Recurring Operations & Escalation Engine</b> | <i>Google Apps Script, Webhooks, HTML/CSS</i>", job_title),
        Paragraph("<b>2026</b>", job_date)
    ]
    t2 = Table([p2_head], colWidths=[440, 120])
    t2.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(t2)
    elements.append(Paragraph("• Built an enterprise recurrence engine automating cycle rollover across Daily, 7d, 15d, and 30d periods with working-day intelligence.", bullet_style))
    elements.append(Paragraph("• Created a single-point Employee Workbench with filtered views, eliminating 100% of duplicated multi-sheet manual reporting.", bullet_style))
    elements.append(Paragraph("• Deployed multi-tiered SLA logic with same-day manager alert emails, 1-click Web App acknowledgement, and executive escalation.", bullet_style))
    elements.append(Paragraph("• Enforced LockService concurrency controls and timestamp idempotency guards, ensuring 0 duplicate cycles or notification spam.", bullet_style))
    elements.append(Spacer(1, 3))

    # Project 3: Conversational AI Agent
    p3_head = [
        Paragraph("<b>Conversational Customer Service AI Agent</b> | <i>Python, FastAPI, NLP / LLM Embeddings, REST APIs</i>", job_title),
        Paragraph("<b>2025</b>", job_date)
    ]
    t3 = Table([p3_head], colWidths=[440, 120])
    t3.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(t3)
    elements.append(Paragraph("• Built an intelligent customer support assistant handling multi-intent queries with dynamic context retrieval and 60% faster resolution.", bullet_style))
    elements.append(Spacer(1, 4))

    # 7. Achievements & Awards
    add_section("ACHIEVEMENTS & AWARDS")
    achievements = [
        "• <b>Runner-up:</b> Cyber Security Hackathon, SIT (competed among 45+ collegiate teams).",
        "• <b>Top Finalist:</b> Ideathon, BIT, recognized for assistive technology architecture.",
        "• <b>KSCST State Sponsorship (2025–26):</b> Awarded research grant for Intelligent Fitness Assistant under 49th Series SPP."
    ]
    for a in achievements:
        elements.append(Paragraph(a, bullet_style))
    elements.append(Spacer(1, 4))

    # 8. Certifications & Workshops
    add_section("CERTIFICATIONS & WORKSHOPS")
    certs = [
        "• <b>Software Testing</b> — NPTEL (Elite Certification)",
        "• <b>Generative AI Workshop</b> — Accurate Info Solution + Dept. of CSE, BGS CET | Feb 2025",
        "• <b>Hands-on Internship on Embedded and IoT Systems</b> — AICTE IDEA LAB, SJCIT + Dept. of CSE, BGS CET"
    ]
    for c in certs:
        elements.append(Paragraph(c, bullet_style))

    # Build document
    doc.build(elements)
    print(f"✅ Generated 1-page PDF: {filename}")

if __name__ == '__main__':
    build_pdf()
