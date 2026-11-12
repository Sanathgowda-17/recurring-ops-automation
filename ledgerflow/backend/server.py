#!/usr/bin/env python3
"""
server.py — Unified REST API Router, ThreadingHTTPServer & ASGI Adapter for LedgerFlow
Supports both:
  1. Zero-dependency execution (`python3 app.py`) via ThreadingHTTPServer
  2. Cloud ASGI deployment (`uvicorn app:app`) on Render / Railway / Docker
"""

import json
import mimetypes
import os
import re
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from .database import read_conn
from .ledger_engine import (
    LedgerError,
    heal_ledger_tamper,
    simulate_ledger_tamper,
    utc_now_iso,
    verify_ledger_integrity,
)
from .payment_flows import (
    capture_payment,
    init_database,
    refund_payment,
    run_double_spend_race_lab,
    run_idempotency_retry_storm_lab,
    settle_payment,
    topup_customer_wallet,
)
from .pdf_generator import generate_audit_report_pdf, generate_gst_invoice_pdf
from .webhook_engine import (
    WEBHOOK_SECRET,
    get_sink_mode_in_conn,
    replay_all_failed_webhooks,
    retry_webhook_delivery,
    set_webhook_sink_mode,
    sign_webhook_payload,
    verify_webhook_signature,
)

FRONTEND_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend"
)


