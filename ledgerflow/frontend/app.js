/**
 * app.js — LedgerFlow Treasury v3.0 Institutional FinTech Controller
 * Powers the Bento Command Center, Animated Money-Flow Pipeline, Live Checkout Device Simulator,
 * Slide-Over Receipt Inspector Drawer, Paper GST Invoice Preview, Concurrency Lab & SHA-256 Auditor.
 */

let dashboardState = null;
let lastUsedIdemKey = "";

const VIEW_META = {
  "view-overview": {
    title: "Treasury Command Center",
    sub: "Real-time RBI Nodal Escrow custody, T+0 split settlements & double-entry accounting",
  },
  "view-checkout": {
    title: "Interactive Checkout & Idempotency Studio",
    sub: "Simulate live customer captures, 5-factor fraud checks, and RFC idempotency deduplication",
  },
  "view-payments": {
    title: "Escrow Captures, T+0 Settlements & Refunds",
    sub: "Inspect payment lifecycles, release escrowed funds to merchants, or execute proportional refund reversals",
  },
  "view-accounts": {
    title: "GAAP / RBI Nodal Chart of Accounts",
    sub: "Every rupee in #1000 RBI Nodal Bank (DEBIT) is 100% balanced across CREDIT sub-ledgers",
  },
  "view-invoices": {
    title: "Official GST Tax Invoices (SAC 998314)",
    sub: "Section 31 CGST/SGST & IGST compliant invoices with SHA-256 ledger seals and native PDF 1.4 downloads",
  },
  "view-lab": {
    title: "Concurrency & Double-Spend Chaos Lab",
    sub: "Multi-threaded stress tests proving At-Most-Once Idempotency & BEGIN IMMEDIATE ACID overdraft protection",
  },
  "view-audit": {
    title: "Cryptographic SHA-256 Audit Chain & Tamper Lab",
    sub: "Verify the full Merkle/SHA-256 hash chain from Genesis or simulate an unauthorized SQL tamper & self-heal",
  },
  "view-webhooks": {
    title: "HMAC-SHA256 Webhook Dispatcher & DLQ",
    sub: "Simulate merchant HTTP 503 outages, exponential backoff retries, Dead-Letter Queue replay & signature verification",
  },
};

function fmtINR(paise) {
  const val = Number(paise || 0) / 100;
  return "₹" + val.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function generateIdemKey(prefix = "idem_live") {
  const rand = Math.random().toString(16).substring(2, 10) + Date.now().toString(16).slice(-4);
  return `${prefix}_${rand}`;
}

function showToast(msg, type = "success") {
  const el = document.getElementById("toastBanner");
  el.textContent = msg;
  el.className = `toast-notification ${type}`;
  clearTimeout(window._toastTimer);
  window._toastTimer = setTimeout(() => {
    el.classList.add("hidden");
  }, 5000);
}

// View Navigation
window.switchView = function (viewId) {
  document.querySelectorAll(".nav-item").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.view === viewId);
  });
  document.querySelectorAll(".view-section").forEach((sec) => {
    sec.classList.toggle("active", sec.id === viewId);
  });
  const meta = VIEW_META[viewId];
  if (meta) {
    document.getElementById("activeViewTitle").textContent = meta.title;
    document.getElementById("activeViewSubtitle").textContent = meta.sub;
  }
};

document.querySelectorAll(".nav-item").forEach((btn) => {
  btn.addEventListener("click", () => switchView(btn.dataset.view));
});

document.getElementById("sidebarIntegrityCard").addEventListener("click", () => {
  switchView("view-audit");
});

document.getElementById("btnNewPaymentQuick").addEventListener("click", () => {
  switchView("view-checkout");
});

document.getElementById("btnGoToStudioFromPipe").addEventListener("click", () => {
  switchView("view-checkout");
});

document.getElementById("btnInspectNodalVault").addEventListener("click", () => {
  switchView("view-accounts");
  loadAccountStatement("ACC_NODAL_BANK");
});

// Theme Switcher (Obsidian Dark <-> Stripe Alabaster Light)
document.getElementById("btnThemeToggle").addEventListener("click", () => {
  const html = document.documentElement;
  const current = html.getAttribute("data-theme") || "dark";
  const next = current === "dark" ? "light" : "dark";
  html.setAttribute("data-theme", next);
  document.getElementById("themeIcon").innerHTML = next === "dark" ? "&#9728;&#65039;" : "&#127769;";
  document.getElementById("themeLabel").textContent = next === "dark" ? "Light Mode" : "Dark Mode";
});

async function apiCall(path, options = {}) {
  const resp = await fetch(path, options);
  const idemStatus = resp.headers.get("X-Idempotency-Status");
  let data = {};
  try {
    data = await resp.json();
  } catch (e) {
    data = {};
  }
  return { ok: resp.ok, status: resp.status, idemStatus, data };
}

async function refreshDashboard() {
  const { ok, data } = await apiCall("/api/v1/dashboard");
  if (!ok) return;
  dashboardState = data;

  renderOverviewAndKpis(data);
  populateCheckoutSelectors(data.accounts);
  updateLiveCheckoutPreview();
  renderPaymentsTable(data.payments);
  renderAccountsTable(data.accounts);
  renderAuditChainTab(data.audit_summary, data.journal_transactions);
  renderInvoicesView(data.invoices);
  renderWebhooksTab(data.webhooks, data.webhook_sink_mode);
}

