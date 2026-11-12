#!/usr/bin/env python3
"""
ledger_engine.py — Strict Double-Entry ACID Accounting & SHA-256 Hash-Chained Audit Engine
Enforces:
  1. Sum(DEBIT) == Sum(CREDIT) in integer paise for every journal transaction
  2. Non-negative balance invariants for protected Customer & Escrow accounts (prevents Double-Spend)
  3. Cryptographic SHA-256 Merkle/Chain linkage across all historical journal transactions
  4. Full Trial Balance & Account Reconciliation verifier + Tamper Detection & Self-Healing
"""

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .database import atomic_write_tx, read_conn

GENESIS_HASH = "0" * 64


class LedgerError(Exception):
    def __init__(self, message: str, code: str = "LEDGER_VIOLATION", status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def compute_journal_hash(
    seq_no_hint: str,
    tx_id: str,
    tx_type: str,
    reference_id: str,
    total_amount_paise: int,
    prev_hash: str,
    canonical_entries_json: str,
) -> str:
    payload = f"{seq_no_hint}|{tx_id}|{tx_type}|{reference_id}|{total_amount_paise}|{prev_hash}|{canonical_entries_json}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def canonicalize_entries(legs: List[Dict[str, Any]]) -> str:
    normalized = [
        {
            "account_id": str(leg["account_id"]),
            "direction": str(leg["direction"]),
            "amount_paise": int(leg["amount_paise"]),
        }
        for leg in legs
    ]
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"))


def post_journal_transaction_in_conn(
    conn: sqlite3.Connection,
    tx_type: str,
    reference_id: str,
    description: str,
    legs: List[Dict[str, Any]],
    metadata: Optional[Dict[str, Any]] = None,
    tx_id: Optional[str] = None,
    created_at: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Posts a balanced Double-Entry Journal Transaction inside an active BEGIN IMMEDIATE SQLite connection.
    Each leg must specify:
      - account_id: str
      - direction: 'DEBIT' | 'CREDIT'
      - amount_paise: int (> 0)
      - narration: Optional[str]
    """
    if len(legs) < 2:
        raise LedgerError(
            "Double-entry transaction requires at least 2 ledger legs (DEBIT and CREDIT).",
            code="MINIMUM_LEGS_VIOLATION",
            status_code=422,
        )

    total_debit = 0
    total_credit = 0

    for leg in legs:
        amt = int(leg.get("amount_paise", 0))
        direction = leg.get("direction", "")
        if amt <= 0:
            raise LedgerError(
                f"Ledger entry amount_paise must be a positive integer, got {amt}.",
                code="INVALID_LEDGER_AMOUNT",
                status_code=422,
            )
        if direction == "DEBIT":
            total_debit += amt
        elif direction == "CREDIT":
            total_credit += amt
        else:
            raise LedgerError(
                f"Invalid ledger direction '{direction}'. Must be 'DEBIT' or 'CREDIT'.",
                code="INVALID_LEDGER_DIRECTION",
                status_code=422,
            )

    if total_debit != total_credit:
        raise LedgerError(
            f"Double-Entry Imbalance Violation: Total Debits ({total_debit} paise) != Total Credits ({total_credit} paise).",
            code="UNBALANCED_JOURNAL_ENTRY",
            status_code=422,
        )

    now = created_at or utc_now_iso()
    final_tx_id = tx_id or f"JRN-{uuid.uuid4().hex[:10].upper()}"

    # Fetch previous transaction hash for cryptographic chain
    prev_row = conn.execute(
        "SELECT seq_no, entry_hash FROM journal_transactions ORDER BY seq_no DESC LIMIT 1"
    ).fetchone()
    prev_hash = prev_row["entry_hash"] if prev_row else GENESIS_HASH
    next_seq_no = (prev_row["seq_no"] + 1) if prev_row else 1

    # Validate accounts and update balances in deterministic order
    resolved_entries = []
    for idx, leg in enumerate(legs):
        acc_id = leg["account_id"]
        direction = leg["direction"]
        amt = int(leg["amount_paise"])
        narration = leg.get("narration") or description

        acc_row = conn.execute(
            "SELECT * FROM accounts WHERE account_id = ?", (acc_id,)
        ).fetchone()
        if not acc_row:
            raise LedgerError(
                f"Account '{acc_id}' does not exist in Chart of Accounts.",
                code="ACCOUNT_NOT_FOUND",
                status_code=404,
            )

        normal_side = acc_row["normal_side"]
        current_balance = int(acc_row["balance_paise"])

        # In double-entry accounting:
        # If normal_side == 'DEBIT' (ASSET, EXPENSE): DEBIT increases (+), CREDIT decreases (-)
        # If normal_side == 'CREDIT' (LIABILITY, EQUITY, REVENUE): CREDIT increases (+), DEBIT decreases (-)
        if direction == normal_side:
            new_balance = current_balance + amt
        else:
            new_balance = current_balance - amt

        if new_balance < 0 and not bool(acc_row["allow_negative"]):
            raise LedgerError(
                f"Insufficient funds in account '{acc_row['name']}' ({acc_row['code']}): "
                f"Available ₹{current_balance / 100:.2f}, Required ₹{amt / 100:.2f}.",
                code="INSUFFICIENT_FUNDS",
                status_code=409,
            )

        conn.execute(
            "UPDATE accounts SET balance_paise = ? WHERE account_id = ?",
            (new_balance, acc_id),
        )

        entry_id = f"ENT-{final_tx_id[4:]}-{idx + 1:02d}"
        resolved_entries.append(
            {
                "entry_id": entry_id,
                "tx_id": final_tx_id,
                "seq_no": next_seq_no,
                "account_id": acc_id,
                "account_code": acc_row["code"],
                "account_name": acc_row["name"],
                "direction": direction,
                "amount_paise": amt,
                "running_balance_paise": new_balance,
                "narration": narration,
                "created_at": now,
            }
        )

    canonical_json = canonicalize_entries(legs)
    entry_hash = compute_journal_hash(
        seq_no_hint=str(next_seq_no),
        tx_id=final_tx_id,
        tx_type=tx_type,
        reference_id=reference_id,
        total_amount_paise=total_debit,
        prev_hash=prev_hash,
        canonical_entries_json=canonical_json,
    )

    conn.execute(
        """
        INSERT INTO journal_transactions (
            seq_no, tx_id, tx_type, reference_id, description,
            total_amount_paise, currency, prev_hash, entry_hash,
            canonical_entries_json, metadata_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, 'INR', ?, ?, ?, ?, ?)
        """,
        (
            next_seq_no,
            final_tx_id,
            tx_type,
            reference_id,
            description,
            total_debit,
            prev_hash,
            entry_hash,
            canonical_json,
            json.dumps(metadata or {}),
            now,
        ),
    )

    for ent in resolved_entries:
        conn.execute(
            """
            INSERT INTO ledger_entries (
                entry_id, tx_id, seq_no, account_id, account_code, account_name,
                direction, amount_paise, running_balance_paise, narration, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ent["entry_id"],
                ent["tx_id"],
                ent["seq_no"],
                ent["account_id"],
                ent["account_code"],
                ent["account_name"],
                ent["direction"],
                ent["amount_paise"],
                ent["running_balance_paise"],
                ent["narration"],
                ent["created_at"],
            ),
        )

    return {
        "seq_no": next_seq_no,
        "tx_id": final_tx_id,
        "tx_type": tx_type,
        "reference_id": reference_id,
        "description": description,
        "total_amount_paise": total_debit,
        "total_amount_inr": round(total_debit / 100.0, 2),
        "prev_hash": prev_hash,
        "entry_hash": entry_hash,
        "entries": resolved_entries,
        "created_at": now,
    }


def verify_ledger_integrity(db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Recomputes the entire SHA-256 hash chain from Genesis, checks every transaction's
    Debit == Credit balance, verifies account balances against historical ledger entries,
    and checks global Trial Balance.
    """
    with read_conn(db_path) as conn:
        tx_rows = conn.execute(
            "SELECT * FROM journal_transactions ORDER BY seq_no ASC"
        ).fetchall()

        expected_prev_hash = GENESIS_HASH
        chain_breaks = []
        unbalanced_txs = []

        for tx in tx_rows:
            seq_no = tx["seq_no"]
            tx_id = tx["tx_id"]

            # 1. Verify ledger entries sum for this transaction
            ent_rows = conn.execute(
                "SELECT account_id, direction, amount_paise FROM ledger_entries WHERE tx_id = ? ORDER BY entry_id ASC",
                (tx_id,),
            ).fetchall()

            debits = sum(r["amount_paise"] for r in ent_rows if r["direction"] == "DEBIT")
            credits = sum(r["amount_paise"] for r in ent_rows if r["direction"] == "CREDIT")

            if debits != credits or debits != tx["total_amount_paise"]:
                unbalanced_txs.append(
                    {
                        "seq_no": seq_no,
                        "tx_id": tx_id,
                        "debits_paise": debits,
                        "credits_paise": credits,
                        "header_amount_paise": tx["total_amount_paise"],
                    }
                )

            # 2. Recompute canonical entries JSON from actual DB rows (detects silent ledger_entries tampering!)
            actual_canonical = canonicalize_entries([dict(r) for r in ent_rows])
            recomputed_hash = compute_journal_hash(
                seq_no_hint=str(seq_no),
                tx_id=tx_id,
                tx_type=tx["tx_type"],
                reference_id=tx["reference_id"],
                total_amount_paise=tx["total_amount_paise"],
                prev_hash=expected_prev_hash,
                canonical_entries_json=actual_canonical,
            )

            if tx["prev_hash"] != expected_prev_hash or tx["entry_hash"] != recomputed_hash:
                chain_breaks.append(
                    {
                        "seq_no": seq_no,
                        "tx_id": tx_id,
                        "expected_prev_hash": expected_prev_hash,
                        "stored_prev_hash": tx["prev_hash"],
                        "stored_entry_hash": tx["entry_hash"],
                        "recomputed_entry_hash": recomputed_hash,
                    }
                )

            expected_prev_hash = tx["entry_hash"]

        # 3. Global Trial Balance across all ledger_entries
        totals = conn.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN direction = 'DEBIT' THEN amount_paise ELSE 0 END), 0) AS grand_debits,
                COALESCE(SUM(CASE WHEN direction = 'CREDIT' THEN amount_paise ELSE 0 END), 0) AS grand_credits,
                COUNT(*) AS total_entries
            FROM ledger_entries
            """
        ).fetchone()

        grand_debits = int(totals["grand_debits"])
        grand_credits = int(totals["grand_credits"])
        trial_delta = grand_debits - grand_credits

        # 4. Account-level reconciliation
        accounts = conn.execute("SELECT * FROM accounts ORDER BY code ASC").fetchall()
        account_mismatches = []
        trial_balance_sheet = []

        for acc in accounts:
            sums = conn.execute(
                """
                SELECT
                    COALESCE(SUM(CASE WHEN direction = 'DEBIT' THEN amount_paise ELSE 0 END), 0) AS acc_debits,
                    COALESCE(SUM(CASE WHEN direction = 'CREDIT' THEN amount_paise ELSE 0 END), 0) AS acc_credits
                FROM ledger_entries
                WHERE account_id = ?
                """,
                (acc["account_id"],),
            ).fetchone()
            d_sum = int(sums["acc_debits"])
            c_sum = int(sums["acc_credits"])
            expected_bal = (d_sum - c_sum) if acc["normal_side"] == "DEBIT" else (c_sum - d_sum)
            stored_bal = int(acc["balance_paise"])

            if expected_bal != stored_bal:
                account_mismatches.append(
                    {
                        "account_id": acc["account_id"],
                        "code": acc["code"],
                        "name": acc["name"],
                        "expected_balance_paise": expected_bal,
                        "stored_balance_paise": stored_bal,
                    }
                )

            trial_balance_sheet.append(
                {
                    "account_id": acc["account_id"],
                    "code": acc["code"],
                    "name": acc["name"],
                    "category": acc["category"],
                    "normal_side": acc["normal_side"],
                    "owner_type": acc["owner_type"],
                    "debits_paise": d_sum,
                    "credits_paise": c_sum,
                    "balance_paise": stored_bal,
                    "balance_inr": round(stored_bal / 100.0, 2),
                }
            )

        is_valid = (
            len(chain_breaks) == 0
            and len(unbalanced_txs) == 0
            and trial_delta == 0
            and len(account_mismatches) == 0
        )

        latest_hash = tx_rows[-1]["entry_hash"] if tx_rows else GENESIS_HASH

        return {
            "verified": is_valid,
            "status": "VERIFIED_IMMUTABLE" if is_valid else "TAMPER_DETECTED_CRITICAL",
            "total_transactions": len(tx_rows),
            "total_ledger_entries": int(totals["total_entries"]),
            "grand_debits_paise": grand_debits,
            "grand_credits_paise": grand_credits,
            "grand_debits_inr": round(grand_debits / 100.0, 2),
            "grand_credits_inr": round(grand_credits / 100.0, 2),
            "trial_balance_delta_paise": trial_delta,
            "latest_merkle_root_hash": latest_hash,
            "genesis_hash": GENESIS_HASH,
            "chain_breaks": chain_breaks,
            "unbalanced_transactions": unbalanced_txs,
            "account_mismatches": account_mismatches,
            "trial_balance_sheet": trial_balance_sheet,
            "checked_at": utc_now_iso(),
        }


def simulate_ledger_tamper(db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Demonstrates cryptographic tamper detection by altering a historical ledger entry by +10000 paise (₹100)
    while storing the original value in system_config so it can be restored cleanly.
    """
    with atomic_write_tx(db_path) as conn:
        existing = conn.execute(
            "SELECT config_value FROM system_config WHERE config_key = 'tamper_backup'"
        ).fetchone()
        if existing:
            return {
                "already_tampered": True,
                "message": "Ledger already has an active simulated tamper. Run Verify or Self-Heal.",
                "backup": json.loads(existing["config_value"]),
            }

        target = conn.execute(
            """
            SELECT entry_id, tx_id, seq_no, account_id, amount_paise
            FROM ledger_entries
            ORDER BY seq_no DESC, entry_id ASC
            LIMIT 1
            """
        ).fetchone()
        if not target:
            raise LedgerError("No ledger entries available to tamper.", status_code=404)

        backup = {
            "entry_id": target["entry_id"],
            "tx_id": target["tx_id"],
            "seq_no": target["seq_no"],
            "account_id": target["account_id"],
            "original_amount_paise": int(target["amount_paise"]),
            "tampered_amount_paise": int(target["amount_paise"]) + 10000,
        }

        conn.execute(
            "UPDATE ledger_entries SET amount_paise = ? WHERE entry_id = ?",
            (backup["tampered_amount_paise"], backup["entry_id"]),
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO system_config (config_key, config_value, updated_at)
            VALUES ('tamper_backup', ?, ?)
            """,
            (json.dumps(backup), utc_now_iso()),
        )

    audit = verify_ledger_integrity(db_path)
    return {
        "tamper_injected": True,
        "compromised_entry": backup,
        "audit_result": audit,
    }


def heal_ledger_tamper(db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Restores any tampered ledger row from the cryptographic snapshot backup and re-verifies the chain.
    """
    with atomic_write_tx(db_path) as conn:
        existing = conn.execute(
            "SELECT config_value FROM system_config WHERE config_key = 'tamper_backup'"
        ).fetchone()
        if not existing:
            return {
                "healed": False,
                "message": "No active tamper found; ledger is already clean.",
                "audit_result": verify_ledger_integrity(db_path),
            }

        backup = json.loads(existing["config_value"])
        conn.execute(
            "UPDATE ledger_entries SET amount_paise = ? WHERE entry_id = ?",
            (backup["original_amount_paise"], backup["entry_id"]),
        )
        conn.execute("DELETE FROM system_config WHERE config_key = 'tamper_backup'")

    audit = verify_ledger_integrity(db_path)
    return {
        "healed": True,
        "restored_entry": backup,
        "audit_result": audit,
    }
