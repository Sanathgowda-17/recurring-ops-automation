#!/usr/bin/env python3
"""
webhook_engine.py — Cryptographic HMAC-SHA256 Webhook Dispatcher, Exponential Backoff Retry & DLQ
Follows the Stripe / Razorpay Webhook Signing Specification:
  Header: X-LedgerFlow-Signature: t=<unix_timestamp>,v1=<hmac_sha256_hex>
  Signed Payload: "<unix_timestamp>.<raw_json_body>"
"""

import hashlib
import hmac
import json
import os
import sqlite3
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from .database import atomic_write_tx, read_conn
from .ledger_engine import LedgerError, utc_now_iso

WEBHOOK_SECRET = os.environ.get(
    "LEDGERFLOW_WEBHOOK_SECRET", "whsec_ledgerflow_live_9f8e7d6c5b4a3210fedcba9876543210"
)
DEFAULT_TARGET_URL = "https://merchant.ledgerflow.internal/api/v1/webhooks/receive"


def sign_webhook_payload(
    raw_payload_json: str,
    secret: str = WEBHOOK_SECRET,
    timestamp: Optional[int] = None,
) -> str:
    ts = int(timestamp if timestamp is not None else time.time())
    signed_content = f"{ts}.{raw_payload_json}".encode("utf-8")
    digest = hmac.new(secret.encode("utf-8"), signed_content, hashlib.sha256).hexdigest()
    return f"t={ts},v1={digest}"


def verify_webhook_signature(
    raw_payload_json: str,
    signature_header: str,
    secret: str = WEBHOOK_SECRET,
    tolerance_seconds: int = 300,
    current_timestamp: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Verifies X-LedgerFlow-Signature header in constant time (hmac.compare_digest)
    and enforces replay-window tolerance (default 300s).
    """
    if not signature_header or "t=" not in signature_header or "v1=" not in signature_header:
        return {
            "valid": False,
            "reason": "MALFORMED_SIGNATURE_HEADER",
            "detail": "Header must contain 't=<unix_timestamp>,v1=<hex_digest>'.",
        }

    parts = {}
    for item in signature_header.split(","):
        if "=" in item:
            k, v = item.strip().split("=", 1)
            parts[k] = v

    try:
        ts = int(parts.get("t", "0"))
    except ValueError:
        return {
            "valid": False,
            "reason": "INVALID_TIMESTAMP",
            "detail": "Timestamp 't' is not a valid integer.",
        }

    provided_sig = parts.get("v1", "")
    now_ts = int(current_timestamp if current_timestamp is not None else time.time())
    age_seconds = abs(now_ts - ts)

    expected_signed = f"{ts}.{raw_payload_json}".encode("utf-8")
    expected_sig = hmac.new(
        secret.encode("utf-8"), expected_signed, hashlib.sha256
    ).hexdigest()

    sig_matches = hmac.compare_digest(provided_sig, expected_sig)
    if not sig_matches:
        return {
            "valid": False,
            "reason": "HMAC_SIGNATURE_MISMATCH",
            "detail": "Cryptographic HMAC-SHA256 digest does not match payload or secret (Tampered Payload).",
            "expected_v1_prefix": expected_sig[:16] + "...",
            "provided_v1_prefix": provided_sig[:16] + "...",
            "timestamp": ts,
            "age_seconds": age_seconds,
        }

    if age_seconds > tolerance_seconds:
        return {
            "valid": False,
            "reason": "TIMESTAMP_OUTSIDE_TOLERANCE_WINDOW",
            "detail": f"Webhook timestamp age ({age_seconds}s) exceeds replay protection window ({tolerance_seconds}s).",
            "timestamp": ts,
            "age_seconds": age_seconds,
        }

    return {
        "valid": True,
        "reason": "VERIFIED_AUTHENTIC",
        "detail": "HMAC-SHA256 digest verified in constant time and timestamp is within replay tolerance.",
        "timestamp": ts,
        "age_seconds": age_seconds,
        "signature_v1": expected_sig,
    }


def get_sink_mode_in_conn(conn: sqlite3.Connection) -> str:
    row = conn.execute(
        "SELECT config_value FROM system_config WHERE config_key = 'webhook_sink_mode'"
    ).fetchone()
    return row["config_value"] if row else "HEALTHY_200"


def set_webhook_sink_mode(mode: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    if mode not in ("HEALTHY_200", "DOWN_503"):
        raise LedgerError(
            "Invalid sink mode. Choose 'HEALTHY_200' or 'DOWN_503'.", status_code=400
        )
    with atomic_write_tx(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO system_config (config_key, config_value, updated_at)
            VALUES ('webhook_sink_mode', ?, ?)
            """,
            (mode, utc_now_iso()),
        )
    return {"sink_mode": mode, "updated_at": utc_now_iso()}