def build_dashboard_payload(db_path: Optional[str] = None) -> Dict[str, Any]:
    audit = verify_ledger_integrity(db_path)

    with read_conn(db_path) as conn:
        accounts = [
            dict(r)
            for r in conn.execute("SELECT * FROM accounts ORDER BY code ASC").fetchall()
        ]
        for a in accounts:
            a["balance_inr"] = round(int(a["balance_paise"]) / 100.0, 2)

        payments = [
            dict(r)
            for r in conn.execute(
                """
                SELECT p.*,
                       ca.name AS customer_name,
                       ma.name AS merchant_name,
                       ma.gstin AS merchant_gstin,
                       ma.state_code AS merchant_state_code
                FROM payments p
                LEFT JOIN accounts ca ON p.customer_account_id = ca.account_id
                LEFT JOIN accounts ma ON p.merchant_account_id = ma.account_id
                ORDER BY p.created_at DESC
                LIMIT 50
                """
            ).fetchall()
        ]
        for p in payments:
            p["amount_inr"] = round(int(p["amount_paise"]) / 100.0, 2)
            p["refunded_inr"] = round(int(p["refunded_paise"]) / 100.0, 2)
            p["net_merchant_inr"] = round(int(p["net_merchant_paise"]) / 100.0, 2)
            p["platform_fee_inr"] = round(int(p["platform_fee_paise"]) / 100.0, 2)
            p["risk_reasons"] = json.loads(p.get("risk_reasons_json") or "[]")

        tx_rows = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM journal_transactions ORDER BY seq_no DESC LIMIT 40"
            ).fetchall()
        ]
        for tx in tx_rows:
            tx["total_amount_inr"] = round(int(tx["total_amount_paise"]) / 100.0, 2)
            entries = [
                dict(e)
                for e in conn.execute(
                    "SELECT * FROM ledger_entries WHERE tx_id = ? ORDER BY entry_id ASC",
                    (tx["tx_id"],),
                ).fetchall()
            ]
            for e in entries:
                e["amount_inr"] = round(int(e["amount_paise"]) / 100.0, 2)
                e["running_balance_inr"] = round(
                    int(e["running_balance_paise"]) / 100.0, 2
                )
            tx["entries"] = entries

        invoices = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM gst_invoices ORDER BY issued_at DESC LIMIT 40"
            ).fetchall()
        ]
        for inv in invoices:
            inv["gross_amount_inr"] = round(int(inv["gross_amount_paise"]) / 100.0, 2)
            inv["taxable_fee_inr"] = round(int(inv["taxable_fee_paise"]) / 100.0, 2)
            inv["total_tax_inr"] = round(int(inv["total_tax_paise"]) / 100.0, 2)
            inv["net_settlement_inr"] = round(
                int(inv["net_settlement_paise"]) / 100.0, 2
            )

        webhooks = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM webhook_deliveries ORDER BY created_at DESC LIMIT 40"
            ).fetchall()
        ]

        idem_keys = [
            dict(r)
            for r in conn.execute(
                "SELECT idempotency_key, endpoint, payload_hash, status_code, resource_id, replay_count, created_at, last_replayed_at FROM idempotency_keys ORDER BY created_at DESC LIMIT 40"
            ).fetchall()
        ]

        sink_mode = get_sink_mode_in_conn(conn)

        # KPI Aggregations
        acc_map = {a["account_id"]: int(a["balance_paise"]) for a in accounts}
        gmv_row = conn.execute(
            "SELECT COALESCE(SUM(amount_paise), 0) AS gmv, COALESCE(SUM(refunded_paise), 0) AS ref FROM payments WHERE status != 'BLOCKED_FRAUD'"
        ).fetchone()
        gmv_paise = int(gmv_row["gmv"])
        refunded_paise = int(gmv_row["ref"])

        replays_saved = int(
            conn.execute(
                "SELECT COALESCE(SUM(replay_count), 0) AS s FROM idempotency_keys"
            ).fetchone()["s"]
        )
        dlq_count = int(
            conn.execute(
                "SELECT COUNT(*) AS c FROM webhook_deliveries WHERE status IN ('RETRY_SCHEDULED', 'DEAD_LETTER_QUEUE')"
            ).fetchone()["c"]
        )

    return {
        "kpis": {
            "gmv_paise": gmv_paise,
            "gmv_inr": round(gmv_paise / 100.0, 2),
            "nodal_bank_asset_paise": acc_map.get("ACC_NODAL_BANK", 0),
            "nodal_bank_asset_inr": round(acc_map.get("ACC_NODAL_BANK", 0) / 100.0, 2),
            "escrow_float_paise": acc_map.get("ACC_ESCROW_HOLD", 0),
            "escrow_float_inr": round(acc_map.get("ACC_ESCROW_HOLD", 0) / 100.0, 2),
            "platform_revenue_paise": acc_map.get("ACC_PLATFORM_REV", 0),
            "platform_revenue_inr": round(acc_map.get("ACC_PLATFORM_REV", 0) / 100.0, 2),
            "gst_payable_paise": acc_map.get("ACC_GST_PAYABLE", 0),
            "gst_payable_inr": round(acc_map.get("ACC_GST_PAYABLE", 0) / 100.0, 2),
            "refunded_paise": refunded_paise,
            "refunded_inr": round(refunded_paise / 100.0, 2),
            "idempotency_replays_saved": replays_saved,
            "webhook_failed_or_dlq_count": dlq_count,
            "ledger_verified": audit["verified"],
            "ledger_status": audit["status"],
            "trial_balance_delta_paise": audit["trial_balance_delta_paise"],
            "latest_merkle_root_hash": audit["latest_merkle_root_hash"],
        },
        "accounts": accounts,
        "payments": payments,
        "journal_transactions": tx_rows,
        "invoices": invoices,
        "webhooks": webhooks,
        "webhook_sink_mode": sink_mode,
        "webhook_secret_preview": WEBHOOK_SECRET[:18] + "...",
        "idempotency_keys": idem_keys,
        "audit_summary": audit,
    }


def get_account_statement(
    account_id: str, db_path: Optional[str] = None
) -> Dict[str, Any]:
    with read_conn(db_path) as conn:
        acc = conn.execute(
            "SELECT * FROM accounts WHERE account_id = ?", (account_id,)
        ).fetchone()
        if not acc:
            raise LedgerError(f"Account '{account_id}' not found.", status_code=404)

        entries = [
            dict(r)
            for r in conn.execute(
                """
                SELECT le.*, jt.tx_type, jt.reference_id, jt.entry_hash
                FROM ledger_entries le
                JOIN journal_transactions jt ON le.tx_id = jt.tx_id
                WHERE le.account_id = ?
                ORDER BY le.seq_no DESC, le.entry_id DESC
                """,
                (account_id,),
            ).fetchall()
        ]
        for e in entries:
            e["amount_inr"] = round(int(e["amount_paise"]) / 100.0, 2)
            e["running_balance_inr"] = round(int(e["running_balance_paise"]) / 100.0, 2)

        acc_dict = dict(acc)
        acc_dict["balance_inr"] = round(int(acc_dict["balance_paise"]) / 100.0, 2)
        return {"account": acc_dict, "entries": entries}