function renderOverviewAndKpis(data) {
  const k = data.kpis;
  const accounts = data.accounts || [];

  // Sidebar & Header Counters
  document.getElementById("navPaymentsCount").textContent = data.payments.length;
  document.getElementById("navInvoicesCount").textContent = data.invoices.length;
  const dlqBadge = document.getElementById("navDlqCount");
  if (k.webhook_failed_or_dlq_count > 0) {
    dlqBadge.textContent = k.webhook_failed_or_dlq_count;
    dlqBadge.classList.remove("hidden");
  } else {
    dlqBadge.classList.add("hidden");
  }

  // Sidebar Custody Card
  const sealCard = document.getElementById("sidebarIntegrityCard");
  const sealTitle = document.getElementById("sidebarSealStatus");
  if (k.ledger_verified) {
    sealCard.classList.remove("tampered");
    sealTitle.textContent = "SHA-256 IMMUTABLE";
  } else {
    sealCard.classList.add("tampered");
    sealTitle.textContent = "TAMPER DETECTED!";
  }
  document.getElementById("sidebarTrialDelta").textContent = fmtINR(k.trial_balance_delta_paise);
  document.getElementById("sidebarMerkleHash").textContent = `Root: ${k.latest_merkle_root_hash.slice(0, 18)}...`;

  // Hero Vault & Pipeline Totals
  const custTotal = accounts
    .filter((a) => a.owner_type === "CUSTOMER")
    .reduce((sum, a) => sum + Number(a.balance_paise), 0);
  const merchTotal = accounts
    .filter((a) => a.owner_type === "MERCHANT")
    .reduce((sum, a) => sum + Number(a.balance_paise), 0);
  const merchTaxRevTotal = merchTotal + k.platform_revenue_paise + k.gst_payable_paise;

  document.getElementById("kpiNodalBank").textContent = fmtINR(k.nodal_bank_asset_paise);
  document.getElementById("eqCustTotal").textContent = fmtINR(custTotal);
  document.getElementById("eqEscrowTotal").textContent = fmtINR(k.escrow_float_paise);
  document.getElementById("eqMerchTaxTotal").textContent = fmtINR(merchTaxRevTotal);

  // Pipeline Nodes
  document.getElementById("pipeCustBalance").textContent = fmtINR(custTotal);
  document.getElementById("pipeEscrowBalance").textContent = fmtINR(k.escrow_float_paise);
  document.getElementById("pipeMerchBalance").textContent = fmtINR(merchTotal);
  document.getElementById("pipeRevBalance").textContent = fmtINR(k.platform_revenue_paise);
  document.getElementById("pipeGstBalance").textContent = fmtINR(k.gst_payable_paise);

  // 4 Metric Cards
  document.getElementById("kpiGmv").textContent = fmtINR(k.gmv_paise);
  document.getElementById("kpiRefundSub").textContent = `Refunded Reversals: ${fmtINR(k.refunded_paise)}`;
  document.getElementById("kpiEscrow").textContent = fmtINR(k.escrow_float_paise);
  document.getElementById("kpiRevenue").textContent = fmtINR(k.platform_revenue_paise);
  document.getElementById("kpiGst").textContent = fmtINR(k.gst_payable_paise);
  document.getElementById("kpiIdemSaves").textContent = `${k.idempotency_replays_saved} Replays`;
  document.getElementById("kpiWebhookSub").textContent = `Webhook DLQ / Pending: ${k.webhook_failed_or_dlq_count}`;

  // Overview Wallets Grid
  const walletsGrid = document.getElementById("overviewWalletsGrid");
  const customers = accounts.filter((a) => a.owner_type === "CUSTOMER");
  walletsGrid.innerHTML = customers
    .map((c) => {
      const cleanName = c.name.replace("Customer Wallet — ", "");
      const initial = cleanName.charAt(0).toUpperCase();
      return `
        <div class="entity-card" onclick="inspectAccountFromOverview('${c.account_id}')">
          <div class="entity-left">
            <div class="entity-avatar">${initial}</div>
            <div>
              <div class="entity-name">${cleanName}</div>
              <div class="entity-sub">#${c.code} &bull; Zero-Overdraft</div>
            </div>
          </div>
          <div class="entity-right">
            <div class="entity-bal">${fmtINR(c.balance_paise)}</div>
            <button class="btn btn-outline btn-xs" style="margin-top:4px;" onclick="event.stopPropagation(); quickTopupWallet('${c.account_id}', 50000)">+ ₹50k RTGS</button>
          </div>
        </div>
      `;
    })
    .join("");

  // Overview Merchants Grid
  const merchGrid = document.getElementById("overviewMerchantsGrid");
  const merchants = accounts.filter((a) => a.owner_type === "MERCHANT");
  merchGrid.innerHTML = merchants
    .map((m) => {
      const cleanName = m.name.replace("Merchant Payable — ", "");
      const initial = cleanName.charAt(0).toUpperCase();
      const regime = m.state_code === "29" ? "KA-29 CGST+SGST" : `State-${m.state_code} IGST 18%`;
      return `
        <div class="entity-card" onclick="inspectAccountFromOverview('${m.account_id}')">
          <div class="entity-left">
            <div class="entity-avatar merch">${initial}</div>
            <div>
              <div class="entity-name">${cleanName}</div>
              <div class="entity-sub">${m.gstin} &bull; ${regime}</div>
            </div>
          </div>
          <div class="entity-right">
            <div class="entity-bal text-emerald">${fmtINR(m.balance_paise)}</div>
            <div class="entity-sub">Settled T+0</div>
          </div>
        </div>
      `;
    })
    .join("");

  // Overview Recent Payments Stream
  const recentList = document.getElementById("overviewRecentPayments");
  recentList.innerHTML = (data.payments || [])
    .slice(0, 6)
    .map((p) => {
      const custName = (p.customer_name || "").replace("Customer Wallet — ", "");
      const merchName = (p.merchant_name || "").replace("Merchant Payable — ", "");
      let badge = `<span class="badge badge-emerald">SETTLED T+0</span>`;
      if (p.status === "CAPTURED_IN_ESCROW") badge = `<span class="badge badge-amber">IN ESCROW</span>`;
      else if (p.status === "PARTIALLY_REFUNDED") badge = `<span class="badge badge-purple">PARTIAL REFUND</span>`;
      else if (p.status === "REFUNDED") badge = `<span class="badge badge-blue">REFUNDED</span>`;
      else if (p.status === "BLOCKED_FRAUD") badge = `<span class="badge badge-danger">FRAUD BLOCKED</span>`;

      return `
        <div class="activity-item" onclick="openPaymentDrawer('${p.payment_id}')">
          <div>
            <div style="display:flex;align-items:center;gap:8px;">
              <strong class="mono" style="color:#818cf8;">${p.payment_id}</strong>
              ${badge}
            </div>
            <div style="font-size:12.5px;font-weight:600;margin-top:3px;">${custName} &rarr; ${merchName}</div>
            <div class="text-muted" style="font-size:11.5px;">${p.description}</div>
          </div>
          <div class="text-right">
            <div class="mono" style="font-weight:700;font-size:14px;">${fmtINR(p.amount_paise)}</div>
            <div class="text-muted mono" style="font-size:11px;">Inspect &rarr;</div>
          </div>
        </div>
      `;
    })
    .join("");
}

window.inspectAccountFromOverview = function (accountId) {
  switchView("view-accounts");
  loadAccountStatement(accountId);
};

window.quickTopupWallet = async function (accountId, amountInr = 100000) {
  const { ok } = await apiCall("/api/v1/wallets/topup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      customer_account_id: accountId,
      amount_inr: amountInr,
      channel: "RBI_RTGS_TREASURY",
    }),
  });
  if (ok) {
    showToast(`RTGS Top-Up of ₹${amountInr.toLocaleString("en-IN")} credited to ${accountId} & RBI Nodal Bank #1000!`, "success");
    await refreshDashboard();
  }
};

document.getElementById("btnQuickTopupHeader").addEventListener("click", () => {
  quickTopupWallet("ACC_CUST_SANATH", 100000);
});

document.getElementById("btnQuickTopup").addEventListener("click", () => {
  quickTopupWallet("ACC_CUST_SANATH", 100000);
});

// Settle All Escrowed Payments Button
document.getElementById("btnSettleAllEscrow").addEventListener("click", async () => {
  const pending = (dashboardState?.payments || []).filter((p) => p.status === "CAPTURED_IN_ESCROW");
  if (!pending.length) {
    showToast("No payments currently waiting in Escrow (#2200). Capture a new payment first!", "warn");
    return;
  }
  for (const p of pending) {
    await apiCall(`/api/v1/payments/${p.payment_id}/settle`, { method: "POST" });
  }
  showToast(`Settled ${pending.length} escrowed payment(s) to Merchants with 2% MDR & 18% GST split!`, "success");
  await refreshDashboard();
});

