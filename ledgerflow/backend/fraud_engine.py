#!/usr/bin/env python3
"""
fraud_engine.py — Real-Time 5-Factor Payment Fraud & Velocity Risk Scoring Engine
Evaluates every transaction before ledger execution and returns a deterministic
Risk Score (0-100), triggered rule breakdown, and enforcement decision.
"""

import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

HIGH_RISK_IP_PREFIXES = ("185.220.", "45.155.", "198.98.", "91.219.")


def evaluate_payment_risk(
    conn: sqlite3.Connection,
    customer_account_id: str,
    merchant_account_id: str,
    amount_paise: int,
    payment_method: str,
    customer_ip: str = "103.21.244.12",
    description: str = "",
) -> Dict[str, Any]:
    score = 0
    reasons: List[Dict[str, Any]] = []

    # 1. High-Ticket Threshold Check
    amount_inr = amount_paise / 100.0
    if amount_inr >= 500000:
        score += 55
        reasons.append(
            {
                "rule": "HIGH_VALUE_RTGS_LIMIT",
                "points": 55,
                "detail": f"Transaction amount ₹{amount_inr:,.2f} exceeds ₹5,00,000 instant capture ceiling.",
            }
        )
    elif amount_inr >= 150000:
        score += 25
        reasons.append(
            {
                "rule": "ELEVATED_TICKET_SIZE",
                "points": 25,
                "detail": f"High-value ticket ₹{amount_inr:,.2f} (> ₹1,50,000 threshold).",
            }
        )

    # 2. Sliding-Window Velocity Check (Last 60 seconds)
    cutoff_60s = (datetime.now(timezone.utc) - timedelta(seconds=60)).strftime(
        "%Y-%m-%dT%H:%M:%S"
    )
    recent_row = conn.execute(
        """
        SELECT COUNT(*) AS cnt
        FROM payments
        WHERE customer_account_id = ? AND created_at >= ?
        """,
        (customer_account_id, cutoff_60s),
    ).fetchone()
    recent_cnt = int(recent_row["cnt"]) if recent_row else 0
    if recent_cnt >= 15:
        score += 45
        reasons.append(
            {
                "rule": "VELOCITY_BURST_60S",
                "points": 45,
                "detail": f"{recent_cnt} transactions from customer in last 60s (velocity burst).",
            }
        )
    elif recent_cnt >= 6:
        score += 15
        reasons.append(
            {
                "rule": "MODERATE_VELOCITY_60S",
                "points": 15,
                "detail": f"{recent_cnt} transactions from customer in last 60s.",
            }
        )

    # 3. Suspicious IP / Tor Exit Node Check
    ip_clean = (customer_ip or "103.21.244.12").strip()
    if any(ip_clean.startswith(prefix) for prefix in HIGH_RISK_IP_PREFIXES):
        score += 50
        reasons.append(
            {
                "rule": "TOR_EXIT_OR_DARKNET_IP",
                "points": 50,
                "detail": f"Source IP {ip_clean} matches known anonymizer / high-risk ASN.",
            }
        )

    # 4. Card-Testing / Description Pattern Check
    desc_lower = (description or "").lower()
    if any(tok in desc_lower for tok in ("card-test", "stolen", "fraud-probe", "exploit", "darkweb")):
        score += 80
        reasons.append(
            {
                "rule": "KNOWN_FRAUD_SIGNATURE",
                "points": 80,
                "detail": "Payload metadata matches known card-testing / fraudulent signature.",
            }
        )

    # 5. Wallet Drain Ratio Check
    acc_row = conn.execute(
        "SELECT balance_paise FROM accounts WHERE account_id = ?",
        (customer_account_id,),
    ).fetchone()
    if acc_row and int(acc_row["balance_paise"]) > 0:
        bal = int(acc_row["balance_paise"])
        drain_ratio = amount_paise / float(bal)
        if drain_ratio > 0.95 and amount_inr >= 50000:
            score += 20
            reasons.append(
                {
                    "rule": "WALLET_SWEEP_RATIO",
                    "points": 20,
                    "detail": f"Transaction sweeps {drain_ratio * 100:.1f}% of available wallet balance.",
                }
            )

    score = min(100, score)
    if score >= 75:
        decision = "BLOCK_FRAUD"
    elif score >= 40:
        decision = "FLAGGED_ESCROW_REVIEW"
    else:
        decision = "ALLOW"
        if not reasons:
            reasons.append(
                {
                    "rule": "CLEAN_TELEMETRY",
                    "points": 0,
                    "detail": "Passed velocity, ticket-size, ASN geo-IP, and behavioral checks.",
                }
            )

    return {
        "risk_score": score,
        "decision": decision,
        "reasons": reasons,
        "customer_ip": ip_clean,
    }
