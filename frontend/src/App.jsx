import React, { useState, useEffect } from "react";
import {
  Vault,
  ArrowUpRight,
  ArrowDownLeft,
  RefreshCw,
  Send,
  PlusCircle,
  AlertCircle,
  CheckCircle2,
  ExternalLink,
  Wallet,
  Copy,
  Check,
  ShieldCheck,
  TrendingUp,
  TrendingDown,
  Layers,
  Database,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  Clock,
  User,
  Activity
} from "lucide-react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

export default function App() {
  const [accounts, setAccounts] = useState([]);
  const [selectedAccountId, setSelectedAccountId] = useState("");
  const [accountBalance, setAccountBalance] = useState(0);
  const [transactions, setTransactions] = useState([]);
  const [pagination, setPagination] = useState({ page: 1, limit: 6, totalRecords: 0, totalPages: 1 });
  const [typeFilter, setTypeFilter] = useState(""); // "" | "credit" | "debit"
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [toast, setToast] = useState(null); // { type: 'success' | 'error', text: '' }
  const [copiedId, setCopiedId] = useState(null);

  // New Account state
  const [newAccountName, setNewAccountName] = useState("");
  const [showNewAccountModal, setShowNewAccountModal] = useState(false);

  // Action Tabs: 'credit' | 'debit' | 'transfer'
  const [activeTab, setActiveTab] = useState("credit");

  // Form states
  const [amount, setAmount] = useState("");
  const [refId, setRefId] = useState(`REF-${Math.floor(1000 + Math.random() * 9000)}`);
  const [description, setDescription] = useState("");
  const [transferDestId, setTransferDestId] = useState("");

  const notify = (type, text) => {
    setToast({ type, text });
    setTimeout(() => setToast(null), 5000);
  };

  const copyToClipboard = (text, key) => {
    navigator.clipboard.writeText(text);
    setCopiedId(key);
    setTimeout(() => setCopiedId(null), 2000);
    notify("success", "Copied to clipboard!");
  };

  // Load accounts on initial mount
  useEffect(() => {
    fetchAccounts();
  }, []);

  // Update balance and transaction ledger on selection/filter/page change
  useEffect(() => {
    if (selectedAccountId) {
      fetchBalance(selectedAccountId);
      fetchTransactions(selectedAccountId, typeFilter, pagination.page);
    }
  }, [selectedAccountId, typeFilter, pagination.page]);

  const fetchAccounts = async () => {
    try {
      const res = await fetch(`${API_BASE}/accounts`);
      if (res.ok) {
        const data = await res.json();
        setAccounts(data);
        if (data.length > 0 && !selectedAccountId) {
          setSelectedAccountId(data[0].id);
        }
      }
    } catch (err) {
      notify("error", "Cannot connect to Backend API at " + API_BASE);
    }
  };

  const fetchBalance = async (accountId) => {
    try {
      const res = await fetch(`${API_BASE}/accounts/${accountId}/balance`);
      if (res.ok) {
        const data = await res.json();
        setAccountBalance(Number(data.balance));
      }
    } catch (err) {
      console.error("Balance fetch error:", err);
    }
  };

  const fetchTransactions = async (accountId, filter, page) => {
    try {
      setLoading(true);
      let url = `${API_BASE}/accounts/${accountId}/transactions?page=${page}&limit=${pagination.limit}`;
      if (filter) url += `&type=${filter}`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setTransactions(data.transactions || []);
        setPagination({
          page: data.current_page,
          limit: data.page_size,
          totalRecords: data.total_records,
          totalPages: data.total_pages || 1
        });
      }
    } catch (err) {
      console.error("Transactions fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAccount = async (e) => {
    e.preventDefault();
    if (!newAccountName.trim()) return;

    try {
      setActionLoading(true);
      const res = await fetch(`${API_BASE}/accounts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newAccountName.trim() })
      });
      const data = await res.json();
      if (res.ok) {
        notify("success", `Account "${data.name}" created with guaranteed 0.00 initial balance!`);
        setNewAccountName("");
        setShowNewAccountModal(false);
        await fetchAccounts();
        setSelectedAccountId(data.id);
      } else {
        notify("error", data.detail?.message || "Failed to create account");
      }
    } catch (err) {
      notify("error", err.message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleTransactionSubmit = async (e) => {
    e.preventDefault();
    if (!selectedAccountId) {
      notify("error", "Select an active account first.");
      return;
    }

    try {
      setActionLoading(true);

      if (activeTab === "transfer") {
        // Bonus: Transfer API
        if (!transferDestId) {
          notify("error", "Please select a destination account.");
          setActionLoading(false);
          return;
        }

        const res = await fetch(`${API_BASE}/transfers`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            source_account_id: selectedAccountId,
            destination_account_id: transferDestId,
            amount: parseFloat(amount),
            reference_id: refId,
            description: description || "Funds Transfer"
          })
        });

        const data = await res.json();
        if (res.ok) {
          notify("success", data.message || "Transfer completed atomically!");
          resetForm();
          fetchBalance(selectedAccountId);
          fetchTransactions(selectedAccountId, typeFilter, 1);
        } else {
          notify("error", data.detail?.message || data.message || "Transfer failed");
        }
      } else {
        // Standard Credit / Debit API
        const res = await fetch(`${API_BASE}/transactions`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            account_id: selectedAccountId,
            type: activeTab,
            amount: parseFloat(amount),
            reference_id: refId,
            description: description || `${activeTab.toUpperCase()} via Web Console`
          })
        });

        const data = await res.json();
        if (res.ok) {
          notify("success", `${activeTab.toUpperCase()} transaction of $${Number(data.amount).toFixed(2)} persisted!`);
          resetForm();
          fetchBalance(selectedAccountId);
          fetchTransactions(selectedAccountId, typeFilter, 1);
        } else {
          notify("error", data.detail?.message || data.message || "Transaction rejected");
        }
      }
    } catch (err) {
      notify("error", err.message);
    } finally {
      setActionLoading(false);
    }
  };

  const resetForm = () => {
    setAmount("");
    setDescription("");
    setRefId(`REF-${Math.floor(1000 + Math.random() * 9000)}`);
  };

  const seedDemoData = async () => {
    try {
      setActionLoading(true);
      // 1. Create Alice
      const aRes = await fetch(`${API_BASE}/accounts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: "Alice Cooper" })
      });
      const alice = await aRes.json();

      // 2. Create Bob
      const bRes = await fetch(`${API_BASE}/accounts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: "Bob Dylan" })
      });
      const bob = await bRes.json();

      // 3. Fund Alice with $250.00
      await fetch(`${API_BASE}/transactions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          account_id: alice.id,
          type: "credit",
          amount: 250.00,
          reference_id: `INIT-${Math.floor(1000 + Math.random() * 9000)}`,
          description: "Initial payroll credit"
        })
      });

      notify("success", "Demo accounts created & funded with $250.00!");
      await fetchAccounts();
      setSelectedAccountId(alice.id);
    } catch (err) {
      notify("error", "Demo seed failed: " + err.message);
    } finally {
      setActionLoading(false);
    }
  };

  const selectedAccount = accounts.find((a) => a.id === selectedAccountId);

  // Compute inflow/outflow totals from currently displayed transactions
  const totalInflow = transactions
    .filter((t) => t.type === "credit")
    .reduce((sum, t) => sum + Number(t.amount), 0);

  const totalOutflow = transactions
    .filter((t) => t.type === "debit")
    .reduce((sum, t) => sum + Number(t.amount), 0);

  return (
    <div className="app-wrapper">
      {/* Toast Notification */}
      {toast && (
        <div className="toast-container">
          <div className={`toast toast-${toast.type}`}>
            {toast.type === "success" ? (
              <CheckCircle2 size={20} color="#10b981" />
            ) : (
              <AlertCircle size={20} color="#f43f5e" />
            )}
            <div style={{ flex: 1, fontSize: 13, fontWeight: 500 }}>{toast.text}</div>
          </div>
        </div>
      )}

      {/* Top Navbar */}
      <nav className="navbar">
        <div className="brand">
          <div className="brand-icon">
            <Vault size={24} />
          </div>
          <div className="brand-text">
            <h1>Apex Ledger Engine</h1>
            <p>Real-Time Financial Ledger • ACID & Idempotency Protected</p>
          </div>
        </div>

        <div className="nav-badges">
          <div className="status-badge">
            <span className="status-dot"></span>
            PostgreSQL • Supabase
          </div>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="btn-subtle"
            style={{ textDecoration: "none" }}
          >
            <ExternalLink size={14} /> Swagger API
          </a>
          <button className="btn-subtle" onClick={() => setShowNewAccountModal(true)}>
            <PlusCircle size={14} color="#6366f1" /> New Account
          </button>
        </div>
      </nav>

      {/* Account Selection Bar */}
      <div className="account-bar">
        <div className="account-selector-group">
          <div style={{ display: "flex", alignItems: "center", gap: 8, color: "var(--text-muted)", fontSize: 13, fontWeight: 600 }}>
            <User size={16} /> Active Account:
          </div>
          <select
            className="account-select"
            value={selectedAccountId}
            onChange={(e) => setSelectedAccountId(e.target.value)}
          >
            {accounts.length === 0 ? (
              <option value="">No accounts found</option>
            ) : (
              accounts.map((acc) => (
                <option key={acc.id} value={acc.id}>
                  {acc.name} — ({acc.id.substring(0, 8)}...)
                </option>
              ))
            )}
          </select>

          <button
            className="btn-subtle"
            onClick={() => {
              if (selectedAccountId) {
                fetchBalance(selectedAccountId);
                fetchTransactions(selectedAccountId, typeFilter, pagination.page);
                notify("success", "Balance synchronized with database");
              }
            }}
          >
            <RefreshCw size={14} /> Refresh
          </button>
        </div>

        {accounts.length === 0 && (
          <button className="btn-subtle" onClick={seedDemoData} disabled={actionLoading} style={{ background: "rgba(99, 102, 241, 0.15)", color: "#a5b4fc", borderColor: "rgba(99, 102, 241, 0.4)" }}>
            <Sparkles size={14} /> Quick Demo Seed
          </button>
        )}
      </div>

      {/* Hero Stats Cards */}
      <div className="hero-stats-grid">
        {/* Main Balance Hero Card */}
        <div className="glass-card balance-hero-card">
          <div className="balance-title">
            <span className="balance-title-text">Available Ledger Balance</span>
            <span className="feature-pill">
              <ShieldCheck size={12} color="#10b981" /> Pessimistic Row Lock
            </span>
          </div>

          <div className="balance-hero-amount">
            ${accountBalance.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>

          {selectedAccount && (
            <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
              <div className="account-meta-badge">
                <span>ID: {selectedAccount.id}</span>
                <button
                  onClick={() => copyToClipboard(selectedAccount.id, "acc-id")}
                  style={{ background: "none", border: "none", cursor: "pointer", color: "#94a3b8" }}
                >
                  {copiedId === "acc-id" ? <Check size={12} color="#10b981" /> : <Copy size={12} />}
                </button>
              </div>
              <div className="account-meta-badge">
                <Clock size={12} /> Created: {new Date(selectedAccount.created_at).toLocaleDateString()}
              </div>
            </div>
          )}
        </div>

        {/* Inflow Stat */}
        <div className="glass-card mini-stat-card">
          <div className="mini-stat-header">
            <span className="mini-stat-label">Recent Credits</span>
            <div className="mini-stat-icon" style={{ background: "var(--emerald-bg)", color: "var(--emerald)" }}>
              <TrendingUp size={18} />
            </div>
          </div>
          <div>
            <div className="mini-stat-value" style={{ color: "var(--emerald)" }}>
              +${totalInflow.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>
              Across visible ledger entries
            </p>
          </div>
        </div>

        {/* Outflow Stat */}
        <div className="glass-card mini-stat-card">
          <div className="mini-stat-header">
            <span className="mini-stat-label">Recent Debits</span>
            <div className="mini-stat-icon" style={{ background: "var(--rose-bg)", color: "var(--rose)" }}>
              <TrendingDown size={18} />
            </div>
          </div>
          <div>
            <div className="mini-stat-value" style={{ color: "var(--rose)" }}>
              -${totalOutflow.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>
              Guaranteed no-overdraft
            </p>
          </div>
        </div>
      </div>

      {/* Main Grid: Action Panel & Ledger Explorer */}
      <div className="main-grid">
        {/* Left Column: Action Studio */}
        <div className="glass-card">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 18 }}>
            <h2 style={{ fontSize: 16, fontWeight: 700 }}>Operation Studio</h2>
            <span className="feature-pill">
              <Layers size={12} color="#6366f1" /> ACID Safe
            </span>
          </div>

          {/* Action Tabs */}
          <div className="tabs-container">
            <button
              className={`tab-btn ${activeTab === "credit" ? "active tab-credit" : ""}`}
              onClick={() => setActiveTab("credit")}
            >
              <ArrowDownLeft size={16} /> Credit
            </button>
            <button
              className={`tab-btn ${activeTab === "debit" ? "active tab-debit" : ""}`}
              onClick={() => setActiveTab("debit")}
            >
              <ArrowUpRight size={16} /> Debit
            </button>
            <button
              className={`tab-btn ${activeTab === "transfer" ? "active tab-transfer" : ""}`}
              onClick={() => setActiveTab("transfer")}
            >
              <Send size={15} /> Transfer
            </button>
          </div>

          <form onSubmit={handleTransactionSubmit}>
            {/* If Transfer, show Recipient Account Picker */}
            {activeTab === "transfer" && (
              <div className="form-group">
                <label className="form-label">
                  <span>Destination Account</span>
                  <span style={{ fontSize: 11, color: "var(--primary)" }}>Recipient</span>
                </label>
                <select
                  className="input-custom"
                  required
                  value={transferDestId}
                  onChange={(e) => setTransferDestId(e.target.value)}
                >
                  <option value="">-- Choose recipient --</option>
                  {accounts
                    .filter((a) => a.id !== selectedAccountId)
                    .map((acc) => (
                      <option key={acc.id} value={acc.id}>
                        {acc.name} ({acc.id.substring(0, 8)}...)
                      </option>
                    ))}
                </select>
              </div>
            )}

            {/* Amount with currency prefix & Preset Chips */}
            <div className="form-group">
              <label className="form-label">
                <span>Amount</span>
                <span style={{ fontSize: 11, color: "var(--text-muted)" }}>USD ($)</span>
              </label>
              <div className="input-wrapper">
                <span className="input-icon-prefix">$</span>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  required
                  placeholder="0.00"
                  className="input-custom has-prefix"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                />
              </div>

              {/* Fast Demo Preset Chips */}
              <div className="preset-chips">
                {[25, 50, 100, 250, 500].map((val) => (
                  <button
                    key={val}
                    type="button"
                    className="chip-btn"
                    onClick={() => setAmount(val.toFixed(2))}
                  >
                    +${val}
                  </button>
                ))}
              </div>
            </div>

            {/* Reference ID with Regenerate Button */}
            <div className="form-group">
              <div className="form-label">
                <span>Reference ID (Idempotency Key)</span>
                <button
                  type="button"
                  onClick={() => setRefId(`REF-${Math.floor(1000 + Math.random() * 9000)}`)}
                  style={{ background: "none", border: "none", color: "var(--primary)", fontSize: 11, fontWeight: 700, cursor: "pointer" }}
                >
                  Regenerate
                </button>
              </div>
              <input
                type="text"
                required
                className="input-custom"
                value={refId}
                onChange={(e) => setRefId(e.target.value)}
              />
              <span style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4, display: "block" }}>
                Enforces compound uniqueness: <code>UNIQUE(account_id, reference_id)</code>
              </span>
            </div>

            {/* Description */}
            <div className="form-group">
              <label className="form-label">
                <span>Description</span>
                <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Optional</span>
              </label>
              <input
                type="text"
                className="input-custom"
                placeholder={
                  activeTab === "credit"
                    ? "e.g. Salary, Client retainer"
                    : activeTab === "debit"
                    ? "e.g. AWS bill, Vendor payment"
                    : "e.g. Monthly division split"
                }
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={actionLoading}
              className={`btn-action btn-${activeTab}`}
            >
              {actionLoading ? (
                "Processing Transaction..."
              ) : activeTab === "credit" ? (
                <>
                  <ArrowDownLeft size={16} /> Execute Credit (+$)
                </>
              ) : activeTab === "debit" ? (
                <>
                  <ArrowUpRight size={16} /> Execute Debit (-$)
                </>
              ) : (
                <>
                  <Send size={15} /> Execute Atomic Transfer
                </>
              )}
            </button>
          </form>
        </div>

        {/* Right Column: Transaction Ledger Table */}
        <div className="glass-card">
          <div className="ledger-table-header">
            <div>
              <h2 style={{ fontSize: 16, fontWeight: 700 }}>Transaction Ledger</h2>
              <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
                Append-only immutable record sorted latest-first
              </p>
            </div>

            {/* Filter Pills */}
            <div className="table-filter-pills">
              <button
                className={`table-filter-pill ${typeFilter === "" ? "active" : ""}`}
                onClick={() => {
                  setTypeFilter("");
                  setPagination((p) => ({ ...p, page: 1 }));
                }}
              >
                All
              </button>
              <button
                className={`table-filter-pill ${typeFilter === "credit" ? "active" : ""}`}
                onClick={() => {
                  setTypeFilter("credit");
                  setPagination((p) => ({ ...p, page: 1 }));
                }}
              >
                Credits
              </button>
              <button
                className={`table-filter-pill ${typeFilter === "debit" ? "active" : ""}`}
                onClick={() => {
                  setTypeFilter("debit");
                  setPagination((p) => ({ ...p, page: 1 }));
                }}
              >
                Debits
              </button>
            </div>
          </div>

          {/* Modern Table */}
          <div style={{ overflowX: "auto" }}>
            <table className="modern-table">
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Amount</th>
                  <th>Reference & Note</th>
                  <th>Status</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={5} style={{ textAlign: "center", padding: "40px 0", color: "var(--text-muted)" }}>
                      Querying database ledger...
                    </td>
                  </tr>
                ) : transactions.length === 0 ? (
                  <tr>
                    <td colSpan={5} style={{ textAlign: "center", padding: "40px 0", color: "var(--text-muted)" }}>
                      No transactions recorded for this account.
                    </td>
                  </tr>
                ) : (
                  transactions.map((tx) => (
                    <tr key={tx.id}>
                      <td>
                        <span className={`tx-type-badge tx-type-${tx.type}`}>
                          {tx.type === "credit" ? <ArrowDownLeft size={12} /> : <ArrowUpRight size={12} />}
                          {tx.type}
                        </span>
                      </td>
                      <td>
                        <span className={`tx-amount-${tx.type}`}>
                          {tx.type === "credit" ? "+" : "-"}${Number(tx.amount).toFixed(2)}
                        </span>
                      </td>
                      <td>
                        <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
                          <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>
                            {tx.description || "Ledger Entry"}
                          </span>
                          <span className="ref-code">Ref: {tx.reference_id}</span>
                        </div>
                      </td>
                      <td>
                        <span className="feature-pill" style={{ color: "#34d399", borderColor: "rgba(16, 185, 129, 0.2)" }}>
                          <Check size={10} /> COMMITTED
                        </span>
                      </td>
                      <td style={{ color: "var(--text-muted)", fontSize: 12 }}>
                        {new Date(tx.created_at).toLocaleString([], {
                          month: "short",
                          day: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                          second: "2-digit"
                        })}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination Bar */}
          <div className="pagination-bar">
            <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
              Page {pagination.page} of {pagination.totalPages} • Total: {pagination.totalRecords} records
            </span>
            <div className="pagination-controls">
              <button
                className="pagination-btn"
                disabled={pagination.page <= 1}
                onClick={() => setPagination((p) => ({ ...p, page: p.page - 1 }))}
              >
                <ChevronLeft size={14} /> Prev
              </button>
              <button
                className="pagination-btn"
                disabled={pagination.page >= pagination.totalPages}
                onClick={() => setPagination((p) => ({ ...p, page: p.page + 1 }))}
              >
                Next <ChevronRight size={14} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Create Account Modal */}
      {showNewAccountModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div style={{ background: "var(--primary-glow)", color: "var(--primary)", padding: 8, borderRadius: 10 }}>
                  <User size={20} />
                </div>
                <div>
                  <h3 style={{ fontSize: 16, fontWeight: 700 }}>Open New Account</h3>
                  <p style={{ fontSize: 12, color: "var(--text-muted)" }}>Strict system-initialized 0.00 balance</p>
                </div>
              </div>
              <button
                onClick={() => setShowNewAccountModal(false)}
                style={{ background: "none", border: "none", color: "var(--text-muted)", fontSize: 18, cursor: "pointer" }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateAccount}>
              <div className="form-group">
                <label className="form-label">
                  <span>Account Holder Name</span>
                </label>
                <input
                  type="text"
                  required
                  autoFocus
                  placeholder="e.g. Satoshi Nakamoto or ACME Corp"
                  className="input-custom"
                  value={newAccountName}
                  onChange={(e) => setNewAccountName(e.target.value)}
                />
              </div>

              {/* Persona presets for quick demo */}
              <div style={{ marginBottom: 18 }}>
                <span style={{ fontSize: 11, color: "var(--text-muted)", display: "block", marginBottom: 6 }}>
                  Quick Presets:
                </span>
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                  {["Satoshi Nakamoto", "Alice Walker", "Horizon Holdings", "Elena Rostova"].map((preset) => (
                    <button
                      key={preset}
                      type="button"
                      className="chip-btn"
                      onClick={() => setNewAccountName(preset)}
                    >
                      {preset}
                    </button>
                  ))}
                </div>
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: 10 }}>
                <button
                  type="button"
                  className="btn-subtle"
                  onClick={() => setShowNewAccountModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="btn-action btn-transfer"
                  style={{ width: "auto", padding: "10px 18px" }}
                >
                  {actionLoading ? "Creating..." : "Create Account"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