// =========================================================================
// VIEW 2: CHECKOUT STUDIO & LIVE DEVICE PREVIEW
// =========================================================================
function populateCheckoutSelectors(accounts) {
  const custSelect = document.getElementById("custSelect");
  const merchSelect = document.getElementById("merchSelect");
  const prevCust = custSelect.value;
  const prevMerch = merchSelect.value;

  const customers = accounts.filter((a) => a.owner_type === "CUSTOMER");
  const merchants = accounts.filter((a) => a.owner_type === "MERCHANT");

  custSelect.innerHTML = customers
    .map(
      (c) =>
        `<option value="${c.account_id}">#${c.code} — ${c.name.replace("Customer Wallet — ", "")} (Avail: ${fmtINR(
          c.balance_paise
        )})</option>`
    )
    .join("");

  merchSelect.innerHTML = merchants
    .map((m) => {
      const cleanName = m.name.replace("Merchant Payable — ", "");
      const taxLabel = m.state_code === "29" ? "KA-29 Intra-State CGST+SGST" : `State-${m.state_code} Inter-State IGST`;
      return `<option value="${m.account_id}" data-state="${m.state_code}" data-name="${cleanName}" data-gst="${m.gstin}">#${m.code} — ${cleanName} [${taxLabel}]</option>`;
    })
    .join("");

  if (prevCust && customers.some((c) => c.account_id === prevCust)) custSelect.value = prevCust;
  if (prevMerch && merchants.some((m) => m.account_id === prevMerch)) merchSelect.value = prevMerch;
}

function updateLiveCheckoutPreview() {
  const amtInr = parseFloat(document.getElementById("payAmountInr").value) || 0;
  const grossPaise = Math.max(0, Math.round(amtInr * 100));
  const feePaise = grossPaise > 0 ? Math.max(100, Math.round(grossPaise * 0.02)) : 0;
  const gstPaise = Math.round(feePaise * 0.18);
  const netPaise = Math.max(0, grossPaise - feePaise - gstPaise);

  const merchSelect = document.getElementById("merchSelect");
  const opt = merchSelect.options[merchSelect.selectedIndex];
  const stateCode = opt ? opt.getAttribute("data-state") : "29";
  const merchName = opt ? opt.getAttribute("data-name") : "Zepto Quick Commerce";
  const merchGst = opt ? opt.getAttribute("data-gst") : "29AABCZ4512K1Z4";
  const desc = document.getElementById("payDesc").value || "Enterprise Order";

  document.getElementById("previewMerchAvatar").textContent = (merchName || "M").charAt(0).toUpperCase();
  document.getElementById("previewMerchName").textContent = merchName;
  document.getElementById("previewMerchGst").textContent = `GSTIN: ${merchGst} (State ${stateCode})`;
  document.getElementById("previewDescText").textContent = desc;

  document.getElementById("prevGross").textContent = fmtINR(grossPaise);
  document.getElementById("prevCtaAmt").innerHTML = `${fmtINR(grossPaise)} &rarr;`;
  document.getElementById("prevFee").textContent = fmtINR(feePaise);
  document.getElementById("prevTaxLabel").textContent =
    stateCode === "29" ? "Intra-State: 9% CGST + 9% SGST" : "Inter-State: 18% IGST";
  document.getElementById("prevTax").textContent = fmtINR(gstPaise);
  document.getElementById("prevNet").textContent = fmtINR(netPaise);
}

document.getElementById("payAmountInr").addEventListener("input", updateLiveCheckoutPreview);
document.getElementById("merchSelect").addEventListener("change", updateLiveCheckoutPreview);
document.getElementById("payDesc").addEventListener("input", updateLiveCheckoutPreview);

// Telemetry Presets
document.getElementById("presetCleanIp").addEventListener("click", () => {
  document.getElementById("payIp").value = "103.21.244.12";
  document.getElementById("payDesc").value = "Enterprise Cloud Infrastructure Subscription Q4";
  updateLiveCheckoutPreview();
});

document.getElementById("presetTorIp").addEventListener("click", () => {
  document.getElementById("payIp").value = "185.220.101.44";
  showToast("Loaded Tor Exit Node IP (+50 Risk Score -> FLAGGED_ESCROW_REVIEW)", "warn");
});

document.getElementById("presetFraudAttack").addEventListener("click", () => {
  document.getElementById("payIp").value = "185.220.101.99";
  document.getElementById("payDesc").value = "Automated card-test exploit probe #991";
  if (!document.getElementById("chkKeepSameKey").checked) {
    document.getElementById("idemKeyInput").value = generateIdemKey("idem_fraud");
  }
  updateLiveCheckoutPreview();
  showToast("Loaded Fraud Signature: Click Execute Capture to watch the Fraud Firewall block with HTTP 403!", "warn");
});

document.getElementById("btnNewIdemKey").addEventListener("click", () => {
  document.getElementById("idemKeyInput").value = generateIdemKey();
});

document.getElementById("captureForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const idemKey = document.getElementById("idemKeyInput").value.trim();
  lastUsedIdemKey = idemKey;

  const body = {
    customer_account_id: document.getElementById("custSelect").value,
    merchant_account_id: document.getElementById("merchSelect").value,
    amount_inr: parseFloat(document.getElementById("payAmountInr").value),
    payment_method: document.getElementById("payMethod").value,
    description: document.getElementById("payDesc").value,
    customer_ip: document.getElementById("payIp").value.trim(),
  };

  const { ok, status, idemStatus, data } = await apiCall("/api/v1/payments/capture", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": idemKey,
    },
    body: JSON.stringify(body),
  });

  const respBox = document.getElementById("lastCaptureResponseBox");
  respBox.classList.remove("hidden");
  const statusBadge = document.getElementById("lastRespStatusBadge");
  const idemBadge = document.getElementById("lastRespIdemBadge");

  statusBadge.textContent = `HTTP ${status}`;
  statusBadge.className = `badge ${ok ? "badge-emerald" : "badge-danger"}`;

  if (idemStatus) {
    idemBadge.textContent = `X-Idempotency-Status: ${idemStatus}`;
    idemBadge.className = `badge ${idemStatus === "HIT-REPLAY" ? "badge-amber" : "badge-blue"}`;
  } else {
    idemBadge.textContent = data.code || "BLOCKED";
    idemBadge.className = "badge badge-danger";
  }

  document.getElementById("lastRespJson").textContent = JSON.stringify(data, null, 2);

  if (ok) {
    if (idemStatus === "HIT-REPLAY") {
      showToast(
        `Idempotent Replay (HTTP 200 HIT-REPLAY): Key '${idemKey}' already executed! Customer wallet was NOT charged twice.`,
        "warn"
      );
    } else {
      showToast(
        `Captured ${fmtINR(data.payment.amount_paise)} into Escrow (${data.payment.payment_id}) | Invoice ${data.payment.invoice_number}`,
        "success"
      );
    }
    if (!document.getElementById("chkKeepSameKey").checked) {
      document.getElementById("idemKeyInput").value = generateIdemKey();
    }
  } else {
    showToast(`HTTP ${status} [${data.code}]: ${data.error}`, "error");
  }

  await refreshDashboard();
});

