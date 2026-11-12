# LedgerFlow Enterprise — Idempotent FinTech Payment Gateway, Double-Entry ACID Ledger & GST Invoice Engine

**LedgerFlow (`v2.4.0-ACID`)** is a production-grade financial payment gateway, double-entry accounting engine, fraud velocity firewall, and GST invoicing platform modeled after **Stripe Treasury & RazorpayX Nodal Escrow Systems**.

---

## Core Architectural Guarantees

1. **Strict Double-Entry ACID Bookkeeping (`backend/ledger_engine.py`)**
   - Every financial mutation (`WALLET_TOPUP_RTGS`, `PAYMENT_ESCROW_CAPTURE`, `MERCHANT_T0_SETTLEMENT`, `PAYMENT_REFUND_REVERSAL`) executes inside a serialized SQLite `WAL` + `BEGIN IMMEDIATE` transaction.
   - Enforces $\sum \text{Debits} = \sum \text{Credits}$ in exact integer minor units (**paise** — `₹1.00 = 100 paise`), eliminating IEEE-754 floating-point drift.
   - **RBI Nodal Custody Invariant**:
     $$\text{RBI Nodal Bank Asset (\#1000 DEBIT)} \equiv \sum \text{Customer Wallets} + \text{Escrow Hold} + \sum \text{Merchant Payables} + \text{Platform MDR Revenue} + \text{GST Tax Liability}$$

2. **RFC-Compliant At-Most-Once Idempotency Engine (`backend/idempotency.py`)**
   - Inspects the `Idempotency-Key` header and computes a canonical `SHA-256` hash of the request payload:
     - **`MISS` (`HTTP 201`)**: First execution commits the journal entry and caches the response atomically.
     - **`HIT-REPLAY` (`HTTP 200`)**: Duplicate retries with the same key and payload return the cached response without touching account balances.
     - **`CONFLICT` (`HTTP 422 IDEMPOTENCY_PAYLOAD_MISMATCH`)**: Reusing an existing `Idempotency-Key` with a mutated amount or beneficiary is rejected.

3. **Concurrency & `TOCTOU` Double-Spend Race-Condition Lab (`backend/payment_flows.py`)**
   - **10-Thread Parallel Retry Storm**: Fires 10 simultaneous threads sharing the same `Idempotency-Key`, proving `1x MISS` and `9x HIT-REPLAY`.
   - **8-Thread Double-Spend Attack**: Fires 8 simultaneous threads attempting to spend `₹3,500` each from a `₹5,000` wallet with distinct keys, proving `BEGIN IMMEDIATE` locking allows `1x HTTP 201` and blocks `7x HTTP 409 INSUFFICIENT_FUNDS`.

4. **Cryptographic SHA-256 Hash-Chained Audit Trail (`backend/ledger_engine.py`)**
   - Each journal transaction block `i` computes:
     $$H_i = \text{SHA256}(\text{seq\_no} \parallel \text{tx\_id} \parallel \text{tx\_type} \parallel \text{amount\_paise} \parallel H_{i-1} \parallel \text{canonical\_entries\_json})$$
   - Includes a live **Tamper Simulator & Self-Healing Auditor** that detects unauthorized 1-paise database edits by recomputing the Merkle/SHA-256 chain from Genesis (`0000...0000`).

5. **Automated T+0 Merchant Settlement, GST Tax Split (`SAC 998314`) & Native Vector PDF 1.4 Engine (`backend/pdf_generator.py`)**
   - Automatically calculates `2.00%` Platform MDR Fee and `18.0%` GST:
     - **Intra-State (Karnataka `29`)**: `9.0% CGST + 9.0% SGST`
     - **Inter-State (`33` Tamil Nadu / `27` Maharashtra)**: `18.0% IGST`
   - Generates downloadable, standards-compliant `%PDF-1.4` Tax Invoices (`/api/v1/invoices/{id}/pdf`) and SOC-2 / RBI Trial Balance Audit Certificates (`/api/v1/ledger/audit-report.pdf`).

6. **HMAC-SHA256 Webhook Dispatcher, Exponential Backoff & Dead-Letter Queue (`backend/webhook_engine.py`)**
   - Signs webhook payloads with `X-LedgerFlow-Signature: t=<unix_timestamp>,v1=<hmac_sha256_hex>`.
   - Enforces constant-time digest verification (`hmac.compare_digest`) and a 300-second replay-protection window.
   - Supports simulated merchant `HTTP 503` outages, exponential backoff (`2^attempt` seconds), Dead-Letter Queue (`DLQ`) isolation, and 1-click bulk replay.

---

## Quick Start (Zero External Dependencies Required)

```bash
# 1. Run the 9-test integration & concurrency suite
python3 -m unittest discover -s tests -t . -v

# 2. Start the live server on http://localhost:8090
python3 app.py
```

Or run with Uvicorn (ASGI):
```bash
uvicorn app:app --host 0.0.0.0 --port 8090
```
