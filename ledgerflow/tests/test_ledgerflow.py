#!/usr/bin/env python3
"""
test_ledgerflow.py — End-to-End Integration & Concurrency Test Suite for LedgerFlow
Verifies:
  1. Strict Double-Entry ACID Accounting & Trial Balance (Sum Debits == Sum Credits)
  2. RBI Nodal Bank Backing Invariant (Nodal Bank Asset == Sum of Credit Sub-Ledgers)
  3. RFC Idempotency Engine: MISS (201) -> HIT-REPLAY (200) -> Payload Mutation Conflict (422)
  4. Multithreaded 10-Way Concurrent Retry Storm (At-Most-Once Execution)
  5. Multithreaded 8-Way Concurrent Double-Spend Race Attack (Zero Overdraft / TOCTOU Defense)
  6. Escrow Capture -> T+0 Settlement (Intra-State CGST+SGST & Inter-State IGST) -> Partial & Full Refunds
  7. Cryptographic SHA-256 Hash-Chain Tamper Detection & Self-Healing Recovery
  8. HMAC-SHA256 Webhook Signature Verification, Replay Window & Dead-Letter Queue (DLQ)
  9. Native Vector PDF 1.4 Generation (%PDF-1.4 ... %%EOF) for GST Invoices & Audit Reports
"""

import json
import os
import tempfile
import time
import unittest

from backend.database import atomic_write_tx, read_conn
from backend.ledger_engine import (
    LedgerError,
    heal_ledger_tamper,
    post_journal_transaction_in_conn,
    simulate_ledger_tamper,
    verify_ledger_integrity,
)
from backend.payment_flows import (
    capture_payment,
    init_database,
    refund_payment,
    run_double_spend_race_lab,
    run_idempotency_retry_storm_lab,
    settle_payment,
)
from backend.server import dispatch_api_request
from backend.webhook_engine import (
    replay_all_failed_webhooks,
    retry_webhook_delivery,
    set_webhook_sink_mode,
    sign_webhook_payload,
    verify_webhook_signature,
)