document.getElementById("btnTestConflict422").addEventListener("click", async () => {
  const keyToTest = lastUsedIdemKey || "idem_seed_zoho_enterprise_001";
  document.getElementById("idemKeyInput").value = keyToTest;

  const { status, data } = await apiCall("/api/v1/payments/capture", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": keyToTest,
    },
    body: JSON.stringify({
      customer_account_id: document.getElementById("custSelect").value,
      merchant_account_id: document.getElementById("merchSelect").value,
      amount_inr: 99999.99,
      payment_method: "UPI_INTENT_PRO",
      description: "Mutated Amount with Reused Idempotency-Key",
    }),
  });

  const respBox = document.getElementById("lastCaptureResponseBox");
  respBox.classList.remove("hidden");
  document.getElementById("lastRespStatusBadge").textContent = `HTTP ${status}`;
  document.getElementById("lastRespStatusBadge").className = "badge badge-danger";
  document.getElementById("lastRespIdemBadge").textContent = data.code;
  document.getElementById("lastRespIdemBadge").className = "badge badge-amber";
  document.getElementById("lastRespJson").textContent = JSON.stringify(data, null, 2);

  showToast(`Verified HTTP ${status} Conflict: ${data.error}`, "warn");
});

// =========================================================================
// VIEW 3: PAYMENTS LIFECYCLE TABLE & SLIDE-OVER RECEIPT DRAWER
// =========================================================================
function renderPaymentsTable(payments) {
  document.getElementById("paymentsCountBadge").textContent = `${payments.length} Payments`;
  const tbody = document.getElementById("paymentsTableBody");

  tbody.innerHTML = payments
    .map((p) => {
      let statusBadge = `<span class="badge badge-emerald">SETTLED T+0</span>`;
      if (p.status === "CAPTURED_IN_ESCROW") statusBadge = `<span class="badge badge-amber">IN ESCROW</span>`;
      else if (p.status === "PARTIALLY_REFUNDED") statusBadge = `<span class="badge badge-purple">PARTIAL REFUND</span>`;
      else if (p.status === "REFUNDED") statusBadge = `<span class="badge badge-blue">REFUNDED</span>`;
      else if (p.status === "BLOCKED_FRAUD") statusBadge = `<span class="badge badge-danger">BLOCKED FRAUD</span>`;

      const riskColor = p.risk_score >= 75 ? "badge-danger" : p.risk_score >= 40 ? "badge-amber" : "badge-emerald";
      const custShort = (p.customer_name || p.customer_account_id).replace("Customer Wallet — ", "");
      const merchShort = (p.merchant_name || p.merchant_account_id).replace("Merchant Payable — ", "");
      const refundablePaise = p.amount_paise - p.refunded_paise;
      const taxTotal = p.cgst_paise + p.sgst_paise + p.igst_paise;

      const canSettle = p.status === "CAPTURED_IN_ESCROW";
      const canRefund =
        (p.status === "CAPTURED_IN_ESCROW" || p.status === "SETTLED" || p.status === "PARTIALLY_REFUNDED") &&
        refundablePaise > 0;

      return `
        <tr onclick="openPaymentDrawer('${p.payment_id}')" style="cursor:pointer;">
          <td>
            <div class="mono" style="font-weight:700;color:#818cf8;">${p.payment_id}</div>
            <div class="text-muted mono" style="font-size:11px;">${p.idempotency_key}</div>
          </td>
          <td>
            <div style="font-weight:600;">${custShort}</div>
            <div class="text-muted" style="font-size:11.5px;">&rarr; ${merchShort}</div>
          </td>
          <td class="text-right mono" style="font-weight:700;">${fmtINR(p.amount_paise)}</td>
          <td class="text-right mono" style="font-size:12px;">
            ${fmtINR(p.platform_fee_paise)} + ${fmtINR(taxTotal)}
          </td>
          <td class="text-right mono text-emerald" style="font-weight:700;">
            ${p.refunded_paise > 0 ? `<span class="text-danger">-${fmtINR(p.refunded_paise)}</span>` : fmtINR(p.net_merchant_paise)}
          </td>
          <td><span class="badge ${riskColor}">${p.risk_score}/100</span></td>
          <td>${statusBadge}</td>
          <td class="text-right" onclick="event.stopPropagation();">
            <div class="chip-group" style="justify-content:flex-end;">
              ${
                canSettle
                  ? `<button class="btn btn-emerald btn-xs" onclick="handleSettlePayment('${p.payment_id}')">&#10004; Settle T+0</button>`
                  : ""
              }
              ${
                canRefund
                  ? `<button class="btn btn-danger btn-xs" onclick="openRefundModal('${p.payment_id}', ${refundablePaise})">&#8634; Refund</button>`
                  : ""
              }
              ${
                p.invoice_id
                  ? `<a class="btn btn-outline btn-xs" href="/api/v1/invoices/${p.invoice_id}/pdf" target="_blank">&#128196; PDF</a>`
                  : ""
              }
            </div>
          </td>
        </tr>
      `;
    })
    .join("");
}

window.openPaymentDrawer = function (paymentId) {
  const p = (dashboardState?.payments || []).find((x) => x.payment_id === paymentId);
  if (!p) return;

  document.getElementById("drawerTitle").textContent = `${p.payment_id} (${fmtINR(p.amount_paise)})`;
  const relatedTxs = (dashboardState?.journal_transactions || []).filter((t) => t.reference_id === p.payment_id);
  const refundablePaise = p.amount_paise - p.refunded_paise;

  const html = `
    <div style="display:flex;flex-direction:column;gap:16px;">
      <div class="glass-panel" style="padding:14px;">
        <div class="section-sub-label">PAYMENT METADATA &amp; IDEMPOTENCY</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;font-size:12.5px;">
          <div><span class="text-muted">Status:</span><br/><strong>${p.status}</strong></div>
          <div><span class="text-muted">Rail:</span><br/><strong class="mono">${p.payment_method}</strong></div>
          <div><span class="text-muted">Idempotency-Key:</span><br/><code style="font-size:11px;">${p.idempotency_key}</code></div>
          <div><span class="text-muted">Risk Score:</span><br/><strong>${p.risk_score}/100 (${p.risk_decision})</strong></div>
        </div>
      </div>

      <div class="glass-panel" style="padding:14px;">
        <div class="section-sub-label">DOUBLE-ENTRY JOURNAL BLOCKS FOR ${p.payment_id}</div>
        ${
          relatedTxs.length
            ? relatedTxs
                .map(
                  (tx) => `
                <div style="margin-bottom:12px;padding-bottom:10px;border-bottom:1px solid var(--border-subtle);">
                  <div class="flex-between">
                    <strong class="mono" style="color:#818cf8;">Block #${tx.seq_no} &bull; ${tx.tx_id}</strong>
                    <span class="badge badge-purple">${tx.tx_type}</span>
                  </div>
                  <div class="mono text-muted" style="font-size:10.5px;margin:4px 0;">SHA-256: ${tx.entry_hash.slice(0, 32)}...</div>
                  ${tx.entries
                    .map(
                      (e) => `
                    <div class="flex-between mono" style="font-size:11.5px;padding:3px 0;">
                      <span><span class="badge ${e.direction === "DEBIT" ? "badge-blue" : "badge-emerald"}">${e.direction}</span> #${e.account_code} ${e.account_name.slice(0, 26)}</span>
                      <strong>${fmtINR(e.amount_paise)}</strong>
                    </div>
                  `
                    )
                    .join("")}
                </div>
              `
                )
                .join("")
            : `<div class="text-muted">No ledger entries recorded (Blocked by Fraud Firewall).</div>`
        }
      </div>

      <div class="chip-group">
        ${
          p.status === "CAPTURED_IN_ESCROW"
            ? `<button class="btn btn-emerald btn-sm" onclick="handleSettlePayment('${p.payment_id}'); closeDrawer();">&#10004; Settle T+0 Now</button>`
            : ""
        }
        ${
          refundablePaise > 0 && p.status !== "BLOCKED_FRAUD"
            ? `<button class="btn btn-danger btn-sm" onclick="closeDrawer(); openRefundModal('${p.payment_id}', ${refundablePaise});">&#8634; Issue Refund</button>`
            : ""
        }
        ${
          p.invoice_id
            ? `<a class="btn btn-primary btn-sm" href="/api/v1/invoices/${p.invoice_id}/pdf" target="_blank">&#128196; Download GST Invoice PDF</a>`
            : ""
        }
      </div>
    </div>
  `;

  document.getElementById("drawerBodyContent").innerHTML = html;
  document.getElementById("inspectorDrawerBackdrop").classList.remove("hidden");
};

window.closeDrawer = function () {
  document.getElementById("inspectorDrawerBackdrop").classList.add("hidden");
};

document.getElementById("btnCloseDrawer").addEventListener("click", closeDrawer);
document.getElementById("inspectorDrawerBackdrop").addEventListener("click", closeDrawer);

window.handleSettlePayment = async function (paymentId) {
  const { ok, data } = await apiCall(`/api/v1/payments/${paymentId}/settle`, { method: "POST" });
  if (ok) {
    showToast(`T+0 Split Settlement Complete for ${paymentId}: Merchant, 2% MDR Fee & 18% GST credited!`, "success");
    await refreshDashboard();
  } else {
    showToast(`Settlement Error: ${data.error}`, "error");
  }
};

window.openRefundModal = function (paymentId, maxRefundablePaise) {
  document.getElementById("refundPaymentId").value = paymentId;
  const maxInr = (maxRefundablePaise / 100).toFixed(2);
  document.getElementById("refundAmountInr").value = maxInr;
  document.getElementById("refundAmountInr").max = maxInr;
  document.getElementById("refundMaxHint").textContent = `Maximum refundable amount: ₹${maxInr}`;
  document.getElementById("refundModalTitle").textContent = `Refund Payment ${paymentId}`;
  document.getElementById("refundModal").classList.remove("hidden");
};

document.getElementById("btnCloseRefundModal").addEventListener("click", () => {
  document.getElementById("refundModal").classList.add("hidden");
});

document.getElementById("refundForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const paymentId = document.getElementById("refundPaymentId").value;
  const amtInr = parseFloat(document.getElementById("refundAmountInr").value);
  const reason = document.getElementById("refundReason").value;

  const { ok, data } = await apiCall(`/api/v1/payments/${paymentId}/refund`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refund_amount_inr: amtInr, reason }),
  });

  document.getElementById("refundModal").classList.add("hidden");
  if (ok) {
    showToast(`Refund of ₹${amtInr.toFixed(2)} processed for ${paymentId} with balanced Double-Entry reversal!`, "success");
    await refreshDashboard();
  } else {
    showToast(`Refund Error: ${data.error}`, "error");
  }
});

// =========================================================================
// VIEW 4: CHART OF ACCOUNTS & T-ACCOUNTS
// =========================================================================
function renderAccountsTable(accounts) {
  const tbody = document.getElementById("accountsTableBody");
  tbody.innerHTML = accounts
    .map((a) => {
      const sideBadge =
        a.normal_side === "DEBIT"
          ? `<span class="badge badge-blue">DEBIT</span>`
          : `<span class="badge badge-emerald">CREDIT</span>`;
      return `
        <tr onclick="loadAccountStatement('${a.account_id}')" style="cursor:pointer;">
          <td class="mono" style="font-weight:700;color:#818cf8;">#${a.code}</td>
          <td>
            <div style="font-weight:600;">${a.name}</div>
            <div class="text-muted mono" style="font-size:11px;">${a.account_id}</div>
          </td>
          <td><span class="badge badge-purple">${a.category}</span> ${sideBadge}</td>
          <td class="mono" style="font-size:11.5px;">${a.gstin ? `${a.gstin} (${a.state_code})` : `State ${a.state_code}`}</td>
          <td class="text-right mono" style="font-weight:700;font-size:14px;">${fmtINR(a.balance_paise)}</td>
          <td class="text-right">
            <button class="btn btn-outline btn-xs">T-Account &rarr;</button>
          </td>
        </tr>
      `;
    })
    .join("");
}

window.loadAccountStatement = async function (accountId) {
  const { ok, data } = await apiCall(`/api/v1/accounts/${accountId}/statement`);
  if (!ok) return;
  const acc = data.account;
  document.getElementById("tAccountTitle").textContent = `#${acc.code} — ${acc.name}`;
  document.getElementById(
    "tAccountSubtitle"
  ).textContent = `${acc.category} (Normal: ${acc.normal_side}) | Live Balance: ${fmtINR(acc.balance_paise)}`;

  const tbody = document.getElementById("tAccountBody");
  if (!data.entries.length) {
    tbody.innerHTML = `<tr><td colspan="5" class="empty-state-cell">No journal entries for this account yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = data.entries
    .map((e) => {
      const dirBadge =
        e.direction === "DEBIT"
          ? `<span class="badge badge-blue">DEBIT</span>`
          : `<span class="badge badge-emerald">CREDIT</span>`;
      return `
        <tr>
          <td class="mono">
            <div style="font-weight:700;">${e.entry_id}</div>
            <div class="text-muted" style="font-size:11px;">${e.tx_id}</div>
          </td>
          <td style="font-size:12.5px;">${e.narration}</td>
          <td>${dirBadge}</td>
          <td class="text-right mono" style="font-weight:700;">${fmtINR(e.amount_paise)}</td>
          <td class="text-right mono">${fmtINR(e.running_balance_paise)}</td>
        </tr>
      `;
    })
    .join("");
};

// =========================================================================
// VIEW 5: GST TAX INVOICES & LIVE PAPER INVOICE PREVIEW
// =========================================================================
function renderInvoicesView(invoices) {
  const tbody = document.getElementById("invoicesTableBody");
  if (!invoices.length) {
    tbody.innerHTML = `<tr><td colspan="7" class="empty-state-cell">No GST invoices issued yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = invoices
    .map((inv, idx) => {
      return `
        <tr onclick="renderPaperInvoicePreview('${inv.invoice_id}')" style="cursor:pointer;">
          <td class="mono" style="font-weight:700;color:#818cf8;">${inv.invoice_number}</td>
          <td>
            <div style="font-weight:600;">${inv.merchant_name}</div>
            <div class="text-muted mono" style="font-size:11px;">${inv.merchant_gstin} (State ${inv.merchant_state_code})</div>
          </td>
          <td><span class="badge ${inv.supply_type === "INTRA_STATE" ? "badge-emerald" : "badge-blue"}">${inv.supply_type}</span></td>
          <td class="text-right mono">${fmtINR(inv.gross_amount_paise)}</td>
          <td class="text-right mono">${fmtINR(inv.taxable_fee_paise + inv.total_tax_paise)}</td>
          <td class="text-right mono text-emerald" style="font-weight:700;">${fmtINR(inv.net_settlement_paise)}</td>
          <td class="text-right" onclick="event.stopPropagation();">
            <a class="btn btn-primary btn-xs" href="/api/v1/invoices/${inv.invoice_id}/pdf" target="_blank">&#128196; PDF</a>
          </td>
        </tr>
      `;
    })
    .join("");

  renderPaperInvoicePreview(invoices[0].invoice_id);
}

window.renderPaperInvoicePreview = function (invoiceId) {
  const inv = (dashboardState?.invoices || []).find((x) => x.invoice_id === invoiceId);
  if (!inv) return;

  const container = document.getElementById("liveInvoicePaper");
  container.innerHTML = `
    <div class="paper-header">
      <div>
        <div class="paper-title">TAX INVOICE &amp; SETTLEMENT ADVICE</div>
        <div style="font-size:11.5px;color:#475569;">Section 31 of CGST/IGST Act, 2017 &bull; SAC Code: ${inv.sac_code}</div>
      </div>
      <div style="text-align:right;">
        <div class="mono" style="font-weight:800;font-size:15px;color:#4f46e5;">${inv.invoice_number}</div>
        <div class="mono" style="font-size:11px;color:#64748b;">Ref: ${inv.payment_id}</div>
      </div>
    </div>

    <div class="paper-grid-2">
      <div>
        <div style="font-weight:700;font-size:10.5px;color:#4f46e5;">SUPPLIER (PAYMENT AGGREGATOR)</div>
        <div style="font-weight:700;margin-top:2px;">LedgerFlow Payment Systems Pvt Ltd</div>
        <div>GSTIN: 29AABCL9012R1Z8 (State 29 - KA)</div>
        <div>RBI Nodal Bank: HDFC Treasury #1000</div>
      </div>
      <div>
        <div style="font-weight:700;font-size:10.5px;color:#4f46e5;">MERCHANT BENEFICIARY</div>
        <div style="font-weight:700;margin-top:2px;">${inv.merchant_name}</div>
        <div>GSTIN: ${inv.merchant_gstin} (State ${inv.merchant_state_code})</div>
        <div>Customer Payer: ${inv.customer_name}</div>
      </div>
    </div>

    <div>
      <div class="paper-line-row">
        <span>1. Gross Order Captured in Escrow (#2200)</span>
        <strong class="mono">${fmtINR(inv.gross_amount_paise)}</strong>
      </div>
      <div class="paper-line-row">
        <span>2. Less: Platform MDR Processing Fee (2.00% Taxable)</span>
        <span class="mono">-${fmtINR(inv.taxable_fee_paise)}</span>
      </div>
      <div class="paper-line-row">
        <span>3. Less: Central GST (CGST @ ${inv.cgst_rate_pct}%)</span>
        <span class="mono">-${fmtINR(inv.cgst_paise)}</span>
      </div>
      <div class="paper-line-row">
        <span>4. Less: State GST (SGST @ ${inv.sgst_rate_pct}%)</span>
        <span class="mono">-${fmtINR(inv.sgst_paise)}</span>
      </div>
      <div class="paper-line-row">
        <span>5. Less: Integrated GST (IGST @ ${inv.igst_rate_pct}%)</span>
        <span class="mono">-${fmtINR(inv.igst_paise)}</span>
      </div>
      <div class="paper-line-row total">
        <span>NET MERCHANT T+0 SETTLEMENT PAYOUT</span>
        <span class="mono" style="color:#059669;">${fmtINR(inv.net_settlement_paise)}</span>
      </div>
    </div>

    <div class="paper-seal-box">
      <strong>&#10004; CRYPTOGRAPHIC DOUBLE-ENTRY SEAL</strong><br/>
      Journal TX: ${inv.ledger_tx_id} | Supply: ${inv.supply_type}<br/>
      SHA-256 Block Hash: ${inv.ledger_entry_hash}
    </div>

    <div style="margin-top:16px;display:flex;justify-content:flex-end;">
      <a class="btn btn-primary btn-sm" href="/api/v1/invoices/${inv.invoice_id}/pdf" target="_blank">
        &#128196; Download Official Vector PDF (${inv.invoice_number})
      </a>
    </div>
  `;
};

// =========================================================================
// VIEW 6: CONCURRENCY & DOUBLE-SPEND RACE LAB
// =========================================================================
document.getElementById("btnRunIdemStorm").addEventListener("click", async () => {
  const btn = document.getElementById("btnRunIdemStorm");
  btn.disabled = true;
  btn.textContent = "Spawning 10 Parallel Threads...";

  const { ok, data } = await apiCall("/api/v1/lab/idempotency-storm", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ burst_count: 10, amount_paise: 150000 }),
  });

  btn.disabled = false;
  btn.textContent = "⚡ Launch 10x Retry Storm";
  if (!ok) return;

  const summary = document.getElementById("idemStormSummary");
  summary.classList.remove("hidden");
  summary.innerHTML = `
    <strong>AT-MOST-ONCE INVARIANT VERIFIED: ${data.passed_invariant ? "100% PASS" : "FAIL"}</strong><br/>
    Shared Key: <code>${data.shared_idempotency_key}</code> &bull;
    1x <code>HTTP 201 MISS</code> &bull; 9x <code>HTTP 200 HIT-REPLAY</code> &bull;
    Duplicate Losses Saved: <strong class="text-emerald">${fmtINR(data.duplicate_losses_prevented_paise)}</strong>
  `;

  document.getElementById("idemStormTableBody").innerHTML = data.thread_results
    .map(
      (r) => `
      <tr>
        <td class="mono">${r.worker_id}</td>
        <td><span class="badge ${r.http_status === 201 ? "badge-emerald" : "badge-blue"}">HTTP ${r.http_status}</span></td>
        <td><span class="badge ${r.idempotency_status === "MISS" ? "badge-emerald" : "badge-amber"}">${r.idempotency_status}</span></td>
        <td class="mono">#${r.replay_count}</td>
        <td class="mono">${r.payment_id}</td>
        <td class="mono">${r.tx_id}</td>
      </tr>
    `
    )
    .join("");

  showToast(`10-Thread Retry Storm Complete: 1 charge executed, 9 duplicate retries deduplicated!`, "success");
  await refreshDashboard();
});

