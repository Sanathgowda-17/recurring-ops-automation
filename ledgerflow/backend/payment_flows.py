#!/usr/bin/env python3
"""
payment_flows.py — Core FinTech Payment Gateway Workflows, GST Tax Split & Concurrency Lab
Implements textbook GAAP/RBI Nodal Escrow Accounting:
  - 1000: RBI Nodal Escrow Bank Account (ASSET, Normal: DEBIT)
  - 2101..2199: Customer Wallets (LIABILITY, Normal: CREDIT, Non-Negative)
  - 2200: Escrow Clearing Hold Account (LIABILITY, Normal: CREDIT, Non-Negative)
  - 2301..2304: Merchant Settlement Accounts (LIABILITY, Normal: CREDIT, Non-Negative)
  - 2401..2403: GST Output Tax Liability - CGST, SGST, IGST (LIABILITY, Normal: CREDIT)
  - 4100: Platform MDR Processing Fee Revenue (REVENUE, Normal: CREDIT)
"""

import json
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

from .database import SCHEMA_SQL, atomic_write_tx, read_conn
from .fraud_engine import evaluate_payment_risk
from .idempotency import check_idempotency_in_conn, save_idempotency_in_conn
from .ledger_engine import (
    LedgerError,
    post_journal_transaction_in_conn,
    utc_now_iso,
    verify_ledger_integrity,
)
from .webhook_engine import dispatch_webhook_in_conn

PLATFORM_STATE_CODE = "29"  # Karnataka (Bengaluru)
PLATFORM_GSTIN = "29AABCL9012R1Z8"
MDR_RATE_BPS = 200  # 2.00% Platform Processing Fee
GST_RATE_PCT = 18.0  # 18% GST on Financial Processing Services (SAC 998314)


def compute_fee_and_gst_paise(
    gross_paise: int, merchant_state_code: str = "29"
) -> Dict[str, Any]:
    """
    Computes exact integer-paise Platform MDR Fee (2.00%) and 18% GST split:
      - Intra-state (Merchant in Karnataka '29'): 9% CGST + 9% SGST
      - Inter-state (Merchant outside '29'): 18% IGST
    """
    fee_paise = max(100, round(gross_paise * (MDR_RATE_BPS / 10000.0)))
    total_gst_paise = round(fee_paise * (GST_RATE_PCT / 100.0))

    if str(merchant_state_code).strip() == PLATFORM_STATE_CODE:
        supply_type = "INTRA_STATE"
        cgst_paise = total_gst_paise // 2
        sgst_paise = total_gst_paise - cgst_paise
        igst_paise = 0
        cgst_rate = 9.0
        sgst_rate = 9.0
        igst_rate = 0.0
    else:
        supply_type = "INTER_STATE"
        cgst_paise = 0
        sgst_paise = 0
        igst_paise = total_gst_paise
        cgst_rate = 0.0
        sgst_rate = 0.0
        igst_rate = 18.0

    net_merchant_paise = gross_paise - fee_paise - total_gst_paise
    return {
        "gross_paise": gross_paise,
        "fee_paise": fee_paise,
        "supply_type": supply_type,
        "cgst_rate_pct": cgst_rate,
        "cgst_paise": cgst_paise,
        "sgst_rate_pct": sgst_rate,
        "sgst_paise": sgst_paise,
        "igst_rate_pct": igst_rate,
        "igst_paise": igst_paise,
        "total_gst_paise": total_gst_paise,
        "net_merchant_paise": net_merchant_paise,
    }


