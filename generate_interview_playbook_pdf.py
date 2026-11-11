#!/usr/bin/env python3
"""
generate_interview_playbook_pdf.py
Generates a comprehensive 2-page Executive System Design & Interview Master Playbook PDF
for Sanath S Gowda covering OmniCache & Guard, AutoRepo, and FinSight Hybrid RAG.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY


def build_playbook(filename="Flagship_AI_Systems_Interview_Playbook.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=34,
        rightMargin=34,
        topMargin=26,
        bottomMargin=24
    )
    styles = getSampleStyleSheet()

    NAVY = colors.HexColor("#0F172A")
    BLUE = colors.HexColor("#1D4ED8")
    SLATE = colors.HexColor("#334155")
    LIGHT_BG = colors.HexColor("#F1F5F9")
    BORDER = colors.HexColor("#CBD5E1")

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        alignment=TA_CENTER,
        textColor=NAVY
    )
    sub_style = ParagraphStyle(
        "DocSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        alignment=TA_CENTER,
        textColor=SLATE
    )
    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=13,
        textColor=BLUE,
        spaceBefore=6,
        spaceAfter=3
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.3,
        leading=11.0,
        textColor=NAVY,
        alignment=TA_JUSTIFY,
        spaceAfter=2.5
    )
    bullet_style = ParagraphStyle(
        "Bullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.2,
        leading=10.8,
        textColor=NAVY,
        leftIndent=12,
        firstLineIndent=-12,
        spaceAfter=2.0
    )

    elements = []

    elements.append(Paragraph("SANATH S GOWDA — AI &amp; SYSTEMS ENGINEERING INTERVIEW PLAYBOOK", title_style))
    elements.append(Spacer(1, 3))
    elements.append(Paragraph(
        "Complete Architecture, Mathematical Formulas &amp; Interview Q&amp;A Guide for OmniCache &amp; Guard, AutoRepo, and FinSight",
        sub_style
    ))
    elements.append(Spacer(1, 8))

    # =========================================================================
    # PROJECT 1: OMNICACHE & GUARD
    # =========================================================================
    elements.append(Paragraph("1. OMNICACHE &amp; GUARD — Distributed Semantic AI Gateway &amp; Zero-Trust WAF", h1_style))
    elements.append(Paragraph(
        "<b>Live App:</b> https://omnicache-gateway.onrender.com &nbsp;|&nbsp; "
        "<b>GitHub:</b> https://github.com/Sanathgowda-17/omnicache-gateway &nbsp;|&nbsp; "
        "<b>Local Port:</b> http://localhost:8000",
        body_style
    ))
    elements.append(Paragraph(
        "&bull;&nbsp;&nbsp;<b>30-Second Elevator Pitch:</b> \"In production AI systems, 30–40% of user prompts are semantically repetitive, "
        "costing thousands of dollars and adding 800–2000 ms of latency per call. Furthermore, enterprises cannot send raw user text to external "
        "LLMs without scrubbing PII and blocking prompt injections. I built OmniCache &amp; Guard, an OpenAI-compatible AI Gateway (/v1/chat/completions) "
        "that intercepts prompts in under 1 ms, scrubs 6 categories of PII, blocks SQLi/Jailbreak payloads via a WAF, and serves semantically "
        "similar queries from a Hybrid Vector Cache in ~2.4 ms (a 345x speedup).\"",
        bullet_style
    ))
    elements.append(Paragraph(
        "&bull;&nbsp;&nbsp;<b>How Hybrid Semantic Caching Works (`cache_engine.py`):</b> Exact-match caches (like Redis `GET/SET`) fail when two "
        "users ask the same question with different wording. OmniCache converts normalized text into L2-normalized vectors combining 65% Word "
        "Unigram/Bigram TF-IDF and 35% Character Subword N-Grams (3–5 chars) to handle typos, then computes Cosine Similarity: "
        "<i>CosineSim(A, B) = (A &middot; B) / (||A|| ||B||)</i>. If the similarity exceeds threshold <i>&tau; = 0.72</i>, the cached response is returned immediately.",
        bullet_style
    ))
    elements.append(Paragraph(
        "&bull;&nbsp;&nbsp;<b>How the Token-Bucket Rate Limiter (`rate_limiter.py`) &amp; Circuit Breaker (`provider_cascade.py`) Work:</b> "
        "Each tenant bucket holds <i>C</i> tokens and refills continuously at rate <i>R</i> tokens/sec in O(1) time: "
        "<i>tokens = min(C, tokens + &Delta;t &times; R)</i>. If upstream LLM APIs fail 3 consecutive times, the 3-state Circuit Breaker trips from "
        "<b>CLOSED &rarr; OPEN</b> (failing fast to local fallback) and probes recovery via <b>HALF_OPEN</b> after a cooldown window.",
        bullet_style
    ))
    elements.append(Spacer(1, 4))

    # =========================================================================
    # PROJECT 2: AUTOREPO
    # =========================================================================
    elements.append(Paragraph("2. AUTOREPO — Autonomous 4-Agent PR Reviewer, Compiler AST &amp; OWASP Security Linter", h1_style))
    elements.append(Paragraph(
        "<b>Live App:</b> https://autorepo-agent.onrender.com &nbsp;|&nbsp; "
        "<b>GitHub:</b> https://github.com/Sanathgowda-17/autorepo-agent &nbsp;|&nbsp; "
        "<b>Local Port:</b> http://localhost:8001",
        body_style
    ))
    elements.append(Paragraph(
        "&bull;&nbsp;&nbsp;<b>30-Second Elevator Pitch:</b> \"Naive AI code review tools pass raw source code to a single LLM prompt, which "
        "hallucinates line numbers and cannot deterministically compute algorithmic complexity. I engineered AutoRepo, which parses Python code "
        "into its native compiler Abstract Syntax Tree (`ast.NodeVisitor`) and orchestrates a 4-Agent Directed Acyclic Graph (DAG): a SecOps SAST "
        "Agent for OWASP/CWE vulnerabilities, an AST Complexity Agent for McCabe &amp; Big-O analysis, a Pytest Synthesizer Agent, and a Lead Patch "
        "Critic that rewrites vulnerable code into side-by-side hardened patches.\"",
        bullet_style
    ))
    elements.append(Paragraph(
        "&bull;&nbsp;&nbsp;<b>How Compiler AST Analysis Works (`ast_engine.py`):</b> By subclassing `ast.NodeVisitor`, AutoRepo walks `FunctionDef`, "
        "`For`, `While`, `If`, and `Try` nodes to compute <b>McCabe Cyclomatic Complexity</b>: <i>M = 1 + branching predicates</i>. It tracks nested "
        "loop depth to classify functions into O(1), O(N), O(N^2), or O(N^3), catches database queries (`cursor.execute`) inside loops (<b>N+1 Query "
        "Detector</b>), and flags mutable default arguments (`def fn(cache=[])`).",
        bullet_style
    ))
    elements.append(Paragraph(
        "&bull;&nbsp;&nbsp;<b>OWASP Top-10 / CWE Rules &amp; Webhook Security (`agent_dag.py`, `app.py`):</b> Deterministically catches CWE-89 "
        "(SQL Injection via f-strings), CWE-798 (Hardcoded Secrets), CWE-95 (`eval`/`exec` RCE), CWE-78 (OS Command Injection), and CWE-502 "
        "(Pickle Deserialization). Incoming GitHub PR webhooks are authenticated via constant-time `hmac.compare_digest` (`HMAC-SHA256`).",
        bullet_style
    ))
    elements.append(Spacer(1, 4))

    # =========================================================================
    # PROJECT 3: FINSIGHT HYBRID RAG
    # =========================================================================
    elements.append(Paragraph("3. FINSIGHT — Multimodal Financial (SEC 10-K / Basel III / RBI) &amp; Legal Hybrid RAG", h1_style))
    elements.append(Paragraph(
        "<b>Live App:</b> https://finsight-rag-p87r.onrender.com &nbsp;|&nbsp; "
        "<b>GitHub:</b> https://github.com/Sanathgowda-17/finsight-rag &nbsp;|&nbsp; "
        "<b>Local Port:</b> http://localhost:8002",
        body_style
    ))
    elements.append(Paragraph(
        "&bull;&nbsp;&nbsp;<b>30-Second Elevator Pitch:</b> \"Standard vector-only RAG fails in financial and legal applications because dense embeddings "
        "smooth over exact regulatory identifiers like `CET1`, `DOR.CRE.REC.21`, `Section 9.2`, or `$115.2B`. I built FinSight, an institutional "
        "Hybrid RAG platform that runs Sparse Lexical `BM25Okapi` and Dense Vector Search in parallel, fuses their ranks via Reciprocal Rank Fusion "
        "(RRF), applies a Cross-Encoder Reranker, extracts embedded Markdown GAAP tables, and verifies every claim using the RAGAS Evaluation Triad.\"",
        bullet_style
    ))
    elements.append(Paragraph(
        "&bull;&nbsp;&nbsp;<b>Why Reciprocal Rank Fusion (RRF) is Used (`hybrid_retriever.py`):</b> BM25 scores (unbounded `0..25+`) and Cosine "
        "Similarity (`0.0..1.0`) live on incompatible numerical scales. RRF combines rank positions scale-free: "
        "<i>RRF(d) = (1 - &alpha;) / (k + rank_BM25(d)) + &alpha; / (k + rank_Dense(d))</i>. Top candidates are then re-scored jointly with the query "
        "by the Cross-Encoder Reranker, achieving 97.8% Recall@3 vs. 74.0% for Naive Dense-Only RAG.",
        bullet_style
    ))
    elements.append(Spacer(1, 6))

    # =========================================================================
    # SUMMARY COMPARISON TABLE
    # =========================================================================
    table_data = [
        [
            Paragraph("<b>System</b>", body_style),
            Paragraph("<b>Core Algorithms &amp; Data Structures</b>", body_style),
            Paragraph("<b>Key Quantitative Metric</b>", body_style),
            Paragraph("<b>Primary Interview Topic</b>", body_style)
        ],
        [
            Paragraph("<b>OmniCache &amp; Guard</b>", body_style),
            Paragraph("TF-IDF Word/Char N-Gram Vectors, Cosine Sim, Token Bucket, Circuit Breaker, Regex WAF/DLP", body_style),
            Paragraph("~2.4 ms cache hit vs ~850 ms LLM (345x speedup)", body_style),
            Paragraph("System Design, Distributed Caching, API Security", body_style)
        ],
        [
            Paragraph("<b>AutoRepo</b>", body_style),
            Paragraph("Python `ast.NodeVisitor`, McCabe Complexity (M), 4-Agent DAG, CWE SAST, HMAC-SHA256", body_style),
            Paragraph("&lt;9 ms full AST + SAST + Pytest synthesis", body_style),
            Paragraph("Compilers, Static Analysis, Agentic Orchestration", body_style)
        ],
        [
            Paragraph("<b>FinSight RAG</b>", body_style),
            Paragraph("BM25Okapi (k1=1.5, b=0.75), Dense Cosine, Reciprocal Rank Fusion (RRF), Cross-Encoder, RAGAS", body_style),
            Paragraph("97.8% Recall@3, 99.0% RAGAS Faithfulness", body_style),
            Paragraph("Information Retrieval, Hybrid Search, LLM Grounding", body_style)
        ]
    ]
    t = Table(table_data, colWidths=[105, 195, 125, 119])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(t)

    doc.build(elements)
    print(f"Generated Playbook PDF: {filename}")


if __name__ == "__main__":
    build_playbook()