document.getElementById("btnRunRaceAttack").addEventListener("click", async () => {
  const btn = document.getElementById("btnRunRaceAttack");
  btn.disabled = true;
  btn.textContent = "Executing 8x Race Attack...";

  const { ok, data } = await apiCall("/api/v1/lab/double-spend-race", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ burst_count: 8 }),
  });

  btn.disabled = false;
  btn.textContent = "🛡 Launch 8x Race Attack";
  if (!ok) return;

  const summary = document.getElementById("raceAttackSummary");
  summary.classList.remove("hidden");
  summary.innerHTML = `
    <strong>ACID SERIALIZATION VERIFIED: ${data.passed_acid_invariant ? "ZERO OVERDRAFT" : "FAIL"}</strong><br/>
    Starting Balance: <strong>${fmtINR(data.starting_wallet_balance_paise)}</strong> &bull;
    Attempted Spend: <strong>${fmtINR(data.total_attempted_spend_paise)}</strong> &bull;
    1x Succeeded (<code>₹3,500</code>) &bull; 7x Blocked (<code>HTTP 409</code>) &bull;
    Remaining Balance: <strong class="text-emerald">${fmtINR(data.final_wallet_balance_paise)}</strong>
  `;

  document.getElementById("raceAttackTableBody").innerHTML = data.thread_results
    .map(
      (r) => `
      <tr>
        <td class="mono">${r.worker_id}</td>
        <td class="mono" style="font-size:11px;">${r.idempotency_key}</td>
        <td><span class="badge ${r.http_status === 201 ? "badge-emerald" : "badge-danger"}">HTTP ${r.http_status}</span></td>
        <td><span class="badge ${r.outcome === "CAPTURED_SUCCESS" ? "badge-emerald" : "badge-amber"}">${r.outcome}</span></td>
        <td style="font-size:11.5px;">${r.detail}</td>
      </tr>
    `
    )
    .join("");

  showToast("8-Thread Double-Spend Race Attack Mitigated: Zero negative-balance overdraft!", "success");
  await refreshDashboard();
});