def init_database(db_path: Optional[str] = None, force_reset: bool = False) -> Dict[str, Any]:
    with atomic_write_tx(db_path) as conn:
        if force_reset:
            for tbl in (
                "webhook_deliveries",
                "gst_invoices",
                "idempotency_keys",
                "payments",
                "ledger_entries",
                "journal_transactions",
                "accounts",
                "system_config",
            ):
                conn.execute(f"DROP TABLE IF EXISTS {tbl};")

        conn.executescript(SCHEMA_SQL)
        if not conn.in_transaction:
            conn.execute("BEGIN IMMEDIATE;")

        existing_cnt = conn.execute("SELECT COUNT(*) AS c FROM accounts").fetchone()["c"]
        if existing_cnt > 0:
            return {"initialized": False, "message": "Database already seeded."}

        now = utc_now_iso()

        # Seed Chart of Accounts
        initial_accounts = [
            # 1. Core Nodal Bank Asset (Normal: DEBIT)
            (
                "ACC_NODAL_BANK",
                "1000",
                "RBI Nodal Escrow Bank (HDFC Treasury)",
                "ASSET",
                "DEBIT",
                "SYSTEM",
                "SYS_TREASURY",
                PLATFORM_GSTIN,
                "29",
                0,
            ),
            # 2. Customer Digital Wallets (Normal: CREDIT)
            (
                "ACC_CUST_SANATH",
                "2101",
                "Customer Wallet — Sanath S Gowda",
                "LIABILITY",
                "CREDIT",
                "CUSTOMER",
                "CUST_01",
                "",
                "29",
                0,
            ),
            (
                "ACC_CUST_AARAV",
                "2102",
                "Customer Wallet — Aarav Mehta (FinCorp)",
                "LIABILITY",
                "CREDIT",
                "CUSTOMER",
                "CUST_02",
                "",
                "27",
                0,
            ),
            (
                "ACC_CUST_PRIYA",
                "2103",
                "Customer Wallet — Priya Nair (CloudScale)",
                "LIABILITY",
                "CREDIT",
                "CUSTOMER",
                "CUST_03",
                "",
                "29",
                0,
            ),
            (
                "ACC_CUST_RACELAB",
                "2199",
                "Concurrency Lab Wallet (Race-Condition Test)",
                "LIABILITY",
                "CREDIT",
                "CUSTOMER",
                "CUST_LAB",
                "",
                "29",
                0,
            ),
            # 3. Escrow Clearing Account (Normal: CREDIT)
            (
                "ACC_ESCROW_HOLD",
                "2200",
                "Escrow Hold & In-Flight Clearing Vault",
                "LIABILITY",
                "CREDIT",
                "SYSTEM",
                "SYS_ESCROW",
                PLATFORM_GSTIN,
                "29",
                0,
            ),
            # 4. Merchant Settlement Payable Accounts (Normal: CREDIT)
            (
                "ACC_MERCH_ZEPTO",
                "2301",
                "Merchant Payable — Zepto Quick Commerce Pvt Ltd",
                "LIABILITY",
                "CREDIT",
                "MERCHANT",
                "MERCH_ZEPTO",
                "29AABCZ4512K1Z4",
                "29",  # Intra-state Karnataka (CGST + SGST)
                0,
            ),
            (
                "ACC_MERCH_CRED",
                "2302",
                "Merchant Payable — CRED (Dreamplug Technologies)",
                "LIABILITY",
                "CREDIT",
                "MERCHANT",
                "MERCH_CRED",
                "29AABCD8821M1Z9",
                "29",  # Intra-state Karnataka (CGST + SGST)
                0,
            ),
            (
                "ACC_MERCH_ZOHO",
                "2303",
                "Merchant Payable — Zoho Corporation Pvt Ltd",
                "LIABILITY",
                "CREDIT",
                "MERCHANT",
                "MERCH_ZOHO",
                "33AABCZ1029E1Z1",
                "33",  # Inter-state Tamil Nadu (IGST 18%)
                0,
            ),
            (
                "ACC_MERCH_RAZOR",
                "2304",
                "Merchant Payable — Enterprise Cloud SaaS Mumbai",
                "LIABILITY",
                "CREDIT",
                "MERCHANT",
                "MERCH_SAAS",
                "27AABCE7731P1Z2",
                "27",  # Inter-state Maharashtra (IGST 18%)
                0,
            ),
            # 5. GST Output Tax Liability Account (Normal: CREDIT)
            (
                "ACC_GST_PAYABLE",
                "2400",
                "GST Output Tax Liability (CGST / SGST / IGST)",
                "LIABILITY",
                "CREDIT",
                "TAX_AUTHORITY",
                "GOV_GSTN",
                PLATFORM_GSTIN,
                "29",
                0,
            ),
            # 6. Platform Revenue Account (Normal: CREDIT)
            (
                "ACC_PLATFORM_REV",
                "4100",
                "LedgerFlow Platform MDR Fee Revenue (2.0%)",
                "REVENUE",
                "CREDIT",
                "SYSTEM",
                "SYS_REVENUE",
                PLATFORM_GSTIN,
                "29",
                0,
            ),
        ]

        for acc in initial_accounts:
            conn.execute(
                """
                INSERT INTO accounts (
                    account_id, code, name, category, normal_side,
                    owner_type, owner_id, gstin, state_code, allow_negative,
                    balance_paise, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
                """,
                (*acc, now),
            )

        conn.execute(
            """
            INSERT INTO system_config (config_key, config_value, updated_at)
            VALUES ('webhook_sink_mode', 'HEALTHY_200', ?)
            """,
            (now,),
        )

        # Seed Initial Customer Wallet Top-Ups via RTGS into Nodal Bank
        seed_topups = [
            ("ACC_CUST_SANATH", 25000000, "Initial RTGS Wallet Funding — Sanath S Gowda (₹2,50,000.00)"),
            ("ACC_CUST_AARAV", 18000000, "Initial NEFT Wallet Funding — Aarav Mehta (₹1,80,000.00)"),
            ("ACC_CUST_PRIYA", 42000000, "Initial RTGS Treasury Funding — Priya Nair (₹4,20,000.00)"),
            ("ACC_CUST_RACELAB", 500000, "Initial Concurrency Lab Funding (₹5,000.00)"),
        ]

        for cust_acc, amt_paise, desc in seed_topups:
            post_journal_transaction_in_conn(
                conn=conn,
                tx_type="WALLET_TOPUP_RTGS",
                reference_id=f"RTGS-{uuid.uuid4().hex[:8].upper()}",
                description=desc,
                legs=[
                    {
                        "account_id": "ACC_NODAL_BANK",
                        "direction": "DEBIT",
                        "amount_paise": amt_paise,
                        "narration": f"Nodal Bank Inward Remittance ({desc})",
                    },
                    {
                        "account_id": cust_acc,
                        "direction": "CREDIT",
                        "amount_paise": amt_paise,
                        "narration": f"Wallet Credit ({desc})",
                    },
                ],
                metadata={"channel": "RBI_RTGS_CLEARING"},
            )

        # Seed 3 Realistic Live Payments (2 Settled with GST Invoices, 1 In Escrow)
        p1 = _capture_payment_in_conn(
            conn=conn,
            idempotency_key="idem_seed_zoho_enterprise_001",
            customer_account_id="ACC_CUST_SANATH",
            merchant_account_id="ACC_MERCH_ZOHO",
            amount_paise=4500000,  # ₹45,000.00
            payment_method="UPI_INTENT_PRO",
            description="Zoho One Enterprise Annual License (25 Seats)",
            customer_ip="103.21.244.12",
        )
        _settle_payment_in_conn(conn, p1["payment"]["payment_id"])

        p2 = _capture_payment_in_conn(
            conn=conn,
            idempotency_key="idem_seed_cred_bill_002",
            customer_account_id="ACC_CUST_PRIYA",
            merchant_account_id="ACC_MERCH_CRED",
            amount_paise=2850000,  # ₹28,500.00
            payment_method="IMPS_EXPRESS",
            description="CRED Corporate Card Treasury Settlement",
            customer_ip="103.21.244.18",
        )
        _settle_payment_in_conn(conn, p2["payment"]["payment_id"])

        _capture_payment_in_conn(
            conn=conn,
            idempotency_key="idem_seed_zepto_escrow_003",
            customer_account_id="ACC_CUST_AARAV",
            merchant_account_id="ACC_MERCH_ZEPTO",
            amount_paise=1240000,  # ₹12,400.00
            payment_method="CARD_VISA_CORPORATE",
            description="Zepto B2B Pantry Supply Order #ZPT-8841 (Held in Escrow)",
            customer_ip="49.207.192.11",
        )

    return {"initialized": True, "message": "LedgerFlow database initialized and seeded."}


