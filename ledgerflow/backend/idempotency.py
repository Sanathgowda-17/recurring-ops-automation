#!/usr/bin/env python3
"""
idempotency.py — Stripe-Compatible RFC Idempotency Engine
Guarantees At-Most-Once financial execution across network retries, mobile timeouts,
and concurrent duplicate webhook/API dispatches.
"""

import hashlib
import json
import sqlite3
from typing import Any, Dict, Optional, Tuple

from .ledger_engine import LedgerError, utc_now_iso


def compute_payload_hash(endpoint: str, payload: Dict[str, Any]) -> str:
    # Exclude volatile client-side metadata fields if any, keeping all financial parameters strict
    filtered = {
        k: v
        for k, v in payload.items()
        if k not in ("client_retry_attempt", "client_timestamp")
    }
    canonical = json.dumps(
        {"endpoint": endpoint, "payload": filtered},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def check_idempotency_in_conn(
    conn: sqlite3.Connection,
    idempotency_key: str,
    endpoint: str,
    payload: Dict[str, Any],
) -> Tuple[bool, int, Optional[Dict[str, Any]], str]:
    """
    Checks idempotency_keys table inside an active BEGIN IMMEDIATE transaction.
    Returns (is_hit, status_code, cached_response, payload_hash).
    Raises LedgerError(422, 'IDEMPOTENCY_PAYLOAD_MISMATCH') if the same key is reused with different parameters.
    """
    clean_key = (idempotency_key or "").strip()
    if not clean_key:
        raise LedgerError(
            "Missing required 'Idempotency-Key' header or field for financial mutation.",
            code="MISSING_IDEMPOTENCY_KEY",
            status_code=400,
        )

    payload_hash = compute_payload_hash(endpoint, payload)
    row = conn.execute(
        "SELECT * FROM idempotency_keys WHERE idempotency_key = ?", (clean_key,)
    ).fetchone()

    if not row:
        return False, 201, None, payload_hash

    if row["payload_hash"] != payload_hash:
        raise LedgerError(
            f"Idempotency-Key '{clean_key}' was already used with a different request payload "
            f"(expected SHA-256 {row['payload_hash'][:12]}..., got {payload_hash[:12]}...). "
            f"Generate a new Idempotency-Key for new payment parameters.",
            code="IDEMPOTENCY_PAYLOAD_MISMATCH",
            status_code=422,
        )

    new_replays = int(row["replay_count"]) + 1
    now = utc_now_iso()
    conn.execute(
        """
        UPDATE idempotency_keys
        SET replay_count = ?, last_replayed_at = ?
        WHERE idempotency_key = ?
        """,
        (new_replays, now, clean_key),
    )

    cached_body = json.loads(row["response_json"])
    cached_body["idempotency"] = {
        "key": clean_key,
        "status": "HIT-REPLAY",
        "replay_count": new_replays,
        "original_created_at": row["created_at"],
        "last_replayed_at": now,
        "payload_hash": payload_hash,
    }
    return True, 200, cached_body, payload_hash


def save_idempotency_in_conn(
    conn: sqlite3.Connection,
    idempotency_key: str,
    endpoint: str,
    payload_hash: str,
    status_code: int,
    response_body: Dict[str, Any],
    resource_id: str,
) -> None:
    clean_key = idempotency_key.strip()
    now = utc_now_iso()
    response_body["idempotency"] = {
        "key": clean_key,
        "status": "MISS",
        "replay_count": 0,
        "original_created_at": now,
        "last_replayed_at": None,
        "payload_hash": payload_hash,
    }
    conn.execute(
        """
        INSERT INTO idempotency_keys (
            idempotency_key, endpoint, payload_hash, status_code,
            response_json, resource_id, replay_count, created_at, last_replayed_at
        ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, NULL)
        """,
        (
            clean_key,
            endpoint,
            payload_hash,
            status_code,
            json.dumps(response_body),
            resource_id,
            now,
        ),
    )