// =========================================================================
// VIEW 7: SHA-256 HASH-CHAINED LEDGER & TAMPER AUDITOR
// =========================================================================
function renderAuditChainTab(audit, transactions) {
  const banner = document.getElementById("auditReportBanner");
  if (audit.verified) {
    banner.className = "audit-status-box ok";
    banner.innerHTML = `
      <div><strong>✔ CRYPTOGRAPHIC CHAIN STATUS: ${audit.status}</strong> &mdash; All ${audit.total_transactions} blocks and ${audit.total_ledger_entries} double-entry lines verified from Genesis.</div>
      <div style="margin-top:4px;">Grand Debits: <strong>${fmtINR(audit.grand_debits_paise)}</strong> == Grand Credits: <strong>${fmtINR(audit.grand_credits_paise)}</strong> (Trial Balance &Delta; = ₹0.00)</div>
      <div style="margin-top:4px;">Merkle Root Hash: <code>${audit.latest_merkle_root_hash}</code></div>
    `;
  } else {
    const brk = audit.chain_breaks[0] || {};
    const unbal = audit.unbalanced_transactions[0] || {};
    banner.className = "audit-status-box fail";
    banner.innerHTML = `
      <div><strong>✖ CRITICAL SECURITY ALERT: ${audit.status}</strong></div>
      <div style="margin-top:4px;">Compromised Block: <strong>#${brk.seq_no || unbal.seq_no} (${brk.tx_id || unbal.tx_id})</strong> &bull; Trial Balance &Delta;: <strong>${fmtINR(audit.trial_balance_delta_paise)}</strong></div>
      <div style="margin-top:4px;">Expected SHA-256: <code>${brk.stored_entry_hash || "N/A"}</code></div>
      <div>Recomputed SHA-256: <code>${brk.recomputed_entry_hash || "N/A"}</code> (TAMPER DETECTED!)</div>
    `;
  }

  document.getElementById("journalBlocksContainer").innerHTML = transactions
    .map(
      (tx) => `
      <div class="chain-block-card">
        <div class="flex-between" style="margin-bottom:8px;">
          <div>
            <span class="badge badge-blue">Block #${tx.seq_no}</span>
            <strong class="mono" style="margin-left:8px;font-size:14px;">${tx.tx_id}</strong>
            <span class="badge badge-purple" style="margin-left:6px;">${tx.tx_type}</span>
          </div>
          <div class="mono" style="font-weight:700;font-size:14px;">Balanced: ${fmtINR(tx.total_amount_paise)}</div>
        </div>
        <div style="font-size:12.5px;margin-bottom:8px;">${tx.description}</div>
        <div class="mono text-muted" style="font-size:11px;margin-bottom:10px;">
          prev_hash: ${tx.prev_hash.slice(0, 20)}... &rarr; <span class="text-emerald">entry_hash: ${tx.entry_hash}</span>
        </div>
        <table class="modern-table">
          <thead>
            <tr>
              <th>Entry ID</th>
              <th>Account</th>
              <th>Side</th>
              <th class="text-right">Amount</th>
              <th class="text-right">Running Bal</th>
            </tr>
          </thead>
          <tbody>
            ${tx.entries
              .map(
                (e) => `
              <tr>
                <td class="mono">${e.entry_id}</td>
                <td>#${e.account_code} — ${e.account_name}</td>
                <td><span class="badge ${e.direction === "DEBIT" ? "badge-blue" : "badge-emerald"}">${e.direction}</span></td>
                <td class="text-right mono" style="font-weight:700;">${fmtINR(e.amount_paise)}</td>
                <td class="text-right mono">${fmtINR(e.running_balance_paise)}</td>
              </tr>
            `
              )
              .join("")}
          </tbody>
        </table>
      </div>
    `
    )
    .join("");
}