def _capture_payment_in_conn(
    conn,
    idempotency_key: str,
    customer_account_id: str,
    merchant_account_id: str,
    amount_paise: int,
    payment_method: str,
    description: str,
    customer_ip: str = "103.21.244.12",
) -> Dict[str, Any]:
    payload_for_hash = {
        "customer_account_id": customer_account_id,
        "merchant_account_id": merchant_account_id,
        "amount_paise": int(amount_paise),
        "payment_method": payment_method,
        "description": description,
    }

    is_hit, status_code, cached_resp, payload_hash = check_idempotency_in_conn(
        conn=conn,
        idempotency_key=idempotency_key,
        endpoint="POST /api/v1/payments/capture",
        payload=payload_for_hash,
    )
    if is_hit and cached_resp is not None:
        return {"http_status": status_code, **cached_resp}

    if int(amount_paise) <= 0:
        raise LedgerError("Payment amount must be greater than ₹0.00.", status_code=422)

    cust_row = conn.execute(
        "SELECT * FROM accounts WHERE account_id = ? AND owner_type = 'CUSTOMER'",
        (customer_account_id,),
    ).fetchone()
    if not cust_row:
        raise LedgerError(f"Customer account '{customer_account_id}' not found.", status_code=404)

    merch_row = conn.execute(
        "SELECT * FROM accounts WHERE account_id = ? AND owner_type = 'MERCHANT'",
        (merchant_account_id,),
    ).fetchone()
    if not merch_row:
        raise LedgerError(f"Merchant account '{merchant_account_id}' not found.", status_code=404)

    # 1. Run Real-Time Fraud & Risk Scoring Engine
    risk = evaluate_payment_risk(
        conn=conn,
        customer_account_id=customer_account_id,
        merchant_account_id=merchant_account_id,
        amount_paise=int(amount_paise),
        payment_method=payment_method,
        customer_ip=customer_ip,
        description=description,
    )

    now = utc_now_iso()
    payment_id = f"PAY-{uuid.uuid4().hex[:10].upper()}"
    tax_calc = compute_fee_and_gst_paise(int(amount_paise), merch_row["state_code"])

    if risk["decision"] == "BLOCK_FRAUD":
        conn.execute(
            """
            INSERT INTO payments (
                payment_id, idempotency_key, customer_account_id, merchant_account_id,
                amount_paise, refunded_paise, platform_fee_paise, gst_Breakup_type,
                cgst_paise, sgst_paise, igst_paise, net_merchant_paise, currency,
                status, payment_method, description, customer_ip,
                risk_score, risk_decision, risk_reasons_json,
                capture_tx_id, settlement_tx_id, invoice_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, 'INR', 'BLOCKED_FRAUD', ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, ?, ?)
            """,
            (
                payment_id,
                idempotency_key,
                customer_account_id,
                merchant_account_id,
                int(amount_paise),
                tax_calc["fee_paise"],
                tax_calc["supply_type"],
                tax_calc["cgst_paise"],
                tax_calc["sgst_paise"],
                tax_calc["igst_paise"],
                tax_calc["net_merchant_paise"],
                payment_method,
                description,
                customer_ip,
                risk["risk_score"],
                risk["decision"],
                json.dumps(risk["reasons"]),
                now,
                now,
            ),
        )
        raise LedgerError(
            f"Payment blocked by Fraud Firewall (Risk Score: {risk['risk_score']}/100 — {risk['reasons'][0]['detail']})",
            code="FRAUD_RISK_BLOCKED",
            status_code=403,
        )

    # 2. Post Atomic Double-Entry Journal: DEBIT Customer Wallet, CREDIT Escrow Hold
    journal = post_journal_transaction_in_conn(
        conn=conn,
        tx_type="PAYMENT_ESCROW_CAPTURE",
        reference_id=payment_id,
        description=f"Escrow Capture: {description} ({cust_row['name']} -> {merch_row['name']})",
        legs=[
            {
                "account_id": customer_account_id,
                "direction": "DEBIT",
                "amount_paise": int(amount_paise),
                "narration": f"Debit Customer Wallet for {payment_id}",
            },
            {
                "account_id": "ACC_ESCROW_HOLD",
                "direction": "CREDIT",
                "amount_paise": int(amount_paise),
                "narration": f"Credit Escrow Hold Vault for {payment_id}",
            },
        ],
        metadata={
            "payment_id": payment_id,
            "idempotency_key": idempotency_key,
            "risk_score": risk["risk_score"],
            "payment_method": payment_method,
        },
    )

    # 3. Record Payment Row First (Parent Foreign Key for gst_invoices)
    inv_seq = conn.execute("SELECT COUNT(*) AS c FROM gst_invoices").fetchone()["c"] + 1
    invoice_id = f"INV-{uuid.uuid4().hex[:8].upper()}"
    invoice_number = f"LF/2026-27/{inv_seq:04d}"

    conn.execute(
        """
        INSERT INTO payments (
            payment_id, idempotency_key, customer_account_id, merchant_account_id,
            amount_paise, refunded_paise, platform_fee_paise, gst_Breakup_type,
            cgst_paise, sgst_paise, igst_paise, net_merchant_paise, currency,
            status, payment_method, description, customer_ip,
            risk_score, risk_decision, risk_reasons_json,
            capture_tx_id, settlement_tx_id, invoice_id, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, 'INR', 'CAPTURED_IN_ESCROW', ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?)
        """,
        (
            payment_id,
            idempotency_key,
            customer_account_id,
            merchant_account_id,
            int(amount_paise),
            tax_calc["fee_paise"],
            tax_calc["supply_type"],
            tax_calc["cgst_paise"],
            tax_calc["sgst_paise"],
            tax_calc["igst_paise"],
            tax_calc["net_merchant_paise"],
            payment_method,
            description,
            customer_ip,
            risk["risk_score"],
            risk["decision"],
            json.dumps(risk["reasons"]),
            journal["tx_id"],
            invoice_id,
            now,
            now,
        ),
    )

    # 4. Generate Official GST Tax Invoice
    conn.execute(
        """
        INSERT INTO gst_invoices (
            invoice_id, invoice_number, payment_id, merchant_account_id,
            merchant_name, merchant_gstin, merchant_state_code, customer_name,
            sac_code, gross_amount_paise, taxable_fee_paise, supply_type,
            cgst_rate_pct, cgst_paise, sgst_rate_pct, sgst_paise,
            igst_rate_pct, igst_paise, total_tax_paise, net_settlement_paise,
            ledger_tx_id, ledger_entry_hash, issued_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, '998314', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            invoice_id,
            invoice_number,
            payment_id,
            merchant_account_id,
            merch_row["name"].replace("Merchant Payable — ", ""),
            merch_row["gstin"] or "29AABCZ0000A1Z5",
            merch_row["state_code"],
            cust_row["name"].replace("Customer Wallet — ", ""),
            int(amount_paise),
            tax_calc["fee_paise"],
            tax_calc["supply_type"],
            tax_calc["cgst_rate_pct"],
            tax_calc["cgst_paise"],
            tax_calc["sgst_rate_pct"],
            tax_calc["sgst_paise"],
            tax_calc["igst_rate_pct"],
            tax_calc["igst_paise"],
            tax_calc["total_gst_paise"],
            tax_calc["net_merchant_paise"],
            journal["tx_id"],
            journal["entry_hash"],
            now,
        ),
    )

    # 5. Dispatch Signed Webhook
    webhook = dispatch_webhook_in_conn(
        conn=conn,
        event_type="payment.captured",
        resource_id=payment_id,
        data={
            "payment_id": payment_id,
            "invoice_number": invoice_number,
            "amount_paise": int(amount_paise),
            "amount_inr": round(int(amount_paise) / 100.0, 2),
            "customer_account_id": customer_account_id,
            "merchant_account_id": merchant_account_id,
            "status": "CAPTURED_IN_ESCROW",
            "ledger_tx_id": journal["tx_id"],
            "ledger_entry_hash": journal["entry_hash"],
        },
    )

    payment_obj = {
        "payment_id": payment_id,
        "idempotency_key": idempotency_key,
        "customer_account_id": customer_account_id,
        "customer_name": cust_row["name"],
        "merchant_account_id": merchant_account_id,
        "merchant_name": merch_row["name"],
        "amount_paise": int(amount_paise),
        "amount_inr": round(int(amount_paise) / 100.0, 2),
        "platform_fee_paise": tax_calc["fee_paise"],
        "total_gst_paise": tax_calc["total_gst_paise"],
        "net_merchant_paise": tax_calc["net_merchant_paise"],
        "status": "CAPTURED_IN_ESCROW",
        "payment_method": payment_method,
        "description": description,
        "risk": risk,
        "invoice_id": invoice_id,
        "invoice_number": invoice_number,
        "capture_tx_id": journal["tx_id"],
        "entry_hash": journal["entry_hash"],
        "created_at": now,
    }

    response_payload = {
        "payment": payment_obj,
        "journal_transaction": journal,
        "webhook_delivery": webhook,
    }

    save_idempotency_in_conn(
        conn=conn,
        idempotency_key=idempotency_key,
        endpoint="POST /api/v1/payments/capture",
        payload_hash=payload_hash,
        status_code=201,
        response_body=response_payload,
        resource_id=payment_id,
    )

    return {"http_status": 201, **response_payload}


def capture_payment(
    idempotency_key: str,
    customer_account_id: str,
    merchant_account_id: str,
    amount_paise: int,
    payment_method: str = "UPI_INTENT_PRO",
    description: str = "Enterprise Order Settlement",
    customer_ip: str = "103.21.244.12",
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    with atomic_write_tx(db_path) as conn:
        return _capture_payment_in_conn(
            conn=conn,
            idempotency_key=idempotency_key,
            customer_account_id=customer_account_id,
            merchant_account_id=merchant_account_id,
            amount_paise=amount_paise,
            payment_method=payment_method,
            description=description,
            customer_ip=customer_ip,
        )


def _settle_payment_in_conn(conn, payment_id: str) -> Dict[str, Any]:
    pay_row = conn.execute(
        "SELECT * FROM payments WHERE payment_id = ?", (payment_id,)
    ).fetchone()
    if not pay_row:
        raise LedgerError(f"Payment '{payment_id}' not found.", status_code=404)

    if pay_row["status"] != "CAPTURED_IN_ESCROW":
        raise LedgerError(
            f"Payment '{payment_id}' cannot be settled because current status is '{pay_row['status']}'.",
            code="INVALID_SETTLEMENT_STATE",
            status_code=409,
        )

    gross_paise = int(pay_row["amount_paise"]) - int(pay_row["refunded_paise"])
    merch_row = conn.execute(
        "SELECT * FROM accounts WHERE account_id = ?",
        (pay_row["merchant_account_id"],),
    ).fetchone()

    tax_calc = compute_fee_and_gst_paise(gross_paise, merch_row["state_code"])

    # 4-Legged Double-Entry Settlement Journal:
    # DEBIT Escrow Hold (Gross) == CREDIT Merchant (Net) + CREDIT Platform Revenue (MDR Fee) + CREDIT GST Output Tax
    legs = [
        {
            "account_id": "ACC_ESCROW_HOLD",
            "direction": "DEBIT",
            "amount_paise": gross_paise,
            "narration": f"Release Escrow Float for Settlement of {payment_id}",
        },
        {
            "account_id": pay_row["merchant_account_id"],
            "direction": "CREDIT",
            "amount_paise": tax_calc["net_merchant_paise"],
            "narration": f"T+0 Net Merchant Settlement for {payment_id} (98% less GST)",
        },
        {
            "account_id": "ACC_PLATFORM_REV",
            "direction": "CREDIT",
            "amount_paise": tax_calc["fee_paise"],
            "narration": f"Platform 2.0% MDR Fee on {payment_id}",
        },
        {
            "account_id": "ACC_GST_PAYABLE",
            "direction": "CREDIT",
            "amount_paise": tax_calc["total_gst_paise"],
            "narration": f"18% GST ({tax_calc['supply_type']}) on Platform MDR Fee for {payment_id}",
        },
    ]

    journal = post_journal_transaction_in_conn(
        conn=conn,
        tx_type="MERCHANT_T0_SETTLEMENT",
        reference_id=payment_id,
        description=f"T+0 Split Settlement for {payment_id} to {merch_row['name']}",
        legs=legs,
        metadata={
            "payment_id": payment_id,
            "gross_paise": gross_paise,
            "net_merchant_paise": tax_calc["net_merchant_paise"],
            "fee_paise": tax_calc["fee_paise"],
            "total_gst_paise": tax_calc["total_gst_paise"],
        },
    )

    now = utc_now_iso()
    conn.execute(
        """
        UPDATE payments
        SET status = 'SETTLED', settlement_tx_id = ?, updated_at = ?
        WHERE payment_id = ?
        """,
        (journal["tx_id"], now, payment_id),
    )

    webhook = dispatch_webhook_in_conn(
        conn=conn,
        event_type="payment.settled",
        resource_id=payment_id,
        data={
            "payment_id": payment_id,
            "status": "SETTLED",
            "gross_paise": gross_paise,
            "net_merchant_paise": tax_calc["net_merchant_paise"],
            "platform_fee_paise": tax_calc["fee_paise"],
            "total_gst_paise": tax_calc["total_gst_paise"],
            "settlement_tx_id": journal["tx_id"],
            "entry_hash": journal["entry_hash"],
        },
    )

    updated_pay = dict(
        conn.execute("SELECT * FROM payments WHERE payment_id = ?", (payment_id,)).fetchone()
    )
    return {
        "payment": updated_pay,
        "journal_transaction": journal,
        "webhook_delivery": webhook,
    }


def settle_payment(payment_id: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    with atomic_write_tx(db_path) as conn:
        return _settle_payment_in_conn(conn, payment_id)


def refund_payment(
    payment_id: str,
    refund_amount_paise: Optional[int] = None,
    reason: str = "Customer requested order cancellation",
    idempotency_key: Optional[str] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executes a Full or Partial Refund with automatic Double-Entry reversal.
    - If payment is CAPTURED_IN_ESCROW: Debits Escrow Hold and Credits Customer Wallet.
    - If payment is SETTLED: Proportionally Debits Merchant Payable, Platform Fee Revenue, and GST Liability,
      and Credits Customer Wallet so all accounts stay strictly balanced!
    """
    with atomic_write_tx(db_path) as conn:
        pay_row = conn.execute(
            "SELECT * FROM payments WHERE payment_id = ?", (payment_id,)
        ).fetchone()
        if not pay_row:
            raise LedgerError(f"Payment '{payment_id}' not found.", status_code=404)

        if pay_row["status"] in ("REFUNDED", "BLOCKED_FRAUD"):
            raise LedgerError(
                f"Payment '{payment_id}' cannot be refunded (status: {pay_row['status']}).",
                status_code=409,
            )

        refundable_paise = int(pay_row["amount_paise"]) - int(pay_row["refunded_paise"])
        req_refund = int(refund_amount_paise) if refund_amount_paise else refundable_paise

        if req_refund <= 0 or req_refund > refundable_paise:
            raise LedgerError(
                f"Invalid refund amount ₹{req_refund / 100:.2f}. Max refundable: ₹{refundable_paise / 100:.2f}.",
                code="REFUND_EXCEEDS_CAPTURABLE",
                status_code=422,
            )

        idem_key = idempotency_key or f"idem_refund_{payment_id}_{pay_row['refunded_paise']}_{req_refund}"
        is_hit, status_code, cached_resp, payload_hash = check_idempotency_in_conn(
            conn=conn,
            idempotency_key=idem_key,
            endpoint=f"POST /api/v1/payments/{payment_id}/refund",
            payload={"payment_id": payment_id, "refund_amount_paise": req_refund},
        )
        if is_hit and cached_resp is not None:
            return {"http_status": status_code, **cached_resp}

        if pay_row["status"] == "CAPTURED_IN_ESCROW":
            legs = [
                {
                    "account_id": "ACC_ESCROW_HOLD",
                    "direction": "DEBIT",
                    "amount_paise": req_refund,
                    "narration": f"Escrow Reversal for Refund on {payment_id}",
                },
                {
                    "account_id": pay_row["customer_account_id"],
                    "direction": "CREDIT",
                    "amount_paise": req_refund,
                    "narration": f"Refund Credit to Customer Wallet for {payment_id} ({reason})",
                },
            ]
        else:
            # Payment was SETTLED: reverse Merchant, Platform Fee, and GST proportionally
            merch_row = conn.execute(
                "SELECT state_code FROM accounts WHERE account_id = ?",
                (pay_row["merchant_account_id"],),
            ).fetchone()
            rev_split = compute_fee_and_gst_paise(req_refund, merch_row["state_code"])
            legs = [
                {
                    "account_id": pay_row["merchant_account_id"],
                    "direction": "DEBIT",
                    "amount_paise": rev_split["net_merchant_paise"],
                    "narration": f"Merchant Settlement Reversal for Refund on {payment_id}",
                },
                {
                    "account_id": "ACC_PLATFORM_REV",
                    "direction": "DEBIT",
                    "amount_paise": rev_split["fee_paise"],
                    "narration": f"Platform Fee Reversal for Refund on {payment_id}",
                },
                {
                    "account_id": "ACC_GST_PAYABLE",
                    "direction": "DEBIT",
                    "amount_paise": rev_split["total_gst_paise"],
                    "narration": f"GST Output Tax Reversal Credit Note on {payment_id}",
                },
                {
                    "account_id": pay_row["customer_account_id"],
                    "direction": "CREDIT",
                    "amount_paise": req_refund,
                    "narration": f"Customer Refund Credit for {payment_id} ({reason})",
                },
            ]

        journal = post_journal_transaction_in_conn(
            conn=conn,
            tx_type="PAYMENT_REFUND_REVERSAL",
            reference_id=payment_id,
            description=f"Refund ₹{req_refund / 100:.2f} for {payment_id}: {reason}",
            legs=legs,
            metadata={"payment_id": payment_id, "refund_paise": req_refund, "reason": reason},
        )

        new_refunded = int(pay_row["refunded_paise"]) + req_refund
        new_status = (
            "REFUNDED"
            if new_refunded >= int(pay_row["amount_paise"])
            else (
                "CAPTURED_IN_ESCROW"
                if pay_row["status"] == "CAPTURED_IN_ESCROW"
                else "PARTIALLY_REFUNDED"
            )
        )
        now = utc_now_iso()
        conn.execute(
            """
            UPDATE payments
            SET refunded_paise = ?, status = ?, updated_at = ?
            WHERE payment_id = ?
            """,
            (new_refunded, new_status, now, payment_id),
        )

        webhook = dispatch_webhook_in_conn(
            conn=conn,
            event_type="payment.refunded",
            resource_id=payment_id,
            data={
                "payment_id": payment_id,
                "refund_amount_paise": req_refund,
                "total_refunded_paise": new_refunded,
                "status": new_status,
                "reason": reason,
                "refund_tx_id": journal["tx_id"],
            },
        )

        updated_pay = dict(
            conn.execute("SELECT * FROM payments WHERE payment_id = ?", (payment_id,)).fetchone()
        )
        resp_body = {
            "payment": updated_pay,
            "journal_transaction": journal,
            "webhook_delivery": webhook,
        }
        save_idempotency_in_conn(
            conn=conn,
            idempotency_key=idem_key,
            endpoint=f"POST /api/v1/payments/{payment_id}/refund",
            payload_hash=payload_hash,
            status_code=200,
            response_body=resp_body,
            resource_id=payment_id,
        )
        return {"http_status": 200, **resp_body}


def topup_customer_wallet(
    customer_account_id: str,
    amount_paise: int,
    channel: str = "RBI_RTGS_TREASURY",
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    if int(amount_paise) <= 0:
        raise LedgerError("Top-up amount must be positive.", status_code=422)

    with atomic_write_tx(db_path) as conn:
        cust = conn.execute(
            "SELECT * FROM accounts WHERE account_id = ?", (customer_account_id,)
        ).fetchone()
        if not cust:
            raise LedgerError(f"Account '{customer_account_id}' not found.", status_code=404)

        ref_id = f"TOPUP-{uuid.uuid4().hex[:8].upper()}"
        journal = post_journal_transaction_in_conn(
            conn=conn,
            tx_type="WALLET_TOPUP_RTGS",
            reference_id=ref_id,
            description=f"Inward {channel} Top-Up to {cust['name']} (₹{int(amount_paise) / 100:,.2f})",
            legs=[
                {
                    "account_id": "ACC_NODAL_BANK",
                    "direction": "DEBIT",
                    "amount_paise": int(amount_paise),
                    "narration": f"Nodal Bank Inward Clearing ({ref_id})",
                },
                {
                    "account_id": customer_account_id,
                    "direction": "CREDIT",
                    "amount_paise": int(amount_paise),
                    "narration": f"Customer Wallet Credit ({ref_id})",
                },
            ],
            metadata={"channel": channel},
        )
        updated_acc = dict(
            conn.execute(
                "SELECT * FROM accounts WHERE account_id = ?", (customer_account_id,)
            ).fetchone()
        )
        return {"account": updated_acc, "journal_transaction": journal}


# =========================================================================
# Interactive Concurrency & Race-Condition Lab
# =========================================================================
def run_idempotency_retry_storm_lab(
    burst_count: int = 10,
    amount_paise: int = 150000,  # ₹1,500.00
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Fires `burst_count` simultaneous parallel payment requests sharing the EXACT SAME Idempotency-Key.
    Demonstrates that exactly 1 request executes the ledger debit (HTTP 201 MISS) while
    `burst_count - 1` requests return cached idempotent replays (HTTP 200 HIT-REPLAY).
    """
    burst_count = max(2, min(25, int(burst_count)))
    shared_key = f"idem_storm_{uuid.uuid4().hex[:10]}"

    with read_conn(db_path) as conn:
        before_bal = int(
            conn.execute(
                "SELECT balance_paise FROM accounts WHERE account_id = 'ACC_CUST_SANATH'"
            ).fetchone()["balance_paise"]
        )

    def _worker(worker_idx: int) -> Dict[str, Any]:
        res = capture_payment(
            idempotency_key=shared_key,
            customer_account_id="ACC_CUST_SANATH",
            merchant_account_id="ACC_MERCH_ZEPTO",
            amount_paise=amount_paise,
            payment_method="UPI_RETRY_STORM",
            description="Concurrent Idempotent Retry Storm Test",
            db_path=db_path,
        )
        return {
            "worker_id": f"Thread-{worker_idx:02d}",
            "http_status": res["http_status"],
            "idempotency_status": res["idempotency"]["status"],
            "replay_count": res["idempotency"]["replay_count"],
            "payment_id": res["payment"]["payment_id"],
            "tx_id": res["journal_transaction"]["tx_id"],
        }

    results: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=burst_count) as pool:
        futures = [pool.submit(_worker, i + 1) for i in range(burst_count)]
        for fut in as_completed(futures):
            results.append(fut.result())

    results.sort(key=lambda r: r["worker_id"])

    with read_conn(db_path) as conn:
        after_bal = int(
            conn.execute(
                "SELECT balance_paise FROM accounts WHERE account_id = 'ACC_CUST_SANATH'"
            ).fetchone()["balance_paise"]
        )

    miss_count = sum(1 for r in results if r["idempotency_status"] == "MISS")
    hit_count = sum(1 for r in results if r["idempotency_status"] == "HIT-REPLAY")
    deducted_paise = before_bal - after_bal

    return {
        "test_type": "IDEMPOTENCY_RETRY_STORM",
        "shared_idempotency_key": shared_key,
        "concurrent_threads": burst_count,
        "amount_per_request_paise": amount_paise,
        "miss_executions": miss_count,
        "hit_replays": hit_count,
        "balance_before_paise": before_bal,
        "balance_after_paise": after_bal,
        "actual_deducted_paise": deducted_paise,
        "duplicate_losses_prevented_paise": amount_paise * (burst_count - 1),
        "passed_invariant": (miss_count == 1 and hit_count == (burst_count - 1) and deducted_paise == amount_paise),
        "thread_results": results,
    }


def run_double_spend_race_lab(
    burst_count: int = 8,
    wallet_target_paise: int = 500000,  # ₹5,000.00 wallet balance
    spend_attempt_paise: int = 350000,  # Each thread tries to spend ₹3,500.00 concurrently
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Sets `ACC_CUST_RACELAB` to exactly ₹5,000.00, then launches 8 concurrent threads
    with DISTINCT Idempotency-Keys each attempting to spend ₹3,500.00 simultaneously.
    Proves SQLite BEGIN IMMEDIATE serializable locking allows ONLY 1 thread to succeed
    and rejects the other 7 with HTTP 409 INSUFFICIENT_FUNDS (zero negative balance!).
    """
    burst_count = max(2, min(20, int(burst_count)))

    # Reset ACC_CUST_RACELAB to exact target balance
    with atomic_write_tx(db_path) as conn:
        cur_bal = int(
            conn.execute(
                "SELECT balance_paise FROM accounts WHERE account_id = 'ACC_CUST_RACELAB'"
            ).fetchone()["balance_paise"]
        )
        diff = wallet_target_paise - cur_bal
        if diff > 0:
            post_journal_transaction_in_conn(
                conn=conn,
                tx_type="LAB_BALANCE_RESET",
                reference_id=f"LAB-TOP-{uuid.uuid4().hex[:6].upper()}",
                description="Concurrency Lab Wallet Replenishment to ₹5,000.00",
                legs=[
                    {"account_id": "ACC_NODAL_BANK", "direction": "DEBIT", "amount_paise": diff},
                    {"account_id": "ACC_CUST_RACELAB", "direction": "CREDIT", "amount_paise": diff},
                ],
            )
        elif diff < 0:
            post_journal_transaction_in_conn(
                conn=conn,
                tx_type="LAB_BALANCE_RESET",
                reference_id=f"LAB-SWP-{uuid.uuid4().hex[:6].upper()}",
                description="Concurrency Lab Wallet Reset to ₹5,000.00",
                legs=[
                    {"account_id": "ACC_CUST_RACELAB", "direction": "DEBIT", "amount_paise": abs(diff)},
                    {"account_id": "ACC_NODAL_BANK", "direction": "CREDIT", "amount_paise": abs(diff)},
                ],
            )

    batch_prefix = uuid.uuid4().hex[:6]

    def _race_worker(worker_idx: int) -> Dict[str, Any]:
        distinct_key = f"idem_race_{batch_prefix}_t{worker_idx}"
        try:
            res = capture_payment(
                idempotency_key=distinct_key,
                customer_account_id="ACC_CUST_RACELAB",
                merchant_account_id="ACC_MERCH_CRED",
                amount_paise=spend_attempt_paise,
                payment_method="CONCURRENT_RACE_ATTEMPT",
                description=f"Parallel Double-Spend Attack Thread #{worker_idx}",
                db_path=db_path,
            )
            return {
                "worker_id": f"Thread-{worker_idx:02d}",
                "idempotency_key": distinct_key,
                "outcome": "CAPTURED_SUCCESS",
                "http_status": res["http_status"],
                "payment_id": res["payment"]["payment_id"],
                "detail": f"Succeeded: Captured ₹{spend_attempt_paise / 100:,.2f}",
            }
        except LedgerError as exc:
            return {
                "worker_id": f"Thread-{worker_idx:02d}",
                "idempotency_key": distinct_key,
                "outcome": exc.code,
                "http_status": exc.status_code,
                "payment_id": None,
                "detail": exc.message,
            }

    results: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=burst_count) as pool:
        futures = [pool.submit(_race_worker, i + 1) for i in range(burst_count)]
        for fut in as_completed(futures):
            results.append(fut.result())

    results.sort(key=lambda r: r["worker_id"])

    with read_conn(db_path) as conn:
        final_bal = int(
            conn.execute(
                "SELECT balance_paise FROM accounts WHERE account_id = 'ACC_CUST_RACELAB'"
            ).fetchone()["balance_paise"]
        )

    succeeded = sum(1 for r in results if r["outcome"] == "CAPTURED_SUCCESS")
    blocked = sum(1 for r in results if r["outcome"] == "INSUFFICIENT_FUNDS")

    return {
        "test_type": "DOUBLE_SPEND_RACE_CONDITION_DEFENSE",
        "concurrent_threads": burst_count,
        "starting_wallet_balance_paise": wallet_target_paise,
        "attempt_per_thread_paise": spend_attempt_paise,
        "total_attempted_spend_paise": spend_attempt_paise * burst_count,
        "succeeded_count": succeeded,
        "blocked_insufficient_funds_count": blocked,
        "final_wallet_balance_paise": final_bal,
        "passed_acid_invariant": (succeeded == 1 and blocked == (burst_count - 1) and final_bal == (wallet_target_paise - spend_attempt_paise)),
        "thread_results": results,
    }