def dispatch_webhook_in_conn(
    conn: sqlite3.Connection,
    event_type: str,
    resource_id: str,
    data: Dict[str, Any],
    target_url: str = DEFAULT_TARGET_URL,
) -> Dict[str, Any]:
    """
    Creates a signed webhook event and executes delivery against the merchant sink.
    If the merchant endpoint is in DOWN_503 outage mode, schedules exponential backoff
    or moves to DEAD_LETTER_QUEUE after max_attempts.
    """
    delivery_id = f"WHK-{uuid.uuid4().hex[:10].upper()}"
    now = utc_now_iso()

    envelope = {
        "event_id": f"evt_{uuid.uuid4().hex[:14]}",
        "event_type": event_type,
        "api_version": "2026-11-01",
        "created_at": now,
        "resource_id": resource_id,
        "data": data,
    }
    raw_json = json.dumps(envelope, sort_keys=True, separators=(",", ":"))
    signature_header = sign_webhook_payload(raw_json)

    sink_mode = get_sink_mode_in_conn(conn)
    if sink_mode == "HEALTHY_200":
        verification = verify_webhook_signature(raw_json, signature_header)
        status = "DELIVERED"
        http_status = 200
        next_retry_at = None
        response_body = json.dumps(
            {
                "received": True,
                "verified_hmac": verification["valid"],
                "ack_id": f"ack_{delivery_id.lower()}",
            }
        )
        error_msg = ""
    else:
        status = "RETRY_SCHEDULED"
        http_status = 503
        next_dt = datetime.now(timezone.utc) + timedelta(seconds=4)
        next_retry_at = next_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        response_body = json.dumps(
            {"error": "503 Service Temporarily Unavailable (Merchant Endpoint Outage)"}
        )
        error_msg = "HTTP 503: Connection refused / upstream timeout on merchant webhook sink."

    conn.execute(
        """
        INSERT INTO webhook_deliveries (
            delivery_id, event_type, resource_id, target_url, payload_json,
            signature_header, status, http_status, attempt_count, max_attempts,
            next_retry_at, response_body, error_message, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 3, ?, ?, ?, ?, ?)
        """,
        (
            delivery_id,
            event_type,
            resource_id,
            target_url,
            raw_json,
            signature_header,
            status,
            http_status,
            next_retry_at,
            response_body,
            error_msg,
            now,
            now,
        ),
    )

    return {
        "delivery_id": delivery_id,
        "event_type": event_type,
        "resource_id": resource_id,
        "status": status,
        "http_status": http_status,
        "attempt_count": 1,
        "max_attempts": 3,
        "signature_header": signature_header,
        "next_retry_at": next_retry_at,
        "created_at": now,
    }


def retry_webhook_delivery(
    delivery_id: str, db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retries a single webhook delivery with fresh HMAC timestamp signature and exponential backoff math.
    Transitions to DEAD_LETTER_QUEUE if attempt_count reaches max_attempts while sink is DOWN_503.
    """
    with atomic_write_tx(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM webhook_deliveries WHERE delivery_id = ?", (delivery_id,)
        ).fetchone()
        if not row:
            raise LedgerError(f"Webhook delivery '{delivery_id}' not found.", status_code=404)

        sink_mode = get_sink_mode_in_conn(conn)
        new_attempt = int(row["attempt_count"]) + 1
        max_attempts = int(row["max_attempts"])
        now = utc_now_iso()
        raw_json = row["payload_json"]
        fresh_sig = sign_webhook_payload(raw_json)

        if sink_mode == "HEALTHY_200":
            status = "DELIVERED"
            http_status = 200
            next_retry_at = None
            response_body = json.dumps(
                {
                    "received": True,
                    "verified_hmac": True,
                    "replayed_on_attempt": new_attempt,
                }
            )
            error_msg = ""
        else:
            http_status = 503
            backoff_sec = 2 ** new_attempt
            if new_attempt >= max_attempts:
                status = "DEAD_LETTER_QUEUE"
                next_retry_at = None
                error_msg = (
                    f"Exhausted {max_attempts}/{max_attempts} attempts (Exponential Backoff). "
                    f"Moved to Dead-Letter Queue (DLQ) for manual inspection."
                )
            else:
                status = "RETRY_SCHEDULED"
                next_dt = datetime.now(timezone.utc) + timedelta(seconds=backoff_sec)
                next_retry_at = next_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                error_msg = (
                    f"Attempt {new_attempt}/{max_attempts} failed with HTTP 503. "
                    f"Next exponential backoff in {backoff_sec}s."
                )
            response_body = json.dumps({"error": "503 Service Unavailable"})

        conn.execute(
            """
            UPDATE webhook_deliveries
            SET signature_header = ?, status = ?, http_status = ?, attempt_count = ?,
                next_retry_at = ?, response_body = ?, error_message = ?, updated_at = ?
            WHERE delivery_id = ?
            """,
            (
                fresh_sig,
                status,
                http_status,
                new_attempt,
                next_retry_at,
                response_body,
                error_msg,
                now,
                delivery_id,
            ),
        )

        updated = conn.execute(
            "SELECT * FROM webhook_deliveries WHERE delivery_id = ?", (delivery_id,)
        ).fetchone()
        return dict(updated)


def replay_all_failed_webhooks(db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Replays all RETRY_SCHEDULED and DEAD_LETTER_QUEUE webhooks in queue order.
    """
    with read_conn(db_path) as conn:
        rows = conn.execute(
            """
            SELECT delivery_id FROM webhook_deliveries
            WHERE status IN ('RETRY_SCHEDULED', 'DEAD_LETTER_QUEUE')
            ORDER BY created_at ASC
            """
        ).fetchall()

    results: List[Dict[str, Any]] = []
    for r in rows:
        res = retry_webhook_delivery(r["delivery_id"], db_path=db_path)
        results.append(res)

    delivered_cnt = sum(1 for x in results if x["status"] == "DELIVERED")
    return {
        "total_processed": len(results),
        "delivered_count": delivered_cnt,
        "remaining_failed": len(results) - delivered_cnt,
        "results": results,
    }
