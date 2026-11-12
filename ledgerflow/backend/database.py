#!/usr/bin/env python3
"""
database.py — ACID SQLite Storage Engine with WAL Mode & Serializable Write Locking
Supports strict integer-paise accounting, Chart of Accounts, Immutable Journal Entries,
Idempotency Keys, GST Tax Invoices, and HMAC-SHA256 Webhook Delivery Queues.
"""

import os
import sqlite3
import threading
from contextlib import contextmanager
from typing import Optional

DEFAULT_DB_PATH = os.environ.get(
    "LEDGERFLOW_DB_PATH",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "ledgerflow.db")
)

# Global re-entrant lock combined with SQLite BEGIN IMMEDIATE for deterministic ACID serialization
_WRITE_LOCK = threading.RLock()


def get_db_path() -> str:
    path = os.environ.get("LEDGERFLOW_DB_PATH", DEFAULT_DB_PATH)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    return path


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    target = db_path or get_db_path()
    os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
    conn = sqlite3.connect(target, timeout=15.0, isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA busy_timeout=15000;")
    return conn


@contextmanager
def atomic_write_tx(db_path: Optional[str] = None):
    """
    Executes a database block inside a serialized BEGIN IMMEDIATE transaction.
    Guarantees zero TOCTOU race conditions during concurrent balance checks or idempotency reservations.
    """
    with _WRITE_LOCK:
        conn = get_connection(db_path)
        try:
            conn.execute("BEGIN IMMEDIATE;")
            yield conn
            conn.execute("COMMIT;")
        except Exception:
            try:
                conn.execute("ROLLBACK;")
            except Exception:
                pass
            raise
        finally:
            conn.close()


@contextmanager
def read_conn(db_path: Optional[str] = None):
    conn = get_connection(db_path)
    try:
        yield conn
    finally:
        conn.close()


SCHEMA_SQL = """
-- 1. Chart of Accounts (Double-Entry Ledger Accounts)
CREATE TABLE IF NOT EXISTS accounts (
    account_id TEXT PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL CHECK(category IN ('ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'EXPENSE')),
    normal_side TEXT NOT NULL CHECK(normal_side IN ('DEBIT', 'CREDIT')),
    owner_type TEXT NOT NULL, -- 'SYSTEM', 'CUSTOMER', 'MERCHANT', 'TAX_AUTHORITY'
    owner_id TEXT NOT NULL,
    gstin TEXT DEFAULT '',
    state_code TEXT DEFAULT '29',
    allow_negative INTEGER NOT NULL DEFAULT 0,
    balance_paise INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

-- 2. Immutable Journal Transactions (SHA-256 Hash-Chained Header)
CREATE TABLE IF NOT EXISTS journal_transactions (
    seq_no INTEGER PRIMARY KEY AUTOINCREMENT,
    tx_id TEXT UNIQUE NOT NULL,
    tx_type TEXT NOT NULL,
    reference_id TEXT NOT NULL,
    description TEXT NOT NULL,
    total_amount_paise INTEGER NOT NULL CHECK(total_amount_paise > 0),
    currency TEXT NOT NULL DEFAULT 'INR',
    prev_hash TEXT NOT NULL,
    entry_hash TEXT NOT NULL,
    canonical_entries_json TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

-- 3. Immutable Double-Entry Ledger Lines (Must Sum Debits == Sum Credits per tx_id)
CREATE TABLE IF NOT EXISTS ledger_entries (
    entry_id TEXT PRIMARY KEY,
    tx_id TEXT NOT NULL REFERENCES journal_transactions(tx_id),
    seq_no INTEGER NOT NULL,
    account_id TEXT NOT NULL REFERENCES accounts(account_id),
    account_code TEXT NOT NULL,
    account_name TEXT NOT NULL,
    direction TEXT NOT NULL CHECK(direction IN ('DEBIT', 'CREDIT')),
    amount_paise INTEGER NOT NULL CHECK(amount_paise > 0),
    running_balance_paise INTEGER NOT NULL,
    narration TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ledger_entries_tx ON ledger_entries(tx_id);
CREATE INDEX IF NOT EXISTS idx_ledger_entries_account ON ledger_entries(account_id);

-- 4. Payments Lifecycle Table (Customer -> Escrow -> Merchant Settlement / Refund)
CREATE TABLE IF NOT EXISTS payments (
    payment_id TEXT PRIMARY KEY,
    idempotency_key TEXT UNIQUE NOT NULL,
    customer_account_id TEXT NOT NULL REFERENCES accounts(account_id),
    merchant_account_id TEXT NOT NULL REFERENCES accounts(account_id),
    amount_paise INTEGER NOT NULL CHECK(amount_paise > 0),
    refunded_paise INTEGER NOT NULL DEFAULT 0,
    platform_fee_paise INTEGER NOT NULL DEFAULT 0,
    gst_Breakup_type TEXT NOT NULL DEFAULT 'INTRA_STATE_CGST_SGST',
    cgst_paise INTEGER NOT NULL DEFAULT 0,
    sgst_paise INTEGER NOT NULL DEFAULT 0,
    igst_paise INTEGER NOT NULL DEFAULT 0,
    net_merchant_paise INTEGER NOT NULL DEFAULT 0,
    currency TEXT NOT NULL DEFAULT 'INR',
    status TEXT NOT NULL CHECK(status IN ('CAPTURED_IN_ESCROW', 'SETTLED', 'PARTIALLY_REFUNDED', 'REFUNDED', 'BLOCKED_FRAUD')),
    payment_method TEXT NOT NULL,
    description TEXT NOT NULL,
    customer_ip TEXT NOT NULL DEFAULT '103.21.244.12',
    risk_score INTEGER NOT NULL DEFAULT 0,
    risk_decision TEXT NOT NULL DEFAULT 'ALLOW',
    risk_reasons_json TEXT NOT NULL DEFAULT '[]',
    capture_tx_id TEXT,
    settlement_tx_id TEXT,
    invoice_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 5. RFC-Compliant Idempotency Keys Store
CREATE TABLE IF NOT EXISTS idempotency_keys (
    idempotency_key TEXT PRIMARY KEY,
    endpoint TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    status_code INTEGER NOT NULL,
    response_json TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    replay_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    last_replayed_at TEXT
);

-- 6. Official GST Tax Invoices
CREATE TABLE IF NOT EXISTS gst_invoices (
    invoice_id TEXT PRIMARY KEY,
    invoice_number TEXT UNIQUE NOT NULL,
    payment_id TEXT NOT NULL REFERENCES payments(payment_id),
    merchant_account_id TEXT NOT NULL,
    merchant_name TEXT NOT NULL,
    merchant_gstin TEXT NOT NULL,
    merchant_state_code TEXT NOT NULL,
    customer_name TEXT NOT NULL,
    sac_code TEXT NOT NULL DEFAULT '998314',
    gross_amount_paise INTEGER NOT NULL,
    taxable_fee_paise INTEGER NOT NULL,
    supply_type TEXT NOT NULL, -- 'INTRA_STATE' or 'INTER_STATE'
    cgst_rate_pct REAL NOT NULL,
    cgst_paise INTEGER NOT NULL,
    sgst_rate_pct REAL NOT NULL,
    sgst_paise INTEGER NOT NULL,
    igst_rate_pct REAL NOT NULL,
    igst_paise INTEGER NOT NULL,
    total_tax_paise INTEGER NOT NULL,
    net_settlement_paise INTEGER NOT NULL,
    ledger_tx_id TEXT NOT NULL,
    ledger_entry_hash TEXT NOT NULL,
    issued_at TEXT NOT NULL
);

-- 7. HMAC-SHA256 Webhook Delivery Queue & Dead-Letter Queue (DLQ)
CREATE TABLE IF NOT EXISTS webhook_deliveries (
    delivery_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    target_url TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    signature_header TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('DELIVERED', 'RETRY_SCHEDULED', 'DEAD_LETTER_QUEUE')),
    http_status INTEGER NOT NULL DEFAULT 0,
    attempt_count INTEGER NOT NULL DEFAULT 1,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    next_retry_at TEXT,
    response_body TEXT DEFAULT '',
    error_message TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 8. System Settings & Tamper Backup Store (for Live Auditor Tamper Demo & Self-Healing)
CREATE TABLE IF NOT EXISTS system_config (
    config_key TEXT PRIMARY KEY,
    config_value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""