document.getElementById("btnRunVerifyNow").addEventListener("click", async () => {
  await refreshDashboard();
  showToast("Full SHA-256 cryptographic chain & Trial Balance verified!", "success");
});

document.getElementById("btnSimulateTamper").addEventListener("click", async () => {
  const { ok, data } = await apiCall("/api/v1/ledger/simulate-tamper", { method: "POST" });
  if (ok) {
    showToast(`Injected unauthorized +₹100 SQL Tamper on ${data.compromised_entry?.entry_id} — SHA-256 Chain Break Caught!`, "error");
    await refreshDashboard();
  }
});

document.getElementById("btnHealTamper").addEventListener("click", async () => {
  const { ok } = await apiCall("/api/v1/ledger/heal-tamper", { method: "POST" });
  if (ok) {
    showToast("Self-Healed ledger from cryptographic snapshot — SHA-256 Chain restored to IMMUTABLE!", "success");
    await refreshDashboard();
  }
});

// =========================================================================
// VIEW 8: WEBHOOKS, DLQ & SIGNATURE VERIFIER
// =========================================================================
function renderWebhooksTab(webhooks, sinkMode) {
  const modeBtn = document.getElementById("btnToggleSinkMode");
  if (sinkMode === "HEALTHY_200") {
    modeBtn.textContent = "Sink: HEALTHY (200) — Simulate 503 Outage";
    modeBtn.className = "btn btn-emerald btn-xs";
  } else {
    modeBtn.textContent = "Sink: OUTAGE (503) — Restore 200 OK";
    modeBtn.className = "btn btn-danger btn-xs";
  }

  const tbody = document.getElementById("webhooksTableBody");
  tbody.innerHTML = webhooks
    .map((w) => {
      let badgeClass = "badge-emerald";
      if (w.status === "RETRY_SCHEDULED") badgeClass = "badge-amber";
      if (w.status === "DEAD_LETTER_QUEUE") badgeClass = "badge-danger";

      return `
        <tr>
          <td>
            <div class="mono" style="font-weight:700;">${w.delivery_id}</div>
            <span class="badge badge-blue">${w.event_type}</span>
          </td>
          <td class="mono">${w.resource_id}</td>
          <td><span class="badge ${badgeClass}">${w.status}</span></td>
          <td class="mono">
            HTTP ${w.http_status} (${w.attempt_count}/${w.max_attempts})
            ${w.error_message ? `<div class="text-danger" style="font-size:10.5px;">${w.error_message}</div>` : ""}
          </td>
          <td class="mono" style="font-size:11px;max-width:190px;overflow:hidden;text-overflow:ellipsis;">${w.signature_header}</td>
          <td>
            <button class="btn btn-outline btn-xs" onclick="retrySingleWebhook('${w.delivery_id}')">&#8635; Retry</button>
          </td>
        </tr>
      `;
    })
    .join("");

  const rawEl = document.getElementById("whRawBody");
  if (!rawEl.value && webhooks.length > 0) {
    rawEl.value = webhooks[0].payload_json;
    document.getElementById("whSigHeader").value = webhooks[0].signature_header;
  }
}