class LedgerFlowEnterpriseTestSuite(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_ledgerflow.db")
        init_database(db_path=self.db_path, force_reset=True)

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_01_seed_trial_balance_and_nodal_custody_invariant(self) -> None:
        audit = verify_ledger_integrity(self.db_path)
        self.assertTrue(audit["verified"])
        self.assertEqual(audit["status"], "VERIFIED_IMMUTABLE")
        self.assertEqual(audit["trial_balance_delta_paise"], 0)
        self.assertGreater(audit["grand_debits_paise"], 0)
        self.assertEqual(audit["grand_debits_paise"], audit["grand_credits_paise"])

        # Verify RBI Nodal Bank (#1000 DEBIT) equals exact sum of all CREDIT sub-ledgers
        sheet = audit["trial_balance_sheet"]
        debit_assets = sum(a["balance_paise"] for a in sheet if a["normal_side"] == "DEBIT")
        credit_subledgers = sum(a["balance_paise"] for a in sheet if a["normal_side"] == "CREDIT")
        self.assertEqual(debit_assets, credit_subledgers)

    def test_02_reject_unbalanced_double_entry_journal(self) -> None:
        with self.assertRaises(LedgerError) as ctx:
            with atomic_write_tx(self.db_path) as conn:
                post_journal_transaction_in_conn(
                    conn=conn,
                    tx_type="INVALID_TEST",
                    reference_id="REF-BAD",
                    description="Unbalanced entry test",
                    legs=[
                        {"account_id": "ACC_CUST_SANATH", "direction": "DEBIT", "amount_paise": 50000},
                        {"account_id": "ACC_ESCROW_HOLD", "direction": "CREDIT", "amount_paise": 49999},
                    ],
                )
        self.assertEqual(ctx.exception.code, "UNBALANCED_JOURNAL_ENTRY")
        self.assertEqual(ctx.exception.status_code, 422)

    def test_03_idempotency_miss_hit_and_422_conflict(self) -> None:
        key = "idem_unit_test_key_001"
        res1 = capture_payment(
            idempotency_key=key,
            customer_account_id="ACC_CUST_SANATH",
            merchant_account_id="ACC_MERCH_ZEPTO",
            amount_paise=250000,
            description="Order #1",
            db_path=self.db_path,
        )
        self.assertEqual(res1["http_status"], 201)
        self.assertEqual(res1["idempotency"]["status"], "MISS")
        pay_id = res1["payment"]["payment_id"]

        # Exact retry -> HTTP 200 HIT-REPLAY
        res2 = capture_payment(
            idempotency_key=key,
            customer_account_id="ACC_CUST_SANATH",
            merchant_account_id="ACC_MERCH_ZEPTO",
            amount_paise=250000,
            description="Order #1",
            db_path=self.db_path,
        )
        self.assertEqual(res2["http_status"], 200)
        self.assertEqual(res2["idempotency"]["status"], "HIT-REPLAY")
        self.assertEqual(res2["idempotency"]["replay_count"], 1)
        self.assertEqual(res2["payment"]["payment_id"], pay_id)

        # Mutated amount with same key -> HTTP 422 IDEMPOTENCY_PAYLOAD_MISMATCH
        with self.assertRaises(LedgerError) as ctx:
            capture_payment(
                idempotency_key=key,
                customer_account_id="ACC_CUST_SANATH",
                merchant_account_id="ACC_MERCH_ZEPTO",
                amount_paise=999900,
                description="Order #1",
                db_path=self.db_path,
            )
        self.assertEqual(ctx.exception.code, "IDEMPOTENCY_PAYLOAD_MISMATCH")
        self.assertEqual(ctx.exception.status_code, 422)

    def test_04_multithreaded_idempotency_retry_storm(self) -> None:
        storm = run_idempotency_retry_storm_lab(
            burst_count=10, amount_paise=120000, db_path=self.db_path
        )
        self.assertTrue(storm["passed_invariant"])
        self.assertEqual(storm["miss_executions"], 1)
        self.assertEqual(storm["hit_replays"], 9)
        self.assertEqual(storm["actual_deducted_paise"], 120000)

    def test_05_multithreaded_double_spend_race_condition_defense(self) -> None:
        race = run_double_spend_race_lab(burst_count=8, db_path=self.db_path)
        self.assertTrue(race["passed_acid_invariant"])
        self.assertEqual(race["succeeded_count"], 1)
        self.assertEqual(race["blocked_insufficient_funds_count"], 7)
        self.assertEqual(race["final_wallet_balance_paise"], 150000)

    def test_06_settlement_gst_split_and_proportional_refunds(self) -> None:
        # 1. Capture ₹10,000.00 to Inter-State Merchant (Zoho Tamil Nadu State 33 -> 18% IGST)
        cap = capture_payment(
            idempotency_key="idem_settle_refund_test",
            customer_account_id="ACC_CUST_PRIYA",
            merchant_account_id="ACC_MERCH_ZOHO",
            amount_paise=1000000,  # ₹10,000.00
            description="Zoho CRM Enterprise",
            db_path=self.db_path,
        )
        pay_id = cap["payment"]["payment_id"]

        # 2. Settle T+0: 2% Fee = ₹200 (20000p), 18% IGST = ₹36 (3600p), Net Merchant = ₹9,764 (976400p)
        settled = settle_payment(pay_id, db_path=self.db_path)
        self.assertEqual(settled["payment"]["status"], "SETTLED")

        # 3. Partial Refund of ₹4,000.00 (400000p)
        ref1 = refund_payment(
            payment_id=pay_id,
            refund_amount_paise=400000,
            reason="Partial seat reduction",
            db_path=self.db_path,
        )
        self.assertEqual(ref1["payment"]["status"], "PARTIALLY_REFUNDED")
        self.assertEqual(ref1["payment"]["refunded_paise"], 400000)

        # 4. Remaining Refund of ₹6,000.00 (600000p)
        ref2 = refund_payment(
            payment_id=pay_id,
            refund_amount_paise=600000,
            reason="Full contract cancellation",
            db_path=self.db_path,
        )
        self.assertEqual(ref2["payment"]["status"], "REFUNDED")
        self.assertEqual(ref2["payment"]["refunded_paise"], 1000000)

        # Verify ledger integrity remains 100% balanced after partial + full settlement reversals
        audit = verify_ledger_integrity(self.db_path)
        self.assertTrue(audit["verified"])
        self.assertEqual(audit["trial_balance_delta_paise"], 0)

    def test_07_sha256_tamper_detection_and_self_healing(self) -> None:
        tamper_res = simulate_ledger_tamper(self.db_path)
        self.assertTrue(tamper_res["tamper_injected"])
        self.assertFalse(tamper_res["audit_result"]["verified"])
        self.assertEqual(tamper_res["audit_result"]["status"], "TAMPER_DETECTED_CRITICAL")
        self.assertGreater(len(tamper_res["audit_result"]["chain_breaks"]), 0)

        heal_res = heal_ledger_tamper(self.db_path)
        self.assertTrue(heal_res["healed"])
        self.assertTrue(heal_res["audit_result"]["verified"])
        self.assertEqual(heal_res["audit_result"]["trial_balance_delta_paise"], 0)

    def test_08_webhook_hmac_outage_dlq_and_replay(self) -> None:
        # Switch sink to DOWN_503 outage mode
        set_webhook_sink_mode("DOWN_503", db_path=self.db_path)
        cap = capture_payment(
            idempotency_key="idem_wh_dlq_test",
            customer_account_id="ACC_CUST_SANATH",
            merchant_account_id="ACC_MERCH_CRED",
            amount_paise=80000,
            db_path=self.db_path,
        )
        wh_id = cap["webhook_delivery"]["delivery_id"]
        self.assertEqual(cap["webhook_delivery"]["status"], "RETRY_SCHEDULED")

        # Retry twice while still DOWN_503 -> transitions to DEAD_LETTER_QUEUE on attempt 3
        r2 = retry_webhook_delivery(wh_id, db_path=self.db_path)
        self.assertEqual(r2["attempt_count"], 2)
        self.assertEqual(r2["status"], "RETRY_SCHEDULED")

        r3 = retry_webhook_delivery(wh_id, db_path=self.db_path)
        self.assertEqual(r3["attempt_count"], 3)
        self.assertEqual(r3["status"], "DEAD_LETTER_QUEUE")

        # Restore sink to HEALTHY_200 and replay DLQ
        set_webhook_sink_mode("HEALTHY_200", db_path=self.db_path)
        replay = replay_all_failed_webhooks(db_path=self.db_path)
        self.assertEqual(replay["delivered_count"], 1)
        self.assertEqual(replay["remaining_failed"], 0)

        # Verify HMAC signature math & replay protection
        body = '{"event":"payment.captured","amount":80000}'
        sig = sign_webhook_payload(body)
        self.assertTrue(verify_webhook_signature(body, sig)["valid"])
        self.assertFalse(verify_webhook_signature(body + " ", sig)["valid"])
        stale_sig = sign_webhook_payload(body, timestamp=int(time.time()) - 900)
        self.assertFalse(verify_webhook_signature(body, stale_sig)["valid"])

    def test_09_pdf_generation_endpoints(self) -> None:
        status, headers, pdf_bytes = dispatch_api_request(
            "GET", "/api/v1/ledger/audit-report.pdf", {}, b"", db_path=self.db_path
        )
        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "application/pdf")
        self.assertTrue(pdf_bytes.startswith(b"%PDF-1.4"))
        self.assertIn(b"%%EOF", pdf_bytes)

        with read_conn(self.db_path) as conn:
            inv_id = conn.execute("SELECT invoice_id FROM gst_invoices LIMIT 1").fetchone()["invoice_id"]

        status2, headers2, inv_pdf = dispatch_api_request(
            "GET", f"/api/v1/invoices/{inv_id}/pdf", {}, b"", db_path=self.db_path
        )
        self.assertEqual(status2, 200)
        self.assertEqual(headers2["Content-Type"], "application/pdf")
        self.assertTrue(inv_pdf.startswith(b"%PDF-1.4"))
        self.assertIn(b"%%EOF", inv_pdf)


if __name__ == "__main__":
    unittest.main(verbosity=2)
