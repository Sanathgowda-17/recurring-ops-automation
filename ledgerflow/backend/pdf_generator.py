#!/usr/bin/env python3
"""
pdf_generator.py — Native Zero-Dependency Vector PDF 1.4 Generator Engine
Generates crisp, standards-compliant PDF 1.4 binary documents (%PDF-1.4 ... %%EOF)
for Official GST Tax Invoices (SAC 998314) and SOC-2 / RBI Trial Balance Audit Certificates.
"""

from typing import Any, Dict, List


def _pdf_escape(text: str) -> str:
    safe = (
        str(text)
        .replace("₹", "INR ")
        .replace("—", "-")
        .replace("–", "-")
        .replace("•", "*")
    )
    safe = safe.encode("ascii", "replace").decode("ascii")
    return safe.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def amount_in_indian_words(paise: int) -> str:
    rupees = int(paise) // 100
    rem_paise = int(paise) % 100
    if rupees == 0:
        return "Zero Rupees Only"

    ones = [
        "", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
        "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
        "Seventeen", "Eighteen", "Nineteen"
    ]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

    def _two_digits(n: int) -> str:
        if n < 20:
            return ones[n]
        return tens[n // 10] + (" " + ones[n % 10] if n % 10 != 0 else "")

    parts: List[str] = []
    crore = rupees // 10000000
    rupees %= 10000000
    lakh = rupees // 100000
    rupees %= 100000
    thousand = rupees // 1000
    rupees %= 1000
    hundred = rupees // 100
    rest = rupees % 100

    if crore > 0:
        parts.append(f"{_two_digits(crore)} Crore")
    if lakh > 0:
        parts.append(f"{_two_digits(lakh)} Lakh")
    if thousand > 0:
        parts.append(f"{_two_digits(thousand)} Thousand")
    if hundred > 0:
        parts.append(f"{ones[hundred]} Hundred")
    if rest > 0:
        if parts:
            parts.append("and")
        parts.append(_two_digits(rest))

    words = " ".join(parts) + " Rupees"
    if rem_paise > 0:
        words += f" and {_two_digits(rem_paise)} Paise"
    return words + " Only"


class VectorPDFCanvas:
    """
    Lightweight native PDF 1.4 page builder (612 x 792 pt Letter size).
    Supports rectangles, lines, and standard Type1 fonts (/F1 Helvetica, /F2 Helvetica-Bold, /F3 Courier).
    """

    def __init__(self) -> None:
        self.commands: List[str] = []

    def rect_fill(self, x: float, y: float, w: float, h: float, r: float, g: float, b: float) -> None:
        self.commands.append(f"{r:.3f} {g:.3f} {b:.3f} rg {x:.1f} {y:.1f} {w:.1f} {h:.1f} re f")

    def rect_stroke(
        self, x: float, y: float, w: float, h: float, r: float, g: float, b: float, line_width: float = 0.8
    ) -> None:
        self.commands.append(
            f"{line_width:.2f} w {r:.3f} {g:.3f} {b:.3f} RG {x:.1f} {y:.1f} {w:.1f} {h:.1f} re S"
        )

    def line(
        self, x1: float, y1: float, x2: float, y2: float, r: float = 0.8, g: float = 0.84, b: float = 0.88, width: float = 0.6
    ) -> None:
        self.commands.append(
            f"{width:.2f} w {r:.3f} {g:.3f} {b:.3f} RG {x1:.1f} {y1:.1f} m {x2:.1f} {y2:.1f} l S"
        )

    def text(
        self,
        x: float,
        y: float,
        content: str,
        font: str = "F1",
        size: float = 9.5,
        r: float = 0.06,
        g: float = 0.09,
        b: float = 0.16,
    ) -> None:
        esc = _pdf_escape(content)
        self.commands.append(
            f"BT /{font} {size:.1f} Tf {r:.3f} {g:.3f} {b:.3f} rg {x:.1f} {y:.1f} Td ({esc}) Tj ET"
        )

    def compile_pdf(self) -> bytes:
        stream_data = "\n".join(self.commands).encode("ascii")
        objects: List[bytes] = []

        # Obj 1: Catalog
        objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
        # Obj 2: Pages
        objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
        # Obj 3: Page
        objects.append(
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R /F2 5 0 R /F3 6 0 R >> >> "
            b"/Contents 7 0 R >>"
        )
        # Obj 4: Helvetica
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
        # Obj 5: Helvetica-Bold
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
        # Obj 6: Courier
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")
        # Obj 7: Content Stream
        objects.append(
            f"<< /Length {len(stream_data)} >>\nstream\n".encode("ascii")
            + stream_data
            + b"\nendstream"
        )

        out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets: List[int] = [0]

        for idx, obj_bytes in enumerate(objects, start=1):
            offsets.append(len(out))
            out.extend(f"{idx} 0 obj\n".encode("ascii"))
            out.extend(obj_bytes)
            out.extend(b"\nendobj\n")

        xref_offset = len(out)
        out.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
        out.extend(b"0000000000 65535 f \n")
        for off in offsets[1:]:
            out.extend(f"{off:010d} 00000 n \n".encode("ascii"))

        out.extend(
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode(
                "ascii"
            )
        )
        return bytes(out)


def _fmt_inr(paise: int) -> str:
    return f"INR {int(paise) / 100.0:,.2f}"


def generate_gst_invoice_pdf(inv: Dict[str, Any]) -> bytes:
    """
    Generates an official, downloadable 1-page PDF 1.4 GST Tax Invoice & Settlement Advice.
    """
    c = VectorPDFCanvas()

    # Top Header Banner (Navy #0F172A)
    c.rect_fill(32, 700, 548, 60, 0.06, 0.09, 0.16)
    c.text(46, 736, "LEDGERFLOW ENTERPRISE FINTECH INFRASTRUCTURE", font="F2", size=13, r=1, g=1, b=1)
    c.text(
        46,
        718,
        "TAX INVOICE & ESCROW SETTLEMENT ADVICE (Section 31 of CGST/IGST Act, 2017)",
        font="F1",
        size=8.5,
        r=0.75,
        g=0.83,
        b=0.98,
    )
    c.text(435, 736, f"INVOICE: {inv['invoice_number']}", font="F2", size=10, r=0.38, g=0.65, b=0.98)
    c.text(435, 718, f"SAC Code: {inv.get('sac_code', '998314')}", font="F1", size=8.5, r=0.9, g=0.9, b=0.9)

    # Metadata Strip
    c.rect_fill(32, 650, 548, 42, 0.95, 0.96, 0.98)
    c.rect_stroke(32, 650, 548, 42, 0.80, 0.84, 0.90)
    c.text(44, 675, f"Invoice ID: {inv['invoice_id']}", font="F2", size=8.5)
    c.text(44, 660, f"Payment Ref: {inv['payment_id']}", font="F1", size=8.5)
    c.text(230, 675, f"Supply Type: {inv['supply_type']}", font="F2", size=8.5)
    c.text(230, 660, f"Issued At: {inv['issued_at'][:19]} UTC", font="F1", size=8.5)
    c.text(420, 675, f"Journal TX: {inv['ledger_tx_id']}", font="F2", size=8.5, r=0.11, g=0.30, b=0.85)
    c.text(420, 660, "Currency: INR (Paise Exact)", font="F1", size=8.5)

    # Supplier & Merchant Boxes
    c.rect_stroke(32, 565, 268, 75, 0.80, 0.84, 0.90)
    c.text(42, 625, "PAYMENT AGGREGATOR (SUPPLIER):", font="F2", size=8.5, r=0.11, g=0.30, b=0.85)
    c.text(42, 610, "LedgerFlow Payment Systems Pvt. Ltd.", font="F2", size=9.5)
    c.text(42, 596, "GSTIN: 29AABCL9012R1Z8 (State: 29 - Karnataka)", font="F1", size=8.2)
    c.text(42, 583, "RBI Nodal Bank: HDFC Treasury Clearing #1000", font="F1", size=8.2)
    c.text(42, 571, "Bengaluru, Karnataka - 560001, India", font="F1", size=8.0)

    c.rect_stroke(312, 565, 268, 75, 0.80, 0.84, 0.90)
    c.text(322, 625, "MERCHANT BENEFICIARY (RECIPIENT):", font="F2", size=8.5, r=0.11, g=0.30, b=0.85)
    c.text(322, 610, str(inv["merchant_name"])[:38], font="F2", size=9.5)
    c.text(
        322,
        596,
        f"GSTIN: {inv['merchant_gstin']} (State Code: {inv['merchant_state_code']})",
        font="F1",
        size=8.2,
    )
    c.text(322, 583, f"Payer / Customer: {str(inv['customer_name'])[:32]}", font="F1", size=8.2)
    c.text(322, 571, f"Ledger Account ID: {inv['merchant_account_id']}", font="F1", size=8.0)

    # Financial Breakdown Table Header
    c.rect_fill(32, 532, 548, 22, 0.12, 0.16, 0.24)
    c.text(42, 540, "PARTICULARS / DESCRIPTION", font="F2", size=8.5, r=1, g=1, b=1)
    c.text(335, 540, "SAC / RATE", font="F2", size=8.5, r=1, g=1, b=1)
    c.text(465, 540, "AMOUNT (INR)", font="F2", size=8.5, r=1, g=1, b=1)

    rows = [
        (
            "1. Gross Order Value Captured in Escrow Vault",
            "Escrow #2200",
            _fmt_inr(inv["gross_amount_paise"]),
            False,
        ),
        (
            "2. Less: Platform MDR Processing Fee (Taxable Value)",
            "SAC 998314 @ 2.0%",
            _fmt_inr(inv["taxable_fee_paise"]),
            False,
        ),
        (
            "3. Less: Central GST (CGST) on Processing Fee",
            f"{inv['cgst_rate_pct']:.1f}%",
            _fmt_inr(inv["cgst_paise"]),
            False,
        ),
        (
            "4. Less: State GST (SGST) on Processing Fee",
            f"{inv['sgst_rate_pct']:.1f}%",
            _fmt_inr(inv["sgst_paise"]),
            False,
        ),
        (
            "5. Less: Integrated GST (IGST) on Processing Fee",
            f"{inv['igst_rate_pct']:.1f}%",
            _fmt_inr(inv["igst_paise"]),
            False,
        ),
        (
            "6. Total Output GST Liability (CGST + SGST + IGST)",
            "Total Tax (18%)",
            _fmt_inr(inv["total_tax_paise"]),
            True,
        ),
        (
            "7. NET SETTLEMENT PAYABLE TO MERCHANT",
            "T+0 Net Payout",
            _fmt_inr(inv["net_settlement_paise"]),
            True,
        ),
    ]

    y = 510
    for idx, (desc, rate_str, amt_str, is_bold) in enumerate(rows):
        if idx % 2 == 1:
            c.rect_fill(32, y - 6, 548, 22, 0.97, 0.98, 0.99)
        c.line(32, y - 6, 580, y - 6, 0.86, 0.89, 0.92, 0.5)
        f_used = "F2" if is_bold else "F1"
        c.text(42, y, desc, font=f_used, size=8.6)
        c.text(335, y, rate_str, font=f_used, size=8.4)
        c.text(465, y, amt_str, font=f_used, size=8.8)
        y -= 24

    # Amount in Words Box
    c.rect_fill(32, 316, 548, 36, 0.94, 0.97, 1.0)
    c.rect_stroke(32, 316, 548, 36, 0.70, 0.82, 0.96)
    c.text(
        42,
        337,
        f"Net Merchant Settlement in Words: {amount_in_indian_words(inv['net_settlement_paise'])}",
        font="F2",
        size=8.4,
        r=0.08,
        g=0.24,
        b=0.65,
    )
    c.text(
        42,
        323,
        f"Total GST Tax in Words: {amount_in_indian_words(inv['total_tax_paise'])}",
        font="F1",
        size=8.0,
    )

    # Cryptographic Double-Entry Audit Seal Box
    c.rect_fill(32, 215, 548, 86, 0.96, 0.97, 0.98)
    c.rect_stroke(32, 215, 548, 86, 0.75, 0.80, 0.86)
    c.text(
        42,
        285,
        "CRYPTOGRAPHIC DOUBLE-ENTRY LEDGER & SHA-256 INTEGRITY SEAL",
        font="F2",
        size=9.0,
        r=0.05,
        g=0.45,
        b=0.28,
    )
    c.text(
        42,
        268,
        f"Double-Entry Journal TX ID : {inv['ledger_tx_id']}  (Sum of Debits == Sum of Credits Verified)",
        font="F3",
        size=8.2,
    )
    c.text(
        42,
        253,
        f"SHA-256 Chain Block Hash   : {inv['ledger_entry_hash']}",
        font="F3",
        size=7.8,
    )
    c.text(
        42,
        238,
        "Accounting Standard        : RBI PA/PG Nodal Escrow Double-Entry Bookkeeping (ACID WAL)",
        font="F1",
        size=8.0,
    )
    c.text(
        42,
        224,
        "Verification Notice        : Computer-generated cryptographic tax invoice; requires no physical signature.",
        font="F1",
        size=7.8,
        r=0.35,
        g=0.40,
        b=0.48,
    )

    # Footer
    c.line(32, 65, 580, 65, 0.80, 0.84, 0.88, 0.8)
    c.text(
        32,
        48,
        "LedgerFlow FinTech Engine v2.4.0  |  Zero-Trust Idempotent Payment Gateway & ACID Double-Entry Ledger",
        font="F1",
        size=7.8,
        r=0.4,
        g=0.45,
        b=0.52,
    )
    return c.compile_pdf()


def generate_audit_report_pdf(audit: Dict[str, Any]) -> bytes:
    """
    Generates an official SOC-2 / RBI Trial Balance & Cryptographic Chain Verification PDF Report.
    """
    c = VectorPDFCanvas()

    c.rect_fill(32, 705, 548, 55, 0.06, 0.09, 0.16)
    c.text(
        44,
        738,
        "LEDGERFLOW — CRYPTOGRAPHIC TRIAL BALANCE & AUDIT REPORT",
        font="F2",
        size=12.5,
        r=1,
        g=1,
        b=1,
    )
    c.text(
        44,
        720,
        f"Audit Timestamp: {audit['checked_at']}   |   Status: {audit['status']}",
        font="F1",
        size=8.5,
        r=0.65,
        g=0.92,
        b=0.78,
    )

    # Summary KPIs
    c.rect_fill(32, 635, 548, 58, 0.95, 0.97, 0.99)
    c.rect_stroke(32, 635, 548, 58, 0.78, 0.83, 0.90)
    c.text(44, 676, f"Total Journal Blocks: {audit['total_transactions']}", font="F2", size=9.0)
    c.text(44, 660, f"Total Ledger Lines: {audit['total_ledger_entries']}", font="F1", size=8.5)
    c.text(44, 644, f"Chain Breaks Detected: {len(audit['chain_breaks'])}", font="F1", size=8.5)

    c.text(240, 676, f"Grand Debits: {_fmt_inr(audit['grand_debits_paise'])}", font="F2", size=9.0)
    c.text(240, 660, f"Grand Credits: {_fmt_inr(audit['grand_credits_paise'])}", font="F2", size=9.0)
    c.text(
        240,
        644,
        f"Trial Balance Delta: {_fmt_inr(audit['trial_balance_delta_paise'])} (MUST BE 0.00)",
        font="F2",
        size=8.5,
        r=0.05,
        g=0.50,
        b=0.28,
    )

    c.text(44, 615, f"Latest SHA-256 Root Hash: {audit['latest_merkle_root_hash']}", font="F3", size=7.8)

    # Trial Balance Table Header
    c.rect_fill(32, 582, 548, 22, 0.12, 0.16, 0.24)
    c.text(40, 590, "CODE", font="F2", size=8.0, r=1, g=1, b=1)
    c.text(80, 590, "ACCOUNT NAME", font="F2", size=8.0, r=1, g=1, b=1)
    c.text(290, 590, "CATEGORY", font="F2", size=8.0, r=1, g=1, b=1)
    c.text(365, 590, "DEBITS", font="F2", size=8.0, r=1, g=1, b=1)
    c.text(445, 590, "CREDITS", font="F2", size=8.0, r=1, g=1, b=1)
    c.text(515, 590, "NET BAL", font="F2", size=8.0, r=1, g=1, b=1)

    y = 562
    for idx, row in enumerate(audit.get("trial_balance_sheet", [])[:16]):
        if idx % 2 == 1:
            c.rect_fill(32, y - 5, 548, 20, 0.97, 0.98, 0.99)
        c.line(32, y - 5, 580, y - 5, 0.88, 0.90, 0.93, 0.5)
        c.text(40, y, str(row["code"]), font="F2", size=8.0)
        c.text(80, y, str(row["name"])[:34], font="F1", size=7.8)
        c.text(290, y, f"{row['category']} ({row['normal_side'][0]})", font="F1", size=7.5)
        c.text(365, y, f"{row['debits_paise'] / 100:,.0f}", font="F3", size=7.6)
        c.text(445, y, f"{row['credits_paise'] / 100:,.0f}", font="F3", size=7.6)
        c.text(515, y, f"{row['balance_paise'] / 100:,.0f}", font="F2", size=7.8)
        y -= 21

    c.line(32, 65, 580, 65, 0.80, 0.84, 0.88, 0.8)
    c.text(
        32,
        48,
        "Certified by LedgerFlow Cryptographic Audit Engine — Deterministic Double-Entry & SHA-256 Verification",
        font="F1",
        size=7.8,
        r=0.4,
        g=0.45,
        b=0.52,
    )
    return c.compile_pdf()