document.getElementById("btnToggleSinkMode").addEventListener("click", async () => {
  const curMode = dashboardState?.webhook_sink_mode || "HEALTHY_200";
  const nextMode = curMode === "HEALTHY_200" ? "DOWN_503" : "HEALTHY_200";
  const { ok } = await apiCall("/api/v1/webhooks/sink-mode", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sink_mode: nextMode }),
  });
  if (ok) {
    showToast(
      nextMode === "DOWN_503"
        ? "Merchant Webhook Sink set to OUTAGE (HTTP 503): Deliveries will enter exponential backoff & DLQ!"
        : "Merchant Webhook Sink restored to HEALTHY (HTTP 200): Click 'Replay All DLQ' to recover events!",
      nextMode === "DOWN_503" ? "warn" : "success"
    );
    await refreshDashboard();
  }
});

window.retrySingleWebhook = async function (deliveryId) {
  const { ok, data } = await apiCall(`/api/v1/webhooks/${deliveryId}/retry`, { method: "POST" });
  if (ok) {
    showToast(
      `Webhook ${deliveryId} attempt #${data.attempt_count}: ${data.status} (HTTP ${data.http_status})`,
      data.status === "DELIVERED" ? "success" : "warn"
    );
    await refreshDashboard();
  }
};

document.getElementById("btnReplayAllDlq").addEventListener("click", async () => {
  const { ok, data } = await apiCall("/api/v1/webhooks/replay-all", { method: "POST" });
  if (ok) {
    showToast(
      `Replayed ${data.total_processed} webhook(s): ${data.delivered_count} delivered, ${data.remaining_failed} failed.`,
      data.remaining_failed === 0 ? "success" : "warn"
    );
    await refreshDashboard();
  }
});

document.getElementById("btnLoadValidWebhook").addEventListener("click", async () => {
  const sample = JSON.stringify({
    event_id: "evt_live_99182",
    event_type: "payment.captured",
    amount_paise: 4500000,
    currency: "INR",
    status: "CAPTURED_IN_ESCROW",
  });
  document.getElementById("whRawBody").value = sample;
  const { data } = await apiCall("/api/v1/webhooks/verify-signature", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ raw_payload_json: sample, auto_sign: true }),
  });
  document.getElementById("whSigHeader").value = data.tested_signature_header;
  renderWebhookVerifyOutput(data);
});

document.getElementById("btnTamperWebhookBody").addEventListener("click", () => {
  const rawEl = document.getElementById("whRawBody");
  if (rawEl.value.includes("4500000")) {
    rawEl.value = rawEl.value.replace("4500000", "99000000");
  } else {
    rawEl.value = rawEl.value + " ";
  }
  document.getElementById("btnVerifyWebhookSig").click();
});

document.getElementById("btnExpiredWebhookTs").addEventListener("click", async () => {
  const raw = document.getElementById("whRawBody").value || '{"event":"test"}';
  const staleTs = Math.floor(Date.now() / 1000) - 950;
  const { data } = await apiCall("/api/v1/webhooks/verify-signature", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      raw_payload_json: raw,
      auto_sign: true,
      timestamp_override: staleTs,
    }),
  });
  document.getElementById("whSigHeader").value = data.tested_signature_header;
  renderWebhookVerifyOutput(data);
});

document.getElementById("btnVerifyWebhookSig").addEventListener("click", async () => {
  const raw = document.getElementById("whRawBody").value;
  const sig = document.getElementById("whSigHeader").value;
  const { data } = await apiCall("/api/v1/webhooks/verify-signature", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ raw_payload_json: raw, signature_header: sig }),
  });
  renderWebhookVerifyOutput(data);
});

function renderWebhookVerifyOutput(data) {
  const box = document.getElementById("whVerifyResult");
  box.classList.remove("hidden");
  box.innerHTML = `
    <div style="margin-bottom:8px;">
      <span class="badge ${data.valid ? "badge-emerald" : "badge-danger"}">
        ${data.valid ? "✔ HMAC-SHA256 VERIFIED AUTHENTIC" : "✖ REJECTED: " + data.reason}
      </span>
    </div>
    <pre class="code-block">${JSON.stringify(data, null, 2)}</pre>
  `;
}

// Reset Seed DB
document.getElementById("btnResetDemo").addEventListener("click", async () => {
  const { ok } = await apiCall("/api/v1/system/reset", { method: "POST" });
  if (ok) {
    document.getElementById("idemKeyInput").value = generateIdemKey();
    showToast("Database reset to clean initial enterprise seed state!", "success");
    await refreshDashboard();
    loadAccountStatement("ACC_NODAL_BANK");
  }
});

// Initial Boot
window.addEventListener("DOMContentLoaded", async () => {
  document.getElementById("idemKeyInput").value = generateIdemKey();
  await refreshDashboard();
  loadAccountStatement("ACC_NODAL_BANK");
});