def dispatch_api_request(
    method: str,
    path: str,
    headers: Dict[str, str],
    body_bytes: bytes,
    db_path: Optional[str] = None,
) -> Tuple[int, Dict[str, str], bytes]:
    """
    Core HTTP router returning (status_code, response_headers, response_bytes).
    """
    resp_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Idempotency-Key, X-LedgerFlow-Signature",
        "Access-Control-Expose-Headers": "X-Idempotency-Status, Content-Disposition",
    }

    if method == "OPTIONS":
        return 204, resp_headers, b""

    parsed = urlparse(path)
    clean_path = parsed.path

    # Parse JSON body if present
    payload: Dict[str, Any] = {}
    if body_bytes:
        try:
            payload = json.loads(body_bytes.decode("utf-8"))
        except Exception:
            payload = {}

    try:
        # 1. Health Endpoint
        if method == "GET" and clean_path == "/api/v1/health":
            audit = verify_ledger_integrity(db_path)
            data = {
                "status": "ok",
                "service": "LedgerFlow Enterprise Payment & Double-Entry Engine",
                "version": "2.4.0",
                "ledger_verified": audit["verified"],
                "trial_balance_delta_paise": audit["trial_balance_delta_paise"],
                "latest_merkle_root_hash": audit["latest_merkle_root_hash"],
                "timestamp": utc_now_iso(),
            }
            resp_headers["Content-Type"] = "application/json; charset=utf-8"
            return 200, resp_headers, json.dumps(data).encode("utf-8")

        # 2. Full Dashboard State
        if method == "GET" and clean_path == "/api/v1/dashboard":
            data = build_dashboard_payload(db_path)
            resp_headers["Content-Type"] = "application/json; charset=utf-8"
            return 200, resp_headers, json.dumps(data).encode("utf-8")

        # 3. Single Account T-Account Statement
        m_acc = re.match(r"^/api/v1/accounts/([^/]+)/statement$", clean_path)
        if method == "GET" and m_acc:
            data = get_account_statement(m_acc.group(1), db_path)
            resp_headers["Content-Type"] = "application/json; charset=utf-8"
            return 200, resp_headers, json.dumps(data).encode("utf-8")

        # 4. Capture Payment into Escrow (Idempotent)
        if method == "POST" and clean_path == "/api/v1/payments/capture":
            idem_key = (
                headers.get("idempotency-key")
                or headers.get("Idempotency-Key")
                or payload.get("idempotency_key")
                or ""
            )
            amount_paise = payload.get("amount_paise")
            if amount_paise is None and payload.get("amount_inr") is not None:
                amount_paise = int(round(float(payload["amount_inr"]) * 100))

            res = capture_payment(
                idempotency_key=str(idem_key),
                customer_account_id=str(
                    payload.get("customer_account_id", "ACC_CUST_SANATH")
                ),
                merchant_account_id=str(
                    payload.get("merchant_account_id", "ACC_MERCH_ZEPTO")
                ),
                amount_paise=int(amount_paise or 0),
                payment_method=str(payload.get("payment_method", "UPI_INTENT_PRO")),
                description=str(
                    payload.get("description", "Enterprise Order Capture")
                ),
                customer_ip=str(payload.get("customer_ip", "103.21.244.12")),
                db_path=db_path,
            )
            http_status = int(res.pop("http_status", 201))
            resp_headers["Content-Type"] = "application/json; charset=utf-8"
            resp_headers["X-Idempotency-Status"] = res["idempotency"]["status"]
            return http_status, resp_headers, json.dumps(res).encode("utf-8")

        # 5. Instant T+0 Merchant Settlement
        m_settle = re.match(r"^/api/v1/payments/([^/]+)/settle$", clean_path)
        if method == "POST" and m_settle:
            res = settle_payment(m_settle.group(1), db_path=db_path)
            resp_headers["Content-Type"] = "application/json; charset=utf-8"
            return 200, resp_headers, json.dumps(res).encode("utf-8")

        # 6. Full or Partial Refund
        m_refund = re.match(r"^/api/v1/payments/([^/]+)/refund$", clean_path)
        if method == "POST" and m_refund:
            refund_paise = payload.get("refund_amount_paise")
            if refund_paise is None and payload.get("refund_amount_inr") is not None:
                refund_paise = int(round(float(payload["refund_amount_inr"]) * 100))

            idem_key = (
                headers.get("idempotency-key")
                or headers.get("Idempotency-Key")
                or payload.get("idempotency_key")
            )
            res = refund_payment(
                payment_id=m_refund.group(1),
                refund_amount_paise=int(refund_paise) if refund_paise is not None else None,
                reason=str(
                    payload.get("reason", "Customer requested refund reversal")
                ),
                idempotency_key=idem_key,
                db_path=db_path,
            )
            http_status = int(res.pop("http_status", 200))
            resp_headers["Content-Type"] = "application/json; charset=utf-8"
            return http_status, resp_headers, json.dumps(res).encode("utf-8")

        # 7. Customer Wallet Top-up
        if method == "POST" and clean_path == "/api/v1/wallets/topup":
            amt_paise = payload.get("amount_paise")
            if amt_paise is None and payload.get("amount_inr") is not None:
                amt_paise = int(round(float(payload["amount_inr"]) * 100))

            res = topup_customer_wallet(
                customer_account_id=str(
                    payload.get("customer_account_id", "ACC_CUST_SANATH")
                ),
                amount_paise=int(amt_paise or 0),
                channel=str(payload.get("channel", "RBI_RTGS_TREASURY")),
                db_path=db_path,
            )
            resp_headers["Content-Type"] = "application/json; charset=utf-8"
            return 200, resp_headers, json.dumps(res).encode("utf-8")

        # 8. Cryptographic Ledger Verification & Tamper Simulation
        if method == "GET" and clean_path == "/api/v1/ledger/verify":
            res = verify_ledger_integrity(db_path)
            resp_headers["Content-Type"] = "application/json; charset=utf-8"
            return 200, resp_headers, json.dumps(res).encode("utf-8")

        if method == "POST" and clean_path == "/api/v1/ledger/simulate-tamper":
            res = simulate_ledger_tamper(db_path)
            resp_headers["Content-Type"] = "application/json; charset=utf-8"
            return 200, resp_headers, json.dumps(res).encode("utf-8")

        if method == "POST" and clean_path == "/api/v1/ledger/heal-tamper":
            res = heal_ledger_tamper(db_path)
            resp_headers["Content-Type"] = "application/json; charset=utf-8"
            return 200, resp_headers, json.dumps(res).encode("utf-8")

        # 9. Downloadable PDF Audit Report & GST Tax Invoices
        if method == "GET" and clean_path == "/api/v1/ledger/audit-report.pdf":
            audit = verify_ledger_integrity(db_path)
            pdf_bytes = generate_audit_report_pdf(audit)
            resp_headers["Content-Type"] = "application/pdf"
            resp_headers["Content-Disposition"] = (
                'attachment; filename="LedgerFlow_Trial_Balance_Audit_Report.pdf"'
            )
            return 200, resp_headers, pdf_bytes

        m_inv_pdf = re.match(r"^/api/v1/invoices/([^/]+)/pdf$", clean_path)
        if method == "GET" and m_inv_pdf:
            inv_id = m_inv_pdf.group(1)
            with read_conn(db_path) as conn:
                inv_row = conn.execute(
                    "SELECT * FROM gst_invoices WHERE invoice_id = ? OR payment_id = ?",
                    (inv_id, inv_id),
                ).fetchone()
            if not inv_row:
                raise LedgerError(f"GST Invoice '{inv_id}' not found.", status_code=404)
            inv_dict = dict(inv_row)
            pdf_bytes = generate_gst_invoice_pdf(inv_dict)
            safe_num = inv_dict["invoice_number"].replace("/", "_")
            resp_headers["Content-Type"] = "application/pdf"
            resp_headers["Content-Disposition"] = (
                f'attachment; filename="GST_Invoice_{safe_num}.pdf"'
            )
            return 200, resp_headers, pdf_bytes

        # 10. Interactive Concurrency & Race-Condition Lab
        if method == "POST" and clean_path == "/api/v1/lab/idempotency-storm":
            burst = int(payload.get("burst_count", 10))
            amt_paise = int(payload.get("amount_paise", 150000))
            res = run_idempotency_retry_storm_lab(
                burst_count=burst, amount_paise=amt_paise, db_path=db_path
            )
            resp_headers["Content-Type"] = "application/json; charset=utf-8"
            return 200, resp_headers, json.dumps(res).encode("utf-8")

        if method == "POST" and clean_path == "/api/v1/lab/double-spend-race":
            burst = int(payload.get("burst_count", 8))
            res = run_double_spend_race_lab(burst_count=burst, db_path=db_path)
            resp_headers["Content-Type"] = "application/json; charset=utf-8"
            return 200, resp_headers, json.dumps(res).encode("utf-8")

        # 11. Webhook Management, DLQ Replay & HMAC Signature Verifier
        if method == "POST" and clean_path == "/api/v1/webhooks/sink-mode":
            mode = str(payload.get("sink_mode", "HEALTHY_200"))
            res = set_webhook_sink_mode(mode, db_path=db_path)
            resp_headers["Content-Type"] = "application/json; charset=utf-8"
            return 200, resp_headers, json.dumps(res).encode("utf-8")

        m_wh_retry = re.match(r"^/api/v1/webhooks/([^/]+)/retry$", clean_path)
        if method == "POST" and m_wh_retry:
            res = retry_webhook_delivery(m_wh_retry.group(1), db_path=db_path)
            resp_headers["Content-Type"] = "application/json; charset=utf-8"
            return 200, resp_headers, json.dumps(res).encode("utf-8")

        if method == "POST" and clean_path == "/api/v1/webhooks/replay-all":
            res = replay_all_failed_webhooks(db_path=db_path)
            resp_headers["Content-Type"] = "application/json; charset=utf-8"
            return 200, resp_headers, json.dumps(res).encode("utf-8")

        if method == "POST" and clean_path == "/api/v1/webhooks/verify-signature":
            raw_json = str(payload.get("raw_payload_json", "{}"))
            sig_header = str(payload.get("signature_header", ""))
            if payload.get("auto_sign"):
                ts_override = payload.get("timestamp_override")
                sig_header = sign_webhook_payload(
                    raw_json,
                    timestamp=int(ts_override) if ts_override is not None else None,
                )
            res = verify_webhook_signature(raw_json, sig_header)
            res["tested_signature_header"] = sig_header
            resp_headers["Content-Type"] = "application/json; charset=utf-8"
            return 200, resp_headers, json.dumps(res).encode("utf-8")

        # 12. System Reset to Seed State
        if method == "POST" and clean_path == "/api/v1/system/reset":
            res = init_database(db_path=db_path, force_reset=True)
            resp_headers["Content-Type"] = "application/json; charset=utf-8"
            return 200, resp_headers, json.dumps(res).encode("utf-8")

        # 13. Static Frontend Asset Serving
        if method == "GET":
            rel = clean_path.lstrip("/") or "index.html"
            if ".." in rel:
                raise LedgerError("Forbidden path", status_code=403)
            target_file = os.path.join(FRONTEND_DIR, rel)
            if not os.path.isfile(target_file):
                target_file = os.path.join(FRONTEND_DIR, "index.html")
            if os.path.isfile(target_file):
                ctype, _ = mimetypes.guess_type(target_file)
                resp_headers["Content-Type"] = ctype or "text/html; charset=utf-8"
                with open(target_file, "rb") as f:
                    return 200, resp_headers, f.read()

        resp_headers["Content-Type"] = "application/json; charset=utf-8"
        return (
            404,
            resp_headers,
            json.dumps({"error": f"Endpoint {method} {clean_path} not found."}).encode(
                "utf-8"
            ),
        )

    except LedgerError as exc:
        resp_headers["Content-Type"] = "application/json; charset=utf-8"
        err_payload = {
            "error": exc.message,
            "code": exc.code,
            "status_code": exc.status_code,
        }
        return exc.status_code, resp_headers, json.dumps(err_payload).encode("utf-8")
    except Exception as exc:
        traceback.print_exc()
        resp_headers["Content-Type"] = "application/json; charset=utf-8"
        return (
            500,
            resp_headers,
            json.dumps(
                {"error": str(exc), "code": "INTERNAL_SERVER_ERROR"}
            ).encode("utf-8"),
        )


class LedgerFlowHTTPRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        # Quiet clean logs
        pass

    def _handle(self, method: str) -> None:
        content_len = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_len) if content_len > 0 else b""
        req_headers = {k: v for k, v in self.headers.items()}

        status, resp_headers, resp_bytes = dispatch_api_request(
            method=method,
            path=self.path,
            headers=req_headers,
            body_bytes=body,
        )
        self.send_response(status)
        for k, v in resp_headers.items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(resp_bytes)))
        self.end_headers()
        if resp_bytes:
            self.wfile.write(resp_bytes)

    def do_GET(self) -> None:
        self._handle("GET")

    def do_POST(self) -> None:
        self._handle("POST")

    def do_OPTIONS(self) -> None:
        self._handle("OPTIONS")


async def asgi_app(scope: Dict[str, Any], receive: Any, send: Any) -> None:
    """
    Standard ASGI 3.0 application callable so `uvicorn app:app` runs natively in production.
    """
    if scope["type"] == "lifespan":
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                init_database()
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})
                return

    if scope["type"] != "http":
        return

    method = scope.get("method", "GET")
    path = scope.get("path", "/")
    query_string = scope.get("query_string", b"").decode("utf-8")
    full_path = f"{path}?{query_string}" if query_string else path

    headers: Dict[str, str] = {}
    for k_bytes, v_bytes in scope.get("headers", []):
        headers[k_bytes.decode("latin1")] = v_bytes.decode("latin1")

    body_chunks = []
    while True:
        event = await receive()
        if event["type"] == "http.request":
            body_chunks.append(event.get("body", b""))
            if not event.get("more_body", False):
                break
        elif event["type"] == "http.disconnect":
            return

    body_bytes = b"".join(body_chunks)
    status_code, resp_headers, resp_bytes = dispatch_api_request(
        method=method, path=full_path, headers=headers, body_bytes=body_bytes
    )

    asgi_headers = [
        (k.lower().encode("latin1"), str(v).encode("latin1"))
        for k, v in resp_headers.items()
    ]
    asgi_headers.append((b"content-length", str(len(resp_bytes)).encode("latin1")))

    await send(
        {
            "type": "http.response.start",
            "status": status_code,
            "headers": asgi_headers,
        }
    )
    await send(
        {
            "type": "http.response.body",
            "body": resp_bytes,
        }
    )


def run_http_server(host: str = "0.0.0.0", port: int = 8090) -> None:
    init_database()
    server = ThreadingHTTPServer((host, port), LedgerFlowHTTPRequestHandler)
    print(f"======================================================================")
    print(f" LedgerFlow Enterprise FinTech Engine v2.4.0")
    print(f" Live Console & API : http://localhost:{port}")
    print(f" Health Check       : http://localhost:{port}/api/v1/health")
    print(f"======================================================================")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down LedgerFlow server...")
        server.server_close()
